"""
FastAPI router for the clinician portal API endpoints.

Provides endpoints for managing clinical alerts, interventions,
and patient risk management.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
from pydantic import UUID4

from api.security import (
    get_current_user, 
    RoleScopes, 
    require_scope,
    get_redis_client
)
from observability import get_telemetry_manager, ComponentName
from structured_logging import get_logger
from clinical.service import get_clinical_service
from clinical.models import (
    PatientAlert, 
    ClinicalIntervention,
    PatientRiskProfile,
    ClinicalDashboardSummary,
    ResourceReferral, 
    InterventionType, 
    InterventionStatus, 
    ClinicalPriority
)
from symbolic.moss.crisis_classifier import CrisisSeverity, RiskDomain


# Configure router
router = APIRouter(
    prefix="/clinical",
    tags=["clinical"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden, insufficient permissions"},
        404: {"description": "Not found"}
    }
)

# Configure logger
logger = get_logger(__name__)


@router.get(
    "/dashboard", 
    response_model=ClinicalDashboardSummary,
    summary="Get clinical dashboard summary",
    description="Returns a summary of clinical data for the dashboard"
)
async def get_dashboard_summary(
    current_user: Dict[str, Any] = Depends(get_current_user),
    scope: str = Depends(require_scope(RoleScopes.CLINICAL_VIEW)),
    redis = Depends(get_redis_client)
):
    """Get a summary of clinical data for the dashboard."""
    
    # Get clinical service
    clinical_service = get_clinical_service(redis=redis)
    
    # Get dashboard summary
    try:
        dashboard = await clinical_service.get_dashboard_summary()
        
        # Record telemetry
        telemetry = get_telemetry_manager()
        if telemetry:
            telemetry.record_api_request(
                endpoint="/clinical/dashboard",
                method="GET",
                status_code=200
            )
        
        return dashboard
    
    except Exception as e:
        logger.error(f"Error getting dashboard summary: {e}")
        
        # Record telemetry
        telemetry = get_telemetry_manager()
        if telemetry:
            telemetry.record_api_request(
                endpoint="/clinical/dashboard",
                method="GET",
                status_code=500
            )
        
        raise HTTPException(
            status_code=500,
            detail="Failed to get dashboard summary"
        )


@router.get(
    "/alerts", 
    response_model=List[PatientAlert],
    summary="Get active clinical alerts",
    description="Returns a list of active clinical alerts"
)
async def get_active_alerts(
    limit: int = Query(20, ge=1, le=100),
    include_acknowledged: bool = Query(False),
    current_user: Dict[str, Any] = Depends(get_current_user),
    scope: str = Depends(require_scope(RoleScopes.CLINICAL_VIEW)),
    redis = Depends(get_redis_client)
):
    """Get active clinical alerts."""
    try:
        # For now, we'll just return the alerts from the dashboard summary
        # In a real implementation, we would fetch from a dedicated alerts service
        clinical_service = get_clinical_service(redis=redis)
        dashboard = await clinical_service.get_dashboard_summary()
        
        alerts = dashboard.recent_alerts
        
        # Filter out acknowledged alerts if requested
        if not include_acknowledged:
            alerts = [alert for alert in alerts if not alert.acknowledged]
        
        # Limit results
        alerts = alerts[:limit]
        
        # Record telemetry
        telemetry = get_telemetry_manager()
        if telemetry:
            telemetry.record_api_request(
                endpoint="/clinical/alerts",
                method="GET",
                status_code=200
            )
        
        return alerts
    
    except Exception as e:
        logger.error(f"Error getting active alerts: {e}")
        
        # Record telemetry
        telemetry = get_telemetry_manager()
        if telemetry:
            telemetry.record_api_request(
                endpoint="/clinical/alerts",
                method="GET",
                status_code=500
            )
        
        raise HTTPException(
            status_code=500,
            detail="Failed to get active alerts"
        )


@router.get(
    "/patients/{patient_id}/alerts", 
    response_model=List[PatientAlert],
    summary="Get patient alerts",
    description="Returns a list of alerts for a specific patient"
)
async def get_patient_alerts(
    patient_id: str = Path(..., description="Patient identifier"),
    limit: int = Query(10, ge=1, le=50),
    include_acknowledged: bool = Query(False),
    current_user: Dict[str, Any] = Depends(get_current_user),
    scope: str = Depends(require_scope(RoleScopes.CLINICAL_VIEW)),
    redis = Depends(get_redis_client)
):
    """Get alerts for a specific patient."""
    try:
        clinical_service = get_clinical_service(redis=redis)
        
        alerts = await clinical_service.get_patient_alerts(
            patient_id=patient_id,
            limit=limit,
            include_acknowledged=include_acknowledged
        )
        
        # Record telemetry
        telemetry = get_telemetry_manager()
        if telemetry:
            telemetry.record_api_request(
                endpoint=f"/clinical/patients/{patient_id}/alerts",
                method="GET",
                status_code=200
            )
        
        return alerts
    
    except Exception as e:
        logger.error(f"Error getting patient alerts: {e}")
        
        # Record telemetry
        telemetry = get_telemetry_manager()
        if telemetry:
            telemetry.record_api_request(
                endpoint=f"/clinical/patients/{patient_id}/alerts",
                method="GET",
                status_code=500
            )
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get alerts for patient {patient_id}"
        )


@router.post(
    "/alerts/{alert_id}/acknowledge", 
    response_model=PatientAlert,
    summary="Acknowledge an alert",
    description="Marks an alert as acknowledged by the current clinician"
)
async def acknowledge_alert(
    alert_id: str = Path(..., description="Alert identifier"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    scope: str = Depends(require_scope(RoleScopes.CLINICAL_MANAGE)),
    redis = Depends(get_redis_client)
):
    """Acknowledge an alert."""
    try:
        clinical_service = get_clinical_service(redis=redis)
        
        # Get clinician ID from current user
        clinician_id = current_user.get("sub", "unknown")
        
        # Acknowledge alert
        updated_alert = await clinical_service.acknowledge_alert(
            alert_id=alert_id,
            clinician_id=clinician_id
        )
        
        # Record telemetry
        telemetry = get_telemetry_manager()
        if telemetry:
            telemetry.record_api_request(
                endpoint=f"/clinical/alerts/{alert_id}/acknowledge",
                method="POST",
                status_code=200
            )
        
        return updated_alert
    
    except ValueError as e:
        logger.error(f"Error acknowledging alert: {e}")
        
        # Record telemetry
        telemetry = get_telemetry_manager()
        if telemetry:
            telemetry.record_api_request(
                endpoint=f"/clinical/alerts/{alert_id}/acknowledge",
                method="POST",
                status_code=404
            )
        
        raise HTTPException(
            status_code=404,
            detail=f"Alert {alert_id} not found"
        )
    
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        
        # Record telemetry
        telemetry = get_telemetry_manager()
        if telemetry:
            telemetry.record_api_request(
                endpoint=f"/clinical/alerts/{alert_id}/acknowledge",
                method="POST",
                status_code=500
            )
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to acknowledge alert {alert_id}"
        )


class InterventionCreate:
    """Request model for creating an intervention."""
    patient_id: str
    intervention_type: InterventionType
    priority: ClinicalPriority
    alert_id: Optional[str] = None
    notes: Optional[str] = None
    scheduled_for: Optional[datetime] = None


@router.post(
    "/interventions", 
    response_model=ClinicalIntervention,
    summary="Create an intervention",
    description="Creates a new clinical intervention"
)
async def create_intervention(
    intervention: InterventionCreate = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    scope: str = Depends(require_scope(RoleScopes.CLINICAL_MANAGE)),
    redis = Depends(get_redis_client)
):
    """Create a new clinical intervention."""
    try:
        clinical_service = get_clinical_service(redis=redis)
        
        # Get clinician ID from current user
        clinician_id = current_user.get("sub", "unknown")
        
        # Create intervention
        new_intervention = await clinical_service.create_intervention(
            patient_id=intervention.patient_id,
            intervention_type=intervention.intervention_type,
            created_by=clinician_id,
            priority=intervention.priority,
            alert_id=intervention.alert_id,
            notes=intervention.notes or "",
            scheduled_for=intervention.scheduled_for
        )
        
        # Record telemetry
        telemetry = get_telemetry_manager()
        if telemetry:
            telemetry.record_api_request(
                endpoint="/clinical/interventions",
                method="POST",
                status_code=200
            )
        
        return new_intervention
    
    except Exception as e:
        logger.error(f"Error creating intervention: {e}")
        
        # Record telemetry
        telemetry = get_telemetry_manager()
        if telemetry:
            telemetry.record_api_request(
                endpoint="/clinical/interventions",
                method="POST",
                status_code=500
            )
        
        raise HTTPException(
            status_code=500,
            detail="Failed to create intervention"
        )


class InterventionStatusUpdate:
    """Request model for updating intervention status."""
    status: InterventionStatus
    notes: Optional[str] = None


@router.put(
    "/interventions/{intervention_id}/status", 
    response_model=ClinicalIntervention,
    summary="Update intervention status",
    description="Updates the status of a clinical intervention"
)
async def update_intervention_status(
    intervention_id: str = Path(..., description="Intervention identifier"),
    update: InterventionStatusUpdate = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    scope: str = Depends(require_scope(RoleScopes.CLINICAL_MANAGE)),
    redis = Depends(get_redis_client)
):
    """Update the status of a clinical intervention."""
    try:
        clinical_service = get_clinical_service(redis=redis)
        
        # Update intervention status
        updated_intervention = await clinical_service.update_intervention_status(
            intervention_id=intervention_id,
            status=update.status,
            notes=update.notes
        )
        
        # Record telemetry
        telemetry = get_telemetry_manager()
        if telemetry:
            telemetry.record_api_request(
                endpoint=f"/clinical/interventions/{intervention_id}/status",
                method="PUT",
                status_code=200
            )
        
        return updated_intervention
    
    except ValueError as e:
        logger.error(f"Error updating intervention status: {e}")
        
        # Record telemetry
        telemetry = get_telemetry_manager()
        if telemetry:
            telemetry.record_api_request(
                endpoint=f"/clinical/interventions/{intervention_id}/status",
                method="PUT",
                status_code=404
            )
        
        raise HTTPException(
            status_code=404,
            detail=f"Intervention {intervention_id} not found"
        )
    
    except Exception as e:
        logger.error(f"Error updating intervention status: {e}")
        
        # Record telemetry
        telemetry = get_telemetry_manager()
        if telemetry:
            telemetry.record_api_request(
                endpoint=f"/clinical/interventions/{intervention_id}/status",
                method="PUT",
                status_code=500
            )
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update intervention {intervention_id}"
        )
