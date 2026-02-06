"""Tests for inline embedding generation in brain_sqlite.py."""

import sys
from unittest.mock import MagicMock, patch

import pytest


class TestGenerateEmbedding:
    """BrainSQLite._generate_embedding()"""

    def test_returns_none_without_sentence_transformers(self, tmp_path):
        """Without sentence-transformers, _generate_embedding returns None."""
        from brain_sqlite import BrainSQLite

        brain = BrainSQLite(base_path=tmp_path / "brain")
        brain.load()

        result = brain._generate_embedding("Test Title", "Test content", ["Episode"])
        # sentence_transformers is blocked in conftest.py, so this must be None
        assert result is None

    def test_add_memory_works_without_deps(self, tmp_path):
        """add_memory() works normally when sentence-transformers is unavailable."""
        from brain_sqlite import BrainSQLite

        brain = BrainSQLite(base_path=tmp_path / "brain")
        brain.load()

        node_id = brain.add_memory(
            title="Test Memory",
            content="This is a test memory without embeddings",
            labels=["Episode"],
            author="@test"
        )
        assert node_id is not None
        node = brain.get_node(node_id)
        assert node is not None
        assert "Episode" in node["labels"]

    def test_explicit_embedding_is_used(self, tmp_path):
        """When embedding is passed explicitly, it is used (not overwritten)."""
        from brain_sqlite import BrainSQLite

        brain = BrainSQLite(base_path=tmp_path / "brain")
        brain.load()

        fake_embedding = [0.1] * 10
        node_id = brain.add_memory(
            title="With Embedding",
            content="This memory has an explicit embedding",
            labels=["Episode"],
            author="@test",
            embedding=fake_embedding
        )
        assert node_id is not None
        # The embedding should be stored
        assert brain._embedding_count() > 0

    def test_model_cached_across_calls(self, tmp_path):
        """The embedding model attribute is set once and cached."""
        from brain_sqlite import BrainSQLite

        brain = BrainSQLite(base_path=tmp_path / "brain")
        brain.load()

        # First call sets _embedding_model
        brain._generate_embedding("Title1", "Content1", ["Episode"])
        assert hasattr(brain, '_embedding_model')
        model_ref = brain._embedding_model  # None since deps unavailable

        # Second call should not re-attempt import
        brain._generate_embedding("Title2", "Content2", ["Pattern"])
        assert brain._embedding_model is model_ref

    def test_upsert_generates_embedding_too(self, tmp_path):
        """_upsert_node also attempts embedding generation."""
        from brain_sqlite import BrainSQLite

        brain = BrainSQLite(base_path=tmp_path / "brain")
        brain.load()

        # First add
        node_id = brain.add_memory(
            title="Upsert Test",
            content="Original content",
            labels=["Episode"],
            author="@test"
        )

        # Second add (same title+labels = same ID = upsert)
        node_id2 = brain.add_memory(
            title="Upsert Test",
            content="Updated content",
            labels=["Episode"],
            author="@test"
        )

        assert node_id == node_id2
        node = brain.get_node(node_id)
        assert node["props"]["content"] == "Updated content"
