"""
Structured logging system for the Emotional Wellness API.
HIPAA-compliant logging with correlation IDs and PII/PHI redaction.
"""

import json
import logging
import sys
import time
import uuid
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Dict, Optional, Union

from fastapi import Request
from pydantic import BaseModel, Field

# Context variable to store request information
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
session_id_var: ContextVar[Optional[str]] = ContextVar("session_id", default=None)


class StructuredLogRecord(BaseModel):
    """Structured log record format that conforms to ECS logging standard."""
    
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    log_level: str
    message: str
    request_id: Optional[str] = None
    user_id: Optional[str] = None  # Anonymized or hashed in production
    session_id: Optional[str] = None
    component: str
    event_type: str
    environment: str
    service_name: str = "emotional-wellness-api"
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    duration_ms: Optional[float] = None
    exception: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None
    
    class Config:
        arbitrary_types_allowed = True


class HipaaCompliantFormatter(logging.Formatter):
    """
    Custom formatter for HIPAA compliance that:
    1. Structures logs in a consistent JSON format
    2. Adds correlation IDs for request tracing
    3. Redacts PII and PHI from logs
    """
    
    # Fields that might contain PII/PHI and should be redacted
    SENSITIVE_FIELDS = {
        "email", "password", "full_name", "first_name", "last_name", 
        "address", "phone", "ssn", "input_text", "content", "emotional_input",
        "personal_details", "health_information", "diagnosis", "symptoms"
    }
    
    def __init__(self, environment: str = "development"):
        super().__init__()
        self.environment = environment
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as structured JSON with HIPAA compliance."""
        # Extract contextual information
        request_id = request_id_var.get()
        user_id = user_id_var.get()
        session_id = session_id_var.get()
        
        # Extract component from the logger name
        component = record.name.split(".")[-1] if "." in record.name else record.name
        
        # Prepare exception info if present
        exception_dict = None
        if record.exc_info:
            exception_type, exception_value, _ = record.exc_info
            exception_dict = {
                "type": exception_type.__name__ if exception_type else "Unknown",
                "message": str(exception_value) if exception_value else "Unknown",
                "traceback": self._redact_traceback(record.exc_text) if record.exc_text else None
            }
        
        # Prepare additional data
        data = {}
        if hasattr(record, "data") and isinstance(record.data, dict):
            # Redact any sensitive information
            data = self._redact_sensitive_data(record.data)
        
        # Create structured log record
        log_record = StructuredLogRecord(
            log_level=record.levelname,
            message=record.getMessage(),
            request_id=request_id,
            user_id=user_id,
            session_id=session_id,
            component=component,
            event_type=getattr(record, "event_type", "log"),
            environment=self.environment,
            trace_id=getattr(record, "trace_id", None),
            span_id=getattr(record, "span_id", None),
            duration_ms=getattr(record, "duration_ms", None),
            exception=exception_dict,
            data=data
        )
        
        return json.dumps(log_record.dict(exclude_none=True))
    
    def _redact_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact sensitive PII/PHI from log data."""
        redacted_data = {}
        for key, value in data.items():
            if key.lower() in self.SENSITIVE_FIELDS:
                redacted_data[key] = "[REDACTED]"
            elif isinstance(value, dict):
                redacted_data[key] = self._redact_sensitive_data(value)
            elif isinstance(value, list):
                redacted_data[key] = [
                    self._redact_sensitive_data(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                redacted_data[key] = value
        return redacted_data
    
    def _redact_traceback(self, traceback: str) -> str:
        """Redact potential sensitive information from tracebacks."""
        # Simple implementation - in a real system, this would be more sophisticated
        # to recognize patterns of sensitive data like credit card numbers, SSNs, etc.
        lines = traceback.split("\n")
        redacted_lines = []
        for line in lines:
            # Redact common patterns that might include sensitive data
            for field in self.SENSITIVE_FIELDS:
                pattern = f"{field}="
                if pattern in line:
                    start = line.find(pattern) + len(pattern)
                    end = line.find(",", start)
                    if end == -1:
                        end = line.find(")", start)
                    if end != -1:
                        line = line[:start] + "[REDACTED]" + line[end:]
            redacted_lines.append(line)
        return "\n".join(redacted_lines)


class RequestContextMiddleware:
    """Middleware that adds correlation IDs to each request context."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        
        # Generate request ID if not present
        headers = dict(scope.get("headers", []))
        request_id = headers.get(b"x-request-id", b"").decode() or str(uuid.uuid4())
        
        # Store in context vars
        request_id_var.set(request_id)
        
        # Process request with context
        return await self.app(scope, receive, send)


class RequestLoggingMiddleware:
    """Middleware that logs request and response information."""
    
    def __init__(self, app, logger=None):
        self.app = app
        self.logger = logger or logging.getLogger("api.request")
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        
        # Start timing the request
        start_time = time.time()
        
        # Prepare request info for logging
        method = scope.get("method", "")
        path = scope["path"]
        query_string = scope.get("query_string", b"").decode()
        path_with_query = f"{path}?{query_string}" if query_string else path
        
        # Log request start
        request_id = request_id_var.get()
        self.logger.info(
            f"Request started: {method} {path_with_query}",
            extra={
                "event_type": "request_start",
                "request_id": request_id,
                "data": {
                    "method": method,
                    "path": path,
                    "query": query_string
                }
            }
        )
        
        # Prepare to capture response info
        status_code = None
        response_headers = {}
        
        # Intercept the send function to capture response info
        async def send_wrapper(message):
            nonlocal status_code, response_headers
            
            if message["type"] == "http.response.start":
                status_code = message["status"]
                response_headers = {
                    k.decode(): v.decode()
                    for k, v in message.get("headers", [])
                }
            
            await send(message)
        
        try:
            # Process the request
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:
            # Log exceptions
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(
                f"Request failed: {method} {path_with_query}",
                exc_info=exc,
                extra={
                    "event_type": "request_error",
                    "request_id": request_id,
                    "duration_ms": duration_ms,
                    "data": {
                        "method": method,
                        "path": path,
                        "status_code": 500,
                        "error": str(exc)
                    }
                }
            )
            raise
        else:
            # Log request completion
            duration_ms = (time.time() - start_time) * 1000
            log_method = self.logger.info
            
            # Use warning level for 4xx and error for 5xx
            if status_code and status_code >= 500:
                log_method = self.logger.error
            elif status_code and status_code >= 400:
                log_method = self.logger.warning
            
            log_method(
                f"Request completed: {method} {path_with_query} {status_code}",
                extra={
                    "event_type": "request_end",
                    "request_id": request_id,
                    "duration_ms": duration_ms,
                    "data": {
                        "method": method,
                        "path": path,
                        "status_code": status_code,
                        "response_time_ms": duration_ms,
                        "content_type": response_headers.get("content-type", "")
                    }
                }
            )


def setup_logging(environment: str = "development", log_level: str = "INFO"):
    """Configure structured logging for the application."""
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler with structured formatter
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(HipaaCompliantFormatter(environment=environment))
    root_logger.addHandler(console)
    
    # Disable propagation for some loggers to avoid double logging
    for logger_name in ["uvicorn", "uvicorn.access"]:
        logging.getLogger(logger_name).propagate = False
    
    # Set SQLAlchemy logging to WARNING to avoid logging queries with PII/PHI
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name that uses structured logging."""
    return logging.getLogger(name)


def log_with_context(
    logger: logging.Logger,
    level: Union[int, str],
    message: str,
    *,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    event_type: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    exc_info: Any = None
):
    """Log with additional context data."""
    # Override context vars if provided
    if user_id is not None:
        user_id_var.set(user_id)
    
    if session_id is not None:
        session_id_var.set(session_id)
    
    # Prepare extra data
    extra = {
        "request_id": request_id_var.get(),
        "data": data or {}
    }
    
    if event_type:
        extra["event_type"] = event_type
    
    # Log the message
    if isinstance(level, str):
        level = getattr(logging, level.upper())
    
    logger.log(level, message, extra=extra, exc_info=exc_info)


async def set_request_context_from_request(request: Request):
    """Extract and set context variables from a FastAPI request."""
    # Set request ID from header or generate new one
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request_id_var.set(request_id)
    
    # Add request ID to response headers
    request.state.request_id = request_id
