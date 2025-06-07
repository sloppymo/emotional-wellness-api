"""
Anomaly Detection Middleware

This middleware integrates the anomaly detection system with the FastAPI application,
providing real-time monitoring of API requests and PHI access patterns.
"""

import time
import json
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ...security.anomaly import AnomalyEvent, AnomalyType, AnomalySeverity
from ...security.anomaly.detector import get_anomaly_detector
from ...utils.structured_logging import get_logger
from ...config.feature_flags import get_feature_flag_manager

logger = get_logger(__name__)


class AnomalyDetectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware for detecting anomalies in API request patterns.
    
    Monitors API request patterns for:
    - Unusual access times
    - Unusual request volumes
    - Suspicious access patterns
    - Potential data exfiltration attempts
    """
    
    def __init__(
        self, 
        app: ASGIApp,
        phi_endpoints: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None
    ):
        """
        Initialize middleware.
        
        Args:
            app: ASGI application
            phi_endpoints: List of endpoint paths that handle PHI
            exclude_paths: List of paths to exclude from monitoring
        """
        super().__init__(app)
        
        # Configure which endpoints handle PHI
        self.phi_endpoints = phi_endpoints or [
            "/api/wellness",
            "/api/patient",
            "/api/health-records",
            "/api/canopy"
        ]
        
        # Exclude paths from monitoring (e.g., health checks, static files)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/metrics",
            "/static",
            "/docs",
            "/openapi.json"
        ]
        
        # Track request counts per user for volume anomaly detection
        self.request_counts: Dict[str, Dict[str, int]] = {}
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process each request for anomaly detection.
        
        Args:
            request: Incoming request
            call_next: Next middleware or endpoint handler
            
        Returns:
            Response from next handler
        """
        # Skip monitoring for excluded paths
        for path in self.exclude_paths:
            if request.url.path.startswith(path):
                return await call_next(request)
                
        # Get user ID from request if authenticated
        user_id = await self._get_user_id(request)
        
        # Skip detailed analysis for unauthenticated requests
        if not user_id:
            return await call_next(request)
            
        # Check if anomaly detection is enabled via feature flags
        feature_flag_manager = await get_feature_flag_manager()
        anomaly_detection_enabled = await feature_flag_manager.get_flag_value(
            "anomaly_detection_enabled", 
            default_value=True
        )
        
        if not anomaly_detection_enabled:
            return await call_next(request)
            
        # Record start time
        start_time = time.time()
        is_phi_access = any(request.url.path.startswith(path) for path in self.phi_endpoints)
        
        # Pre-process the request - update counters and check for anomalies
        if is_phi_access:
            await self._update_request_counters(user_id, request)
            await self._check_pre_request_anomalies(user_id, request)
        
        # Process the request
        response = await call_next(request)
        
        # Post-process the request
        if is_phi_access:
            duration = time.time() - start_time
            await self._check_post_request_anomalies(user_id, request, response, duration)
        
        return response
    
    async def _get_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request."""
        # In a real implementation, this would get the actual user ID from authentication
        # This is a placeholder implementation
        if "authorization" in request.headers:
            # Extract user ID from token or session
            # For this example, we'll use a dummy value
            return "user-123"
        return None
        
    async def _update_request_counters(self, user_id: str, request: Request):
        """Update request counters for user."""
        current_minute = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        
        if user_id not in self.request_counts:
            self.request_counts[user_id] = {}
            
        if current_minute not in self.request_counts[user_id]:
            self.request_counts[user_id][current_minute] = 0
            
        self.request_counts[user_id][current_minute] += 1
        
        # Cleanup old entries
        old_minutes = [k for k in self.request_counts[user_id].keys() 
                      if k < datetime.utcnow().strftime("%Y-%m-%d %H:%M")]
                      
        for old_minute in old_minutes:
            del self.request_counts[user_id][old_minute]
    
    async def _check_pre_request_anomalies(self, user_id: str, request: Request):
        """Check for anomalies before processing request."""
        try:
            # Get anomaly detector
            anomaly_detector = await get_anomaly_detector()
            
            # Prepare event context
            context = {
                "path": request.url.path,
                "method": request.method,
                "client_ip": request.client.host if hasattr(request, "client") and request.client else None,
                "user_agent": request.headers.get("user-agent", ""),
                "referer": request.headers.get("referer", "")
            }
            
            # Check for unusual access time - consider this a PHI access event
            data_elements = ["request_data"]  # Placeholder for actual PHI elements
            anomaly = await anomaly_detector.process_phi_access_event(
                user_id=user_id,
                action=f"{request.method}_{request.url.path}",
                data_elements=data_elements,
                context=context
            )
            
            if anomaly:
                # Report the anomaly but allow request to continue
                await anomaly_detector.report_anomaly(anomaly)
                
                # For critical anomalies, we might want to block the request
                # This is commented out as it's a significant decision to block access
                # if anomaly.severity == AnomalySeverity.CRITICAL:
                #    raise HTTPException(status_code=403, detail="Access denied due to security concerns")
        
        except Exception as e:
            # Log error but don't block request on detection failure
            logger.error(f"Error in pre-request anomaly detection: {e}")
    
    async def _check_post_request_anomalies(self, 
                                          user_id: str, 
                                          request: Request,
                                          response: Response,
                                          duration: float):
        """Check for anomalies after processing request."""
        try:
            # Check for unusually large responses which could indicate data exfiltration
            response_size = len(response.body) if hasattr(response, "body") and response.body else 0
            
            # Check response size anomaly if significant
            if response_size > 1000000:  # 1MB threshold
                # Get anomaly detector
                anomaly_detector = await get_anomaly_detector()
                
                context = {
                    "path": request.url.path,
                    "method": request.method,
                    "response_size": response_size,
                    "response_time": duration,
                    "client_ip": request.client.host if hasattr(request, "client") and request.client else None
                }
                
                anomaly_event = AnomalyEvent(
                    event_type=AnomalyType.DATA_EXFILTRATION_ATTEMPT,
                    user_id=user_id,
                    system_component="api_response",
                    severity=AnomalySeverity.HIGH,
                    confidence_score=0.8,
                    description=f"Unusually large response: {response_size} bytes",
                    raw_data=context
                )
                
                await anomaly_detector.report_anomaly(anomaly_event)
                
        except Exception as e:
            # Log error but don't block response on detection failure
            logger.error(f"Error in post-request anomaly detection: {e}")
