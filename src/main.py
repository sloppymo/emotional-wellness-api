"""
Emotional Wellness Companion API
Main application entry point

This module initializes the FastAPI application, including middleware,
routes, and dependencies.

honestly most of this is middleware hell for hipaa compliance. proceed with caution
"""

#  ⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️
#  ⚠️                        ⚠️
#  ⚠️  HERE BE DRAGONS       ⚠️
#  ⚠️  MODIFY AT YOUR PERIL  ⚠️
#  ⚠️                        ⚠️
#  ⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️

import logging
import socketio
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse
from sqlalchemy import text
import uvicorn

# Import routers
from routers.auth import router as auth_router
from routers.users import router as users_router
from routers.assessments import router as assessments_router
from routers.interventions import router as interventions_router

# Import database and Redis utilities
from database.session import get_async_session
from cache.redis import get_redis_client
from redis.asyncio import Redis
from contextlib import asynccontextmanager
from sqlalchemy import text
from datetime import datetime

from api.version import API_VERSION
from api.middleware import RateLimiterMiddleware
from middleware.ip_whitelist import IPWhitelistMiddleware
from security.headers import add_security_headers
from routers import (
    emotional_state,
    sessions,
    users,
    health,
    symbolic,
    auth,
    clinical,
    clinical_analytics,
    longitudinal,
    security,
    alerts,
    metrics,
)
from accessibility.router import router as accessibility_router
from accessibility.integration import register_accessibility_features
from integration import router as integration_router
from dashboard import admin_router
from security.auth import get_api_key
from api.security import setup_security, get_current_user
from config.settings import get_settings
from observability import get_telemetry_manager
from monitoring.metrics import initialize_metrics_collection
from monitoring.metrics_collector import (
    start_metrics_collection,
    stop_metrics_collection,
    get_metrics_collector,
)
from monitoring.metrics_storage import get_metrics_storage
from monitoring.alert_manager import get_alert_manager
from .middleware.error_handling import error_handling_middleware
from .middleware.hipaa_compliance import HIPAAComplianceMiddleware
from .middleware.cors import get_cors_middleware
from .routers.tasks import router as tasks_router, sio as task_sio
from .dashboard import dashboard_router

# Setup logging - pretty standard, nothing fancy
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize settings - this is where all the env var magic happens
settings = get_settings()

# Redis client for rate limiting - because we can't trust humans not to spam us
redis_client: Redis = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """startup/shutdown sequence. if this fails, everything fails"""
    # Startup
    global redis_client
    # redis connection - critical for rate limiting crisis requests
    redis_client = Redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    # Initialize alert manager - sends emails when people are in crisis
    alert_manager = get_alert_manager()
    await alert_manager.initialize()

    # Initialize metrics collector - for showing off to stakeholders
    metrics_collector = get_metrics_collector()
    await metrics_collector.initialize()

    # Initialize metrics storage - where the numbers live
    metrics_storage = get_metrics_storage()
    await metrics_storage.initialize()

    # Start metrics collection - background task that never stops
    await start_metrics_collection()

    yield

    # Shutdown - pray everything closes cleanly
    logger.info("Shutting down Emotional Wellness API")

    # Stop metrics collection - kill the background task
    await stop_metrics_collection()

    # Close alert manager - stop sending emails
    await alert_manager.close()

    # Close metrics storage - disconnect from databases
    await metrics_storage.close()


app = FastAPI(
    title="Emotional Wellness Companion API",
    description="HIPAA-compliant symbolic emotional analysis API with crisis response",
    version=API_VERSION,
    docs_url=None,  # disabled because we need auth for docs (security theater)
    redoc_url=None,  # same deal
    lifespan=lifespan,
)

# Set up JWT security middleware - the auth bouncer
setup_security(app)

# Add security headers middleware - more security theater for auditors
add_security_headers(app)

# Add rate limiter middleware - crisis people bypass this, everyone else gets throttled
app.add_middleware(
    RateLimiterMiddleware,
    redis_client=redis_client,
    authenticated_limit=settings.RATE_LIMIT_AUTHENTICATED,
    unauthenticated_limit=settings.RATE_LIMIT_UNAUTHENTICATED,
    window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
)

# Initialize Prometheus metrics collection - for grafana dashboards nobody looks at
initialize_metrics_collection(app)

# Register accessibility features - middleware and router
register_accessibility_features(app)

# CORS configuration - tightly controlled for HIPAA compliance
# basically only our frontend can talk to us
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # intentionally limited
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Request-ID", "X-API-Version"],
)

# IP Whitelist middleware for administrative routes - only certain IPs can access admin stuff
app.add_middleware(
    IPWhitelistMiddleware,
    whitelist=settings.ADMIN_IP_WHITELIST,
    admin_routes=settings.ADMIN_ROUTE_PATTERNS,
)


# Middleware for request ID tracking and audit logging
@app.middleware("http")
async def add_request_id_and_audit(request: Request, call_next):
    """audit everything but don't log PHI. compliance people love this"""
    # HIPAA-compliant audit trail - metadata only, no PHI
    request_id = request.headers.get("X-Request-ID", None)
    # Log request metadata (no content) - the content might have personal info
    logger.info(f"Request {request_id}: {request.method} {request.url.path}")

    # Get telemetry manager if available - might not be there during startup
    telemetry = get_telemetry_manager()

    response = await call_next(request)

    # Record API request metrics - numbers for dashboards
    if telemetry:
        telemetry.record_api_request(
            endpoint=request.url.path, method=request.method, status_code=response.status_code
        )

    # Add response headers - api version for debugging, request id for tracing
    response.headers["X-API-Version"] = API_VERSION
    if request_id:
        response.headers["X-Request-ID"] = request_id

    # Add trace context for distributed tracing if available - opentelemetry magic
    if telemetry:
        trace_context = telemetry.get_trace_context()
        for header, value in trace_context.items():
            response.headers[header] = value

    return response


# Security exception handler - hide all the implementation details from users
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """catch everything and hide it from users. log internally for debugging"""
    # Log the error but don't expose details to client
    logger.error(f"Error processing request: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred"},  # vague on purpose
    )


# Register public routes - these don't need auth
app.include_router(health.router, tags=["System"])
app.include_router(accessibility_router, prefix="/accessibility", tags=["Accessibility"])
app.include_router(
    auth.router, tags=["Authentication"]
)  # auth endpoints obviously can't require auth
app.include_router(alerts.router, tags=["Alerts"])
app.include_router(metrics.router, tags=["Metrics"])
app.include_router(admin_router.router, tags=["Admin"])

# Routes with JWT security - everything else needs both user auth AND api key
# double auth because we're paranoid
secure_routes = [
    app.include_router(
        emotional_state.router,
        tags=["Emotional Processing"],
        dependencies=[Depends(get_current_user), Depends(get_api_key)],
    ),
    app.include_router(
        sessions.router,
        tags=["Sessions"],
        dependencies=[Depends(get_current_user), Depends(get_api_key)],
    ),
    app.include_router(
        users.router,
        prefix="/users",
        tags=["Users"],
        dependencies=[Depends(get_current_user), Depends(get_api_key)],
    ),
    app.include_router(
        symbolic.router,
        prefix="/symbolic",
        tags=["Symbolic Analysis"],
        dependencies=[Depends(get_current_user), Depends(get_api_key)],
    ),
    app.include_router(
        integration_router,
        prefix="/integrate",
        tags=["Integration"],
        dependencies=[Depends(get_current_user), Depends(get_api_key)],
    ),
    app.include_router(
        clinical.router,
        prefix="/clinical",
        tags=["Clinical Portal"],
        dependencies=[Depends(get_current_user), Depends(get_api_key)],
    ),
    app.include_router(
        clinical_analytics.router,
        tags=["Clinical Analytics"],
        dependencies=[Depends(get_current_user), Depends(get_api_key)],
    ),
    app.include_router(
        longitudinal.router,
        tags=["Longitudinal Analysis"],
        dependencies=[Depends(get_current_user), Depends(get_api_key)],
    ),
    app.include_router(
        security.router,
        tags=["Security"],
        dependencies=[Depends(get_current_user), Depends(get_api_key)],
    ),
]

app.include_router(
    sessions.router,
    prefix="/v1/session",
    tags=["Session Management"],
    dependencies=[Depends(get_api_key)],
)
app.include_router(
    users.router, prefix="/v1/users", tags=["User Management"], dependencies=[Depends(get_api_key)]
)


# Custom OpenAPI docs with security
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html(api_key: str = Depends(get_api_key)):
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=app.title + " - API Documentation",
        oauth2_redirect_url=None,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )


# Root route
@app.get("/", tags=["System"])
async def root():
    return {
        "name": "Emotional Wellness Companion API",
        "version": API_VERSION,
        "status": "operational",
        "docs": "/docs",
    }


# Initialize Socket.IO app
socket_app = socketio.ASGIApp(task_sio, app)

# Add middleware
app.middleware("http")(error_handling_middleware)
app.add_middleware(HIPAAComplianceMiddleware)
app.add_middleware(get_cors_middleware())

# Include routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(assessments_router)
app.include_router(interventions_router)
app.include_router(tasks_router)
app.include_router(dashboard_router)


# Health check endpoint with detailed status
@app.get("/health", tags=["health"])
async def health_check():
    """Enhanced health check endpoint with service status."""
    try:
        # Check database connectivity
        async with get_async_session() as session:
            await session.execute(text("SELECT 1"))
            db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "unhealthy"

    try:
        # Check Redis connectivity
        redis_client = await get_redis_client()
        await redis_client.ping()
        redis_status = "healthy"
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        redis_status = "unhealthy"

    try:
        # Check Celery workers
        from .tasks import celery_app

        inspector = celery_app.control.inspect()
        stats = inspector.stats()
        celery_status = "healthy" if stats else "unhealthy"
        worker_count = len(stats) if stats else 0
    except Exception as e:
        logger.error(f"Celery health check failed: {str(e)}")
        celery_status = "unhealthy"
        worker_count = 0

    overall_status = (
        "healthy"
        if all(status == "healthy" for status in [db_status, redis_status, celery_status])
        else "degraded"
    )

    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.VERSION,
        "services": {
            "database": db_status,
            "redis": redis_status,
            "celery": celery_status,
            "worker_count": worker_count,
        },
    }


if __name__ == "__main__":
    # For development only - use a proper ASGI server in production
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
