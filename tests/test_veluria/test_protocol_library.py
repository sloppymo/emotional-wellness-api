"""
Test suite for the VELURIA Protocol Library.

This module contains tests for the predefined crisis intervention protocols,
verifying their structure, trigger conditions, and step transitions.
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

logger = get_logger(__name__)

# --- Test Fixtures ---

@pytest.fixture
def protocols():
    """Returns all available protocols for testing."""
    return get_protocol_library()

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
def moderate_risk_assessment() -> RiskAssessment:
    """Create a moderate-risk assessment for testing."""
    return RiskAssessment(
        assessment_id="test-moderate-risk",
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

# --- Test Cases ---

class TestProtocolLibrary:
    """Tests for the protocol library structure and content."""

    def test_protocol_library_not_empty(self, protocols):
        """Test that the protocol library contains protocols."""
        assert len(protocols) > 0
        assert all(isinstance(p, InterventionProtocol) for p in protocols)

    def test_protocol_identifiers_unique(self, protocols):
        """Test that all protocols have unique identifiers."""
        protocol_ids = [p.protocol_id for p in protocols]
        assert len(protocol_ids) == len(set(protocol_ids))

    def test_protocol_structure(self, protocols):
        """Test that all protocols have required fields and valid structure."""
        for protocol in protocols:
            assert protocol.protocol_id
            assert protocol.name
            assert protocol.description
            assert protocol.trigger_conditions
            assert protocol.initial_step_id
            assert protocol.steps
            
            # Verify initial step exists
            assert protocol.initial_step_id in protocol.steps
            
            # Verify all steps have valid next_step_logic
            for step_id, step in protocol.steps.items():
                assert step.step_id == step_id
                assert step.description
                assert step.actions
                assert step.next_step_logic is not None
                
                # Verify all next steps exist
                for next_step in step.next_step_logic.values():
                    if next_step:  # Some steps might not have next steps
                        assert next_step in protocol.steps

class TestHighRiskSuicideProtocol:
    """Tests for the high-risk suicide intervention protocol."""

    def test_protocol_trigger_conditions(self, protocols, high_risk_assessment):
        """Test that the high-risk suicide protocol triggers on appropriate conditions."""
        suicide_protocol = next(p for p in protocols if p.protocol_id == "high_risk_suicide_v1")
        
        # Test matching conditions
        assert suicide_protocol.trigger_conditions["severity"] == "high"
        assert suicide_protocol.trigger_conditions["domain"] == "suicide"
        
        # Test non-matching conditions
        low_risk_assessment = RiskAssessment(
            assessment_id="test-low-risk-1",
            severity=CrisisSeverity.LOW,
            primary_concerns=[RiskDomain.SUICIDE],
            confidence_score=0.7,
            timestamp=datetime.utcnow()
        )
        assert low_risk_assessment.severity.value != suicide_protocol.trigger_conditions["severity"]

    def test_protocol_step_sequence(self, protocols):
        """Test that the high-risk suicide protocol has a valid step sequence."""
        suicide_protocol = next(p for p in protocols if p.protocol_id == "high_risk_suicide_v1")
        
        # Verify critical steps exist
        required_steps = [
            "step_1_acknowledge_and_validate",
            "step_2_assess_immediate_danger",
            "step_3a_emergency_escalation",
            "step_3b_explore_safety",
            "step_4_safety_planning",
            "step_5_reinforce_and_close"
        ]
        for step_id in required_steps:
            assert step_id in suicide_protocol.steps

        # Verify escalation paths
        danger_step = suicide_protocol.steps["step_2_assess_immediate_danger"]
        assert "user_confirms_immediate_danger" in danger_step.next_step_logic
        assert "user_denies_immediate_danger" in danger_step.next_step_logic
        assert "timeout" in danger_step.next_step_logic

    def test_protocol_actions(self, protocols):
        """Test that the high-risk suicide protocol has appropriate actions."""
        suicide_protocol = next(p for p in protocols if p.protocol_id == "high_risk_suicide_v1")
        
        # Verify initial step actions
        initial_step = suicide_protocol.steps[suicide_protocol.initial_step_id]
        assert any(a.action_type == ActionType.LOG_EVENT for a in initial_step.actions)
        assert any(a.action_type == ActionType.SEND_MESSAGE for a in initial_step.actions)
        
        # Verify escalation step actions
        escalation_step = suicide_protocol.steps["step_3a_emergency_escalation"]
        assert any(a.action_type == ActionType.TRIGGER_ESCALATION for a in escalation_step.actions)
        assert any(a.action_type == ActionType.SUGGEST_RESOURCE for a in escalation_step.actions)

class TestModerateSelfHarmProtocol:
    """Tests for the moderate self-harm intervention protocol."""

    def test_protocol_trigger_conditions(self, protocols, moderate_risk_assessment):
        """Test that the moderate self-harm protocol triggers on appropriate conditions."""
        self_harm_protocol = next(p for p in protocols if p.protocol_id == "moderate_self_harm_v1")
        
        # Test matching conditions
        assert self_harm_protocol.trigger_conditions["severity"] == "medium"
        assert self_harm_protocol.trigger_conditions["domain"] == "self_harm"
        
        # Test non-matching conditions
        high_risk_assessment = RiskAssessment(
            assessment_id="test-high-risk-2",
            severity=CrisisSeverity.HIGH,
            primary_concerns=[RiskDomain.SELF_HARM],
            confidence_score=0.9,
            timestamp=datetime.utcnow()
        )
        assert high_risk_assessment.severity.value != self_harm_protocol.trigger_conditions["severity"]

    def test_protocol_step_sequence(self, protocols):
        """Test that the moderate self-harm protocol has a valid step sequence."""
        self_harm_protocol = next(p for p in protocols if p.protocol_id == "moderate_self_harm_v1")
        
        # Verify required steps exist
        required_steps = [
            "step_1_validate_and_open",
            "step_2_introduce_alternatives",
            "step_3_offer_resources",
            "step_4_explore_alternatives"
        ]
        for step_id in required_steps:
            assert step_id in self_harm_protocol.steps

        # Verify step transitions
        initial_step = self_harm_protocol.steps["step_1_validate_and_open"]
        assert "user_responds" in initial_step.next_step_logic
        assert "no_response" in initial_step.next_step_logic

    def test_protocol_actions(self, protocols):
        """Test that the moderate self-harm protocol has appropriate actions."""
        self_harm_protocol = next(p for p in protocols if p.protocol_id == "moderate_self_harm_v1")
        
        # Verify initial step actions
        initial_step = self_harm_protocol.steps["step_1_validate_and_open"]
        assert any(a.action_type == ActionType.SEND_MESSAGE for a in initial_step.actions)
        assert any(a.action_type == ActionType.REQUEST_USER_INPUT for a in initial_step.actions)
        
        # Verify resource step actions
        resource_step = self_harm_protocol.steps["step_3_offer_resources"]
        assert any(a.action_type == ActionType.SEND_MESSAGE for a in resource_step.actions)
        assert any(a.action_type == ActionType.SUGGEST_RESOURCE for a in resource_step.actions) 