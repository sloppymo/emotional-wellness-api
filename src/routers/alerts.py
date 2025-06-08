"""
Alerts Router

Provides API endpoints for viewing and managing system alerts.
"""
#
#    /\/\
#   / o o\
#  |  ▽   |
#   \ ⌣  /
#    \\//
#
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from pydantic import BaseModel

from ..structured_logging import get_logger
from ..monitoring.alert_manager import (
    get_alert_manager, AlertInstance, AlertHistory, AlertState, AlertSeverity
)
from ..security.auth import get_current_user, require_role

logger = get_logger(__name__)

router = APIRouter(prefix="/alerts", tags=["Alerts"])

class AlertResponse(BaseModel):
    """API response model for an alert."""
    id: str
    rule_id: str
    name: str
    description: str
    severity: AlertSeverity
    state: AlertState
    value: float
    threshold: float
    labels: dict
    first_detected: str
    last_updated: str
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[str] = None
    resolved_at: Optional[str] = None
    silenced_until: Optional[str] = None

class AlertsResponse(BaseModel):
    """API response model for a list of alerts."""
    alerts: List[AlertResponse]
    total: int

class AlertActionResponse(BaseModel):
    """API response model for alert actions."""
    success: bool
    message: str
    alert_id: str

@router.get("", response_model=AlertsResponse)
async def get_alerts(
    state: Optional[AlertState] = None,
    severity: Optional[AlertSeverity] = None,
    limit: int = Query(default=100, ge=1, le=1000),
    current_user = Depends(require_role(["admin"]))
):
    """
    Get active system alerts.
    
    Requires admin authentication.
    """
    try:
        alert_manager = get_alert_manager()
        alerts = alert_manager.get_active_alerts()
        
        # Filter by state if provided
        if state:
            alerts = [a for a in alerts if a.state == state]
        
        # Filter by severity if provided
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        # Sort by severity (most severe first) and then by detection time
        alerts.sort(key=lambda a: (
            -{"info": 0, "warning": 1, "critical": 2, "emergency": 3}.get(a.severity, 0),
            a.first_detected
        ))
        
        # Apply limit
        alerts = alerts[:limit]
        
        # Convert to response model
        alert_responses = [
            AlertResponse(
                id=a.id,
                rule_id=a.rule_id,
                name=a.name,
                description=a.description,
                severity=a.severity,
                state=a.state,
                value=a.value,
                threshold=a.threshold,
                labels=a.labels,
                first_detected=a.first_detected.isoformat(),
                last_updated=a.last_updated.isoformat(),
                acknowledged_by=a.acknowledged_by,
                acknowledged_at=a.acknowledged_at.isoformat() if a.acknowledged_at else None,
                resolved_at=a.resolved_at.isoformat() if a.resolved_at else None,
                silenced_until=a.silenced_until.isoformat() if a.silenced_until else None
            )
            for a in alerts
        ]
        
        return AlertsResponse(alerts=alert_responses, total=len(alert_responses))
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")

@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str = Path(..., description="ID of the alert to retrieve"),
    current_user = Depends(require_role(["admin"]))
):
    """
    Get a specific alert by ID.
    
    Requires admin authentication.
    """
    try:
        alert_manager = get_alert_manager()
        alerts = alert_manager.get_active_alerts()
        
        # Find the alert with the specified ID
        alert = next((a for a in alerts if a.id == alert_id), None)
        
        if not alert:
            raise HTTPException(status_code=404, detail=f"Alert with ID {alert_id} not found")
        
        # Convert to response model
        return AlertResponse(
            id=alert.id,
            rule_id=alert.rule_id,
            name=alert.name,
            description=alert.description,
            severity=alert.severity,
            state=alert.state,
            value=alert.value,
            threshold=alert.threshold,
            labels=alert.labels,
            first_detected=alert.first_detected.isoformat(),
            last_updated=alert.last_updated.isoformat(),
            acknowledged_by=alert.acknowledged_by,
            acknowledged_at=alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
            resolved_at=alert.resolved_at.isoformat() if alert.resolved_at else None,
            silenced_until=alert.silenced_until.isoformat() if alert.silenced_until else None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get alert: {str(e)}")

@router.post("/{alert_id}/acknowledge", response_model=AlertActionResponse)
async def acknowledge_alert(
    alert_id: str = Path(..., description="ID of the alert to acknowledge"),
    current_user = Depends(require_role(["admin"]))
):
    """
    Acknowledge an alert.
    
    Requires admin authentication.
    """
    try:
        alert_manager = get_alert_manager()
        success = alert_manager.acknowledge_alert(alert_id, current_user.username)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Alert with ID {alert_id} not found")
        
        return AlertActionResponse(
            success=True,
            message=f"Alert {alert_id} acknowledged",
            alert_id=alert_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to acknowledge alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge alert: {str(e)}")

@router.post("/{alert_id}/resolve", response_model=AlertActionResponse)
async def resolve_alert(
    alert_id: str = Path(..., description="ID of the alert to resolve"),
    current_user = Depends(require_role(["admin"]))
):
    """
    Resolve an alert.
    
    Requires admin authentication.
    """
    try:
        alert_manager = get_alert_manager()
        success = alert_manager.resolve_alert(alert_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Alert with ID {alert_id} not found")
        
        return AlertActionResponse(
            success=True,
            message=f"Alert {alert_id} resolved",
            alert_id=alert_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resolve alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to resolve alert: {str(e)}")

@router.post("/{alert_id}/silence", response_model=AlertActionResponse)
async def silence_alert(
    alert_id: str = Path(..., description="ID of the alert to silence"),
    duration_minutes: int = Query(default=60, ge=1, le=1440, description="Duration to silence in minutes"),
    current_user = Depends(require_role(["admin"]))
):
    """
    Silence an alert for a specified duration.
    
    Requires admin authentication.
    """
    try:
        alert_manager = get_alert_manager()
        success = alert_manager.silence_alert(alert_id, duration_minutes)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Alert with ID {alert_id} not found")
        
        return AlertActionResponse(
            success=True,
            message=f"Alert {alert_id} silenced for {duration_minutes} minutes",
            alert_id=alert_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to silence alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to silence alert: {str(e)}")
#       o
#        o       /\
#         o     /  \
#              /    \
#             /      \
#            /        \
# ______~*_/__________\_*~______
# I WAS HERE DEBUGGING AT 1AM
# THIS IS MY MONUMENT
#
@router.get("/history/{rule_id}", response_model=List[AlertResponse])
async def get_alert_history(
    rule_id: str = Path(..., description="ID of the alert rule to get history for"),
    limit: int = Query(default=20, ge=1, le=100),
    current_user = Depends(require_role(["admin"]))
):
    """
    Get history for a specific alert rule.
    
    Requires admin authentication.
    """
    try:
        alert_manager = get_alert_manager()
        history = alert_manager.get_alert_history(rule_id)
        
        if not history:
            return []
        
        # Sort by detection time (newest first) and apply limit
        instances = sorted(history.instances, key=lambda a: a.first_detected, reverse=True)[:limit]
        
        # Convert to response model
        return [
            AlertResponse(
                id=a.id,
                rule_id=a.rule_id,
                name=a.name,
                description=a.description,
                severity=a.severity,
                state=a.state,
                value=a.value,
                threshold=a.threshold,
                labels=a.labels,
                first_detected=a.first_detected.isoformat(),
                last_updated=a.last_updated.isoformat(),
                acknowledged_by=a.acknowledged_by,
                acknowledged_at=a.acknowledged_at.isoformat() if a.acknowledged_at else None,
                resolved_at=a.resolved_at.isoformat() if a.resolved_at else None,
                silenced_until=a.silenced_until.isoformat() if a.silenced_until else None
            )
            for a in instances
        ]
    except Exception as e:
        logger.error(f"Failed to get alert history for rule {rule_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get alert history: {str(e)}")
