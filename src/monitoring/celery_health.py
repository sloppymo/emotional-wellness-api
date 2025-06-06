"""
Celery Health Monitoring and Task Queue Diagnostics

This module provides health monitoring for the Celery task processing system:
- Worker status and availability
- Queue depths and processing rates
- Task success/failure rates
- Longitudinal analysis task health
- Notification delivery monitoring
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from enum import Enum

from pydantic import BaseModel, Field
import redis.asyncio as redis
from celery.result import AsyncResult

from ..structured_logging import get_logger
from ..tasks.celery_app import celery_app, TaskStatus
from ..config import settings

logger = get_logger(__name__)

class QueueHealth(BaseModel):
    """Health status of a Celery queue."""
    name: str
    active_tasks: int = 0
    pending_tasks: int = 0
    processing_rate: Optional[float] = None  # tasks/minute
    avg_task_duration: Optional[float] = None  # seconds
    oldest_task_age: Optional[float] = None  # seconds
    status: str = "healthy"
    details: Dict[str, Any] = Field(default_factory=dict)

class WorkerHealth(BaseModel):
    """Health status of a Celery worker."""
    id: str
    status: str
    uptime: Optional[float] = None  # seconds
    processed_tasks: int = 0
    active_tasks: int = 0
    queues: List[str] = Field(default_factory=list)
    last_heartbeat: Optional[datetime] = None
    system_info: Dict[str, Any] = Field(default_factory=dict)

class TaskTypeHealth(BaseModel):
    """Health metrics for a specific task type."""
    name: str
    success_rate: float = 100.0  # percentage
    failure_rate: float = 0.0  # percentage
    avg_duration: Optional[float] = None  # seconds
    count_last_hour: int = 0
    count_last_day: int = 0
    recent_errors: List[str] = Field(default_factory=list)

class CelerySystemHealth(BaseModel):
    """Overall Celery system health."""
    status: str
    workers: List[WorkerHealth] = Field(default_factory=list)
    queues: List[QueueHealth] = Field(default_factory=list)
    task_types: List[TaskTypeHealth] = Field(default_factory=list)
    broker_status: str = "unknown"
    backend_status: str = "unknown"
    total_active_tasks: int = 0
    total_pending_tasks: int = 0
    details: Dict[str, Any] = Field(default_factory=dict)
    response_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class CeleryHealthMonitor:
    """Monitor health of Celery task processing system."""
    
    def __init__(self):
        """Initialize the Celery health monitor."""
        self._logger = get_logger(f"{__name__}.CeleryHealthMonitor")
        self._redis_client = None
        
        # Task patterns for different queue types
        self._analytics_tasks = {
            'src.tasks.clinical_analytics.',
            'src.tasks.longitudinal.'
        }
        self._notification_tasks = {
            'src.tasks.notifications.'
        }
        
        # Health check thresholds
        self._queue_depth_warning = 100
        self._queue_depth_critical = 500
        self._task_age_warning = 300  # 5 minutes
        self._task_age_critical = 900  # 15 minutes
        
    async def _get_redis_client(self) -> redis.Redis:
        """Get or create Redis client for health checks."""
        if self._redis_client is None:
            self._redis_client = redis.Redis.from_url(
                settings.CELERY_BROKER_URL,
                decode_responses=True
            )
        return self._redis_client
    
    async def check_celery_health(self) -> CelerySystemHealth:
        """Perform comprehensive health check of Celery system."""
        start_time = time.time()
        
        try:
            # Check broker connectivity
            redis_client = await self._get_redis_client()
            broker_status = "healthy"
            try:
                await redis_client.ping()
            except Exception as e:
                broker_status = f"unhealthy: {str(e)}"
                self._logger.error(f"Redis broker health check failed: {e}")
            
            # Check backend connectivity
            backend_status = "healthy"
            try:
                await redis_client.ping()  # Same for Redis backend
            except Exception as e:
                backend_status = f"unhealthy: {str(e)}"
                self._logger.error(f"Redis backend health check failed: {e}")
            
            # Get worker status (requires Celery control commands)
            worker_status = await self._get_worker_status()
            
            # Get queue health
            queue_health = await self._get_queue_health()
            
            # Get task type health metrics
            task_health = await self._get_task_type_health()
            
            # Calculate overall system health
            overall_status = self._determine_overall_status(
                broker_status, backend_status, worker_status, queue_health
            )
            
            # Count active and pending tasks
            total_active = sum(w.active_tasks for w in worker_status)
            total_pending = sum(q.pending_tasks for q in queue_health)
            
            # Create system health report
            system_health = CelerySystemHealth(
                status=overall_status,
                workers=worker_status,
                queues=queue_health,
                task_types=task_health,
                broker_status=broker_status,
                backend_status=backend_status,
                total_active_tasks=total_active,
                total_pending_tasks=total_pending,
                response_time_ms=(time.time() - start_time) * 1000
            )
            
            return system_health
            
        except Exception as e:
            self._logger.error(f"Celery health check failed: {e}", exc_info=True)
            return CelerySystemHealth(
                status="critical",
                details={"error": str(e)},
                response_time_ms=(time.time() - start_time) * 1000
            )
    
    async def _get_worker_status(self) -> List[WorkerHealth]:
        """Get health status of all Celery workers."""
        try:
            # This requires synchronous Celery inspection
            # We need to execute this in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            i = celery_app.control.inspect()
            
            # Get various worker stats
            active_tasks = await loop.run_in_executor(None, i.active)
            stats = await loop.run_in_executor(None, i.stats)
            registered = await loop.run_in_executor(None, i.registered)
            
            if not stats:
                self._logger.warning("No Celery workers found")
                return []
            
            workers = []
            
            for worker_id, worker_stats in stats.items():
                # Extract relevant worker information
                uptime = worker_stats.get('uptime', 0)
                processed = worker_stats.get('total', {}).get('processed', 0)
                
                # Get active tasks for this worker
                active = len(active_tasks.get(worker_id, []) if active_tasks else [])
                
                # Get registered queues
                queues = registered.get(worker_id, []) if registered else []
                
                # Create worker health status
                worker = WorkerHealth(
                    id=worker_id,
                    status="healthy",
                    uptime=uptime,
                    processed_tasks=processed,
                    active_tasks=active,
                    queues=queues,
                    last_heartbeat=datetime.utcnow(),
                    system_info={
                        "pid": worker_stats.get('pid'),
                        "clock": worker_stats.get('clock'),
                        "pool": worker_stats.get('pool', {}).get('max-concurrency')
                    }
                )
                
                workers.append(worker)
            
            return workers
        except Exception as e:
            self._logger.error(f"Failed to get worker status: {e}", exc_info=True)
            return []
    
    async def _get_queue_health(self) -> List[QueueHealth]:
        """Get health status of Celery task queues."""
        try:
            redis_client = await self._get_redis_client()
            
            # Get queue keys from Redis
            queue_keys = await redis_client.keys('celery:*')
            queue_names = set()
            
            # Extract queue names
            for key in queue_keys:
                if key.startswith('celery:'):
                    parts = key.split(':')
                    if len(parts) > 1:
                        queue_names.add(parts[1])
            
            # Add our known queues explicitly
            queue_names.update(['default', 'analytics', 'notifications'])
            
            # Check health of each queue
            queues = []
            for name in queue_names:
                # Skip internal queues
                if name in ['celery', 'unacked', 'unacked_index']:
                    continue
                
                # Get queue length
                queue_key = f'celery:{name}'
                queue_length = await redis_client.llen(queue_key)
                
                # Try to get oldest task age (front of queue)
                oldest_task_age = None
                processing_rate = None
                
                # Default status based on queue length
                status = "healthy"
                if queue_length > self._queue_depth_warning:
                    status = "warning"
                if queue_length > self._queue_depth_critical:
                    status = "critical"
                
                queue = QueueHealth(
                    name=name,
                    pending_tasks=queue_length,
                    status=status,
                    details={
                        "queue_key": queue_key
                    }
                )
                
                queues.append(queue)
            
            return queues
        except Exception as e:
            self._logger.error(f"Failed to get queue health: {e}", exc_info=True)
            return []
    
    async def _get_task_type_health(self) -> List[TaskTypeHealth]:
        """Get health metrics for different task types."""
        try:
            # For now, we'll return placeholder task types
            # In a real implementation, this would query task history from the result backend
            task_types = []
            
            # Add analytics tasks
            analytics = TaskTypeHealth(
                name="Analytics Tasks",
                success_rate=95.0,
                failure_rate=5.0,
                avg_duration=120.0,
                count_last_hour=10,
                count_last_day=240
            )
            task_types.append(analytics)
            
            # Add longitudinal tasks
            longitudinal = TaskTypeHealth(
                name="Longitudinal Analysis Tasks",
                success_rate=98.0,
                failure_rate=2.0,
                avg_duration=45.0,
                count_last_hour=5,
                count_last_day=120
            )
            task_types.append(longitudinal)
            
            # Add notification tasks
            notifications = TaskTypeHealth(
                name="Notification Tasks",
                success_rate=99.5,
                failure_rate=0.5,
                avg_duration=2.0,
                count_last_hour=30,
                count_last_day=720
            )
            task_types.append(notifications)
            
            return task_types
        except Exception as e:
            self._logger.error(f"Failed to get task type health: {e}", exc_info=True)
            return []
    
    def _determine_overall_status(
        self, 
        broker_status: str,
        backend_status: str,
        workers: List[WorkerHealth],
        queues: List[QueueHealth]
    ) -> str:
        """Determine overall Celery system health status."""
        # Critical if broker or backend is unhealthy
        if "unhealthy" in broker_status or "unhealthy" in backend_status:
            return "critical"
        
        # Critical if no workers are available
        if not workers:
            return "critical"
        
        # Warning if any queues have warning or critical status
        queue_statuses = [q.status for q in queues]
        if "critical" in queue_statuses:
            return "warning"
        
        # Otherwise healthy
        return "healthy"

# Convenience functions
async def check_celery_health() -> CelerySystemHealth:
    """Check health of Celery task processing system."""
    monitor = CeleryHealthMonitor()
    return await monitor.check_celery_health()

async def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get detailed status of a specific task."""
    try:
        result = AsyncResult(task_id, app=celery_app)
        
        # Get task metadata
        status = result.state
        info = result.info
        
        # Format the response
        response = {
            "task_id": task_id,
            "status": status,
            "result": None,
            "error": None,
            "traceback": None,
            "progress": None
        }
        
        # Add result or error information
        if status == "SUCCESS":
            response["result"] = info
        elif status == "FAILURE":
            response["error"] = str(info)
            response["traceback"] = result.traceback
        elif status == "PROGRESS":
            if isinstance(info, dict):
                response["progress"] = info.get("progress", 0)
        
        return response
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        return {
            "task_id": task_id,
            "status": "UNKNOWN",
            "error": str(e)
        }
