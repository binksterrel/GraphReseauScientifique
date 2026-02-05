"""
Shared fixtures for Episteme-Network tests.
"""

import os
import sys
import tempfile
import shutil
from typing import Generator, Dict, List, Any

import pytest
import networkx as nx

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def temp_cache_dir() -> Generator[str, None, None]:
    """Create a temporary cache directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_graph() -> nx.DiGraph:
    """Create a sample graph for testing."""
    G = nx.DiGraph()
    G.add_node("Albert Einstein", depth=0, field="Physics", birth_year=1879)
    G.add_node("Max Planck", depth=1, field="Physics", birth_year=1858)
    G.add_node("Niels Bohr", depth=1, field="Physics", birth_year=1885)
    G.add_node("Werner Heisenberg", depth=2, field="Physics", birth_year=1901)

    G.add_edge("Max Planck", "Albert Einstein", relation="inspired")
    G.add_edge("Albert Einstein", "Niels Bohr", relation="inspired")
    G.add_edge("Niels Bohr", "Werner Heisenberg", relation="inspired")

    return G


@pytest.fixture
def sample_wikipedia_text() -> str:
    """Sample Wikipedia-like text for testing."""
    return """
    Albert Einstein (1879-1955) was a German-born theoretical physicist
    who developed the theory of relativity. He was influenced by
    Ernst Mach and Max Planck. Einstein's work influenced many physicists
    including Niels Bohr and Werner Heisenberg.
    """


@pytest.fixture
def sample_llm_response() -> Dict[str, List[str]]:
    """Sample LLM response for testing."""
    return {
        "inspired_by": ["Ernst Mach", "Max Planck"],
        "inspired": ["Niels Bohr", "Werner Heisenberg"]
    }


@pytest.fixture
def sample_llm_json_response() -> str:
    """Sample raw JSON response from LLM."""
    return '''
    Here is the analysis:
    {
        "inspired_by": ["Ernst Mach", "Max Planck"],
        "inspired": ["Niels Bohr", "Werner Heisenberg"]
    }
    '''


@pytest.fixture
def mock_cache_entry() -> Dict[str, Any]:
    """Sample cache entry for testing."""
    return {
        "scientist_name": "Albert Einstein",
        "prompt_version": "v2.0-fewshot-cot",
        "text_hash": "abc123",
        "text_length": 1000,
        "result": {
            "inspired_by": ["Ernst Mach"],
            "inspired": ["Niels Bohr"]
        },
        "timestamp": "2024-01-01T00:00:00"
    }
