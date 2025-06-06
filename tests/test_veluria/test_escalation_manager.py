"""
Test suite for the VELURIA Escalation Manager.

This module contains tests for the escalation management system,
verifying proper handling of crisis escalations and notifications.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from src.symbolic.veluria.escalation_manager import (
    EscalationManager,
    EscalationTarget,
    EscalationRequest,
    EscalationLevel,
    ContactMethod
)

# --- Test Fixtures ---

@pytest.fixture
def mock_targets():
    """Creates mock escalation targets for testing."""
    return [
        EscalationTarget(
            name="Emergency Services",
            contact_method=ContactMethod.PHONE_CALL,
            contact_info="911",
            triggers_on_levels=[EscalationLevel.CRITICAL],
            description="Emergency services for immediate life-threatening situations"
        ),
        EscalationTarget(
            name="On-Call Clinician",
            contact_method=ContactMethod.SMS,
            contact_info="+15551234567",
            triggers_on_levels=[EscalationLevel.HIGH, EscalationLevel.CRITICAL],
            description="On-call mental health professional"
        ),
        EscalationTarget(
            name="Crisis Team",
            contact_method=ContactMethod.EMAIL,
            contact_info="crisis@example.com",
            triggers_on_levels=[EscalationLevel.MODERATE, EscalationLevel.HIGH],
            description="Crisis intervention team"
        )
    ]

@pytest.fixture
def sample_escalation_request():
    """Creates a sample escalation request for testing."""
    return EscalationRequest(
        level=EscalationLevel.HIGH,
        reason="User expressed immediate suicidal intent",
        user_id="user-123",
        session_id="session-456",
        protocol_instance_id="protocol-789",
        supporting_data={
            "assessment": {
                "severity": "high",
                "confidence": 0.95
            }
        }
    )

# --- Test Cases ---

class TestEscalationTarget:
    """Tests for escalation target configuration."""

    def test_target_creation(self):
        """Test that escalation targets can be created with valid parameters."""
        target = EscalationTarget(
            name="Test Target",
            contact_method=ContactMethod.EMAIL,
            contact_info="test@example.com",
            triggers_on_levels=[EscalationLevel.HIGH],
            description="Test target for unit tests"
        )
        
        assert target.name == "Test Target"
        assert target.contact_method == ContactMethod.EMAIL
        assert target.contact_info == "test@example.com"
        assert EscalationLevel.HIGH in target.triggers_on_levels
        assert target.description == "Test target for unit tests"

    def test_target_validation(self):
        """Test that target creation validates required fields."""
        with pytest.raises(ValueError):
            EscalationTarget(
                name="",  # Empty name
                contact_method=ContactMethod.EMAIL,
                contact_info="test@example.com",
                triggers_on_levels=[EscalationLevel.HIGH],
                description="Test target"
            )
        
        with pytest.raises(ValueError):
            EscalationTarget(
                name="Test Target",
                contact_method=ContactMethod.EMAIL,
                contact_info="",  # Empty contact info
                triggers_on_levels=[EscalationLevel.HIGH],
                description="Test target"
            )
        
        with pytest.raises(ValueError):
            EscalationTarget(
                name="Test Target",
                contact_method=ContactMethod.EMAIL,
                contact_info="test@example.com",
                triggers_on_levels=[],  # Empty trigger levels
                description="Test target"
            )

class TestEscalationManager:
    """Tests for escalation manager functionality."""

    async def test_manager_initialization(self, mock_targets):
        """Test that the escalation manager initializes correctly."""
        manager = EscalationManager(mock_targets)
        assert len(manager.targets) == len(mock_targets)
        assert all(t in manager.targets for t in mock_targets)

    async def test_trigger_escalation_notifies_correct_targets(self, mock_targets, sample_escalation_request):
        """Test that escalation triggers notifications to appropriate targets."""
        # Mock the notification sending method
        with patch.object(EscalationManager, '_send_notification', new_callable=AsyncMock) as mock_send:
            manager = EscalationManager(mock_targets)
            await manager.trigger_escalation(sample_escalation_request)
            
            # Verify that only targets configured for HIGH level were notified
            assert mock_send.call_count == 2  # On-call clinician and crisis team
            notified_targets = {call.args[0].name for call in mock_send.call_args_list}
            assert "Emergency Services" not in notified_targets
            assert "On-Call Clinician" in notified_targets
            assert "Crisis Team" in notified_targets

    async def test_trigger_escalation_critical_level(self, mock_targets):
        """Test that critical level escalations notify all appropriate targets."""
        critical_request = EscalationRequest(
            level=EscalationLevel.CRITICAL,
            reason="Immediate life-threatening situation",
            user_id="user-123",
            session_id="session-456",
            protocol_instance_id="protocol-789",
            supporting_data={}
        )
        
        with patch.object(EscalationManager, '_send_notification', new_callable=AsyncMock) as mock_send:
            manager = EscalationManager(mock_targets)
            await manager.trigger_escalation(critical_request)
            
            # Verify that all targets configured for CRITICAL level were notified
            assert mock_send.call_count == 2  # Emergency services and on-call clinician
            notified_targets = {call.args[0].name for call in mock_send.call_args_list}
            assert "Emergency Services" in notified_targets
            assert "On-Call Clinician" in notified_targets
            assert "Crisis Team" not in notified_targets

    async def test_trigger_escalation_handles_failures(self, mock_targets, sample_escalation_request):
        """Test that the manager handles notification failures gracefully."""
        # Mock _send_notification to fail for one target
        async def mock_send_notification(target, request):
            if target.name == "On-Call Clinician":
                raise Exception("Failed to send SMS")
            return True
        
        with patch.object(EscalationManager, '_send_notification', side_effect=mock_send_notification):
            manager = EscalationManager(mock_targets)
            # Should not raise an exception
            await manager.trigger_escalation(sample_escalation_request)
            # Verify that other targets were still notified
            assert len(manager._send_notification.call_args_list) == 2

    async def test_trigger_escalation_logs_events(self, mock_targets, sample_escalation_request):
        """Test that escalation events are properly logged."""
        with patch('structured_logging.get_logger') as mock_logger:
            logger = Mock()
            mock_logger.return_value = logger
            
            manager = EscalationManager(mock_targets)
            await manager.trigger_escalation(sample_escalation_request)
            
            # Verify that appropriate log messages were created
            assert logger.warning.call_count >= 1  # Initial escalation trigger
            assert logger.info.call_count >= 2    # Target notifications
            assert any("Escalation triggered" in call.args[0] for call in logger.warning.call_args_list)

class TestEscalationLevels:
    """Tests for escalation level handling."""

    def test_level_comparison(self):
        """Test that escalation levels can be compared for severity."""
        assert EscalationLevel.CRITICAL > EscalationLevel.HIGH
        assert EscalationLevel.HIGH > EscalationLevel.MODERATE
        assert EscalationLevel.MODERATE > EscalationLevel.LOW
        
        # Test level ordering
        levels = [EscalationLevel.LOW, EscalationLevel.MODERATE, EscalationLevel.HIGH, EscalationLevel.CRITICAL]
        assert levels == sorted(levels)

    def test_level_string_conversion(self):
        """Test that escalation levels can be converted to and from strings."""
        level = EscalationLevel.HIGH
        assert str(level) == "high"
        assert EscalationLevel("high") == level
        
        with pytest.raises(ValueError):
            EscalationLevel("invalid_level") 