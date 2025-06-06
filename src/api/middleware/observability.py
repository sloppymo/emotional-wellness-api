from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import json
import logging
from redis.asyncio import Redis
from opentelemetry import trace
from prometheus_client import Counter, Histogram, Gauge
from collections import defaultdict, deque

# Prometheus metrics
sli_success_rate = Gauge('rate_limit_sli_success_rate', 'Success rate SLI', ['service', 'endpoint', 'tenant'])
slo_error_budget = Gauge('rate_limit_slo_error_budget_remaining', 'Remaining error budget', ['slo_name', 'tenant'])
abuse_detections = Counter('rate_limit_abuse_detections_total', 'Abuse patterns detected', ['pattern_type', 'severity'])

class SLIType(Enum):
    """Service Level Indicator types."""
    SUCCESS_RATE = "success_rate"
    LATENCY = "latency"
    AVAILABILITY = "availability"

class AbusePatternType(Enum):
    """Types of abuse patterns."""
    RAPID_FIRE = "rapid_fire"
    CREDENTIAL_STUFFING = "credential_stuffing"
    SCRAPING = "scraping"
    DDOS = "ddos"

@dataclass
class SLIEvent:
    """Service Level Indicator event."""
    timestamp: datetime
    sli_name: str
    value: float
    success: bool
    latency: float
    tenant_id: str
    service: str
    endpoint: str

@dataclass
class AbusePattern:
    """Detected abuse pattern."""
    pattern_type: AbusePatternType
    severity: str
    client_id: str
    tenant_id: str
    detection_time: datetime
    evidence: Dict[str, Any]
    confidence_score: float

class RateLimitObservability:
    """Advanced observability system for rate limiting."""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.tracer = trace.get_tracer(__name__)
        self.logger = logging.getLogger(__name__)
        
        # Redis keys
        self.sli_events_key = "observability:sli_events:{}"
        self.slo_configs_key = "observability:slo_configs"
        self.abuse_patterns_key = "observability:abuse_patterns"
        self.error_budget_key = "observability:error_budget:{}"
        
        # Tracking for abuse detection
        self.request_tracking = defaultdict(lambda: deque(maxlen=1000))
    
    async def record_sli_event(
        self,
        sli_name: str,
        value: float,
        success: bool,
        latency: float,
        tenant_id: str,
        service: str,
        endpoint: str
    ):
        """Record a Service Level Indicator event."""
        with self.tracer.start_as_current_span("record_sli_event") as span:
            event = SLIEvent(
                timestamp=datetime.now(),
                sli_name=sli_name,
                value=value,
                success=success,
                latency=latency,
                tenant_id=tenant_id,
                service=service,
                endpoint=endpoint
            )
            
            # Store in Redis
            events_key = self.sli_events_key.format(sli_name)
            await self.redis.lpush(events_key, json.dumps(asdict(event), default=str))
            await self.redis.ltrim(events_key, 0, 9999)
            
            # Update metrics
            sli_success_rate.labels(
                service=service,
                endpoint=endpoint,
                tenant=tenant_id
            ).set(1.0 if success else 0.0)
            
            # Log for compliance
            self.logger.info(
                "SLI event recorded",
                extra={
                    "sli_name": sli_name,
                    "success": success,
                    "tenant_id": tenant_id,
                    "event_type": "sli_event",
                    "compliance_category": "hipaa_monitoring"
                }
            )
    
    async def detect_abuse_patterns(
        self,
        client_id: str,
        tenant_id: str,
        request_data: Dict[str, Any]
    ) -> List[AbusePattern]:
        """Detect abuse patterns in real-time."""
        patterns = []
        
        # Update tracking
        self.request_tracking[client_id].append({
            "timestamp": datetime.now(),
            "endpoint": request_data.get("endpoint"),
            "status_code": request_data.get("status_code"),
            "user_agent": request_data.get("user_agent")
        })
        
        # Check for rapid-fire pattern
        rapid_fire = await self._detect_rapid_fire(client_id, tenant_id)
        if rapid_fire:
            patterns.append(rapid_fire)
        
        # Check for credential stuffing
        credential_stuffing = await self._detect_credential_stuffing(client_id, tenant_id)
        if credential_stuffing:
            patterns.append(credential_stuffing)
        
        return patterns
    
    async def _detect_rapid_fire(self, client_id: str, tenant_id: str) -> Optional[AbusePattern]:
        """Detect rapid-fire request patterns."""
        requests = self.request_tracking[client_id]
        if len(requests) < 10:
            return None
        
        # Check for rapid requests in last 60 seconds
        now = datetime.now()
        recent_requests = [
            r for r in requests
            if (now - r["timestamp"]).total_seconds() <= 60
        ]
        
        if len(recent_requests) > 100:
            pattern = AbusePattern(
                pattern_type=AbusePatternType.RAPID_FIRE,
                severity="high",
                client_id=client_id,
                tenant_id=tenant_id,
                detection_time=now,
                evidence={
                    "requests_per_minute": len(recent_requests),
                    "threshold_exceeded": True
                },
                confidence_score=min(1.0, len(recent_requests) / 200)
            )
            
            await self._record_abuse_pattern(pattern)
            return pattern
        
        return None
    
    async def _detect_credential_stuffing(self, client_id: str, tenant_id: str) -> Optional[AbusePattern]:
        """Detect credential stuffing patterns."""
        requests = self.request_tracking[client_id]
        
        # Look for multiple auth failures
        auth_failures = [
            r for r in requests
            if r.get("endpoint", "").endswith("/auth") and r.get("status_code") == 401
        ]
        
        if len(auth_failures) > 10:
            pattern = AbusePattern(
                pattern_type=AbusePatternType.CREDENTIAL_STUFFING,
                severity="critical",
                client_id=client_id,
                tenant_id=tenant_id,
                detection_time=datetime.now(),
                evidence={
                    "auth_failures": len(auth_failures),
                    "pattern": "multiple_failed_authentications"
                },
                confidence_score=min(1.0, len(auth_failures) / 50)
            )
            
            await self._record_abuse_pattern(pattern)
            return pattern
        
        return None
    
    async def _record_abuse_pattern(self, pattern: AbusePattern):
        """Record detected abuse pattern."""
        # Store in Redis
        await self.redis.lpush(
            self.abuse_patterns_key,
            json.dumps(asdict(pattern), default=str)
        )
        
        # Update metrics
        abuse_detections.labels(
            pattern_type=pattern.pattern_type.value,
            severity=pattern.severity
        ).inc()
        
        # Log for HIPAA compliance
        self.logger.warning(
            "Abuse pattern detected",
            extra={
                "pattern_type": pattern.pattern_type.value,
                "severity": pattern.severity,
                "client_id": pattern.client_id,
                "tenant_id": pattern.tenant_id,
                "confidence_score": pattern.confidence_score,
                "event_type": "abuse_detection",
                "compliance_category": "hipaa_security_monitoring"
            }
        )
    
    async def get_slo_status(self, slo_name: str) -> Dict[str, Any]:
        """Get SLO status and error budget."""
        budget_key = self.error_budget_key.format(slo_name)
        budget_data = await self.redis.get(budget_key)
        
        if not budget_data:
            return {"status": "unknown", "error_budget": 1.0}
        
        budget = json.loads(budget_data)
        remaining = budget.get("remaining_budget", 1.0)
        
        if remaining > 0.5:
            status = "healthy"
        elif remaining > 0.2:
            status = "warning"
        else:
            status = "critical"
        
        return {
            "status": status,
            "error_budget": remaining,
            "events_processed": budget.get("events_processed", 0)
        } 