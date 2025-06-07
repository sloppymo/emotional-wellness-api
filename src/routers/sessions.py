"""
Session management router

This module provides endpoints for managing the lifecycle of user sessions,
including creation, retrieval, and termination with appropriate audit logging
for HIPAA compliance.
"""
#    _________________________
#   /                        /|
#  /________________________/ |
# |                        |  |
# |    > DAD IM GAY     |  |
# |    > I KNOW     |  |
# |    > ME TOO   |  |
# |                        | /
# |________________________|/
#
import logging
import uuid
from typing import Dict, Optional, List, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from security.auth import get_current_user_with_scope, User

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory session store (in production, this would be in Redis/database)
sessions = {}

class SessionCreate(BaseModel):
    """Session creation request payload"""
    user_id: str = Field(..., description="User identifier")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Session metadata")
    

class SessionResponse(BaseModel):
    """Session information response"""
    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    created_at: datetime = Field(..., description="Session creation timestamp")
    last_active: datetime = Field(..., description="Last activity timestamp")
    status: str = Field(..., description="Session status")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Session metadata")


@router.post("/start", response_model=SessionResponse)
async def start_session(
    session_data: SessionCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_with_scope(["emotional_processing"]))
):
    """
    Start a new session for emotional state processing
    
    Creates a new session record with unique identifier and associates it with the user.
    For HIPAA compliance, this logs the session creation without PHI.
    """
    # Verify user has permission to create session for this user_id
    if current_user.id != session_data.user_id and "admin" not in current_user.scopes:
        logger.warning(f"User {current_user.id} attempted to create session for user {session_data.user_id}")
        raise HTTPException(status_code=403, detail="Not authorized to create session for this user")
    
    # Create session
    session_id = str(uuid.uuid4())
    now = datetime.now()
    
    session = {
        "session_id": session_id,
        "user_id": session_data.user_id,
        "created_at": now,
        "last_active": now,
        "status": "active",
        "metadata": session_data.metadata
    }
    
    # Store session
    sessions[session_id] = session
    
    # Log session creation for audit trail (HIPAA)
    logger.info(f"Session {session_id} created for user {session_data.user_id}")
    
    # Background task to record session creation in audit log
    background_tasks.add_task(
        audit_log_session_event, 
        session_id, 
        session_data.user_id, 
        "session_created"
    )
    
    return SessionResponse(**session)


@router.post("/end", response_model=SessionResponse)
async def end_session(
    session_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_with_scope(["emotional_processing"]))
):
    """
    End an active session
    
    Marks the session as terminated and records the end time.
    For HIPAA compliance, this logs the session termination.
    """
    # Verify session exists
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    # Verify user has permission to end this session
    if current_user.id != session["user_id"] and "admin" not in current_user.scopes:
        logger.warning(f"User {current_user.id} attempted to end session for user {session['user_id']}")
        raise HTTPException(status_code=403, detail="Not authorized to end this session")
    
    # Update session status
    session["status"] = "ended"
    session["last_active"] = datetime.now()
    
    # Log session end for audit trail (HIPAA)
    logger.info(f"Session {session_id} ended for user {session['user_id']}")
    
    # Background task to record session end in audit log
    background_tasks.add_task(
        audit_log_session_event, 
        session_id, 
        session["user_id"], 
        "session_ended"
    )
    
    return SessionResponse(**session)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user_with_scope(["emotional_processing"]))
):
    """
    Get session information
    
    Retrieves details about a specific session.
    For HIPAA compliance, this logs the session access.
    """
    # Verify session exists
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    # Verify user has permission to access this session
    if current_user.id != session["user_id"] and "admin" not in current_user.scopes:
        logger.warning(f"User {current_user.id} attempted to access session for user {session['user_id']}")
        raise HTTPException(status_code=403, detail="Not authorized to access this session")
    
    # Update last active timestamp
    session["last_active"] = datetime.now()
    
    # Log session access for audit trail (HIPAA)
    logger.info(f"Session {session_id} accessed by user {current_user.id}")
    
    return SessionResponse(**session)


@router.get("/", response_model=List[SessionResponse])
async def list_user_sessions(
    user_id: str,
    status: Optional[str] = None,
    limit: int = 10,
    current_user: User = Depends(get_current_user_with_scope(["emotional_processing"]))
):
    """
    List sessions for a user
    
    Returns a list of sessions for the specified user.
    Optional filter by status (active, ended).
    For HIPAA compliance, this logs the access to session list.
    """
    # Verify user has permission to list sessions for this user_id
    if current_user.id != user_id and "admin" not in current_user.scopes:
        logger.warning(f"User {current_user.id} attempted to list sessions for user {user_id}")
        raise HTTPException(status_code=403, detail="Not authorized to list sessions for this user")
    
    # Filter sessions by user_id and optional status
    user_sessions = [
        session for session in sessions.values()
        if session["user_id"] == user_id and 
           (status is None or session["status"] == status)
    ]
    
    # Sort by last active timestamp (most recent first) and apply limit
    user_sessions.sort(key=lambda s: s["last_active"], reverse=True)
    user_sessions = user_sessions[:limit]
    
    # Log session list access for audit trail (HIPAA)
    logger.info(f"Sessions listed for user {user_id} by {current_user.id}")
    
    return [SessionResponse(**session) for session in user_sessions]


async def audit_log_session_event(session_id: str, user_id: str, event_type: str):
    """
    Record session events in audit log for HIPAA compliance
    
    In production, this would write to a secure, immutable audit log system.
    """
    # This is a placeholder - in production, use a proper audit logging system
    logger.info(f"AUDIT: {event_type} - Session: {session_id}, User: {user_id}, Time: {datetime.now().isoformat()}")
