"""
Tests for graph_builder.py
"""

import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest
import networkx as nx

from graph_builder import GraphBuilder


class TestIsChronologicallyValid:
    """Tests for _is_chronologically_valid method."""

    @pytest.fixture
    def builder(self) -> GraphBuilder:
        """Create a GraphBuilder with mocked dependencies."""
        with patch('graph_builder.WikipediaClient') as mock_wiki, \
             patch('graph_builder.LLMExtractor') as mock_llm:

            mock_wiki_instance = MagicMock()
            mock_wiki_instance.extract_years.return_value = (None, None)
            mock_wiki.return_value = mock_wiki_instance

            mock_llm.return_value = MagicMock()

            builder = GraphBuilder()
            builder.wiki_client = mock_wiki_instance
            return builder

    def test_valid_inspired_by_relation(self, builder: GraphBuilder) -> None:
        """Test that mentor being older is valid for inspired_by."""
        builder.graph.add_node("Student", birth_year=1900)
        builder.graph.add_node("Mentor", birth_year=1850)

        result = builder._is_chronologically_valid("Student", "Mentor", "inspired_by")

        assert result is True

    def test_invalid_inspired_by_younger_mentor(self, builder: GraphBuilder) -> None:
        """Test that younger mentor is invalid for inspired_by."""
        builder.graph.add_node("Student", birth_year=1850)
        builder.graph.add_node("Mentor", birth_year=1900)

        result = builder._is_chronologically_valid("Student", "Mentor", "inspired_by")

        assert result is False

    def test_valid_inspired_relation(self, builder: GraphBuilder) -> None:
        """Test that student being younger is valid for inspired."""
        builder.graph.add_node("Mentor", birth_year=1850)
        builder.graph.add_node("Student", birth_year=1900)

        result = builder._is_chronologically_valid("Mentor", "Student", "inspired")

        assert result is True

    def test_invalid_inspired_older_student(self, builder: GraphBuilder) -> None:
        """Test that older student is invalid for inspired."""
        builder.graph.add_node("Mentor", birth_year=1900)
        builder.graph.add_node("Student", birth_year=1850)

        result = builder._is_chronologically_valid("Mentor", "Student", "inspired")

        assert result is False

    def test_contemporaries_within_margin(self, builder: GraphBuilder) -> None:
        """Test that contemporaries within 5 year margin are valid."""
        builder.graph.add_node("Person1", birth_year=1900)
        builder.graph.add_node("Person2", birth_year=1903)

        result1 = builder._is_chronologically_valid("Person1", "Person2", "inspired_by")
        result2 = builder._is_chronologically_valid("Person1", "Person2", "inspired")

        assert result1 is True
        assert result2 is True

    def test_missing_dates_fail_open(self, builder: GraphBuilder) -> None:
        """Test that missing dates result in fail open (accept)."""
        builder.graph.add_node("Person1", birth_year=1900)
        builder.graph.add_node("Person2")  # No birth_year

        builder.wiki_client.extract_years.return_value = (None, None)

        result = builder._is_chronologically_valid("Person1", "Person2", "inspired_by")

        assert result is True


class TestIsValidName:
    """Tests for _is_valid_name method."""

    @pytest.fixture
    def builder(self) -> GraphBuilder:
        """Create a GraphBuilder with mocked dependencies."""
        with patch('graph_builder.WikipediaClient') as mock_wiki, \
             patch('graph_builder.LLMExtractor') as mock_llm:

            mock_wiki_instance = MagicMock()
            mock_wiki_instance.is_scientist.return_value = True
            mock_wiki.return_value = mock_wiki_instance

            mock_llm.return_value = MagicMock()

            builder = GraphBuilder()
            builder.wiki_client = mock_wiki_instance
            return builder

    def test_valid_name(self, builder: GraphBuilder) -> None:
        """Test that valid scientist names are accepted."""
        assert builder._is_valid_name("Albert Einstein") is True
        assert builder._is_valid_name("Marie Curie") is True

    def test_rejects_empty_name(self, builder: GraphBuilder) -> None:
        """Test that empty names are rejected."""
        assert builder._is_valid_name("") is False
        assert builder._is_valid_name(None) is False  # type: ignore

    def test_rejects_short_name(self, builder: GraphBuilder) -> None:
        """Test that short names are rejected."""
        assert builder._is_valid_name("Al") is False

    def test_rejects_single_word_name(self, builder: GraphBuilder) -> None:
        """Test that single word names are rejected."""
        assert builder._is_valid_name("Einstein") is False

    def test_rejects_blacklisted_name(self, builder: GraphBuilder) -> None:
        """Test that blacklisted names are rejected."""
        assert builder._is_valid_name("Adolf Hitler") is False
        assert builder._is_valid_name("Joseph Stalin") is False

    def test_rejects_exclusion_pattern(self, builder: GraphBuilder) -> None:
        """Test that names matching exclusion patterns are rejected."""
        assert builder._is_valid_name("Vienna Circle") is False
        assert builder._is_valid_name("Harvard University") is False
        assert builder._is_valid_name("Pythagorean theorem") is False


class TestSaveGraph:
    """Tests for save_graph method."""

    @pytest.fixture
    def builder_with_graph(self) -> GraphBuilder:
        """Create a GraphBuilder with a sample graph."""
        with patch('graph_builder.WikipediaClient') as mock_wiki, \
             patch('graph_builder.LLMExtractor') as mock_llm:

            mock_wiki.return_value = MagicMock()
            mock_llm.return_value = MagicMock()

            builder = GraphBuilder()
            builder.graph.add_node("Einstein", depth=0, field="Physics", birth_year=1879)
            builder.graph.add_node("Bohr", depth=1, field="Physics", birth_year=1885)
            builder.graph.add_edge("Einstein", "Bohr", relation="inspired")
            return builder

    def test_save_creates_file(self, builder_with_graph: GraphBuilder) -> None:
        """Test that save_graph creates a GEXF file."""
        with tempfile.NamedTemporaryFile(suffix=".gexf", delete=False) as f:
            filename = f.name

        try:
            builder_with_graph.save_graph(filename)
            assert os.path.exists(filename)

            # Verify file is valid GEXF
            loaded = nx.read_gexf(filename)
            assert loaded.number_of_nodes() == 2
            assert loaded.number_of_edges() == 1
        finally:
            if os.path.exists(filename):
                os.unlink(filename)

    def test_save_handles_none_values(self, builder_with_graph: GraphBuilder) -> None:
        """Test that save_graph handles None attribute values."""
        builder_with_graph.graph.add_node("Unknown", depth=2, field=None, birth_year=None)

        with tempfile.NamedTemporaryFile(suffix=".gexf", delete=False) as f:
            filename = f.name

        try:
            builder_with_graph.save_graph(filename)
            assert os.path.exists(filename)

            loaded = nx.read_gexf(filename)
            assert "Unknown" in loaded.nodes()
        finally:
            if os.path.exists(filename):
                os.unlink(filename)


class TestLoadExistingGraph:
    """Tests for _load_existing_graph method."""

    @pytest.fixture
    def builder(self) -> GraphBuilder:
        """Create a GraphBuilder with mocked dependencies."""
        with patch('graph_builder.WikipediaClient') as mock_wiki, \
             patch('graph_builder.LLMExtractor') as mock_llm:

            mock_wiki.return_value = MagicMock()
            mock_llm.return_value = MagicMock()

            return GraphBuilder()

    def test_returns_start_queue_for_new_graph(self, builder: GraphBuilder) -> None:
        """Test that new graph returns queue with start scientist."""
        queue = builder._load_existing_graph("nonexistent.gexf", "Einstein")

        assert len(queue) == 1
        assert queue[0] == ("Einstein", 0)

    def test_loads_existing_graph(self, builder: GraphBuilder, sample_graph: nx.DiGraph) -> None:
        """Test that existing graph is loaded correctly."""
        with tempfile.NamedTemporaryFile(suffix=".gexf", delete=False) as f:
            filename = f.name
            nx.write_gexf(sample_graph, filename)

        try:
            queue = builder._load_existing_graph(filename, "Albert Einstein")

            assert builder.graph.number_of_nodes() == sample_graph.number_of_nodes()
            assert "Albert Einstein" in builder.visited
        finally:
            if os.path.exists(filename):
                os.unlink(filename)
