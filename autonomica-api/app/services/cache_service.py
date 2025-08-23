"""
Cache Service
Handles caching operations for performance optimization
"""

import json
import logging
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import asyncio
from enum import Enum

logger = logging.getLogger(__name__)

class CacheLevel(str, Enum):
    """Cache levels for different storage tiers"""
    MEMORY = "memory"
    REDIS = "redis"
    HYBRID = "hybrid"

class CacheStrategy(str, Enum):
    """Cache strategies for different use cases"""
    LRU = "lru"
    TTL = "ttl"
    HYBRID = "hybrid"

class CacheConfig:
    """Configuration for cache service"""
    def __init__(
        self,
        default_ttl: int = 3600,
        max_memory_mb: int = 100,
        compression_enabled: bool = False,
        redis_enabled: bool = False,
        redis_url: str = "redis://localhost:6379",
        redis_db: int = 0,
        redis_password: Optional[str] = None,
        redis_ssl: bool = False,
        fallback_to_memory: bool = True,
        cache_strategy: CacheStrategy = CacheStrategy.TTL,
        lru_max_size: int = 1000,
        cleanup_interval: int = 300
    ):
        self.default_ttl = default_ttl
        self.max_memory_mb = max_memory_mb
        self.compression_enabled = compression_enabled
        self.redis_enabled = redis_enabled
        self.redis_url = redis_url
        self.redis_db = redis_db
        self.redis_password = redis_password
        self.redis_ssl = redis_ssl
        self.fallback_to_memory = fallback_to_memory
        self.cache_strategy = cache_strategy
        self.lru_max_size = lru_max_size
        self.cleanup_interval = cleanup_interval

async def create_cache_service(config: Optional[CacheConfig] = None) -> 'CacheService':
    """Create a new cache service instance"""
    if config is None:
        config = CacheConfig()
    
    # For now, create without Redis service (can be added later)
    redis_service = None
    return CacheService(redis_service, config)

class CacheService:
    """Service for caching operations"""
    
    def __init__(self, redis_service=None, config: Optional[CacheConfig] = None):
        """Initialize cache service"""
        self.redis_service = redis_service
        self.config = config or CacheConfig()
        self.memory_cache = {}
        self.cache_locks = {}
        self.default_ttl = self.config.default_ttl
        
        # Initialize cache statistics
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "eviction_count": 0,
            "last_cleanup": None
        }
        
        # Start cleanup task
        asyncio.create_task(self._cleanup_task())
    
    async def _cleanup_task(self):
        """Background task to clean up expired entries"""
        while True:
            try:
                await self._cleanup_expired()
                self.stats["last_cleanup"] = datetime.utcnow().isoformat()
                await asyncio.sleep(self.config.cleanup_interval)
            except Exception as e:
                logger.error(f"Cleanup task error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def _cleanup_expired(self):
        """Remove expired entries from memory cache"""
        current_time = datetime.utcnow()
        expired_keys = []
        
        for key, entry in self.memory_cache.items():
            if self._is_expired(entry):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.memory_cache[key]
            self.stats["eviction_count"] += 1
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    async def get(self, key: str, use_memory: bool = True) -> Optional[Any]:
        """Get value from cache"""
        try:
            self.stats["total_requests"] += 1
            
            # Try memory cache first if enabled
            if use_memory and key in self.memory_cache:
                cache_entry = self.memory_cache[key]
                if not self._is_expired(cache_entry):
                    self.stats["cache_hits"] += 1
                    return cache_entry["value"]
                else:
                    # Remove expired entry
                    del self.memory_cache[key]
            
            # Try Redis cache if available
            if self.redis_service:
                cached_value = await self.redis_service.get(f"cache:{key}")
                if cached_value:
                    try:
                        data = json.loads(cached_value)
                        # Also store in memory cache for faster access
                        if use_memory:
                            self.memory_cache[key] = {
                                "value": data["value"],
                                "expires_at": data["expires_at"]
                            }
                        self.stats["cache_hits"] += 1
                        return data["value"]
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in cache for key {key}")
            
            self.stats["cache_misses"] += 1
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cache for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = None, use_memory: bool = True) -> bool:
        """Set value in cache"""
        try:
            ttl = ttl or self.default_ttl
            expires_at = datetime.utcnow() + timedelta(seconds=ttl)
            
            # Store in memory cache if enabled
            if use_memory:
                self.memory_cache[key] = {
                    "value": value,
                    "expires_at": expires_at
                }
            
            # Store in Redis cache if available
            if self.redis_service:
                cache_data = {
                    "value": value,
                    "expires_at": expires_at.isoformat()
                }
                json_data = json.dumps(cache_data, default=str)
                return await self.redis_service.set(f"cache:{key}", json_data, ex=ttl)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to set cache for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            # Remove from memory cache
            if key in self.memory_cache:
                del self.memory_cache[key]
            
            # Remove from Redis cache if available
            if self.redis_service:
                return await self.redis_service.delete(f"cache:{key}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete cache for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            # Check memory cache
            if key in self.memory_cache:
                return not self._is_expired(self.memory_cache[key])
            
            # Check Redis cache if available
            if self.redis_service:
                return await self.redis_service.exists(f"cache:{key}")
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check cache existence for key {key}: {e}")
            return False
    
    async def get_or_set(self, key: str, default_func, ttl: int = None, use_memory: bool = True) -> Any:
        """Get value from cache or set default if not exists"""
        try:
            # Try to get from cache
            cached_value = await self.get(key, use_memory)
            if cached_value is not None:
                return cached_value
            
            # Get lock to prevent multiple executions of default_func
            lock_key = f"lock:{key}"
            if lock_key not in self.cache_locks:
                self.cache_locks[lock_key] = asyncio.Lock()
            
            async with self.cache_locks[lock_key]:
                # Double-check cache after acquiring lock
                cached_value = await self.get(key, use_memory)
                if cached_value is not None:
                    return cached_value
                
                # Execute default function
                if asyncio.iscoroutinefunction(default_func):
                    value = await default_func()
                else:
                    value = default_func()
                
                # Store in cache
                await self.set(key, value, ttl, use_memory)
                return value
                
        except Exception as e:
            logger.error(f"Failed to get or set cache for key {key}: {e}")
            # Execute default function on error
            if asyncio.iscoroutinefunction(default_func):
                return await default_func()
            else:
                return default_func()
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all cache keys matching a pattern"""
        try:
            count = 0
            
            # Invalidate memory cache keys
            keys_to_remove = [key for key in self.memory_cache.keys() if pattern in key]
            for key in keys_to_remove:
                del self.memory_cache[key]
                count += 1
            
            # Invalidate Redis cache keys if available
            if self.redis_service:
                # Note: Redis doesn't support pattern deletion directly
                # This is a simplified implementation
                # In production, you might want to use SCAN command
                logger.warning("Pattern invalidation for Redis not fully implemented")
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to invalidate cache pattern {pattern}: {e}")
            return 0
    
    async def clear_all(self) -> bool:
        """Clear all cache"""
        try:
            # Clear memory cache
            self.memory_cache.clear()
            
            # Clear Redis cache if available
            if self.redis_service:
                # This is a simplified implementation
                # In production, you might want to use FLUSHDB or similar
                logger.warning("Full cache clear for Redis not fully implemented")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear all cache: {e}")
            return False
    
    def _is_expired(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is expired"""
        try:
            expires_at = cache_entry.get("expires_at")
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            
            return datetime.utcnow() > expires_at
        except Exception:
            return True
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            stats = {
                "memory_cache_size": len(self.memory_cache),
                "memory_cache_keys": list(self.memory_cache.keys()),
                "default_ttl": self.default_ttl
            }
            
            if self.redis_service:
                redis_stats = await self.redis_service.health_check()
                stats["redis_status"] = redis_stats
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e)}
    
    async def cleanup_expired(self) -> int:
        """Clean up expired cache entries"""
        try:
            count = 0
            keys_to_remove = []
            
            for key, entry in self.memory_cache.items():
                if self._is_expired(entry):
                    keys_to_remove.append(key)
                    count += 1
            
            for key in keys_to_remove:
                del self.memory_cache[key]
            
            logger.info(f"Cleaned up {count} expired cache entries")
            return count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired cache: {e}")
            return 0
    
    async def set_multi(self, data: Dict[str, Any], ttl: int = None, use_memory: bool = True) -> Dict[str, bool]:
        """Set multiple values in cache"""
        try:
            results = {}
            ttl = ttl or self.default_ttl
            
            for key, value in data.items():
                success = await self.set(key, value, ttl, use_memory)
                results[key] = success
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to set multiple cache values: {e}")
            return {key: False for key in data.keys()}
    
    async def get_multi(self, keys: List[str], use_memory: bool = True) -> Dict[str, Any]:
        """Get multiple values from cache"""
        try:
            results = {}
            
            for key in keys:
                value = await self.get(key, use_memory)
                if value is not None:
                    results[key] = value
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get multiple cache values: {e}")
            return {}
    
    async def increment(self, key: str, amount: int = 1, ttl: int = None) -> Optional[int]:
        """Increment a numeric value in cache"""
        try:
            current_value = await self.get(key)
            if current_value is None:
                current_value = 0
            
            if not isinstance(current_value, (int, float)):
                logger.warning(f"Cache value for key {key} is not numeric")
                return None
            
            new_value = current_value + amount
            await self.set(key, new_value, ttl)
            return new_value
            
        except Exception as e:
            logger.error(f"Failed to increment cache for key {key}: {e}")
            return None
    
    async def decrement(self, key: str, amount: int = 1, ttl: int = None) -> Optional[int]:
        """Decrement a numeric value in cache"""
        return await self.increment(key, -amount, ttl)
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get cache health status for API endpoints"""
        try:
            memory_size = len(self.memory_cache)
            total_entries = memory_size
            
            # Calculate total size in bytes (rough estimate)
            total_size_bytes = 0
            for entry in self.memory_cache.values():
                try:
                    total_size_bytes += len(str(entry.get("value", "")))
                except:
                    pass
            
            return {
                "status": "healthy",
                "redis_connected": self.redis_service is not None,
                "memory_cache_size": memory_size,
                "total_entries": total_entries,
                "last_cleanup": self.stats.get("last_cleanup"),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get health status: {e}")
            return {
                "status": "error",
                "redis_connected": False,
                "memory_cache_size": 0,
                "total_entries": 0,
                "last_cleanup": None,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    async def get_detailed_stats(self) -> Dict[str, Any]:
        """Get detailed cache statistics for API endpoints"""
        try:
            hit_rate = 0
            if self.stats["total_requests"] > 0:
                hit_rate = self.stats["cache_hits"] / self.stats["total_requests"]
            
            return {
                "total_requests": self.stats["total_requests"],
                "cache_hits": self.stats["cache_hits"],
                "cache_misses": self.stats["cache_misses"],
                "hit_rate": round(hit_rate, 4),
                "total_size_bytes": len(str(self.memory_cache)),
                "entries_count": len(self.memory_cache),
                "compression_savings_bytes": 0,  # Not implemented yet
                "compression_savings_percent": 0.0,  # Not implemented yet
                "eviction_count": self.stats["eviction_count"],
                "last_cleanup": self.stats.get("last_cleanup")
            }
        except Exception as e:
            logger.error(f"Failed to get detailed stats: {e}")
            return {"error": str(e)}
    
    async def clear_by_level(self, level: str = None, pattern: str = None) -> Dict[str, Any]:
        """Clear cache by level or pattern for API endpoints"""
        try:
            cleared_entries = 0
            
            if level == "memory" or level is None:
                if pattern:
                    # Clear by pattern
                    keys_to_remove = [key for key in self.memory_cache.keys() if pattern in key]
                    for key in keys_to_remove:
                        del self.memory_cache[key]
                        cleared_entries += 1
                else:
                    # Clear all memory cache
                    cleared_entries = len(self.memory_cache)
                    self.memory_cache.clear()
            
            if level == "redis" and self.redis_service:
                # Redis clear not fully implemented
                logger.warning("Redis cache clear not fully implemented")
            
            return {
                "success": True,
                "cleared_entries": cleared_entries,
                "message": f"Cleared {cleared_entries} entries from {level or 'all'} cache"
            }
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return {
                "success": False,
                "cleared_entries": 0,
                "message": f"Failed to clear cache: {str(e)}"
            }
    
    async def update_config(self, config_updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update cache configuration for API endpoints"""
        try:
            updated_fields = []
            
            for field, value in config_updates.items():
                if hasattr(self.config, field):
                    setattr(self.config, field, value)
                    updated_fields.append(field)
            
            # Update instance variables that depend on config
            if "default_ttl" in config_updates:
                self.default_ttl = self.config.default_ttl
            
            return {
                "success": True,
                "updated_fields": updated_fields,
                "message": f"Updated {len(updated_fields)} configuration fields"
            }
        except Exception as e:
            logger.error(f"Failed to update config: {e}")
            return {
                "success": False,
                "updated_fields": [],
                "message": f"Failed to update config: {str(e)}"
            }

