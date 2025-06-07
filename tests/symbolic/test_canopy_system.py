"""
System integration tests for the CANOPY symbolic processing system.

Tests cover:
1. Integration with external systems (VELURIA, ROOT)
2. System-wide error handling
3. Cross-component communication
4. System state management
5. End-to-end processing flows
"""

import pytest
from datetime import datetime, timedelta
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import json

from src.symbolic.canopy import CanopyProcessor
from src.symbolic.adapters.sylva_adapter import SylvaAdapter
from src.symbolic.adapters.veluria_adapter import VeluriaAdapter
from src.symbolic.adapters.root_adapter import RootAdapter
from src.models.emotional_state import SymbolicMapping, EmotionalMetaphor
from src.models.sylva import SylvaContext, ProcessingResult
from src.utils.structured_logging import get_logger

@pytest.fixture
def system_setup():
    """Set up the complete system for testing"""
    processor = CanopyProcessor(api_key="test_key")
    sylva_adapter = SylvaAdapter()
    veluria_adapter = VeluriaAdapter()
    root_adapter = RootAdapter()
    
    return {
        "processor": processor,
        "sylva_adapter": sylva_adapter,
        "veluria_adapter": veluria_adapter,
        "root_adapter": root_adapter
    }

@pytest.fixture
def mock_system_state():
    """Create a mock system state"""
    return {
        "user_id": "test_user",
        "session_id": "test_session",
        "timestamp": datetime.now(),
        "context": {
            "enable_veluria": True,
            "enable_root": True,
            "cultural_context": "western"
        }
    }

# System Integration Tests
@pytest.mark.asyncio
async def test_full_system_integration(system_setup, mock_system_state):
    """Test integration of all system components"""
    processor = system_setup["processor"]
    sylva_adapter = system_setup["sylva_adapter"]
    veluria_adapter = system_setup["veluria_adapter"]
    root_adapter = system_setup["root_adapter"]
    
    # Test end-to-end processing
    input_text = "I feel like I'm standing at the edge of a cliff, but I know I can fly"
    
    # Process through SYLVA
    sylva_result = await sylva_adapter.process(
        processor=processor,
        context=SylvaContext(**mock_system_state["context"]),
        input_text=input_text
    )
    assert sylva_result.success
    assert isinstance(sylva_result.output, SymbolicMapping)
    
    # Check VELURIA integration
    veluria_result = await veluria_adapter.analyze(sylva_result.output)
    assert veluria_result is not None
    assert "crisis_indicators" in veluria_result
    
    # Check ROOT integration
    root_result = await root_adapter.analyze(
        user_id=mock_system_state["user_id"],
        current_state=sylva_result.output
    )
    assert root_result is not None
    assert "baseline" in root_result
    assert "deviation" in root_result

@pytest.mark.asyncio
async def test_cross_component_communication(system_setup, mock_system_state):
    """Test communication between system components"""
    processor = system_setup["processor"]
    sylva_adapter = system_setup["sylva_adapter"]
    
    # Test SYLVA to VELURIA communication
    sylva_result = await sylva_adapter.process(
        processor=processor,
        context=SylvaContext(**mock_system_state["context"]),
        input_text="I feel overwhelmed and hopeless"
    )
    
    # Verify crisis detection
    assert sylva_result.output.valence < -0.5
    assert sylva_result.output.arousal > 0.7
    
    # Test SYLVA to ROOT communication
    root_result = await system_setup["root_adapter"].analyze(
        user_id=mock_system_state["user_id"],
        current_state=sylva_result.output
    )
    
    assert root_result["deviation"] > 0.5  # Significant deviation from baseline

@pytest.mark.asyncio
async def test_system_state_management(system_setup, mock_system_state):
    """Test system state management and persistence"""
    processor = system_setup["processor"]
    
    # Test state initialization
    assert processor._symbolic_history.get(mock_system_state["user_id"]) is not None
    
    # Test state updates
    result = await processor.process(
        text="I feel like a mountain",
        user_id=mock_system_state["user_id"],
        context=mock_system_state["context"]
    )
    
    assert len(processor._symbolic_history[mock_system_state["user_id"]]) > 0
    assert processor._cultural_cache.get(result.primary_symbol) is not None
    
    # Test state cleanup
    processor._cleanup_old_states()
    assert len(processor._symbolic_history[mock_system_state["user_id"]]) <= processor.MAX_HISTORY_SIZE

@pytest.mark.asyncio
async def test_system_error_handling(system_setup, mock_system_state):
    """Test system-wide error handling"""
    processor = system_setup["processor"]
    sylva_adapter = system_setup["sylva_adapter"]
    
    # Test SYLVA failure
    with patch.object(sylva_adapter, "process", side_effect=Exception("SYLVA Error")):
        result = await processor.process(
            text="test",
            user_id=mock_system_state["user_id"],
            context=mock_system_state["context"]
        )
        assert isinstance(result, SymbolicMapping)
        assert result.confidence < 0.5
    
    # Test VELURIA failure
    with patch.object(system_setup["veluria_adapter"], "analyze", side_effect=Exception("VELURIA Error")):
        result = await processor.process(
            text="test",
            user_id=mock_system_state["user_id"],
            context=mock_system_state["context"]
        )
        assert isinstance(result, SymbolicMapping)
        assert "crisis_indicators" not in result.metaphors[0].text
    
    # Test ROOT failure
    with patch.object(system_setup["root_adapter"], "analyze", side_effect=Exception("ROOT Error")):
        result = await processor.process(
            text="test",
            user_id=mock_system_state["user_id"],
            context=mock_system_state["context"]
        )
        assert isinstance(result, SymbolicMapping)
        assert "baseline" not in result.metaphors[0].text

@pytest.mark.asyncio
async def test_system_performance(system_setup, mock_system_state):
    """Test system performance under load"""
    processor = system_setup["processor"]
    
    # Test concurrent processing
    async def process_concurrent():
        tasks = []
        for i in range(10):
            task = processor.process(
                text=f"Test input {i}",
                user_id=f"user_{i}",
                context=mock_system_state["context"]
            )
            tasks.append(task)
        return await asyncio.gather(*tasks)
    
    start_time = datetime.now()
    results = await process_concurrent()
    processing_time = (datetime.now() - start_time).total_seconds()
    
    assert len(results) == 10
    assert all(isinstance(r, SymbolicMapping) for r in results)
    assert processing_time < 5.0  # Should process 10 requests in under 5 seconds

@pytest.mark.asyncio
async def test_system_recovery(system_setup, mock_system_state):
    """Test system recovery after failures"""
    processor = system_setup["processor"]
    
    # Test recovery after SYLVA failure
    with patch.object(system_setup["sylva_adapter"], "process", side_effect=Exception("SYLVA Error")):
        result1 = await processor.process(
            text="test1",
            user_id=mock_system_state["user_id"],
            context=mock_system_state["context"]
        )
        assert result1.confidence < 0.5
    
    # Should recover and work normally
    result2 = await processor.process(
        text="test2",
        user_id=mock_system_state["user_id"],
        context=mock_system_state["context"]
    )
    assert result2.confidence > 0.5
    
    # Test recovery after state corruption
    processor._symbolic_history[mock_system_state["user_id"]] = None
    result3 = await processor.process(
        text="test3",
        user_id=mock_system_state["user_id"],
        context=mock_system_state["context"]
    )
    assert isinstance(result3, SymbolicMapping)
    assert processor._symbolic_history[mock_system_state["user_id"]] is not None 