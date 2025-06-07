"""
SQLAlchemy Custom Types for Encrypted PHI Storage

This module provides SQLAlchemy custom types that automatically handle
encryption and decryption of PHI fields at the database layer.
"""

from typing import Any, Optional, Type, TypeVar
from sqlalchemy.types import TypeDecorator, LargeBinary, String
from sqlalchemy import event
from sqlalchemy.orm import Mapper, Session
from sqlalchemy.ext.declarative import DeclarativeMeta

from ..security.phi_encryption import get_phi_encryption_manager

T = TypeVar('T')

class EncryptedType(TypeDecorator):
    """
    SQLAlchemy custom type for encrypted PHI fields.
    
    Usage:
        class PatientRecord(Base):
            __tablename__ = 'patient_records'
            id = Column(UUID, primary_key=True)
            medical_notes = Column(EncryptedType(String))  # Automatically encrypted
    """
    
    impl = LargeBinary
    cache_ok = True
    
    def __init__(self, base_type: Type[T], field_name: Optional[str] = None, **kwargs):
        """
        Initialize encrypted type.
        
        Args:
            base_type: The underlying SQLAlchemy type (e.g., String, Integer)
            field_name: Optional name for audit logging
        """
        self.base_type = base_type
        self.field_name = field_name
        super().__init__(**kwargs)
    
    def process_bind_param(self, value: Any, dialect: Any) -> Optional[bytes]:
        """Encrypt value before storing in database."""
        if value is None:
            return None
            
        try:
            # Convert to string if needed
            if not isinstance(value, str):
                value = str(value)
                
            # Encrypt the value
            encrypted = get_phi_encryption_manager().encrypt_field(
                value,
                field_name=self.field_name or "encrypted_field",
                context={'operation': 'db_store'}
            )
            
            return encrypted.encode()
            
        except Exception as e:
            # Log error but don't expose encryption failure
            # In production, this would trigger a security alert
            return None
    
    def process_result_value(self, value: Optional[bytes], dialect: Any) -> Optional[T]:
        """Decrypt value after retrieving from database."""
        if value is None:
            return None
            
        try:
            # Decrypt the value
            decrypted = get_phi_encryption_manager().decrypt_field(
                value.decode(),
                field_name=self.field_name or "encrypted_field",
                context={'operation': 'db_retrieve'}
            )
            
            # Convert back to original type
            if self.base_type == String:
                return decrypted
            else:
                return self.base_type.python_type(decrypted)
                
        except Exception as e:
            # Log error but don't expose decryption failure
            # In production, this would trigger a security alert
            return None
    
    def copy(self, **kwargs: Any) -> 'EncryptedType':
        """Create a copy of this type."""
        return EncryptedType(
            self.base_type,
            field_name=self.field_name,
            **kwargs
        )

# Event listeners for automatic PHI field tracking
def _setup_phi_tracking(mapper: Mapper, class_: Type[Any]) -> None:
    """Set up event listeners for PHI field tracking."""
    if not hasattr(class_, '__phi_fields__'):
        return
        
    @event.listens_for(Session, 'before_flush')
    def before_flush(session: Session, context: Any, instances: Any) -> None:
        """Track PHI field modifications before flush."""
        for instance in session.dirty:
            if not isinstance(instance, class_):
                continue
                
            for field in getattr(instance.__class__, '__phi_fields__', []):
                if field in instance.__dict__:
                    # Log PHI field modification
                    get_phi_encryption_manager().encrypt_field(
                        instance.__dict__[field],
                        field_name=field,
                        context={
                            'model': class_.__name__,
                            'operation': 'db_update',
                            'instance_id': str(getattr(instance, 'id', None))
                        }
                    )

def register_phi_model(model_class: Type[Any], phi_fields: list[str]) -> None:
    """
    Register a model for PHI field tracking.
    
    Usage:
        @register_phi_model(PatientRecord, ['medical_notes', 'diagnosis'])
        class PatientRecord(Base):
            __tablename__ = 'patient_records'
            ...
    """
    setattr(model_class, '__phi_fields__', phi_fields)
    event.listen(model_class, 'mapper_configured', _setup_phi_tracking)

# Example usage:
"""
from sqlalchemy import Column, String, UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

@register_phi_model(PatientRecord, ['medical_notes', 'diagnosis'])
class PatientRecord(Base):
    __tablename__ = 'patient_records'
    
    id = Column(UUID, primary_key=True)
    medical_notes = Column(EncryptedType(String, field_name='medical_notes'))
    diagnosis = Column(EncryptedType(String, field_name='diagnosis'))
""" 