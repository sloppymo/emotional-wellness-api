"""
API Security Middleware for Emotional Wellness API

Provides JWT authentication, rate limiting, and request validation
middleware for FastAPI routes with HIPAA compliance.
"""

import time
from datetime import datetime, timedelta
import os
import jwt
import hashlib
from typing import Dict, List, Optional, Any, Callable
from fastapi import Depends, FastAPI, HTTPException, Request, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import asyncio
from pydantic import BaseModel, Field, ConfigDict
import logging
from structured_logging import get_logger

# Configure logger
logger = get_logger(__name__)

# Security configuration from environment
JWT_SECRET = os.environ.get("JWT_SECRET_KEY", "dev-secret-replace-in-production")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_MINUTES = int(os.environ.get("JWT_EXPIRATION_MINUTES", "60"))
RATE_LIMIT_ENABLED = os.environ.get("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_REQUESTS = int(os.environ.get("RATE_LIMIT_REQUESTS", "60"))  # requests per minute
RATE_LIMIT_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW", "60"))  # window in seconds


class TokenData(BaseModel):
    """JWT token data model."""
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    user_id: str = Field(..., description="User identifier")
    role: str = Field("user", description="User role")
    exp: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES))
    scope: List[str] = Field(default_factory=list, description="Permission scopes")
    

class SecurityManager:
    """
    Security manager for API authentication and authorization.
    
    Provides:
    - JWT token generation and validation
    - Role-based access control
    - Request tracing for audit purposes
    """
    
    def __init__(self):
        """Initialize security manager."""
        self._logger = get_logger(f"{__name__}.SecurityManager")
        self._token_blacklist = set()
        
    def create_token(self, user_id: str, role: str = "user", 
                     scopes: List[str] = None) -> str:
        """
        Create a JWT token for the user.
        
        Args:
            user_id: User identifier
            role: User role (user, admin, clinician)
            scopes: Permission scopes
            
        Returns:
            JWT token string
        """
        token_data = TokenData(
            user_id=user_id,
            role=role,
            scope=scopes or []
        )
        
        to_encode = token_data.model_dump()
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return encoded_jwt
    
    def validate_token(self, token: str) -> TokenData:
        """
        Validate a JWT token and extract claims.
        
        Args:
            token: JWT token string
            
        Returns:
            TokenData with validated claims
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            # Check if token is blacklisted
            if token in self._token_blacklist:
                raise HTTPException(
                    status_code=401,
                    detail="Token has been revoked"
                )
                
            # Decode and validate token
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            
            # Convert payload to TokenData
            token_data = TokenData(**payload)
            
            # Check expiration
            if datetime.utcnow() > token_data.exp:
                raise HTTPException(
                    status_code=401,
                    detail="Token has expired"
                )
                
            return token_data
            
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=401,
                detail="Could not validate credentials"
            )
    
    def revoke_token(self, token: str) -> None:
        """
        Revoke a JWT token.
        
        Args:
            token: JWT token to revoke
        """
        self._token_blacklist.add(token)
        
        # Clean up old tokens from blacklist periodically
        # In production, this would use a persistent store with TTL


# Singleton instance
_security_manager = SecurityManager()

# FastAPI security scheme
security = HTTPBearer()

def get_security_manager() -> SecurityManager:
    """Get the global security manager instance."""
    global _security_manager
    return _security_manager


class RateLimiter:
    """
    Rate limiter for API endpoints.
    
    Uses a token bucket algorithm to limit request rates.
    """
    
    def __init__(self):
        """Initialize rate limiter."""
        self._logger = get_logger(f"{__name__}.RateLimiter")
        self._requests = {}  # {key: [timestamps]}
        
    async def is_rate_limited(self, key: str) -> bool:
        """
        Check if a request should be rate limited.
        
        Args:
            key: Rate limiting key (e.g., IP or user_id)
            
        Returns:
            True if request should be limited, False otherwise
        """
        if not RATE_LIMIT_ENABLED:
            return False
            
        # Clean up old entries
        now = time.time()
        if key in self._requests:
            self._requests[key] = [ts for ts in self._requests[key] if now - ts < RATE_LIMIT_WINDOW]
            
        # Check rate limit
        if key not in self._requests:
            self._requests[key] = []
            
        if len(self._requests[key]) >= RATE_LIMIT_REQUESTS:
            self._logger.warning(f"Rate limit exceeded for {key}")
            return True
            
        # Add request timestamp
        self._requests[key].append(now)
        return False


# Singleton instance
_rate_limiter = RateLimiter()

def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    global _rate_limiter
    return _rate_limiter


# Dependency for JWT authentication
async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Security(security)
    ) -> TokenData:
    """
    Validate JWT token and return current user.
    
    Args:
        credentials: HTTP Authorization credentials
        
    Returns:
        TokenData with user information
        
    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    return get_security_manager().validate_token(token)


# Dependency for admin access
async def get_admin_user(
        current_user: TokenData = Depends(get_current_user)
    ) -> TokenData:
    """
    Validate that current user has admin role.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        TokenData with admin user information
        
    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions"
        )
    return current_user


# Middleware for rate limiting
async def rate_limit_middleware(request: Request, call_next) -> Any:
    """
    Rate limiting middleware.
    
    Args:
        request: FastAPI request
        call_next: Next middleware or route handler
        
    Returns:
        Response from next handler
        
    Raises:
        HTTPException: If rate limit is exceeded
    """
    # Get client identifier (IP address or Authorization header if present)
    client_id = request.client.host
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        # Use token fingerprint instead of the full token
        token = auth_header.replace("Bearer ", "")
        client_id = f"token:{hashlib.sha256(token.encode()).hexdigest()[:16]}"
        
    # Check rate limit
    if await get_rate_limiter().is_rate_limited(client_id):
        raise HTTPException(
            status_code=429,
            detail="Too many requests"
        )
        
    # Process request
    return await call_next(request)


def setup_security(app: FastAPI) -> None:
    """
    Set up security middleware for FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    # Add rate limiting middleware
    if RATE_LIMIT_ENABLED:
        app.middleware("http")(rate_limit_middleware)
        
    logger.info("Security middleware configured")
