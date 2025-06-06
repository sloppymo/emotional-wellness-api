from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import logging
from redis.asyncio import Redis
from opentelemetry import trace, metrics
from opentelemetry.trace import Status, StatusCode
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from prometheus_client import Counter, Histogram, Gauge, Summary
import numpy as np
from collections import defaultdict, deque

# Prometheus metrics for observability
sli_success_rate = Gauge(
    'rate_limit_sli_success_rate',
    'Success rate SLI for rate limiting',
    ['service', 'endpoint', 'tenant']
)
sli_latency_p99 = Histogram(
    'rate_limit_sli_latency_p99',
    'P99 latency SLI for rate limiting',
    ['service', 'endpoint', 'tenant']
)
sli_availability = Gauge(
    'rate_limit_sli_availability',
    'Availability SLI for rate limiting',
    ['service', 'tenant']
)
slo_error_budget = Gauge(
    'rate_limit_slo_error_budget_remaining',
    'Remaining error budget for SLO',
    ['slo_name', 'tenant']
)
abuse_pattern_detections = Counter(
    'rate_limit_abuse_pattern_detections_total',
    'Number of abuse patterns detected',
    ['pattern_type', 'severity', 'tenant']
)

class SLIType(Enum):
    """Service Level Indicator types."""
    SUCCESS_RATE = "success_rate"
    LATENCY = "latency"
    AVAILABILITY = "availability"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"

class SLOStatus(Enum):
    """Service Level Objective status."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    BREACHED = "breached"

class AbusePatternType(Enum):
    """Types of abuse patterns."""
    RAPID_FIRE = "rapid_fire"
    CREDENTIAL_STUFFING = "credential_stuffing"
    SCRAPING = "scraping"
    DDoS = "ddos"
    API_ABUSE = "api_abuse"
    SUSPICIOUS_GEOGRAPHIC = "suspicious_geographic"
    UNUSUAL_USER_AGENT = "unusual_user_agent"

@dataclass
class SLITarget:
    """Service Level Indicator target definition."""
    name: str
    sli_type: SLIType
    target_value: float
    measurement_window: timedelta
    tenant_id: Optional[str] = None
    service: Optional[str] = None
    endpoint: Optional[str] = None

@dataclass
class SLO:
    """Service Level Objective definition."""
    name: str
    description: str
    sli_targets: List[SLITarget]
    error_budget_policy: Dict[str, Any]
    notification_thresholds: Dict[str, float]
    compliance_requirements: List[str]
    tenant_id: Optional[str] = None

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
    trace_id: Optional[str] = None
    span_id: Optional[str] = None

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
    recommended_action: str

class RateLimitObservability:
    """Advanced observability system for rate limiting with SLI/SLO management."""
    
    def __init__(
        self,
        redis_client: Redis,
        tracer: Optional[trace.Tracer] = None,
        meter_provider: Optional[MeterProvider] = None,
        structured_logger: Optional[logging.Logger] = None
    ):
        self.redis = redis_client
        self.tracer = tracer or trace.get_tracer(__name__)
        self.meter_provider = meter_provider
        self.logger = structured_logger or logging.getLogger(__name__)
        
        # Redis keys
        self.sli_events_key = "observability:sli_events:{}"
        self.slo_configs_key = "observability:slo_configs"
        self.slo_status_key = "observability:slo_status:{}"
        self.abuse_patterns_key = "observability:abuse_patterns"
        self.error_budget_key = "observability:error_budget:{}"
        
        # Abuse detection
        self.abuse_detectors = {
            AbusePatternType.RAPID_FIRE: self._detect_rapid_fire,
            AbusePatternType.CREDENTIAL_STUFFING: self._detect_credential_stuffing,
            AbusePatternType.SCRAPING: self._detect_scraping,
            AbusePatternType.DDoS: self._detect_ddos,
            AbusePatternType.API_ABUSE: self._detect_api_abuse,
            AbusePatternType.SUSPICIOUS_GEOGRAPHIC: self._detect_suspicious_geographic,
            AbusePatternType.UNUSUAL_USER_AGENT: self._detect_unusual_user_agent
        }
        
        # In-memory tracking for patterns
        self.request_tracking = defaultdict(lambda: deque(maxlen=1000))
        self.geographic_tracking = defaultdict(set)
        self.user_agent_tracking = defaultdict(int)
        
        # Initialize metrics
        if self.meter_provider:
            self.meter = self.meter_provider.get_meter(__name__)
            self._setup_custom_metrics()
    
    def _setup_custom_metrics(self):
        """Setup custom OpenTelemetry metrics."""
        self.sli_counter = self.meter.create_counter(
            "rate_limit_sli_events_total",
            description="Total SLI events recorded"
        )
        self.slo_gauge = self.meter.create_gauge(
            "rate_limit_slo_compliance",
            description="SLO compliance percentage"
        )
        self.abuse_counter = self.meter.create_counter(
            "rate_limit_abuse_detections_total",
            description="Total abuse patterns detected"
        )
    
    async def record_sli_event(
        self,
        sli_name: str,
        value: float,
        success: bool,
        latency: float,
        tenant_id: str,
        service: str,
        endpoint: str,
        trace_context: Optional[Dict[str, str]] = None
    ):
        """Record a Service Level Indicator event with distributed tracing context."""
        with self.tracer.start_as_current_span(
            "record_sli_event",
            attributes={
                "sli.name": sli_name,
                "sli.value": value,
                "sli.success": success,
                "sli.latency": latency,
                "tenant.id": tenant_id,
                "service.name": service,
                "endpoint.name": endpoint
            }
        ) as span:
            try:
                event = SLIEvent(
                    timestamp=datetime.now(),
                    sli_name=sli_name,
                    value=value,
                    success=success,
                    latency=latency,
                    tenant_id=tenant_id,
                    service=service,
                    endpoint=endpoint,
                    trace_id=trace_context.get("trace_id") if trace_context else None,
                    span_id=trace_context.get("span_id") if trace_context else None
                )
                
                # Store event in Redis
                events_key = self.sli_events_key.format(sli_name)
                await self.redis.lpush(events_key, json.dumps(asdict(event), default=str))
                await self.redis.ltrim(events_key, 0, 9999)  # Keep last 10k events
                await self.redis.expire(events_key, 86400 * 7)  # 7 days
                
                # Update Prometheus metrics
                sli_success_rate.labels(
                    service=service,
                    endpoint=endpoint,
                    tenant=tenant_id
                ).set(1.0 if success else 0.0)
                
                sli_latency_p99.labels(
                    service=service,
                    endpoint=endpoint,
                    tenant=tenant_id
                ).observe(latency)
                
                # Update OpenTelemetry metrics
                if self.meter_provider:
                    self.sli_counter.add(1, {
                        "sli_name": sli_name,
                        "tenant_id": tenant_id,
                        "success": str(success)
                    })
                
                # Check SLO compliance
                await self._check_slo_compliance(event)
                
                # Update structured logging
                self.logger.info(
                    "SLI event recorded",
                    extra={
                        "sli_name": sli_name,
                        "value": value,
                        "success": success,
                        "latency": latency,
                        "tenant_id": tenant_id,
                        "service": service,
                        "endpoint": endpoint,
                        "trace_id": event.trace_id,
                        "span_id": event.span_id,
                        "event_type": "sli_event",
                        "compliance_category": "hipaa_monitoring"
                    }
                )
                
                span.set_status(Status(StatusCode.OK))
                
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                self.logger.error(
                    f"Failed to record SLI event: {e}",
                    extra={
                        "error_type": "sli_recording_failure",
                        "sli_name": sli_name,
                        "tenant_id": tenant_id
                    }
                )
                raise
    
    async def create_slo(self, slo: SLO) -> bool:
        """Create a new Service Level Objective."""
        with self.tracer.start_as_current_span(
            "create_slo",
            attributes={
                "slo.name": slo.name,
                "tenant.id": slo.tenant_id or "global"
            }
        ) as span:
            try:
                slo_data = {
                    **asdict(slo),
                    "created_at": datetime.now().isoformat(),
                    "sli_targets": [asdict(target) for target in slo.sli_targets]
                }
                
                # Store SLO configuration
                slos_data = await self.redis.get(self.slo_configs_key)
                slos = json.loads(slos_data) if slos_data else {}
                slos[slo.name] = slo_data
                
                await self.redis.set(self.slo_configs_key, json.dumps(slos))
                
                # Initialize error budget
                await self._initialize_error_budget(slo)
                
                self.logger.info(
                    "SLO created",
                    extra={
                        "slo_name": slo.name,
                        "tenant_id": slo.tenant_id,
                        "sli_count": len(slo.sli_targets),
                        "event_type": "slo_created",
                        "compliance_category": "hipaa_slo_management"
                    }
                )
                
                span.set_status(Status(StatusCode.OK))
                return True
                
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                self.logger.error(f"Failed to create SLO: {e}")
                return False
    
    async def _check_slo_compliance(self, event: SLIEvent):
        """Check SLO compliance for an SLI event."""
        slos_data = await self.redis.get(self.slo_configs_key)
        if not slos_data:
            return
        
        slos = json.loads(slos_data)
        
        for slo_name, slo_data in slos.items():
            # Check if event applies to this SLO
            if slo_data.get("tenant_id") and slo_data["tenant_id"] != event.tenant_id:
                continue
            
            # Check each SLI target
            for sli_target in slo_data["sli_targets"]:
                if sli_target["name"] == event.sli_name:
                    await self._evaluate_sli_target(slo_name, sli_target, event)
    
    async def _evaluate_sli_target(self, slo_name: str, sli_target: Dict[str, Any], event: SLIEvent):
        """Evaluate an SLI target against an event."""
        target_type = SLIType(sli_target["sli_type"])
        target_value = sli_target["target_value"]
        
        # Determine if event meets target
        meets_target = False
        
        if target_type == SLIType.SUCCESS_RATE:
            meets_target = event.success
        elif target_type == SLIType.LATENCY:
            meets_target = event.latency <= target_value
        elif target_type == SLIType.ERROR_RATE:
            meets_target = event.success  # Success means no error
        elif target_type == SLIType.AVAILABILITY:
            meets_target = event.success
        elif target_type == SLIType.THROUGHPUT:
            meets_target = event.value >= target_value
        
        # Update error budget
        await self._update_error_budget(slo_name, meets_target)
        
        # Check for SLO breach
        error_budget_remaining = await self._get_error_budget_remaining(slo_name)
        
        if error_budget_remaining <= 0:
            await self._trigger_slo_breach_alert(slo_name, sli_target, event)
    
    async def _initialize_error_budget(self, slo: SLO):
        """Initialize error budget for an SLO."""
        budget_key = self.error_budget_key.format(slo.name)
        
        # Calculate initial error budget based on policy
        error_budget_policy = slo.error_budget_policy
        budget_percentage = error_budget_policy.get("budget_percentage", 0.1)  # 99.9% = 0.1% error budget
        window_hours = error_budget_policy.get("window_hours", 24 * 30)  # 30 days
        
        initial_budget = {
            "total_budget": budget_percentage,
            "remaining_budget": budget_percentage,
            "window_hours": window_hours,
            "reset_time": (datetime.now() + timedelta(hours=window_hours)).isoformat(),
            "events_processed": 0,
            "errors_consumed": 0
        }
        
        await self.redis.set(budget_key, json.dumps(initial_budget))
        await self.redis.expire(budget_key, int(window_hours * 3600))
    
    async def _update_error_budget(self, slo_name: str, meets_target: bool):
        """Update error budget for an SLO."""
        budget_key = self.error_budget_key.format(slo_name)
        budget_data = await self.redis.get(budget_key)
        
        if not budget_data:
            return
        
        budget = json.loads(budget_data)
        budget["events_processed"] += 1
        
        if not meets_target:
            budget["errors_consumed"] += 1
            # Recalculate remaining budget
            error_rate = budget["errors_consumed"] / budget["events_processed"]
            budget["remaining_budget"] = max(0, budget["total_budget"] - error_rate)
        
        await self.redis.set(budget_key, json.dumps(budget))
        
        # Update Prometheus metric
        slo_error_budget.labels(
            slo_name=slo_name,
            tenant=budget.get("tenant_id", "global")
        ).set(budget["remaining_budget"])
    
    async def _get_error_budget_remaining(self, slo_name: str) -> float:
        """Get remaining error budget for an SLO."""
        budget_key = self.error_budget_key.format(slo_name)
        budget_data = await self.redis.get(budget_key)
        
        if not budget_data:
            return 1.0
        
        budget = json.loads(budget_data)
        return budget.get("remaining_budget", 1.0)
    
    async def _trigger_slo_breach_alert(self, slo_name: str, sli_target: Dict[str, Any], event: SLIEvent):
        """Trigger alert for SLO breach."""
        self.logger.critical(
            "SLO breach detected",
            extra={
                "slo_name": slo_name,
                "sli_target": sli_target["name"],
                "tenant_id": event.tenant_id,
                "service": event.service,
                "endpoint": event.endpoint,
                "event_type": "slo_breach",
                "compliance_category": "hipaa_slo_breach",
                "alert_severity": "critical",
                "requires_immediate_attention": True
            }
        )
    
    # Abuse Pattern Detection Methods
    
    async def detect_abuse_patterns(
        self,
        client_id: str,
        tenant_id: str,
        request_data: Dict[str, Any]
    ) -> List[AbusePattern]:
        """Detect abuse patterns in real-time."""
        patterns = []
        
        # Update tracking data
        self.request_tracking[client_id].append({
            "timestamp": datetime.now(),
            "endpoint": request_data.get("endpoint"),
            "status_code": request_data.get("status_code"),
            "user_agent": request_data.get("user_agent"),
            "ip_address": request_data.get("ip_address"),
            "country": request_data.get("country")
        })
        
        # Run all detectors
        for pattern_type, detector in self.abuse_detectors.items():
            try:
                pattern = await detector(client_id, tenant_id, request_data)
                if pattern:
                    patterns.append(pattern)
                    await self._record_abuse_pattern(pattern)
            except Exception as e:
                self.logger.error(f"Error in abuse detector {pattern_type}: {e}")
        
        return patterns
    
    async def _detect_rapid_fire(
        self,
        client_id: str,
        tenant_id: str,
        request_data: Dict[str, Any]
    ) -> Optional[AbusePattern]:
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
        
        if len(recent_requests) > 100:  # More than 100 requests per minute
            confidence = min(1.0, len(recent_requests) / 200)
            
            return AbusePattern(
                pattern_type=AbusePatternType.RAPID_FIRE,
                severity="high" if len(recent_requests) > 200 else "medium",
                client_id=client_id,
                tenant_id=tenant_id,
                detection_time=now,
                evidence={
                    "requests_per_minute": len(recent_requests),
                    "time_window": "60_seconds",
                    "threshold_exceeded": len(recent_requests) > 100
                },
                confidence_score=confidence,
                recommended_action="temporary_rate_limit" if confidence > 0.8 else "monitor"
            )
        
        return None
    
    async def _detect_credential_stuffing(
        self,
        client_id: str,
        tenant_id: str,
        request_data: Dict[str, Any]
    ) -> Optional[AbusePattern]:
        """Detect credential stuffing patterns."""
        requests = self.request_tracking[client_id]
        
        # Look for multiple auth failures
        auth_failures = [
            r for r in requests
            if r.get("endpoint", "").endswith("/auth") and r.get("status_code") == 401
        ]
        
        if len(auth_failures) > 10:  # More than 10 auth failures
            confidence = min(1.0, len(auth_failures) / 50)
            
            return AbusePattern(
                pattern_type=AbusePatternType.CREDENTIAL_STUFFING,
                severity="critical",
                client_id=client_id,
                tenant_id=tenant_id,
                detection_time=datetime.now(),
                evidence={
                    "auth_failures": len(auth_failures),
                    "success_rate": 0.0,
                    "pattern": "multiple_failed_authentications"
                },
                confidence_score=confidence,
                recommended_action="block_client"
            )
        
        return None
    
    async def _detect_scraping(
        self,
        client_id: str,
        tenant_id: str,
        request_data: Dict[str, Any]
    ) -> Optional[AbusePattern]:
        """Detect scraping patterns."""
        requests = self.request_tracking[client_id]
        
        # Look for systematic endpoint access
        endpoints = set(r.get("endpoint") for r in requests)
        
        if len(endpoints) > 50:  # Accessing many different endpoints
            user_agents = set(r.get("user_agent") for r in requests)
            
            # Scraping often uses few user agents across many endpoints
            if len(user_agents) <= 3:
                confidence = min(1.0, len(endpoints) / 100)
                
                return AbusePattern(
                    pattern_type=AbusePatternType.SCRAPING,
                    severity="medium",
                    client_id=client_id,
                    tenant_id=tenant_id,
                    detection_time=datetime.now(),
                    evidence={
                        "unique_endpoints": len(endpoints),
                        "unique_user_agents": len(user_agents),
                        "endpoint_diversity": len(endpoints) / len(requests)
                    },
                    confidence_score=confidence,
                    recommended_action="rate_limit_aggressive"
                )
        
        return None
    
    async def _detect_ddos(
        self,
        client_id: str,
        tenant_id: str,
        request_data: Dict[str, Any]
    ) -> Optional[AbusePattern]:
        """Detect DDoS patterns."""
        requests = self.request_tracking[client_id]
        
        # Check for extremely high volume in short time
        now = datetime.now()
        last_minute = [
            r for r in requests
            if (now - r["timestamp"]).total_seconds() <= 60
        ]
        
        if len(last_minute) > 500:  # More than 500 requests per minute
            return AbusePattern(
                pattern_type=AbusePatternType.DDoS,
                severity="critical",
                client_id=client_id,
                tenant_id=tenant_id,
                detection_time=now,
                evidence={
                    "requests_per_minute": len(last_minute),
                    "volume_threshold_exceeded": True,
                    "attack_vector": "high_volume"
                },
                confidence_score=1.0,
                recommended_action="immediate_block"
            )
        
        return None
    
    async def _detect_api_abuse(
        self,
        client_id: str,
        tenant_id: str,
        request_data: Dict[str, Any]
    ) -> Optional[AbusePattern]:
        """Detect API abuse patterns."""
        requests = self.request_tracking[client_id]
        
        # Check for errors indicating abuse
        error_requests = [
            r for r in requests
            if r.get("status_code", 200) >= 400
        ]
        
        error_rate = len(error_requests) / len(requests) if requests else 0
        
        if error_rate > 0.5 and len(requests) > 20:  # High error rate
            return AbusePattern(
                pattern_type=AbusePatternType.API_ABUSE,
                severity="medium",
                client_id=client_id,
                tenant_id=tenant_id,
                detection_time=datetime.now(),
                evidence={
                    "error_rate": error_rate,
                    "total_requests": len(requests),
                    "error_requests": len(error_requests)
                },
                confidence_score=error_rate,
                recommended_action="monitor_closely"
            )
        
        return None
    
    async def _detect_suspicious_geographic(
        self,
        client_id: str,
        tenant_id: str,
        request_data: Dict[str, Any]
    ) -> Optional[AbusePattern]:
        """Detect suspicious geographic patterns."""
        requests = self.request_tracking[client_id]
        
        # Check for requests from multiple countries
        countries = set(r.get("country") for r in requests if r.get("country"))
        
        if len(countries) > 5:  # Requests from more than 5 countries
            return AbusePattern(
                pattern_type=AbusePatternType.SUSPICIOUS_GEOGRAPHIC,
                severity="medium",
                client_id=client_id,
                tenant_id=tenant_id,
                detection_time=datetime.now(),
                evidence={
                    "unique_countries": len(countries),
                    "countries": list(countries),
                    "geographic_diversity": "high"
                },
                confidence_score=min(1.0, len(countries) / 10),
                recommended_action="verify_identity"
            )
        
        return None
    
    async def _detect_unusual_user_agent(
        self,
        client_id: str,
        tenant_id: str,
        request_data: Dict[str, Any]
    ) -> Optional[AbusePattern]:
        """Detect unusual user agent patterns."""
        user_agent = request_data.get("user_agent", "")
        
        # Check for suspicious user agents
        suspicious_patterns = [
            "bot", "crawler", "spider", "scraper", "curl", "wget", "python", "requests"
        ]
        
        is_suspicious = any(pattern in user_agent.lower() for pattern in suspicious_patterns)
        
        if is_suspicious:
            return AbusePattern(
                pattern_type=AbusePatternType.UNUSUAL_USER_AGENT,
                severity="low",
                client_id=client_id,
                tenant_id=tenant_id,
                detection_time=datetime.now(),
                evidence={
                    "user_agent": user_agent,
                    "suspicious_keywords": [p for p in suspicious_patterns if p in user_agent.lower()],
                    "automated_tool_detected": True
                },
                confidence_score=0.7,
                recommended_action="flag_for_review"
            )
        
        return None
    
    async def _record_abuse_pattern(self, pattern: AbusePattern):
        """Record detected abuse pattern."""
        # Store in Redis
        await self.redis.lpush(
            self.abuse_patterns_key,
            json.dumps(asdict(pattern), default=str)
        )
        await self.redis.ltrim(self.abuse_patterns_key, 0, 9999)  # Keep last 10k
        
        # Update metrics
        abuse_pattern_detections.labels(
            pattern_type=pattern.pattern_type.value,
            severity=pattern.severity,
            tenant=pattern.tenant_id
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
                "recommended_action": pattern.recommended_action,
                "evidence": pattern.evidence,
                "event_type": "abuse_detection",
                "compliance_category": "hipaa_security_monitoring",
                "requires_investigation": pattern.severity in ["high", "critical"]
            }
        )
    
    async def get_slo_dashboard_data(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get SLO dashboard data for monitoring."""
        slos_data = await self.redis.get(self.slo_configs_key)
        if not slos_data:
            return {}
        
        slos = json.loads(slos_data)
        dashboard_data = {}
        
        for slo_name, slo_config in slos.items():
            if tenant_id and slo_config.get("tenant_id") != tenant_id:
                continue
            
            error_budget = await self._get_error_budget_remaining(slo_name)
            
            # Determine status
            if error_budget > 0.5:
                status = SLOStatus.HEALTHY
            elif error_budget > 0.2:
                status = SLOStatus.WARNING
            elif error_budget > 0:
                status = SLOStatus.CRITICAL
            else:
                status = SLOStatus.BREACHED
            
            dashboard_data[slo_name] = {
                "status": status.value,
                "error_budget_remaining": error_budget,
                "sli_targets": slo_config["sli_targets"],
                "compliance_requirements": slo_config.get("compliance_requirements", [])
            }
        
        return dashboard_data
    
    async def cleanup_old_data(self):
        """Cleanup old observability data."""
        # Clean up old SLI events (older than 7 days)
        cutoff = datetime.now() - timedelta(days=7)
        
        # This is a simplified cleanup - in production you'd want more sophisticated cleanup
        patterns = await self.redis.keys("observability:sli_events:*")
        for pattern in patterns:
            await self.redis.expire(pattern, 86400 * 7) 