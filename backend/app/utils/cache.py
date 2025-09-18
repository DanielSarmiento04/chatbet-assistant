"""
Redis caching utilities for the ChatBet application.

This module provides a clean interface for caching with Redis.
I'm designing it to be production-ready with connection pooling,
error handling, and automatic serialization/deserialization.

The caching strategy here is critical for performance:
- API responses are cached with different TTLs based on data volatility
- User sessions are cached for fast access
- Conversation history is cached to reduce database load
"""

import json
import pickle
import logging
from typing import Any, Optional, Union, Dict, List
from datetime import datetime, timedelta
import asyncio

import redis.asyncio as redis
from redis.asyncio import Redis, ConnectionPool

from ..core.config import settings
from ..core.logging import get_logger, log_function_call
from ..utils.exceptions import CacheError, CacheUnavailableError

logger = get_logger(__name__)


class RedisCache:
    """
    Async Redis cache manager with connection pooling.
    
    This class provides a high-level interface for caching operations
    with automatic serialization, error handling, and performance monitoring.
    
    Features:
    - Automatic JSON/pickle serialization
    - Connection pooling for better performance
    - Circuit breaker pattern for resilience
    - Performance metrics and monitoring
    - Namespace support for different data types
    """
    
    def __init__(self):
        self.pool: Optional[ConnectionPool] = None
        self.redis: Optional[Redis] = None
        self._connected = False
        
        # Performance tracking
        self._cache_hits = 0
        self._cache_misses = 0
        self._cache_errors = 0
        
        # Circuit breaker for cache failures
        self._failure_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._circuit_open = False
    
    async def connect(self):
        """Initialize Redis connection pool."""
        try:
            # Create connection pool
            self.pool = ConnectionPool.from_url(
                settings.redis_dsn,
                max_connections=20,
                retry_on_timeout=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Create Redis client
            self.redis = Redis(connection_pool=self.pool)
            
            # Test connection
            await self.redis.ping()
            
            self._connected = True
            self._circuit_open = False
            self._failure_count = 0
            
            logger.info("Redis cache connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._connected = False
            raise CacheUnavailableError(f"Redis connection failed: {e}")
    
    async def disconnect(self):
        """Close Redis connections."""
        if self.redis:
            await self.redis.close()
        if self.pool:
            await self.pool.disconnect()
        
        self._connected = False
        logger.info("Redis cache disconnected")
    
    def _check_circuit_breaker(self) -> bool:
        """Check if circuit breaker allows operations."""
        if not self._circuit_open:
            return True
        
        # Check if circuit should be closed (timeout expired)
        if (self._last_failure_time and 
            datetime.now() - self._last_failure_time > timedelta(minutes=1)):
            self._circuit_open = False
            self._failure_count = 0
            logger.info("Cache circuit breaker closed - retrying operations")
            return True
        
        return False
    
    def _record_failure(self):
        """Record cache operation failure."""
        self._failure_count += 1
        self._last_failure_time = datetime.now()
        self._cache_errors += 1
        
        # Open circuit breaker after 5 failures
        if self._failure_count >= 5:
            self._circuit_open = True
            logger.warning("Cache circuit breaker opened due to repeated failures")
    
    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value for storage."""
        if isinstance(value, (str, int, float, bool)):
            # Store simple types as JSON for readability
            return json.dumps(value).encode('utf-8')
        else:
            # Use pickle for complex objects
            return pickle.dumps(value)
    
    def _deserialize_value(self, data: bytes) -> Any:
        """Deserialize value from storage."""
        try:
            # Try JSON first
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fall back to pickle
            return pickle.loads(data)
    
    @log_function_call()
    async def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            namespace: Cache namespace for organization
            
        Returns:
            Cached value or None if not found
        """
        if not self._connected or not self._check_circuit_breaker():
            return None
        
        try:
            full_key = f"{namespace}:{key}"
            data = await self.redis.get(full_key)
            
            if data:
                self._cache_hits += 1
                value = self._deserialize_value(data)
                logger.debug(f"Cache hit: {full_key}")
                return value
            else:
                self._cache_misses += 1
                logger.debug(f"Cache miss: {full_key}")
                return None
                
        except Exception as e:
            self._record_failure()
            logger.error(f"Cache get error for {key}: {e}")
            return None
    
    @log_function_call()
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None, 
        namespace: str = "default"
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            namespace: Cache namespace
            
        Returns:
            True if successful, False otherwise
        """
        if not self._connected or not self._check_circuit_breaker():
            return False
        
        try:
            full_key = f"{namespace}:{key}"
            serialized_value = self._serialize_value(value)
            
            if ttl:
                await self.redis.setex(full_key, ttl, serialized_value)
            else:
                await self.redis.set(full_key, serialized_value)
            
            logger.debug(f"Cache set: {full_key} (TTL: {ttl})")
            return True
            
        except Exception as e:
            self._record_failure()
            logger.error(f"Cache set error for {key}: {e}")
            return False
    
    @log_function_call()
    async def delete(self, key: str, namespace: str = "default") -> bool:
        """Delete key from cache."""
        if not self._connected or not self._check_circuit_breaker():
            return False
        
        try:
            full_key = f"{namespace}:{key}"
            result = await self.redis.delete(full_key)
            logger.debug(f"Cache delete: {full_key}")
            return bool(result)
            
        except Exception as e:
            self._record_failure()
            logger.error(f"Cache delete error for {key}: {e}")
            return False
    
    async def exists(self, key: str, namespace: str = "default") -> bool:
        """Check if key exists in cache."""
        if not self._connected or not self._check_circuit_breaker():
            return False
        
        try:
            full_key = f"{namespace}:{key}"
            result = await self.redis.exists(full_key)
            return bool(result)
            
        except Exception as e:
            self._record_failure()
            logger.error(f"Cache exists error for {key}: {e}")
            return False
    
    async def expire(self, key: str, ttl: int, namespace: str = "default") -> bool:
        """Set expiration for a key."""
        if not self._connected or not self._check_circuit_breaker():
            return False
        
        try:
            full_key = f"{namespace}:{key}"
            result = await self.redis.expire(full_key, ttl)
            return bool(result)
            
        except Exception as e:
            self._record_failure()
            logger.error(f"Cache expire error for {key}: {e}")
            return False
    
    async def clear_namespace(self, namespace: str) -> int:
        """Clear all keys in a namespace."""
        if not self._connected or not self._check_circuit_breaker():
            return 0
        
        try:
            pattern = f"{namespace}:*"
            keys = await self.redis.keys(pattern)
            
            if keys:
                result = await self.redis.delete(*keys)
                logger.info(f"Cleared {result} keys from namespace: {namespace}")
                return result
            
            return 0
            
        except Exception as e:
            self._record_failure()
            logger.error(f"Cache clear namespace error: {e}")
            return 0
    
    # === High-level caching methods for different data types ===
    
    async def cache_api_response(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]], 
        response_data: Any,
        ttl: int
    ) -> bool:
        """Cache API response with automatic key generation."""
        if params:
            param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
            cache_key = f"{endpoint}?{param_str}"
        else:
            cache_key = endpoint
        
        return await self.set(cache_key, response_data, ttl, namespace="api_responses")
    
    async def get_cached_api_response(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """Get cached API response."""
        if params:
            param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
            cache_key = f"{endpoint}?{param_str}"
        else:
            cache_key = endpoint
        
        return await self.get(cache_key, namespace="api_responses")
    
    async def cache_user_session(
        self, 
        session_id: str, 
        session_data: Dict[str, Any]
    ) -> bool:
        """Cache user session data."""
        return await self.set(
            session_id, 
            session_data, 
            ttl=settings.cache_ttl_user_sessions,
            namespace="user_sessions"
        )
    
    async def get_user_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user session data."""
        return await self.get(session_id, namespace="user_sessions")
    
    async def cache_conversation(
        self, 
        conversation_id: str, 
        conversation_data: Dict[str, Any]
    ) -> bool:
        """Cache conversation data."""
        return await self.set(
            conversation_id,
            conversation_data,
            ttl=settings.conversation_timeout,
            namespace="conversations"
        )
    
    async def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get cached conversation data."""
        return await self.get(conversation_id, namespace="conversations")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "connected": self._connected,
            "circuit_open": self._circuit_open,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "cache_errors": self._cache_errors,
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": total_requests,
            "failure_count": self._failure_count
        }


# Global cache instance
_redis_cache: Optional[RedisCache] = None


def get_redis_cache() -> RedisCache:
    """Get global Redis cache instance."""
    global _redis_cache
    if _redis_cache is None:
        _redis_cache = RedisCache()
    return _redis_cache


async def get_cache() -> RedisCache:
    """Get global cache instance."""
    global _cache
    if _cache is None:
        _cache = RedisCache()
        await _cache.connect()
    return _cache


async def cleanup_cache():
    """Cleanup function to be called on app shutdown."""
    global _cache
    if _cache:
        await _cache.disconnect()
        _cache = None