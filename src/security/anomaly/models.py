"""
Anomaly Detection Models

This module defines the data models for anomaly detection events.
"""

import uuid
from enum import Enum
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from pydantic import BaseModel, Field


class AnomalyType(str, Enum):
    """Types of anomalies that can be detected."""
    UNUSUAL_ACCESS_TIME = "unusual_access_time"
    UNUSUAL_ACCESS_VOLUME = "unusual_access_volume"
    UNUSUAL_ACCESS_PATTERN = "unusual_access_pattern"
    UNUSUAL_USER_BEHAVIOR = "unusual_user_behavior"
    UNUSUAL_DATA_ACCESS = "unusual_data_access"
    UNUSUAL_IP_ADDRESS = "unusual_ip_address"
    SUSPICIOUS_EXPORT_ACTIVITY = "suspicious_export_activity"
    MULTIPLE_FAILED_AUTHENTICATIONS = "multiple_failed_authentications"
    UNUSUAL_RECORD_MODIFICATIONS = "unusual_record_modifications"
    CREDENTIAL_SHARING = "credential_sharing"
    DATA_EXFILTRATION_ATTEMPT = "data_exfiltration_attempt"


class AnomalySeverity(str, Enum):
    """Severity levels for anomaly events."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyEvent(BaseModel):
    """Model representing a specific anomaly observation."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for this event")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the event occurred")
    event_type: AnomalyType = Field(..., description="Type of anomaly observed")
    user_id: Optional[str] = Field(None, description="User associated with this event")
    system_component: str = Field(..., description="System component where anomaly was detected")
    severity: AnomalySeverity = Field(..., description="Severity of the anomaly")
    confidence_score: float = Field(..., description="Confidence in the anomaly detection (0-1)")
    description: str = Field(..., description="Human-readable description of the anomaly")
    raw_data: Dict[str, Any] = Field(default_factory=dict, description="Raw data associated with this event")
    related_events: List[str] = Field(default_factory=list, description="IDs of related anomaly events")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class Anomaly(BaseModel):
    """
    Model representing an aggregated anomaly with related events.
    
    An anomaly may consist of multiple related events that together
    indicate a potential security issue or HIPAA compliance violation.
    """
    anomaly_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for this anomaly")
    first_detected: datetime = Field(..., description="When first event was detected")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="When last updated")
    anomaly_type: AnomalyType = Field(..., description="Primary type of anomaly")
    severity: AnomalySeverity = Field(..., description="Overall severity")
    status: str = Field("new", description="Status of investigation")
    confidence_score: float = Field(..., description="Overall confidence score (0-1)")
    affected_users: List[str] = Field(default_factory=list, description="Users associated with this anomaly")
    events: List[AnomalyEvent] = Field(default_factory=list, description="Events comprising this anomaly")
    summary: str = Field(..., description="Summary description")
    
    # Investigation and resolution fields
    assigned_to: Optional[str] = Field(None, description="Person assigned to investigate")
    resolution: Optional[str] = Field(None, description="Resolution details")
    resolved_at: Optional[datetime] = Field(None, description="When resolved")
    actions_taken: List[str] = Field(default_factory=list, description="Actions taken to address")
    risk_assessment: Dict[str, Any] = Field(default_factory=dict, description="Risk assessment details")


class AnomalyRule(BaseModel):
    """
    Rule for detecting anomalies in system behavior.
    
    These rules define conditions that indicate potential security issues.
    """
    rule_id: str = Field(..., description="Unique identifier for this rule")
    name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Detailed rule description")
    enabled: bool = Field(True, description="Whether this rule is active")
    anomaly_type: AnomalyType = Field(..., description="Type of anomaly this detects")
    default_severity: AnomalySeverity = Field(..., description="Default severity if detected")
    
    # Rule conditions
    conditions: Dict[str, Any] = Field(..., description="Conditions that trigger this rule")
    min_confidence: float = Field(0.7, description="Minimum confidence to trigger detection")
    cooldown_minutes: int = Field(60, description="Minimum minutes between repeat detections")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags for categorizing")
    author: Optional[str] = Field(None, description="Author of this rule")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When rule was created")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="When rule was last updated")
    version: str = Field("1.0.0", description="Rule version")
