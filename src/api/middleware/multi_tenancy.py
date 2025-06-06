from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
from redis.asyncio import Redis
from enum import Enum

class TenantStatus(Enum):
    """Tenant status."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    INACTIVE = "inactive"

class TenantPlan(Enum):
    """Tenant plan types."""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

@dataclass
class TenantConfig:
    """Tenant configuration."""
    tenant_id: str
    name: str
    status: TenantStatus
    plan: TenantPlan
    rate_limits: Dict[str, Dict[str, Any]]
    custom_rules: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]

@dataclass
class TenantUsage:
    """Tenant usage statistics."""
    tenant_id: str
    total_requests: int
    rate_limited_requests: int
    unique_clients: int
    last_activity: datetime
    monthly_usage: int
    quota_usage_percent: float

class MultiTenancyManager:
    """Multi-tenancy support for rate limiting."""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.tenants_key = "rate_limit:tenants"
        self.tenant_usage_key = "rate_limit:tenant_usage:{}"
        self.tenant_clients_key = "rate_limit:tenant_clients:{}"
        self.tenant_quotas_key = "rate_limit:tenant_quotas"
        
        # Default plan configurations
        self.plan_configs = {
            TenantPlan.FREE: {
                "rate_limits": {
                    "authenticated": {"requests_per_minute": 100, "burst_multiplier": 1.2},
                    "unauthenticated": {"requests_per_minute": 20, "burst_multiplier": 1.1}
                },
                "monthly_quota": 10000,
                "max_clients": 10,
                "features": ["basic_rate_limiting"]
            },
            TenantPlan.BASIC: {
                "rate_limits": {
                    "authenticated": {"requests_per_minute": 1000, "burst_multiplier": 1.5},
                    "unauthenticated": {"requests_per_minute": 200, "burst_multiplier": 1.3}
                },
                "monthly_quota": 100000,
                "max_clients": 100,
                "features": ["basic_rate_limiting", "analytics", "alerts"]
            },
            TenantPlan.PREMIUM: {
                "rate_limits": {
                    "authenticated": {"requests_per_minute": 10000, "burst_multiplier": 2.0},
                    "unauthenticated": {"requests_per_minute": 2000, "burst_multiplier": 1.8}
                },
                "monthly_quota": 1000000,
                "max_clients": 1000,
                "features": ["basic_rate_limiting", "analytics", "alerts", "custom_rules", "geographic_controls"]
            },
            TenantPlan.ENTERPRISE: {
                "rate_limits": {
                    "authenticated": {"requests_per_minute": 100000, "burst_multiplier": 3.0},
                    "unauthenticated": {"requests_per_minute": 20000, "burst_multiplier": 2.5}
                },
                "monthly_quota": -1,  # Unlimited
                "max_clients": -1,    # Unlimited
                "features": ["all"]
            }
        }
    
    async def create_tenant(
        self,
        tenant_id: str,
        name: str,
        plan: TenantPlan,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> TenantConfig:
        """Create a new tenant."""
        # Get default config for plan
        plan_config = self.plan_configs[plan]
        
        # Merge with custom config if provided
        rate_limits = plan_config["rate_limits"].copy()
        if custom_config and "rate_limits" in custom_config:
            rate_limits.update(custom_config["rate_limits"])
        
        tenant_config = TenantConfig(
            tenant_id=tenant_id,
            name=name,
            status=TenantStatus.ACTIVE,
            plan=plan,
            rate_limits=rate_limits,
            custom_rules=custom_config.get("custom_rules", []) if custom_config else [],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata=custom_config.get("metadata", {}) if custom_config else {}
        )
        
        await self._store_tenant(tenant_config)
        return tenant_config
    
    async def get_tenant(self, tenant_id: str) -> Optional[TenantConfig]:
        """Get tenant configuration."""
        tenant_data = await self.redis.hget(self.tenants_key, tenant_id)
        if not tenant_data:
            return None
        
        data = json.loads(tenant_data)
        return TenantConfig(
            tenant_id=data["tenant_id"],
            name=data["name"],
            status=TenantStatus(data["status"]),
            plan=TenantPlan(data["plan"]),
            rate_limits=data["rate_limits"],
            custom_rules=data["custom_rules"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data["metadata"]
        )
    
    async def update_tenant(
        self,
        tenant_id: str,
        updates: Dict[str, Any]
    ) -> Optional[TenantConfig]:
        """Update tenant configuration."""
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return None
        
        # Apply updates
        if "name" in updates:
            tenant.name = updates["name"]
        if "status" in updates:
            tenant.status = TenantStatus(updates["status"])
        if "plan" in updates:
            tenant.plan = TenantPlan(updates["plan"])
            # Update rate limits to match new plan
            tenant.rate_limits = self.plan_configs[tenant.plan]["rate_limits"].copy()
        if "rate_limits" in updates:
            tenant.rate_limits.update(updates["rate_limits"])
        if "custom_rules" in updates:
            tenant.custom_rules = updates["custom_rules"]
        if "metadata" in updates:
            tenant.metadata.update(updates["metadata"])
        
        tenant.updated_at = datetime.now()
        
        await self._store_tenant(tenant)
        return tenant
    
    async def get_tenant_rate_limits(
        self,
        tenant_id: str,
        category: str
    ) -> Optional[Dict[str, Any]]:
        """Get rate limits for a tenant and category."""
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return None
        
        return tenant.rate_limits.get(category)
    
    async def check_tenant_quota(self, tenant_id: str) -> bool:
        """Check if tenant is within quota."""
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return False
        
        plan_config = self.plan_configs[tenant.plan]
        monthly_quota = plan_config["monthly_quota"]
        
        # Unlimited quota
        if monthly_quota == -1:
            return True
        
        # Check current usage
        usage = await self.get_tenant_usage(tenant_id)
        return usage.monthly_usage < monthly_quota
    
    async def register_client(self, tenant_id: str, client_id: str) -> bool:
        """Register a client for a tenant."""
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return False
        
        plan_config = self.plan_configs[tenant.plan]
        max_clients = plan_config["max_clients"]
        
        # Check client limit
        if max_clients != -1:
            clients_key = self.tenant_clients_key.format(tenant_id)
            current_clients = await self.redis.scard(clients_key)
            if current_clients >= max_clients:
                return False
        
        # Add client
        clients_key = self.tenant_clients_key.format(tenant_id)
        await self.redis.sadd(clients_key, client_id)
        return True
    
    async def unregister_client(self, tenant_id: str, client_id: str):
        """Unregister a client from a tenant."""
        clients_key = self.tenant_clients_key.format(tenant_id)
        await self.redis.srem(clients_key, client_id)
    
    async def get_tenant_clients(self, tenant_id: str) -> List[str]:
        """Get all clients for a tenant."""
        clients_key = self.tenant_clients_key.format(tenant_id)
        clients = await self.redis.smembers(clients_key)
        return [client.decode() for client in clients]
    
    async def record_tenant_request(
        self,
        tenant_id: str,
        client_id: str,
        is_rate_limited: bool = False
    ):
        """Record a request for tenant usage tracking."""
        usage_key = self.tenant_usage_key.format(tenant_id)
        
        # Update usage statistics
        current_usage = await self.redis.hgetall(usage_key)
        if current_usage:
            usage_data = {k.decode(): v.decode() for k, v in current_usage.items()}
        else:
            usage_data = {
                "total_requests": "0",
                "rate_limited_requests": "0",
                "unique_clients": "0",
                "monthly_usage": "0"
            }
        
        # Update counters
        usage_data["total_requests"] = str(int(usage_data["total_requests"]) + 1)
        if is_rate_limited:
            usage_data["rate_limited_requests"] = str(int(usage_data["rate_limited_requests"]) + 1)
        usage_data["last_activity"] = datetime.now().isoformat()
        
        # Update monthly usage (reset monthly if needed)
        current_month = datetime.now().strftime("%Y-%m")
        last_month = usage_data.get("last_month", current_month)
        if last_month != current_month:
            usage_data["monthly_usage"] = "1"
            usage_data["last_month"] = current_month
        else:
            usage_data["monthly_usage"] = str(int(usage_data["monthly_usage"]) + 1)
        
        # Store updated usage
        await self.redis.hset(usage_key, mapping=usage_data)
        
        # Add client to unique clients set
        await self.redis.sadd(f"{usage_key}:clients", client_id)
    
    async def get_tenant_usage(self, tenant_id: str) -> TenantUsage:
        """Get tenant usage statistics."""
        usage_key = self.tenant_usage_key.format(tenant_id)
        usage_data = await self.redis.hgetall(usage_key)
        
        if not usage_data:
            return TenantUsage(
                tenant_id=tenant_id,
                total_requests=0,
                rate_limited_requests=0,
                unique_clients=0,
                last_activity=datetime.now(),
                monthly_usage=0,
                quota_usage_percent=0.0
            )
        
        # Decode Redis data
        data = {k.decode(): v.decode() for k, v in usage_data.items()}
        
        # Get unique clients count
        unique_clients = await self.redis.scard(f"{usage_key}:clients")
        
        # Calculate quota usage
        tenant = await self.get_tenant(tenant_id)
        if tenant:
            plan_config = self.plan_configs[tenant.plan]
            monthly_quota = plan_config["monthly_quota"]
            if monthly_quota == -1:
                quota_usage_percent = 0.0
            else:
                quota_usage_percent = (int(data.get("monthly_usage", 0)) / monthly_quota) * 100
        else:
            quota_usage_percent = 0.0
        
        return TenantUsage(
            tenant_id=tenant_id,
            total_requests=int(data.get("total_requests", 0)),
            rate_limited_requests=int(data.get("rate_limited_requests", 0)),
            unique_clients=unique_clients,
            last_activity=datetime.fromisoformat(data.get("last_activity", datetime.now().isoformat())),
            monthly_usage=int(data.get("monthly_usage", 0)),
            quota_usage_percent=quota_usage_percent
        )
    
    async def list_tenants(self) -> List[TenantConfig]:
        """List all tenants."""
        all_tenants = await self.redis.hgetall(self.tenants_key)
        
        tenants = []
        for tenant_id, tenant_data in all_tenants.items():
            data = json.loads(tenant_data)
            tenants.append(TenantConfig(
                tenant_id=data["tenant_id"],
                name=data["name"],
                status=TenantStatus(data["status"]),
                plan=TenantPlan(data["plan"]),
                rate_limits=data["rate_limits"],
                custom_rules=data["custom_rules"],
                created_at=datetime.fromisoformat(data["created_at"]),
                updated_at=datetime.fromisoformat(data["updated_at"]),
                metadata=data["metadata"]
            ))
        
        return sorted(tenants, key=lambda x: x.created_at, reverse=True)
    
    async def get_billing_data(self, tenant_id: str) -> Dict[str, Any]:
        """Get billing data for a tenant."""
        tenant = await self.get_tenant(tenant_id)
        usage = await self.get_tenant_usage(tenant_id)
        
        if not tenant:
            return {}
        
        plan_config = self.plan_configs[tenant.plan]
        
        # Calculate costs (simplified)
        base_cost = {
            TenantPlan.FREE: 0,
            TenantPlan.BASIC: 49.99,
            TenantPlan.PREMIUM: 199.99,
            TenantPlan.ENTERPRISE: 999.99
        }[tenant.plan]
        
        # Calculate overage costs
        overage_cost = 0
        if plan_config["monthly_quota"] != -1 and usage.monthly_usage > plan_config["monthly_quota"]:
            overage_requests = usage.monthly_usage - plan_config["monthly_quota"]
            overage_cost = overage_requests * 0.001  # $0.001 per overage request
        
        return {
            "tenant_id": tenant_id,
            "plan": tenant.plan.value,
            "base_cost": base_cost,
            "overage_cost": overage_cost,
            "total_cost": base_cost + overage_cost,
            "monthly_usage": usage.monthly_usage,
            "quota": plan_config["monthly_quota"],
            "quota_usage_percent": usage.quota_usage_percent,
            "billing_period": datetime.now().strftime("%Y-%m")
        }
    
    async def _store_tenant(self, tenant: TenantConfig):
        """Store tenant configuration."""
        tenant_data = {
            "tenant_id": tenant.tenant_id,
            "name": tenant.name,
            "status": tenant.status.value,
            "plan": tenant.plan.value,
            "rate_limits": tenant.rate_limits,
            "custom_rules": tenant.custom_rules,
            "created_at": tenant.created_at.isoformat(),
            "updated_at": tenant.updated_at.isoformat(),
            "metadata": tenant.metadata
        }
        
        await self.redis.hset(
            self.tenants_key,
            tenant.tenant_id,
            json.dumps(tenant_data)
        ) 