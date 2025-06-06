"""
Main processor module for the CANOPY system.
Handles high-level symbolic processing and integration with other subsystems.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import numpy as np

from src.utils.structured_logging import get_logger
from .metaphor_extraction import MetaphorExtractor, SymbolicMapping

logger = get_logger(__name__)

async def get_veluria_data(text: str, user_id: str) -> Dict[str, Any]:
    """Get crisis indicators from VELURIA system."""
    # TODO: Implement actual VELURIA integration
    return {
        "crisis_indicators": {
            "severity": 0.2,
            "confidence": 0.8
        }
    }

async def get_root_analysis(user_id: str) -> Dict[str, Any]:
    """Get longitudinal analysis from ROOT system."""
    # TODO: Implement actual ROOT integration
    return {
        "baseline": 0.5,
        "deviation": 0.2,
        "trend": "improving"
    }

class CanopyProcessor:
    """Main processor for the CANOPY system."""
    
    def __init__(
        self,
        api_key: str,
        symbol_library_path: Optional[str] = None,
        max_cache_size: int = 1000
    ):
        """Initialize the CANOPY processor."""
        self.extractor = MetaphorExtractor(api_key)
        self._symbolic_history: Dict[str, List[SymbolicMapping]] = {}
        self._cultural_cache: Dict[str, Dict[str, Any]] = {}
        self.MAX_CACHE_SIZE = max_cache_size
    
    async def process(
        self,
        text: str,
        user_id: str,
        biomarkers: Optional[Dict[str, float]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> SymbolicMapping:
        """Process text and extract symbolic mappings."""
        try:
            # Get VELURIA data if enabled
            if context and context.get("enable_veluria"):
                veluria_data = await get_veluria_data(text, user_id)
                if "biomarkers" not in context:
                    context["biomarkers"] = {}
                context["biomarkers"].update({
                    "crisis_severity": veluria_data["crisis_indicators"]["severity"],
                    "crisis_confidence": veluria_data["crisis_indicators"]["confidence"]
                })
            
            # Get ROOT analysis if enabled
            if context and context.get("enable_root"):
                root_data = await get_root_analysis(user_id)
                if "biomarkers" not in context:
                    context["biomarkers"] = {}
                context["biomarkers"].update({
                    "emotional_baseline": root_data["baseline"],
                    "baseline_deviation": root_data["deviation"],
                    "trend": root_data["trend"]
                })
            
            # Extract metaphors
            mapping = await self.extractor.extract(text, biomarkers, context)
            
            # Store in history
            if user_id not in self._symbolic_history:
                self._symbolic_history[user_id] = []
            self._symbolic_history[user_id].append(mapping)
            
            # Analyze patterns
            patterns = await self._analyze_patterns(mapping, user_id)
            
            # Apply cultural adaptations if context specifies
            if context and context.get("cultural_context"):
                adaptations = await self._apply_cultural_adaptations(
                    mapping,
                    context["cultural_context"]
                )
                # Update mapping with adaptations
                mapping.alternative_symbols.extend(
                    adaptations["primary_symbol"]["alternatives"]
                )
            
            logger.info(
                "Successfully processed text",
                user_id=user_id,
                text_length=len(text),
                patterns_found=len(patterns)
            )
            
            return mapping
        
        except Exception as e:
            logger.error(
                "Failed to process text",
                error=str(e),
                user_id=user_id,
                text_length=len(text)
            )
            raise
    
    async def _analyze_patterns(
        self,
        current_mapping: SymbolicMapping,
        user_id: str
    ) -> Dict[str, Any]:
        """Analyze patterns in user's symbolic history."""
        history = self._symbolic_history.get(user_id, [])
        
        patterns = {
            "recurring_symbols": self._find_recurring_symbols(history),
            "archetypal_progression": self._analyze_archetypes(history),
            "symbol_clusters": self._cluster_symbols(history),
            "emotional_patterns": self._analyze_emotions(history),
            "cyclic_patterns": self._find_cycles(history)
        }
        
        return patterns
    
    def _find_recurring_symbols(
        self,
        history: List[SymbolicMapping]
    ) -> List[Dict[str, Any]]:
        """Find recurring symbols in history."""
        symbol_count = {}
        for mapping in history:
            symbol = mapping.primary_symbol
            symbol_count[symbol] = symbol_count.get(symbol, 0) + 1
        
        return [
            {"symbol": symbol, "count": count}
            for symbol, count in symbol_count.items()
        ]
    
    def _analyze_archetypes(
        self,
        history: List[SymbolicMapping]
    ) -> Dict[str, Any]:
        """Analyze archetypal progression."""
        if not history:
            return {
                "sequence": [],
                "current": None,
                "suggested_next": "self"
            }
        
        sequence = [m.archetype for m in history]
        current = sequence[-1] if sequence else None
        
        return {
            "sequence": sequence,
            "current": current,
            "suggested_next": self._predict_next_archetype(sequence)
        }
    
    def _predict_next_archetype(self, sequence: List[str]) -> str:
        """Predict the next archetype in sequence."""
        if not sequence:
            return "self"
        
        # Simple prediction based on common progressions
        common_progressions = {
            "hero": ["mentor", "shadow", "self"],
            "shadow": ["self", "anima", "hero"],
            "mentor": ["hero", "sage", "trickster"],
            "self": ["hero", "anima", "shadow"]
        }
        
        current = sequence[-1]
        return common_progressions.get(current, ["self"])[0]
    
    def _cluster_symbols(
        self,
        history: List[SymbolicMapping]
    ) -> List[Dict[str, Any]]:
        """Cluster related symbols."""
        # Simple clustering based on common associations
        clusters = [
            {
                "name": "water",
                "symbols": ["water", "ocean", "river", "flow"]
            },
            {
                "name": "fire",
                "symbols": ["fire", "flame", "light", "sun"]
            },
            {
                "name": "earth",
                "symbols": ["mountain", "tree", "rock", "ground"]
            }
        ]
        
        return clusters
    
    def _analyze_emotions(
        self,
        history: List[SymbolicMapping]
    ) -> Dict[str, Any]:
        """Analyze emotional patterns."""
        if not history:
            return {
                "valence_trend": {"mean": 0.0, "variance": 0.0, "direction": "stable"},
                "arousal_trend": {"mean": 0.0, "variance": 0.0, "direction": "stable"}
            }
        
        valences = [m.valence for m in history]
        arousals = [m.arousal for m in history]
        
        return {
            "valence_trend": {
                "mean": float(np.mean(valences)),
                "variance": float(np.var(valences)),
                "direction": self._get_trend_direction(valences)
            },
            "arousal_trend": {
                "mean": float(np.mean(arousals)),
                "variance": float(np.var(arousals)),
                "direction": self._get_trend_direction(arousals)
            }
        }
    
    def _get_trend_direction(self, values: List[float]) -> str:
        """Get the direction of a trend."""
        if len(values) < 2:
            return "stable"
        
        diff = values[-1] - values[-2]
        if abs(diff) < 0.1:
            return "stable"
        return "increasing" if diff > 0 else "decreasing"
    
    def _find_cycles(
        self,
        history: List[SymbolicMapping]
    ) -> List[Dict[str, Any]]:
        """Find cyclic patterns in symbol sequences."""
        if len(history) < 4:
            return []
        
        symbols = [m.primary_symbol for m in history]
        cycles = []
        
        # Look for repeating sequences of 2-4 symbols
        for length in range(2, 5):
            for i in range(len(symbols) - length * 2):
                sequence = symbols[i:i + length]
                next_sequence = symbols[i + length:i + length * 2]
                if sequence == next_sequence:
                    cycles.append({
                        "symbols": sequence,
                        "length": length,
                        "occurrences": 2
                    })
        
        return cycles
    
    async def _apply_cultural_adaptations(
        self,
        mapping: SymbolicMapping,
        cultural_context: str
    ) -> Dict[str, Any]:
        """Apply cultural adaptations to symbolic mapping."""
        cache_key = f"{mapping.primary_symbol}:{cultural_context}"
        
        # Check cache
        if cache_key in self._cultural_cache:
            return self._cultural_cache[cache_key]
        
        # Basic cultural adaptations
        adaptations = {
            "primary_symbol": {
                "original": mapping.primary_symbol,
                "cultural_meaning": self._get_cultural_meaning(
                    mapping.primary_symbol,
                    cultural_context
                ),
                "cultural_associations": self._get_cultural_associations(
                    mapping.primary_symbol,
                    cultural_context
                ),
                "alternatives": self._get_cultural_alternatives(
                    mapping.primary_symbol,
                    cultural_context
                )
            },
            "archetype": {
                "original": mapping.archetype,
                "cultural_variant": self._adapt_archetype(
                    mapping.archetype,
                    cultural_context
                )
            },
            "timestamp": datetime.now()
        }
        
        # Cache result
        self._cultural_cache[cache_key] = adaptations
        await self._cleanup_cache()
        
        return adaptations
    
    def _get_cultural_meaning(
        self,
        symbol: str,
        context: str
    ) -> str:
        """Get cultural meaning of a symbol."""
        meanings = {
            "water": {
                "western": "purification and renewal",
                "eastern": "flow and adaptability",
                "indigenous": "life force and spirit"
            }
        }
        return meanings.get(symbol, {}).get(context, "universal symbol")
    
    def _get_cultural_associations(
        self,
        symbol: str,
        context: str
    ) -> List[str]:
        """Get cultural associations for a symbol."""
        associations = {
            "water": {
                "western": ["cleansing", "baptism", "renewal"],
                "eastern": ["harmony", "wisdom", "balance"],
                "indigenous": ["spirit", "healing", "connection"]
            }
        }
        return associations.get(symbol, {}).get(context, [])
    
    def _get_cultural_alternatives(
        self,
        symbol: str,
        context: str
    ) -> List[str]:
        """Get culturally appropriate alternative symbols."""
        alternatives = {
            "water": {
                "western": ["ocean", "river", "rain"],
                "eastern": ["stream", "mist", "dew"],
                "indigenous": ["spring", "waterfall", "lake"]
            }
        }
        return alternatives.get(symbol, {}).get(context, [])
    
    def _adapt_archetype(
        self,
        archetype: str,
        context: str
    ) -> str:
        """Adapt archetype to cultural context."""
        adaptations = {
            "hero": {
                "western": "hero",
                "eastern": "sage",
                "indigenous": "spirit-guide"
            }
        }
        return adaptations.get(archetype, {}).get(context, archetype)
    
    async def _cleanup_cache(self):
        """Clean up old cache entries."""
        if len(self._cultural_cache) <= self.MAX_CACHE_SIZE:
            return
        
        # Remove oldest entries
        sorted_entries = sorted(
            self._cultural_cache.items(),
            key=lambda x: x[1]["timestamp"]
        )
        
        to_remove = len(self._cultural_cache) - self.MAX_CACHE_SIZE
        for key, _ in sorted_entries[:to_remove]:
            del self._cultural_cache[key]