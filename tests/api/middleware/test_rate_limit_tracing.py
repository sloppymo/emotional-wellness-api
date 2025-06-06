import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import InMemorySpanExporter
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

from src.api.middleware.rate_limit_tracing import RateLimitTracing

@pytest.fixture
def span_exporter():
    """Create in-memory span exporter for testing."""
    return InMemorySpanExporter()

@pytest.fixture
def tracer_provider(span_exporter):
    """Create tracer provider with in-memory exporter."""
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(span_exporter))
    trace.set_tracer_provider(provider)
    return provider

@pytest.fixture
def rate_limit_tracing(tracer_provider, span_exporter):
    """Create RateLimitTracing instance with test configuration."""
    return RateLimitTracing(
        service_name="test-service",
        tracing_enabled=True
    )

@pytest.fixture
def app():
    """Create FastAPI test app."""
    return FastAPI()

class TestTracingSetup:
    """Test tracing setup and configuration."""
    
    def test_tracing_initialization(self, rate_limit_tracing):
        """Test tracing initialization."""
        assert rate_limit_tracing.tracing_enabled is True
        assert rate_limit_tracing.tracer is not None
    
    def test_tracing_disabled(self):
        """Test tracing when disabled."""
        tracing = RateLimitTracing(tracing_enabled=False)
        assert tracing.tracing_enabled is False
        assert tracing.tracer is None
    
    def test_fastapi_instrumentation(self, app, rate_limit_tracing):
        """Test FastAPI instrumentation."""
        rate_limit_tracing.instrument_fastapi(app)
        # Verify instrumentation by checking if middleware is added
        assert len(app.user_middleware) > 0

class TestSpanOperations:
    """Test span operations."""
    
    def test_start_span(self, rate_limit_tracing, span_exporter):
        """Test starting a new span."""
        attributes = {
            "test.attribute": "value",
            "test.number": 42
        }
        
        span = rate_limit_tracing.start_span(
            "test_span",
            attributes=attributes
        )
        
        assert span is not None
        assert span.name == "test_span"
        
        # Verify span was exported
        spans = span_exporter.get_finished_spans()
        assert len(spans) == 0  # Span not finished yet
        
        # Verify attributes were set
        assert span.attributes["test.attribute"] == "value"
        assert span.attributes["test.number"] == 42
    
    def test_end_span(self, rate_limit_tracing, span_exporter):
        """Test ending a span."""
        span = rate_limit_tracing.start_span("test_span")
        rate_limit_tracing.end_span(span)
        
        # Verify span was exported
        spans = span_exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].name == "test_span"
        assert spans[0].status.status_code == StatusCode.OK
    
    def test_end_span_with_error(self, rate_limit_tracing, span_exporter):
        """Test ending a span with error status."""
        span = rate_limit_tracing.start_span("test_span")
        rate_limit_tracing.end_span(span, StatusCode.ERROR)
        
        # Verify span was exported with error status
        spans = span_exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].status.status_code == StatusCode.ERROR
    
    def test_record_exception(self, rate_limit_tracing, span_exporter):
        """Test recording an exception in a span."""
        span = rate_limit_tracing.start_span("test_span")
        
        try:
            raise ValueError("Test error")
        except Exception as e:
            rate_limit_tracing.record_exception(span, e)
        
        rate_limit_tracing.end_span(span)
        
        # Verify exception was recorded
        spans = span_exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].status.status_code == StatusCode.ERROR
        assert len(spans[0].events) > 0
        assert "exception" in spans[0].events[0].name
    
    def test_add_event(self, rate_limit_tracing, span_exporter):
        """Test adding an event to a span."""
        span = rate_limit_tracing.start_span("test_span")
        rate_limit_tracing.add_event(
            span,
            "test_event",
            {"event.attribute": "value"}
        )
        rate_limit_tracing.end_span(span)
        
        # Verify event was added
        spans = span_exporter.get_finished_spans()
        assert len(spans) == 1
        assert len(spans[0].events) == 1
        assert spans[0].events[0].name == "test_event"
        assert spans[0].events[0].attributes["event.attribute"] == "value"

class TestTraceContext:
    """Test trace context operations."""
    
    def test_get_trace_context(self, rate_limit_tracing):
        """Test getting trace context."""
        span = rate_limit_tracing.start_span("test_span")
        context = rate_limit_tracing.get_trace_context()
        
        assert "trace_id" in context
        assert "span_id" in context
        assert "trace_flags" in context
        
        # Verify context values
        assert len(context["trace_id"]) == 32
        assert len(context["span_id"]) == 16
        assert len(context["trace_flags"]) == 2
    
    def test_get_trace_context_no_span(self, rate_limit_tracing):
        """Test getting trace context when no span is active."""
        context = rate_limit_tracing.get_trace_context()
        assert context == {}

class TestMetrics:
    """Test Prometheus metrics."""
    
    def test_span_metrics(self, rate_limit_tracing, span_exporter):
        """Test span-related metrics."""
        # Start and end multiple spans
        for i in range(3):
            span = rate_limit_tracing.start_span(f"test_span_{i}")
            rate_limit_tracing.end_span(span)
        
        # Verify metrics
        from prometheus_client import REGISTRY
        
        # Check trace counter
        trace_counter = REGISTRY.get_sample_value(
            'rate_limit_traces_total',
            {'operation': 'test_span_0', 'status': 'started'}
        )
        assert trace_counter == 1
        
        # Check active spans gauge
        active_spans = REGISTRY.get_sample_value(
            'rate_limit_active_spans',
            {'operation': 'test_span_0'}
        )
        assert active_spans == 0  # All spans ended
    
    def test_error_metrics(self, rate_limit_tracing, span_exporter):
        """Test error-related metrics."""
        span = rate_limit_tracing.start_span("test_span")
        
        try:
            raise ValueError("Test error")
        except Exception as e:
            rate_limit_tracing.record_exception(span, e)
        
        rate_limit_tracing.end_span(span)
        
        # Verify error metrics
        from prometheus_client import REGISTRY
        
        error_counter = REGISTRY.get_sample_value(
            'rate_limit_span_errors_total',
            {'operation': 'test_span', 'error_type': 'ValueError'}
        )
        assert error_counter == 1
    
    def test_duration_metrics(self, rate_limit_tracing, span_exporter):
        """Test duration-related metrics."""
        with patch('datetime.datetime') as mock_datetime:
            # Mock start time
            start_time = datetime(2024, 1, 1, 12, 0, 0)
            mock_datetime.now.return_value = start_time
            
            span = rate_limit_tracing.start_span("test_span")
            
            # Mock end time (1 second later)
            end_time = start_time + timedelta(seconds=1)
            mock_datetime.now.return_value = end_time
            
            rate_limit_tracing.end_span(span)
        
        # Verify duration metrics
        from prometheus_client import REGISTRY
        
        duration_bucket = REGISTRY.get_sample_value(
            'rate_limit_span_duration_seconds_bucket',
            {'operation': 'test_span', 'le': '1.0'}
        )
        assert duration_bucket == 1

class TestIntegration:
    """Integration tests for tracing."""
    
    @pytest.fixture
    def client(self, app, rate_limit_tracing):
        """Create test client with tracing middleware."""
        rate_limit_tracing.instrument_fastapi(app)
        
        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}
        
        return TestClient(app)
    
    def test_request_tracing(self, client, span_exporter):
        """Test tracing of HTTP requests."""
        response = client.get("/test")
        assert response.status_code == 200
        
        # Verify request was traced
        spans = span_exporter.get_finished_spans()
        assert len(spans) > 0
        
        # Find the request span
        request_span = next(
            span for span in spans
            if span.name == "GET /test"
        )
        
        assert request_span.status.status_code == StatusCode.OK
        assert "http.method" in request_span.attributes
        assert "http.url" in request_span.attributes
    
    def test_error_tracing(self, app, client, span_exporter):
        """Test tracing of HTTP errors."""
        @app.get("/error")
        async def error_endpoint():
            raise ValueError("Test error")
        
        response = client.get("/error")
        assert response.status_code == 500
        
        # Verify error was traced
        spans = span_exporter.get_finished_spans()
        error_span = next(
            span for span in spans
            if span.name == "GET /error"
        )
        
        assert error_span.status.status_code == StatusCode.ERROR
        assert len(error_span.events) > 0
        assert "exception" in error_span.events[0].name
    
    def test_trace_propagation(self, client, span_exporter):
        """Test trace context propagation."""
        # Start a span
        with trace.get_tracer("test").start_span("parent_span") as parent_span:
            # Make request with trace context
            headers = {
                "traceparent": f"00-{parent_span.get_span_context().trace_id:032x}-{parent_span.get_span_context().span_id:016x}-01"
            }
            response = client.get("/test", headers=headers)
            assert response.status_code == 200
        
        # Verify trace context was propagated
        spans = span_exporter.get_finished_spans()
        request_span = next(
            span for span in spans
            if span.name == "GET /test"
        )
        
        assert request_span.parent.span_id == parent_span.get_span_context().span_id
        assert request_span.context.trace_id == parent_span.get_span_context().trace_id

class TestCleanup:
    """Test cleanup operations."""
    
    def test_tracing_cleanup(self, rate_limit_tracing, tracer_provider):
        """Test tracing cleanup."""
        # Start a span
        span = rate_limit_tracing.start_span("test_span")
        rate_limit_tracing.end_span(span)
        
        # Cleanup
        rate_limit_tracing.cleanup()
        
        # Verify tracer was shut down
        assert tracer_provider.force_flush.called
        assert tracer_provider.shutdown.called 