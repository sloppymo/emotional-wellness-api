"""
OpenTelemetry integration for the Emotional Wellness API.

Provides distributed tracing, metrics, and structured logging integration
for HIPAA-compliant observability of the entire system.
"""

import logging
import os
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from contextlib import contextmanager
import time
import uuid

# OpenTelemetry imports - will be installed as dependencies
try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False

from structured_logging import get_logger

# Configure logger
logger = get_logger(__name__)

# Environment variables
OTEL_ENABLED = os.environ.get("OTEL_ENABLED", "false").lower() == "true"
OTEL_SERVICE_NAME = os.environ.get("OTEL_SERVICE_NAME", "emotional-wellness-api")
OTEL_EXPORTER_ENDPOINT = os.environ.get("OTEL_EXPORTER_ENDPOINT", "http://localhost:4318")


class ComponentName(str, Enum):
    """Component names for telemetry categorization."""
    COORDINATOR = "coordinator"
    MOSS_ADAPTER = "moss_adapter"
    PHI_LOGGER = "phi_logger"
    CRISIS_CLASSIFIER = "crisis_classifier"
    API_ROUTER = "api_router"
    SECURITY = "security"


class TelemetryManager:
    """
    Telemetry manager for tracing, metrics, and logging integration.
    
    Provides:
    - Distributed tracing with OpenTelemetry
    - Metrics collection for performance and error monitoring
    - Context propagation for cross-service tracing
    - HIPAA-compliant sanitized telemetry
    """
    
    def __init__(self):
        """Initialize telemetry manager."""
        self._logger = get_logger(f"{__name__}.TelemetryManager")
        self._tracer = None
        self._meter = None
        
        # Initialize OpenTelemetry if available and enabled
        if OPENTELEMETRY_AVAILABLE and OTEL_ENABLED:
            self._init_opentelemetry()
    
    def _init_opentelemetry(self):
        """Initialize OpenTelemetry SDK."""
        try:
            # Create a resource with service information
            resource = Resource.create({
                SERVICE_NAME: OTEL_SERVICE_NAME
            })
            
            # Set up tracing
            tracer_provider = TracerProvider(resource=resource)
            
            # Configure span exporter
            span_exporter = OTLPSpanExporter(
                endpoint=f"{OTEL_EXPORTER_ENDPOINT}/v1/traces"
            )
            span_processor = BatchSpanProcessor(span_exporter)
            tracer_provider.add_span_processor(span_processor)
            
            # Register tracer provider
            trace.set_tracer_provider(tracer_provider)
            self._tracer = trace.get_tracer(__name__)
            
            # Set up metrics
            meter_provider = MeterProvider(resource=resource)
            
            # Configure metrics exporter
            metrics_exporter = OTLPMetricExporter(
                endpoint=f"{OTEL_EXPORTER_ENDPOINT}/v1/metrics"
            )
            
            # Register meter provider
            metrics.set_meter_provider(meter_provider)
            self._meter = metrics.get_meter(__name__)
            
            # Create common metrics
            self._request_counter = self._meter.create_counter(
                name="api.requests",
                description="Count of API requests",
                unit="1"
            )
            
            self._request_duration = self._meter.create_histogram(
                name="api.request.duration",
                description="Duration of API requests",
                unit="ms"
            )
            
            self._crisis_counter = self._meter.create_counter(
                name="crisis.detection",
                description="Count of crisis detections",
                unit="1"
            )
            
            self._logger.info("OpenTelemetry initialized successfully")
            
        except Exception as e:
            self._logger.error(f"Failed to initialize OpenTelemetry: {e}")
    
    @contextmanager
    def span(self, name: str, component: ComponentName, attributes: Optional[Dict[str, Any]] = None):
        """
        Create a span for tracing.
        
        Args:
            name: Name of the span
            component: Component name enum
            attributes: Additional span attributes
            
        Yields:
            Span context manager
        """
        if not OPENTELEMETRY_AVAILABLE or not OTEL_ENABLED or not self._tracer:
            # Return no-op context if OpenTelemetry is not available
            yield None
            return
        
        # Create span
        try:
            # Start span
            span_attributes = {
                "component": component,
                "span.kind": "internal"
            }
            
            # Add custom attributes, sanitizing any PHI
            if attributes:
                for key, value in attributes.items():
                    # Skip PHI attributes
                    if key in ["user_id", "patient_id", "name", "email"]:
                        continue
                    span_attributes[key] = value
            
            with self._tracer.start_as_current_span(name, attributes=span_attributes) as span:
                start_time = time.time()
                
                try:
                    yield span
                finally:
                    # Record duration
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Record metrics
                    if self._meter and name.startswith("api."):
                        self._request_duration.record(
                            duration_ms,
                            {"component": component, "name": name}
                        )
        
        except Exception as e:
            self._logger.error(f"Error in span {name}: {e}")
            # Re-raise to not swallow exceptions
            raise
    
    def record_api_request(self, endpoint: str, method: str, status_code: int):
        """
        Record API request metrics.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            status_code: Response status code
        """
        if not OPENTELEMETRY_AVAILABLE or not OTEL_ENABLED or not self._meter:
            return
        
        try:
            self._request_counter.add(
                1,
                {
                    "endpoint": endpoint,
                    "method": method,
                    "status_code": status_code
                }
            )
        except Exception as e:
            self._logger.error(f"Failed to record API request metric: {e}")
    
    def record_crisis_detection(self, severity: int, confidence: float, risk_domains: List[str]):
        """
        Record crisis detection metrics.
        
        Args:
            severity: Crisis severity level
            confidence: Detection confidence score
            risk_domains: List of risk domains
        """
        if not OPENTELEMETRY_AVAILABLE or not OTEL_ENABLED or not self._meter:
            return
        
        try:
            self._crisis_counter.add(
                1,
                {
                    "severity": severity,
                    "confidence_bin": self._get_confidence_bin(confidence),
                    "risk_domain": ",".join(risk_domains)
                }
            )
        except Exception as e:
            self._logger.error(f"Failed to record crisis detection metric: {e}")
    
    def _get_confidence_bin(self, confidence: float) -> str:
        """Get confidence bin for metrics aggregation."""
        if confidence < 0.25:
            return "low"
        elif confidence < 0.5:
            return "medium-low"
        elif confidence < 0.75:
            return "medium-high"
        else:
            return "high"
    
    def get_trace_context(self) -> Dict[str, str]:
        """
        Get current trace context for propagation.
        
        Returns:
            Dictionary with trace context headers
        """
        if not OPENTELEMETRY_AVAILABLE or not OTEL_ENABLED:
            return {"traceparent": f"00-{uuid.uuid4().hex}{uuid.uuid4().hex[:16]}-0-01"}
        
        carrier = {}
        TraceContextTextMapPropagator().inject(carrier)
        return carrier


# Singleton instance
_telemetry_manager = TelemetryManager() if OTEL_ENABLED else None


def get_telemetry_manager() -> TelemetryManager:
    """Get the global telemetry manager instance."""
    global _telemetry_manager
    if _telemetry_manager is None and OTEL_ENABLED:
        _telemetry_manager = TelemetryManager()
    return _telemetry_manager


# Convenience functions
def record_span(name: str, component: ComponentName, attributes: Optional[Dict[str, Any]] = None):
    """Decorator to record a span for a function."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            manager = get_telemetry_manager()
            if not manager:
                return await func(*args, **kwargs)
            
            with manager.span(name, component, attributes):
                return await func(*args, **kwargs)
        return wrapper
    return decorator