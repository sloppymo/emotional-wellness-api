"""
Authentication router for Emotional Wellness API.

Provides endpoints for JWT token generation, validation, and revocation.
"""
#
#    /\
#   /  \
#  | .. |
#  | (O)|
#   \__/
#
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Dict, Optional, List
from datetime import datetime

from api.security import get_security_manager, get_current_user, TokenData
from security.auth import get_api_key
from structured_logging import get_logger

# Configure logger
logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    """Login request data model."""
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    user_id: str = Field(..., description="User identifier")
    api_key: str = Field(..., description="API authentication key")


class TokenResponse(BaseModel):
    """Token response data model."""
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    user_id: str = Field(..., description="User identifier")
    role: str = Field(..., description="User role")
    expiration: datetime = Field(..., description="Token expiration time")


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    request: Request,
    login_data: LoginRequest,
    api_key: str = Depends(get_api_key)
) -> TokenResponse:
    """
    Authenticate user and generate JWT token.
    
    In a production environment, this would validate credentials against a secure database.
    For now, it just verifies the API key is valid.
    
    Args:
        request: FastAPI request object
        login_data: Login credentials
        api_key: API key for authentication
        
    Returns:
        TokenResponse with JWT token and metadata
        
    Raises:
        HTTPException: If authentication fails
    """
    # In production, validate user credentials here
    # For now, just check API key is valid (already done by dependency)
    
    # Check if API key matches the one provided in the request
    if api_key != login_data.api_key:
        logger.warning(f"Invalid API key attempt for user {login_data.user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Generate JWT token
    token = get_security_manager().create_token(
        user_id=login_data.user_id,
        role="user",  # Default role
        scopes=["emotional:read", "emotional:write"]  # Default scopes
    )
    
    # Get token data for response
    token_data = get_security_manager().validate_token(token)
    
    # Return token response
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=token_data.user_id,
        role=token_data.role,
        expiration=token_data.exp
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    current_user: TokenData = Depends(get_current_user)
) -> None:
    """
    Revoke current JWT token.
    
    Args:
        request: FastAPI request object
        current_user: Current authenticated user
        
    Raises:
        HTTPException: If token revocation fails
    """
    # Get token from authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
        # Revoke token
        get_security_manager().revoke_token(token)
        
    # Return no content
    return None


@router.get("/me", response_model=TokenData)
async def read_users_me(
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """
    Get current user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user information
    """
    return current_user
