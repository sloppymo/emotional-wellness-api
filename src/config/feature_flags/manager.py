"""
Feature Flag Manager

This module provides the feature flag management functionality for dynamically
controlling application behavior without code deployments.
"""

import os
import json
import hashlib
import asyncio
import time
from typing import Dict, Any, Optional, List, Union, Set, Tuple
from datetime import datetime, timedelta

import redis.asyncio as redis

from .models import FeatureFlag, FeatureFlagValue, FeatureFlagType
from ...utils.structured_logging import get_logger

logger = get_logger(__name__)


class FeatureFlagManager:
    """
    Feature flag management system.
    
    Features:
    - Dynamic configuration at runtime
    - Redis-based distributed feature flags
    - Percentage-based rollouts and user targeting
    - Audit logging of flag changes
    - Default values for graceful fallback
    """
    
    def __init__(self, redis_url: str):
        """
        Initialize the feature flag manager.
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis = redis.from_url(redis_url)
        self.redis_prefix = "feature_flag:"
        self.cache: Dict[str, Tuple[FeatureFlag, float]] = {}
        self.cache_ttl_seconds = 60
        
        # Background refresh task
        self._refresh_task = None
        
        logger.info("FeatureFlagManager initialized")
    
    async def start_refresh_task(self):
        """Start background refresh task for feature flags."""
        if self._refresh_task is None or self._refresh_task.done():
            self._refresh_task = asyncio.create_task(self._periodic_refresh())
    
    async def _periodic_refresh(self):
        """Periodically refresh cached feature flags."""
        try:
            while True:
                # Refresh once per minute
                await asyncio.sleep(60)
                
                try:
                    # Refresh all cached flags
                    keys_to_refresh = list(self.cache.keys())
                    for key in keys_to_refresh:
                        # Check if cache entry is expired
                        cached = self.cache.get(key)
                        if cached and time.time() - cached[1] > self.cache_ttl_seconds:
                            await self._load_flag_from_redis(key)
                except Exception as e:
                    logger.error(f"Error refreshing feature flags: {e}")
        except asyncio.CancelledError:
            logger.info("Feature flag refresh task cancelled")
        except Exception as e:
            logger.error(f"Feature flag refresh task failed: {e}")
    
    async def _load_flag_from_redis(self, key: str) -> Optional[FeatureFlag]:
        """
        Load a feature flag from Redis.
        
        Args:
            key: Feature flag key
            
        Returns:
            FeatureFlag if found, None otherwise
        """
        redis_key = f"{self.redis_prefix}{key}"
        
        try:
            # Get from Redis
            flag_data = await self.redis.get(redis_key)
            
            if flag_data:
                # Parse and cache
                flag = FeatureFlag.model_validate_json(flag_data)
                self.cache[key] = (flag, time.time())
                return flag
        except Exception as e:
            logger.error(f"Error loading feature flag '{key}' from Redis: {e}")
            
        return None
    
    async def get_flag(self, key: str) -> Optional[FeatureFlag]:
        """
        Get a feature flag by key.
        
        Args:
            key: Feature flag key
            
        Returns:
            FeatureFlag if found, None otherwise
        """
        # Check cache first
        cached = self.cache.get(key)
        if cached and time.time() - cached[1] <= self.cache_ttl_seconds:
            return cached[0]
            
        # Load from Redis
        return await self._load_flag_from_redis(key)
    
    async def get_flag_value(self, 
                           key: str, 
                           default_value: Any = None, 
                           user_id: Optional[str] = None) -> Any:
        """
        Get a feature flag value, considering targeting rules.
        
        Args:
            key: Feature flag key
            default_value: Default value if flag not found
            user_id: Optional user ID for targeting
            
        Returns:
            Feature flag value or default value
        """
        flag = await self.get_flag(key)
        
        if not flag or not flag.enabled:
            return default_value if default_value is not None else flag.default_value if flag else None
            
        # Check if user is in target list
        if user_id and flag.target_users and user_id in flag.target_users:
            return flag.value.value
            
        # Check percentage rollout if applicable
        if user_id and flag.percentage_rollout is not None:
            # Use hash of user ID for consistent percentage assignment
            hash_input = f"{key}:{user_id}"
            user_hash = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
            user_bucket = (user_hash % 100) + 1  # 1-100
            
            if user_bucket <= flag.percentage_rollout:
                return flag.value.value
            else:
                return flag.default_value
                
        # Normal case - return current value
        return flag.value.value
    
    async def set_flag(self, flag: FeatureFlag, updated_by: Optional[str] = None) -> bool:
        """
        Set or update a feature flag.
        
        Args:
            flag: Feature flag to set
            updated_by: Who is updating this flag
            
        Returns:
            True if successful
        """
        redis_key = f"{self.redis_prefix}{flag.key}"
        
        # Update last_updated and updated_by
        if updated_by:
            flag.value.updated_by = updated_by
        flag.value.last_updated = datetime.utcnow()
        
        try:
            # Save to Redis
            await self.redis.set(redis_key, flag.model_dump_json())
            
            # Update cache
            self.cache[flag.key] = (flag, time.time())
            
            logger.info(f"Feature flag '{flag.key}' set to {flag.value.value} by {updated_by}")
            return True
        except Exception as e:
            logger.error(f"Error setting feature flag '{flag.key}': {e}")
            return False
    
    async def list_flags(self, category: Optional[str] = None, tags: Optional[List[str]] = None) -> List[FeatureFlag]:
        """
        List all feature flags, optionally filtered.
        
        Args:
            category: Optional category filter
            tags: Optional tags to filter by
            
        Returns:
            List of feature flags
        """
        flags = []
        
        try:
            # Get all flag keys
            keys = await self.redis.keys(f"{self.redis_prefix}*")
            
            for key in keys:
                try:
                    # Remove prefix to get flag key
                    flag_key = key.decode('utf-8').replace(self.redis_prefix, '')
                    
                    # Get flag
                    flag = await self.get_flag(flag_key)
                    if flag:
                        # Apply filters
                        if category and flag.category != category:
                            continue
                            
                        if tags and not all(tag in flag.tags for tag in tags):
                            continue
                            
                        flags.append(flag)
                except Exception as e:
                    logger.error(f"Error loading flag for key {key}: {e}")
        except Exception as e:
            logger.error(f"Error listing feature flags: {e}")
            
        return flags
    
    async def delete_flag(self, key: str) -> bool:
        """
        Delete a feature flag.
        
        Args:
            key: Feature flag key to delete
            
        Returns:
            True if successful
        """
        redis_key = f"{self.redis_prefix}{key}"
        
        try:
            # Delete from Redis
            result = await self.redis.delete(redis_key)
            
            # Remove from cache
            if key in self.cache:
                del self.cache[key]
                
            logger.info(f"Feature flag '{key}' deleted")
            return result > 0
        except Exception as e:
            logger.error(f"Error deleting feature flag '{key}': {e}")
            return False
    
    async def create_or_update_flag(self,
                                  key: str,
                                  name: str,
                                  description: str,
                                  value: Any,
                                  value_type: FeatureFlagType,
                                  default_value: Any,
                                  category: str = "general",
                                  tags: Optional[List[str]] = None,
                                  enabled: bool = True,
                                  updated_by: Optional[str] = None) -> FeatureFlag:
        """
        Create or update a feature flag.
        
        Args:
            key: Feature flag key
            name: Human-readable name
            description: Description of flag
            value: Current value
            value_type: Type of value
            default_value: Default value
            category: Category for organizing
            tags: Optional tags
            enabled: Whether flag is enabled
            updated_by: Who is updating this flag
            
        Returns:
            Created/updated feature flag
        """
        # Check if flag exists
        existing_flag = await self.get_flag(key)
        
        if existing_flag:
            # Update existing
            existing_flag.name = name
            existing_flag.description = description
            existing_flag.value = FeatureFlagValue(
                value=value,
                type=value_type,
                updated_by=updated_by,
                last_updated=datetime.utcnow()
            )
            existing_flag.default_value = default_value
            existing_flag.category = category
            existing_flag.tags = tags or existing_flag.tags
            existing_flag.enabled = enabled
            
            flag = existing_flag
        else:
            # Create new
            flag = FeatureFlag(
                key=key,
                name=name,
                description=description,
                value=FeatureFlagValue(
                    value=value,
                    type=value_type,
                    updated_by=updated_by
                ),
                default_value=default_value,
                category=category,
                tags=tags or [],
                enabled=enabled,
                created_at=datetime.utcnow()
            )
            
        # Save
        await self.set_flag(flag, updated_by)
        return flag
    
    async def toggle_flag(self, key: str, enabled: bool, updated_by: Optional[str] = None) -> Optional[FeatureFlag]:
        """
        Toggle a feature flag on or off.
        
        Args:
            key: Feature flag key
            enabled: Whether flag should be enabled
            updated_by: Who is updating this flag
            
        Returns:
            Updated feature flag or None if not found
        """
        flag = await self.get_flag(key)
        if not flag:
            return None
            
        flag.enabled = enabled
        if updated_by:
            flag.value.updated_by = updated_by
            
        flag.value.last_updated = datetime.utcnow()
        
        await self.set_flag(flag, updated_by)
        return flag


# Global instance
_feature_flag_manager = None

async def get_feature_flag_manager(redis_url: Optional[str] = None) -> FeatureFlagManager:
    """
    Get the global feature flag manager instance.
    
    Args:
        redis_url: Redis URL (only used on first initialization)
        
    Returns:
        The global feature flag manager instance
    """
    global _feature_flag_manager
    
    if _feature_flag_manager is None:
        if redis_url is None:
            from ...config.settings import get_settings
            redis_url = get_settings().REDIS_URL
            
        _feature_flag_manager = FeatureFlagManager(redis_url)
        await _feature_flag_manager.start_refresh_task()
    
    return _feature_flag_manager
