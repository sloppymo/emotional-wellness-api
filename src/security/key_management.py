"""
Key Management Service for PHI Encryption

This module provides a service for managing encryption keys with:
- Integration with secrets managers (AWS KMS, HashiCorp Vault)
- Automatic key rotation
- Key access auditing
- Compliance reporting
"""

import os
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import asyncio
from enum import Enum

import boto3
from botocore.exceptions import ClientError
import hvac
from pydantic import BaseModel, Field

from ..utils.structured_logging import get_logger
from ..config.settings import Settings

logger = get_logger(__name__)

class KeyProvider(str, Enum):
    """Supported key management providers."""
    AWS_KMS = "aws_kms"
    HASHICORP_VAULT = "hashicorp_vault"
    LOCAL = "local"  # For development/testing only

class KeyMetadata(BaseModel):
    """Metadata for an encryption key."""
    key_id: str = Field(..., description="Unique identifier for this key")
    provider: KeyProvider = Field(..., description="Key management provider")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(None, description="Key expiration date")
    is_active: bool = Field(default=True, description="Whether this key is currently active")
    rotation_reason: Optional[str] = Field(None, description="Reason for key rotation if applicable")
    tags: Dict[str, str] = Field(default_factory=dict, description="Additional metadata tags")

class KeyAccessEvent(BaseModel):
    """Record of key access for audit purposes."""
    event_id: str = Field(default_factory=lambda: f"key-access-{os.urandom(8).hex()}")
    key_id: str = Field(..., description="ID of the key that was accessed")
    operation: str = Field(..., description="Operation performed (e.g., 'encrypt', 'decrypt')")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = Field(None, description="User who accessed the key")
    resource_id: Optional[str] = Field(None, description="Resource being encrypted/decrypted")
    success: bool = Field(..., description="Whether the operation succeeded")
    error: Optional[str] = Field(None, description="Error message if operation failed")

class KeyManagementService:
    """
    Service for managing encryption keys with provider integration.
    
    Features:
    - Integration with AWS KMS and HashiCorp Vault
    - Automatic key rotation
    - Key access auditing
    - Compliance reporting
    """
    
    def __init__(self, settings: Settings):
        """Initialize the key management service."""
        self.settings = settings
        self.provider = KeyProvider(settings.KEY_PROVIDER)
        self._client = None
        self._keys: Dict[str, KeyMetadata] = {}
        self._access_log: List[KeyAccessEvent] = []
        
        # Initialize provider client
        self._initialize_provider()
        
        # Start background tasks
        asyncio.create_task(self._rotation_checker())
        asyncio.create_task(self._access_log_cleanup())
    
    def _initialize_provider(self) -> None:
        """Initialize the key management provider client."""
        try:
            if self.provider == KeyProvider.AWS_KMS:
                self._client = boto3.client(
                    'kms',
                    aws_access_key_id=self.settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=self.settings.AWS_SECRET_ACCESS_KEY,
                    region_name=self.settings.AWS_REGION
                )
            elif self.provider == KeyProvider.HASHICORP_VAULT:
                self._client = hvac.Client(
                    url=self.settings.VAULT_URL,
                    token=self.settings.VAULT_TOKEN
                )
            else:
                # Local provider - use file-based storage
                self._client = None
                
            logger.info(
                f"Key management initialized with provider: {self.provider}",
                extra={'provider': self.provider}
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize key management provider: {e}")
            raise

    async def _rotation_checker(self) -> None:
        """Background task to check and rotate keys."""
        while True:
            try:
                # Check for keys that need rotation
                for key_id, metadata in self._keys.items():
                    if (
                        metadata.is_active
                        and metadata.expires_at
                        and metadata.expires_at <= datetime.utcnow() + timedelta(days=7)
                    ):
                        await self.rotate_key(key_id, reason="scheduled_rotation")
                        
                # Sleep for a day
                await asyncio.sleep(86400)
                
            except Exception as e:
                logger.error(f"Key rotation checker failed: {e}")
                await asyncio.sleep(3600)  # Sleep for an hour on error
    
    async def _access_log_cleanup(self) -> None:
        """Background task to clean up old access logs."""
        while True:
            try:
                # Remove logs older than retention period
                cutoff = datetime.utcnow() - timedelta(days=self.settings.KEY_ACCESS_LOG_RETENTION_DAYS)
                self._access_log = [log for log in self._access_log if log.timestamp > cutoff]
                
                # Sleep for a day
                await asyncio.sleep(86400)
                
            except Exception as e:
                logger.error(f"Access log cleanup failed: {e}")
                await asyncio.sleep(3600)  # Sleep for an hour on error
    
    async def create_key(self, tags: Optional[Dict[str, str]] = None) -> KeyMetadata:
        """
        Create a new encryption key.
        
        Args:
            tags: Optional metadata tags for the key
            
        Returns:
            KeyMetadata for the new key
        """
        try:
            if self.provider == KeyProvider.AWS_KMS:
                response = self._client.create_key(
                    Description="PHI encryption key",
                    KeyUsage="ENCRYPT_DECRYPT",
                    Origin="AWS_KMS",
                    Tags=[{"TagKey": k, "TagValue": v} for k, v in (tags or {}).items()]
                )
                key_id = response["KeyMetadata"]["KeyId"]
                metadata = KeyMetadata(
                    key_id=key_id,
                    provider=self.provider,
                    created_at=response["KeyMetadata"]["CreationDate"],
                    expires_at=datetime.utcnow() + timedelta(days=90),
                    tags=tags or {}
                )
            elif self.provider == KeyProvider.HASHICORP_VAULT:
                # Create a new transit key in Vault
                self._client.secrets.transit.create_key(
                    name=f"phi-key-{os.urandom(4).hex()}",
                    exportable=False,
                    allow_plaintext_backup=False,
                    type="aes256-gcm96"
                )
                key_id = f"transit/{os.urandom(4).hex()}"
                metadata = KeyMetadata(
                    key_id=key_id,
                    provider=self.provider,
                    expires_at=datetime.utcnow() + timedelta(days=90),
                    tags=tags or {}
                )
            else:
                # Local provider - generate a key and store metadata
                key_id = f"local-{os.urandom(8).hex()}"
                metadata = KeyMetadata(
                    key_id=key_id,
                    provider=self.provider,
                    expires_at=datetime.utcnow() + timedelta(days=90),
                    tags=tags or {}
                )
            
            self._keys[key_id] = metadata
            logger.info(f"Created new encryption key: {key_id}", extra=metadata.dict())
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to create encryption key: {e}")
            raise
    
    async def rotate_key(self, key_id: str, reason: str = "manual_rotation") -> KeyMetadata:
        """
        Rotate an encryption key.
        
        Args:
            key_id: ID of the key to rotate
            reason: Reason for rotation
            
        Returns:
            Updated KeyMetadata
        """
        try:
            if key_id not in self._keys:
                raise ValueError(f"Key {key_id} not found")
                
            old_metadata = self._keys[key_id]
            
            if self.provider == KeyProvider.AWS_KMS:
                # Schedule deletion of the old key (30-day window)
                self._client.schedule_key_deletion(
                    KeyId=key_id,
                    PendingWindowInDays=30
                )
                # Create a new key
                new_metadata = await self.create_key(tags=old_metadata.tags)
            elif self.provider == KeyProvider.HASHICORP_VAULT:
                # Rotate the transit key (Vault handles re-encryption)
                self._client.secrets.transit.rotate_key(name=key_id.split("/")[-1])
                new_metadata = KeyMetadata(
                    key_id=key_id,
                    provider=self.provider,
                    created_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(days=90),
                    rotation_reason=reason,
                    tags=old_metadata.tags
                )
            else:
                # Local provider - mark old key as inactive and create a new one
                old_metadata.is_active = False
                old_metadata.expires_at = datetime.utcnow() + timedelta(days=30)
                new_metadata = await self.create_key(tags=old_metadata.tags)
            
            logger.info(
                f"Rotated encryption key: {key_id}",
                extra={
                    "old_key_id": key_id,
                    "new_key_id": new_metadata.key_id,
                    "reason": reason
                }
            )
            return new_metadata
            
        except Exception as e:
            logger.error(f"Failed to rotate encryption key {key_id}: {e}")
            raise
    
    def log_key_access(self, event: KeyAccessEvent) -> None:
        """
        Log a key access event for audit.
        
        Args:
            event: KeyAccessEvent to log
        """
        self._access_log.append(event)
        logger.info(
            f"Key access: {event.operation} key {event.key_id}",
            extra=event.dict()
        )
    
    def get_access_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        key_id: Optional[str] = None,
        user_id: Optional[str] = None,
        success_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Generate a report of key access events.
        
        Args:
            start_date: Filter events after this date
            end_date: Filter events before this date
            key_id: Filter events for this key
            user_id: Filter events for this user
            success_only: Only include successful events
            
        Returns:
            List of access event dicts
        """
        filtered = self._access_log
        if start_date:
            filtered = [e for e in filtered if e.timestamp >= start_date]
        if end_date:
            filtered = [e for e in filtered if e.timestamp <= end_date]
        if key_id:
            filtered = [e for e in filtered if e.key_id == key_id]
        if user_id:
            filtered = [e for e in filtered if e.user_id == user_id]
        if success_only:
            filtered = [e for e in filtered if e.success]
        return [e.dict() for e in filtered]

# Global instance
_key_management_service: Optional[KeyManagementService] = None

def get_key_management_service() -> KeyManagementService:
    """Get the global key management service instance."""
    global _key_management_service
    if _key_management_service is None:
        from ..config.settings import get_settings
        _key_management_service = KeyManagementService(get_settings())
    return _key_management_service 