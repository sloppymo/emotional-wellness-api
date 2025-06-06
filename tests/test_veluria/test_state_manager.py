"""
Test suite for the VELURIA State Manager.

This module contains tests for the state persistence and versioning system,
verifying proper handling of protocol states across system restarts and updates.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import asyncio

from src.symbolic.veluria.state_manager import (
    ProtocolStateManager,
    StateStorageType,
    ProtocolVersion,
    StateMetadata,
    get_state_manager
)
from src.symbolic.veluria import (
    ProtocolState,
    ProtocolStatus,
    InterventionProtocol,
    ProtocolStep,
    InterventionAction,
    ActionType
)

# --- Test Fixtures ---

@pytest.fixture
def state_manager():
    """Creates a state manager instance for testing."""
    return get_state_manager(StateStorageType.MEMORY)

@pytest.fixture
def sample_protocol_state():
    """Creates a sample protocol state for testing."""
    return ProtocolState(
        protocol_id="test_protocol_v1",
        user_id="test-user-123",
        session_id="test-session-456",
        status=ProtocolStatus.ACTIVE,
        current_step_id="step_1",
        variables={
            "user_name": "Test User",
            "last_assessment": {
                "severity": "high",
                "confidence": 0.95
            }
        },
        history=[
            {
                "step_id": "step_1",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "completed"
            }
        ],
        started_at=datetime.utcnow(),
        last_updated_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )

# --- Test Cases ---

class TestStateStorage:
    """Tests for basic state storage operations."""

    async def test_store_and_retrieve_state(self, state_manager, sample_protocol_state):
        """Test that states can be stored and retrieved correctly."""
        # Store the state
        await state_manager.store_state(sample_protocol_state)
        
        # Retrieve the state
        retrieved_state = await state_manager.retrieve_state(sample_protocol_state.instance_id)
        
        assert retrieved_state is not None
        assert retrieved_state.protocol_id == sample_protocol_state.protocol_id
        assert retrieved_state.user_id == sample_protocol_state.user_id
        assert retrieved_state.session_id == sample_protocol_state.session_id
        assert retrieved_state.status == sample_protocol_state.status
        assert retrieved_state.current_step_id == sample_protocol_state.current_step_id
        assert retrieved_state.variables == sample_protocol_state.variables
        assert len(retrieved_state.history) == len(sample_protocol_state.history)

    async def test_delete_state(self, state_manager, sample_protocol_state):
        """Test that states can be deleted."""
        # Store the state
        await state_manager.store_state(sample_protocol_state)
        
        # Verify it exists
        assert await state_manager.retrieve_state(sample_protocol_state.instance_id) is not None
        
        # Delete the state
        await state_manager.delete_state(sample_protocol_state.instance_id)
        
        # Verify it's gone
        assert await state_manager.retrieve_state(sample_protocol_state.instance_id) is None

    async def test_state_expiration(self, state_manager):
        """Test that expired states are handled correctly."""
        # Create a state that's already expired
        expired_state = ProtocolState(
            protocol_id="test_protocol_v1",
            user_id="test-user-123",
            session_id="test-session-456",
            status=ProtocolStatus.ACTIVE,
            current_step_id="step_1",
            started_at=datetime.utcnow() - timedelta(hours=25),
            last_updated_at=datetime.utcnow() - timedelta(hours=25),
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        
        # Store the expired state
        await state_manager.store_state(expired_state)
        
        # Try to retrieve it
        retrieved_state = await state_manager.retrieve_state(expired_state.instance_id)
        assert retrieved_state is None  # Should be automatically deleted

    async def test_list_active_states(self, state_manager, sample_protocol_state):
        """Test that active states can be listed with filtering."""
        # Store a state
        await state_manager.store_state(sample_protocol_state)
        
        # List all active states
        all_states = await state_manager.list_active_states()
        assert len(all_states) == 1
        
        # Filter by user_id
        user_states = await state_manager.list_active_states(user_id="test-user-123")
        assert len(user_states) == 1
        
        # Filter by non-existent user
        no_states = await state_manager.list_active_states(user_id="non-existent")
        assert len(no_states) == 0
        
        # Filter by status
        active_states = await state_manager.list_active_states(status=ProtocolStatus.ACTIVE)
        assert len(active_states) == 1
        
        completed_states = await state_manager.list_active_states(status=ProtocolStatus.COMPLETED)
        assert len(completed_states) == 0

    async def test_concurrent_state_access(self, state_manager):
        """Test that concurrent access to states is handled correctly."""
        # Create multiple states
        states = []
        for i in range(5):
            state = ProtocolState(
                protocol_id=f"test_protocol_v1",
                user_id=f"test-user-{i}",
                session_id=f"test-session-{i}",
                status=ProtocolStatus.ACTIVE,
                current_step_id="step_1"
            )
            states.append(state)
        
        # Store states concurrently
        await asyncio.gather(*[state_manager.store_state(state) for state in states])
        
        # Retrieve states concurrently
        retrieved_states = await asyncio.gather(*[
            state_manager.retrieve_state(state.instance_id) for state in states
        ])
        
        # Verify all states were stored and retrieved correctly
        assert all(state is not None for state in retrieved_states)
        assert len(set(state.instance_id for state in retrieved_states)) == len(states)

    async def test_invalid_state_data(self, state_manager):
        """Test handling of invalid state data."""
        # Test with missing required fields
        with pytest.raises(ValueError):
            await state_manager.store_state(ProtocolState(
                protocol_id="test",  # Missing required fields
                user_id="test",
                session_id="test"
            ))
        
        # Test with invalid state data in storage
        if state_manager.storage_type == StateStorageType.MEMORY:
            # Manually insert invalid data
            state_manager._storage["invalid-state"] = {
                "metadata": {"instance_id": "invalid-state"},  # Incomplete metadata
                "state": {}  # Empty state
            }
            
            # Attempt to retrieve invalid state
            with pytest.raises(ValueError):
                await state_manager.retrieve_state("invalid-state")

class TestStateVersioning:
    """Tests for protocol state versioning and migration."""

    async def test_state_migration(self, state_manager, sample_protocol_state):
        """Test that states can be migrated between versions."""
        # Store initial state
        await state_manager.store_state(sample_protocol_state)
        
        # Migrate to V2
        migrated_state = await state_manager.migrate_state(
            sample_protocol_state.instance_id,
            ProtocolVersion.V2
        )
        
        assert migrated_state is not None
        assert "migrated_to_v2" in migrated_state.variables
        assert "migration_timestamp" in migrated_state.variables
        assert "version_migration_history" in migrated_state.variables
        
        # Verify migration history
        history = migrated_state.variables["version_migration_history"]
        assert len(history) == 1
        assert history[0]["from_version"] == ProtocolVersion.V1
        assert history[0]["to_version"] == ProtocolVersion.V2
        assert history[0]["success"] is True

    async def test_migration_failure_handling(self, state_manager, sample_protocol_state):
        """Test that migration failures are handled gracefully."""
        # Store initial state
        await state_manager.store_state(sample_protocol_state)
        
        # Mock a migration failure
        with patch.object(
            state_manager,
            '_perform_version_migration',
            side_effect=Exception("Migration failed")
        ):
            migrated_state = await state_manager.migrate_state(
                sample_protocol_state.instance_id,
                ProtocolVersion.V2
            )
            
            assert migrated_state is None
            
            # Verify failure was recorded
            state = await state_manager.retrieve_state(sample_protocol_state.instance_id)
            assert state is not None
            history = state.variables.get("version_migration_history", [])
            assert len(history) == 1
            assert history[0]["success"] is False
            assert "error" in history[0]

    async def test_cleanup_expired_states(self, state_manager):
        """Test that expired states are cleaned up properly."""
        # Create and store some expired states
        expired_states = []
        for i in range(3):
            state = ProtocolState(
                protocol_id=f"test_protocol_v1",
                user_id=f"test-user-{i}",
                session_id=f"test-session-{i}",
                status=ProtocolStatus.ACTIVE,
                current_step_id="step_1",
                started_at=datetime.utcnow() - timedelta(hours=25),
                last_updated_at=datetime.utcnow() - timedelta(hours=25),
                expires_at=datetime.utcnow() - timedelta(hours=1)
            )
            await state_manager.store_state(state)
            expired_states.append(state)
        
        # Create and store an active state
        active_state = ProtocolState(
            protocol_id="test_protocol_v1",
            user_id="test-user-active",
            session_id="test-session-active",
            status=ProtocolStatus.ACTIVE,
            current_step_id="step_1",
            started_at=datetime.utcnow(),
            last_updated_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        await state_manager.store_state(active_state)
        
        # Run cleanup
        cleaned_count = await state_manager.cleanup_expired_states()
        assert cleaned_count == 3
        
        # Verify only active state remains
        all_states = await state_manager.list_active_states()
        assert len(all_states) == 1
        assert all_states[0].user_id == "test-user-active"

    async def test_migration_edge_cases(self, state_manager, sample_protocol_state):
        """Test edge cases in state migration."""
        # Test migration to same version
        await state_manager.store_state(sample_protocol_state)
        same_version_state = await state_manager.migrate_state(
            sample_protocol_state.instance_id,
            ProtocolVersion.V1
        )
        assert same_version_state is not None
        assert "version_migration_history" not in same_version_state.variables
        
        # Test migration of non-existent state
        non_existent_state = await state_manager.migrate_state(
            "non-existent-id",
            ProtocolVersion.V2
        )
        assert non_existent_state is None
        
        # Test migration with corrupted state data
        if state_manager.storage_type == StateStorageType.MEMORY:
            # Store state
            await state_manager.store_state(sample_protocol_state)
            
            # Corrupt the state data
            state_manager._storage[sample_protocol_state.instance_id]["state"] = {
                "protocol_id": "test",  # Incomplete state
                "user_id": "test"
            }
            
            # Attempt migration
            with pytest.raises(ValueError):
                await state_manager.migrate_state(
                    sample_protocol_state.instance_id,
                    ProtocolVersion.V2
                )

    async def test_protocol_specific_migration(self, state_manager):
        """Test protocol-specific state transformations during migration."""
        # Create a state with protocol-specific data
        state = ProtocolState(
            protocol_id="crisis_intervention_v1",
            user_id="test-user",
            session_id="test-session",
            status=ProtocolStatus.ACTIVE,
            current_step_id="step_1",
            variables={
                "risk_level": "high",
                "intervention_history": [
                    {"type": "assessment", "timestamp": datetime.utcnow().isoformat()}
                ]
            }
        )
        
        # Store and migrate the state
        await state_manager.store_state(state)
        migrated_state = await state_manager.migrate_state(
            state.instance_id,
            ProtocolVersion.V2
        )
        
        # Verify protocol-specific transformations
        assert migrated_state is not None
        assert "risk_level" in migrated_state.variables
        assert "intervention_history" in migrated_state.variables
        assert len(migrated_state.variables["intervention_history"]) == 1
        
        # Verify migration preserved protocol-specific data
        assert migrated_state.variables["risk_level"] == "high"
        assert "migrated_to_v2" in migrated_state.variables

class TestStateManagerConfiguration:
    """Tests for state manager configuration and initialization."""

    def test_state_manager_initialization(self):
        """Test that state manager can be initialized with different configurations."""
        # Test with memory storage
        memory_manager = get_state_manager(StateStorageType.MEMORY)
        assert memory_manager.storage_type == StateStorageType.MEMORY
        
        # Test with custom TTL
        custom_ttl_manager = ProtocolStateManager(
            storage_type=StateStorageType.MEMORY,
            state_ttl=timedelta(hours=48)
        )
        assert custom_ttl_manager.state_ttl == timedelta(hours=48)
        
        # Test with storage config
        config_manager = get_state_manager(
            StateStorageType.MEMORY,
            storage_config={"max_states": 1000}
        )
        assert config_manager.storage_config["max_states"] == 1000

    @pytest.mark.parametrize("storage_type", [
        StateStorageType.REDIS,
        StateStorageType.DATABASE
    ])
    def test_unsupported_storage_types(self, storage_type):
        """Test that unsupported storage types raise appropriate errors."""
        manager = get_state_manager(storage_type)
        
        with pytest.raises(NotImplementedError):
            # Any operation should raise NotImplementedError
            pytest.mark.asyncio(manager.store_state(ProtocolState(
                protocol_id="test",
                user_id="test",
                session_id="test",
                status=ProtocolStatus.ACTIVE,
                current_step_id="step_1"
            )))

    def test_storage_config_validation(self):
        """Test validation of storage configuration parameters."""
        # Test with invalid TTL
        with pytest.raises(ValueError):
            ProtocolStateManager(
                storage_type=StateStorageType.MEMORY,
                state_ttl=timedelta(seconds=-1)  # Invalid TTL
            )
        
        # Test with invalid storage config
        with pytest.raises(ValueError):
            ProtocolStateManager(
                storage_type=StateStorageType.MEMORY,
                storage_config={"invalid_param": "value"}
            )
        
        # Test with valid but unusual config
        manager = ProtocolStateManager(
            storage_type=StateStorageType.MEMORY,
            state_ttl=timedelta(minutes=30),  # Short TTL
            storage_config={"max_states": 1}  # Small limit
        )
        assert manager.state_ttl == timedelta(minutes=30)
        assert manager.storage_config["max_states"] == 1 