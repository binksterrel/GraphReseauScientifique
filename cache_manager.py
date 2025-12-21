"""
Cache Manager for LLM Responses
================================
Provides intelligent caching with:
- Hash-based keys (text + prompt version)
- Automatic invalidation on prompt change
- Statistics and hit rate tracking
"""

import hashlib
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any

# Cache configuration
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
PROMPT_VERSION = "v2.0-fewshot-cot"  # Increment when prompt changes significantly

class CacheManager:
    """Manages caching of LLM extraction results."""
    
    def __init__(self, cache_dir: str = CACHE_DIR, prompt_version: str = PROMPT_VERSION):
        self.cache_dir = cache_dir
        self.prompt_version = prompt_version
        self.stats = {"hits": 0, "misses": 0}
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def _generate_key(self, text: str, scientist_name: str) -> str:
        """Generate a unique cache key based on text content and prompt version."""
        # Use first 5000 chars of text to speed up hashing while maintaining uniqueness
        content = f"{scientist_name}|{self.prompt_version}|{text[:5000]}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _get_cache_path(self, key: str) -> str:
        """Get the file path for a cache entry."""
        return os.path.join(self.cache_dir, f"{key}.json")
    
    def get(self, text: str, scientist_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a cached result if available.
        Returns None if not cached or if cache is from different prompt version.
        """
        key = self._generate_key(text, scientist_name)
        cache_path = self._get_cache_path(key)
        
        if not os.path.exists(cache_path):
            self.stats["misses"] += 1
            return None
            
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached = json.load(f)
                
            # Validate prompt version
            if cached.get("prompt_version") != self.prompt_version:
                self.stats["misses"] += 1
                return None
                
            self.stats["hits"] += 1
            return cached.get("result")
            
        except (json.JSONDecodeError, IOError):
            self.stats["misses"] += 1
            return None
    
    def set(self, text: str, scientist_name: str, result: Dict[str, Any]) -> None:
        """Store a result in the cache."""
        key = self._generate_key(text, scientist_name)
        cache_path = self._get_cache_path(key)
        
        cache_entry = {
            "scientist_name": scientist_name,
            "prompt_version": self.prompt_version,
            "text_hash": hashlib.md5(text.encode('utf-8')).hexdigest(),
            "text_length": len(text),
            "result": result,
            "timestamp": datetime.now().isoformat(),
        }
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_entry, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"  ⚠️ Cache write error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Return cache statistics."""
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total * 100) if total > 0 else 0
        
        # Count total cached files
        try:
            cached_files = len([f for f in os.listdir(self.cache_dir) if f.endswith('.json')])
        except OSError:
            cached_files = 0
            
        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate": f"{hit_rate:.1f}%",
            "cached_entries": cached_files,
            "prompt_version": self.prompt_version,
        }
    
    def clear(self, confirm: bool = False) -> int:
        """Clear all cached entries. Returns number of files deleted."""
        if not confirm:
            print("⚠️ Pass confirm=True to actually clear cache.")
            return 0
            
        count = 0
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.json'):
                try:
                    os.remove(os.path.join(self.cache_dir, filename))
                    count += 1
                except OSError:
                    pass
        
        self.stats = {"hits": 0, "misses": 0}
        return count
    
    def invalidate_version(self, old_version: str) -> int:
        """Remove cache entries from a specific prompt version."""
        count = 0
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.json'):
                path = os.path.join(self.cache_dir, filename)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        cached = json.load(f)
                    if cached.get("prompt_version") == old_version:
                        os.remove(path)
                        count += 1
                except (json.JSONDecodeError, IOError, OSError):
                    pass
        return count


# Global cache instance
_cache_instance = None

def get_cache() -> CacheManager:
    """Get or create the global cache manager instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheManager()
    return _cache_instance


if __name__ == "__main__":
    # Test the cache manager
    cache = CacheManager()
    
    # Test set and get
    test_text = "Albert Einstein was a theoretical physicist..."
    test_result = {"inspirations": ["Ernst Mach"], "inspired": ["Bohr"]}
    
    cache.set(test_text, "Albert Einstein", test_result)
    retrieved = cache.get(test_text, "Albert Einstein")
    
    print(f"Cache test: {'✅ PASS' if retrieved == test_result else '❌ FAIL'}")
    print(f"Stats: {cache.get_stats()}")
