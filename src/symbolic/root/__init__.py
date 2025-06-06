"""
ROOT Subsystem
Longitudinal Emotional State Mapping and Archetype Identification

The ROOT subsystem maps emotional states over time, creating narrative arcs
and applying archetype identification principles to help users understand
their emotional patterns.
"""

from symbolic.root.analysis import (
    analyze_emotional_timeline,
    identify_archetypes,
    map_journey_pattern
)
from symbolic.root.patterns import (
    EmotionalJourneyPattern,
    ArchetypeMapping,
    PatternStrength,
    extract_journey_patterns,
    classify_emotional_pattern
)
from symbolic.root.archetypes import (
    ArchetypeCategory,
    EmotionalArchetype,
    get_archetype_description,
    create_archetype_profile,
    get_dominant_archetypes
)

__all__ = [
    "analyze_emotional_timeline",
    "identify_archetypes",
    "map_journey_pattern",
    "EmotionalJourneyPattern",
    "ArchetypeMapping", 
    "PatternStrength",
    "extract_journey_patterns",
    "classify_emotional_pattern",
    "ArchetypeCategory",
    "EmotionalArchetype",
    "get_archetype_description",
    "create_archetype_profile",
    "get_dominant_archetypes"
]
