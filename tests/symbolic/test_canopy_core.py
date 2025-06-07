"""
Core unit tests for the CANOPY symbolic processing system.

Tests cover:
1. Basic metaphor extraction
2. Symbol processing
3. Archetype mapping
4. Emotional state analysis
5. Core processing pipeline
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
import json
import numpy as np

from src.symbolic.canopy import CanopyProcessor
from src.symbolic.canopy.processor import JUNGIAN_ARCHETYPES, SYMBOL_CATEGORIES
from src.models.emotional_state import SymbolicMapping, EmotionalMetaphor

# Test data
SAMPLE_TEXTS = [
    "I feel like I'm drowning in responsibilities",
    "My heart is a mountain, strong and steady",
    "I'm walking through a dark forest of uncertainty",
    "The fire of my passion burns bright",
    "I'm floating on a cloud of happiness"
]

@pytest.fixture
def canopy_processor():
    """Create a CANOPY processor instance for testing"""
    processor = CanopyProcessor(api_key="test_key")
    return processor

@pytest.fixture
def sample_history():
    """Create a sample symbolic history for testing"""
    return [
        SymbolicMapping(
            primary_symbol="water",
            archetype="shadow",
            alternative_symbols=["ocean", "depth"],
            valence=-0.7,
            arousal=0.8,
            metaphors=[
                EmotionalMetaphor(text="drowning", symbol="water", confidence=0.9)
            ],
            confidence=0.9,
            timestamp=datetime.now()
        ),
        SymbolicMapping(
            primary_symbol="mountain",
            archetype="self",
            alternative_symbols=["peak", "summit"],
            valence=0.6,
            arousal=0.4,
            metaphors=[
                EmotionalMetaphor(text="standing tall", symbol="mountain", confidence=0.85)
            ],
            confidence=0.85,
            timestamp=datetime.now()
        )
    ]

# Basic Processing Tests
@pytest.mark.asyncio
async def test_basic_metaphor_extraction(canopy_processor):
    """Test basic metaphor extraction from various input texts"""
    for text in SAMPLE_TEXTS:
        result = await canopy_processor.extract(text)
        assert isinstance(result, SymbolicMapping)
        assert result.primary_symbol
        assert result.archetype in JUNGIAN_ARCHETYPES
        assert len(result.metaphors) > 0
        assert -1.0 <= result.valence <= 1.0
        assert 0.0 <= result.arousal <= 1.0
        assert 0.0 <= result.confidence <= 1.0

@pytest.mark.asyncio
async def test_symbol_processing(canopy_processor):
    """Test symbol processing and validation"""
    result = await canopy_processor.extract(SAMPLE_TEXTS[0])
    
    # Test symbol properties
    assert result.primary_symbol in canopy_processor.symbol_library
    assert len(result.alternative_symbols) > 0
    assert all(s in canopy_processor.symbol_library for s in result.alternative_symbols)
    
    # Test symbol relationships
    assert canopy_processor._validate_symbol_relationships(result.primary_symbol, result.alternative_symbols)

@pytest.mark.asyncio
async def test_archetype_mapping(canopy_processor):
    """Test archetype mapping and validation"""
    for text in SAMPLE_TEXTS:
        result = await canopy_processor.extract(text)
        
        # Test archetype properties
        assert result.archetype in JUNGIAN_ARCHETYPES
        assert canopy_processor._validate_archetype_mapping(result.primary_symbol, result.archetype)
        
        # Test archetype transitions
        if len(canopy_processor._symbolic_history.get("test_user", [])) > 0:
            previous = canopy_processor._symbolic_history["test_user"][-1]
            assert canopy_processor._validate_archetype_transition(previous.archetype, result.archetype)

@pytest.mark.asyncio
async def test_emotional_state_analysis(canopy_processor, sample_history):
    """Test emotional state analysis and validation"""
    canopy_processor._symbolic_history["test_user"] = sample_history
    
    # Test current state analysis
    current_state = await canopy_processor._analyze_current_state(sample_history[-1], "test_user")
    assert isinstance(current_state, dict)
    assert "valence" in current_state
    assert "arousal" in current_state
    assert "dominant_archetype" in current_state
    
    # Test emotional drift
    drift = canopy_processor._calculate_emotional_drift(sample_history)
    assert isinstance(drift, float)
    assert 0.0 <= drift <= 1.0

@pytest.mark.asyncio
async def test_processing_pipeline(canopy_processor):
    """Test the complete processing pipeline"""
    for text in SAMPLE_TEXTS:
        # Test full processing
        result = await canopy_processor.process(
            text=text,
            user_id="test_user",
            context={"session_id": "test_session"}
        )
        
        assert isinstance(result, SymbolicMapping)
        assert result.primary_symbol
        assert result.archetype
        assert len(result.metaphors) > 0
        assert result.confidence > 0
        
        # Verify history update
        assert "test_user" in canopy_processor._symbolic_history
        assert len(canopy_processor._symbolic_history["test_user"]) > 0
        
        # Verify cultural adaptation
        assert canopy_processor._cultural_cache.get(result.primary_symbol) is not None

# Error Handling Tests
@pytest.mark.asyncio
async def test_error_handling(canopy_processor):
    """Test error handling in core processing"""
    # Test empty input
    result = await canopy_processor.process("")
    assert isinstance(result, SymbolicMapping)
    assert result.confidence < 0.5  # Low confidence for empty input
    
    # Test invalid input
    result = await canopy_processor.process(None)
    assert isinstance(result, SymbolicMapping)
    assert result.confidence < 0.5
    
    # Test processing error
    with patch.object(canopy_processor.extractor, "extract", side_effect=Exception("Test error")):
        result = await canopy_processor.process("test")
        assert isinstance(result, SymbolicMapping)
        assert result.confidence < 0.5

# Validation Tests
def test_symbol_validation(canopy_processor):
    """Test symbol validation functions"""
    # Test valid symbols
    assert canopy_processor._validate_symbol("water")
    assert canopy_processor._validate_symbol("fire")
    
    # Test invalid symbols
    assert not canopy_processor._validate_symbol("invalid_symbol")
    assert not canopy_processor._validate_symbol("")

def test_archetype_validation(canopy_processor):
    """Test archetype validation functions"""
    # Test valid archetypes
    for archetype in JUNGIAN_ARCHETYPES:
        assert canopy_processor._validate_archetype(archetype)
    
    # Test invalid archetypes
    assert not canopy_processor._validate_archetype("invalid_archetype")
    assert not canopy_processor._validate_archetype("")

def test_emotional_validation(canopy_processor):
    """Test emotional state validation"""
    # Test valid emotional states
    assert canopy_processor._validate_emotional_state(-0.5, 0.5)
    assert canopy_processor._validate_emotional_state(0.0, 0.0)
    assert canopy_processor._validate_emotional_state(1.0, 1.0)
    
    # Test invalid emotional states
    assert not canopy_processor._validate_emotional_state(-1.5, 0.5)
    assert not canopy_processor._validate_emotional_state(0.5, 1.5)
    assert not canopy_processor._validate_emotional_state(None, 0.5) 