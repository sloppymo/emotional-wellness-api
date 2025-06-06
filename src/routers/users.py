"""
User management and consent router

This module provides endpoints for managing users and their consent records,
which is critical for HIPAA compliance.
"""

import logging
import uuid
from typing import Dict, Optional, List, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, EmailStr

from security.auth import get_current_user_with_scope, User, verify_phi_scope
from config.settings import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()

# In-memory user store (in production, this would be in a database)
users = {}
# In-memory consent records (in production, this would be in a database)
consent_records = {}


class UserCreate(BaseModel):
    """User creation request payload"""
    username: str = Field(..., description="Unique username")
    email: Optional[EmailStr] = Field(None, description="Email address")
    full_name: Optional[str] = Field(None, description="Full name")
    provider_id: Optional[str] = Field(None, description="Healthcare provider ID if applicable")


class UserResponse(BaseModel):
    """User information response"""
    id: str = Field(..., description="User identifier")
    username: str = Field(..., description="Username")
    email: Optional[str] = Field(None, description="Email address")
    full_name: Optional[str] = Field(None, description="Full name")
    created_at: datetime = Field(..., description="User creation timestamp")
    has_active_consent: bool = Field(..., description="Whether user has valid consent")


class ConsentRecord(BaseModel):
    """Consent record for HIPAA compliance"""
    user_id: str = Field(..., description="User identifier")
    consent_version: str = Field(..., description="Version of consent document agreed to")
    data_usage_approved: bool = Field(..., description="Approval for data usage")
    crisis_protocol_approved: bool = Field(..., description="Approval for crisis intervention")
    data_retention_period: int = Field(..., description="Agreed data retention period in days")
    ip_address: Optional[str] = Field(None, description="IP address at time of consent")


class ConsentResponse(BaseModel):
    """Consent record response"""
    id: str = Field(..., description="Consent record identifier")
    user_id: str = Field(..., description="User identifier")
    timestamp: datetime = Field(..., description="When consent was recorded")
    consent_version: str = Field(..., description="Version of consent document")
    data_usage_approved: bool = Field(..., description="Approval for data usage")
    crisis_protocol_approved: bool = Field(..., description="Approval for crisis intervention")
    data_retention_period: int = Field(..., description="Agreed data retention period in days")
    revocable: bool = Field(..., description="Whether consent can be revoked")
    active: bool = Field(..., description="Whether consent is currently active")


@router.post("/create", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_with_scope(["user_management"]))
):
    """
    Create a new user
    
    For HIPAA compliance, this logs user creation without PHI.
    """
    # Check if username already exists
    for user in users.values():
        if user["username"] == user_data.username:
            raise HTTPException(status_code=400, detail="Username already registered")
    
    # Create user
    user_id = str(uuid.uuid4())
    now = datetime.now()
    
    user = {
        "id": user_id,
        "username": user_data.username,
        "email": user_data.email,
        "full_name": user_data.full_name,
        "created_at": now,
        "provider_id": user_data.provider_id,
        "has_active_consent": False
    }
    
    # Store user
    users[user_id] = user
    
    # Log user creation for audit trail (HIPAA)
    logger.info(f"User {user_id} created by {current_user.id}")
    
    # Background task to record user creation in audit log
    background_tasks.add_task(
        audit_log_user_event, 
        user_id, 
        current_user.id, 
        "user_created"
    )
    
    # Return sanitized user response
    return UserResponse(
        id=user_id,
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        created_at=now,
        has_active_consent=False
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user_with_scope(["user_management"]))
):
    """
    Get user information
    
    For HIPAA compliance, only returns minimal information unless PHI scope is present.
    """
    # Verify user exists
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = users[user_id]
    
    # Verify user has permission to access this user information
    if current_user.id != user_id and "admin" not in current_user.scopes:
        logger.warning(f"User {current_user.id} attempted to access information for user {user_id}")
        raise HTTPException(status_code=403, detail="Not authorized to access this user information")
    
    # Log user access for audit trail (HIPAA)
    logger.info(f"User {user_id} accessed by {current_user.id}")
    
    # Check if user has active consent
    has_active_consent = any(
        record["user_id"] == user_id and record["active"] 
        for record in consent_records.values()
    )
    
    # Return sanitized user response
    return UserResponse(
        id=user_id,
        username=user["username"],
        email=user["email"],
        full_name=user["full_name"],
        created_at=user["created_at"],
        has_active_consent=has_active_consent
    )


@router.post("/consent", response_model=ConsentResponse)
async def record_consent(
    consent_data: ConsentRecord,
    background_tasks: BackgroundTasks,
    request_ip: str = "127.0.0.1",  # In production, extract from request
    current_user: User = Depends(get_current_user_with_scope(["user_management"]))
):
    """
    Record a user's consent for data processing
    
    For HIPAA compliance, this creates an immutable record of consent.
    """
    # Verify user exists
    if consent_data.user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify user has permission to record consent for this user
    if current_user.id != consent_data.user_id and "admin" not in current_user.scopes:
        logger.warning(f"User {current_user.id} attempted to record consent for user {consent_data.user_id}")
        raise HTTPException(status_code=403, detail="Not authorized to record consent for this user")
    
    # Create consent record
    consent_id = str(uuid.uuid4())
    now = datetime.now()
    
    # Hash the IP address for privacy
    import hashlib
    ip_hash = hashlib.sha256((request_ip + settings.PHI_ENCRYPTION_KEY).encode()).hexdigest()
    
    consent = {
        "id": consent_id,
        "user_id": consent_data.user_id,
        "timestamp": now,
        "consent_version": consent_data.consent_version,
        "data_usage_approved": consent_data.data_usage_approved,
        "crisis_protocol_approved": consent_data.crisis_protocol_approved,
        "data_retention_period": consent_data.data_retention_period,
        "ip_address_hash": ip_hash,
        "revocable": True,
        "active": True
    }
    
    # Store consent record
    consent_records[consent_id] = consent
    
    # Update user's active consent status
    users[consent_data.user_id]["has_active_consent"] = True
    
    # Log consent recording for audit trail (HIPAA)
    logger.info(f"Consent {consent_id} recorded for user {consent_data.user_id}")
    
    # Background task to record consent in audit log
    background_tasks.add_task(
        audit_log_consent_event, 
        consent_id, 
        consent_data.user_id, 
        "consent_recorded"
    )
    
    return ConsentResponse(**consent)


@router.post("/consent/{consent_id}/revoke", response_model=ConsentResponse)
async def revoke_consent(
    consent_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_with_scope(["user_management"]))
):
    """
    Revoke a previously given consent
    
    For HIPAA compliance, this records the revocation but maintains the consent history.
    """
    # Verify consent exists
    if consent_id not in consent_records:
        raise HTTPException(status_code=404, detail="Consent record not found")
    
    consent = consent_records[consent_id]
    
    # Verify user has permission to revoke this consent
    if current_user.id != consent["user_id"] and "admin" not in current_user.scopes:
        logger.warning(f"User {current_user.id} attempted to revoke consent for user {consent['user_id']}")
        raise HTTPException(status_code=403, detail="Not authorized to revoke this consent")
    
    # Verify consent is revocable
    if not consent["revocable"]:
        raise HTTPException(status_code=400, detail="This consent record cannot be revoked")
    
    # Verify consent is active
    if not consent["active"]:
        raise HTTPException(status_code=400, detail="This consent record is already inactive")
    
    # Update consent status
    consent["active"] = False
    
    # Check if user has any other active consent records
    has_other_active = any(
        record["user_id"] == consent["user_id"] and record["active"] and record["id"] != consent_id
        for record in consent_records.values()
    )
    
    # Update user's active consent status if no other active consents
    if not has_other_active:
        users[consent["user_id"]]["has_active_consent"] = False
    
    # Log consent revocation for audit trail (HIPAA)
    logger.info(f"Consent {consent_id} revoked for user {consent['user_id']}")
    
    # Background task to record consent revocation in audit log
    background_tasks.add_task(
        audit_log_consent_event, 
        consent_id, 
        consent["user_id"], 
        "consent_revoked"
    )
    
    return ConsentResponse(**consent)


@router.get("/{user_id}/consent-status", response_model=List[ConsentResponse])
async def get_user_consent_status(
    user_id: str,
    include_inactive: bool = False,
    current_user: User = Depends(get_current_user_with_scope(["user_management"]))
):
    """
    Get consent status for a user
    
    For HIPAA compliance, this returns the active consent records.
    """
    # Verify user exists
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify user has permission to access this user's consent status
    if current_user.id != user_id and "admin" not in current_user.scopes:
        logger.warning(f"User {current_user.id} attempted to access consent status for user {user_id}")
        raise HTTPException(status_code=403, detail="Not authorized to access consent status for this user")
    
    # Filter consent records by user_id and active status
    user_consent_records = [
        record for record in consent_records.values()
        if record["user_id"] == user_id and (include_inactive or record["active"])
    ]
    
    # Sort by timestamp (most recent first)
    user_consent_records.sort(key=lambda r: r["timestamp"], reverse=True)
    
    # Log consent status access for audit trail (HIPAA)
    logger.info(f"Consent status for user {user_id} accessed by {current_user.id}")
    
    return [ConsentResponse(**record) for record in user_consent_records]


async def audit_log_user_event(user_id: str, actor_id: str, event_type: str):
    """
    Record user events in audit log for HIPAA compliance
    
    In production, this would write to a secure, immutable audit log system.
    """
    # This is a placeholder - in production, use a proper audit logging system
    logger.info(f"AUDIT: {event_type} - User: {user_id}, Actor: {actor_id}, Time: {datetime.now().isoformat()}")


async def audit_log_consent_event(consent_id: str, user_id: str, event_type: str):
    """
    Record consent events in audit log for HIPAA compliance
    
    In production, this would write to a secure, immutable audit log system.
    """
    # This is a placeholder - in production, use a proper audit logging system
    logger.info(f"AUDIT: {event_type} - Consent: {consent_id}, User: {user_id}, Time: {datetime.now().isoformat()}")
