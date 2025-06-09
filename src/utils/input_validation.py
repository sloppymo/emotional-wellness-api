"""
Input validation utilities for preventing injection attacks.
"""

import re
import html
from typing import Any, List, Optional
from fastapi import HTTPException

class InputValidator:
    """Utilities for validating and sanitizing user input."""
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"('|(\'))+.*(or|union|select|insert|update|delete|drop|create|alter)",
        r"(union|select|insert|update|delete|drop|create|alter).+",
        r"(exec|execute|sp_|xp_).+",
        r"(script|javascript|vbscript|onload|onerror|onclick).+"
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"vbscript:",
        r"onload\s*=",
        r"onerror\s*=",
        r"onclick\s*="
    ]
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """Sanitize string input to prevent XSS."""
        if not value:
            return ""
        
        # Truncate if too long
        if len(value) > max_length:
            value = value[:max_length]
        
        # HTML escape
        value = html.escape(value)
        
        # Remove potentially dangerous patterns
        for pattern in InputValidator.XSS_PATTERNS:
            value = re.sub(pattern, "", value, flags=re.IGNORECASE)
        
        return value.strip()
    
    @staticmethod
    def validate_sql_safe(value: str) -> bool:
        """Check if string is safe from SQL injection."""
        if not value:
            return True
        
        for pattern in InputValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return False
        
        return True
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_user_input(
        value: Any,
        field_name: str,
        max_length: int = 1000,
        required: bool = True,
        allow_sql: bool = False
    ) -> str:
        """Comprehensive input validation."""
        
        # Check if required
        if required and not value:
            raise HTTPException(
                status_code=400,
                detail=f"{field_name} is required"
            )
        
        if not value:
            return ""
        
        # Convert to string
        str_value = str(value)
        
        # Check length
        if len(str_value) > max_length:
            raise HTTPException(
                status_code=400,
                detail=f"{field_name} exceeds maximum length of {max_length}"
            )
        
        # Check for SQL injection if not allowed
        if not allow_sql and not InputValidator.validate_sql_safe(str_value):
            raise HTTPException(
                status_code=400,
                detail=f"{field_name} contains potentially dangerous content"
            )
        
        # Sanitize and return
        return InputValidator.sanitize_string(str_value, max_length)

def validate_request_data(data: dict, validation_rules: dict) -> dict:
    """Validate request data according to rules."""
    validated_data = {}
    
    for field, rules in validation_rules.items():
        value = data.get(field)
        
        validated_data[field] = InputValidator.validate_user_input(
            value=value,
            field_name=field,
            max_length=rules.get("max_length", 1000),
            required=rules.get("required", True),
            allow_sql=rules.get("allow_sql", False)
        )
    
    return validated_data
