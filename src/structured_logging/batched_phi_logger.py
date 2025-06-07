"""
Batched PHI Logger Module

This module provides batched logging for PHI access to improve efficiency
while maintaining HIPAA compliance.
"""

import time
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from pydantic import BaseModel

from .phi_logger import PHILogger, PHIAccessRecord, get_phi_logger
from ..utils.structured_logging import get_logger
from .audit_chain import log_immutable_phi_access

logger = get_logger(__name__)


class BatchedPHILogger(PHILogger):
    """
    PHI Logger with batched writes for efficiency.
    
    Features:
    - Batches multiple PHI access records for efficient persistence
    - Periodic automatic flushing of batched records
    - Immediate critical record logging
    - Maintains full HIPAA compliance audit trails
    """
    
    def __init__(self, batch_size: int = 50, flush_interval_sec: int = 60):
        """
        Initialize the batched PHI logger.
        
        Args:
            batch_size: Maximum batch size before forced flush
            flush_interval_sec: Maximum time before automatic flush
        """
        super().__init__()
        self.batch_size = batch_size
        self.flush_interval = flush_interval_sec
        self.batch_buffer: List[PHIAccessRecord] = []
        self.last_flush_time = time.time()
        
        # Background task for automatic flushing
        self._flush_task = None
        
        logger.info(f"BatchedPHILogger initialized with batch_size={batch_size}, flush_interval={flush_interval_sec}s")
    
    async def start_flush_task(self):
        """Start the background task for automatic flushing."""
        if self._flush_task is None or self._flush_task.done():
            self._flush_task = asyncio.create_task(self._periodic_flush())
            
    async def _periodic_flush(self):
        """Periodically flush the buffer based on the flush interval."""
        try:
            while True:
                # Sleep for flush interval
                await asyncio.sleep(self.flush_interval)
                
                # Check if flush is needed
                if time.time() - self.last_flush_time >= self.flush_interval and self.batch_buffer:
                    await self._flush_buffer()
        except asyncio.CancelledError:
            # Ensure any remaining records are flushed
            if self.batch_buffer:
                await self._flush_buffer()
            logger.info("Batched flush task cancelled")
        except Exception as e:
            logger.error(f"Error in periodic flush task: {e}")
            
    async def log_access(self, 
                       user_id: str, 
                       action: str, 
                       system_component: str = "unknown",
                       access_purpose: str = "wellness_processing",
                       data_elements: Optional[List[str]] = None,
                       session_id: Optional[str] = None,
                       additional_context: Optional[Dict[str, Any]] = None,
                       critical: bool = False) -> str:
        """
        Log PHI access with batching.
        
        Args:
            user_id: User whose PHI was accessed
            action: Action performed (e.g., "view", "process")
            system_component: System component performing access
            access_purpose: Business purpose for access
            data_elements: Specific PHI elements accessed
            session_id: Session identifier
            additional_context: Additional context information
            critical: Whether this record is critical and should bypass batching
            
        Returns:
            Record ID of the logged access
        """
        # Create record
        record = self._create_record(
            user_id=user_id,
            action=action,
            system_component=system_component,
            access_purpose=access_purpose,
            data_elements=data_elements or [],
            session_id=session_id,
            additional_context=additional_context or {}
        )
        
        # If critical or batch size reached, flush immediately
        if critical or len(self.batch_buffer) >= self.batch_size:
            if critical:
                # For critical records, log directly and then flush batch
                await self._store_record(record)
                
                # Also log to immutable chain for critical records
                await log_immutable_phi_access(record)
                
                # Flush the rest of the batch
                if self.batch_buffer:
                    await self._flush_buffer()
            else:
                # Add to batch and flush
                self.batch_buffer.append(record)
                await self._flush_buffer()
        else:
            # Add to batch
            self.batch_buffer.append(record)
            
            # Check if flush interval elapsed
            if time.time() - self.last_flush_time >= self.flush_interval:
                await self._flush_buffer()
        
        return record.record_id
    
    async def _flush_buffer(self):
        """Flush buffered records to storage."""
        if not self.batch_buffer:
            return
            
        try:
            # Get batch
            batch = self.batch_buffer
            self.batch_buffer = []
            
            # Store records in a single transaction
            await self._store_batch(batch)
            
            # Log immutable copies for each record
            for record in batch:
                asyncio.create_task(log_immutable_phi_access(record))
                
            # Update flush time
            self.last_flush_time = time.time()
            
            logger.info(f"Flushed {len(batch)} PHI access records")
        except Exception as e:
            logger.error(f"Error flushing PHI access batch: {e}")
            
            # Restore batch to buffer
            self.batch_buffer = batch + self.batch_buffer
    
    async def _store_batch(self, batch: List[PHIAccessRecord]):
        """
        Store a batch of records.
        
        Override this method in subclasses for specific storage implementations.
        """
        # Default implementation just calls store_record for each record
        # In a real implementation, you'd use a more efficient batch operation
        for record in batch:
            await self._store_record(record)
            
    async def get_pending_record_count(self) -> int:
        """
        Get the number of pending records in the batch buffer.
        
        Returns:
            Number of pending records
        """
        return len(self.batch_buffer)
        
    async def force_flush(self) -> int:
        """
        Force a flush of all pending records.
        
        Returns:
            Number of records flushed
        """
        count = len(self.batch_buffer)
        if count > 0:
            await self._flush_buffer()
        return count
        
    async def shutdown(self):
        """Shutdown the logger, flushing any pending records."""
        # Cancel periodic flush task
        if self._flush_task and not self._flush_task.done():
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
                
        # Flush any remaining records
        await self.force_flush()


# Global instance
_batched_phi_logger = None

async def get_batched_phi_logger(batch_size: int = None, flush_interval_sec: int = None) -> BatchedPHILogger:
    """
    Get the global batched PHI logger instance.
    
    Args:
        batch_size: Batch size (only used on first initialization)
        flush_interval_sec: Flush interval (only used on first initialization)
        
    Returns:
        The global batched PHI logger instance
    """
    global _batched_phi_logger
    
    if _batched_phi_logger is None:
        if batch_size is None:
            from ..config.settings import get_settings
            settings = get_settings()
            batch_size = getattr(settings, "PHI_LOGGER_BATCH_SIZE", 50)
            flush_interval_sec = getattr(settings, "PHI_LOGGER_FLUSH_INTERVAL", 60)
            
        _batched_phi_logger = BatchedPHILogger(batch_size, flush_interval_sec)
        await _batched_phi_logger.start_flush_task()
    
    return _batched_phi_logger


async def log_phi_access_batched(user_id: str, 
                                action: str, 
                                system_component: str = "unknown",
                                critical: bool = False,
                                **kwargs) -> str:
    """
    Convenience function to log PHI access with batching.
    
    Args:
        user_id: User whose PHI was accessed
        action: Action performed (e.g., "view", "process")
        system_component: System component performing access
        critical: Whether this record is critical and should bypass batching
        **kwargs: Additional arguments passed to log_access
        
    Returns:
        Record ID of the logged access
    """
    phi_logger = await get_batched_phi_logger()
    return await phi_logger.log_access(
        user_id=user_id,
        action=action,
        system_component=system_component,
        critical=critical,
        **kwargs
    )
