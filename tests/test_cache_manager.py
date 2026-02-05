"""
Tests for cache_manager.py
"""

import json
import os
from unittest.mock import patch

import pytest

from cache_manager import CacheManager, get_cache, PROMPT_VERSION


class TestCacheManager:
    """Tests for CacheManager class."""

    def test_init_creates_cache_dir(self, temp_cache_dir: str) -> None:
        """Test that initialization creates the cache directory."""
        cache_dir = os.path.join(temp_cache_dir, "new_cache")
        cache = CacheManager(cache_dir=cache_dir)
        assert os.path.exists(cache_dir)
        assert cache.prompt_version == PROMPT_VERSION

    def test_generate_key_deterministic(self, temp_cache_dir: str) -> None:
        """Test that key generation is deterministic."""
        cache = CacheManager(cache_dir=temp_cache_dir)
        text = "Sample text about Einstein"
        name = "Albert Einstein"

        key1 = cache._generate_key(text, name)
        key2 = cache._generate_key(text, name)

        assert key1 == key2
        assert len(key1) == 32  # MD5 hex length

    def test_generate_key_different_inputs(self, temp_cache_dir: str) -> None:
        """Test that different inputs generate different keys."""
        cache = CacheManager(cache_dir=temp_cache_dir)

        key1 = cache._generate_key("Text 1", "Einstein")
        key2 = cache._generate_key("Text 2", "Einstein")
        key3 = cache._generate_key("Text 1", "Bohr")

        assert key1 != key2
        assert key1 != key3

    def test_set_creates_file(self, temp_cache_dir: str) -> None:
        """Test that set creates a cache file."""
        cache = CacheManager(cache_dir=temp_cache_dir)
        text = "Einstein was a physicist"
        name = "Albert Einstein"
        result = {"inspired_by": ["Mach"], "inspired": ["Bohr"]}

        cache.set(text, name, result)

        files = os.listdir(temp_cache_dir)
        assert len(files) == 1
        assert files[0].endswith(".json")

    def test_get_returns_cached_result(self, temp_cache_dir: str) -> None:
        """Test that get returns the cached result."""
        cache = CacheManager(cache_dir=temp_cache_dir)
        text = "Einstein was a physicist"
        name = "Albert Einstein"
        result = {"inspired_by": ["Mach"], "inspired": ["Bohr"]}

        cache.set(text, name, result)
        retrieved = cache.get(text, name)

        assert retrieved == result

    def test_get_returns_none_for_miss(self, temp_cache_dir: str) -> None:
        """Test that get returns None for cache miss."""
        cache = CacheManager(cache_dir=temp_cache_dir)

        result = cache.get("Nonexistent text", "Unknown Scientist")

        assert result is None
        assert cache.stats["misses"] == 1

    def test_get_invalidates_different_version(self, temp_cache_dir: str) -> None:
        """Test that cache is invalidated for different prompt version."""
        cache1 = CacheManager(cache_dir=temp_cache_dir, prompt_version="v1.0")
        cache2 = CacheManager(cache_dir=temp_cache_dir, prompt_version="v2.0")

        text = "Einstein was a physicist"
        name = "Albert Einstein"
        result = {"inspired_by": ["Mach"], "inspired": ["Bohr"]}

        cache1.set(text, name, result)
        retrieved = cache2.get(text, name)

        assert retrieved is None

    def test_stats_tracking(self, temp_cache_dir: str) -> None:
        """Test that stats are tracked correctly."""
        cache = CacheManager(cache_dir=temp_cache_dir)
        text = "Einstein was a physicist"
        name = "Albert Einstein"
        result = {"inspired_by": [], "inspired": []}

        cache.set(text, name, result)
        cache.get(text, name)  # Hit
        cache.get("Other text", "Other name")  # Miss

        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["cached_entries"] == 1

    def test_clear_removes_files(self, temp_cache_dir: str) -> None:
        """Test that clear removes all cache files."""
        cache = CacheManager(cache_dir=temp_cache_dir)

        for i in range(5):
            cache.set(f"Text {i}", f"Scientist {i}", {"inspired_by": [], "inspired": []})

        assert len(os.listdir(temp_cache_dir)) == 5

        count = cache.clear(confirm=True)

        assert count == 5
        assert len(os.listdir(temp_cache_dir)) == 0

    def test_clear_requires_confirmation(self, temp_cache_dir: str) -> None:
        """Test that clear requires confirmation."""
        cache = CacheManager(cache_dir=temp_cache_dir)
        cache.set("Text", "Scientist", {"inspired_by": [], "inspired": []})

        count = cache.clear(confirm=False)

        assert count == 0
        assert len(os.listdir(temp_cache_dir)) == 1


class TestGetCache:
    """Tests for get_cache singleton function."""

    def test_returns_same_instance(self) -> None:
        """Test that get_cache returns the same instance."""
        # Reset global instance
        import cache_manager
        cache_manager._cache_instance = None

        cache1 = get_cache()
        cache2 = get_cache()

        assert cache1 is cache2
