"""
Unit tests for the CANOPY cultural adaptation system.

This test suite focuses on the cultural adaptation functionality of the CANOPY system,
ensuring proper handling of cultural contexts and symbol adaptations.
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from typing import Dict, List, Optional

from src.symbolic.canopy.processor import CanopyProcessor
from src.symbolic.canopy.metaphor_extraction import SymbolicMapping, EmotionalMetaphor

# Test data
SAMPLE_TEXT = "I feel like a fish out of water in this new environment"
SAMPLE_CULTURAL_CONTEXT = {
    "culture_code": "jp",  # Japanese
    "language": "ja",
    "region": "asia",
    "value_dimensions": {
        "collectivism": 0.8,
        "power_distance": 0.7,
        "uncertainty_avoidance": 0.9
    }
}

MOCK_INITIAL_MAPPING = SymbolicMapping(
    primary_symbol="water",
    archetype="self",
    alternative_symbols=["displacement", "environment", "adaptation"],
    valence=-0.4,
    arousal=0.5,
    metaphors=[
        EmotionalMetaphor(text="fish out of water", symbol="water", confidence=0.9)
    ],
    confidence=0.8
)

@pytest.fixture
def canopy_processor():
    """Create a CANOPY processor instance for testing"""
    with patch("src.symbolic.canopy.processor.MetaphorExtractor") as mock_extractor_cls:
        mock_extractor = AsyncMock()
        mock_extractor.extract.return_value = MOCK_INITIAL_MAPPING
        mock_extractor_cls.return_value = mock_extractor
        
        processor = CanopyProcessor(api_key="test_key")
        yield processor

@pytest.mark.asyncio
async def test_process_with_cultural_adaptation(canopy_processor):
    """Test processing with cultural adaptation"""
    # Mock the _apply_cultural_adaptations method to return specific adaptations
    with patch.object(
        canopy_processor,
        "_apply_cultural_adaptations",
        return_value={
            "primary_symbol": {
                "original": "water",
                "cultural_equivalent": "海 (umi)",
                "alternatives": ["和 (harmony)", "適応 (adaptation)"]
            },
            "archetype": {
                "original": "self",
                "cultural_equivalent": "本当の自己 (true self)"
            }
        }
    ) as mock_adapt:
        context = {"cultural_context": SAMPLE_CULTURAL_CONTEXT}
        result = await canopy_processor.process(
            text=SAMPLE_TEXT,
            user_id="test_user",
            context=context
        )
        
        # Verify that cultural adaptation was applied
        mock_adapt.assert_called_once()
        assert "和 (harmony)" in result.alternative_symbols
        assert "適応 (adaptation)" in result.alternative_symbols

@pytest.mark.asyncio
async def test_apply_cultural_adaptations_method(canopy_processor):
    """Test the _apply_cultural_adaptations method directly"""
    # Since this is a private method, we're deliberately testing implementation details
    adaptations = await canopy_processor._apply_cultural_adaptations(
        mapping=MOCK_INITIAL_MAPPING,
        cultural_context=SAMPLE_CULTURAL_CONTEXT
    )
    
    assert isinstance(adaptations, dict)
    assert "primary_symbol" in adaptations
    assert "original" in adaptations["primary_symbol"]
    assert adaptations["primary_symbol"]["original"] == "water"

@pytest.mark.asyncio
async def test_caching_of_cultural_adaptations(canopy_processor):
    """Test that cultural adaptations are cached for performance"""
    # Call twice with same context to test caching
    context1 = {"cultural_context": SAMPLE_CULTURAL_CONTEXT}
    context2 = {"cultural_context": SAMPLE_CULTURAL_CONTEXT}
    
    await canopy_processor.process(text=SAMPLE_TEXT, user_id="test_user", context=context1)
    
    # Mock _apply_cultural_adaptations to verify if it's called again
    with patch.object(
        canopy_processor,
        "_apply_cultural_adaptations",
        return_value={}
    ) as mock_adapt:
        await canopy_processor.process(text="Another text", user_id="test_user", context=context2)
        
        # The method should not be called again due to caching
        assert mock_adapt.call_count == 0

@pytest.mark.asyncio
async def test_cultural_adaptation_with_different_cultures(canopy_processor):
    """Test adaptation with different cultural contexts"""
    # Define two different cultural contexts
    japanese_context = {"cultural_context": {
        "culture_code": "jp",
        "language": "ja",
        "region": "asia"
    }}
    
    arabic_context = {"cultural_context": {
        "culture_code": "sa",
        "language": "ar",
        "region": "middle_east"
    }}
    
    # Mock different responses for different contexts
    async def mock_adapt(mapping, cultural_context):
        if cultural_context.get("culture_code") == "jp":
            return {
                "primary_symbol": {
                    "original": "water",
                    "cultural_equivalent": "海 (umi)",
                    "alternatives": ["和 (harmony)"]
                }
            }
        elif cultural_context.get("culture_code") == "sa":
            return {
                "primary_symbol": {
                    "original": "water",
                    "cultural_equivalent": "ماء (ma')",
                    "alternatives": ["وئام (harmony)"]
                }
            }
        return {}
    
    with patch.object(
        canopy_processor,
        "_apply_cultural_adaptations",
        side_effect=mock_adapt
    ) as mock_adapt_fn:
        # Process with Japanese context
        result_jp = await canopy_processor.process(
            text=SAMPLE_TEXT,
            user_id="test_user",
            context=japanese_context
        )
        
        # Process with Arabic context
        result_ar = await canopy_processor.process(
            text=SAMPLE_TEXT,
            user_id="test_user",
            context=arabic_context
        )
        
        # Verify different adaptations were applied
        assert mock_adapt_fn.call_count == 2
        mock_adapt_fn.assert_any_call(MOCK_INITIAL_MAPPING, japanese_context["cultural_context"])
        mock_adapt_fn.assert_any_call(MOCK_INITIAL_MAPPING, arabic_context["cultural_context"])

@pytest.mark.asyncio
async def test_no_cultural_adaptation_when_not_requested(canopy_processor):
    """Test that no cultural adaptation is applied when not requested"""
    # Process without cultural context
    result = await canopy_processor.process(
        text=SAMPLE_TEXT,
        user_id="test_user",
        context={}
    )
    
    # The result should be the original mapping from the extractor
    assert result.primary_symbol == MOCK_INITIAL_MAPPING.primary_symbol
    assert result.archetype == MOCK_INITIAL_MAPPING.archetype
    assert result.alternative_symbols == MOCK_INITIAL_MAPPING.alternative_symbols

@pytest.mark.asyncio
async def test_cultural_adaptation_cache_limiting(canopy_processor):
    """Test that the cultural adaptation cache is limited in size"""
    # Set a small cache size for testing
    canopy_processor.MAX_CACHE_SIZE = 2
    
    # Create multiple different cultural contexts
    contexts = [
        {"cultural_context": {"culture_code": f"test{i}"}}
        for i in range(5)  # Create 5 contexts, but cache only holds 2
    ]
    
    # Process with each context
    for i, context in enumerate(contexts):
        await canopy_processor.process(
            text=f"Sample text {i}",
            user_id="test_user",
            context=context
        )
    
    # Cache should only contain at most MAX_CACHE_SIZE entries
    assert len(canopy_processor._cultural_cache) <= canopy_processor.MAX_CACHE_SIZE
