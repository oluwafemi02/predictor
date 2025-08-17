"""
Cache utilities for the Football Prediction App
"""
import json
import hashlib
from functools import wraps
from flask import request
import redis
from config import Config
import logging

logger = logging.getLogger(__name__)

# Initialize Redis client
try:
    redis_client = redis.from_url(Config.REDIS_URL, decode_responses=True)
    redis_client.ping()
    REDIS_AVAILABLE = True
except Exception as e:
    logger.warning(f"Redis not available: {e}")
    redis_client = None
    REDIS_AVAILABLE = False


def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate a cache key from prefix and arguments"""
    # Create a unique key from arguments
    key_data = {
        'args': args,
        'kwargs': kwargs,
        'path': request.path if request else '',
        'query': request.query_string.decode() if request and request.query_string else ''
    }
    
    # Create hash of the key data
    key_hash = hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
    
    return f"{prefix}:{key_hash}"


def cache_response(timeout: int = 300, prefix: str = 'cache'):
    """
    Cache decorator for Flask routes
    
    Args:
        timeout: Cache timeout in seconds (default: 5 minutes)
        prefix: Cache key prefix
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Skip caching if Redis is not available
            if not REDIS_AVAILABLE:
                return f(*args, **kwargs)
            
            # Skip caching for non-GET requests
            if request and request.method != 'GET':
                return f(*args, **kwargs)
            
            # Generate cache key
            cache_key = generate_cache_key(prefix, *args, **kwargs)
            
            try:
                # Try to get from cache
                cached_data = redis_client.get(cache_key)
                if cached_data:
                    logger.debug(f"Cache hit: {cache_key}")
                    return json.loads(cached_data)
                
                # Call the function
                result = f(*args, **kwargs)
                
                # Cache the result if it's a dict or list
                if isinstance(result, (dict, list)):
                    redis_client.setex(cache_key, timeout, json.dumps(result))
                    logger.debug(f"Cached: {cache_key} for {timeout}s")
                elif isinstance(result, tuple) and len(result) == 2:
                    # Handle Flask response tuples (data, status_code)
                    data, status_code = result
                    if status_code == 200 and isinstance(data, (dict, list)):
                        redis_client.setex(cache_key, timeout, json.dumps(data))
                        logger.debug(f"Cached: {cache_key} for {timeout}s")
                
                return result
                
            except Exception as e:
                logger.error(f"Cache error: {e}")
                # If caching fails, just return the result
                return f(*args, **kwargs)
        
        return wrapper
    return decorator


def invalidate_cache(pattern: str = '*'):
    """
    Invalidate cache entries matching a pattern
    
    Args:
        pattern: Redis key pattern (e.g., 'cache:matches:*')
    """
    if not REDIS_AVAILABLE:
        return 0
    
    try:
        keys = redis_client.keys(pattern)
        if keys:
            deleted = redis_client.delete(*keys)
            logger.info(f"Invalidated {deleted} cache entries matching '{pattern}'")
            return deleted
        return 0
    except Exception as e:
        logger.error(f"Cache invalidation error: {e}")
        return 0


def get_cache_stats() -> dict:
    """Get cache statistics"""
    if not REDIS_AVAILABLE:
        return {'available': False, 'message': 'Redis not available'}
    
    try:
        info = redis_client.info()
        return {
            'available': True,
            'used_memory': info.get('used_memory_human', 'N/A'),
            'connected_clients': info.get('connected_clients', 0),
            'total_commands': info.get('total_commands_processed', 0),
            'keyspace_hits': info.get('keyspace_hits', 0),
            'keyspace_misses': info.get('keyspace_misses', 0),
            'hit_rate': (
                info.get('keyspace_hits', 0) / 
                (info.get('keyspace_hits', 0) + info.get('keyspace_misses', 1))
            ) if info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0) > 0 else 0
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {'available': False, 'error': str(e)}


class CacheManager:
    """
    Cache manager for more complex caching scenarios
    """
    
    def __init__(self, redis_client=redis_client):
        self.redis = redis_client
    
    def get_or_set(self, key: str, func, timeout: int = 300):
        """Get from cache or compute and set"""
        if not self.redis:
            return func()
        
        try:
            # Try to get from cache
            cached = self.redis.get(key)
            if cached:
                return json.loads(cached)
            
            # Compute value
            value = func()
            
            # Cache it
            self.redis.setex(key, timeout, json.dumps(value))
            
            return value
        except Exception as e:
            logger.error(f"Cache error in get_or_set: {e}")
            return func()
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching a pattern"""
        return invalidate_cache(pattern)
    
    def set_many(self, data: dict, timeout: int = 300):
        """Set multiple cache entries"""
        if not self.redis:
            return
        
        try:
            pipe = self.redis.pipeline()
            for key, value in data.items():
                pipe.setex(key, timeout, json.dumps(value))
            pipe.execute()
        except Exception as e:
            logger.error(f"Error in set_many: {e}")


# Global cache manager instance
cache_manager = CacheManager()