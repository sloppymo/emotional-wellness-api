"""
Enhanced Authentication Router with RBAC for Emotional Wellness API

This router implements:
- User authentication with JWT
- Token refresh and rotation
- Password management
- Role and permission assignment
- Security audit logging
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Security, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field

from src.security.auth import User
from src.security.rbac import role_manager, Permission, Role, UserRole
from src.security.token_manager import token_manager, TokenMetadata
from src.utils.audit import log_security_event
from config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={401: {"description": "Unauthorized"}}
)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


# Request Models
class UserCreate(BaseModel):
    """User creation request model"""
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """User login request model"""
    username: str
    password: str


class PasswordResetRequest(BaseModel):
    """Password reset request model"""
    email: EmailStr


class PasswordReset(BaseModel):
    """Password reset model"""
    reset_token: str
    new_password: str


class RoleAssignment(BaseModel):
    """Role assignment model"""
    user_id: str
    role_id: str
    expires_at: Optional[datetime] = None


# Response Models
class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class UserResponse(BaseModel):
    """User response model"""
    id: str
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    roles: List[str] = []
    permissions: List[str] = []


class SuccessResponse(BaseModel):
    """Generic success response"""
    message: str
    success: bool = True


# Auth dependencies
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Get the current authenticated user from token
    
    Args:
        token: JWT token from authorization header
        
    Returns:
        User object if valid
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        # Decode the token
        payload = token_manager.decode_token(token)
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # In production, this would fetch the user from the database
        # For now, we'll create a user object with data from the token
        user = User(
            id=user_id,
            username=user_id,  # Using ID as username for this example
            scopes=payload.get("permissions", [])
        )
        
        return user
        
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Check if user is active
    
    Args:
        current_user: User from token
        
    Returns:
        User if active
        
    Raises:
        HTTPException: If user is inactive
    """
    if current_user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


def has_permission(required_permission: Permission):
    """
    Create a dependency that checks for a specific permission
    
    Args:
        required_permission: Permission to check for
        
    Returns:
        Dependency function for FastAPI
    """
    async def check_permission(
        token: str = Depends(oauth2_scheme)
    ) -> bool:
        payload = token_manager.decode_token(token)
        user_id = payload.get("sub")
        
        # Check permission through role manager
        if not role_manager.has_permission(user_id, required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {required_permission}",
            )
        
        return True
    
    return check_permission


# Auth endpoints
@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    # In a real implementation, this would validate against a database
    # This is a simplified example for demonstration
    
    # For demo purposes - validate with a dummy user
    # In production, use proper password validation
    if form_data.username != "demo" or form_data.password != "password":
        log_security_event(
            event_type="failed_login",
            user_id=form_data.username,
            ip_address=request.client.host,
            details="Invalid username or password"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Create metadata with request information
    metadata = TokenMetadata(
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host,
    )
    
    # Create tokens
    access_token = token_manager.create_access_token(
        form_data.username, metadata=metadata
    )
    
    refresh_token = token_manager.create_refresh_token(
        form_data.username, metadata=metadata
    )
    
    # Log successful login
    log_security_event(
        event_type="successful_login",
        user_id=form_data.username,
        ip_address=request.client.host
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # seconds
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: Request, refresh_token: str):
    """
    Get a new access token using a refresh token
    """
    try:
        # Get new tokens
        tokens = token_manager.refresh_access_token(refresh_token)
        
        # Extract payload to get user info for logging
        payload = token_manager.decode_token(tokens["access_token"])
        user_id = payload.get("sub")
        
        # Log token refresh
        log_security_event(
            event_type="token_refresh",
            user_id=user_id,
            ip_address=request.client.host
        )
        
        return {
            **tokens,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # seconds
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid refresh token"
        )


@router.post("/logout", response_model=SuccessResponse)
async def logout(
    request: Request,
    token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_active_user)
):
    """
    Logout by blacklisting the current token
    """
    try:
        # Decode token to get jti (JWT ID)
        payload = token_manager.decode_token(token)
        token_id = payload.get("jti")
        
        # Revoke token
        token_manager.revoke_token(token_id)
        
        # Log logout
        log_security_event(
            event_type="logout",
            user_id=current_user.id,
            ip_address=request.client.host
        )
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Logout failed"
        )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    request: Request,
    user_data: UserCreate
):
    """
    Register a new user
    """
    # In a real implementation, this would create a user in the database
    # and handle email verification, etc.
    
    # Generate a dummy user ID
    user_id = f"user_{user_data.username}"
    
    # Assign default patient role
    role_manager.assign_role_to_user(user_id, "patient")
    
    # Get assigned permissions
    permissions = role_manager.get_user_permissions(user_id)
    
    # Log user creation
    log_security_event(
        event_type="user_created",
        user_id=user_id,
        ip_address=request.client.host,
        details={
            "username": user_data.username,
            "email": user_data.email
        }
    )
    
    return {
        "id": user_id,
        "username": user_data.username,
        "email": user_data.email,
        "full_name": user_data.full_name,
        "roles": ["patient"],
        "permissions": [p.value for p in permissions]
    }


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get information about the current logged-in user
    """
    # Get user roles and permissions
    roles = role_manager.get_user_roles(current_user.id)
    permissions = role_manager.get_user_permissions(current_user.id)
    
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "roles": [role.id for role in roles],
        "permissions": [p.value for p in permissions]
    }


# Role management endpoints (admin only)
@router.post("/roles/assign", response_model=SuccessResponse)
async def assign_role(
    request: Request,
    role_assignment: RoleAssignment,
    current_user: User = Depends(get_current_active_user),
    has_admin: bool = Depends(has_permission(Permission.MANAGE_ROLES))
):
    """
    Assign a role to a user (admin only)
    """
    # Assign the role
    role_manager.assign_role_to_user(
        user_id=role_assignment.user_id,
        role_id=role_assignment.role_id,
        assigned_by=current_user.id,
        expires_at=role_assignment.expires_at
    )
    
    # Log role assignment
    log_security_event(
        event_type="role_assigned",
        user_id=current_user.id,
        ip_address=request.client.host,
        details={
            "target_user": role_assignment.user_id,
            "role_id": role_assignment.role_id,
            "expires_at": role_assignment.expires_at.isoformat() if role_assignment.expires_at else None
        }
    )
    
    return {
        "message": f"Role {role_assignment.role_id} assigned to user {role_assignment.user_id}"
    }


@router.delete("/roles/remove", response_model=SuccessResponse)
async def remove_role(
    request: Request,
    user_id: str,
    role_id: str,
    current_user: User = Depends(get_current_active_user),
    has_admin: bool = Depends(has_permission(Permission.MANAGE_ROLES))
):
    """
    Remove a role from a user (admin only)
    """
    # Remove the role
    success = role_manager.remove_role_from_user(user_id, role_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role {role_id} not found for user {user_id}"
        )
    
    # Log role removal
    log_security_event(
        event_type="role_removed",
        user_id=current_user.id,
        ip_address=request.client.host,
        details={
            "target_user": user_id,
            "role_id": role_id
        }
    )
    
    return {
        "message": f"Role {role_id} removed from user {user_id}"
    }


@router.get("/revoke-all/{user_id}", response_model=SuccessResponse)
async def revoke_all_tokens(
    request: Request,
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    has_admin: bool = Depends(has_permission(Permission.MANAGE_USERS))
):
    """
    Revoke all tokens for a user (admin only)
    Used on password change, security breach, etc.
    """
    # Revoke all user tokens
    token_manager.revoke_all_user_tokens(user_id)
    
    # Log token revocation
    log_security_event(
        event_type="all_tokens_revoked",
        user_id=current_user.id,
        ip_address=request.client.host,
        details={
            "target_user": user_id
        }
    )
    
    return {
        "message": f"All tokens revoked for user {user_id}"
    }
