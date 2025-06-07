"""
Encrypted Field Module for HIPAA Compliance

This module provides field-level encryption for Protected Health Information (PHI)
with context tracking, audit integration, and automatic encryption/decryption.
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional, Union, Type, TypeVar, Generic, get_origin, get_args

from pydantic import BaseModel, Field, field_validator, model_validator
from cryptography.fernet import InvalidToken

from .phi_encryption import get_phi_encryption_manager
from ..structured_logging.phi_logger import get_phi_logger, PHICategory
from ..utils.structured_logging import get_logger

logger = get_logger(__name__)
T = TypeVar('T')

class EncryptedField(BaseModel, Generic[T]):
    """
    Base model for fields requiring encryption.
    
    This class provides transparent encryption/decryption of PHI with context tracking
    and audit integration. It supports any JSON-serializable type.
    
    Features:
    - Automatic encryption/decryption
    - Rich metadata including modification history
    - Audit logging integration
    - Type validation
    """
    value: str = Field(..., description="Encrypted value")
    encryption_context: Dict[str, str] = Field(default_factory=dict, description="Context of encryption")
    encryption_date: datetime = Field(default_factory=datetime.utcnow)
    field_name: str = Field(..., description="Name of the field being protected")
    phi_category: PHICategory = Field(default=PHICategory.SENSITIVE_HEALTH_DATA)
    version: int = Field(default=1, description="Schema version for future compatibility")
    modification_history: Optional[Dict[str, datetime]] = Field(default=None, 
                                                              description="Record of modifications")
    _decrypted_value: Any = None
    _original_type: Optional[Type] = None
    
    @classmethod
    def encrypt(cls, value: T, field_name: str, context: Dict[str, str], 
                category: PHICategory = PHICategory.SENSITIVE_HEALTH_DATA) -> 'EncryptedField[T]':
        """
        Factory method to create encrypted field with proper typing.
        
        Args:
            value: The value to encrypt
            field_name: Name of the field being encrypted
            context: Encryption context for audit and tracing
            category: PHI category for compliance classification
            
        Returns:
            Encrypted field instance with original type preserved
        """
        # Get encryption manager
        encryptor = get_phi_encryption_manager()
        
        # Log PHI access
        phi_logger = get_phi_logger()
        user_id = context.get("user_id", "system")
        system_component = context.get("system_component", "EncryptedField")
        
        field = cls(
            value=encryptor.encrypt_field(value, field_name, context),
            encryption_context=context,
            field_name=field_name,
            phi_category=category,
            modification_history={"created": datetime.utcnow()}
        )
        
        # Store original type information for validation
        field._original_type = type(value)
        
        # Log the encryption operation
        phi_logger.log_access(
            user_id=user_id,
            action="encrypt",
            system_component=system_component,
            access_purpose="phi_protection",
            data_elements=[field_name],
            additional_context={"operation": "encrypt", "phi_category": category.value}
        )
        
        return field
    
    def decrypt(self, context: Optional[Dict[str, str]] = None) -> T:
        """
        Decrypt the value with audit logging.
        
        Args:
            context: Additional context for the decryption operation
            
        Returns:
            The decrypted value with original type
        """
        if self._decrypted_value is not None:
            return self._decrypted_value
            
        # Get encryption manager
        encryptor = get_phi_encryption_manager()
        
        # Merge with original context and add current context
        full_context = {**self.encryption_context, **(context or {})}
        
        # Log PHI access
        phi_logger = get_phi_logger()
        user_id = full_context.get("user_id", "system")
        system_component = full_context.get("system_component", "EncryptedField")
        
        try:
            # Decrypt the value
            decrypted = encryptor.decrypt_field(self.value, self.field_name, full_context)
            
            # Cache the decrypted value
            self._decrypted_value = decrypted
            
            # Log the decryption operation
            phi_logger.log_access(
                user_id=user_id,
                action="decrypt",
                system_component=system_component,
                access_purpose="phi_access",
                data_elements=[self.field_name],
                additional_context={"operation": "decrypt", "phi_category": self.phi_category.value}
            )
            
            return decrypted
            
        except InvalidToken:
            logger.error(f"Failed to decrypt field {self.field_name}: Invalid token")
            raise ValueError(f"Cannot decrypt field {self.field_name}: The encryption key may have changed")
        except Exception as e:
            logger.error(f"Failed to decrypt field {self.field_name}: {e}")
            raise
    
    def update(self, new_value: T, context: Dict[str, str]) -> 'EncryptedField[T]':
        """
        Update the encrypted value with new data.
        
        Args:
            new_value: New value to encrypt
            context: Context for the update operation
            
        Returns:
            Updated encrypted field
        """
        # Get encryption manager
        encryptor = get_phi_encryption_manager()
        
        # Log PHI access
        phi_logger = get_phi_logger()
        user_id = context.get("user_id", "system")
        system_component = context.get("system_component", "EncryptedField")
        
        # Update modification history
        if self.modification_history is None:
            self.modification_history = {}
        self.modification_history["updated"] = datetime.utcnow()
        
        # Encrypt new value
        self.value = encryptor.encrypt_field(new_value, self.field_name, context)
        
        # Update context with merge strategy
        self.encryption_context = {**self.encryption_context, **context}
        
        # Update encryption date
        self.encryption_date = datetime.utcnow()
        
        # Reset cached decrypted value
        self._decrypted_value = None
        
        # Log the update operation
        phi_logger.log_access(
            user_id=user_id,
            action="update",
            system_component=system_component,
            access_purpose="phi_modification",
            data_elements=[self.field_name],
            additional_context={"operation": "update", "phi_category": self.phi_category.value}
        )
        
        return self

    def __eq__(self, other):
        """Compare encrypted fields by decrypting and comparing values."""
        if not isinstance(other, EncryptedField):
            return False
        
        return self.decrypt() == other.decrypt()
        
    def __repr__(self):
        """Safe representation that doesn't reveal encrypted content."""
        return f"EncryptedField(field_name='{self.field_name}', phi_category='{self.phi_category}', encrypted=True)"


class EncryptedPHIModel(BaseModel):
    """
    Base model for Pydantic models containing encrypted PHI fields.
    
    This class provides automatic handling of encrypted fields during
    serialization and deserialization.
    """
    @model_validator(mode='after')
    def encrypt_phi_fields(self) -> 'EncryptedPHIModel':
        """Encrypt all fields marked for encryption."""
        for field_name, field in self.model_fields.items():
            if hasattr(field.annotation, "__origin__") and field.annotation.__origin__ == EncryptedField:
                # Get the raw value
                value = getattr(self, field_name, None)
                
                # Skip if already encrypted or None
                if isinstance(value, EncryptedField) or value is None:
                    continue
                    
                # Create encryption context
                context = {
                    "user_id": getattr(self, "user_id", "system"),
                    "system_component": self.__class__.__name__,
                    "operation": "model_encryption"
                }
                
                # Get PHI category from field metadata if available
                phi_category = PHICategory.SENSITIVE_HEALTH_DATA
                if hasattr(field, "json_schema_extra") and field.json_schema_extra:
                    category_name = field.json_schema_extra.get("phi_category")
                    if category_name:
                        phi_category = PHICategory(category_name)
                
                # Encrypt the field
                encrypted_field = EncryptedField.encrypt(
                    value, 
                    field_name, 
                    context,
                    phi_category
                )
                
                # Replace with encrypted field
                setattr(self, field_name, encrypted_field)
                
        return self
    
    def model_dump(self, decrypt_phi: bool = False, **kwargs):
        """
        Serialize model to dictionary with option to decrypt PHI fields.
        
        Args:
            decrypt_phi: Whether to decrypt PHI fields in output
            **kwargs: Additional arguments to pass to parent model_dump
            
        Returns:
            Dictionary representation of the model
        """
        # Get the base serialized model
        data = super().model_dump(**kwargs)
        
        # Handle encrypted fields
        if decrypt_phi:
            for field_name, field_value in data.items():
                if isinstance(field_value, dict) and "value" in field_value and "encryption_context" in field_value:
                    # This is likely an EncryptedField serialized to dict
                    # Get the actual field from the model
                    model_field = getattr(self, field_name, None)
                    if isinstance(model_field, EncryptedField):
                        # Replace with decrypted value
                        data[field_name] = model_field.decrypt()
        
        return data
