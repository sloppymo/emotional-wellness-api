"""
Unit tests for PHI logger module.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
from datetime import datetime
import hashlib
import uuid
import json

from structured_logging.phi_logger import (
    PHILogger, get_phi_logger, log_phi_access,
    PHILogEvent, PHILogMetadata, ComplianceFramework
)


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    mock = AsyncMock()
    mock.set = AsyncMock()
    mock.get = AsyncMock(return_value=None)
    mock.keys = AsyncMock(return_value=[])
    return mock


@pytest.fixture
def mock_moss_audit():
    """Mock MOSS audit logger for testing."""
    mock = AsyncMock()
    mock.log_event = AsyncMock()
    return mock


@pytest.fixture
def phi_logger(mock_redis, mock_moss_audit):
    """PHI logger with mocked dependencies for testing."""
    logger = PHILogger()
    logger.redis = mock_redis
    logger.moss_audit = mock_moss_audit
    return logger


@pytest.mark.asyncio
async def test_log_access_basic(phi_logger):
    """Test basic PHI access logging."""
    # Act
    event_id = await phi_logger.log_access(
        user_id="user-123",
        action="view",
        system_component="test_component",
        data_elements=["emotional_state"]
    )
    
    # Assert
    assert event_id is not None
    assert len(event_id) > 0
    phi_logger.moss_audit.log_event.assert_called_once()
    phi_logger.redis.set.assert_called_once()
    
    # Verify the cached data structure
    call_args = phi_logger.redis.set.call_args
    assert call_args is not None
    
    # Key should include event ID
    key = call_args[0][0]
    assert "phi:access:" in key
    assert event_id in key
    
    # Value should be JSON with correct fields
    value = call_args[0][1]
    data = json.loads(value)
    assert data["event_id"] == event_id
    assert data["user_id"] != "user-123"  # Should be hashed
    assert data["action"] == "view"
    assert data["system_component"] == "test_component"
    assert "emotional_state" in data["data_elements"]
    assert "timestamp" in data
    assert "request_id" in data


@pytest.mark.asyncio
async def test_log_access_with_additional_context(phi_logger):
    """Test PHI access logging with additional context."""
    # Act
    event_id = await phi_logger.log_access(
        user_id="user-123",
        action="process",
        system_component="test_component",
        data_elements=["crisis_assessment"],
        additional_context={"session_id": "sess-456", "clinician_id": "clin-789"}
    )
    
    # Assert
    phi_logger.redis.set.assert_called_once()
    
    # Verify context is included
    call_args = phi_logger.redis.set.call_args
    value = call_args[0][1]
    data = json.loads(value)
    assert data["context"]["session_id"] == "sess-456"
    assert data["context"]["clinician_id"] == "clin-789"


@pytest.mark.asyncio
async def test_hash_user_id(phi_logger):
    """Test user ID hashing for privacy."""
    # Act
    user_id = "user-123"
    hashed_id = phi_logger._hash_user_id(user_id)
    
    # Assert
    assert hashed_id != user_id
    assert len(hashed_id) > 0
    
    # Same input should produce same hash
    assert phi_logger._hash_user_id(user_id) == hashed_id
    
    # Different input should produce different hash
    assert phi_logger._hash_user_id("user-456") != hashed_id


@pytest.mark.asyncio
async def test_query_access_logs(phi_logger):
    """Test querying access logs by user ID."""
    # Arrange
    user_id = "user-123"
    hashed_user_id = phi_logger._hash_user_id(user_id)
    
    # Mock Redis to return keys and values
    mock_keys = [f"phi:access:{uuid.uuid4().hex}" for _ in range(3)]
    phi_logger.redis.keys.return_value = mock_keys
    
    # Mock Redis get to return log data for each key
    async def mock_get(key):
        log_data = {
            "event_id": key.split(":")[-1],
            "user_id": hashed_user_id,
            "action": "view",
            "timestamp": datetime.utcnow().isoformat(),
            "system_component": "test",
            "data_elements": ["emotional_state"]
        }
        return json.dumps(log_data)
    
    phi_logger.redis.get = AsyncMock(side_effect=mock_get)
    
    # Act
    logs = await phi_logger.query_access_logs_by_user(user_id)
    
    # Assert
    assert len(logs) == 3
    phi_logger.redis.keys.assert_called_once()
    assert phi_logger.redis.get.call_count == 3


@pytest.mark.asyncio
async def test_fallback_when_redis_unavailable(phi_logger):
    """Test fallback logging when Redis is unavailable."""
    # Arrange
    phi_logger.redis.set.side_effect = Exception("Redis connection error")
    
    # Act - This should not raise an exception
    event_id = await phi_logger.log_access(
        user_id="user-123",
        action="view",
        system_component="test_component",
        data_elements=["emotional_state"]
    )
    
    # Assert - Should still log using MOSS audit logger
    assert event_id is not None
    phi_logger.moss_audit.log_event.assert_called_once()


@pytest.mark.asyncio
async def test_fallback_when_moss_audit_unavailable(phi_logger):
    """Test fallback logging when MOSS audit logger is unavailable."""
    # Arrange
    phi_logger.moss_audit.log_event.side_effect = Exception("MOSS audit service unavailable")
    
    # Act - This should not raise an exception
    event_id = await phi_logger.log_access(
        user_id="user-123",
        action="view",
        system_component="test_component",
        data_elements=["emotional_state"]
    )
    
    # Assert - Should still log to Redis
    assert event_id is not None
    phi_logger.redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_global_log_phi_access_function():
    """Test the global log_phi_access convenience function."""
    # Arrange
    with patch('structured_logging.phi_logger.get_phi_logger') as mock_get_logger:
        mock_logger = AsyncMock()
        mock_logger.log_access = AsyncMock(return_value="test-event-id")
        mock_get_logger.return_value = mock_logger
        
        # Act
        event_id = await log_phi_access(
            user_id="user-123",
            action="view",
            system_component="test_component",
            data_elements=["emotional_state"]
        )
        
        # Assert
        assert event_id == "test-event-id"
        mock_logger.log_access.assert_called_once_with(
            user_id="user-123",
            action="view",
            system_component="test_component",
            data_elements=["emotional_state"],
            additional_context=None
        )


@pytest.mark.asyncio
async def test_get_phi_logger_singleton():
    """Test that get_phi_logger returns a singleton instance."""
    # Act
    logger1 = get_phi_logger()
    logger2 = get_phi_logger()
    
    # Assert
    assert logger1 is logger2  # Same instance
    assert isinstance(logger1, PHILogger)
