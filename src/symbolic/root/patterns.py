"""
Emotional journey pattern analysis and classification

This module provides tools for identifying patterns in emotional timelines
and classifying them according to established narrative structures.
"""
from enum import Enum
from typing import List, Dict, Any, Optional


class PatternStrength(Enum):
    """Strength of an identified pattern"""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


class EmotionalJourneyPattern(Enum):
    """Common emotional journey patterns"""
    HERO = "hero"
    TRANSFORMATION = "transformation"
    RESILIENCE = "resilience"
    DISCOVERY = "discovery"
    STRUGGLE = "struggle"
    GROWTH = "growth"


class ArchetypeMapping:
    """Maps emotional patterns to archetypes"""
    pattern: EmotionalJourneyPattern
    strength: PatternStrength
    description: str
    
    def __init__(self, pattern: EmotionalJourneyPattern, strength: PatternStrength, description: str):
        self.pattern = pattern
        self.strength = strength
        self.description = description
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "pattern": self.pattern.value,
            "strength": self.strength.value,
            "description": self.description
        }


def extract_journey_patterns(emotional_states: List[Dict[str, Any]]) -> List[EmotionalJourneyPattern]:
    """
    Extract journey patterns from a sequence of emotional states
    
    Args:
        emotional_states: List of emotional state entries
        
    Returns:
        List of identified journey patterns
    """
    # Simplified implementation for testing
    if not emotional_states:
        return []
    
    # Example pattern detection logic
    states = [e["state"].lower() for e in emotional_states]
    patterns = []
    
    if "struggle" in states and "confident" in states:
        patterns.append(EmotionalJourneyPattern.HERO)
    
    if "resilient" in states:
        patterns.append(EmotionalJourneyPattern.RESILIENCE)
        
    if len(set(states)) >= 3:
        patterns.append(EmotionalJourneyPattern.TRANSFORMATION)
    
    return patterns


def classify_emotional_pattern(emotional_states: List[Dict[str, Any]]) -> Optional[ArchetypeMapping]:
    """
    Classify an emotional pattern based on a sequence of states
    
    Args:
        emotional_states: List of emotional state entries
        
    Returns:
        ArchetypeMapping if a pattern is identified, None otherwise
    """
    patterns = extract_journey_patterns(emotional_states)
    
    if not patterns:
        return None
    
    # Select the most significant pattern (simplified)
    primary_pattern = patterns[0]
    
    # Determine strength based on pattern clarity
    strength = PatternStrength.MODERATE
    if len(patterns) == 1:
        strength = PatternStrength.STRONG
    
    descriptions = {
        EmotionalJourneyPattern.HERO: "A journey from struggle to triumph",
        EmotionalJourneyPattern.TRANSFORMATION: "A significant emotional transformation",
        EmotionalJourneyPattern.RESILIENCE: "A pattern of emotional resilience",
        EmotionalJourneyPattern.DISCOVERY: "A journey of emotional discovery",
        EmotionalJourneyPattern.STRUGGLE: "A period of emotional struggle",
        EmotionalJourneyPattern.GROWTH: "A pattern of emotional growth"
    }
    
    return ArchetypeMapping(
        pattern=primary_pattern,
        strength=strength,
        description=descriptions.get(primary_pattern, "Unclassified pattern")
    )
