"""
Cache for agentic correction completion calls.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
import pickle


class AgenticCorrectCache:
    """
    File-based cache for agentic correction completion calls.
    Caches based on hash of messages, model_name, and temperature.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        if cache_dir is None:
            cache_dir = Path.home() / 'research_desk_cache' / 'agentic_correct'
        
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, messages: list, model_name: str, temperature: float) -> str:
        """
        Generate a hash-based cache key from the input parameters.
        """
        # Create a deterministic representation of the input
        cache_input = {
            'messages': messages,
            'model_name': model_name,
            'temperature': temperature
        }
        
        # Convert to JSON string with sorted keys for deterministic hashing
        cache_str = json.dumps(cache_input, sort_keys=True, ensure_ascii=True)
        
        # Generate SHA256 hash
        return hashlib.sha256(cache_str.encode('utf-8')).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get the file path for a cache key."""
        return self.cache_dir / f"{cache_key}.pkl"
    
    def get(self, messages: list, model_name: str, temperature: float) -> Optional[Any]:
        """
        Retrieve cached result if it exists.
        
        Args:
            messages: The messages sent to the completion API
            model_name: The model name used
            temperature: The temperature parameter used
            
        Returns:
            Cached response object or None if not found
        """
        cache_key = self._get_cache_key(messages, model_name, temperature)
        cache_path = self._get_cache_path(cache_key)
        
        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
            except (pickle.PickleError, OSError) as e:
                print(f"Warning: Failed to load cache file {cache_path}: {e}")
                # Remove corrupted cache file
                try:
                    cache_path.unlink()
                except OSError:
                    pass
        
        return None
    
    def set(self, messages: list, model_name: str, temperature: float, response: Any) -> None:
        """
        Store a response in the cache.
        
        Args:
            messages: The messages sent to the completion API
            model_name: The model name used
            temperature: The temperature parameter used
            response: The response object to cache
        """
        cache_key = self._get_cache_key(messages, model_name, temperature)
        cache_path = self._get_cache_path(cache_key)
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(response, f)
        except (pickle.PickleError, OSError) as e:
            print(f"Warning: Failed to save cache file {cache_path}: {e}")
    
    def clear(self) -> None:
        """Clear all cached entries."""
        for cache_file in self.cache_dir.glob("*.pkl"):
            try:
                cache_file.unlink()
            except OSError:
                pass
    
    def size(self) -> int:
        """Return the number of cached entries."""
        return len(list(self.cache_dir.glob("*.pkl")))


# Global cache instance
_cache = AgenticCorrectCache()


def get_cached_completion(messages: list, model_name: str, temperature: float) -> Optional[Any]:
    """
    Get a cached completion response.
    
    Args:
        messages: The messages sent to the completion API
        model_name: The model name used
        temperature: The temperature parameter used
        
    Returns:
        Cached response object or None if not found
    """
    return _cache.get(messages, model_name, temperature)


def cache_completion(messages: list, model_name: str, temperature: float, response: Any) -> None:
    """
    Cache a completion response.
    
    Args:
        messages: The messages sent to the completion API
        model_name: The model name used
        temperature: The temperature parameter used
        response: The response object to cache
    """
    _cache.set(messages, model_name, temperature, response)


def clear_cache() -> None:
    """Clear all cached completion responses."""
    _cache.clear()


def cache_size() -> int:
    """Return the number of cached completion responses."""
    return _cache.size()
