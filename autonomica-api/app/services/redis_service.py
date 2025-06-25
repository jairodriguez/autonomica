"""
Redis Service Module for Autonomica

Supports both traditional Redis and Vercel KV (Redis-compatible)
Implements user-scoped caching and task queue functionality with Clerk authentication.
"""

import json
import os
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import asyncio
import logging

try:
    import redis.asyncio as redis
    from redis.asyncio import Redis
except ImportError:
    # Fallback if redis package not available
    redis = None
    Redis = None

import httpx

logger = logging.getLogger(__name__)


class CacheKey:
    """Helper class for generating consistent cache keys with user scoping."""
    
    @staticmethod
    def user_scoped(user_id: str, key: str) -> str:
        """Generate user-scoped cache key."""
        return f"user:{user_id}:{key}"
    
    @staticmethod
    def agent_response(user_id: str, agent_type: str) -> str:
        """Generate cache key for agent responses."""
        return f"user:{user_id}:agent:{agent_type}:last_response"
    
    @staticmethod
    def agent_state(user_id: str, agent_id: str) -> str:
        """Generate cache key for agent state."""
        return f"user:{user_id}:agent_state:{agent_id}"
    
    @staticmethod
    def chat_session(user_id: str, session_id: str) -> str:
        """Generate cache key for chat sessions."""
        return f"user:{user_id}:chat:{session_id}"
    
    @staticmethod
    def task_queue(user_id: str) -> str:
        """Generate cache key for user task queue."""
        return f"user:{user_id}:tasks"
    
    @staticmethod
    def rate_limit(user_id: str) -> str:
        """Generate cache key for rate limiting."""
        return f"user:{user_id}:rate_limit"


class VercelKVClient:
    """Vercel KV client using REST API."""
    
    def __init__(self, url: str, token: str):
        self.base_url = url.rstrip('/')
        self.token = token
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {token}"},
            timeout=30.0
        )
    
    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set a key-value pair with optional expiration."""
        try:
            data = {"key": key, "value": value}
            if ex:
                data["ex"] = ex
            
            response = await self.client.post(f"{self.base_url}/set", json=data)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Vercel KV set error: {e}")
            return False
    
    async def get(self, key: str) -> Optional[str]:
        """Get a value by key."""
        try:
            response = await self.client.get(f"{self.base_url}/get/{key}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json().get("result")
        except Exception as e:
            logger.error(f"Vercel KV get error: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete a key."""
        try:
            response = await self.client.delete(f"{self.base_url}/del/{key}")
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Vercel KV delete error: {e}")
            return False
    
    async def lpush(self, key: str, value: str) -> bool:
        """Push to left of list."""
        try:
            data = {"key": key, "value": value}
            response = await self.client.post(f"{self.base_url}/lpush", json=data)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Vercel KV lpush error: {e}")
            return False
    
    async def rpop(self, key: str) -> Optional[str]:
        """Pop from right of list."""
        try:
            response = await self.client.post(f"{self.base_url}/rpop", json={"key": key})
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json().get("result")
        except Exception as e:
            logger.error(f"Vercel KV rpop error: {e}")
            return None
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


class RedisService:
    """
    Redis service that supports both traditional Redis and Vercel KV.
    
    Automatically detects which backend to use based on environment variables.
    Provides user-scoped caching and task queue functionality.
    """
    
    def __init__(self):
        self.client: Optional[Any] = None  # Union[Redis, VercelKVClient] when properly typed
        self.is_vercel_kv = False
        self._initialized = False
    
    async def initialize(self):
        """Initialize the Redis client based on configuration."""
        if self._initialized:
            return
        
        # Check if Vercel KV configuration is available
        kv_url = os.getenv("KV_REST_API_URL")
        kv_token = os.getenv("KV_REST_API_TOKEN")
        
        if kv_url and kv_token:
            # Use Vercel KV
            logger.info("Initializing Vercel KV client")
            self.client = VercelKVClient(kv_url, kv_token)
            self.is_vercel_kv = True
        else:
            # Use traditional Redis
            if redis is None:
                raise RuntimeError("Redis package not available. Please install redis package or configure Vercel KV.")
            logger.info("Initializing traditional Redis client")
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.client = redis.from_url(redis_url, decode_responses=True)
            self.is_vercel_kv = False
        
        self._initialized = True
        logger.info(f"Redis service initialized with {'Vercel KV' if self.is_vercel_kv else 'traditional Redis'}")
    
    async def close(self):
        """Close the Redis client."""
        if self.client:
            if self.is_vercel_kv:
                await self.client.close()
            else:
                await self.client.close()
            self._initialized = False
    
    # Cache Operations
    
    async def cache_set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set a cache value with TTL (time to live in seconds)."""
        await self.initialize()
        if not self.client:
            logger.error("Redis client not initialized")
            return False
            
        try:
            json_value = json.dumps(value) if not isinstance(value, str) else value
            
            if self.is_vercel_kv:
                return await self.client.set(key, json_value, ex=ttl)
            else:
                return await self.client.set(key, json_value, ex=ttl)
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def cache_get(self, key: str) -> Optional[Any]:
        """Get a cache value."""
        await self.initialize()
        try:
            if self.is_vercel_kv:
                value = await self.client.get(key)
            else:
                value = await self.client.get(key)
            
            if value is None:
                return None
            
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def cache_delete(self, key: str) -> bool:
        """Delete a cache key."""
        await self.initialize()
        try:
            if self.is_vercel_kv:
                return await self.client.delete(key)
            else:
                return bool(await self.client.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    # User-Scoped Cache Operations
    
    async def cache_user_data(self, user_id: str, key: str, data: Any, ttl: int = 3600) -> bool:
        """Cache data for a specific user."""
        cache_key = CacheKey.user_scoped(user_id, key)
        return await self.cache_set(cache_key, data, ttl)
    
    async def get_user_data(self, user_id: str, key: str) -> Optional[Any]:
        """Get cached data for a specific user."""
        cache_key = CacheKey.user_scoped(user_id, key)
        return await self.cache_get(cache_key)
    
    async def delete_user_data(self, user_id: str, key: str) -> bool:
        """Delete cached data for a specific user."""
        cache_key = CacheKey.user_scoped(user_id, key)
        return await self.cache_delete(cache_key)
    
    # Agent State Management
    
    async def cache_agent_response(self, user_id: str, agent_type: str, response: Dict[str, Any], ttl: int = 1800) -> bool:
        """Cache the last agent response for a user."""
        cache_key = CacheKey.agent_response(user_id, agent_type)
        cached_data = {
            "response": response,
            "timestamp": datetime.utcnow().isoformat(),
            "agent_type": agent_type
        }
        return await self.cache_set(cache_key, cached_data, ttl)
    
    async def get_agent_response(self, user_id: str, agent_type: str) -> Optional[Dict[str, Any]]:
        """Get the last cached agent response for a user."""
        cache_key = CacheKey.agent_response(user_id, agent_type)
        return await self.cache_get(cache_key)
    
    async def cache_agent_state(self, user_id: str, agent_id: str, state: Dict[str, Any], ttl: int = 7200) -> bool:
        """Cache agent state for persistence."""
        cache_key = CacheKey.agent_state(user_id, agent_id)
        state_data = {
            "state": state,
            "last_updated": datetime.utcnow().isoformat(),
            "agent_id": agent_id
        }
        return await self.cache_set(cache_key, state_data, ttl)
    
    async def get_agent_state(self, user_id: str, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get cached agent state."""
        cache_key = CacheKey.agent_state(user_id, agent_id)
        cached = await self.cache_get(cache_key)
        return cached.get("state") if cached else None
    
    # Chat Session Management
    
    async def cache_chat_session(self, user_id: str, session_id: str, messages: List[Dict], ttl: int = 3600) -> bool:
        """Cache chat session messages."""
        cache_key = CacheKey.chat_session(user_id, session_id)
        session_data = {
            "messages": messages,
            "last_updated": datetime.utcnow().isoformat(),
            "session_id": session_id
        }
        return await self.cache_set(cache_key, session_data, ttl)
    
    async def get_chat_session(self, user_id: str, session_id: str) -> Optional[List[Dict]]:
        """Get cached chat session messages."""
        cache_key = CacheKey.chat_session(user_id, session_id)
        cached = await self.cache_get(cache_key)
        return cached.get("messages") if cached else None
    
    # Task Queue Operations
    
    async def enqueue_task(self, user_id: str, task_data: Dict[str, Any]) -> bool:
        """Add a task to the user's task queue."""
        await self.initialize()
        try:
            queue_key = CacheKey.task_queue(user_id)
            task_with_metadata = {
                "task": task_data,
                "enqueued_at": datetime.utcnow().isoformat(),
                "user_id": user_id
            }
            json_task = json.dumps(task_with_metadata)
            
            if self.is_vercel_kv:
                return await self.client.lpush(queue_key, json_task)
            else:
                return bool(await self.client.lpush(queue_key, json_task))
        except Exception as e:
            logger.error(f"Task enqueue error: {e}")
            return False
    
    async def dequeue_task(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get the next task from the user's task queue."""
        await self.initialize()
        try:
            queue_key = CacheKey.task_queue(user_id)
            
            if self.is_vercel_kv:
                task_json = await self.client.rpop(queue_key)
            else:
                task_json = await self.client.rpop(queue_key)
            
            if task_json:
                return json.loads(task_json)
            return None
        except Exception as e:
            logger.error(f"Task dequeue error: {e}")
            return None
    
    # Rate Limiting
    
    async def check_rate_limit(self, user_id: str, limit: int = 60, window: int = 60) -> bool:
        """Check if user is within rate limit."""
        await self.initialize()
        try:
            rate_key = CacheKey.rate_limit(user_id)
            
            if self.is_vercel_kv:
                current = await self.client.get(rate_key)
                current_count = int(current) if current else 0
                
                if current_count >= limit:
                    return False
                
                new_count = current_count + 1
                await self.client.set(rate_key, str(new_count), ex=window)
                return True
            else:
                # Use Redis INCR with EXPIRE for atomic rate limiting
                current = await self.client.incr(rate_key)
                if current == 1:
                    await self.client.expire(rate_key, window)
                
                return current <= limit
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return True  # Allow on error to avoid blocking users
    
    # Health Check
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Redis service health."""
        await self.initialize()
        try:
            test_key = "health_check"
            test_value = "ok"
            
            # Test write
            write_success = await self.cache_set(test_key, test_value, 60)
            if not write_success:
                return {"status": "unhealthy", "error": "Write failed"}
            
            # Test read
            read_value = await self.cache_get(test_key)
            if read_value != test_value:
                return {"status": "unhealthy", "error": "Read failed"}
            
            # Clean up
            await self.cache_delete(test_key)
            
            return {
                "status": "healthy",
                "backend": "Vercel KV" if self.is_vercel_kv else "Redis",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# Global Redis service instance
redis_service = RedisService()


# Dependency for FastAPI
async def get_redis_service() -> RedisService:
    """FastAPI dependency to get Redis service."""
    return redis_service 