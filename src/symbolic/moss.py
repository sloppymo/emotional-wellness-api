"""
MOSS: Crisis lexicon matching and safety evaluation subsystem

This module is responsible for detecting potential crisis indicators,
evaluating safety risks, and triggering the appropriate VELURIA
protocol level if necessary.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any, Set
import json
import os
import re
from datetime import datetime

from models.emotional_state import SymbolicMapping, SafetyStatus

logger = logging.getLogger(__name__)

class MossProcessor:
    """Core processor for crisis detection and safety evaluation"""
    
    def __init__(self, crisis_lexicon_path: Optional[str] = None):
        """Initialize the MOSS processor with an optional crisis lexicon path"""
        self.crisis_lexicons = {
            "high_risk": set(),
            "medium_risk": set(),
            "concerning": set(),
        }
        
        self.biometric_thresholds = {
            "hrv": {"min": 40, "concerning": 50, "normal": 60},
            "gsr": {"max": 0.5, "concerning": 0.3, "normal": 0.2},
            "voice_tremor": {"max": 0.6, "concerning": 0.4, "normal": 0.3}
        }
        
        # Load crisis lexicon if path provided
        if crisis_lexicon_path and os.path.exists(crisis_lexicon_path):
            try:
                with open(crisis_lexicon_path, 'r') as f:
                    lexicons = json.load(f)
                    for level, terms in lexicons.items():
                        self.crisis_lexicons[level] = set(terms)
                logger.info(f"Loaded crisis lexicon from {crisis_lexicon_path}")
            except Exception as e:
                logger.error(f"Error loading crisis lexicon: {str(e)}")
                self._load_default_lexicon()
        else:
            logger.warning("Crisis lexicon path not provided or invalid, using default")
            self._load_default_lexicon()
    
    def _load_default_lexicon(self):
        """Load a default crisis lexicon when no file is provided"""
        # IMPORTANT: This is a minimal set for demonstration purposes only
        # A real implementation would use a comprehensive, clinically validated lexicon
        self.crisis_lexicons = {
            "high_risk": {
                "suicide", "kill myself", "end my life", "better off dead",
                "no reason to live", "can't go on", "want to die"
            },
            "medium_risk": {
                "hopeless", "worthless", "trapped", "burden", "unbearable",
                "no way out", "darkness closing in", "no future"
            },
            "concerning": {
                "overwhelmed", "desperate", "exhausted", "can't cope",
                "falling apart", "breaking point", "lost", "empty"
            }
        }
        logger.info("Loaded default crisis lexicon")
    
    def evaluate(self, 
                symbols: SymbolicMapping, 
                text: Optional[str] = None,
                biomarkers: Optional[Dict[str, float]] = None) -> SafetyStatus:
        """
        Evaluate symbolic mapping and optional raw text for crisis indicators
        
        Args:
            symbols: SymbolicMapping from CANOPY
            text: Optional raw text (if not already processed)
            biomarkers: Optional dict of biomarker readings
            
        Returns:
            SafetyStatus object indicating risk level and recommended actions
        """
        logger.info("Evaluating safety with MOSS")
        
        # Track triggers for transparency
        triggers = []
        risk_score = 0.0
        metaphor_risk = self._calculate_metaphor_risk(symbols)
        
        # Check metaphor risk threshold
        if metaphor_risk > 0.75:
            risk_score += 0.4
            triggers.append("metaphor_risk_high")
        elif metaphor_risk > 0.5:
            risk_score += 0.2
            triggers.append("metaphor_risk_moderate")
        
        # Check lexical matches if text is provided
        if text:
            lexical_score, lexical_triggers = self._check_lexical_matches(text)
            risk_score += lexical_score
            triggers.extend(lexical_triggers)
        
        # Check biomarkers if provided
        if biomarkers:
            bio_score, bio_triggers = self._check_biomarkers(biomarkers)
            risk_score += bio_score
            triggers.extend(bio_triggers)
        
        # Determine safety level based on cumulative risk score
        if risk_score >= 0.7:
            level = 3  # Highest risk - human intervention
            actions = ["human_intervention", "provide_resources", "crisis_protocol"]
        elif risk_score >= 0.5:
            level = 2  # Moderate risk - automated protocols
            actions = ["safety_resources", "grounding_techniques", "support_options"]
        elif risk_score >= 0.3:
            level = 1  # Low risk - symbolic grounding
            actions = ["symbolic_grounding", "emotional_acknowledgment"]
        else:
            level = 0  # No detected risk
            actions = []
        
        return SafetyStatus(
            level=level,
            risk_score=risk_score,
            metaphor_risk=metaphor_risk,
            triggers=triggers,
            timestamp=datetime.now(),
            recommended_actions=actions
        )
    
    def _calculate_metaphor_risk(self, symbols: SymbolicMapping) -> float:
        """Calculate risk score based on symbolic content"""
        risk_score = 0.0
        
        # Check for high-risk archetypes
        high_risk_archetypes = {"shadow", "destroyer", "outlaw"}
        medium_risk_archetypes = {"trickster", "sage", "magician"}
        
        if symbols.archetype in high_risk_archetypes:
            risk_score += 0.3
        elif symbols.archetype in medium_risk_archetypes:
            risk_score += 0.1
        
        # Check for concerning symbols
        high_risk_symbols = {"abyss", "void", "knife", "poison", "cliff", "falling", "death"}
        medium_risk_symbols = {"darkness", "storm", "broken", "trapped", "maze", "wall"}
        
        # Check primary symbol
        if symbols.primary_symbol in high_risk_symbols:
            risk_score += 0.3
        elif symbols.primary_symbol in medium_risk_symbols:
            risk_score += 0.1
            
        # Check alternative symbols
        for symbol in symbols.alternative_symbols:
            if symbol in high_risk_symbols:
                risk_score += 0.2
            elif symbol in medium_risk_symbols:
                risk_score += 0.1
        
        # Check valence/arousal combination (high arousal + negative valence)
        if symbols.valence < -0.5 and symbols.arousal > 0.7:
            risk_score += 0.2
        elif symbols.valence < -0.3 and symbols.arousal > 0.5:
            risk_score += 0.1
            
        # Cap at 1.0
        return min(risk_score, 1.0)
    
    def _check_lexical_matches(self, text: str) -> Tuple[float, List[str]]:
        """Check for matches against crisis lexicon"""
        risk_score = 0.0
        triggers = []
        
        # Normalize text for matching
        text_lower = text.lower()
        
        # Check high risk terms - direct matches
        for term in self.crisis_lexicons["high_risk"]:
            pattern = r'\b' + re.escape(term) + r'\b'
            if re.search(pattern, text_lower):
                risk_score += 0.5
                triggers.append(f"high_risk_term")
                break  # One high risk match is sufficient
                
        # Check medium risk terms
        medium_matches = 0
        for term in self.crisis_lexicons["medium_risk"]:
            pattern = r'\b' + re.escape(term) + r'\b'
            if re.search(pattern, text_lower):
                medium_matches += 1
                if medium_matches == 1:
                    triggers.append("medium_risk_term")
        
        # Only count up to 3 medium risk matches
        risk_score += min(medium_matches, 3) * 0.1
        
        # Check concerning terms 
        concerning_matches = 0
        for term in self.crisis_lexicons["concerning"]:
            pattern = r'\b' + re.escape(term) + r'\b'
            if re.search(pattern, text_lower):
                concerning_matches += 1
                if concerning_matches == 1:
                    triggers.append("concerning_term")
        
        # Only count up to 5 concerning matches
        risk_score += min(concerning_matches, 5) * 0.05
        
        return min(risk_score, 0.8), triggers
    
    def _check_biomarkers(self, biomarkers: Dict[str, float]) -> Tuple[float, List[str]]:
        """Evaluate risk based on biomarker readings"""
        risk_score = 0.0
        triggers = []
        
        # Check heart rate variability (HRV) - lower is concerning
        if "hrv" in biomarkers:
            hrv = biomarkers["hrv"]
            if hrv < self.biometric_thresholds["hrv"]["min"]:
                risk_score += 0.3
                triggers.append("hrv_critical")
            elif hrv < self.biometric_thresholds["hrv"]["concerning"]:
                risk_score += 0.15
                triggers.append("hrv_concerning")
        
        # Check galvanic skin response (GSR) - higher is concerning
        if "gsr" in biomarkers:
            gsr = biomarkers["gsr"]
            if gsr > self.biometric_thresholds["gsr"]["max"]:
                risk_score += 0.3
                triggers.append("gsr_critical")
            elif gsr > self.biometric_thresholds["gsr"]["concerning"]:
                risk_score += 0.15
                triggers.append("gsr_concerning")
        
        # Check voice tremor - higher is concerning
        if "voice_tremor" in biomarkers:
            tremor = biomarkers["voice_tremor"]
            if tremor > self.biometric_thresholds["voice_tremor"]["max"]:
                risk_score += 0.3
                triggers.append("voice_critical")
            elif tremor > self.biometric_thresholds["voice_tremor"]["concerning"]:
                risk_score += 0.15
                triggers.append("voice_concerning")
        
        # Cap at 0.6 - biomarkers alone shouldn't trigger highest level
        return min(risk_score, 0.6), triggers


# Singleton instance for application-wide use
_instance = None

def get_moss_processor():
    """Get or create the singleton instance of MossProcessor"""
    global _instance
    if _instance is None:
        _instance = MossProcessor()
    return _instance
