"""Tests for embeddings.py with fully mocked dependencies."""

import json
from unittest.mock import patch, MagicMock
from pathlib import Path

import pytest


class TestBuildEmbeddings:
    """embeddings.build_embeddings() — uses ChromaDB mock from conftest."""

    def test_build_stores_in_chromadb(self, tmp_path):
        """build_embeddings() should upsert into ChromaDB when available."""
        from brain_sqlite import BrainSQLite
        brain = BrainSQLite(base_path=tmp_path)
        brain.load()
        brain.add_node_raw(
            "n1",
            labels=["Concept"],
            props={"title": "Test Node", "content": "Some content", "summary": "short"},
            memory={"strength": 1.0},
        )

        fake_vector = [0.1, 0.2, 0.3]

        # Patch _get_brain to return a brain with ChromaDB already initialized
        brain._ensure_vector_store()
        assert brain._use_chromadb

        with patch("embeddings.get_embedding", return_value=fake_vector), \
             patch("embeddings._get_brain", return_value=brain):
            from embeddings import build_embeddings
            build_embeddings(brain_path=tmp_path)

        # Verify ChromaDB has the embedding (same brain instance)
        assert brain._chroma_collection.count() >= 1

    def test_build_fallback_npz(self, tmp_path):
        """If ChromaDB init fails, build_embeddings() falls back to npz."""
        import sys
        np_mock = sys.modules["numpy"]

        from brain_sqlite import BrainSQLite
        brain = BrainSQLite(base_path=tmp_path)
        brain.load()
        brain.add_node_raw(
            "n1",
            labels=["Concept"],
            props={"title": "Test Node", "content": "Some content", "summary": "short"},
            memory={"strength": 1.0},
        )

        fake_vector = [0.1, 0.2, 0.3]

        # Force ChromaDB to fail so we fall back to npz
        import chromadb
        original_client = chromadb.PersistentClient
        chromadb.PersistentClient = MagicMock(side_effect=Exception("no chromadb"))

        try:
            with patch("embeddings.get_embedding", return_value=fake_vector), \
                 patch("embeddings._get_brain", return_value=brain):
                with patch.object(np_mock, "savez_compressed") as mock_save:
                    from embeddings import build_embeddings
                    build_embeddings(brain_path=tmp_path)
                    mock_save.assert_called_once()
        finally:
            chromadb.PersistentClient = original_client


class TestSearchEmbeddings:
    """embeddings.search_embeddings() — uses ChromaDB mock from conftest."""

    def test_search_returns_results_chromadb(self, tmp_path):
        """search_embeddings() should use ChromaDB when available."""
        from brain_sqlite import BrainSQLite
        brain = BrainSQLite(base_path=tmp_path)
        brain.load()
        brain.add_node_raw(
            "n1",
            labels=["Concept"],
            props={"title": "Auth System", "summary": "Authentication"},
            memory={"strength": 1.0},
        )

        # Pre-populate ChromaDB with an embedding
        brain._ensure_vector_store()
        brain._store_embedding("n1", [0.1, 0.2, 0.3])

        with patch("embeddings.get_embedding", return_value=[0.1, 0.2, 0.3]), \
             patch("embeddings._get_brain", return_value=brain):
            from embeddings import search_embeddings
            results = search_embeddings("auth", brain_path=tmp_path, top_k=5)
            assert len(results) >= 1
            assert results[0]["id"] == "n1"


class TestMigrateEmbeddings:
    """embeddings.migrate_embeddings() — npz -> ChromaDB migration."""

    def test_migrate_from_npz(self, tmp_path):
        """migrate_embeddings() should read npz and upsert into ChromaDB."""
        import sys
        np_mock = sys.modules["numpy"]

        # Create a fake npz file
        fake_npz = MagicMock()
        fake_npz.files = ["n1", "n2"]
        fake_npz.__getitem__ = lambda self, k: [0.1, 0.2, 0.3]
        (tmp_path / "embeddings.npz").write_text("fake")

        # Create brain.db
        from brain_sqlite import BrainSQLite
        brain = BrainSQLite(base_path=tmp_path)
        brain.load()
        brain._ensure_vector_store()

        with patch.object(np_mock, "load", return_value=fake_npz), \
             patch("embeddings._get_brain", return_value=brain):
            from embeddings import migrate_embeddings
            migrate_embeddings(brain_path=tmp_path)

        # Verify ChromaDB received the embeddings (same brain instance)
        assert brain._chroma_collection.count() == 2
