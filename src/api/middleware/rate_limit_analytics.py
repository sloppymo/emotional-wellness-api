from prometheus_client import Counter, Histogram, Gauge
from typing import Dict, Optional
import time
from datetime import datetime, timedelta
from redis.asyncio import Redis
import json
from .rate_limit_types import RateLimitCategory

# Prometheus metrics
RATE_LIMIT_REQUESTS = Counter(
    'rate_limit_requests_total',
    'Total number of rate limit checks',
    ['category', 'status', 'is_authenticated']
)

RATE_LIMIT_BURST_USAGE = Counter(
    'rate_limit_burst_usage_total',
    'Number of times burst limits were used',
    ['category', 'is_authenticated']
)

RATE_LIMIT_EXCEEDED = Counter(
    'rate_limit_exceeded_total',
    'Number of times rate limits were exceeded',
    ['category', 'is_authenticated']
)

RATE_LIMIT_LATENCY = Histogram(
    'rate_limit_check_duration_seconds',
    'Time spent checking rate limits',
    ['category']
)

RATE_LIMIT_REMAINING = Gauge(
    'rate_limit_remaining',
    'Remaining requests in current window',
    ['category', 'client_id']
)

class RateLimitAnalytics:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.analytics_ttl = 86400  # 24 hours for analytics data
        
    async def record_request(
        self,
        category: RateLimitCategory,
        client_id: str,
        is_authenticated: bool,
        status: str,
        remaining: int,
        used_burst: bool = False
    ):
        """Record a rate limit check result."""
        timestamp = int(time.time())
        
        # Update Prometheus metrics
        RATE_LIMIT_REQUESTS.labels(
            category=category.value,
            status=status,
            is_authenticated=str(is_authenticated)
        ).inc()
        
        RATE_LIMIT_REMAINING.labels(
            category=category.value,
            client_id=client_id
        ).set(remaining)
        
        if used_burst:
            RATE_LIMIT_BURST_USAGE.labels(
                category=category.value,
                is_authenticated=str(is_authenticated)
            ).inc()
            
        if status == "exceeded":
            RATE_LIMIT_EXCEEDED.labels(
                category=category.value,
                is_authenticated=str(is_authenticated)
            ).inc()
        
        # Store detailed analytics in Redis
        analytics_key = f"ratelimit:analytics:{category.value}:{client_id}:{timestamp}"
        analytics_data = {
            "timestamp": timestamp,
            "category": category.value,
            "client_id": client_id,
            "is_authenticated": is_authenticated,
            "status": status,
            "remaining": remaining,
            "used_burst": used_burst
        }
        
        await self.redis.setex(
            analytics_key,
            self.analytics_ttl,
            json.dumps(analytics_data)
        )
        
    async def get_client_analytics(
        self,
        client_id: str,
        category: Optional[RateLimitCategory] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict:
        """Get analytics for a specific client."""
        if not start_time:
            start_time = datetime.now() - timedelta(hours=24)
        if not end_time:
            end_time = datetime.now()
            
        start_ts = int(start_time.timestamp())
        end_ts = int(end_time.timestamp())
        
        # Get all analytics keys for the client
        pattern = f"ratelimit:analytics:{category.value if category else '*'}:{client_id}:*"
        keys = await self.redis.keys(pattern)
        
        analytics = []
        for key in keys:
            data = await self.redis.get(key)
            if data:
                entry = json.loads(data)
                if start_ts <= entry["timestamp"] <= end_ts:
                    analytics.append(entry)
                    
        return {
            "client_id": client_id,
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "total_requests": len(analytics),
            "exceeded_count": sum(1 for a in analytics if a["status"] == "exceeded"),
            "burst_usage_count": sum(1 for a in analytics if a["used_burst"]),
            "details": analytics
        }
        
    async def get_category_analytics(
        self,
        category: RateLimitCategory,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict:
        """Get analytics for a specific category."""
        if not start_time:
            start_time = datetime.now() - timedelta(hours=24)
        if not end_time:
            end_time = datetime.now()
            
        start_ts = int(start_time.timestamp())
        end_ts = int(end_time.timestamp())
        
        # Get all analytics keys for the category
        pattern = f"ratelimit:analytics:{category.value}:*"
        keys = await self.redis.keys(pattern)
        
        analytics = []
        for key in keys:
            data = await self.redis.get(key)
            if data:
                entry = json.loads(data)
                if start_ts <= entry["timestamp"] <= end_ts:
                    analytics.append(entry)
                    
        return {
            "category": category.value,
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "total_requests": len(analytics),
            "unique_clients": len(set(a["client_id"] for a in analytics)),
            "exceeded_count": sum(1 for a in analytics if a["status"] == "exceeded"),
            "burst_usage_count": sum(1 for a in analytics if a["used_burst"]),
            "authenticated_requests": sum(1 for a in analytics if a["is_authenticated"]),
            "unauthenticated_requests": sum(1 for a in analytics if not a["is_authenticated"])
        }
        
    async def cleanup_old_analytics(self):
        """Clean up analytics data older than the TTL."""
        # Redis will automatically clean up expired keys
        # This method is for explicit cleanup if needed
        pattern = "ratelimit:analytics:*"
        keys = await self.redis.keys(pattern)
        for key in keys:
            ttl = await self.redis.ttl(key)
            if ttl < 0:  # Key has expired
                await self.redis.delete(key) 