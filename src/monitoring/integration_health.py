"""
Integration Health Monitoring

This module provides health checks for external service integrations:
- MOSS symbolic processing system
- Crisis response system
- Authentication services
- External notification providers
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

from pydantic import BaseModel, Field

from ..structured_logging import get_logger
from ..config import settings

logger = get_logger(__name__)

class IntegrationStatus(str, Enum):
    """Status of an external integration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"

class IntegrationType(str, Enum):
    """Types of external integrations."""
    MOSS = "moss"
    CRISIS_RESPONSE = "crisis_response"
    AUTH_SERVICE = "auth_service"
    NOTIFICATION_SERVICE = "notification_service"
    EXTERNAL_ANALYTICS = "external_analytics"

class IntegrationHealthCheck(BaseModel):
    """Health check result for an external integration."""
    integration_type: IntegrationType
    status: IntegrationStatus
    latency_ms: Optional[float] = None
    last_success: Optional[datetime] = None
    error_message: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class IntegrationHealthSummary(BaseModel):
    """Summary of all integration health checks."""
    overall_status: IntegrationStatus
    integrations: List[IntegrationHealthCheck] = Field(default_factory=list)
    response_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class IntegrationHealthMonitor:
    """Monitor health of external integrations."""
    
    def __init__(self):
        """Initialize integration health monitor."""
        self._logger = get_logger(f"{__name__}.IntegrationHealthMonitor")
        
        # Store last successful checks
        self._last_successful_checks = {}
        
    async def check_all_integrations(self) -> IntegrationHealthSummary:
        """Check health of all external integrations."""
        start_time = time.time()
        
        try:
            # Check all integrations in parallel
            integration_checks = [
                self._check_moss_integration(),
                self._check_crisis_response_integration(),
                self._check_auth_service_integration(),
                self._check_notification_service_integration()
            ]
            
            results = await asyncio.gather(*integration_checks, return_exceptions=True)
            
            # Process results
            integration_results = []
            for result in results:
                if isinstance(result, Exception):
                    self._logger.error(f"Integration health check failed: {result}")
                    # Create a generic error health check
                    integration_results.append(IntegrationHealthCheck(
                        integration_type=IntegrationType.UNKNOWN,
                        status=IntegrationStatus.UNAVAILABLE,
                        error_message=str(result)
                    ))
                else:
                    integration_results.append(result)
            
            # Determine overall status
            overall_status = self._determine_overall_status(integration_results)
            
            return IntegrationHealthSummary(
                overall_status=overall_status,
                integrations=integration_results,
                response_time_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            self._logger.error(f"Failed to check integration health: {str(e)}", exc_info=True)
            return IntegrationHealthSummary(
                overall_status=IntegrationStatus.UNKNOWN,
                response_time_ms=(time.time() - start_time) * 1000
            )
    
    def _determine_overall_status(
        self, integration_checks: List[IntegrationHealthCheck]
    ) -> IntegrationStatus:
        """Determine overall status based on individual integration statuses."""
        if not integration_checks:
            return IntegrationStatus.UNKNOWN
        
        # Count statuses
        status_counts = {
            IntegrationStatus.HEALTHY: 0,
            IntegrationStatus.DEGRADED: 0,
            IntegrationStatus.UNAVAILABLE: 0,
            IntegrationStatus.UNKNOWN: 0
        }
        
        for check in integration_checks:
            status_counts[check.status] += 1
        
        # Determine overall status
        if status_counts[IntegrationStatus.UNAVAILABLE] > 0:
            return IntegrationStatus.DEGRADED
        
        if status_counts[IntegrationStatus.DEGRADED] > 0:
            return IntegrationStatus.DEGRADED
        
        if status_counts[IntegrationStatus.UNKNOWN] == len(integration_checks):
            return IntegrationStatus.UNKNOWN
        
        return IntegrationStatus.HEALTHY
    
    async def _check_moss_integration(self) -> IntegrationHealthCheck:
        """Check health of MOSS integration."""
        start_time = time.time()
        
        try:
            # Import here to avoid circular imports
            from ..integration.moss_adapter import MOSSAdapter
            
            # Create test instance
            moss_adapter = MOSSAdapter()
            
            # Try a lightweight operation
            is_available = await moss_adapter.ping()
            
            latency = (time.time() - start_time) * 1000
            
            if is_available:
                self._last_successful_checks[IntegrationType.MOSS] = datetime.utcnow()
                return IntegrationHealthCheck(
                    integration_type=IntegrationType.MOSS,
                    status=IntegrationStatus.HEALTHY,
                    latency_ms=latency,
                    last_success=datetime.utcnow()
                )
            else:
                return IntegrationHealthCheck(
                    integration_type=IntegrationType.MOSS,
                    status=IntegrationStatus.DEGRADED,
                    latency_ms=latency,
                    last_success=self._last_successful_checks.get(IntegrationType.MOSS),
                    error_message="MOSS system reported unavailable"
                )
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            self._logger.error(f"MOSS health check failed: {str(e)}")
            return IntegrationHealthCheck(
                integration_type=IntegrationType.MOSS,
                status=IntegrationStatus.UNAVAILABLE,
                latency_ms=latency,
                last_success=self._last_successful_checks.get(IntegrationType.MOSS),
                error_message=str(e)
            )
    
    async def _check_crisis_response_integration(self) -> IntegrationHealthCheck:
        """Check health of crisis response integration."""
        start_time = time.time()
        
        try:
            # In a real implementation, we would check the crisis response system
            # For now, we'll simulate a successful check
            await asyncio.sleep(0.1)  # Simulate network latency
            
            latency = (time.time() - start_time) * 1000
            self._last_successful_checks[IntegrationType.CRISIS_RESPONSE] = datetime.utcnow()
            
            return IntegrationHealthCheck(
                integration_type=IntegrationType.CRISIS_RESPONSE,
                status=IntegrationStatus.HEALTHY,
                latency_ms=latency,
                last_success=datetime.utcnow(),
                details={"endpoints_available": 5}
            )
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            self._logger.error(f"Crisis response health check failed: {str(e)}")
            return IntegrationHealthCheck(
                integration_type=IntegrationType.CRISIS_RESPONSE,
                status=IntegrationStatus.UNAVAILABLE,
                latency_ms=latency,
                last_success=self._last_successful_checks.get(IntegrationType.CRISIS_RESPONSE),
                error_message=str(e)
            )
    
    async def _check_auth_service_integration(self) -> IntegrationHealthCheck:
        """Check health of authentication service integration."""
        start_time = time.time()
        
        try:
            # In a real implementation, we would check the auth service
            # For now, we'll simulate a successful check
            await asyncio.sleep(0.05)  # Simulate network latency
            
            latency = (time.time() - start_time) * 1000
            self._last_successful_checks[IntegrationType.AUTH_SERVICE] = datetime.utcnow()
            
            return IntegrationHealthCheck(
                integration_type=IntegrationType.AUTH_SERVICE,
                status=IntegrationStatus.HEALTHY,
                latency_ms=latency,
                last_success=datetime.utcnow()
            )
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            self._logger.error(f"Auth service health check failed: {str(e)}")
            return IntegrationHealthCheck(
                integration_type=IntegrationType.AUTH_SERVICE,
                status=IntegrationStatus.UNAVAILABLE,
                latency_ms=latency,
                last_success=self._last_successful_checks.get(IntegrationType.AUTH_SERVICE),
                error_message=str(e)
            )
    
    async def _check_notification_service_integration(self) -> IntegrationHealthCheck:
        """Check health of notification service integration."""
        start_time = time.time()
        
        try:
            # In a real implementation, we would check notification services
            # For now, we'll simulate a successful check
            await asyncio.sleep(0.075)  # Simulate network latency
            
            latency = (time.time() - start_time) * 1000
            self._last_successful_checks[IntegrationType.NOTIFICATION_SERVICE] = datetime.utcnow()
            
            return IntegrationHealthCheck(
                integration_type=IntegrationType.NOTIFICATION_SERVICE,
                status=IntegrationStatus.HEALTHY,
                latency_ms=latency,
                last_success=datetime.utcnow(),
                details={
                    "sms_provider": "available",
                    "email_provider": "available",
                    "app_notifications": "available"
                }
            )
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            self._logger.error(f"Notification service health check failed: {str(e)}")
            return IntegrationHealthCheck(
                integration_type=IntegrationType.NOTIFICATION_SERVICE,
                status=IntegrationStatus.UNAVAILABLE,
                latency_ms=latency,
                last_success=self._last_successful_checks.get(IntegrationType.NOTIFICATION_SERVICE),
                error_message=str(e)
            )

# Convenience functions
async def check_integration_health() -> IntegrationHealthSummary:
    """Check health of all external integrations."""
    monitor = IntegrationHealthMonitor()
    return await monitor.check_all_integrations()

async def check_specific_integration(
    integration_type: IntegrationType
) -> IntegrationHealthCheck:
    """Check health of a specific integration."""
    monitor = IntegrationHealthMonitor()
    
    if integration_type == IntegrationType.MOSS:
        return await monitor._check_moss_integration()
    elif integration_type == IntegrationType.CRISIS_RESPONSE:
        return await monitor._check_crisis_response_integration()
    elif integration_type == IntegrationType.AUTH_SERVICE:
        return await monitor._check_auth_service_integration()
    elif integration_type == IntegrationType.NOTIFICATION_SERVICE:
        return await monitor._check_notification_service_integration()
    else:
        raise ValueError(f"Unknown integration type: {integration_type}")
