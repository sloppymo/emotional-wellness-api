"""
Tests for the VELURIA intervention protocol.
"""

import pytest
from datetime import datetime
from typing import Dict, Any, Optional

from src.symbolic.moss.processor import get_moss_processor
from src.symbolic.moss import (
    RiskAssessment,
    CrisisSeverity,
    RiskDomain,
    CrisisContext
)
from src.symbolic.veluria.intervention_protocol import (
    InterventionProtocol,
    ProtocolState,
    ProtocolStatus,
    ActionType
)
from structured_logging import get_logger
from unittest.mock import MagicMock, AsyncMock

from src.symbolic.veluria import VeluriaProtocolExecutor, get_protocol_library
from src.symbolic.veluria.intervention_protocol import ProtocolExecutionError
from src.symbolic.veluria.escalation_manager import EscalationManager

logger = get_logger(__name__)

@pytest.fixture
def mock_escalation_manager():
    """Provides a mocked EscalationManager."""
    manager = MagicMock(spec=EscalationManager)
    manager.trigger_escalation = AsyncMock()
    return manager

@pytest.fixture
def protocol_executor(mock_escalation_manager):
    """Provides a VeluriaProtocolExecutor instance with a mock escalation manager."""
    protocols = get_protocol_library()
    return VeluriaProtocolExecutor(protocols=protocols, escalation_manager=mock_escalation_manager)

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
def medium_risk_assessment() -> RiskAssessment:
    """Create a medium-risk assessment for testing."""
    return RiskAssessment(
        assessment_id="test-medium-risk",
        severity=CrisisSeverity.MEDIUM,
        confidence=0.8,
        risk_domains={
            RiskDomain.SUICIDE: 0.5,
            RiskDomain.SELF_HARM: 0.4
        },
        primary_concerns=["depression", "isolation"],
        urgency_score=0.5,
        recommendations=["therapy referral", "support group"],
        escalation_required=False
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

@pytest.mark.asyncio
class TestVeluriaProtocolExecutor:

    def test_initialization(self, protocol_executor):
        assert len(protocol_executor.protocols) > 0
        assert protocol_executor.escalation_manager is not None
        assert "high_risk_suicide_v1" in protocol_executor.protocols

    def test_select_protocol_high_risk(self, protocol_executor, high_risk_assessment):
        protocol = protocol_executor.select_protocol(high_risk_assessment)
        assert protocol is not None
        assert protocol.protocol_id == "high_risk_suicide_v1"

    def test_select_protocol_medium_risk(self, protocol_executor, medium_risk_assessment):
        protocol = protocol_executor.select_protocol(medium_risk_assessment)
        assert protocol is not None
        assert protocol.protocol_id == "moderate_self_harm_v1"

    def test_select_protocol_no_match(self, protocol_executor, low_risk_assessment):
        protocol = protocol_executor.select_protocol(low_risk_assessment)
        assert protocol is None

    async def test_start_protocol_success(self, protocol_executor, high_risk_assessment):
        protocol = protocol_executor.select_protocol(high_risk_assessment)
        state = await protocol_executor.start_protocol(
            protocol=protocol,
            assessment=high_risk_assessment,
            user_id="test-user",
            session_id="test-session"
        )
        assert state is not None
        assert state.protocol_id == "high_risk_suicide_v1"
        assert state.status == ProtocolStatus.ACTIVE
        assert state.current_step_id == "step_1_acknowledge_and_validate"
        assert state.user_id == "test-user"
        assert len(state.history) == 1
        assert "last_step_results" in state.variables
        
        actions = state.variables["last_step_results"]
        assert len(actions) == 3
        assert actions[0]["action"] == "log_event"
        assert actions[1]["action"] == "send_message"
        assert "taking what you're saying very seriously" in actions[1]["content"]

    async def test_start_protocol_invalid_initial_step_raises_error(self, protocol_executor, high_risk_assessment):
        protocol = protocol_executor.select_protocol(high_risk_assessment)
        protocol.initial_step_id = "invalid_step" # Intentionally break the protocol
        
        with pytest.raises(ProtocolExecutionError, match="Initial step 'invalid_step' not found"):
            await protocol_executor.start_protocol(
                protocol=protocol,
                assessment=high_risk_assessment,
                user_id="test-user",
                session_id="test-session"
            )
        
        # Restore for other tests
        protocol.initial_step_id = "step_1_acknowledge_and_validate"
    
    async def test_execute_step_with_escalation(self, protocol_executor, high_risk_assessment, mock_escalation_manager):
        # Start the protocol
        protocol = protocol_executor.select_protocol(high_risk_assessment)
        state = await protocol_executor.start_protocol(
            protocol=protocol,
            assessment=high_risk_assessment,
            user_id="test-user-escalate",
            session_id="test-session-escalate"
        )
        
        # Manually set the step to one that causes escalation
        state.current_step_id = "step_3a_emergency_escalation"
        
        updated_state = await protocol_executor.execute_step(state)
        
        assert updated_state is not None
        mock_escalation_manager.trigger_escalation.assert_called_once()
        
        # Inspect the call arguments
        call_args = mock_escalation_manager.trigger_escalation.call_args
        request_arg = call_args[0][0] # First positional argument of the call
        
        assert request_arg.level.value == "critical"
        assert "User confirmed immediate suicidal intent" in request_arg.reason
        assert request_arg.user_id == "test-user-escalate"
        
        actions = updated_state.variables["last_step_results"]
        assert any(a["action"] == "trigger_escalation" for a in actions)
        assert any(a["status"] == "completed" for a in actions)

    async def test_execute_step_pending_user_input(self, protocol_executor, high_risk_assessment):
        protocol = protocol_executor.select_protocol(high_risk_assessment)
        state = await protocol_executor.start_protocol(
            protocol=protocol,
            assessment=high_risk_assessment,
            user_id="test-user",
            session_id="test-session"
        )
        
        # Manually set to a step that waits for input
        state.current_step_id = "step_2_assess_immediate_danger"
        
        updated_state = await protocol_executor.execute_step(state)
        
        assert updated_state.status == ProtocolStatus.PENDING_USER_RESPONSE
        actions = updated_state.variables["last_step_results"]
        assert len(actions) == 2
        assert actions[0]["action"] == "request_user_input"
        assert actions[0]["status"] == "pending"
        assert actions[1]["action"] == "wait_for_response"
        assert actions[1]["status"] == "pending"

    async def test_execute_invalid_step_raises_error(self, protocol_executor, high_risk_assessment):
        protocol = protocol_executor.select_protocol(high_risk_assessment)
        state = await protocol_executor.start_protocol(
            protocol=protocol,
            assessment=high_risk_assessment,
            user_id="test-user",
            session_id="test-session"
        )
        
        state.current_step_id = "non_existent_step"
        
        with pytest.raises(ProtocolExecutionError, match="Step 'non_existent_step' not found"):
            await protocol_executor.execute_step(state) 