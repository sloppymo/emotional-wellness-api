"""
Unit tests for MOSS Adapter

Tests cover:
- MOSS adapter integration with SYLVA framework
- Crisis assessment orchestration
- Prompt generation integration
- Safety status mapping
- Resource recommendation
- Error handling and edge cases
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from src.symbolic.adapters.moss_adapter import MOSSAdapter, MOSSInput, MOSSOutput
from src.symbolic.moss.crisis_classifier import CrisisSeverity, RiskDomain, CrisisContext
from src.symbolic.moss.prompt_templates import PromptCategory, CommunicationChannel
from src.core.symbolic.veluria import VeluriaRequest, VeluriaResponse


class TestMOSSAdapter:
    """Test suite for MOSSAdapter."""
    
    @pytest.fixture
    def moss_adapter(self):
        """Create a MOSSAdapter instance for testing."""
        return MOSSAdapter()
    
    @pytest.fixture
    def sample_moss_input(self):
        """Create a sample MOSSInput for testing."""
        return MOSSInput(
            text="I'm feeling really depressed and don't see the point in continuing",
            user_id="test_user_123",
            session_id="test_session_456",
            context={
                "time_of_day": "late_night",
                "support_available": False,
                "therapy_engaged": False,
                "previous_episodes": 1
            },
            channel=CommunicationChannel.CHAT
        )
    
    @pytest.fixture
    def sample_veluria_request(self):
        """Create a sample VeluriaRequest for testing."""
        return VeluriaRequest(
            user_input="I'm having thoughts of hurting myself",
            session_id="test_session",
            user_id="test_user",
            context={
                "emotional_state": "distressed",
                "support_available": False
            }
        )
    
    @pytest.mark.asyncio
    async def test_assess_crisis_high_severity(self, moss_adapter, sample_moss_input):
        """Test crisis assessment for high severity input."""
        # Update input to be more severe
        sample_moss_input.text = "I want to kill myself and I have a plan"
        
        with patch.multiple(
            moss_adapter,
            _perform_crisis_assessment=AsyncMock(return_value=Mock(
                severity=CrisisSeverity.CRITICAL,
                primary_concerns=["suicide"],
                escalation_required=True,
                confidence=0.9
            )),
            _generate_intervention_prompt=AsyncMock(return_value=Mock(
                generated_content="I'm concerned about your safety.",
                template_id="crisis_intervention"
            )),
            _log_assessment=AsyncMock(return_value="audit_123")
        ):
            result = await moss_adapter.assess_crisis(sample_moss_input)
        
        assert isinstance(result, MOSSOutput)
        assert result.safety_status == "critical"
        assert result.escalation_required == True
        assert result.confidence > 0.8
        assert "suicide" in result.primary_concerns
        assert len(result.intervention_prompt) > 0
    
    @pytest.mark.asyncio
    async def test_assess_crisis_low_severity(self, moss_adapter, sample_moss_input):
        """Test crisis assessment for low severity input."""
        # Update input to be less severe
        sample_moss_input.text = "I'm feeling a bit sad today but I'm okay"
        
        with patch.multiple(
            moss_adapter,
            _perform_crisis_assessment=AsyncMock(return_value=Mock(
                severity=CrisisSeverity.LOW,
                primary_concerns=["mood"],
                escalation_required=False,
                confidence=0.6
            )),
            _generate_intervention_prompt=AsyncMock(return_value=Mock(
                generated_content="It sounds like you're going through a tough time.",
                template_id="supportive_response"
            )),
            _log_assessment=AsyncMock(return_value="audit_124")
        ):
            result = await moss_adapter.assess_crisis(sample_moss_input)
        
        assert isinstance(result, MOSSOutput)
        assert result.safety_status == "low"
        assert result.escalation_required == False
        assert 0.5 <= result.confidence <= 0.7
        assert len(result.intervention_prompt) > 0
    
    @pytest.mark.asyncio
    async def test_emergency_assessment(self, moss_adapter):
        """Test emergency assessment fast-track processing."""
        emergency_input = MOSSInput(
            text="I'm going to kill myself right now",
            user_id="emergency_user",
            session_id="emergency_session",
            context={"time_of_day": "night", "support_available": False},
            channel=CommunicationChannel.CHAT,
            priority="emergency"
        )
        
        with patch.multiple(
            moss_adapter,
            _perform_crisis_assessment=AsyncMock(return_value=Mock(
                severity=CrisisSeverity.IMMINENT,
                primary_concerns=["suicide"],
                escalation_required=True,
                confidence=0.95
            )),
            _generate_intervention_prompt=AsyncMock(return_value=Mock(
                generated_content="I'm very concerned about your immediate safety. Please call 911 or go to your nearest emergency room right now.",
                template_id="emergency_response"
            )),
            _log_assessment=AsyncMock(return_value="audit_emergency")
        ):
            start_time = datetime.now()
            result = await moss_adapter.emergency_assessment(emergency_input)
            processing_time = (datetime.now() - start_time).total_seconds()
        
        assert isinstance(result, MOSSOutput)
        assert result.safety_status == "imminent"
        assert result.escalation_required == True
        assert result.confidence > 0.9
        assert "emergency" in result.intervention_prompt.lower() or "911" in result.intervention_prompt
        
        # Emergency assessment should be fast
        assert processing_time < 5.0  # Should complete within 5 seconds
    
    @pytest.mark.asyncio
    async def test_veluria_integration(self, moss_adapter, sample_veluria_request):
        """Test integration with VELURIA coordinator."""
        with patch.multiple(
            moss_adapter,
            _perform_crisis_assessment=AsyncMock(return_value=Mock(
                severity=CrisisSeverity.MEDIUM,
                primary_concerns=["depression"],
                escalation_required=False,
                confidence=0.7,
                protective_factors=["support_system"]
            )),
            _generate_intervention_prompt=AsyncMock(return_value=Mock(
                generated_content="I hear that you're struggling. Can you tell me more about what's been difficult?",
                template_id="empathetic_response"
            )),
            _log_assessment=AsyncMock(return_value="audit_veluria")
        ):
            result = await moss_adapter.process_veluria_request(sample_veluria_request)
        
        assert isinstance(result, VeluriaResponse)
        assert result.response_text is not None
        assert len(result.response_text) > 0
        assert result.safety_assessment is not None
        assert "medium" in result.safety_assessment["status"].lower()
    
    def test_context_conversion(self, moss_adapter):
        """Test conversion from VELURIA context to MOSS context."""
        veluria_context = {
            "emotional_state": "distressed",
            "time_of_day": "evening",
            "support_available": True,
            "therapy_engaged": False,
            "previous_episodes": 2
        }
        
        moss_context = moss_adapter._convert_context_to_moss(veluria_context)
        
        assert isinstance(moss_context, CrisisContext)
        assert moss_context.time_of_day == "evening"
        assert moss_context.support_available == True
        assert moss_context.therapy_engaged == False
        assert moss_context.previous_episodes == 2
    
    def test_safety_status_mapping(self, moss_adapter):
        """Test mapping from crisis severity to safety status."""
        # Test all severity levels
        severity_mappings = [
            (CrisisSeverity.NONE, "none"),
            (CrisisSeverity.LOW, "low"),
            (CrisisSeverity.MEDIUM, "moderate"),
            (CrisisSeverity.HIGH, "high"),
            (CrisisSeverity.CRITICAL, "critical"),
            (CrisisSeverity.IMMINENT, "imminent")
        ]
        
        for severity, expected_status in severity_mappings:
            status = moss_adapter._map_severity_to_safety_status(severity)
            assert status == expected_status
    
    def test_resource_recommendations(self, moss_adapter):
        """Test resource recommendation based on severity and concerns."""
        # High severity suicide risk
        high_suicide_resources = moss_adapter._get_resource_recommendations(
            severity=CrisisSeverity.HIGH,
            primary_concerns=["suicide"],
            context={"support_available": False}
        )
        
        assert isinstance(high_suicide_resources, list)
        assert len(high_suicide_resources) > 0
        
        # Should include crisis hotlines for suicide risk
        resource_text = " ".join(str(r) for r in high_suicide_resources).lower()
        assert any(keyword in resource_text for keyword in ["crisis", "hotline", "988", "emergency"])
        
        # Medium severity with support available
        medium_support_resources = moss_adapter._get_resource_recommendations(
            severity=CrisisSeverity.MEDIUM,
            primary_concerns=["depression"],
            context={"support_available": True}
        )
        
        assert isinstance(medium_support_resources, list)
        # Should include different resources than high severity
        assert medium_support_resources != high_suicide_resources
    
    @pytest.mark.asyncio
    async def test_processing_statistics(self, moss_adapter):
        """Test processing statistics tracking."""
        # Perform some mock assessments
        sample_input = MOSSInput(
            text="Test input",
            user_id="stats_test",
            session_id="stats_session"
        )
        
        with patch.multiple(
            moss_adapter,
            _perform_crisis_assessment=AsyncMock(return_value=Mock(
                severity=CrisisSeverity.MEDIUM,
                primary_concerns=["test"],
                escalation_required=False,
                confidence=0.7
            )),
            _generate_intervention_prompt=AsyncMock(return_value=Mock(
                generated_content="Test response",
                template_id="test_template"
            )),
            _log_assessment=AsyncMock(return_value="audit_stats")
        ):
            await moss_adapter.assess_crisis(sample_input)
        
        # Get statistics
        stats = moss_adapter.get_processing_statistics()
        
        assert isinstance(stats, dict)
        assert "total_assessments" in stats
        assert "average_processing_time_ms" in stats
        assert "severity_distribution" in stats
        assert "escalation_rate" in stats
        
        assert stats["total_assessments"] > 0
    
    @pytest.mark.asyncio
    async def test_error_handling_assessment_failure(self, moss_adapter, sample_moss_input):
        """Test error handling when crisis assessment fails."""
        with patch.object(
            moss_adapter, 
            '_perform_crisis_assessment', 
            side_effect=Exception("Assessment service unavailable")
        ):
            result = await moss_adapter.assess_crisis(sample_moss_input)
        
        # Should return safe fallback response
        assert isinstance(result, MOSSOutput)
        assert result.safety_status == "unknown"
        assert result.escalation_required == True  # Err on side of caution
        assert "error" in result.processing_metadata
    
    @pytest.mark.asyncio
    async def test_error_handling_prompt_generation_failure(self, moss_adapter, sample_moss_input):
        """Test error handling when prompt generation fails."""
        with patch.multiple(
            moss_adapter,
            _perform_crisis_assessment=AsyncMock(return_value=Mock(
                severity=CrisisSeverity.MEDIUM,
                primary_concerns=["depression"],
                escalation_required=False,
                confidence=0.7
            )),
            _generate_intervention_prompt=AsyncMock(side_effect=Exception("Prompt service unavailable"))
        ):
            result = await moss_adapter.assess_crisis(sample_moss_input)
        
        # Should return assessment with fallback prompt
        assert isinstance(result, MOSSOutput)
        assert result.safety_status == "moderate"
        assert result.intervention_prompt is not None
        assert len(result.intervention_prompt) > 0  # Should have fallback prompt
    
    @pytest.mark.asyncio
    async def test_concurrent_assessments(self, moss_adapter):
        """Test handling of concurrent crisis assessments."""
        inputs = [
            MOSSInput(text=f"Test input {i}", user_id=f"user_{i}", session_id=f"session_{i}")
            for i in range(5)
        ]
        
        with patch.multiple(
            moss_adapter,
            _perform_crisis_assessment=AsyncMock(return_value=Mock(
                severity=CrisisSeverity.LOW,
                primary_concerns=["test"],
                escalation_required=False,
                confidence=0.6
            )),
            _generate_intervention_prompt=AsyncMock(return_value=Mock(
                generated_content="Concurrent test response",
                template_id="concurrent_template"
            )),
            _log_assessment=AsyncMock(return_value="concurrent_audit")
        ):
            # Run assessments concurrently
            tasks = [moss_adapter.assess_crisis(input_item) for input_item in inputs]
            results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        for result in results:
            assert isinstance(result, MOSSOutput)
            assert result.safety_status == "low"
    
    def test_moss_input_validation(self):
        """Test MOSSInput model validation."""
        # Valid input
        valid_input = MOSSInput(
            text="I'm feeling sad",
            user_id="test_user",
            session_id="test_session"
        )
        
        assert valid_input.text == "I'm feeling sad"
        assert valid_input.user_id == "test_user"
        assert valid_input.session_id == "test_session"
        assert valid_input.channel == CommunicationChannel.CHAT  # Default
        
        # Test with custom channel
        voice_input = MOSSInput(
            text="I need help",
            user_id="voice_user",
            session_id="voice_session",
            channel=CommunicationChannel.VOICE
        )
        
        assert voice_input.channel == CommunicationChannel.VOICE
    
    def test_moss_output_validation(self):
        """Test MOSSOutput model validation."""
        # Valid output
        valid_output = MOSSOutput(
            assessment_id="test_assessment_123",
            safety_status="moderate",
            confidence=0.75,
            primary_concerns=["depression", "anxiety"],
            escalation_required=False,
            intervention_prompt="How are you feeling today?",
            resource_recommendations=["Crisis Text Line: Text HOME to 741741"],
            processing_time_ms=150.0
        )
        
        assert valid_output.assessment_id == "test_assessment_123"
        assert valid_output.safety_status == "moderate"
        assert valid_output.confidence == 0.75
        assert len(valid_output.primary_concerns) == 2
        assert not valid_output.escalation_required
        assert valid_output.processing_time_ms == 150.0
    
    @pytest.mark.asyncio
    async def test_audit_logging_integration(self, moss_adapter, sample_moss_input):
        """Test that assessments are properly logged for audit compliance."""
        with patch.multiple(
            moss_adapter,
            _perform_crisis_assessment=AsyncMock(return_value=Mock(
                assessment_id="audit_test_123",
                severity=CrisisSeverity.HIGH,
                primary_concerns=["suicide"],
                escalation_required=True,
                confidence=0.85
            )),
            _generate_intervention_prompt=AsyncMock(return_value=Mock(
                generated_content="Audit test response",
                template_id="audit_template"
            )),
            _log_assessment=AsyncMock(return_value="audit_event_123")
        ) as mocks:
            result = await moss_adapter.assess_crisis(sample_moss_input)
        
        # Verify audit logging was called
        mocks['_log_assessment'].assert_called_once()
        call_args = mocks['_log_assessment'].call_args[1]
        
        assert "assessment_id" in call_args
        assert call_args["severity"] == "high"
        assert call_args["escalation_required"] == True


if __name__ == "__main__":
    pytest.main([__file__]) 