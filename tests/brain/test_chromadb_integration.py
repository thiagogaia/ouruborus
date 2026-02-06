"""Integration tests for ChromaDB vector storage in BrainSQLite.

Uses MockChromaClient/MockChromaCollection from conftest.py to validate
the full store/retrieve/search/fallback cycle without a real ChromaDB install.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest


class TestVectorStoreInit:
    """_ensure_vector_store() initialization and fallback."""

    def test_chromadb_initializes(self, tmp_path):
        """When chromadb module is available, brain uses ChromaDB."""
        from brain_sqlite import BrainSQLite
        brain = BrainSQLite(base_path=tmp_path)
        brain.load()
        brain._ensure_vector_store()

        assert brain._use_chromadb is True
        assert brain._chroma_collection is not None
        assert brain._chroma_client is not None

    def test_fallback_to_npz_when_chromadb_fails(self, tmp_path):
        """When ChromaDB init fails, falls back to npz."""
        import chromadb
        original = chromadb.PersistentClient

        chromadb.PersistentClient = MagicMock(side_effect=Exception("fail"))
        try:
            from brain_sqlite import BrainSQLite
            brain = BrainSQLite(base_path=tmp_path)
            brain.load()
            brain._ensure_vector_store()

            assert brain._use_chromadb is False
            assert brain._chroma_collection is None
        finally:
            chromadb.PersistentClient = original

    def test_idempotent_init(self, tmp_path):
        """Calling _ensure_vector_store() multiple times is a no-op."""
        from brain_sqlite import BrainSQLite
        brain = BrainSQLite(base_path=tmp_path)
        brain.load()
        brain._ensure_vector_store()
        coll1 = brain._chroma_collection
        brain._ensure_vector_store()
        coll2 = brain._chroma_collection
        assert coll1 is coll2


class TestStoreAndRetrieve:
    """_store_embedding(), get_embedding_vectors(), _remove_embedding()."""

    def test_store_and_retrieve(self, tmp_path):
        """Store an embedding and retrieve it."""
        from brain_sqlite import BrainSQLite
        brain = BrainSQLite(base_path=tmp_path)
        brain.load()

        brain._store_embedding("node1", [0.1, 0.2, 0.3])
        vectors = brain.get_embedding_vectors(["node1"])
        assert "node1" in vectors
        assert list(vectors["node1"]) == [0.1, 0.2, 0.3]

    def test_store_multiple(self, tmp_path):
        """Store multiple embeddings."""
        from brain_sqlite import BrainSQLite
        brain = BrainSQLite(base_path=tmp_path)
        brain.load()

        brain._store_embedding("a", [1.0, 0.0, 0.0])
        brain._store_embedding("b", [0.0, 1.0, 0.0])
        brain._store_embedding("c", [0.0, 0.0, 1.0])

        assert brain._embedding_count() == 3
        vecs = brain.get_embedding_vectors(["a", "b", "c"])
        assert len(vecs) == 3

    def test_upsert_overwrites(self, tmp_path):
        """Upsert should overwrite existing embedding."""
        from brain_sqlite import BrainSQLite
        brain = BrainSQLite(base_path=tmp_path)
        brain.load()

        brain._store_embedding("n1", [1.0, 0.0, 0.0])
        brain._store_embedding("n1", [0.0, 1.0, 0.0])

        assert brain._embedding_count() == 1
        vecs = brain.get_embedding_vectors(["n1"])
        assert list(vecs["n1"]) == [0.0, 1.0, 0.0]

    def test_remove_embedding(self, tmp_path):
        """_remove_embedding() should delete from store."""
        from brain_sqlite import BrainSQLite
        brain = BrainSQLite(base_path=tmp_path)
        brain.load()

        brain._store_embedding("n1", [0.1, 0.2, 0.3])
        assert brain._embedding_count() == 1

        brain._remove_embedding("n1")
        assert brain._embedding_count() == 0

    def test_remove_nonexistent_is_safe(self, tmp_path):
        """Removing a nonexistent embedding should not raise."""
        from brain_sqlite import BrainSQLite
        brain = BrainSQLite(base_path=tmp_path)
        brain.load()
        brain._ensure_vector_store()

        brain._remove_embedding("does_not_exist")  # should not raise

    def test_get_nonexistent_returns_empty(self, tmp_path):
        """Getting embeddings for missing IDs returns empty dict."""
        from brain_sqlite import BrainSQLite
        brain = BrainSQLite(base_path=tmp_path)
        brain.load()
        brain._ensure_vector_store()

        vecs = brain.get_embedding_vectors(["missing1", "missing2"])
        assert vecs == {}

    def test_get_empty_list(self, tmp_path):
        """Getting embeddings for empty list returns empty dict."""
        from brain_sqlite import BrainSQLite
        brain = BrainSQLite(base_path=tmp_path)
        brain.load()
        brain._ensure_vector_store()

        vecs = brain.get_embedding_vectors([])
        assert vecs == {}


class TestSearchByEmbedding:
    """search_by_embedding() with ChromaDB backend."""

    def test_search_returns_sorted_results(self, tmp_path):
        """Search should return results sorted by similarity."""
        from brain_sqlite import BrainSQLite
        brain = BrainSQLite(base_path=tmp_path)
        brain.load()

        # Store embeddings: n1 is closest to query, n3 is furthest
        brain._store_embedding("n1", [1.0, 0.0, 0.0])
        brain._store_embedding("n2", [0.5, 0.5, 0.0])
        brain._store_embedding("n3", [0.0, 0.0, 1.0])

        results = brain.search_by_embedding([1.0, 0.0, 0.0], top_k=3)
        assert len(results) == 3
        # n1 should be the most similar (cosine similarity = 1.0)
        assert results[0][0] == "n1"
        assert results[0][1] > results[1][1]

    def test_search_empty_store(self, tmp_path):
        """Search on empty store returns empty list."""
        from brain_sqlite import BrainSQLite
        brain = BrainSQLite(base_path=tmp_path)
        brain.load()
        brain._ensure_vector_store()

        results = brain.search_by_embedding([1.0, 0.0, 0.0], top_k=5)
        assert results == []

    def test_search_top_k_limit(self, tmp_path):
        """top_k should limit results."""
        from brain_sqlite import BrainSQLite
        brain = BrainSQLite(base_path=tmp_path)
        brain.load()

        for i in range(10):
            brain._store_embedding(f"n{i}", [float(i % 3), float(i % 2), 0.1])

        results = brain.search_by_embedding([1.0, 0.0, 0.0], top_k=3)
        assert len(results) <= 3


class TestAddMemoryWithEmbedding:
    """add_memory() and _upsert_node() embedding integration."""

    def test_add_memory_stores_embedding(self, tmp_path):
        """add_memory with embedding param should store in ChromaDB."""
        from brain_sqlite import BrainSQLite
        brain = BrainSQLite(base_path=tmp_path)
        brain.load()

        node_id = brain.add_memory(
            title="Test Memory",
            content="Some content about testing",
            labels=["Concept"],
            author="test@dev.com",
            embedding=[0.1, 0.2, 0.3]
        )

        assert brain._embedding_count() >= 1
        vecs = brain.get_embedding_vectors([node_id])
        assert node_id in vecs

    def test_remove_node_removes_embedding(self, tmp_path):
        """remove_node() should also remove from ChromaDB."""
        from brain_sqlite import BrainSQLite
        brain = BrainSQLite(base_path=tmp_path)
        brain.load()

        node_id = brain.add_memory(
            title="To Be Removed",
            content="Will be deleted",
            labels=["Concept"],
            author="test@dev.com",
            embedding=[0.1, 0.2, 0.3]
        )

        assert brain._embedding_count() >= 1
        brain.remove_node(node_id)

        vecs = brain.get_embedding_vectors([node_id])
        assert node_id not in vecs


class TestGetStats:
    """get_stats() with ChromaDB backend."""

    def test_stats_include_vector_backend(self, tmp_path):
        """Stats should report which vector backend is active."""
        from brain_sqlite import BrainSQLite
        brain = BrainSQLite(base_path=tmp_path)
        brain.load()
        brain._ensure_vector_store()

        stats = brain.get_stats()
        assert "vector_backend" in stats
        assert stats["vector_backend"] == "chromadb"

    def test_stats_embedding_count(self, tmp_path):
        """Stats embedding count should reflect ChromaDB store."""
        from brain_sqlite import BrainSQLite
        brain = BrainSQLite(base_path=tmp_path)
        brain.load()

        brain._store_embedding("x1", [0.1, 0.2, 0.3])
        brain._store_embedding("x2", [0.4, 0.5, 0.6])

        stats = brain.get_stats()
        assert stats["embeddings"] == 2


class TestBackwardCompat:
    """Backward compatibility: brain.embeddings property."""

    def test_embeddings_property_returns_dict(self, tmp_path):
        """brain.embeddings should still be a dict (npz fallback)."""
        from brain_sqlite import BrainSQLite
        brain = BrainSQLite(base_path=tmp_path)
        brain.load()

        assert isinstance(brain.embeddings, dict)

    def test_embeddings_setter(self, tmp_path):
        """brain.embeddings = {...} should still work."""
        from brain_sqlite import BrainSQLite
        brain = BrainSQLite(base_path=tmp_path)
        brain.load()

        brain.embeddings = {"n1": [0.1, 0.2]}
        assert brain.embeddings == {"n1": [0.1, 0.2]}
        assert brain._npz_embeddings == {"n1": [0.1, 0.2]}
