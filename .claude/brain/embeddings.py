#!/usr/bin/env python3
"""
embeddings.py - Geracao de embeddings para busca semantica

Suporta dois providers:
- local: sentence-transformers (gratis, offline)
- openai: text-embedding-ada-002 (melhor qualidade, pago)

Uso:
    python embeddings.py build          # Gera embeddings para todos os nos
    python embeddings.py search "query" # Busca semantica

Instalacao (local):
    pip install sentence-transformers

Instalacao (openai):
    pip install openai
    export OPENAI_API_KEY=sk-...
"""

import json
import os
import site
import sys
from pathlib import Path
from typing import List, Optional

# Auto-activate brain venv (PAT-036)
_venv_dir = Path(__file__).parent / ".venv"
if _venv_dir.exists() and "brain/.venv" not in os.environ.get("VIRTUAL_ENV", ""):
    _site_packages = list(_venv_dir.glob("lib/python*/site-packages"))
    if _site_packages:
        site.addsitedir(str(_site_packages[0]))

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("Error: numpy required. Run: pip install numpy")
    sys.exit(1)


# Provider de embedding (pode ser alterado)
PROVIDER = os.environ.get("EMBEDDING_PROVIDER", "local")  # "local" ou "openai"


def get_embedding_local(text: str) -> np.ndarray:
    """Embedding local com sentence-transformers (gratis)."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("Error: sentence-transformers required. Run: pip install sentence-transformers")
        sys.exit(1)

    # Usa cache de modelo
    if not hasattr(get_embedding_local, "model"):
        print("Loading local embedding model...")
        get_embedding_local.model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Model loaded.")

    return get_embedding_local.model.encode(text)


def get_embedding_openai(text: str) -> np.ndarray:
    """Embedding via OpenAI (melhor qualidade, pago)."""
    try:
        import openai
    except ImportError:
        print("Error: openai required. Run: pip install openai")
        sys.exit(1)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set")
        sys.exit(1)

    client = openai.OpenAI(api_key=api_key)

    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )

    return np.array(response.data[0].embedding)


def get_embedding(text: str) -> np.ndarray:
    """Obtem embedding usando provider configurado."""
    if PROVIDER == "openai":
        return get_embedding_openai(text)
    else:
        return get_embedding_local(text)


def _load_all_nodes(brain_path: Path) -> dict:
    """Load all nodes from the brain via SQLite backend.

    Returns {node_id: node_data} dict.
    """
    sys.path.insert(0, str(Path(__file__).parent))

    from brain_sqlite import BrainSQLite
    brain = BrainSQLite(base_path=brain_path)
    brain.load()
    return brain.get_all_nodes()


def _get_brain(brain_path: Path):
    """Get a BrainSQLite instance (loaded)."""
    sys.path.insert(0, str(Path(__file__).parent))
    from brain_sqlite import BrainSQLite
    brain = BrainSQLite(base_path=brain_path)
    brain.load()
    return brain


def _node_to_text(node_id: str, node_data: dict) -> str:
    """Build embedding text from a node's data."""
    props = node_data.get("props", {})
    parts = []

    title = props.get("title", "")
    if title:
        parts.append(title)

    content = props.get("content", "")
    if content:
        parts.append(content[:1000])
    else:
        summary = props.get("summary", "")
        if summary:
            parts.append(summary)

    labels = node_data.get("labels", [])
    if labels:
        parts.append(" ".join(labels))

    return " ".join(parts)


def build_embeddings(brain_path: Path = Path(__file__).parent):
    """Build embeddings for all nodes, using ChromaDB (primary) or npz (fallback)."""
    brain = _get_brain(brain_path)
    nodes = brain.get_all_nodes()

    if not nodes:
        print("Error: No nodes found in brain")
        return

    print(f"Building embeddings for {len(nodes)} nodes...")

    # Try ChromaDB via brain's vector store
    brain._ensure_vector_store()
    use_chroma = brain._use_chromadb and brain._chroma_collection is not None

    embeddings = {}
    count = 0
    batch_ids = []
    batch_embeddings = []
    batch_size = 100

    for node_id, node_data in nodes.items():
        text = _node_to_text(node_id, node_data)
        if not text.strip():
            continue

        try:
            emb = get_embedding(text)

            if use_chroma:
                emb_list = emb.tolist() if hasattr(emb, 'tolist') else list(emb)
                batch_ids.append(node_id)
                batch_embeddings.append(emb_list)

                if len(batch_ids) >= batch_size:
                    brain._chroma_collection.upsert(
                        ids=batch_ids,
                        embeddings=batch_embeddings
                    )
                    batch_ids = []
                    batch_embeddings = []
            else:
                embeddings[node_id] = emb

            count += 1
            if count % 10 == 0:
                print(f"  Processed {count} nodes...")
        except Exception as e:
            print(f"  Error embedding {node_id}: {e}")

    # Flush remaining ChromaDB batch
    if use_chroma and batch_ids:
        brain._chroma_collection.upsert(
            ids=batch_ids,
            embeddings=batch_embeddings
        )
        print(f"Done. Stored {count} embeddings in ChromaDB")
    else:
        # Fallback: save to npz
        emb_file = brain_path / "embeddings.npz"
        np.savez_compressed(emb_file, **embeddings)
        print(f"Done. Saved {count} embeddings to {emb_file}")


def search_embeddings(
    query: str,
    brain_path: Path = Path(__file__).parent,
    top_k: int = 10
) -> List[dict]:
    """Semantic search using ChromaDB (primary) or npz fallback."""
    brain = _get_brain(brain_path)
    nodes = brain.get_all_nodes()

    if not nodes:
        print("Error: No nodes found in brain")
        return []

    # Generate query embedding
    query_emb = get_embedding(query)

    # Use brain's search_by_embedding (handles ChromaDB vs npz)
    pairs = brain.search_by_embedding(query_emb, top_k=top_k)

    results = []
    for node_id, score in pairs:
        node_data = nodes.get(node_id, {})
        props = node_data.get("props", {})
        results.append({
            "id": node_id,
            "score": float(score),
            "title": props.get("title", "N/A"),
            "labels": node_data.get("labels", []),
            "summary": props.get("summary", "")[:100]
        })

    return results


def migrate_embeddings(brain_path: Path = Path(__file__).parent):
    """Migrate embeddings from npz to ChromaDB.

    Reads existing embeddings.npz and upserts all vectors into ChromaDB.
    """
    emb_file = brain_path / "embeddings.npz"
    if not emb_file.exists():
        print(f"No embeddings.npz found at {emb_file}")
        return

    brain = _get_brain(brain_path)
    brain._ensure_vector_store()

    if not brain._use_chromadb or brain._chroma_collection is None:
        print("Error: ChromaDB not available. Install: pip install chromadb")
        return

    # Load npz
    loaded = np.load(emb_file)
    node_ids = loaded.files
    print(f"Migrating {len(node_ids)} embeddings from npz to ChromaDB...")

    batch_ids = []
    batch_embeddings = []
    batch_size = 100
    count = 0

    for node_id in node_ids:
        emb = loaded[node_id]
        emb_list = emb.tolist() if hasattr(emb, 'tolist') else list(emb)
        batch_ids.append(node_id)
        batch_embeddings.append(emb_list)

        if len(batch_ids) >= batch_size:
            brain._chroma_collection.upsert(
                ids=batch_ids,
                embeddings=batch_embeddings
            )
            count += len(batch_ids)
            print(f"  Migrated {count} embeddings...")
            batch_ids = []
            batch_embeddings = []

    # Flush remaining
    if batch_ids:
        brain._chroma_collection.upsert(
            ids=batch_ids,
            embeddings=batch_embeddings
        )
        count += len(batch_ids)

    print(f"Done. Migrated {count} embeddings to ChromaDB")
    print(f"ChromaDB collection count: {brain._chroma_collection.count()}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: embeddings.py <command> [args]")
        print("Commands:")
        print("  build              Build embeddings for all nodes")
        print("  search <query>     Semantic search")
        print("  migrate            Migrate npz -> ChromaDB")
        print("")
        print(f"Current provider: {PROVIDER}")
        print("Set EMBEDDING_PROVIDER=openai for OpenAI embeddings")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "build":
        build_embeddings()

    elif cmd == "search":
        if len(sys.argv) < 3:
            print("Usage: embeddings.py search <query>")
            sys.exit(1)

        query = " ".join(sys.argv[2:])
        results = search_embeddings(query)

        print(f"\nResults for: {query}\n")
        for r in results:
            print(f"{r['score']:.3f} | {r['title']}")
            print(f"       Labels: {', '.join(r['labels'])}")
            if r['summary']:
                print(f"       {r['summary']}...")
            print()

    elif cmd == "migrate":
        migrate_embeddings()

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
