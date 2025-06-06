"""
Prometheus Metrics for API Monitoring

This module provides Prometheus metrics integration for monitoring
the API's performance, health, and background task execution status.
"""

from typing import Dict, Any, Optional, List
import time
from fastapi import Request, Response
from prometheus_client import Counter, Gauge, Histogram, Summary, REGISTRY
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import prometheus_client

from ..structured_logging import get_logger

logger = get_logger(__name__)

# Initialize Prometheus metrics
REQUEST_COUNT = Counter(
    "api_request_total", 
    "Total count of requests by method and path",
    ["method", "path", "status_code"]
)

REQUEST_LATENCY = Histogram(
    "api_request_latency_seconds", 
    "Request latency in seconds by method and path",
    ["method", "path"],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1, 2.5, 5, 7.5, 10)
)

ACTIVE_REQUESTS = Gauge(
    "api_active_requests",
    "Number of active requests being processed"
)

# Task metrics
TASK_COUNT = Counter(
    "background_task_total",
    "Total count of background tasks by type and status",
    ["task_type", "status"]
)

TASK_LATENCY = Histogram(
    "background_task_latency_seconds",
    "Task execution time in seconds by task type",
    ["task_type"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0, 120.0, 300.0, 600.0)
)

TASK_QUEUE_SIZE = Gauge(
    "background_task_queue_size",
    "Size of task queues by queue name",
    ["queue_name"]
)

# MOSS and integration metrics
INTEGRATION_LATENCY = Histogram(
    "integration_latency_seconds",
    "Integration request latency in seconds by integration name",
    ["integration_name"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 1, 2.5, 5)
)

INTEGRATION_AVAILABILITY = Gauge(
    "integration_availability",
    "Integration availability status (1=available, 0=unavailable)",
    ["integration_name"]
)

# System health metrics
SYSTEM_HEALTH = Gauge(
    "system_health_status",
    "Overall system health status (1=healthy, 0=unhealthy)",
    ["component"]
)

# Memory usage metrics
MEMORY_USAGE = Gauge(
    "memory_usage_bytes",
    "Memory usage in bytes"
)

async def metrics_endpoint() -> Response:
    """
    Generate the metrics endpoint response for Prometheus.
    """
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

class PrometheusMiddleware:
    """
    FastAPI middleware for Prometheus metrics collection.
    
    Tracks request counts, latency, and active requests.
    """
    
    def __init__(self, app):
        self.app = app
        self._logger = get_logger(f"{__name__}.PrometheusMiddleware")
    
    async def __call__(self, request: Request, call_next):
        request_start_time = time.time()
        
        # Increment active requests gauge
        ACTIVE_REQUESTS.inc()
        
        try:
            # Process the request and capture the response
            response = await call_next(request)
            
            # Record request latency
            request_latency = time.time() - request_start_time
            
            # Clean path to avoid high cardinality
            path = request.url.path
            # Remove IDs from path to reduce cardinality
            if path.startswith("/api/v1"):
                path_parts = path.split("/")
                for i, part in enumerate(path_parts):
                    # Replace numeric IDs with {id}
                    if i > 3 and part.isdigit():
                        path_parts[i] = "{id}"
                path = "/".join(path_parts)
            
            # Record request count and latency
            REQUEST_COUNT.labels(
                method=request.method, 
                path=path,
                status_code=response.status_code
            ).inc()
            
            REQUEST_LATENCY.labels(
                method=request.method, 
                path=path
            ).observe(request_latency)
            
            return response
        except Exception as e:
            self._logger.error(f"Error handling request: {e}")
            raise
        finally:
            # Always decrement active requests gauge
            ACTIVE_REQUESTS.dec()

# Functions for updating task metrics
def record_task_start(task_type: str):
    """Record the start of a background task."""
    TASK_COUNT.labels(task_type=task_type, status="started").inc()

def record_task_success(task_type: str, duration_seconds: float):
    """Record a successful task completion."""
    TASK_COUNT.labels(task_type=task_type, status="success").inc()
    TASK_LATENCY.labels(task_type=task_type).observe(duration_seconds)

def record_task_failure(task_type: str):
    """Record a failed task."""
    TASK_COUNT.labels(task_type=task_type, status="failure").inc()

def update_queue_size(queue_name: str, size: int):
    """Update the queue size gauge."""
    TASK_QUEUE_SIZE.labels(queue_name=queue_name).set(size)

# Functions for updating integration metrics
def record_integration_request(integration_name: str, duration_seconds: float, available: bool):
    """Record an integration request."""
    INTEGRATION_LATENCY.labels(integration_name=integration_name).observe(duration_seconds)
    INTEGRATION_AVAILABILITY.labels(integration_name=integration_name).set(1 if available else 0)

# Functions for updating system health metrics
def update_system_health(component: str, healthy: bool):
    """Update system health status."""
    SYSTEM_HEALTH.labels(component=component).set(1 if healthy else 0)

def update_memory_usage(memory_bytes: int):
    """Update memory usage gauge."""
    MEMORY_USAGE.set(memory_bytes)

def initialize_metrics_collection(app) -> None:
    """Initialize metrics collection for the FastAPI app."""
    # Add Prometheus middleware
    app.add_middleware(PrometheusMiddleware)
    
    # Add metrics endpoint
    app.add_route("/metrics", metrics_endpoint)
    
    logger.info("Prometheus metrics collection initialized")
