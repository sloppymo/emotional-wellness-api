from typing import Optional, Tuple, Dict, Any, List
from datetime import datetime, timedelta
import time
import re
import logging
from fastapi import Request, Response, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware
from redis.asyncio import Redis
import ipaddress
from starlette.status import HTTP_429_TOO_MANY_REQUESTS, HTTP_403_FORBIDDEN
from ..config.settings import get_settings
from .rate_limit_types import (
    RateLimitCategory,
    DEFAULT_RATE_LIMITS,
    BURST_MULTIPLIERS,
    ENDPOINT_PATTERNS,
    DEFAULT_CATEGORY,
    RateLimitConfig
)
from .rate_limit_analytics import RateLimitAnalytics
from .rate_limit_access import RateLimitAccess
from .rate_limit_cost import RateLimitCost, RateLimitCache
from .rate_limit_advanced import RateLimitAdvanced
from .rate_limit_tracing import RateLimitTracing
from .observability_2 import RateLimitObservability2
from .business_intelligence import RateLimitBusinessIntelligence, UserSegment, JourneyStage
from .zero_trust_security import ZeroTrustRateLimitSecurity, SecurityContext, TrustLevel
import json
import jwt

settings = get_settings()
logger = logging.getLogger(__name__)

class RateLimitExceeded(HTTPException):
    def __init__(self, retry_after: int, category: RateLimitCategory, detail: Optional[str] = None):
        if not detail:
            detail = f"Rate limit exceeded for {category.value} endpoints"
            if category == RateLimitCategory.CRISIS_INTERVENTION:
                detail = "Crisis intervention rate limit exceeded. Please contact support if this is an emergency."
        super().__init__(
            status_code=HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers={"Retry-After": str(retry_after)}
        )

class RateLimitForbidden(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=HTTP_403_FORBIDDEN,
            detail=detail
        )

class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        redis_client: Redis,
        custom_limits: Optional[Dict[str, RateLimitConfig]] = None,
        burst_multipliers: Optional[Dict[str, float]] = None,
        custom_costs: Optional[Dict[str, int]] = None,
        enable_analytics: bool = True,
        enable_caching: bool = True,
        enable_cost_limits: bool = True,
        enable_circuit_breaker: bool = True,
        enable_token_bucket: bool = True,
        enable_geographic: bool = True,
        enable_ml: bool = True,
        enable_tracing: bool = True,
        tracing_endpoint: Optional[str] = None
    ):
        super().__init__(app)
        self.redis = redis_client
        self.custom_limits = custom_limits or {}
        self.burst_multipliers = burst_multipliers or {}
        self.custom_costs = custom_costs or {}
        
        # Initialize components
        self.analytics = RateLimitAnalytics(redis_client) if enable_analytics else None
        self.access = RateLimitAccess(redis_client)
        self.cost = RateLimitCost(redis_client) if enable_cost_limits else None
        self.cache = RateLimitCache(redis_client) if enable_caching else None
        self.advanced = RateLimitAdvanced(
            redis_client,
            enable_circuit_breaker=enable_circuit_breaker,
            enable_token_bucket=enable_token_bucket,
            enable_geographic=enable_geographic,
            enable_ml=enable_ml
        )
        self.tracing = RateLimitTracing(
            endpoint=tracing_endpoint,
            tracing_enabled=enable_tracing
        )
        
        # Initialize advanced systems
        self.observability2 = RateLimitObservability2(redis_client)
        self.business_intelligence = RateLimitBusinessIntelligence(redis_client)
        self.zero_trust = ZeroTrustRateLimitSecurity(redis_client)
        
        # Compile regex patterns for endpoint matching
        self.endpoint_patterns = {
            re.compile(pattern): category 
            for pattern, category in ENDPOINT_PATTERNS.items()
        }
        
        # Instrument FastAPI
        self.tracing.instrument_fastapi(app)

    def _get_category_for_path(self, path: str) -> RateLimitCategory:
        """Determine the rate limit category for a given path."""
        for pattern, category in self.endpoint_patterns.items():
            if pattern.match(path):
                return category
        return DEFAULT_CATEGORY

    async def _get_rate_limit_key(self, request: Request, category: RateLimitCategory) -> Tuple[str, int, int, int]:
        """Generate rate limit key based on IP, API key, and category."""
        client_ip = request.client.host
        
        # Check IP access
        if not await self.access.is_ip_allowed(client_ip):
            raise RateLimitForbidden(f"Access denied for IP {client_ip}")
        
        # Get API key from header if present
        api_key = request.headers.get("X-API-Key")
        
        # Check bypass token if present
        bypass_token = request.headers.get("X-RateLimit-Bypass")
        if bypass_token:
            if await self.access.validate_bypass_token(bypass_token, client_ip, category):
                return None, 0, 0, 0  # Bypass rate limiting
        
        # Base key on IP, API key, and category
        key_parts = [f"ratelimit:{category.value}:{client_ip}"]
        if api_key:
            key_parts.append(api_key)
            
        # Add user ID if authenticated
        if hasattr(request.state, "user") and request.state.user:
            key_parts.append(str(request.state.user.id))
            
        key = ":".join(key_parts)
        
        # Get limits for this category
        auth_limit, unauth_limit, window = self.rate_limits[category]
        
        # Determine limit based on authentication status
        limit = auth_limit if api_key or hasattr(request.state, "user") else unauth_limit
        
        # Apply burst multiplier
        burst_limit = int(limit * self.burst_multipliers[category])
        
        return key, limit, burst_limit, window

    async def _get_current_window(self, window_seconds: int) -> int:
        """Get the current time window."""
        return int(time.time() / window_seconds)

    async def _check_rate_limit(
        self, 
        key: str, 
        limit: int, 
        burst_limit: int,
        window_seconds: int,
        category: RateLimitCategory,
        client_id: str,
        operation: str
    ) -> Tuple[bool, int, int, bool, Optional[Dict[str, Any]]]:
        """Check if request is within rate limit and return remaining requests."""
        if key is None:  # Bypass token was used
            return True, 0, 0, False, None
            
        current_window = await self._get_current_window(window_seconds)
        window_key = f"{key}:{current_window}"
        burst_key = f"{key}:burst:{current_window}"
        
        # Check cost limits if enabled
        if self.cost:
            cost_allowed, current_cost, cost_limit = await self.cost.check_cost_limit(
                client_id,
                category,
                operation,
                cost_limit=100,  # Example limit, should be configurable
                custom_costs=self.custom_costs
            )
            if not cost_allowed:
                return False, 0, 0, False, {
                    "error": "cost_limit_exceeded",
                    "current_cost": current_cost,
                    "cost_limit": cost_limit
                }
        
        # Check quota if set
        quota_allowed = await self.access.increment_quota(
            client_id,
            category,
            period="daily"
        )
        if not quota_allowed:
            return False, 0, 0, False, {
                "error": "quota_exceeded",
                "period": "daily"
            }
        
        # Use Redis pipeline for atomic operations
        pipe = self.redis.pipeline()
        pipe.incr(window_key)
        pipe.incr(burst_key)
        pipe.expire(window_key, window_seconds)
        pipe.expire(burst_key, window_seconds)
        current, burst_current, _, _ = await pipe.execute()
        
        # Check both regular and burst limits
        is_within_limit = current <= limit
        is_within_burst = burst_current <= burst_limit
        
        remaining = max(0, limit - current)
        reset_time = (current_window + 1) * window_seconds
        
        # Record analytics if enabled
        if self.analytics:
            await self.analytics.record_request(
                category=category,
                client_id=client_id,
                is_authenticated=bool(key.split(":")[-1]),  # Check if user ID is present
                status="exceeded" if not is_within_limit else "allowed",
                remaining=remaining,
                used_burst=not is_within_limit and is_within_burst
            )
        
        return is_within_limit, remaining, reset_time, is_within_burst, None

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process the request with enhanced rate limiting."""
        client_id = self._get_client_id(request)
        category = self._determine_category(request)
        
        # Start tracing span
        span = self.tracing.start_span(
            "rate_limit_check",
            attributes={
                "client_id": client_id,
                "category": category.value,
                "path": request.url.path,
                "method": request.method
            }
        )
        
        try:
            # Check bypass token
            if await self._check_bypass_token(request, category):
                self.tracing.add_event(span, "bypass_token_valid")
                return await call_next(request)
            
            # Zero-Trust Security Assessment
            security_context = await self._build_security_context(request, client_id)
            trust_assessment = await self.zero_trust.evaluate_trust(
                security_context, request.url.path, request.method
            )
            
            # Enforce HIPAA compliance if needed
            hipaa_compliance = await self.zero_trust.enforce_hipaa_compliance(
                security_context, request.url.path, trust_assessment
            )
            if not hipaa_compliance["allowed"]:
                self.tracing.record_exception(
                    span,
                    RateLimitForbidden(f"HIPAA compliance violation: {', '.join(hipaa_compliance['restrictions'])}"),
                    {"client_id": client_id, "trust_level": trust_assessment.trust_level.value}
                )
                raise RateLimitForbidden(f"HIPAA compliance violation: {', '.join(hipaa_compliance['restrictions'])}")
            
            # Apply zero-trust rate limits
            base_limits = self._get_base_limits(category)
            adjusted_limits = await self.zero_trust.apply_zero_trust_rate_limits(
                trust_assessment, base_limits, request.url.path, security_context
            )
            
            # Check IP access
            if not await self._check_ip_access(request, client_id, category):
                self.tracing.record_exception(
                    span,
                    RateLimitForbidden("IP access denied"),
                    {"client_id": client_id, "category": category.value}
                )
                raise RateLimitForbidden("IP access denied")
            
            # Check circuit breaker
            if not self.advanced.check_circuit_breaker(request.url.path, category.value):
                self.tracing.record_exception(
                    span,
                    RateLimitForbidden("Circuit breaker open"),
                    {"endpoint": request.url.path, "category": category.value}
                )
                raise RateLimitForbidden("Circuit breaker open")
            
            # Check geographic limits
            geo_allowed, geo_reason = self.advanced.check_geographic_limits(
                request.client.host,
                category.value
            )
            if not geo_allowed:
                self.tracing.record_exception(
                    span,
                    RateLimitForbidden(geo_reason),
                    {"ip": request.client.host, "category": category.value}
                )
                raise RateLimitForbidden(geo_reason)
            
            # Check token bucket
            if self.advanced.enable_token_bucket:
                allowed, remaining = self.advanced.check_token_bucket(
                    client_id,
                    category.value
                )
                if not allowed:
                    self.tracing.record_exception(
                        span,
                        RateLimitExceeded("Token bucket empty", 60),
                        {"client_id": client_id, "category": category.value}
                    )
                    raise RateLimitExceeded("Token bucket empty", 60)
            
            # Check ML anomaly detection
            if self.advanced.enable_ml:
                features = self.advanced.extract_features({
                    "request_rate": await self._get_request_rate(client_id),
                    "error_rate": await self._get_error_rate(client_id),
                    "avg_response_time": await self._get_avg_response_time(client_id),
                    "unique_ips": await self._get_unique_ips(client_id),
                    "payload_size": len(await request.body()),
                    "time_of_day": datetime.now().hour + datetime.now().minute / 60.0,
                    "day_of_week": datetime.now().weekday()
                })
                
                is_anomaly, score = self.advanced.detect_anomaly(features, category.value)
                if is_anomaly:
                    self.tracing.record_exception(
                        span,
                        RateLimitForbidden("Anomaly detected"),
                        {
                            "client_id": client_id,
                            "category": category.value,
                            "anomaly_score": score
                        }
                    )
                    raise RateLimitForbidden("Anomaly detected")
            
            # Check cache
            if self.cache:
                cached_response = await self._check_cache(request, client_id, category)
                if cached_response:
                    self.tracing.add_event(span, "cache_hit")
                    return cached_response
            
            # Check rate limits
            allowed, remaining, reset_time = await self._check_rate_limits(
                request,
                client_id,
                category
            )
            
            if not allowed:
                retry_after = int((reset_time - datetime.now()).total_seconds())
                self.tracing.record_exception(
                    span,
                    RateLimitExceeded("Rate limit exceeded", retry_after),
                    {
                        "client_id": client_id,
                        "category": category.value,
                        "remaining": remaining,
                        "reset_time": reset_time.isoformat()
                    }
                )
                raise RateLimitExceeded("Rate limit exceeded", retry_after)
            
            # Check cost limits
            if self.cost:
                cost_allowed, cost_remaining = await self._check_cost_limits(
                    request,
                    client_id,
                    category
                )
                if not cost_allowed:
                    self.tracing.record_exception(
                        span,
                        RateLimitExceeded("Cost limit exceeded", 3600),
                        {
                            "client_id": client_id,
                            "category": category.value,
                            "remaining_cost": cost_remaining
                        }
                    )
                    raise RateLimitExceeded("Cost limit exceeded", 3600)
            
            # Process request
            response = await call_next(request)
            
            # Cache response if enabled
            if self.cache and response.status_code == 200:
                await self._cache_response(request, response, client_id, category)
            
            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(self._get_limit(category))
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(reset_time.timestamp()))
            
            if self.cost:
                response.headers["X-RateLimit-Cost-Remaining"] = str(cost_remaining)
            
            # Record analytics
            if self.analytics:
                await self._record_analytics(request, response, client_id, category)
            
            # Record business intelligence events
            await self._record_business_intelligence_event(
                request, response, client_id, category, security_context, trust_assessment
            )
            
            # Record success in circuit breaker
            self.advanced.record_circuit_breaker_success(request.url.path, category.value)
            
            # End span successfully
            self.tracing.end_span(
                span,
                attributes={
                    "remaining": remaining,
                    "reset_time": reset_time.isoformat(),
                    "status_code": response.status_code
                }
            )
            
            return response
            
        except Exception as e:
            # Record failure in circuit breaker
            self.advanced.record_circuit_breaker_failure(request.url.path, category.value)
            
            # End span with error
            self.tracing.record_exception(span, e)
            self.tracing.end_span(span, StatusCode.ERROR)
            
            raise

    async def _check_bypass_token(self, request: Request, category: RateLimitCategory) -> bool:
        """Check if request has a valid bypass token."""
        token = request.headers.get("X-RateLimit-Bypass")
        if not token:
            return False
        
        return self.access.validate_bypass_token(token, category.value)

    async def _check_ip_access(self, request: Request, client_id: str, category: RateLimitCategory) -> bool:
        """Check if IP is allowed to access the endpoint."""
        return self.access.is_ip_allowed(request.client.host, category.value)

    async def _check_cache(self, request: Request, client_id: str, category: RateLimitCategory) -> Optional[Response]:
        """Check if response is cached."""
        return self.cache.get_cached_response(
            client_id,
            category.value,
            request.url.path,
            request.query_params
        )

    async def _cache_response(self, request: Request, response: Response, client_id: str, category: RateLimitCategory):
        """Cache the response if caching is enabled."""
        if not self.cache:
            return
        
        await self.cache.cache_response(
            client_id,
            category.value,
            request.url.path,
            request.query_params,
            response.body,
            response.headers
        )

    async def _check_rate_limits(
        self,
        request: Request,
        client_id: str,
        category: RateLimitCategory
    ) -> Tuple[bool, int, datetime]:
        """Check rate limits for the request."""
        limit = self._get_limit(category)
        burst_multiplier = self.burst_multipliers.get(category.value, 1.5)
        
        key = f"rate_limit:{category.value}:{client_id}"
        pipe = self.redis.pipeline()
        
        now = datetime.now()
        window_start = now - timedelta(seconds=60)
        
        # Get current count
        pipe.zremrangebyscore(key, 0, window_start.timestamp())
        pipe.zcard(key)
        pipe.zadd(key, {str(now.timestamp()): now.timestamp()})
        pipe.expire(key, 60)
        
        _, current, _, _ = pipe.execute()
        
        # Calculate remaining and reset time
        remaining = max(0, int(limit * burst_multiplier) - current)
        reset_time = now + timedelta(seconds=60)
        
        return current < int(limit * burst_multiplier), remaining, reset_time

    async def _check_cost_limits(
        self,
        request: Request,
        client_id: str,
        category: RateLimitCategory
    ) -> Tuple[bool, int]:
        """Check cost limits for the request."""
        if not self.cost:
            return True, 0
        
        operation_cost = self.cost.get_operation_cost(
            category.value,
            request.url.path,
            self.custom_costs.get(request.url.path)
        )
        
        return self.cost.check_cost_limit(
            client_id,
            category.value,
            operation_cost
        )

    async def _record_analytics(self, request: Request, response: Response, client_id: str, category: RateLimitCategory):
        """Record analytics for the request."""
        if not self.analytics:
            return
        
        await self.analytics.record_request(
            client_id=client_id,
            category=category.value,
            endpoint=request.url.path,
            method=request.method,
            status_code=response.status_code,
            response_time=response.headers.get("X-Response-Time", 0),
            user_agent=request.headers.get("User-Agent"),
            ip_address=request.client.host
        )

    async def _get_request_rate(self, client_id: str) -> float:
        """Get request rate for a client."""
        key = f"rate_limit:analytics:request_rate:{client_id}"
        return float(self.redis.get(key) or 0.0)

    async def _get_error_rate(self, client_id: str) -> float:
        """Get error rate for a client."""
        key = f"rate_limit:analytics:error_rate:{client_id}"
        return float(self.redis.get(key) or 0.0)

    async def _get_avg_response_time(self, client_id: str) -> float:
        """Get average response time for a client."""
        key = f"rate_limit:analytics:avg_response_time:{client_id}"
        return float(self.redis.get(key) or 0.0)

    async def _get_unique_ips(self, client_id: str) -> int:
        """Get number of unique IPs for a client."""
        key = f"rate_limit:analytics:unique_ips:{client_id}"
        return int(self.redis.scard(key) or 0)

    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request."""
        # Try API key first
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key}"
        
        # Try user authentication
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                payload = jwt.decode(
                    token,
                    settings.JWT_SECRET_KEY,
                    algorithms=[settings.JWT_ALGORITHM]
                )
                return f"user:{payload['sub']}"
            except Exception:
                pass
        
        # Fallback to IP address
        return f"ip:{request.client.host}"

    def _determine_category(self, request: Request) -> RateLimitCategory:
        """Determine rate limit category for the request."""
        path = request.url.path
        
        # Check custom limits first
        for pattern, config in self.custom_limits.items():
            if path.startswith(pattern):
                return config.category
        
        # Default categorization
        if path.startswith("/api/v1/phi"):
            return RateLimitCategory.PHI_OPERATION
        elif path.startswith("/api/v1/crisis"):
            return RateLimitCategory.CRISIS_INTERVENTION
        elif path.startswith("/api/v1/auth"):
            return RateLimitCategory.AUTHENTICATED
        elif request.method in ["GET", "HEAD", "OPTIONS"]:
            return RateLimitCategory.READ_ONLY
        else:
            return RateLimitCategory.PUBLIC

    def _get_limit(self, category: RateLimitCategory) -> int:
        """Get rate limit for a category."""
        return settings.RATE_LIMITS.get(category.value, 100)

    def cleanup(self):
        """Cleanup resources."""
        if self.analytics:
            self.analytics.cleanup()
        if self.tracing:
            self.tracing.cleanup()
        if self.advanced:
            self.advanced.cleanup()
    
    async def _build_security_context(self, request: Request, client_id: str) -> SecurityContext:
        """Build security context for zero-trust evaluation."""
        # Extract user information
        user_id = client_id.split(":")[-1] if ":" in client_id else client_id
        tenant_id = getattr(request.state, "tenant_id", "default")
        
        # Build device fingerprint
        device_id = self._generate_device_id(request)
        
        # Get location from IP (simplified)
        location = await self._get_location_from_ip(request.client.host)
        
        # Extract clinical role from JWT if present
        clinical_role = await self._extract_clinical_role(request)
        
        # Check MFA status
        mfa_verified = await self._check_mfa_status(request)
        
        return SecurityContext(
            user_id=user_id,
            tenant_id=tenant_id,
            device_id=device_id,
            ip_address=request.client.host,
            user_agent=request.headers.get("User-Agent", ""),
            location=location,
            session_id=request.headers.get("X-Session-ID"),
            authentication_method=self._get_auth_method(request),
            mfa_verified=mfa_verified,
            device_fingerprint=self._generate_device_fingerprint(request),
            clinical_role=clinical_role,
            phi_access_level=await self._get_phi_access_level(request)
        )
    
    def _generate_device_id(self, request: Request) -> str:
        """Generate device ID from request headers."""
        fingerprint_data = f"{request.headers.get('User-Agent', '')}{request.headers.get('Accept-Language', '')}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]
    
    def _generate_device_fingerprint(self, request: Request) -> str:
        """Generate device fingerprint for security analysis."""
        fingerprint_elements = [
            request.headers.get("User-Agent", ""),
            request.headers.get("Accept", ""),
            request.headers.get("Accept-Language", ""),
            request.headers.get("Accept-Encoding", ""),
            str(request.client.host)
        ]
        fingerprint_string = "|".join(fingerprint_elements)
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()
    
    async def _get_location_from_ip(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Get location information from IP address."""
        # This would integrate with a GeoIP service
        # Simplified implementation
        return {
            "country": "US",
            "region": "CA",
            "city": "San Francisco",
            "latitude": 37.7749,
            "longitude": -122.4194,
            "is_proxy": False,
            "is_healthcare_facility": False
        }
    
    async def _extract_clinical_role(self, request: Request) -> Optional[str]:
        """Extract clinical role from JWT token."""
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        try:
            token = auth_header.split(" ")[1]
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
                options={"verify_exp": False}  # For demo purposes
            )
            return payload.get("clinical_role")
        except Exception:
            return None
    
    async def _check_mfa_status(self, request: Request) -> bool:
        """Check if MFA was used for authentication."""
        # Check for MFA headers or session data
        mfa_verified = request.headers.get("X-MFA-Verified")
        if mfa_verified and mfa_verified.lower() == "true":
            return True
        
        # Check JWT claims
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                payload = jwt.decode(
                    token,
                    settings.JWT_SECRET_KEY,
                    algorithms=[settings.JWT_ALGORITHM],
                    options={"verify_exp": False}
                )
                return payload.get("mfa_verified", False)
            except Exception:
                pass
        
        return False
    
    def _get_auth_method(self, request: Request) -> Optional[str]:
        """Get authentication method used."""
        if request.headers.get("X-API-Key"):
            return "api_key"
        elif request.headers.get("Authorization"):
            return "bearer_token"
        else:
            return None
    
    async def _get_phi_access_level(self, request: Request) -> Optional[str]:
        """Get PHI access level for the user."""
        clinical_role = await self._extract_clinical_role(request)
        if not clinical_role:
            return None
        
        role_mapping = {
            "psychiatrist": "FULL",
            "therapist": "THERAPEUTIC",
            "crisis_counselor": "CRISIS_ONLY",
            "patient": "SELF_ONLY",
            "administrator": "ADMINISTRATIVE"
        }
        
        return role_mapping.get(clinical_role, "SELF_ONLY")
    
    def _get_base_limits(self, category: RateLimitCategory) -> Dict[str, int]:
        """Get base rate limits for a category."""
        # This would normally come from configuration
        base_limits = {
            "requests_per_minute": self._get_limit(category),
            "requests_per_hour": self._get_limit(category) * 60,
            "requests_per_day": self._get_limit(category) * 60 * 24
        }
        return base_limits
    
    async def _record_business_intelligence_event(
        self,
        request: Request,
        response: Response,
        client_id: str,
        category: RateLimitCategory,
        security_context: SecurityContext,
        trust_assessment: TrustAssessment
    ):
        """Record business intelligence events for customer journey tracking."""
        # Determine user segment
        segment = self._map_clinical_role_to_segment(security_context.clinical_role)
        
        # Determine journey stage based on behavior
        journey_stage = self._determine_journey_stage(
            client_id, request.url.path, response.status_code
        )
        
        # Extract emotional state if available
        emotional_state = request.headers.get("X-Emotional-State")
        
        # Calculate session duration (simplified)
        session_duration = None
        if hasattr(request.state, "session_start"):
            session_duration = (datetime.now() - request.state.session_start).total_seconds()
        
        # Calculate satisfaction score based on response
        satisfaction_score = self._calculate_satisfaction_score(response, trust_assessment)
        
        # Record the journey event
        await self.business_intelligence.record_journey_event(
            user_id=security_context.user_id,
            tenant_id=security_context.tenant_id,
            segment=segment,
            stage=journey_stage,
            event_type="api_request",
            rate_limit_context={
                "category": category.value,
                "trust_level": trust_assessment.trust_level.value,
                "trust_score": trust_assessment.trust_score,
                "endpoint": request.url.path,
                "method": request.method
            },
            emotional_state=emotional_state,
            session_duration=session_duration,
            api_calls_made=1,
            rate_limited=response.status_code == 429,
            satisfaction_score=satisfaction_score
        )
    
    def _map_clinical_role_to_segment(self, clinical_role: Optional[str]) -> UserSegment:
        """Map clinical role to user segment."""
        if not clinical_role:
            return UserSegment.INDIVIDUAL_USERS
        
        role_mapping = {
            "psychiatrist": UserSegment.HEALTHCARE_PROVIDERS,
            "therapist": UserSegment.THERAPISTS,
            "crisis_counselor": UserSegment.CRISIS_COUNSELORS,
            "wellness_coach": UserSegment.WELLNESS_COACHES,
            "researcher": UserSegment.RESEARCHERS,
            "administrator": UserSegment.ENTERPRISE_CLIENTS,
            "patient": UserSegment.INDIVIDUAL_USERS
        }
        
        return role_mapping.get(clinical_role, UserSegment.INDIVIDUAL_USERS)
    
    def _determine_journey_stage(
        self, client_id: str, endpoint: str, status_code: int
    ) -> JourneyStage:
        """Determine customer journey stage based on behavior."""
        # This would normally involve more sophisticated analysis
        # For now, use simple heuristics
        
        if "/auth" in endpoint:
            return JourneyStage.DISCOVERY
        elif "/onboarding" in endpoint:
            return JourneyStage.ONBOARDING
        elif status_code >= 400:
            return JourneyStage.CHURN_RISK
        elif "/api/v1/crisis" in endpoint:
            return JourneyStage.POWER_USE
        else:
            return JourneyStage.REGULAR_USE
    
    def _calculate_satisfaction_score(
        self, response: Response, trust_assessment: TrustAssessment
    ) -> float:
        """Calculate satisfaction score based on response and trust."""
        base_score = 3.0  # Neutral
        
        # Adjust based on status code
        if response.status_code == 200:
            base_score = 4.0
        elif response.status_code == 429:
            base_score = 2.0  # Rate limited = dissatisfied
        elif response.status_code >= 500:
            base_score = 1.0  # Server error = very dissatisfied
        elif response.status_code >= 400:
            base_score = 2.5  # Client error = somewhat dissatisfied
        
        # Adjust based on trust level
        if trust_assessment.trust_level == TrustLevel.VERIFIED_TRUST:
            base_score += 0.5
        elif trust_assessment.trust_level == TrustLevel.UNTRUSTED:
            base_score -= 1.0
        
        # Clamp to 1-5 range
        return max(1.0, min(5.0, base_score)) 