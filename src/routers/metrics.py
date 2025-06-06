"""
Metrics Router

Provides API endpoints for accessing system metrics data.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..structured_logging import get_logger
from ..monitoring.metrics_storage import get_metrics_storage, MetricSeries
from ..security.auth import get_current_user, require_role

logger = get_logger(__name__)

router = APIRouter(prefix="/metrics", tags=["Metrics"])

class MetricDataPointResponse(BaseModel):
    """API response model for a metric data point."""
    timestamp: str
    value: float

class MetricSeriesResponse(BaseModel):
    """API response model for a metric time series."""
    name: str
    data_points: List[MetricDataPointResponse]
    labels: Dict[str, str]

class MetricInfoResponse(BaseModel):
    """API response model for metric metadata."""
    name: str
    labels: Dict[str, str]
    sample_count: int
    first_timestamp: Optional[str] = None
    last_timestamp: Optional[str] = None

class MetricsListResponse(BaseModel):
    """API response model for a list of metrics."""
    metrics: List[MetricInfoResponse]
    count: int

@router.get("", response_model=MetricsListResponse)
async def list_metrics(
    current_user = Depends(require_role(["admin"]))
):
    """
    List all available metrics.
    
    Requires admin authentication.
    """
    try:
        storage = get_metrics_storage()
        metrics_list = await storage.list_metrics()
        
        # Convert to response model
        metrics_info = [
            MetricInfoResponse(
                name=m["name"],
                labels=m["labels"],
                sample_count=m["sample_count"],
                first_timestamp=m["first_timestamp"].isoformat() if m["first_timestamp"] else None,
                last_timestamp=m["last_timestamp"].isoformat() if m["last_timestamp"] else None
            )
            for m in metrics_list
        ]
        
        return MetricsListResponse(
            metrics=metrics_info,
            count=len(metrics_info)
        )
    except Exception as e:
        logger.error(f"Failed to list metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list metrics: {str(e)}")

@router.get("/{metric_name}", response_model=MetricSeriesResponse)
async def get_metric(
    metric_name: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    aggregation: str = Query("raw", enum=["raw", "hourly", "daily", "monthly"]),
    current_user = Depends(require_role(["admin"]))
):
    """
    Get data for a specific metric.
    
    Requires admin authentication.
    """
    try:
        storage = get_metrics_storage()
        metric_data = await storage.get_metric(
            name=metric_name,
            start_time=start_time,
            end_time=end_time,
            aggregation=aggregation
        )
        
        if not metric_data:
            raise HTTPException(status_code=404, detail=f"Metric {metric_name} not found")
        
        # Convert to response model
        data_points = [
            MetricDataPointResponse(
                timestamp=dp.timestamp.isoformat(),
                value=dp.value
            )
            for dp in metric_data.data_points
        ]
        
        return MetricSeriesResponse(
            name=metric_data.name,
            data_points=data_points,
            labels=metric_data.labels
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metric {metric_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metric: {str(e)}")

@router.delete("/{metric_name}")
async def delete_metric(
    metric_name: str,
    current_user = Depends(require_role(["admin"]))
):
    """
    Delete a metric and all its aggregations.
    
    Requires admin authentication.
    """
    try:
        storage = get_metrics_storage()
        success = await storage.delete_metric(metric_name)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Failed to delete metric {metric_name}")
        
        return {"success": True, "message": f"Metric {metric_name} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete metric {metric_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete metric: {str(e)}")

@router.get("/system/resources", response_model=Dict[str, MetricSeriesResponse])
async def get_system_resources(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    aggregation: str = Query("raw", enum=["raw", "hourly", "daily", "monthly"]),
    current_user = Depends(require_role(["admin"]))
):
    """
    Get system resource metrics (CPU, memory, disk).
    
    Requires admin authentication.
    """
    try:
        storage = get_metrics_storage()
        metrics = {}
        
        # Get CPU, memory, and disk metrics
        for metric_name in ["system.cpu_percent", "system.memory_percent", "system.disk_percent"]:
            metric_data = await storage.get_metric(
                name=metric_name,
                start_time=start_time,
                end_time=end_time,
                aggregation=aggregation
            )
            
            if metric_data:
                # Convert to response model
                data_points = [
                    MetricDataPointResponse(
                        timestamp=dp.timestamp.isoformat(),
                        value=dp.value
                    )
                    for dp in metric_data.data_points
                ]
                
                metrics[metric_name] = MetricSeriesResponse(
                    name=metric_data.name,
                    data_points=data_points,
                    labels=metric_data.labels
                )
        
        return metrics
    except Exception as e:
        logger.error(f"Failed to get system resource metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system resource metrics: {str(e)}")

@router.get("/api/requests", response_model=Dict[str, MetricSeriesResponse])
async def get_api_request_metrics(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    aggregation: str = Query("raw", enum=["raw", "hourly", "daily", "monthly"]),
    current_user = Depends(require_role(["admin"]))
):
    """
    Get API request metrics (request rate, error rate, latency).
    
    Requires admin authentication.
    """
    try:
        storage = get_metrics_storage()
        metrics = {}
        
        # Get API request metrics
        for metric_name in ["api.request_rate", "api.error_rate", "api.latency_avg"]:
            metric_data = await storage.get_metric(
                name=metric_name,
                start_time=start_time,
                end_time=end_time,
                aggregation=aggregation
            )
            
            if metric_data:
                # Convert to response model
                data_points = [
                    MetricDataPointResponse(
                        timestamp=dp.timestamp.isoformat(),
                        value=dp.value
                    )
                    for dp in metric_data.data_points
                ]
                
                metrics[metric_name] = MetricSeriesResponse(
                    name=metric_data.name,
                    data_points=data_points,
                    labels=metric_data.labels
                )
        
        return metrics
    except Exception as e:
        logger.error(f"Failed to get API request metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get API request metrics: {str(e)}")

@router.get("/integrations/health", response_model=Dict[str, MetricSeriesResponse])
async def get_integration_health_metrics(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    aggregation: str = Query("raw", enum=["raw", "hourly", "daily", "monthly"]),
    current_user = Depends(require_role(["admin"]))
):
    """
    Get integration health metrics (availability, latency).
    
    Requires admin authentication.
    """
    try:
        storage = get_metrics_storage()
        metrics = {}
        
        # Get integration metrics for each integration
        for integration in ["moss", "crisis", "auth", "notification"]:
            # Get availability metric
            avail_metric = await storage.get_metric(
                name=f"integration.{integration}.availability",
                start_time=start_time,
                end_time=end_time,
                aggregation=aggregation
            )
            
            if avail_metric:
                # Convert to response model
                data_points = [
                    MetricDataPointResponse(
                        timestamp=dp.timestamp.isoformat(),
                        value=dp.value
                    )
                    for dp in avail_metric.data_points
                ]
                
                metrics[f"integration.{integration}.availability"] = MetricSeriesResponse(
                    name=avail_metric.name,
                    data_points=data_points,
                    labels=avail_metric.labels
                )
            
            # Get latency metric
            latency_metric = await storage.get_metric(
                name=f"integration.{integration}.latency",
                start_time=start_time,
                end_time=end_time,
                aggregation=aggregation
            )
            
            if latency_metric:
                # Convert to response model
                data_points = [
                    MetricDataPointResponse(
                        timestamp=dp.timestamp.isoformat(),
                        value=dp.value
                    )
                    for dp in latency_metric.data_points
                ]
                
                metrics[f"integration.{integration}.latency"] = MetricSeriesResponse(
                    name=latency_metric.name,
                    data_points=data_points,
                    labels=latency_metric.labels
                )
        
        return metrics
    except Exception as e:
        logger.error(f"Failed to get integration health metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get integration health metrics: {str(e)}")
