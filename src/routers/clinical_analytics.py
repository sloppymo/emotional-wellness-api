"""
FastAPI router for clinical analytics API endpoints.

Provides advanced reporting, trend analysis, and outcome tracking for clinical users.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from api.security import (
    get_current_user, 
    RoleScopes, 
    require_scope,
    get_redis_client
)
from structured_logging import get_logger
from observability import get_telemetry_manager, ComponentName
from clinical.analytics import get_clinical_analytics


# Configure router
router = APIRouter(
    prefix="/clinical/analytics",
    tags=["clinical_analytics"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden, insufficient permissions"},
        404: {"description": "Not found"}
    }
)

# Configure logger
logger = get_logger(__name__)


@router.get(
    "/trends/crisis",
    response_model=Dict[str, Any],
    summary="Get crisis alert trends",
    description="Returns crisis alert trends over time with configurable time range and granularity"
)
async def get_crisis_trends(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    granularity: str = Query("day", description="Time granularity (hour, day, week)"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    scope: str = Depends(require_scope(RoleScopes.CLINICAL_VIEW)),
    redis = Depends(get_redis_client)
):
    """Get crisis alert trends over time."""
    try:
        analytics = await get_clinical_analytics(redis)
        trends = await analytics.get_crisis_trends(days=days, granularity=granularity)
        
        # Record telemetry
        telemetry = get_telemetry_manager()
        if telemetry:
            telemetry.record_api_request(
                endpoint="/clinical/analytics/trends/crisis",
                method="GET",
                status_code=200
            )
        
        return trends
    
    except Exception as e:
        logger.error(f"Error getting crisis trends: {e}")
        
        # Record telemetry
        telemetry = get_telemetry_manager()
        if telemetry:
            telemetry.record_api_request(
                endpoint="/clinical/analytics/trends/crisis",
                method="GET",
                status_code=500
            )
        
        raise HTTPException(
            status_code=500,
            detail="Failed to get crisis trends"
        )


@router.get(
    "/outcomes",
    response_model=Dict[str, Any],
    summary="Get intervention outcomes",
    description="Returns analysis of intervention outcomes and effectiveness"
)
async def get_intervention_outcomes(
    current_user: Dict[str, Any] = Depends(get_current_user),
    scope: str = Depends(require_scope(RoleScopes.CLINICAL_VIEW)),
    redis = Depends(get_redis_client)
):
    """Get intervention outcome analysis."""
    try:
        analytics = await get_clinical_analytics(redis)
        outcomes = await analytics.get_intervention_outcomes()
        
        # Record telemetry
        telemetry = get_telemetry_manager()
        if telemetry:
            telemetry.record_api_request(
                endpoint="/clinical/analytics/outcomes",
                method="GET",
                status_code=200
            )
        
        return outcomes
    
    except Exception as e:
        logger.error(f"Error getting intervention outcomes: {e}")
        
        # Record telemetry
        telemetry = get_telemetry_manager()
        if telemetry:
            telemetry.record_api_request(
                endpoint="/clinical/analytics/outcomes",
                method="GET",
                status_code=500
            )
        
        raise HTTPException(
            status_code=500,
            detail="Failed to get intervention outcomes"
        )


@router.get(
    "/risk-stratification",
    response_model=Dict[str, Any],
    summary="Get patient risk stratification",
    description="Returns patient risk stratification analysis"
)
async def get_risk_stratification(
    current_user: Dict[str, Any] = Depends(get_current_user),
    scope: str = Depends(require_scope(RoleScopes.CLINICAL_VIEW)),
    redis = Depends(get_redis_client)
):
    """Get patient risk stratification analysis."""
    try:
        analytics = await get_clinical_analytics(redis)
        stratification = await analytics.get_patient_risk_stratification()
        
        # Record telemetry
        telemetry = get_telemetry_manager()
        if telemetry:
            telemetry.record_api_request(
                endpoint="/clinical/analytics/risk-stratification",
                method="GET",
                status_code=200
            )
        
        return stratification
    
    except Exception as e:
        logger.error(f"Error getting risk stratification: {e}")
        
        # Record telemetry
        telemetry = get_telemetry_manager()
        if telemetry:
            telemetry.record_api_request(
                endpoint="/clinical/analytics/risk-stratification",
                method="GET",
                status_code=500
            )
        
        raise HTTPException(
            status_code=500,
            detail="Failed to get risk stratification"
        )
