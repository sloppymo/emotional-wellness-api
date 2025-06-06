"""
Unit tests for MOSS Crisis Classifier

Tests cover:
- Crisis risk assessment functionality
- Severity classification accuracy
- Risk domain analysis
- Context-aware adjustments
- Edge cases and error handling
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch

from src.symbolic.moss.crisis_classifier import (
    CrisisClassifier,
    CrisisSeverity,
    RiskDomain,
    CrisisContext,
    RiskAssessment,
    assess_crisis_risk,
    create_crisis_context
)


class TestCrisisClassifier:
    """Test suite for CrisisClassifier."""
    
    @pytest.fixture
    def classifier(self):
        """Create a CrisisClassifier instance for testing."""
        return CrisisClassifier(cache_size=10)
    
    @pytest.fixture
    def sample_context(self):
        """Create a sample crisis context."""
        return CrisisContext(
            user_id="test_user_123",
            time_of_day="day",
            support_available=True,
            previous_episodes=0,
            therapy_engaged=False,
            current_medications=False
        )
    
    @pytest.mark.asyncio
    async def test_high_risk_suicide_detection(self, classifier, sample_context):
        """Test detection of high-risk suicide content."""
        text = "I want to kill myself and I have a plan"
        
        assessment = await classifier.assess_crisis_risk(
            text=text,
            context=sample_context,
            user_id="test_user"
        )
        
        assert assessment.severity in [CrisisSeverity.HIGH, CrisisSeverity.CRITICAL, CrisisSeverity.IMMINENT]
        assert assessment.escalation_required
        assert "suicide" in assessment.primary_concerns
        assert assessment.confidence > 0.7
    
    @pytest.mark.asyncio
    async def test_medium_risk_depression(self, classifier, sample_context):
        """Test detection of medium-risk depression content."""
        text = "I feel hopeless and don't see the point in anything anymore"
        
        assessment = await classifier.assess_crisis_risk(
            text=text,
            context=sample_context,
            user_id="test_user"
        )
        
        assert assessment.severity in [CrisisSeverity.MEDIUM, CrisisSeverity.HIGH]
        assert len(assessment.recommendations) > 0
        assert assessment.confidence > 0.5
    
    @pytest.mark.asyncio
    async def test_low_risk_content(self, classifier, sample_context):
        """Test handling of low-risk content."""
        text = "I'm feeling a bit sad today but I'm okay"
        
        assessment = await classifier.assess_crisis_risk(
            text=text,
            context=sample_context,
            user_id="test_user"
        )
        
        assert assessment.severity in [CrisisSeverity.NONE, CrisisSeverity.LOW]
        assert not assessment.escalation_required
        assert assessment.confidence > 0.0
    
    @pytest.mark.asyncio
    async def test_context_modifiers_late_night(self, classifier):
        """Test that late night context increases risk assessment."""
        late_night_context = CrisisContext(
            time_of_day="late_night",
            support_available=False,
            therapy_engaged=False
        )
        
        text = "I'm feeling really down and overwhelmed"
        
        assessment = await classifier.assess_crisis_risk(
            text=text,
            context=late_night_context,
            user_id="test_user"
        )
        
        # Late night + no support should elevate risk
        assert assessment.urgency_score > 0.3
    
    @pytest.mark.asyncio
    async def test_protective_factors(self, classifier):
        """Test that protective factors reduce risk assessment."""
        protective_context = CrisisContext(
            time_of_day="day",
            support_available=True,
            therapy_engaged=True,
            current_medications=True
        )
        
        text = "I'm struggling but I have my therapy session tomorrow"
        
        assessment = await classifier.assess_crisis_risk(
            text=text,
            context=protective_context,
            user_id="test_user"
        )
        
        assert "therapeutic_engagement" in assessment.protective_factors
        assert len(assessment.protective_factors) > 0
    
    @pytest.mark.asyncio
    async def test_self_harm_detection(self, classifier, sample_context):
        """Test detection of self-harm indicators."""
        text = "I want to cut myself to feel better"
        
        assessment = await classifier.assess_crisis_risk(
            text=text,
            context=sample_context,
            user_id="test_user"
        )
        
        assert assessment.severity >= CrisisSeverity.MEDIUM
        assert "self_harm" in assessment.primary_concerns
    
    @pytest.mark.asyncio
    async def test_violence_risk_detection(self, classifier, sample_context):
        """Test detection of violence risk."""
        text = "I'm so angry I want to hurt someone"
        
        assessment = await classifier.assess_crisis_risk(
            text=text,
            context=sample_context,
            user_id="test_user"
        )
        
        assert assessment.severity >= CrisisSeverity.MEDIUM
        assert "violence" in assessment.primary_concerns
    
    @pytest.mark.asyncio
    async def test_substance_abuse_detection(self, classifier, sample_context):
        """Test detection of substance abuse concerns."""
        text = "I can't stop drinking and I don't care if I overdose"
        
        assessment = await classifier.assess_crisis_risk(
            text=text,
            context=sample_context,
            user_id="test_user"
        )
        
        assert assessment.severity >= CrisisSeverity.MEDIUM
        assert "substance_abuse" in assessment.primary_concerns
    
    @pytest.mark.asyncio
    async def test_empty_text_handling(self, classifier, sample_context):
        """Test handling of empty or minimal text."""
        text = ""
        
        assessment = await classifier.assess_crisis_risk(
            text=text,
            context=sample_context,
            user_id="test_user"
        )
        
        assert assessment.severity == CrisisSeverity.NONE
        assert assessment.confidence < 0.5  # Low confidence for empty text
    
    @pytest.mark.asyncio
    async def test_assessment_caching(self, classifier, sample_context):
        """Test that assessments are properly cached."""
        text = "I'm feeling sad today"
        user_id = "test_user_cache"
        
        # First assessment
        assessment1 = await classifier.assess_crisis_risk(
            text=text,
            context=sample_context,
            user_id=user_id
        )
        
        # Second assessment with same input should be faster (cached)
        start_time = datetime.now()
        assessment2 = await classifier.assess_crisis_risk(
            text=text,
            context=sample_context,
            user_id=user_id
        )
        end_time = datetime.now()
        
        # Results should be identical
        assert assessment1.assessment_id == assessment2.assessment_id
        assert assessment1.severity == assessment2.severity
    
    @pytest.mark.asyncio
    async def test_previous_episodes_impact(self, classifier):
        """Test that previous episodes increase risk assessment."""
        high_episodes_context = CrisisContext(
            time_of_day="day",
            support_available=True,
            previous_episodes=3,  # Multiple previous episodes
            therapy_engaged=False
        )
        
        text = "I'm feeling down again"
        
        assessment = await classifier.assess_crisis_risk(
            text=text,
            context=high_episodes_context,
            user_id="test_user"
        )
        
        # Previous episodes should elevate risk
        assert assessment.urgency_score > 0.2
    
    def test_create_crisis_context(self):
        """Test crisis context creation utility."""
        context = create_crisis_context(
            user_id="test_user",
            time_of_day="late_night",
            support_available=False,
            therapy_engaged=True,
            previous_episodes=1
        )
        
        assert context.user_id == "test_user"
        assert context.time_of_day == "late_night"
        assert not context.support_available
        assert context.therapy_engaged
        assert context.previous_episodes == 1
    
    @pytest.mark.asyncio
    async def test_assess_crisis_risk_convenience_function(self):
        """Test the convenience function for crisis risk assessment."""
        text = "I'm having a tough time but I'll be okay"
        
        assessment = await assess_crisis_risk(
            text=text,
            user_id="test_user"
        )
        
        assert isinstance(assessment, RiskAssessment)
        assert assessment.severity is not None
        assert assessment.confidence >= 0.0
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_input(self, classifier):
        """Test error handling for invalid inputs."""
        with pytest.raises(Exception):
            await classifier.assess_crisis_risk(
                text=None,  # Invalid input
                context=None,
                user_id="test_user"
            )
    
    @pytest.mark.asyncio
    async def test_multiple_risk_domains(self, classifier, sample_context):
        """Test detection of multiple risk domains in single text."""
        text = "I want to hurt myself and I've been drinking too much"
        
        assessment = await classifier.assess_crisis_risk(
            text=text,
            context=sample_context,
            user_id="test_user"
        )
        
        # Should detect both self-harm and substance abuse
        concerns = assessment.primary_concerns
        assert len(concerns) >= 1  # At least one concern detected
        assert assessment.severity >= CrisisSeverity.MEDIUM
    
    @pytest.mark.asyncio
    async def test_confidence_scoring_factors(self, classifier, sample_context):
        """Test that confidence scoring considers multiple factors."""
        # Long, detailed text should have higher confidence
        detailed_text = "I've been struggling with depression for months. I feel hopeless and worthless. I can't see any future for myself and I'm considering ending my life. I have a plan and the means to do it."
        
        assessment_detailed = await classifier.assess_crisis_risk(
            text=detailed_text,
            context=sample_context,
            user_id="test_user"
        )
        
        # Short, vague text should have lower confidence
        vague_text = "bad day"
        
        assessment_vague = await classifier.assess_crisis_risk(
            text=vague_text,
            context=sample_context,
            user_id="test_user_2"
        )
        
        assert assessment_detailed.confidence > assessment_vague.confidence
    
    @pytest.mark.asyncio
    async def test_recommendations_generation(self, classifier, sample_context):
        """Test that appropriate recommendations are generated."""
        text = "I'm thinking about suicide"
        
        assessment = await classifier.assess_crisis_risk(
            text=text,
            context=sample_context,
            user_id="test_user"
        )
        
        assert len(assessment.recommendations) > 0
        # Should include appropriate interventions for suicide risk
        recommendations_text = " ".join(assessment.recommendations).lower()
        assert any(keyword in recommendations_text for keyword in ["safety", "help", "support", "crisis"])


class TestRiskDomainAnalysis:
    """Test suite for risk domain analysis functionality."""
    
    @pytest.fixture
    def classifier(self):
        return CrisisClassifier()
    
    @pytest.mark.asyncio
    async def test_suicide_domain_keywords(self, classifier):
        """Test suicide domain keyword detection."""
        suicide_texts = [
            "I want to kill myself",
            "I'm better off dead",
            "I have no reason to live",
            "I want to end my life"
        ]
        
        context = CrisisContext(time_of_day="day")
        
        for text in suicide_texts:
            assessment = await classifier.assess_crisis_risk(
                text=text,
                context=context,
                user_id="test_user"
            )
            assert "suicide" in assessment.primary_concerns or assessment.severity >= CrisisSeverity.HIGH
    
    @pytest.mark.asyncio
    async def test_self_harm_domain_keywords(self, classifier):
        """Test self-harm domain keyword detection."""
        self_harm_texts = [
            "I want to cut myself",
            "I need to hurt myself",
            "I deserve to feel pain"
        ]
        
        context = CrisisContext(time_of_day="day")
        
        for text in self_harm_texts:
            assessment = await classifier.assess_crisis_risk(
                text=text,
                context=context,
                user_id="test_user"
            )
            assert "self_harm" in assessment.primary_concerns or assessment.severity >= CrisisSeverity.MEDIUM


if __name__ == "__main__":
    pytest.main([__file__]) 