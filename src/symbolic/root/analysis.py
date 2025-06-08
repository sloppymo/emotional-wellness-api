"""
ROOT Subsystem Analysis
Longitudinal Emotional State Mapping and Archetype Identification
"""
#
#  /\_/\
# / o o \
# \~(*)~/
#  " " "
# 
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

# Example archetype categories (can be expanded)
class Archetype(str, Enum):
    HERO = "Hero"
    SAGE = "Sage"
    CAREGIVER = "Caregiver"
    EXPLORER = "Explorer"
    EVERYPERSON = "Everyperson"
    REBEL = "Rebel"
    LOVER = "Lover"
    CREATOR = "Creator"
    JESTER = "Jester"
    RULER = "Ruler"
    MAGICIAN = "Magician"
    OUTLAW = "Outlaw"


def analyze_emotional_timeline(emotional_states: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze a user's longitudinal emotional state timeline.
    Returns summary statistics and detected narrative arcs.
    """
    if not emotional_states:
        return {"summary": "No data", "arcs": []}

    # Example: calculate frequency of each state
    freq = {}
    for entry in emotional_states:
        state = entry.get("state")
        freq[state] = freq.get(state, 0) + 1

    # Example: detect simple arcs (e.g., improvement, decline)
    arc = "stable"
    if len(emotional_states) >= 2:
        first = emotional_states[0]["state"]
        last = emotional_states[-1]["state"]
        if first != last:
            arc = "improvement" if last > first else "decline"

    return {
        "state_frequencies": freq,
        "arc": arc,
        "total_entries": len(emotional_states)
    }


def identify_archetypes(emotional_states: List[Dict[str, Any]]) -> List[Archetype]:
    """
    Identify narrative archetypes from a user's emotional state history.
    Returns a list of matching archetypes.
    """
    # Example heuristic: match based on state transitions
    archetypes = set()
    for entry in emotional_states:
        state = entry.get("state")
        # Dummy logic: assign archetype based on state
        if state in ("resilient", "confident"):
            archetypes.add(Archetype.HERO)
        elif state in ("curious", "reflective"):
            archetypes.add(Archetype.SAGE)
        elif state in ("supportive", "nurturing"):
            archetypes.add(Archetype.CAREGIVER)
        elif state in ("adventurous", "exploring"):
            archetypes.add(Archetype.EXPLORER)
    return list(archetypes)


def map_journey_pattern(emotional_states: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Map the user's emotional journey to a symbolic pattern.
    Returns pattern name and supporting evidence.
    """
    # Example: detect "Hero's Journey" if certain states are present
    journey = "Unknown"
    evidence = []
    states = [e.get("state") for e in emotional_states]
    if "struggle" in states and "resilient" in states and "confident" in states:
        journey = "Hero's Journey"
        evidence = [s for s in states if s in ("struggle", "resilient", "confident")]
    elif "curious" in states and "reflective" in states:
        journey = "Quest for Wisdom"
        evidence = [s for s in states if s in ("curious", "reflective")]
    return {
        "pattern": journey,
        "evidence": evidence
    }
