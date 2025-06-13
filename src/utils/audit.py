"""
Application-wide Audit Logging for Security and Compliance

This module provides a general-purpose audit logging system for:
- Security events (authentication, authorization, etc.)
- PHI/PII access tracking
- Data operations (create, read, update, delete)
- User activity monitoring
- HIPAA compliance requirements
"""

import json
import logging
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import socket
import os
import threading
import asyncio
from contextlib import contextmanager

from fastapi import Request
from pydantic import BaseModel, Field

logger = logging.getLogger("security_audit")

# Setup specific handler for audit logs
handler = logging.FileHandler("logs/audit/security_audit.log")
formatter = logging.Formatter(
    '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}'
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Thread local storage for request context
_request_context = threading.local()


class AuditEventCategory(str, Enum):
    """Categories of audit events"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    SYSTEM_SECURITY = "system_security"
    CONFIGURATION = "configuration"
    USER_MANAGEMENT = "user_management"
    PHI_ACCESS = "phi_access"
    TOKEN_MANAGEMENT = "token_management"


class AuditEventMetadata(BaseModel):
    """Metadata for audit events"""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    category: AuditEventCategory
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    status: str = "success"
    hipaa_relevant: bool = False


@contextmanager
def audit_context(request: Request = None):
    """
    Context manager for audit logging to capture request information
    
    Args:
        request: FastAPI request object
        
    Example:
        with audit_context(request):
            # All audit logs within this context will have request metadata
            log_security_event("user_login", user_id="user123")
    """
    if request:
        _request_context.request = request
        _request_context.request_id = str(uuid.uuid4())
    
    try:
        yield
    finally:
        if hasattr(_request_context, 'request'):
            delattr(_request_context, 'request')
        if hasattr(_request_context, 'request_id'):
            delattr(_request_context, 'request_id')


def log_security_event(
    event_type: str, 
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None, 
    category: AuditEventCategory = AuditEventCategory.SYSTEM_SECURITY,
    details: Optional[Union[Dict, str]] = None,
    status: str = "success",
    hipaa_relevant: bool = False
):
    """
    Log a security-related event for audit purposes
    
    Args:
        event_type: Type of event (e.g., login_attempt, access_denied)
        user_id: ID of user associated with event
        ip_address: Source IP address
        category: Event category
        details: Additional details about the event
        status: Event outcome (success, failure, error)
        hipaa_relevant: Whether this event is relevant to HIPAA compliance
    """
    # Try to get values from context if not provided
    if hasattr(_request_context, 'request') and not ip_address:
        ip_address = _request_context.request.client.host
        
    request_id = getattr(_request_context, 'request_id', None)
    
    if hasattr(_request_context, 'request') and not user_id:
        # Try to get user ID from request if available
        pass  # This would require access to the auth system
    
    # Create metadata
    metadata = AuditEventMetadata(
        category=category,
        user_id=user_id,
        ip_address=ip_address,
        request_id=request_id,
        status=status,
        hipaa_relevant=hipaa_relevant
    )
    
    # Create event payload
    event = {
        "event_type": event_type,
        "metadata": metadata.dict(),
        "details": details
    }
    
    # Log the event
    logger.info(json.dumps(event))
    
    # For HIPAA-relevant events, ensure they're also logged to the compliance system
    if hipaa_relevant:
        _log_hipaa_event(event)


def log_data_access(
    resource_type: str,
    resource_id: str,
    access_type: str,
    user_id: Optional[str] = None,
    data_elements: Optional[List[str]] = None,
    phi_accessed: bool = False
):
    """
    Log access to specific data resources, especially PHI
    
    Args:
        resource_type: Type of resource (e.g., patient, assessment, note)
        resource_id: Identifier of the resource
        access_type: Type of access (read, write, delete)
        user_id: ID of user accessing the data
        data_elements: Specific data elements accessed (not the values)
        phi_accessed: Whether PHI was accessed
    """
    details = {
        "resource_type": resource_type,
        "resource_id": resource_id,
        "access_type": access_type
    }
    
    if data_elements:
        details["data_elements"] = data_elements
        
    category = AuditEventCategory.DATA_ACCESS
    if phi_accessed:
        category = AuditEventCategory.PHI_ACCESS
        
    log_security_event(
        event_type="data_access",
        user_id=user_id,
        category=category,
        details=details,
        hipaa_relevant=phi_accessed
    )


def log_auth_event(
    auth_event: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    success: bool = True,
    details: Optional[Dict] = None
):
    """
    Log authentication and authorization events
    
    Args:
        auth_event: Type of auth event (login, logout, etc.)
        user_id: User identifier
        ip_address: Source IP address
        success: Whether the auth attempt succeeded
        details: Additional auth details
    """
    status = "success" if success else "failure"
    
    log_security_event(
        event_type=auth_event,
        user_id=user_id,
        ip_address=ip_address,
        category=AuditEventCategory.AUTHENTICATION,
        details=details,
        status=status,
        hipaa_relevant=True
    )


def log_token_event(
    token_event: str,
    token_id: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    details: Optional[Dict] = None
):
    """
    Log token-related events
    
    Args:
        token_event: Token event type (created, refreshed, revoked)
        token_id: Token identifier (JTI)
        user_id: User associated with token
        ip_address: Source IP address
        details: Additional token details
    """
    token_details = {
        "token_id": token_id,
        **(details or {})
    }
    
    log_security_event(
        event_type=f"token_{token_event}",
        user_id=user_id,
        ip_address=ip_address,
        category=AuditEventCategory.TOKEN_MANAGEMENT,
        details=token_details,
        hipaa_relevant=True
    )


def _log_hipaa_event(event: Dict):
    """
    Ensure HIPAA-relevant events are logged to dedicated compliance systems
    
    Args:
        event: Event details
    """
    # This would integrate with enterprise HIPAA compliance systems
    # For now, we'll log to a dedicated HIPAA audit log file
    hipaa_logger = logging.getLogger("hipaa_compliance")
    
    if not hipaa_logger.handlers:
        # Setup handler for HIPAA-specific logs
        hipaa_handler = logging.FileHandler("logs/compliance/hipaa_audit.log")
        hipaa_formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}'
        )
        hipaa_handler.setFormatter(hipaa_formatter)
        hipaa_logger.addHandler(hipaa_handler)
        hipaa_logger.setLevel(logging.INFO)
    
    # Add compliance metadata
    event["compliance"] = {
        "framework": "HIPAA",
        "retention_days": 2555,  # 7 years
        "requires_encryption": True
    }
    
    hipaa_logger.info(json.dumps(event))


class DataRetentionPolicy:
    """Data retention policy manager for HIPAA compliance"""
    
    @staticmethod
    def get_retention_period(data_type: str) -> int:
        """
        Get retention period in days for a specific data type
        
        Args:
            data_type: Type of data
            
        Returns:
            Retention period in days
        """
        # HIPAA retention periods
        retention_periods = {
            "patient_records": 2555,  # 7 years
            "audit_logs": 2555,      # 7 years
            "auth_events": 2555,     # 7 years
            "security_incidents": 2555,  # 7 years
            "consent_records": 2555,  # 7 years
            "session_data": 365,     # 1 year
            "temporary_data": 30     # 30 days
        }
        
        return retention_periods.get(data_type, 2555)  # Default to 7 years
    
    @staticmethod
    def should_retain(data_type: str, creation_date: datetime) -> bool:
        """
        Check if data should be retained based on policy
        
        Args:
            data_type: Type of data
            creation_date: When the data was created
            
        Returns:
            True if data should be retained, False if it can be purged
        """
        retention_days = DataRetentionPolicy.get_retention_period(data_type)
        retention_delta = timedelta(days=retention_days)
        expiration_date = creation_date + retention_delta
        
        return datetime.utcnow() <= expiration_date
