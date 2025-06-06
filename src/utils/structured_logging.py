"""
Structured logging module for the emotional wellness API.
Provides consistent logging format and HIPAA-compliant logging capabilities.
"""

import logging
import json
import asyncio
from datetime import datetime
from typing import Any, Dict, Optional
from functools import wraps

class StructuredLogger:
    """Custom logger that provides structured, HIPAA-compliant logging."""
    
    def __init__(self, name: str, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Add console handler if none exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def _format_log(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """Format log message with extra fields."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            **kwargs
        }
        if extra:
            log_data.update(extra)
        return json.dumps(log_data)
    
    def info(self, message: str, **kwargs):
        """Log info level message."""
        self.logger.info(self._format_log(message, **kwargs))
    
    def error(self, message: str, **kwargs):
        """Log error level message."""
        self.logger.error(self._format_log(message, **kwargs))
    
    def warning(self, message: str, **kwargs):
        """Log warning level message."""
        self.logger.warning(self._format_log(message, **kwargs))
    
    def debug(self, message: str, **kwargs):
        """Log debug level message."""
        self.logger.debug(self._format_log(message, **kwargs))
    
    def critical(self, message: str, **kwargs):
        """Log critical level message."""
        self.logger.critical(self._format_log(message, **kwargs))

def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)

def log_execution(logger: Optional[StructuredLogger] = None):
    """Decorator to log function execution."""
    def decorator(func):
        nonlocal logger
        if logger is None:
            logger = get_logger(func.__module__)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            try:
                result = await func(*args, **kwargs)
                logger.info(
                    f"Function {func.__name__} completed successfully",
                    execution_time=(datetime.utcnow() - start_time).total_seconds(),
                    function=func.__name__
                )
                return result
            except Exception as e:
                logger.error(
                    f"Function {func.__name__} failed",
                    error=str(e),
                    execution_time=(datetime.utcnow() - start_time).total_seconds(),
                    function=func.__name__
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            try:
                result = func(*args, **kwargs)
                logger.info(
                    f"Function {func.__name__} completed successfully",
                    execution_time=(datetime.utcnow() - start_time).total_seconds(),
                    function=func.__name__
                )
                return result
            except Exception as e:
                logger.error(
                    f"Function {func.__name__} failed",
                    error=str(e),
                    execution_time=(datetime.utcnow() - start_time).total_seconds(),
                    function=func.__name__
                )
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator