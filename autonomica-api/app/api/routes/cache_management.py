"""
Cache Management API Routes
Provides endpoints for monitoring and controlling the caching system
"""
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime

from app.auth.clerk_middleware import get_current_user, ClerkUser
from app.services.cache_service import (
    create_cache_service,
    CacheService,
    CacheConfig,
    CacheLevel,
    CacheStrategy
)

router = APIRouter(prefix="/api/cache", tags=["Cache Management"])

class CacheConfigRequest(BaseModel):
    """Request to update cache configuration"""
    default_ttl: Optional[int] = Field(None, description="Default TTL in seconds")
    max_memory_mb: Optional[int] = Field(None, description="Maximum memory usage in MB")
    compression_enabled: Optional[bool] = Field(None, description="Enable compression")
    redis_enabled: Optional[bool] = Field(None, description="Enable Redis")
    redis_url: Optional[str] = Field(None, description="Redis connection URL")
    redis_db: Optional[int] = Field(None, description="Redis database number")
    redis_password: Optional[str] = Field(None, description="Redis password")
    redis_ssl: Optional[bool] = Field(None, description="Enable Redis SSL")
    fallback_to_memory: Optional[bool] = Field(None, description="Fallback to memory cache")
    cache_strategy: Optional[str] = Field(None, description="Cache strategy (lru, ttl, hybrid)")
    lru_max_size: Optional[int] = Field(None, description="LRU cache max size")
    cleanup_interval: Optional[int] = Field(None, description="Cleanup interval in seconds")

class CacheConfigResponse(BaseModel):
    """Cache configuration response"""
    default_ttl: int
    max_memory_mb: int
    compression_enabled: bool
    redis_enabled: bool
    redis_url: str
    redis_db: int
    redis_ssl: bool
    fallback_to_memory: bool
    cache_strategy: str
    lru_max_size: int
    cleanup_interval: int
    redis_connected: bool

class CacheStatsResponse(BaseModel):
    """Cache statistics response"""
    total_requests: int
    cache_hits: int
    cache_misses: int
    hit_rate: float
    total_size_bytes: int
    entries_count: int
    compression_savings_bytes: int
    compression_savings_percent: float
    eviction_count: int
    last_cleanup: Optional[str]

class CacheEntryInfo(BaseModel):
    """Information about a cache entry"""
    key: str
    level: str
    identifier: str
    created_at: str
    expires_at: Optional[str]
    access_count: int
    last_accessed: str
    size_bytes: int
    compression_ratio: float

class CacheClearRequest(BaseModel):
    """Request to clear cache entries"""
    level: Optional[str] = Field(None, description="Cache level to clear (optional)")
    pattern: Optional[str] = Field(None, description="Pattern to match keys (optional)")

class CacheClearResponse(BaseModel):
    """Response for cache clear operation"""
    success: bool
    cleared_entries: int
    message: str

class CacheHealthResponse(BaseModel):
    """Cache health check response"""
    status: str
    redis_connected: bool
    memory_cache_size: int
    total_entries: int
    last_cleanup: Optional[str]
    timestamp: str

_cache_service_instance: Optional[CacheService] = None

async def get_cache_service() -> CacheService:
    """Get or create the global cache service instance"""
    global _cache_service_instance
    if _cache_service_instance is None:
        _cache_service_instance = await create_cache_service()
    return _cache_service_instance

@router.get("/health", response_model=CacheHealthResponse)
async def cache_health_check(
    current_user: ClerkUser = Depends(get_current_user),
    cache_service: CacheService = Depends(get_cache_service)
):
    """Health check for the cache service"""
    try:
        stats = await cache_service.get_stats()
        
        return CacheHealthResponse(
            status="healthy" if cache_service.redis_connected or cache_service.memory_cache else "degraded",
            redis_connected=cache_service.redis_connected,
            memory_cache_size=len(cache_service.memory_cache),
            total_entries=stats.entries_count,
            last_cleanup=stats.last_cleanup.isoformat() if stats.last_cleanup else None,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        return CacheHealthResponse(
            status="unhealthy",
            redis_connected=False,
            memory_cache_size=0,
            total_entries=0,
            last_cleanup=None,
            timestamp=datetime.now().isoformat()
        )

@router.get("/stats", response_model=CacheStatsResponse)
async def get_cache_statistics(
    current_user: ClerkUser = Depends(get_current_user),
    cache_service: CacheService = Depends(get_cache_service)
):
    """Get cache performance statistics"""
    try:
        stats = await cache_service.get_stats()
        
        return CacheStatsResponse(
            total_requests=stats.total_requests,
            cache_hits=stats.cache_hits,
            cache_misses=stats.cache_misses,
            hit_rate=stats.hit_rate,
            total_size_bytes=stats.total_size_bytes,
            entries_count=stats.entries_count,
            compression_savings_bytes=stats.compression_savings_bytes,
            compression_savings_percent=stats.compression_savings_percent,
            eviction_count=stats.eviction_count,
            last_cleanup=stats.last_cleanup.isoformat() if stats.last_cleanup else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cache stats: {str(e)}")

@router.get("/config", response_model=CacheConfigResponse)
async def get_cache_configuration(
    current_user: ClerkUser = Depends(get_current_user),
    cache_service: CacheService = Depends(get_cache_service)
):
    """Get current cache configuration"""
    try:
        config = cache_service.config
        
        return CacheConfigResponse(
            default_ttl=config.default_ttl,
            max_memory_mb=config.max_memory_mb,
            compression_enabled=config.compression_enabled,
            redis_enabled=config.redis_enabled,
            redis_url=config.redis_url,
            redis_db=config.redis_db,
            redis_ssl=config.redis_ssl,
            fallback_to_memory=config.fallback_to_memory,
            cache_strategy=config.cache_strategy.value,
            lru_max_size=config.lru_max_size,
            cleanup_interval=config.cleanup_interval,
            redis_connected=cache_service.redis_connected
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cache config: {str(e)}")

@router.put("/config", response_model=CacheConfigResponse)
async def update_cache_configuration(
    request: CacheConfigRequest,
    current_user: ClerkUser = Depends(get_current_user),
    cache_service: CacheService = Depends(get_cache_service)
):
    """Update cache configuration"""
    try:
        config = cache_service.config
        
        # Update configuration fields
        if request.default_ttl is not None:
            config.default_ttl = request.default_ttl
        if request.max_memory_mb is not None:
            config.max_memory_mb = request.max_memory_mb
        if request.compression_enabled is not None:
            config.compression_enabled = request.compression_enabled
        if request.redis_enabled is not None:
            config.redis_enabled = request.redis_enabled
        if request.redis_url is not None:
            config.redis_url = request.redis_url
        if request.redis_db is not None:
            config.redis_db = request.redis_db
        if request.redis_password is not None:
            config.redis_password = request.redis_password
        if request.redis_ssl is not None:
            config.redis_ssl = request.redis_ssl
        if request.fallback_to_memory is not None:
            config.fallback_to_memory = request.fallback_to_memory
        if request.cache_strategy is not None:
            try:
                config.cache_strategy = CacheStrategy(request.cache_strategy)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid cache strategy: {request.cache_strategy}")
        if request.lru_max_size is not None:
            config.lru_max_size = request.lru_max_size
        if request.cleanup_interval is not None:
            config.cleanup_interval = request.cleanup_interval
        
        # Reconnect to Redis if settings changed
        if request.redis_enabled is not None or request.redis_url is not None:
            await cache_service._connect_redis()
        
        return await get_cache_configuration(current_user, cache_service)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating cache config: {str(e)}")

@router.get("/levels")
async def get_cache_levels(
    current_user: ClerkUser = Depends(get_current_user)
):
    """Get available cache levels"""
    try:
        levels = []
        for level in CacheLevel:
            levels.append({
                "value": level.value,
                "name": level.value.replace("_", " ").title(),
                "description": f"Cache level for {level.value.replace('_', ' ')} data"
            })
        
        return {
            "levels": levels,
            "total_levels": len(levels)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cache levels: {str(e)}")

@router.get("/entries")
async def list_cache_entries(
    level: Optional[str] = Query(None, description="Filter by cache level"),
    limit: int = Query(100, description="Maximum number of entries to return", ge=1, le=1000),
    current_user: ClerkUser = Depends(get_current_user),
    cache_service: CacheService = Depends(get_cache_service)
):
    """List cache entries with optional filtering"""
    try:
        entries = []
        count = 0
        
        # Get entries from memory cache
        for key, entry in cache_service.memory_cache.items():
            if count >= limit:
                break
                
            # Filter by level if specified
            if level and entry.metadata.get('level') != level:
                continue
            
            entries.append(CacheEntryInfo(
                key=key,
                level=entry.metadata.get('level', 'unknown'),
                identifier=entry.metadata.get('identifier', 'unknown'),
                created_at=entry.created_at.isoformat(),
                expires_at=entry.expires_at.isoformat() if entry.expires_at else None,
                access_count=entry.access_count,
                last_accessed=entry.last_accessed.isoformat(),
                size_bytes=entry.size_bytes,
                compression_ratio=entry.compression_ratio
            ))
            count += 1
        
        return {
            "entries": entries,
            "total_returned": len(entries),
            "total_available": len(cache_service.memory_cache),
            "level_filter": level
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing cache entries: {str(e)}")

@router.post("/clear", response_model=CacheClearResponse)
async def clear_cache(
    request: CacheClearRequest,
    current_user: ClerkUser = Depends(get_current_user),
    cache_service: CacheService = Depends(get_cache_service)
):
    """Clear cache entries"""
    try:
        if request.level:
            # Clear specific level
            try:
                cache_level = CacheLevel(request.level)
                success = await cache_service.clear(cache_level)
                if success:
                    return CacheClearResponse(
                        success=True,
                        cleared_entries=0,  # Count not available from clear method
                        message=f"Cache level '{request.level}' cleared successfully"
                    )
                else:
                    raise HTTPException(status_code=500, detail="Failed to clear cache")
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid cache level: {request.level}")
        else:
            # Clear all cache
            success = await cache_service.clear()
            if success:
                return CacheClearResponse(
                    success=True,
                    cleared_entries=0,  # Count not available from clear method
                    message="All cache entries cleared successfully"
                )
            else:
                raise HTTPException(status_code=500, detail="Failed to clear cache")
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")

@router.delete("/entries/{level}/{identifier}")
async def delete_cache_entry(
    level: str,
    identifier: str,
    current_user: ClerkUser = Depends(get_current_user),
    cache_service: CacheService = Depends(get_cache_service)
):
    """Delete a specific cache entry"""
    try:
        # Validate cache level
        try:
            cache_level = CacheLevel(level)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid cache level: {level}")
        
        # Delete the entry
        success = await cache_service.delete(cache_level, identifier)
        
        if success:
            return {"message": f"Cache entry '{identifier}' in level '{level}' deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete cache entry")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting cache entry: {str(e)}")

@router.post("/entries/{level}/{identifier}/refresh")
async def refresh_cache_entry(
    level: str,
    identifier: str,
    current_user: ClerkUser = Depends(get_current_user),
    cache_service: CacheService = Depends(get_cache_service)
):
    """Refresh a cache entry (delete and allow re-creation)"""
    try:
        # Validate cache level
        try:
            cache_level = CacheLevel(level)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid cache level: {level}")
        
        # Delete the entry to force refresh
        success = await cache_service.delete(cache_level, identifier)
        
        if success:
            return {"message": f"Cache entry '{identifier}' in level '{level}' refreshed successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to refresh cache entry")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refreshing cache entry: {str(e)}")

@router.get("/performance")
async def get_cache_performance(
    current_user: ClerkUser = Depends(get_current_user),
    cache_service: CacheService = Depends(get_cache_service)
):
    """Get cache performance metrics"""
    try:
        stats = await cache_service.get_stats()
        
        # Calculate performance metrics
        total_requests = stats.total_requests
        hit_rate = stats.hit_rate
        avg_response_time = 0.0  # Not tracked in current implementation
        memory_efficiency = (stats.total_size_bytes / (1024 * 1024)) / cache_service.config.max_memory_mb if cache_service.config.max_memory_mb > 0 else 0
        
        return {
            "performance_metrics": {
                "total_requests": total_requests,
                "hit_rate_percent": hit_rate,
                "miss_rate_percent": 100 - hit_rate,
                "memory_efficiency_percent": min(memory_efficiency * 100, 100),
                "compression_savings_percent": stats.compression_savings_percent,
                "eviction_rate": stats.eviction_count / max(total_requests, 1) * 100
            },
            "recommendations": _generate_performance_recommendations(stats, cache_service.config),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting performance metrics: {str(e)}")

def _generate_performance_recommendations(stats, config) -> List[str]:
    """Generate performance improvement recommendations"""
    recommendations = []
    
    if stats.hit_rate < 50:
        recommendations.append("Consider increasing cache TTL to improve hit rate")
    
    if stats.eviction_count > stats.total_requests * 0.1:
        recommendations.append("Consider increasing LRU cache size to reduce evictions")
    
    if stats.compression_savings_percent > 20:
        recommendations.append("Compression is working well, consider enabling for more data types")
    
    if not config.redis_enabled and stats.total_size_bytes > 50 * 1024 * 1024:  # 50MB
        recommendations.append("Consider enabling Redis for better memory management")
    
    if stats.hit_rate > 80:
        recommendations.append("Cache performance is excellent")
    
    return recommendations
