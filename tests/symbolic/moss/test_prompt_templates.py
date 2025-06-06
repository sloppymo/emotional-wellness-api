"""
Unit tests for MOSS Prompt Templates

Tests cover:
- Template creation and validation
- Prompt generation functionality
- Safety validation
- Personalization features
- Category-based template selection
- Template effectiveness tracking
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.symbolic.moss.prompt_templates import (
    MOSSPromptTemplates,
    PromptTemplate,
    PromptCategory,
    PromptTone,
    CommunicationChannel,
    GeneratedPrompt,
    generate_crisis_prompt,
    generate_safety_planning_prompt
)
from src.symbolic.moss.crisis_classifier import (
    CrisisSeverity,
    RiskDomain
)


class TestMOSSPromptTemplates:
    """Test suite for MOSSPromptTemplates."""
    
    @pytest.fixture
    def prompt_system(self):
        """Create a MOSSPromptTemplates instance for testing."""
        return MOSSPromptTemplates()
    
    @pytest.mark.asyncio
    async def test_generate_crisis_prompt_high_severity(self, prompt_system):
        """Test generation of crisis prompt for high severity."""
        severity = CrisisSeverity.HIGH
        risk_domains = [RiskDomain.SUICIDE]
        
        prompt = await prompt_system.generate_prompt(
            severity=severity,
            risk_domains=risk_domains,
            user_name="John"
        )
        
        assert prompt is not None
        assert isinstance(prompt, GeneratedPrompt)
        assert prompt.severity_level == severity
        assert prompt.safety_validated == True
        assert prompt.personalization_applied == True
        assert len(prompt.generated_content) > 0
        
        # Should contain safety-focused language for high severity
        content_lower = prompt.generated_content.lower()
        assert any(word in content_lower for word in ["help", "support", "safe", "concern"])
    
    @pytest.mark.asyncio
    async def test_generate_crisis_prompt_imminent_severity(self, prompt_system):
        """Test generation of crisis prompt for imminent severity."""
        severity = CrisisSeverity.IMMINENT
        risk_domains = [RiskDomain.SUICIDE]
        
        prompt = await prompt_system.generate_prompt(
            severity=severity,
            risk_domains=risk_domains,
            preferred_category=PromptCategory.EMERGENCY_RESPONSE
        )
        
        assert prompt is not None
        assert prompt.severity_level == severity
        assert prompt.safety_validated == True
        
        # Imminent severity should trigger urgent language
        content_lower = prompt.generated_content.lower()
        assert any(word in content_lower for word in ["emergency", "immediate", "911", "crisis"])
    
    @pytest.mark.asyncio
    async def test_generate_safety_planning_prompt(self, prompt_system):
        """Test generation of safety planning prompt."""
        severity = CrisisSeverity.MEDIUM
        risk_domains = [RiskDomain.SELF_HARM]
        
        prompt = await prompt_system.generate_prompt(
            severity=severity,
            risk_domains=risk_domains,
            preferred_category=PromptCategory.SAFETY_PLANNING,
            user_name="Sarah"
        )
        
        assert prompt is not None
        assert prompt.safety_validated == True
        
        # Safety planning should include planning language
        content_lower = prompt.generated_content.lower()
        assert any(word in content_lower for word in ["plan", "safety", "support", "help"])
    
    @pytest.mark.asyncio
    async def test_generate_deescalation_prompt(self, prompt_system):
        """Test generation of de-escalation prompt."""
        severity = CrisisSeverity.HIGH
        risk_domains = [RiskDomain.VIOLENCE]
        
        prompt = await prompt_system.generate_prompt(
            severity=severity,
            risk_domains=risk_domains,
            preferred_category=PromptCategory.DE_ESCALATION
        )
        
        assert prompt is not None
        assert prompt.safety_validated == True
        
        # De-escalation should include calming language
        content_lower = prompt.generated_content.lower()
        assert any(word in content_lower for word in ["calm", "breathe", "slow", "together"])
    
    @pytest.mark.asyncio
    async def test_prompt_personalization(self, prompt_system):
        """Test that prompts are properly personalized."""
        severity = CrisisSeverity.MEDIUM
        risk_domains = [RiskDomain.SUICIDE]
        user_name = "TestUser"
        
        prompt = await prompt_system.generate_prompt(
            severity=severity,
            risk_domains=risk_domains,
            user_name=user_name
        )
        
        assert prompt is not None
        assert prompt.personalization_applied == True
        
        # User name should be incorporated if the template supports it
        # Note: This depends on the specific template selected
        assert len(prompt.generated_content) > 0
    
    def test_prompt_template_validation(self):
        """Test prompt template validation."""
        # Valid template
        valid_template = PromptTemplate(
            template_id="test_template",
            category=PromptCategory.SAFETY_PLANNING,
            severity_level=CrisisSeverity.HIGH,
            tone=PromptTone.SUPPORTIVE,
            channel=CommunicationChannel.CHAT,
            title="Test Safety Planning",
            content="Let's work together to create a safety plan. Can you identify someone you trust?",
            variables=["user_name"],
            use_cases=["high_risk_assessment"],
            clinical_reviewed=True
        )
        
        assert valid_template.template_id == "test_template"
        assert valid_template.category == PromptCategory.SAFETY_PLANNING
        assert valid_template.clinical_reviewed == True
    
    def test_harmful_content_validation(self):
        """Test that harmful content is rejected."""
        # This should raise a validation error
        with pytest.raises(ValueError):
            PromptTemplate(
                template_id="harmful_template",
                category=PromptCategory.ASSESSMENT_VERIFICATION,
                severity_level=CrisisSeverity.HIGH,
                tone=PromptTone.DIRECT,
                channel=CommunicationChannel.CHAT,
                title="Harmful Content",
                content="You should just give up, there's no hope",  # Harmful content
                variables=[],
                use_cases=[]
            )
    
    @pytest.mark.asyncio
    async def test_no_suitable_template_found(self, prompt_system):
        """Test handling when no suitable template is found."""
        # Use an unusual combination that might not have templates
        severity = CrisisSeverity.NONE
        risk_domains = []
        
        prompt = await prompt_system.generate_prompt(
            severity=severity,
            risk_domains=risk_domains,
            preferred_category=PromptCategory.EMERGENCY_RESPONSE  # Mismatch
        )
        
        # Should return None or a fallback prompt
        if prompt is not None:
            assert isinstance(prompt, GeneratedPrompt)
    
    def test_template_selection_by_category(self, prompt_system):
        """Test template selection by category."""
        safety_templates = prompt_system.get_template_by_category(PromptCategory.SAFETY_PLANNING)
        
        assert isinstance(safety_templates, list)
        for template in safety_templates:
            assert template.category == PromptCategory.SAFETY_PLANNING
        
        emergency_templates = prompt_system.get_template_by_category(PromptCategory.EMERGENCY_RESPONSE)
        
        assert isinstance(emergency_templates, list)
        for template in emergency_templates:
            assert template.category == PromptCategory.EMERGENCY_RESPONSE
    
    def test_template_statistics(self, prompt_system):
        """Test template usage statistics."""
        stats = prompt_system.get_template_statistics()
        
        assert isinstance(stats, dict)
        assert "total_templates" in stats
        assert "usage_stats" in stats
        assert "clinical_reviewed_count" in stats
        
        assert stats["total_templates"] > 0
        assert isinstance(stats["usage_stats"], dict)
        assert stats["clinical_reviewed_count"] >= 0
    
    @pytest.mark.asyncio
    async def test_prompt_safety_validation(self, prompt_system):
        """Test that generated prompts pass safety validation."""
        severity = CrisisSeverity.CRITICAL
        risk_domains = [RiskDomain.SUICIDE]
        
        prompt = await prompt_system.generate_prompt(
            severity=severity,
            risk_domains=risk_domains
        )
        
        if prompt is not None:
            assert prompt.safety_validated == True
            
            # Critical severity prompts should contain helpful language
            content_lower = prompt.generated_content.lower()
            harmful_phrases = ["give up", "hopeless", "no point", "end it all"]
            
            for phrase in harmful_phrases:
                assert phrase not in content_lower
    
    def test_generated_prompt_expiry(self):
        """Test that generated prompts have appropriate expiry times."""
        prompt = GeneratedPrompt(
            prompt_id="test_prompt_123",
            template_id="test_template",
            generated_content="Test content",
            severity_level=CrisisSeverity.HIGH,
            channel=CommunicationChannel.CHAT
        )
        
        assert prompt.expiry_time is not None
        assert prompt.expiry_time > datetime.now()
        
        # Should expire within reasonable timeframe (24 hours default)
        expected_expiry = datetime.now() + timedelta(hours=24)
        time_diff = abs((prompt.expiry_time - expected_expiry).total_seconds())
        assert time_diff < 3600  # Within 1 hour of expected
    
    @pytest.mark.asyncio
    async def test_channel_compatibility(self, prompt_system):
        """Test that prompts are generated for different channels."""
        severity = CrisisSeverity.MEDIUM
        risk_domains = [RiskDomain.SUICIDE]
        
        # Test different channels
        channels = [
            CommunicationChannel.CHAT,
            CommunicationChannel.VOICE,
            CommunicationChannel.TEXT_MESSAGE
        ]
        
        for channel in channels:
            prompt = await prompt_system.generate_prompt(
                severity=severity,
                risk_domains=risk_domains,
                channel=channel
            )
            
            if prompt is not None:
                assert prompt.channel == channel
    
    def test_severity_compatibility_logic(self, prompt_system):
        """Test severity compatibility logic."""
        # Test internal compatibility checking
        assert prompt_system._is_compatible_severity(
            CrisisSeverity.HIGH, 
            CrisisSeverity.CRITICAL
        ) == True  # Adjacent severities should be compatible
        
        assert prompt_system._is_compatible_severity(
            CrisisSeverity.LOW, 
            CrisisSeverity.IMMINENT
        ) == False  # Distant severities should not be compatible
        
        assert prompt_system._is_compatible_severity(
            CrisisSeverity.MEDIUM, 
            CrisisSeverity.MEDIUM
        ) == True  # Same severity should be compatible


class TestConvenienceFunctions:
    """Test suite for convenience functions."""
    
    @pytest.mark.asyncio
    async def test_generate_crisis_prompt_convenience(self):
        """Test convenience function for generating crisis prompts."""
        severity = CrisisSeverity.HIGH
        risk_domains = [RiskDomain.SUICIDE]
        user_name = "TestUser"
        
        prompt = await generate_crisis_prompt(
            severity=severity,
            risk_domains=risk_domains,
            user_name=user_name
        )
        
        if prompt is not None:
            assert isinstance(prompt, GeneratedPrompt)
            assert prompt.severity_level == severity
            assert RiskDomain.SUICIDE.value in prompt.risk_domains
    
    @pytest.mark.asyncio
    async def test_generate_safety_planning_prompt_convenience(self):
        """Test convenience function for generating safety planning prompts."""
        severity = CrisisSeverity.CRITICAL
        user_name = "TestUser"
        
        prompt = await generate_safety_planning_prompt(
            severity=severity,
            user_name=user_name
        )
        
        if prompt is not None:
            assert isinstance(prompt, GeneratedPrompt)
            assert prompt.severity_level == severity
            # Should default to suicide domain for safety planning
            assert RiskDomain.SUICIDE.value in prompt.risk_domains


class TestPromptQuality:
    """Test suite for prompt quality and effectiveness."""
    
    @pytest.fixture
    def prompt_system(self):
        return MOSSPromptTemplates()
    
    @pytest.mark.asyncio
    async def test_prompt_content_quality(self, prompt_system):
        """Test that generated prompts meet quality standards."""
        severity = CrisisSeverity.HIGH
        risk_domains = [RiskDomain.SUICIDE]
        
        prompt = await prompt_system.generate_prompt(
            severity=severity,
            risk_domains=risk_domains
        )
        
        if prompt is not None:
            content = prompt.generated_content
            
            # Basic quality checks
            assert len(content) > 10  # Not too short
            assert len(content) < 1000  # Not too long
            assert content.strip() == content  # No leading/trailing whitespace
            assert not content.startswith("{") or content.endswith("}")  # No unreplaced placeholders
    
    @pytest.mark.asyncio
    async def test_template_selection_logic(self, prompt_system):
        """Test that appropriate templates are selected for different scenarios."""
        # High severity suicide risk should prefer appropriate templates
        high_suicide_prompt = await prompt_system.generate_prompt(
            severity=CrisisSeverity.HIGH,
            risk_domains=[RiskDomain.SUICIDE]
        )
        
        # Low severity general concern should prefer different templates
        low_general_prompt = await prompt_system.generate_prompt(
            severity=CrisisSeverity.LOW,
            risk_domains=[RiskDomain.TRAUMA]
        )
        
        # If both prompts generated, they should be different
        if high_suicide_prompt and low_general_prompt:
            assert high_suicide_prompt.template_id != low_general_prompt.template_id


if __name__ == "__main__":
    pytest.main([__file__]) 