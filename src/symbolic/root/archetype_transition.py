"""
ROOT Archetype Transition Analysis System

This module provides sophisticated archetype transition analysis including:
- Temporal transition pattern detection
- Transition velocity and acceleration analysis
- Predictive modeling for future archetype states
- Crisis-related transition monitoring
- Therapeutic progression tracking
"""

import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from functools import lru_cache
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
import json

from pydantic import BaseModel, Field, ConfigDict, validator
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.cluster import DBSCAN

from .archetypes import ArchetypeCategory, EmotionalArchetype
from .archetype_mapping import ArchetypeMapping, TemporalPattern, MappingConfidence
from structured_logging import get_logger

logger = get_logger(__name__)

class TransitionType(str, Enum):
    """Types of archetype transitions."""
    GRADUAL = "gradual"
    SUDDEN = "sudden"
    CYCLICAL = "cyclical"
    PROGRESSIVE = "progressive"
    REGRESSIVE = "regressive"
    CRISIS_DRIVEN = "crisis_driven"
    THERAPEUTIC = "therapeutic"

class TransitionVelocity(str, Enum):
    """Velocity of archetype transitions."""
    VERY_SLOW = "very_slow"
    SLOW = "slow"
    MODERATE = "moderate"
    FAST = "fast"
    VERY_FAST = "very_fast"

class TransitionDirection(str, Enum):
    """Direction of archetype development."""
    ASCENDING = "ascending"  # Toward more integrated archetypes
    DESCENDING = "descending"  # Toward less integrated archetypes
    LATERAL = "lateral"  # Between similar-level archetypes
    OSCILLATING = "oscillating"  # Back and forth

class CrisisIndicator(str, Enum):
    """Crisis-related transition indicators."""
    STABLE = "stable"
    CONCERNING = "concerning"
    HIGH_RISK = "high_risk"
    CRISIS = "crisis"

@dataclass
class TransitionMetrics:
    """Comprehensive metrics for an archetype transition."""
    from_archetype: ArchetypeCategory
    to_archetype: ArchetypeCategory
    transition_time: timedelta
    velocity: float
    acceleration: float
    stability_before: float
    stability_after: float
    confidence: float
    context_factors: List[str] = field(default_factory=list)

class ArchetypeTransition(BaseModel):
    """Individual archetype transition with comprehensive metadata."""
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    transition_id: str = Field(..., description="Unique transition identifier")
    user_id: Optional[str] = Field(None, description="User identifier (hashed)")
    session_id: Optional[str] = Field(None, description="Session identifier")
    from_archetype: ArchetypeCategory = Field(..., description="Source archetype")
    to_archetype: ArchetypeCategory = Field(..., description="Target archetype")
    transition_type: TransitionType = Field(..., description="Type of transition")
    velocity: TransitionVelocity = Field(..., description="Transition velocity")
    direction: TransitionDirection = Field(..., description="Transition direction")
    start_time: datetime = Field(..., description="Transition start time")
    end_time: datetime = Field(..., description="Transition end time")
    duration: float = Field(..., ge=0.0, description="Transition duration in hours")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Transition confidence")
    stability_change: float = Field(..., ge=-1.0, le=1.0, description="Change in stability")
    crisis_indicator: CrisisIndicator = Field(default=CrisisIndicator.STABLE)
    context_factors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)

class TransitionPrediction(BaseModel):
    """Prediction of future archetype transitions."""
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    predicted_archetype: ArchetypeCategory = Field(..., description="Predicted next archetype")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Prediction confidence")
    estimated_time: float = Field(..., ge=0.0, description="Estimated time to transition (hours)")
    risk_factors: List[str] = Field(default_factory=list)
    intervention_opportunities: List[str] = Field(default_factory=list)
    stability_outlook: float = Field(..., ge=0.0, le=1.0, description="Predicted stability")

class TransitionAnalysis(BaseModel):
    """Comprehensive transition analysis results."""
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    analysis_id: str = Field(..., description="Unique analysis identifier")
    user_id: Optional[str] = Field(None, description="User identifier (hashed)")
    analysis_period: Tuple[datetime, datetime] = Field(..., description="Analysis time period")
    recent_transitions: List[ArchetypeTransition] = Field(default_factory=list)
    dominant_patterns: List[TemporalPattern] = Field(default_factory=list)
    transition_velocity_trend: str = Field(..., description="Velocity trend over time")
    stability_trend: str = Field(..., description="Stability trend over time")
    crisis_risk_level: CrisisIndicator = Field(..., description="Overall crisis risk")
    predictions: List[TransitionPrediction] = Field(default_factory=list)
    therapeutic_insights: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)

class ArchetypeTransitionAnalyzer:
    """
    Advanced archetype transition analysis system.
    
    This class provides comprehensive analysis of archetype transitions including:
    - Transition detection and classification
    - Velocity and acceleration analysis
    - Pattern recognition across time
    - Predictive modeling
    - Crisis risk assessment
    - Therapeutic progress tracking
    """
    
    def __init__(
        self, 
        cache_size: int = 256,
        analysis_window_hours: int = 168,  # 1 week default
        prediction_horizon_hours: int = 72  # 3 days default
    ):
        self.cache_size = cache_size
        self.analysis_window = timedelta(hours=analysis_window_hours)
        self.prediction_horizon = timedelta(hours=prediction_horizon_hours)
        self._logger = get_logger(f"{__name__}.ArchetypeTransitionAnalyzer")
        
        # Data structures
        self._user_transitions: Dict[str, deque] = defaultdict(lambda: deque(maxlen=500))
        self._transition_cache: Dict[str, TransitionAnalysis] = {}
        self._prediction_models: Dict[str, LinearRegression] = {}
        
        # Archetype hierarchy for direction analysis
        self._archetype_hierarchy = self._build_archetype_hierarchy()
        
        # Transition matrices
        self._transition_frequencies: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._transition_velocities: Dict[str, List[float]] = defaultdict(list)
        
        self._logger.info("ArchetypeTransitionAnalyzer initialized")
    
    def _build_archetype_hierarchy(self) -> Dict[ArchetypeCategory, int]:
        """Build archetype hierarchy for development analysis."""
        # Based on Jungian development and integration levels
        return {
            ArchetypeCategory.INNOCENT: 1,
            ArchetypeCategory.EVERYMAN: 2,
            ArchetypeCategory.HERO: 3,
            ArchetypeCategory.CAREGIVER: 4,
            ArchetypeCategory.LOVER: 5,
            ArchetypeCategory.EXPLORER: 6,
            ArchetypeCategory.OUTLAW: 7,
            ArchetypeCategory.CREATOR: 8,
            ArchetypeCategory.RULER: 9,
            ArchetypeCategory.MAGICIAN: 10,
            ArchetypeCategory.SAGE: 11,
            ArchetypeCategory.JESTER: 12  # Special case - transcendent
        }
    
    async def analyze_transitions(
        self,
        archetype_mappings: List[ArchetypeMapping],
        user_id: Optional[str] = None,
        include_predictions: bool = True
    ) -> TransitionAnalysis:
        """
        Analyze archetype transitions from a sequence of mappings.
        
        Args:
            archetype_mappings: List of archetype mappings in chronological order
            user_id: Optional user identifier
            include_predictions: Whether to include future predictions
            
        Returns:
            TransitionAnalysis with comprehensive results
        """
        start_time = datetime.now()
        
        try:
            # Sort mappings by timestamp
            sorted_mappings = sorted(archetype_mappings, key=lambda m: m.created_at)
            
            if len(sorted_mappings) < 2:
                return await self._create_minimal_analysis(user_id, sorted_mappings)
            
            # Detect transitions
            transitions = await self._detect_transitions(sorted_mappings, user_id)
            
            # Analyze patterns
            patterns = await self._analyze_transition_patterns(transitions)
            
            # Calculate trends
            velocity_trend = await self._analyze_velocity_trend(transitions)
            stability_trend = await self._analyze_stability_trend(sorted_mappings)
            
            # Assess crisis risk
            crisis_risk = await self._assess_crisis_risk(transitions, sorted_mappings)
            
            # Generate predictions if requested
            predictions = []
            if include_predictions and len(transitions) >= 3:
                predictions = await self._generate_predictions(transitions, user_id)
            
            # Generate therapeutic insights
            insights = await self._generate_therapeutic_insights(
                transitions, patterns, crisis_risk
            )
            
            # Create analysis
            analysis_period = (sorted_mappings[0].created_at, sorted_mappings[-1].created_at)
            
            analysis = TransitionAnalysis(
                analysis_id=self._generate_analysis_id(sorted_mappings, user_id),
                user_id=user_id,
                analysis_period=analysis_period,
                recent_transitions=transitions[-10:],  # Last 10 transitions
                dominant_patterns=patterns,
                transition_velocity_trend=velocity_trend,
                stability_trend=stability_trend,
                crisis_risk_level=crisis_risk,
                predictions=predictions,
                therapeutic_insights=insights,
                metadata={
                    "processing_time": (datetime.now() - start_time).total_seconds(),
                    "total_transitions": len(transitions),
                    "mappings_analyzed": len(sorted_mappings),
                    "analysis_window_hours": self.analysis_window.total_seconds() / 3600
                }
            )
            
            # Store transitions for user
            if user_id:
                await self._store_user_transitions(user_id, transitions)
            
            # Cache analysis
            self._cache_analysis(analysis)
            
            self._logger.info(
                f"Transition analysis completed",
                extra={
                    "user_id": user_id,
                    "transitions_detected": len(transitions),
                    "crisis_risk": crisis_risk.value,
                    "processing_time": analysis.metadata["processing_time"]
                }
            )
            
            return analysis
            
        except Exception as e:
            self._logger.error(
                f"Error in transition analysis: {str(e)}",
                extra={
                    "user_id": user_id,
                    "error_type": type(e).__name__
                }
            )
            raise
    
    async def _detect_transitions(
        self, 
        mappings: List[ArchetypeMapping],
        user_id: Optional[str]
    ) -> List[ArchetypeTransition]:
        """Detect archetype transitions from mapping sequence."""
        transitions = []
        
        for i in range(len(mappings) - 1):
            current = mappings[i]
            next_mapping = mappings[i + 1]
            
            # Check if there's an archetype change
            if current.primary_archetype != next_mapping.primary_archetype:
                transition = await self._create_transition(
                    current, next_mapping, user_id
                )
                transitions.append(transition)
        
        return transitions
    
    async def _create_transition(
        self,
        from_mapping: ArchetypeMapping,
        to_mapping: ArchetypeMapping,
        user_id: Optional[str]
    ) -> ArchetypeTransition:
        """Create a detailed transition object."""
        # Calculate transition metrics
        duration = (to_mapping.created_at - from_mapping.created_at).total_seconds() / 3600
        
        # Determine transition type
        transition_type = await self._classify_transition_type(
            from_mapping, to_mapping, duration
        )
        
        # Calculate velocity
        velocity_score = await self._calculate_velocity_score(
            from_mapping.primary_archetype, to_mapping.primary_archetype, duration
        )
        velocity = self._classify_velocity(velocity_score)
        
        # Determine direction
        direction = self._determine_direction(
            from_mapping.primary_archetype, to_mapping.primary_archetype
        )
        
        # Calculate stability change
        from_stability = await self._estimate_stability(from_mapping)
        to_stability = await self._estimate_stability(to_mapping)
        stability_change = to_stability - from_stability
        
        # Assess crisis indicator
        crisis_indicator = await self._assess_transition_crisis_risk(
            from_mapping, to_mapping, transition_type, velocity_score
        )
        
        # Extract context factors
        context_factors = self._extract_context_factors(from_mapping, to_mapping)
        
        # Calculate confidence
        confidence = self._calculate_transition_confidence(
            from_mapping, to_mapping, duration
        )
        
        return ArchetypeTransition(
            transition_id=self._generate_transition_id(from_mapping, to_mapping),
            user_id=user_id,
            session_id=to_mapping.session_id,
            from_archetype=from_mapping.primary_archetype,
            to_archetype=to_mapping.primary_archetype,
            transition_type=transition_type,
            velocity=velocity,
            direction=direction,
            start_time=from_mapping.created_at,
            end_time=to_mapping.created_at,
            duration=duration,
            confidence=confidence,
            stability_change=stability_change,
            crisis_indicator=crisis_indicator,
            context_factors=context_factors,
            metadata={
                "from_confidence": from_mapping.confidence.value,
                "to_confidence": to_mapping.confidence.value,
                "velocity_score": velocity_score
            }
        )
    
    async def _classify_transition_type(
        self,
        from_mapping: ArchetypeMapping,
        to_mapping: ArchetypeMapping,
        duration: float
    ) -> TransitionType:
        """Classify the type of transition."""
        # Analyze archetype relationship
        from_arch = from_mapping.primary_archetype
        to_arch = to_mapping.primary_archetype
        
        # Check for crisis-driven transitions
        if (from_mapping.confidence == MappingConfidence.LOW or 
            to_mapping.confidence == MappingConfidence.LOW):
            return TransitionType.CRISIS_DRIVEN
        
        # Check for therapeutic progression
        from_level = self._archetype_hierarchy[from_arch]
        to_level = self._archetype_hierarchy[to_arch]
        
        if to_level > from_level and duration > 24:  # More than a day
            return TransitionType.THERAPEUTIC
        
        # Check duration for sudden vs gradual
        if duration < 1:  # Less than 1 hour
            return TransitionType.SUDDEN
        elif duration > 48:  # More than 2 days
            return TransitionType.GRADUAL
        
        # Check for progression vs regression
        if to_level > from_level:
            return TransitionType.PROGRESSIVE
        elif to_level < from_level:
            return TransitionType.REGRESSIVE
        
        # Default to gradual
        return TransitionType.GRADUAL
    
    async def _calculate_velocity_score(
        self,
        from_archetype: ArchetypeCategory,
        to_archetype: ArchetypeCategory,
        duration: float
    ) -> float:
        """Calculate transition velocity score."""
        # Calculate archetype distance
        from_level = self._archetype_hierarchy[from_archetype]
        to_level = self._archetype_hierarchy[to_archetype]
        archetype_distance = abs(to_level - from_level)
        
        # Velocity = distance / time (with time normalization)
        if duration <= 0:
            return 10.0  # Maximum velocity for instant transitions
        
        # Normalize duration (hours to days)
        duration_days = duration / 24.0
        velocity = archetype_distance / max(0.1, duration_days)
        
        return min(10.0, velocity)
    
    def _classify_velocity(self, velocity_score: float) -> TransitionVelocity:
        """Classify velocity score into categories."""
        if velocity_score >= 8.0:
            return TransitionVelocity.VERY_FAST
        elif velocity_score >= 5.0:
            return TransitionVelocity.FAST
        elif velocity_score >= 2.0:
            return TransitionVelocity.MODERATE
        elif velocity_score >= 1.0:
            return TransitionVelocity.SLOW
        else:
            return TransitionVelocity.VERY_SLOW
    
    def _determine_direction(
        self,
        from_archetype: ArchetypeCategory,
        to_archetype: ArchetypeCategory
    ) -> TransitionDirection:
        """Determine the direction of transition."""
        from_level = self._archetype_hierarchy[from_archetype]
        to_level = self._archetype_hierarchy[to_archetype]
        
        level_diff = to_level - from_level
        
        if level_diff > 2:
            return TransitionDirection.ASCENDING
        elif level_diff < -2:
            return TransitionDirection.DESCENDING
        elif abs(level_diff) <= 2:
            return TransitionDirection.LATERAL
        
        return TransitionDirection.LATERAL
    
    async def _estimate_stability(self, mapping: ArchetypeMapping) -> float:
        """Estimate stability from an archetype mapping."""
        # Use confidence and temporal pattern as stability indicators
        confidence_factor = {
            MappingConfidence.VERY_HIGH: 1.0,
            MappingConfidence.HIGH: 0.8,
            MappingConfidence.MEDIUM: 0.6,
            MappingConfidence.LOW: 0.3
        }.get(mapping.confidence, 0.5)
        
        pattern_factor = {
            TemporalPattern.STABLE: 1.0,
            TemporalPattern.TRANSITIONAL: 0.7,
            TemporalPattern.ASCENDING: 0.8,
            TemporalPattern.DESCENDING: 0.6,
            TemporalPattern.CYCLICAL: 0.5,
            TemporalPattern.CHAOTIC: 0.2
        }.get(mapping.temporal_pattern, 0.5)
        
        return (confidence_factor + pattern_factor) / 2.0
    
    async def _assess_transition_crisis_risk(
        self,
        from_mapping: ArchetypeMapping,
        to_mapping: ArchetypeMapping,
        transition_type: TransitionType,
        velocity_score: float
    ) -> CrisisIndicator:
        """Assess crisis risk for a transition."""
        risk_factors = 0
        
        # High velocity transitions
        if velocity_score >= 6.0:
            risk_factors += 2
        elif velocity_score >= 4.0:
            risk_factors += 1
        
        # Crisis-driven or regressive transitions
        if transition_type in [TransitionType.CRISIS_DRIVEN, TransitionType.REGRESSIVE]:
            risk_factors += 2
        elif transition_type == TransitionType.SUDDEN:
            risk_factors += 1
        
        # Low confidence mappings
        if (from_mapping.confidence == MappingConfidence.LOW or 
            to_mapping.confidence == MappingConfidence.LOW):
            risk_factors += 1
        
        # Chaotic patterns
        if (from_mapping.temporal_pattern == TemporalPattern.CHAOTIC or
            to_mapping.temporal_pattern == TemporalPattern.CHAOTIC):
            risk_factors += 2
        
        # Map risk factors to indicators
        if risk_factors >= 5:
            return CrisisIndicator.CRISIS
        elif risk_factors >= 3:
            return CrisisIndicator.HIGH_RISK
        elif risk_factors >= 1:
            return CrisisIndicator.CONCERNING
        else:
            return CrisisIndicator.STABLE
    
    def _extract_context_factors(
        self,
        from_mapping: ArchetypeMapping,
        to_mapping: ArchetypeMapping
    ) -> List[str]:
        """Extract context factors that may have influenced the transition."""
        factors = []
        
        # Confidence changes
        if from_mapping.confidence != to_mapping.confidence:
            factors.append(f"confidence_change_{from_mapping.confidence.value}_to_{to_mapping.confidence.value}")
        
        # Pattern changes
        if from_mapping.temporal_pattern != to_mapping.temporal_pattern:
            factors.append(f"pattern_change_{from_mapping.temporal_pattern.value}_to_{to_mapping.temporal_pattern.value}")
        
        # Cultural context
        if from_mapping.cultural_context != to_mapping.cultural_context:
            factors.append(f"cultural_shift_{from_mapping.cultural_context.value}_to_{to_mapping.cultural_context.value}")
        
        return factors
    
    def _calculate_transition_confidence(
        self,
        from_mapping: ArchetypeMapping,
        to_mapping: ArchetypeMapping,
        duration: float
    ) -> float:
        """Calculate confidence in the transition detection."""
        confidence_factors = []
        
        # Mapping confidence factor
        from_conf = {
            MappingConfidence.VERY_HIGH: 1.0,
            MappingConfidence.HIGH: 0.8,
            MappingConfidence.MEDIUM: 0.6,
            MappingConfidence.LOW: 0.3
        }.get(from_mapping.confidence, 0.5)
        
        to_conf = {
            MappingConfidence.VERY_HIGH: 1.0,
            MappingConfidence.HIGH: 0.8,
            MappingConfidence.MEDIUM: 0.6,
            MappingConfidence.LOW: 0.3
        }.get(to_mapping.confidence, 0.5)
        
        confidence_factors.append((from_conf + to_conf) / 2.0)
        
        # Duration factor (very short or very long transitions are less confident)
        if 1 <= duration <= 72:  # 1 hour to 3 days is optimal
            duration_factor = 1.0
        elif 0.1 <= duration < 1 or 72 < duration <= 168:  # Sub-optimal ranges
            duration_factor = 0.7
        else:  # Very short or very long
            duration_factor = 0.4
        
        confidence_factors.append(duration_factor)
        
        # Archetype distance factor (closer archetypes = higher confidence)
        from_level = self._archetype_hierarchy[from_mapping.primary_archetype]
        to_level = self._archetype_hierarchy[to_mapping.primary_archetype]
        distance = abs(to_level - from_level)
        
        if distance <= 2:
            distance_factor = 1.0
        elif distance <= 4:
            distance_factor = 0.8
        else:
            distance_factor = 0.6
        
        confidence_factors.append(distance_factor)
        
        return sum(confidence_factors) / len(confidence_factors)
    
    async def _analyze_transition_patterns(
        self, 
        transitions: List[ArchetypeTransition]
    ) -> List[TemporalPattern]:
        """Analyze patterns in the transition sequence."""
        if len(transitions) < 3:
            return [TemporalPattern.STABLE]
        
        patterns = []
        
        # Analyze velocity patterns
        velocities = [t.metadata.get("velocity_score", 1.0) for t in transitions]
        velocity_trend = self._analyze_trend(velocities)
        
        # Analyze direction patterns
        directions = [t.direction for t in transitions]
        direction_counts = {d: directions.count(d) for d in set(directions)}
        dominant_direction = max(direction_counts, key=direction_counts.get)
        
        # Detect cyclical patterns
        archetype_sequence = [t.to_archetype.value for t in transitions]
        if self._detect_cycles(archetype_sequence):
            patterns.append(TemporalPattern.CYCLICAL)
        
        # Detect progressive patterns
        if dominant_direction == TransitionDirection.ASCENDING:
            patterns.append(TemporalPattern.ASCENDING)
        elif dominant_direction == TransitionDirection.DESCENDING:
            patterns.append(TemporalPattern.DESCENDING)
        
        # Detect chaotic patterns
        unique_types = len(set(t.transition_type for t in transitions))
        if unique_types >= len(transitions) * 0.8:  # High variety
            patterns.append(TemporalPattern.CHAOTIC)
        
        return patterns if patterns else [TemporalPattern.STABLE]
    
    def _detect_cycles(self, sequence: List[str]) -> bool:
        """Detect cyclical patterns in archetype sequence."""
        if len(sequence) < 6:
            return False
        
        # Look for repeating subsequences
        for cycle_length in range(2, len(sequence) // 2 + 1):
            cycles_found = 0
            for i in range(len(sequence) - cycle_length * 2 + 1):
                subsequence = sequence[i:i + cycle_length]
                next_subsequence = sequence[i + cycle_length:i + cycle_length * 2]
                
                if subsequence == next_subsequence:
                    cycles_found += 1
            
            if cycles_found >= 2:
                return True
        
        return False
    
    def _analyze_trend(self, values: List[float]) -> str:
        """Analyze trend in a sequence of values."""
        if len(values) < 3:
            return "stable"
        
        # Simple linear regression
        x = np.array(range(len(values)))
        y = np.array(values)
        
        # Calculate slope
        n = len(x)
        slope = (n * np.sum(x * y) - np.sum(x) * np.sum(y)) / (n * np.sum(x * x) - np.sum(x) * np.sum(x))
        
        if slope > 0.1:
            return "increasing"
        elif slope < -0.1:
            return "decreasing"
        else:
            return "stable"
    
    async def _analyze_velocity_trend(self, transitions: List[ArchetypeTransition]) -> str:
        """Analyze velocity trend over time."""
        if len(transitions) < 3:
            return "stable"
        
        velocities = [t.metadata.get("velocity_score", 1.0) for t in transitions]
        return self._analyze_trend(velocities)
    
    async def _analyze_stability_trend(self, mappings: List[ArchetypeMapping]) -> str:
        """Analyze stability trend over time."""
        if len(mappings) < 3:
            return "stable"
        
        stabilities = []
        for mapping in mappings:
            stability = await self._estimate_stability(mapping)
            stabilities.append(stability)
        
        return self._analyze_trend(stabilities)
    
    async def _assess_crisis_risk(
        self,
        transitions: List[ArchetypeTransition],
        mappings: List[ArchetypeMapping]
    ) -> CrisisIndicator:
        """Assess overall crisis risk from transitions and mappings."""
        if not transitions:
            return CrisisIndicator.STABLE
        
        # Count high-risk indicators
        risk_score = 0
        
        # Recent high-risk transitions
        recent_transitions = transitions[-5:]  # Last 5 transitions
        high_risk_count = sum(1 for t in recent_transitions 
                            if t.crisis_indicator in [CrisisIndicator.HIGH_RISK, CrisisIndicator.CRISIS])
        
        risk_score += high_risk_count * 2
        
        # Rapid velocity changes
        rapid_velocity_count = sum(1 for t in recent_transitions 
                                 if t.velocity in [TransitionVelocity.FAST, TransitionVelocity.VERY_FAST])
        
        risk_score += rapid_velocity_count
        
        # Regressive transitions
        regressive_count = sum(1 for t in recent_transitions 
                             if t.transition_type == TransitionType.REGRESSIVE)
        
        risk_score += regressive_count
        
        # Overall stability trend
        recent_mappings = mappings[-10:]  # Last 10 mappings
        low_confidence_count = sum(1 for m in recent_mappings 
                                 if m.confidence == MappingConfidence.LOW)
        
        risk_score += low_confidence_count
        
        # Map to crisis indicators
        if risk_score >= 8:
            return CrisisIndicator.CRISIS
        elif risk_score >= 5:
            return CrisisIndicator.HIGH_RISK
        elif risk_score >= 2:
            return CrisisIndicator.CONCERNING
        else:
            return CrisisIndicator.STABLE
    
    async def _generate_predictions(
        self,
        transitions: List[ArchetypeTransition],
        user_id: Optional[str]
    ) -> List[TransitionPrediction]:
        """Generate predictions for future transitions."""
        if len(transitions) < 3:
            return []
        
        predictions = []
        
        # Analyze recent patterns
        recent_transitions = transitions[-10:]
        
        # Pattern-based prediction
        pattern_prediction = await self._predict_from_patterns(recent_transitions)
        if pattern_prediction:
            predictions.append(pattern_prediction)
        
        # Velocity-based prediction
        velocity_prediction = await self._predict_from_velocity(recent_transitions)
        if velocity_prediction:
            predictions.append(velocity_prediction)
        
        return predictions[:3]  # Return top 3 predictions
    
    async def _predict_from_patterns(
        self, 
        transitions: List[ArchetypeTransition]
    ) -> Optional[TransitionPrediction]:
        """Predict next transition based on patterns."""
        if len(transitions) < 3:
            return None
        
        # Analyze archetype sequence
        archetype_sequence = [t.to_archetype for t in transitions]
        
        # Simple pattern matching - look for most common next archetype
        archetype_counts = defaultdict(int)
        for i in range(len(archetype_sequence) - 1):
            current = archetype_sequence[i]
            next_arch = archetype_sequence[i + 1]
            archetype_counts[next_arch] += 1
        
        if archetype_counts:
            predicted_archetype = max(archetype_counts, key=archetype_counts.get)
            confidence = archetype_counts[predicted_archetype] / len(transitions)
            
            # Estimate time based on average transition duration
            durations = [t.duration for t in transitions]
            estimated_time = np.mean(durations)
            
            return TransitionPrediction(
                predicted_archetype=predicted_archetype,
                confidence=min(0.9, confidence),
                estimated_time=estimated_time,
                risk_factors=[],
                intervention_opportunities=[],
                stability_outlook=0.5
            )
        
        return None
    
    async def _predict_from_velocity(
        self, 
        transitions: List[ArchetypeTransition]
    ) -> Optional[TransitionPrediction]:
        """Predict next transition based on velocity trends."""
        if len(transitions) < 3:
            return None
        
        # Analyze velocity trend
        velocities = [t.metadata.get("velocity_score", 1.0) for t in transitions]
        
        # If velocity is increasing, predict faster transitions
        velocity_trend = self._analyze_trend(velocities)
        
        if velocity_trend == "increasing":
            # Predict accelerated transition
            last_transition = transitions[-1]
            next_archetype = self._predict_next_archetype_by_direction(
                last_transition.to_archetype, last_transition.direction
            )
            
            if next_archetype:
                return TransitionPrediction(
                    predicted_archetype=next_archetype,
                    confidence=0.6,
                    estimated_time=last_transition.duration * 0.7,  # Faster
                    risk_factors=["accelerating_transitions"],
                    intervention_opportunities=["stabilization_techniques"],
                    stability_outlook=0.4
                )
        
        return None
    
    def _predict_next_archetype_by_direction(
        self, 
        current_archetype: ArchetypeCategory,
        direction: TransitionDirection
    ) -> Optional[ArchetypeCategory]:
        """Predict next archetype based on direction."""
        current_level = self._archetype_hierarchy[current_archetype]
        
        if direction == TransitionDirection.ASCENDING:
            # Move to next higher level
            target_level = current_level + 1
        elif direction == TransitionDirection.DESCENDING:
            # Move to next lower level
            target_level = current_level - 1
        else:
            # Lateral movement - stay at same level or move slightly
            return None
        
        # Find archetype at target level
        for archetype, level in self._archetype_hierarchy.items():
            if level == target_level:
                return archetype
        
        return None
    
    async def _generate_therapeutic_insights(
        self,
        transitions: List[ArchetypeTransition],
        patterns: List[TemporalPattern],
        crisis_risk: CrisisIndicator
    ) -> List[str]:
        """Generate therapeutic insights from transition analysis."""
        insights = []
        
        if not transitions:
            insights.append("Stable archetype expression - consider exploring new aspects of personality")
            return insights
        
        # Pattern-based insights
        if TemporalPattern.ASCENDING in patterns:
            insights.append("Positive developmental trajectory observed - encourage continued growth")
        
        if TemporalPattern.DESCENDING in patterns:
            insights.append("Regressive pattern detected - may benefit from stabilization interventions")
        
        if TemporalPattern.CYCLICAL in patterns:
            insights.append("Cyclical patterns suggest underlying themes that may benefit from exploration")
        
        if TemporalPattern.CHAOTIC in patterns:
            insights.append("Chaotic transition patterns indicate need for grounding and stability work")
        
        # Crisis risk insights
        if crisis_risk == CrisisIndicator.CRISIS:
            insights.append("URGENT: High crisis risk detected - immediate therapeutic intervention recommended")
        elif crisis_risk == CrisisIndicator.HIGH_RISK:
            insights.append("Elevated risk patterns - increased therapeutic support recommended")
        elif crisis_risk == CrisisIndicator.CONCERNING:
            insights.append("Some concerning patterns - monitoring and support recommended")
        
        # Velocity insights
        recent_transitions = transitions[-5:]
        fast_transitions = sum(1 for t in recent_transitions 
                             if t.velocity in [TransitionVelocity.FAST, TransitionVelocity.VERY_FAST])
        
        if fast_transitions >= 3:
            insights.append("Rapid archetype changes suggest emotional intensity - grounding techniques may help")
        
        # Therapeutic progression insights
        therapeutic_transitions = sum(1 for t in transitions 
                                    if t.transition_type == TransitionType.THERAPEUTIC)
        
        if therapeutic_transitions >= len(transitions) * 0.5:
            insights.append("Strong therapeutic progression observed - continue current approach")
        
        return insights
    
    async def _create_minimal_analysis(
        self, 
        user_id: Optional[str], 
        mappings: List[ArchetypeMapping]
    ) -> TransitionAnalysis:
        """Create minimal analysis for insufficient data."""
        if mappings:
            analysis_period = (mappings[0].created_at, mappings[-1].created_at)
        else:
            now = datetime.now()
            analysis_period = (now, now)
        
        return TransitionAnalysis(
            analysis_id=self._generate_analysis_id(mappings, user_id),
            user_id=user_id,
            analysis_period=analysis_period,
            recent_transitions=[],
            dominant_patterns=[TemporalPattern.STABLE],
            transition_velocity_trend="stable",
            stability_trend="stable",
            crisis_risk_level=CrisisIndicator.STABLE,
            predictions=[],
            therapeutic_insights=["Insufficient data for comprehensive analysis - continue monitoring"],
            metadata={"insufficient_data": True}
        )
    
    def _generate_analysis_id(
        self, 
        mappings: List[ArchetypeMapping], 
        user_id: Optional[str]
    ) -> str:
        """Generate unique analysis ID."""
        content = {
            "user_id": user_id,
            "mapping_count": len(mappings),
            "timestamp": datetime.now().isoformat()
        }
        return json.dumps(content, sort_keys=True).encode().hex()[:16]
    
    def _generate_transition_id(
        self, 
        from_mapping: ArchetypeMapping, 
        to_mapping: ArchetypeMapping
    ) -> str:
        """Generate unique transition ID."""
        content = f"{from_mapping.mapping_id}:{to_mapping.mapping_id}"
        return content.encode().hex()[:16]
    
    async def _store_user_transitions(
        self, 
        user_id: str, 
        transitions: List[ArchetypeTransition]
    ) -> None:
        """Store transitions in user timeline."""
        for transition in transitions:
            self._user_transitions[user_id].append({
                "transition_id": transition.transition_id,
                "from_archetype": transition.from_archetype.value,
                "to_archetype": transition.to_archetype.value,
                "transition_type": transition.transition_type.value,
                "velocity": transition.velocity.value,
                "duration": transition.duration,
                "crisis_indicator": transition.crisis_indicator.value,
                "timestamp": transition.end_time.isoformat()
            })
    
    def _cache_analysis(self, analysis: TransitionAnalysis) -> None:
        """Cache the transition analysis."""
        cache_key = f"{analysis.user_id}:{analysis.analysis_id}"
        self._transition_cache[cache_key] = analysis
        
        # Maintain cache size
        if len(self._transition_cache) > self.cache_size:
            oldest_key = min(
                self._transition_cache.keys(),
                key=lambda k: self._transition_cache[k].created_at
            )
            del self._transition_cache[oldest_key]
    
    async def get_user_transition_history(
        self, 
        user_id: str, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get transition history for a user."""
        transitions = self._user_transitions.get(user_id, deque())
        return list(transitions)[-limit:] if transitions else []


# Convenience functions
async def analyze_archetype_transitions(
    mappings: List[ArchetypeMapping],
    user_id: Optional[str] = None
) -> TransitionAnalysis:
    """Convenience function for archetype transition analysis."""
    analyzer = ArchetypeTransitionAnalyzer()
    return await analyzer.analyze_transitions(mappings, user_id)

async def predict_next_archetype(
    transitions: List[ArchetypeTransition]
) -> Optional[TransitionPrediction]:
    """Convenience function for archetype prediction."""
    analyzer = ArchetypeTransitionAnalyzer()
    predictions = await analyzer._generate_predictions(transitions, None)
    return predictions[0] if predictions else None 