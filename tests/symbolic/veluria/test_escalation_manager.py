"""
Unit tests for the VELURIA Escalation Manager.
"""
import pytest
from unittest.mock import patch, AsyncMock

from src.symbolic.veluria.escalation_manager import (
    EscalationManager,
    EscalationRequest,
    EscalationLevel,
    EscalationTarget,
    ContactMethod
)

@pytest.fixture
def sample_targets():
    """Provides a sample list of escalation targets."""
    return [
        EscalationTarget(
            name="Clinician Email",
            contact_method=ContactMethod.EMAIL,
            contact_details="clinician@test.com",
            triggers_on_levels=[EscalationLevel.HIGH, EscalationLevel.CRITICAL]
        ),
        EscalationTarget(
            name="Supervisor SMS",
            contact_method=ContactMethod.SMS,
            contact_details="1234567890",
            triggers_on_levels=[EscalationLevel.CRITICAL]
        ),
        EscalationTarget(
            name="Low-level Pager",
            contact_method=ContactMethod.PAGER,
            contact_details="pager-id",
            triggers_on_levels=[EscalationLevel.LOW]
        )
    ]

@pytest.fixture
def escalation_manager(sample_targets):
    """Provides an EscalationManager instance with sample targets."""
    return EscalationManager(targets=sample_targets)

@pytest.fixture
def high_level_request():
    """Provides a sample high-level escalation request."""
    return EscalationRequest(
        level=EscalationLevel.HIGH,
        reason="User expressed suicidal ideation without a plan.",
        user_id="user-123",
        session_id="session-abc",
        protocol_instance_id="proto-xyz"
    )

@pytest.fixture
def critical_level_request():
    """Provides a sample critical-level escalation request."""
    return EscalationRequest(
        level=EscalationLevel.CRITICAL,
        reason="User confirmed immediate intent and plan for self-harm.",
        user_id="user-456",
        session_id="session-def",
        protocol_instance_id="proto-uvw"
    )

@pytest.mark.asyncio
@patch('src.symbolic.veluria.escalation_manager.EscalationManager._send_sms', new_callable=AsyncMock)
@patch('src.symbolic.veluria.escalation_manager.EscalationManager._send_email', new_callable=AsyncMock)
async def test_trigger_escalation_high_level(mock_send_email, mock_send_sms, escalation_manager, high_level_request):
    """
    Tests that a HIGH level escalation triggers only the email notification.
    """
    await escalation_manager.trigger_escalation(high_level_request)

    mock_send_email.assert_called_once()
    mock_send_sms.assert_not_called()

    # Check email details
    email_args = mock_send_email.call_args
    to_address = email_args[0][0]
    subject = email_args[0][1]
    
    assert to_address == "clinician@test.com"
    assert "HIGH" in subject
    assert "user-123" in subject

@pytest.mark.asyncio
@patch('src.symbolic.veluria.escalation_manager.EscalationManager._send_sms', new_callable=AsyncMock)
@patch('src.symbolic.veluria.escalation_manager.EscalationManager._send_email', new_callable=AsyncMock)
async def test_trigger_escalation_critical_level(mock_send_email, mock_send_sms, escalation_manager, critical_level_request):
    """
    Tests that a CRITICAL level escalation triggers both email and SMS notifications.
    """
    await escalation_manager.trigger_escalation(critical_level_request)

    mock_send_email.assert_called_once()
    mock_send_sms.assert_called_once()

    # Check email details
    email_args = mock_send_email.call_args
    email_to_address = email_args[0][0]
    assert email_to_address == "clinician@test.com"
    
    # Check SMS details
    sms_args = mock_send_sms.call_args
    sms_to_number = sms_args[0][0]
    sms_message = sms_args[0][1]
    assert sms_to_number == "1234567890"
    assert "CRITICAL" in sms_message
    assert "user-456" in sms_message

@pytest.mark.asyncio
@patch('src.symbolic.veluria.escalation_manager.EscalationManager._send_sms', new_callable=AsyncMock)
@patch('src.symbolic.veluria.escalation_manager.EscalationManager._send_email', new_callable=AsyncMock)
async def test_trigger_escalation_low_level_not_implemented(mock_send_email, mock_send_sms, escalation_manager):
    """
    Tests that a level with an unimplemented contact method does not trigger other notifications
    and does not raise an unhandled exception.
    """
    low_level_request = EscalationRequest(
        level=EscalationLevel.LOW,
        reason="Testing unimplemented method.",
        user_id="user-789",
        session_id="session-ghi",
        protocol_instance_id="proto-opq"
    )
    
    # We expect this to run without errors, logging a warning internally.
    await escalation_manager.trigger_escalation(low_level_request)

    mock_send_email.assert_not_called()
    mock_send_sms.assert_not_called()

@pytest.mark.asyncio
@patch('src.symbolic.veluria.escalation_manager.EscalationManager._send_sms', new_callable=AsyncMock)
@patch('src.symbolic.veluria.escalation_manager.EscalationManager._send_email', new_callable=AsyncMock)
async def test_trigger_escalation_no_matching_target(mock_send_email, mock_send_sms, escalation_manager):
    """
    Tests that an escalation level with no configured target does not trigger any notifications.
    """
    medium_level_request = EscalationRequest(
        level=EscalationLevel.MEDIUM,
        reason="No target for this level.",
        user_id="user-101",
        session_id="session-jkl",
        protocol_instance_id="proto-rst"
    )
    
    await escalation_manager.trigger_escalation(medium_level_request)

    mock_send_email.assert_not_called()
    mock_send_sms.assert_not_called() 