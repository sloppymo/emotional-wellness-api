"""
Unit tests for the CANOPY symbolic processing system.

Tests cover:
1. Metaphor extraction
2. Archetype mapping
3. Symbol library integration
4. Claude integration and fallback behavior
5. Error handling and edge cases
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from typing import Dict, List, Optional

from src.symbolic.canopy import CanopyProcessor, JUNGIAN_ARCHETYPES, SYMBOL_CATEGORIES
from src.models.emotional_state import SymbolicMapping, EmotionalMetaphor

# Test data
SAMPLE_TEXT = "I feel like I'm drowning in a sea of responsibilities"
SAMPLE_BIOMARKERS = {"heart_rate": 80.0, "respiratory_rate": 16.0}
SAMPLE_CONTEXT = {"previous_symbols": ["water", "path"]}

MOCK_CLAUDE_RESPONSE = {
    "primary_symbol": "water",
    "archetype": "shadow",
    "alternative_symbols": ["burden", "ocean", "depth"],
    "valence": -0.7,
    "arousal": 0.8,
    "metaphors": [
        {"text": "drowning in a sea", "symbol": "water", "confidence": 0.9}
    ]
}

@pytest.fixture
def canopy_processor():
    """Create a CANOPY processor instance for testing"""
    return CanopyProcessor(api_key="test_key")

@pytest.fixture
def mock_anthropic():
    """Mock the Anthropic client"""
    with patch("src.symbolic.canopy.Anthropic") as mock:
        mock_client = Mock()
        mock_client.messages = AsyncMock()
        mock_client.messages.create.return_value = Mock(
            content=[Mock(text=json.dumps(MOCK_CLAUDE_RESPONSE))]
        )
        mock.return_value = mock_client
        yield mock

@pytest.mark.asyncio
async def test_extract_with_claude(canopy_processor, mock_anthropic):
    """Test metaphor extraction using Claude integration"""
    result = await canopy_processor.extract(SAMPLE_TEXT, SAMPLE_BIOMARKERS, SAMPLE_CONTEXT)
    
    assert isinstance(result, SymbolicMapping)
    assert result.primary_symbol == "water"
    assert result.archetype == "shadow"
    assert len(result.alternative_symbols) == 3
    assert result.valence == -0.7
    assert result.arousal == 0.8
    assert len(result.metaphors) == 1
    assert result.metaphors[0].text == "drowning in a sea"

@pytest.mark.asyncio
async def test_extract_fallback(canopy_processor):
    """Test fallback processing when Claude is unavailable"""
    # Force fallback by setting client to None
    canopy_processor.client = None
    
    result = await canopy_processor.extract(SAMPLE_TEXT)
    
    assert isinstance(result, SymbolicMapping)
    assert result.primary_symbol in ["water", "fire", "path"]
    assert result.archetype in JUNGIAN_ARCHETYPES
    assert len(result.alternative_symbols) > 0
    assert -1.0 <= result.valence <= 1.0
    assert 0.0 <= result.arousal <= 1.0

def test_symbol_library_loading(tmp_path):
    """Test loading of symbol library from file"""
    # Create a temporary symbol library file
    library_path = tmp_path / "symbols.json"
    test_library = {
        "water": {
            "associations": ["flow", "depth", "cleansing"],
            "cultural_variants": {
                "western": "purification",
                "eastern": "harmony"
            }
        }
    }
    
    with open(library_path, "w") as f:
        json.dump(test_library, f)
    
    processor = CanopyProcessor(symbol_library_path=str(library_path))
    assert processor.symbol_library == test_library

@pytest.mark.asyncio
async def test_error_handling(canopy_processor, mock_anthropic):
    """Test error handling in Claude integration"""
    # Make Claude raise an exception
    mock_anthropic.return_value.messages.create.side_effect = Exception("API Error")
    
    # Should fall back to basic processing without error
    result = await canopy_processor.extract(SAMPLE_TEXT)
    assert isinstance(result, SymbolicMapping)

@pytest.mark.asyncio
async def test_empty_input(canopy_processor):
    """Test handling of empty or invalid input"""
    result = await canopy_processor.extract("")
    assert isinstance(result, SymbolicMapping)
    
    result = await canopy_processor.extract(None)
    assert isinstance(result, SymbolicMapping)

def test_drift_calculation(canopy_processor):
    """Test symbolic drift calculation"""
    current = SymbolicMapping(
        primary_symbol="water",
        archetype="shadow",
        alternative_symbols=["ocean", "depth"],
        valence=-0.7,
        arousal=0.8,
        metaphors=[EmotionalMetaphor(text="drowning", symbol="water", confidence=0.9)]
    )
    
    previous = [
        SymbolicMapping(
            primary_symbol="path",
            archetype="hero",
            alternative_symbols=["journey", "quest"],
            valence=0.5,
            arousal=0.6,
            metaphors=[EmotionalMetaphor(text="walking", symbol="path", confidence=0.8)]
        )
    ]
    
    drift = canopy_processor.calculate_drift(current, previous)
    assert isinstance(drift, float)
    assert 0.0 <= drift <= 1.0

@pytest.mark.asyncio
async def test_context_integration(canopy_processor, mock_anthropic):
    """Test integration of previous context in processing"""
    context = {
        "previous_symbols": ["fire", "mountain"],
        "session_start": datetime.now().isoformat()
    }
    
    result = await canopy_processor.extract(SAMPLE_TEXT, context=context)
    assert isinstance(result, SymbolicMapping)
    
    # Verify Claude was called with context
    call_args = mock_anthropic.return_value.messages.create.call_args
    assert "previous symbols" in call_args[1]["messages"][0]["content"]

def test_archetype_validation():
    """Test validation of Jungian archetypes"""
    for archetype in JUNGIAN_ARCHETYPES:
        assert isinstance(archetype, str)
        assert len(archetype) > 0

def test_symbol_categories_validation():
    """Test validation of symbol categories"""
    for category in SYMBOL_CATEGORIES:
        assert isinstance(category, str)
        assert len(category) > 0
        assert "_" in category  # Categories should use snake_case 