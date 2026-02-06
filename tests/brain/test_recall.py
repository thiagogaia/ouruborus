"""Tests for recall.py functions."""

from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import pytest


class TestFormatHumanReadable:
    """recall.format_human_readable()"""

    def test_formats_error(self):
        from recall import format_human_readable
        data = {"error": "Something broke", "fallback": "Try this"}
        result = format_human_readable(data)
        assert "Something broke" in result
        assert "Try this" in result

    def test_formats_empty_results(self):
        from recall import format_human_readable
        data = {"query": "test", "total": 0, "results": []}
        result = format_human_readable(data)
        assert "Nenhuma" in result
        assert "test" in result

    def test_formats_results_with_connections(self):
        from recall import format_human_readable
        data = {
            "query": "auth",
            "total": 1,
            "results": [
                {
                    "id": "n1",
                    "title": "Auth Pattern",
                    "type": "Pattern",
                    "labels": ["Pattern"],
                    "summary": "Authentication pattern",
                    "content": "Full content here",
                    "score": 0.8,
                    "author": "dev@test.com",
                    "connections": [
                        {"target": "n2", "title": "Related ADR", "type": "REFERENCES", "weight": 0.6}
                    ],
                }
            ],
        }
        result = format_human_readable(data)
        assert "Auth Pattern" in result
        assert "dev@test.com" in result
        assert "REFERENCES" in result
        assert "Related ADR" in result

    def test_score_bar_rendering(self):
        from recall import format_human_readable
        data = {
            "query": "test",
            "total": 1,
            "results": [
                {
                    "id": "n1",
                    "title": "Test",
                    "type": "Concept",
                    "labels": ["Concept"],
                    "summary": "A test",
                    "content": None,
                    "score": 1.0,
                    "author": None,
                    "connections": [],
                }
            ],
        }
        result = format_human_readable(data)
        assert "█" in result


class TestSearchBrain:
    """recall.search_brain() — needs mocked Brain."""

    def test_returns_error_when_deps_missing(self):
        from recall import search_brain

        with patch("recall.HAS_DEPS", False):
            # IMPORT_ERROR may not exist when HAS_DEPS is True, so create it
            with patch("recall.IMPORT_ERROR", "test error", create=True):
                result = search_brain("test query")
                assert "error" in result

    def test_text_search_returns_results(self, seeded_brain):
        """Integration test: search_brain with a real seeded brain."""
        from recall import search_brain

        # Mock Brain() and brain.load() to return our seeded_brain
        mock_brain_cls = MagicMock(return_value=seeded_brain)
        seeded_brain.load = MagicMock(return_value=True)
        seeded_brain.save = MagicMock()

        with patch("recall.HAS_DEPS", True), \
             patch("recall.Brain", mock_brain_cls), \
             patch("recall.HAS_EMBEDDINGS", False):
            result = search_brain("FallbackGraph", top_k=5)
            assert result["total"] > 0
            assert result["results"][0]["title"]

    def test_search_with_since_passes_to_retrieve(self, seeded_brain):
        """search_brain passes since and sort_by to brain.retrieve()."""
        from recall import search_brain

        mock_brain_cls = MagicMock(return_value=seeded_brain)
        seeded_brain.load = MagicMock(return_value=True)
        seeded_brain.save = MagicMock()
        seeded_brain.retrieve = MagicMock(return_value=[])

        with patch("recall.HAS_DEPS", True), \
             patch("recall.Brain", mock_brain_cls), \
             patch("recall.HAS_EMBEDDINGS", False):
            result = search_brain("test", since="7d", sort_by="date")
            # Verify retrieve was called with since and sort_by
            call_kwargs = seeded_brain.retrieve.call_args[1]
            assert call_kwargs["since"] == "7d"
            assert call_kwargs["sort_by"] == "date"

    def test_temporal_only_query(self, seeded_brain):
        """search_brain without query but with since returns temporal results."""
        from recall import search_brain

        mock_brain_cls = MagicMock(return_value=seeded_brain)
        seeded_brain.load = MagicMock(return_value=True)
        seeded_brain.save = MagicMock()

        with patch("recall.HAS_DEPS", True), \
             patch("recall.Brain", mock_brain_cls), \
             patch("recall.HAS_EMBEDDINGS", False):
            # No query, just since — should not error
            result = search_brain(query=None, since="7d", sort_by="date")
            assert "error" not in result
            assert result["query"] == "(temporal)"

    def test_results_include_date_field(self, seeded_brain):
        """Results include a 'date' field for temporal context."""
        from recall import search_brain

        mock_brain_cls = MagicMock(return_value=seeded_brain)
        seeded_brain.load = MagicMock(return_value=True)
        seeded_brain.save = MagicMock()

        with patch("recall.HAS_DEPS", True), \
             patch("recall.Brain", mock_brain_cls), \
             patch("recall.HAS_EMBEDDINGS", False):
            result = search_brain("FallbackGraph", top_k=5)
            if result["total"] > 0:
                assert "date" in result["results"][0]

    def test_filters_include_since_and_sort(self):
        """Result dict includes since and sort_by in filters."""
        from recall import search_brain

        mock_brain = MagicMock()
        mock_brain.load.return_value = True
        mock_brain.retrieve.return_value = []
        mock_brain_cls = MagicMock(return_value=mock_brain)

        with patch("recall.HAS_DEPS", True), \
             patch("recall.Brain", mock_brain_cls), \
             patch("recall.HAS_EMBEDDINGS", False):
            result = search_brain("test", since="30d", sort_by="date")
            assert result["filters"]["since"] == "30d"
            assert result["filters"]["sort_by"] == "date"


class TestFormatHumanReadableDate:
    """Test date display in human readable format."""

    def test_shows_date_in_output(self):
        from recall import format_human_readable
        data = {
            "query": "test",
            "filters": {"since": "7d", "sort_by": "date"},
            "total": 1,
            "results": [
                {
                    "id": "n1",
                    "title": "Test Commit",
                    "type": "Commit",
                    "labels": ["Commit"],
                    "date": "2026-02-06",
                    "summary": "A commit",
                    "content": None,
                    "score": 1.0,
                    "author": None,
                    "connections": [],
                }
            ],
        }
        result = format_human_readable(data)
        assert "2026-02-06" in result
        assert "desde: 7d" in result
        assert "ordenado por data" in result

    def test_no_date_filter_labels(self):
        from recall import format_human_readable
        data = {
            "query": "test",
            "filters": {},
            "total": 1,
            "results": [
                {
                    "id": "n1",
                    "title": "Test",
                    "type": "Concept",
                    "labels": ["Concept"],
                    "date": "",
                    "summary": "test",
                    "content": None,
                    "score": 1.0,
                    "author": None,
                    "connections": [],
                }
            ],
        }
        result = format_human_readable(data)
        assert "desde:" not in result
        assert "ordenado por data" not in result


class TestResolveSince:
    """BrainSQLite._resolve_since() static method."""

    def test_relative_days(self):
        from brain_sqlite import BrainSQLite
        result = BrainSQLite._resolve_since("7d")
        expected = (datetime.now() - timedelta(days=7)).isoformat()
        # Compare date part only (ignore sub-second differences)
        assert result[:10] == expected[:10]

    def test_relative_hours(self):
        from brain_sqlite import BrainSQLite
        result = BrainSQLite._resolve_since("24h")
        expected = (datetime.now() - timedelta(hours=24)).isoformat()
        assert result[:13] == expected[:13]

    def test_absolute_date(self):
        from brain_sqlite import BrainSQLite
        result = BrainSQLite._resolve_since("2026-02-01")
        assert result == "2026-02-01"

    def test_none_returns_none(self):
        from brain_sqlite import BrainSQLite
        assert BrainSQLite._resolve_since(None) is None

    def test_empty_returns_none(self):
        from brain_sqlite import BrainSQLite
        assert BrainSQLite._resolve_since("") is None
