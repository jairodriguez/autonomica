"""
SEO Cache Manager

This module provides comprehensive caching management for SEO services:
- Intelligent caching strategies
- Cache invalidation policies
- Performance optimization
- Cache analytics and monitoring
- Multi-level caching
- Cache warming strategies
"""

import asyncio
import logging
import json
import hashlib
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import time
from collections import defaultdict, OrderedDict

from app.services.redis_service import RedisService

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Individual cache entry with metadata"""
    key: str
    data: Any
    created_at: datetime
    accessed_at: datetime
    access_count: int
    size_bytes: int
    ttl: int
    cache_type: str
    priority: int

@dataclass
class CacheStats:
    """Cache performance statistics"""
    total_entries: int
    total_size_bytes: int
    hit_rate: float
    miss_rate: float
    eviction_count: int
    average_access_time: float
    cache_efficiency: float
    last_updated: datetime

@dataclass
class CachePolicy:
    """Cache policy configuration"""
    max_size_mb: int
    max_entries: int
    default_ttl: int
    eviction_policy: str  # lru, lfu, fifo
    compression_enabled: bool
    warm_cache_enabled: bool
    analytics_enabled: bool

class SEOCacheManager:
    """Comprehensive SEO caching management service"""
    
    def __init__(self):
        self.redis_service = RedisService()
        
        # Cache policies for different data types
        self.cache_policies = {
            "keyword_data": CachePolicy(
                max_size_mb=100,
                max_entries=1000,
                default_ttl=3600 * 24,  # 24 hours
                eviction_policy="lru",
                compression_enabled=True,
                warm_cache_enabled=True,
                analytics_enabled=True
            ),
            "serp_data": CachePolicy(
                max_size_mb=200,
                max_entries=2000,
                default_ttl=3600 * 6,   # 6 hours
                eviction_policy="lru",
                compression_enabled=True,
                warm_cache_enabled=False,
                analytics_enabled=True
            ),
            "clustering": CachePolicy(
                max_size_mb=150,
                max_entries=1500,
                default_ttl=3600 * 24,  # 24 hours
                eviction_policy="lfu",
                compression_enabled=True,
                warm_cache_enabled=True,
                analytics_enabled=True
            ),
            "analysis": CachePolicy(
                max_size_mb=100,
                max_entries=1000,
                default_ttl=3600 * 12,  # 12 hours
                eviction_policy="lru",
                compression_enabled=True,
                warm_cache_enabled=False,
                analytics_enabled=True
            ),
            "seo_score": CachePolicy(
                max_size_mb=50,
                max_entries=500,
                default_ttl=3600 * 6,   # 6 hours
                eviction_policy="lru",
                compression_enabled=False,
                warm_cache_enabled=False,
                analytics_enabled=True
            ),
            "suggestions": CachePolicy(
                max_size_mb=80,
                max_entries=800,
                default_ttl=3600 * 24,  # 24 hours
                eviction_policy="lfu",
                compression_enabled=True,
                warm_cache_enabled=True,
                analytics_enabled=True
            )
        }
        
        # Cache analytics
        self.cache_analytics = {
            "hits": defaultdict(int),
            "misses": defaultdict(int),
            "evictions": defaultdict(int),
            "access_times": defaultdict(list),
            "size_usage": defaultdict(int)
        }
        
        # Cache warming strategies
        self.warming_strategies = {
            "keyword_data": self._warm_keyword_cache,
            "clustering": self._warm_clustering_cache,
            "suggestions": self._warm_suggestions_cache
        }
        
        # Performance monitoring
        self.performance_metrics = {
            "average_response_time": 0.0,
            "cache_hit_ratio": 0.0,
            "memory_usage": 0.0,
            "last_optimization": None
        }
    
    def _generate_cache_key(self, cache_type: str, *args) -> str:
        """Generate a unique cache key"""
        key_string = f"seo:{cache_type}:{'|'.join(str(arg) for arg in args)}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cache_policy(self, cache_type: str) -> CachePolicy:
        """Get cache policy for a specific type"""
        return self.cache_policies.get(cache_type, self.cache_policies["keyword_data"])
    
    async def _compress_data(self, data: Any) -> bytes:
        """Compress data for storage"""
        try:
            import gzip
            json_data = json.dumps(data, default=str)
            compressed = gzip.compress(json_data.encode('utf-8'))
            return compressed
        except ImportError:
            # Fallback to JSON if gzip not available
            return json.dumps(data, default=str).encode('utf-8')
    
    async def _decompress_data(self, compressed_data: bytes) -> Any:
        """Decompress data from storage"""
        try:
            import gzip
            decompressed = gzip.decompress(compressed_data)
            return json.loads(decompressed.decode('utf-8'))
        except (ImportError, Exception):
            # Fallback to direct JSON parsing
            return json.loads(compressed_data.decode('utf-8'))
    
    async def _calculate_data_size(self, data: Any) -> int:
        """Calculate approximate size of data in bytes"""
        try:
            json_data = json.dumps(data, default=str)
            return len(json_data.encode('utf-8'))
        except Exception:
            return 0
    
    async def _record_cache_access(self, cache_type: str, key: str, hit: bool, response_time: float):
        """Record cache access for analytics"""
        try:
            # Record hit/miss
            if hit:
                self.cache_analytics["hits"][cache_type] += 1
            else:
                self.cache_analytics["misses"][cache_type] += 1
            
            # Record access time
            self.cache_analytics["access_times"][cache_type].append(response_time)
            
            # Keep only last 100 access times for performance
            if len(self.cache_analytics["access_times"][cache_type]) > 100:
                self.cache_analytics["access_times"][cache_type] = self.cache_analytics["access_times"][cache_type][-100:]
            
            # Update performance metrics
            all_times = []
            for times in self.cache_analytics["access_times"].values():
                all_times.extend(times)
            
            if all_times:
                self.performance_metrics["average_response_time"] = sum(all_times) / len(all_times)
            
            # Calculate hit ratio
            total_requests = sum(self.cache_analytics["hits"].values()) + sum(self.cache_analytics["misses"].values())
            if total_requests > 0:
                self.performance_metrics["cache_hit_ratio"] = sum(self.cache_analytics["hits"].values()) / total_requests
            
        except Exception as e:
            logger.warning(f"Failed to record cache access: {e}")
    
    async def get(self, cache_type: str, *args) -> Optional[Any]:
        """
        Retrieve data from cache
        
        Args:
            cache_type: Type of cached data
            *args: Arguments to generate cache key
        
        Returns:
            Cached data or None if not found
        """
        start_time = time.time()
        
        try:
            cache_key = self._generate_cache_key(cache_type, *args)
            policy = self._get_cache_policy(cache_type)
            
            # Try to get from cache
            cached_data = await self.redis_service.get(cache_key)
            
            if cached_data:
                # Cache hit
                response_time = time.time() - start_time
                await self._record_cache_access(cache_type, cache_key, True, response_time)
                
                # Decompress if needed
                if policy.compression_enabled:
                    try:
                        decompressed_data = await self._decompress_data(cached_data)
                        return decompressed_data
                    except Exception as e:
                        logger.warning(f"Failed to decompress cached data: {e}")
                        # Return raw data if decompression fails
                        return json.loads(cached_data.decode('utf-8'))
                else:
                    return json.loads(cached_data.decode('utf-8'))
            else:
                # Cache miss
                response_time = time.time() - start_time
                await self._record_cache_access(cache_type, cache_key, False, response_time)
                return None
                
        except Exception as e:
            logger.error(f"Failed to retrieve from cache: {e}")
            return None
    
    async def set(self, cache_type: str, data: Any, ttl: Optional[int] = None, *args) -> bool:
        """
        Store data in cache
        
        Args:
            cache_type: Type of data to cache
            data: Data to store
            ttl: Time to live in seconds
            *args: Arguments to generate cache key
        
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_key = self._generate_cache_key(cache_type, *args)
            policy = self._get_cache_policy(cache_type)
            
            # Use policy default TTL if none specified
            if ttl is None:
                ttl = policy.default_ttl
            
            # Calculate data size
            data_size = await self._calculate_data_size(data)
            
            # Check if we need to evict entries
            await self._check_cache_limits(cache_type, data_size)
            
            # Prepare data for storage
            if policy.compression_enabled:
                storage_data = await self._compress_data(data)
            else:
                storage_data = json.dumps(data, default=str).encode('utf-8')
            
            # Store in cache
            success = await self.redis_service.set(cache_key, storage_data, expire=ttl)
            
            if success:
                # Update analytics
                self.cache_analytics["size_usage"][cache_type] += data_size
                
                # Store metadata
                metadata = {
                    "created_at": datetime.now().isoformat(),
                    "size_bytes": data_size,
                    "cache_type": cache_type,
                    "ttl": ttl
                }
                
                metadata_key = f"{cache_key}:metadata"
                await self.redis_service.set(metadata_key, json.dumps(metadata), expire=ttl)
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to store in cache: {e}")
            return False
    
    async def _check_cache_limits(self, cache_type: str, new_data_size: int):
        """Check and enforce cache limits"""
        try:
            policy = self._get_cache_policy(cache_type)
            
            # Check size limits
            current_size_mb = self.cache_analytics["size_usage"][cache_type] / (1024 * 1024)
            if current_size_mb + (new_data_size / (1024 * 1024)) > policy.max_size_mb:
                await self._evict_cache_entries(cache_type, policy, "size")
            
            # Check entry limits
            # Note: This is a simplified check. In production, you'd want to track actual entry counts
            # For now, we'll rely on Redis's built-in eviction policies
            
        except Exception as e:
            logger.warning(f"Failed to check cache limits: {e}")
    
    async def _evict_cache_entries(self, cache_type: str, policy: CachePolicy, reason: str):
        """Evict cache entries based on policy"""
        try:
            logger.info(f"Evicting cache entries for {cache_type} due to {reason}")
            
            # Get all keys for this cache type
            pattern = f"seo:{cache_type}:*"
            keys = await self.redis_service.keys(pattern)
            
            if not keys:
                return
            
            # Simple eviction strategy (remove oldest entries)
            # In production, you'd implement more sophisticated eviction based on policy
            keys_to_remove = keys[:len(keys) // 4]  # Remove 25% of entries
            
            for key in keys_to_remove:
                await self.redis_service.delete(key)
                # Also remove metadata
                metadata_key = f"{key}:metadata"
                await self.redis_service.delete(metadata_key)
            
            # Update analytics
            self.cache_analytics["evictions"][cache_type] += len(keys_to_remove)
            
            logger.info(f"Evicted {len(keys_to_remove)} entries from {cache_type} cache")
            
        except Exception as e:
            logger.error(f"Failed to evict cache entries: {e}")
    
    async def invalidate(self, cache_type: str, *args) -> bool:
        """
        Invalidate specific cache entries
        
        Args:
            cache_type: Type of cache to invalidate
            *args: Arguments to generate cache key
        
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_key = self._generate_cache_key(cache_type, *args)
            
            # Remove main cache entry
            await self.redis_service.delete(cache_key)
            
            # Remove metadata
            metadata_key = f"{cache_key}:metadata"
            await self.redis_service.delete(metadata_key)
            
            logger.info(f"Invalidated cache entry: {cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to invalidate cache: {e}")
            return False
    
    async def invalidate_type(self, cache_type: str) -> bool:
        """
        Invalidate all entries of a specific cache type
        
        Args:
            cache_type: Type of cache to invalidate
        
        Returns:
            True if successful, False otherwise
        """
        try:
            pattern = f"seo:{cache_type}:*"
            keys = await self.redis_service.keys(pattern)
            
            if keys:
                for key in keys:
                    await self.redis_service.delete(key)
                
                # Reset size usage
                self.cache_analytics["size_usage"][cache_type] = 0
                
                logger.info(f"Invalidated {len(keys)} entries from {cache_type} cache")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to invalidate cache type: {e}")
            return False
    
    async def clear_all(self) -> bool:
        """Clear all SEO cache entries"""
        try:
            pattern = "seo:*"
            keys = await self.redis_service.keys(pattern)
            
            if keys:
                for key in keys:
                    await self.redis_service.delete(key)
                
                # Reset all analytics
                for cache_type in self.cache_analytics["size_usage"]:
                    self.cache_analytics["size_usage"][cache_type] = 0
                
                logger.info(f"Cleared all {len(keys)} SEO cache entries")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear all cache: {e}")
            return False
    
    async def get_cache_stats(self) -> CacheStats:
        """Get comprehensive cache statistics"""
        try:
            total_entries = 0
            total_size_bytes = 0
            
            # Count entries and calculate total size
            for cache_type in self.cache_policies.keys():
                pattern = f"seo:{cache_type}:*"
                keys = await self.redis_service.keys(pattern)
                
                # Filter out metadata keys
                cache_keys = [k for k in keys if not k.endswith(':metadata')]
                total_entries += len(cache_keys)
                total_size_bytes += self.cache_analytics["size_usage"][cache_type]
            
            # Calculate hit rates
            total_hits = sum(self.cache_analytics["hits"].values())
            total_misses = sum(self.cache_analytics["misses"].values())
            total_requests = total_hits + total_misses
            
            hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0
            miss_rate = (total_misses / total_requests * 100) if total_requests > 0 else 0
            
            # Calculate average access time
            all_access_times = []
            for times in self.cache_analytics["access_times"].values():
                all_access_times.extend(times)
            
            average_access_time = sum(all_access_times) / len(all_access_times) if all_access_times else 0
            
            # Calculate cache efficiency (hit rate weighted by size)
            cache_efficiency = hit_rate * (1 - (total_size_bytes / (1024 * 1024 * 1000)))  # Normalize to 1GB
            
            stats = CacheStats(
                total_entries=total_entries,
                total_size_bytes=total_size_bytes,
                hit_rate=round(hit_rate, 2),
                miss_rate=round(miss_rate, 2),
                eviction_count=sum(self.cache_analytics["evictions"].values()),
                average_access_time=round(average_access_time, 4),
                cache_efficiency=round(cache_efficiency, 2),
                last_updated=datetime.now()
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return CacheStats(
                total_entries=0,
                total_size_bytes=0,
                hit_rate=0.0,
                miss_rate=0.0,
                eviction_count=0,
                average_access_time=0.0,
                cache_efficiency=0.0,
                last_updated=datetime.now()
            )
    
    async def optimize_cache(self) -> Dict[str, Any]:
        """Optimize cache performance"""
        try:
            optimization_results = {
                "timestamp": datetime.now().isoformat(),
                "actions_taken": [],
                "performance_improvements": {}
            }
            
            # Analyze cache performance
            stats = await self.get_cache_stats()
            
            # Optimize based on hit rates
            for cache_type in self.cache_policies.keys():
                hit_rate = self.cache_analytics["hits"][cache_type]
                miss_rate = self.cache_analytics["misses"][cache_type]
                total_requests = hit_rate + miss_rate
                
                if total_requests > 0:
                    current_hit_rate = hit_rate / total_requests
                    
                    if current_hit_rate < 0.5:  # Low hit rate
                        # Increase TTL for better retention
                        policy = self.cache_policies[cache_type]
                        new_ttl = min(policy.default_ttl * 2, 3600 * 48)  # Double TTL, max 48 hours
                        
                        optimization_results["actions_taken"].append(
                            f"Increased TTL for {cache_type} from {policy.default_ttl}s to {new_ttl}s"
                        )
                        
                        # Update policy
                        policy.default_ttl = new_ttl
                    
                    elif current_hit_rate > 0.9:  # Very high hit rate
                        # Consider reducing TTL to save memory
                        policy = self.cache_policies[cache_type]
                        new_ttl = max(policy.default_ttl // 2, 3600 * 2)  # Halve TTL, min 2 hours
                        
                        optimization_results["actions_taken"].append(
                            f"Reduced TTL for {cache_type} from {policy.default_ttl}s to {new_ttl}s"
                        )
                        
                        # Update policy
                        policy.default_ttl = new_ttl
            
            # Memory optimization
            if stats.total_size_bytes > 500 * 1024 * 1024:  # 500MB
                # Aggressive eviction for large caches
                for cache_type in self.cache_policies.keys():
                    await self._evict_cache_entries(cache_type, self.cache_policies[cache_type], "memory")
                
                optimization_results["actions_taken"].append("Performed aggressive cache eviction due to high memory usage")
            
            # Update performance metrics
            self.performance_metrics["last_optimization"] = datetime.now()
            
            # Get updated stats
            new_stats = await self.get_cache_stats()
            
            optimization_results["performance_improvements"] = {
                "hit_rate_change": new_stats.hit_rate - stats.hit_rate,
                "memory_reduction": stats.total_size_bytes - new_stats.total_size_bytes,
                "efficiency_improvement": new_stats.cache_efficiency - stats.cache_efficiency
            }
            
            logger.info("Cache optimization completed")
            return optimization_results
            
        except Exception as e:
            logger.error(f"Failed to optimize cache: {e}")
            return {"error": str(e)}
    
    async def warm_cache(self, cache_type: str, warm_data: List[Tuple[Any, ...]]) -> Dict[str, Any]:
        """
        Warm cache with frequently accessed data
        
        Args:
            cache_type: Type of cache to warm
            warm_data: List of data tuples to cache
        
        Returns:
            Warming results
        """
        try:
            if cache_type not in self.warming_strategies:
                return {"error": f"No warming strategy for {cache_type}"}
            
            warming_strategy = self.warming_strategies[cache_type]
            results = await warming_strategy(warm_data)
            
            logger.info(f"Cache warming completed for {cache_type}: {len(warm_data)} entries")
            return results
            
        except Exception as e:
            logger.error(f"Failed to warm cache: {e}")
            return {"error": str(e)}
    
    async def _warm_keyword_cache(self, warm_data: List[Tuple[Any, ...]]) -> Dict[str, Any]:
        """Warm keyword data cache"""
        try:
            results = {
                "cache_type": "keyword_data",
                "entries_warmed": 0,
                "errors": []
            }
            
            for data_tuple in warm_data:
                try:
                    # Assuming data_tuple contains (keyword, country, data)
                    if len(data_tuple) >= 3:
                        keyword, country, data = data_tuple[0], data_tuple[1], data_tuple[2]
                        await self.set("keyword_data", data, None, keyword, country)
                        results["entries_warmed"] += 1
                except Exception as e:
                    results["errors"].append(str(e))
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to warm keyword cache: {e}")
            return {"error": str(e)}
    
    async def _warm_clustering_cache(self, warm_data: List[Tuple[Any, ...]]) -> Dict[str, Any]:
        """Warm clustering cache"""
        try:
            results = {
                "cache_type": "clustering",
                "entries_warmed": 0,
                "errors": []
            }
            
            for data_tuple in warm_data:
                try:
                    # Assuming data_tuple contains (keywords, algorithm, parameters, data)
                    if len(data_tuple) >= 4:
                        keywords, algorithm, parameters, data = data_tuple[0], data_tuple[1], data_tuple[2], data_tuple[3]
                        await self.set("clustering", data, None, keywords, algorithm, parameters)
                        results["entries_warmed"] += 1
                except Exception as e:
                    results["errors"].append(str(e))
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to warm clustering cache: {e}")
            return {"error": str(e)}
    
    async def _warm_suggestions_cache(self, warm_data: List[Tuple[Any, ...]]) -> Dict[str, Any]:
        """Warm suggestions cache"""
        try:
            results = {
                "cache_type": "suggestions",
                "entries_warmed": 0,
                "errors": []
            }
            
            for data_tuple in warm_data:
                try:
                    # Assuming data_tuple contains (seed_keyword, context, data)
                    if len(data_tuple) >= 3:
                        seed_keyword, context, data = data_tuple[0], data_tuple[1], data_tuple[2]
                        await self.set("suggestions", data, None, seed_keyword, context)
                        results["entries_warmed"] += 1
                except Exception as e:
                    results["errors"].append(str(e))
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to warm suggestions cache: {e}")
            return {"error": str(e)}
    
    async def export_cache_analytics(self, format: str = "json") -> str:
        """
        Export cache analytics data
        
        Args:
            format: Export format (json, csv)
        
        Returns:
            Exported analytics data
        """
        try:
            if format.lower() == "json":
                export_data = {
                    "cache_analytics": dict(self.cache_analytics),
                    "performance_metrics": self.performance_metrics,
                    "cache_policies": {
                        cache_type: {
                            "max_size_mb": policy.max_size_mb,
                            "max_entries": policy.max_entries,
                            "default_ttl": policy.default_ttl,
                            "eviction_policy": policy.eviction_policy
                        }
                        for cache_type, policy in self.cache_policies.items()
                    },
                    "export_timestamp": datetime.now().isoformat()
                }
                
                return json.dumps(export_data, indent=2, default=str)
                
            elif format.lower() == "csv":
                # Create CSV with key metrics
                csv_lines = [
                    "cache_type,hits,misses,evictions,size_usage_mb,hit_rate"
                ]
                
                for cache_type in self.cache_policies.keys():
                    hits = self.cache_analytics["hits"][cache_type]
                    misses = self.cache_analytics["misses"][cache_type]
                    evictions = self.cache_analytics["evictions"][cache_type]
                    size_mb = self.cache_analytics["size_usage"][cache_type] / (1024 * 1024)
                    
                    total_requests = hits + misses
                    hit_rate = (hits / total_requests * 100) if total_requests > 0 else 0
                    
                    csv_lines.append(
                        f"{cache_type},{hits},{misses},{evictions},{size_mb:.2f},{hit_rate:.2f}"
                    )
                
                return "\n".join(csv_lines)
                
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to export cache analytics: {e}")
            return json.dumps({"error": str(e)})
    
    async def get_cache_health(self) -> Dict[str, Any]:
        """Get cache health status"""
        try:
            health_status = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "issues": [],
                "recommendations": []
            }
            
            # Check Redis connectivity
            try:
                await self.redis_service.ping()
                health_status["redis_connected"] = True
            except Exception:
                health_status["redis_connected"] = False
                health_status["status"] = "unhealthy"
                health_status["issues"].append("Redis connection failed")
                health_status["recommendations"].append("Check Redis service status")
            
            # Check cache performance
            stats = await self.get_cache_stats()
            
            if stats.hit_rate < 50:
                health_status["status"] = "degraded"
                health_status["issues"].append(f"Low cache hit rate: {stats.hit_rate}%")
                health_status["recommendations"].append("Consider increasing TTL or warming cache")
            
            if stats.total_size_bytes > 1000 * 1024 * 1024:  # 1GB
                health_status["status"] = "degraded"
                health_status["issues"].append("High memory usage")
                health_status["recommendations"].append("Consider cache eviction or size limits")
            
            # Check for excessive evictions
            if stats.eviction_count > 100:
                health_status["status"] = "degraded"
                health_status["issues"].append("High eviction count")
                health_status["recommendations"].append("Review cache size policies")
            
            return health_status
            
        except Exception as e:
            logger.error(f"Failed to get cache health: {e}")
            return {
                "status": "unknown",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }