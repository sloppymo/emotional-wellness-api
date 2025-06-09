"""
Real-Time Trend Analysis and Forecasting for Emotional Wellness

This module provides real-time analytics for:
- Emotional state trend analysis and pattern detection
- Population-level wellness trend monitoring
- Predictive forecasting for individual and group outcomes
- Real-time alerting for concerning trends
- Adaptive baseline adjustment and anomaly detection
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from collections import deque, defaultdict
import json
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

from src.utils.structured_logging import get_logger
from src.models.emotional_state import SymbolicMapping
from src.analytics.ml_risk_prediction import RiskLevel

logger = get_logger(__name__)

class TrendDirection(Enum):
    """Trend direction enumeration"""
    STRONGLY_IMPROVING = "strongly_improving"
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    STRONGLY_DECLINING = "strongly_declining"

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class TrendPoint:
    """Single point in a trend analysis"""
    timestamp: datetime
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TrendAnalysis:
    """Complete trend analysis result"""
    trend_direction: TrendDirection
    trend_strength: float  # 0.0 to 1.0
    confidence: float
    slope: float
    r_squared: float
    forecast_7d: float
    forecast_30d: float
    anomaly_score: float
    data_points: List[TrendPoint]
    analysis_timestamp: datetime
    
@dataclass
class PopulationTrend:
    """Population-level trend analysis"""
    metric_name: str
    trend_direction: TrendDirection
    average_value: float
    percentile_25: float
    percentile_75: float
    standard_deviation: float
    sample_size: int
    time_period: str
    demographics: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TrendAlert:
    """Real-time trend alert"""
    alert_id: str
    severity: AlertSeverity
    metric_name: str
    user_id: Optional[str]
    current_value: float
    expected_value: float
    deviation_magnitude: float
    alert_timestamp: datetime
    description: str
    recommended_actions: List[str]

class RealTimeTrendAnalyzer:
    """Real-time trend analysis and forecasting engine"""
    
    def __init__(self, window_size: int = 100, alert_threshold: float = 2.0):
        self.window_size = window_size
        self.alert_threshold = alert_threshold
        
        # Data storage for real-time analysis
        self.user_data_streams: Dict[str, Dict[str, deque]] = defaultdict(
            lambda: defaultdict(lambda: deque(maxlen=window_size))
        )
        
        # Population-level aggregated data
        self.population_metrics: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=window_size * 10)
        )
        
        # Baseline models for anomaly detection
        self.user_baselines: Dict[str, Dict[str, Dict[str, float]]] = defaultdict(
            lambda: defaultdict(dict)
        )
        
        # Alert tracking
        self.active_alerts: Dict[str, TrendAlert] = {}
        self.alert_history: List[TrendAlert] = []
        
        # Metrics to track
        self.tracked_metrics = [
            'valence', 'arousal', 'confidence', 'emotional_intensity',
            'symbol_diversity', 'metaphor_count', 'crisis_indicators'
        ]
    
    async def process_emotional_data(
        self,
        user_id: str,
        mapping: SymbolicMapping,
        biomarkers: Optional[Dict[str, float]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, TrendAnalysis]:
        """Process new emotional data and update trends"""
        
        timestamp = mapping.timestamp or datetime.now()
        
        # Extract metrics from the mapping
        metrics = self._extract_metrics(mapping, biomarkers)
        
        # Update user data streams
        for metric_name, value in metrics.items():
            self.user_data_streams[user_id][metric_name].append(
                TrendPoint(timestamp=timestamp, value=value)
            )
        
        # Update population metrics
        for metric_name, value in metrics.items():
            self.population_metrics[metric_name].append(
                TrendPoint(timestamp=timestamp, value=value, metadata={'user_id': user_id})
            )
        
        # Analyze trends for this user
        trend_analyses = {}
        for metric_name in self.tracked_metrics:
            if len(self.user_data_streams[user_id][metric_name]) >= 5:
                analysis = await self._analyze_trend(
                    user_id, metric_name, self.user_data_streams[user_id][metric_name]
                )
                trend_analyses[metric_name] = analysis
                
                # Check for alerts
                await self._check_trend_alerts(user_id, metric_name, analysis)
        
        # Update user baselines
        await self._update_user_baselines(user_id, metrics)
        
        logger.info(
            f"Processed emotional data for user {user_id}",
            extra={
                'user_id': user_id,
                'metrics_processed': len(metrics),
                'trends_analyzed': len(trend_analyses)
            }
        )
        
        return trend_analyses
    
    def _extract_metrics(
        self,
        mapping: SymbolicMapping,
        biomarkers: Optional[Dict[str, float]]
    ) -> Dict[str, float]:
        """Extract numerical metrics from symbolic mapping"""
        
        metrics = {
            'valence': mapping.valence,
            'arousal': mapping.arousal,
            'confidence': mapping.confidence,
            'emotional_intensity': abs(mapping.valence) + mapping.arousal,
            'symbol_diversity': len(set([mapping.primary_symbol] + mapping.alternative_symbols)),
            'metaphor_count': len(mapping.metaphors),
        }
        
        # Calculate crisis indicators
        crisis_symbols = {'darkness', 'void', 'abyss', 'collapse', 'storm'}
        crisis_score = 0
        if mapping.primary_symbol in crisis_symbols:
            crisis_score += 2
        crisis_score += sum(1 for symbol in mapping.alternative_symbols if symbol in crisis_symbols)
        metrics['crisis_indicators'] = min(crisis_score / 5.0, 1.0)  # Normalize to 0-1
        
        # Add biomarker-derived metrics
        if biomarkers:
            metrics['stress_index'] = self._calculate_stress_index(biomarkers)
            metrics['autonomic_activation'] = self._calculate_autonomic_activation(biomarkers)
        
        return metrics
    
    def _calculate_stress_index(self, biomarkers: Dict[str, float]) -> float:
        """Calculate composite stress index from biomarkers"""
        hr_norm = (biomarkers.get('heart_rate', 70) - 60) / 40  # Normalize around 60-100 bpm
        rr_norm = (biomarkers.get('respiratory_rate', 16) - 12) / 8  # Normalize around 12-20 bpm
        sc_norm = biomarkers.get('skin_conductance', 0.5)  # Already 0-1
        
        stress_index = (hr_norm + rr_norm + sc_norm) / 3
        return max(0, min(1, stress_index))  # Clamp to 0-1
    
    def _calculate_autonomic_activation(self, biomarkers: Dict[str, float]) -> float:
        """Calculate autonomic nervous system activation"""
        hr = biomarkers.get('heart_rate', 70)
        rr = biomarkers.get('respiratory_rate', 16)
        
        # Higher heart rate and respiratory rate indicate higher activation
        activation = ((hr - 60) / 60) + ((rr - 12) / 12)
        return max(0, min(1, activation / 2))  # Normalize to 0-1
    
    async def _analyze_trend(
        self,
        user_id: str,
        metric_name: str,
        data_points: deque
    ) -> TrendAnalysis:
        """Analyze trend for a specific metric"""
        
        if len(data_points) < 3:
            return self._create_insufficient_data_analysis(metric_name)
        
        # Convert to arrays for analysis
        timestamps = np.array([point.timestamp.timestamp() for point in data_points])
        values = np.array([point.value for point in data_points])
        
        # Normalize timestamps to start from 0
        timestamps = timestamps - timestamps[0]
        
        # Linear trend analysis
        slope, intercept, r_value, p_value, std_err = stats.linregress(timestamps, values)
        r_squared = r_value ** 2
        
        # Determine trend direction and strength
        trend_direction = self._classify_trend_direction(slope, std_err)
        trend_strength = min(abs(slope) * len(data_points), 1.0)
        confidence = max(0, min(1, r_squared))
        
        # Forecasting
        if len(data_points) >= 7:
            forecast_7d = self._forecast_value(timestamps, values, days=7)
            forecast_30d = self._forecast_value(timestamps, values, days=30)
        else:
            forecast_7d = values[-1]
            forecast_30d = values[-1]
        
        # Anomaly detection
        anomaly_score = self._calculate_anomaly_score(user_id, metric_name, values[-1])
        
        return TrendAnalysis(
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            confidence=confidence,
            slope=slope,
            r_squared=r_squared,
            forecast_7d=forecast_7d,
            forecast_30d=forecast_30d,
            anomaly_score=anomaly_score,
            data_points=list(data_points),
            analysis_timestamp=datetime.now()
        )
    
    def _classify_trend_direction(self, slope: float, std_err: float) -> TrendDirection:
        """Classify trend direction based on slope and significance"""
        
        # Calculate significance threshold
        significance_threshold = std_err * 2  # 2 standard errors
        
        if slope > significance_threshold:
            if slope > significance_threshold * 2:
                return TrendDirection.STRONGLY_IMPROVING
            else:
                return TrendDirection.IMPROVING
        elif slope < -significance_threshold:
            if slope < -significance_threshold * 2:
                return TrendDirection.STRONGLY_DECLINING
            else:
                return TrendDirection.DECLINING
        else:
            return TrendDirection.STABLE
    
    def _forecast_value(self, timestamps: np.ndarray, values: np.ndarray, days: int) -> float:
        """Forecast value for future timepoint"""
        
        # Simple linear extrapolation
        if len(values) < 3:
            return values[-1]
        
        # Fit linear model
        model = LinearRegression()
        model.fit(timestamps.reshape(-1, 1), values)
        
        # Predict future value (convert days to seconds)
        future_timestamp = timestamps[-1] + (days * 24 * 3600)
        forecast = model.predict([[future_timestamp]])[0]
        
        return forecast
    
    def _calculate_anomaly_score(self, user_id: str, metric_name: str, current_value: float) -> float:
        """Calculate anomaly score for current value"""
        
        baseline = self.user_baselines.get(user_id, {}).get(metric_name, {})
        if not baseline:
            return 0.0
        
        mean = baseline.get('mean', current_value)
        std = baseline.get('std', 1.0)
        
        # Z-score based anomaly detection
        z_score = abs(current_value - mean) / max(std, 0.1)
        anomaly_score = min(z_score / 3.0, 1.0)  # Normalize to 0-1
        
        return anomaly_score
    
    def _create_insufficient_data_analysis(self, metric_name: str) -> TrendAnalysis:
        """Create analysis result for insufficient data"""
        return TrendAnalysis(
            trend_direction=TrendDirection.STABLE,
            trend_strength=0.0,
            confidence=0.0,
            slope=0.0,
            r_squared=0.0,
            forecast_7d=0.0,
            forecast_30d=0.0,
            anomaly_score=0.0,
            data_points=[],
            analysis_timestamp=datetime.now()
        )
    
    async def _check_trend_alerts(
        self,
        user_id: str,
        metric_name: str,
        analysis: TrendAnalysis
    ):
        """Check if trend analysis should trigger alerts"""
        
        alerts = []
        
        # Anomaly-based alerts
        if analysis.anomaly_score > 0.8:
            severity = AlertSeverity.WARNING if analysis.anomaly_score < 0.9 else AlertSeverity.CRITICAL
            alerts.append(self._create_anomaly_alert(user_id, metric_name, analysis, severity))
        
        # Trend-based alerts
        if analysis.trend_direction in [TrendDirection.STRONGLY_DECLINING, TrendDirection.DECLINING]:
            if metric_name in ['valence', 'confidence'] and analysis.trend_strength > 0.7:
                alerts.append(self._create_trend_alert(user_id, metric_name, analysis))
        
        # Crisis indicator alerts
        if metric_name == 'crisis_indicators' and analysis.data_points:
            current_value = analysis.data_points[-1].value
            if current_value > 0.7:
                alerts.append(self._create_crisis_alert(user_id, analysis))
        
        # Store and process alerts
        for alert in alerts:
            self.active_alerts[alert.alert_id] = alert
            self.alert_history.append(alert)
            await self._process_alert(alert)
    
    def _create_anomaly_alert(
        self,
        user_id: str,
        metric_name: str,
        analysis: TrendAnalysis,
        severity: AlertSeverity
    ) -> TrendAlert:
        """Create anomaly-based alert"""
        
        alert_id = f"anomaly_{user_id}_{metric_name}_{datetime.now().timestamp()}"
        current_value = analysis.data_points[-1].value if analysis.data_points else 0
        
        return TrendAlert(
            alert_id=alert_id,
            severity=severity,
            metric_name=metric_name,
            user_id=user_id,
            current_value=current_value,
            expected_value=self._get_baseline_value(user_id, metric_name),
            deviation_magnitude=analysis.anomaly_score,
            alert_timestamp=datetime.now(),
            description=f"Anomalous {metric_name} detected for user {user_id}",
            recommended_actions=[
                "Review recent user activity",
                "Consider intervention assessment",
                "Monitor closely for next 24 hours"
            ]
        )
    
    def _create_trend_alert(
        self,
        user_id: str,
        metric_name: str,
        analysis: TrendAnalysis
    ) -> TrendAlert:
        """Create trend-based alert"""
        
        alert_id = f"trend_{user_id}_{metric_name}_{datetime.now().timestamp()}"
        current_value = analysis.data_points[-1].value if analysis.data_points else 0
        
        return TrendAlert(
            alert_id=alert_id,
            severity=AlertSeverity.WARNING,
            metric_name=metric_name,
            user_id=user_id,
            current_value=current_value,
            expected_value=analysis.forecast_7d,
            deviation_magnitude=analysis.trend_strength,
            alert_timestamp=datetime.now(),
            description=f"Concerning {metric_name} trend for user {user_id}",
            recommended_actions=[
                "Schedule check-in session",
                "Review therapeutic progress",
                "Consider intervention adjustment"
            ]
        )
    
    def _create_crisis_alert(self, user_id: str, analysis: TrendAnalysis) -> TrendAlert:
        """Create crisis-level alert"""
        
        alert_id = f"crisis_{user_id}_{datetime.now().timestamp()}"
        current_value = analysis.data_points[-1].value if analysis.data_points else 0
        
        return TrendAlert(
            alert_id=alert_id,
            severity=AlertSeverity.EMERGENCY,
            metric_name="crisis_indicators",
            user_id=user_id,
            current_value=current_value,
            expected_value=0.3,  # Expected low crisis indicators
            deviation_magnitude=current_value,
            alert_timestamp=datetime.now(),
            description=f"High crisis indicators detected for user {user_id}",
            recommended_actions=[
                "Immediate safety assessment required",
                "Contact crisis intervention team",
                "Implement safety protocols",
                "Consider emergency services"
            ]
        )
    
    def _get_baseline_value(self, user_id: str, metric_name: str) -> float:
        """Get baseline value for user and metric"""
        baseline = self.user_baselines.get(user_id, {}).get(metric_name, {})
        return baseline.get('mean', 0.5)  # Default neutral value
    
    async def _process_alert(self, alert: TrendAlert):
        """Process and handle an alert"""
        
        logger.warning(
            f"Trend alert generated: {alert.description}",
            extra={
                'alert_id': alert.alert_id,
                'severity': alert.severity.value,
                'user_id': alert.user_id,
                'metric': alert.metric_name,
                'current_value': alert.current_value,
                'deviation': alert.deviation_magnitude
            }
        )
        
        # Here you would integrate with notification systems, emergency protocols, etc.
        # For now, we just log the alert
    
    async def _update_user_baselines(self, user_id: str, metrics: Dict[str, float]):
        """Update user baseline models with new data"""
        
        for metric_name, value in metrics.items():
            if user_id not in self.user_baselines:
                self.user_baselines[user_id] = {}
            
            if metric_name not in self.user_baselines[user_id]:
                self.user_baselines[user_id][metric_name] = {
                    'mean': value,
                    'std': 0.1,
                    'count': 1
                }
            else:
                baseline = self.user_baselines[user_id][metric_name]
                count = baseline['count']
                old_mean = baseline['mean']
                
                # Update running mean
                new_mean = (old_mean * count + value) / (count + 1)
                
                # Update running standard deviation
                if count > 1:
                    old_var = baseline['std'] ** 2
                    new_var = ((count - 1) * old_var + (value - old_mean) * (value - new_mean)) / count
                    new_std = np.sqrt(new_var)
                else:
                    new_std = abs(value - old_mean) / 2  # Simple estimate
                
                baseline.update({
                    'mean': new_mean,
                    'std': max(new_std, 0.05),  # Minimum std to avoid division by zero
                    'count': count + 1
                })
    
    async def get_population_trends(
        self,
        time_period: str = "24h",
        demographic_filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, PopulationTrend]:
        """Get population-level trend analysis"""
        
        trends = {}
        
        for metric_name in self.tracked_metrics:
            if metric_name in self.population_metrics:
                trend = await self._analyze_population_metric(
                    metric_name, time_period, demographic_filters
                )
                trends[metric_name] = trend
        
        return trends
    
    async def _analyze_population_metric(
        self,
        metric_name: str,
        time_period: str,
        demographic_filters: Optional[Dict[str, Any]]
    ) -> PopulationTrend:
        """Analyze population trend for a specific metric"""
        
        # Get data points within time period
        cutoff_time = self._get_cutoff_time(time_period)
        recent_points = [
            point for point in self.population_metrics[metric_name]
            if point.timestamp >= cutoff_time
        ]
        
        if not recent_points:
            return self._create_empty_population_trend(metric_name, time_period)
        
        # Extract values
        values = [point.value for point in recent_points]
        
        # Calculate statistics
        average_value = np.mean(values)
        percentile_25 = np.percentile(values, 25)
        percentile_75 = np.percentile(values, 75)
        standard_deviation = np.std(values)
        
        # Determine trend direction (simplified)
        if len(values) >= 10:
            recent_avg = np.mean(values[-5:])
            earlier_avg = np.mean(values[:5])
            
            if recent_avg > earlier_avg + 0.1:
                trend_direction = TrendDirection.IMPROVING
            elif recent_avg < earlier_avg - 0.1:
                trend_direction = TrendDirection.DECLINING
            else:
                trend_direction = TrendDirection.STABLE
        else:
            trend_direction = TrendDirection.STABLE
        
        return PopulationTrend(
            metric_name=metric_name,
            trend_direction=trend_direction,
            average_value=average_value,
            percentile_25=percentile_25,
            percentile_75=percentile_75,
            standard_deviation=standard_deviation,
            sample_size=len(values),
            time_period=time_period
        )
    
    def _get_cutoff_time(self, time_period: str) -> datetime:
        """Get cutoff time for time period"""
        now = datetime.now()
        
        if time_period == "1h":
            return now - timedelta(hours=1)
        elif time_period == "24h":
            return now - timedelta(hours=24)
        elif time_period == "7d":
            return now - timedelta(days=7)
        elif time_period == "30d":
            return now - timedelta(days=30)
        else:
            return now - timedelta(hours=24)  # Default to 24h
    
    def _create_empty_population_trend(self, metric_name: str, time_period: str) -> PopulationTrend:
        """Create empty population trend for insufficient data"""
        return PopulationTrend(
            metric_name=metric_name,
            trend_direction=TrendDirection.STABLE,
            average_value=0.0,
            percentile_25=0.0,
            percentile_75=0.0,
            standard_deviation=0.0,
            sample_size=0,
            time_period=time_period
        )
    
    def get_active_alerts(self, severity_filter: Optional[AlertSeverity] = None) -> List[TrendAlert]:
        """Get currently active alerts"""
        alerts = list(self.active_alerts.values())
        
        if severity_filter:
            alerts = [alert for alert in alerts if alert.severity == severity_filter]
        
        return sorted(alerts, key=lambda x: x.alert_timestamp, reverse=True)
    
    def clear_resolved_alerts(self, alert_ids: List[str]):
        """Clear resolved alerts"""
        for alert_id in alert_ids:
            if alert_id in self.active_alerts:
                del self.active_alerts[alert_id]
    
    def get_trend_summary(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive trend summary for a user"""
        
        summary = {
            'user_id': user_id,
            'analysis_timestamp': datetime.now(),
            'metrics': {},
            'overall_trajectory': TrendDirection.STABLE,
            'risk_indicators': [],
            'recommendations': []
        }
        
        # Analyze each metric
        improving_count = 0
        declining_count = 0
        
        for metric_name in self.tracked_metrics:
            if user_id in self.user_data_streams and metric_name in self.user_data_streams[user_id]:
                data_points = self.user_data_streams[user_id][metric_name]
                if len(data_points) >= 3:
                    # Get trend analysis (this would normally be cached)
                    trend_direction = self._quick_trend_analysis(data_points)
                    summary['metrics'][metric_name] = {
                        'trend_direction': trend_direction,
                        'latest_value': data_points[-1].value,
                        'data_points': len(data_points)
                    }
                    
                    if trend_direction in [TrendDirection.IMPROVING, TrendDirection.STRONGLY_IMPROVING]:
                        improving_count += 1
                    elif trend_direction in [TrendDirection.DECLINING, TrendDirection.STRONGLY_DECLINING]:
                        declining_count += 1
        
        # Determine overall trajectory
        if improving_count > declining_count:
            summary['overall_trajectory'] = TrendDirection.IMPROVING
        elif declining_count > improving_count:
            summary['overall_trajectory'] = TrendDirection.DECLINING
        
        return summary
    
    def _quick_trend_analysis(self, data_points: deque) -> TrendDirection:
        """Quick trend analysis for summary"""
        if len(data_points) < 3:
            return TrendDirection.STABLE
        
        values = [point.value for point in data_points]
        recent_avg = np.mean(values[-3:])
        earlier_avg = np.mean(values[:-3])
        
        diff = recent_avg - earlier_avg
        
        if diff > 0.1:
            return TrendDirection.IMPROVING
        elif diff < -0.1:
            return TrendDirection.DECLINING
        else:
            return TrendDirection.STABLE 