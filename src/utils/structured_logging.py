"""
Structured logging utilities for the CANOPY system.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional

class StructuredLogFormatter(logging.Formatter):
    """Formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Get a structured logger instance."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Add handler if none exists
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(StructuredLogFormatter())
        logger.addHandler(handler)
    
    return logger

def log_structured(logger: logging.Logger,
                  level: int,
                  message: str,
                  extra: Optional[Dict[str, Any]] = None) -> None:
    """Log a structured message."""
    logger.log(level, message, extra=extra or {})