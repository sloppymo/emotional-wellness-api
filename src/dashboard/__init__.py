"""Clinical Dashboard for Emotional Wellness API."""

from .router import router as dashboard_router
from .admin_router import router as admin_router

__all__ = ['dashboard_router', 'admin_router']