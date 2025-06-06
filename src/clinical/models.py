"""
Clinical integration models for the Emotional Wellness API.

Defines data models for clinician portal, patient management, and intervention tracking.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, EmailStr, ConfigDict

from symbolic.moss.crisis_classifier import CrisisSeverity, RiskDomain


class InterventionStatus(str, Enum):
    """Status of a clinical intervention."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELED = "canceled"
    REFERRED = "referred"


class InterventionType(str, Enum):
    """Type of clinical intervention."""
    ASSESSMENT = "assessment"
    SAFETY_PLAN = "safety_plan"
    RESOURCES = "resources"
    REFERRAL = "referral"
    FOLLOW_UP = "follow_up"
    URGENT_CARE = "urgent_care"
    EMERGENCY_SERVICES = "emergency_services"


class ClinicalPriority(str, Enum):
    """Clinical priority levels for interventions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    EMERGENCY = "emergency"


class PatientAlert(BaseModel):
    """Alert related to a patient requiring clinician attention."""
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    id: str = Field(..., description="Unique identifier for the alert")
    patient_id: str = Field(..., description="Patient identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Alert creation time")
    severity: CrisisSeverity = Field(..., description="Alert severity level")
    description: str = Field(..., description="Alert description")
    risk_domains: List[RiskDomain] = Field(default_factory=list, description="Risk domains identified")
    priority: ClinicalPriority = Field(..., description="Clinical priority level")
    acknowledged: bool = Field(False, description="Whether alert has been acknowledged by clinician")
    acknowledged_by: Optional[str] = Field(None, description="ID of clinician who acknowledged alert")
    acknowledged_at: Optional[datetime] = Field(None, description="Timestamp of acknowledgment")


class ClinicalIntervention(BaseModel):
    """Clinical intervention created in response to a crisis alert."""
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    id: str = Field(..., description="Unique identifier for the intervention")
    patient_id: str = Field(..., description="Patient identifier")
    alert_id: Optional[str] = Field(None, description="Alert that triggered intervention, if any")
    created_by: str = Field(..., description="ID of clinician who created intervention")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    intervention_type: InterventionType = Field(..., description="Type of intervention")
    status: InterventionStatus = Field(default=InterventionStatus.PENDING, description="Current status")
    priority: ClinicalPriority = Field(..., description="Clinical priority level")
    notes: str = Field("", description="Clinical notes")
    scheduled_for: Optional[datetime] = Field(None, description="When intervention is scheduled")
    completed_at: Optional[datetime] = Field(None, description="When intervention was completed")
    resources_provided: List[str] = Field(default_factory=list, description="Resources provided to patient")
    follow_up_required: bool = Field(False, description="Whether follow-up is required")
    follow_up_by: Optional[datetime] = Field(None, description="When follow-up should occur")


class PatientRiskProfile(BaseModel):
    """Patient risk profile with historical crisis data and risk factors."""
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    patient_id: str = Field(..., description="Patient identifier")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last profile update")
    risk_level: CrisisSeverity = Field(default=CrisisSeverity.NONE, description="Current risk level")
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")
    protective_factors: List[str] = Field(default_factory=list, description="Identified protective factors")
    crisis_history: List[Dict[str, Any]] = Field(default_factory=list, description="Historical crisis events")
    safety_plan: Optional[Dict[str, Any]] = Field(None, description="Patient safety plan if available")
    clinical_notes: str = Field("", description="Clinical notes about risk")
    last_assessment: Optional[datetime] = Field(None, description="Last clinical assessment date")


class ClinicalDashboardSummary(BaseModel):
    """Summary of clinical data for the clinician dashboard."""
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    total_patients: int = Field(..., description="Total patients under care")
    active_alerts: int = Field(..., description="Number of active alerts requiring attention")
    pending_interventions: int = Field(..., description="Number of pending interventions")
    high_risk_patients: int = Field(..., description="Number of high-risk patients")
    alerts_by_priority: Dict[str, int] = Field(..., description="Alerts grouped by priority")
    interventions_by_status: Dict[str, int] = Field(..., description="Interventions grouped by status")
    recent_alerts: List[PatientAlert] = Field(..., description="Most recent alerts")


class ResourceReferral(BaseModel):
    """External resource referral for patient."""
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    id: str = Field(..., description="Unique identifier for referral")
    patient_id: str = Field(..., description="Patient identifier")
    provider_id: str = Field(..., description="Provider identifier")
    provider_name: str = Field(..., description="Provider name")
    service_type: str = Field(..., description="Type of service")
    reason: str = Field(..., description="Reason for referral")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    status: str = Field("pending", description="Referral status")
    scheduled_date: Optional[datetime] = Field(None, description="Scheduled appointment date")
    notes: str = Field("", description="Additional notes")
    contact_info: Dict[str, str] = Field(..., description="Provider contact information")
