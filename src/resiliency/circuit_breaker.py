"""
Circuit Breaker Pattern Implementation

This module provides a circuit breaker implementation for external API calls
to improve resiliency and prevent cascading failures.
"""
#       .-========-.
#      / _       _ \
#     //|_|     |_|\\ 
#    || |_|     |_| ||
#    ||___________|_||
#    |S_S_S_S_S_S_S_S|
#    |S_S_S_S_S_S_S_S|
#        |       |
#        |       |
#        |_______|
#  FOUND AND FIXED THE BUG
#  THAT NOBODY ELSE COULD

import asyncio
import time
import functools
from enum import Enum
from typing import Dict, Any, Callable, Optional, TypeVar, List, Set, Union, Awaitable
from dataclasses import dataclass, field

from pydantic import BaseModel, Field

from ..utils.structured_logging import get_logger

logger = get_logger(__name__)

# Type definitions
T = TypeVar('T')  # Generic return type
F = TypeVar('F', bound=Callable)  # Generic function type


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation, requests pass through
    OPEN = "open"          # Failing, no requests pass through
    HALF_OPEN = "half_open"  # Testing if system has recovered


class CircuitBreakerMetrics(BaseModel):
    """Circuit breaker performance metrics."""
    success_count: int = 0
    failure_count: int = 0
    rejection_count: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    failure_threshold: int = 5  # Number of failures before opening circuit
    recovery_threshold: int = 3  # Successful calls before closing circuit
    timeout_seconds: int = 30   # How long to keep circuit open
    exclude_exceptions: Set[type] = field(default_factory=set)  # Exceptions to ignore


class CircuitBreaker:
    """
    Circuit breaker implementation for API call resiliency.
    
    Features:
    - Prevents cascading failures from unavailable services
    - Adaptive timeout based on failure recovery
    - Support for async and synchronous functions
    - Configurable thresholds and exception handling
    """
    
    # Class-level registry of circuit breakers by name
    _circuit_registry: Dict[str, 'CircuitBreaker'] = {}
    
    def __init__(self, 
                name: str, 
                config: Optional[CircuitBreakerConfig] = None):
        """
        Initialize a circuit breaker.
        
        Args:
            name: Unique name for this circuit
            config: Configuration for circuit behavior
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        
        self.state = CircuitState.CLOSED
        self.metrics = CircuitBreakerMetrics()
        self.last_state_change = time.time()
        
        self._lock = asyncio.Lock()
        
        # Register this circuit
        CircuitBreaker._circuit_registry[name] = self
        
        logger.info(f"Circuit breaker '{name}' initialized in {self.state} state")
    
    @classmethod
    def get_or_create(cls, name: str, config: Optional[CircuitBreakerConfig] = None) -> 'CircuitBreaker':
        """
        Get existing circuit breaker or create new one.
        
        Args:
            name: Name of the circuit breaker
            config: Optional config for new circuit breaker
            
        Returns:
            Circuit breaker instance
        """
        if name in cls._circuit_registry:
            return cls._circuit_registry[name]
        return cls(name, config)
    
    @classmethod
    def get_all_circuits(cls) -> Dict[str, 'CircuitBreaker']:
        """Get all registered circuit breakers."""
        return cls._circuit_registry
    
    def get_metrics(self) -> CircuitBreakerMetrics:
        """Get current metrics for this circuit."""
        return self.metrics
        
    async def _update_state(self, new_state: CircuitState):
        """Update circuit state with logging."""
        if new_state != self.state:
            old_state = self.state
            self.state = new_state
            self.last_state_change = time.time()
            logger.info(f"Circuit '{self.name}' changed from {old_state} to {new_state}")
        
    async def record_success(self):
        """Record a successful call."""
        async with self._lock:
            self.metrics.success_count += 1
            self.metrics.consecutive_failures = 0
            self.metrics.consecutive_successes += 1
            self.metrics.last_success_time = time.time()
            
            # If half-open and enough successes, close circuit
            if self.state == CircuitState.HALF_OPEN and self.metrics.consecutive_successes >= self.config.recovery_threshold:
                await self._update_state(CircuitState.CLOSED)
    
    async def record_failure(self, exception: Exception):
        """Record a failed call."""
        # Check if this exception should be ignored
        if type(exception) in self.config.exclude_exceptions:
            return
            
        async with self._lock:
            self.metrics.failure_count += 1
            self.metrics.consecutive_successes = 0
            self.metrics.consecutive_failures += 1
            self.metrics.last_failure_time = time.time()
            
            # If closed or half-open and too many failures, open circuit
            if (self.state in [CircuitState.CLOSED, CircuitState.HALF_OPEN] and 
                    self.metrics.consecutive_failures >= self.config.failure_threshold):
                await self._update_state(CircuitState.OPEN)
    
    async def is_call_permitted(self) -> bool:
        """Check if a call should be permitted based on circuit state."""
        async with self._lock:
            now = time.time()
            
            if self.state == CircuitState.CLOSED:
                return True
                
            if self.state == CircuitState.OPEN:
                # Check if timeout elapsed and circuit should try half-open
                if now - self.last_state_change >= self.config.timeout_seconds:
                    await self._update_state(CircuitState.HALF_OPEN)
                    return True
                return False
                
            # Half-open: allow one test call
            return True
    
    async def execute_async(self, func: Callable[..., Awaitable[T]], *args, **kwargs) -> T:
        """
        Execute an async function with circuit breaker protection.
        
        Args:
            func: Async function to execute
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the function
            
        Raises:
            CircuitOpenError: If circuit is open
            Exception: Original exception if call fails
        """
        if not await self.is_call_permitted():
            self.metrics.rejection_count += 1
            logger.warning(f"Circuit '{self.name}' is OPEN, rejecting call to {func.__name__}")
            raise CircuitOpenError(f"Circuit '{self.name}' is open")
        
        try:
            result = await func(*args, **kwargs)
            await self.record_success()
            return result
        except Exception as e:
            await self.record_failure(e)
            raise
            
    def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute a synchronous function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the function
            
        Raises:
            CircuitOpenError: If circuit is open
            Exception: Original exception if call fails
        """
        # We need to run the async methods in a new event loop
        # This is not ideal for production, but works for simple cases
        loop = asyncio.new_event_loop()
        try:
            if not loop.run_until_complete(self.is_call_permitted()):
                self.metrics.rejection_count += 1
                logger.warning(f"Circuit '{self.name}' is OPEN, rejecting call to {func.__name__}")
                raise CircuitOpenError(f"Circuit '{self.name}' is open")
            
            try:
                result = func(*args, **kwargs)
                loop.run_until_complete(self.record_success())
                return result
            except Exception as e:
                loop.run_until_complete(self.record_failure(e))
                raise
        finally:
            loop.close()


class CircuitOpenError(Exception):
    """Exception raised when a circuit is open."""
    pass


def circuit_breaker(name: str, **config_kwargs):
    """
    Decorator for applying circuit breaker to functions.
    
    Args:
        name: Name of the circuit
        **config_kwargs: Configuration parameters
        
    Returns:
        Decorated function
    """
    config = CircuitBreakerConfig(**config_kwargs)
    circuit = CircuitBreaker.get_or_create(name, config)
    
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await circuit.execute_async(func, *args, **kwargs)
            
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            return circuit.execute(func, *args, **kwargs)
        
        # Choose appropriate wrapper based on if function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore
            
    return decorator


class CircuitBreakerManager:
    """
    Manages multiple circuit breakers and provides global operations.
    
    Features:
    - Status reporting across all circuits
    - Forced reset capability
    - Health monitoring
    """
    
    @classmethod
    async def get_all_statuses(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get status information for all circuits.
        
        Returns:
            Dictionary of circuit statuses
        """
        statuses = {}
        
        for name, circuit in CircuitBreaker.get_all_circuits().items():
            metrics = circuit.get_metrics()
            
            statuses[name] = {
                "state": circuit.state,
                "metrics": metrics.model_dump(),
                "config": {
                    "failure_threshold": circuit.config.failure_threshold,
                    "recovery_threshold": circuit.config.recovery_threshold,
                    "timeout_seconds": circuit.config.timeout_seconds
                },
                "last_state_change": circuit.last_state_change,
                "state_age_seconds": time.time() - circuit.last_state_change
            }
            
        return statuses
    
    @classmethod
    async def reset_circuit(cls, name: str) -> bool:
        """
        Reset a circuit to closed state.
        
        Args:
            name: Name of the circuit to reset
            
        Returns:
            True if reset was successful
        """
        circuits = CircuitBreaker.get_all_circuits()
        if name not in circuits:
            return False
            
        circuit = circuits[name]
        async with circuit._lock:
            await circuit._update_state(CircuitState.CLOSED)
            circuit.metrics.consecutive_failures = 0
            circuit.metrics.consecutive_successes = 0
            
        logger.info(f"Circuit '{name}' was manually reset to CLOSED state")
        return True
    
    @classmethod
    async def reset_all_circuits(cls) -> List[str]:
        """
        Reset all circuits to closed state.
        
        Returns:
            List of circuit names that were reset
        """
        reset_circuits = []
        for name in CircuitBreaker.get_all_circuits():
            if await cls.reset_circuit(name):
                reset_circuits.append(name)
        return reset_circuits
