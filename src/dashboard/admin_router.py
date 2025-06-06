"""
Admin Dashboard Router

Provides routes for the admin monitoring dashboard.
"""

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
from pathlib import Path

from ..structured_logging import get_logger
from ..security.auth import get_current_user, require_role
from ..monitoring.alert_manager import get_alert_manager
from ..monitoring.metrics_collector import get_metrics_collector

logger = get_logger(__name__)

# Set up templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    current_user = Depends(require_role(["admin"]))
):
    """
    Admin dashboard home page.
    
    Requires admin authentication.
    """
    try:
        return templates.TemplateResponse(
            "admin/dashboard.html",
            {
                "request": request,
                "user": current_user,
                "page_title": "Admin Dashboard"
            }
        )
    except Exception as e:
        logger.error(f"Error rendering admin dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Error rendering dashboard: {str(e)}")

@router.get("/monitoring", response_class=HTMLResponse)
async def monitoring_dashboard(
    request: Request,
    current_user = Depends(require_role(["admin"]))
):
    """
    System monitoring dashboard.
    
    Requires admin authentication.
    """
    try:
        # Get active alerts
        alert_manager = get_alert_manager()
        active_alerts = alert_manager.get_active_alerts()
        
        # Sort alerts by severity
        severity_order = {"emergency": 0, "critical": 1, "warning": 2, "info": 3}
        active_alerts.sort(key=lambda a: severity_order.get(a.severity, 4))
        
        return templates.TemplateResponse(
            "admin/monitoring_dashboard.html",
            {
                "request": request,
                "user": current_user,
                "page_title": "System Monitoring",
                "active_alerts": active_alerts,
                "alert_count": len(active_alerts)
            }
        )
    except Exception as e:
        logger.error(f"Error rendering monitoring dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Error rendering dashboard: {str(e)}")

@router.get("/alerts", response_class=HTMLResponse)
async def alerts_dashboard(
    request: Request,
    current_user = Depends(require_role(["admin"]))
):
    """
    System alerts dashboard.
    
    Requires admin authentication.
    """
    try:
        # Get active alerts
        alert_manager = get_alert_manager()
        active_alerts = alert_manager.get_active_alerts()
        
        # Sort alerts by severity and then by time
        severity_order = {"emergency": 0, "critical": 1, "warning": 2, "info": 3}
        active_alerts.sort(key=lambda a: (
            severity_order.get(a.severity, 4),
            a.first_detected
        ))
        
        return templates.TemplateResponse(
            "admin/alerts_dashboard.html",
            {
                "request": request,
                "user": current_user,
                "page_title": "System Alerts",
                "active_alerts": active_alerts,
                "alert_count": len(active_alerts)
            }
        )
    except Exception as e:
        logger.error(f"Error rendering alerts dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Error rendering dashboard: {str(e)}")

@router.get("/metrics", response_class=HTMLResponse)
async def metrics_dashboard(
    request: Request,
    current_user = Depends(require_role(["admin"]))
):
    """
    System metrics dashboard.
    
    Requires admin authentication.
    """
    try:
        return templates.TemplateResponse(
            "admin/metrics_dashboard.html",
            {
                "request": request,
                "user": current_user,
                "page_title": "System Metrics"
            }
        )
    except Exception as e:
        logger.error(f"Error rendering metrics dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Error rendering dashboard: {str(e)}")

@router.get("/tasks", response_class=HTMLResponse)
async def tasks_dashboard(
    request: Request,
    current_user = Depends(require_role(["admin"]))
):
    """
    Background tasks dashboard.
    
    Requires admin authentication.
    """
    try:
        return templates.TemplateResponse(
            "admin/tasks_dashboard.html",
            {
                "request": request,
                "user": current_user,
                "page_title": "Background Tasks"
            }
        )
    except Exception as e:
        logger.error(f"Error rendering tasks dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Error rendering dashboard: {str(e)}")

@router.get("/integrations", response_class=HTMLResponse)
async def integrations_dashboard(
    request: Request,
    current_user = Depends(require_role(["admin"]))
):
    """
    External integrations dashboard.
    
    Requires admin authentication.
    """
    try:
        return templates.TemplateResponse(
            "admin/integrations_dashboard.html",
            {
                "request": request,
                "user": current_user,
                "page_title": "External Integrations"
            }
        )
    except Exception as e:
        logger.error(f"Error rendering integrations dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Error rendering dashboard: {str(e)}")
