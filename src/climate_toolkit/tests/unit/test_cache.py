"""
Unit tests for caching system.

Tests ensure caching works correctly and respects expiry times.
"""

import pytest
import time
from pathlib import Path

from climate_toolkit.core.cache import CacheManager, cached, get_cache_manager


class TestCacheManager:
    """Test suite for CacheManager."""

    def test_init_default_dir(self):
        """Test cache manager initialization with default directory."""
        cache_mgr = CacheManager()
        assert cache_mgr.cache_dir.exists()
        assert 'climate_toolkit' in str(cache_mgr.cache_dir)

    def test_init_custom_dir(self, tmp_path):
        """Test cache manager initialization with custom directory."""
        custom_dir = tmp_path / "custom_cache"
        cache_mgr = CacheManager(cache_dir=custom_dir)

        assert cache_mgr.cache_dir == custom_dir
        assert custom_dir.exists()

    def test_cache_get_set(self, tmp_path):
        """Test basic cache get/set operations."""
        cache_mgr = CacheManager(cache_dir=tmp_path)

        # Set a value
        result = {"data": [1, 2, 3], "metadata": "test"}
        cache_mgr.set("test_func", (1, 2), {"arg": "value"}, result)

        # Get it back
        retrieved = cache_mgr.get("test_func", (1, 2), {"arg": "value"})

        assert retrieved == result

    def test_cache_miss(self, tmp_path):
        """Test cache miss returns None."""
        cache_mgr = CacheManager(cache_dir=tmp_path)

        retrieved = cache_mgr.get("nonexistent", (), {})
        assert retrieved is None

    def test_cache_expiry(self, tmp_path):
        """Test cache expiry based on age."""
        cache_mgr = CacheManager(cache_dir=tmp_path)

        # Cache with very short expiry
        cache_mgr.set("test_func", (), {}, "test_value")

        # Should be retrievable immediately
        assert cache_mgr.get("test_func", (), {}, max_age_hours=1) == "test_value"

        # Modify file timestamp to simulate old cache
        cache_key = cache_mgr._get_cache_key("test_func", (), {})
        meta_path = cache_mgr._get_metadata_path(cache_key)

        if meta_path.exists():
            import json
            from datetime import datetime, timedelta

            with open(meta_path, 'r') as f:
                metadata = json.load(f)

            # Set timestamp to 2 hours ago
            old_time = datetime.now() - timedelta(hours=2)
            metadata['timestamp'] = old_time.isoformat()

            with open(meta_path, 'w') as f:
                json.dump(metadata, f)

            # Should be expired with max_age_hours=1
            assert cache_mgr.get("test_func", (), {}, max_age_hours=1) is None

    def test_cache_clear_all(self, tmp_path):
        """Test clearing all cache files."""
        cache_mgr = CacheManager(cache_dir=tmp_path)

        # Add multiple cached items
        for i in range(5):
            cache_mgr.set(f"func_{i}", (i,), {}, f"value_{i}")

        # Verify they exist
        files_before = list(tmp_path.glob("*.pkl"))
        assert len(files_before) == 5

        # Clear all
        count = cache_mgr.clear()
        assert count == 5

        # Verify they're gone
        files_after = list(tmp_path.glob("*.pkl"))
        assert len(files_after) == 0

    def test_cache_different_args(self, tmp_path):
        """Test that different arguments create different cache entries."""
        cache_mgr = CacheManager(cache_dir=tmp_path)

        cache_mgr.set("test_func", (1,), {}, "result_1")
        cache_mgr.set("test_func", (2,), {}, "result_2")

        assert cache_mgr.get("test_func", (1,), {}) == "result_1"
        assert cache_mgr.get("test_func", (2,), {}) == "result_2"

    def test_cache_kwargs_order_independent(self, tmp_path):
        """Test that keyword argument order doesn't affect caching."""
        cache_mgr = CacheManager(cache_dir=tmp_path)

        cache_mgr.set("test_func", (), {"a": 1, "b": 2}, "result")

        # Should get same result regardless of kwarg order
        assert cache_mgr.get("test_func", (), {"b": 2, "a": 1}) == "result"


class TestCachedDecorator:
    """Test suite for @cached decorator."""

    def test_cached_decorator_basic(self, tmp_path):
        """Test basic cached decorator functionality."""
        # Use temporary cache directory
        original_mgr = get_cache_manager()
        original_mgr.cache_dir = tmp_path

        call_count = 0

        @cached(max_age_hours=1)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1

        # Second call should use cache
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # Not called again

    def test_cached_decorator_different_args(self, tmp_path):
        """Test cached decorator with different arguments."""
        cache_mgr = get_cache_manager()
        cache_mgr.cache_dir = tmp_path

        call_count = 0

        @cached(max_age_hours=1)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = expensive_function(5)
        result2 = expensive_function(10)

        assert result1 == 10
        assert result2 == 20
        assert call_count == 2  # Called twice for different args

    def test_cached_decorator_with_kwargs(self, tmp_path):
        """Test cached decorator with keyword arguments."""
        cache_mgr = get_cache_manager()
        cache_mgr.cache_dir = tmp_path

        @cached(max_age_hours=1)
        def function_with_kwargs(a, b=10):
            return a + b

        result1 = function_with_kwargs(5, b=10)
        result2 = function_with_kwargs(5, b=10)

        assert result1 == 15
        assert result2 == 15

    def test_cached_decorator_no_expiry(self, tmp_path):
        """Test cached decorator with no expiry."""
        cache_mgr = get_cache_manager()
        cache_mgr.cache_dir = tmp_path

        @cached(max_age_hours=None)
        def function_no_expiry(x):
            return x * 3

        result = function_no_expiry(7)
        assert result == 21

        # Should still be cached
        cached_result = function_no_expiry(7)
        assert cached_result == 21


class TestGetCacheManager:
    """Test suite for get_cache_manager singleton."""

    def test_get_cache_manager_singleton(self):
        """Test that get_cache_manager returns singleton instance."""
        mgr1 = get_cache_manager()
        mgr2 = get_cache_manager()

        assert mgr1 is mgr2

    def test_get_cache_manager_creates_dir(self):
        """Test that get_cache_manager creates cache directory."""
        mgr = get_cache_manager()
        assert mgr.cache_dir.exists()
