from enum import Enum
from typing import Dict, Tuple, Optional, List

class RateLimitConfig:
    """Configuration for a rate limit."""
    
    def __init__(self, limit: int, window_seconds: int, burst_multiplier: float = 1.0):
        self.limit = limit
        self.window_seconds = window_seconds
        self.burst_multiplier = burst_multiplier

class RateLimitCategory(Enum):
    """Categories of endpoints with different rate limit requirements."""
    
    # High-security PHI operations (strictest limits)
    PHI_OPERATION = "phi_operation"
    
    # Crisis intervention endpoints (moderate limits, but with burst allowance)
    CRISIS_INTERVENTION = "crisis_intervention"
    
    # Standard authenticated operations
    AUTHENTICATED = "authenticated"
    
    # Read-only operations (more lenient limits)
    READ_ONLY = "read_only"
    
    # Public endpoints (strictest unauthenticated limits)
    PUBLIC = "public"
    
    # System endpoints (health checks, metrics, etc.)
    SYSTEM = "system"

# Default rate limits for each category (requests per window)
# Format: (authenticated_limit, unauthenticated_limit, window_seconds)
DEFAULT_RATE_LIMITS: Dict[RateLimitCategory, Tuple[int, int, int]] = {
    RateLimitCategory.PHI_OPERATION: (30, 5, 60),      # 30/5 requests per minute
    RateLimitCategory.CRISIS_INTERVENTION: (50, 10, 60),  # 50/10 requests per minute
    RateLimitCategory.AUTHENTICATED: (100, 20, 60),    # 100/20 requests per minute
    RateLimitCategory.READ_ONLY: (200, 40, 60),        # 200/40 requests per minute
    RateLimitCategory.PUBLIC: (50, 10, 60),            # 50/10 requests per minute
    RateLimitCategory.SYSTEM: (300, 300, 60),          # 300/300 requests per minute
}

# Burst allowance multipliers for each category
# This allows temporary spikes above the base rate
BURST_MULTIPLIERS: Dict[RateLimitCategory, float] = {
    RateLimitCategory.PHI_OPERATION: 1.2,      # 20% burst allowance
    RateLimitCategory.CRISIS_INTERVENTION: 2.0,  # 100% burst allowance for crisis endpoints
    RateLimitCategory.AUTHENTICATED: 1.5,      # 50% burst allowance
    RateLimitCategory.READ_ONLY: 2.0,          # 100% burst allowance
    RateLimitCategory.PUBLIC: 1.2,             # 20% burst allowance
    RateLimitCategory.SYSTEM: 3.0,             # 300% burst allowance
}

# Endpoint path patterns for automatic category assignment
ENDPOINT_PATTERNS: Dict[str, RateLimitCategory] = {
    # PHI operations
    r"/v1/users/\d+/phi": RateLimitCategory.PHI_OPERATION,
    r"/v1/medical-records": RateLimitCategory.PHI_OPERATION,
    r"/v1/health-data": RateLimitCategory.PHI_OPERATION,
    
    # Crisis intervention
    r"/v1/crisis": RateLimitCategory.CRISIS_INTERVENTION,
    r"/v1/emergency": RateLimitCategory.CRISIS_INTERVENTION,
    r"/v1/hotline": RateLimitCategory.CRISIS_INTERVENTION,
    
    # Read-only operations
    r"/v1/emotional-state/read": RateLimitCategory.READ_ONLY,
    r"/v1/sessions/read": RateLimitCategory.READ_ONLY,
    r"/v1/symbolic/patterns": RateLimitCategory.READ_ONLY,
    
    # System endpoints
    r"/health": RateLimitCategory.SYSTEM,
    r"/metrics": RateLimitCategory.SYSTEM,
    r"/docs": RateLimitCategory.SYSTEM,
    r"/redoc": RateLimitCategory.SYSTEM,
    r"/openapi.json": RateLimitCategory.SYSTEM,
}

# Default category for unmatched endpoints
DEFAULT_CATEGORY = RateLimitCategory.AUTHENTICATED 