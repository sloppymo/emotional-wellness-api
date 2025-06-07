"""
Enhanced Security Integration Module

This module provides integration points between the core API architecture and
the advanced security and performance enhancements:
- Redis-based pattern caching
- Batched PHI access logging
- Vectorized crisis detection
- Circuit breaker pattern
- Feature flags
- Anomaly detection
"""

import asyncio
import functools
from typing import Dict, Any, Optional, Callable, TypeVar, cast, List, Union
from datetime import datetime

from fastapi import FastAPI, Request, Depends, BackgroundTasks, HTTPException

from ..config.feature_flags import get_feature_flag_manager
from ..symbolic.caching.pattern_cache import CachedPatternAnalyzer
from ..structured_logging.batched_phi_logger import get_batched_phi_logger
from ..symbolic.crisis.vectorized_detector import VectorizedCrisisDetector
from ..resiliency.circuit_breaker import CircuitBreaker, CircuitBreakerManager
from ..security.anomaly.detector import get_anomaly_detector
from ..utils.structured_logging import get_logger
from ..api.middleware.anomaly_detection_middleware import AnomalyDetectionMiddleware

logger = get_logger(__name__)

# Type variables for function decorators
T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


class EnhancedSecurityManager:
    """
    Manager class for integrating security and performance enhancements.

    Provides:
    1. Initialization of all enhanced security components
    2. Integration with FastAPI application
    3. Utility methods for accessing enhanced components
    4. Decorators for applying enhancements to functions
    """

    def __init__(self):
        """Initialize enhanced security manager."""
        # Component initialization flags
        self._is_initialized = False

        # Component references - will be initialized during setup
        self.pattern_cache = None
        self.batched_phi_logger = None
        self.vectorized_crisis_detector = None
        self.circuit_breaker_manager = None

    async def initialize(self, app: FastAPI = None):
        """
        Initialize all enhanced security components.

        Args:
            app: Optional FastAPI application to integrate with
        """
        if self._is_initialized:
            logger.debug("EnhancedSecurityManager already initialized")
            return

        try:
            # Initialize feature flags first - other components may depend on them
            logger.info("Initializing feature flags")
            feature_manager = await get_feature_flag_manager()

            # Initialize Redis-based pattern caching
            if await feature_manager.get_flag_value("enable_pattern_caching", default_value=True):
                logger.info("Initializing Redis-based pattern caching")
                self.pattern_cache = CachedPatternAnalyzer()
                await self.pattern_cache.initialize()

            # Initialize batched PHI logging
            if await feature_manager.get_flag_value(
                "enable_batched_phi_logging", default_value=True
            ):
                logger.info("Initializing batched PHI logging")
                self.batched_phi_logger = await get_batched_phi_logger()

            # Initialize vectorized crisis detector
            if await feature_manager.get_flag_value(
                "enable_vectorized_crisis_detection", default_value=True
            ):
                logger.info("Initializing vectorized crisis detector")
                self.vectorized_crisis_detector = VectorizedCrisisDetector()
                await self.vectorized_crisis_detector.initialize()

            # Initialize circuit breaker manager
            if await feature_manager.get_flag_value("enable_circuit_breaker", default_value=True):
                logger.info("Initializing circuit breaker manager")
                self.circuit_breaker_manager = CircuitBreakerManager()

            # Initialize anomaly detection
            if await feature_manager.get_flag_value("enable_anomaly_detection", default_value=True):
                logger.info("Initializing anomaly detection")
                anomaly_detector = await get_anomaly_detector()

                # Integrate with FastAPI if provided
                if app:
                    app.add_middleware(
                        AnomalyDetectionMiddleware,
                        phi_endpoints=[
                            "/api/wellness",
                            "/api/patient",
                            "/api/health-records",
                            "/api/canopy",
                        ],
                    )

            self._is_initialized = True
            logger.info("EnhancedSecurityManager initialization complete")

        except Exception as e:
            logger.error(f"Error initializing EnhancedSecurityManager: {e}")
            raise

    async def shutdown(self):
        """Gracefully shut down all enhanced security components."""
        if not self._is_initialized:
            return

        try:
            # Shutdown pattern cache
            if self.pattern_cache:
                logger.info("Shutting down pattern cache")
                await self.pattern_cache.shutdown()

            # Shutdown batched PHI logger
            if self.batched_phi_logger:
                logger.info("Shutting down batched PHI logger")
                await self.batched_phi_logger.shutdown()

            # Shut down anomaly detection
            logger.info("Shutting down anomaly detection")
            anomaly_detector = await get_anomaly_detector()
            await anomaly_detector.shutdown()

            self._is_initialized = False
            logger.info("EnhancedSecurityManager shutdown complete")

        except Exception as e:
            logger.error(f"Error during EnhancedSecurityManager shutdown: {e}")

    def cached_pattern_analysis(self, ttl: Optional[int] = None) -> Callable[[F], F]:
        """
        Decorator to apply Redis-based pattern caching to a function.

        Args:
            ttl: Optional TTL override for cache entries

        Returns:
            Function decorator
        """

        def decorator(func: F) -> F:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                if not self._is_initialized or not self.pattern_cache:
                    return await func(*args, **kwargs)

                # Extract text and user_id from args/kwargs based on function signature
                # This is a simplified example - would need adjustment for actual functions
                text = None
                user_id = None

                if "text" in kwargs:
                    text = kwargs.get("text")
                elif args and isinstance(args[0], str):
                    text = args[0]

                if "user_id" in kwargs:
                    user_id = kwargs.get("user_id")

                if not text:
                    return await func(*args, **kwargs)

                # Try to get from cache
                cache_key = self.pattern_cache.generate_cache_key(text, user_id)
                cached_result = await self.pattern_cache.get_cached_pattern(cache_key)

                if cached_result:
                    return cached_result

                # Not in cache, call original function
                result = await func(*args, **kwargs)

                # Cache the result
                if result:
                    await self.pattern_cache.cache_pattern_result(cache_key, result, ttl=ttl)

                return result

            return cast(F, wrapper)

        return decorator

    def with_circuit_breaker(
        self, name: str, max_failures: int = 3, reset_timeout_seconds: int = 60
    ) -> Callable[[F], F]:
        """
        Decorator to apply circuit breaker pattern to a function.

        Args:
            name: Circuit name
            max_failures: Maximum number of failures before opening circuit
            reset_timeout_seconds: Seconds before trying to close circuit again

        Returns:
            Function decorator
        """

        def decorator(func: F) -> F:
            if not self._is_initialized or not self.circuit_breaker_manager:
                return func

            # Create circuit breaker for this function
            circuit = CircuitBreaker(
                name=name, max_failures=max_failures, reset_timeout=reset_timeout_seconds
            )

            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                return await circuit.execute_async(func, *args, **kwargs)

            return cast(F, wrapper)

        return decorator

    def with_vectorized_crisis_detection(
        self, severity_threshold: float = 0.7, log_phi_access: bool = True
    ) -> Callable[[F], F]:
        """
        Decorator to apply vectorized crisis detection to a function that processes text.

        Args:
            severity_threshold: Threshold for crisis severity to trigger actions
            log_phi_access: Whether to log PHI access for crisis detection

        Returns:
            Function decorator
        """

        def decorator(func: F) -> F:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                # Get original result
                result = await func(*args, **kwargs)

                if not self._is_initialized or not self.vectorized_crisis_detector:
                    return result

                # Extract text from result/args/kwargs
                # This is simplified and would need adjustment for actual functions
                text = None
                user_id = None

                if isinstance(result, dict) and "text" in result:
                    text = result["text"]
                elif "text" in kwargs:
                    text = kwargs.get("text")

                if "user_id" in kwargs:
                    user_id = kwargs.get("user_id")

                if not text:
                    return result

                # Detect crisis patterns
                detection_result = await self.vectorized_crisis_detector.detect_crisis_patterns(
                    text, user_id
                )

                # Add detection results to output
                if isinstance(result, dict):
                    result["crisis_detection"] = {
                        "severity": detection_result.severity,
                        "patterns": [p.dict() for p in detection_result.matched_patterns],
                        "recommendations": detection_result.recommendations,
                    }

                    # Raise alert if severity exceeds threshold
                    if detection_result.severity >= severity_threshold:
                        logger.warning(
                            f"Crisis pattern detected with severity {detection_result.severity}",
                            extra={
                                "user_id": user_id,
                                "severity": detection_result.severity,
                                "patterns": [
                                    p.pattern_name for p in detection_result.matched_patterns
                                ],
                            },
                        )

                return result

            return cast(F, wrapper)

        return decorator


# Global instance
_enhanced_security_manager = None


async def get_enhanced_security_manager() -> EnhancedSecurityManager:
    """Get the global enhanced security manager instance."""
    global _enhanced_security_manager

    if _enhanced_security_manager is None:
        _enhanced_security_manager = EnhancedSecurityManager()

    if not _enhanced_security_manager._is_initialized:
        await _enhanced_security_manager.initialize()

    return _enhanced_security_manager


def setup_enhanced_security(app: FastAPI):
    """
    Set up enhanced security components for a FastAPI application.

    Args:
        app: FastAPI application instance
    """

    @app.on_event("startup")
    async def initialize_enhanced_security():
        """Initialize enhanced security components on app startup."""
        manager = await get_enhanced_security_manager()
        await manager.initialize(app)

    @app.on_event("shutdown")
    async def shutdown_enhanced_security():
        """Shut down enhanced security components on app shutdown."""
        if _enhanced_security_manager:
            await _enhanced_security_manager.shutdown()

    logger.info("Enhanced security setup complete for FastAPI application")
