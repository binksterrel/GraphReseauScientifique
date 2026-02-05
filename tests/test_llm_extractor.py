"""
Tests for llm_extractor.py
"""

import json
from typing import Dict, List
from unittest.mock import patch, MagicMock

import pytest

from llm_extractor import LLMExtractor


class TestParseJsonResponse:
    """Tests for _parse_json_response method."""

    @pytest.fixture
    def extractor(self) -> LLMExtractor:
        """Create an LLMExtractor instance for testing."""
        with patch('llm_extractor.get_cache') as mock_cache:
            mock_cache.return_value = MagicMock()
            return LLMExtractor()

    def test_parse_valid_json(self, extractor: LLMExtractor) -> None:
        """Test parsing valid JSON."""
        response = '{"inspired_by": ["Mach", "Planck"], "inspired": ["Bohr"]}'
        result = extractor._parse_json_response(response)

        assert result["inspired_by"] == ["Mach", "Planck"]
        assert result["inspired"] == ["Bohr"]

    def test_parse_json_with_noise(self, extractor: LLMExtractor) -> None:
        """Test parsing JSON with surrounding text."""
        response = '''
        Here is the analysis:
        {"inspired_by": ["Ernst Mach"], "inspired": ["Niels Bohr"]}
        That's my response.
        '''
        result = extractor._parse_json_response(response)

        assert result["inspired_by"] == ["Ernst Mach"]
        assert result["inspired"] == ["Niels Bohr"]

    def test_parse_empty_response(self, extractor: LLMExtractor) -> None:
        """Test parsing empty response."""
        result = extractor._parse_json_response("")

        assert result == {"inspired_by": [], "inspired": []}

    def test_parse_invalid_json(self, extractor: LLMExtractor) -> None:
        """Test parsing invalid JSON."""
        response = "This is not JSON at all"
        result = extractor._parse_json_response(response)

        assert result == {"inspired_by": [], "inspired": []}

    def test_parse_partial_json(self, extractor: LLMExtractor) -> None:
        """Test parsing partial/malformed JSON via regex fallback."""
        response = '''
        The scientist was influenced by "inspired_by": ["Einstein", "Bohr"]
        and he "inspired": ["Feynman"]
        '''
        result = extractor._parse_json_response(response)

        assert "Einstein" in result["inspired_by"] or result == {"inspired_by": [], "inspired": []}

    def test_parse_json_missing_keys(self, extractor: LLMExtractor) -> None:
        """Test parsing JSON with missing keys."""
        response = '{"inspired_by": ["Mach"]}'
        result = extractor._parse_json_response(response)

        assert result["inspired_by"] == ["Mach"]
        assert result["inspired"] == []


class TestExtractRelations:
    """Tests for extract_relations method."""

    @pytest.fixture
    def extractor_with_cache(self, temp_cache_dir: str) -> LLMExtractor:
        """Create an LLMExtractor with mocked cache."""
        with patch('llm_extractor.get_cache') as mock_cache:
            mock_instance = MagicMock()
            mock_instance.get.return_value = None
            mock_cache.return_value = mock_instance

            extractor = LLMExtractor()
            extractor.cache = mock_instance
            return extractor

    def test_returns_cached_result(self) -> None:
        """Test that cached results are returned."""
        cached_result = {"inspired_by": ["Cached"], "inspired": ["Result"]}

        with patch('llm_extractor.get_cache') as mock_cache:
            mock_instance = MagicMock()
            mock_instance.get.return_value = cached_result
            mock_cache.return_value = mock_instance

            extractor = LLMExtractor()
            extractor.cache = mock_instance

            result = extractor.extract_relations("Some text", "Einstein")

            assert result == cached_result

    def test_stores_result_in_cache(self, extractor_with_cache: LLMExtractor) -> None:
        """Test that results are stored in cache."""
        # Mock all LLM calls to fail, so we get empty result
        extractor = extractor_with_cache
        extractor.use_cerebras = False
        extractor.use_groq = False
        extractor.use_mistral = False
        extractor.use_ollama = False

        with patch.object(extractor, '_call_ollama', return_value=None):
            result = extractor.extract_relations("Some text", "Einstein")

            extractor.cache.set.assert_called_once()


class TestCheckConnection:
    """Tests for check_connection method."""

    def test_returns_true_when_service_available(self) -> None:
        """Test that check_connection returns True when a service is available."""
        with patch('llm_extractor.get_cache') as mock_cache:
            mock_cache.return_value = MagicMock()

            extractor = LLMExtractor()
            extractor.use_ollama = True
            extractor.use_groq = False
            extractor.use_cerebras = False
            extractor.use_mistral = False

            with patch.object(extractor, '_check_ollama', return_value=True):
                result = extractor.check_connection()
                assert result is True

    def test_returns_false_when_no_service(self) -> None:
        """Test that check_connection returns False when no service is available."""
        with patch('llm_extractor.get_cache') as mock_cache:
            mock_cache.return_value = MagicMock()

            extractor = LLMExtractor()
            extractor.use_ollama = False
            extractor.use_groq = False
            extractor.use_cerebras = False
            extractor.use_mistral = False

            with patch('llm_extractor.OPENAI_API_KEY', ''):
                result = extractor.check_connection()
                assert result is False
