"""
Clinical analytics module providing advanced reporting capabilities.

Offers trend analysis, risk prediction, and dashboards for clinicians.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import statistics
from collections import defaultdict
from redis.asyncio import Redis

import numpy as np
from scipy import stats

from structured_logging import get_logger
from observability import get_telemetry_manager, ComponentName, record_span
from clinical.models import (
    PatientAlert, ClinicalIntervention, PatientRiskProfile,
    ClinicalPriority, InterventionStatus, InterventionType
)
from symbolic.moss.crisis_classifier import CrisisSeverity


# Configure logger
logger = get_logger(__name__)


class TrendDirection(str):
    """Trend direction indicators for analytics."""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"


class ClinicalAnalytics:
    """
    Clinical analytics service for advanced reporting and trend analysis.
    
    Provides:
    - Historical trend analysis
    - Population level statistics
    - Patient cohort comparisons
    - Intervention outcome analysis
    """
    
    def __init__(self, redis: Redis):
        """
        Initialize clinical analytics service.
        
        Args:
            redis: Redis client for data access
        """
        self.redis = redis
        self._logger = get_logger(f"{__name__}.ClinicalAnalytics")
    
    @record_span("analytics.get_crisis_trends", ComponentName.SECURITY)
    async def get_crisis_trends(
        self,
        days: int = 30,
        granularity: str = "day"
    ) -> Dict[str, Any]:
        """
        Get crisis alert trends over time.
        
        Args:
            days: Number of days to analyze
            granularity: Time granularity (hour, day, week)
            
        Returns:
            Dictionary with trend data
        """
        if not self.redis:
            return {"error": "Redis connection not available"}
            
        now = datetime.utcnow()
        start_date = now - timedelta(days=days)
        
        # Get all alerts in time range
        alerts = []
        alert_keys = await self.redis.keys("clinical:alert:*")
        
        for key in alert_keys:
            alert_json = await self.redis.get(key)
            if not alert_json:
                continue
                
            try:
                alert_data = json.loads(alert_json)
                timestamp = datetime.fromisoformat(alert_data["timestamp"].replace("Z", "+00:00"))
                
                if timestamp >= start_date:
                    alerts.append({
                        "timestamp": timestamp,
                        "severity": alert_data["severity"],
                        "priority": alert_data.get("priority", "MEDIUM")
                    })
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                self._logger.error(f"Error parsing alert data: {e}")
        
        # Group by time period
        result = {
            "time_periods": [],
            "alert_counts": [],
            "severity_distribution": [],
            "priority_distribution": []
        }
        
        # Define time buckets based on granularity
        if granularity == "hour":
            bucket_format = "%Y-%m-%d %H:00"
            bucket_delta = timedelta(hours=1)
        elif granularity == "week":
            bucket_format = "%Y-%W"  # Year and week number
            bucket_delta = timedelta(days=7)
        else:  # default: day
            bucket_format = "%Y-%m-%d"
            bucket_delta = timedelta(days=1)
        
        # Create time buckets
        current = start_date
        buckets = {}
        
        while current <= now:
            period_key = current.strftime(bucket_format)
            buckets[period_key] = {
                "count": 0,
                "severity": {s.name: 0 for s in CrisisSeverity},
                "priority": {p.value: 0 for p in ClinicalPriority}
            }
            current += bucket_delta
        
        # Populate buckets
        for alert in alerts:
            period_key = alert["timestamp"].strftime(bucket_format)
            if period_key in buckets:
                buckets[period_key]["count"] += 1
                buckets[period_key]["severity"][alert["severity"]] = buckets[period_key]["severity"].get(alert["severity"], 0) + 1
                buckets[period_key]["priority"][alert["priority"]] = buckets[period_key]["priority"].get(alert["priority"], 0) + 1
        
        # Format response
        for period, data in sorted(buckets.items()):
            result["time_periods"].append(period)
            result["alert_counts"].append(data["count"])
            result["severity_distribution"].append(data["severity"])
            result["priority_distribution"].append(data["priority"])
        
        # Calculate trend
        if len(result["alert_counts"]) >= 2:
            # Simple linear regression for trend
            x = list(range(len(result["alert_counts"])))
            y = result["alert_counts"]
            slope, _, _, _, _ = stats.linregress(x, y)
            
            if slope > 0.1:
                result["trend"] = TrendDirection.UP
                result["trend_value"] = slope
            elif slope < -0.1:
                result["trend"] = TrendDirection.DOWN
                result["trend_value"] = slope
            else:
                result["trend"] = TrendDirection.STABLE
                result["trend_value"] = slope
        else:
            result["trend"] = TrendDirection.STABLE
            result["trend_value"] = 0
            
        return result
    
    @record_span("analytics.get_intervention_outcomes", ComponentName.SECURITY)
    async def get_intervention_outcomes(self) -> Dict[str, Any]:
        """
        Analyze intervention outcomes and effectiveness.
        
        Returns:
            Dictionary with intervention outcome data
        """
        if not self.redis:
            return {"error": "Redis connection not available"}
            
        # Get all interventions
        interventions = []
        intervention_keys = await self.redis.keys("clinical:intervention:*")
        
        for key in intervention_keys:
            intervention_json = await self.redis.get(key)
            if not intervention_json:
                continue
                
            try:
                interventions.append(json.loads(intervention_json))
            except json.JSONDecodeError as e:
                self._logger.error(f"Error parsing intervention data: {e}")
        
        # Analyze outcomes by type
        outcomes_by_type = defaultdict(lambda: {
            "total": 0,
            "completed": 0,
            "canceled": 0,
            "referred": 0,
            "completion_rate": 0,
            "avg_completion_time_hours": 0
        })
        
        completion_times = defaultdict(list)
        
        for intervention in interventions:
            int_type = intervention.get("intervention_type", "unknown")
            status = intervention.get("status", "unknown")
            
            outcomes_by_type[int_type]["total"] += 1
            
            if status == InterventionStatus.COMPLETED.value:
                outcomes_by_type[int_type]["completed"] += 1
                
                # Calculate completion time if available
                if "created_at" in intervention and "completed_at" in intervention:
                    try:
                        created = datetime.fromisoformat(intervention["created_at"].replace("Z", "+00:00"))
                        completed = datetime.fromisoformat(intervention["completed_at"].replace("Z", "+00:00"))
                        
                        hours = (completed - created).total_seconds() / 3600
                        completion_times[int_type].append(hours)
                    except (ValueError, TypeError) as e:
                        self._logger.error(f"Error calculating completion time: {e}")
                        
            elif status == InterventionStatus.CANCELED.value:
                outcomes_by_type[int_type]["canceled"] += 1
                
            elif status == InterventionStatus.REFERRED.value:
                outcomes_by_type[int_type]["referred"] += 1
        
        # Calculate rates and averages
        for int_type, data in outcomes_by_type.items():
            if data["total"] > 0:
                data["completion_rate"] = round(data["completed"] / data["total"] * 100, 1)
                
            if int_type in completion_times and completion_times[int_type]:
                data["avg_completion_time_hours"] = round(statistics.mean(completion_times[int_type]), 1)
        
        return {
            "outcomes_by_type": dict(outcomes_by_type),
            "total_interventions": sum(data["total"] for data in outcomes_by_type.values()),
            "overall_completion_rate": round(
                sum(data["completed"] for data in outcomes_by_type.values()) / 
                max(1, sum(data["total"] for data in outcomes_by_type.values())) * 100, 1
            )
        }
    
    @record_span("analytics.get_patient_risk_stratification", ComponentName.SECURITY)
    async def get_patient_risk_stratification(self) -> Dict[str, Any]:
        """
        Get patient risk stratification analysis.
        
        Returns:
            Dictionary with risk stratification data
        """
        if not self.redis:
            return {"error": "Redis connection not available"}
            
        # Get all patient risk profiles
        profiles = []
        profile_keys = await self.redis.keys("clinical:patient:*:risk_profile")
        
        for key in profile_keys:
            profile_json = await self.redis.get(key)
            if not profile_json:
                continue
                
            try:
                profiles.append(json.loads(profile_json))
            except json.JSONDecodeError as e:
                self._logger.error(f"Error parsing risk profile data: {e}")
        
        # Count patients by risk level
        risk_distribution = {level.name: 0 for level in CrisisSeverity}
        
        for profile in profiles:
            risk_level = profile.get("risk_level", CrisisSeverity.NONE.name)
            risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1
        
        # Identify common risk factors
        risk_factors = defaultdict(int)
        protective_factors = defaultdict(int)
        
        for profile in profiles:
            for factor in profile.get("risk_factors", []):
                risk_factors[factor] += 1
                
            for factor in profile.get("protective_factors", []):
                protective_factors[factor] += 1
        
        # Get top factors
        top_risk_factors = [
            {"factor": factor, "count": count}
            for factor, count in sorted(risk_factors.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        top_protective_factors = [
            {"factor": factor, "count": count}
            for factor, count in sorted(protective_factors.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        return {
            "risk_distribution": risk_distribution,
            "top_risk_factors": top_risk_factors,
            "top_protective_factors": top_protective_factors,
            "total_patients_analyzed": len(profiles)
        }


# Singleton instance
_clinical_analytics: Optional[ClinicalAnalytics] = None


async def get_clinical_analytics(redis: Redis) -> ClinicalAnalytics:
    """Get the global clinical analytics instance."""
    global _clinical_analytics
    if _clinical_analytics is None:
        _clinical_analytics = ClinicalAnalytics(redis=redis)
    return _clinical_analytics
