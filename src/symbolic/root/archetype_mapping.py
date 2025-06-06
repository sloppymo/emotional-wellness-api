"""
ROOT Archetype Mapping System

This module provides advanced archetype mapping functionality including:
- Sophisticated emotional state to archetype analysis
- Temporal pattern recognition and stability metrics
- Cultural context integration
- Multi-dimensional archetype scoring
- Predictive archetype modeling
"""

import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from functools import lru_cache
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, validator
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

from .archetypes import ArchetypeCategory, EmotionalArchetype, EMOTIONAL_STATE_ARCHETYPES
from structured_logging import get_logger

logger = get_logger(__name__)

class MappingConfidence(str, Enum):
    """Confidence levels for archetype mappings."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

class TemporalPattern(str, Enum):
    """Temporal patterns in archetype expression."""
    STABLE = "stable"
    CYCLICAL = "cyclical"
    ASCENDING = "ascending"
    DESCENDING = "descending"
    CHAOTIC = "chaotic"
    TRANSITIONAL = "transitional"

class CulturalContext(str, Enum):
    """Cultural contexts for archetype interpretation."""
    WESTERN = "western"
    EASTERN = "eastern"
    INDIGENOUS = "indigenous"
    MEDITERRANEAN = "mediterranean"
    UNIVERSAL = "universal"

@dataclass
class ArchetypeScore:
    """Individual archetype score with metadata."""
    category: ArchetypeCategory
    raw_score: float
    weighted_score: float
    confidence: float
    contributing_states: List[str]
    temporal_stability: float
    cultural_modifiers: Dict[str, float]

class EmotionalStateVector(BaseModel):
    """Multi-dimensional representation of emotional states."""
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    valence: float = Field(..., ge=-1.0, le=1.0, description="Emotional valence")
    arousal: float = Field(..., ge=0.0, le=1.0, description="Emotional arousal")
    dominance: float = Field(default=0.5, ge=0.0, le=1.0, description="Sense of control/dominance")
    intensity: float = Field(default=1.0, ge=0.1, le=2.0, description="Emotional intensity")
    complexity: float = Field(default=0.5, ge=0.0, le=1.0, description="Emotional complexity")
    timestamp: datetime = Field(default_factory=datetime.now)
    context_tags: List[str] = Field(default_factory=list)

class ArchetypeMapping(BaseModel):
    """Advanced archetype mapping with comprehensive metadata."""
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    mapping_id: str = Field(..., description="Unique mapping identifier")
    user_id: Optional[str] = Field(None, description="User identifier (hashed)")
    session_id: Optional[str] = Field(None, description="Session identifier")
    primary_archetype: ArchetypeCategory = Field(..., description="Primary archetype")
    archetype_scores: Dict[str, float] = Field(..., description="All archetype scores")
    confidence: MappingConfidence = Field(..., description="Mapping confidence level")
    temporal_pattern: TemporalPattern = Field(..., description="Temporal pattern")
    cultural_context: CulturalContext = Field(default=CulturalContext.UNIVERSAL)
    contributing_states: List[str] = Field(..., description="Contributing emotional states")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    
    @validator('archetype_scores')
    def validate_scores(cls, v):
        """Validate archetype scores."""
        for category, score in v.items():
            if not (0.0 <= score <= 10.0):
                raise ValueError(f"Score for {category} must be between 0.0 and 10.0")
        return v

class ArchetypeMapper:
    """
    Advanced archetype mapping system with cultural awareness and temporal analysis.
    
    This class provides sophisticated archetype analysis including:
    - Multi-dimensional emotional state analysis
    - Cultural context integration
    - Temporal pattern recognition
    - Predictive modeling
    - Stability metrics
    """
    
    def __init__(
        self, 
        cache_size: int = 512,
        cultural_context: CulturalContext = CulturalContext.UNIVERSAL,
        temporal_window_hours: int = 168  # 1 week default
    ):
        self.cache_size = cache_size
        self.cultural_context = cultural_context
        self.temporal_window = timedelta(hours=temporal_window_hours)
        self._logger = get_logger(f"{__name__}.ArchetypeMapper")
        
        # Caching structures
        self._mapping_cache: Dict[str, ArchetypeMapping] = {}
        self._pattern_cache: Dict[str, TemporalPattern] = {}
        self._cultural_modifiers = self._load_cultural_modifiers()
        
        # Temporal analysis structures
        self._user_timelines: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._stability_metrics: Dict[str, Dict[str, float]] = defaultdict(dict)
        
        # Machine learning components
        self._scaler = StandardScaler()
        self._clusterer = None
        self._is_trained = False
        
        self._logger.info(f"ArchetypeMapper initialized with {cultural_context} context")
    
    def _load_cultural_modifiers(self) -> Dict[CulturalContext, Dict[ArchetypeCategory, float]]:
        """Load cultural modifiers for archetype interpretation."""
        return {
            CulturalContext.WESTERN: {
                ArchetypeCategory.HERO: 1.2,
                ArchetypeCategory.EXPLORER: 1.1,
                ArchetypeCategory.CREATOR: 1.1,
                ArchetypeCategory.RULER: 1.0,
                ArchetypeCategory.EVERYMAN: 0.9,
                ArchetypeCategory.SAGE: 1.0,
                ArchetypeCategory.INNOCENT: 0.8,
                ArchetypeCategory.MAGICIAN: 0.9,
                ArchetypeCategory.LOVER: 1.0,
                ArchetypeCategory.JESTER: 1.0,
                ArchetypeCategory.CAREGIVER: 1.0,
                ArchetypeCategory.OUTLAW: 0.9
            },
            CulturalContext.EASTERN: {
                ArchetypeCategory.SAGE: 1.3,
                ArchetypeCategory.CAREGIVER: 1.2,
                ArchetypeCategory.EVERYMAN: 1.1,
                ArchetypeCategory.INNOCENT: 1.1,
                ArchetypeCategory.HERO: 0.9,
                ArchetypeCategory.EXPLORER: 0.9,
                ArchetypeCategory.OUTLAW: 0.7,
                ArchetypeCategory.RULER: 1.0,
                ArchetypeCategory.CREATOR: 1.0,
                ArchetypeCategory.MAGICIAN: 1.1,
                ArchetypeCategory.LOVER: 1.0,
                ArchetypeCategory.JESTER: 0.8
            },
            CulturalContext.INDIGENOUS: {
                ArchetypeCategory.SAGE: 1.4,
                ArchetypeCategory.CAREGIVER: 1.3,
                ArchetypeCategory.MAGICIAN: 1.2,
                ArchetypeCategory.EVERYMAN: 1.2,
                ArchetypeCategory.EXPLORER: 1.1,
                ArchetypeCategory.HERO: 1.0,
                ArchetypeCategory.INNOCENT: 1.1,
                ArchetypeCategory.CREATOR: 1.1,
                ArchetypeCategory.LOVER: 1.0,
                ArchetypeCategory.JESTER: 1.0,
                ArchetypeCategory.RULER: 0.8,
                ArchetypeCategory.OUTLAW: 0.8
            },
            CulturalContext.UNIVERSAL: {
                category: 1.0 for category in ArchetypeCategory
            }
        }
    
    async def map_emotional_states(
        self,
        emotional_states: List[Dict[str, Any]],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        cultural_context: Optional[CulturalContext] = None
    ) -> ArchetypeMapping:
        """
        Map emotional states to archetypes with advanced analysis.
        
        Args:
            emotional_states: List of emotional state dictionaries
            user_id: Optional user identifier (will be hashed)
            session_id: Optional session identifier
            cultural_context: Optional cultural context override
            
        Returns:
            ArchetypeMapping with comprehensive analysis
        """
        start_time = datetime.now()
        
        try:
            # Hash user_id for privacy
            hashed_user_id = self._hash_user_id(user_id) if user_id else None
            
            # Use provided cultural context or default
            context = cultural_context or self.cultural_context
            
            # Convert to emotional state vectors
            state_vectors = await self._convert_to_vectors(emotional_states)
            
            # Calculate base archetype scores
            base_scores = await self._calculate_base_scores(state_vectors)
            
            # Apply cultural modifiers
            cultural_scores = self._apply_cultural_modifiers(base_scores, context)
            
            # Apply temporal weighting if user history exists
            temporal_scores = await self._apply_temporal_weighting(
                cultural_scores, hashed_user_id, state_vectors
            )
            
            # Determine primary archetype and confidence
            primary_archetype = max(temporal_scores, key=temporal_scores.get)
            confidence = self._calculate_confidence(temporal_scores, state_vectors)
            
            # Analyze temporal patterns
            temporal_pattern = await self._analyze_temporal_pattern(
                hashed_user_id, state_vectors
            )
            
            # Extract contributing states
            contributing_states = self._extract_contributing_states(emotional_states)
            
            # Create mapping
            mapping = ArchetypeMapping(
                mapping_id=self._generate_mapping_id(emotional_states, hashed_user_id),
                user_id=hashed_user_id,
                session_id=session_id,
                primary_archetype=ArchetypeCategory(primary_archetype),
                archetype_scores={k.value: v for k, v in temporal_scores.items()},
                confidence=confidence,
                temporal_pattern=temporal_pattern,
                cultural_context=context,
                contributing_states=contributing_states,
                metadata={
                    "processing_time": (datetime.now() - start_time).total_seconds(),
                    "state_count": len(emotional_states),
                    "cultural_modifiers_applied": True,
                    "temporal_weighting_applied": hashed_user_id is not None
                }
            )
            
            # Store in user timeline for future analysis
            if hashed_user_id:
                await self._store_in_timeline(hashed_user_id, mapping, state_vectors)
            
            # Cache the mapping
            self._cache_mapping(mapping)
            
            self._logger.info(
                f"Archetype mapping completed",
                extra={
                    "user_id": hashed_user_id,
                    "session_id": session_id,
                    "primary_archetype": primary_archetype.value,
                    "confidence": confidence.value,
                    "cultural_context": context.value,
                    "processing_time": mapping.metadata["processing_time"]
                }
            )
            
            return mapping
            
        except Exception as e:
            self._logger.error(
                f"Error in archetype mapping: {str(e)}",
                extra={
                    "user_id": hashed_user_id,
                    "session_id": session_id,
                    "error_type": type(e).__name__
                }
            )
            raise
    
    async def _convert_to_vectors(
        self, 
        emotional_states: List[Dict[str, Any]]
    ) -> List[EmotionalStateVector]:
        """Convert emotional states to multi-dimensional vectors."""
        vectors = []
        
        for state in emotional_states:
            # Extract or estimate dimensions
            valence = state.get("valence", 0.0)
            arousal = state.get("arousal", 0.5)
            dominance = state.get("dominance", 0.5)
            intensity = state.get("intensity", 1.0)
            
            # Estimate complexity based on state description
            complexity = self._estimate_complexity(state.get("state", ""))
            
            # Extract timestamp
            timestamp = datetime.now()
            if "timestamp" in state:
                try:
                    timestamp = datetime.fromisoformat(
                        state["timestamp"].replace('Z', '+00:00')
                    )
                except (ValueError, TypeError):
                    pass
            
            # Extract context tags
            context_tags = state.get("context_tags", [])
            if "context" in state and isinstance(state["context"], dict):
                context_tags.extend(state["context"].keys())
            
            vector = EmotionalStateVector(
                valence=valence,
                arousal=arousal,
                dominance=dominance,
                intensity=intensity,
                complexity=complexity,
                timestamp=timestamp,
                context_tags=context_tags
            )
            
            vectors.append(vector)
        
        return vectors
    
    def _estimate_complexity(self, state_description: str) -> float:
        """Estimate emotional complexity from state description."""
        if not state_description:
            return 0.5
        
        # Simple heuristics for complexity estimation
        complexity_indicators = [
            "conflicted", "ambivalent", "mixed", "complex", "complicated",
            "nuanced", "layered", "multifaceted", "paradoxical", "contradictory"
        ]
        
        state_lower = state_description.lower()
        complexity_score = 0.0
        
        for indicator in complexity_indicators:
            if indicator in state_lower:
                complexity_score += 0.2
        
        # Length-based complexity (longer descriptions may indicate complexity)
        length_factor = min(0.3, len(state_description.split()) * 0.05)
        complexity_score += length_factor
        
        return min(1.0, max(0.0, complexity_score))
    
    async def _calculate_base_scores(
        self, 
        state_vectors: List[EmotionalStateVector]
    ) -> Dict[ArchetypeCategory, float]:
        """Calculate base archetype scores from emotional state vectors."""
        archetype_scores = {category: 0.0 for category in ArchetypeCategory}
        
        total_weight = 0.0
        
        for vector in state_vectors:
            # Apply time decay weighting (recent states weighted more heavily)
            time_diff = datetime.now() - vector.timestamp
            time_weight = np.exp(-time_diff.total_seconds() / (24 * 3600))  # Daily decay
            
            # Apply intensity weighting
            intensity_weight = vector.intensity
            
            # Combined weight
            weight = time_weight * intensity_weight
            total_weight += weight
            
            # Multi-dimensional archetype mapping
            for category in ArchetypeCategory:
                score = self._calculate_dimensional_score(vector, category)
                archetype_scores[category] += score * weight
        
        # Normalize scores
        if total_weight > 0:
            for category in archetype_scores:
                archetype_scores[category] = (archetype_scores[category] / total_weight) * 10.0
        
        return archetype_scores
    
    def _calculate_dimensional_score(
        self, 
        vector: EmotionalStateVector, 
        category: ArchetypeCategory
    ) -> float:
        """Calculate archetype score based on multi-dimensional analysis."""
        # Define dimensional profiles for each archetype
        dimensional_profiles = {
            ArchetypeCategory.HERO: {
                "valence": (0.2, 0.8),  # Moderate to positive
                "arousal": (0.6, 1.0),  # High arousal
                "dominance": (0.6, 1.0),  # High dominance
                "complexity": (0.3, 0.8)  # Moderate complexity
            },
            ArchetypeCategory.SAGE: {
                "valence": (-0.2, 0.6),  # Neutral to moderately positive
                "arousal": (0.2, 0.6),  # Low to moderate arousal
                "dominance": (0.4, 0.8),  # Moderate to high dominance
                "complexity": (0.6, 1.0)  # High complexity
            },
            ArchetypeCategory.INNOCENT: {
                "valence": (0.4, 1.0),  # Positive
                "arousal": (0.2, 0.6),  # Low to moderate arousal
                "dominance": (0.2, 0.6),  # Low to moderate dominance
                "complexity": (0.0, 0.4)  # Low complexity
            },
            ArchetypeCategory.EXPLORER: {
                "valence": (0.0, 0.8),  # Neutral to positive
                "arousal": (0.5, 1.0),  # Moderate to high arousal
                "dominance": (0.5, 0.9),  # Moderate to high dominance
                "complexity": (0.4, 0.8)  # Moderate complexity
            },
            ArchetypeCategory.OUTLAW: {
                "valence": (-0.8, 0.2),  # Negative to neutral
                "arousal": (0.6, 1.0),  # High arousal
                "dominance": (0.3, 0.8),  # Variable dominance
                "complexity": (0.5, 0.9)  # Moderate to high complexity
            },
            # Add more profiles as needed
        }
        
        # Default profile for categories not explicitly defined
        default_profile = {
            "valence": (-1.0, 1.0),
            "arousal": (0.0, 1.0),
            "dominance": (0.0, 1.0),
            "complexity": (0.0, 1.0)
        }
        
        profile = dimensional_profiles.get(category, default_profile)
        
        # Calculate fit score for each dimension
        scores = []
        
        for dimension, (min_val, max_val) in profile.items():
            value = getattr(vector, dimension)
            
            # Calculate how well the value fits within the expected range
            if min_val <= value <= max_val:
                # Value is within range - calculate proximity to optimal
                range_center = (min_val + max_val) / 2
                max_distance = (max_val - min_val) / 2
                distance = abs(value - range_center)
                fit_score = 1.0 - (distance / max_distance)
            else:
                # Value is outside range - calculate penalty
                if value < min_val:
                    distance = min_val - value
                else:
                    distance = value - max_val
                
                # Apply exponential penalty for values outside range
                fit_score = np.exp(-distance * 2)
            
            scores.append(fit_score)
        
        # Return weighted average of dimensional scores
        return np.mean(scores)
    
    def _apply_cultural_modifiers(
        self, 
        base_scores: Dict[ArchetypeCategory, float], 
        cultural_context: CulturalContext
    ) -> Dict[ArchetypeCategory, float]:
        """Apply cultural modifiers to base archetype scores."""
        modifiers = self._cultural_modifiers.get(cultural_context, {})
        modified_scores = {}
        
        for category, base_score in base_scores.items():
            modifier = modifiers.get(category, 1.0)
            modified_scores[category] = min(10.0, base_score * modifier)
        
        return modified_scores
    
    async def _apply_temporal_weighting(
        self,
        cultural_scores: Dict[ArchetypeCategory, float],
        user_id: Optional[str],
        state_vectors: List[EmotionalStateVector]
    ) -> Dict[ArchetypeCategory, float]:
        """Apply temporal weighting based on user history."""
        if not user_id or user_id not in self._user_timelines:
            return cultural_scores
        
        # Get recent user timeline
        timeline = self._user_timelines[user_id]
        if not timeline:
            return cultural_scores
        
        # Calculate stability metrics
        stability_scores = await self._calculate_stability_metrics(user_id, timeline)
        
        # Apply temporal adjustments
        temporal_scores = {}
        for category, score in cultural_scores.items():
            stability = stability_scores.get(category.value, 0.5)
            
            # Stable archetypes get slight boost, unstable ones get slight penalty
            stability_modifier = 0.8 + (stability * 0.4)  # Range: 0.8 to 1.2
            temporal_scores[category] = min(10.0, score * stability_modifier)
        
        return temporal_scores
    
    async def _calculate_stability_metrics(
        self, 
        user_id: str, 
        timeline: deque
    ) -> Dict[str, float]:
        """Calculate archetype stability metrics for a user."""
        if len(timeline) < 3:
            return {}
        
        # Extract archetype scores from recent timeline
        recent_mappings = list(timeline)[-10:]  # Last 10 mappings
        archetype_history = defaultdict(list)
        
        for mapping_data in recent_mappings:
            if isinstance(mapping_data, dict) and "archetype_scores" in mapping_data:
                for category, score in mapping_data["archetype_scores"].items():
                    archetype_history[category].append(score)
        
        # Calculate stability for each archetype
        stability_metrics = {}
        for category, scores in archetype_history.items():
            if len(scores) >= 3:
                # Calculate coefficient of variation (lower = more stable)
                mean_score = np.mean(scores)
                std_score = np.std(scores)
                
                if mean_score > 0:
                    cv = std_score / mean_score
                    # Convert to stability score (0-1, higher = more stable)
                    stability = max(0.0, 1.0 - (cv / 2.0))
                    stability_metrics[category] = stability
        
        return stability_metrics
    
    def _calculate_confidence(
        self, 
        archetype_scores: Dict[ArchetypeCategory, float],
        state_vectors: List[EmotionalStateVector]
    ) -> MappingConfidence:
        """Calculate confidence in the archetype mapping."""
        # Factor 1: Score differentiation (higher difference = higher confidence)
        sorted_scores = sorted(archetype_scores.values(), reverse=True)
        if len(sorted_scores) >= 2:
            score_gap = sorted_scores[0] - sorted_scores[1]
            differentiation_factor = min(1.0, score_gap / 3.0)  # Normalize to 0-1
        else:
            differentiation_factor = 0.5
        
        # Factor 2: Data quantity (more data = higher confidence)
        data_factor = min(1.0, len(state_vectors) / 10.0)  # Normalize to 0-1
        
        # Factor 3: Data quality (intensity and complexity)
        quality_scores = []
        for vector in state_vectors:
            quality = (vector.intensity + vector.complexity) / 2.0
            quality_scores.append(quality)
        
        quality_factor = np.mean(quality_scores) if quality_scores else 0.5
        
        # Combine factors
        overall_confidence = (differentiation_factor + data_factor + quality_factor) / 3.0
        
        # Map to confidence levels
        if overall_confidence >= 0.8:
            return MappingConfidence.VERY_HIGH
        elif overall_confidence >= 0.6:
            return MappingConfidence.HIGH
        elif overall_confidence >= 0.4:
            return MappingConfidence.MEDIUM
        else:
            return MappingConfidence.LOW
    
    async def _analyze_temporal_pattern(
        self, 
        user_id: Optional[str],
        state_vectors: List[EmotionalStateVector]
    ) -> TemporalPattern:
        """Analyze temporal patterns in emotional states."""
        if not user_id or len(state_vectors) < 3:
            return TemporalPattern.STABLE
        
        # Get user timeline
        timeline = self._user_timelines.get(user_id, deque())
        if len(timeline) < 5:
            return TemporalPattern.TRANSITIONAL
        
        # Analyze recent patterns
        recent_data = list(timeline)[-20:]  # Last 20 mappings
        
        # Extract primary archetype sequence
        archetype_sequence = []
        for mapping_data in recent_data:
            if isinstance(mapping_data, dict) and "primary_archetype" in mapping_data:
                archetype_sequence.append(mapping_data["primary_archetype"])
        
        if len(archetype_sequence) < 5:
            return TemporalPattern.TRANSITIONAL
        
        # Analyze pattern characteristics
        unique_archetypes = len(set(archetype_sequence))
        sequence_length = len(archetype_sequence)
        
        # Calculate pattern metrics
        stability_ratio = 1.0 - (unique_archetypes / sequence_length)
        
        # Detect cyclical patterns
        cycle_detected = self._detect_cycles(archetype_sequence)
        
        # Detect trends
        trend = self._detect_trend(archetype_sequence)
        
        # Determine pattern type
        if cycle_detected:
            return TemporalPattern.CYCLICAL
        elif stability_ratio >= 0.7:
            return TemporalPattern.STABLE
        elif trend == "ascending":
            return TemporalPattern.ASCENDING
        elif trend == "descending":
            return TemporalPattern.DESCENDING
        elif stability_ratio <= 0.3:
            return TemporalPattern.CHAOTIC
        else:
            return TemporalPattern.TRANSITIONAL
    
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
            
            # If we find multiple cycles of the same length, it's cyclical
            if cycles_found >= 2:
                return True
        
        return False
    
    def _detect_trend(self, sequence: List[str]) -> str:
        """Detect ascending or descending trends in archetype sequence."""
        if len(sequence) < 4:
            return "stable"
        
        # Map archetypes to numeric values for trend analysis
        archetype_values = {
            ArchetypeCategory.INNOCENT.value: 1,
            ArchetypeCategory.EVERYMAN.value: 2,
            ArchetypeCategory.HERO.value: 3,
            ArchetypeCategory.CAREGIVER.value: 4,
            ArchetypeCategory.LOVER.value: 5,
            ArchetypeCategory.EXPLORER.value: 6,
            ArchetypeCategory.OUTLAW.value: 7,
            ArchetypeCategory.CREATOR.value: 8,
            ArchetypeCategory.RULER.value: 9,
            ArchetypeCategory.MAGICIAN.value: 10,
            ArchetypeCategory.SAGE.value: 11,
            ArchetypeCategory.JESTER.value: 12
        }
        
        numeric_sequence = [archetype_values.get(archetype, 6) for archetype in sequence]
        
        # Calculate trend using linear regression
        x = np.array(range(len(numeric_sequence)))
        y = np.array(numeric_sequence)
        
        # Simple linear regression
        n = len(x)
        slope = (n * np.sum(x * y) - np.sum(x) * np.sum(y)) / (n * np.sum(x * x) - np.sum(x) * np.sum(x))
        
        # Determine trend based on slope
        if slope > 0.5:
            return "ascending"
        elif slope < -0.5:
            return "descending"
        else:
            return "stable"
    
    def _extract_contributing_states(self, emotional_states: List[Dict[str, Any]]) -> List[str]:
        """Extract contributing emotional states for the mapping."""
        states = []
        for state in emotional_states:
            if "state" in state:
                # Hash the state for privacy
                state_hash = hashlib.sha256(state["state"].encode()).hexdigest()[:8]
                states.append(state_hash)
        return states
    
    def _generate_mapping_id(
        self, 
        emotional_states: List[Dict[str, Any]], 
        user_id: Optional[str]
    ) -> str:
        """Generate unique mapping ID."""
        content = {
            "states": [state.get("state", "") for state in emotional_states],
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        return hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()[:16]
    
    def _hash_user_id(self, user_id: str) -> str:
        """Hash user ID for privacy compliance."""
        return hashlib.sha256(user_id.encode()).hexdigest()[:16]
    
    async def _store_in_timeline(
        self, 
        user_id: str, 
        mapping: ArchetypeMapping,
        state_vectors: List[EmotionalStateVector]
    ) -> None:
        """Store mapping in user timeline for future analysis."""
        timeline_entry = {
            "mapping_id": mapping.mapping_id,
            "primary_archetype": mapping.primary_archetype.value,
            "archetype_scores": mapping.archetype_scores,
            "confidence": mapping.confidence.value,
            "temporal_pattern": mapping.temporal_pattern.value,
            "timestamp": mapping.created_at.isoformat(),
            "state_count": len(state_vectors)
        }
        
        self._user_timelines[user_id].append(timeline_entry)
        
        # Update stability metrics
        self._stability_metrics[user_id] = await self._calculate_stability_metrics(
            user_id, self._user_timelines[user_id]
        )
    
    def _cache_mapping(self, mapping: ArchetypeMapping) -> None:
        """Cache the archetype mapping."""
        cache_key = f"{mapping.user_id}:{mapping.session_id}:{mapping.mapping_id}"
        self._mapping_cache[cache_key] = mapping
        
        # Maintain cache size
        if len(self._mapping_cache) > self.cache_size:
            # Remove oldest entries
            oldest_key = min(
                self._mapping_cache.keys(),
                key=lambda k: self._mapping_cache[k].created_at
            )
            del self._mapping_cache[oldest_key]
    
    async def get_user_archetype_history(
        self, 
        user_id: str, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get archetype history for a user."""
        hashed_user_id = self._hash_user_id(user_id)
        timeline = self._user_timelines.get(hashed_user_id, deque())
        
        # Return recent entries
        recent_entries = list(timeline)[-limit:] if timeline else []
        
        return recent_entries
    
    async def get_stability_metrics(self, user_id: str) -> Dict[str, float]:
        """Get archetype stability metrics for a user."""
        hashed_user_id = self._hash_user_id(user_id)
        return self._stability_metrics.get(hashed_user_id, {})
    
    def get_cultural_modifiers(self, cultural_context: CulturalContext) -> Dict[str, float]:
        """Get cultural modifiers for a specific context."""
        modifiers = self._cultural_modifiers.get(cultural_context, {})
        return {category.value: modifier for category, modifier in modifiers.items()}


# Convenience functions for direct usage
async def create_archetype_mapper(
    cultural_context: CulturalContext = CulturalContext.UNIVERSAL
) -> ArchetypeMapper:
    """Create and initialize an archetype mapper."""
    mapper = ArchetypeMapper(cultural_context=cultural_context)
    return mapper

@lru_cache(maxsize=128)
def get_cached_cultural_modifiers(cultural_context: str) -> Dict[str, float]:
    """Get cached cultural modifiers for performance."""
    context = CulturalContext(cultural_context)
    mapper = ArchetypeMapper()
    return mapper.get_cultural_modifiers(context) 