#!/usr/bin/env python3
"""
brain_sqlite.py - SQLite + FTS5 backend for the Organizational Brain (Schema v2)

Drop-in replacement for Brain (brain.py). Same public API, backed by
SQLite instead of in-memory graph + JSON.

Schema v2 improvements over v1:
- Single source of truth: `properties` JSON column with GENERATED STORED columns
- Normalized labels: `node_labels` table with indexed lookups (no json_each scans)
- Multi-edge support: UNIQUE(from_id, to_id, type) instead of PRIMARY KEY(src, tgt)
- Zero json.loads() in Python: all extraction done via SQL generated columns

Usage:
    from brain_sqlite import BrainSQLite as Brain

    brain = Brain()
    brain.load()
    brain.add_memory(...)
    results = brain.retrieve(query="authentication")
"""

import json
import math
import hashlib
import subprocess
import re
import os
import site
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from uuid import uuid4

# ── Auto-activate brain venv (PAT-012) ──
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

# ── ChromaDB import with Python 3.14 workaround ──
# ChromaDB ≤1.4.1 uses pydantic.v1 compat layer which crashes on Python 3.14+.
# The fix (PR #6356) uses pydantic-settings instead, but isn't released yet.
# Workaround: pre-inject pydantic_settings.BaseSettings into pydantic namespace
# so chromadb.config finds it at `from pydantic import BaseSettings`.
# See: https://github.com/chroma-core/chroma/issues/5996
# Remove this block when ChromaDB releases with PR #6356 merged.
HAS_CHROMADB = False
if sys.version_info >= (3, 14):
    try:
        import pydantic
        import pydantic_settings
        pydantic.BaseSettings = pydantic_settings.BaseSettings
    except Exception:
        pass
try:
    import chromadb
    HAS_CHROMADB = True
except Exception:
    pass


# ══════════════════════════════════════════════════════════
# SCHEMA v2 — Hybrid Property Graph with Generated Columns
# ══════════════════════════════════════════════════════════

SCHEMA_VERSION = "2"

SCHEMA_SQL = """\
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS nodes (
    id          TEXT PRIMARY KEY,
    properties  JSON NOT NULL DEFAULT '{}',
    -- Generated STORED columns (auto-extracted from properties)
    title       TEXT GENERATED ALWAYS AS (json_extract(properties, '$.title')) STORED,
    author      TEXT GENERATED ALWAYS AS (json_extract(properties, '$.author')) STORED,
    content     TEXT GENERATED ALWAYS AS (json_extract(properties, '$.content')) STORED,
    summary     TEXT GENERATED ALWAYS AS (json_extract(properties, '$.summary')) STORED,
    strength    REAL GENERATED ALWAYS AS (COALESCE(json_extract(properties, '$.strength'), 1.0)) STORED,
    access_count INTEGER GENERATED ALWAYS AS (COALESCE(json_extract(properties, '$.access_count'), 0)) STORED,
    last_accessed TEXT GENERATED ALWAYS AS (json_extract(properties, '$.last_accessed')) STORED,
    created_at  TEXT GENERATED ALWAYS AS (json_extract(properties, '$.created_at')) STORED,
    decay_rate  REAL GENERATED ALWAYS AS (COALESCE(json_extract(properties, '$.decay_rate'), 0.02)) STORED
);

CREATE TABLE IF NOT EXISTS node_labels (
    node_id TEXT NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    label   TEXT NOT NULL,
    PRIMARY KEY (node_id, label)
);

CREATE TABLE IF NOT EXISTS edges (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    from_id    TEXT NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    to_id      TEXT NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    type       TEXT NOT NULL DEFAULT 'REFERENCES',
    weight     REAL NOT NULL DEFAULT 0.5,
    properties JSON NOT NULL DEFAULT '{}',
    created_at TEXT,
    UNIQUE(from_id, to_id, type)
);

CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE INDEX IF NOT EXISTS idx_labels_label ON node_labels(label);
CREATE INDEX IF NOT EXISTS idx_nodes_author ON nodes(author);
CREATE INDEX IF NOT EXISTS idx_nodes_strength ON nodes(strength);
CREATE INDEX IF NOT EXISTS idx_nodes_last_accessed ON nodes(last_accessed);
CREATE INDEX IF NOT EXISTS idx_edges_from ON edges(from_id);
CREATE INDEX IF NOT EXISTS idx_edges_to ON edges(to_id);
CREATE INDEX IF NOT EXISTS idx_edges_type ON edges(type);
CREATE INDEX IF NOT EXISTS idx_nodes_created_at ON nodes(created_at);
"""

FTS_SCHEMA_SQL = """\
CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(
    title, content, summary,
    content='nodes', content_rowid='rowid',
    tokenize='porter unicode61'
);

CREATE TRIGGER IF NOT EXISTS nodes_ai AFTER INSERT ON nodes BEGIN
    INSERT INTO nodes_fts(rowid, title, content, summary)
    VALUES (new.rowid, new.title, new.content, new.summary);
END;

CREATE TRIGGER IF NOT EXISTS nodes_ad AFTER DELETE ON nodes BEGIN
    INSERT INTO nodes_fts(nodes_fts, rowid, title, content, summary)
    VALUES ('delete', old.rowid, old.title, old.content, old.summary);
END;

CREATE TRIGGER IF NOT EXISTS nodes_au AFTER UPDATE ON nodes BEGIN
    INSERT INTO nodes_fts(nodes_fts, rowid, title, content, summary)
    VALUES ('delete', old.rowid, old.title, old.content, old.summary);
    INSERT INTO nodes_fts(rowid, title, content, summary)
    VALUES (new.rowid, new.title, new.content, new.summary);
END;
"""


class BrainSQLite:
    """
    Organizational brain backed by SQLite + FTS5 (Schema v2).
    Same public API as Brain (brain.py).
    """

    def __init__(self, base_path: Path = None):
        if base_path is None:
            base_path = Path(__file__).parent
        self.base_path = Path(base_path)
        self.memory_path = self.base_path.parent / "memory"
        self.db_path = self.base_path / "brain.db"

        # Connection (lazy — opened on load())
        self._conn: Optional[sqlite3.Connection] = None

        # Vector store: ChromaDB (primary) or numpy dict (fallback)
        self._chroma_client = None
        self._chroma_collection = None
        self._use_chromadb = False
        self._npz_embeddings: Dict[str, Any] = {}  # fallback numpy store
        self._embeddings_dirty = False

        # Cache
        self._stats_cache = None
        self._stats_time = None

    # ══════════════════════════════════════════════════════════
    # CONNECTION
    # ══════════════════════════════════════════════════════════

    def _get_conn(self) -> sqlite3.Connection:
        """Get or create the SQLite connection."""
        if self._conn is None:
            self.base_path.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode = WAL")
            self._conn.execute("PRAGMA foreign_keys = ON")
        return self._conn

    def _init_schema(self):
        """Create tables, indexes, and FTS if they don't exist."""
        conn = self._get_conn()
        conn.executescript(SCHEMA_SQL)
        try:
            conn.executescript(FTS_SCHEMA_SQL)
        except sqlite3.OperationalError:
            pass
        # Set schema version
        conn.execute(
            "INSERT OR IGNORE INTO meta (key, value) VALUES ('schema_version', ?)",
            (SCHEMA_VERSION,)
        )
        conn.commit()

    # ══════════════════════════════════════════════════════════
    # PERSISTENCE
    # ══════════════════════════════════════════════════════════

    def load(self) -> bool:
        """Open brain.db (or create it with empty schema v2)."""
        if not self.db_path.exists():
            self._init_schema()
            if self.db_path.exists():
                return self._finish_load()
            return True

        self._init_schema()
        return self._finish_load()

    def _finish_load(self) -> bool:
        """Finish loading: print stats and return True."""
        conn = self._get_conn()
        node_count = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
        edge_count = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
        sys.stderr.write(f"Loaded: {node_count} nodes, {edge_count} edges\n")
        return True

    def _ensure_vector_store(self):
        """Initialize vector store: ChromaDB (primary) or npz fallback."""
        if self._use_chromadb:
            return  # already initialized
        if self._npz_embeddings:
            return  # fallback already loaded

        # Try ChromaDB first
        if HAS_CHROMADB:
            try:
                chroma_path = self.base_path / "chroma"
                chroma_path.mkdir(parents=True, exist_ok=True)
                self._chroma_client = chromadb.PersistentClient(
                    path=str(chroma_path)
                )
                self._chroma_collection = self._chroma_client.get_or_create_collection(
                    name="brain_embeddings",
                    metadata={"hnsw:space": "cosine"}
                )
                self._use_chromadb = True
                count = self._chroma_collection.count()
                if count > 0:
                    sys.stderr.write(f"Loaded: {count} embeddings (ChromaDB)\n")
                return
            except Exception as e:
                sys.stderr.write(f"ChromaDB init failed, falling back to npz: {e}\n")
                self._chroma_client = None
                self._chroma_collection = None
                self._use_chromadb = False

        # Fallback: load from npz
        if not HAS_NUMPY:
            return
        emb_file = self.base_path / "embeddings.npz"
        if emb_file.exists():
            try:
                loaded = np.load(emb_file)
                self._npz_embeddings = {k: loaded[k] for k in loaded.files}
                sys.stderr.write(f"Loaded: {len(self._npz_embeddings)} embeddings (npz)\n")
            except Exception as e:
                print(f"Error loading embeddings: {e}")

    def _store_embedding(self, node_id: str, embedding, metadata: Dict[str, Any] = None):
        """Store an embedding in the active vector store."""
        self._ensure_vector_store()
        if self._use_chromadb and self._chroma_collection is not None:
            emb_list = embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
            meta = metadata or {}
            # ChromaDB doesn't allow None values in metadata
            meta = {k: v for k, v in meta.items() if v is not None}
            self._chroma_collection.upsert(
                ids=[node_id],
                embeddings=[emb_list],
                metadatas=[meta] if meta else None
            )
        elif HAS_NUMPY:
            self._npz_embeddings[node_id] = np.array(embedding)
            self._embeddings_dirty = True

    def _generate_embedding(self, title: str, content: str, labels: List[str]):
        """Generate embedding inline. Returns None silently if deps unavailable."""
        if not HAS_NUMPY:
            return None
        if not hasattr(self, '_embedding_model'):
            self._embedding_model = None
            self._embedding_model_name = None
            try:
                from sentence_transformers import SentenceTransformer
                model_name = 'all-MiniLM-L6-v2'
                self._embedding_model = SentenceTransformer(model_name)
                self._embedding_model_name = model_name
            except Exception:
                pass
        if self._embedding_model is None:
            return None
        try:
            text = f"{title} {(content or '')[:1000]} {' '.join(labels)}"
            emb = self._embedding_model.encode(text)
            # Track model info on first successful generation
            if not hasattr(self, '_model_tracked'):
                self._track_embedding_model(self._embedding_model_name, len(emb))
                self._model_tracked = True
            return emb
        except Exception:
            return None

    def _track_embedding_model(self, model_name: str, dim: int):
        """Store embedding model info in meta table for compatibility checks."""
        conn = self._get_conn()
        existing_model = conn.execute(
            "SELECT value FROM meta WHERE key = 'embedding_model'"
        ).fetchone()
        existing_dim = conn.execute(
            "SELECT value FROM meta WHERE key = 'embedding_dim'"
        ).fetchone()

        if existing_model and existing_model["value"] != model_name:
            sys.stderr.write(
                f"WARNING: Embedding model changed from '{existing_model['value']}' "
                f"to '{model_name}'. Run 'python3 embeddings.py build' to re-embed.\n"
            )
        if existing_dim and int(existing_dim["value"]) != dim:
            sys.stderr.write(
                f"WARNING: Embedding dimension changed from {existing_dim['value']} "
                f"to {dim}. Existing embeddings are incompatible!\n"
            )

        conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES ('embedding_model', ?)",
            (model_name,)
        )
        conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES ('embedding_dim', ?)",
            (str(dim),)
        )
        conn.commit()

    def _remove_embedding(self, node_id: str):
        """Remove an embedding from the active vector store."""
        if self._use_chromadb and self._chroma_collection is not None:
            try:
                self._chroma_collection.delete(ids=[node_id])
            except Exception:
                pass  # ID might not exist
        self._npz_embeddings.pop(node_id, None)

    def _embedding_count(self) -> int:
        """Count embeddings in the active vector store."""
        self._ensure_vector_store()
        if self._use_chromadb and self._chroma_collection is not None:
            return self._chroma_collection.count()
        return len(self._npz_embeddings)

    def get_embedding_vectors(self, node_ids: List[str]) -> Dict[str, Any]:
        """Batch fetch embeddings for given node IDs.

        Used by sleep.py phase_relate() for matrix operations.
        Returns {node_id: numpy_array} dict.
        """
        self._ensure_vector_store()
        result = {}

        if self._use_chromadb and self._chroma_collection is not None:
            if not node_ids:
                return result
            try:
                fetched = self._chroma_collection.get(
                    ids=node_ids,
                    include=["embeddings"]
                )
                ids = fetched.get("ids") if fetched else []
                embs = fetched.get("embeddings") if fetched else None
                if ids and embs is not None and HAS_NUMPY:
                    for nid, emb in zip(ids, embs):
                        if emb is not None:
                            result[nid] = np.array(emb)
            except Exception:
                pass  # some IDs might not exist
        else:
            for nid in node_ids:
                if nid in self._npz_embeddings:
                    result[nid] = self._npz_embeddings[nid]

        return result

    @property
    def embeddings(self) -> Dict[str, Any]:
        """Backward-compat property for sleep.py and other consumers.

        Returns the npz fallback dict. When ChromaDB is active, this may be
        empty — consumers should use get_embedding_vectors() instead.
        """
        return self._npz_embeddings

    @embeddings.setter
    def embeddings(self, value: Dict[str, Any]):
        """Backward-compat setter."""
        self._npz_embeddings = value

    def save(self):
        """No-op for graph data (SQLite auto-persists).

        ChromaDB auto-persists too. Only saves npz fallback if dirty.
        """
        if self._use_chromadb:
            return  # ChromaDB PersistentClient auto-persists
        if self._embeddings_dirty and HAS_NUMPY and self._npz_embeddings:
            self.base_path.mkdir(parents=True, exist_ok=True)
            emb_file = self.base_path / "embeddings.npz"
            np.savez_compressed(emb_file, **self._npz_embeddings)
            print(f"Saved: {emb_file}")
            self._embeddings_dirty = False

    def close(self):
        """Close the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    # ══════════════════════════════════════════════════════════
    # PROPERTIES HELPERS
    # ══════════════════════════════════════════════════════════

    def _build_properties(self, title: str, author: str, content: str,
                          summary: str, strength: float, access_count: int,
                          last_accessed: str, created_at: str, decay_rate: float,
                          extra_props: Dict[str, Any] = None) -> str:
        """Build a unified properties JSON blob."""
        props = {
            "title": title,
            "author": author,
            "content": content,
            "summary": summary,
            "strength": strength,
            "access_count": access_count,
            "last_accessed": last_accessed,
            "created_at": created_at,
            "decay_rate": decay_rate,
        }
        if extra_props:
            props.update(extra_props)
        return json.dumps(props, default=str)

    def _set_labels(self, node_id: str, labels: List[str]):
        """Set labels for a node (replaces existing)."""
        conn = self._get_conn()
        conn.execute("DELETE FROM node_labels WHERE node_id = ?", (node_id,))
        for label in labels:
            conn.execute(
                "INSERT OR IGNORE INTO node_labels (node_id, label) VALUES (?, ?)",
                (node_id, label)
            )

    def _add_labels(self, node_id: str, labels: List[str]):
        """Add labels to a node (keeps existing)."""
        conn = self._get_conn()
        for label in labels:
            conn.execute(
                "INSERT OR IGNORE INTO node_labels (node_id, label) VALUES (?, ?)",
                (node_id, label)
            )

    def _get_labels(self, node_id: str) -> List[str]:
        """Get labels for a node."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT label FROM node_labels WHERE node_id = ?", (node_id,)
        ).fetchall()
        return [r["label"] for r in rows]

    # ══════════════════════════════════════════════════════════
    # ENCODING (create memory)
    # ══════════════════════════════════════════════════════════

    def add_memory(
        self,
        title: str,
        content: str,
        labels: List[str],
        author: str,
        props: Dict[str, Any] = None,
        references: List[str] = None,
        embedding: Any = None
    ) -> str:
        """Add a new memory to the brain. Same API as Brain.add_memory()."""
        # Deterministic ID: md5(title|labels) for dedup
        id_source = f"{title}|{'|'.join(sorted(labels))}"
        node_id = hashlib.md5(id_source.encode()).hexdigest()[:8]
        now = datetime.now().isoformat()

        # Upsert: if node already exists, update
        if self._node_exists(node_id):
            return self._upsert_node(node_id, title, content, labels, author, props, references, embedding)

        summary = self._generate_summary(content)
        extra_props = dict(props or {})
        decay_rate = self._get_decay_rate(labels)

        properties_json = self._build_properties(
            title=title, author=author, content=content, summary=summary,
            strength=1.0, access_count=1, last_accessed=now, created_at=now,
            decay_rate=decay_rate, extra_props=extra_props
        )

        conn = self._get_conn()
        conn.execute(
            "INSERT INTO nodes (id, properties) VALUES (?, ?)",
            (node_id, properties_json)
        )
        self._set_labels(node_id, labels)
        conn.commit()

        # Embedding (inline generation if not provided)
        if embedding is None:
            embedding = self._generate_embedding(title, content, labels)
        if embedding is not None:
            emb_metadata = {
                "labels": ",".join(labels),
                "author": author or "",
                "created_at": now,
                "title": title[:200] if title else "",
            }
            self._store_embedding(node_id, embedding, metadata=emb_metadata)

        # Author edge
        author_node = self._ensure_person_node(author)
        self.add_edge(node_id, author_node, "AUTHORED_BY")

        # Reference edges
        if references:
            for ref_id in references:
                if self._node_exists(ref_id):
                    self.add_edge(node_id, ref_id, "REFERENCES")

        # Extract [[links]] from content
        links = self._extract_links(content)
        for link in links:
            target = self._resolve_link(link)
            if target:
                self.add_edge(node_id, target, "REFERENCES")

        # Domain inference
        domain = self._infer_domain(content, labels)
        if domain:
            domain_node = self._ensure_domain_node(domain)
            self.add_edge(node_id, domain_node, "BELONGS_TO")

        return node_id

    def _upsert_node(
        self,
        node_id: str,
        title: str,
        content: str,
        labels: List[str],
        author: str,
        props: Dict[str, Any] = None,
        references: List[str] = None,
        embedding: Any = None
    ) -> str:
        """Update existing node instead of creating duplicate."""
        conn = self._get_conn()
        row = conn.execute("SELECT properties FROM nodes WHERE id = ?", (node_id,)).fetchone()
        if row is None:
            return node_id

        existing_props = json.loads(row["properties"])

        # Merge extra props
        if props:
            existing_props.update(props)

        # Update core fields
        existing_props["title"] = title
        existing_props["content"] = content
        existing_props["summary"] = self._generate_summary(content)
        existing_props["last_accessed"] = datetime.now().isoformat()

        conn.execute(
            "UPDATE nodes SET properties = ? WHERE id = ?",
            (json.dumps(existing_props, default=str), node_id)
        )

        # Merge labels (union)
        existing_labels = set(self._get_labels(node_id))
        existing_labels.update(labels)
        self._set_labels(node_id, list(existing_labels))
        conn.commit()

        # Embedding (inline generation if not provided)
        if embedding is None:
            embedding = self._generate_embedding(title, content, labels)
        if embedding is not None:
            emb_metadata = {
                "labels": ",".join(list(existing_labels)),
                "author": author or "",
                "created_at": existing_props.get("created_at", ""),
                "title": title[:200] if title else "",
            }
            self._store_embedding(node_id, embedding, metadata=emb_metadata)

        # New references
        if references:
            for ref_id in references:
                resolved = self._resolve_link(ref_id) if not self._node_exists(ref_id) else ref_id
                if resolved and not self.has_edge(node_id, resolved):
                    self.add_edge(node_id, resolved, "REFERENCES")

        return node_id

    def add_edge(
        self,
        source: str,
        target: str,
        edge_type: str,
        weight: float = 0.5,
        props: Dict[str, Any] = None
    ):
        """Add an edge to the graph. Multi-edge safe (unique per type)."""
        conn = self._get_conn()
        now = datetime.now().isoformat()
        try:
            conn.execute(
                """INSERT INTO edges (from_id, to_id, type, weight, properties, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(from_id, to_id, type) DO UPDATE SET
                       weight = MAX(weight, excluded.weight)""",
                (source, target, edge_type, weight,
                 json.dumps(props or {}, default=str), now)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # FK violation — endpoint doesn't exist

    def add_node_raw(self, node_id: str, labels: List[str] = None,
                     props: Dict[str, Any] = None, memory: Dict[str, Any] = None):
        """Add a synthetic node directly (for Theme, PatternCluster, etc.).

        This bypasses add_memory() — no author edge, no domain inference.
        Used by sleep.py for synthetic nodes.
        """
        labels = labels or []
        props = props or {}
        memory = memory or {}
        now = datetime.now().isoformat()

        # Build properties blob merging props + memory
        properties = {
            "title": props.get("title", ""),
            "author": props.get("author", ""),
            "content": props.get("content", ""),
            "summary": props.get("summary", ""),
            "strength": memory.get("strength", 1.0),
            "access_count": memory.get("access_count", 0),
            "last_accessed": memory.get("last_accessed", now),
            "created_at": memory.get("created_at", now),
            "decay_rate": memory.get("decay_rate", 0.02),
        }
        # Add extra props that aren't core fields
        for k, v in props.items():
            if k not in ("title", "author", "content", "summary"):
                properties[k] = v

        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT OR IGNORE INTO nodes (id, properties) VALUES (?, ?)",
                (node_id, json.dumps(properties, default=str))
            )
            for label in labels:
                conn.execute(
                    "INSERT OR IGNORE INTO node_labels (node_id, label) VALUES (?, ?)",
                    (node_id, label)
                )
            conn.commit()
        except sqlite3.IntegrityError:
            pass

    # ══════════════════════════════════════════════════════════
    # HELPERS (same as brain.py)
    # ══════════════════════════════════════════════════════════

    def _generate_summary(self, content: str, max_length: int = 500) -> str:
        """Generate summary from content."""
        text = re.sub(r'#+ ', '', content)
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
        text = re.sub(r'\n+', ' ', text)
        text = text.strip()
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."

    def _get_decay_rate(self, labels: List[str]) -> float:
        """Decay rate per memory type."""
        if "Decision" in labels:
            return 0.001
        elif "Pattern" in labels:
            return 0.005
        elif "Concept" in labels:
            return 0.003
        elif "Episode" in labels:
            return 0.01
        elif "Person" in labels:
            return 0.0001
        else:
            return 0.02

    def _ensure_person_node(self, author: str) -> str:
        """Ensure a Person node exists for the author."""
        if "@" in author and not author.startswith("@"):
            person_id = f"person-{author}"
            display_name = author.split("@")[0]
        elif author.startswith("@"):
            existing = self._find_person_by_alias(author)
            if existing:
                return existing
            person_id = f"person-{author[1:]}"
            display_name = author[1:]
        else:
            person_id = f"person-{author}"
            display_name = author

        if not self._node_exists(person_id):
            now = datetime.now().isoformat()
            extra_props = {
                "email": author if "@" in author and not author.startswith("@") else "",
                "name": display_name,
                "aliases": [author] if author.startswith("@") else [],
            }
            properties = self._build_properties(
                title=display_name, author="", content="", summary="",
                strength=1.0, access_count=0, last_accessed=now,
                created_at=now, decay_rate=0.0001, extra_props=extra_props
            )
            conn = self._get_conn()
            conn.execute(
                "INSERT OR IGNORE INTO nodes (id, properties) VALUES (?, ?)",
                (person_id, properties)
            )
            conn.execute(
                "INSERT OR IGNORE INTO node_labels (node_id, label) VALUES (?, ?)",
                (person_id, "Person")
            )
            conn.commit()

        return person_id

    def _find_person_by_alias(self, alias: str) -> Optional[str]:
        """Find Person node by alias (@username)."""
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT n.id, n.properties FROM nodes n
               JOIN node_labels nl ON n.id = nl.node_id
               WHERE nl.label = 'Person'"""
        ).fetchall()
        for row in rows:
            p = json.loads(row["properties"])
            if alias in p.get("aliases", []):
                return row["id"]
        return None

    def _ensure_domain_node(self, domain: str) -> str:
        """Ensure a Domain node exists."""
        domain_id = f"domain-{domain.lower()}"
        if not self._node_exists(domain_id):
            now = datetime.now().isoformat()
            properties = self._build_properties(
                title=domain, author="", content="", summary="",
                strength=1.0, access_count=0, last_accessed=now,
                created_at=now, decay_rate=0.0001,
                extra_props={"name": domain}
            )
            conn = self._get_conn()
            conn.execute(
                "INSERT OR IGNORE INTO nodes (id, properties) VALUES (?, ?)",
                (domain_id, properties)
            )
            conn.execute(
                "INSERT OR IGNORE INTO node_labels (node_id, label) VALUES (?, ?)",
                (domain_id, "Domain")
            )
            conn.commit()
        return domain_id

    def _node_exists(self, node_id: str) -> bool:
        """Check if node exists."""
        conn = self._get_conn()
        row = conn.execute("SELECT 1 FROM nodes WHERE id = ?", (node_id,)).fetchone()
        return row is not None

    def _extract_links(self, content: str) -> List[str]:
        """Extract [[links]] from content."""
        return re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', content)

    def _resolve_link(self, link: str) -> Optional[str]:
        """Resolve link to node ID."""
        conn = self._get_conn()

        # Person
        if link.startswith("@"):
            pid = f"person-{link[1:]}"
            if self._node_exists(pid):
                return pid
            return None

        # ADR-XXX
        if link.upper().startswith("ADR-"):
            found = self._find_node_by_prop("adr_id", link.upper())
            if found:
                return found
            legacy = f"decision-{link.lower()}"
            if self._node_exists(legacy):
                return legacy

        # PAT-XXX
        if link.upper().startswith("PAT-"):
            found = self._find_node_by_prop("pat_id", link.upper())
            if found:
                return found

        # EXP-XXX
        if link.upper().startswith("EXP-"):
            found = self._find_node_by_prop("exp_id", link.upper())
            if found:
                return found

        # Title prefix match
        found = self._find_node_by_title_prefix(link)
        if found:
            return found

        # Exact title match
        row = conn.execute(
            "SELECT id FROM nodes WHERE LOWER(title) = LOWER(?)", (link,)
        ).fetchone()
        if row:
            return row["id"]

        return None

    def _find_node_by_prop(self, prop_name: str, prop_value: str) -> Optional[str]:
        """Find a node by a specific property value."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT id FROM nodes WHERE UPPER(json_extract(properties, ?)) = UPPER(?)",
            (f"$.{prop_name}", prop_value)
        ).fetchone()
        if row:
            return row["id"]
        return None

    def _find_node_by_title_prefix(self, prefix: str) -> Optional[str]:
        """Find a node whose title starts with prefix."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT id FROM nodes WHERE LOWER(title) LIKE LOWER(?) || '%'",
            (prefix,)
        ).fetchone()
        if row:
            return row["id"]
        return None

    def _infer_domain(self, content: str, labels: List[str]) -> Optional[str]:
        """Infer domain from content."""
        content_lower = content.lower()
        domain_keywords = {
            "auth": ["auth", "login", "jwt", "token", "password", "session", "oauth"],
            "payments": ["payment", "billing", "stripe", "invoice", "subscription"],
            "database": ["database", "sql", "postgres", "migration", "query", "index"],
            "api": ["api", "endpoint", "rest", "graphql", "request", "response"],
            "frontend": ["react", "vue", "component", "css", "html", "ui", "ux"],
            "infra": ["deploy", "docker", "kubernetes", "ci", "cd", "aws", "cloud"],
            "testing": ["test", "spec", "mock", "fixture", "coverage"]
        }
        scores = {}
        for domain, keywords in domain_keywords.items():
            score = sum(1 for kw in keywords if kw in content_lower)
            if score > 0:
                scores[domain] = score
        if scores:
            return max(scores, key=scores.get)
        return None

    # ══════════════════════════════════════════════════════════
    # RETRIEVAL
    # ══════════════════════════════════════════════════════════

    def search_by_embedding(
        self,
        query_embedding: Any,
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """Semantic similarity search using embeddings.

        Uses ChromaDB HNSW index (O(log n)) when available,
        falls back to numpy brute-force (O(n)).
        """
        self._ensure_vector_store()

        # ChromaDB path: HNSW search
        if self._use_chromadb and self._chroma_collection is not None:
            count = self._chroma_collection.count()
            if count == 0:
                return []
            emb_list = query_embedding.tolist() if hasattr(query_embedding, 'tolist') else list(query_embedding)
            n_results = min(top_k, count)
            try:
                result = self._chroma_collection.query(
                    query_embeddings=[emb_list],
                    n_results=n_results
                )
                if not result or not result.get("ids") or not result["ids"][0]:
                    return []
                # ChromaDB cosine distance -> similarity: sim = 1 - distance
                pairs = []
                for nid, dist in zip(result["ids"][0], result["distances"][0]):
                    similarity = 1.0 - dist
                    pairs.append((nid, float(similarity)))
                return pairs
            except Exception:
                pass  # fall through to numpy fallback

        # Numpy brute-force fallback
        if not HAS_NUMPY or not self._npz_embeddings:
            return []

        query_emb = np.array(query_embedding)
        results = []

        for node_id, emb in self._npz_embeddings.items():
            dot = np.dot(query_emb, emb)
            norm = np.linalg.norm(query_emb) * np.linalg.norm(emb)
            if norm > 0:
                sim = dot / norm
                results.append((node_id, float(sim)))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def spreading_activation(
        self,
        seed_nodes: List[str],
        max_depth: int = 3,
        decay: float = 0.5
    ) -> Dict[str, float]:
        """Spreading activation from seed nodes (batched SQL — no N+1)."""
        activation = {}
        conn = self._get_conn()

        # Validate seeds exist in batch
        if not seed_nodes:
            return activation
        placeholders = ",".join("?" for _ in seed_nodes)
        existing = conn.execute(
            f"SELECT id FROM nodes WHERE id IN ({placeholders})", seed_nodes
        ).fetchall()
        existing_ids = {r["id"] for r in existing}
        activation = {node: 1.0 for node in seed_nodes if node in existing_ids}
        frontier = set(activation.keys())

        for depth in range(max_depth):
            if not frontier:
                break
            next_frontier = set()
            frontier_list = list(frontier)
            ph = ",".join("?" for _ in frontier_list)

            # Batch: out-edges with neighbor strength (single JOIN query)
            out_rows = conn.execute(
                f"""SELECT e.from_id, e.to_id, e.weight, n.strength AS nb_strength
                    FROM edges e
                    JOIN nodes n ON n.id = e.to_id
                    WHERE e.from_id IN ({ph})""",
                frontier_list
            ).fetchall()

            for row in out_rows:
                node = row["from_id"]
                neighbor = row["to_id"]
                current_act = activation.get(node, 0)
                new_act = current_act * row["weight"] * decay * (row["nb_strength"] or 1.0)

                if neighbor in activation:
                    activation[neighbor] = max(activation[neighbor], new_act)
                else:
                    activation[neighbor] = new_act
                    next_frontier.add(neighbor)

            # Batch: in-edges with neighbor strength (backward, half weight)
            in_rows = conn.execute(
                f"""SELECT e.from_id, e.to_id, e.weight, n.strength AS nb_strength
                    FROM edges e
                    JOIN nodes n ON n.id = e.from_id
                    WHERE e.to_id IN ({ph})""",
                frontier_list
            ).fetchall()

            for row in in_rows:
                node = row["to_id"]
                neighbor = row["from_id"]
                current_act = activation.get(node, 0)
                new_act = current_act * row["weight"] * decay * 0.5 * (row["nb_strength"] or 1.0)

                if neighbor in activation:
                    activation[neighbor] = max(activation[neighbor], new_act)
                else:
                    activation[neighbor] = new_act
                    next_frontier.add(neighbor)

            frontier = next_frontier

        return activation

    def retrieve(
        self,
        query: str = None,
        query_embedding: Any = None,
        labels: List[str] = None,
        author: str = None,
        top_k: int = 20,
        spread_depth: int = 2,
        since: str = None,
        sort_by: str = "score",
        reinforce: bool = True,
        compact: bool = False
    ) -> List[Dict]:
        """Full hybrid search: embedding + spreading activation + FTS5 fusion + filters.

        Args:
            query: Text query for FTS5 keyword search.
            query_embedding: Vector for semantic similarity search.
            labels: Filter by node labels.
            author: Filter by author.
            top_k: Max results to return.
            spread_depth: Spreading activation depth.
            since: ISO date or relative (e.g. "7d", "30d", "2026-02-01").
            sort_by: "score" (default) or "date" (newest first).
            reinforce: If True, reinforce accessed memories (set False for read-only).
            compact: If True, return minimal dicts (id, score, title, type, date only).
                     Use expand_nodes() to get full details for selected IDs.
        """
        results = {}

        # 0. Resolve temporal filter
        since_dt = self._resolve_since(since) if since else None

        # 1. Temporal-only query (no text/embedding — just "show me recent")
        if not query and query_embedding is None:
            conn = self._get_conn()
            sql = "SELECT id FROM nodes"
            params = []
            if since_dt:
                sql += " WHERE created_at >= ?"
                params.append(since_dt)
            rows = conn.execute(sql, params).fetchall()
            for row in rows:
                results[row["id"]] = 1.0

        # 2. Hybrid search (embedding + FTS5 fusion)
        elif query_embedding is not None and HAS_NUMPY:
            # 2a. Semantic: embedding → seeds → spreading activation
            self._ensure_vector_store()
            seeds = self.search_by_embedding(query_embedding, top_k=5)
            seed_nodes = [node_id for node_id, _ in seeds]

            activated = self.spreading_activation(seed_nodes, max_depth=spread_depth)

            for node_id, score in seeds:
                results[node_id] = score * 2

            for node_id, act_score in activated.items():
                if node_id in results:
                    results[node_id] += act_score
                else:
                    results[node_id] = act_score

            # 2b. FTS5 fusion: if text query available, merge keyword results
            if query:
                fts_results = self._text_search(query)
                if fts_results:
                    # Normalize FTS5 scores to 0-1 range
                    max_fts = max(fts_results.values()) if fts_results else 1.0
                    if max_fts > 0:
                        for nid, fts_score in fts_results.items():
                            normalized_fts = fts_score / max_fts
                            if nid in results:
                                # Boost: node found by BOTH semantic + keyword
                                results[nid] += normalized_fts * 0.5
                            else:
                                # New: node found only by keyword (exact match)
                                results[nid] = normalized_fts * 0.5

        # 3. Text-only search (FTS5 or fallback, when no embedding)
        elif query:
            results = self._text_search(query)

        # 4. Apply filters (batch SQL — no per-node queries)
        if results:
            result_ids = list(results.keys())
            conn = self._get_conn()
            ph = ",".join("?" for _ in result_ids)

            if since_dt and (query or query_embedding is not None):
                rows = conn.execute(
                    f"SELECT id FROM nodes WHERE id IN ({ph}) AND created_at >= ?",
                    result_ids + [since_dt]
                ).fetchall()
                valid = {r["id"] for r in rows}
                results = {nid: s for nid, s in results.items() if nid in valid}
                result_ids = list(results.keys())
                ph = ",".join("?" for _ in result_ids)

            if labels and result_ids:
                label_ph = ",".join("?" for _ in labels)
                rows = conn.execute(
                    f"""SELECT DISTINCT node_id FROM node_labels
                        WHERE node_id IN ({ph}) AND label IN ({label_ph})""",
                    result_ids + labels
                ).fetchall()
                valid = {r["node_id"] for r in rows}
                results = {nid: s for nid, s in results.items() if nid in valid}
                result_ids = list(results.keys())
                ph = ",".join("?" for _ in result_ids)

            if author and result_ids:
                rows = conn.execute(
                    f"SELECT id FROM nodes WHERE id IN ({ph}) AND LOWER(author) LIKE ?",
                    result_ids + [f"%{author.lower()}%"]
                ).fetchall()
                valid = {r["id"] for r in rows}
                results = {nid: s for nid, s in results.items() if nid in valid}

        # 5. Sort
        if sort_by == "date":
            sorted_results = self._sort_by_date(results)
        else:
            sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)

        # 6. Reinforce accessed memories (optional — skip for read-only)
        if reinforce:
            for node_id, _ in sorted_results[:10]:
                self._reinforce(node_id)

        # 7. Format output
        output = []
        conn = self._get_conn()
        if compact:
            # Progressive disclosure layer 1: minimal index (~50 tokens/result)
            result_ids = [nid for nid, _ in sorted_results[:top_k]]
            if result_ids:
                ph = ",".join("?" for _ in result_ids)
                rows = conn.execute(
                    f"""SELECT n.id, n.title, n.created_at,
                               (SELECT GROUP_CONCAT(nl.label) FROM node_labels nl
                                WHERE nl.node_id = n.id) AS labels_str
                        FROM nodes n WHERE n.id IN ({ph})""",
                    result_ids
                ).fetchall()
                row_map = {r["id"]: r for r in rows}
                score_map = dict(sorted_results[:top_k])
                for nid in result_ids:
                    r = row_map.get(nid)
                    if r:
                        labels_list = r["labels_str"].split(",") if r["labels_str"] else []
                        date = r["created_at"] or ""
                        if "T" in date:
                            date = date.split("T")[0]
                        output.append({
                            "id": nid,
                            "score": score_map.get(nid, 0),
                            "title": r["title"] or nid,
                            "type": self._primary_type(labels_list),
                            "date": date,
                        })
        else:
            # Full output (layer 2: ~500 tokens/result)
            for node_id, score in sorted_results[:top_k]:
                row = conn.execute("SELECT * FROM nodes WHERE id = ?", (node_id,)).fetchone()
                if row:
                    output.append(self._row_to_legacy_dict(row, score))

        return output

    @staticmethod
    def _resolve_since(since: str) -> str:
        """Convert relative or absolute since to ISO datetime string.

        Accepts: "7d", "30d", "24h" (relative) or "2026-02-01" (absolute ISO date).
        """
        if not since:
            return None
        # Relative: Nd or Nh
        m = re.match(r'^(\d+)([dh])$', since.strip())
        if m:
            amount = int(m.group(1))
            unit = m.group(2)
            if unit == 'd':
                dt = datetime.now() - timedelta(days=amount)
            else:
                dt = datetime.now() - timedelta(hours=amount)
            return dt.isoformat()
        # Absolute ISO date
        return since

    def _sort_by_date(self, results: Dict[str, float]) -> List[tuple]:
        """Sort results by created_at descending (newest first) — single batch query."""
        if not results:
            return []
        conn = self._get_conn()
        result_ids = list(results.keys())
        ph = ",".join("?" for _ in result_ids)
        rows = conn.execute(
            f"SELECT id, created_at FROM nodes WHERE id IN ({ph})",
            result_ids
        ).fetchall()
        date_map = {r["id"]: r["created_at"] or "" for r in rows}
        dated = [(nid, score, date_map.get(nid, "")) for nid, score in results.items()]
        dated.sort(key=lambda x: x[2], reverse=True)
        return [(nid, score) for nid, score, _ in dated]

    def _text_search(self, query: str) -> Dict[str, float]:
        """Full-text search using FTS5 with fallback to LIKE."""
        conn = self._get_conn()
        results = {}

        # Try FTS5 first
        try:
            fts_query = self._sanitize_fts_query(query)
            if fts_query:
                rows = conn.execute(
                    """SELECT n.id, bm25(nodes_fts, 10.0, 1.0, 5.0) AS rank
                       FROM nodes_fts
                       JOIN nodes n ON n.rowid = nodes_fts.rowid
                       WHERE nodes_fts MATCH ?
                       ORDER BY rank
                       LIMIT 50""",
                    (fts_query,)
                ).fetchall()

                for row in rows:
                    results[row["id"]] = -row["rank"]

                if results:
                    return results
        except sqlite3.OperationalError:
            pass

        # Fallback: LIKE search
        query_lower = query.lower()
        rows = conn.execute("SELECT id, title, summary, content FROM nodes").fetchall()
        for row in rows:
            score = 0.0
            if row["title"] and query_lower in row["title"].lower():
                score += 1.0
            if row["summary"] and query_lower in row["summary"].lower():
                score += 0.5
            if row["content"] and query_lower in row["content"].lower():
                score += 0.3
            if score > 0:
                results[row["id"]] = score

        return results

    def _sanitize_fts_query(self, query: str) -> str:
        """Sanitize a user query for FTS5 MATCH syntax.

        Supports:
        - Quoted phrases preserved as-is: "token refresh" → exact phrase
        - Unquoted words joined with AND (all terms required)
        - Prefix search with trailing *: auth* → prefix match
        """
        # Extract quoted phrases first
        phrases = re.findall(r'"([^"]+)"', query)
        remaining = re.sub(r'"[^"]*"', '', query)

        # Extract individual words from remaining text
        words = re.findall(r'[\w*]+', remaining, re.UNICODE)

        parts = []
        for phrase in phrases:
            parts.append(f'"{phrase}"')
        for word in words:
            if word.endswith('*'):
                parts.append(word)  # prefix search: auth*
            else:
                parts.append(f'"{word}"')

        if not parts:
            return ""
        return " AND ".join(parts)

    def _row_to_legacy_dict(self, row: sqlite3.Row, score: float = 0.0) -> Dict:
        """Convert a SQLite row to the legacy dict format expected by consumers."""
        all_props = json.loads(row["properties"])

        # Separate memory fields from regular props
        memory_keys = {"strength", "access_count", "last_accessed", "created_at", "decay_rate"}
        props = {k: v for k, v in all_props.items() if k not in memory_keys}
        memory = {k: all_props.get(k, None) for k in memory_keys}
        # Defaults
        memory.setdefault("strength", 1.0)
        memory.setdefault("access_count", 0)
        memory.setdefault("decay_rate", 0.02)

        labels = self._get_labels(row["id"])

        return {
            "id": row["id"],
            "score": score,
            "labels": labels,
            "props": props,
            "memory": memory
        }

    @staticmethod
    def _primary_type(labels: List[str]) -> str:
        """Determine the primary type from a list of labels."""
        priority = ["ADR", "Decision", "Pattern", "Concept", "Rule",
                     "Episode", "Commit", "BugFix", "Experience", "Person"]
        for t in priority:
            if t in labels:
                return t
        return "Memory"

    def expand_nodes(self, node_ids: List[str]) -> List[Dict]:
        """Progressive disclosure layer 2: full details for selected node IDs.

        Returns full props, content, memory, labels, and semantic connections
        for the given IDs. Use after compact retrieve() to expand only the
        nodes the consumer actually needs (~500 tokens/result).
        """
        conn = self._get_conn()
        output = []
        semantic_types = {"REFERENCES", "INFORMED_BY", "APPLIES", "RELATED_TO",
                          "SAME_SCOPE", "MODIFIES_SAME", "BELONGS_TO_THEME", "CLUSTERED_IN"}

        for node_id in node_ids:
            row = conn.execute("SELECT * FROM nodes WHERE id = ?", (node_id,)).fetchone()
            if not row:
                continue

            node_data = self._row_to_legacy_dict(row)
            props = node_data.get("props", {})
            labels_list = node_data.get("labels", [])

            # Collect semantic connections
            connections = []
            for neighbor in self.get_neighbors(node_id):
                edge = self.get_edge(node_id, neighbor)
                if edge and edge.get("type") in semantic_types:
                    nb = self.get_node(neighbor)
                    nb_title = nb.get("props", {}).get("title", neighbor) if nb else neighbor
                    connections.append({
                        "target": neighbor, "title": nb_title,
                        "type": edge["type"], "weight": round(edge.get("weight", 0.5), 2)
                    })
            for neighbor in self.get_predecessors(node_id):
                edge = self.get_edge(neighbor, node_id)
                if edge and edge.get("type") in semantic_types:
                    nb = self.get_node(neighbor)
                    nb_title = nb.get("props", {}).get("title", neighbor) if nb else neighbor
                    connections.append({
                        "source": neighbor, "title": nb_title,
                        "type": edge["type"], "weight": round(edge.get("weight", 0.5), 2)
                    })

            date = props.get("date", props.get("created_at", ""))
            if date and "T" in str(date):
                date = str(date).split("T")[0]

            output.append({
                "id": node_id,
                "title": props.get("title", node_id),
                "type": self._primary_type(labels_list),
                "labels": labels_list,
                "date": date,
                "content": props.get("content", ""),
                "summary": props.get("summary", ""),
                "author": props.get("author"),
                "memory": node_data.get("memory", {}),
                "connections": connections[:10],
            })

        return output

    def _has_labels(self, node_id: str, labels: List[str]) -> bool:
        """Check if node has any of the given labels."""
        conn = self._get_conn()
        placeholders = ",".join("?" for _ in labels)
        row = conn.execute(
            f"SELECT 1 FROM node_labels WHERE node_id = ? AND label IN ({placeholders})",
            (node_id, *labels)
        ).fetchone()
        return row is not None

    def _has_author(self, node_id: str, author: str) -> bool:
        """Check if node was created by author."""
        conn = self._get_conn()
        row = conn.execute("SELECT author FROM nodes WHERE id = ?", (node_id,)).fetchone()
        if not row or not row["author"]:
            return False
        return author.lower() in row["author"].lower()

    def _reinforce(self, node_id: str):
        """Reinforce an accessed memory — single UPDATE via json_set, no Python parse."""
        conn = self._get_conn()
        conn.execute(
            """UPDATE nodes SET properties = json_set(
                   json_set(
                       json_set(properties,
                           '$.access_count', COALESCE(json_extract(properties, '$.access_count'), 0) + 1),
                       '$.last_accessed', ?),
                   '$.strength', MIN(1.0, COALESCE(json_extract(properties, '$.strength'), 0.5) * 1.05)
               ) WHERE id = ?""",
            (datetime.now().isoformat(), node_id)
        )
        conn.commit()

    # ══════════════════════════════════════════════════════════
    # CONSOLIDATION
    # ══════════════════════════════════════════════════════════

    def consolidate(self) -> Dict:
        """Consolidation process — strengthen co-accessed edges, create CO_ACCESSED edges."""
        stats = {
            "edges_strengthened": 0,
            "edges_created": 0,
            "patterns_detected": 0,
            "summaries_created": 0
        }
        conn = self._get_conn()
        recent_cutoff = (datetime.now() - timedelta(days=7)).isoformat()

        # 1. Strengthen edges between recently accessed nodes
        rows = conn.execute(
            """SELECT e.id, e.from_id, e.to_id, e.weight
               FROM edges e
               JOIN nodes n1 ON e.from_id = n1.id
               JOIN nodes n2 ON e.to_id = n2.id
               WHERE n1.last_accessed > ? AND n2.last_accessed > ?""",
            (recent_cutoff, recent_cutoff)
        ).fetchall()

        for row in rows:
            new_weight = min(1.0, row["weight"] * 1.1)
            conn.execute(
                "UPDATE edges SET weight = ? WHERE id = ?",
                (new_weight, row["id"])
            )
            stats["edges_strengthened"] += 1

        # 2. Create CO_ACCESSED edges between recently co-accessed nodes
        recent_nodes = conn.execute(
            """SELECT n.id FROM nodes n
               LEFT JOIN node_labels nl ON n.id = nl.node_id AND nl.label IN ('Person', 'Domain')
               WHERE n.access_count >= 2 AND n.last_accessed > ?
               AND nl.node_id IS NULL""",
            (recent_cutoff,)
        ).fetchall()
        recent_ids = [r["id"] for r in recent_nodes]

        created = 0
        max_new = 50
        for i, nid_a in enumerate(recent_ids):
            if created >= max_new:
                break
            for nid_b in recent_ids[i + 1:]:
                if created >= max_new:
                    break
                if not self.has_edge(nid_a, nid_b) and not self.has_edge(nid_b, nid_a):
                    self.add_edge(nid_a, nid_b, "CO_ACCESSED", 0.3)
                    created += 1

        stats["edges_created"] = created

        # 3. Identify hubs
        hubs_rows = conn.execute(
            """SELECT n.id,
                  (SELECT COUNT(*) FROM edges WHERE from_id = n.id) +
                  (SELECT COUNT(*) FROM edges WHERE to_id = n.id) AS degree
               FROM nodes n
               ORDER BY degree DESC
               LIMIT 20"""
        ).fetchall()
        stats["hubs"] = [(r["id"], r["degree"]) for r in hubs_rows]

        conn.commit()
        return stats

    # ══════════════════════════════════════════════════════════
    # DECAY
    # ══════════════════════════════════════════════════════════

    def apply_decay(self) -> Dict:
        """Apply Ebbinghaus forgetting curve — batch SQL, minimal Python."""
        now = datetime.now()
        conn = self._get_conn()
        weak = []
        to_archive = []

        rows = conn.execute(
            "SELECT id, strength, last_accessed, decay_rate FROM nodes"
        ).fetchall()

        for row in rows:
            last_accessed = row["last_accessed"]
            if not last_accessed:
                continue
            try:
                last_time = datetime.fromisoformat(
                    last_accessed.replace('Z', '+00:00').split('+')[0])
                days_since = (now - last_time).days
                decay_rate = row["decay_rate"]
                decay_factor = math.exp(-decay_rate * days_since)
                new_strength = row["strength"] * decay_factor

                node_id = row["id"]
                labels = self._get_labels(node_id)

                if new_strength < 0.1:
                    to_archive.append(node_id)
                elif new_strength < 0.3:
                    weak.append(node_id)
                    if "WeakMemory" not in labels:
                        self._add_labels(node_id, ["WeakMemory"])
                else:
                    if "WeakMemory" in labels:
                        conn.execute(
                            "DELETE FROM node_labels WHERE node_id = ? AND label = 'WeakMemory'",
                            (node_id,)
                        )

                # Update strength via json_set
                conn.execute(
                    "UPDATE nodes SET properties = json_set(properties, '$.strength', ?) WHERE id = ?",
                    (new_strength, node_id)
                )
            except Exception:
                pass

        conn.commit()

        return {
            "weak_count": len(weak),
            "archive_count": len(to_archive),
            "weak_nodes": weak[:10],
            "archive_nodes": to_archive[:10]
        }

    # ══════════════════════════════════════════════════════════
    # QUERIES
    # ══════════════════════════════════════════════════════════

    def get_by_label(self, label: str) -> List[str]:
        """Return nodes with a specific label (indexed via node_labels)."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT node_id FROM node_labels WHERE label = ?",
            (label,)
        ).fetchall()
        return [r["node_id"] for r in rows]

    def get_node(self, node_id: str) -> Optional[Dict]:
        """Return node data in legacy dict format (labels, props, memory)."""
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM nodes WHERE id = ?", (node_id,)).fetchone()
        if row is None:
            return None

        all_props = json.loads(row["properties"])
        memory_keys = {"strength", "access_count", "last_accessed", "created_at", "decay_rate"}
        props = {k: v for k, v in all_props.items() if k not in memory_keys}
        memory = {k: all_props.get(k, None) for k in memory_keys}
        memory.setdefault("strength", 1.0)
        memory.setdefault("access_count", 0)
        memory.setdefault("decay_rate", 0.02)

        return {
            "labels": self._get_labels(node_id),
            "props": props,
            "memory": memory
        }

    def get_neighbors(self, node_id: str, edge_type: str = None) -> List[str]:
        """Return successors of a node."""
        conn = self._get_conn()
        if edge_type:
            rows = conn.execute(
                "SELECT to_id FROM edges WHERE from_id = ? AND type = ?",
                (node_id, edge_type)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT DISTINCT to_id FROM edges WHERE from_id = ?", (node_id,)
            ).fetchall()
        return [r["to_id"] for r in rows]

    def get_predecessors(self, node_id: str, edge_type: str = None) -> List[str]:
        """Return predecessors of a node."""
        conn = self._get_conn()
        if edge_type:
            rows = conn.execute(
                "SELECT from_id FROM edges WHERE to_id = ? AND type = ?",
                (node_id, edge_type)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT DISTINCT from_id FROM edges WHERE to_id = ?", (node_id,)
            ).fetchall()
        return [r["from_id"] for r in rows]

    def get_all_nodes(self) -> Dict[str, Dict]:
        """Return all nodes as {id: data} dict."""
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM nodes").fetchall()
        result = {}
        for row in rows:
            all_props = json.loads(row["properties"])
            memory_keys = {"strength", "access_count", "last_accessed", "created_at", "decay_rate"}
            props = {k: v for k, v in all_props.items() if k not in memory_keys}
            memory = {k: all_props.get(k, None) for k in memory_keys}
            memory.setdefault("strength", 1.0)
            memory.setdefault("access_count", 0)
            memory.setdefault("decay_rate", 0.02)

            result[row["id"]] = {
                "labels": self._get_labels(row["id"]),
                "props": props,
                "memory": memory
            }
        return result

    def has_edge(self, source: str, target: str, edge_type: str = None) -> bool:
        """Check if edge exists. Supports optional edge_type filter."""
        conn = self._get_conn()
        if edge_type:
            row = conn.execute(
                "SELECT 1 FROM edges WHERE from_id = ? AND to_id = ? AND type = ?",
                (source, target, edge_type)
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT 1 FROM edges WHERE from_id = ? AND to_id = ?",
                (source, target)
            ).fetchone()
        return row is not None

    def get_edge(self, source: str, target: str, edge_type: str = None) -> Optional[Dict]:
        """Get edge data between two nodes. If edge_type given, returns that specific edge."""
        conn = self._get_conn()
        if edge_type:
            row = conn.execute(
                "SELECT * FROM edges WHERE from_id = ? AND to_id = ? AND type = ?",
                (source, target, edge_type)
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT * FROM edges WHERE from_id = ? AND to_id = ? LIMIT 1",
                (source, target)
            ).fetchone()
        if row is None:
            return None
        return {
            "type": row["type"],
            "weight": row["weight"],
            "props": json.loads(row["properties"]),
            "created_at": row["created_at"]
        }

    def remove_node(self, node_id: str):
        """Remove a node and all its edges."""
        conn = self._get_conn()
        # node_labels and edges are removed by ON DELETE CASCADE
        conn.execute("DELETE FROM nodes WHERE id = ?", (node_id,))
        conn.commit()
        self._remove_embedding(node_id)

    def get_edges_by_type(self, edge_type: str) -> List[Tuple[str, str, Dict]]:
        """Return all edges of a specific type."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT from_id, to_id, type, weight, properties, created_at FROM edges WHERE type = ?",
            (edge_type,)
        ).fetchall()
        result = []
        for row in rows:
            result.append((row["from_id"], row["to_id"], {
                "type": row["type"],
                "weight": row["weight"],
                "props": json.loads(row["properties"]),
                "created_at": row["created_at"]
            }))
        return result

    def get_stats(self) -> Dict:
        """Brain statistics."""
        conn = self._get_conn()
        self._ensure_vector_store()

        node_count = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
        edge_count = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]

        # Count by label (from node_labels table — no JSON parsing)
        label_counts = {}
        label_rows = conn.execute(
            "SELECT label, COUNT(*) as cnt FROM node_labels GROUP BY label"
        ).fetchall()
        for row in label_rows:
            label_counts[row["label"]] = row["cnt"]

        weak_count = label_counts.get("WeakMemory", 0)

        # Count by edge type
        edge_type_counts = {}
        edge_rows = conn.execute("SELECT type, COUNT(*) as cnt FROM edges GROUP BY type").fetchall()
        for row in edge_rows:
            edge_type_counts[row["type"]] = row["cnt"]

        structural_types = {"AUTHORED_BY", "BELONGS_TO"}
        semantic_edges = sum(v for k, v in edge_type_counts.items() if k not in structural_types)

        # Average degree
        if node_count > 0:
            avg_degree = (edge_count * 2) / node_count
        else:
            avg_degree = 0

        return {
            "nodes": node_count,
            "edges": edge_count,
            "semantic_edges": semantic_edges,
            "embeddings": self._embedding_count(),
            "by_label": label_counts,
            "by_edge_type": edge_type_counts,
            "weak_memories": weak_count,
            "avg_degree": avg_degree,
            "vector_backend": "chromadb" if self._use_chromadb else "npz"
        }

    def number_of_nodes(self) -> int:
        """Return number of nodes in the graph."""
        conn = self._get_conn()
        return conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]

    def number_of_edges(self) -> int:
        """Return number of edges in the graph."""
        conn = self._get_conn()
        return conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]

    # ══════════════════════════════════════════════════════════
    # DEV STATE (same as brain.py)
    # ══════════════════════════════════════════════════════════

    def update_dev_state(self, email: str, focus: str = None,
                         last_session: str = None, name: str = None) -> str:
        """Update developer state on Person node."""
        person_id = self._ensure_person_node(email)
        node = self.get_node(person_id)
        if node is None:
            return person_id

        props = node.get("props", {})
        memory = node.get("memory", {})
        now = datetime.now().isoformat()

        if focus is not None:
            props["focus"] = focus
            props["focus_updated_at"] = now
        if last_session is not None:
            props["last_session"] = last_session
            props["last_session_at"] = now
        if name is not None:
            props["name"] = name

        # Derive expertise from AUTHORED_BY edges
        conn = self._get_conn()
        authored_rows = conn.execute(
            "SELECT from_id FROM edges WHERE to_id = ? AND type = 'AUTHORED_BY'",
            (person_id,)
        ).fetchall()

        from collections import Counter
        label_counts = Counter()
        for r in authored_rows:
            n = self.get_node(r["from_id"])
            if n:
                for label in n.get("labels", []):
                    if label.endswith("Domain"):
                        label_counts[label.replace("Domain", "")] += 1
        if label_counts:
            props["expertise"] = [area for area, _ in label_counts.most_common(10) if area]

        props["sessions_count"] = props.get("sessions_count", 0) + (1 if last_session else 0)

        # Rebuild properties: merge props + memory
        properties = {**props, **memory}
        properties["last_accessed"] = now

        conn.execute(
            "UPDATE nodes SET properties = ? WHERE id = ?",
            (json.dumps(properties, default=str), person_id)
        )
        conn.commit()

        return person_id

    def get_dev_state(self, email: str) -> Optional[Dict]:
        """Return current developer state."""
        person_id = f"person-{email}"
        node = self.get_node(person_id)
        if node is None:
            return None
        props = node.get("props", {})
        return {
            "email": props.get("email", email),
            "name": props.get("name", ""),
            "focus": props.get("focus", ""),
            "last_session": props.get("last_session", ""),
            "last_session_at": props.get("last_session_at", ""),
            "expertise": props.get("expertise", []),
            "sessions_count": props.get("sessions_count", 0),
            "aliases": props.get("aliases", []),
        }

    # ══════════════════════════════════════════════════════════
    # EXPORT (for git diffs and rollback)
    # ══════════════════════════════════════════════════════════

    def export_json(self, output_path: Path = None) -> Path:
        """Export brain.db -> graph.json for git diffs and rollback."""
        if output_path is None:
            output_path = self.base_path / "graph.json"

        conn = self._get_conn()

        # Export nodes
        nodes_data = {}
        rows = conn.execute("SELECT * FROM nodes").fetchall()
        for row in rows:
            all_props = json.loads(row["properties"])
            memory_keys = {"strength", "access_count", "last_accessed", "created_at", "decay_rate"}
            node_props = {k: v for k, v in all_props.items() if k not in memory_keys}
            memory = {k: all_props.get(k, None) for k in memory_keys}
            memory.setdefault("strength", 1.0)
            memory.setdefault("access_count", 0)
            memory.setdefault("decay_rate", 0.02)

            nodes_data[row["id"]] = {
                "labels": self._get_labels(row["id"]),
                "props": node_props,
                "memory": memory
            }

        # Export edges
        edges_data = []
        edge_rows = conn.execute("SELECT * FROM edges").fetchall()
        for row in edge_rows:
            edges_data.append({
                "src": row["from_id"],
                "tgt": row["to_id"],
                "type": row["type"],
                "weight": row["weight"],
                "props": json.loads(row["properties"]),
                "created_at": row["created_at"]
            })

        data = {
            "version": "1.0",
            "meta": {
                "saved_at": datetime.now().isoformat(),
                "node_count": len(nodes_data),
                "edge_count": len(edges_data),
                "backend": "sqlite_v2"
            },
            "nodes": nodes_data,
            "edges": edges_data
        }

        output_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False, default=str),
            encoding='utf-8'
        )
        print(f"Exported: {output_path}")
        return output_path

    # ══════════════════════════════════════════════════════════
    # GRAPH COMPATIBILITY SHIM
    # ══════════════════════════════════════════════════════════

    @property
    def graph(self):
        """Return self as a graph-like interface for backward compat."""
        return self

    def successors(self, node_id: str) -> List[str]:
        """Graph compat: return successor node IDs."""
        return self.get_neighbors(node_id)

    def predecessors(self, node_id: str) -> List[str]:
        """Graph compat: return predecessor node IDs."""
        return self.get_predecessors(node_id)

    def degree(self) -> List[Tuple[str, int]]:
        """Graph compat: return (node_id, degree) for all nodes."""
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT n.id,
                  (SELECT COUNT(*) FROM edges WHERE from_id = n.id) +
                  (SELECT COUNT(*) FROM edges WHERE to_id = n.id) AS deg
               FROM nodes n"""
        ).fetchall()
        return [(r["id"], r["deg"]) for r in rows]

    @property
    def nodes(self):
        """Graph compat: return a NodeView-like object."""
        return _NodeView(self)

    @property
    def edges(self):
        """Graph compat: return an EdgeView-like object."""
        return _EdgeView(self)


class _NodeView:
    """Minimal shim for brain.graph.nodes access patterns used by consumers."""

    def __init__(self, brain: BrainSQLite):
        self._brain = brain

    def __contains__(self, node_id: str) -> bool:
        return self._brain._node_exists(node_id)

    def __iter__(self):
        conn = self._brain._get_conn()
        rows = conn.execute("SELECT id FROM nodes").fetchall()
        return iter(r["id"] for r in rows)

    def __len__(self):
        return self._brain.number_of_nodes()

    def __getitem__(self, node_id: str) -> Dict:
        node = self._brain.get_node(node_id)
        if node is None:
            raise KeyError(node_id)
        return node

    def get(self, node_id: str, default=None):
        node = self._brain.get_node(node_id)
        return node if node is not None else default


class _EdgeView:
    """Minimal shim for brain.graph.edges access patterns used by consumers."""

    def __init__(self, brain: BrainSQLite):
        self._brain = brain

    def __iter__(self):
        conn = self._brain._get_conn()
        rows = conn.execute("SELECT from_id, to_id FROM edges").fetchall()
        return iter((r["from_id"], r["to_id"]) for r in rows)

    def __len__(self):
        return self._brain.number_of_edges()

    def __getitem__(self, key):
        if isinstance(key, tuple) and len(key) == 2:
            src, tgt = key
            edge = self._brain.get_edge(src, tgt)
            if edge is None:
                raise KeyError(key)
            return edge
        raise KeyError(key)

    def __call__(self, *args, data=False, **kwargs):
        """Support brain.graph.edges(data=True) iteration."""
        conn = self._brain._get_conn()
        rows = conn.execute(
            "SELECT from_id, to_id, type, weight, properties, created_at FROM edges"
        ).fetchall()
        if data:
            return [
                (r["from_id"], r["to_id"], {
                    "type": r["type"], "weight": r["weight"],
                    "props": json.loads(r["properties"]), "created_at": r["created_at"]
                })
                for r in rows
            ]
        return [(r["from_id"], r["to_id"]) for r in rows]


# ══════════════════════════════════════════════════════════
# CLI (same as brain.py)
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    # Reuse get_current_developer from brain.py
    sys.path.insert(0, str(Path(__file__).parent))
    from brain import get_current_developer

    brain = BrainSQLite()

    if len(sys.argv) < 2:
        print("Usage: brain_sqlite.py <command> [args]")
        print("Commands: load, save, stats, search, consolidate, decay, export")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "load":
        brain.load()
        print(json.dumps(brain.get_stats(), indent=2))

    elif cmd == "stats":
        brain.load()
        print(json.dumps(brain.get_stats(), indent=2))

    elif cmd == "search":
        if len(sys.argv) < 3:
            print("Usage: brain_sqlite.py search <query>")
            sys.exit(1)
        brain.load()
        query = " ".join(sys.argv[2:])
        results = brain.retrieve(query=query, top_k=10)
        for r in results:
            print(f"{r['score']:.2f} | {r.get('props', {}).get('title', 'N/A')} | {r['id']}")

    elif cmd == "consolidate":
        brain.load()
        stats = brain.consolidate()
        print(json.dumps(stats, indent=2))

    elif cmd == "decay":
        brain.load()
        stats = brain.apply_decay()
        print(json.dumps(stats, indent=2))

    elif cmd == "export":
        brain.load()
        brain.export_json()

    elif cmd == "add":
        if len(sys.argv) < 4:
            print("Usage: brain_sqlite.py add <title> <content>")
            sys.exit(1)
        brain.load()
        dev = get_current_developer()
        title = sys.argv[2]
        content = " ".join(sys.argv[3:])
        node_id = brain.add_memory(
            title=title, content=content, labels=["Episode"], author=dev["author"]
        )
        print(f"Created: {node_id}")

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
