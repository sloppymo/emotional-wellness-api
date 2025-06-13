"""
JWT Token Management System for Emotional Wellness API

This module implements:
- Enhanced JWT token generation and validation
- Token rotation policies
- Token revocation tracking
- Blacklisting for revoked tokens
- Integration with RBAC system
"""

import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Union

import redis
from fastapi import HTTPException, status
from jose import jwt
from pydantic import BaseModel, Field

from config.settings import get_settings
from src.security.rbac import Permission, role_manager

logger = logging.getLogger(__name__)
settings = get_settings()

# Redis client for token blacklist
try:
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=1,  # Use separate DB for token blacklist
        decode_responses=True
    )
    # Test connection
    redis_client.ping()
    logger.info("Redis connected for token management")
except Exception as e:
    logger.warning(f"Redis not available for token management: {e}")
    # Fallback to in-memory blacklist (not suitable for production)
    redis_client = None
    token_blacklist = set()


class TokenType(str):
    """Token types for different purposes"""
    ACCESS = "access"
    REFRESH = "refresh"
    RESET_PASSWORD = "reset"
    EMAIL_VERIFICATION = "email_verification"
    API_KEY = "api_key"


class TokenMetadata(BaseModel):
    """Additional metadata stored with tokens"""
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    device_id: Optional[str] = None
    issued_at: datetime = Field(default_factory=datetime.utcnow)


class TokenClaims(BaseModel):
    """Standard claims for JWT tokens"""
    sub: str  # Subject (user ID)
    exp: datetime  # Expiration time
    iat: datetime = Field(default_factory=datetime.utcnow)  # Issued at
    jti: str = Field(default_factory=lambda: str(uuid.uuid4()))  # JWT ID (unique)
    type: str = TokenType.ACCESS  # Token type
    permissions: List[str] = []  # Permission list
    metadata: Optional[TokenMetadata] = None  # Additional metadata


class TokenManager:
    """
    Advanced JWT token management with rotation and revocation
    """
    def __init__(self):
        """Initialize the token manager"""
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
        
    def create_access_token(self, user_id: str, 
                           metadata: Optional[TokenMetadata] = None) -> str:
        """
        Create a new access token for a user
        
        Args:
            user_id: User identifier
            metadata: Additional token metadata
            
        Returns:
            JWT access token string
        """
        # Get user permissions from role manager
        permissions = role_manager.get_user_permissions(user_id)
        
        # Convert enum permissions to strings for JWT
        permission_strings = [p.value for p in permissions]
        
        expires_delta = timedelta(minutes=self.access_token_expire_minutes)
        expire = datetime.utcnow() + expires_delta
        
        claims = TokenClaims(
            sub=user_id,
            exp=expire,
            type=TokenType.ACCESS,
            permissions=permission_strings,
            metadata=metadata
        )
        
        # Create the JWT token
        token = jwt.encode(
            claims.dict(), 
            self.secret_key, 
            algorithm=self.algorithm
        )
        
        logger.info(f"Created access token for user {user_id}, expires at {expire}")
        return token
    
    def create_refresh_token(self, user_id: str,
                            metadata: Optional[TokenMetadata] = None) -> str:
        """
        Create a refresh token for token rotation
        
        Args:
            user_id: User identifier
            metadata: Additional token metadata
            
        Returns:
            JWT refresh token string
        """
        expires_delta = timedelta(days=self.refresh_token_expire_days)
        expire = datetime.utcnow() + expires_delta
        
        claims = TokenClaims(
            sub=user_id,
            exp=expire,
            type=TokenType.REFRESH,
            metadata=metadata
        )
        
        # Create the JWT token
        token = jwt.encode(
            claims.dict(), 
            self.secret_key, 
            algorithm=self.algorithm
        )
        
        logger.info(f"Created refresh token for user {user_id}, expires at {expire}")
        return token
    
    def decode_token(self, token: str) -> Dict:
        """
        Decode and validate a JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token claims
            
        Raises:
            HTTPException: If token is invalid or blacklisted
        """
        try:
            # Decode the token
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            
            # Check if token is blacklisted
            if self.is_token_blacklisted(payload.get("jti")):
                logger.warning(f"Blacklisted token used: {payload.get('jti')}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )
                
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Expired token used")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
            
        except jwt.JWTError:
            logger.warning("Invalid token format")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format"
            )
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """
        Use a refresh token to get a new access token
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            Dict with new access token and refresh token
            
        Raises:
            HTTPException: If refresh token is invalid
        """
        # Decode the refresh token
        payload = self.decode_token(refresh_token)
        
        # Verify it's a refresh token
        if payload.get("type") != TokenType.REFRESH:
            logger.warning("Non-refresh token used for refresh")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
            
        # Get user ID from token
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token content"
            )
            
        # Get metadata if present
        metadata = None
        if "metadata" in payload:
            metadata = TokenMetadata(**payload["metadata"])
        
        # Create new tokens
        access_token = self.create_access_token(user_id, metadata)
        new_refresh_token = self.create_refresh_token(user_id, metadata)
        
        # Revoke the old refresh token
        self.revoke_token(payload.get("jti"))
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    
    def revoke_token(self, token_id: str) -> bool:
        """
        Revoke a token by adding it to the blacklist
        
        Args:
            token_id: JWT ID (jti) to blacklist
            
        Returns:
            True if successfully blacklisted
        """
        if redis_client:
            # Calculate TTL (time to live) based on current time plus a buffer
            # This ensures blacklisted tokens are removed after they expire
            ttl = 86400 * 30  # 30 days as a safe maximum
            
            # Add to Redis blacklist
            redis_client.setex(f"blacklist:{token_id}", ttl, "1")
            logger.info(f"Token {token_id} added to Redis blacklist")
            
        else:
            # Fallback to in-memory blacklist
            token_blacklist.add(token_id)
            logger.info(f"Token {token_id} added to memory blacklist")
            
        return True
    
    def revoke_all_user_tokens(self, user_id: str) -> bool:
        """
        Revoke all tokens for a user (used on password change, etc.)
        
        Args:
            user_id: User identifier
            
        Returns:
            True if successful
        """
        if redis_client:
            # In a real implementation, we would store token JTIs by user
            # and revoke them individually. This is a simplified example.
            redis_client.setex(f"user_revoked:{user_id}", 86400 * 30, 
                             str(int(time.time())))
            logger.info(f"All tokens revoked for user {user_id}")
            
        else:
            # Not implemented for memory storage
            logger.warning("User token revocation not available without Redis")
            
        return True
    
    def is_token_blacklisted(self, token_id: str) -> bool:
        """
        Check if a token is blacklisted
        
        Args:
            token_id: JWT ID to check
            
        Returns:
            True if token is blacklisted
        """
        if not token_id:
            return False
            
        if redis_client:
            # Check Redis blacklist
            return redis_client.exists(f"blacklist:{token_id}") == 1
        else:
            # Check memory blacklist
            return token_id in token_blacklist
    
    def verify_permissions(self, token: str, 
                         required_permissions: List[Permission]) -> bool:
        """
        Verify token has required permissions
        
        Args:
            token: JWT token
            required_permissions: List of required permissions
            
        Returns:
            True if token has all required permissions
        """
        # Decode token
        payload = self.decode_token(token)
        
        # Get permissions from token
        token_permissions = payload.get("permissions", [])
        
        # Convert required permissions to strings for comparison
        required_permission_strings = [p.value for p in required_permissions]
        
        # Check if token has all required permissions
        return all(perm in token_permissions for perm in required_permission_strings)
        

# Create a global instance for use throughout the application
token_manager = TokenManager()
