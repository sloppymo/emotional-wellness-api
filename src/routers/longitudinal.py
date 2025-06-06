"""
FastAPI router for longitudinal analysis API endpoints.

Provides patient history trend analysis, early warning detection,
and pattern recognition for clinical intervention.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Path

from api.security import (
    get_current_user, 
    RoleScopes, 
    require_scope,
    get_redis_client
)
from structured_logging import get_logger
from observability import get_telemetry_manager, ComponentName
from clinical.longitudinal import get_longitudinal_analyzer


# Configure router
router = APIRouter(
    prefix="/clinical/longitudinal",
    tags=["longitudinal"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden, insufficient permissions"},
        404: {"description": "Not found"}
    }
)

# Configure logger
logger = get_logger(__name__)


@router.get(
    "/patient/{patient_id}/history",
    response_model=Dict[str, Any],
    summary="Analyze patient history",
    description="Returns trend analysis results from patient historical data"
)
async def analyze_patient_history(
    patient_id: str = Path(..., description="Patient identifier"),
    days: int = Query(90, ge=10, le=365, description="Number of days to analyze"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    scope: str = Depends(require_scope(RoleScopes.CLINICAL_VIEW)),
    redis = Depends(get_redis_client)
):
    """Analyze patient history over the specified time period."""
    try:
        analyzer = await get_longitudinal_analyzer(redis)
        analysis = await analyzer.analyze_patient_history(patient_id=patient_id, days=days)
        
        # Record telemetry
        telemetry = get_telemetry_manager()
        if telemetry:
            with telemetry.create_span(
                name="clinical.analyze_patient_history",
                component=ComponentName.SECURITY
            ) as span:
                span.set_attribute("patient_id", patient_id)
                span.set_attribute("days_analyzed", days)
                span.set_attribute("data_points", analysis.get("data_points", 0))
            
            telemetry.record_api_request(
                endpoint=f"/clinical/longitudinal/patient/{patient_id}/history",
                method="GET",
                status_code=200
            )
        
        return analysis
    
    except Exception as e:
        logger.error(f"Error analyzing patient history: {e}")
        
        # Record telemetry
        telemetry = get_telemetry_manager()
        if telemetry:
            telemetry.record_api_request(
                endpoint=f"/clinical/longitudinal/patient/{patient_id}/history",
                method="GET",
                status_code=500
            )
        
        raise HTTPException(
            status_code=500,
            detail="Failed to analyze patient history"
        )


@router.get(
    "/patient/{patient_id}/warning",
    response_model=Dict[str, Any],
    summary="Early warning check",
    description="Performs early warning check for rising crisis risk"
)
async def early_warning_check(
    patient_id: str = Path(..., description="Patient identifier"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    scope: str = Depends(require_scope(RoleScopes.CLINICAL_VIEW)),
    redis = Depends(get_redis_client)
):
    """Perform early warning check for rising crisis risk."""
    try:
        analyzer = await get_longitudinal_analyzer(redis)
        warning = await analyzer.early_warning_check(patient_id=patient_id)
        
        # Record telemetry
        telemetry = get_telemetry_manager()
        if telemetry:
            with telemetry.create_span(
                name="clinical.early_warning_check",
                component=ComponentName.SECURITY
            ) as span:
                span.set_attribute("patient_id", patient_id)
                span.set_attribute("warning_status", warning.get("warning_status", "none"))
                span.set_attribute("warning_level", warning.get("warning_level", 0))
            
            telemetry.record_api_request(
                endpoint=f"/clinical/longitudinal/patient/{patient_id}/warning",
                method="GET",
                status_code=200
            )
        
        return warning
    
    except Exception as e:
        logger.error(f"Error performing early warning check: {e}")
        
        # Record telemetry
        telemetry = get_telemetry_manager()
        if telemetry:
            telemetry.record_api_request(
                endpoint=f"/clinical/longitudinal/patient/{patient_id}/warning",
                method="GET",
                status_code=500
            )
        
        raise HTTPException(
            status_code=500,
            detail="Failed to perform early warning check"
        )


@router.get(
    "/early-warnings",
    response_model=Dict[str, Any],
    summary="Scan for early warnings",
    description="Scans all patients for early warning signs of increasing risk"
)
async def scan_early_warnings(
    days: int = Query(30, ge=7, le=90, description="Look back period for trend analysis"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    scope: str = Depends(require_scope(RoleScopes.CLINICAL_VIEW)),
    redis = Depends(get_redis_client)
):
    """Scan all patients for early warning signs of increasing risk."""
    try:
        # Get current time for performance tracking
        start_time = datetime.utcnow()
        
        # Perform scan
        analyzer = await get_longitudinal_analyzer(redis)
        warnings = await analyzer.early_warning_scan(days_threshold=days)
        
        # Calculate execution time
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Record telemetry
        telemetry = get_telemetry_manager()
        if telemetry:
            with telemetry.create_span(
                name="clinical.scan_early_warnings",
                component=ComponentName.SECURITY
            ) as span:
                span.set_attribute("days_analyzed", days)
                span.set_attribute("warnings_detected", len(warnings))
                span.set_attribute("execution_time_seconds", execution_time)
            
            telemetry.record_api_request(
                endpoint="/clinical/longitudinal/early-warnings",
                method="GET",
                status_code=200
            )
        
        # Sort warnings by warning level (highest first)
        warnings.sort(key=lambda x: x.get("warning_level", 0), reverse=True)
        
        return {
            "warnings": warnings,
            "count": len(warnings),
            "execution_time_seconds": round(execution_time, 3),
            "days_analyzed": days
        }
    
    except Exception as e:
        logger.error(f"Error scanning for early warnings: {e}")
        
        # Record telemetry
        telemetry = get_telemetry_manager()
        if telemetry:
            telemetry.record_api_request(
                endpoint="/clinical/longitudinal/early-warnings",
                method="GET",
                status_code=500
            )
        
        raise HTTPException(
            status_code=500,
            detail="Failed to scan for early warnings"
        )
