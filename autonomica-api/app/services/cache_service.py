"""
Cache Service for SEO Module
Provides efficient caching for API responses, keyword data, and analysis results
"""
import asyncio
import json
import logging
import hashlib
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import pickle
import gzip

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)


class CacheStrategy(Enum):
    """Cache strategy types"""
    LRU = "lru"
    TTL = "ttl"
    HYBRID = "hybrid"


class CacheLevel(Enum):
    """Cache levels for different types of data"""
    API_RESPONSE = "api_response"
    KEYWORD_DATA = "keyword_data"
    ANALYSIS_RESULT = "analysis_result"
    COMPETITOR_DATA = "competitor_data"
    SERP_DATA = "serp_data"
    CLUSTERING_RESULT = "clustering_result"
    SUGGESTION_RESULT = "suggestion_result"
    SCORE_RESULT = "score_result"


@dataclass
class CacheConfig:
    """Configuration for caching behavior"""
    default_ttl: int = 3600  # 1 hour in seconds
    max_memory_mb: int = 100  # Maximum memory usage for in-memory cache
    compression_enabled: bool = True
    redis_enabled: bool = True
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0
    redis_password: Optional[str] = None
    redis_ssl: bool = False
    fallback_to_memory: bool = True
    cache_strategy: CacheStrategy = CacheStrategy.HYBRID
    lru_max_size: int = 1000
    cleanup_interval: int = 300  # 5 minutes


@dataclass
class CacheEntry:
    """Represents a cached item"""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime]
    access_count: int = 0
    last_accessed: datetime = None
    size_bytes: int = 0
    compression_ratio: float = 1.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.created_at
        if self.metadata is None:
            self.metadata = {}


@dataclass
class CacheStats:
    """Cache performance statistics"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_size_bytes: int = 0
    entries_count: int = 0
    compression_savings_bytes: int = 0
    eviction_count: int = 0
    last_cleanup: Optional[datetime] = None

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        if self.total_requests == 0:
            return 0.0
        return (self.cache_hits / self.total_requests) * 100

    @property
    def compression_savings_percent(self) -> float:
        """Calculate compression savings percentage"""
        if self.total_size_bytes == 0:
            return 0.0
        return (self.compression_savings_bytes / self.total_size_bytes) * 100


class CacheService:
    """Main caching service with Redis and in-memory fallback"""
    
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize Redis connection
        self.redis_client = None
        self.redis_connected = False
        
        # In-memory cache fallback
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.access_order: List[str] = []  # For LRU implementation
        
        # Statistics
        self.stats = CacheStats()
        
        # Cleanup task
        self.cleanup_task = None
        
        # Initialize the service
        asyncio.create_task(self._initialize())
    
    async def _initialize(self):
        """Initialize the cache service"""
        try:
            if self.config.redis_enabled and REDIS_AVAILABLE:
                await self._connect_redis()
            
            # Start cleanup task
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            self.logger.info("Cache service initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize cache service: {e}")
            if self.config.fallback_to_memory:
                self.logger.info("Falling back to in-memory cache")
    
    async def _connect_redis(self):
        """Connect to Redis server"""
        try:
            if self.config.redis_password:
                self.redis_client = redis.Redis.from_url(
                    self.config.redis_url,
                    db=self.config.redis_db,
                    password=self.config.redis_password,
                    ssl=self.config.redis_ssl,
                    decode_responses=False  # Keep as bytes for compression
                )
            else:
                self.redis_client = redis.Redis.from_url(
                    self.config.redis_url,
                    db=self.config.redis_db,
                    ssl=self.config.redis_ssl,
                    decode_responses=False
                )
            
            # Test connection
            await self.redis_client.ping()
            self.redis_connected = True
            self.logger.info("Successfully connected to Redis")
            
        except Exception as e:
            self.logger.warning(f"Failed to connect to Redis: {e}")
            self.redis_connected = False
            if self.config.fallback_to_memory:
                self.logger.info("Using in-memory cache as fallback")
    
    def _generate_cache_key(self, level: CacheLevel, identifier: str, **kwargs) -> str:
        """Generate a unique cache key"""
        # Create a base key from level and identifier
        base_key = f"seo:{level.value}:{identifier}"
        
        # Add additional parameters if provided
        if kwargs:
            # Sort kwargs for consistent key generation
            sorted_kwargs = sorted(kwargs.items())
            param_str = ":".join(f"{k}={v}" for k, v in sorted_kwargs)
            base_key = f"{base_key}:{param_str}"
        
        # Hash the key to ensure it's Redis-safe and not too long
        return hashlib.md5(base_key.encode()).hexdigest()
    
    def _serialize_value(self, value: Any) -> bytes:
        """Serialize and optionally compress a value"""
        try:
            # Try to serialize as JSON first (for simple data types)
            if isinstance(value, (dict, list, str, int, float, bool)) or value is None:
                serialized = json.dumps(value, default=str).encode('utf-8')
            else:
                # Use pickle for complex objects
                serialized = pickle.dumps(value)
            
            # Compress if enabled
            if self.config.compression_enabled and len(serialized) > 100:  # Only compress larger data
                compressed = gzip.compress(serialized)
                if len(compressed) < len(serialized):
                    return compressed
            
            return serialized
            
        except Exception as e:
            self.logger.warning(f"Serialization failed, using pickle: {e}")
            return pickle.dumps(value)
    
    def _deserialize_value(self, data: bytes) -> Any:
        """Deserialize and optionally decompress a value"""
        try:
            # Try to decompress first
            try:
                decompressed = gzip.decompress(data)
                data = decompressed
            except (OSError, EOFError):
                # Not compressed, use as-is
                pass
            
            # Try JSON first
            try:
                return json.loads(data.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Fall back to pickle
                return pickle.loads(data)
                
        except Exception as e:
            self.logger.error(f"Deserialization failed: {e}")
            return None
    
    async def get(self, level: CacheLevel, identifier: str, **kwargs) -> Optional[Any]:
        """Retrieve a value from cache"""
        cache_key = self._generate_cache_key(level, identifier, **kwargs)
        self.stats.total_requests += 1
        
        try:
            # Try Redis first
            if self.redis_connected and self.redis_client:
                value = await self._get_from_redis(cache_key)
                if value is not None:
                    self.stats.cache_hits += 1
                    return value
            
            # Fall back to memory cache
            if cache_key in self.memory_cache:
                entry = self.memory_cache[cache_key]
                if not self._is_expired(entry):
                    # Update access statistics
                    entry.access_count += 1
                    entry.last_accessed = datetime.now()
                    self._update_access_order(cache_key)
                    
                    self.stats.cache_hits += 1
                    return entry.value
            
            self.stats.cache_misses += 1
            return None
            
        except Exception as e:
            self.logger.error(f"Error retrieving from cache: {e}")
            self.stats.cache_misses += 1
            return None
    
    async def _get_from_redis(self, cache_key: str) -> Optional[Any]:
        """Get value from Redis"""
        try:
            data = await self.redis_client.get(cache_key)
            if data is not None:
                # Get metadata
                meta_key = f"{cache_key}:meta"
                meta_data = await self.redis_client.get(meta_key)
                
                if meta_data:
                    metadata = json.loads(meta_data.decode('utf-8'))
                    # Check expiration
                    if 'expires_at' in metadata and metadata['expires_at']:
                        expires_at = datetime.fromisoformat(metadata['expires_at'])
                        if datetime.now() > expires_at:
                            # Expired, remove from Redis
                            await self.redis_client.delete(cache_key, meta_key)
                            return None
                
                return self._deserialize_value(data)
            return None
            
        except Exception as e:
            self.logger.warning(f"Redis get failed: {e}")
            return None
    
    async def set(self, level: CacheLevel, identifier: str, value: Any, 
                  ttl: Optional[int] = None, **kwargs) -> bool:
        """Store a value in cache"""
        cache_key = self._generate_cache_key(level, identifier, **kwargs)
        ttl = ttl or self.config.default_ttl
        
        try:
            # Create cache entry
            entry = CacheEntry(
                key=cache_key,
                value=value,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(seconds=ttl) if ttl > 0 else None,
                size_bytes=0,  # Will be calculated
                metadata={
                    'level': level.value,
                    'identifier': identifier,
                    'kwargs': kwargs
                }
            )
            
            # Serialize and store
            serialized = self._serialize_value(value)
            entry.size_bytes = len(serialized)
            
            # Try Redis first
            if self.redis_connected and self.redis_client:
                success = await self._set_in_redis(cache_key, serialized, entry, ttl)
                if success:
                    return True
            
            # Fall back to memory cache
            return self._set_in_memory(cache_key, entry)
            
        except Exception as e:
            self.logger.error(f"Error setting cache value: {e}")
            return False
    
    async def _set_in_redis(self, cache_key: str, serialized: bytes, 
                           entry: CacheEntry, ttl: int) -> bool:
        """Set value in Redis"""
        try:
            # Store the value
            if ttl > 0:
                await self.redis_client.setex(cache_key, ttl, serialized)
            else:
                await self.redis_client.set(cache_key, serialized)
            
            # Store metadata
            meta_key = f"{cache_key}:meta"
            metadata = {
                'created_at': entry.created_at.isoformat(),
                'expires_at': entry.expires_at.isoformat() if entry.expires_at else None,
                'size_bytes': entry.size_bytes,
                'level': entry.metadata['level'],
                'identifier': entry.metadata['identifier']
            }
            
            await self.redis_client.set(meta_key, json.dumps(metadata).encode('utf-8'))
            if ttl > 0:
                await self.redis_client.expire(meta_key, ttl)
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Redis set failed: {e}")
            return False
    
    def _set_in_memory(self, cache_key: str, entry: CacheEntry) -> bool:
        """Set value in memory cache"""
        try:
            # Check memory limits
            if len(self.memory_cache) >= self.config.lru_max_size:
                self._evict_lru_entry()
            
            # Store entry
            self.memory_cache[cache_key] = entry
            self._update_access_order(cache_key)
            
            # Update statistics
            self.stats.entries_count = len(self.memory_cache)
            self.stats.total_size_bytes += entry.size_bytes
            
            return True
            
        except Exception as e:
            self.logger.error(f"Memory cache set failed: {e}")
            return False
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if a cache entry has expired"""
        if entry.expires_at is None:
            return False
        return datetime.now() > entry.expires_at
    
    def _update_access_order(self, cache_key: str):
        """Update LRU access order"""
        if cache_key in self.access_order:
            self.access_order.remove(cache_key)
        self.access_order.append(cache_key)
    
    def _evict_lru_entry(self):
        """Evict least recently used entry"""
        if not self.access_order:
            return
        
        # Remove oldest entry
        oldest_key = self.access_order.pop(0)
        if oldest_key in self.memory_cache:
            entry = self.memory_cache[oldest_key]
            self.stats.total_size_bytes -= entry.size_bytes
            del self.memory_cache[oldest_key]
            self.stats.eviction_count += 1
    
    async def delete(self, level: CacheLevel, identifier: str, **kwargs) -> bool:
        """Delete a value from cache"""
        cache_key = self._generate_cache_key(level, identifier, **kwargs)
        
        try:
            # Delete from Redis
            if self.redis_connected and self.redis_client:
                await self.redis_client.delete(cache_key, f"{cache_key}:meta")
            
            # Delete from memory cache
            if cache_key in self.memory_cache:
                entry = self.memory_cache[cache_key]
                self.stats.total_size_bytes -= entry.size_bytes
                del self.memory_cache[cache_key]
                if cache_key in self.access_order:
                    self.access_order.remove(cache_key)
                self.stats.entries_count = len(self.memory_cache)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting cache value: {e}")
            return False
    
    async def clear(self, level: Optional[CacheLevel] = None) -> bool:
        """Clear cache entries, optionally by level"""
        try:
            if level:
                # Clear specific level
                pattern = f"seo:{level.value}:*"
            else:
                # Clear all
                pattern = "seo:*"
            
            # Clear from Redis
            if self.redis_connected and self.redis_client:
                keys = await self.redis_client.keys(pattern)
                if keys:
                    await self.redis_client.delete(*keys)
            
            # Clear from memory cache
            keys_to_remove = []
            for key, entry in self.memory_cache.items():
                if level is None or entry.metadata.get('level') == level.value:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                entry = self.memory_cache[key]
                self.stats.total_size_bytes -= entry.size_bytes
                del self.memory_cache[key]
                if key in self.access_order:
                    self.access_order.remove(key)
            
            self.stats.entries_count = len(self.memory_cache)
            return True
            
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
            return False
    
    async def exists(self, level: CacheLevel, identifier: str, **kwargs) -> bool:
        """Check if a key exists in cache"""
        cache_key = self._generate_cache_key(level, identifier, **kwargs)
        
        try:
            # Check Redis first
            if self.redis_connected and self.redis_client:
                exists = await self.redis_client.exists(cache_key)
                if exists:
                    return True
            
            # Check memory cache
            if cache_key in self.memory_cache:
                entry = self.memory_cache[cache_key]
                if not self._is_expired(entry):
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking cache existence: {e}")
            return False
    
    async def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        try:
            # Update Redis stats if available
            if self.redis_connected and self.redis_client:
                info = await self.redis_client.info()
                self.stats.total_size_bytes = info.get('used_memory', 0)
            
            return self.stats
            
        except Exception as e:
            self.logger.error(f"Error getting cache stats: {e}")
            return self.stats
    
    async def _cleanup_loop(self):
        """Background cleanup loop"""
        while True:
            try:
                await asyncio.sleep(self.config.cleanup_interval)
                await self._cleanup_expired()
                self.stats.last_cleanup = datetime.now()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Cleanup loop error: {e}")
    
    async def _cleanup_expired(self):
        """Remove expired entries from memory cache"""
        try:
            keys_to_remove = []
            for key, entry in self.memory_cache.items():
                if self._is_expired(entry):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                entry = self.memory_cache[key]
                self.stats.total_size_bytes -= entry.size_bytes
                del self.memory_cache[key]
                if key in self.access_order:
                    self.access_order.remove(key)
            
            self.stats.entries_count = len(self.memory_cache)
            
            if keys_to_remove:
                self.logger.info(f"Cleaned up {len(keys_to_remove)} expired cache entries")
                
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    async def close(self):
        """Close the cache service"""
        try:
            # Cancel cleanup task
            if self.cleanup_task:
                self.cleanup_task.cancel()
                try:
                    await self.cleanup_task
                except asyncio.CancelledError:
                    pass
            
            # Close Redis connection
            if self.redis_client:
                await self.redis_client.close()
            
            # Clear memory cache
            self.memory_cache.clear()
            self.access_order.clear()
            
            self.logger.info("Cache service closed successfully")
            
        except Exception as e:
            self.logger.error(f"Error closing cache service: {e}")


# Factory function for creating cache service
async def create_cache_service(config: Optional[CacheConfig] = None) -> CacheService:
    """Create and initialize a new cache service instance"""
    service = CacheService(config)
    # Wait a bit for initialization
    await asyncio.sleep(0.1)
    return service


# Convenience functions for common cache operations
async def cache_api_response(identifier: str, response: Any, ttl: int = 3600) -> bool:
    """Cache an API response"""
    from .cache_service import create_cache_service
    cache = await create_cache_service()
    return await cache.set(CacheLevel.API_RESPONSE, identifier, response, ttl)


async def get_cached_api_response(identifier: str) -> Optional[Any]:
    """Get a cached API response"""
    from .cache_service import create_cache_service
    cache = await create_cache_service()
    return await cache.get(CacheLevel.API_RESPONSE, identifier)


async def cache_keyword_data(keyword: str, data: Any, ttl: int = 7200) -> bool:
    """Cache keyword analysis data"""
    from .cache_service import create_cache_service
    cache = await create_cache_service()
    return await cache.set(CacheLevel.KEYWORD_DATA, keyword, data, ttl)


async def get_cached_keyword_data(keyword: str) -> Optional[Any]:
    """Get cached keyword analysis data"""
    from .cache_service import create_cache_service
    cache = await create_cache_service()
    return await cache.get(CacheLevel.KEYWORD_DATA, keyword)
