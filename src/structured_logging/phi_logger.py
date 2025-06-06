"""
PHI Logger for HIPAA-Compliant Audit Logging

This module provides specialized logging for Protected Health Information (PHI)
with complete HIPAA compliance and integration with the MOSS audit system.
"""

import asyncio
import uuid
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Set
from enum import Enum
from functools import lru_cache

from pydantic import BaseModel, Field, ConfigDict

from .structured import get_logger, log_with_context
try:
    from symbolic.moss.audit_logging import (
        MOSSAuditLogger, 
        AuditEventType, 
        AuditSeverity,
        PHICategory, 
        ComplianceFramework
    )
    MOSS_AVAILABLE = True
except ImportError:
    MOSS_AVAILABLE = False
    
# Fallback classes if MOSS isn't available
if not MOSS_AVAILABLE:
    class PHICategory(str, Enum):
        """Categories of Protected Health Information."""
        DIRECT_IDENTIFIER = "direct_identifier"
        QUASI_IDENTIFIER = "quasi_identifier"
        SENSITIVE_HEALTH_DATA = "sensitive_health_data"
        BEHAVIORAL_DATA = "behavioral_data"
        NONE = "none"

    class AuditEventType(str, Enum):
        """Types of audit events."""
        USER_ACCESS = "user_access"
        SYSTEM_ACCESS = "system_access"
        DATA_EXPORT = "data_export"

    class AuditSeverity(str, Enum):
        """Severity levels for audit events."""
        INFO = "info"
        WARNING = "warning"
        ERROR = "error"
        CRITICAL = "critical"
    
    class ComplianceFramework(str, Enum):
        """Compliance frameworks"""
        HIPAA = "hipaa"
        GDPR = "gdpr"

logger = get_logger(__name__)

# Global instance for convenience
_phi_logger = None


class PHIAccessRecord(BaseModel):
    """Record of PHI access for HIPAA compliance."""
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    record_id: str = Field(default_factory=lambda: f"phi-{uuid.uuid4().hex}")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = Field(None, description="User whose PHI was accessed")
    user_id_hash: Optional[str] = Field(None, description="Hashed user identifier")
    action: str = Field(..., description="Action performed on PHI")
    system_component: str = Field(..., description="Component that accessed PHI")
    data_elements: List[str] = Field(default_factory=list, description="PHI elements accessed")
    request_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    session_id: Optional[str] = Field(None, description="Session identifier")
    access_purpose: str = Field(..., description="Purpose for accessing PHI")
    phi_category: PHICategory = Field(default=PHICategory.SENSITIVE_HEALTH_DATA)
    access_result: str = Field(default="success")
    compliance_tags: List[str] = Field(default_factory=lambda: ["hipaa"])
    additional_context: Dict[str, Any] = Field(default_factory=dict)


class PHILogger:
    """
    HIPAA-compliant logger for Protected Health Information access.
    
    Provides:
    - Structured PHI access logging
    - Integration with MOSS audit system when available
    - Fallback to standard logging when MOSS is unavailable
    - Compliance with HIPAA Security Rule requirements for audit controls
    """
    
    def __init__(self):
        """Initialize the PHI Logger."""
        self._logger = get_logger(f"{__name__}.PHILogger")
        
        # Try to connect to MOSS audit system
        self.moss_audit_logger = None
        if MOSS_AVAILABLE:
            try:
                self.moss_audit_logger = MOSSAuditLogger()
                self._logger.info("PHI Logger initialized with MOSS audit integration")
            except Exception as e:
                self._logger.warning(f"Failed to initialize MOSS audit integration: {e}")
        else:
            self._logger.info("PHI Logger initialized in standalone mode (MOSS not available)")
            
        # In-memory cache for recent access records (short-term only)
        self._recent_accesses = {}
    
    async def log_access(self, 
                         user_id: str, 
                         action: str, 
                         system_component: str = "unknown",
                         access_purpose: str = "wellness_processing",
                         data_elements: Optional[List[str]] = None,
                         session_id: Optional[str] = None,
                         additional_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Log PHI access for HIPAA compliance.
        
        Args:
            user_id: User whose PHI was accessed
            action: Action performed (e.g., "view", "process")
            system_component: System component performing access
            access_purpose: Business purpose for access
            data_elements: Specific PHI elements accessed
            session_id: Session identifier
            additional_context: Additional context information
            
        Returns:
            Record ID of the logged access
        """
        # Create PHI access record
        record = PHIAccessRecord(
            user_id=user_id,
            user_id_hash=self._hash_user_id(user_id) if user_id else None,
            action=action,
            system_component=system_component,
            data_elements=data_elements or ["emotional_data"],
            session_id=session_id,
            access_purpose=access_purpose,
            additional_context=additional_context or {}
        )
        
        # Log to MOSS audit system if available
        if self.moss_audit_logger:
            try:
                await self.moss_audit_logger.log_user_access(
                    user_id=user_id,
                    action=f"phi_{action}",
                    resource=f"phi:{';'.join(record.data_elements)}",
                    session_id=session_id,
                    outcome="success"
                )
            except Exception as e:
                self._logger.error(f"Failed to log to MOSS audit system: {e}")
                
        # Always log locally for redundancy
        log_with_context(
            self._logger,
            "INFO",
            f"PHI access: {action} for user {record.user_id_hash} by {system_component}",
            user_id=record.user_id_hash,
            session_id=session_id,
            event_type="phi_access",
            data={
                "record_id": record.record_id,
                "action": action,
                "phi_category": record.phi_category,
                "timestamp": record.timestamp.isoformat()
            }
        )
        
        # Cache recent access
        self._recent_accesses[record.record_id] = record
        
        # Return the record ID for reference
        return record.record_id
    
    def _hash_user_id(self, user_id: str) -> str:
        """Create secure hash of user ID for privacy."""
        if not user_id:
            return "anonymous"
        return hashlib.sha256(f"phi-user-{user_id}".encode()).hexdigest()
    
    async def get_access_history(self, 
                                user_id: Optional[str] = None, 
                                limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get PHI access history (from MOSS if available).
        
        Args:
            user_id: Filter by specific user
            limit: Maximum number of records to return
            
        Returns:
            List of access records
        """
        if self.moss_audit_logger:
            try:
                from symbolic.moss.audit_logging import AuditQuery
                query = AuditQuery(
                    user_id_hash=self._hash_user_id(user_id) if user_id else None,
                    event_types=[AuditEventType.USER_ACCESS],
                    limit=limit
                )
                return await self.moss_audit_logger.query_audit_logs(query)
            except Exception as e:
                self._logger.error(f"Failed to query MOSS audit logs: {e}")
        
        # Fallback to local cache
        result = []
        for record in self._recent_accesses.values():
            if user_id and record.user_id != user_id:
                continue
            result.append(record.model_dump())
            if len(result) >= limit:
                break
        
        return result


def get_phi_logger() -> PHILogger:
    """Get the global PHI Logger instance."""
    global _phi_logger
    if _phi_logger is None:
        _phi_logger = PHILogger()
    return _phi_logger


async def log_phi_access(user_id: str, 
                         action: str, 
                         system_component: str = "unknown",
                         **kwargs) -> str:
    """
    Convenience function to log PHI access.
    
    Args:
        user_id: User whose PHI was accessed
        action: Action performed (e.g., "view", "process")
        system_component: System component performing access
        **kwargs: Additional arguments passed to log_access
        
    Returns:
        Record ID of the logged access
    """
    phi_logger = get_phi_logger()
    return await phi_logger.log_access(
        user_id=user_id,
        action=action,
        system_component=system_component,
        **kwargs
    )