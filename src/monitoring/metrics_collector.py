"""
Metrics Collector Module

Collects metrics from various sources and triggers alert evaluations.
Provides a centralized service for metrics collection and monitoring.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable
import psutil
import os

from ..structured_logging import get_logger
from .alert_manager import get_alert_manager, AlertInstance
from .alert_rules import AlertRuleSet, create_high_queue_depth_rule, create_integration_availability_rule
from .alert_rules import create_high_error_rate_rule, create_high_memory_usage_rule, create_auth_failure_spike_rule
from .metrics import (
    TASK_QUEUE_SIZE, INTEGRATION_AVAILABILITY, SYSTEM_HEALTH, 
    MEMORY_USAGE, REQUEST_COUNT, ACTIVE_REQUESTS
)
from .metrics_storage import get_metrics_storage, store_metric
from ..config import settings

logger = get_logger(__name__)

class MetricsCollector:
    """
    Collects system metrics and evaluates alert rules.
    
    This class is responsible for:
    1. Collecting metrics from various sources
    2. Formatting metrics for alert evaluation
    3. Triggering alert evaluations
    4. Scheduling periodic metric collection
    """
    
    def __init__(self, collection_interval_seconds: int = 60):
        """
        Initialize the metrics collector.
        
        Args:
            collection_interval_seconds: Interval between metric collections
        """
        self._logger = get_logger(f"{__name__}.MetricsCollector")
        self._collection_interval = collection_interval_seconds
        self._alert_manager = get_alert_manager()
        self._running = False
        self._last_collection: Optional[datetime] = None
        
        # Register default alert rules
        self._register_default_alert_rules()
    
    def _register_default_alert_rules(self) -> None:
        """Register default alert rules."""
        # Create rule sets
        system_rules = AlertRuleSet(
            name="system",
            description="System resource and performance alerts"
        )
        
        queue_rules = AlertRuleSet(
            name="queues",
            description="Task queue health alerts"
        )
        
        integration_rules = AlertRuleSet(
            name="integrations",
            description="External integration health alerts"
        )
        
        security_rules = AlertRuleSet(
            name="security",
            description="Security and authentication alerts"
        )
        
        # Add rules to sets
        system_rules.add_rule(create_high_memory_usage_rule(threshold_percent=90.0))
        
        # Queue depth rules for each queue
        for queue_name in ["default", "analytics", "notifications", "longitudinal"]:
            queue_rules.add_rule(create_high_queue_depth_rule(queue_name, threshold=100))
        
        # Integration availability rules
        for integration_name in ["moss", "crisis_response", "auth_service", "notification_service"]:
            integration_rules.add_rule(create_integration_availability_rule(integration_name))
        
        # Security rules
        security_rules.add_rule(create_auth_failure_spike_rule(threshold=5))
        
        # Register rule sets with alert manager
        self._alert_manager.register_rule_set(system_rules)
        self._alert_manager.register_rule_set(queue_rules)
        self._alert_manager.register_rule_set(integration_rules)
        self._alert_manager.register_rule_set(security_rules)
    
    async def start(self) -> None:
        """Start periodic metric collection."""
        if self._running:
            return
            
        self._running = True
        self._logger.info(f"Starting metrics collector with {self._collection_interval}s interval")
        
        while self._running:
            try:
                await self.collect_and_evaluate()
            except Exception as e:
                self._logger.error(f"Error in metrics collection: {e}", exc_info=True)
            
            await asyncio.sleep(self._collection_interval)
    
    async def stop(self) -> None:
        """Stop metric collection."""
        self._running = False
        self._logger.info("Stopping metrics collector")
    
    async def collect_and_evaluate(self) -> List[AlertInstance]:
        """
        Collect metrics and evaluate alert rules.
        
        Returns:
            List of triggered alert instances
        """
        start_time = time.time()
        self._last_collection = datetime.utcnow()
        
        # Collect metrics from various sources
        metrics = {}
        
        # System metrics
        await self.collect_system_metrics(metrics)
        
        # Queue metrics
        await self.collect_queue_metrics(metrics)
        
        # Integration metrics
        await self.collect_integration_metrics(metrics)
        
        # Security metrics
        await self.collect_security_metrics(metrics)
        
        # API metrics
        await self.collect_api_metrics(metrics)
        
        # Evaluate alerts
        triggered_alerts = await self._alert_manager.evaluate_alerts(metrics)
        
        collection_time = time.time() - start_time
        self._logger.debug(
            f"Collected {len(metrics)} metrics and triggered {len(triggered_alerts)} alerts "
            f"in {collection_time:.2f}s"
        )
        
        return triggered_alerts
    
    async def collect_system_metrics(self) -> Dict[str, float]:
        """Collect system resource metrics."""
        metrics = {}
        try:
            # CPU usage
            metrics["system.cpu_percent"] = psutil.cpu_percent(interval=0.5)
            
            # Memory usage
            memory = psutil.virtual_memory()
            metrics["system.memory_percent"] = memory.percent
            metrics["system.memory_available"] = memory.available
            metrics["system.memory_used"] = memory.used
            
            # Disk usage
            disk = psutil.disk_usage('/')
            metrics["system.disk_percent"] = disk.percent
            metrics["system.disk_free"] = disk.free
            metrics["system.disk_used"] = disk.used
            
            # Network I/O
            net_io = psutil.net_io_counters()
            metrics["system.net_bytes_sent"] = net_io.bytes_sent
            metrics["system.net_bytes_recv"] = net_io.bytes_recv
            
            # Store metrics in time-series storage
            for name, value in metrics.items():
                await store_metric(name, value)
            
            logger.debug(f"Collected system metrics: {metrics}")
            return metrics
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return metrics
    
    async def collect_queue_metrics(self) -> Dict[str, float]:
        """Collect queue metrics from Redis."""
        metrics = {}
        try:
            # In a real implementation, we would query Redis or RabbitMQ
            # for actual queue depths
            
            # For now, we'll use the Prometheus metrics directly
            for queue_name in ["default", "analytics", "notifications", "longitudinal"]:
                # Get queue size from Prometheus
                queue_size = TASK_QUEUE_SIZE._metrics.get({"queue_name": queue_name})
                if queue_size is not None:
                    metrics[f"background_task_queue_size_{queue_name}"] = queue_size.value
                else:
                    # Default to 0 if not found
                    metrics[f"background_task_queue_size_{queue_name}"] = 0
            
            # Store metrics in time-series storage
            for name, value in metrics.items():
                await store_metric(name, value)
            
            logger.debug(f"Collected queue metrics: {metrics}")
            return metrics
        except Exception as e:
            logger.error(f"Error collecting queue metrics: {e}")
            return metrics
    
    async def collect_integration_metrics(self) -> Dict[str, float]:
        """Collect integration metrics."""
        metrics = {}
        try:
            # In a real implementation, we would query the integration health
            # endpoints for actual availability
            
            # For now, we'll use the Prometheus metrics directly
            for integration_name in ["moss", "crisis_response", "auth_service", "notification_service"]:
                # Get availability from Prometheus
                availability = INTEGRATION_AVAILABILITY._metrics.get({"integration_name": integration_name})
                if availability is not None:
                    metrics[f"integration_availability_{integration_name}"] = availability.value
                else:
                    # Default to 1 (available) if not found
                    metrics[f"integration_availability_{integration_name}"] = 1
            
            # Store metrics in time-series storage
            for name, value in metrics.items():
                await store_metric(name, value)
            
            logger.debug(f"Collected integration metrics: {metrics}")
            return metrics
        except Exception as e:
            logger.error(f"Error collecting integration metrics: {e}")
            return metrics
    
    async def collect_security_metrics(self) -> Dict[str, float]:
        """Collect security metrics."""
        metrics = {}
        try:
            # In a real implementation, we would query logs or security
            # monitoring systems for actual counts
            
            # For now, we'll use a placeholder
            metrics["authentication_failures_total"] = 0
            
            # Store metrics in time-series storage
            for name, value in metrics.items():
                await store_metric(name, value)
            
            logger.debug(f"Collected security metrics: {metrics}")
            return metrics
        except Exception as e:
            logger.error(f"Error collecting security metrics: {e}")
            return metrics
    
    async def collect_api_metrics(self) -> Dict[str, float]:
        """Collect API metrics."""
        metrics = {}
        try:
            # Active requests
            active_requests = ACTIVE_REQUESTS._value.get()
            metrics["active_requests"] = active_requests
            
            # Calculate error rates for endpoints
            # This is a simplified implementation - in reality we would
            # calculate this from actual request counts
            
            # For now, we'll use a placeholder
            metrics["api_error_rate_overall"] = 0.01  # 1% error rate
            
        except Exception as e:
            self._logger.error(f"Error collecting API metrics: {e}")

# Global instance
_metrics_collector: Optional[MetricsCollector] = None

def get_metrics_collector() -> MetricsCollector:
    """Get the global MetricsCollector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector

async def start_metrics_collection() -> None:
    """Start the metrics collection service."""
    collector = get_metrics_collector()
    await collector.start()

async def stop_metrics_collection() -> None:
    """Stop the metrics collection service."""
    collector = get_metrics_collector()
    await collector.stop()
