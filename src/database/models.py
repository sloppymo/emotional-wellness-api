"""
Database models for the Emotional Wellness API.
HIPAA-compliant models with strict access controls.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, 
    Integer, String, Text, JSON, LargeBinary
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """User model for authentication and identification."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(255), nullable=False, unique=True)
    email = Column(String(255), unique=True)
    full_name = Column(String(255))
    provider_id = Column(String(255))
    password_hash = Column(String(255))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    last_login = Column(DateTime(timezone=True))
    disabled = Column(Boolean, nullable=False, default=False)

    # Relationships
    roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    consent_records = relationship("ConsentRecord", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    emotional_states = relationship("EmotionalState", back_populates="user")
    encrypted_contents = relationship("EncryptedContent", back_populates="user")
    safety_assessments = relationship("SafetyAssessment", back_populates="user")
    intervention_records = relationship("InterventionRecord", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.username}>"


class UserRole(Base):
    """User roles for access control."""
    __tablename__ = "user_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="roles")

    def __repr__(self):
        return f"<UserRole {self.role} for {self.user_id}>"


class ConsentRecord(Base):
    """HIPAA-compliant consent records."""
    __tablename__ = "consent_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    consent_version = Column(String(50), nullable=False)
    data_usage_approved = Column(Boolean, nullable=False)
    crisis_protocol_approved = Column(Boolean, nullable=False)
    data_retention_period = Column(Integer, nullable=False)
    ip_address_hash = Column(String(255))
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    revocable = Column(Boolean, nullable=False, default=True)
    active = Column(Boolean, nullable=False, default=True)

    # Relationships
    user = relationship("User", back_populates="consent_records")

    def __repr__(self):
        return f"<ConsentRecord {self.id} for {self.user_id}>"


class Session(Base):
    """User interaction sessions."""
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    last_active = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    status = Column(String(50), nullable=False, default="active")
    metadata = Column(JSON)

    # Relationships
    user = relationship("User", back_populates="sessions")
    emotional_states = relationship("EmotionalState", back_populates="session")
    symbolic_mappings = relationship("SymbolicMapping", back_populates="session", cascade="all, delete-orphan")
    encrypted_contents = relationship("EncryptedContent", back_populates="session")
    safety_assessments = relationship("SafetyAssessment", back_populates="session")
    intervention_records = relationship("InterventionRecord", back_populates="session")

    def __repr__(self):
        return f"<Session {self.id} for {self.user_id}>"


class SymbolicMapping(Base):
    """CANOPY symbolic metaphor mappings."""
    __tablename__ = "symbolic_mappings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    primary_symbol = Column(String(255), nullable=False)
    alternative_symbols = Column(JSON)
    archetype = Column(String(255))
    valence = Column(Float)
    arousal = Column(Float)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    session = relationship("Session", back_populates="symbolic_mappings")

    def __repr__(self):
        return f"<SymbolicMapping {self.primary_symbol} for {self.session_id}>"


class EncryptedContent(Base):
    """Encrypted PHI storage with AES-256."""
    __tablename__ = "encrypted_content"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"))
    content_type = Column(String(50), nullable=False)
    encrypted_data = Column(LargeBinary, nullable=False)
    iv = Column(String(255), nullable=False)
    hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="encrypted_contents")
    session = relationship("Session", back_populates="encrypted_contents")

    def __repr__(self):
        return f"<EncryptedContent {self.content_type} for {self.user_id}>"


class SafetyAssessment(Base):
    """MOSS safety assessment records."""
    __tablename__ = "safety_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"))
    level = Column(Integer, nullable=False)
    risk_score = Column(Float, nullable=False)
    triggers = Column(JSON)
    recommended_actions = Column(JSON)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="safety_assessments")
    session = relationship("Session", back_populates="safety_assessments")
    intervention_records = relationship("InterventionRecord", back_populates="safety_assessment")

    def __repr__(self):
        return f"<SafetyAssessment level={self.level} for {self.user_id}>"


class InterventionRecord(Base):
    """VELURIA intervention protocol records."""
    __tablename__ = "intervention_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"))
    safety_assessment_id = Column(UUID(as_uuid=True), ForeignKey("safety_assessments.id"))
    level = Column(Integer, nullable=False)
    actions_taken = Column(JSON)
    protocol_state = Column(String(50), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime(timezone=True))
    outcome = Column(String(50))
    notes = Column(Text)

    # Relationships
    user = relationship("User", back_populates="intervention_records")
    session = relationship("Session", back_populates="intervention_records")
    safety_assessment = relationship("SafetyAssessment", back_populates="intervention_records")

    def __repr__(self):
        return f"<InterventionRecord level={self.level} for {self.user_id}>"


class EmotionalState(Base):
    """User emotional state records."""
    __tablename__ = "emotional_states"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"))
    valence = Column(Float)
    arousal = Column(Float)
    primary_symbol = Column(String(255), nullable=False)
    alternative_symbols = Column(JSON)
    archetype = Column(String(255))
    drift_index = Column(Float)
    safety_level = Column(Integer, nullable=False)
    input_text_hash = Column(String(255), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    metadata = Column(JSON)

    # Relationships
    user = relationship("User", back_populates="emotional_states")
    session = relationship("Session", back_populates="emotional_states")

    def __repr__(self):
        return f"<EmotionalState {self.primary_symbol} for {self.user_id}>"


class AuditLog(Base):
    """HIPAA-compliant audit logs."""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    action = Column(String(255), nullable=False)
    resource_type = Column(String(255), nullable=False)
    resource_id = Column(UUID(as_uuid=True))
    ip_address = Column(String(255))
    user_agent = Column(Text)
    details = Column(JSON)

    def __repr__(self):
        return f"<AuditLog {self.action} on {self.resource_type}>"
