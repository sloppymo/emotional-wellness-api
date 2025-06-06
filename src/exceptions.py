"""Custom exception hierarchy for Emotional Wellness API."""

from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status


class BaseAPIException(Exception):
    """Base exception for all API exceptions."""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)
    
    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException."""
        return HTTPException(
            status_code=self.status_code,
            detail={
                "error": self.error_code,
                "message": self.message,
                "details": self.details
            }
        )


# Authentication & Authorization Exceptions
class AuthenticationError(BaseAPIException):
    """Raised when authentication fails."""
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_ERROR",
            details=details
        )


class AuthorizationError(BaseAPIException):
    """Raised when user lacks required permissions."""
    def __init__(self, message: str = "Insufficient permissions", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTHORIZATION_ERROR",
            details=details
        )


class TokenError(AuthenticationError):
    """Raised when token validation fails."""
    def __init__(self, message: str = "Invalid or expired token", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            details=details
        )
        self.error_code = "TOKEN_ERROR"


# Resource Exceptions
class ResourceNotFoundError(BaseAPIException):
    """Raised when a requested resource is not found."""
    def __init__(self, resource_type: str, resource_id: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"{resource_type} with ID '{resource_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id, **(details or {})}
        )


class ResourceConflictError(BaseAPIException):
    """Raised when there's a conflict with existing resources."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="RESOURCE_CONFLICT",
            details=details
        )


# Validation Exceptions
class ValidationError(BaseAPIException):
    """Raised when input validation fails."""
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details={"field": field, **(details or {})} if field else details
        )


class InvalidInputError(ValidationError):
    """Raised when input data is invalid."""
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            field=field,
            details=details
        )
        self.error_code = "INVALID_INPUT"


# Clinical Domain Exceptions
class ClinicalError(BaseAPIException):
    """Base exception for clinical domain errors."""
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status_code,
            error_code="CLINICAL_ERROR",
            details=details
        )


class AssessmentError(ClinicalError):
    """Raised when assessment processing fails."""
    def __init__(self, message: str, assessment_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            details={"assessment_id": assessment_id, **(details or {})} if assessment_id else details
        )
        self.error_code = "ASSESSMENT_ERROR"


class InterventionError(ClinicalError):
    """Raised when intervention execution fails."""
    def __init__(self, message: str, intervention_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            details={"intervention_id": intervention_id, **(details or {})} if intervention_id else details
        )
        self.error_code = "INTERVENTION_ERROR"


class ProtocolError(ClinicalError):
    """Raised when protocol execution fails."""
    def __init__(self, message: str, protocol_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            details={"protocol_id": protocol_id, **(details or {})} if protocol_id else details
        )
        self.error_code = "PROTOCOL_ERROR"


class EscalationError(ClinicalError):
    """Raised when escalation process fails."""
    def __init__(self, message: str, escalation_level: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,  # Escalation errors are critical
            details={"escalation_level": escalation_level, **(details or {})} if escalation_level else details
        )
        self.error_code = "ESCALATION_ERROR"


# Analytics Exceptions
class AnalyticsError(BaseAPIException):
    """Base exception for analytics errors."""
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status_code,
            error_code="ANALYTICS_ERROR",
            details=details
        )


class DataProcessingError(AnalyticsError):
    """Raised when data processing fails."""
    def __init__(self, message: str, dataset: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            details={"dataset": dataset, **(details or {})} if dataset else details
        )
        self.error_code = "DATA_PROCESSING_ERROR"


class InsufficientDataError(AnalyticsError):
    """Raised when there's insufficient data for analysis."""
    def __init__(self, message: str = "Insufficient data for analysis", required: Optional[int] = None, available: Optional[int] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"required": required, "available": available} if required and available else {}
        )
        self.error_code = "INSUFFICIENT_DATA"


# Integration Exceptions
class IntegrationError(BaseAPIException):
    """Base exception for external integration errors."""
    def __init__(self, message: str, service: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_code="INTEGRATION_ERROR",
            details={"service": service, **(details or {})} if service else details
        )


class ExternalServiceError(IntegrationError):
    """Raised when external service call fails."""
    def __init__(self, service: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"External service '{service}' error: {message}",
            service=service,
            details=details
        )
        self.error_code = "EXTERNAL_SERVICE_ERROR"


# Task & Background Processing Exceptions
class TaskError(BaseAPIException):
    """Base exception for task processing errors."""
    def __init__(self, message: str, task_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="TASK_ERROR",
            details={"task_id": task_id, **(details or {})} if task_id else details
        )


class TaskTimeoutError(TaskError):
    """Raised when a task times out."""
    def __init__(self, task_id: str, timeout_seconds: int):
        super().__init__(
            message=f"Task {task_id} timed out after {timeout_seconds} seconds",
            task_id=task_id,
            details={"timeout_seconds": timeout_seconds}
        )
        self.error_code = "TASK_TIMEOUT"


# Database Exceptions
class DatabaseError(BaseAPIException):
    """Base exception for database errors."""
    def __init__(self, message: str, operation: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="DATABASE_ERROR",
            details={"operation": operation, **(details or {})} if operation else details
        )


class TransactionError(DatabaseError):
    """Raised when a database transaction fails."""
    def __init__(self, message: str, operation: Optional[str] = None):
        super().__init__(
            message=f"Transaction failed: {message}",
            operation=operation
        )
        self.error_code = "TRANSACTION_ERROR"


# Rate Limiting Exceptions
class RateLimitError(BaseAPIException):
    """Raised when rate limit is exceeded."""
    def __init__(self, limit: int, window: str, retry_after: Optional[int] = None):
        super().__init__(
            message=f"Rate limit exceeded: {limit} requests per {window}",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"limit": limit, "window": window, "retry_after": retry_after}
        )


# Business Logic Exceptions
class BusinessLogicError(BaseAPIException):
    """Base exception for business logic violations."""
    def __init__(self, message: str, rule: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="BUSINESS_LOGIC_ERROR",
            details={"rule": rule, **(details or {})} if rule else details
        )


class StateTransitionError(BusinessLogicError):
    """Raised when an invalid state transition is attempted."""
    def __init__(self, current_state: str, requested_state: str, allowed_states: Optional[List[str]] = None):
        super().__init__(
            message=f"Invalid state transition from '{current_state}' to '{requested_state}'",
            rule="state_transition",
            details={
                "current_state": current_state,
                "requested_state": requested_state,
                "allowed_states": allowed_states or []
            }
        )
        self.error_code = "INVALID_STATE_TRANSITION" 