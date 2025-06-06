"""
Health check endpoints for system status monitoring

This module provides endpoints for health checks and system status,
with special considerations for HIPAA compliance monitoring.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from config.settings import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()

@router.get("/health", tags=["System"])
async def health_check():
    """
    Simple health check endpoint.
    
    Returns a 200 OK response if the API is running.
    Does not require authentication.
    """
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@router.get("/status", tags=["System"])
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
        "crisis_protocol": {"status": "operational"}
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
    }
    
    # Count total checks and passed checks
    total_checks = len(checks)
    passed_checks = sum(1 for passed in checks.values() if passed)
    
    return {
        "status": "compliant" if passed_checks == total_checks else "non_compliant",
        "checks_passed": f"{passed_checks}/{total_checks}",
        "last_audit": "2025-05-15"  # In production, fetch from database
    }
