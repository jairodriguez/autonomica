"""
Redis Service
Handles Redis operations for caching, queues, and session management
"""

import json
import logging
from typing import Any, Optional, List, Dict, Union
import redis.asyncio as redis
from datetime import timedelta

logger = logging.getLogger(__name__)

class RedisService:
    """Service for Redis operations"""
    
    def __init__(self, redis_url: str = None):
        """Initialize Redis connection"""
        self.redis_url = redis_url or "redis://localhost:6379"
        self.redis_client = None
        self._connect()
    
    def _connect(self):
        """Establish Redis connection"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    async def is_connected(self) -> bool:
        """Check if Redis is connected"""
        if not self.redis_client:
            return False
        
        try:
            await self.redis_client.ping()
            return True
        except Exception:
            return False
    
    async def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        try:
            if not await self.is_connected():
                return None
            return await self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Failed to get key {key}: {e}")
            return None
    
    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set key-value pair with optional expiration"""
        try:
            if not await self.is_connected():
                return False
            
            if ex:
                return await self.redis_client.setex(key, ex, value)
            else:
                return await self.redis_client.set(key, value)
        except Exception as e:
            logger.error(f"Failed to set key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key"""
        try:
            if not await self.is_connected():
                return False
            result = await self.redis_client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Failed to delete key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            if not await self.is_connected():
                return False
            result = await self.redis_client.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"Failed to check existence of key {key}: {e}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for key"""
        try:
            if not await self.is_connected():
                return False
            return await self.redis_client.expire(key, seconds)
        except Exception as e:
            logger.error(f"Failed to set expiration for key {key}: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """Get time to live for key"""
        try:
            if not await self.is_connected():
                return -2
            return await self.redis_client.ttl(key)
        except Exception as e:
            logger.error(f"Failed to get TTL for key {key}: {e}")
            return -2
    
    # List operations
    async def lpush(self, key: str, value: str) -> bool:
        """Push value to left of list"""
        try:
            if not await self.is_connected():
                return False
            result = await self.redis_client.lpush(key, value)
            return result > 0
        except Exception as e:
            logger.error(f"Failed to lpush to {key}: {e}")
            return False
    
    async def rpush(self, key: str, value: str) -> bool:
        """Push value to right of list"""
        try:
            if not await self.is_connected():
                return False
            result = await self.redis_client.rpush(key, value)
            return result > 0
        except Exception as e:
            logger.error(f"Failed to rpush to {key}: {e}")
            return False
    
    async def lpop(self, key: str) -> Optional[str]:
        """Pop value from left of list"""
        try:
            if not await self.is_connected():
                return None
            return await self.redis_client.lpop(key)
        except Exception as e:
            logger.error(f"Failed to lpop from {key}: {e}")
            return None
    
    async def rpop(self, key: str) -> Optional[str]:
        """Pop value from right of list"""
        try:
            if not await self.is_connected():
                return None
            return await self.redis_client.rpop(key)
        except Exception as e:
            logger.error(f"Failed to rpop from {key}: {e}")
            return None
    
    async def lrange(self, key: str, start: int, stop: int) -> List[str]:
        """Get range of values from list"""
        try:
            if not await self.is_connected():
                return []
            return await self.redis_client.lrange(key, start, stop)
        except Exception as e:
            logger.error(f"Failed to lrange from {key}: {e}")
            return []
    
    async def llen(self, key: str) -> int:
        """Get length of list"""
        try:
            if not await self.is_connected():
                return 0
            return await self.redis_client.llen(key)
        except Exception as e:
            logger.error(f"Failed to get length of list {key}: {e}")
            return 0
    
    # Sorted set operations
    async def zadd(self, key: str, score: float, member: str) -> bool:
        """Add member to sorted set with score"""
        try:
            if not await self.is_connected():
                return False
            result = await self.redis_client.zadd(key, {member: score})
            return result > 0
        except Exception as e:
            logger.error(f"Failed to zadd to {key}: {e}")
            return False
    
    async def zrem(self, key: str, member: str) -> bool:
        """Remove member from sorted set"""
        try:
            if not await self.is_connected():
                return False
            result = await self.redis_client.zrem(key, member)
            return result > 0
        except Exception as e:
            logger.error(f"Failed to zrem from {key}: {e}")
            return False
    
    async def zrange(self, key: str, start: int, stop: int, withscores: bool = False) -> Union[List[str], List[tuple]]:
        """Get range of members from sorted set"""
        try:
            if not await self.is_connected():
                return []
            return await self.redis_client.zrange(key, start, stop, withscores=withscores)
        except Exception as e:
            logger.error(f"Failed to zrange from {key}: {e}")
            return []
    
    async def zrangebyscore(self, key: str, min_score: float, max_score: float) -> List[str]:
        """Get members with scores in range"""
        try:
            if not await self.is_connected():
                return []
            return await self.redis_client.zrangebyscore(key, min_score, max_score)
        except Exception as e:
            logger.error(f"Failed to zrangebyscore from {key}: {e}")
            return []
    
    async def zcard(self, key: str) -> int:
        """Get cardinality of sorted set"""
        try:
            if not await self.is_connected():
                return 0
            return await self.redis_client.zcard(key)
        except Exception as e:
            logger.error(f"Failed to get cardinality of sorted set {key}: {e}")
            return 0
    
    # Hash operations
    async def hset(self, key: str, field: str, value: str) -> bool:
        """Set field in hash"""
        try:
            if not await self.is_connected():
                return False
            result = await self.redis_client.hset(key, field, value)
            return result >= 0
        except Exception as e:
            logger.error(f"Failed to hset {field} in {key}: {e}")
            return False
    
    async def hget(self, key: str, field: str) -> Optional[str]:
        """Get field from hash"""
        try:
            if not await self.is_connected():
                return None
            return await self.redis_client.hget(key, field)
        except Exception as e:
            logger.error(f"Failed to hget {field} from {key}: {e}")
            return None
    
    async def hgetall(self, key: str) -> Dict[str, str]:
        """Get all fields from hash"""
        try:
            if not await self.is_connected():
                return {}
            return await self.redis_client.hgetall(key)
        except Exception as e:
            logger.error(f"Failed to hgetall from {key}: {e}")
            return {}
    
    async def hdel(self, key: str, field: str) -> bool:
        """Delete field from hash"""
        try:
            if not await self.is_connected():
                return False
            result = await self.redis_client.hdel(key, field)
            return result > 0
        except Exception as e:
            logger.error(f"Failed to hdel {field} from {key}: {e}")
            return False
    
    # JSON operations
    async def set_json(self, key: str, data: Dict[str, Any], ex: Optional[int] = None) -> bool:
        """Set JSON data"""
        try:
            json_data = json.dumps(data)
            return await self.set(key, json_data, ex)
        except Exception as e:
            logger.error(f"Failed to set JSON for key {key}: {e}")
            return False
    
    async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Get JSON data"""
        try:
            data = await self.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get JSON for key {key}: {e}")
            return None
    
    # Queue operations
    async def enqueue(self, queue_name: str, data: Dict[str, Any]) -> bool:
        """Add item to queue"""
        try:
            json_data = json.dumps(data)
            return await self.lpush(queue_name, json_data)
        except Exception as e:
            logger.error(f"Failed to enqueue to {queue_name}: {e}")
            return False
    
    async def dequeue(self, queue_name: str) -> Optional[Dict[str, Any]]:
        """Remove and return item from queue"""
        try:
            data = await self.rpop(queue_name)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to dequeue from {queue_name}: {e}")
            return None
    
    async def peek_queue(self, queue_name: str, count: int = 1) -> List[Dict[str, Any]]:
        """Peek at items in queue without removing them"""
        try:
            items = await self.lrange(queue_name, 0, count - 1)
            return [json.loads(item) for item in items]
        except Exception as e:
            logger.error(f"Failed to peek queue {queue_name}: {e}")
            return []
    
    async def get_queue_length(self, queue_name: str) -> int:
        """Get length of queue"""
        return await self.llen(queue_name)
    
    # Health check
    async def health_check(self) -> Dict[str, Any]:
        """Check Redis health"""
        try:
            is_connected = await self.is_connected()
            if is_connected:
                info = await self.redis_client.info()
                return {
                    "status": "healthy",
                    "connected": True,
                    "version": info.get("redis_version", "unknown"),
                    "used_memory": info.get("used_memory_human", "unknown"),
                    "connected_clients": info.get("connected_clients", 0)
                }
            else:
                return {
                    "status": "unhealthy",
                    "connected": False,
                    "error": "Cannot connect to Redis"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e)
            }
    
    async def close(self):
        """Close Redis connection"""
        try:
            if self.redis_client:
                await self.redis_client.close()
                logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Failed to close Redis connection: {e}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close() 