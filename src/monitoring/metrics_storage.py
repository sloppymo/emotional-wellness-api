"""
Metrics Storage Module

Provides functionality for storing, retrieving, and managing historical metrics data.
Uses Redis Time Series for efficient time-series data storage with automatic retention policies.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Tuple, Any

import redis
from redis.commands.timeseries.commands import TimeSeriesCommands
from pydantic import BaseModel, Field

from ..structured_logging import get_logger
from ..config.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()

# Define metric types and retention policies
class RetentionPolicy(BaseModel):
    """Retention policy for metrics data."""
    name: str
    duration_seconds: int
    aggregation_type: str = "avg"
    bucket_size_seconds: int

# Default retention policies
DEFAULT_RETENTION_POLICIES = [
    RetentionPolicy(
        name="raw",
        duration_seconds=86400,  # 1 day of raw data
        aggregation_type="avg",
        bucket_size_seconds=60,  # 1 minute buckets
    ),
    RetentionPolicy(
        name="hourly",
        duration_seconds=604800,  # 7 days of hourly data
        aggregation_type="avg",
        bucket_size_seconds=3600,  # 1 hour buckets
    ),
    RetentionPolicy(
        name="daily",
        duration_seconds=2592000,  # 30 days of daily data
        aggregation_type="avg",
        bucket_size_seconds=86400,  # 1 day buckets
    ),
    RetentionPolicy(
        name="monthly",
        duration_seconds=31536000,  # 365 days of monthly data
        aggregation_type="avg",
        bucket_size_seconds=2592000,  # 30 day buckets
    ),
]

class MetricDataPoint(BaseModel):
    """A single metric data point."""
    timestamp: datetime
    value: float

class MetricSeries(BaseModel):
    """A time series of metric data points."""
    name: str
    data_points: List[MetricDataPoint]
    labels: Dict[str, str] = Field(default_factory=dict)

class MetricsStorage:
    """
    Manages storage and retrieval of time-series metrics data.
    
    Uses Redis Time Series for efficient storage with automatic downsampling
    and retention policies.
    """
    _instance = None
    
    def __init__(self):
        """Initialize the metrics storage."""
        self.redis_client = None
        self.ts = None
        self.initialized = False
        self.retention_policies = DEFAULT_RETENTION_POLICIES
    
    @classmethod
    def get_instance(cls) -> 'MetricsStorage':
        """Get the singleton instance of MetricsStorage."""
        if cls._instance is None:
            cls._instance = MetricsStorage()
        return cls._instance
    
    async def initialize(self) -> bool:
        """Initialize the connection to Redis Time Series."""
        if self.initialized:
            return True
        
        try:
            # Connect to Redis
            redis_url = settings.REDIS_URL
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            
            # Get Redis Time Series client
            self.ts = self.redis_client
            
            # Test connection
            self.redis_client.ping()
            
            self.initialized = True
            logger.info("Metrics storage initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize metrics storage: {e}")
            return False
    
    async def store_metric(
        self, 
        name: str, 
        value: float, 
        timestamp: Optional[int] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Store a metric data point.
        
        Args:
            name: The name of the metric
            value: The value of the metric
            timestamp: Optional timestamp (in milliseconds), defaults to current time
            labels: Optional labels for the metric
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.initialized:
            await self.initialize()
        
        if not self.initialized:
            logger.error("Cannot store metric: metrics storage not initialized")
            return False
        
        try:
            # Use current time if timestamp not provided
            if timestamp is None:
                timestamp = int(time.time() * 1000)  # Convert to milliseconds
            
            # Ensure labels is a dictionary
            if labels is None:
                labels = {}
            
            # Create key for the time series
            key = f"metrics:{name}"
            
            # Check if time series exists, create if not
            try:
                self.ts.ts().info(key)
            except redis.exceptions.ResponseError:
                # Time series doesn't exist, create it with retention policy
                self.ts.ts().create(
                    key,
                    retention_msecs=self.retention_policies[0].duration_seconds * 1000,
                    labels={"metric": name, **labels}
                )
                
                # Create compacted time series for each retention policy
                for policy in self.retention_policies[1:]:
                    compacted_key = f"{key}:{policy.name}"
                    self.ts.ts().create(
                        compacted_key,
                        retention_msecs=policy.duration_seconds * 1000,
                        labels={"metric": name, "aggregation": policy.name, **labels}
                    )
                    
                    # Create rule for automatic downsampling
                    self.ts.ts().createrule(
                        source_key=key,
                        dest_key=compacted_key,
                        aggregation_type=policy.aggregation_type,
                        bucket_size_msec=policy.bucket_size_seconds * 1000
                    )
            
            # Add the data point
            self.ts.ts().add(key, timestamp, value, labels=labels)
            return True
        except Exception as e:
            logger.error(f"Failed to store metric {name}: {e}")
            return False
    
    async def get_metric(
        self,
        name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        aggregation: str = "raw",
        labels: Optional[Dict[str, str]] = None
    ) -> Optional[MetricSeries]:
        """
        Retrieve metric data for a specific time range.
        
        Args:
            name: The name of the metric
            start_time: Start time for the query (defaults to 1 hour ago)
            end_time: End time for the query (defaults to now)
            aggregation: Aggregation level (raw, hourly, daily, monthly)
            labels: Optional labels to filter by
            
        Returns:
            MetricSeries or None if no data or error
        """
        if not self.initialized:
            await self.initialize()
        
        if not self.initialized:
            logger.error("Cannot get metric: metrics storage not initialized")
            return None
        
        try:
            # Set default time range if not provided
            if end_time is None:
                end_time = datetime.now()
            
            if start_time is None:
                # Default to 1 hour for raw data, adjust based on aggregation
                if aggregation == "raw":
                    start_time = end_time - timedelta(hours=1)
                elif aggregation == "hourly":
                    start_time = end_time - timedelta(days=7)
                elif aggregation == "daily":
                    start_time = end_time - timedelta(days=30)
                else:  # monthly
                    start_time = end_time - timedelta(days=365)
            
            # Convert to milliseconds timestamp
            start_ts = int(start_time.timestamp() * 1000)
            end_ts = int(end_time.timestamp() * 1000)
            
            # Determine the key based on aggregation
            if aggregation == "raw":
                key = f"metrics:{name}"
            else:
                key = f"metrics:{name}:{aggregation}"
            
            # Query the data
            result = self.ts.ts().range(
                key,
                from_time=start_ts,
                to_time=end_ts
            )
            
            if not result:
                logger.debug(f"No data found for metric {name}")
                return MetricSeries(name=name, data_points=[], labels={})
            
            # Convert to MetricDataPoint objects
            data_points = [
                MetricDataPoint(
                    timestamp=datetime.fromtimestamp(ts / 1000),
                    value=value
                )
                for ts, value in result
            ]
            
            # Get labels from the time series
            ts_info = self.ts.ts().info(key)
            labels_dict = {label[0]: label[1] for label in ts_info.get('labels', [])}
            
            return MetricSeries(
                name=name,
                data_points=data_points,
                labels=labels_dict
            )
        except Exception as e:
            logger.error(f"Failed to get metric {name}: {e}")
            return None
    
    async def list_metrics(self) -> List[Dict[str, Any]]:
        """
        List all available metrics.
        
        Returns:
            List of metric information dictionaries
        """
        if not self.initialized:
            await self.initialize()
        
        if not self.initialized:
            logger.error("Cannot list metrics: metrics storage not initialized")
            return []
        
        try:
            # Use Redis search to find all metric keys
            keys = self.redis_client.keys("metrics:*")
            
            # Filter out aggregation keys
            base_keys = [k for k in keys if len(k.split(':')) == 2]
            
            metrics = []
            for key in base_keys:
                try:
                    info = self.ts.ts().info(key)
                    metric_name = key.split(':')[1]
                    
                    # Extract labels
                    labels = {label[0]: label[1] for label in info.get('labels', [])}
                    
                    # Get sample count and time range
                    sample_count = info.get('totalSamples', 0)
                    first_timestamp = info.get('firstTimestamp', 0)
                    last_timestamp = info.get('lastTimestamp', 0)
                    
                    metrics.append({
                        "name": metric_name,
                        "labels": labels,
                        "sample_count": sample_count,
                        "first_timestamp": datetime.fromtimestamp(first_timestamp / 1000) if first_timestamp else None,
                        "last_timestamp": datetime.fromtimestamp(last_timestamp / 1000) if last_timestamp else None
                    })
                except Exception as e:
                    logger.error(f"Error getting info for metric {key}: {e}")
            
            return metrics
        except Exception as e:
            logger.error(f"Failed to list metrics: {e}")
            return []
    
    async def delete_metric(self, name: str) -> bool:
        """
        Delete a metric and all its aggregations.
        
        Args:
            name: The name of the metric to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.initialized:
            await self.initialize()
        
        if not self.initialized:
            logger.error("Cannot delete metric: metrics storage not initialized")
            return False
        
        try:
            # Delete the base time series
            base_key = f"metrics:{name}"
            self.redis_client.delete(base_key)
            
            # Delete all aggregation time series
            for policy in self.retention_policies[1:]:
                agg_key = f"{base_key}:{policy.name}"
                self.redis_client.delete(agg_key)
            
            return True
        except Exception as e:
            logger.error(f"Failed to delete metric {name}: {e}")
            return False
    
    async def close(self):
        """Close the Redis connection."""
        if self.redis_client:
            self.redis_client.close()
            self.initialized = False

# Singleton accessor
def get_metrics_storage() -> MetricsStorage:
    """Get the singleton instance of MetricsStorage."""
    return MetricsStorage.get_instance()

# Convenience functions
async def store_metric(
    name: str, 
    value: float, 
    labels: Optional[Dict[str, str]] = None
) -> bool:
    """
    Store a metric data point.
    
    Args:
        name: The name of the metric
        value: The value of the metric
        labels: Optional labels for the metric
        
    Returns:
        bool: True if successful, False otherwise
    """
    storage = get_metrics_storage()
    return await storage.store_metric(name, value, labels=labels)

async def get_metric(
    name: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    aggregation: str = "raw"
) -> Optional[MetricSeries]:
    """
    Retrieve metric data for a specific time range.
    
    Args:
        name: The name of the metric
        start_time: Start time for the query (defaults to 1 hour ago)
        end_time: End time for the query (defaults to now)
        aggregation: Aggregation level (raw, hourly, daily, monthly)
        
    Returns:
        MetricSeries or None if no data or error
    """
    storage = get_metrics_storage()
    return await storage.get_metric(name, start_time, end_time, aggregation)
