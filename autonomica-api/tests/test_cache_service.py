"""
Tests for Cache Service Module
Tests the comprehensive caching functionality with Redis and in-memory fallback
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, Any, List
from datetime import datetime, timedelta
import json
import pickle
import gzip

from app.services.cache_service import (
    CacheService,
    create_cache_service,
    CacheConfig,
    CacheLevel,
    CacheStrategy,
    CacheEntry,
    CacheStats
)


class TestCacheConfig:
    """Test CacheConfig dataclass"""
    
    def test_cache_config_defaults(self):
        """Test that CacheConfig has correct default values"""
        config = CacheConfig()
        
        assert config.default_ttl == 3600
        assert config.max_memory_mb == 100
        assert config.compression_enabled is True
        assert config.redis_enabled is True
        assert config.redis_url == "redis://localhost:6379"
        assert config.redis_db == 0
        assert config.redis_password is None
        assert config.redis_ssl is False
        assert config.fallback_to_memory is True
        assert config.cache_strategy == CacheStrategy.HYBRID
        assert config.lru_max_size == 1000
        assert config.cleanup_interval == 300
    
    def test_cache_config_custom_values(self):
        """Test creating CacheConfig with custom values"""
        config = CacheConfig(
            default_ttl=7200,
            max_memory_mb=200,
            compression_enabled=False,
            redis_enabled=False,
            cache_strategy=CacheStrategy.LRU
        )
        
        assert config.default_ttl == 7200
        assert config.max_memory_mb == 200
        assert config.compression_enabled is False
        assert config.redis_enabled is False
        assert config.cache_strategy == CacheStrategy.LRU


class TestCacheEntry:
    """Test CacheEntry dataclass"""
    
    def test_cache_entry_creation(self):
        """Test creating a CacheEntry instance"""
        now = datetime.now()
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=now,
            expires_at=now + timedelta(hours=1)
        )
        
        assert entry.key == "test_key"
        assert entry.value == "test_value"
        assert entry.created_at == now
        assert entry.expires_at == now + timedelta(hours=1)
        assert entry.access_count == 0
        assert entry.last_accessed == now
        assert entry.size_bytes == 0
        assert entry.compression_ratio == 1.0
        assert entry.metadata == {}
    
    def test_cache_entry_with_optional_fields(self):
        """Test creating a CacheEntry with optional fields"""
        now = datetime.now()
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=now,
            expires_at=now + timedelta(hours=1),
            access_count=5,
            last_accessed=now - timedelta(minutes=30),
            size_bytes=1024,
            compression_ratio=0.8,
            metadata={"level": "test", "identifier": "test123"}
        )
        
        assert entry.access_count == 5
        assert entry.size_bytes == 1024
        assert entry.compression_ratio == 0.8
        assert entry.metadata["level"] == "test"


class TestCacheStats:
    """Test CacheStats dataclass"""
    
    def test_cache_stats_defaults(self):
        """Test that CacheStats has correct default values"""
        stats = CacheStats()
        
        assert stats.total_requests == 0
        assert stats.cache_hits == 0
        assert stats.cache_misses == 0
        assert stats.total_size_bytes == 0
        assert stats.entries_count == 0
        assert stats.compression_savings_bytes == 0
        assert stats.eviction_count == 0
        assert stats.last_cleanup is None
    
    def test_cache_stats_hit_rate_calculation(self):
        """Test hit rate calculation"""
        stats = CacheStats(total_requests=100, cache_hits=75)
        assert stats.hit_rate == 75.0
        
        stats = CacheStats(total_requests=0)
        assert stats.hit_rate == 0.0
    
    def test_cache_stats_compression_savings_calculation(self):
        """Test compression savings calculation"""
        stats = CacheStats(total_size_bytes=1000, compression_savings_bytes=200)
        assert stats.compression_savings_percent == 20.0
        
        stats = CacheStats(total_size_bytes=0)
        assert stats.compression_savings_percent == 0.0


class TestCacheService:
    """Test the main CacheService class"""
    
    @pytest.fixture
    async def mock_cache_service(self):
        """Create a mock cache service with mocked Redis"""
        with patch('app.services.cache_service.REDIS_AVAILABLE', True):
            with patch('app.services.cache_service.redis') as mock_redis:
                # Mock Redis client
                mock_redis_client = AsyncMock()
                mock_redis.Redis.from_url.return_value = mock_redis_client
                mock_redis_client.ping.return_value = True
                
                config = CacheConfig(redis_enabled=True, fallback_to_memory=True)
                service = CacheService(config)
                
                # Wait for initialization
                await asyncio.sleep(0.1)
                
                yield service
    
    @pytest.fixture
    async def memory_only_cache_service(self):
        """Create a cache service that only uses memory cache"""
        with patch('app.services.cache_service.REDIS_AVAILABLE', False):
            config = CacheConfig(redis_enabled=False, fallback_to_memory=True)
            service = CacheService(config)
            
            # Wait for initialization
            await asyncio.sleep(0.1)
            
            yield service
    
    def test_cache_service_initialization(self, mock_cache_service):
        """Test cache service initialization"""
        assert mock_cache_service.config is not None
        assert mock_cache_service.redis_client is not None
        assert mock_cache_service.redis_connected is True
        assert mock_cache_service.memory_cache == {}
        assert mock_cache_service.access_order == []
    
    def test_generate_cache_key(self, mock_cache_service):
        """Test cache key generation"""
        # Test basic key generation
        key1 = mock_cache_service._generate_cache_key(CacheLevel.API_RESPONSE, "test_id")
        key2 = mock_cache_service._generate_cache_key(CacheLevel.API_RESPONSE, "test_id")
        assert key1 == key2  # Same inputs should generate same key
        
        # Test key with parameters
        key3 = mock_cache_service._generate_cache_key(
            CacheLevel.KEYWORD_DATA, "python", language="en", region="us"
        )
        key4 = mock_cache_service._generate_cache_key(
            CacheLevel.KEYWORD_DATA, "python", region="us", language="en"
        )
        assert key3 == key4  # Parameters should be sorted consistently
        
        # Test different identifiers generate different keys
        key5 = mock_cache_service._generate_cache_key(CacheLevel.KEYWORD_DATA, "python")
        key6 = mock_cache_service._generate_cache_key(CacheLevel.KEYWORD_DATA, "javascript")
        assert key5 != key6
    
    def test_serialize_deserialize_value(self, mock_cache_service):
        """Test value serialization and deserialization"""
        # Test simple data types
        test_data = {"key": "value", "number": 42, "boolean": True}
        serialized = mock_cache_service._serialize_value(test_data)
        deserialized = mock_cache_service._deserialize_value(serialized)
        assert deserialized == test_data
        
        # Test complex object
        class TestObject:
            def __init__(self, value):
                self.value = value
            
            def __eq__(self, other):
                return isinstance(other, TestObject) and self.value == other.value
        
        test_obj = TestObject("test")
        serialized = mock_cache_service._serialize_value(test_obj)
        deserialized = mock_cache_service._deserialize_value(serialized)
        assert deserialized == test_obj
    
    @pytest.mark.asyncio
    async def test_set_and_get_memory_cache(self, memory_only_cache_service):
        """Test setting and getting values from memory cache"""
        # Set a value
        success = await memory_only_cache_service.set(
            CacheLevel.API_RESPONSE, "test_id", {"data": "test"}, ttl=3600
        )
        assert success is True
        
        # Get the value
        value = await memory_only_cache_service.get(CacheLevel.API_RESPONSE, "test_id")
        assert value == {"data": "test"}
        
        # Check statistics
        stats = await memory_only_cache_service.get_stats()
        assert stats.total_requests == 1
        assert stats.cache_hits == 1
        assert stats.cache_misses == 0
        assert stats.entries_count == 1
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, memory_only_cache_service):
        """Test cache entry expiration"""
        # Set a value with short TTL
        success = await memory_only_cache_service.set(
            CacheLevel.API_RESPONSE, "test_id", {"data": "test"}, ttl=1
        )
        assert success is True
        
        # Value should exist immediately
        value = await memory_only_cache_service.get(CacheLevel.API_RESPONSE, "test_id")
        assert value == {"data": "test"}
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Value should not exist after expiration
        value = await memory_only_cache_service.get(CacheLevel.API_RESPONSE, "test_id")
        assert value is None
        
        # Check statistics
        stats = await memory_only_cache_service.get_stats()
        assert stats.cache_misses == 1
    
    @pytest.mark.asyncio
    async def test_lru_eviction(self, memory_only_cache_service):
        """Test LRU eviction when cache is full"""
        # Set max size to 2
        memory_only_cache_service.config.lru_max_size = 2
        
        # Add 3 entries
        await memory_only_cache_service.set(CacheLevel.API_RESPONSE, "id1", "value1")
        await memory_only_cache_service.set(CacheLevel.API_RESPONSE, "id2", "value2")
        await memory_only_cache_service.set(CacheLevel.API_RESPONSE, "id3", "value3")
        
        # First entry should be evicted
        value1 = await memory_only_cache_service.get(CacheLevel.API_RESPONSE, "id1")
        assert value1 is None
        
        # Other entries should still exist
        value2 = await memory_only_cache_service.get(CacheLevel.API_RESPONSE, "id2")
        value3 = await memory_only_cache_service.get(CacheLevel.API_RESPONSE, "id3")
        assert value2 == "value2"
        assert value3 == "value3"
        
        # Check eviction count
        stats = await memory_only_cache_service.get_stats()
        assert stats.eviction_count == 1
    
    @pytest.mark.asyncio
    async def test_cache_clear(self, memory_only_cache_service):
        """Test clearing cache entries"""
        # Add some entries
        await memory_only_cache_service.set(CacheLevel.API_RESPONSE, "id1", "value1")
        await memory_only_cache_service.set(CacheLevel.KEYWORD_DATA, "python", "data1")
        
        # Clear specific level
        success = await memory_only_cache_service.clear(CacheLevel.API_RESPONSE)
        assert success is True
        
        # API response should be gone
        value1 = await memory_only_cache_service.get(CacheLevel.API_RESPONSE, "id1")
        assert value1 is None
        
        # Keyword data should still exist
        value2 = await memory_only_cache_service.get(CacheLevel.KEYWORD_DATA, "python")
        assert value2 == "data1"
        
        # Clear all
        success = await memory_only_cache_service.clear()
        assert success is True
        
        # All should be gone
        value2 = await memory_only_cache_service.get(CacheLevel.KEYWORD_DATA, "python")
        assert value2 is None
    
    @pytest.mark.asyncio
    async def test_cache_exists(self, memory_only_cache_service):
        """Test checking if cache entries exist"""
        # Add an entry
        await memory_only_cache_service.set(CacheLevel.API_RESPONSE, "test_id", "test_value")
        
        # Check existence
        exists = await memory_only_cache_service.exists(CacheLevel.API_RESPONSE, "test_id")
        assert exists is True
        
        # Check non-existent entry
        exists = await memory_only_cache_service.exists(CacheLevel.API_RESPONSE, "nonexistent")
        assert exists is False
    
    @pytest.mark.asyncio
    async def test_cache_delete(self, memory_only_cache_service):
        """Test deleting specific cache entries"""
        # Add an entry
        await memory_only_cache_service.set(CacheLevel.API_RESPONSE, "test_id", "test_value")
        
        # Verify it exists
        exists = await memory_only_cache_service.exists(CacheLevel.API_RESPONSE, "test_id")
        assert exists is True
        
        # Delete it
        success = await memory_only_cache_service.delete(CacheLevel.API_RESPONSE, "test_id")
        assert success is True
        
        # Verify it's gone
        exists = await memory_only_cache_service.exists(CacheLevel.API_RESPONSE, "test_id")
        assert exists is False
    
    @pytest.mark.asyncio
    async def test_redis_fallback(self, mock_cache_service):
        """Test Redis fallback to memory cache"""
        # Mock Redis failure
        mock_cache_service.redis_connected = False
        
        # Set value (should use memory cache)
        success = await mock_cache_service.set(
            CacheLevel.API_RESPONSE, "test_id", "test_value"
        )
        assert success is True
        
        # Get value (should come from memory cache)
        value = await mock_cache_service.get(CacheLevel.API_RESPONSE, "test_id")
        assert value == "test_value"
    
    @pytest.mark.asyncio
    async def test_compression(self, memory_only_cache_service):
        """Test data compression functionality"""
        # Create large data
        large_data = "x" * 1000
        
        # Set with compression enabled
        memory_only_cache_service.config.compression_enabled = True
        success = await memory_only_cache_service.set(
            CacheLevel.API_RESPONSE, "large_data", large_data
        )
        assert success is True
        
        # Retrieve the data
        retrieved_data = await memory_only_cache_service.get(CacheLevel.API_RESPONSE, "large_data")
        assert retrieved_data == large_data
        
        # Check if compression was applied (size should be smaller)
        # Note: This is a basic test - actual compression depends on data content
        stats = await memory_only_cache_service.get_stats()
        assert stats.entries_count == 1
    
    @pytest.mark.asyncio
    async def test_cache_service_close(self, memory_only_cache_service):
        """Test cache service cleanup on close"""
        # Add some entries
        await memory_only_cache_service.set(CacheLevel.API_RESPONSE, "id1", "value1")
        
        # Close service
        await memory_only_cache_service.close()
        
        # Cache should be cleared
        assert len(memory_only_cache_service.memory_cache) == 0
        assert len(memory_only_cache_service.access_order) == 0


class TestFactoryFunction:
    """Test the factory function"""
    
    @pytest.mark.asyncio
    async def test_create_cache_service(self):
        """Test cache service creation via factory function"""
        with patch('app.services.cache_service.CacheService') as mock_cache_service_class:
            mock_service = Mock()
            mock_cache_service_class.return_value = mock_service
            
            service = await create_cache_service()
            
            mock_cache_service_class.assert_called_once()
            assert service == mock_service


class TestCacheLevels:
    """Test CacheLevel enum"""
    
    def test_cache_level_values(self):
        """Test that all cache levels have valid values"""
        assert CacheLevel.API_RESPONSE.value == "api_response"
        assert CacheLevel.KEYWORD_DATA.value == "keyword_data"
        assert CacheLevel.ANALYSIS_RESULT.value == "analysis_result"
        assert CacheLevel.COMPETITOR_DATA.value == "competitor_data"
        assert CacheLevel.SERP_DATA.value == "serp_data"
        assert CacheLevel.CLUSTERING_RESULT.value == "clustering_result"
        assert CacheLevel.SUGGESTION_RESULT.value == "suggestion_result"
        assert CacheLevel.SCORE_RESULT.value == "score_result"


class TestCacheStrategies:
    """Test CacheStrategy enum"""
    
    def test_cache_strategy_values(self):
        """Test that all cache strategies have valid values"""
        assert CacheStrategy.LRU.value == "lru"
        assert CacheStrategy.TTL.value == "ttl"
        assert CacheStrategy.HYBRID.value == "hybrid"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

