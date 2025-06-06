"""
Longitudinal analysis module for monitoring patient emotional states over time.

Provides trend detection, pattern recognition, and early warning indicators
for clinical risk assessment based on historical patient data.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
import json
from collections import defaultdict
import uuid
from redis.asyncio import Redis

import numpy as np
from scipy import stats

from structured_logging import get_logger
from observability import get_telemetry_manager, ComponentName, record_span
from clinical.models import PatientRiskProfile, ClinicalPriority
from symbolic.moss.crisis_classifier import CrisisSeverity, RiskDomain


# Configure logger
logger = get_logger(__name__)


class TrendDirection(str):
    """Trend direction indicators for longitudinal analysis."""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    FLUCTUATING = "fluctuating"


class LongitudinalAnalyzer:
    """
    Longitudinal analyzer for monitoring patient emotional states over time.
    
    Provides:
    - Trend detection in emotional states
    - Early warning indicators for rising crisis risk
    - Pattern recognition for recurring emotional cycles
    - Historical context for current crisis assessment
    """
    
    def __init__(self, redis: Redis):
        """
        Initialize longitudinal analyzer.
        
        Args:
            redis: Redis client for data access
        """
        self.redis = redis
        self._logger = get_logger(f"{__name__}.LongitudinalAnalyzer")
    
    @record_span("longitudinal.analyze_patient_history", ComponentName.SECURITY)
    async def analyze_patient_history(self, patient_id: str, days: int = 90) -> Dict[str, Any]:
        """
        Analyze patient emotional history over the specified time period.
        
        Args:
            patient_id: Patient identifier
            days: Number of days to analyze backward from now
            
        Returns:
            Dictionary with trend analysis results
        """
        try:
            # Get patient history data
            history = await self._get_patient_history(patient_id, days)
            
            if not history or len(history) < 3:
                # Not enough data for meaningful trend analysis
                return {
                    "patient_id": patient_id,
                    "trend": TrendDirection.STABLE,
                    "confidence": 0.0,
                    "data_points": len(history) if history else 0,
                    "period_days": days,
                    "warning_signs": [],
                    "risk_factors": []
                }
            
            # Analyze emotional state trends
            emotional_trends = self._analyze_emotional_trends(history)
            
            # Detect patterns and cycles
            patterns = self._detect_patterns(history)
            
            # Identify risk factors
            risk_factors = self._identify_risk_factors(history, emotional_trends)
            
            # Determine current trend and confidence
            current_trend, confidence = self._determine_trend(emotional_trends)
            
            # Identify early warning signs
            warning_signs = self._identify_warning_signs(history, emotional_trends, patterns)
            
            return {
                "patient_id": patient_id,
                "trend": current_trend,
                "confidence": confidence,
                "data_points": len(history),
                "period_days": days,
                "emotional_trends": emotional_trends,
                "patterns": patterns,
                "warning_signs": warning_signs,
                "risk_factors": risk_factors
            }
            
        except Exception as e:
            self._logger.error(f"Error analyzing patient history: {e}")
            return {
                "patient_id": patient_id,
                "error": str(e),
                "trend": TrendDirection.STABLE,
                "confidence": 0.0
            }
    
    @record_span("longitudinal.early_warning_check", ComponentName.SECURITY)
    async def early_warning_check(self, patient_id: str) -> Dict[str, Any]:
        """
        Perform early warning check for rising crisis risk.
        
        Args:
            patient_id: Patient identifier
            
        Returns:
            Dictionary with early warning check results
        """
        try:
            # Analyze recent history (30 days)
            recent_analysis = await self.analyze_patient_history(patient_id, 30)
            
            # Also get longer-term context (90 days)
            context_analysis = await self.analyze_patient_history(patient_id, 90)
            
            # Determine if there are warning signs
            warning_level = 0
            
            # Look for increasing negative trends
            if recent_analysis["trend"] == TrendDirection.INCREASING and recent_analysis["confidence"] > 0.6:
                warning_level += 2
                
            # Check for identified warning signs
            warning_level += len(recent_analysis["warning_signs"])
            
            # Compare with long-term context
            if context_analysis["trend"] != TrendDirection.INCREASING and recent_analysis["trend"] == TrendDirection.INCREASING:
                # Recent change in trend direction
                warning_level += 1
            
            # Determine warning status
            warning_status = "none"
            if warning_level >= 5:
                warning_status = "high"
            elif warning_level >= 3:
                warning_status = "moderate"
            elif warning_level >= 1:
                warning_status = "low"
                
            return {
                "patient_id": patient_id,
                "warning_status": warning_status,
                "warning_level": warning_level,
                "warning_factors": recent_analysis["warning_signs"],
                "recent_trend": recent_analysis["trend"],
                "longer_trend": context_analysis["trend"],
                "risk_factors": recent_analysis["risk_factors"]
            }
            
        except Exception as e:
            self._logger.error(f"Error performing early warning check: {e}")
            return {
                "patient_id": patient_id,
                "warning_status": "error",
                "error": str(e)
            }
    
    async def _get_patient_history(self, patient_id: str, days: int) -> List[Dict[str, Any]]:
        """Get patient history for the specified time period."""
        history = []
        now = datetime.utcnow()
        start_date = now - timedelta(days=days)
        
        try:
            # Get crisis alerts
            alert_keys = await self.redis.keys(f"clinical:patient:{patient_id}:alert:*")
            
            for key in alert_keys:
                alert_json = await self.redis.get(key)
                if not alert_json:
                    continue
                    
                try:
                    alert_data = json.loads(alert_json)
                    timestamp = datetime.fromisoformat(alert_data["timestamp"].replace("Z", "+00:00"))
                    
                    if timestamp >= start_date:
                        history.append({
                            "type": "crisis_alert",
                            "timestamp": timestamp,
                            "severity": alert_data["severity"],
                            "domain": alert_data.get("domain", "UNDEFINED"),
                            "acknowledged": alert_data.get("acknowledged", False)
                        })
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    self._logger.error(f"Error parsing alert data: {e}")
            
            # Get emotional assessments
            assessment_keys = await self.redis.keys(f"wellness:patient:{patient_id}:assessment:*")
            
            for key in assessment_keys:
                assessment_json = await self.redis.get(key)
                if not assessment_json:
                    continue
                    
                try:
                    assessment_data = json.loads(assessment_json)
                    timestamp = datetime.fromisoformat(assessment_data["timestamp"].replace("Z", "+00:00"))
                    
                    if timestamp >= start_date:
                        history.append({
                            "type": "assessment",
                            "timestamp": timestamp,
                            "emotional_state": assessment_data.get("emotional_state", {}),
                            "wellness_score": assessment_data.get("wellness_score", 0)
                        })
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    self._logger.error(f"Error parsing assessment data: {e}")
            
            # Get interventions
            intervention_keys = await self.redis.keys(f"clinical:patient:{patient_id}:intervention:*")
            
            for key in intervention_keys:
                intervention_json = await self.redis.get(key)
                if not intervention_json:
                    continue
                    
                try:
                    intervention_data = json.loads(intervention_json)
                    timestamp = datetime.fromisoformat(intervention_data["created_at"].replace("Z", "+00:00"))
                    
                    if timestamp >= start_date:
                        history.append({
                            "type": "intervention",
                            "timestamp": timestamp,
                            "intervention_type": intervention_data.get("intervention_type"),
                            "status": intervention_data.get("status"),
                            "completed_at": intervention_data.get("completed_at")
                        })
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    self._logger.error(f"Error parsing intervention data: {e}")
            
            # Sort history by timestamp
            history.sort(key=lambda x: x["timestamp"])
            
            return history
            
        except Exception as e:
            self._logger.error(f"Error getting patient history: {e}")
            return []
    
    def _analyze_emotional_trends(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze emotional state trends from history."""
        # Extract assessment data points
        assessment_points = []
        for item in history:
            if item["type"] == "assessment" and "wellness_score" in item:
                assessment_points.append({
                    "timestamp": item["timestamp"],
                    "wellness_score": item["wellness_score"]
                })
        
        if not assessment_points or len(assessment_points) < 3:
            return {
                "trend": TrendDirection.STABLE,
                "wellness_slope": 0,
                "p_value": 1.0,
                "volatility": 0
            }
        
        # Extract time series data
        timestamps = [(point["timestamp"] - assessment_points[0]["timestamp"]).total_seconds() / 86400 for point in assessment_points]  # Convert to days
        scores = [point["wellness_score"] for point in assessment_points]
        
        # Linear regression to find trend
        slope, intercept, r_value, p_value, std_err = stats.linregress(timestamps, scores)
        
        # Calculate volatility (standard deviation)
        volatility = np.std(scores) if len(scores) > 1 else 0
        
        # Determine trend direction
        trend_direction = TrendDirection.STABLE
        if abs(slope) < 0.05:
            trend_direction = TrendDirection.STABLE
        elif slope > 0:
            trend_direction = TrendDirection.INCREASING
        else:
            trend_direction = TrendDirection.DECREASING
            
        # Check for fluctuation
        if volatility > 20 and abs(r_value) < 0.3:
            trend_direction = TrendDirection.FLUCTUATING
        
        return {
            "trend": trend_direction,
            "wellness_slope": slope,
            "r_squared": r_value ** 2,
            "p_value": p_value,
            "volatility": volatility,
            "data_points": len(assessment_points)
        }
    
    def _detect_patterns(self, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect patterns and cycles in patient history."""
        patterns = []
        
        # Group crisis alerts by domain
        crisis_by_domain = defaultdict(list)
        
        for item in history:
            if item["type"] == "crisis_alert" and "domain" in item:
                domain = item["domain"]
                crisis_by_domain[domain].append(item["timestamp"])
        
        # Look for recurring patterns in each domain
        for domain, timestamps in crisis_by_domain.items():
            if len(timestamps) >= 3:
                # Calculate intervals between events
                intervals = [(timestamps[i] - timestamps[i-1]).total_seconds() / 86400 for i in range(1, len(timestamps))]  # in days
                
                # Check if intervals are consistent (within 20%)
                if len(intervals) >= 2:
                    avg_interval = sum(intervals) / len(intervals)
                    consistent = all(abs(interval - avg_interval) / avg_interval < 0.2 for interval in intervals)
                    
                    if consistent and avg_interval <= 30:  # Pattern within a month
                        patterns.append({
                            "domain": domain,
                            "type": "recurring_crisis",
                            "interval_days": round(avg_interval, 1),
                            "occurrences": len(timestamps),
                            "last_occurrence": timestamps[-1].isoformat()
                        })
        
        # Look for crisis following specific emotional states
        emotional_triggers = defaultdict(int)
        last_assessment = None
        
        for item in history:
            if item["type"] == "assessment":
                last_assessment = item
            elif item["type"] == "crisis_alert" and last_assessment is not None:
                # Check if assessment was within 48 hours before crisis
                time_diff = (item["timestamp"] - last_assessment["timestamp"]).total_seconds() / 3600  # hours
                
                if time_diff > 0 and time_diff <= 48:
                    # This emotional state may be a precursor
                    wellness_score = last_assessment.get("wellness_score", 0)
                    emotional_triggers[f"wellness_below_{wellness_score}"] += 1
        
        # Add significant triggers to patterns
        for trigger, count in emotional_triggers.items():
            if count >= 2:  # At least 2 occurrences to consider significant
                patterns.append({
                    "type": "emotional_trigger",
                    "trigger": trigger,
                    "occurrences": count
                })
        
        return patterns
    
    def _identify_risk_factors(self, history: List[Dict[str, Any]], emotional_trends: Dict[str, Any]) -> List[str]:
        """Identify risk factors from patient history."""
        risk_factors = set()
        
        # Check for multiple crisis events
        crisis_events = [item for item in history if item["type"] == "crisis_alert"]
        if len(crisis_events) >= 3:
            risk_factors.add("multiple_crisis_events")
        
        # Check for severe crisis events
        severe_events = [item for item in crisis_events if item.get("severity") in (CrisisSeverity.SEVERE.name, CrisisSeverity.EXTREME.name)]
        if len(severe_events) >= 1:
            risk_factors.add("history_of_severe_crisis")
        
        # Check for negative emotional trend
        if emotional_trends.get("trend") == TrendDirection.DECREASING and emotional_trends.get("r_squared", 0) > 0.3:
            risk_factors.add("declining_emotional_wellbeing")
        
        # Check for high volatility
        if emotional_trends.get("volatility", 0) > 25:
            risk_factors.add("emotional_instability")
        
        # Check for failed interventions
        interventions = [item for item in history if item["type"] == "intervention"]
        failed_interventions = [item for item in interventions if item.get("status") == InterventionStatus.CANCELED.value]
        
        if failed_interventions and len(failed_interventions) / max(1, len(interventions)) > 0.3:
            risk_factors.add("poor_intervention_response")
        
        # Check for suicide/self-harm domain alerts
        suicide_alerts = [item for item in crisis_events if item.get("domain") == RiskDomain.SELF_HARM.name]
        if suicide_alerts:
            risk_factors.add("history_of_self_harm_ideation")
        
        return list(risk_factors)
    
    def _determine_trend(self, emotional_trends: Dict[str, Any]) -> Tuple[str, float]:
        """Determine current trend and confidence level."""
        trend = emotional_trends.get("trend", TrendDirection.STABLE)
        
        # Calculate confidence based on statistical measures
        r_squared = emotional_trends.get("r_squared", 0)
        p_value = emotional_trends.get("p_value", 1.0)
        data_points = emotional_trends.get("data_points", 0)
        
        # Initial confidence based on r-squared
        confidence = min(1.0, r_squared * 2)  # Scale r-squared for better confidence values
        
        # Adjust based on p-value (lower p-value increases confidence)
        if p_value < 0.05:
            confidence += 0.3
        elif p_value < 0.1:
            confidence += 0.15
        
        # Adjust based on number of data points
        if data_points >= 10:
            confidence *= 1.2
        elif data_points < 5:
            confidence *= 0.8
        
        # Cap confidence
        confidence = max(0.0, min(1.0, confidence))
        
        # If trend is FLUCTUATING, reduce confidence
        if trend == TrendDirection.FLUCTUATING:
            confidence *= 0.7
        
        return trend, confidence
    
    def _identify_warning_signs(self, history: List[Dict[str, Any]], emotional_trends: Dict[str, Any], patterns: List[Dict[str, Any]]) -> List[str]:
        """Identify early warning signs from history and analysis."""
        warning_signs = set()
        
        # Recent crisis events (last 2 weeks)
        two_weeks_ago = datetime.utcnow() - timedelta(days=14)
        recent_crises = [item for item in history if item["type"] == "crisis_alert" and item["timestamp"] >= two_weeks_ago]
        
        if recent_crises:
            warning_signs.add("recent_crisis_event")
        
        # Declining emotional trend
        if emotional_trends.get("trend") == TrendDirection.DECREASING and emotional_trends.get("r_squared", 0) > 0.3:
            warning_signs.add("declining_emotional_trend")
        
        # High emotional volatility
        if emotional_trends.get("volatility", 0) > 20:
            warning_signs.add("high_emotional_volatility")
        
        # Pattern-based warnings
        for pattern in patterns:
            if pattern["type"] == "recurring_crisis":
                # Check if we're approaching the next predicted crisis
                try:
                    last_occurrence = datetime.fromisoformat(pattern["last_occurrence"].replace("Z", "+00:00"))
                    interval_days = pattern.get("interval_days", 30)
                    next_predicted = last_occurrence + timedelta(days=interval_days)
                    days_until = (next_predicted - datetime.utcnow()).total_seconds() / 86400
                    
                    if 0 <= days_until <= 7:  # Within a week of predicted recurrence
                        warning_signs.add(f"approaching_predicted_crisis_{pattern['domain']}")
                except (ValueError, TypeError):
                    pass
            
            elif pattern["type"] == "emotional_trigger" and pattern["occurrences"] >= 3:
                warning_signs.add(f"identified_crisis_trigger_{pattern['trigger']}")
        
        # Check for multiple domains in recent crises
        recent_domains = set(item.get("domain") for item in recent_crises if "domain" in item)
        if len(recent_domains) >= 2:
            warning_signs.add("multiple_crisis_domains")
        
        return list(warning_signs)


# Singleton instance
_longitudinal_analyzer: Optional[LongitudinalAnalyzer] = None


async def get_longitudinal_analyzer(redis: Redis) -> LongitudinalAnalyzer:
    """Get the global longitudinal analyzer instance."""
    global _longitudinal_analyzer
    if _longitudinal_analyzer is None:
        _longitudinal_analyzer = LongitudinalAnalyzer(redis=redis)
    return _longitudinal_analyzer
