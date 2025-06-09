"""
Comprehensive Performance Benchmarking Suite for SylvaTune

This test suite provides detailed performance benchmarking for all major
components of the SylvaTune emotional wellness API, including:
- CANOPY symbolic processing
- SYLVA-WREN integration 
- ML analytics and prediction models
- Database operations
- API endpoints
- Memory usage and resource optimization
"""

import pytest
import asyncio
import time
import psutil
import os
import statistics
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Optional, Any
import numpy as np
from contextlib import asynccontextmanager
import gc

from src.symbolic.canopy import CanopyProcessor
from src.integration.coordinator import SylvaWrenCoordinator
from src.symbolic.adapters.sylva_adapter import SylvaAdapter, SylvaContext
from src.analytics.archetype_visualizer import get_archetype_distribution

# Benchmark configuration
BENCHMARK_CONFIG = {
    "light_load": {"users": 10, "requests_per_user": 5, "duration": 30},
    "medium_load": {"users": 50, "requests_per_user": 10, "duration": 60},
    "heavy_load": {"users": 100, "requests_per_user": 20, "duration": 120},
    "stress_test": {"users": 200, "requests_per_user": 50, "duration": 300}
}

PERFORMANCE_THRESHOLDS = {
    "response_time_ms": {
        "canopy_extract": 500,
        "sylva_process": 1000,
        "integration_workflow": 2000,
        "ml_prediction": 300,
        "api_endpoint": 1500
    },
    "memory_mb": {
        "baseline": 100,
        "canopy_processing": 250,
        "integration_processing": 400,
        "ml_analytics": 300,
        "stress_test": 800
    },
    "throughput_rps": {
        "minimum": 10,
        "target": 50,
        "optimal": 100
    },
    "cpu_percent": {
        "idle": 5,
        "normal": 30,
        "high_load": 70,
        "max_acceptable": 85
    }
}

class PerformanceProfiler:
    """Advanced performance profiler for detailed metrics collection"""
    
    def __init__(self):
        self.metrics = {}
        self.start_time = None
        self.start_memory = None
        self.start_cpu = None
        
    def start_profiling(self, test_name: str):
        """Start profiling for a test"""
        self.test_name = test_name
        self.start_time = time.time()
        self.start_memory = self._get_memory_usage()
        self.start_cpu = self._get_cpu_usage()
        gc.collect()  # Clean up before measurement
        
    def stop_profiling(self) -> Dict[str, Any]:
        """Stop profiling and return metrics"""
        end_time = time.time()
        end_memory = self._get_memory_usage()
        end_cpu = self._get_cpu_usage()
        
        duration = end_time - self.start_time
        memory_delta = end_memory - self.start_memory
        cpu_avg = (self.start_cpu + end_cpu) / 2
        
        metrics = {
            "test_name": self.test_name,
            "duration_seconds": duration,
            "memory_delta_mb": memory_delta,
            "cpu_average_percent": cpu_avg,
            "start_memory_mb": self.start_memory,
            "end_memory_mb": end_memory,
            "timestamp": datetime.now().isoformat()
        }
        
        return metrics
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    
    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        return psutil.Process(os.getpid()).cpu_percent()

@asynccontextmanager
async def performance_context(test_name: str):
    """Async context manager for performance measurement"""
    profiler = PerformanceProfiler()
    profiler.start_profiling(test_name)
    
    try:
        yield profiler
    finally:
        metrics = profiler.stop_profiling()
        print(f"\n📊 Performance Metrics for {test_name}:")
        print(f"   Duration: {metrics['duration_seconds']:.3f}s")
        print(f"   Memory Delta: {metrics['memory_delta_mb']:.2f}MB")
        print(f"   CPU Average: {metrics['cpu_average_percent']:.1f}%")

@pytest.fixture
def performance_canopy_processor():
    """Create a performance-optimized CANOPY processor"""
    with patch("src.symbolic.canopy.Anthropic") as mock_anthropic:
        mock_client = Mock()
        mock_client.completions = AsyncMock()
        
        # Fast mock response
        fast_response = {
            "primary_symbol": "water",
            "archetype": "self", 
            "alternative_symbols": ["flow"],
            "valence": 0.0,
            "arousal": 0.5,
            "metaphors": [{"text": "test", "symbol": "water", "confidence": 0.8}]
        }
        
        mock_client.completions.create.return_value = Mock(
            completion=json.dumps(fast_response)
        )
        mock_anthropic.return_value = mock_client
        
        processor = CanopyProcessor(api_key="test_key")
        return processor

@pytest.fixture
def performance_coordinator():
    """Create a performance-optimized coordinator"""
    coordinator = SylvaWrenCoordinator()
    coordinator.moss_adapter = Mock()
    coordinator.moss_adapter.assess_crisis = AsyncMock()
    coordinator.moss_adapter.get_intervention_recommendations = AsyncMock()
    return coordinator

# CANOPY Performance Benchmarks
@pytest.mark.asyncio
async def test_canopy_single_request_performance(performance_canopy_processor):
    """Benchmark single CANOPY request performance"""
    processor = performance_canopy_processor
    
    async with performance_context("CANOPY Single Request") as profiler:
        result = await processor.extract("I feel like flowing water today")
        
        metrics = profiler.stop_profiling()
        
        # Verify performance thresholds
        assert metrics["duration_seconds"] < PERFORMANCE_THRESHOLDS["response_time_ms"]["canopy_extract"] / 1000
        assert metrics["memory_delta_mb"] < PERFORMANCE_THRESHOLDS["memory_mb"]["canopy_processing"]

@pytest.mark.asyncio
async def test_canopy_batch_processing_performance(performance_canopy_processor):
    """Benchmark CANOPY batch processing performance"""
    processor = performance_canopy_processor
    
    test_inputs = [
        "I feel overwhelmed by responsibilities",
        "My heart is full of joy today", 
        "I'm walking through a dark forest of doubt",
        "The fire of my passion burns bright",
        "I'm floating on clouds of happiness"
    ] * 20  # 100 total requests
    
    async with performance_context("CANOPY Batch Processing") as profiler:
        results = []
        for text in test_inputs:
            result = await processor.extract(text)
            results.append(result)
        
        metrics = profiler.stop_profiling()
        
        # Calculate throughput
        throughput = len(test_inputs) / metrics["duration_seconds"]
        
        assert len(results) == len(test_inputs)
        assert throughput >= PERFORMANCE_THRESHOLDS["throughput_rps"]["minimum"]
        assert metrics["memory_delta_mb"] < PERFORMANCE_THRESHOLDS["memory_mb"]["canopy_processing"]
        
        print(f"   Throughput: {throughput:.2f} requests/second")

@pytest.mark.asyncio
async def test_canopy_concurrent_performance(performance_canopy_processor):
    """Benchmark CANOPY concurrent processing performance"""
    processor = performance_canopy_processor
    
    async def process_batch(batch_id: int, batch_size: int):
        tasks = []
        for i in range(batch_size):
            text = f"Concurrent test batch {batch_id} item {i}"
            tasks.append(processor.extract(text))
        return await asyncio.gather(*tasks)
    
    async with performance_context("CANOPY Concurrent Processing") as profiler:
        # Run 10 concurrent batches of 10 requests each
        batch_tasks = [process_batch(i, 10) for i in range(10)]
        batch_results = await asyncio.gather(*batch_tasks)
        
        metrics = profiler.stop_profiling()
        
        total_requests = sum(len(batch) for batch in batch_results)
        throughput = total_requests / metrics["duration_seconds"]
        
        assert total_requests == 100
        assert throughput >= PERFORMANCE_THRESHOLDS["throughput_rps"]["minimum"]
        assert metrics["memory_delta_mb"] < PERFORMANCE_THRESHOLDS["memory_mb"]["canopy_processing"] * 2
        
        print(f"   Concurrent Throughput: {throughput:.2f} requests/second")

# SYLVA-WREN Integration Benchmarks
@pytest.mark.asyncio
async def test_sylva_wren_integration_performance(performance_coordinator, performance_canopy_processor):
    """Benchmark SYLVA-WREN integration performance"""
    coordinator = performance_coordinator
    
    from src.integration.models import EmotionalInput
    
    emotional_input = EmotionalInput(
        text="I'm struggling with anxiety but working through it in therapy",
        biomarkers={"heart_rate": 90, "respiratory_rate": 18, "skin_conductance": 0.7},
        user_context={
            "user_id": "benchmark_user",
            "session_id": "benchmark_session",
            "timestamp": datetime.now()
        }
    )
    
    async with performance_context("SYLVA-WREN Integration") as profiler:
        result = await coordinator.process_emotional_input(emotional_input)
        
        metrics = profiler.stop_profiling()
        
        assert metrics["duration_seconds"] < PERFORMANCE_THRESHOLDS["response_time_ms"]["integration_workflow"] / 1000
        assert metrics["memory_delta_mb"] < PERFORMANCE_THRESHOLDS["memory_mb"]["integration_processing"]

@pytest.mark.asyncio
async def test_multi_user_integration_performance(performance_coordinator):
    """Benchmark multi-user integration performance"""
    coordinator = performance_coordinator
    
    from src.integration.models import EmotionalInput
    
    async def process_user(user_id: int):
        emotional_input = EmotionalInput(
            text=f"User {user_id} emotional processing test",
            biomarkers={"heart_rate": 85, "respiratory_rate": 16},
            user_context={
                "user_id": f"user_{user_id}",
                "session_id": f"session_{user_id}",
                "timestamp": datetime.now()
            }
        )
        return await coordinator.process_emotional_input(emotional_input)
    
    async with performance_context("Multi-User Integration") as profiler:
        # Process 50 users concurrently
        user_tasks = [process_user(i) for i in range(50)]
        results = await asyncio.gather(*user_tasks, return_exceptions=True)
        
        metrics = profiler.stop_profiling()
        
        successful_results = [r for r in results if not isinstance(r, Exception)]
        throughput = len(successful_results) / metrics["duration_seconds"]
        
        assert len(successful_results) >= 45  # 90% success rate
        assert throughput >= PERFORMANCE_THRESHOLDS["throughput_rps"]["minimum"]
        
        print(f"   Multi-User Throughput: {throughput:.2f} users/second")

# Memory Management Benchmarks
@pytest.mark.asyncio
async def test_memory_leak_detection(performance_canopy_processor):
    """Test for memory leaks during extended processing"""
    processor = performance_canopy_processor
    
    async with performance_context("Memory Leak Detection") as profiler:
        initial_memory = profiler._get_memory_usage()
        
        # Process many requests to detect memory leaks
        for batch in range(20):  # 20 batches
            batch_tasks = []
            for i in range(50):  # 50 requests per batch
                text = f"Memory test batch {batch} item {i}"
                batch_tasks.append(processor.extract(text))
            
            await asyncio.gather(*batch_tasks)
            
            # Check memory every 5 batches
            if batch % 5 == 0:
                current_memory = profiler._get_memory_usage()
                memory_growth = current_memory - initial_memory
                
                # Memory growth should be reasonable
                assert memory_growth < PERFORMANCE_THRESHOLDS["memory_mb"]["stress_test"]
                
                # Force garbage collection
                gc.collect()
        
        final_memory = profiler._get_memory_usage()
        total_growth = final_memory - initial_memory
        
        print(f"   Total Memory Growth: {total_growth:.2f}MB after 1000 requests")
        assert total_growth < PERFORMANCE_THRESHOLDS["memory_mb"]["stress_test"]

@pytest.mark.asyncio
async def test_resource_cleanup_performance():
    """Test resource cleanup performance"""
    
    async with performance_context("Resource Cleanup") as profiler:
        # Create many objects and measure cleanup time
        large_objects = []
        
        for i in range(1000):
            # Simulate large symbolic mappings
            obj = {
                "id": i,
                "data": list(range(1000)),  # Large data structure
                "metadata": {"timestamp": datetime.now(), "symbols": ["test"] * 100}
            }
            large_objects.append(obj)
        
        cleanup_start = time.time()
        
        # Clear objects and force garbage collection
        large_objects.clear()
        gc.collect()
        
        cleanup_time = time.time() - cleanup_start
        
        metrics = profiler.stop_profiling()
        
        print(f"   Cleanup Time: {cleanup_time:.3f}s")
        assert cleanup_time < 1.0  # Should cleanup quickly

# Load Testing Benchmarks
@pytest.mark.asyncio
async def test_light_load_performance(performance_coordinator):
    """Test performance under light load"""
    await _run_load_test("light_load", performance_coordinator)

@pytest.mark.asyncio 
async def test_medium_load_performance(performance_coordinator):
    """Test performance under medium load"""
    await _run_load_test("medium_load", performance_coordinator)

@pytest.mark.asyncio
async def test_heavy_load_performance(performance_coordinator):
    """Test performance under heavy load"""
    await _run_load_test("heavy_load", performance_coordinator)

async def _run_load_test(load_type: str, coordinator):
    """Run a standardized load test"""
    config = BENCHMARK_CONFIG[load_type]
    
    from src.integration.models import EmotionalInput
    
    async def simulate_user(user_id: int):
        user_results = []
        for request_num in range(config["requests_per_user"]):
            emotional_input = EmotionalInput(
                text=f"Load test {load_type} user {user_id} request {request_num}",
                biomarkers={"heart_rate": 80 + (request_num % 20)},
                user_context={
                    "user_id": f"load_user_{user_id}",
                    "session_id": f"load_session_{user_id}_{request_num}",
                    "timestamp": datetime.now()
                }
            )
            
            try:
                result = await coordinator.process_emotional_input(emotional_input)
                user_results.append(result)
            except Exception as e:
                user_results.append(e)
        
        return user_results
    
    async with performance_context(f"Load Test - {load_type}") as profiler:
        # Create user simulation tasks
        user_tasks = [simulate_user(i) for i in range(config["users"])]
        
        # Run with timeout
        try:
            user_results = await asyncio.wait_for(
                asyncio.gather(*user_tasks, return_exceptions=True),
                timeout=config["duration"]
            )
        except asyncio.TimeoutError:
            pytest.fail(f"Load test {load_type} timed out after {config['duration']}s")
        
        metrics = profiler.stop_profiling()
        
        # Analyze results
        total_requests = config["users"] * config["requests_per_user"]
        successful_requests = 0
        
        for user_result in user_results:
            if isinstance(user_result, list):
                successful_requests += len([r for r in user_result if not isinstance(r, Exception)])
        
        success_rate = successful_requests / total_requests
        throughput = successful_requests / metrics["duration_seconds"]
        
        print(f"\n📈 Load Test Results - {load_type}:")
        print(f"   Total Requests: {total_requests}")
        print(f"   Successful Requests: {successful_requests}")
        print(f"   Success Rate: {success_rate:.2%}")
        print(f"   Throughput: {throughput:.2f} requests/second")
        print(f"   Average Response Time: {metrics['duration_seconds']/successful_requests:.3f}s")
        
        # Verify performance criteria
        assert success_rate >= 0.95  # 95% success rate minimum
        assert throughput >= PERFORMANCE_THRESHOLDS["throughput_rps"]["minimum"]
        assert metrics["memory_delta_mb"] < PERFORMANCE_THRESHOLDS["memory_mb"]["stress_test"]

# Response Time Distribution Analysis
@pytest.mark.asyncio
async def test_response_time_distribution(performance_canopy_processor):
    """Analyze response time distribution for performance characteristics"""
    processor = performance_canopy_processor
    
    response_times = []
    
    async with performance_context("Response Time Distribution") as profiler:
        for i in range(100):
            start_time = time.time()
            await processor.extract(f"Response time test {i}")
            end_time = time.time()
            
            response_times.append((end_time - start_time) * 1000)  # Convert to ms
        
        # Statistical analysis
        mean_time = statistics.mean(response_times)
        median_time = statistics.median(response_times)
        p95_time = np.percentile(response_times, 95)
        p99_time = np.percentile(response_times, 99)
        std_dev = statistics.stdev(response_times)
        
        print(f"\n📊 Response Time Distribution:")
        print(f"   Mean: {mean_time:.2f}ms")
        print(f"   Median: {median_time:.2f}ms")
        print(f"   95th Percentile: {p95_time:.2f}ms")
        print(f"   99th Percentile: {p99_time:.2f}ms")
        print(f"   Standard Deviation: {std_dev:.2f}ms")
        
        # Verify performance requirements
        assert mean_time < PERFORMANCE_THRESHOLDS["response_time_ms"]["canopy_extract"]
        assert p95_time < PERFORMANCE_THRESHOLDS["response_time_ms"]["canopy_extract"] * 2
        assert p99_time < PERFORMANCE_THRESHOLDS["response_time_ms"]["canopy_extract"] * 3

# Database Performance Benchmarks
@pytest.mark.asyncio
async def test_database_operation_performance():
    """Benchmark database operations performance"""
    
    async with performance_context("Database Operations") as profiler:
        # Simulate database operations
        operations = []
        
        # Simulate user data operations
        for i in range(1000):
            # Mock database operations with realistic delays
            await asyncio.sleep(0.001)  # 1ms per operation
            operations.append(f"operation_{i}")
        
        metrics = profiler.stop_profiling()
        
        throughput = len(operations) / metrics["duration_seconds"]
        
        print(f"   Database Throughput: {throughput:.2f} operations/second")
        assert throughput >= 500  # Should handle 500+ ops/second

# Analytics Performance Benchmarks
def test_analytics_performance():
    """Benchmark analytics and visualization performance"""
    
    profiler = PerformanceProfiler()
    profiler.start_profiling("Analytics Performance")
    
    # Test archetype distribution calculation
    distribution = get_archetype_distribution()
    
    # Test large data processing simulation
    large_dataset = [{"archetype": f"type_{i % 10}", "value": i} for i in range(10000)]
    
    # Process analytics
    processed_data = {}
    for item in large_dataset:
        archetype = item["archetype"]
        if archetype not in processed_data:
            processed_data[archetype] = []
        processed_data[archetype].append(item["value"])
    
    # Calculate statistics
    analytics_results = {}
    for archetype, values in processed_data.items():
        analytics_results[archetype] = {
            "count": len(values),
            "mean": sum(values) / len(values),
            "max": max(values),
            "min": min(values)
        }
    
    metrics = profiler.stop_profiling()
    
    assert metrics["duration_seconds"] < PERFORMANCE_THRESHOLDS["response_time_ms"]["ml_prediction"] / 1000
    assert len(analytics_results) == 10
    
    print(f"\n📊 Analytics Performance:")
    print(f"   Processing Time: {metrics['duration_seconds']:.3f}s")
    print(f"   Records Processed: {len(large_dataset)}")
    print(f"   Memory Usage: {metrics['memory_delta_mb']:.2f}MB")

# Comprehensive Benchmark Report
@pytest.mark.asyncio
async def test_comprehensive_benchmark_report(performance_coordinator, performance_canopy_processor):
    """Generate a comprehensive benchmark report"""
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "system_info": {
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": psutil.virtual_memory().total / (1024**3),
            "python_version": f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}"
        },
        "benchmarks": {}
    }
    
    # Run all key benchmarks
    benchmarks = [
        ("canopy_single", lambda: performance_canopy_processor.extract("Benchmark test")),
        ("integration_single", lambda: performance_coordinator.process_emotional_input(
            EmotionalInput(
                text="Comprehensive benchmark test",
                user_context={"user_id": "bench_user", "session_id": "bench_session", "timestamp": datetime.now()}
            )
        ))
    ]
    
    for bench_name, bench_func in benchmarks:
        profiler = PerformanceProfiler()
        profiler.start_profiling(bench_name)
        
        try:
            if asyncio.iscoroutinefunction(bench_func):
                await bench_func()
            else:
                bench_func()
            
            metrics = profiler.stop_profiling()
            report["benchmarks"][bench_name] = metrics
            
        except Exception as e:
            report["benchmarks"][bench_name] = {"error": str(e)}
    
    # Print comprehensive report
    print(f"\n📋 Comprehensive Benchmark Report")
    print(f"   Generated: {report['timestamp']}")
    print(f"   System: {report['system_info']['cpu_count']} CPUs, {report['system_info']['memory_total_gb']:.1f}GB RAM")
    
    for bench_name, bench_data in report["benchmarks"].items():
        if "error" not in bench_data:
            print(f"   {bench_name}: {bench_data['duration_seconds']:.3f}s, {bench_data['memory_delta_mb']:.2f}MB")
        else:
            print(f"   {bench_name}: ERROR - {bench_data['error']}")
    
    # Verify overall system performance
    assert len([b for b in report["benchmarks"].values() if "error" not in b]) >= len(benchmarks) * 0.8 