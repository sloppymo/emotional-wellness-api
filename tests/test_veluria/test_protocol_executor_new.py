"""
Tests for the VELURIA protocol executor.
"""

import pytest
from datetime import datetime
from typing import Dict, Any, Optional
from unittest.mock import AsyncMock, MagicMock

from src.symbolic.moss.processor import get_moss_processor
from src.symbolic.moss import (
    RiskAssessment,
    CrisisSeverity,  # Use CrisisSeverity directly
    RiskDomain,
    CrisisContext
)
from src.symbolic.veluria import (
    InterventionProtocol,
    ProtocolStep,
    ProtocolState,
    ProtocolStatus,
    ActionType
)
from structured_logging import get_logger

logger = get_logger(__name__)

@pytest.fixture
def high_risk_assessment() -> RiskAssessment:
    """Create a high-risk assessment for testing."""
    return RiskAssessment(
        assessment_id="test-high-risk",
        severity=CrisisSeverity.HIGH,  # Use CrisisSeverity directly
        confidence=0.85,
        risk_domains={
            RiskDomain.SUICIDE: 0.8,
            RiskDomain.SELF_HARM: 0.7
        },
        primary_concerns=["suicidal ideation", "self-harm"],
        urgency_score=0.75,
        recommendations=["immediate safety check", "crisis hotline"],
        escalation_required=True
    )

@pytest.fixture
def low_risk_assessment() -> RiskAssessment:
    """Create a low-risk assessment for testing."""
    return RiskAssessment(
        assessment_id="test-low-risk",
        severity=CrisisSeverity.LOW,  # Use CrisisSeverity directly
        confidence=0.9,
        risk_domains={
            RiskDomain.SUICIDE: 0.2,
            RiskDomain.SELF_HARM: 0.1
        },
        primary_concerns=["mild anxiety"],
        urgency_score=0.2,
        recommendations=["self-care", "support network"],
        escalation_required=False
    )

@pytest.fixture
def mock_action_handlers() -> Dict[ActionType, AsyncMock]:
    """Create mock action handlers for testing."""
    return {
        ActionType.SEND_MESSAGE: AsyncMock(return_value={"status": "sent"}),
        ActionType.REQUEST_USER_INPUT: AsyncMock(return_value={"status": "pending"}),
        ActionType.SUGGEST_RESOURCE: AsyncMock(return_value={"status": "suggested"}),
        ActionType.INITIATE_SAFETY_PLAN: AsyncMock(return_value={"status": "initiated"}),
        ActionType.TRIGGER_ESCALATION: AsyncMock(return_value={"status": "escalated"}),
        ActionType.LOG_EVENT: AsyncMock(return_value={"status": "logged"}),
        ActionType.UPDATE_STATE: AsyncMock(return_value={"status": "updated"}),
        ActionType.WAIT_FOR_RESPONSE: AsyncMock(return_value={"status": "pending"})
    }

@pytest.mark.asyncio
async def test_protocol_execution_high_risk(
    high_risk_assessment: RiskAssessment,
    mock_action_handlers: Dict[ActionType, AsyncMock]
) -> None:
    """Test protocol execution for high-risk assessment."""
    # Create a test protocol
    protocol = InterventionProtocol(
        protocol_id="test-high-risk-protocol",
        name="High Risk Intervention",
        description="Protocol for high-risk situations",
        trigger_conditions={
            "severity": CrisisSeverity.HIGH,  # Use CrisisSeverity directly
            "domain": "suicide"
        },
        steps={
            "step_1": ProtocolStep(
                step_id="step_1",
                description="Initial safety check",
                actions=[
                    ActionType.SEND_MESSAGE,
                    ActionType.REQUEST_USER_INPUT
                ],
                next_step_logic={
                    "user_confirms": "step_2",
                    "timeout": "escalate"
                }
            )
        },
        initial_step_id="step_1"
    )
    
    # Create protocol executor
    executor = VeluriaProtocolExecutor([protocol])
    
    # Start protocol
    state = await executor.start_protocol(
        protocol=protocol,
        assessment=high_risk_assessment,
        user_id="test-user",
        session_id="test-session"
    )
    
    # Verify state
    assert state.protocol_id == protocol.protocol_id
    assert state.status == ProtocolStatus.ACTIVE
    assert state.current_step_id == "step_1"
    
    # Verify action handlers were called
    assert mock_action_handlers[ActionType.SEND_MESSAGE].called
    assert mock_action_handlers[ActionType.REQUEST_USER_INPUT].called

@pytest.mark.asyncio
async def test_protocol_execution_low_risk(
    low_risk_assessment: RiskAssessment,
    mock_action_handlers: Dict[ActionType, AsyncMock]
) -> None:
    """Test protocol execution for low-risk assessment."""
    # Create a test protocol
    protocol = InterventionProtocol(
        protocol_id="test-low-risk-protocol",
        name="Low Risk Intervention",
        description="Protocol for low-risk situations",
        trigger_conditions={
            "severity": CrisisSeverity.LOW,  # Use CrisisSeverity directly
            "domain": "anxiety"
        },
        steps={
            "step_1": ProtocolStep(
                step_id="step_1",
                description="Initial support",
                actions=[
                    ActionType.SEND_MESSAGE,
                    ActionType.SUGGEST_RESOURCE
                ],
                next_step_logic={
                    "user_confirms": "step_2",
                    "timeout": "complete"
                }
            )
        },
        initial_step_id="step_1"
    )
    
    # Create protocol executor
    executor = VeluriaProtocolExecutor([protocol])
    
    # Start protocol
    state = await executor.start_protocol(
        protocol=protocol,
        assessment=low_risk_assessment,
        user_id="test-user",
        session_id="test-session"
    )
    
    # Verify state
    assert state.protocol_id == protocol.protocol_id
    assert state.status == ProtocolStatus.ACTIVE
    assert state.current_step_id == "step_1"
    
    # Verify action handlers were called
    assert mock_action_handlers[ActionType.SEND_MESSAGE].called
    assert mock_action_handlers[ActionType.SUGGEST_RESOURCE].called 