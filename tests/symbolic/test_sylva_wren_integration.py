"""
Integration tests for the SYLVA-WREN framework integration.

These tests verify the integration between the SYLVA framework adapter and
the various components of the emotional wellness API, including CANOPY and WREN.
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from typing import Dict, List, Optional

from src.symbolic.adapters.sylva_adapter import SylvaAdapter, SylvaContext, ProcessingResult
from src.symbolic.canopy import CanopyProcessor
from src.symbolic.canopy.metaphor_extraction import SymbolicMapping, EmotionalMetaphor

# Test data
SAMPLE_TEXT = "I'm feeling overwhelmed by waves of anxiety lately"
SAMPLE_BIOMARKERS = {"heart_rate": 92.0, "respiratory_rate": 20.0, "skin_conductance": 0.8}
SAMPLE_PROCESSING_FLAGS = {
    "enable_cultural_adaptation": True,
    "cultural_context": {
        "culture_code": "us",
        "language": "en",
        "region": "north_america"
    },
    "enable_veluria": True,
    "enable_root": True
}

@pytest.fixture
def mock_canopy_processor():
    """Create a mock CanopyProcessor for testing"""
    with patch("src.symbolic.canopy.CanopyProcessor") as mock_processor_cls:
        mock_processor = AsyncMock()
        mock_processor.process.return_value = SymbolicMapping(
            primary_symbol="water",
            archetype="shadow",
            alternative_symbols=["wave", "ocean", "depth"],
            valence=-0.6,
            arousal=0.7,
            metaphors=[
                EmotionalMetaphor(text="waves of anxiety", symbol="water", confidence=0.85)
            ],
            confidence=0.9
        )
        mock_processor_cls.return_value = mock_processor
        yield mock_processor

@pytest.fixture
def sylva_adapter():
    """Create a SylvaAdapter for testing"""
    return SylvaAdapter()

@pytest.fixture
def sylva_context():
    """Create a SylvaContext for testing"""
    return SylvaContext(
        user_id="test_user_123",
        session_id="test_session_456",
        timestamp=datetime.now(),
        processing_flags=SAMPLE_PROCESSING_FLAGS
    )

@pytest.mark.asyncio
async def test_sylva_adapter_basic_processing(sylva_adapter, mock_canopy_processor, sylva_context):
    """Test basic processing through SylvaAdapter"""
    result = await sylva_adapter.process(
        processor=mock_canopy_processor,
        context=sylva_context,
        input_text=SAMPLE_TEXT,
        biomarkers=SAMPLE_BIOMARKERS
    )
    
    # Verify successful processing
    assert isinstance(result, ProcessingResult)
    assert result.success is True
    assert result.error is None
    assert result.processing_time > 0
    
    # Verify output mapping
    assert isinstance(result.output, SymbolicMapping)
    assert result.output.primary_symbol == "water"
    assert result.output.archetype == "shadow"
    assert "wave" in result.output.alternative_symbols
    
    # Verify that CANOPY was called with correct parameters
    mock_canopy_processor.process.assert_called_once()
    call_args = mock_canopy_processor.process.call_args
    assert call_args[1]["text"] == SAMPLE_TEXT
    assert call_args[1]["user_id"] == sylva_context.user_id
    assert call_args[1]["biomarkers"] == SAMPLE_BIOMARKERS
    assert call_args[1]["context"]["session_id"] == sylva_context.session_id
    assert "cultural_context" in call_args[1]["context"]

@pytest.mark.asyncio
async def test_sylva_adapter_empty_input(sylva_adapter, mock_canopy_processor, sylva_context):
    """Test SylvaAdapter with empty input text"""
    result = await sylva_adapter.process(
        processor=mock_canopy_processor,
        context=sylva_context,
        input_text="",
        biomarkers=SAMPLE_BIOMARKERS
    )
    
    # Should fail with an error
    assert isinstance(result, ProcessingResult)
    assert result.success is False
    assert result.error is not None
    assert "empty" in result.error.lower()
    assert result.output is None

@pytest.mark.asyncio
async def test_sylva_adapter_canopy_error(sylva_adapter, mock_canopy_processor, sylva_context):
    """Test SylvaAdapter when CANOPY raises an exception"""
    # Make CANOPY processor raise an exception
    mock_canopy_processor.process.side_effect = Exception("CANOPY processing failed")
    
    result = await sylva_adapter.process(
        processor=mock_canopy_processor,
        context=sylva_context,
        input_text=SAMPLE_TEXT,
        biomarkers=SAMPLE_BIOMARKERS
    )
    
    # Should fail with an error
    assert isinstance(result, ProcessingResult)
    assert result.success is False
    assert result.error is not None
    assert "CANOPY processing failed" in result.error
    assert result.output is None

@pytest.mark.asyncio
async def test_sylva_adapter_context_conversion(sylva_adapter, mock_canopy_processor, sylva_context):
    """Test conversion of SYLVA context to CANOPY context"""
    await sylva_adapter.process(
        processor=mock_canopy_processor,
        context=sylva_context,
        input_text=SAMPLE_TEXT,
        biomarkers=SAMPLE_BIOMARKERS
    )
    
    # Verify context conversion
    call_args = mock_canopy_processor.process.call_args
    canopy_context = call_args[1]["context"]
    
    assert canopy_context["session_id"] == sylva_context.session_id
    assert canopy_context["timestamp"] is not None
    assert canopy_context["cultural_context"] == sylva_context.processing_flags["cultural_context"]
    assert canopy_context["enable_cultural_adaptation"] == sylva_context.processing_flags["enable_cultural_adaptation"]

@pytest.mark.asyncio
async def test_sylva_adapter_different_flags(sylva_adapter, mock_canopy_processor):
    """Test SylvaAdapter with different processing flags"""
    # Create context with different flags
    context = SylvaContext(
        user_id="test_user_123",
        session_id="test_session_456",
        timestamp=datetime.now(),
        processing_flags={
            "enable_cultural_adaptation": False,
            "enable_veluria": False,
            "enable_root": True
        }
    )
    
    await sylva_adapter.process(
        processor=mock_canopy_processor,
        context=context,
        input_text=SAMPLE_TEXT,
        biomarkers=SAMPLE_BIOMARKERS
    )
    
    # Verify that flags were passed correctly
    call_args = mock_canopy_processor.process.call_args
    canopy_context = call_args[1]["context"]
    
    assert canopy_context["enable_cultural_adaptation"] is False
    assert canopy_context["cultural_context"] is None

@pytest.mark.asyncio
async def test_sylva_adapter_performance_timing(sylva_adapter, mock_canopy_processor, sylva_context):
    """Test performance timing in SylvaAdapter"""
    result = await sylva_adapter.process(
        processor=mock_canopy_processor,
        context=sylva_context,
        input_text=SAMPLE_TEXT,
        biomarkers=SAMPLE_BIOMARKERS
    )
    
    # Verify that timing is recorded
    assert result.processing_time > 0
    
    # Make CANOPY processing take longer
    async def slow_process(*args, **kwargs):
        import asyncio
        await asyncio.sleep(0.1)  # Simulate processing time
        return SymbolicMapping(
            primary_symbol="water",
            archetype="shadow",
            alternative_symbols=[],
            valence=0,
            arousal=0,
            metaphors=[]
        )
    
    mock_canopy_processor.process.side_effect = slow_process
    
    slow_result = await sylva_adapter.process(
        processor=mock_canopy_processor,
        context=sylva_context,
        input_text=SAMPLE_TEXT,
        biomarkers=SAMPLE_BIOMARKERS
    )
    
    # Verify that the processing time reflects the delay
    assert slow_result.processing_time >= 0.1

@pytest.mark.asyncio
async def test_sylva_wren_end_to_end_flow():
    """Test full end-to-end flow between SYLVA and WREN systems"""
    # Mock the required components
    with patch("src.symbolic.canopy.CanopyProcessor") as mock_processor_cls, \
         patch("src.symbolic.adapters.wren_adapter.WrenAdapter") as mock_wren_cls:
        
        # Set up CANOPY mock
        mock_canopy = AsyncMock()
        symbolic_mapping = SymbolicMapping(
            primary_symbol="path",
            archetype="hero",
            alternative_symbols=["journey", "quest"],
            valence=0.4,
            arousal=0.6,
            metaphors=[
                EmotionalMetaphor(text="on a difficult path", symbol="path", confidence=0.8)
            ],
            confidence=0.9
        )
        mock_canopy.process.return_value = symbolic_mapping
        mock_processor_cls.return_value = mock_canopy
        
        # Set up WREN mock
        mock_wren = AsyncMock()
        mock_wren.process.return_value = {
            "narrative_arc": "growth",
            "character_position": "challenge",
            "symbolic_reinforcement": "positive",
            "next_steps": ["reflection", "resource_gathering"]
        }
        mock_wren_cls.return_value = mock_wren
        
        # Create the adapter and context
        sylva_adapter = SylvaAdapter()
        wren_adapter = mock_wren_cls.return_value
        
        context = SylvaContext(
            user_id="test_user_789",
            session_id="test_session_012",
            timestamp=datetime.now(),
            processing_flags={
                "enable_cultural_adaptation": True,
                "enable_wren_narrative": True
            }
        )
        
        # Process through SYLVA adapter
        sylva_result = await sylva_adapter.process(
            processor=mock_canopy,
            context=context,
            input_text="I'm trying to overcome a difficult challenge in my life",
            biomarkers=None
        )
        
        # Verify SYLVA processing succeeded
        assert sylva_result.success is True
        assert sylva_result.output is symbolic_mapping
        
        # Process through WREN adapter using SYLVA output
        wren_result = await wren_adapter.process(
            mapping=sylva_result.output,
            context=context
        )
        
        # Verify WREN integration
        assert mock_wren.process.called
        assert wren_result["narrative_arc"] == "growth"
        assert wren_result["character_position"] == "challenge"
