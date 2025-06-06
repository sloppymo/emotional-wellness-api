"""
Unit tests for MOSS adapter module.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
from datetime import datetime

from integration.moss_adapter import MOSSAdapter, get_moss_adapter
from integration.models import EmotionalInput, UserContext, CrisisAssessment
from symbolic.moss.crisis_classifier import CrisisSeverity, RiskDomain, CrisisContext


@pytest.fixture
def mock_crisis_classifier():
    mock = AsyncMock()
    mock.assess_risk = AsyncMock(return_value={
        "severity": CrisisSeverity.MODERATE,
        "risk_domains": [RiskDomain.SELF_HARM, RiskDomain.SUICIDAL_IDEATION],
        "confidence": 0.87,
        "context": CrisisContext(
            detected_phrases=["feeling hopeless", "no point anymore"],
            risk_factors=["isolation", "previous history"],
            protective_factors=["supportive family"],
            temporal_markers=["recent job loss"]
        )
    })
    return mock


@pytest.fixture
def mock_detection_thresholds():
    mock = AsyncMock()
    mock.validate_crisis = AsyncMock(return_value=True)
    mock.get_threshold_for_user = AsyncMock(return_value=0.75)
    return mock


@pytest.fixture
def mock_prompt_templates():
    mock = AsyncMock()
    mock.generate_crisis_prompt = AsyncMock(
        return_value="I notice you're going through a difficult time. Help is available."
    )
    return mock


@pytest.fixture
def mock_audit_logger():
    mock = AsyncMock()
    mock.log_event = AsyncMock()
    return mock


@pytest.fixture
def moss_adapter(mock_crisis_classifier, mock_detection_thresholds, 
                mock_prompt_templates, mock_audit_logger):
    adapter = MOSSAdapter()
    adapter.crisis_classifier = mock_crisis_classifier
    adapter.detection_thresholds = mock_detection_thresholds
    adapter.prompt_templates = mock_prompt_templates
    adapter.audit_logger = mock_audit_logger
    adapter._cache = {}
    return adapter


@pytest.mark.asyncio
async def test_assess_crisis_risk(moss_adapter):
    """Test that crisis risk assessment works correctly."""
    # Arrange
    emotional_input = EmotionalInput(
        user_id="test-user-123",
        text="I've been feeling really hopeless lately and don't see the point anymore",
        metadata={"age": 35, "context": "therapy_session"}
    )
    
    # Act
    result = await moss_adapter.assess_crisis_risk(
        emotional_input=emotional_input,
        user_id="test-user-123",
        user_context={"prev_sessions": 3}
    )
    
    # Assert
    assert result.level == CrisisSeverity.MODERATE
    assert RiskDomain.SELF_HARM in result.risk_domains
    assert result.confidence > 0.8
    moss_adapter.crisis_classifier.assess_risk.assert_called_once()
    moss_adapter.detection_thresholds.validate_crisis.assert_called_once()
    moss_adapter.audit_logger.log_event.assert_called_once()


@pytest.mark.asyncio
async def test_generate_crisis_response(moss_adapter):
    """Test that crisis response generation works correctly."""
    # Arrange
    crisis = CrisisAssessment(
        level=CrisisSeverity.MODERATE,
        risk_domains=[RiskDomain.SELF_HARM],
        confidence=0.87,
        timestamp=datetime.utcnow()
    )
    
    # Act
    result = await moss_adapter.generate_crisis_response(
        crisis_assessment=crisis,
        user_name="Alex"
    )
    
    # Assert
    assert isinstance(result, str)
    assert len(result) > 0
    moss_adapter.prompt_templates.generate_crisis_prompt.assert_called_once()
    moss_adapter.audit_logger.log_event.assert_called_once()


@pytest.mark.asyncio
async def test_caching_behavior(moss_adapter):
    """Test that caching works correctly."""
    # Arrange
    emotional_input = EmotionalInput(
        user_id="test-user-123",
        text="I've been feeling down",
        metadata={"age": 35}
    )
    
    # Act - First call
    result1 = await moss_adapter.assess_crisis_risk(
        emotional_input=emotional_input,
        user_id="test-user-123",
        user_context={}
    )
    
    # Reset mocks to verify they aren't called again
    moss_adapter.crisis_classifier.assess_risk.reset_mock()
    moss_adapter.detection_thresholds.validate_crisis.reset_mock()
    
    # Act - Second call with same input
    result2 = await moss_adapter.assess_crisis_risk(
        emotional_input=emotional_input,
        user_id="test-user-123",
        user_context={}
    )
    
    # Assert
    assert result1.level == result2.level
    assert result1.confidence == result2.confidence
    # Verify the mocks weren't called again
    moss_adapter.crisis_classifier.assess_risk.assert_not_called()
    moss_adapter.detection_thresholds.validate_crisis.assert_not_called()


@pytest.mark.asyncio
async def test_fallback_behavior(moss_adapter):
    """Test that adapter gracefully handles component failures."""
    # Arrange
    emotional_input = EmotionalInput(
        user_id="test-user-123",
        text="I've been feeling down",
        metadata={"age": 35}
    )
    
    # Make classifier throw an exception
    moss_adapter.crisis_classifier.assess_risk.side_effect = Exception("Service unavailable")
    
    # Act
    result = await moss_adapter.assess_crisis_risk(
        emotional_input=emotional_input,
        user_id="test-user-123",
        user_context={}
    )
    
    # Assert
    # Should return a low-severity result as fallback
    assert result.level == CrisisSeverity.NONE
    assert result.confidence == 0
    assert "error" in result.metadata
    # Should still log the error
    moss_adapter.audit_logger.log_event.assert_called_once()


@pytest.mark.asyncio
async def test_get_moss_adapter():
    """Test that singleton adapter factory works correctly."""
    # Act
    adapter1 = get_moss_adapter()
    adapter2 = get_moss_adapter()
    
    # Assert
    assert adapter1 is adapter2  # Same instance
    assert isinstance(adapter1, MOSSAdapter)
