"""
Security router for the Emotional Wellness API.

Provides endpoints for security scanning and reporting to support HIPAA compliance
and security hardening efforts.
"""

from typing import Dict, Any
from datetime import datetime
import json

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials
from redis.asyncio import Redis

from security.scanner import get_security_scanner, SecurityScanner
from security.auth import get_api_key
from api.security import get_current_user, RoleScopeValidator
from db.redis import get_redis
from observability import get_telemetry_manager, ComponentName, record_span
from structured_logging import get_logger

# Configure router
router = APIRouter(prefix="/security", tags=["Security"])
logger = get_logger(__name__)

# Role-based access control for security endpoints
require_security_admin = RoleScopeValidator(required_scope="SECURITY_ADMIN")


@router.post("/scan", response_model=Dict[str, Any])
@record_span("api.security_scan", ComponentName.API)
async def run_security_scan(
    app=None,  # Will be injected by middleware
    user: Dict[str, Any] = Security(get_current_user, scopes=["SECURITY_ADMIN"]),
    api_key: HTTPAuthorizationCredentials = Depends(get_api_key),
    redis: Redis = Depends(get_redis)
):
    """
    Run a comprehensive security scan.
    
    Scans environment variables, API endpoints, and security configurations
    for potential vulnerabilities.
    
    Restricted to users with SECURITY_ADMIN scope.
    """
    logger.info(f"Security scan initiated by user ID: {user.get('sub')}")
    
    try:
        # Get the security scanner instance
        scanner = await get_security_scanner(app, redis)
        
        # Run the full scan
        scan_results = await scanner.full_scan()
        
        # Get telemetry manager if available
        telemetry = get_telemetry_manager()
        if telemetry:
            telemetry.record_custom_metric(
                name="security_scan_execution",
                value=1,
                attributes={
                    "findings_count": scan_results.get("total_findings", 0),
                    "critical_findings": scan_results.get("findings_by_severity", {}).get("critical", 0)
                }
            )
        
        return {
            "status": "success",
            "scan_id": f"security:scan:{datetime.utcnow().isoformat()}",
            "timestamp": datetime.utcnow().isoformat(),
            "results": scan_results
        }
    except Exception as e:
        logger.error(f"Error during security scan: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred during the security scan"
        )


@router.get("/history", response_model=Dict[str, Any])
@record_span("api.security_history", ComponentName.API)
async def get_security_scan_history(
    limit: int = 10,
    user: Dict[str, Any] = Security(get_current_user, scopes=["SECURITY_ADMIN"]),
    api_key: HTTPAuthorizationCredentials = Depends(get_api_key),
    redis: Redis = Depends(get_redis)
):
    """
    Get historical security scan results.
    
    Returns a list of previous security scans with their findings.
    
    Restricted to users with SECURITY_ADMIN scope.
    """
    logger.info(f"Security scan history requested by user ID: {user.get('sub')}")
    
    try:
        # Get scan IDs from Redis list
        scan_ids = await redis.lrange("security:scans", 0, limit - 1)
        
        # Get scan results for each ID
        scans = []
        for scan_id in scan_ids:
            scan_data = await redis.get(scan_id)
            if scan_data:
                scan = json.loads(scan_data)
                # Add the scan ID
                scan["id"] = scan_id
                scans.append(scan)
        
        return {
            "status": "success",
            "scans": scans,
            "count": len(scans),
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error retrieving security scan history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving security scan history"
        )


@router.get("/findings/summary", response_model=Dict[str, Any])
@record_span("api.security_findings_summary", ComponentName.API)
async def get_security_findings_summary(
    user: Dict[str, Any] = Security(get_current_user, scopes=["SECURITY_ADMIN"]),
    api_key: HTTPAuthorizationCredentials = Depends(get_api_key),
    redis: Redis = Depends(get_redis)
):
    """
    Get a summary of recent security findings.
    
    Returns counts of findings by severity level from the most recent scan.
    
    Restricted to users with SECURITY_ADMIN scope.
    """
    logger.info(f"Security findings summary requested by user ID: {user.get('sub')}")
    
    try:
        # Get the most recent scan ID
        scan_ids = await redis.lrange("security:scans", 0, 0)
        if not scan_ids:
            return {
                "status": "success",
                "message": "No security scans found",
                "findings": {}
            }
        
        # Get the scan data
        scan_data = await redis.get(scan_ids[0])
        if not scan_data:
            return {
                "status": "success",
                "message": "No security scan data found",
                "findings": {}
            }
        
        scan = json.loads(scan_data)
        
        # Extract findings summary
        findings_summary = scan.get("findings_by_severity", {})
        
        return {
            "status": "success",
            "scan_id": scan_ids[0],
            "timestamp": scan.get("timestamp", datetime.utcnow().isoformat()),
            "findings": findings_summary,
            "total": scan.get("total_findings", 0)
        }
    except Exception as e:
        logger.error(f"Error retrieving security findings summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving security findings summary"
        )
