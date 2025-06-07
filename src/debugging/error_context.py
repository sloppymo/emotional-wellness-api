"""
Advanced Error Context Capture System

Provides comprehensive error context capture with system state,
user context, and automated debugging suggestions.
"""

import asyncio
import traceback
import sys
import time
import uuid
import json
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from contextlib import asynccontextmanager
from functools import wraps
import inspect

from ..structured_logging import get_logger
from ..config.settings import get_settings


@dataclass
class SystemSnapshot:
    """Snapshot of system state at error time."""
    timestamp: datetime
    memory_percent: float
    cpu_percent: float
    disk_usage_percent: float
    active_connections: int
    process_count: int
    load_average: List[float] = field(default_factory=list)
    
    @classmethod
    async def capture(cls) -> 'SystemSnapshot':
        """Capture current system state."""
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get load average (Unix-like systems)
            try:
                load_avg = list(psutil.getloadavg())
            except (AttributeError, OSError):
                load_avg = []
            
            return cls(
                timestamp=datetime.utcnow(),
                memory_percent=memory.percent,
                cpu_percent=psutil.cpu_percent(interval=0.1),
                disk_usage_percent=(disk.used / disk.total) * 100,
                active_connections=len(psutil.net_connections()),
                process_count=len(psutil.pids()),
                load_average=load_avg
            )
        except Exception:
            # Fallback if system monitoring fails
            return cls(
                timestamp=datetime.utcnow(),
                memory_percent=0.0,
                cpu_percent=0.0,
                disk_usage_percent=0.0,
                active_connections=0,
                process_count=0
            )


@dataclass
class ApplicationContext:
    """Application-specific context at error time."""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    component: Optional[str] = None
    operation: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorContext:
    """Comprehensive error context information."""
    error_id: str
    timestamp: datetime
    error_type: str
    error_message: str
    traceback_text: str
    function_name: str
    file_name: str
    line_number: int
    
    # Context information
    system_snapshot: SystemSnapshot
    app_context: ApplicationContext
    
    # Code context
    local_variables: Dict[str, str] = field(default_factory=dict)
    function_arguments: Dict[str, str] = field(default_factory=dict)
    call_stack: List[Dict[str, Any]] = field(default_factory=list)
    
    # Related errors
    similar_errors: List[str] = field(default_factory=list)
    error_frequency: int = 1
    
    # Debugging suggestions
    suggestions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


class ErrorContextCapture:
    """
    Advanced error context capture system.
    
    Features:
    - Comprehensive system state capture
    - Application context tracking
    - Local variable inspection
    - Call stack analysis
    - Error pattern detection
    - Automated debugging suggestions
    """
    
    def __init__(self):
        self.logger = get_logger("error_context")
        self.settings = get_settings()
        
        # Error tracking
        self.error_history: List[ErrorContext] = []
        self.error_patterns: Dict[str, int] = {}
        
        # Context stack for nested operations
        self.context_stack: List[ApplicationContext] = []
        
        # Error handlers
        self.error_handlers: List[Callable] = []
        
        # Maximum items to keep in memory
        self.max_history_size = 1000
        
    def push_context(self, context: ApplicationContext):
        """Push application context onto the stack."""
        self.context_stack.append(context)
        
    def pop_context(self) -> Optional[ApplicationContext]:
        """Pop application context from the stack."""
        return self.context_stack.pop() if self.context_stack else None
    
    def get_current_context(self) -> Optional[ApplicationContext]:
        """Get current application context."""
        return self.context_stack[-1] if self.context_stack else None
    
    @asynccontextmanager
    async def capture_context(
        self,
        component: str,
        operation: str,
        user_id: str = None,
        session_id: str = None,
        **metadata
    ):
        """Context manager for automatic error context capture."""
        context = ApplicationContext(
            user_id=user_id,
            session_id=session_id,
            component=component,
            operation=operation,
            metadata=metadata
        )
        
        self.push_context(context)
        
        try:
            yield context
        except Exception as e:
            # Capture error context automatically
            await self.capture_error(e, context)
            raise
        finally:
            self.pop_context()
    
    async def capture_error(
        self,
        error: Exception,
        app_context: ApplicationContext = None
    ) -> ErrorContext:
        """Capture comprehensive error context."""
        error_id = str(uuid.uuid4())
        
        # Get traceback information
        tb = traceback.extract_tb(error.__traceback__)
        if tb:
            last_frame = tb[-1]
            function_name = last_frame.name
            file_name = last_frame.filename
            line_number = last_frame.lineno
        else:
            function_name = "unknown"
            file_name = "unknown"
            line_number = 0
        
        # Capture system state
        system_snapshot = await SystemSnapshot.capture()
        
        # Use current context if none provided
        if app_context is None:
            app_context = self.get_current_context() or ApplicationContext()
        
        # Capture local variables and function arguments
        local_vars, func_args = self._capture_local_context(error)
        
        # Build call stack
        call_stack = self._build_call_stack(error)
        
        # Create error context
        error_context = ErrorContext(
            error_id=error_id,
            timestamp=datetime.utcnow(),
            error_type=type(error).__name__,
            error_message=str(error),
            traceback_text=traceback.format_exc(),
            function_name=function_name,
            file_name=file_name,
            line_number=line_number,
            system_snapshot=system_snapshot,
            app_context=app_context,
            local_variables=local_vars,
            function_arguments=func_args,
            call_stack=call_stack
        )
        
        # Analyze error patterns
        await self._analyze_error_patterns(error_context)
        
        # Generate debugging suggestions
        error_context.suggestions = await self._generate_suggestions(error_context)
        
        # Store error context
        self._store_error_context(error_context)
        
        # Notify error handlers
        await self._notify_error_handlers(error_context)
        
        self.logger.error(
            f"Error captured: {error_context.error_type}",
            extra={
                "error_id": error_id,
                "component": app_context.component,
                "operation": app_context.operation,
                "user_id": app_context.user_id,
                "session_id": app_context.session_id
            }
        )
        
        return error_context
    
    def _capture_local_context(self, error: Exception) -> tuple[Dict[str, str], Dict[str, str]]:
        """Capture local variables and function arguments."""
        local_vars = {}
        func_args = {}
        
        try:
            # Get the frame where the error occurred
            frame = error.__traceback__.tb_frame
            
            # Capture local variables (safely)
            for name, value in frame.f_locals.items():
                try:
                    # Convert to string representation, truncate if too long
                    str_value = str(value)
                    if len(str_value) > 200:
                        str_value = str_value[:200] + "..."
                    local_vars[name] = str_value
                except Exception:
                    local_vars[name] = "<unable to serialize>"
            
            # Try to identify function arguments
            if frame.f_code:
                arg_names = frame.f_code.co_varnames[:frame.f_code.co_argcount]
                for arg_name in arg_names:
                    if arg_name in local_vars:
                        func_args[arg_name] = local_vars[arg_name]
                        
        except Exception as e:
            self.logger.warning(f"Failed to capture local context: {e}")
        
        return local_vars, func_args
    
    def _build_call_stack(self, error: Exception) -> List[Dict[str, Any]]:
        """Build detailed call stack information."""
        call_stack = []
        
        try:
            tb = traceback.extract_tb(error.__traceback__)
            for frame in tb:
                call_stack.append({
                    "filename": frame.filename,
                    "function": frame.name,
                    "line_number": frame.lineno,
                    "code": frame.line or ""
                })
        except Exception as e:
            self.logger.warning(f"Failed to build call stack: {e}")
        
        return call_stack
    
    async def _analyze_error_patterns(self, error_context: ErrorContext):
        """Analyze error patterns and frequency."""
        # Create error signature for pattern matching
        error_signature = f"{error_context.error_type}:{error_context.function_name}:{error_context.line_number}"
        
        # Update pattern frequency
        self.error_patterns[error_signature] = self.error_patterns.get(error_signature, 0) + 1
        error_context.error_frequency = self.error_patterns[error_signature]
        
        # Find similar errors
        similar_errors = []
        for existing_error in self.error_history[-50:]:  # Check last 50 errors
            if (existing_error.error_type == error_context.error_type and
                existing_error.function_name == error_context.function_name):
                similar_errors.append(existing_error.error_id)
        
        error_context.similar_errors = similar_errors
    
    async def _generate_suggestions(self, error_context: ErrorContext) -> List[str]:
        """Generate debugging suggestions based on error context."""
        suggestions = []
        
        # System resource suggestions
        if error_context.system_snapshot.memory_percent > 90:
            suggestions.append("High memory usage detected - consider restarting services or investigating memory leaks")
        
        if error_context.system_snapshot.cpu_percent > 90:
            suggestions.append("High CPU usage detected - check for infinite loops or heavy computations")
        
        if error_context.system_snapshot.disk_usage_percent > 95:
            suggestions.append("Low disk space - clean up logs or temporary files")
        
        # Error type specific suggestions
        error_type = error_context.error_type
        
        if error_type == "ConnectionError":
            suggestions.append("Check network connectivity and service availability")
            suggestions.append("Verify database and Redis connections")
            
        elif error_type == "TimeoutError":
            suggestions.append("Increase timeout values or optimize slow operations")
            suggestions.append("Check for blocking operations in async code")
            
        elif error_type == "KeyError":
            suggestions.append("Validate input data structure and required fields")
            suggestions.append("Add defensive programming checks for missing keys")
            
        elif error_type == "AttributeError":
            suggestions.append("Check object initialization and method availability")
            suggestions.append("Verify object types and inheritance")
            
        elif error_type == "ImportError":
            suggestions.append("Check package installation and Python path")
            suggestions.append("Verify virtual environment activation")
        
        # Component specific suggestions
        component = error_context.app_context.component
        
        if component == "moss":
            suggestions.append("Check MOSS system health with: make debug-moss")
            suggestions.append("Verify crisis detection thresholds and configuration")
            
        elif component == "veluria":
            suggestions.append("Check VELURIA protocol definitions and escalation manager")
            suggestions.append("Verify intervention protocol state management")
            
        elif component == "database":
            suggestions.append("Check database connectivity and migration status")
            suggestions.append("Verify database credentials and permissions")
            
        elif component == "redis":
            suggestions.append("Check Redis server status and connectivity")
            suggestions.append("Verify Redis configuration and memory usage")
        
        # Frequency-based suggestions
        if error_context.error_frequency > 5:
            suggestions.append(f"This error has occurred {error_context.error_frequency} times - investigate root cause")
            suggestions.append("Consider adding circuit breaker pattern or retry logic")
        
        # Default suggestions if none found
        if not suggestions:
            suggestions.append("Check application logs for additional context")
            suggestions.append("Run system health check with: make debug-health")
            suggestions.append("Review recent code changes and deployments")
        
        return suggestions
    
    def _store_error_context(self, error_context: ErrorContext):
        """Store error context in memory (and optionally persist)."""
        self.error_history.append(error_context)
        
        # Trim history if too large
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size:]
    
    async def _notify_error_handlers(self, error_context: ErrorContext):
        """Notify registered error handlers."""
        for handler in self.error_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(error_context)
                else:
                    handler(error_context)
            except Exception as e:
                self.logger.warning(f"Error handler failed: {e}")
    
    def add_error_handler(self, handler: Callable):
        """Add an error handler function."""
        self.error_handlers.append(handler)
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the specified time period."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        recent_errors = [
            error for error in self.error_history
            if error.timestamp >= cutoff_time
        ]
        
        # Count by error type
        error_types = {}
        for error in recent_errors:
            error_types[error.error_type] = error_types.get(error.error_type, 0) + 1
        
        # Count by component
        components = {}
        for error in recent_errors:
            component = error.app_context.component or "unknown"
            components[component] = components.get(component, 0) + 1
        
        # Most frequent errors
        frequent_patterns = sorted(
            self.error_patterns.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            "total_errors": len(recent_errors),
            "time_period_hours": hours,
            "error_types": error_types,
            "components": components,
            "frequent_patterns": frequent_patterns,
            "system_health": self._assess_system_health(recent_errors)
        }
    
    def _assess_system_health(self, recent_errors: List[ErrorContext]) -> str:
        """Assess overall system health based on recent errors."""
        if not recent_errors:
            return "healthy"
        
        error_rate = len(recent_errors) / 24  # errors per hour
        
        if error_rate > 10:
            return "critical"
        elif error_rate > 5:
            return "degraded"
        elif error_rate > 1:
            return "warning"
        else:
            return "healthy"


# Global error context capture instance
_error_capture = ErrorContextCapture()


def enhanced_error_handler(func):
    """Decorator for automatic error context capture."""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            await _error_capture.capture_error(e)
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # For sync functions, we can't await, so we schedule the capture
            asyncio.create_task(_error_capture.capture_error(e))
            raise
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def get_error_capture() -> ErrorContextCapture:
    """Get the global error capture instance."""
    return _error_capture 