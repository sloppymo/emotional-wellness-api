"""
Redis client for caching and rate limiting in the Emotional Wellness API.
"""

import logging
from typing import Optional, Any, Dict, Union
import json

import redis
from redis.exceptions import RedisError

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

# Global redis client
_redis_client = None

def get_redis_client() -> redis.Redis:
    """
    Get a Redis client instance.
    Uses connection pooling for efficient connections.
    
    Returns:
        redis.Redis: Redis client configured from settings
    """
    global _redis_client
    
    if _redis_client is None:
        settings = get_settings()
        try:
            logger.info(f"Connecting to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
            _redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                decode_responses=True,
            )
            logger.info("Redis client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {str(e)}")
            # Initialize dummy client for development if Redis is not available
            if settings.DEBUG:
                logger.warning("Using dummy Redis client in DEBUG mode")
                _redis_client = DummyRedis()
            else:
                raise
    
    return _redis_client


class DummyRedis:
    """
    Dummy Redis implementation for development when Redis is not available.
    Only implements the minimal set of methods needed for the application.
    """
    def __init__(self):
        self.data = {}
        logger.warning("Using DummyRedis - no actual Redis connection")
        
    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Set a key with optional expiration"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            self.data[key] = value
            logger.debug(f"DummyRedis SET: {key} (ex={ex})")
            return True
        except Exception as e:
            logger.error(f"DummyRedis SET error: {str(e)}")
            return False
    
    def get(self, key: str) -> Optional[str]:
        """Get a key value"""
        value = self.data.get(key)
        logger.debug(f"DummyRedis GET: {key} -> {value != None}")
        return value
    
    def delete(self, key: str) -> int:
        """Delete a key"""
        if key in self.data:
            del self.data[key]
            logger.debug(f"DummyRedis DEL: {key}")
            return 1
        return 0
    
    def exists(self, key: str) -> int:
        """Check if key exists"""
        result = int(key in self.data)
        logger.debug(f"DummyRedis EXISTS: {key} -> {result}")
        return result
    
    def expire(self, key: str, seconds: int) -> int:
        """Set expiration on key (dummy implementation always succeeds)"""
        if key in self.data:
            logger.debug(f"DummyRedis EXPIRE: {key} -> {seconds}s")
            return 1
        return 0
    
    def incr(self, key: str, amount: int = 1) -> int:
        """Increment a key by amount"""
        try:
            if key not in self.data:
                self.data[key] = "0"
            current = int(self.data[key])
            new_value = current + amount
            self.data[key] = str(new_value)
            logger.debug(f"DummyRedis INCR: {key} by {amount} -> {new_value}")
            return new_value
        except Exception as e:
            logger.error(f"DummyRedis INCR error: {str(e)}")
            return 0
    
    def hset(self, name: str, key: str, value: Any) -> int:
        """Set field in hash table"""
        try:
            if name not in self.data:
                self.data[name] = {}
            if not isinstance(self.data[name], dict):
                self.data[name] = {}
            
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            is_new = key not in self.data[name]
            self.data[name][key] = value
            logger.debug(f"DummyRedis HSET: {name}.{key}")
            return int(is_new)
        except Exception as e:
            logger.error(f"DummyRedis HSET error: {str(e)}")
            return 0
    
    def hget(self, name: str, key: str) -> Optional[str]:
        """Get field from hash table"""
        try:
            result = None
            if name in self.data and isinstance(self.data[name], dict):
                result = self.data[name].get(key)
            logger.debug(f"DummyRedis HGET: {name}.{key} -> {result != None}")
            return result
        except Exception as e:
            logger.error(f"DummyRedis HGET error: {str(e)}")
            return None
    
    def hgetall(self, name: str) -> Dict[str, str]:
        """Get all fields from hash table"""
        if name in self.data and isinstance(self.data[name], dict):
            logger.debug(f"DummyRedis HGETALL: {name} -> {len(self.data[name])} fields")
            return self.data[name]
        logger.debug(f"DummyRedis HGETALL: {name} -> 0 fields")
        return {}
