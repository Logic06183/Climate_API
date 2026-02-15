"""
Intelligent caching system for expensive operations.

Respects API quotas and speeds up repeated analyses.
"""

import hashlib
import json
import pickle
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional
from datetime import datetime, timedelta

from ..logger import get_logger

logger = get_logger()


class CacheManager:
    """
    Manages disk-based caching for expensive operations.

    Helps researchers avoid re-downloading data and respect API quotas.
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize cache manager.

        Args:
            cache_dir: Directory for cache files (default: ~/.cache/climate_toolkit)
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".cache" / "climate_toolkit"

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.debug(f"Cache directory: {self.cache_dir}")

    def _get_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate unique cache key from function name and arguments."""
        # Create a deterministic representation
        key_dict = {
            "function": func_name,
            "args": str(args),
            "kwargs": sorted(kwargs.items())
        }

        key_str = json.dumps(key_dict, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get file path for cache key."""
        return self.cache_dir / f"{cache_key}.pkl"

    def _get_metadata_path(self, cache_key: str) -> Path:
        """Get metadata file path for cache key."""
        return self.cache_dir / f"{cache_key}.meta"

    def get(self, func_name: str, args: tuple, kwargs: dict,
            max_age_hours: Optional[float] = None) -> Optional[Any]:
        """
        Retrieve cached result if available and not expired.

        Args:
            func_name: Name of the function
            args: Function positional arguments
            kwargs: Function keyword arguments
            max_age_hours: Maximum age in hours (None = no expiry)

        Returns:
            Cached result or None if not found/expired
        """
        cache_key = self._get_cache_key(func_name, args, kwargs)
        cache_path = self._get_cache_path(cache_key)
        meta_path = self._get_metadata_path(cache_key)

        if not cache_path.exists():
            return None

        # Check expiry
        if max_age_hours is not None and meta_path.exists():
            with open(meta_path, 'r') as f:
                metadata = json.load(f)
                cached_time = datetime.fromisoformat(metadata['timestamp'])
                age = datetime.now() - cached_time

                if age > timedelta(hours=max_age_hours):
                    logger.debug(f"Cache expired for {func_name}")
                    return None

        # Load cached result
        try:
            with open(cache_path, 'rb') as f:
                result = pickle.load(f)
            logger.info(f"✓ Loaded from cache: {func_name}")
            return result
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            return None

    def set(self, func_name: str, args: tuple, kwargs: dict, result: Any) -> None:
        """
        Cache a result.

        Args:
            func_name: Name of the function
            args: Function positional arguments
            kwargs: Function keyword arguments
            result: Result to cache
        """
        cache_key = self._get_cache_key(func_name, args, kwargs)
        cache_path = self._get_cache_path(cache_key)
        meta_path = self._get_metadata_path(cache_key)

        # Save result
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(result, f)

            # Save metadata
            metadata = {
                'function': func_name,
                'timestamp': datetime.now().isoformat(),
                'cache_key': cache_key
            }
            with open(meta_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            logger.debug(f"Cached result for {func_name}")
        except Exception as e:
            logger.warning(f"Failed to cache result: {e}")

    def clear(self, older_than_days: Optional[int] = None) -> int:
        """
        Clear cache files.

        Args:
            older_than_days: Only clear files older than this many days

        Returns:
            Number of files deleted
        """
        count = 0
        cutoff_time = None

        if older_than_days is not None:
            cutoff_time = datetime.now() - timedelta(days=older_than_days)

        for cache_file in self.cache_dir.glob("*.pkl"):
            if cutoff_time is None or datetime.fromtimestamp(
                cache_file.stat().st_mtime
            ) < cutoff_time:
                cache_file.unlink()
                # Also remove metadata
                meta_file = cache_file.with_suffix('.meta')
                if meta_file.exists():
                    meta_file.unlink()
                count += 1

        logger.info(f"Cleared {count} cache file(s)")
        return count


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def cached(max_age_hours: Optional[float] = 24):
    """
    Decorator to cache function results.

    Args:
        max_age_hours: Maximum cache age in hours (None = never expire)

    Example:
        @cached(max_age_hours=24)
        def expensive_function(arg1, arg2):
            # This result will be cached for 24 hours
            return compute_expensive_result(arg1, arg2)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_mgr = get_cache_manager()

            # Try to get from cache
            cached_result = cache_mgr.get(
                func.__name__, args, kwargs, max_age_hours
            )

            if cached_result is not None:
                return cached_result

            # Compute result
            result = func(*args, **kwargs)

            # Cache result
            cache_mgr.set(func.__name__, args, kwargs, result)

            return result

        return wrapper
    return decorator
