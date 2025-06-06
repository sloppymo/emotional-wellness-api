"""
Advanced crisis pattern detection and risk prediction for VELURIA.

This module implements:
1. Pattern detection using temporal analysis
2. Machine learning-based risk prediction
3. Early warning system
4. Intervention effectiveness analysis
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from models.emotional_state import SafetyStatus, InterventionRecord

logger = logging.getLogger(__name__)

@dataclass
class RiskPrediction:
    """Risk prediction output"""
    risk_score: float
    confidence: float
    contributing_factors: List[str]
    recommended_actions: List[str]
    prediction_horizon: timedelta
    warning_signs: List[Dict[str, Any]]

@dataclass
class PatternAnalysis:
    """Crisis pattern analysis output"""
    detected_patterns: List[Dict[str, Any]]
    temporal_trends: Dict[str, Any]
    risk_factors: List[Dict[str, float]]
    cyclical_patterns: Optional[Dict[str, Any]]
    intervention_effectiveness: Dict[str, float]

class CrisisPatternDetector:
    """Advanced pattern detection for crisis situations"""
    
    def __init__(self):
        """Initialize the pattern detector"""
        self.scaler = StandardScaler()
        self.anomaly_detector = IsolationForest(
            contamination=0.1,
            random_state=42
        )
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize machine learning models"""
        self.temporal_patterns = {
            "daily": [],
            "weekly": [],
            "monthly": []
        }
        self.known_triggers = set()
        self.effectiveness_scores = {}
    
    def analyze_patterns(
        self,
        safety_history: List[SafetyStatus],
        intervention_history: List[InterventionRecord],
        timeframe: timedelta = timedelta(days=90)
    ) -> PatternAnalysis:
        """
        Analyze patterns in safety status and intervention history.
        
        Args:
            safety_history: Historical safety status records
            intervention_history: Historical intervention records
            timeframe: Time window for analysis
            
        Returns:
            PatternAnalysis containing detected patterns and trends
        """
        # Filter history to timeframe
        cutoff = datetime.now() - timeframe
        recent_safety = [
            status for status in safety_history
            if status.timestamp >= cutoff
        ]
        recent_interventions = [
            record for record in intervention_history
            if record.timestamp >= cutoff
        ]
        
        # Detect temporal patterns
        temporal_patterns = self._analyze_temporal_patterns(recent_safety)
        
        # Identify risk factors
        risk_factors = self._identify_risk_factors(recent_safety, recent_interventions)
        
        # Analyze cyclical patterns
        cyclical_patterns = self._detect_cyclical_patterns(recent_safety)
        
        # Evaluate intervention effectiveness
        effectiveness = self._evaluate_interventions(recent_interventions, recent_safety)
        
        return PatternAnalysis(
            detected_patterns=temporal_patterns["patterns"],
            temporal_trends=temporal_patterns["trends"],
            risk_factors=risk_factors,
            cyclical_patterns=cyclical_patterns,
            intervention_effectiveness=effectiveness
        )
    
    def predict_risk(
        self,
        current_status: SafetyStatus,
        safety_history: List[SafetyStatus],
        user_context: Optional[Dict[str, Any]] = None
    ) -> RiskPrediction:
        """
        Predict future risk levels using machine learning.
        
        Args:
            current_status: Current safety status
            safety_history: Historical safety status records
            user_context: Additional context about the user
            
        Returns:
            RiskPrediction with risk assessment and contributing factors
        """
        # Prepare feature vector
        features = self._extract_prediction_features(
            current_status,
            safety_history,
            user_context
        )
        
        # Detect anomalies
        anomaly_score = self._detect_anomalies(features)
        
        # Calculate risk score
        base_risk = current_status.risk_score
        temporal_risk = self._calculate_temporal_risk(safety_history)
        anomaly_risk = max(0, anomaly_score)
        
        # Combine risk factors
        risk_score = 0.5 * base_risk + 0.3 * temporal_risk + 0.2 * anomaly_risk
        
        # Identify contributing factors
        factors = self._identify_contributing_factors(
            current_status,
            safety_history,
            anomaly_score
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            risk_score,
            factors,
            current_status
        )
        
        # Identify warning signs
        warnings = self._identify_warning_signs(
            current_status,
            safety_history,
            risk_score
        )
        
        return RiskPrediction(
            risk_score=risk_score,
            confidence=0.8,  # TODO: Calculate actual confidence
            contributing_factors=factors,
            recommended_actions=recommendations,
            prediction_horizon=timedelta(hours=24),
            warning_signs=warnings
        )
    
    def _analyze_temporal_patterns(
        self,
        safety_history: List[SafetyStatus]
    ) -> Dict[str, Any]:
        """Analyze temporal patterns in safety status history"""
        if not safety_history:
            return {"patterns": [], "trends": {}}
        
        patterns = []
        trends = {
            "risk_trend": "stable",
            "intervention_frequency": "low",
            "recovery_time": "normal"
        }
        
        # Sort by timestamp
        sorted_history = sorted(safety_history, key=lambda x: x.timestamp)
        
        # Calculate risk score trends
        risk_scores = [status.risk_score for status in sorted_history]
        if len(risk_scores) > 1:
            trend = np.polyfit(range(len(risk_scores)), risk_scores, 1)[0]
            if trend > 0.1:
                trends["risk_trend"] = "increasing"
            elif trend < -0.1:
                trends["risk_trend"] = "decreasing"
        
        # Detect rapid changes
        for i in range(1, len(sorted_history)):
            prev = sorted_history[i-1]
            curr = sorted_history[i]
            if abs(curr.risk_score - prev.risk_score) > 0.3:
                patterns.append({
                    "type": "rapid_change",
                    "timestamp": curr.timestamp,
                    "magnitude": curr.risk_score - prev.risk_score,
                    "triggers": curr.triggers
                })
        
        # Detect persistent high risk
        high_risk_threshold = 0.7
        high_risk_periods = []
        current_period = None
        
        for status in sorted_history:
            if status.risk_score >= high_risk_threshold:
                if current_period is None:
                    current_period = {
                        "start": status.timestamp,
                        "triggers": set(status.triggers)
                    }
                else:
                    current_period["triggers"].update(status.triggers)
            elif current_period is not None:
                current_period["end"] = status.timestamp
                high_risk_periods.append(current_period)
                current_period = None
        
        for period in high_risk_periods:
            patterns.append({
                "type": "persistent_high_risk",
                "start": period["start"],
                "end": period.get("end", sorted_history[-1].timestamp),
                "triggers": list(period["triggers"])
            })
        
        return {
            "patterns": patterns,
            "trends": trends
        }
    
    def _identify_risk_factors(
        self,
        safety_history: List[SafetyStatus],
        intervention_history: List[InterventionRecord]
    ) -> List[Dict[str, float]]:
        """Identify key risk factors from historical data"""
        risk_factors = []
        
        # Analyze trigger frequencies
        trigger_counts = {}
        total_records = len(safety_history)
        
        for status in safety_history:
            for trigger in status.triggers:
                trigger_counts[trigger] = trigger_counts.get(trigger, 0) + 1
        
        # Calculate trigger importance
        for trigger, count in trigger_counts.items():
            frequency = count / total_records
            avg_risk = sum(
                status.risk_score
                for status in safety_history
                if trigger in status.triggers
            ) / count
            
            risk_factors.append({
                "factor": trigger,
                "frequency": frequency,
                "average_risk": avg_risk,
                "importance": frequency * avg_risk
            })
        
        # Sort by importance
        risk_factors.sort(key=lambda x: x["importance"], reverse=True)
        
        return risk_factors
    
    def _detect_cyclical_patterns(
        self,
        safety_history: List[SafetyStatus]
    ) -> Optional[Dict[str, Any]]:
        """Detect cyclical patterns in risk levels"""
        if len(safety_history) < 7:  # Need at least a week of data
            return None
            
        sorted_history = sorted(safety_history, key=lambda x: x.timestamp)
        
        # Analyze daily patterns
        daily_patterns = self._analyze_daily_patterns(sorted_history)
        
        # Analyze weekly patterns
        weekly_patterns = self._analyze_weekly_patterns(sorted_history)
        
        # Analyze monthly patterns
        monthly_patterns = self._analyze_monthly_patterns(sorted_history)
        
        return {
            "daily": daily_patterns,
            "weekly": weekly_patterns,
            "monthly": monthly_patterns
        }
    
    def _evaluate_interventions(
        self,
        interventions: List[InterventionRecord],
        safety_history: List[SafetyStatus]
    ) -> Dict[str, float]:
        """Evaluate the effectiveness of different intervention types"""
        effectiveness = {}
        
        for intervention in interventions:
            # Find safety status changes after intervention
            post_intervention = [
                status for status in safety_history
                if status.timestamp > intervention.timestamp
                and status.timestamp <= intervention.timestamp + timedelta(hours=24)
            ]
            
            if post_intervention:
                # Calculate risk reduction
                initial_risk = intervention.risk_score
                final_risk = post_intervention[-1].risk_score
                reduction = max(0, initial_risk - final_risk)
                
                # Update effectiveness scores
                for action in intervention.actions_taken:
                    if action not in effectiveness:
                        effectiveness[action] = []
                    effectiveness[action].append(reduction)
        
        # Calculate average effectiveness
        return {
            action: sum(scores) / len(scores)
            for action, scores in effectiveness.items()
        }
    
    def _extract_prediction_features(
        self,
        current_status: SafetyStatus,
        safety_history: List[SafetyStatus],
        user_context: Optional[Dict[str, Any]]
    ) -> np.ndarray:
        """Extract features for risk prediction"""
        features = [
            current_status.risk_score,
            len(current_status.triggers),
            self._calculate_trigger_severity(current_status.triggers)
        ]
        
        if safety_history:
            recent = sorted(safety_history, key=lambda x: x.timestamp)[-5:]
            features.extend([s.risk_score for s in recent])
        else:
            features.extend([current_status.risk_score] * 5)
        
        if user_context:
            features.extend([
                user_context.get("stress_level", 0),
                user_context.get("sleep_quality", 0),
                user_context.get("support_level", 0)
            ])
        else:
            features.extend([0, 0, 0])
        
        return np.array(features).reshape(1, -1)
    
    def _detect_anomalies(self, features: np.ndarray) -> float:
        """Detect anomalies in the feature vector"""
        # Scale features
        scaled_features = self.scaler.fit_transform(features)
        
        # Get anomaly score
        score = self.anomaly_detector.score_samples(scaled_features)[0]
        
        # Convert to 0-1 range
        normalized_score = 1 / (1 + np.exp(score))
        
        return normalized_score
    
    def _calculate_temporal_risk(
        self,
        safety_history: List[SafetyStatus]
    ) -> float:
        """Calculate risk based on temporal patterns"""
        if not safety_history:
            return 0.0
            
        recent = sorted(safety_history, key=lambda x: x.timestamp)[-5:]
        
        # Calculate trend
        risk_scores = [s.risk_score for s in recent]
        if len(risk_scores) > 1:
            trend = np.polyfit(range(len(risk_scores)), risk_scores, 1)[0]
            return max(0, min(1, 0.5 + trend))
        
        return recent[-1].risk_score
    
    def _calculate_trigger_severity(self, triggers: List[str]) -> float:
        """Calculate severity score for triggers"""
        severity_weights = {
            "suicide": 1.0,
            "self_harm": 0.9,
            "violence": 0.8,
            "substance": 0.7,
            "trauma": 0.6
        }
        
        severity = 0.0
        for trigger in triggers:
            severity += severity_weights.get(trigger, 0.3)
        
        return min(1.0, severity / len(triggers) if triggers else 0.0)
    
    def _identify_contributing_factors(
        self,
        current_status: SafetyStatus,
        safety_history: List[SafetyStatus],
        anomaly_score: float
    ) -> List[str]:
        """Identify factors contributing to current risk level"""
        factors = []
        
        # Add current triggers
        factors.extend(current_status.triggers)
        
        # Check for rapid escalation
        if safety_history:
            recent = sorted(safety_history, key=lambda x: x.timestamp)[-1]
            if current_status.risk_score - recent.risk_score > 0.3:
                factors.append("rapid_escalation")
        
        # Check for anomalous behavior
        if anomaly_score > 0.7:
            factors.append("unusual_pattern")
        
        return factors
    
    def _generate_recommendations(
        self,
        risk_score: float,
        factors: List[str],
        current_status: SafetyStatus
    ) -> List[str]:
        """Generate recommended actions based on risk assessment"""
        recommendations = []
        
        if risk_score > 0.8:
            recommendations.extend([
                "immediate_crisis_team_notification",
                "prepare_emergency_response",
                "continuous_monitoring"
            ])
        elif risk_score > 0.6:
            recommendations.extend([
                "increase_monitoring_frequency",
                "prepare_intervention_resources",
                "alert_support_network"
            ])
        elif risk_score > 0.4:
            recommendations.extend([
                "enhance_safety_measures",
                "review_crisis_plan",
                "preventive_support"
            ])
        
        # Add factor-specific recommendations
        for factor in factors:
            if factor == "rapid_escalation":
                recommendations.append("urgent_assessment")
            elif factor == "unusual_pattern":
                recommendations.append("detailed_pattern_analysis")
        
        return recommendations
    
    def _identify_warning_signs(
        self,
        current_status: SafetyStatus,
        safety_history: List[SafetyStatus],
        risk_score: float
    ) -> List[Dict[str, Any]]:
        """Identify specific warning signs"""
        warnings = []
        
        # Check for increasing risk trend
        if safety_history:
            recent = sorted(safety_history, key=lambda x: x.timestamp)[-3:]
            risk_trend = [s.risk_score for s in recent]
            if len(risk_trend) > 1 and all(b > a for a, b in zip(risk_trend, risk_trend[1:])):
                warnings.append({
                    "type": "increasing_risk",
                    "severity": "high",
                    "description": "Consistently increasing risk levels"
                })
        
        # Check for multiple high-severity triggers
        high_severity_triggers = [t for t in current_status.triggers if t in ["suicide", "self_harm", "violence"]]
        if len(high_severity_triggers) > 1:
            warnings.append({
                "type": "multiple_severe_triggers",
                "severity": "critical",
                "triggers": high_severity_triggers
            })
        
        # Check overall risk level
        if risk_score > 0.8:
            warnings.append({
                "type": "critical_risk_level",
                "severity": "critical",
                "risk_score": risk_score
            })
        
        return warnings 