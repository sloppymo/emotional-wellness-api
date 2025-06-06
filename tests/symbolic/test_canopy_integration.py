"""
Integration tests for CANOPY system, focusing on SYLVA integration,
performance, and complex scenarios.
"""

import pytest
from datetime import datetime, timedelta
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

from src.symbolic.canopy import CanopyProcessor
from src.symbolic.adapters.sylva_adapter import SylvaAdapter
from src.models.emotional_state import SymbolicMapping, EmotionalMetaphor
from src.models.sylva import SylvaContext, ProcessingResult

# Test data generators
def create_symbolic_mapping(
    symbol: str,
    archetype: str,
    valence: float,
    arousal: float,
    timestamp: datetime = None
) -> SymbolicMapping:
    """Create a test symbolic mapping"""
    return SymbolicMapping(
        primary_symbol=symbol,
        archetype=archetype,
        alternative_symbols=[f"{symbol}_alt1", f"{symbol}_alt2"],
        valence=valence,
        arousal=arousal,
        metaphors=[
            EmotionalMetaphor(
                text=f"test metaphor with {symbol}",
                symbol=symbol,
                confidence=0.9
            )
        ],
        confidence=0.9,
        timestamp=timestamp or datetime.now()
    )

def create_test_history(days: int = 7) -> List[SymbolicMapping]:
    """Create test history data"""
    now = datetime.now()
    symbols = ["water", "fire", "earth", "air", "path", "mountain", "tree"]
    archetypes = ["hero", "shadow", "mentor", "trickster", "self", "anima", "sage"]
    
    return [
        create_symbolic_mapping(
            symbols[i % len(symbols)],
            archetypes[i % len(archetypes)],
            valence=(i % 10) / 10.0,
            arousal=((i + 5) % 10) / 10.0,
            timestamp=now - timedelta(days=days-i)
        )
        for i in range(days)
    ]

# Test fixtures
@pytest.fixture
def canopy_processor():
    """Create a CANOPY processor instance"""
    processor = CanopyProcessor(api_key="test_key")
    processor._symbolic_history["test_user"] = create_test_history()
    return processor

@pytest.fixture
def sylva_adapter():
    """Create a SYLVA adapter instance"""
    return SylvaAdapter()

@pytest.fixture
def mock_sylva_context():
    """Create a mock SYLVA context"""
    return SylvaContext(
        user_id="test_user",
        session_id="test_session",
        timestamp=datetime.now(),
        processing_flags={"enable_cultural_adaptation": True}
    )

# SYLVA Integration Tests
@pytest.mark.asyncio
async def test_sylva_integration_basic(canopy_processor, sylva_adapter, mock_sylva_context):
    """Test basic SYLVA integration functionality"""
    # Process through SYLVA
    result = await sylva_adapter.process(
        processor=canopy_processor,
        context=mock_sylva_context,
        input_text="I feel like a mountain standing alone in the storm"
    )
    
    assert isinstance(result, ProcessingResult)
    assert result.success
    assert result.output is not None
    assert isinstance(result.output, SymbolicMapping)
    assert result.processing_time > 0

@pytest.mark.asyncio
async def test_sylva_integration_error_handling(
    canopy_processor,
    sylva_adapter,
    mock_sylva_context
):
    """Test SYLVA integration error handling"""
    # Test with invalid input
    result = await sylva_adapter.process(
        processor=canopy_processor,
        context=mock_sylva_context,
        input_text=None
    )
    assert not result.success
    assert result.error is not None
    
    # Test with processing error
    with patch.object(canopy_processor.extractor, "extract", side_effect=Exception("Test error")):
        result = await sylva_adapter.process(
            processor=canopy_processor,
            context=mock_sylva_context,
            input_text="test"
        )
        assert not result.success
        assert "Test error" in str(result.error)

@pytest.mark.asyncio
async def test_sylva_integration_cultural_adaptation(
    canopy_processor,
    sylva_adapter,
    mock_sylva_context
):
    """Test cultural adaptation in SYLVA integration"""
    # Test with different cultural contexts
    contexts = ["western", "eastern", "indigenous"]
    results = []
    
    for culture in contexts:
        mock_sylva_context.processing_flags["cultural_context"] = culture
        result = await sylva_adapter.process(
            processor=canopy_processor,
            context=mock_sylva_context,
            input_text="The mountain represents my journey"
        )
        results.append(result.output)
    
    # Verify different cultural interpretations
    symbols = [r.primary_symbol for r in results]
    assert len(set(symbols)) > 1  # Should have different interpretations
    
    # Verify cultural cache
    assert len(canopy_processor._cultural_cache) > 0

# Performance and Concurrency Tests
@pytest.mark.asyncio
async def test_concurrent_processing(canopy_processor, sylva_adapter, mock_sylva_context):
    """Test concurrent processing capabilities"""
    # Create multiple processing tasks
    tasks = []
    for i in range(10):
        task = sylva_adapter.process(
            processor=canopy_processor,
            context=mock_sylva_context,
            input_text=f"Test input {i}"
        )
        tasks.append(task)
    
    # Run concurrently
    results = await asyncio.gather(*tasks)
    
    assert len(results) == 10
    assert all(r.success for r in results)
    assert len(set(r.processing_time for r in results)) > 1  # Times should vary

@pytest.mark.asyncio
async def test_large_history_performance(canopy_processor):
    """Test performance with large history sets"""
    # Create large history
    large_history = create_test_history(days=100)
    canopy_processor._symbolic_history["test_user"] = large_history
    
    start_time = datetime.now()
    patterns = await canopy_processor._analyze_patterns(
        large_history[-1],
        "test_user"
    )
    processing_time = (datetime.now() - start_time).total_seconds()
    
    assert processing_time < 1.0  # Should process in under 1 second
    assert "recurring_symbols" in patterns
    assert len(patterns["recurring_symbols"]) > 0

# Cache Management Tests
@pytest.mark.asyncio
async def test_cache_invalidation(canopy_processor):
    """Test cache invalidation and management"""
    # Fill cache
    for i in range(canopy_processor.MAX_CACHE_SIZE + 10):
        key = f"test_key_{i}"
        canopy_processor._cultural_cache[key] = {
            "timestamp": datetime.now(),
            "data": f"test_data_{i}"
        }
    
    # Verify cache size is maintained
    assert len(canopy_processor._cultural_cache) <= canopy_processor.MAX_CACHE_SIZE
    
    # Verify oldest entries were removed
    assert "test_key_0" not in canopy_processor._cultural_cache
    assert f"test_key_{canopy_processor.MAX_CACHE_SIZE + 9}" in canopy_processor._cultural_cache

@pytest.mark.asyncio
async def test_complex_pattern_recognition(canopy_processor):
    """Test complex pattern recognition capabilities"""
    # Create cyclic pattern
    pattern = [
        create_symbolic_mapping("water", "self", 0.5, 0.5),
        create_symbolic_mapping("fire", "shadow", -0.3, 0.8),
        create_symbolic_mapping("water", "self", 0.5, 0.5),
        create_symbolic_mapping("fire", "shadow", -0.3, 0.8)
    ]
    canopy_processor._symbolic_history["test_user"] = pattern
    
    cycles = canopy_processor._find_cycles(pattern)
    assert len(cycles) > 0
    assert any(c["length"] == 2 for c in cycles)

@pytest.mark.asyncio
async def test_veluria_integration(canopy_processor):
    """Test integration with VELURIA system"""
    # Mock VELURIA response
    veluria_data = {
        "crisis_indicators": {
            "severity": 0.2,
            "confidence": 0.8
        }
    }
    
    with patch("src.symbolic.canopy.processor.get_veluria_data", return_value=veluria_data):
        result = await canopy_processor.process(
            text="I feel overwhelmed but managing",
            user_id="test_user",
            context={"enable_veluria": True}
        )
        
        assert result.valence < 0  # Negative emotion detected
        assert result.confidence > 0.7  # High confidence due to VELURIA

@pytest.mark.asyncio
async def test_root_integration(canopy_processor):
    """Test integration with ROOT system"""
    # Mock ROOT analysis
    root_data = {
        "baseline": 0.5,
        "deviation": 0.2,
        "trend": "improving"
    }
    
    with patch("src.symbolic.canopy.processor.get_root_analysis", return_value=root_data):
        result = await canopy_processor.process(
            text="I'm feeling more stable lately",
            user_id="test_user",
            context={"enable_root": True}
        )
        
        assert result.confidence > 0.8  # High confidence with ROOT data
        assert "baseline" in result.metaphors[0].text.lower()

@pytest.mark.asyncio
async def test_advanced_error_handling(canopy_processor, sylva_adapter, mock_sylva_context):
    """Test advanced error handling scenarios"""
    # Test timeout handling
    async def slow_process(*args, **kwargs):
        await asyncio.sleep(2)
        return create_symbolic_mapping("timeout", "error", 0, 0)
    
    with patch.object(canopy_processor.extractor, "extract", side_effect=slow_process):
        with pytest.raises(asyncio.TimeoutError):
            async with asyncio.timeout(1):
                await sylva_adapter.process(
                    processor=canopy_processor,
                    context=mock_sylva_context,
                    input_text="test"
                )
    
    # Test partial failure handling
    def partial_failure(*args, **kwargs):
        if "error" in args[0].lower():
            raise ValueError("Test error")
        return create_symbolic_mapping("success", "test", 0.5, 0.5)
    
    with patch.object(canopy_processor.extractor, "extract", side_effect=partial_failure):
        # This should succeed
        result1 = await sylva_adapter.process(
            processor=canopy_processor,
            context=mock_sylva_context,
            input_text="success test"
        )
        assert result1.success
        
        # This should fail gracefully
        result2 = await sylva_adapter.process(
            processor=canopy_processor,
            context=mock_sylva_context,
            input_text="error test"
        )
        assert not result2.success
        assert "Test error" in str(result2.error)

@pytest.mark.asyncio
async def test_memory_optimization(canopy_processor):
    """Test memory optimization features"""
    # Fill history with large dataset
    large_history = create_test_history(days=1000)
    canopy_processor._symbolic_history["test_user"] = large_history
    
    # Monitor memory usage
    import psutil
    process = psutil.Process()
    initial_memory = process.memory_info().rss
    
    # Perform intensive operation
    await canopy_processor.process(
        text="test",
        user_id="test_user",
        context={"full_analysis": True}
    )
    
    final_memory = process.memory_info().rss
    memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB
    
    assert memory_increase < 100  # Should not increase memory by more than 100MB