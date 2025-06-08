"""
ROOT: Longitudinal Analysis System

This module implements advanced pattern recognition and predictive analytics
for long-term emotional and symbolic pattern analysis.

Key features:
1. Advanced pattern recognition - fancy word for "look for repeating stuff"
2. Predictive analytics - try to guess what happens next
3. Emotional baseline calculation - figure out what's "normal" for this person
4. Trend analysis and visualization - make charts for management
5. Machine learning-based forecasting - throw data at sklearn and hope

most of this is statistical theater but it does spot actual patterns sometimes
"""
#
#   __
#  (oo)____
#  (__)    )\ 
#     ||--|| *
# 
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
from sklearn.ensemble import RandomForestRegressor  # because random forest fixes everything
from sklearn.preprocessing import StandardScaler   # normalize the chaos
from sklearn.model_selection import train_test_split
from scipy import stats

from models.emotional_state import EmotionalState, SymbolicMapping

logger = logging.getLogger(__name__)

@dataclass
class EmotionalBaseline:
    """Emotional baseline calculation results - what's normal for this human"""
    valence_baseline: float      # how positive they usually are
    arousal_baseline: float      # how excited they usually get
    confidence: float            # how sure we are about these numbers
    stability_score: float       # how consistent they are
    variability: Dict[str, float]  # how much they bounce around
    timeframe: timedelta         # how far back we looked

@dataclass
class TrendAnalysis:
    """Trend analysis results - are they getting better or worse"""
    primary_trends: List[Dict[str, Any]]      # main patterns we found
    seasonal_patterns: Optional[Dict[str, Any]]  # monday blues, winter sadness, etc
    change_points: List[Dict[str, Any]]       # moments when everything shifted
    stability_metrics: Dict[str, float]       # how predictable they are
    forecast: Dict[str, List[float]]          # our best guess at the future

@dataclass
class PatternRecognitionResult:
    """Pattern recognition results - what keeps happening to this person"""
    detected_patterns: List[Dict[str, Any]]   # repetitive emotional stuff
    pattern_significance: Dict[str, float]    # which patterns actually matter
    temporal_distribution: Dict[str, Any]     # when patterns show up
    correlations: Dict[str, float]            # what goes with what
    recommendations: List[str]                # helpful suggestions (hopefully)

class ROOTAnalyzer:
    """
    Advanced emotional pattern analysis system.
    
    This class implements longitudinal analysis of emotional states
    and symbolic patterns, providing insights into long-term trends
    and predictions for future states.
    
    basically tries to be a therapist with math
    """
    
    def __init__(self):
        """Initialize the ROOT analyzer - set up all the ML nonsense"""
        self.scaler = StandardScaler()  # make numbers behave
        self.predictor = RandomForestRegressor(
            n_estimators=100,    # 100 decision trees because more = better right?
            random_state=42      # the answer to everything
        )
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize analysis models and parameters - start with empty everything"""
        self.known_patterns = set()      # patterns we've seen before
        self.baseline_cache = {}         # cached baselines so we don't recalculate
        self.trend_models = {}           # models for different trend types
    
    def calculate_baseline(
        self,
        emotional_history: List[EmotionalState],
        timeframe: timedelta = timedelta(days=90)  # 90 days seems reasonable
    ) -> EmotionalBaseline:
        """
        Calculate emotional baseline from historical data.
        
        figure out what's "normal" for this particular human being
        everyone's different, some people are just naturally grumpy
        
        Args:
            emotional_history: List of historical emotional states
            timeframe: Time window for baseline calculation (default 3 months)
            
        Returns:
            EmotionalBaseline containing baseline metrics
        """
        # Filter history to timeframe - only look at recent stuff
        cutoff = datetime.now() - timeframe
        recent_history = [
            state for state in emotional_history
            if state.timestamp >= cutoff
        ]
        
        # if no data, return zeros - can't calculate baseline from nothing
        if not recent_history:
            return EmotionalBaseline(
                valence_baseline=0.0,
                arousal_baseline=0.0,
                confidence=0.0,      # no confidence because no data
                stability_score=0.0,
                variability={},
                timeframe=timeframe
            )
        
        # Calculate baseline metrics - just averages mostly
        valences = [state.valence for state in recent_history]
        arousals = [state.arousal for state in recent_history]
        
        # Calculate baselines with confidence - basic statistics
        valence_baseline = np.mean(valences)  # average happiness/sadness
        arousal_baseline = np.mean(arousals)  # average energy level
        
        # Calculate stability and variability - how consistent are they
        stability = self._calculate_stability(valences, arousals)
        variability = {
            "valence": np.std(valences),     # how much happiness varies
            "arousal": np.std(arousals),     # how much energy varies
            "daily": self._calculate_daily_variability(recent_history),    # day to day changes
            "weekly": self._calculate_weekly_variability(recent_history)   # week to week changes
        }
        
        # Calculate confidence based on data quality and consistency
        # more data + less chaos = higher confidence
        confidence = self._calculate_baseline_confidence(
            recent_history,
            stability,
            variability
        )
        
        return EmotionalBaseline(
            valence_baseline=valence_baseline,
            arousal_baseline=arousal_baseline,
            confidence=confidence,
            stability_score=stability,
            variability=variability,
            timeframe=timeframe
        )
    
    def analyze_trends(
        self,
        emotional_history: List[EmotionalState],
        timeframe: timedelta = timedelta(days=180)  # 6 months for trend analysis
    ) -> TrendAnalysis:
        """
        Analyze emotional trends and patterns.
        
        are they getting better? worse? staying the same?
        also look for seasonal stuff like winter depression
        
        Args:
            emotional_history: List of historical emotional states
            timeframe: Time window for trend analysis (default 6 months)
            
        Returns:
            TrendAnalysis containing trend metrics and forecasts
        """
        # Filter and sort history - only recent stuff, in chronological order
        cutoff = datetime.now() - timeframe
        recent_history = sorted(
            [state for state in emotional_history if state.timestamp >= cutoff],
            key=lambda x: x.timestamp
        )
        
        # if no data, return empty results - can't analyze trends from nothing
        if not recent_history:
            return TrendAnalysis(
                primary_trends=[],
                seasonal_patterns=None,
                change_points=[],
                stability_metrics={},
                forecast={}
            )
        
        # Identify primary trends - are they going up, down, or sideways
        primary_trends = self._identify_primary_trends(recent_history)
        
        # Detect seasonal patterns - winter blues, monday mornings, etc
        seasonal_patterns = self._detect_seasonal_patterns(recent_history)
        
        # Identify change points - moments when everything suddenly shifted
        change_points = self._identify_change_points(recent_history)
        
        # Calculate stability metrics - how predictable are they
        stability_metrics = self._calculate_stability_metrics(recent_history)
        
        # Generate forecasts - our best guess at what happens next
        forecast = self._generate_forecast(recent_history)
        
        return TrendAnalysis(
            primary_trends=primary_trends,
            seasonal_patterns=seasonal_patterns,
            change_points=change_points,
            stability_metrics=stability_metrics,
            forecast=forecast
        )
    
    def recognize_patterns(
        self,
        emotional_history: List[EmotionalState],
        symbolic_history: List[SymbolicMapping]
    ) -> PatternRecognitionResult:
        """
        Recognize complex patterns in emotional and symbolic data.
        
        Args:
            emotional_history: List of historical emotional states
            symbolic_history: List of historical symbolic mappings
            
        Returns:
            PatternRecognitionResult containing recognized patterns
        """
        # Sort histories
        emotional_history = sorted(emotional_history, key=lambda x: x.timestamp)
        symbolic_history = sorted(symbolic_history, key=lambda x: x.timestamp)
        
        # Detect emotional patterns
        emotional_patterns = self._detect_emotional_patterns(emotional_history)
        
        # Detect symbolic patterns
        symbolic_patterns = self._detect_symbolic_patterns(symbolic_history)
        
        # Calculate pattern significance
        significance = self._calculate_pattern_significance(
            emotional_patterns,
            symbolic_patterns
        )
        
        # Analyze temporal distribution
        temporal_dist = self._analyze_temporal_distribution(
            emotional_history,
            symbolic_history
        )
        
        # Calculate correlations
        correlations = self._calculate_correlations(
            emotional_history,
            symbolic_history
        )
        
        # Generate recommendations
        recommendations = self._generate_pattern_recommendations(
            emotional_patterns,
            symbolic_patterns,
            significance
        )
        
        return PatternRecognitionResult(
            detected_patterns=emotional_patterns + symbolic_patterns,
            pattern_significance=significance,
            temporal_distribution=temporal_dist,
            correlations=correlations,
            recommendations=recommendations
        )
    
    def _calculate_stability(
        self,
        valences: List[float],
        arousals: List[float]
    ) -> float:
        """Calculate emotional stability score"""
        if not valences or not arousals:
            return 0.0
        
        # Calculate variability
        valence_var = np.std(valences)
        arousal_var = np.std(arousals)
        
        # Calculate rate of change
        valence_changes = np.diff(valences)
        arousal_changes = np.diff(arousals)
        
        change_rate = np.mean(np.abs(valence_changes) + np.abs(arousal_changes))
        
        # Combine metrics into stability score
        stability = 1.0 - (0.4 * valence_var + 0.4 * arousal_var + 0.2 * change_rate)
        
        return max(0.0, min(1.0, stability))
    
    def _calculate_daily_variability(
        self,
        history: List[EmotionalState]
    ) -> float:
        """Calculate daily emotional variability"""
        if not history:
            return 0.0
        
        # Group by day
        daily_stats = {}
        for state in history:
            day = state.timestamp.date()
            if day not in daily_stats:
                daily_stats[day] = []
            daily_stats[day].append((state.valence, state.arousal))
        
        # Calculate daily ranges
        daily_ranges = []
        for day_stats in daily_stats.values():
            if day_stats:
                valences, arousals = zip(*day_stats)
                valence_range = max(valences) - min(valences)
                arousal_range = max(arousals) - min(arousals)
                daily_ranges.append(valence_range + arousal_range)
        
        return np.mean(daily_ranges) if daily_ranges else 0.0
    
    def _calculate_weekly_variability(
        self,
        history: List[EmotionalState]
    ) -> float:
        """Calculate weekly emotional variability"""
        if not history:
            return 0.0
        
        # Group by week
        weekly_stats = {}
        for state in history:
            week = state.timestamp.isocalendar()[1]
            if week not in weekly_stats:
                weekly_stats[week] = []
            weekly_stats[week].append((state.valence, state.arousal))
        
        # Calculate weekly ranges
        weekly_ranges = []
        for week_stats in weekly_stats.values():
            if week_stats:
                valences, arousals = zip(*week_stats)
                valence_range = max(valences) - min(valences)
                arousal_range = max(arousals) - min(arousals)
                weekly_ranges.append(valence_range + arousal_range)
        
        return np.mean(weekly_ranges) if weekly_ranges else 0.0
    
    def _calculate_baseline_confidence(
        self,
        history: List[EmotionalState],
        stability: float,
        variability: Dict[str, float]
    ) -> float:
        """Calculate confidence in baseline calculations"""
        if not history:
            return 0.0
        
        # Factors affecting confidence
        data_density = min(1.0, len(history) / 100)  # Normalize to 0-1
        time_span = (history[-1].timestamp - history[0].timestamp).days / 90
        consistency = 1.0 - (variability["valence"] + variability["arousal"]) / 2
        
        # Combine factors with weights
        confidence = (
            0.3 * data_density +
            0.3 * stability +
            0.2 * time_span +
            0.2 * consistency
        )
        
        return max(0.0, min(1.0, confidence))
    
    def _identify_primary_trends(
        self,
        history: List[EmotionalState]
    ) -> List[Dict[str, Any]]:
        """Identify primary emotional trends"""
        if not history:
            return []
        
        trends = []
        
        # Extract time series
        times = [(state.timestamp - history[0].timestamp).total_seconds() / 86400
                for state in history]  # Convert to days
        valences = [state.valence for state in history]
        arousals = [state.arousal for state in history]
        
        # Fit linear trends
        valence_trend = np.polyfit(times, valences, 1)
        arousal_trend = np.polyfit(times, arousals, 1)
        
        # Add valence trend
        if abs(valence_trend[0]) > 0.01:  # Significant trend
            trends.append({
                "type": "valence",
                "direction": "increasing" if valence_trend[0] > 0 else "decreasing",
                "magnitude": abs(valence_trend[0]),
                "confidence": self._calculate_trend_confidence(times, valences, valence_trend)
            })
        
        # Add arousal trend
        if abs(arousal_trend[0]) > 0.01:  # Significant trend
            trends.append({
                "type": "arousal",
                "direction": "increasing" if arousal_trend[0] > 0 else "decreasing",
                "magnitude": abs(arousal_trend[0]),
                "confidence": self._calculate_trend_confidence(times, arousals, arousal_trend)
            })
        
        return trends
    
    def _detect_seasonal_patterns(
        self,
        history: List[EmotionalState]
    ) -> Optional[Dict[str, Any]]:
        """Detect seasonal patterns in emotional states"""
        if len(history) < 14:  # Need at least 2 weeks of data
            return None
        
        patterns = {
            "daily": self._analyze_daily_patterns(history),
            "weekly": self._analyze_weekly_patterns(history),
            "monthly": self._analyze_monthly_patterns(history)
        }
        
        return patterns if any(patterns.values()) else None
    
    def _identify_change_points(
        self,
        history: List[EmotionalState]
    ) -> List[Dict[str, Any]]:
        """Identify significant change points in emotional states"""
        if len(history) < 3:
            return []
        
        change_points = []
        window_size = 5
        
        for i in range(window_size, len(history) - window_size):
            before = history[i-window_size:i]
            after = history[i:i+window_size]
            
            # Calculate means
            before_valence = np.mean([s.valence for s in before])
            before_arousal = np.mean([s.arousal for s in after])
            after_valence = np.mean([s.valence for s in after])
            after_arousal = np.mean([s.arousal for s in after])
            
            # Check for significant changes
            if (abs(after_valence - before_valence) > 0.2 or
                abs(after_arousal - before_arousal) > 0.2):
                change_points.append({
                    "timestamp": history[i].timestamp,
                    "valence_change": after_valence - before_valence,
                    "arousal_change": after_arousal - before_arousal,
                    "magnitude": max(
                        abs(after_valence - before_valence),
                        abs(after_arousal - before_arousal)
                    )
                })
        
        return sorted(change_points, key=lambda x: x["magnitude"], reverse=True)
    
    def _calculate_stability_metrics(
        self,
        history: List[EmotionalState]
    ) -> Dict[str, float]:
        """Calculate various stability metrics"""
        if not history:
            return {}
        
        valences = [state.valence for state in history]
        arousals = [state.arousal for state in history]
        
        return {
            "valence_stability": 1.0 - np.std(valences),
            "arousal_stability": 1.0 - np.std(arousals),
            "emotional_entropy": self._calculate_entropy(valences, arousals),
            "trend_consistency": self._calculate_trend_consistency(history)
        }
    
    def _generate_forecast(
        self,
        history: List[EmotionalState]
    ) -> Dict[str, List[float]]:
        """Generate emotional state forecasts"""
        if len(history) < 10:  # Need sufficient history
            return {}
        
        # Prepare data
        X = np.array([
            [(state.timestamp - history[0].timestamp).total_seconds() / 86400]
            for state in history
        ])
        y_valence = np.array([state.valence for state in history])
        y_arousal = np.array([state.arousal for state in history])
        
        # Train models
        self.predictor.fit(X, y_valence)
        valence_forecast = self.predictor.predict(
            X[-1].reshape(1, -1) + np.array([[1, 2, 3, 4, 5]]).T
        )
        
        self.predictor.fit(X, y_arousal)
        arousal_forecast = self.predictor.predict(
            X[-1].reshape(1, -1) + np.array([[1, 2, 3, 4, 5]]).T
        )
        
        return {
            "valence": valence_forecast.tolist(),
            "arousal": arousal_forecast.tolist()
        }
    
    def _detect_emotional_patterns(
        self,
        history: List[EmotionalState]
    ) -> List[Dict[str, Any]]:
        """Detect patterns in emotional states"""
        patterns = []
        
        if len(history) < 5:
            return patterns
        
        # Detect cycles
        cycles = self._detect_cycles(history)
        if cycles:
            patterns.extend(cycles)
        
        # Detect state transitions
        transitions = self._detect_state_transitions(history)
        if transitions:
            patterns.extend(transitions)
        
        # Detect stability periods
        stability = self._detect_stability_periods(history)
        if stability:
            patterns.extend(stability)
        
        return patterns
    
    def _detect_symbolic_patterns(
        self,
        history: List[SymbolicMapping]
    ) -> List[Dict[str, Any]]:
        """Detect patterns in symbolic mappings"""
        patterns = []
        
        if len(history) < 3:
            return patterns
        
        # Analyze symbol sequences
        symbol_sequences = self._analyze_symbol_sequences(history)
        if symbol_sequences:
            patterns.extend(symbol_sequences)
        
        # Analyze archetype transitions
        archetype_transitions = self._analyze_archetype_transitions(history)
        if archetype_transitions:
            patterns.extend(archetype_transitions)
        
        return patterns
    
    def _calculate_pattern_significance(
        self,
        emotional_patterns: List[Dict[str, Any]],
        symbolic_patterns: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate significance scores for detected patterns"""
        significance = {}
        
        # Calculate significance for each pattern
        for pattern in emotional_patterns + symbolic_patterns:
            pattern_type = pattern["type"]
            if "confidence" in pattern:
                significance[pattern_type] = pattern["confidence"]
            elif "magnitude" in pattern:
                significance[pattern_type] = min(1.0, pattern["magnitude"])
            else:
                significance[pattern_type] = 0.5  # Default significance
        
        return significance
    
    def _analyze_temporal_distribution(
        self,
        emotional_history: List[EmotionalState],
        symbolic_history: List[SymbolicMapping]
    ) -> Dict[str, Any]:
        """Analyze temporal distribution of patterns"""
        return {
            "emotional": self._analyze_emotional_distribution(emotional_history),
            "symbolic": self._analyze_symbolic_distribution(symbolic_history),
            "combined": self._analyze_combined_distribution(
                emotional_history,
                symbolic_history
            )
        }
    
    def _calculate_correlations(
        self,
        emotional_history: List[EmotionalState],
        symbolic_history: List[SymbolicMapping]
    ) -> Dict[str, float]:
        """Calculate correlations between emotional and symbolic patterns"""
        correlations = {}
        
        if not emotional_history or not symbolic_history:
            return correlations
        
        # Calculate temporal correlations
        temporal_corr = self._calculate_temporal_correlation(
            emotional_history,
            symbolic_history
        )
        if temporal_corr is not None:
            correlations["temporal"] = temporal_corr
        
        # Calculate symbol-emotion correlations
        symbol_corr = self._calculate_symbol_correlations(
            emotional_history,
            symbolic_history
        )
        correlations.update(symbol_corr)
        
        return correlations
    
    def _generate_pattern_recommendations(
        self,
        emotional_patterns: List[Dict[str, Any]],
        symbolic_patterns: List[Dict[str, Any]],
        significance: Dict[str, float]
    ) -> List[str]:
        """Generate recommendations based on detected patterns"""
        recommendations = []
        
        # Add pattern-specific recommendations
        for pattern in emotional_patterns:
            if pattern["type"] == "cycle" and significance.get("cycle", 0) > 0.7:
                recommendations.append(
                    "Consider tracking emotional cycles for better self-awareness"
                )
            elif pattern["type"] == "transition" and significance.get("transition", 0) > 0.8:
                recommendations.append(
                    "Pay attention to emotional transitions and their triggers"
                )
        
        for pattern in symbolic_patterns:
            if pattern["type"] == "symbol_sequence" and significance.get("symbol_sequence", 0) > 0.7:
                recommendations.append(
                    "Explore recurring symbolic patterns in your emotional journey"
                )
            elif pattern["type"] == "archetype_transition" and significance.get("archetype_transition", 0) > 0.8:
                recommendations.append(
                    "Consider how archetypal patterns influence your emotional state"
                )
        
        return recommendations
