"""
Assessment management router

This module provides endpoints for managing user assessments and their results,
including emotional wellness evaluations and crisis risk scoring.
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

# In-memory assessment store (in production, this would be in a database)
assessments = {}


class AssessmentCreate(BaseModel):
    """Assessment creation request payload"""
    user_id: str = Field(..., description="User identifier")
    assessment_type: str = Field(..., description="Type of assessment (e.g., 'emotional', 'crisis', 'wellness')")
    responses: Dict[str, Any] = Field(..., description="Assessment responses")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class AssessmentResponse(BaseModel):
    """Assessment information response"""
    id: str = Field(..., description="Assessment identifier")
    user_id: str = Field(..., description="User identifier")
    assessment_type: str = Field(..., description="Type of assessment")
    timestamp: datetime = Field(..., description="When assessment was recorded")
    responses: Dict[str, Any] = Field(..., description="Assessment responses")
    score: Optional[Dict[str, Any]] = Field(None, description="Assessment scores")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    flags: Optional[List[str]] = Field(None, description="Assessment flags (e.g., 'crisis_risk')")


class AssessmentResult(BaseModel):
    """Assessment result model"""
    assessment_id: str = Field(..., description="Assessment identifier")
    score: Dict[str, Any] = Field(..., description="Assessment scores")
    timestamp: datetime = Field(..., description="When assessment was scored")
    recommendations: Optional[List[str]] = Field(None, description="Recommendations based on assessment")
    flags: Optional[List[str]] = Field(None, description="Assessment flags (e.g., 'crisis_risk')")


@router.post("/assessments/", response_model=AssessmentResponse, status_code=201)
async def create_assessment(
    assessment_data: AssessmentCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_with_scope(["assessment_management"]))
):
    """
    Create a new assessment

    For HIPAA compliance, this logs assessment creation without PHI.
    """
    # Verify user has permission to create assessments for this user_id
    if current_user.id != assessment_data.user_id and "admin" not in current_user.roles:
        verify_phi_scope(current_user, "write")
        
    assessment_id = str(uuid.uuid4())
    timestamp = datetime.utcnow()
    
    new_assessment = {
        "id": assessment_id,
        "user_id": assessment_data.user_id,
        "assessment_type": assessment_data.assessment_type,
        "timestamp": timestamp,
        "responses": assessment_data.responses,
        "score": None,
        "metadata": assessment_data.metadata or {},
        "flags": []
    }
    
    assessments[assessment_id] = new_assessment
    
    # In a real implementation, we would queue this for scoring
    background_tasks.add_task(
        audit_log_assessment_event, 
        assessment_id, 
        assessment_data.user_id, 
        "created"
    )
    
    # In a real implementation, we would also queue the assessment for scoring
    # background_tasks.add_task(score_assessment, assessment_id)
    
    return AssessmentResponse(**new_assessment)


@router.get("/assessments/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(
    assessment_id: str,
    current_user: User = Depends(get_current_user_with_scope(["assessment_management"]))
):
    """
    Get assessment information

    For HIPAA compliance, only returns minimal information unless PHI scope is present.
    """
    if assessment_id not in assessments:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    assessment = assessments[assessment_id]
    
    # Check permissions
    if current_user.id != assessment["user_id"] and "admin" not in current_user.roles:
        verify_phi_scope(current_user, "read")
    
    return AssessmentResponse(**assessment)


@router.get("/users/{user_id}/assessments/", response_model=List[AssessmentResponse])
async def get_user_assessments(
    user_id: str,
    assessment_type: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user_with_scope(["assessment_management"]))
):
    """
    Get assessments for a user

    For HIPAA compliance, only returns minimal information unless PHI scope is present.
    """
    # Check permissions
    if current_user.id != user_id and "admin" not in current_user.roles:
        verify_phi_scope(current_user, "read")
    
    user_assessments = [
        assessment for assessment in assessments.values()
        if assessment["user_id"] == user_id
        and (assessment_type is None or assessment["assessment_type"] == assessment_type)
    ]
    
    # Sort by timestamp, newest first
    sorted_assessments = sorted(
        user_assessments, 
        key=lambda a: a["timestamp"],
        reverse=True
    )
    
    # Apply pagination
    paginated = sorted_assessments[offset:offset+limit]
    
    return [AssessmentResponse(**assessment) for assessment in paginated]


@router.post("/assessments/{assessment_id}/score", response_model=AssessmentResult)
async def score_assessment(
    assessment_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_with_scope(["assessment_scoring"]))
):
    """
    Score an existing assessment

    This would typically involve complex analysis algorithms.
    """
    if assessment_id not in assessments:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    assessment = assessments[assessment_id]
    
    # Check permissions
    if current_user.id != assessment["user_id"] and "admin" not in current_user.roles:
        verify_phi_scope(current_user, "write")
    
    # In a real implementation, this would involve actual scoring algorithms
    # For now, we'll just provide a sample score
    score = {
        "emotional_wellbeing": 75,
        "anxiety": 30,
        "depression": 25,
        "crisis_risk": 10
    }
    
    # Update the assessment with scores
    assessment["score"] = score
    
    # Add flags if needed
    flags = []
    if score["crisis_risk"] > 70:
        flags.append("high_crisis_risk")
    elif score["crisis_risk"] > 40:
        flags.append("moderate_crisis_risk")
        
    if score["depression"] > 60:
        flags.append("elevated_depression")
        
    assessment["flags"] = flags
    
    # Log the scoring event
    background_tasks.add_task(
        audit_log_assessment_event, 
        assessment_id, 
        assessment["user_id"], 
        "scored"
    )
    
    result = {
        "assessment_id": assessment_id,
        "score": score,
        "timestamp": datetime.utcnow(),
        "recommendations": generate_recommendations(score),
        "flags": flags
    }
    
    return AssessmentResult(**result)


def generate_recommendations(score: Dict[str, Any]) -> List[str]:
    """Generate recommendations based on assessment scores"""
    recommendations = []
    
    if score["emotional_wellbeing"] < 50:
        recommendations.append("Consider daily mindfulness practice")
        
    if score["anxiety"] > 50:
        recommendations.append("Try breathing exercises when feeling anxious")
        
    if score["depression"] > 50:
        recommendations.append("Consider scheduling a session with a therapist")
        
    if score["crisis_risk"] > 40:
        recommendations.append("Please reach out to your support network")
    
    if not recommendations:
        recommendations.append("Continue your current wellness practices")
        
    return recommendations


def audit_log_assessment_event(assessment_id: str, user_id: str, event_type: str):
    """
    Record assessment events in audit log for HIPAA compliance
    
    In production, this would write to a secure, immutable audit log system.
    """
    timestamp = datetime.utcnow().isoformat()
    logger.info(
        f"AUDIT:ASSESSMENT:{event_type}:{timestamp}:assessment_id={assessment_id}:user_id={user_id}"
    )
