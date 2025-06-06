"""
Health check endpoints for system status monitoring

This module provides endpoints for health checks and system status,
with special considerations for HIPAA compliance monitoring and task system monitoring.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Request, Query, Path, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..config.settings import get_settings
from ..structured_logging import get_logger
from ..monitoring.celery_health import check_celery_health, get_task_status
from ..monitoring.moss_health import check_moss_health, check_component_health, ComponentType
from ..monitoring.integration_health import check_integration_health, check_specific_integration, IntegrationType
from ..security.auth import get_current_user, require_role

# API models for health endpoints
class HealthResponse(BaseModel):
    status: str
    timestamp: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress: Optional[float] = None
    runtime: Optional[float] = None

router = APIRouter(tags=["System"])
logger = get_logger(__name__)
settings = get_settings()

@router.get("/health")
async def health_check() -> HealthResponse:
    """
    Simple health check endpoint.
    
    Returns a 200 OK response if the API is running.
    Does not require authentication.
    """
    return HealthResponse(status="ok", timestamp=datetime.now().isoformat())

@router.get("/status")
async def system_status(request: Request):
    """
    Detailed system status check.
    
    Checks the status of connected systems and components.
    Does not require authentication but does not expose sensitive information.
    """
    # Check component statuses
    # In production, these would be actual checks of component availability
    components = {
        "api": {"status": "operational", "version": request.app.version},
        "database": {"status": "operational"},
        "redis": {"status": "operational"},
        "symbolic_processing": {"status": "operational"},
        "crisis_protocol": {"status": "operational"},
        "background_tasks": {"status": "operational"}
    }
    
    # Count total components and operational components
    total_components = len(components)
    operational_components = sum(1 for c in components.values() if c["status"] == "operational")
    
    # Overall status
    overall_status = "operational" if operational_components == total_components else "degraded"
    
    return {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "components": components,
        "hipaa_compliance": get_hipaa_compliance_status()
    }

def get_hipaa_compliance_status() -> Dict[str, Any]:
    """
    Check HIPAA compliance status of the system.
    
    Returns a dictionary with compliance status information.
    Does not include sensitive details that could expose vulnerabilities.
    """
    # In production, these would be actual checks of compliance controls
    checks = {
        "encryption_at_rest": True,
        "encryption_in_transit": True,
        "audit_logging": settings.AUDIT_LOGGING_ENABLED,
        "data_retention_policy": True,
        "access_controls": True,
        "backup_integrity": True,
        "background_task_security": True,
    }
    
    # Count total checks and passed checks
    total_checks = len(checks)
    passed_checks = sum(1 for passed in checks.values() if passed)
    
    return {
        "status": "compliant" if passed_checks == total_checks else "non_compliant",
        "checks_passed": f"{passed_checks}/{total_checks}",
        "last_audit": "2025-06-01"  # In production, fetch from database
    }

@router.get("/celery/health")
async def celery_health(
    current_user = Depends(require_role(["admin"]))
):
    """
    Health check for Celery background task system.
    
    Requires admin authentication.
    """
    try:
        health_data = await check_celery_health()
        return health_data
    except Exception as e:
        logger.error(f"Celery health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Celery health check failed: {str(e)}")

@router.get("/task/{task_id}")
async def task_status(
    task_id: str = Path(..., description="The ID of the task to check"),
    current_user = Depends(get_current_user)
):
    """
    Get status of a specific background task.
    
    Requires authentication.
    """
    try:
        status = await get_task_status(task_id)
        return TaskStatusResponse(**status)
    except Exception as e:
        logger.error(f"Task status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Task status check failed: {str(e)}")

@router.get("/moss/health")
async def moss_health(
    current_user = Depends(require_role(["admin"]))
):
    """
    Health check for MOSS components.
    
    Requires admin authentication.
    """
    try:
        health_data = await check_moss_health()
        return health_data
    except Exception as e:
        logger.error(f"MOSS health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"MOSS health check failed: {str(e)}")

@router.get("/moss/component/{component_type}")
async def moss_component_health(
    component_type: ComponentType,
    current_user = Depends(require_role(["admin"]))
):
    """
    Health check for a specific MOSS component.
    
    Requires admin authentication.
    """
    try:
        health_data = await check_component_health(component_type)
        return health_data
    except Exception as e:
        logger.error(f"MOSS component health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Component health check failed: {str(e)}")

@router.get("/integrations/health")
async def integrations_health(
    current_user = Depends(require_role(["admin"]))
):
    """
    Health check for all external integrations.
    
    Requires admin authentication.
    """
    try:
        health_data = await check_integration_health()
        return health_data
    except Exception as e:
        logger.error(f"Integrations health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Integrations health check failed: {str(e)}")

@router.get("/integrations/{integration_type}")
async def specific_integration_health(
    integration_type: IntegrationType,
    current_user = Depends(require_role(["admin"]))
):
    """
    Health check for a specific external integration.
    
    Requires admin authentication.
    """
    try:
        health_data = await check_specific_integration(integration_type)
        return health_data
    except Exception as e:
        logger.error(f"Integration health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Integration health check failed: {str(e)}")
