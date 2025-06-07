"""
Distributed Symbolic Processing Module

This module provides distributed processing capabilities for the symbolic
emotional wellness API using Ray for horizontal scaling.
"""

import os
import asyncio
from typing import Dict, List, Any, Optional
import ray
from pydantic import BaseModel

from ..symbolic.canopy import CanopyProcessor
from ..symbolic.adapters.canopy_adapter import SylvaRequest, CanopyAdapter
from ..utils.structured_logging import get_logger

logger = get_logger(__name__)

# Initialize Ray conditionally based on environment
RAY_INITIALIZED = False


def ensure_ray_initialized():
    """Ensure Ray is initialized exactly once."""
    global RAY_INITIALIZED
    
    if not RAY_INITIALIZED:
        try:
            # Check if Ray is already initialized
            try:
                ray.get_runtime_context()
            except Exception:
                # Initialize Ray with appropriate resources
                ray.init(
                    ignore_reinit_error=True,
                    include_dashboard=False,  # Disable dashboard in production
                    _temp_dir="/tmp/ray",  # Specify temp directory
                    address=os.environ.get("RAY_ADDRESS", None)  # Allow external cluster
                )
                
            RAY_INITIALIZED = True
            logger.info("Ray initialized for distributed processing")
        except Exception as e:
            logger.error(f"Failed to initialize Ray: {e}")
            # Fall back to local processing
            logger.warning("Falling back to local processing")


@ray.remote
class DistributedSymbolicProcessor:
    """
    Distributed version of symbolic processor for horizontal scaling.
    
    This actor can be deployed across multiple nodes to scale processing
    horizontally while maintaining local state.
    """
    
    def __init__(self):
        """Initialize the distributed processor."""
        self.processor = CanopyProcessor()
        self.adapter = CanopyAdapter(canopy_processor=self.processor)
        self._health_check_count = 0
        logger.info("Distributed symbolic processor initialized")
        
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single request.
        
        Args:
            request: Request data as dictionary
            
        Returns:
            Processed result
        """
        try:
            # Convert dictionary to SylvaRequest
            sylva_request = SylvaRequest(**request)
            
            # Process request
            result = await self.adapter._process_request(sylva_request)
            return result
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return {"error": str(e), "status": "failed"}
            
    async def process_batch(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process multiple requests in parallel.
        
        Args:
            requests: List of request dictionaries
            
        Returns:
            List of results
        """
        results = []
        
        for request in requests:
            result = await self.process_request(request)
            results.append(result)
            
        return results
        
    def health_check(self) -> Dict[str, Any]:
        """
        Check the health of this worker.
        
        Returns:
            Health status information
        """
        self._health_check_count += 1
        return {
            "status": "healthy",
            "worker_id": ray.get_runtime_context().get_node_id(),
            "health_check_count": self._health_check_count,
            "processor_ready": self.processor is not None
        }


class SymbolicProcessingCluster:
    """
    Manages a cluster of distributed symbolic processors.
    
    This class provides load balancing, fault tolerance, and
    horizontal scaling for symbolic processing.
    """
    
    def __init__(self, num_workers: int = 4):
        """
        Initialize the symbolic processing cluster.
        
        Args:
            num_workers: Number of worker actors to create
        """
        ensure_ray_initialized()
        
        # Create workers
        self.workers = [DistributedSymbolicProcessor.remote() for _ in range(num_workers)]
        self.next_worker_idx = 0
        self.num_workers = num_workers
        
        logger.info(f"Symbolic processing cluster initialized with {num_workers} workers")
        
    async def process_request(self, request: SylvaRequest) -> Dict[str, Any]:
        """
        Process a single request with load balancing.
        
        Args:
            request: The request to process
            
        Returns:
            Processing result
        """
        # Convert request to dict for serialization
        request_dict = request.model_dump()
        
        # Select worker using round-robin
        worker = self.workers[self.next_worker_idx]
        self.next_worker_idx = (self.next_worker_idx + 1) % self.num_workers
        
        try:
            # Process request
            result_ref = worker.process_request.remote(request_dict)
            result = await asyncio.to_thread(ray.get, result_ref, timeout=30)
            return result
        except ray.exceptions.RayActorError:
            # Worker failed, replace it
            logger.warning(f"Worker failed, replacing")
            self.workers[self.next_worker_idx] = DistributedSymbolicProcessor.remote()
            
            # Try with new worker
            worker = self.workers[self.next_worker_idx]
            result_ref = worker.process_request.remote(request_dict)
            result = await asyncio.to_thread(ray.get, result_ref, timeout=30)
            return result
        except ray.exceptions.GetTimeoutError:
            # Timeout, try another worker
            logger.warning(f"Request timed out, trying another worker")
            
            # Select different worker
            self.next_worker_idx = (self.next_worker_idx + 1) % self.num_workers
            worker = self.workers[self.next_worker_idx]
            
            # Try with new worker
            result_ref = worker.process_request.remote(request_dict)
            result = await asyncio.to_thread(ray.get, result_ref, timeout=30)
            return result
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return {"error": str(e), "status": "failed"}
            
    async def process_batch(self, requests: List[SylvaRequest]) -> List[Dict[str, Any]]:
        """
        Process multiple requests in parallel across workers.
        
        Args:
            requests: The requests to process
            
        Returns:
            List of results
        """
        # Convert requests to dicts for serialization
        request_dicts = [req.model_dump() for req in requests]
        
        # Split requests among workers
        chunks = [[] for _ in range(self.num_workers)]
        for i, req in enumerate(request_dicts):
            chunks[i % self.num_workers].append(req)
            
        # Process in parallel on all workers
        result_refs = []
        for i, chunk in enumerate(chunks):
            if chunk:  # Skip empty chunks
                worker = self.workers[i]
                result_refs.append(worker.process_batch.remote(chunk))
        
        # Collect results
        all_results = []
        for result_ref in result_refs:
            try:
                chunk_results = await asyncio.to_thread(ray.get, result_ref, timeout=60)
                all_results.extend(chunk_results)
            except Exception as e:
                logger.error(f"Error processing batch: {e}")
                # Add error result for each request in the failed chunk
                # This is an approximation since we don't know chunk size
                estimated_chunk_size = len(request_dicts) // self.num_workers + 1
                for _ in range(estimated_chunk_size):
                    all_results.append({"error": str(e), "status": "failed"})
                
        return all_results
            
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of all workers.
        
        Returns:
            Health status of the cluster
        """
        health_refs = [worker.health_check.remote() for worker in self.workers]
        
        # Collect health status with timeout
        statuses = []
        for health_ref in health_refs:
            try:
                status = await asyncio.to_thread(ray.get, health_ref, timeout=5)
                statuses.append(status)
            except Exception:
                statuses.append({"status": "unhealthy"})
                
        # Calculate overall health
        healthy_count = sum(1 for status in statuses if status["status"] == "healthy")
        overall_health = "healthy" if healthy_count >= len(self.workers) // 2 else "degraded"
        
        return {
            "overall_status": overall_health,
            "healthy_workers": healthy_count,
            "total_workers": len(self.workers),
            "worker_statuses": statuses
        }
        
    async def scale(self, target_workers: int) -> None:
        """
        Scale the cluster to the desired number of workers.
        
        Args:
            target_workers: Target number of workers
        """
        current_workers = len(self.workers)
        
        if target_workers > current_workers:
            # Scale up
            for _ in range(target_workers - current_workers):
                self.workers.append(DistributedSymbolicProcessor.remote())
        elif target_workers < current_workers:
            # Scale down
            for _ in range(current_workers - target_workers):
                worker = self.workers.pop()
                ray.kill(worker)
                
        self.num_workers = len(self.workers)
        logger.info(f"Scaled cluster to {self.num_workers} workers")


# Global instance
_processing_cluster = None

def get_processing_cluster(num_workers: int = None) -> SymbolicProcessingCluster:
    """
    Get the global symbolic processing cluster instance.
    
    Args:
        num_workers: Number of workers (only used on first initialization)
        
    Returns:
        The global cluster instance
    """
    global _processing_cluster
    
    if _processing_cluster is None:
        if num_workers is None:
            # Default to number of CPUs if not specified
            import multiprocessing
            num_workers = max(1, multiprocessing.cpu_count() // 2)
            
        _processing_cluster = SymbolicProcessingCluster(num_workers)
    
    return _processing_cluster
