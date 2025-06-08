"""
Unit tests for the CANOPY metaphor extraction system.

This test suite focuses specifically on the metaphor extraction functionality,
including cultural adaptation, pattern analysis, and integration with other systems.
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from typing import Dict, List, Optional

from src.symbolic.canopy.metaphor_extraction import MetaphorExtractor, SymbolicMapping, EmotionalMetaphor
from src.symbolic.canopy.processor import CanopyProcessor, JUNGIAN_ARCHETYPES, SYMBOL_CATEGORIES

# Test data
SAMPLE_TEXT = "I feel like I'm climbing a mountain with no end in sight"
SAMPLE_BIOMARKERS = {"heart_rate": 85.0, "respiratory_rate": 18.0, "skin_conductance": 0.7}
SAMPLE_CONTEXT = {
    "previous_symbols": ["mountain", "path"],
    "user_preferences": {"detail_level": "high"}
}

MOCK_CLAUDE_METAPHOR_RESPONSE = {
    "primary_symbol": "mountain",
    "archetype": "hero",
    "alternative_symbols": ["obstacle", "journey", "challenge"],
    "valence": -0.3,
    "arousal": 0.6,
    "metaphors": [
        {"text": "climbing a mountain", "symbol": "mountain", "confidence": 0.85},
        {"text": "no end in sight", "symbol": "journey", "confidence": 0.7}
    ]
}

@pytest.fixture
def metaphor_extractor():
    """Create a MetaphorExtractor instance for testing"""
    with patch("src.symbolic.canopy.metaphor_extraction.Anthropic") as mock_anthropic:
        mock_client = Mock()
        mock_client.completions = AsyncMock()
        mock_client.completions.create.return_value = Mock(
            completion=json.dumps(MOCK_CLAUDE_METAPHOR_RESPONSE)
        )
        mock_anthropic.return_value = mock_client
        
        extractor = MetaphorExtractor(api_key="test_key")
        yield extractor

@pytest.mark.asyncio
async def test_metaphor_extraction_basic(metaphor_extractor):
    """Test basic metaphor extraction functionality"""
    result = await metaphor_extractor.extract(SAMPLE_TEXT)
    
    assert isinstance(result, SymbolicMapping)
    assert result.primary_symbol == "mountain"
    assert result.archetype == "hero"
    assert "obstacle" in result.alternative_symbols
    assert result.valence == -0.3
    assert result.arousal == 0.6
    assert len(result.metaphors) == 2
    assert result.metaphors[0].text == "climbing a mountain"
    assert result.metaphors[0].symbol == "mountain"
    assert result.metaphors[0].confidence == 0.85

@pytest.mark.asyncio
async def test_metaphor_extraction_with_biomarkers(metaphor_extractor):
    """Test metaphor extraction with biomarkers included"""
    result = await metaphor_extractor.extract(SAMPLE_TEXT, SAMPLE_BIOMARKERS)
    
    # Verify that the prompt includes biomarkers
    call_args = metaphor_extractor.client.completions.create.call_args
    assert "Biomarkers" in call_args[1]["prompt"]
    assert "heart_rate" in call_args[1]["prompt"]
    assert "85.0" in call_args[1]["prompt"]

@pytest.mark.asyncio
async def test_metaphor_extraction_with_context(metaphor_extractor):
    """Test metaphor extraction with context included"""
    result = await metaphor_extractor.extract(SAMPLE_TEXT, context=SAMPLE_CONTEXT)
    
    # Verify that the prompt includes context
    call_args = metaphor_extractor.client.completions.create.call_args
    assert "Context" in call_args[1]["prompt"]
    assert "previous_symbols" in call_args[1]["prompt"]
    assert "mountain" in call_args[1]["prompt"]

@pytest.mark.asyncio
async def test_metaphor_extraction_claude_error_handling(metaphor_extractor):
    """Test handling of Claude API errors"""
    # Make Claude raise an exception
    metaphor_extractor.client.completions.create.side_effect = Exception("API Error")
    
    # Should fall back to basic mapping without raising an exception
    result = await metaphor_extractor.extract(SAMPLE_TEXT)
    
    assert isinstance(result, SymbolicMapping)
    assert result.primary_symbol == "unknown"
    assert result.confidence == 0.1

@pytest.mark.asyncio
async def test_metaphor_extraction_response_parsing_error(metaphor_extractor):
    """Test handling of response parsing errors"""
    # Return an invalid JSON response
    metaphor_extractor.client.completions.create.return_value = Mock(
        completion="This is not valid JSON"
    )
    
    result = await metaphor_extractor.extract(SAMPLE_TEXT)
    
    # Should fall back to default mapping
    assert isinstance(result, SymbolicMapping)
    assert result.primary_symbol == "unknown"
    assert result.confidence == 0.1

@pytest.mark.asyncio
async def test_metaphor_extraction_empty_input(metaphor_extractor):
    """Test handling of empty input text"""
    result = await metaphor_extractor.extract("")
    
    # Should fall back to default mapping
    assert isinstance(result, SymbolicMapping)
    assert result.primary_symbol == "unknown"
    assert result.confidence == 0.1

@pytest.mark.asyncio
async def test_metaphor_extraction_realistic_example(metaphor_extractor):
    """Test metaphor extraction with a realistic example"""
    complex_text = "After years of therapy, I finally feel like I've emerged from a dark cave into sunlight."
    
    metaphor_extractor.client.completions.create.return_value = Mock(
        completion=json.dumps({
            "primary_symbol": "cave",
            "archetype": "rebirth",
            "alternative_symbols": ["darkness", "light", "emergence"],
            "valence": 0.8,
            "arousal": 0.6,
            "metaphors": [
                {"text": "emerged from a dark cave", "symbol": "cave", "confidence": 0.9},
                {"text": "into sunlight", "symbol": "light", "confidence": 0.85}
            ]
        })
    )
    
    result = await metaphor_extractor.extract(complex_text)
    
    assert isinstance(result, SymbolicMapping)
    assert result.primary_symbol == "cave"
    assert result.archetype == "rebirth"
    assert "light" in result.alternative_symbols
    assert result.valence == 0.8
    assert len(result.metaphors) == 2

def test_symbol_library_handling(metaphor_extractor):
    """Test handling and access of the symbol library"""
    # Access the symbol library
    library = metaphor_extractor.symbol_library
    
    # Should have at least one entry
    assert isinstance(library, dict)
    assert len(library) > 0
    assert "water" in library
    assert "associations" in library["water"]

def test_emotional_metaphor_model():
    """Test the EmotionalMetaphor model"""
    metaphor = EmotionalMetaphor(
        text="drowning in work",
        symbol="water",
        confidence=0.75
    )
    
    assert metaphor.text == "drowning in work"
    assert metaphor.symbol == "water"
    assert metaphor.confidence == 0.75

def test_symbolic_mapping_model():
    """Test the SymbolicMapping model"""
    mapping = SymbolicMapping(
        primary_symbol="fire",
        archetype="shadow",
        alternative_symbols=["passion", "destruction"],
        valence=-0.2,
        arousal=0.8,
        metaphors=[
            EmotionalMetaphor(text="burning with anger", symbol="fire", confidence=0.9)
        ]
    )
    
    assert mapping.primary_symbol == "fire"
    assert mapping.archetype == "shadow"
    assert "passion" in mapping.alternative_symbols
    assert mapping.valence == -0.2
    assert mapping.arousal == 0.8
    assert len(mapping.metaphors) == 1
    assert mapping.metaphors[0].text == "burning with anger"
    assert mapping.timestamp is not None  # Should have auto-generated timestamp
