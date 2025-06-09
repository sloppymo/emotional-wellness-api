from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import hashlib
import json
import random
from redis.asyncio import Redis
from enum import Enum

class TestStatus(Enum):
    """A/B test status."""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"

@dataclass
class ABTestConfig:
    """A/B test configuration."""
    name: str
    description: str
    variants: Dict[str, Dict[str, Any]]
    traffic_allocation: Dict[str, float]
    start_date: datetime
    end_date: datetime
    status: TestStatus
    success_metrics: List[str]
    minimum_sample_size: int = 1000
    confidence_level: float = 0.95

@dataclass
class TestResult:
    """A/B test result."""
    variant: str
    metric: str
    value: float
    sample_size: int
    confidence_interval: tuple

class ABTesting:
    """A/B testing framework for rate limiting strategies."""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.tests_key = "ab_tests"
        self.results_key = "ab_test_results:{}"
        self.assignments_key = "ab_test_assignments:{}"
    
    async def create_test(self, config: ABTestConfig) -> bool:
        """Create a new A/B test."""
        try:
            tests_data = await self.redis.get(self.tests_key)
            tests = json.loads(tests_data) if tests_data else {}
            
            # Validate traffic allocation
            if sum(config.traffic_allocation.values()) != 1.0:
                raise ValueError("Traffic allocation must sum to 1.0")
            
            tests[config.name] = {
                **asdict(config),
                "start_date": config.start_date.isoformat(),
                "end_date": config.end_date.isoformat(),
                "status": config.status.value
            }
            
            await self.redis.set(self.tests_key, json.dumps(tests))
            return True
        except Exception as e:
            print(f"Failed to create test {config.name}: {e}")
            return False
    
    async def get_variant(self, test_name: str, client_id: str) -> Optional[str]:
        """Get the variant assignment for a client."""
        # Check if test is active
        test_config = await self._get_test_config(test_name)
        if not test_config or test_config["status"] != TestStatus.RUNNING.value:
            return None
        
        # Check existing assignment
        assignment_key = self.assignments_key.format(test_name)
        existing_assignment = await self.redis.hget(assignment_key, client_id)
        if existing_assignment:
            return existing_assignment.decode()
        
        # Create new assignment
        variant = self._assign_variant(client_id, test_config["traffic_allocation"])
        await self.redis.hset(assignment_key, client_id, variant)
        
        return variant
    
    def _assign_variant(self, client_id: str, traffic_allocation: Dict[str, float]) -> str:
        """Assign a variant based on traffic allocation."""
        # Use consistent hashing for stable assignments - Security fix: Use SHA-256 instead of MD5
        hash_value = int(hashlib.sha256(client_id.encode()).hexdigest(), 16)
        random_value = (hash_value % 10000) / 10000.0
        
        cumulative = 0.0
        for variant, allocation in traffic_allocation.items():
            cumulative += allocation
            if random_value <= cumulative:
                return variant
        
        return list(traffic_allocation.keys())[-1]
    
    async def record_metric(
        self,
        test_name: str,
        client_id: str,
        metric_name: str,
        value: float
    ):
        """Record a metric for A/B testing."""
        variant = await self.get_variant(test_name, client_id)
        if not variant:
            return
        
        results_key = self.results_key.format(test_name)
        metric_key = f"{variant}:{metric_name}"
        
        # Store individual measurement
        await self.redis.lpush(
            f"{results_key}:{metric_key}",
            json.dumps({"value": value, "timestamp": datetime.now().isoformat()})
        )
        await self.redis.expire(f"{results_key}:{metric_key}", 86400 * 30)  # 30 days
    
    async def get_test_results(self, test_name: str) -> Dict[str, List[TestResult]]:
        """Get A/B test results with statistical analysis."""
        test_config = await self._get_test_config(test_name)
        if not test_config:
            return {}
        
        results = {}
        results_key = self.results_key.format(test_name)
        
        for variant in test_config["variants"].keys():
            variant_results = []
            
            for metric in test_config["success_metrics"]:
                metric_key = f"{variant}:{metric}"
                data_key = f"{results_key}:{metric_key}"
                
                # Get all measurements
                measurements_data = await self.redis.lrange(data_key, 0, -1)
                measurements = [
                    json.loads(data)["value"]
                    for data in measurements_data
                ]
                
                if measurements:
                    import numpy as np
                    from scipy import stats
                    
                    mean_value = np.mean(measurements)
                    sample_size = len(measurements)
                    
                    # Calculate confidence interval
                    if sample_size > 1:
                        std_error = stats.sem(measurements)
                        confidence_interval = stats.t.interval(
                            test_config["confidence_level"],
                            sample_size - 1,
                            loc=mean_value,
                            scale=std_error
                        )
                    else:
                        confidence_interval = (mean_value, mean_value)
                    
                    variant_results.append(TestResult(
                        variant=variant,
                        metric=metric,
                        value=mean_value,
                        sample_size=sample_size,
                        confidence_interval=confidence_interval
                    ))
            
            results[variant] = variant_results
        
        return results
    
    async def _get_test_config(self, test_name: str) -> Optional[Dict[str, Any]]:
        """Get test configuration."""
        tests_data = await self.redis.get(self.tests_key)
        if not tests_data:
            return None
        
        tests = json.loads(tests_data)
        return tests.get(test_name)
    
    async def stop_test(self, test_name: str) -> bool:
        """Stop a running test."""
        tests_data = await self.redis.get(self.tests_key)
        if not tests_data:
            return False
        
        tests = json.loads(tests_data)
        if test_name in tests:
            tests[test_name]["status"] = TestStatus.COMPLETED.value
            await self.redis.set(self.tests_key, json.dumps(tests))
            return True
        
        return False 