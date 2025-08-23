"""
Test cache service functionality
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any, Dict

from app.services.cache_service import (
    CacheService,
    CacheConfig,
    CacheLevel,
    CacheStrategy,
    create_cache_service
)


@pytest.fixture
def cache_config():
    """Create test cache configuration"""
    return CacheConfig(
        default_ttl=300,
        max_memory_mb=50,
        compression_enabled=False,
        redis_enabled=False,
        fallback_to_memory=True,
        cache_strategy=CacheStrategy.TTL,
        lru_max_size=500,
        cleanup_interval=60
    )


@pytest.fixture
def cache_service(cache_config):
    """Create cache service instance with mocked initialization"""
    with patch('asyncio.create_task'):
        service = CacheService(redis_service=None, config=cache_config)
        return service


class TestCacheConfig:
    """Test cache configuration"""

    def test_cache_config_defaults(self):
        """Test default cache configuration values"""
        config = CacheConfig()

        assert config.default_ttl == 3600
        assert config.max_memory_mb == 100
        assert config.compression_enabled is False
        assert config.redis_enabled is False
        assert config.redis_url == "redis://localhost:6379"
        assert config.fallback_to_memory is True
        assert config.cache_strategy == CacheStrategy.TTL
        assert config.lru_max_size == 1000
        assert config.cleanup_interval == 300

    def test_cache_config_custom_values(self):
        """Test custom cache configuration values"""
        config = CacheConfig(
            default_ttl=600,
            max_memory_mb=200,
            redis_enabled=True,
            redis_url="redis://test:6379",
            cache_strategy=CacheStrategy.LRU
        )

        assert config.default_ttl == 600
        assert config.max_memory_mb == 200
        assert config.redis_enabled is True
        assert config.redis_url == "redis://test:6379"
        assert config.cache_strategy == CacheStrategy.LRU


class TestCacheService:
    """Test cache service functionality"""

    @pytest.mark.asyncio
    async def test_cache_service_initialization(self, cache_service):
        """Test cache service initialization"""
        assert cache_service.redis_service is None
        assert cache_service.config is not None
        assert cache_service.memory_cache == {}
        assert cache_service.cache_locks == {}
        assert cache_service.default_ttl == 300
        assert isinstance(cache_service.stats, dict)

    @pytest.mark.asyncio
    async def test_set_and_get_cache(self, cache_service):
        """Test setting and getting cache values"""
        # Test setting a value
        result = await cache_service.set("test_key", "test_value", ttl=300)
        assert result is True

        # Test getting the value
        cached_value = await cache_service.get("test_key")
        assert cached_value == "test_value"

        # Verify stats
        assert cache_service.stats["total_requests"] == 1
        assert cache_service.stats["cache_hits"] == 1

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, cache_service):
        """Test getting a key that doesn't exist"""
        result = await cache_service.get("nonexistent_key")
        assert result is None

        # Verify stats
        assert cache_service.stats["cache_misses"] == 1

    @pytest.mark.asyncio
    async def test_cache_expiration(self, cache_service):
        """Test cache expiration"""
        # Set a value with short TTL
        await cache_service.set("expire_key", "expire_value", ttl=1)

        # Verify it exists immediately
        cached_value = await cache_service.get("expire_key")
        assert cached_value == "expire_value"

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Verify it's expired
        expired_value = await cache_service.get("expire_key")
        assert expired_value is None

    @pytest.mark.asyncio
    async def test_delete_cache(self, cache_service):
        """Test deleting cache values"""
        # Set a value
        await cache_service.set("delete_key", "delete_value")
        assert await cache_service.get("delete_key") == "delete_value"

        # Delete the value
        result = await cache_service.delete("delete_key")
        assert result is True

        # Verify it's deleted
        assert await cache_service.get("delete_key") is None

    @pytest.mark.asyncio
    async def test_exists_cache(self, cache_service):
        """Test checking if cache key exists"""
        # Key doesn't exist
        assert await cache_service.exists("nonexistent") is False

        # Set a value
        await cache_service.set("exists_key", "exists_value")
        assert await cache_service.exists("exists_key") is True

        # Delete the value
        await cache_service.delete("exists_key")
        assert await cache_service.exists("exists_key") is False

    @pytest.mark.asyncio
    async def test_get_or_set_cache(self, cache_service):
        """Test get_or_set functionality"""
        async def expensive_operation():
            return "computed_value"

        # First call should compute and cache
        result1 = await cache_service.get_or_set("computed_key", expensive_operation)
        assert result1 == "computed_value"

        # Second call should return cached value
        result2 = await cache_service.get_or_set("computed_key", expensive_operation)
        assert result2 == "computed_value"

        # Verify cache hit
        assert cache_service.stats["cache_hits"] == 1

    @pytest.mark.asyncio
    async def test_increment_cache(self, cache_service):
        """Test increment functionality"""
        # Increment from zero
        result = await cache_service.increment("counter")
        assert result == 1

        # Increment existing value
        result = await cache_service.increment("counter", 5)
        assert result == 6

        # Verify cached value
        cached_value = await cache_service.get("counter")
        assert cached_value == 6

    @pytest.mark.asyncio
    async def test_decrement_cache(self, cache_service):
        """Test decrement functionality"""
        # Set initial value
        await cache_service.set("counter", 10)

        # Decrement
        result = await cache_service.decrement("counter", 3)
        assert result == 7

        # Verify cached value
        cached_value = await cache_service.get("counter")
        assert cached_value == 7

    @pytest.mark.asyncio
    async def test_increment_non_numeric(self, cache_service):
        """Test increment with non-numeric value"""
        await cache_service.set("non_numeric", "not_a_number")
        result = await cache_service.increment("non_numeric")
        assert result is None

    @pytest.mark.asyncio
    async def test_invalidate_pattern(self, cache_service):
        """Test pattern-based cache invalidation"""
        # Set multiple values
        await cache_service.set("user:1", "data1")
        await cache_service.set("user:2", "data2")
        await cache_service.set("post:1", "post1")

        # Verify they exist
        assert await cache_service.exists("user:1") is True
        assert await cache_service.exists("user:2") is True
        assert await cache_service.exists("post:1") is True

        # Invalidate user pattern
        count = await cache_service.invalidate_pattern("user:")
        assert count == 2

        # Verify invalidation
        assert await cache_service.exists("user:1") is False
        assert await cache_service.exists("user:2") is False
        assert await cache_service.exists("post:1") is True

    @pytest.mark.asyncio
    async def test_clear_all_cache(self, cache_service):
        """Test clearing all cache"""
        # Set some values
        await cache_service.set("key1", "value1")
        await cache_service.set("key2", "value2")

        # Verify they exist
        assert await cache_service.exists("key1") is True
        assert await cache_service.exists("key2") is True

        # Clear all
        result = await cache_service.clear_all()
        assert result is True

        # Verify they're cleared
        assert await cache_service.exists("key1") is False
        assert await cache_service.exists("key2") is False
        assert len(cache_service.memory_cache) == 0

    @pytest.mark.asyncio
    async def test_set_multi_cache(self, cache_service):
        """Test setting multiple cache values"""
        data = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
        }

        results = await cache_service.set_multi(data, ttl=300)

        # Verify all were set successfully
        for key in data.keys():
            assert results[key] is True
            assert await cache_service.get(key) == data[key]

    @pytest.mark.asyncio
    async def test_get_multi_cache(self, cache_service):
        """Test getting multiple cache values"""
        # Set some values
        await cache_service.set("key1", "value1")
        await cache_service.set("key2", "value2")
        await cache_service.set("key3", "value3")

        # Get multiple values
        results = await cache_service.get_multi(["key1", "key2", "key3"])

        assert results["key1"] == "value1"
        assert results["key2"] == "value2"
        assert results["key3"] == "value3"

    @pytest.mark.asyncio
    async def test_get_multi_with_missing_keys(self, cache_service):
        """Test getting multiple cache values with some missing keys"""
        await cache_service.set("key1", "value1")

        results = await cache_service.get_multi(["key1", "missing1", "missing2"])

        assert results["key1"] == "value1"
        assert "missing1" not in results
        assert "missing2" not in results

    @pytest.mark.asyncio
    async def test_cache_stats(self, cache_service):
        """Test cache statistics"""
        # Perform some operations
        await cache_service.set("key1", "value1")
        await cache_service.get("key1")  # Hit
        await cache_service.get("missing")  # Miss

        stats = await cache_service.get_cache_stats()

        assert stats["memory_cache_size"] == 1
        assert "default_ttl" in stats

    @pytest.mark.asyncio
    async def test_health_status(self, cache_service):
        """Test cache health status"""
        health = await cache_service.get_health_status()

        assert health["status"] == "healthy"
        assert health["redis_connected"] is False
        assert health["memory_cache_size"] == 0
        assert "timestamp" in health

    @pytest.mark.asyncio
    async def test_detailed_stats(self, cache_service):
        """Test detailed cache statistics"""
        # Perform some operations
        await cache_service.set("key1", "value1")
        await cache_service.get("key1")  # Hit
        await cache_service.get("missing")  # Miss

        stats = await cache_service.get_detailed_stats()

        assert stats["total_requests"] == 2
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 1
        assert stats["hit_rate"] == 0.5
        assert stats["entries_count"] == 1

    @pytest.mark.asyncio
    async def test_cleanup_expired(self, cache_service):
        """Test cleanup of expired entries"""
        # Set a value with very short TTL
        await cache_service.set("expire_key", "expire_value", ttl=1)

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Manual cleanup
        count = await cache_service.cleanup_expired()
        assert count == 1

        # Verify it's cleaned up
        assert await cache_service.get("expire_key") is None


class TestCreateCacheService:
    """Test cache service factory function"""

    @pytest.mark.asyncio
    async def test_create_cache_service_with_default_config(self):
        """Test creating cache service with default config"""
        service = await create_cache_service()

        assert isinstance(service, CacheService)
        assert service.config.default_ttl == 3600
        assert service.redis_service is None

    @pytest.mark.asyncio
    async def test_create_cache_service_with_custom_config(self, cache_config):
        """Test creating cache service with custom config"""
        service = await create_cache_service(cache_config)

        assert isinstance(service, CacheService)
        assert service.config.default_ttl == 300
        assert service.redis_service is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
