"""
Tests for wikipedia_client.py
"""

from unittest.mock import patch, MagicMock

import pytest

from wikipedia_client import WikipediaClient


class TestExtractYears:
    """Tests for extract_years method."""

    @pytest.fixture
    def client(self) -> WikipediaClient:
        """Create a WikipediaClient for testing."""
        with patch('wikipedia_client.wikipediaapi.Wikipedia'):
            with patch('wikipedia_client.wikipedia'):
                return WikipediaClient()

    def test_extract_standard_format(self, client: WikipediaClient) -> None:
        """Test extraction from standard (1879-1955) format."""
        mock_page = MagicMock()
        mock_page.exists.return_value = True
        mock_page.summary = "Albert Einstein (1879–1955) was a physicist."
        mock_page.categories = {}

        with patch.object(client.wiki, 'page', return_value=mock_page):
            with patch('wikipedia_client.wikipedia.search', return_value=["Albert Einstein"]):
                birth, death = client.extract_years("Albert Einstein")

        assert birth == 1879
        assert death == 1955

    def test_extract_born_format(self, client: WikipediaClient) -> None:
        """Test extraction from 'born 1879' format."""
        mock_page = MagicMock()
        mock_page.exists.return_value = True
        mock_page.summary = "He was born 1879 and died 1955."
        mock_page.categories = {}

        with patch.object(client.wiki, 'page', return_value=mock_page):
            with patch('wikipedia_client.wikipedia.search', return_value=["Scientist"]):
                birth, death = client.extract_years("Scientist")

        assert birth == 1879
        assert death == 1955

    def test_extract_from_categories(self, client: WikipediaClient) -> None:
        """Test extraction from Wikipedia categories."""
        mock_page = MagicMock()
        mock_page.exists.return_value = True
        mock_page.summary = "A physicist who made contributions."
        mock_page.categories = {
            "Category:1879 births": None,
            "Category:1955 deaths": None,
            "Category:Physicists": None,
        }

        with patch.object(client.wiki, 'page', return_value=mock_page):
            with patch('wikipedia_client.wikipedia.search', return_value=["Scientist"]):
                birth, death = client.extract_years("Scientist")

        assert birth == 1879
        assert death == 1955

    def test_returns_none_for_missing_page(self, client: WikipediaClient) -> None:
        """Test that missing page returns None values."""
        mock_page = MagicMock()
        mock_page.exists.return_value = False

        with patch.object(client.wiki, 'page', return_value=mock_page):
            with patch('wikipedia_client.wikipedia.search', return_value=[]):
                birth, death = client.extract_years("Unknown Person")

        assert birth is None
        assert death is None


class TestIsScientist:
    """Tests for is_scientist method."""

    @pytest.fixture
    def client(self) -> WikipediaClient:
        """Create a WikipediaClient for testing."""
        with patch('wikipedia_client.wikipediaapi.Wikipedia'):
            with patch('wikipedia_client.wikipedia'):
                return WikipediaClient()

    def test_physicist_is_scientist(self, client: WikipediaClient) -> None:
        """Test that physicist is identified as scientist."""
        mock_page = MagicMock()
        mock_page.exists.return_value = True
        mock_page.categories = {
            "Category:German physicists": None,
            "Category:Nobel laureates in Physics": None,
        }

        with patch.object(client.wiki, 'page', return_value=mock_page):
            with patch('wikipedia_client.wikipedia.search', return_value=["Scientist"]):
                result = client.is_scientist("Scientist")

        assert result is True

    def test_actor_is_not_scientist(self, client: WikipediaClient) -> None:
        """Test that actor is not identified as scientist."""
        mock_page = MagicMock()
        mock_page.exists.return_value = True
        mock_page.categories = {
            "Category:American actors": None,
            "Category:Film directors": None,
        }

        with patch.object(client.wiki, 'page', return_value=mock_page):
            with patch('wikipedia_client.wikipedia.search', return_value=["Actor"]):
                result = client.is_scientist("Actor")

        assert result is False

    def test_missing_page_fail_open(self, client: WikipediaClient) -> None:
        """Test that missing page returns True (fail open)."""
        mock_page = MagicMock()
        mock_page.exists.return_value = False

        with patch.object(client.wiki, 'page', return_value=mock_page):
            with patch('wikipedia_client.wikipedia.search', return_value=[]):
                result = client.is_scientist("Unknown")

        assert result is True


class TestGetScientificField:
    """Tests for get_scientific_field method."""

    @pytest.fixture
    def client(self) -> WikipediaClient:
        """Create a WikipediaClient for testing."""
        with patch('wikipedia_client.wikipediaapi.Wikipedia'):
            with patch('wikipedia_client.wikipedia'):
                return WikipediaClient()

    def test_physics_field(self, client: WikipediaClient) -> None:
        """Test that physicist is classified as Physics."""
        mock_page = MagicMock()
        mock_page.exists.return_value = True
        mock_page.categories = {
            "Category:Theoretical physicists": None,
            "Category:Quantum physicists": None,
        }

        with patch.object(client.wiki, 'page', return_value=mock_page):
            with patch('wikipedia_client.wikipedia.search', return_value=["Physicist"]):
                field = client.get_scientific_field("Physicist")

        assert field == "Physics"

    def test_mathematics_field(self, client: WikipediaClient) -> None:
        """Test that mathematician is classified as Mathematics."""
        mock_page = MagicMock()
        mock_page.exists.return_value = True
        mock_page.categories = {
            "Category:German mathematicians": None,
            "Category:Algebraists": None,
        }

        with patch.object(client.wiki, 'page', return_value=mock_page):
            with patch('wikipedia_client.wikipedia.search', return_value=["Mathematician"]):
                field = client.get_scientific_field("Mathematician")

        assert field == "Mathematics"

    def test_returns_none_for_missing_page(self, client: WikipediaClient) -> None:
        """Test that missing page returns None."""
        mock_page = MagicMock()
        mock_page.exists.return_value = False

        with patch.object(client.wiki, 'page', return_value=mock_page):
            with patch('wikipedia_client.wikipedia.search', return_value=[]):
                field = client.get_scientific_field("Unknown")

        assert field is None


class TestGetScientistText:
    """Tests for get_scientist_text method."""

    @pytest.fixture
    def client(self) -> WikipediaClient:
        """Create a WikipediaClient for testing."""
        with patch('wikipedia_client.wikipediaapi.Wikipedia'):
            with patch('wikipedia_client.wikipedia'):
                return WikipediaClient()

    def test_returns_content_and_links(self, client: WikipediaClient) -> None:
        """Test that content and links are returned."""
        mock_page = MagicMock()
        mock_page.exists.return_value = True
        mock_page.title = "Albert Einstein"
        mock_page.summary = "A famous physicist"
        mock_page.text = "Detailed biography..."
        mock_page.links = {"Physics": None, "Relativity": None}

        with patch.object(client.wiki, 'page', return_value=mock_page):
            with patch('wikipedia_client.wikipedia.search', return_value=["Albert Einstein"]):
                result = client.get_scientist_text("Einstein")

        assert result is not None
        content, links = result
        assert "Albert Einstein" in content
        assert len(links) == 2

    def test_returns_none_for_concept_page(self, client: WikipediaClient) -> None:
        """Test that concept pages (theorem, law) return None."""
        mock_page = MagicMock()
        mock_page.exists.return_value = True
        mock_page.title = "Pythagorean theorem"

        with patch.object(client.wiki, 'page', return_value=mock_page):
            with patch('wikipedia_client.wikipedia.search', return_value=["Pythagorean theorem"]):
                result = client.get_scientist_text("Pythagorean theorem")

        assert result is None

    def test_returns_none_for_missing_page(self, client: WikipediaClient) -> None:
        """Test that missing page returns None."""
        mock_page = MagicMock()
        mock_page.exists.return_value = False

        with patch.object(client.wiki, 'page', return_value=mock_page):
            with patch('wikipedia_client.wikipedia.search', return_value=[]):
                result = client.get_scientist_text("Unknown Person")

        assert result is None
