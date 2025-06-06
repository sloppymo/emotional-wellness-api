"""
CANOPY Adapter for SYLVA Integration

This adapter bridges the existing CANOPY metaphor extraction system
with the SYLVA symbolic processing framework.
"""

from typing import Dict, List, Optional, Any
import asyncio
from datetime import datetime

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
            symbolic_evolution=symbolic_evolution
        )
        
        self._logger.info(
            f"CANOPY processing completed",
            extra={
                "primary_symbol": mapping.primary_symbol,
                "archetype": mapping.archetype,
                "confidence": mapping.confidence,
                "drift_score": drift_score,
                "user_id": request.user_id,
                "session_id": request.session_id
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