"""
Authentication and authorization module for HIPAA-compliant API access

This module implements:
- API key validation
- OAuth2 JWT token authentication
- Role and attribute-based access control
- Scope verification for PHI access
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer, SecurityScopes
from jose import JWTError, jwt
from pydantic import BaseModel, ValidationError

from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Security scheme definitions
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "emotional_processing": "Process emotional state data",
        "emotional_history": "Access emotional state history",
        "user_management": "Manage user data and consent",
        "admin": "Administrative access",
        "phi_access": "Access to Protected Health Information",
    },
)

class User(BaseModel):
    """User model for authentication and authorization"""
    id: str
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: bool = False
    scopes: List[str] = []


class TokenData(BaseModel):
    """JWT token data"""
    sub: Optional[str] = None
    scopes: List[str] = []
    exp: Optional[datetime] = None


async def get_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Validate API key from header
    
    In production, this would validate against a secure database
    with rate limiting and proper key rotation.
    """
    # For development - use a static API key from environment
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
        )
    
    # Static key for development, in production use secure comparison
    if api_key != settings.API_KEY:
        logger.warning(f"Invalid API key attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    
    return api_key


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    
    Args:
        data: Data to encode in token
        expires_delta: Token expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


async def get_current_user(
    security_scopes: SecurityScopes, token: str = Depends(oauth2_scheme)
) -> User:
    """
    Decode and validate JWT token to get current user
    
    Args:
        security_scopes: Required security scopes
        token: JWT token
        
    Returns:
        User object if valid
        
    Raises:
        HTTPException: If token is invalid or user doesn't have required scopes
    """
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
        
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    
    try:
        # Decode token
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        username: str = payload.get("sub")
        
        if username is None:
            raise credentials_exception
            
        token_scopes = payload.get("scopes", [])
        token_data = TokenData(scopes=token_scopes, sub=username)
        
    except (JWTError, ValidationError):
        logger.warning("Invalid token attempt")
        raise credentials_exception
        
    # In production, this would fetch user from database
    # For now, simulate a user record
    user = User(
        id=username,
        username=username,
        scopes=token_data.scopes
    )
    
    # Check if user exists and is active
    if user is None or user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    # Check scopes
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            logger.warning(f"User {username} missing required scope {scope}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Required scope: {scope}",
                headers={"WWW-Authenticate": authenticate_value},
            )
            
    # Log access for audit trail (metadata only, not PHI)
    logger.info(f"Authenticated access for user {username}, scopes: {token_data.scopes}")
    
    return user


def get_current_user_with_scope(required_scopes: List[str]):
    """
    Create a dependency function for checking specific scopes
    
    Args:
        required_scopes: List of required scopes
        
    Returns:
        Dependency function for FastAPI
    """
    async def get_user_with_scope(
        current_user: User = Security(get_current_user, scopes=required_scopes)
    ) -> User:
        return current_user
        
    return get_user_with_scope


def verify_phi_scope(user: User = Depends(get_current_user_with_scope(["phi_access"]))):
    """
    Verify user has PHI access scope
    
    This function provides additional logging for PHI access and
    could implement additional checks for HIPAA compliance.
    
    Args:
        user: Authenticated user with phi_access scope
        
    Returns:
        User if authorized
    """
    # Log PHI access for HIPAA audit trail
    logger.info(f"PHI access by user {user.id} - identity verified with phi_access scope")
    
    # In production, additional checks could be performed here
    # - Check user's agreement to BAA
    # - Verify specialized training completion
    # - Apply minimum-necessary principle based on role
    
    return user
