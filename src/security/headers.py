"""
Security headers middleware for FastAPI applications.

Adds security-related HTTP headers to responses to protect against common web vulnerabilities.
Implements HIPAA-recommended security practices for web APIs.
"""

from typing import Callable, Dict
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from structured_logging import get_logger

# Configure logger
logger = get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security-related headers to HTTP responses.
    
    Implements OWASP security header recommendations and HIPAA best practices.
    """
    
    def __init__(
        self,
        app: FastAPI,
        hsts: bool = True,
        xss_protection: bool = True,
        content_protection: bool = True,
        frame_deny: bool = True,
        cache_control: bool = True,
        permissions_policy: bool = True,
        rate_limit_header: bool = True,
    ):
        """
        Initialize the middleware.
        
        Args:
            app: The FastAPI application
            hsts: Whether to add Strict-Transport-Security header
            xss_protection: Whether to add X-XSS-Protection header
            content_protection: Whether to add Content-Security-Policy header
            frame_deny: Whether to add X-Frame-Options header
            cache_control: Whether to add Cache-Control header
            permissions_policy: Whether to add Permissions-Policy header
            rate_limit_header: Whether to add rate limit headers
        """
        super().__init__(app)
        self.hsts = hsts
        self.xss_protection = xss_protection
        self.content_protection = content_protection
        self.frame_deny = frame_deny
        self.cache_control = cache_control
        self.permissions_policy = permissions_policy
        self.rate_limit_header = rate_limit_header
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and add security headers to the response.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            The processed response with security headers
        """
        response = await call_next(request)
        
        # HTTP Strict Transport Security
        if self.hsts:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # Protection against XSS attacks
        if self.xss_protection:
            response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Content Security Policy
        if self.content_protection:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "connect-src 'self'; "
                "font-src 'self'; "
                "object-src 'none'; "
                "media-src 'none'; "
                "frame-src 'none'"
            )
        
        # Prevent embedding in frames (clickjacking protection)
        if self.frame_deny:
            response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent content type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Cache control for sensitive data
        if self.cache_control:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
        
        # Permissions policy (formerly Feature-Policy)
        if self.permissions_policy:
            response.headers["Permissions-Policy"] = (
                "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
                "magnetometer=(), microphone=(), payment=(), usb=()"
            )
        
        # Add basic security headers for all responses
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Server"] = "Wellness-API"  # Obscure server details
        
        return response


def add_security_headers(app: FastAPI) -> None:
    """
    Add security headers middleware to a FastAPI application.
    
    Args:
        app: The FastAPI application to add the middleware to
    """
    app.add_middleware(SecurityHeadersMiddleware)
    logger.info("Added security headers middleware")
