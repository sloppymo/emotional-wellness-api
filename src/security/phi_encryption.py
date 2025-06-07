"""
PHI Encryption Module for HIPAA Compliance

This module provides field-level encryption for Protected Health Information (PHI)
using AES-256 (Fernet) with key rotation support and audit logging.
"""

import os
import json
import base64
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union, List
from cryptography.fernet import Fernet, MultiFernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from pydantic import BaseModel, Field

from ..utils.structured_logging import get_logger
from ..config.settings import Settings

logger = get_logger(__name__)

class PHIEncryptionKey(BaseModel):
    """PHI encryption key with metadata."""
    key_id: str = Field(..., description="Unique identifier for this key")
    key: bytes = Field(..., description="The actual encryption key")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(None, description="Key expiration date")
    is_active: bool = Field(default=True, description="Whether this key is currently active")
    rotation_reason: Optional[str] = Field(None, description="Reason for key rotation if applicable")

class PHIEncryptionManager:
    """
    Manages PHI encryption with key rotation and audit logging.
    
    Features:
    - Field-level encryption using AES-256 (Fernet)
    - Automatic key rotation
    - Audit logging of encryption operations
    - Support for multiple active keys during rotation
    """
    
    def __init__(self, settings: Settings):
        """Initialize the PHI encryption manager."""
        self.settings = settings
        self._keys: Dict[str, PHIEncryptionKey] = {}
        self._fernet: Optional[MultiFernet] = None
        self._initialize_keys()
        
    def _initialize_keys(self) -> None:
        """Initialize encryption keys from settings."""
        try:
            # Load primary key from settings
            primary_key = self._derive_key(self.settings.PHI_ENCRYPTION_KEY)
            key_id = self._generate_key_id(primary_key)
            
            self._keys[key_id] = PHIEncryptionKey(
                key_id=key_id,
                key=primary_key,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=90)  # 90-day key rotation
            )
            
            # Initialize Fernet with primary key
            self._fernet = MultiFernet([Fernet(primary_key)])
            
            logger.info(
                "PHI encryption initialized",
                extra={
                    "key_id": key_id,
                    "key_created_at": self._keys[key_id].created_at.isoformat(),
                    "key_expires_at": self._keys[key_id].expires_at.isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize PHI encryption: {e}")
            raise
    
    def _derive_key(self, master_key: str) -> bytes:
        """Derive an encryption key from the master key."""
        salt = b"PHI_ENCRYPTION_SALT"  # In production, use a secure random salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
    
    def _generate_key_id(self, key: bytes) -> str:
        """Generate a unique identifier for a key."""
        return base64.urlsafe_b64encode(key[:8]).decode()
    
    def encrypt_field(self, value: Any, field_name: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Encrypt a single field value.
        
        Args:
            value: The value to encrypt
            field_name: Name of the field being encrypted
            context: Additional context for audit logging
            
        Returns:
            Encrypted value as a string
        """
        if value is None:
            return None
            
        try:
            # Convert value to JSON string for consistent encryption
            value_str = json.dumps(value)
            
            # Encrypt the value
            encrypted = self._fernet.encrypt(value_str.encode())
            
            # Log the encryption operation
            logger.info(
                "PHI field encrypted",
                extra={
                    "field_name": field_name,
                    "key_id": list(self._keys.keys())[0],  # Current active key
                    "context": context or {}
                }
            )
            
            return encrypted.decode()
            
        except Exception as e:
            logger.error(
                f"Failed to encrypt PHI field: {e}",
                extra={
                    "field_name": field_name,
                    "context": context or {}
                }
            )
            raise
    
    def decrypt_field(self, encrypted_value: str, field_name: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Decrypt a single field value.
        
        Args:
            encrypted_value: The encrypted value to decrypt
            field_name: Name of the field being decrypted
            context: Additional context for audit logging
            
        Returns:
            Decrypted value
        """
        if encrypted_value is None:
            return None
            
        try:
            # Decrypt the value
            decrypted = self._fernet.decrypt(encrypted_value.encode())
            
            # Parse the JSON string back to original type
            value = json.loads(decrypted.decode())
            
            # Log the decryption operation
            logger.info(
                "PHI field decrypted",
                extra={
                    "field_name": field_name,
                    "key_id": list(self._keys.keys())[0],  # Current active key
                    "context": context or {}
                }
            )
            
            return value
            
        except Exception as e:
            logger.error(
                f"Failed to decrypt PHI field: {e}",
                extra={
                    "field_name": field_name,
                    "context": context or {}
                }
            )
            raise
    
    def rotate_keys(self, reason: str = "scheduled_rotation") -> None:
        """
        Rotate encryption keys.
        
        Args:
            reason: Reason for key rotation
        """
        try:
            # Generate new key
            new_key = Fernet.generate_key()
            key_id = self._generate_key_id(new_key)
            
            # Create new key record
            self._keys[key_id] = PHIEncryptionKey(
                key_id=key_id,
                key=new_key,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=90),
                rotation_reason=reason
            )
            
            # Update Fernet with all active keys
            active_keys = [k.key for k in self._keys.values() if k.is_active]
            self._fernet = MultiFernet([Fernet(k) for k in active_keys])
            
            # Mark old keys as inactive after grace period
            for key in self._keys.values():
                if key.key_id != key_id and key.is_active:
                    key.is_active = False
                    key.expires_at = datetime.utcnow() + timedelta(days=30)  # 30-day grace period
            
            logger.info(
                "PHI encryption keys rotated",
                extra={
                    "new_key_id": key_id,
                    "reason": reason,
                    "active_keys": len(active_keys)
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to rotate PHI encryption keys: {e}")
            raise
    
    def get_key_status(self) -> Dict[str, Any]:
        """Get status of all encryption keys."""
        return {
            "active_keys": len([k for k in self._keys.values() if k.is_active]),
            "total_keys": len(self._keys),
            "keys": [
                {
                    "key_id": k.key_id,
                    "created_at": k.created_at.isoformat(),
                    "expires_at": k.expires_at.isoformat() if k.expires_at else None,
                    "is_active": k.is_active,
                    "rotation_reason": k.rotation_reason
                }
                for k in self._keys.values()
            ]
        }

# Global instance
_phi_encryption_manager: Optional[PHIEncryptionManager] = None

def get_phi_encryption_manager() -> PHIEncryptionManager:
    """Get the global PHI encryption manager instance."""
    global _phi_encryption_manager
    if _phi_encryption_manager is None:
        from ..config.settings import get_settings
        _phi_encryption_manager = PHIEncryptionManager(get_settings())
    return _phi_encryption_manager 