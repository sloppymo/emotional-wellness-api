"""
HIPAA compliance utilities for the CANOPY system.
"""
#  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
#  ┃                               ┃
#  ┃  If this code works,          ┃
#  ┃  it was written by me.        ┃
#  ┃                               ┃
#  ┃  If it doesn't work,          ┃
#  ┃  I don't know who wrote it.   ┃
#  ┃                               ┃
#  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

import re
from datetime import datetime
from typing import Dict, Any, List, Optional

class HIPAACompliance:
    """HIPAA compliance checking and validation."""
    
    # PHI patterns - regex to catch personal data like ssn, phone, email, names, dates
    PHI_PATTERNS = [
        r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b',  # SSN
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
        r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',  # Dates
        r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'  # Names
    ]
    
    @classmethod
    def check_processor(cls, processor: Any) -> bool:
        """Check if a processor is HIPAA compliant - verify it won't leak personal data."""
        # Check logging configuration
        if not hasattr(processor, '_logger'):
            return False
        
        # Check data handling
        if not hasattr(processor, '_clean_phi'):
            return False
        
        # Check audit trail
        if not hasattr(processor, '_audit_log'):
            return False
        
        return True
    
    @classmethod
    def check_output(cls, output: Any) -> bool:
        """Check if output is HIPAA compliant."""
        if not output:
            return True
        
        # Convert output to string for checking
        output_str = str(output)
        
        # Check for PHI
        for pattern in cls.PHI_PATTERNS:
            if re.search(pattern, output_str):
                return False
        
        return True
    
    @classmethod
    def check_storage(cls, data: Dict[str, Any]) -> bool:
        """Check if stored data is HIPAA compliant."""
        if not data:
            return True
        
        # Convert data to string for checking
        data_str = str(data)
        
        # Check for PHI
        for pattern in cls.PHI_PATTERNS:
            if re.search(pattern, data_str):
                return False
        
        return True
    
    @classmethod
    def check_transmission(cls, data: Any) -> bool:
        """Check if transmitted data is HIPAA compliant."""
        return cls.check_output(data)
    
    @classmethod
    def clean_phi(cls, text: str) -> str:
        """Clean PHI from text."""
        if not text:
            return text
        
        # Replace PHI with placeholders
        for pattern in cls.PHI_PATTERNS:
            text = re.sub(pattern, '[REDACTED]', text)
        
        return text
    
    @classmethod
    def audit_log(cls, 
                 action: str,
                 user_id: str,
                 timestamp: Optional[datetime] = None,
                 details: Optional[Dict[str, Any]] = None) -> None:
        """Log HIPAA-relevant actions."""
        from structured_logging import get_logger
        
        logger = get_logger("hipaa_audit")
        log_data = {
            "action": action,
            "user_id": user_id,
            "timestamp": timestamp or datetime.now().isoformat(),
            "details": details or {}
        }
        
        logger.info("HIPAA audit", extra=log_data) 