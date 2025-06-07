"""
Redis-Based Pattern Caching Module

This module provides caching for pattern recognition to improve 
performance and scalability of the symbolic analysis pipeline.
"""

import json
import hashlib
import asyncio
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta

import redis.asyncio as redis
from pydantic import BaseModel, Field

from ...utils.structured_logging import get_logger

logger = get_logger(__name__)


class CachedPattern(BaseModel):
    """Model for cached pattern analysis results."""
    pattern_hash: str = Field(..., description="Hash of the input pattern")
    result: Dict[str, Any] = Field(..., description="Analysis result")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(..., description="Expiration timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CachedPatternAnalyzer:
    """
    Pattern analyzer with Redis caching for performance optimization.
    
    Features:
    - Redis-based distributed caching
    - Automatic TTL management
    - Adaptive caching based on pattern complexity
    - Fallback to non-cached processing
    """
    
    def __init__(self, redis_url: str, default_ttl: int = 3600):
        """
        Initialize the cached pattern analyzer.
        
        Args:
            redis_url: Redis connection URL
            default_ttl: Default cache TTL in seconds
        """
        self.redis = redis.from_url(redis_url)
        self.default_ttl = default_ttl
        self.cache_prefix = "pattern:"
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Background task for cleaning up expired entries
        self._cleanup_task = None
        
        logger.info(f"CachedPatternAnalyzer initialized with TTL {default_ttl}s")
        
    async def start_cleanup_task(self):
        """Start the background task for cleaning up expired cache entries."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            
    async def _periodic_cleanup(self):
        """Periodically clean up expired cache entries."""
        try:
            while True:
                # Clean up once per hour
                await asyncio.sleep(3600)
                
                # Get all pattern keys
                pattern_keys = await self.redis.keys(f"{self.cache_prefix}*")
                
                # Check each key
                for key in pattern_keys:
                    try:
                        cached_data = await self.redis.get(key)
                        if cached_data:
                            cached = CachedPattern.model_validate_json(cached_data)
                            if cached.expires_at < datetime.utcnow():
                                await self.redis.delete(key)
                                logger.debug(f"Cleaned up expired cache entry: {key}")
                    except Exception as e:
                        logger.error(f"Error cleaning up cache entry {key}: {e}")
        except asyncio.CancelledError:
            logger.info("Cache cleanup task cancelled")
        except Exception as e:
            logger.error(f"Cache cleanup task failed: {e}")
    
    def _generate_cache_key(self, text: str, user_id: Optional[str] = None) -> str:
        """
        Generate a cache key based on normalized text and optional user ID.
        
        Args:
            text: The text to analyze
            user_id: Optional user ID for user-specific caching
            
        Returns:
            Cache key
        """
        # Normalize text
        normalized = text.lower().strip()
        
        # Generate hash
        hash_input = normalized
        if user_id:
            hash_input += f"|{user_id}"
            
        text_hash = hashlib.md5(hash_input.encode()).hexdigest()
        
        return f"{self.cache_prefix}{text_hash}"
    
    async def analyze_pattern(self, 
                            text: str, 
                            analyzer_func: callable, 
                            user_id: Optional[str] = None,
                            ttl: Optional[int] = None) -> Dict[str, Any]:
        """
        Analyze patterns with caching for repeated patterns.
        
        Args:
            text: The text to analyze
            analyzer_func: The function to call for analysis if cache miss
            user_id: Optional user ID for user-specific caching
            ttl: Optional custom TTL in seconds
            
        Returns:
            Analysis result
        """
        # Skip caching for very short inputs
        if len(text) < 10:
            return await analyzer_func(text, user_id)
        
        # Generate cache key
        cache_key = self._generate_cache_key(text, user_id)
        
        # Try cache first
        cached_data = await self.redis.get(cache_key)
        
        if cached_data:
            try:
                cached = CachedPattern.model_validate_json(cached_data)
                
                # Check if expired
                if cached.expires_at > datetime.utcnow():
                    self.cache_hits += 1
                    logger.debug(f"Pattern cache hit for {cache_key}")
                    return cached.result
                    
                # Expired, remove from cache
                await self.redis.delete(cache_key)
                
            except Exception as e:
                logger.error(f"Error deserializing cached pattern: {e}")
                # Continue to perform analysis
        
        # Cache miss or expired entry
        self.cache_misses += 1
        logger.debug(f"Pattern cache miss for {cache_key}")
        
        # Calculate adaptive TTL based on text complexity
        if ttl is None:
            ttl = self._calculate_adaptive_ttl(text)
        
        # Perform analysis
        try:
            result = await analyzer_func(text, user_id)
            
            # Cache result
            cached = CachedPattern(
                pattern_hash=cache_key,
                result=result,
                expires_at=datetime.utcnow() + timedelta(seconds=ttl),
                metadata={
                    "text_length": len(text),
                    "user_id": user_id,
                    "ttl": ttl
                }
            )
            
            # Store in Redis
            await self.redis.set(
                cache_key, 
                cached.model_dump_json(),
                ex=ttl
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error performing pattern analysis: {e}")
            raise
    
    def _calculate_adaptive_ttl(self, text: str) -> int:
        """
        Calculate adaptive TTL based on text complexity.
        
        Args:
            text: The text to analyze
            
        Returns:
            TTL in seconds
        """
        # Simple adaptive TTL based on text length
        text_length = len(text)
        
        if text_length < 50:
            # Short texts - cache for shorter time (more likely to change)
            return self.default_ttl // 2
        elif text_length < 200:
            # Medium texts - use default TTL
            return self.default_ttl
        else:
            # Long texts - cache for longer (less likely to be resubmitted)
            return self.default_ttl * 2
    
    async def clear_cache(self, user_id: Optional[str] = None) -> int:
        """
        Clear cache entries.
        
        Args:
            user_id: Optional user ID to clear only user-specific entries
            
        Returns:
            Number of entries cleared
        """
        try:
            if user_id:
                # Clear only user-specific entries
                # This is a simplification - in a full implementation, we'd need a more
                # sophisticated way to identify user-specific entries
                pattern_keys = await self.redis.keys(f"{self.cache_prefix}*{user_id}*")
            else:
                # Clear all pattern entries
                pattern_keys = await self.redis.keys(f"{self.cache_prefix}*")
                
            # Delete entries
            count = 0
            for key in pattern_keys:
                await self.redis.delete(key)
                count += 1
                
            logger.info(f"Cleared {count} cache entries")
            return count
        
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return 0
            
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Cache statistics
        """
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = 0 if total_requests == 0 else self.cache_hits / total_requests
        
        # Count entries in cache
        pattern_keys = await self.redis.keys(f"{self.cache_prefix}*")
        
        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": hit_rate,
            "total_entries": len(pattern_keys)
        }


# Global instance
_pattern_analyzer = None

async def get_pattern_analyzer(redis_url: Optional[str] = None) -> CachedPatternAnalyzer:
    """
    Get the global pattern analyzer instance.
    
    Args:
        redis_url: Redis URL (only used on first initialization)
        
    Returns:
        The global pattern analyzer instance
    """
    global _pattern_analyzer
    
    if _pattern_analyzer is None:
        if redis_url is None:
            from ...config.settings import get_settings
            redis_url = get_settings().REDIS_URL
            
        _pattern_analyzer = CachedPatternAnalyzer(redis_url)
        
        # Start cleanup task
        await _pattern_analyzer.start_cleanup_task()
    
    return _pattern_analyzer
