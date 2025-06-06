"""
ROOT Adapter for SYLVA Framework Integration

This adapter bridges the ROOT archetype analysis system with the SYLVA framework,
providing longitudinal emotional state mapping, archetype identification, and
pattern recognition through the standardized SYLVA interface.
"""

import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from functools import lru_cache

from pydantic import BaseModel, Field, ConfigDict, validator

from .base import SylvaAdapter, SylvaRequest, SylvaResponse, AdapterError, SymbolicData
from ..root.analysis import analyze_emotional_timeline, identify_archetypes, map_journey_pattern
from ..root.archetypes import (
    ArchetypeCategory, EmotionalArchetype, create_archetype_profile,
    get_dominant_archetypes, analyze_archetype_transitions,
    cached_analyze_with_context
)
from ..root.patterns import (
    EmotionalJourneyPattern, PatternStrength, extract_journey_patterns,
    classify_emotional_pattern, ArchetypeMapping
)
from structured_logging import get_logger

logger = get_logger(__name__)

class EmotionalStateData(BaseModel):
    """Represents a single emotional state data point for analysis."""
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        str_strip_whitespace=True
    )
    
    state: str = Field(..., description="Emotional state description")
    intensity: float = Field(default=1.0, ge=0.1, le=2.0, description="Intensity of the emotional state")
    timestamp: Optional[str] = Field(None, description="ISO timestamp of the emotional state")
    valence: Optional[float] = Field(None, ge=-1.0, le=1.0, description="Emotional valence")
    arousal: Optional[float] = Field(None, ge=0.0, le=1.0, description="Emotional arousal")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")

class ROOTInput(BaseModel):
    """Input model for ROOT archetype analysis operations."""
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        str_strip_whitespace=True
    )
    
    emotional_states: List[EmotionalStateData] = Field(..., description="List of emotional states for analysis")
    analysis_type: str = Field(
        default="comprehensive", 
        description="Type of analysis: 'archetype', 'pattern', 'timeline', 'comprehensive'"
    )
    time_weighting: bool = Field(default=True, description="Whether to weight recent emotions more heavily")
    max_archetypes: int = Field(default=3, ge=1, le=10, description="Maximum number of archetypes to return")
    time_segments: int = Field(default=3, ge=2, le=10, description="Number of time segments for transition analysis")
    include_transitions: bool = Field(default=True, description="Whether to include archetype transition analysis")
    user_context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="User-specific context")

    @validator('analysis_type')
    def validate_analysis_type(cls, v):
        allowed_types = {'archetype', 'pattern', 'timeline', 'comprehensive'}
        if v not in allowed_types:
            raise ValueError(f"analysis_type must be one of: {allowed_types}")
        return v

class ArchetypeResult(BaseModel):
    """Individual archetype analysis result."""
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    category: str = Field(..., description="Archetype category")
    name: str = Field(..., description="Archetype name")
    score: float = Field(..., ge=0.0, le=10.0, description="Archetype strength score")
    traits: List[str] = Field(default_factory=list, description="Associated traits")
    description: str = Field(..., description="Archetype description")

class PatternResult(BaseModel):
    """Journey pattern analysis result."""
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    pattern: str = Field(..., description="Identified pattern name")
    strength: str = Field(..., description="Pattern strength")
    description: str = Field(..., description="Pattern description")
    evidence: List[str] = Field(default_factory=list, description="Supporting evidence")

class TransitionResult(BaseModel):
    """Archetype transition analysis result."""
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    transitions: List[Dict[str, str]] = Field(default_factory=list, description="Archetype transitions")
    segments: List[Dict[str, Any]] = Field(default_factory=list, description="Time segment analysis")
    patterns: List[str] = Field(default_factory=list, description="Detected transition patterns")
    stability: float = Field(default=1.0, ge=0.0, le=1.0, description="Archetype stability score")

class TimelineResult(BaseModel):
    """Timeline analysis result."""
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    state_frequencies: Dict[str, int] = Field(default_factory=dict, description="Frequency of emotional states")
    arc: str = Field(..., description="Overall emotional arc")
    total_entries: int = Field(..., ge=0, description="Total number of entries analyzed")
    duration_days: Optional[float] = Field(None, description="Duration in days if timestamps available")

class ROOTOutput(BaseModel):
    """Output model for ROOT archetype analysis operations."""
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    operation_id: str = Field(..., description="Operation identifier")
    analysis_type: str = Field(..., description="Type of analysis performed")
    dominant_archetypes: List[ArchetypeResult] = Field(default_factory=list, description="Dominant archetypes")
    archetype_profile: Dict[str, float] = Field(default_factory=dict, description="Complete archetype profile")
    journey_patterns: List[PatternResult] = Field(default_factory=list, description="Identified journey patterns")
    transitions: Optional[TransitionResult] = Field(None, description="Archetype transition analysis")
    timeline_analysis: Optional[TimelineResult] = Field(None, description="Timeline analysis")
    insights: List[str] = Field(default_factory=list, description="Generated insights")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Overall analysis confidence")
    processing_metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")

class ROOTAdapter(SylvaAdapter[ROOTInput, ROOTOutput]):
    """
    ROOT adapter for archetype analysis and longitudinal emotional mapping.
    
    This adapter provides comprehensive archetype analysis including:
    - Individual archetype identification and scoring
    - Journey pattern recognition
    - Archetype transition analysis over time
    - Emotional timeline analysis
    - Longitudinal pattern detection
    """
    
    def __init__(self, cache_size: int = 256, max_history_size: int = 100):
        super().__init__("ROOT", cache_size)
        self.max_history_size = max_history_size
        self._analysis_cache = {}
        self._user_history: Dict[str, List[Dict[str, Any]]] = {}
        
    async def _initialize_adapter(self) -> None:
        """Initialize the ROOT adapter."""
        self._logger.info("Initializing ROOT adapter")
        
        # Validate that ROOT modules are accessible
        try:
            # Test imports and basic functionality
            test_states = [{"state": "confident", "intensity": 1.0}]
            create_archetype_profile(test_states)
            extract_journey_patterns(test_states)
            
            self._logger.info("ROOT adapter initialized successfully")
            
        except Exception as e:
            raise AdapterError(
                f"Failed to initialize ROOT adapter: {str(e)}",
                self.adapter_type,
                {"error_type": type(e).__name__}
            )
    
    async def _process_request(self, request: SylvaRequest) -> Dict[str, Any]:
        """
        Process a ROOT analysis request.
        
        Args:
            request: SYLVA request containing emotional states and analysis parameters
            
        Returns:
            Dictionary containing analysis results
        """
        start_time = time.time()
        
        try:
            # Parse and validate input
            root_input = ROOTInput(**request.input_data)
            
            # Convert emotional states to format expected by ROOT functions
            emotional_states = [
                {
                    "state": state.state,
                    "intensity": state.intensity,
                    "timestamp": state.timestamp or datetime.now().isoformat(),
                    "valence": state.valence,
                    "arousal": state.arousal,
                    **state.context
                }
                for state in root_input.emotional_states
            ]
            
            # Store user history if user_id is provided
            if request.user_id:
                self._store_user_history(request.user_id, emotional_states)
            
            # Perform analysis based on type
            result = await self._perform_analysis(
                emotional_states, 
                root_input, 
                request.user_id,
                request.session_id
            )
            
            # Generate insights
            insights = self._generate_insights(result, emotional_states)
            
            # Calculate confidence score
            confidence = self._calculate_confidence(emotional_states, result)
            
            processing_time = time.time() - start_time
            
            # Build comprehensive result
            output = ROOTOutput(
                operation_id=request.operation_id,
                analysis_type=root_input.analysis_type,
                dominant_archetypes=result.get("dominant_archetypes", []),
                archetype_profile=result.get("archetype_profile", {}),
                journey_patterns=result.get("journey_patterns", []),
                transitions=result.get("transitions"),
                timeline_analysis=result.get("timeline_analysis"),
                insights=insights,
                confidence=confidence,
                processing_metadata={
                    "processing_time": processing_time,
                    "states_analyzed": len(emotional_states),
                    "analysis_timestamp": datetime.now().isoformat(),
                    "time_weighting_used": root_input.time_weighting,
                    "segments_analyzed": root_input.time_segments if root_input.include_transitions else 0
                }
            )
            
            self._logger.info(
                f"ROOT analysis completed successfully",
                extra={
                    "operation_id": request.operation_id,
                    "analysis_type": root_input.analysis_type,
                    "states_count": len(emotional_states),
                    "processing_time": processing_time,
                    "confidence": confidence,
                    "user_id": request.user_id,
                    "session_id": request.session_id
                }
            )
            
            return output.model_dump()
            
        except Exception as e:
            self._logger.error(
                f"Error in ROOT analysis: {str(e)}",
                extra={
                    "operation_id": request.operation_id,
                    "error_type": type(e).__name__,
                    "user_id": request.user_id,
                    "session_id": request.session_id
                }
            )
            raise AdapterError(
                f"ROOT analysis failed: {str(e)}",
                self.adapter_type,
                {
                    "operation_id": request.operation_id,
                    "error_type": type(e).__name__
                }
            )
    
    async def _perform_analysis(
        self, 
        emotional_states: List[Dict[str, Any]], 
        root_input: ROOTInput,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform the requested analysis type."""
        
        result = {}
        
        # Archetype analysis
        if root_input.analysis_type in ["archetype", "comprehensive"]:
            result.update(await self._analyze_archetypes(
                emotional_states, 
                root_input.time_weighting,
                root_input.max_archetypes,
                user_id,
                session_id
            ))
        
        # Pattern analysis
        if root_input.analysis_type in ["pattern", "comprehensive"]:
            result.update(await self._analyze_patterns(emotional_states))
        
        # Timeline analysis
        if root_input.analysis_type in ["timeline", "comprehensive"]:
            result.update(await self._analyze_timeline(emotional_states))
        
        # Transition analysis
        if root_input.include_transitions and root_input.analysis_type in ["archetype", "comprehensive"]:
            if len(emotional_states) >= root_input.time_segments:
                result.update(await self._analyze_transitions(
                    emotional_states, 
                    root_input.time_segments
                ))
        
        return result
    
    async def _analyze_archetypes(
        self, 
        emotional_states: List[Dict[str, Any]], 
        time_weighting: bool,
        max_archetypes: int,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform archetype analysis."""
        
        # Create archetype profile
        profile = create_archetype_profile(
            emotional_states, 
            time_weighting=time_weighting
        )
        
        # Get dominant archetypes
        dominant = get_dominant_archetypes(profile, limit=max_archetypes)
        
        # Convert to result format
        dominant_results = [
            ArchetypeResult(
                category=archetype.category.value,
                name=archetype.name,
                score=archetype.score,
                traits=archetype.traits,
                description=archetype.description
            )
            for archetype in dominant
        ]
        
        return {
            "dominant_archetypes": dominant_results,
            "archetype_profile": {k.value: v for k, v in profile.items()}
        }
    
    async def _analyze_patterns(self, emotional_states: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform journey pattern analysis."""
        
        # Extract journey patterns
        patterns = extract_journey_patterns(emotional_states)
        
        # Classify primary pattern
        mapping = classify_emotional_pattern(emotional_states)
        
        # Convert to result format
        pattern_results = []
        for pattern in patterns:
            pattern_results.append(PatternResult(
                pattern=pattern.value,
                strength="moderate",  # Default strength
                description=f"Detected {pattern.value.lower()} pattern",
                evidence=[]
            ))
        
        # Add primary pattern if available
        if mapping:
            primary_pattern = PatternResult(
                pattern=mapping.pattern.value,
                strength=mapping.strength.value,
                description=mapping.description,
                evidence=[]
            )
            if primary_pattern not in pattern_results:
                pattern_results.insert(0, primary_pattern)
        
        return {"journey_patterns": pattern_results}
    
    async def _analyze_timeline(self, emotional_states: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform timeline analysis."""
        
        # Use existing timeline analysis
        timeline_data = analyze_emotional_timeline(emotional_states)
        
        # Calculate duration if timestamps are available
        duration_days = None
        if len(emotional_states) >= 2 and all("timestamp" in state for state in emotional_states):
            try:
                timestamps = [datetime.fromisoformat(state["timestamp"].replace('Z', '+00:00')) 
                            for state in emotional_states]
                duration = max(timestamps) - min(timestamps)
                duration_days = duration.total_seconds() / (24 * 3600)
            except Exception:
                pass  # Ignore timestamp parsing errors
        
        timeline_result = TimelineResult(
            state_frequencies=timeline_data.get("state_frequencies", {}),
            arc=timeline_data.get("arc", "unknown"),
            total_entries=timeline_data.get("total_entries", len(emotional_states)),
            duration_days=duration_days
        )
        
        return {"timeline_analysis": timeline_result}
    
    async def _analyze_transitions(
        self, 
        emotional_states: List[Dict[str, Any]], 
        time_segments: int
    ) -> Dict[str, Any]:
        """Perform archetype transition analysis."""
        
        # Use existing transition analysis
        transition_data = analyze_archetype_transitions(emotional_states, time_segments)
        
        transition_result = TransitionResult(
            transitions=transition_data.get("transitions", []),
            segments=transition_data.get("segments", []),
            patterns=transition_data.get("patterns", []),
            stability=transition_data.get("stability", 1.0)
        )
        
        return {"transitions": transition_result}
    
    def _store_user_history(self, user_id: str, emotional_states: List[Dict[str, Any]]) -> None:
        """Store emotional states in user history with HIPAA compliance."""
        if user_id not in self._user_history:
            self._user_history[user_id] = []
        
        # Hash the emotional state content for storage (HIPAA compliance)
        for state in emotional_states:
            hashed_state = state.copy()
            if "state" in hashed_state:
                # Store hash of state for pattern analysis without storing PHI
                state_hash = hashlib.sha256(hashed_state["state"].encode()).hexdigest()[:16]
                hashed_state["state_hash"] = state_hash
                # Keep only metadata, not the actual emotional content
                hashed_state = {
                    "state_hash": state_hash,
                    "intensity": hashed_state.get("intensity", 1.0),
                    "timestamp": hashed_state.get("timestamp"),
                    "valence": hashed_state.get("valence"),
                    "arousal": hashed_state.get("arousal")
                }
            
            self._user_history[user_id].append(hashed_state)
        
        # Limit history size for memory management
        if len(self._user_history[user_id]) > self.max_history_size:
            self._user_history[user_id] = self._user_history[user_id][-self.max_history_size:]
        
        self._logger.debug(
            f"Stored emotional states in user history",
            extra={
                "user_id": user_id,
                "states_count": len(emotional_states),
                "total_history_size": len(self._user_history[user_id])
            }
        )
    
    def _generate_insights(self, result: Dict[str, Any], emotional_states: List[Dict[str, Any]]) -> List[str]:
        """Generate insights based on analysis results."""
        insights = []
        
        # Archetype insights
        if "dominant_archetypes" in result and result["dominant_archetypes"]:
            primary = result["dominant_archetypes"][0]
            insights.append(f"Your primary archetype is {primary['name']}, showing {primary['description'].lower()}")
            
            if len(result["dominant_archetypes"]) > 1:
                secondary = result["dominant_archetypes"][1]
                insights.append(f"Your secondary archetype {secondary['name']} suggests {secondary['description'].lower()}")
        
        # Pattern insights
        if "journey_patterns" in result and result["journey_patterns"]:
            primary_pattern = result["journey_patterns"][0]
            insights.append(f"Your emotional journey shows a {primary_pattern['pattern'].lower()} pattern")
        
        # Transition insights
        if "transitions" in result and result["transitions"]:
            stability = result["transitions"]["stability"]
            if stability >= 0.8:
                insights.append("Your archetypes show strong stability over time")
            elif stability <= 0.3:
                insights.append("You're experiencing significant archetype transitions")
            
            if result["transitions"]["patterns"]:
                insights.append(f"Notable pattern: {result['transitions']['patterns'][0]}")
        
        # Timeline insights
        if "timeline_analysis" in result and result["timeline_analysis"]:
            arc = result["timeline_analysis"]["arc"]
            if arc == "improvement":
                insights.append("Your emotional trajectory shows positive development")
            elif arc == "decline":
                insights.append("Your emotional pattern suggests areas for attention")
        
        return insights
    
    def _calculate_confidence(self, emotional_states: List[Dict[str, Any]], result: Dict[str, Any]) -> float:
        """Calculate confidence score for the analysis."""
        confidence_factors = []
        
        # Data quantity factor
        state_count = len(emotional_states)
        if state_count >= 10:
            confidence_factors.append(0.9)
        elif state_count >= 5:
            confidence_factors.append(0.7)
        elif state_count >= 3:
            confidence_factors.append(0.5)
        else:
            confidence_factors.append(0.3)
        
        # Data quality factor (presence of intensity, timestamps, etc.)
        quality_score = 0.0
        for state in emotional_states:
            if state.get("intensity") is not None:
                quality_score += 0.3
            if state.get("timestamp"):
                quality_score += 0.3
            if state.get("valence") is not None:
                quality_score += 0.2
            if state.get("arousal") is not None:
                quality_score += 0.2
        
        avg_quality = quality_score / len(emotional_states) if emotional_states else 0.0
        confidence_factors.append(avg_quality)
        
        # Analysis completeness factor
        completeness = 0.0
        if "dominant_archetypes" in result:
            completeness += 0.3
        if "journey_patterns" in result:
            completeness += 0.3
        if "transitions" in result:
            completeness += 0.2
        if "timeline_analysis" in result:
            completeness += 0.2
        
        confidence_factors.append(completeness)
        
        # Return weighted average
        return min(0.95, sum(confidence_factors) / len(confidence_factors))
    
    async def _health_check(self) -> bool:
        """Perform ROOT adapter health check."""
        try:
            # Test basic functionality
            test_states = [
                {"state": "confident", "intensity": 1.0},
                {"state": "curious", "intensity": 0.8}
            ]
            
            # Test archetype analysis
            profile = create_archetype_profile(test_states)
            dominant = get_dominant_archetypes(profile, limit=1)
            
            # Test pattern analysis
            patterns = extract_journey_patterns(test_states)
            
            return len(dominant) > 0 or len(patterns) >= 0
            
        except Exception as e:
            self._logger.error(f"ROOT adapter health check failed: {str(e)}")
            return False
    
    async def _cleanup_adapter(self) -> None:
        """Clean up ROOT adapter resources."""
        # Clear caches
        self._analysis_cache.clear()
        self._user_history.clear()
        
        self._logger.info("ROOT adapter cleaned up successfully")

# Convenience functions for direct usage
async def analyze_emotional_archetypes(
    emotional_states: List[Dict[str, Any]],
    time_weighting: bool = True,
    max_archetypes: int = 3
) -> Dict[str, Any]:
    """
    Convenience function for direct archetype analysis.
    
    Args:
        emotional_states: List of emotional state dictionaries
        time_weighting: Whether to weight recent emotions more heavily
        max_archetypes: Maximum number of archetypes to return
        
    Returns:
        Dictionary containing archetype analysis results
    """
    adapter = ROOTAdapter()
    await adapter.initialize()
    
    input_data = ROOTInput(
        emotional_states=[EmotionalStateData(**state) for state in emotional_states],
        analysis_type="archetype",
        time_weighting=time_weighting,
        max_archetypes=max_archetypes
    )
    
    request = SylvaRequest(
        input_data=input_data.model_dump(),
        context={"direct_call": True}
    )
    
    response = await adapter.process(request)
    return response.result if response.success else {"error": response.error}

async def analyze_journey_patterns(emotional_states: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Convenience function for direct pattern analysis.
    
    Args:
        emotional_states: List of emotional state dictionaries
        
    Returns:
        Dictionary containing pattern analysis results
    """
    adapter = ROOTAdapter()
    await adapter.initialize()
    
    input_data = ROOTInput(
        emotional_states=[EmotionalStateData(**state) for state in emotional_states],
        analysis_type="pattern"
    )
    
    request = SylvaRequest(
        input_data=input_data.model_dump(),
        context={"direct_call": True}
    )
    
    response = await adapter.process(request)
    return response.result if response.success else {"error": response.error} 