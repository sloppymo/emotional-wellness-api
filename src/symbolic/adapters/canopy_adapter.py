"""
CANOPY Adapter for SYLVA Integration

This adapter bridges the existing CANOPY metaphor extraction system
with the SYLVA symbolic processing framework.
"""

from typing import Dict, List, Optional, Any
import asyncio
from datetime import datetime
import os
import json

from pydantic import BaseModel, Field, ConfigDict
from structured_logging import get_logger

from .base import SylvaAdapter, SylvaRequest, AdapterError
from ..canopy import CanopyProcessor, get_canopy_processor
from models.emotional_state import SymbolicMapping, EmotionalMetaphor

logger = get_logger(__name__)

class CanopyInput(BaseModel):
    """Input model for CANOPY operations."""
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        str_strip_whitespace=True
    )
    
    text: str = Field(min_length=1, max_length=10000)
    biomarkers: Optional[Dict[str, float]] = None
    context: Optional[Dict[str, Any]] = None
    previous_symbols: Optional[List[str]] = None
    cultural_context: Optional[str] = Field(None, description="Cultural context for symbol interpretation")
    visualization_format: Optional[str] = Field(None, description="Format for metaphor visualization")

class CanopyOutput(BaseModel):
    """Output model for CANOPY operations."""
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    primary_symbol: str
    archetype: str
    alternative_symbols: List[str]
    valence: float = Field(ge=-1.0, le=1.0)
    arousal: float = Field(ge=0.0, le=1.0)
    metaphors: List[Dict[str, Any]]
    confidence: float = Field(ge=0.0, le=1.0)
    drift_score: Optional[float] = None
    symbolic_evolution: Optional[Dict[str, Any]] = None
    cultural_interpretations: Optional[Dict[str, Any]] = None
    visualization_data: Optional[Dict[str, Any]] = None
    pattern_analysis: Optional[Dict[str, Any]] = None

class CanopyAdapter(SylvaAdapter[CanopyInput, CanopyOutput]):
    """
    Adapter for CANOPY metaphor extraction system.
    
    This adapter provides a standardized interface to the CANOPY system,
    enabling metaphor extraction and symbolic mapping with caching and
    enhanced error handling.
    """
    
    def __init__(self, canopy_processor: Optional[CanopyProcessor] = None):
        """
        Initialize the CANOPY adapter.
        
        Args:
            canopy_processor: Optional custom CANOPY processor instance
        """
        super().__init__("canopy", cache_size=256)
        self._canopy_processor = canopy_processor
        self._symbolic_history: Dict[str, List[SymbolicMapping]] = {}
        self._max_history_size = 50
        self._pattern_cache: Dict[str, Dict[str, Any]] = {}
        self._cultural_cache: Dict[str, Dict[str, Any]] = {}
        self._cultural_symbols: Dict[str, Dict[str, Any]] = {}
        
        # Load cultural symbols database
        self._load_cultural_symbols()
    
    def _load_cultural_symbols(self) -> None:
        """Load cultural symbols from the database file."""
        try:
            symbols_path = os.path.join(
                os.path.dirname(__file__),
                "..",
                "data",
                "cultural_symbols.json"
            )
            with open(symbols_path, 'r') as f:
                self._cultural_symbols = json.load(f)
            self._logger.info("Loaded cultural symbols database")
        except Exception as e:
            self._logger.error(f"Failed to load cultural symbols: {str(e)}")
            self._cultural_symbols = {}
    
    async def _initialize_adapter(self) -> None:
        """Initialize the CANOPY processor."""
        if self._canopy_processor is None:
            self._canopy_processor = get_canopy_processor()
        
        # Test the processor
        try:
            test_mapping = await self._canopy_processor.extract(
                "This is a test message for initialization.",
                biomarkers=None,
                context=None
            )
            self._logger.info("CANOPY processor initialized and tested successfully")
        except Exception as e:
            raise AdapterError(
                f"Failed to initialize CANOPY processor: {str(e)}",
                self.adapter_type,
                {"error_type": type(e).__name__}
            )
    
    async def _process_request(self, request: SylvaRequest) -> Dict[str, Any]:
        """
        Process a metaphor extraction request through CANOPY.
        
        Args:
            request: The standardized SYLVA request
            
        Returns:
            Dictionary containing the metaphor extraction results
        """
        # Validate input data
        try:
            canopy_input = CanopyInput(**request.input_data)
        except Exception as e:
            raise AdapterError(
                f"Invalid input data for CANOPY: {str(e)}",
                self.adapter_type,
                {"input_data": request.input_data}
            )
        
        # Prepare context with previous symbols if available
        enhanced_context = canopy_input.context or {}
        if canopy_input.previous_symbols:
            enhanced_context["previous_symbols"] = canopy_input.previous_symbols
        elif request.user_id:
            # Get historical symbols for this user
            user_history = self._get_user_history(request.user_id)
            if user_history:
                enhanced_context["previous_symbols"] = [
                    mapping.primary_symbol for mapping in user_history[-5:]
                ]
        
        # Extract metaphors using CANOPY
        try:
            mapping = await self._canopy_processor.extract(
                text=canopy_input.text,
                biomarkers=canopy_input.biomarkers,
                context=enhanced_context
            )
        except Exception as e:
            raise AdapterError(
                f"CANOPY extraction failed: {str(e)}",
                self.adapter_type,
                {"text_length": len(canopy_input.text)}
            )
        
        # Calculate symbolic drift if user history exists
        drift_score = None
        symbolic_evolution = None
        
        if request.user_id:
            user_history = self._get_user_history(request.user_id)
            if user_history:
                drift_score = self._canopy_processor.calculate_drift(mapping, user_history)
                symbolic_evolution = self._analyze_symbolic_evolution(mapping, user_history)
            
            # Store this mapping in user history
            self._store_user_mapping(request.user_id, mapping)
        
        # Perform advanced pattern analysis
        pattern_analysis = await self._analyze_patterns(mapping, request.user_id)
        
        # Apply cultural adaptations if context provided
        cultural_interpretations = None
        if canopy_input.cultural_context:
            cultural_interpretations = await self._apply_cultural_adaptations(
                mapping,
                canopy_input.cultural_context
            )
        
        # Generate visualization data if requested
        visualization_data = None
        if canopy_input.visualization_format:
            visualization_data = await self._generate_visualization(
                mapping,
                canopy_input.visualization_format
            )
        
        # Convert metaphors to dictionaries for JSON serialization
        metaphor_dicts = []
        for metaphor in mapping.metaphors:
            metaphor_dicts.append({
                "text": metaphor.text,
                "symbol": metaphor.symbol,
                "confidence": metaphor.confidence
            })
        
        # Create output
        output = CanopyOutput(
            primary_symbol=mapping.primary_symbol,
            archetype=mapping.archetype,
            alternative_symbols=mapping.alternative_symbols,
            valence=mapping.valence,
            arousal=mapping.arousal,
            metaphors=metaphor_dicts,
            confidence=mapping.confidence,
            drift_score=drift_score,
            symbolic_evolution=symbolic_evolution,
            pattern_analysis=pattern_analysis,
            cultural_interpretations=cultural_interpretations,
            visualization_data=visualization_data
        )
        
        self._logger.info(
            f"CANOPY processing completed",
            extra={
                "primary_symbol": mapping.primary_symbol,
                "archetype": mapping.archetype,
                "confidence": mapping.confidence,
                "drift_score": drift_score,
                "user_id": request.user_id,
                "session_id": request.session_id,
                "has_cultural_adaptations": cultural_interpretations is not None,
                "has_visualization": visualization_data is not None
            }
        )
        
        return output.model_dump()
    
    def _get_user_history(self, user_id: str) -> List[SymbolicMapping]:
        """Get symbolic mapping history for a user."""
        return self._symbolic_history.get(user_id, [])
    
    def _store_user_mapping(self, user_id: str, mapping: SymbolicMapping) -> None:
        """Store a symbolic mapping in user history."""
        if user_id not in self._symbolic_history:
            self._symbolic_history[user_id] = []
        
        self._symbolic_history[user_id].append(mapping)
        
        # Limit history size
        if len(self._symbolic_history[user_id]) > self._max_history_size:
            self._symbolic_history[user_id] = self._symbolic_history[user_id][-self._max_history_size:]
    
    def _analyze_symbolic_evolution(
        self, 
        current: SymbolicMapping, 
        history: List[SymbolicMapping]
    ) -> Dict[str, Any]:
        """
        Analyze the evolution of symbolic patterns over time.
        
        Args:
            current: Current symbolic mapping
            history: Historical symbolic mappings
            
        Returns:
            Dictionary containing evolution analysis
        """
        if not history:
            return {"stage": "initial", "patterns": []}
        
        # Analyze symbol stability
        recent_symbols = [mapping.primary_symbol for mapping in history[-10:]]
        symbol_counts = {}
        for symbol in recent_symbols:
            symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
        
        most_common_symbol = max(symbol_counts, key=symbol_counts.get) if symbol_counts else None
        
        # Analyze archetype patterns
        recent_archetypes = [mapping.archetype for mapping in history[-10:]]
        archetype_counts = {}
        for archetype in recent_archetypes:
            archetype_counts[archetype] = archetype_counts.get(archetype, 0) + 1
        
        # Analyze emotional trajectory
        valence_trend = []
        arousal_trend = []
        for mapping in history[-5:]:
            valence_trend.append(mapping.valence)
            arousal_trend.append(mapping.arousal)
        
        # Determine evolutionary stage
        stage = "stable"
        if len(history) < 5:
            stage = "emerging"
        elif current.primary_symbol != most_common_symbol:
            stage = "transitional"
        elif len(set(recent_symbols)) > len(recent_symbols) * 0.7:
            stage = "exploratory"
        
        return {
            "stage": stage,
            "dominant_symbol": most_common_symbol,
            "symbol_stability": symbol_counts.get(most_common_symbol, 0) / len(recent_symbols) if recent_symbols else 0,
            "archetype_patterns": archetype_counts,
            "valence_trend": valence_trend,
            "arousal_trend": arousal_trend,
            "recent_diversity": len(set(recent_symbols)) / len(recent_symbols) if recent_symbols else 0
        }
    
    async def extract_metaphors(
        self, 
        text: str, 
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        biomarkers: Optional[Dict[str, float]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> CanopyOutput:
        """
        Convenience method for direct metaphor extraction.
        
        Args:
            text: Input text for metaphor extraction
            user_id: Optional user identifier
            session_id: Optional session identifier
            biomarkers: Optional biomarker data
            context: Optional additional context
            
        Returns:
            CanopyOutput with extraction results
        """
        request = SylvaRequest(
            input_data={
                "text": text,
                "biomarkers": biomarkers,
                "context": context
            },
            user_id=user_id,
            session_id=session_id
        )
        
        response = await self.process(request)
        
        if not response.success:
            raise AdapterError(
                f"Metaphor extraction failed: {response.error}",
                self.adapter_type
            )
        
        return CanopyOutput(**response.result)
    
    async def _health_check(self) -> bool:
        """Perform CANOPY-specific health check."""
        try:
            # Test extraction with a simple phrase
            test_result = await self.extract_metaphors("I feel like flowing water today.")
            return test_result.confidence > 0.0
        except Exception:
            return False
    
    async def _cleanup_adapter(self) -> None:
        """Clean up CANOPY adapter resources."""
        # Clear symbolic history to free memory
        self._symbolic_history.clear()
        self._logger.info("CANOPY adapter cleanup completed")
    
    def get_user_symbolic_summary(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a summary of a user's symbolic patterns.
        
        Args:
            user_id: User identifier
            
        Returns:
            Summary of symbolic patterns or None if no history
        """
        history = self._get_user_history(user_id)
        if not history:
            return None
        
        # Analyze patterns
        symbols = [mapping.primary_symbol for mapping in history]
        archetypes = [mapping.archetype for mapping in history]
        
        symbol_counts = {}
        archetype_counts = {}
        
        for symbol in symbols:
            symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
        
        for archetype in archetypes:
            archetype_counts[archetype] = archetype_counts.get(archetype, 0) + 1
        
        # Calculate averages
        avg_valence = sum(mapping.valence for mapping in history) / len(history)
        avg_arousal = sum(mapping.arousal for mapping in history) / len(history)
        avg_confidence = sum(mapping.confidence for mapping in history) / len(history)
        
        return {
            "total_mappings": len(history),
            "dominant_symbols": sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            "dominant_archetypes": sorted(archetype_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            "average_valence": avg_valence,
            "average_arousal": avg_arousal,
            "average_confidence": avg_confidence,
            "symbolic_diversity": len(set(symbols)) / len(symbols),
            "first_mapping": history[0].timestamp,
            "last_mapping": history[-1].timestamp
        }
    
    async def _analyze_patterns(
        self,
        mapping: SymbolicMapping,
        user_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Perform advanced pattern analysis on symbolic mappings.
        
        This method identifies recurring patterns, symbolic clusters,
        and archetypal progressions in the user's symbolic journey.
        """
        patterns = {
            "recurring_symbols": [],
            "archetypal_progression": [],
            "symbol_clusters": [],
            "emotional_patterns": []
        }
        
        if not user_id:
            return patterns
            
        history = self._get_user_history(user_id)
        if not history:
            return patterns
            
        # Analyze recurring symbols
        symbol_counts = {}
        for hist_mapping in history:
            symbol = hist_mapping.primary_symbol
            symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
        
        patterns["recurring_symbols"] = [
            {"symbol": s, "count": c}
            for s, c in sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # Analyze archetypal progression
        archetype_sequence = [m.archetype for m in history[-10:]]  # Last 10 archetypes
        patterns["archetypal_progression"] = {
            "sequence": archetype_sequence,
            "current": mapping.archetype,
            "suggested_next": self._predict_next_archetype(archetype_sequence)
        }
        
        # Identify symbol clusters
        patterns["symbol_clusters"] = self._identify_symbol_clusters(history)
        
        # Analyze emotional patterns
        patterns["emotional_patterns"] = self._analyze_emotional_patterns(history)
        
        return patterns
    
    async def _apply_cultural_adaptations(
        self,
        mapping: SymbolicMapping,
        cultural_context: str
    ) -> Dict[str, Any]:
        """
        Apply cultural adaptations to symbolic interpretations.
        
        This method adjusts symbolic meanings based on cultural context
        and provides culture-specific interpretations.
        """
        # Check cache first
        cache_key = f"{mapping.primary_symbol}:{cultural_context}"
        if cache_key in self._cultural_cache:
            return self._cultural_cache[cache_key]
            
        interpretations = {
            "primary_symbol": {
                "original": mapping.primary_symbol,
                "cultural_meaning": "",
                "cultural_associations": [],
                "taboos": [],
                "alternatives": []
            },
            "archetype": {
                "original": mapping.archetype,
                "cultural_equivalent": "",
                "cultural_variations": []
            }
        }
        
        # Get cultural symbols for the context
        cultural_symbols = await self._get_cultural_symbols(cultural_context)
        
        if mapping.primary_symbol in cultural_symbols:
            symbol_data = cultural_symbols[mapping.primary_symbol]
            interpretations["primary_symbol"].update({
                "cultural_meaning": symbol_data["cultural_meaning"],
                "cultural_associations": symbol_data["cultural_associations"],
                "taboos": symbol_data.get("taboos", []),
                "alternatives": symbol_data["alternatives"]
            })
            
            # Add archetypal resonance if available
            if "archetypal_resonance" in symbol_data:
                interpretations["archetype"]["cultural_variations"] = symbol_data["archetypal_resonance"]
                # Find the closest matching archetype
                if mapping.archetype in symbol_data["archetypal_resonance"]:
                    interpretations["archetype"]["cultural_equivalent"] = mapping.archetype
                else:
                    interpretations["archetype"]["cultural_equivalent"] = symbol_data["archetypal_resonance"][0]
        
        # Cache the result
        self._cultural_cache[cache_key] = interpretations
        
        return interpretations
    
    async def _generate_visualization(
        self,
        mapping: SymbolicMapping,
        format: str
    ) -> Dict[str, Any]:
        """
        Generate visualization data for metaphors and symbols.
        
        This method creates structured data that can be used to
        visualize the symbolic and metaphorical content.
        """
        visualization = {
            "format": format,
            "elements": [],
            "relationships": [],
            "metadata": {}
        }
        
        if format == "network":
            # Create network visualization data
            central_node = {
                "id": "primary",
                "type": "symbol",
                "label": mapping.primary_symbol,
                "size": 1.0
            }
            visualization["elements"].append(central_node)
            
            # Add metaphor nodes
            for i, metaphor in enumerate(mapping.metaphors):
                node = {
                    "id": f"metaphor_{i}",
                    "type": "metaphor",
                    "label": metaphor.text,
                    "size": metaphor.confidence
                }
                visualization["elements"].append(node)
                
                # Add relationship to primary symbol
                visualization["relationships"].append({
                    "source": "primary",
                    "target": f"metaphor_{i}",
                    "type": "expresses",
                    "weight": metaphor.confidence
                })
                
        elif format == "temporal":
            # Create temporal visualization data
            visualization["elements"] = [{
                "timestamp": datetime.now().isoformat(),
                "symbol": mapping.primary_symbol,
                "archetype": mapping.archetype,
                "valence": mapping.valence,
                "arousal": mapping.arousal
            }]
            
        return visualization
    
    def _predict_next_archetype(self, sequence: List[str]) -> str:
        """Predict the next likely archetype in a sequence."""
        if not sequence:
            return "self"  # Default prediction
            
        # Simple Markov-chain-like prediction
        transitions = {}
        for i in range(len(sequence) - 1):
            current = sequence[i]
            next_arch = sequence[i + 1]
            if current not in transitions:
                transitions[current] = {}
            transitions[current][next_arch] = transitions[current].get(next_arch, 0) + 1
            
        current_archetype = sequence[-1]
        if current_archetype in transitions:
            most_likely = max(
                transitions[current_archetype].items(),
                key=lambda x: x[1]
            )[0]
            return most_likely
            
        return "self"  # Default if no pattern found
    
    def _identify_symbol_clusters(self, history: List[SymbolicMapping]) -> List[Dict[str, Any]]:
        """Identify clusters of related symbols in user history."""
        clusters = []
        
        # Simple clustering based on common attributes
        element_cluster = {
            "name": "elemental",
            "symbols": ["water", "fire", "earth", "air"],
            "count": 0
        }
        
        journey_cluster = {
            "name": "journey",
            "symbols": ["path", "bridge", "door", "road", "mountain"],
            "count": 0
        }
        
        for mapping in history:
            if mapping.primary_symbol in element_cluster["symbols"]:
                element_cluster["count"] += 1
            if mapping.primary_symbol in journey_cluster["symbols"]:
                journey_cluster["count"] += 1
                
        if element_cluster["count"] > 0:
            clusters.append(element_cluster)
        if journey_cluster["count"] > 0:
            clusters.append(journey_cluster)
            
        return clusters
    
    def _analyze_emotional_patterns(self, history: List[SymbolicMapping]) -> Dict[str, Any]:
        """Analyze patterns in emotional valence and arousal."""
        if not history:
            return {}
            
        valences = [m.valence for m in history]
        arousals = [m.arousal for m in history]
        
        return {
            "valence_trend": {
                "mean": sum(valences) / len(valences),
                "variance": sum((v - sum(valences)/len(valences))**2 for v in valences) / len(valences),
                "direction": "increasing" if valences[-1] > valences[0] else "decreasing"
            },
            "arousal_trend": {
                "mean": sum(arousals) / len(arousals),
                "variance": sum((a - sum(arousals)/len(arousals))**2 for a in arousals) / len(arousals),
                "direction": "increasing" if arousals[-1] > arousals[0] else "decreasing"
            }
        }
    
    async def _get_cultural_symbols(self, cultural_context: str) -> Dict[str, Any]:
        """Retrieve cultural symbol mappings."""
        if not cultural_context or cultural_context not in self._cultural_symbols:
            return {}
        
        return self._cultural_symbols[cultural_context] 