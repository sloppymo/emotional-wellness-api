"""
Clinical service layer for the Emotional Wellness API.

Provides business logic for clinical alert management, intervention tracking,
and patient risk assessment.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple

from redis.asyncio import Redis
from pydantic import ValidationError

from structured_logging import get_logger
from observability import get_telemetry_manager, ComponentName, record_span
from clinical.models import (
    PatientAlert, ClinicalIntervention, PatientRiskProfile,
    ClinicalDashboardSummary, ResourceReferral, 
    InterventionType, InterventionStatus, ClinicalPriority
)
from symbolic.moss.crisis_classifier import CrisisSeverity, RiskDomain


# Configure logger
logger = get_logger(__name__)


class ClinicalService:
    """
    Clinical service for managing patient alerts, interventions, and referrals.
    
    This service is used by the clinician portal and provides the backend 
    functionality for clinical oversight of patient wellness.
    """
    
    def __init__(self, redis: Optional[Redis] = None):
        """
        Initialize clinical service.
        
        Args:
            redis: Redis client for data persistence (optional)
        """
        self.redis = redis
        self._logger = get_logger(f"{__name__}.ClinicalService")
    
    @record_span("clinical.create_alert", ComponentName.SECURITY)
    async def create_alert(self, patient_id: str, 
                         severity: CrisisSeverity, 
                         description: str,
                         risk_domains: List[RiskDomain] = None) -> PatientAlert:
        """
        Create a new patient alert for clinical attention.
        
        Args:
            patient_id: Identifier of the patient
            severity: Severity level of the alert
            description: Description of the alert
            risk_domains: Risk domains identified
            
        Returns:
            Created patient alert
        """
        # Map severity to clinical priority
        priority_map = {
            CrisisSeverity.NONE: ClinicalPriority.LOW,
            CrisisSeverity.MILD: ClinicalPriority.LOW,
            CrisisSeverity.MODERATE: ClinicalPriority.MEDIUM,
            CrisisSeverity.SEVERE: ClinicalPriority.HIGH,
            CrisisSeverity.EXTREME: ClinicalPriority.URGENT
        }
        
        # Create alert
        alert_id = str(uuid.uuid4())
        alert = PatientAlert(
            id=alert_id,
            patient_id=patient_id,
            timestamp=datetime.utcnow(),
            severity=severity,
            description=description,
            risk_domains=risk_domains or [],
            priority=priority_map.get(severity, ClinicalPriority.MEDIUM)
        )
        
        # Persist alert if Redis is available
        if self.redis:
            key = f"clinical:alert:{alert_id}"
            await self.redis.set(key, alert.model_dump_json())
            
            # Add to patient's alert list
            patient_alerts_key = f"clinical:patient:{patient_id}:alerts"
            await self.redis.lpush(patient_alerts_key, alert_id)
            
            # Add to active alerts list
            active_alerts_key = "clinical:alerts:active"
            await self.redis.lpush(active_alerts_key, alert_id)
            
            # Set expiration for HIPAA compliance (default 7 years)
            await self.redis.expire(key, 220752000)  # 7 years in seconds
        
        self._logger.info(f"Created alert {alert_id} for patient {patient_id} with {severity} severity")
        return alert
    
    @record_span("clinical.acknowledge_alert", ComponentName.SECURITY)
    async def acknowledge_alert(self, alert_id: str, clinician_id: str) -> PatientAlert:
        """
        Acknowledge a patient alert, marking it as seen by a clinician.
        
        Args:
            alert_id: Identifier of the alert
            clinician_id: Identifier of the clinician
            
        Returns:
            Updated patient alert
            
        Raises:
            ValueError: If alert is not found
        """
        alert = await self.get_alert(alert_id)
        if not alert:
            raise ValueError(f"Alert {alert_id} not found")
        
        # Update alert
        alert.acknowledged = True
        alert.acknowledged_by = clinician_id
        alert.acknowledged_at = datetime.utcnow()
        
        # Persist updated alert
        if self.redis:
            key = f"clinical:alert:{alert_id}"
            await self.redis.set(key, alert.model_dump_json())
        
        self._logger.info(f"Alert {alert_id} acknowledged by clinician {clinician_id}")
        return alert
    
    @record_span("clinical.get_alert", ComponentName.SECURITY)
    async def get_alert(self, alert_id: str) -> Optional[PatientAlert]:
        """
        Get a patient alert by ID.
        
        Args:
            alert_id: Identifier of the alert
            
        Returns:
            Patient alert if found, None otherwise
        """
        if not self.redis:
            self._logger.warning("Redis not available, cannot retrieve alert")
            return None
            
        key = f"clinical:alert:{alert_id}"
        alert_json = await self.redis.get(key)
        
        if not alert_json:
            return None
            
        try:
            return PatientAlert.model_validate_json(alert_json)
        except ValidationError as e:
            self._logger.error(f"Failed to parse alert data: {e}")
            return None
    
    @record_span("clinical.get_patient_alerts", ComponentName.SECURITY)
    async def get_patient_alerts(self, patient_id: str, 
                               limit: int = 10, 
                               include_acknowledged: bool = False) -> List[PatientAlert]:
        """
        Get alerts for a specific patient.
        
        Args:
            patient_id: Identifier of the patient
            limit: Maximum number of alerts to return
            include_acknowledged: Whether to include acknowledged alerts
            
        Returns:
            List of patient alerts
        """
        if not self.redis:
            self._logger.warning("Redis not available, cannot retrieve alerts")
            return []
            
        # Get alert IDs for patient
        patient_alerts_key = f"clinical:patient:{patient_id}:alerts"
        alert_ids = await self.redis.lrange(patient_alerts_key, 0, limit - 1)
        
        alerts = []
        for alert_id in alert_ids:
            if isinstance(alert_id, bytes):
                alert_id = alert_id.decode('utf-8')
                
            alert = await self.get_alert(alert_id)
            if alert and (include_acknowledged or not alert.acknowledged):
                alerts.append(alert)
                
        return alerts
    
    @record_span("clinical.create_intervention", ComponentName.SECURITY)
    async def create_intervention(self, 
                                patient_id: str, 
                                intervention_type: InterventionType,
                                created_by: str,
                                priority: ClinicalPriority,
                                alert_id: Optional[str] = None,
                                notes: str = "",
                                scheduled_for: Optional[datetime] = None) -> ClinicalIntervention:
        """
        Create a new clinical intervention.
        
        Args:
            patient_id: Identifier of the patient
            intervention_type: Type of intervention
            created_by: Identifier of the clinician creating the intervention
            priority: Clinical priority level
            alert_id: Identifier of the alert that triggered intervention, if any
            notes: Clinical notes
            scheduled_for: When intervention is scheduled
            
        Returns:
            Created clinical intervention
        """
        # Create intervention
        intervention_id = str(uuid.uuid4())
        intervention = ClinicalIntervention(
            id=intervention_id,
            patient_id=patient_id,
            alert_id=alert_id,
            created_by=created_by,
            intervention_type=intervention_type,
            priority=priority,
            notes=notes,
            scheduled_for=scheduled_for
        )
        
        # Persist intervention if Redis is available
        if self.redis:
            key = f"clinical:intervention:{intervention_id}"
            await self.redis.set(key, intervention.model_dump_json())
            
            # Add to patient's intervention list
            patient_key = f"clinical:patient:{patient_id}:interventions"
            await self.redis.lpush(patient_key, intervention_id)
            
            # Add to pending interventions list
            pending_key = "clinical:interventions:pending"
            await self.redis.lpush(pending_key, intervention_id)
            
            # Set expiration for HIPAA compliance (default 7 years)
            await self.redis.expire(key, 220752000)  # 7 years in seconds
        
        self._logger.info(
            f"Created {intervention_type} intervention {intervention_id} for patient {patient_id}"
        )
        
        # If linked to alert, log the connection
        if alert_id:
            self._logger.info(f"Intervention {intervention_id} linked to alert {alert_id}")
        
        return intervention
    
    @record_span("clinical.update_intervention", ComponentName.SECURITY)
    async def update_intervention_status(
        self, intervention_id: str, status: InterventionStatus, notes: Optional[str] = None
    ) -> ClinicalIntervention:
        """
        Update the status of a clinical intervention.
        
        Args:
            intervention_id: Identifier of the intervention
            status: New status
            notes: Additional notes
            
        Returns:
            Updated clinical intervention
            
        Raises:
            ValueError: If intervention is not found
        """
        intervention = await self.get_intervention(intervention_id)
        if not intervention:
            raise ValueError(f"Intervention {intervention_id} not found")
        
        # Update intervention
        intervention.status = status
        
        if notes:
            intervention.notes += f"\n[{datetime.utcnow().isoformat()}] {notes}"
        
        if status == InterventionStatus.COMPLETED:
            intervention.completed_at = datetime.utcnow()
        
        # Persist updated intervention
        if self.redis:
            key = f"clinical:intervention:{intervention_id}"
            await self.redis.set(key, intervention.model_dump_json())
            
            # Update status lists
            if status == InterventionStatus.COMPLETED:
                # Remove from pending list
                pending_key = "clinical:interventions:pending"
                await self.redis.lrem(pending_key, 0, intervention_id)
                
                # Store completed intervention for tracking
                # Use a configurable key prefix instead of hardcoded value
                completed_key = f"clinical:interventions:completed:{intervention_id}"
                await self.redis.lpush(completed_key, intervention_id)
        
        self._logger.info(f"Updated intervention {intervention_id} status to {status}")
        return intervention
    
    @record_span("clinical.get_intervention", ComponentName.SECURITY)
    async def get_intervention(self, intervention_id: str) -> Optional[ClinicalIntervention]:
        """
        Get a clinical intervention by ID.
        
        Args:
            intervention_id: Identifier of the intervention
            
        Returns:
            Clinical intervention if found, None otherwise
        """
        if not self.redis:
            self._logger.warning("Redis not available, cannot retrieve intervention")
            return None
            
        key = f"clinical:intervention:{intervention_id}"
        intervention_json = await self.redis.get(key)
        
        if not intervention_json:
            return None
            
        try:
            return ClinicalIntervention.model_validate_json(intervention_json)
        except ValidationError as e:
            self._logger.error(f"Failed to parse intervention data: {e}")
            return None
    
    @record_span("clinical.get_dashboard_summary", ComponentName.SECURITY)
    async def get_dashboard_summary(self) -> ClinicalDashboardSummary:
        """
        Get a summary of clinical data for the dashboard.
        
        Returns:
            Clinical dashboard summary
        """
        if not self.redis:
            self._logger.warning("Redis not available, returning placeholder dashboard summary")
            # Return placeholder data
            return ClinicalDashboardSummary(
                total_patients=0,
                active_alerts=0,
                pending_interventions=0,
                high_risk_patients=0,
                alerts_by_priority={},
                interventions_by_status={},
                recent_alerts=[]
            )
        
        # Get counts from Redis
        total_patients = await self.redis.scard("clinical:patients") or 0
        active_alerts = await self.redis.llen("clinical:alerts:active") or 0
        pending_interventions = await self.redis.llen("clinical:interventions:pending") or 0
        
        # Get recent alerts
        alert_ids = await self.redis.lrange("clinical:alerts:active", 0, 9)
        recent_alerts = []
        
        for alert_id in alert_ids:
            if isinstance(alert_id, bytes):
                alert_id = alert_id.decode('utf-8')
                
            alert = await self.get_alert(alert_id)
            if alert:
                recent_alerts.append(alert)
        
        # Count high risk patients
        high_risk_key = "clinical:patients:high_risk"
        high_risk_patients = await self.redis.scard(high_risk_key) or 0
        
        # Count alerts by priority
        alerts_by_priority = {
            priority.value: 0 for priority in ClinicalPriority
        }
        
        for alert in recent_alerts:
            if alert.priority.value in alerts_by_priority:
                alerts_by_priority[alert.priority.value] += 1
        
        # Count interventions by status
        interventions_by_status = {
            status.value: 0 for status in InterventionStatus
        }
        
        # Get pending intervention IDs
        intervention_ids = await self.redis.lrange("clinical:interventions:pending", 0, -1)
        
        for intervention_id in intervention_ids:
            if isinstance(intervention_id, bytes):
                intervention_id = intervention_id.decode('utf-8')
                
            intervention = await self.get_intervention(intervention_id)
            if intervention:
                if intervention.status.value in interventions_by_status:
                    interventions_by_status[intervention.status.value] += 1
        
        return ClinicalDashboardSummary(
            total_patients=total_patients,
            active_alerts=active_alerts,
            pending_interventions=pending_interventions,
            high_risk_patients=high_risk_patients,
            alerts_by_priority=alerts_by_priority,
            interventions_by_status=interventions_by_status,
            recent_alerts=recent_alerts
        )


# Singleton instance
_clinical_service: Optional[ClinicalService] = None


def get_clinical_service(redis: Optional[Redis] = None) -> ClinicalService:
    """Get the global clinical service instance."""
    global _clinical_service
    if _clinical_service is None:
        _clinical_service = ClinicalService(redis=redis)
    return _clinical_service
