"""
Interventions management router

This module provides endpoints for managing therapeutic interventions,
including crisis responses, recommendations, and follow-up protocols.
"""

import logging
import uuid
from typing import Dict, Optional, List, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field

from security.auth import get_current_user_with_scope, User, verify_phi_scope
from config.settings import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()

# In-memory intervention store (in production, this would be in a database)
interventions = {}


class InterventionCreate(BaseModel):
    """Intervention creation request payload"""
    user_id: str = Field(..., description="User identifier")
    intervention_type: str = Field(..., description="Type of intervention (e.g., 'crisis', 'coping', 'wellness')")
    triggered_by: Optional[str] = Field(None, description="ID of assessment or event that triggered this")
    content: Dict[str, Any] = Field(..., description="Intervention content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class InterventionResponse(BaseModel):
    """Intervention information response"""
    id: str = Field(..., description="Intervention identifier")
    user_id: str = Field(..., description="User identifier")
    intervention_type: str = Field(..., description="Type of intervention")
    triggered_by: Optional[str] = Field(None, description="ID of assessment or event that triggered this")
    timestamp: datetime = Field(..., description="When intervention was created")
    content: Dict[str, Any] = Field(..., description="Intervention content")
    status: str = Field(..., description="Intervention status (e.g., 'pending', 'delivered', 'completed')")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class InterventionUpdate(BaseModel):
    """Intervention update request"""
    status: Optional[str] = Field(None, description="New intervention status")
    user_response: Optional[Dict[str, Any]] = Field(None, description="User response to intervention")
    notes: Optional[str] = Field(None, description="Clinical notes about the intervention")


class InterventionOutcome(BaseModel):
    """Intervention outcome model"""
    intervention_id: str = Field(..., description="Intervention identifier")
    effectiveness_score: Optional[int] = Field(None, description="Effectiveness score (0-100)")
    user_feedback: Optional[str] = Field(None, description="Feedback from user")
    completion_time: Optional[datetime] = Field(None, description="When intervention was completed")
    follow_up_needed: bool = Field(False, description="Whether follow-up is needed")
    follow_up_type: Optional[str] = Field(None, description="Type of follow-up if needed")


@router.post("/interventions/", response_model=InterventionResponse, status_code=201)
async def create_intervention(
    intervention_data: InterventionCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_with_scope(["intervention_management"]))
):
    """
    Create a new intervention

    For HIPAA compliance, this logs intervention creation without PHI.
    """
    # Verify user has permission to create interventions for this user_id
    if current_user.id != intervention_data.user_id and "admin" not in current_user.roles:
        verify_phi_scope(current_user, "write")
        
    intervention_id = str(uuid.uuid4())
    timestamp = datetime.utcnow()
    
    new_intervention = {
        "id": intervention_id,
        "user_id": intervention_data.user_id,
        "intervention_type": intervention_data.intervention_type,
        "triggered_by": intervention_data.triggered_by,
        "timestamp": timestamp,
        "content": intervention_data.content,
        "status": "pending",
        "metadata": intervention_data.metadata or {}
    }
    
    interventions[intervention_id] = new_intervention
    
    # In a real implementation, we would queue this for delivery
    background_tasks.add_task(
        audit_log_intervention_event, 
        intervention_id, 
        intervention_data.user_id, 
        "created"
    )
    
    # If this is a crisis intervention, it would be prioritized
    if intervention_data.intervention_type == "crisis":
        background_tasks.add_task(
            process_crisis_intervention,
            intervention_id
        )
    
    return InterventionResponse(**new_intervention)


@router.get("/interventions/{intervention_id}", response_model=InterventionResponse)
async def get_intervention(
    intervention_id: str,
    current_user: User = Depends(get_current_user_with_scope(["intervention_management"]))
):
    """
    Get intervention information

    For HIPAA compliance, only returns minimal information unless PHI scope is present.
    """
    if intervention_id not in interventions:
        raise HTTPException(status_code=404, detail="Intervention not found")
    
    intervention = interventions[intervention_id]
    
    # Check permissions
    if current_user.id != intervention["user_id"] and "admin" not in current_user.roles:
        verify_phi_scope(current_user, "read")
    
    return InterventionResponse(**intervention)


@router.get("/users/{user_id}/interventions/", response_model=List[InterventionResponse])
async def get_user_interventions(
    user_id: str,
    intervention_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user_with_scope(["intervention_management"]))
):
    """
    Get interventions for a user

    For HIPAA compliance, only returns minimal information unless PHI scope is present.
    """
    # Check permissions
    if current_user.id != user_id and "admin" not in current_user.roles:
        verify_phi_scope(current_user, "read")
    
    user_interventions = [
        intervention for intervention in interventions.values()
        if intervention["user_id"] == user_id
        and (intervention_type is None or intervention["intervention_type"] == intervention_type)
        and (status is None or intervention["status"] == status)
    ]
    
    # Sort by timestamp, newest first
    sorted_interventions = sorted(
        user_interventions, 
        key=lambda a: a["timestamp"],
        reverse=True
    )
    
    # Apply pagination
    paginated = sorted_interventions[offset:offset+limit]
    
    return [InterventionResponse(**intervention) for intervention in paginated]


@router.patch("/interventions/{intervention_id}", response_model=InterventionResponse)
async def update_intervention(
    intervention_id: str,
    update_data: InterventionUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_with_scope(["intervention_management"]))
):
    """
    Update an intervention's status or add response data

    This allows tracking the progress and outcomes of interventions.
    """
    if intervention_id not in interventions:
        raise HTTPException(status_code=404, detail="Intervention not found")
    
    intervention = interventions[intervention_id]
    
    # Check permissions
    if current_user.id != intervention["user_id"] and "admin" not in current_user.roles:
        verify_phi_scope(current_user, "write")
    
    # Update fields if provided
    if update_data.status is not None:
        intervention["status"] = update_data.status
        
    if update_data.user_response is not None:
        if "user_responses" not in intervention:
            intervention["user_responses"] = []
            
        intervention["user_responses"].append({
            "response": update_data.user_response,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    if update_data.notes is not None:
        if "clinical_notes" not in intervention:
            intervention["clinical_notes"] = []
            
        intervention["clinical_notes"].append({
            "note": update_data.notes,
            "author_id": current_user.id,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    # Log the update event
    background_tasks.add_task(
        audit_log_intervention_event, 
        intervention_id, 
        intervention["user_id"], 
        f"updated_status_{update_data.status}" if update_data.status else "updated"
    )
    
    # Check if this completes a crisis intervention
    if (update_data.status == "completed" and 
        intervention["intervention_type"] == "crisis"):
        background_tasks.add_task(
            process_crisis_completion,
            intervention_id
        )
    
    return InterventionResponse(**intervention)


@router.post("/interventions/{intervention_id}/outcome", response_model=InterventionOutcome)
async def record_intervention_outcome(
    intervention_id: str,
    outcome_data: InterventionOutcome,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_with_scope(["intervention_management"]))
):
    """
    Record the outcome of an intervention

    This is important for tracking effectiveness and determining follow-up needs.
    """
    if intervention_id not in interventions:
        raise HTTPException(status_code=404, detail="Intervention not found")
    
    intervention = interventions[intervention_id]
    
    # Check permissions
    if current_user.id != intervention["user_id"] and "admin" not in current_user.roles:
        verify_phi_scope(current_user, "write")
    
    # Create or update outcome data
    if "outcome" not in intervention:
        intervention["outcome"] = {}
        
    intervention["outcome"]["effectiveness_score"] = outcome_data.effectiveness_score
    intervention["outcome"]["user_feedback"] = outcome_data.user_feedback
    intervention["outcome"]["completion_time"] = outcome_data.completion_time or datetime.utcnow()
    intervention["outcome"]["follow_up_needed"] = outcome_data.follow_up_needed
    intervention["outcome"]["follow_up_type"] = outcome_data.follow_up_type
    
    # Update intervention status if not already completed
    if intervention["status"] != "completed":
        intervention["status"] = "completed"
    
    # Log the outcome recording
    background_tasks.add_task(
        audit_log_intervention_event, 
        intervention_id, 
        intervention["user_id"], 
        "outcome_recorded"
    )
    
    # Schedule follow-up if needed
    if outcome_data.follow_up_needed:
        background_tasks.add_task(
            schedule_intervention_follow_up,
            intervention_id,
            outcome_data.follow_up_type
        )
    
    return InterventionOutcome(
        intervention_id=intervention_id,
        effectiveness_score=intervention["outcome"]["effectiveness_score"],
        user_feedback=intervention["outcome"]["user_feedback"],
        completion_time=intervention["outcome"]["completion_time"],
        follow_up_needed=intervention["outcome"]["follow_up_needed"],
        follow_up_type=intervention["outcome"]["follow_up_type"]
    )


def process_crisis_intervention(intervention_id: str):
    """
    Process a crisis intervention (would be more complex in production)
    
    In a real implementation, this might involve notifications, escalations, etc.
    """
    if intervention_id in interventions:
        intervention = interventions[intervention_id]
        intervention["status"] = "in_progress"
        
        logger.info(f"CRISIS: Processing intervention {intervention_id} for user {intervention['user_id']}")
        
        # In a real system, this would involve additional steps like:
        # - Sending notifications to crisis team
        # - Escalating based on severity
        # - Alerting clinical staff


def process_crisis_completion(intervention_id: str):
    """
    Process the completion of a crisis intervention
    
    In a real implementation, this would include follow-up scheduling and reporting.
    """
    if intervention_id in interventions:
        intervention = interventions[intervention_id]
        
        logger.info(f"CRISIS: Completed intervention {intervention_id} for user {intervention['user_id']}")
        
        # In a real system, this would involve additional steps like:
        # - Scheduling follow-up
        # - Updating crisis protocol status
        # - Recording metrics on response time


def schedule_intervention_follow_up(intervention_id: str, follow_up_type: Optional[str]):
    """
    Schedule a follow-up for an intervention
    
    In a real implementation, this would create tasks in a workflow system.
    """
    if intervention_id in interventions:
        intervention = interventions[intervention_id]
        
        logger.info(
            f"FOLLOW-UP: Scheduling {follow_up_type or 'standard'} follow-up for "
            f"intervention {intervention_id}, user {intervention['user_id']}"
        )
        
        # In a real system, this would involve additional steps like:
        # - Creating follow-up tasks
        # - Scheduling notifications
        # - Alerting clinical staff if needed


def audit_log_intervention_event(intervention_id: str, user_id: str, event_type: str):
    """
    Record intervention events in audit log for HIPAA compliance
    
    In production, this would write to a secure, immutable audit log system.
    """
    timestamp = datetime.utcnow().isoformat()
    logger.info(
        f"AUDIT:INTERVENTION:{event_type}:{timestamp}:intervention_id={intervention_id}:user_id={user_id}"
    )
