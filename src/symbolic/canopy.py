"""
CANOPY: Symbolic archetype extraction and metaphor mapping subsystem

This module is responsible for processing emotional input text,
extracting metaphors, and mapping them to appropriate archetypes
using NLP techniques and integration with Claude 3 Haiku.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
import json
import asyncio
from datetime import datetime
import os

# For local development without LLM access, we use a fallback
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from models.emotional_state import SymbolicMapping, EmotionalMetaphor

logger = logging.getLogger(__name__)

# Constants
JUNGIAN_ARCHETYPES = [
    "hero", "shadow", "anima", "animus", "mentor", 
    "trickster", "self", "persona", "caregiver", 
    "sage", "explorer", "creator", "ruler", "innocent",
    "magician", "lover", "everyman", "jester", "outlaw", "destroyer"
]

SYMBOL_CATEGORIES = [
    "natural_elements", "celestial_bodies", "animals", "plants",
    "structures", "journeys", "containers", "transformations", 
    "thresholds", "landscapes", "weather", "colors", "directions"
]

class CanopyProcessor:
    """Core processor for metaphor extraction and archetype mapping"""
    
    def __init__(self, api_key: Optional[str] = None, symbol_library_path: Optional[str] = None):
        """Initialize the CANOPY processor with optional API key and symbol library"""
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.client = None
        self.symbol_library = {}
        
        if ANTHROPIC_AVAILABLE and self.api_key:
            self.client = Anthropic(api_key=self.api_key)
            logger.info("Initialized CANOPY with Claude integration")
        else:
            logger.warning("Anthropic client not available, using fallback mode")
            
        # Load symbol library if path provided
        if symbol_library_path and os.path.exists(symbol_library_path):
            try:
                with open(symbol_library_path, 'r') as f:
                    self.symbol_library = json.load(f)
                logger.info(f"Loaded symbol library from {symbol_library_path}")
            except Exception as e:
                logger.error(f"Error loading symbol library: {str(e)}")
    
    async def extract(self, 
                     text: str, 
                     biomarkers: Optional[Dict[str, float]] = None,
                     context: Optional[Dict[str, Any]] = None) -> SymbolicMapping:
        """
        Extract metaphors and symbolic meanings from input text
        
        Args:
            text: User's emotional text input
            biomarkers: Optional dict of biomarker readings
            context: Optional context from previous interactions
            
        Returns:
            SymbolicMapping object containing extracted metaphors and archetypes
        """
        logger.info("Processing text through CANOPY")
        
        # For HIPAA compliance, we don't log the actual text
        text_length = len(text) if text else 0
        logger.info(f"Processing input of length {text_length}")
        
        # Use Claude if available, otherwise use fallback
        if self.client:
            return await self._process_with_claude(text, biomarkers, context)
        else:
            return self._process_fallback(text, biomarkers, context)
    
    async def _process_with_claude(self, 
                                 text: str, 
                                 biomarkers: Optional[Dict[str, float]] = None,
                                 context: Optional[Dict[str, Any]] = None) -> SymbolicMapping:
        """Process text using Claude 3 Haiku for metaphor extraction"""
        try:
            # Construct prompt with careful handling of PHI
            prompt = f"""
            As CANOPY, a symbolic analysis system for emotional wellness, your task is to:
            
            1. Identify metaphors in the text
            2. Map these metaphors to appropriate Jungian archetypes
            3. Return symbolic interpretations and alternatives
            4. Ensure all responses maintain emotional safety
            
            Rules:
            - Do NOT include ANY personally identifiable information in your response
            - Do not attempt to diagnose or provide medical/therapeutic advice
            - Focus on symbolic representation, not fixing problems
            
            Text to analyze: {text}
            
            Please provide a JSON response with:
            - primary_symbol: The main symbolic element
            - archetype: The primary Jungian archetype present
            - alternative_symbols: 2-3 alternative symbolic representations
            - valence: Numerical approximation of emotional valence (-1.0 to 1.0)
            - arousal: Numerical approximation of emotional arousal (0.0 to 1.0)
            - metaphors: List of identified metaphorical expressions
            """
            
            # Add context if available
            if context and "previous_symbols" in context:
                symbols_context = ", ".join(context["previous_symbols"])
                prompt += f"\nAdditional context - previous symbols: {symbols_context}"
            
            response = await self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                temperature=0.4,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Extract JSON from response
            try:
                content = response.content[0].text
                # Find JSON in the response
                start = content.find('{')
                end = content.rfind('}') + 1
                if start >= 0 and end > start:
                    json_content = content[start:end]
                    data = json.loads(json_content)
                else:
                    raise ValueError("No valid JSON found in response")
                
                # Create SymbolicMapping from Claude response
                return self._create_mapping_from_response(data)
                
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON from Claude response")
                return self._process_fallback(text, biomarkers, context)
                
        except Exception as e:
            logger.error(f"Error using Claude integration: {str(e)}")
            return self._process_fallback(text, biomarkers, context)
    
    def _process_fallback(self, 
                        text: str, 
                        biomarkers: Optional[Dict[str, float]] = None,
                        context: Optional[Dict[str, Any]] = None) -> SymbolicMapping:
        """Fallback processing when Claude is not available"""
        logger.info("Using fallback symbolic processing")
        
        # Simple keyword-based metaphor extraction
        metaphors = []
        primary_symbol = "water"  # Default
        archetype = "self"  # Default
        alternatives = ["path", "light", "container"]
        valence = 0.0
        arousal = 0.5
        
        # Very basic keyword matching
        water_terms = ["water", "ocean", "river", "flow", "sink", "swim", "drown", "wave"]
        fire_terms = ["fire", "burn", "flame", "light", "candle", "spark", "ignite"]
        path_terms = ["road", "path", "journey", "walk", "direction", "lost", "found"]
        
        text_lower = text.lower()
        
        # Detect symbols from keywords
        if any(term in text_lower for term in water_terms):
            primary_symbol = "water"
            metaphors.append(EmotionalMetaphor(
                text=next((term for term in water_terms if term in text_lower), "water"),
                symbol="water",
                confidence=0.8
            ))
            if "drown" in text_lower:
                valence = -0.7
                arousal = 0.8
                archetype = "shadow"
            elif "flow" in text_lower:
                valence = 0.3
                arousal = 0.4
                archetype = "self"
        
        elif any(term in text_lower for term in fire_terms):
            primary_symbol = "fire"
            metaphors.append(EmotionalMetaphor(
                text=next((term for term in fire_terms if term in text_lower), "fire"),
                symbol="fire",
                confidence=0.8
            ))
            if "burn" in text_lower:
                valence = -0.5
                arousal = 0.9
                archetype = "destroyer"
            else:
                valence = 0.5
                arousal = 0.7
                archetype = "creator"
                
        elif any(term in text_lower for term in path_terms):
            primary_symbol = "path"
            metaphors.append(EmotionalMetaphor(
                text=next((term for term in path_terms if term in text_lower), "path"),
                symbol="path",
                confidence=0.8
            ))
            if "lost" in text_lower:
                valence = -0.6
                arousal = 0.5
                archetype = "explorer"
            else:
                valence = 0.4
                arousal = 0.6
                archetype = "hero"
        
        # Create symbolic mapping
        return SymbolicMapping(
            primary_symbol=primary_symbol,
            archetype=archetype,
            alternative_symbols=alternatives,
            valence=valence,
            arousal=arousal,
            metaphors=metaphors,
            timestamp=datetime.now(),
            confidence=0.6
        )
    
    def _create_mapping_from_response(self, data: Dict[str, Any]) -> SymbolicMapping:
        """Convert Claude JSON response to SymbolicMapping object"""
        # Extract metaphors if available
        metaphors = []
        if "metaphors" in data and isinstance(data["metaphors"], list):
            for m in data["metaphors"]:
                if isinstance(m, str):
                    metaphors.append(EmotionalMetaphor(
                        text=m,
                        symbol=data.get("primary_symbol", "unknown"),
                        confidence=0.8
                    ))
                elif isinstance(m, dict):
                    metaphors.append(EmotionalMetaphor(
                        text=m.get("text", "unknown"),
                        symbol=m.get("symbol", data.get("primary_symbol", "unknown")),
                        confidence=m.get("confidence", 0.8)
                    ))
        
        # Create mapping object
        return SymbolicMapping(
            primary_symbol=data.get("primary_symbol", "unknown"),
            archetype=data.get("archetype", "self"),
            alternative_symbols=data.get("alternative_symbols", []),
            valence=data.get("valence", 0.0),
            arousal=data.get("arousal", 0.5),
            metaphors=metaphors,
            timestamp=datetime.now(),
            confidence=data.get("confidence", 0.8)
        )
    
    def calculate_drift(self, 
                      current: SymbolicMapping, 
                      previous: List[SymbolicMapping]) -> float:
        """
        Calculate symbolic drift between current and previous symbolic mappings
        
        Args:
            current: Current symbolic mapping
            previous: List of previous symbolic mappings, ordered by recency
            
        Returns:
            Float value between 0.0 and 1.0 representing drift magnitude
        """
        if not previous:
            return 0.0
            
        # Start with simple algorithm - can be enhanced with more sophisticated
        # symbolic relationship modeling
        
        # Check if symbols are completely different
        latest = previous[0]
        if (current.primary_symbol != latest.primary_symbol and
            current.primary_symbol not in latest.alternative_symbols and
            latest.primary_symbol not in current.alternative_symbols):
            base_drift = 0.7
        else:
            base_drift = 0.3
            
        # Factor in archetype changes
        if current.archetype != latest.archetype:
            archetype_drift = 0.2
        else:
            archetype_drift = 0.0
            
        # Factor in valence/arousal changes
        emotion_drift = (
            abs(current.valence - latest.valence) * 0.5 +
            abs(current.arousal - latest.arousal) * 0.3
        )
        
        # Combine factors with weights
        return min(base_drift + archetype_drift + emotion_drift, 1.0)


# Singleton instance for application-wide use
_instance = None

def get_canopy_processor():
    """Get or create the singleton instance of CanopyProcessor"""
    global _instance
    if _instance is None:
        _instance = CanopyProcessor()
    return _instance


# 
#    ,_,
#   (O,O)
#   (   )
#  --"-"--
#