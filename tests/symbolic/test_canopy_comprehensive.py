"""
Comprehensive unit tests for CANOPY symbolic processing system.

This test suite provides complete coverage for edge cases, error conditions,
and advanced features that might not be covered in other test files.
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, List, Optional, Any
import numpy as np

from src.symbolic.canopy import CanopyProcessor
from src.symbolic.canopy.metaphor_extraction import MetaphorExtractor, SymbolicMapping, EmotionalMetaphor
from src.symbolic.canopy.processor import CanopyProcessor as ProcessorClass
from src.models.emotional_state import SymbolicMapping, EmotionalMetaphor

# Comprehensive test data
EDGE_CASE_TEXTS = [
    "",  # Empty string
    "   ",  # Whitespace only
    "a",  # Single character
    "1234567890",  # Numbers only
    "!!@#$%^&*()",  # Special characters only
    "😀😢😡😍🤔",  # Emojis only
    "The " * 1000,  # Very long text
    "I feel... I don't know how I feel. Maybe sad? Or angry? I'm confused.",  # Ambiguous emotions
    "Everything is fine. I'm happy. Life is good.",  # Potentially false positive happiness
    "I want to hurt myself. I can't take it anymore.",  # Crisis language
    "The mitochondria is the powerhouse of the cell.",  # Non-emotional scientific text
    "Купить хлеб в магазине завтра утром.",  # Non-English text
    "I'm feeling absolutely devastatingly ecstatically overwhelmingly incredibly amazingly fantastically wonderful today!",  # Extreme language
]

COMPLEX_BIOMARKERS = [
    {"heart_rate": 120, "respiratory_rate": 25, "skin_conductance": 0.9, "temperature": 99.5},
    {"heart_rate": 45, "respiratory_rate": 8, "skin_conductance": 0.1, "temperature": 95.2},
    {"heart_rate": None, "respiratory_rate": 15, "skin_conductance": 0.5},  # Missing data
    {"invalid_metric": 100},  # Invalid metrics
    {},  # Empty biomarkers
    {"heart_rate": "not_a_number"},  # Invalid data types
]

COMPLEX_CONTEXTS = [
    {"previous_symbols": ["water", "fire", "earth"], "cultural_context": "western", "session_duration": 3600},
    {"enable_veluria": True, "enable_root": True, "crisis_level": 3},
    {"user_preferences": {"language": "es", "cultural_background": "latin_american"}},
    {"temporal_context": {"time_of_day": "night", "season": "winter"}},
    {"therapeutic_context": {"session_number": 15, "therapy_type": "cbt"}},
    None,  # None context
    "invalid_context",  # Invalid context type
]

@pytest.fixture
def comprehensive_canopy_processor():
    """Create a comprehensive CANOPY processor for testing"""
    with patch("src.symbolic.canopy.Anthropic") as mock_anthropic:
        # Create a more sophisticated mock that can handle various responses
        mock_client = Mock()
        mock_client.completions = AsyncMock()
        
        # Default response
        default_response = {
            "primary_symbol": "water",
            "archetype": "self",
            "alternative_symbols": ["flow", "depth"],
            "valence": 0.0,
            "arousal": 0.5,
            "metaphors": [{"text": "test", "symbol": "water", "confidence": 0.8}],
            "confidence": 0.8
        }
        
        mock_client.completions.create.return_value = Mock(
            completion=json.dumps(default_response)
        )
        mock_anthropic.return_value = mock_client
        
        processor = CanopyProcessor(api_key="test_key")
        yield processor

# Edge Case Testing
@pytest.mark.asyncio
async def test_edge_case_inputs(comprehensive_canopy_processor):
    """Test CANOPY with various edge case inputs"""
    processor = comprehensive_canopy_processor
    
    for text in EDGE_CASE_TEXTS:
        try:
            result = await processor.extract(text)
            
            # All results should be valid SymbolicMapping objects
            assert isinstance(result, SymbolicMapping)
            assert result.primary_symbol is not None
            assert result.archetype is not None
            assert isinstance(result.metaphors, list)
            assert 0.0 <= result.confidence <= 1.0
            assert -1.0 <= result.valence <= 1.0
            assert 0.0 <= result.arousal <= 1.0
            
            # Empty or very short inputs should have low confidence
            if len(text.strip()) < 3:
                assert result.confidence < 0.5
                
        except Exception as e:
            pytest.fail(f"CANOPY failed on edge case input '{text[:50]}...': {str(e)}")

@pytest.mark.asyncio
async def test_complex_biomarkers(comprehensive_canopy_processor):
    """Test CANOPY with various biomarker configurations"""
    processor = comprehensive_canopy_processor
    
    for biomarkers in COMPLEX_BIOMARKERS:
        try:
            result = await processor.extract("I feel anxious today", biomarkers=biomarkers)
            
            assert isinstance(result, SymbolicMapping)
            # Should handle invalid biomarkers gracefully
            if biomarkers and any(isinstance(v, str) for v in biomarkers.values()):
                # Should still process but may have lower confidence
                assert result.confidence >= 0.0
                
        except Exception as e:
            pytest.fail(f"CANOPY failed with biomarkers {biomarkers}: {str(e)}")

@pytest.mark.asyncio
async def test_complex_contexts(comprehensive_canopy_processor):
    """Test CANOPY with various context configurations"""
    processor = comprehensive_canopy_processor
    
    for context in COMPLEX_CONTEXTS:
        try:
            result = await processor.extract("I feel confused", context=context)
            
            assert isinstance(result, SymbolicMapping)
            # Should handle invalid contexts gracefully
            
        except Exception as e:
            pytest.fail(f"CANOPY failed with context {context}: {str(e)}")

# Concurrency and Race Condition Testing
@pytest.mark.asyncio
async def test_concurrent_processing(comprehensive_canopy_processor):
    """Test concurrent processing for race conditions"""
    processor = comprehensive_canopy_processor
    
    async def process_user(user_id, session_id):
        return await processor.process(
            text=f"Test message for user {user_id}",
            user_id=f"user_{user_id}",
            context={"session_id": session_id}
        )
    
    # Run many concurrent operations
    tasks = []
    for i in range(50):
        tasks.append(process_user(i % 10, f"session_{i}"))  # Multiple sessions per user
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Verify all operations completed successfully
    successful_results = [r for r in results if isinstance(r, SymbolicMapping)]
    assert len(successful_results) == 50
    
    # Check for race conditions in history management
    for user_id in range(10):
        user_key = f"user_{user_id}"
        if user_key in processor._symbolic_history:
            history = processor._symbolic_history[user_key]
            # History should be consistent (no corrupted data)
            assert all(isinstance(item, SymbolicMapping) for item in history)

# Memory and Resource Testing
@pytest.mark.asyncio
async def test_memory_leak_prevention(comprehensive_canopy_processor):
    """Test for memory leaks and resource management"""
    processor = comprehensive_canopy_processor
    
    # Process many items and verify cleanup
    for i in range(1000):
        await processor.process(
            text=f"Memory test {i}",
            user_id=f"user_{i % 100}",  # Reuse user IDs to test cleanup
            context={"session_id": f"session_{i}"}
        )
        
        # Force cleanup every 100 iterations
        if i % 100 == 0:
            processor._cleanup_old_states()
            
            # Verify reasonable memory usage
            total_history_items = sum(
                len(history) for history in processor._symbolic_history.values()
            )
            assert total_history_items < 5000  # Reasonable limit
            
            total_cache_items = len(processor._cultural_cache)
            assert total_cache_items < 1000  # Reasonable cache size

# Error Recovery Testing
@pytest.mark.asyncio
async def test_error_recovery(comprehensive_canopy_processor):
    """Test error recovery and graceful degradation"""
    processor = comprehensive_canopy_processor
    
    # Test Claude API failure recovery
    original_client = processor.client
    processor.client = None  # Simulate API unavailability
    
    result = await processor.extract("Test message")
    assert isinstance(result, SymbolicMapping)
    assert result.confidence < 0.7  # Should indicate degraded mode
    
    # Restore client
    processor.client = original_client
    
    # Test Claude API timeout
    async def timeout_response(*args, **kwargs):
        await asyncio.sleep(10)  # Simulate timeout
        return Mock(completion='{"primary_symbol": "timeout"}')
    
    with patch.object(processor.client.completions, 'create', side_effect=timeout_response):
        with patch('asyncio.wait_for', side_effect=asyncio.TimeoutError):
            result = await processor.extract("Test message")
            assert isinstance(result, SymbolicMapping)
            assert result.confidence < 0.7

# Data Validation Testing
def test_symbolic_mapping_validation():
    """Test SymbolicMapping data validation"""
    # Valid mapping
    valid_mapping = SymbolicMapping(
        primary_symbol="water",
        archetype="self",
        alternative_symbols=["flow", "depth"],
        valence=0.5,
        arousal=0.7,
        metaphors=[EmotionalMetaphor(text="flowing", symbol="water", confidence=0.9)],
        confidence=0.8
    )
    assert valid_mapping.primary_symbol == "water"
    
    # Test boundary values
    boundary_mapping = SymbolicMapping(
        primary_symbol="test",
        archetype="self",
        alternative_symbols=[],
        valence=-1.0,  # Minimum
        arousal=1.0,   # Maximum
        metaphors=[],
        confidence=0.0  # Minimum
    )
    assert boundary_mapping.valence == -1.0
    assert boundary_mapping.arousal == 1.0

def test_emotional_metaphor_validation():
    """Test EmotionalMetaphor data validation"""
    # Valid metaphor
    valid_metaphor = EmotionalMetaphor(
        text="drowning in sorrow",
        symbol="water",
        confidence=0.95
    )
    assert valid_metaphor.text == "drowning in sorrow"
    assert valid_metaphor.confidence == 0.95
    
    # Boundary values
    boundary_metaphor = EmotionalMetaphor(
        text="",  # Empty text
        symbol="unknown",
        confidence=0.0
    )
    assert boundary_metaphor.confidence == 0.0

# State Management Testing
@pytest.mark.asyncio
async def test_state_management(comprehensive_canopy_processor):
    """Test symbolic state management across sessions"""
    processor = comprehensive_canopy_processor
    
    user_id = "test_user_state"
    
    # Process multiple messages
    messages = [
        "I feel like I'm drowning",
        "Now I'm climbing a mountain",
        "I see a light at the end of the tunnel",
        "I'm flying free like a bird"
    ]
    
    results = []
    for i, message in enumerate(messages):
        result = await processor.process(
            text=message,
            user_id=user_id,
            context={"session_id": f"session_{i}"}
        )
        results.append(result)
    
    # Verify state progression
    assert len(processor._symbolic_history[user_id]) == len(messages)
    
    # Test symbolic drift calculation
    if len(results) > 1:
        drift = processor.calculate_drift(results[-1], processor._symbolic_history[user_id])
        assert isinstance(drift, float)
        assert 0.0 <= drift <= 1.0

# Cultural Adaptation Testing
@pytest.mark.asyncio
async def test_cultural_adaptation(comprehensive_canopy_processor):
    """Test cultural adaptation features"""
    processor = comprehensive_canopy_processor
    
    # Test different cultural contexts
    cultural_contexts = [
        {"cultural_context": "western", "language": "en"},
        {"cultural_context": "eastern", "language": "zh"},
        {"cultural_context": "indigenous", "language": "na"},
        {"cultural_context": "unknown", "language": "unknown"}
    ]
    
    for context in cultural_contexts:
        result = await processor.extract(
            "I feel connected to nature",
            context=context
        )
        
        assert isinstance(result, SymbolicMapping)
        # Cultural context should influence symbol selection
        # (Implementation detail would check specific adaptations)

# Integration Point Testing
@pytest.mark.asyncio
async def test_veluria_integration(comprehensive_canopy_processor):
    """Test integration with VELURIA crisis detection"""
    processor = comprehensive_canopy_processor
    
    # Mock VELURIA integration
    with patch('src.symbolic.canopy.processor.get_veluria_data') as mock_veluria:
        mock_veluria.return_value = {
            "crisis_indicators": {
                "severity": 0.8,
                "confidence": 0.9
            }
        }
        
        result = await processor.process(
            text="I want to hurt myself",
            user_id="test_user",
            context={"enable_veluria": True}
        )
        
        assert isinstance(result, SymbolicMapping)
        # Should have called VELURIA integration
        mock_veluria.assert_called_once()

@pytest.mark.asyncio
async def test_root_integration(comprehensive_canopy_processor):
    """Test integration with ROOT analysis system"""
    processor = comprehensive_canopy_processor
    
    # Mock ROOT integration
    with patch('src.symbolic.canopy.processor.get_root_analysis') as mock_root:
        mock_root.return_value = {
            "baseline": 0.3,
            "deviation": 0.2,
            "trend": "improving"
        }
        
        result = await processor.process(
            text="I'm feeling better today",
            user_id="test_user",
            context={"enable_root": True}
        )
        
        assert isinstance(result, SymbolicMapping)
        # Should have called ROOT integration
        mock_root.assert_called_once()

# Performance Edge Case Testing
@pytest.mark.asyncio
async def test_performance_edge_cases(comprehensive_canopy_processor):
    """Test performance with edge case scenarios"""
    processor = comprehensive_canopy_processor
    
    # Test very large input
    large_text = "I feel overwhelmed. " * 1000
    result = await processor.extract(large_text)
    assert isinstance(result, SymbolicMapping)
    
    # Test very complex context
    complex_context = {
        "previous_symbols": ["symbol_" + str(i) for i in range(100)],
        "nested_data": {"level_" + str(i): {"data": list(range(100))} for i in range(10)},
        "large_list": list(range(1000))
    }
    
    result = await processor.extract("Test", context=complex_context)
    assert isinstance(result, SymbolicMapping)

# API Contract Testing
@pytest.mark.asyncio
async def test_api_contracts(comprehensive_canopy_processor):
    """Test that API contracts are maintained"""
    processor = comprehensive_canopy_processor
    
    # Test extract method contract
    result = await processor.extract("test")
    assert hasattr(result, 'primary_symbol')
    assert hasattr(result, 'archetype')
    assert hasattr(result, 'alternative_symbols')
    assert hasattr(result, 'valence')
    assert hasattr(result, 'arousal')
    assert hasattr(result, 'metaphors')
    assert hasattr(result, 'confidence')
    assert hasattr(result, 'timestamp')
    
    # Test process method contract
    result = await processor.process("test", "user_id")
    assert isinstance(result, SymbolicMapping)
    
    # Test that all methods return appropriate types
    assert isinstance(result.metaphors, list)
    assert all(isinstance(m, EmotionalMetaphor) for m in result.metaphors)
    assert isinstance(result.alternative_symbols, list)
    assert all(isinstance(s, str) for s in result.alternative_symbols) 