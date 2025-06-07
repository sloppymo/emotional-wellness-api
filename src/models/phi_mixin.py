"""
PHI Model Mixin for Automatic Field Encryption

This module provides a Pydantic model mixin that automatically handles
encryption and decryption of PHI fields.
"""

from typing import Any, Dict, Optional, Type, TypeVar, get_type_hints
from pydantic import BaseModel, Field, ConfigDict
from pydantic.fields import FieldInfo

from ..security.phi_encryption import get_phi_encryption_manager

T = TypeVar('T', bound='PHIModelMixin')

class PHIModelMixin(BaseModel):
    """
    Mixin for Pydantic models that need PHI field encryption.
    
    Usage:
        class PatientRecord(PHIModelMixin):
            model_config = ConfigDict(phi_fields=['medical_notes', 'diagnosis'])
            medical_notes: Optional[str] = None
            diagnosis: Optional[str] = None
    """
    
    model_config = ConfigDict(
        phi_fields=[],  # List of field names that contain PHI
        extra='forbid'
    )
    
    def __init__(self, **data: Any):
        """Initialize model with automatic PHI field encryption."""
        # Get PHI fields from model config
        phi_fields = self.model_config.get('phi_fields', [])
        
        # Encrypt PHI fields before model initialization
        for field in phi_fields:
            if field in data and data[field] is not None:
                data[field] = get_phi_encryption_manager().encrypt_field(
                    data[field],
                    field_name=field,
                    context={'model': self.__class__.__name__}
                )
        
        super().__init__(**data)
    
    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Dump model to dict with automatic PHI field decryption."""
        # Get base dict
        data = super().model_dump(**kwargs)
        
        # Get PHI fields from model config
        phi_fields = self.model_config.get('phi_fields', [])
        
        # Decrypt PHI fields
        for field in phi_fields:
            if field in data and data[field] is not None:
                try:
                    data[field] = get_phi_encryption_manager().decrypt_field(
                        data[field],
                        field_name=field,
                        context={'model': self.__class__.__name__}
                    )
                except Exception as e:
                    # Log error but don't expose decryption failure
                    # In production, this would trigger a security alert
                    data[field] = None
        
        return data
    
    @classmethod
    def model_validate(cls: Type[T], obj: Any) -> T:
        """Validate and create model with automatic PHI field encryption."""
        if isinstance(obj, dict):
            # Get PHI fields from model config
            phi_fields = cls.model_config.get('phi_fields', [])
            
            # Encrypt PHI fields before validation
            for field in phi_fields:
                if field in obj and obj[field] is not None:
                    obj[field] = get_phi_encryption_manager().encrypt_field(
                        obj[field],
                        field_name=field,
                        context={'model': cls.__name__}
                    )
        
        return super().model_validate(obj)
    
    def model_copy(self, **kwargs) -> 'PHIModelMixin':
        """Create a copy of the model with PHI fields properly handled."""
        # Get base copy
        copy = super().model_copy(**kwargs)
        
        # Get PHI fields from model config
        phi_fields = self.model_config.get('phi_fields', [])
        
        # Ensure PHI fields are encrypted in the copy
        for field in phi_fields:
            value = getattr(self, field)
            if value is not None:
                # Re-encrypt to ensure proper key usage
                setattr(
                    copy,
                    field,
                    get_phi_encryption_manager().encrypt_field(
                        value,
                        field_name=field,
                        context={'model': self.__class__.__name__, 'operation': 'copy'}
                    )
                )
        
        return copy
    
    @classmethod
    def phi_field(cls, field_type: Type[Any], **field_kwargs) -> Any:
        """
        Helper method to create PHI fields with proper metadata.
        
        Usage:
            class PatientRecord(PHIModelMixin):
                model_config = ConfigDict(phi_fields=['medical_notes'])
                medical_notes: Optional[str] = phi_field(str, description="Patient medical notes")
        """
        # Add field to phi_fields if not already there
        if 'phi_fields' not in cls.model_config:
            cls.model_config['phi_fields'] = []
        
        field_name = field_kwargs.get('alias') or field_kwargs.get('name')
        if field_name and field_name not in cls.model_config['phi_fields']:
            cls.model_config['phi_fields'].append(field_name)
        
        # Add PHI metadata to field
        field_kwargs.setdefault('description', 'Protected Health Information')
        field_kwargs['phi_field'] = True
        
        return Field(field_type, **field_kwargs) 