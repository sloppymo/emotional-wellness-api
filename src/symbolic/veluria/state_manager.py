"""
VELURIA State Manager

This module handles the persistence and versioning of protocol states,
ensuring that protocol instances can be resumed and tracked across
system restarts and updates.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from uuid import UUID
import asyncio
from enum import Enum

from pydantic import BaseModel, Field, validator, ValidationError
from structured_logging import get_logger

from .intervention_protocol import ProtocolState, ProtocolStatus, InterventionProtocol
from .protocol_library import get_protocol_library

logger = get_logger(__name__)

class ProtocolVersion(str, Enum):
    """Represents the version of a protocol."""
    V1 = "v1"
    V2 = "v2"  # Future version

class StateStorageType(str, Enum):
    """Types of storage backends for protocol states."""
    MEMORY = "memory"
    REDIS = "redis"
    DATABASE = "database"

class StateMetadata(BaseModel):
    """Metadata about a stored protocol state."""
    instance_id: str
    protocol_id: str
    protocol_version: ProtocolVersion
    user_id: str
    session_id: str
    created_at: datetime
    last_updated_at: datetime
    expires_at: datetime
    status: ProtocolStatus
    current_step_id: str
    version_migration_history: List[Dict[str, Any]] = Field(default_factory=list)

class ProtocolStateManager:
    """
    Manages the persistence and versioning of protocol states.
    Handles state storage, retrieval, and migration between protocol versions.
    """

    def __init__(
        self,
        storage_type: StateStorageType = StateStorageType.MEMORY,
        storage_config: Optional[Dict[str, Any]] = None,
        state_ttl: timedelta = timedelta(hours=24)
    ):
        if state_ttl.total_seconds() <= 0:
            raise ValueError("State TTL must be positive")
        
        self.storage_type = storage_type
        self.storage_config = storage_config or {}
        self._validate_storage_config()
        self.state_ttl = state_ttl
        self._storage: Dict[str, Dict[str, Any]] = {}  # In-memory storage
        self._protocols = {p.protocol_id: p for p in get_protocol_library()}
        self._lock = asyncio.Lock()  # For concurrent access
        logger.info(f"ProtocolStateManager initialized with {storage_type} storage")

    def _validate_storage_config(self) -> None:
        """Validate storage configuration parameters."""
        if self.storage_type == StateStorageType.MEMORY:
            valid_params = {"max_states"}
            invalid_params = set(self.storage_config.keys()) - valid_params
            if invalid_params:
                raise ValueError(f"Invalid storage config parameters: {invalid_params}")
            
            if "max_states" in self.storage_config:
                max_states = self.storage_config["max_states"]
                if not isinstance(max_states, int) or max_states <= 0:
                    raise ValueError("max_states must be a positive integer")

    async def store_state(self, state: ProtocolState) -> None:
        """Store a protocol state with metadata."""
        try:
            # Validate state
            if not state.protocol_id or not state.user_id or not state.session_id:
                raise ValueError("Missing required fields in protocol state")
            
            metadata = StateMetadata(
                instance_id=state.instance_id,
                protocol_id=state.protocol_id,
                protocol_version=ProtocolVersion.V1,  # Current version
                user_id=state.user_id,
                session_id=state.session_id,
                created_at=state.started_at,
                last_updated_at=state.last_updated_at,
                expires_at=state.expires_at or (datetime.utcnow() + self.state_ttl),
                status=state.status,
                current_step_id=state.current_step_id
            )

            state_data = {
                "metadata": metadata.model_dump(),
                "state": state.model_dump(),
                "variables": state.variables,
                "history": state.history
            }

            async with self._lock:
                if self.storage_type == StateStorageType.MEMORY:
                    # Check storage limits
                    if "max_states" in self.storage_config:
                        if len(self._storage) >= self.storage_config["max_states"]:
                            # Remove oldest state if at limit
                            oldest_key = min(
                                self._storage.keys(),
                                key=lambda k: self._storage[k]["metadata"]["created_at"]
                            )
                            del self._storage[oldest_key]
                    
                    self._storage[state.instance_id] = state_data
                else:
                    raise NotImplementedError(f"Storage type {self.storage_type} not implemented")

            logger.info(f"Stored state for protocol instance {state.instance_id}")

        except ValidationError as e:
            logger.error(f"Validation error storing state: {e}")
            raise ValueError(f"Invalid state data: {e}")

    async def retrieve_state(self, instance_id: str) -> Optional[ProtocolState]:
        """Retrieve a protocol state by its instance ID."""
        async with self._lock:
            if self.storage_type == StateStorageType.MEMORY:
                state_data = self._storage.get(instance_id)
                if not state_data:
                    return None

                try:
                    # Check if state has expired
                    if datetime.utcnow() > state_data["metadata"]["expires_at"]:
                        await self.delete_state(instance_id)
                        return None

                    # Validate and reconstruct the state
                    state = ProtocolState(**state_data["state"])
                    state.variables = state_data["variables"]
                    state.history = state_data["history"]
                    return state

                except (ValidationError, KeyError) as e:
                    logger.error(f"Error retrieving state {instance_id}: {e}")
                    raise ValueError(f"Invalid state data: {e}")
            else:
                raise NotImplementedError(f"Storage type {self.storage_type} not implemented")

    async def delete_state(self, instance_id: str) -> None:
        """Delete a stored protocol state."""
        if self.storage_type == StateStorageType.MEMORY:
            self._storage.pop(instance_id, None)
            logger.info(f"Deleted state for protocol instance {instance_id}")
        else:
            raise NotImplementedError(f"Storage type {self.storage_type} not implemented")

    async def list_active_states(
        self,
        user_id: Optional[str] = None,
        protocol_id: Optional[str] = None,
        status: Optional[ProtocolStatus] = None
    ) -> List[StateMetadata]:
        """List active protocol states with optional filtering."""
        if self.storage_type == StateStorageType.MEMORY:
            states = []
            for state_data in self._storage.values():
                metadata = StateMetadata(**state_data["metadata"])
                
                # Apply filters
                if user_id and metadata.user_id != user_id:
                    continue
                if protocol_id and metadata.protocol_id != protocol_id:
                    continue
                if status and metadata.status != status:
                    continue
                
                # Check expiration
                if datetime.utcnow() > metadata.expires_at:
                    continue
                
                states.append(metadata)
            return states
        else:
            raise NotImplementedError(f"Storage type {self.storage_type} not implemented")

    async def migrate_state(
        self,
        instance_id: str,
        target_version: ProtocolVersion
    ) -> Optional[ProtocolState]:
        """
        Migrate a protocol state to a new version.
        This handles any necessary data transformations and updates.
        """
        state = await self.retrieve_state(instance_id)
        if not state:
            return None

        current_version = ProtocolVersion.V1  # Get from metadata
        if current_version == target_version:
            return state  # No migration needed

        # Record migration attempt
        migration_record = {
            "from_version": current_version,
            "to_version": target_version,
            "timestamp": datetime.utcnow().isoformat(),
            "success": False
        }

        try:
            async with self._lock:
                # Perform version-specific migrations
                if current_version == ProtocolVersion.V1 and target_version == ProtocolVersion.V2:
                    # Example migration: Add new fields or transform data
                    state.variables["migrated_to_v2"] = True
                    state.variables["migration_timestamp"] = datetime.utcnow().isoformat()
                    
                    # Update protocol if available in new version
                    if state.protocol_id in self._protocols:
                        new_protocol = self._protocols[state.protocol_id]
                        # Handle protocol-specific transformations
                        if state.protocol_id == "crisis_intervention_v1":
                            # Preserve protocol-specific data
                            if "risk_level" in state.variables:
                                state.variables["risk_level_v2"] = state.variables["risk_level"]
                            if "intervention_history" in state.variables:
                                state.variables["intervention_history_v2"] = state.variables["intervention_history"]

                migration_record["success"] = True
                state.variables["version_migration_history"] = state.variables.get(
                    "version_migration_history", []
                ) + [migration_record]

                # Store the migrated state
                await self.store_state(state)
                logger.info(
                    f"Successfully migrated state {instance_id} from {current_version} to {target_version}"
                )
                return state

        except Exception as e:
            logger.error(
                f"Failed to migrate state {instance_id} from {current_version} to {target_version}: {e}"
            )
            migration_record["error"] = str(e)
            state.variables["version_migration_history"] = state.variables.get(
                "version_migration_history", []
            ) + [migration_record]
            await self.store_state(state)
            return None

    async def cleanup_expired_states(self) -> int:
        """Remove expired states and return the count of cleaned states."""
        if self.storage_type == StateStorageType.MEMORY:
            expired_ids = [
                instance_id
                for instance_id, state_data in self._storage.items()
                if datetime.utcnow() > state_data["metadata"]["expires_at"]
            ]
            for instance_id in expired_ids:
                await self.delete_state(instance_id)
            return len(expired_ids)
        else:
            raise NotImplementedError(f"Storage type {self.storage_type} not implemented")

# --- Factory Function ---

def get_state_manager(
    storage_type: StateStorageType = StateStorageType.MEMORY,
    storage_config: Optional[Dict[str, Any]] = None
) -> ProtocolStateManager:
    """Factory function to create a configured state manager."""
    return ProtocolStateManager(storage_type, storage_config) 