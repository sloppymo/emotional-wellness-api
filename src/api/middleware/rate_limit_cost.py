from typing import Dict, Optional, Any, Callable
from redis.asyncio import Redis
import json
import hashlib
from datetime import datetime, timedelta
from .rate_limit_types import RateLimitCategory

class RateLimitCost:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.cost_key_prefix = "ratelimit:cost:"
        self.cache_key_prefix = "ratelimit:cache:"
        
        # Default costs for different operations
        self.default_costs = {
            RateLimitCategory.PHI_OPERATION: 5,      # High cost for PHI operations
            RateLimitCategory.CRISIS_INTERVENTION: 3,  # Moderate cost for crisis endpoints
            RateLimitCategory.AUTHENTICATED: 2,      # Standard cost for authenticated ops
            RateLimitCategory.READ_ONLY: 1,          # Low cost for read operations
            RateLimitCategory.PUBLIC: 1,             # Low cost for public endpoints
            RateLimitCategory.SYSTEM: 0,             # No cost for system endpoints
        }
        
    async def get_operation_cost(
        self,
        category: RateLimitCategory,
        operation: str,
        custom_costs: Optional[Dict[str, int]] = None
    ) -> int:
        """Get the cost of an operation."""
        # Check custom costs first
        if custom_costs and operation in custom_costs:
            return custom_costs[operation]
            
        # Use category default cost
        return self.default_costs.get(category, 1)
        
    async def check_cost_limit(
        self,
        client_id: str,
        category: RateLimitCategory,
        operation: str,
        cost_limit: int,
        window_seconds: int = 3600,  # 1 hour window
        custom_costs: Optional[Dict[str, int]] = None
    ) -> Tuple[bool, int, int]:
        """Check if an operation is within cost limits."""
        cost = await self.get_operation_cost(category, operation, custom_costs)
        current_window = int(datetime.now().timestamp() / window_seconds)
        
        # Get current cost usage
        cost_key = f"{self.cost_key_prefix}{client_id}:{category.value}:{current_window}"
        current_cost = int(await self.redis.get(cost_key) or 0)
        
        # Check if operation would exceed limit
        if current_cost + cost > cost_limit:
            return False, current_cost, cost_limit
            
        # Increment cost
        await self.redis.incrby(cost_key, cost)
        await self.redis.expire(cost_key, window_seconds)
        
        return True, current_cost + cost, cost_limit
        
    async def get_cost_usage(
        self,
        client_id: str,
        category: RateLimitCategory,
        window_seconds: int = 3600
    ) -> Dict[str, Any]:
        """Get the current cost usage for a client."""
        current_window = int(datetime.now().timestamp() / window_seconds)
        cost_key = f"{self.cost_key_prefix}{client_id}:{category.value}:{current_window}"
        
        current_cost = int(await self.redis.get(cost_key) or 0)
        cost_limit = self.default_costs.get(category, 1) * 100  # Example limit
        
        return {
            "client_id": client_id,
            "category": category.value,
            "current_cost": current_cost,
            "cost_limit": cost_limit,
            "remaining": max(0, cost_limit - current_cost),
            "window_seconds": window_seconds,
            "reset_at": (datetime.now() + timedelta(seconds=window_seconds)).isoformat()
        }

class RateLimitCache:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.cache_ttl = 300  # 5 minutes default TTL
        
    def _generate_cache_key(
        self,
        client_id: str,
        category: RateLimitCategory,
        operation: str,
        params: Dict[str, Any]
    ) -> str:
        """Generate a cache key for a request."""
        # Sort params to ensure consistent keys
        param_str = json.dumps(params, sort_keys=True)
        key_data = f"{client_id}:{category.value}:{operation}:{param_str}"
        return f"{self.cache_key_prefix}{hashlib.md5(key_data.encode()).hexdigest()}"
        
    async def get_cached_response(
        self,
        client_id: str,
        category: RateLimitCategory,
        operation: str,
        params: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get a cached response if available."""
        cache_key = self._generate_cache_key(client_id, category, operation, params)
        data = await self.redis.get(cache_key)
        
        if not data:
            return None
            
        cached = json.loads(data)
        if datetime.fromisoformat(cached["expires_at"]) < datetime.now():
            await self.redis.delete(cache_key)
            return None
            
        return cached["response"]
        
    async def cache_response(
        self,
        client_id: str,
        category: RateLimitCategory,
        operation: str,
        params: Dict[str, Any],
        response: Dict[str, Any],
        ttl: Optional[int] = None
    ):
        """Cache a response."""
        cache_key = self._generate_cache_key(client_id, category, operation, params)
        expires_at = datetime.now() + timedelta(seconds=ttl or self.cache_ttl)
        
        cache_data = {
            "response": response,
            "expires_at": expires_at.isoformat(),
            "cached_at": datetime.now().isoformat()
        }
        
        await self.redis.setex(
            cache_key,
            ttl or self.cache_ttl,
            json.dumps(cache_data)
        )
        
    async def invalidate_cache(
        self,
        client_id: str,
        category: Optional[RateLimitCategory] = None,
        operation: Optional[str] = None
    ):
        """Invalidate cached responses."""
        pattern = f"{self.cache_key_prefix}*"
        if client_id:
            pattern = f"{self.cache_key_prefix}{client_id}:*"
        if category:
            pattern = f"{pattern}{category.value}:*"
        if operation:
            pattern = f"{pattern}{operation}:*"
            
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
            
    async def get_cache_stats(
        self,
        client_id: Optional[str] = None,
        category: Optional[RateLimitCategory] = None
    ) -> Dict[str, Any]:
        """Get cache statistics."""
        pattern = f"{self.cache_key_prefix}*"
        if client_id:
            pattern = f"{self.cache_key_prefix}{client_id}:*"
        if category:
            pattern = f"{pattern}{category.value}:*"
            
        keys = await self.redis.keys(pattern)
        total_size = 0
        total_items = len(keys)
        
        for key in keys:
            data = await self.redis.get(key)
            if data:
                total_size += len(data)
                
        return {
            "total_items": total_items,
            "total_size_bytes": total_size,
            "average_size_bytes": total_size / total_items if total_items > 0 else 0
        } 