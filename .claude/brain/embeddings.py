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


def build_embeddings(brain_path: Path = Path(".claude/brain")):
    """Gera embeddings para todos os nos do grafo."""
    graph_file = brain_path / "graph.json"

    if not graph_file.exists():
        print(f"Error: No graph found at {graph_file}")
        return

    graph = json.loads(graph_file.read_text())
    nodes = graph.get("nodes", {})

    print(f"Building embeddings for {len(nodes)} nodes...")

    embeddings = {}
    count = 0

    for node_id, node_data in nodes.items():
        props = node_data.get("props", {})

        # Texto para embedding: titulo + content (or summary) + labels
        # Uses full content (up to 1000 chars) for richer embeddings
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

        text = " ".join(parts)

        if not text.strip():
            continue

        try:
            emb = get_embedding(text)
            embeddings[node_id] = emb
            count += 1

            if count % 10 == 0:
                print(f"  Processed {count} nodes...")
        except Exception as e:
            print(f"  Error embedding {node_id}: {e}")

    # Salva embeddings
    emb_file = brain_path / "embeddings.npz"
    np.savez_compressed(emb_file, **embeddings)

    print(f"Done. Saved {count} embeddings to {emb_file}")


def search_embeddings(
    query: str,
    brain_path: Path = Path(".claude/brain"),
    top_k: int = 10
) -> List[dict]:
    """Busca semantica no grafo."""
    # Carrega grafo
    graph_file = brain_path / "graph.json"
    if not graph_file.exists():
        print(f"Error: No graph found at {graph_file}")
        return []

    graph = json.loads(graph_file.read_text())
    nodes = graph.get("nodes", {})

    # Carrega embeddings
    emb_file = brain_path / "embeddings.npz"
    if not emb_file.exists():
        print(f"Error: No embeddings found at {emb_file}")
        print("Run: python embeddings.py build")
        return []

    loaded = np.load(emb_file)
    embeddings = {k: loaded[k] for k in loaded.files}

    # Gera embedding da query
    query_emb = get_embedding(query)

    # Calcula similaridade
    results = []

    for node_id, emb in embeddings.items():
        # Cosine similarity
        dot = np.dot(query_emb, emb)
        norm = np.linalg.norm(query_emb) * np.linalg.norm(emb)

        if norm > 0:
            sim = dot / norm
            node_data = nodes.get(node_id, {})
            props = node_data.get("props", {})

            results.append({
                "id": node_id,
                "score": float(sim),
                "title": props.get("title", "N/A"),
                "labels": node_data.get("labels", []),
                "summary": props.get("summary", "")[:100]
            })

    # Ordena por similaridade
    results.sort(key=lambda x: x["score"], reverse=True)

    return results[:top_k]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: embeddings.py <command> [args]")
        print("Commands:")
        print("  build              Build embeddings for all nodes")
        print("  search <query>     Semantic search")
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

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
