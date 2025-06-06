from typing import Dict, Optional, Any
from datetime import datetime
import logging
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from prometheus_client import Counter, Gauge, Histogram, Summary
import json

# Prometheus metrics
rate_limit_traces = Counter(
    'rate_limit_traces_total',
    'Number of rate limit traces',
    ['operation', 'status']
)
rate_limit_span_duration = Histogram(
    'rate_limit_span_duration_seconds',
    'Duration of rate limit spans',
    ['operation'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0]
)
rate_limit_active_spans = Gauge(
    'rate_limit_active_spans',
    'Number of active rate limit spans',
    ['operation']
)
rate_limit_span_errors = Counter(
    'rate_limit_span_errors_total',
    'Number of rate limit span errors',
    ['operation', 'error_type']
)
rate_limit_span_attributes = Summary(
    'rate_limit_span_attributes',
    'Rate limit span attributes',
    ['operation', 'attribute']
)

class RateLimitTracing:
    """Distributed tracing and monitoring for rate limiting operations."""
    
    def __init__(
        self,
        service_name: str = "emotional-wellness-api",
        endpoint: Optional[str] = None,
        tracing_enabled: bool = True
    ):
        self.logger = logging.getLogger(__name__)
        self.tracing_enabled = tracing_enabled
        
        if tracing_enabled:
            self._setup_tracing(service_name, endpoint)
        else:
            self.tracer = None

    def _setup_tracing(self, service_name: str, endpoint: Optional[str]):
        """Setup OpenTelemetry tracing."""
        try:
            # Create tracer provider
            provider = TracerProvider()
            
            # Setup exporter
            if endpoint:
                exporter = OTLPSpanExporter(endpoint=endpoint)
            else:
                # Use default endpoint (localhost:4317)
                exporter = OTLPSpanExporter()
            
            # Add span processor
            provider.add_span_processor(BatchSpanProcessor(exporter))
            
            # Set the tracer provider
            trace.set_tracer_provider(provider)
            
            # Get tracer
            self.tracer = trace.get_tracer(service_name)
            
            # Instrument Redis
            RedisInstrumentor().instrument()
            
            self.logger.info("Tracing setup completed successfully")
        except Exception as e:
            self.logger.error(f"Failed to setup tracing: {e}")
            self.tracer = None

    def instrument_fastapi(self, app):
        """Instrument FastAPI application with OpenTelemetry."""
        if self.tracing_enabled and self.tracer:
            try:
                FastAPIInstrumentor.instrument_app(app)
                self.logger.info("FastAPI instrumentation completed successfully")
            except Exception as e:
                self.logger.error(f"Failed to instrument FastAPI: {e}")

    def start_span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        kind: trace.SpanKind = trace.SpanKind.INTERNAL
    ) -> Optional[trace.Span]:
        """Start a new span for rate limiting operations."""
        if not self.tracing_enabled or not self.tracer:
            return None
        
        try:
            span = self.tracer.start_span(
                name=name,
                kind=kind,
                attributes=attributes or {}
            )
            
            rate_limit_active_spans.labels(operation=name).inc()
            rate_limit_traces.labels(operation=name, status="started").inc()
            
            if attributes:
                for key, value in attributes.items():
                    rate_limit_span_attributes.labels(
                        operation=name,
                        attribute=key
                    ).observe(float(value) if isinstance(value, (int, float)) else 0.0)
            
            return span
        except Exception as e:
            self.logger.error(f"Failed to start span {name}: {e}")
            rate_limit_span_errors.labels(
                operation=name,
                error_type="start_span"
            ).inc()
            return None

    def end_span(
        self,
        span: Optional[trace.Span],
        status: StatusCode = StatusCode.OK,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """End a span with status and attributes."""
        if not span:
            return
        
        try:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
            
            span.set_status(Status(status))
            span.end()
            
            operation = span.name
            rate_limit_active_spans.labels(operation=operation).dec()
            rate_limit_traces.labels(
                operation=operation,
                status="completed"
            ).inc()
            
            duration = (datetime.now() - span.start_time).total_seconds()
            rate_limit_span_duration.labels(operation=operation).observe(duration)
        except Exception as e:
            self.logger.error(f"Failed to end span {span.name}: {e}")
            rate_limit_span_errors.labels(
                operation=span.name,
                error_type="end_span"
            ).inc()

    def record_exception(
        self,
        span: Optional[trace.Span],
        exception: Exception,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Record an exception in a span."""
        if not span:
            return
        
        try:
            span.record_exception(exception, attributes)
            span.set_status(Status(StatusCode.ERROR))
            
            operation = span.name
            rate_limit_span_errors.labels(
                operation=operation,
                error_type=type(exception).__name__
            ).inc()
        except Exception as e:
            self.logger.error(f"Failed to record exception in span {span.name}: {e}")

    def add_event(
        self,
        span: Optional[trace.Span],
        name: str,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Add an event to a span."""
        if not span:
            return
        
        try:
            span.add_event(name, attributes or {})
        except Exception as e:
            self.logger.error(f"Failed to add event to span {span.name}: {e}")

    def get_trace_context(self) -> Dict[str, str]:
        """Get current trace context for propagation."""
        if not self.tracing_enabled or not self.tracer:
            return {}
        
        try:
            current_span = trace.get_current_span()
            if not current_span:
                return {}
            
            context = trace.get_current_span().get_span_context()
            return {
                "trace_id": format(context.trace_id, "032x"),
                "span_id": format(context.span_id, "016x"),
                "trace_flags": format(context.trace_flags, "02x")
            }
        except Exception as e:
            self.logger.error(f"Failed to get trace context: {e}")
            return {}

    def cleanup(self):
        """Cleanup tracing resources."""
        if self.tracing_enabled and self.tracer:
            try:
                self.tracer.shutdown()
                self.logger.info("Tracing cleanup completed successfully")
            except Exception as e:
                self.logger.error(f"Failed to cleanup tracing: {e}") 