"""
Enhanced Testing Infrastructure for Emotional Wellness API

This package provides advanced testing capabilities designed to make
testing and debugging as comprehensive and easy as possible.

Key Features:
- Automated test data generation
- Test environment orchestration  
- Real-time test monitoring
- Integration test helpers
- Performance test utilities
- Crisis scenario testing
- Symbolic processing test tools
"""

from .test_orchestrator import TestOrchestrator, create_test_environment
from .test_data_factory import TestDataFactory, generate_test_scenarios
from .integration_test_helpers import IntegrationTestHelper, mock_external_services
from .performance_test_utils import PerformanceTestRunner, benchmark_component
from .crisis_test_scenarios import CrisisTestScenarios, simulate_crisis_event
from .symbolic_test_tools import SymbolicTestHelper, validate_symbolic_processing

__all__ = [
    'TestOrchestrator',
    'create_test_environment',
    'TestDataFactory', 
    'generate_test_scenarios',
    'IntegrationTestHelper',
    'mock_external_services',
    'PerformanceTestRunner',
    'benchmark_component',
    'CrisisTestScenarios',
    'simulate_crisis_event',
    'SymbolicTestHelper',
    'validate_symbolic_processing'
] 