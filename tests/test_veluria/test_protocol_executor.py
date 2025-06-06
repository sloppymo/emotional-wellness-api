"""
Test suite for the VELURIA Protocol Executor.

This module contains tests for the core protocol execution logic,
including protocol selection, step execution, and state management.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, Optional

from src.symbolic.veluria import (
    VeluriaProtocolExecutor,
    InterventionProtocol,
    ProtocolStep,
    InterventionAction,
    ActionType,
    ProtocolState,
    ProtocolStatus,
    ProtocolExecutionError
)
from src.symbolic.moss.processor import get_moss_processor
from src.symbolic.moss import (
    RiskAssessment,
    CrisisSeverity,
    RiskDomain,
    CrisisContext
)
from src.symbolic.veluria.escalation_manager import EscalationManager, EscalationLevel
from structured_logging import get_logger

logger = get_logger(__name__)

# --- Test Fixtures ---

@pytest.fixture
def mock_escalation_manager():
    """Creates a mock escalation manager for testing."""
    manager = Mock(spec=EscalationManager)
    manager.trigger_escalation = AsyncMock()
    return manager

@pytest.fixture
def sample_protocol():
    """Creates a sample protocol for testing."""
    return InterventionProtocol(
        protocol_id="test_protocol_v1",
        name="Test Protocol",
        description="A protocol for testing",
        trigger_conditions={"severity": "high", "domain": "suicide"},
        initial_step_id="step_1",
        steps={
            "step_1": ProtocolStep(
                step_id="step_1",
                description="First step",
                actions=[
                    InterventionAction(
                        action_type=ActionType.SEND_MESSAGE,
                        parameters={"content": "Hello, I'm here to help."}
                    ),
                    InterventionAction(
                        action_type=ActionType.REQUEST_USER_INPUT,
                        parameters={"prompt": "How are you feeling?"}
                    )
                ],
                next_step_logic={"user_responds": "step_2", "timeout": "step_escalate"}
            ),
            "step_2": ProtocolStep(
                step_id="step_2",
                description="Second step",
                actions=[
                    InterventionAction(
                        action_type=ActionType.SEND_MESSAGE,
                        parameters={"content": "Thank you for sharing."}
                    )
                ],
                next_step_logic={"default": "step_complete"}
            ),
            "step_escalate": ProtocolStep(
                step_id="step_escalate",
                description="Escalation step",
                actions=[
                    InterventionAction(
                        action_type=ActionType.TRIGGER_ESCALATION,
                        parameters={"level": "high", "reason": "No response from user"}
                    )
                ],
                next_step_logic={}
            ),
            "step_complete": ProtocolStep(
                step_id="step_complete",
                description="Completion step",
                actions=[
                    InterventionAction(
                        action_type=ActionType.LOG_EVENT,
                        parameters={"name": "protocol_completed"}
                    )
                ],
                next_step_logic={}
            )
        }
    )

@pytest.fixture
def high_risk_assessment() -> RiskAssessment:
    """Create a high-risk assessment for testing."""
    return RiskAssessment(
        assessment_id="test-high-risk",
        severity=CrisisSeverity.HIGH,
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
        severity=CrisisSeverity.LOW,
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

# --- Test Cases ---

class TestProtocolSelection:
    """Tests for protocol selection logic."""

    async def test_select_protocol_matching_conditions(self, sample_protocol, high_risk_assessment):
        """Test that a protocol is selected when conditions match."""
        executor = VeluriaProtocolExecutor([sample_protocol])
        selected = executor.select_protocol(high_risk_assessment)
        assert selected is not None
        assert selected.protocol_id == "test_protocol_v1"

    async def test_select_protocol_no_match(self, sample_protocol):
        """Test that no protocol is selected when conditions don't match."""
        assessment = RiskAssessment(
            assessment_id="test-assessment-2",
            severity=CrisisSeverity.LOW,
            primary_concerns=[RiskDomain.ANXIETY],
            confidence_score=0.8,
            timestamp=datetime.utcnow()
        )
        executor = VeluriaProtocolExecutor([sample_protocol])
        selected = executor.select_protocol(assessment)
        assert selected is None

class TestProtocolExecution:
    """Tests for protocol execution logic."""

    async def test_start_protocol_initializes_state(self, sample_protocol, high_risk_assessment, mock_escalation_manager):
        """Test that starting a protocol creates proper initial state."""
        executor = VeluriaProtocolExecutor([sample_protocol], mock_escalation_manager)
        state = await executor.start_protocol(sample_protocol, high_risk_assessment, "user-1", "session-1")
        
        assert state.protocol_id == "test_protocol_v1"
        assert state.user_id == "user-1"
        assert state.session_id == "session-1"
        assert state.status == ProtocolStatus.ACTIVE
        assert state.current_step_id == "step_1"
        assert "assessment" in state.variables
        assert state.expires_at is not None

    async def test_execute_step_runs_actions(self, sample_protocol, high_risk_assessment):
        """Test that executing a step runs all actions in sequence."""
        executor = VeluriaProtocolExecutor([sample_protocol])
        state = await executor.start_protocol(sample_protocol, high_risk_assessment, "user-1", "session-1")
        
        # Verify the first step's actions were executed
        assert len(state.history) == 1
        step_record = state.history[0]
        assert step_record["step_id"] == "step_1"
        assert step_record["status"] == "completed"
        
        # Verify the action results
        results = step_record["results"]
        assert len(results) == 2
        assert results[0]["action"] == "send_message"
        assert results[1]["action"] == "request_user_input"
        assert results[1]["status"] == "pending"  # Waiting for user input

    async def test_execute_step_handles_escalation(self, sample_protocol, high_risk_assessment, mock_escalation_manager):
        """Test that escalation is triggered when appropriate."""
        executor = VeluriaProtocolExecutor([sample_protocol], mock_escalation_manager)
        state = await executor.start_protocol(sample_protocol, high_risk_assessment, "user-1", "session-1")
        
        # Force execution of the escalation step
        state.current_step_id = "step_escalate"
        updated_state = await executor.execute_step(state)
        
        # Verify escalation was triggered
        mock_escalation_manager.trigger_escalation.assert_called_once()
        call_args = mock_escalation_manager.trigger_escalation.call_args[0][0]
        assert call_args.level == EscalationLevel.HIGH
        assert call_args.user_id == "user-1"

    async def test_execute_step_handles_invalid_step(self, sample_protocol, high_risk_assessment):
        """Test that executing an invalid step raises an error."""
        executor = VeluriaProtocolExecutor([sample_protocol])
        state = await executor.start_protocol(sample_protocol, high_risk_assessment, "user-1", "session-1")
        state.current_step_id = "nonexistent_step"
        
        with pytest.raises(ProtocolExecutionError):
            await executor.execute_step(state)

class TestProtocolStateManagement:
    """Tests for protocol state management."""

    async def test_protocol_state_expiration(self, sample_protocol, high_risk_assessment):
        """Test that protocol state expires after the configured time."""
        executor = VeluriaProtocolExecutor([sample_protocol])
        state = await executor.start_protocol(sample_protocol, high_risk_assessment, "user-1", "session-1")
        
        assert state.expires_at is not None
        assert state.expires_at > datetime.utcnow()
        assert state.expires_at <= datetime.utcnow() + timedelta(hours=24)

    async def test_protocol_state_history(self, sample_protocol, high_risk_assessment):
        """Test that protocol state maintains a history of executed steps."""
        executor = VeluriaProtocolExecutor([sample_protocol])
        state = await executor.start_protocol(sample_protocol, high_risk_assessment, "user-1", "session-1")
        
        # Execute a few steps
        state.current_step_id = "step_2"
        state = await executor.execute_step(state)
        state.current_step_id = "step_complete"
        state = await executor.execute_step(state)
        
        assert len(state.history) == 3  # Initial step + 2 executed steps
        assert all(record["status"] == "completed" for record in state.history)
        assert [record["step_id"] for record in state.history] == ["step_1", "step_2", "step_complete"]

    async def test_protocol_state_variables(self, sample_protocol, high_risk_assessment):
        """Test that protocol state variables are properly maintained."""
        executor = VeluriaProtocolExecutor([sample_protocol])
        state = await executor.start_protocol(sample_protocol, high_risk_assessment, "user-1", "session-1")
        
        # Update state variables
        state.current_step_id = "step_2"
        state.variables["custom_var"] = "test_value"
        updated_state = await executor.execute_step(state)
        
        assert "custom_var" in updated_state.variables
        assert updated_state.variables["custom_var"] == "test_value"
        assert "assessment" in updated_state.variables  # Original variables preserved 

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
            "severity": CrisisSeverity.HIGH,
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
            "severity": CrisisSeverity.LOW,
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