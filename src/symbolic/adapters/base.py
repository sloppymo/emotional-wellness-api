"""
Base adapter class for SYLVA symbolic processing integration.

This module defines the abstract base class and core interfaces for all
SYLVA adapters, ensuring consistent behavior across different symbolic components.
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any, TypeVar, Generic
from functools import lru_cache
import asyncio
import logging

from pydantic import BaseModel, Field, ConfigDict
from structured_logging import get_logger

# Type variables for generic adapter implementation
T = TypeVar('T', bound=BaseModel)
U = TypeVar('U', bound=BaseModel)

# Configure logging
logger = get_logger(__name__)

class AdapterError(Exception):
    """Base exception for all adapter-related errors."""
    
    def __init__(self, message: str, adapter_type: str, context: Optional[Dict[str, Any]] = None):
        self.adapter_type = adapter_type
        self.context = context or {}
        self.timestamp = datetime.now()
        super().__init__(message)

class SymbolicData(BaseModel):
    """Base model for symbolic data exchanged between adapters."""
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        str_strip_whitespace=True
    )
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SylvaRequest(BaseModel):
    """Standard request format for SYLVA operations."""
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        str_strip_whitespace=True
    )
    
    operation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    input_data: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    
class SylvaResponse(BaseModel):
    """Standard response format for SYLVA operations."""
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    operation_id: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)
    adapter_metadata: Dict[str, Any] = Field(default_factory=dict)

class AdapterRegistry:
    """Registry for managing SYLVA adapters."""
    
    def __init__(self):
        self._adapters: Dict[str, 'SylvaAdapter'] = {}
        self._logger = get_logger(f"{__name__}.AdapterRegistry")
    
    def register(self, adapter_type: str, adapter: 'SylvaAdapter') -> None:
        """Register an adapter instance."""
        if adapter_type in self._adapters:
            self._logger.warning(f"Overwriting existing adapter for type: {adapter_type}")
        
        self._adapters[adapter_type] = adapter
        self._logger.info(f"Registered adapter: {adapter_type}")
    
    def get_adapter(self, adapter_type: str) -> Optional['SylvaAdapter']:
        """Get an adapter by type."""
        return self._adapters.get(adapter_type)
    
    def list_adapters(self) -> List[str]:
        """List all registered adapter types."""
        return list(self._adapters.keys())
    
    def unregister(self, adapter_type: str) -> bool:
        """Unregister an adapter."""
        if adapter_type in self._adapters:
            del self._adapters[adapter_type]
            self._logger.info(f"Unregistered adapter: {adapter_type}")
            return True
        return False

class SylvaAdapter(ABC, Generic[T, U]):
    """
    Abstract base class for all SYLVA adapters.
    
    This class defines the standard interface for adapters that bridge between
    the existing symbolic components and the SYLVA framework.
    
    Type parameters:
        T: Input data type (must be a Pydantic BaseModel)
        U: Output data type (must be a Pydantic BaseModel)
    """
    
    def __init__(self, adapter_type: str, cache_size: int = 128):
        """
        Initialize the adapter.
        
        Args:
            adapter_type: Unique identifier for this adapter type
            cache_size: Maximum size of the LRU cache
        """
        self.adapter_type = adapter_type
        self.cache_size = cache_size
        self._logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self._initialized = False
        self._stats = {
            "requests_processed": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": 0,
            "average_processing_time": 0.0
        }
    
    async def initialize(self) -> None:
        """Initialize the adapter. Called before first use."""
        if self._initialized:
            return
        
        try:
            await self._initialize_adapter()
            self._initialized = True
            self._logger.info(f"Adapter {self.adapter_type} initialized successfully")
        except Exception as e:
            self._logger.error(f"Failed to initialize adapter {self.adapter_type}: {str(e)}")
            raise AdapterError(
                f"Initialization failed: {str(e)}", 
                self.adapter_type,
                {"error_type": type(e).__name__}
            )
    
    @abstractmethod
    async def _initialize_adapter(self) -> None:
        """Adapter-specific initialization logic. Must be implemented by subclasses."""
        pass
    
    async def process(self, request: SylvaRequest) -> SylvaResponse:
        """
        Process a SYLVA request through this adapter.
        
        Args:
            request: The standardized SYLVA request
            
        Returns:
            SylvaResponse with the processing results
        """
        if not self._initialized:
            await self.initialize()
        
        start_time = datetime.now()
        
        try:
            # Check cache first
            cache_key = self._generate_cache_key(request)
            cached_result = self._get_cached_result(cache_key)
            
            if cached_result is not None:
                self._stats["cache_hits"] += 1
                self._logger.debug(f"Cache hit for request {request.operation_id}")
                
                return SylvaResponse(
                    operation_id=request.operation_id,
                    success=True,
                    result=cached_result,
                    processing_time=0.0,
                    adapter_metadata={
                        "cached": True,
                        "adapter_type": self.adapter_type
                    }
                )
            
            self._stats["cache_misses"] += 1
            
            # Process the request
            result = await self._process_request(request)
            
            # Cache the result
            self._cache_result(cache_key, result)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_stats(processing_time)
            
            self._logger.info(
                f"Successfully processed request {request.operation_id}",
                extra={
                    "adapter_type": self.adapter_type,
                    "processing_time": processing_time,
                    "user_id": request.user_id,
                    "session_id": request.session_id
                }
            )
            
            return SylvaResponse(
                operation_id=request.operation_id,
                success=True,
                result=result,
                processing_time=processing_time,
                adapter_metadata={
                    "cached": False,
                    "adapter_type": self.adapter_type
                }
            )
            
        except Exception as e:
            self._stats["errors"] += 1
            processing_time = (datetime.now() - start_time).total_seconds()
            
            self._logger.error(
                f"Error processing request {request.operation_id}: {str(e)}",
                extra={
                    "adapter_type": self.adapter_type,
                    "error_type": type(e).__name__,
                    "user_id": request.user_id,
                    "session_id": request.session_id
                }
            )
            
            return SylvaResponse(
                operation_id=request.operation_id,
                success=False,
                error=str(e),
                processing_time=processing_time,
                adapter_metadata={
                    "adapter_type": self.adapter_type,
                    "error_type": type(e).__name__
                }
            )
    
    @abstractmethod
    async def _process_request(self, request: SylvaRequest) -> Dict[str, Any]:
        """
        Adapter-specific request processing logic.
        
        Args:
            request: The standardized SYLVA request
            
        Returns:
            Dictionary containing the processing results
        """
        pass
    
    def _generate_cache_key(self, request: SylvaRequest) -> str:
        """Generate a cache key for the request."""
        # Create a deterministic hash based on input data
        import hashlib
        import json
        
        # Only cache based on input data, not metadata like timestamps
        cache_data = {
            "input_data": request.input_data,
            "context": request.context
        }
        
        # Sort keys for deterministic serialization
        cache_json = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_json.encode()).hexdigest()
    
    @lru_cache(maxsize=128)
    def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached result. Using LRU cache for in-memory caching."""
        # This is a placeholder - in production, you might want Redis caching
        return None
    
    def _cache_result(self, cache_key: str, result: Dict[str, Any]) -> None:
        """Cache the result. Implement caching strategy here."""
        # This would implement actual caching logic
        # For now, we rely on the LRU cache decorator
        pass
    
    def _update_stats(self, processing_time: float) -> None:
        """Update adapter statistics."""
        self._stats["requests_processed"] += 1
        
        # Update running average
        current_avg = self._stats["average_processing_time"]
        total_requests = self._stats["requests_processed"]
        
        if total_requests == 1:
            self._stats["average_processing_time"] = processing_time
        else:
            # Incremental average calculation
            self._stats["average_processing_time"] = (
                (current_avg * (total_requests - 1) + processing_time) / total_requests
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get adapter statistics."""
        return {
            "adapter_type": self.adapter_type,
            "initialized": self._initialized,
            **self._stats
        }
    
    async def health_check(self) -> bool:
        """Perform a health check on the adapter."""
        try:
            if not self._initialized:
                return False
            
            # Perform adapter-specific health check
            return await self._health_check()
        except Exception as e:
            self._logger.error(f"Health check failed for {self.adapter_type}: {str(e)}")
            return False
    
    async def _health_check(self) -> bool:
        """Adapter-specific health check logic. Override in subclasses."""
        return True
    
    async def cleanup(self) -> None:
        """Cleanup adapter resources."""
        try:
            await self._cleanup_adapter()
            self._logger.info(f"Adapter {self.adapter_type} cleaned up successfully")
        except Exception as e:
            self._logger.error(f"Error during cleanup of {self.adapter_type}: {str(e)}")
    
    async def _cleanup_adapter(self) -> None:
        """Adapter-specific cleanup logic. Override in subclasses."""
        pass

# Global adapter registry instance
adapter_registry = AdapterRegistry() 