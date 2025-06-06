import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src')))

"""
Common test fixtures and configuration for the VELURIA test suite.

This module provides shared fixtures and configuration that can be used
across all VELURIA test modules.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from src.symbolic.veluria import (
    VeluriaProtocolExecutor,
    InterventionProtocol,
    ProtocolStep,
    InterventionAction,
    ActionType,
    ProtocolState,
    ProtocolStatus
)
from src.symbolic.moss.processor import get_moss_processor
from src.symbolic.moss import (
    RiskAssessment,
    CrisisSeverity,
    RiskDomain,
    CrisisContext
)
from src.symbolic.veluria.escalation_manager import (
    EscalationManager,
    EscalationTarget,
    EscalationRequest,
    EscalationLevel,
    ContactMethod
)
from structured_logging import get_logger

logger = get_logger(__name__)

# --- Async Test Configuration ---

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# --- Common Test Data ---

@pytest.fixture
def base_protocol_variables() -> Dict[str, Any]:
    """Common variables used across protocol tests."""
    return {
        "user_id": "test-user-123",
        "session_id": "test-session-456",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": "test",
        "version": "1.0.0"
    }

@pytest.fixture
def mock_risk_assessments() -> Dict[str, RiskAssessment]:
    """A collection of risk assessments for testing different scenarios."""
    return {
        "high_risk_suicide": RiskAssessment(
            assessment_id="test-high-suicide-1",
            severity=CrisisSeverity.HIGH,
            primary_concerns=[RiskDomain.SUICIDE],
            confidence_score=0.95,
            timestamp=datetime.utcnow()
        ),
        "moderate_self_harm": RiskAssessment(
            assessment_id="test-moderate-self-harm-1",
            severity=CrisisSeverity.MODERATE,
            primary_concerns=[RiskDomain.SELF_HARM],
            confidence_score=0.85,
            timestamp=datetime.utcnow()
        ),
        "low_anxiety": RiskAssessment(
            assessment_id="test-low-anxiety-1",
            severity=CrisisSeverity.LOW,
            primary_concerns=[RiskDomain.ANXIETY],
            confidence_score=0.75,
            timestamp=datetime.utcnow()
        )
    }

# --- Protocol Test Fixtures ---

@pytest.fixture
def sample_protocol_steps() -> Dict[str, ProtocolStep]:
    """A collection of reusable protocol steps for testing."""
    return {
        "initial_contact": ProtocolStep(
            step_id="step_initial_contact",
            description="Initial contact and validation step",
            actions=[
                InterventionAction(
                    action_type=ActionType.SEND_MESSAGE,
                    parameters={"content": "Hello, I'm here to help. How are you feeling?"}
                ),
                InterventionAction(
                    action_type=ActionType.LOG_EVENT,
                    parameters={"name": "protocol_started"}
                )
            ],
            next_step_logic={"default": "step_assessment"}
        ),
        "assessment": ProtocolStep(
            step_id="step_assessment",
            description="Assessment and risk evaluation step",
            actions=[
                InterventionAction(
                    action_type=ActionType.REQUEST_USER_INPUT,
                    parameters={"prompt": "Can you tell me more about what's bringing you here today?"}
                )
            ],
            next_step_logic={
                "high_risk": "step_escalate",
                "moderate_risk": "step_support",
                "low_risk": "step_resources"
            }
        ),
        "escalation": ProtocolStep(
            step_id="step_escalate",
            description="Emergency escalation step",
            actions=[
                InterventionAction(
                    action_type=ActionType.TRIGGER_ESCALATION,
                    parameters={"level": "high", "reason": "High risk situation detected"}
                )
            ],
            next_step_logic={}
        )
    }

@pytest.fixture
def test_protocol(sample_protocol_steps) -> InterventionProtocol:
    """A complete test protocol for general testing."""
    return InterventionProtocol(
        protocol_id="test_protocol_v1",
        name="Test Protocol",
        description="A protocol for testing the VELURIA system",
        trigger_conditions={"severity": "high", "domain": "suicide"},
        initial_step_id="step_initial_contact",
        steps=sample_protocol_steps
    )

# --- Escalation Test Fixtures ---

@pytest.fixture
def mock_escalation_targets() -> List[EscalationTarget]:
    """A collection of escalation targets for testing."""
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
def mock_escalation_manager(mock_escalation_targets) -> EscalationManager:
    """A configured escalation manager for testing."""
    return EscalationManager(mock_escalation_targets)

# --- Protocol Executor Fixtures ---

@pytest.fixture
def protocol_executor(test_protocol, mock_escalation_manager) -> VeluriaProtocolExecutor:
    """A configured protocol executor for testing."""
    return VeluriaProtocolExecutor([test_protocol], mock_escalation_manager)

@pytest.fixture
async def active_protocol_state(protocol_executor, test_protocol, mock_risk_assessments) -> ProtocolState:
    """An active protocol state for testing protocol execution."""
    return await protocol_executor.start_protocol(
        test_protocol,
        mock_risk_assessments["high_risk_suicide"],
        "test-user-123",
        "test-session-456"
    )

# --- Mock Handlers ---

@pytest.fixture
def mock_action_handlers():
    """Mock handlers for protocol actions."""
    return {
        ActionType.SEND_MESSAGE: AsyncMock(return_value={"status": "completed"}),
        ActionType.REQUEST_USER_INPUT: AsyncMock(return_value={"status": "pending"}),
        ActionType.TRIGGER_ESCALATION: AsyncMock(return_value={"status": "completed"}),
        ActionType.LOG_EVENT: AsyncMock(return_value={"status": "completed"}),
        ActionType.SUGGEST_RESOURCE: AsyncMock(return_value={"status": "completed"}),
        ActionType.INITIATE_SAFETY_PLAN: AsyncMock(return_value={"status": "pending"}),
        ActionType.UPDATE_STATE: AsyncMock(return_value={"status": "completed"}),
        ActionType.WAIT_FOR_RESPONSE: AsyncMock(return_value={"status": "pending"})
    }

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