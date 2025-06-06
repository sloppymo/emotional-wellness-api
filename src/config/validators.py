"""
Settings validators for the Emotional Wellness API.
Ensures that configurations meet security and HIPAA compliance requirements.
"""

import re
import secrets
import string
from typing import Any, Callable, Dict, Optional

from pydantic import validator, SecretStr


class SettingsValidators:
    """Validation methods for application settings."""
    
    @staticmethod
    @validator("database_url")
    def validate_database_url(cls, v: str) -> str:
        """
        Validate database URL format and ensure it's secure.
        Doesn't log the actual URL for HIPAA compliance.
        """
        if not v.startswith(("postgresql://", "postgresql+psycopg2://")):
            raise ValueError("Database URL must be PostgreSQL")
            
        # Check for SSL mode in production
        if "environment" in cls.__dict__ and cls.__dict__["environment"] == "production":
            if "sslmode=require" not in v and "sslmode=verify-full" not in v:
                raise ValueError("Production database connections must use SSL")
                
        return v
    
    @staticmethod
    @validator("jwt_secret_key")
    def validate_jwt_secret(cls, v: SecretStr) -> SecretStr:
        """Ensure JWT secret key meets security requirements."""
        secret = v.get_secret_value()
        if len(secret) < 32:
            raise ValueError("JWT secret key must be at least 32 characters")
        
        # Check entropy requirements
        has_lower = any(c.islower() for c in secret)
        has_upper = any(c.isupper() for c in secret)
        has_digit = any(c.isdigit() for c in secret)
        has_special = any(c in string.punctuation for c in secret)
        
        if not all([has_lower, has_upper, has_digit, has_special]):
            raise ValueError(
                "JWT secret must contain lowercase, uppercase, "
                "digits and special characters"
            )
            
        return v
    
    @staticmethod
    @validator("phi_encryption_key")
    def validate_phi_encryption_key(cls, v: SecretStr) -> SecretStr:
        """Ensure PHI encryption key meets HIPAA security requirements."""
        secret = v.get_secret_value()
        # For AES-256, key should be 32 bytes (256 bits)
        if len(secret) != 32:
            raise ValueError("PHI encryption key must be exactly 32 characters (256 bits)")
            
        return v
    
    @staticmethod
    @validator("api_key")
    def validate_api_key(cls, v: SecretStr) -> SecretStr:
        """Validate API key meets security requirements."""
        secret = v.get_secret_value()
        if len(secret) < 32:
            raise ValueError("API key must be at least 32 characters")
            
        # Ensure it's sufficiently random looking
        if re.search(r'(.)\1{5,}', secret):  # Check for repeated characters
            raise ValueError("API key cannot contain long repeated sequences")
            
        return v
    
    @staticmethod
    @validator("redis_url")
    def validate_redis_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate Redis URL format."""
        if v is None:
            return v
            
        if not v.startswith(("redis://", "rediss://")):
            raise ValueError("Redis URL must start with redis:// or rediss://")
            
        # Ensure TLS in production
        if "environment" in cls.__dict__ and cls.__dict__["environment"] == "production":
            if not v.startswith("rediss://"):
                raise ValueError("Production Redis connections must use TLS (rediss://)")
                
        return v
    
    @staticmethod
    @validator("audit_log_retention_days")
    def validate_audit_retention(cls, v: int) -> int:
        """Ensure audit log retention meets HIPAA requirements."""
        # HIPAA requires 6 years of audit logs
        min_retention = 365 * 6  # 6 years
        
        if "environment" in cls.__dict__ and cls.__dict__["environment"] == "production":
            if v < min_retention:
                raise ValueError(f"Audit logs must be retained for at least {min_retention} days in production")
                
        return v
    
    @staticmethod
    @validator("allowed_cors_origins")
    def validate_cors_origins(cls, v: list) -> list:
        """Validate CORS origins for security."""
        # In production, don't allow wildcards
        if "environment" in cls.__dict__ and cls.__dict__["environment"] == "production":
            if "*" in v:
                raise ValueError("Wildcard CORS origin not allowed in production")
                
        return v
    
    @staticmethod
    def generate_secret_key(length: int = 32) -> str:
        """Generate a cryptographically secure random key."""
        alphabet = string.ascii_letters + string.digits + string.punctuation
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def mask_secret(secret: str, show_chars: int = 4) -> str:
        """Mask a secret value for logging, showing only the last few chars."""
        if not secret or len(secret) <= show_chars:
            return "****"
        return "****" + secret[-show_chars:]
