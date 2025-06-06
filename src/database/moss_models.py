"""
MOSS-specific database models for crisis detection and audit logging.

These models extend the core database structure to support:
- Comprehensive HIPAA-compliant audit logging
- Adaptive threshold management
- Crisis assessment caching
- Prompt template management
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, 
    Integer, String, Text, JSON, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from .models import Base, User, Session

# MOSS-specific enums
class AuditEventType(str, Enum):
    """MOSS audit event types."""
    ASSESSMENT_STARTED = "assessment_started"
    ASSESSMENT_COMPLETED = "assessment_completed"
    CRISIS_DETECTED = "crisis_detected"
    INTERVENTION_TRIGGERED = "intervention_triggered"
    ESCALATION_INITIATED = "escalation_initiated"
    THRESHOLD_ADJUSTED = "threshold_adjusted"
    PROMPT_GENERATED = "prompt_generated"
    USER_ACCESS = "user_access"
    SYSTEM_ERROR = "system_error"
    COMPLIANCE_CHECK = "compliance_check"
    DATA_RETENTION = "data_retention"

class AuditSeverity(str, Enum):
    """MOSS audit severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class CrisisSeverity(str, Enum):
    """MOSS crisis severity levels."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    IMMINENT = "imminent"

class RiskDomain(str, Enum):
    """MOSS risk domains."""
    SUICIDE = "suicide"
    SELF_HARM = "self_harm"
    VIOLENCE = "violence"
    SUBSTANCE_ABUSE = "substance_abuse"
    TRAUMA = "trauma"
    EATING_DISORDER = "eating_disorder"
    NEGLECT = "neglect"
    PSYCHOSIS = "psychosis"


class MOSSAuditEvent(Base):
    """MOSS comprehensive audit events for HIPAA compliance."""
    __tablename__ = "moss_audit_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(String(255), nullable=False, unique=True, index=True)
    event_type = Column(SQLEnum(AuditEventType), nullable=False, index=True)
    severity = Column(SQLEnum(AuditSeverity), nullable=False, index=True)
    
    # User context (hashed for privacy)
    user_id_hash = Column(String(64), index=True)  # SHA-256 hash of user ID
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="SET NULL"))
    
    # Event details
    source_component = Column(String(255), nullable=False)
    action_performed = Column(String(255), nullable=False)
    outcome = Column(String(255), nullable=False)
    
    # Crisis-specific data
    assessment_id = Column(String(255), index=True)
    crisis_severity = Column(SQLEnum(CrisisSeverity))
    escalation_required = Column(Boolean, default=False)
    intervention_triggered = Column(Boolean, default=False)
    
    # Metadata and compliance
    event_data = Column(JSON)  # Additional structured event data
    compliance_tags = Column(JSON)  # HIPAA, GDPR, etc.
    phi_category = Column(String(50))  # Type of PHI involved
    retention_until = Column(DateTime(timezone=True))  # Data retention
    
    # Timing and performance
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    processing_time_ms = Column(Float)
    
    # System context
    server_instance = Column(String(255))
    request_id = Column(String(255))
    
    # Relationships
    session = relationship("Session")
    
    def __repr__(self):
        return f"<MOSSAuditEvent {self.event_type} severity={self.severity} at {self.timestamp}>"


class MOSSCrisisAssessment(Base):
    """MOSS crisis assessment results for caching and analysis."""
    __tablename__ = "moss_crisis_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id = Column(String(255), nullable=False, unique=True, index=True)
    
    # User context (hashed for privacy)
    user_id_hash = Column(String(64), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="SET NULL"))
    
    # Assessment results
    severity = Column(SQLEnum(CrisisSeverity), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    urgency_score = Column(Float, nullable=False)
    
    # Risk analysis
    risk_domains = Column(JSON, nullable=False)  # Dict of domain -> score
    primary_concerns = Column(JSON, nullable=False)  # List of main concerns
    protective_factors = Column(JSON, default=list)  # List of protective factors
    
    # Decision factors
    escalation_required = Column(Boolean, nullable=False, default=False)
    recommendations = Column(JSON, default=list)  # List of recommendations
    
    # Input data (sanitized)
    input_text_hash = Column(String(64), nullable=False)  # SHA-256 of input text
    context_data = Column(JSON)  # Non-PHI context information
    
    # Metadata
    processing_metadata = Column(JSON)  # Processing details
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime(timezone=True))  # Cache expiration
    
    # Relationships
    session = relationship("Session")
    threshold_adjustments = relationship("MOSSThresholdAdjustment", back_populates="assessment")
    
    def __repr__(self):
        return f"<MOSSCrisisAssessment {self.assessment_id} severity={self.severity} confidence={self.confidence}>"


class MOSSThresholdConfiguration(Base):
    """MOSS adaptive threshold configurations."""
    __tablename__ = "moss_threshold_configurations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    config_id = Column(String(255), nullable=False, unique=True, index=True)
    
    # Configuration metadata
    threshold_type = Column(String(50), nullable=False)  # "static", "adaptive", "contextual"
    version = Column(String(50), nullable=False)
    description = Column(Text)
    
    # Threshold data
    domain_thresholds = Column(JSON, nullable=False)  # Risk domain thresholds
    contextual_modifiers = Column(JSON, default=dict)  # Context-based adjustments
    population_groups = Column(JSON, default=dict)  # Population-specific thresholds
    
    # Validation and performance
    validation_metrics = Column(JSON)  # Accuracy, precision, recall, etc.
    performance_stats = Column(JSON)  # Usage statistics
    
    # Lifecycle
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    active = Column(Boolean, nullable=False, default=True)
    
    # Clinical validation
    clinical_approved = Column(Boolean, default=False)
    approved_by = Column(String(255))  # Clinician who approved
    approved_at = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<MOSSThresholdConfiguration {self.config_id} type={self.threshold_type}>"


class MOSSThresholdAdjustment(Base):
    """MOSS individual threshold adjustments for adaptive learning."""
    __tablename__ = "moss_threshold_adjustments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    adjustment_id = Column(String(255), nullable=False, unique=True, index=True)
    
    # User context (hashed for privacy)
    user_id_hash = Column(String(64), index=True)
    
    # Adjustment details
    domain = Column(SQLEnum(RiskDomain), nullable=False)
    severity_level = Column(String(50), nullable=False)
    original_threshold = Column(Float, nullable=False)
    adjusted_threshold = Column(Float, nullable=False)
    adjustment_factor = Column(Float, nullable=False)
    
    # Justification
    reason = Column(Text, nullable=False)
    source_assessment_id = Column(UUID(as_uuid=True), ForeignKey("moss_crisis_assessments.id"))
    actual_outcome = Column(String(50))  # What actually happened
    
    # Validation
    validation_score = Column(Float)  # How well this adjustment performed
    confidence_interval = Column(JSON)  # Statistical confidence bounds
    
    # Lifecycle
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime(timezone=True))  # When this adjustment expires
    active = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    assessment = relationship("MOSSCrisisAssessment", back_populates="threshold_adjustments")
    
    def __repr__(self):
        return f"<MOSSThresholdAdjustment {self.domain} {self.original_threshold}->{self.adjusted_threshold}>"


class MOSSPromptTemplate(Base):
    """MOSS intervention prompt templates."""
    __tablename__ = "moss_prompt_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(String(255), nullable=False, unique=True, index=True)
    
    # Template metadata
    category = Column(String(100), nullable=False, index=True)  # "crisis", "safety_planning", etc.
    severity_level = Column(SQLEnum(CrisisSeverity), nullable=False, index=True)
    tone = Column(String(50), nullable=False)  # "empathetic", "direct", "supportive"
    channel = Column(String(50), nullable=False)  # "chat", "voice", "text", "email"
    
    # Template content
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    variables = Column(JSON, default=list)  # List of template variables
    
    # Usage and validation
    use_cases = Column(JSON, default=list)  # Appropriate use cases
    contraindications = Column(JSON, default=list)  # When NOT to use
    clinical_reviewed = Column(Boolean, nullable=False, default=False)
    effectiveness_score = Column(Float)  # User feedback score
    usage_count = Column(Integer, default=0)
    
    # Lifecycle
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    active = Column(Boolean, nullable=False, default=True)
    
    # Clinical approval
    approved_by = Column(String(255))  # Clinician who approved
    approved_at = Column(DateTime(timezone=True))
    
    # Relationships
    generated_prompts = relationship("MOSSGeneratedPrompt", back_populates="template")
    
    def __repr__(self):
        return f"<MOSSPromptTemplate {self.template_id} category={self.category} severity={self.severity_level}>"


class MOSSGeneratedPrompt(Base):
    """MOSS generated prompt instances for tracking and analytics."""
    __tablename__ = "moss_generated_prompts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prompt_id = Column(String(255), nullable=False, unique=True, index=True)
    
    # Source template
    template_id = Column(UUID(as_uuid=True), ForeignKey("moss_prompt_templates.id", ondelete="CASCADE"), nullable=False)
    
    # User context (hashed for privacy)
    user_id_hash = Column(String(64), index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="SET NULL"))
    assessment_id = Column(String(255), index=True)  # Related crisis assessment
    
    # Generated content
    generated_content = Column(Text, nullable=False)
    personalization_applied = Column(Boolean, default=False)
    variables_used = Column(JSON, default=dict)  # Variables and their values
    
    # Context and delivery
    severity_level = Column(SQLEnum(CrisisSeverity), nullable=False)
    risk_domains = Column(JSON, default=list)  # Related risk domains
    channel = Column(String(50), nullable=False)
    
    # Safety and validation
    safety_validated = Column(Boolean, nullable=False, default=False)
    harmful_content_detected = Column(Boolean, default=False)
    
    # Usage tracking
    delivered_at = Column(DateTime(timezone=True))
    user_response = Column(String(50))  # "helpful", "not_helpful", "harmful"
    effectiveness_rating = Column(Integer)  # 1-5 scale
    
    # Lifecycle
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime(timezone=True))  # Content expiration
    
    # Relationships
    template = relationship("MOSSPromptTemplate", back_populates="generated_prompts")
    session = relationship("Session")
    
    def __repr__(self):
        return f"<MOSSGeneratedPrompt {self.prompt_id} template={self.template_id} severity={self.severity_level}>"


class MOSSSystemMetrics(Base):
    """MOSS system performance and health metrics."""
    __tablename__ = "moss_system_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Time bucket for aggregation
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    time_bucket = Column(String(50), nullable=False, index=True)  # "minute", "hour", "day"
    
    # Performance metrics
    total_assessments = Column(Integer, default=0)
    avg_processing_time_ms = Column(Float, default=0.0)
    cache_hit_rate = Column(Float, default=0.0)
    error_rate = Column(Float, default=0.0)
    
    # Crisis detection metrics
    crisis_detection_rate = Column(Float, default=0.0)
    false_positive_rate = Column(Float, default=0.0)
    false_negative_rate = Column(Float, default=0.0)
    escalation_rate = Column(Float, default=0.0)
    
    # Intervention metrics
    prompt_generation_rate = Column(Float, default=0.0)
    prompt_effectiveness_avg = Column(Float, default=0.0)
    user_satisfaction_avg = Column(Float, default=0.0)
    
    # System health
    threshold_accuracy = Column(Float, default=0.0)
    model_confidence_avg = Column(Float, default=0.0)
    audit_compliance_rate = Column(Float, default=0.0)
    
    # Resource utilization
    memory_usage_mb = Column(Float, default=0.0)
    cpu_usage_percent = Column(Float, default=0.0)
    database_connections = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<MOSSSystemMetrics {self.time_bucket} at {self.timestamp}>" 