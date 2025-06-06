"""
Tests for the VELURIA adapter.
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
from src.symbolic.adapters.veluria_adapter import VeluriaAdapter
from structured_logging import get_logger

logger = get_logger(__name__)

@pytest.fixture
def veluria_adapter():
    """Provides a fresh instance of the VeluriaAdapter for each test."""
    return VeluriaAdapter()

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

@pytest.mark.asyncio
class TestVeluriaAdapter:

    def test_initialization(self, veluria_adapter):
        assert veluria_adapter.executor is not None
        assert len(veluria_adapter.executor.protocols) > 0
        assert veluria_adapter._active_protocols == {}

    async def test_process_request_starts_new_protocol(self, veluria_adapter, high_risk_assessment):
        """
        Tests that a new protocol is started when a high-risk assessment is processed
        and no protocol is currently active for the user.
        """
        user_id = "new-user-1"
        request = VeluriaAdapterRequest(
            assessment=high_risk_assessment,
            user_id=user_id,
            session_id="session-1"
        )

        response = await veluria_adapter.process_request(request)

        assert response.is_protocol_active is True
        assert response.protocol_state is not None
        assert response.protocol_state.protocol_id == "high_risk_suicide_v1"
        assert response.protocol_state.user_id == user_id
        assert user_id in veluria_adapter._active_protocols

        # Check that the initial actions are returned
        assert len(response.actions) == 3
        assert response.actions[1]["action"] == "send_message"

    async def test_process_request_no_protocol_triggered(self, veluria_adapter, low_risk_assessment):
        """
        Tests that no protocol is started for a low-risk assessment.
        """
        user_id = "new-user-2"
        request = VeluriaAdapterRequest(
            assessment=low_risk_assessment,
            user_id=user_id,
            session_id="session-2"
        )

        response = await veluria_adapter.process_request(request)

        assert response.is_protocol_active is False
        assert response.protocol_state is None
        assert len(response.actions) == 0
        assert user_id not in veluria_adapter._active_protocols

    async def test_process_request_with_active_protocol(self, veluria_adapter, high_risk_assessment):
        """
        Tests that if a protocol is already active, the adapter recognizes it and
        doesn't start a new one.
        """
        user_id = "active-user-1"
        
        # Manually start a protocol to simulate an active state
        start_request = VeluriaAdapterRequest(
            assessment=high_risk_assessment,
            user_id=user_id,
            session_id="session-3a"
        )
        start_response = await veluria_adapter.process_request(start_request)
        original_instance_id = start_response.protocol_state.instance_id
        assert user_id in veluria_adapter._active_protocols

        # Now, process a second request for the same user
        continue_request = VeluriaAdapterRequest(
            assessment=high_risk_assessment, # A new assessment comes in
            user_id=user_id,
            session_id="session-3b",
            user_response="User says something."
        )
        continue_response = await veluria_adapter.process_request(continue_request)

        # The existing protocol state should be returned
        assert continue_response.is_protocol_active is True
        assert continue_response.protocol_state is not None
        assert continue_response.protocol_state.user_id == user_id
        
        # Ensure it's the same protocol instance and not a new one
        assert continue_response.protocol_state.instance_id == original_instance_id
        
        # The current simplified logic doesn't generate new actions on 'continue'
        assert len(continue_response.actions) == 0

    async def test_end_protocol(self, veluria_adapter, high_risk_assessment):
        """
        Tests the end_protocol method.
        """
        user_id = "user-to-end"
        
        # Start a protocol
        request = VeluriaAdapterRequest(
            assessment=high_risk_assessment,
            user_id=user_id,
            session_id="session-4"
        )
        await veluria_adapter.process_request(request)
        assert user_id in veluria_adapter._active_protocols
        
        # Now, end it
        veluria_adapter.end_protocol(user_id)
        assert user_id not in veluria_adapter._active_protocols
        
        # Calling it again for a non-existent user should not fail
        veluria_adapter.end_protocol("non-existent-user")

    def test_get_active_protocol_state(self, veluria_adapter):
        """
        Tests that get_active_protocol_state returns None when no protocol is active.
        """
        state = veluria_adapter.get_active_protocol_state("some-user")
        assert state is None 