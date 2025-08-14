"""
Cache Manager for Football Prediction App
Handles caching of ML predictions, API responses, and computed features
"""

import os
import json
import hashlib
import redis
from typing import Any, Optional, Union, Callable
from datetime import datetime, timedelta
from functools import wraps
import pickle
import logging

from config import Config

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching with Redis backend"""
    
    def __init__(self, redis_url: Optional[str] = None):
        """Initialize cache manager with Redis connection"""
        self.redis_url = redis_url or os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
        self._redis_client = None
        self._connect()
    
    def _connect(self):
        """Establish Redis connection"""
        try:
            self._redis_client = redis.from_url(
                self.redis_url,
                decode_responses=False,  # We'll handle encoding/decoding
                socket_keepalive=True,
                socket_keepalive_options={1: 1, 2: 3, 3: 5}
            )
            # Test connection
            self._redis_client.ping()
            logger.info("Redis cache connected successfully")
        except Exception as e:
            logger.error(f"Redis connection failed: {str(e)}")
            self._redis_client = None
    
    @property
    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        if not self._redis_client:
            return False
        try:
            self._redis_client.ping()
            return True
        except:
            return False
    
    def _make_key(self, prefix: str, identifier: str) -> str:
        """Create a cache key with prefix"""
        return f"football_prediction:{prefix}:{identifier}"
    
    def _serialize(self, data: Any) -> bytes:
        """Serialize data for storage"""
        try:
            # Try JSON first (more readable, better for simple data)
            return json.dumps(data).encode('utf-8')
        except (TypeError, ValueError):
            # Fall back to pickle for complex objects
            return pickle.dumps(data)
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize data from storage"""
        if not data:
            return None
        try:
            # Try JSON first
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fall back to pickle
            return pickle.loads(data)
    
    def get(self, key: str, prefix: str = 'general') -> Optional[Any]:
        """Get value from cache"""
        if not self.is_connected:
            return None
        
        full_key = self._make_key(prefix, key)
        try:
            data = self._redis_client.get(full_key)
            if data:
                logger.debug(f"Cache hit: {full_key}")
                return self._deserialize(data)
            logger.debug(f"Cache miss: {full_key}")
            return None
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 300, prefix: str = 'general') -> bool:
        """Set value in cache with TTL"""
        if not self.is_connected:
            return False
        
        full_key = self._make_key(prefix, key)
        try:
            serialized = self._serialize(value)
            self._redis_client.setex(full_key, ttl, serialized)
            logger.debug(f"Cache set: {full_key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
            return False
    
    def delete(self, key: str, prefix: str = 'general') -> bool:
        """Delete value from cache"""
        if not self.is_connected:
            return False
        
        full_key = self._make_key(prefix, key)
        try:
            result = self._redis_client.delete(full_key)
            logger.debug(f"Cache delete: {full_key}")
            return bool(result)
        except Exception as e:
            logger.error(f"Cache delete error: {str(e)}")
            return False
    
    def clear_prefix(self, prefix: str) -> int:
        """Clear all keys with given prefix"""
        if not self.is_connected:
            return 0
        
        pattern = self._make_key(prefix, '*')
        try:
            keys = self._redis_client.keys(pattern)
            if keys:
                deleted = self._redis_client.delete(*keys)
                logger.info(f"Cleared {deleted} keys with prefix: {prefix}")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Cache clear error: {str(e)}")
            return 0
    
    def get_ttl(self, key: str, prefix: str = 'general') -> int:
        """Get remaining TTL for a key"""
        if not self.is_connected:
            return -1
        
        full_key = self._make_key(prefix, key)
        try:
            ttl = self._redis_client.ttl(full_key)
            return ttl if ttl >= 0 else -1
        except Exception as e:
            logger.error(f"Cache TTL error: {str(e)}")
            return -1


# Global cache instance
cache = CacheManager()


def cache_key_for_prediction(match_id: int, model_version: str = 'latest') -> str:
    """Generate cache key for match prediction"""
    return f"prediction:{match_id}:{model_version}"


def cache_key_for_features(match_id: int) -> str:
    """Generate cache key for match features"""
    return f"features:{match_id}"


def cache_key_for_team_stats(team_id: int, season: str) -> str:
    """Generate cache key for team statistics"""
    return f"team_stats:{team_id}:{season}"


def cache_key_for_api_response(endpoint: str, params: dict) -> str:
    """Generate cache key for API response"""
    # Sort params for consistent keys
    sorted_params = sorted(params.items())
    param_str = json.dumps(sorted_params)
    param_hash = hashlib.md5(param_str.encode()).hexdigest()
    return f"api:{endpoint}:{param_hash}"


def cached(prefix: str = 'general', ttl: int = 300, key_func: Optional[Callable] = None):
    """
    Decorator for caching function results
    
    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds
        key_func: Optional function to generate cache key from arguments
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_value = cache.get(cache_key, prefix=prefix)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache the result
            cache.set(cache_key, result, ttl=ttl, prefix=prefix)
            
            return result
        
        # Add cache management methods
        wrapper.invalidate = lambda *args, **kwargs: cache.delete(
            key_func(*args, **kwargs) if key_func else ":".join([func.__name__] + [str(arg) for arg in args]),
            prefix=prefix
        )
        wrapper.clear_all = lambda: cache.clear_prefix(prefix)
        
        return wrapper
    return decorator


# Specialized cache decorators
def cache_prediction(ttl: int = 1800):  # 30 minutes
    """Cache ML predictions"""
    return cached(
        prefix='predictions',
        ttl=ttl,
        key_func=lambda match_id, *args, **kwargs: cache_key_for_prediction(match_id, kwargs.get('model_version', 'latest'))
    )


def cache_team_stats(ttl: int = 3600):  # 1 hour
    """Cache team statistics"""
    return cached(
        prefix='team_stats',
        ttl=ttl,
        key_func=lambda team_id, season, *args, **kwargs: cache_key_for_team_stats(team_id, season)
    )


def cache_api_response(ttl: int = 300):  # 5 minutes
    """Cache API responses"""
    def decorator(func):
        @wraps(func)
        def wrapper(endpoint: str, params: dict = None, *args, **kwargs):
            params = params or {}
            cache_key = cache_key_for_api_response(endpoint, params)
            
            # Try cache first
            cached_value = cache.get(cache_key, prefix='api_responses')
            if cached_value is not None:
                logger.debug(f"API cache hit: {endpoint}")
                return cached_value
            
            # Call API
            result = func(endpoint, params, *args, **kwargs)
            
            # Cache successful responses
            if result and isinstance(result, dict) and not result.get('error'):
                cache.set(cache_key, result, ttl=ttl, prefix='api_responses')
            
            return result
        return wrapper
    return decorator


def invalidate_match_caches(match_id: int):
    """Invalidate all caches related to a match"""
    # Delete prediction cache
    cache.delete(cache_key_for_prediction(match_id), prefix='predictions')
    # Delete features cache
    cache.delete(cache_key_for_features(match_id), prefix='features')
    logger.info(f"Invalidated caches for match {match_id}")


def invalidate_team_caches(team_id: int):
    """Invalidate all caches related to a team"""
    # Clear all team stats for this team
    pattern = f"team_stats:{team_id}:*"
    cleared = cache.clear_prefix(pattern)
    logger.info(f"Invalidated {cleared} caches for team {team_id}")


def get_cache_stats() -> dict:
    """Get cache statistics"""
    if not cache.is_connected:
        return {"status": "disconnected"}
    
    try:
        info = cache._redis_client.info()
        return {
            "status": "connected",
            "used_memory": info.get('used_memory_human', 'N/A'),
            "connected_clients": info.get('connected_clients', 0),
            "total_commands_processed": info.get('total_commands_processed', 0),
            "keyspace_hits": info.get('keyspace_hits', 0),
            "keyspace_misses": info.get('keyspace_misses', 0),
            "hit_rate": round(
                info.get('keyspace_hits', 0) / 
                (info.get('keyspace_hits', 0) + info.get('keyspace_misses', 1)) * 100, 
                2
            ) if info.get('keyspace_hits', 0) > 0 else 0
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {str(e)}")
        return {"status": "error", "error": str(e)}