"""
Emotional Wellness Companion API
Main application entry point

This module initializes the FastAPI application, including middleware,
routes, and dependencies.
"""

import logging
from structured_logging import setup_logging
from fastapi import FastAPI, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
import uvicorn
from redis.asyncio import Redis
from contextlib import asynccontextmanager

from api.version import API_VERSION
from api.middleware import RateLimiterMiddleware
from middleware.ip_whitelist import IPWhitelistMiddleware
from routers import emotional_state, sessions, users, health, symbolic
from security.auth import get_api_key
from config.settings import get_settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize settings
settings = get_settings()

# Redis client for rate limiting
redis_client: Redis = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global redis_client
    redis_client = Redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )
    yield
    # Shutdown
    if redis_client:
        await redis_client.close()

app = FastAPI(
    title="Emotional Wellness Companion API",
    description="HIPAA-compliant symbolic emotional analysis API with crisis response",
    version=API_VERSION,
    docs_url=None,  # Disable default docs to use custom security
    redoc_url=None,  # Disable default redoc
    lifespan=lifespan,
)

# Add rate limiter middleware
app.add_middleware(
    RateLimiterMiddleware,
    redis_client=redis_client,
    authenticated_limit=settings.RATE_LIMIT_AUTHENTICATED,
    unauthenticated_limit=settings.RATE_LIMIT_UNAUTHENTICATED,
    window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
)

# CORS configuration - tightly controlled for HIPAA compliance
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Request-ID", "X-API-Version"],
)

# IP Whitelist middleware for administrative routes
app.add_middleware(
    IPWhitelistMiddleware,
    whitelist=settings.ADMIN_IP_WHITELIST,
    admin_routes=settings.ADMIN_ROUTE_PATTERNS
)

# Middleware for request ID tracking and audit logging
@app.middleware("http")
async def add_request_id_and_audit(request: Request, call_next):
    # HIPAA-compliant audit trail - metadata only, no PHI
    request_id = request.headers.get("X-Request-ID", None)
    # Log request metadata (no content)
    logger.info(f"Request {request_id}: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    # Add response headers
    response.headers["X-API-Version"] = API_VERSION
    if request_id:
        response.headers["X-Request-ID"] = request_id
    return response

# Security exception handler
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Log the error but don't expose details to client
    logger.error(f"Error processing request: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred"},
    )

# Register routers
app.include_router(health.router, tags=["System"])
app.include_router(emotional_state.router, tags=["Emotional Processing"], dependencies=[Depends(get_api_key)])
app.include_router(sessions.router, tags=["Sessions"], dependencies=[Depends(get_api_key)])
app.include_router(users.router, tags=["Users"], dependencies=[Depends(get_api_key)])
# Add symbolic router with prefix
app.include_router(
    symbolic.router,
    prefix="/symbolic",
    dependencies=[Depends(get_api_key)]
)
app.include_router(
    sessions.router, 
    prefix="/v1/session", 
    tags=["Session Management"],
    dependencies=[Depends(get_api_key)]
)
app.include_router(
    users.router, 
    prefix="/v1/users", 
    tags=["User Management"],
    dependencies=[Depends(get_api_key)]
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
        "docs": "/docs"
    }

if __name__ == "__main__":
    # For development only - use a proper ASGI server in production
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
