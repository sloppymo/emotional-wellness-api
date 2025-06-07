"""
Performance tests for the CANOPY symbolic processing system.

Tests cover:
1. Load testing
2. Memory usage
3. Response times
4. Cache performance
5. Concurrent processing
6. Resource utilization
"""

import pytest
import asyncio
import time
import psutil
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import numpy as np

from src.symbolic.canopy import CanopyProcessor
from src.models.emotional_state import SymbolicMapping, EmotionalMetaphor

# Performance test constants
LOAD_TEST_SIZE = 100
CONCURRENT_USERS = 50
MEMORY_THRESHOLD_MB = 500
RESPONSE_TIME_THRESHOLD_MS = 1000
CACHE_SIZE_THRESHOLD = 1000

@pytest.fixture
def performance_setup():
    """Set up the system for performance testing"""
    processor = CanopyProcessor(api_key="test_key")
    return processor

def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

# Load Testing
@pytest.mark.asyncio
async def test_load_processing(performance_setup):
    """Test system performance under load"""
    processor = performance_setup
    start_memory = get_memory_usage()
    start_time = time.time()
    
    # Process multiple inputs
    results = []
    for i in range(LOAD_TEST_SIZE):
        result = await processor.process(
            text=f"Test input {i} with some emotional content",
            user_id=f"user_{i}",
            context={"session_id": f"session_{i}"}
        )
        results.append(result)
    
    end_time = time.time()
    end_memory = get_memory_usage()
    
    # Verify results
    assert len(results) == LOAD_TEST_SIZE
    assert all(isinstance(r, SymbolicMapping) for r in results)
    
    # Check performance metrics
    total_time = end_time - start_time
    avg_time = total_time / LOAD_TEST_SIZE
    memory_increase = end_memory - start_memory
    
    assert avg_time < RESPONSE_TIME_THRESHOLD_MS / 1000  # Convert to seconds
    assert memory_increase < MEMORY_THRESHOLD_MB

@pytest.mark.asyncio
async def test_concurrent_processing(performance_setup):
    """Test concurrent processing performance"""
    processor = performance_setup
    start_memory = get_memory_usage()
    start_time = time.time()
    
    # Create concurrent processing tasks
    async def process_user(user_id):
        return await processor.process(
            text=f"Concurrent test for user {user_id}",
            user_id=f"user_{user_id}",
            context={"session_id": f"session_{user_id}"}
        )
    
    # Run concurrent processing
    tasks = [process_user(i) for i in range(CONCURRENT_USERS)]
    results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    end_memory = get_memory_usage()
    
    # Verify results
    assert len(results) == CONCURRENT_USERS
    assert all(isinstance(r, SymbolicMapping) for r in results)
    
    # Check performance metrics
    total_time = end_time - start_time
    avg_time = total_time / CONCURRENT_USERS
    memory_increase = end_memory - start_memory
    
    assert avg_time < RESPONSE_TIME_THRESHOLD_MS / 1000
    assert memory_increase < MEMORY_THRESHOLD_MB

# Cache Performance
@pytest.mark.asyncio
async def test_cache_performance(performance_setup):
    """Test cache performance and memory usage"""
    processor = performance_setup
    start_memory = get_memory_usage()
    
    # Fill cache
    for i in range(CACHE_SIZE_THRESHOLD):
        symbol = f"test_symbol_{i}"
        processor._cultural_cache[symbol] = {
            "timestamp": datetime.now(),
            "data": f"test_data_{i}"
        }
    
    # Test cache hit performance
    start_time = time.time()
    for i in range(100):
        symbol = f"test_symbol_{i % CACHE_SIZE_THRESHOLD}"
        _ = processor._cultural_cache.get(symbol)
    cache_hit_time = time.time() - start_time
    
    # Test cache miss performance
    start_time = time.time()
    for i in range(100):
        symbol = f"nonexistent_symbol_{i}"
        _ = processor._cultural_cache.get(symbol)
    cache_miss_time = time.time() - start_time
    
    end_memory = get_memory_usage()
    
    # Verify performance
    assert cache_hit_time < cache_miss_time  # Cache hits should be faster
    assert end_memory - start_memory < MEMORY_THRESHOLD_MB

# Memory Management
@pytest.mark.asyncio
async def test_memory_management(performance_setup):
    """Test memory management and cleanup"""
    processor = performance_setup
    start_memory = get_memory_usage()
    
    # Create large history
    large_history = []
    for i in range(1000):
        large_history.append(
            SymbolicMapping(
                primary_symbol=f"symbol_{i}",
                archetype="self",
                alternative_symbols=[f"alt_{i}"],
                valence=0.5,
                arousal=0.5,
                metaphors=[
                    EmotionalMetaphor(
                        text=f"test metaphor {i}",
                        symbol=f"symbol_{i}",
                        confidence=0.9
                    )
                ],
                confidence=0.9,
                timestamp=datetime.now()
            )
        )
    
    # Add to processor
    processor._symbolic_history["test_user"] = large_history
    
    # Force cleanup
    processor._cleanup_old_states()
    
    end_memory = get_memory_usage()
    
    # Verify cleanup
    assert len(processor._symbolic_history["test_user"]) <= processor.MAX_HISTORY_SIZE
    assert end_memory - start_memory < MEMORY_THRESHOLD_MB

# Response Time Testing
@pytest.mark.asyncio
async def test_response_times(performance_setup):
    """Test response times for different operations"""
    processor = performance_setup
    
    # Test basic processing
    start_time = time.time()
    result = await processor.process(
        text="Simple test input",
        user_id="test_user",
        context={"session_id": "test_session"}
    )
    basic_time = time.time() - start_time
    
    # Test complex processing
    start_time = time.time()
    result = await processor.process(
        text="Complex emotional input with multiple metaphors and deep symbolic meaning",
        user_id="test_user",
        context={
            "session_id": "test_session",
            "enable_veluria": True,
            "enable_root": True
        }
    )
    complex_time = time.time() - start_time
    
    # Verify response times
    assert basic_time < RESPONSE_TIME_THRESHOLD_MS / 1000
    assert complex_time < RESPONSE_TIME_THRESHOLD_MS * 2 / 1000  # Allow more time for complex processing

# Resource Utilization
@pytest.mark.asyncio
async def test_resource_utilization(performance_setup):
    """Test system resource utilization"""
    processor = performance_setup
    start_cpu = psutil.Process(os.getpid()).cpu_percent()
    start_memory = get_memory_usage()
    
    # Run intensive processing
    async def intensive_processing():
        tasks = []
        for i in range(10):
            task = processor.process(
                text=f"Intensive test {i} with complex emotional content and multiple metaphors",
                user_id=f"user_{i}",
                context={
                    "session_id": f"session_{i}",
                    "enable_veluria": True,
                    "enable_root": True
                }
            )
            tasks.append(task)
        return await asyncio.gather(*tasks)
    
    results = await intensive_processing()
    
    end_cpu = psutil.Process(os.getpid()).cpu_percent()
    end_memory = get_memory_usage()
    
    # Verify resource usage
    assert end_cpu - start_cpu < 80  # CPU usage should not spike too high
    assert end_memory - start_memory < MEMORY_THRESHOLD_MB

# Long-running Performance
@pytest.mark.asyncio
async def test_long_running_performance(performance_setup):
    """Test system performance over extended period"""
    processor = performance_setup
    start_memory = get_memory_usage()
    start_time = time.time()
    
    # Run processing over time
    for i in range(100):
        result = await processor.process(
            text=f"Long running test {i}",
            user_id="test_user",
            context={"session_id": "test_session"}
        )
        
        # Check memory periodically
        if i % 10 == 0:
            current_memory = get_memory_usage()
            assert current_memory - start_memory < MEMORY_THRESHOLD_MB
    
    end_time = time.time()
    end_memory = get_memory_usage()
    
    # Verify long-running performance
    total_time = end_time - start_time
    avg_time = total_time / 100
    assert avg_time < RESPONSE_TIME_THRESHOLD_MS / 1000
    assert end_memory - start_memory < MEMORY_THRESHOLD_MB 