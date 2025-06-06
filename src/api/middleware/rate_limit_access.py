from typing import Set, Dict, Optional, List
import ipaddress
from redis.asyncio import Redis
import json
from datetime import datetime, timedelta
from .rate_limit_types import RateLimitCategory

class RateLimitAccess:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.whitelist_key = "ratelimit:whitelist"
        self.blacklist_key = "ratelimit:blacklist"
        self.quota_key_prefix = "ratelimit:quota:"
        self.bypass_tokens_key = "ratelimit:bypass_tokens"
        
    async def is_ip_allowed(self, ip: str) -> bool:
        """Check if an IP is allowed (not blacklisted)."""
        # Check blacklist first
        if await self.is_ip_blacklisted(ip):
            return False
            
        # If whitelist is empty, all non-blacklisted IPs are allowed
        whitelist = await self.get_whitelist()
        if not whitelist:
            return True
            
        # Otherwise, IP must be in whitelist
        return ip in whitelist
        
    async def is_ip_blacklisted(self, ip: str) -> bool:
        """Check if an IP is blacklisted."""
        blacklist = await self.get_blacklist()
        return ip in blacklist
        
    async def get_whitelist(self) -> Set[str]:
        """Get the current IP whitelist."""
        data = await self.redis.get(self.whitelist_key)
        return set(json.loads(data)) if data else set()
        
    async def get_blacklist(self) -> Set[str]:
        """Get the current IP blacklist."""
        data = await self.redis.get(self.blacklist_key)
        return set(json.loads(data)) if data else set()
        
    async def add_to_whitelist(self, ip: str, cidr: bool = False):
        """Add an IP or CIDR to the whitelist."""
        whitelist = await self.get_whitelist()
        if cidr:
            # Add all IPs in the CIDR range
            network = ipaddress.ip_network(ip, strict=False)
            whitelist.update(str(ip) for ip in network.hosts())
        else:
            whitelist.add(ip)
        await self.redis.set(self.whitelist_key, json.dumps(list(whitelist)))
        
    async def add_to_blacklist(self, ip: str, cidr: bool = False):
        """Add an IP or CIDR to the blacklist."""
        blacklist = await self.get_blacklist()
        if cidr:
            # Add all IPs in the CIDR range
            network = ipaddress.ip_network(ip, strict=False)
            blacklist.update(str(ip) for ip in network.hosts())
        else:
            blacklist.add(ip)
        await self.redis.set(self.blacklist_key, json.dumps(list(blacklist)))
        
    async def remove_from_whitelist(self, ip: str):
        """Remove an IP from the whitelist."""
        whitelist = await self.get_whitelist()
        whitelist.discard(ip)
        await self.redis.set(self.whitelist_key, json.dumps(list(whitelist)))
        
    async def remove_from_blacklist(self, ip: str):
        """Remove an IP from the blacklist."""
        blacklist = await self.get_blacklist()
        blacklist.discard(ip)
        await self.redis.set(self.blacklist_key, json.dumps(list(blacklist)))
        
    async def set_quota(
        self,
        client_id: str,
        category: RateLimitCategory,
        quota: int,
        period: str = "daily"
    ):
        """Set a quota for a client in a specific category."""
        quota_key = f"{self.quota_key_prefix}{client_id}:{category.value}:{period}"
        quota_data = {
            "quota": quota,
            "period": period,
            "reset_at": self._get_next_reset_time(period).isoformat()
        }
        await self.redis.set(quota_key, json.dumps(quota_data))
        
    async def get_quota(
        self,
        client_id: str,
        category: RateLimitCategory,
        period: str = "daily"
    ) -> Optional[Dict]:
        """Get the current quota for a client."""
        quota_key = f"{self.quota_key_prefix}{client_id}:{category.value}:{period}"
        data = await self.redis.get(quota_key)
        if not data:
            return None
            
        quota_data = json.loads(data)
        reset_at = datetime.fromisoformat(quota_data["reset_at"])
        
        # Check if quota needs to be reset
        if datetime.now() >= reset_at:
            await self.reset_quota(client_id, category, period)
            return await self.get_quota(client_id, category, period)
            
        return quota_data
        
    async def reset_quota(
        self,
        client_id: str,
        category: RateLimitCategory,
        period: str = "daily"
    ):
        """Reset the quota for a client."""
        await self.set_quota(client_id, category, 0, period)
        
    async def increment_quota(
        self,
        client_id: str,
        category: RateLimitCategory,
        amount: int = 1,
        period: str = "daily"
    ) -> bool:
        """Increment the quota usage. Returns True if within quota."""
        quota_data = await self.get_quota(client_id, category, period)
        if not quota_data:
            return True  # No quota set
            
        current_usage = quota_data.get("usage", 0)
        if current_usage + amount > quota_data["quota"]:
            return False
            
        quota_key = f"{self.quota_key_prefix}{client_id}:{category.value}:{period}"
        quota_data["usage"] = current_usage + amount
        await self.redis.set(quota_key, json.dumps(quota_data))
        return True
        
    async def create_bypass_token(
        self,
        client_id: str,
        category: Optional[RateLimitCategory] = None,
        expires_in: int = 3600  # 1 hour
    ) -> str:
        """Create a temporary bypass token for rate limits."""
        token = f"bypass_{client_id}_{int(datetime.now().timestamp())}"
        token_data = {
            "client_id": client_id,
            "category": category.value if category else None,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(seconds=expires_in)).isoformat()
        }
        
        await self.redis.setex(
            f"{self.bypass_tokens_key}:{token}",
            expires_in,
            json.dumps(token_data)
        )
        return token
        
    async def validate_bypass_token(
        self,
        token: str,
        client_id: str,
        category: Optional[RateLimitCategory] = None
    ) -> bool:
        """Validate a bypass token."""
        token_key = f"{self.bypass_tokens_key}:{token}"
        data = await self.redis.get(token_key)
        if not data:
            return False
            
        token_data = json.loads(data)
        if token_data["client_id"] != client_id:
            return False
            
        if category and token_data["category"] and token_data["category"] != category.value:
            return False
            
        return True
        
    def _get_next_reset_time(self, period: str) -> datetime:
        """Get the next reset time for a quota period."""
        now = datetime.now()
        if period == "daily":
            return (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "weekly":
            days_until_monday = (7 - now.weekday()) % 7
            return (now + timedelta(days=days_until_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "monthly":
            if now.month == 12:
                next_month = now.replace(year=now.year + 1, month=1)
            else:
                next_month = now.replace(month=now.month + 1)
            return next_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            raise ValueError(f"Invalid period: {period}") 