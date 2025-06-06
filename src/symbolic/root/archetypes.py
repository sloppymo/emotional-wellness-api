"""
Emotional archetypes and their classifications

This module defines emotional archetypes and provides tools for
mapping emotional states to archetypal patterns.
"""
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from functools import lru_cache
import time
import re
import json
from datetime import datetime, timedelta

# For local in-memory caching
from functools import lru_cache

# Optional Redis client for distributed caching
try:
    from redis import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class ArchetypeCategory(Enum):
    """Categories of emotional archetypes"""
    HERO = "hero"
    CAREGIVER = "caregiver"
    EXPLORER = "explorer"
    CREATOR = "creator"
    SAGE = "sage"
    INNOCENT = "innocent"
    RULER = "ruler"
    MAGICIAN = "magician"
    LOVER = "lover"
    JESTER = "jester"
    EVERYMAN = "everyman"
    OUTLAW = "outlaw"


class EmotionalArchetype:
    """Representation of an emotional archetype"""
    category: ArchetypeCategory
    name: str
    description: str
    traits: List[str]
    
    def __init__(self, category: ArchetypeCategory, name: str, description: str, traits: List[str]):
        self.category = category
        self.name = name
        self.description = description
        self.traits = traits
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "category": self.category.value,
            "name": self.name,
            "description": self.description,
            "traits": self.traits
        }


# Dictionary of archetype descriptions
ARCHETYPE_DESCRIPTIONS = {
    ArchetypeCategory.HERO: "One who overcomes obstacles and transforms through courage",
    ArchetypeCategory.CAREGIVER: "One who protects and cares for others",
    ArchetypeCategory.EXPLORER: "One who seeks new experiences and discoveries",
    ArchetypeCategory.CREATOR: "One who brings new ideas and concepts into being",
    ArchetypeCategory.SAGE: "One who seeks truth and understanding",
    ArchetypeCategory.INNOCENT: "One who maintains optimism and faith",
    ArchetypeCategory.RULER: "One who creates order and structure",
    ArchetypeCategory.MAGICIAN: "One who transforms and makes dreams reality",
    ArchetypeCategory.LOVER: "One who seeks connection and intimacy",
    ArchetypeCategory.JESTER: "One who brings joy and lightness",
    ArchetypeCategory.EVERYMAN: "One who seeks belonging and connection",
    ArchetypeCategory.OUTLAW: "One who challenges convention and authority"
}


# Dictionary mapping emotional states to likely archetypes with weighting
# Format: emotional_state: [(archetype, weight), ...]
EMOTIONAL_STATE_ARCHETYPES = {
    # Positive emotions
    "confident": [(ArchetypeCategory.HERO, 0.8), (ArchetypeCategory.RULER, 0.6)],
    "curious": [(ArchetypeCategory.EXPLORER, 0.9), (ArchetypeCategory.SAGE, 0.7)],
    "creative": [(ArchetypeCategory.CREATOR, 0.9), (ArchetypeCategory.MAGICIAN, 0.7)],
    "joyful": [(ArchetypeCategory.JESTER, 0.8), (ArchetypeCategory.INNOCENT, 0.7)],
    "loving": [(ArchetypeCategory.LOVER, 0.9), (ArchetypeCategory.CAREGIVER, 0.6)],
    "caring": [(ArchetypeCategory.CAREGIVER, 0.9), (ArchetypeCategory.LOVER, 0.6)],
    "reflective": [(ArchetypeCategory.SAGE, 0.8), (ArchetypeCategory.EVERYMAN, 0.4)],
    "resilient": [(ArchetypeCategory.HERO, 0.7), (ArchetypeCategory.MAGICIAN, 0.5)],
    "excited": [(ArchetypeCategory.EXPLORER, 0.7), (ArchetypeCategory.JESTER, 0.6)],
    "peaceful": [(ArchetypeCategory.INNOCENT, 0.7), (ArchetypeCategory.EVERYMAN, 0.5)],
    "proud": [(ArchetypeCategory.RULER, 0.8), (ArchetypeCategory.HERO, 0.5)],
    "hopeful": [(ArchetypeCategory.INNOCENT, 0.8), (ArchetypeCategory.CREATOR, 0.5)],
    "inspired": [(ArchetypeCategory.CREATOR, 0.8), (ArchetypeCategory.MAGICIAN, 0.7)],
    "grateful": [(ArchetypeCategory.CAREGIVER, 0.6), (ArchetypeCategory.INNOCENT, 0.5)],
    "content": [(ArchetypeCategory.EVERYMAN, 0.7), (ArchetypeCategory.INNOCENT, 0.5)],
    
    # Challenging emotions
    "anxious": [(ArchetypeCategory.INNOCENT, 0.6), (ArchetypeCategory.EXPLORER, 0.4)],
    "sad": [(ArchetypeCategory.EVERYMAN, 0.6), (ArchetypeCategory.LOVER, 0.4)],
    "angry": [(ArchetypeCategory.OUTLAW, 0.8), (ArchetypeCategory.RULER, 0.5)],
    "frustrated": [(ArchetypeCategory.OUTLAW, 0.6), (ArchetypeCategory.CREATOR, 0.4)],
    "confused": [(ArchetypeCategory.EXPLORER, 0.5), (ArchetypeCategory.SAGE, 0.4)],
    "overwhelmed": [(ArchetypeCategory.EVERYMAN, 0.7), (ArchetypeCategory.HERO, 0.5)],
    "disappointed": [(ArchetypeCategory.INNOCENT, 0.6), (ArchetypeCategory.RULER, 0.4)],
    "fearful": [(ArchetypeCategory.INNOCENT, 0.7), (ArchetypeCategory.HERO, 0.5)],
    "guilty": [(ArchetypeCategory.EVERYMAN, 0.6), (ArchetypeCategory.OUTLAW, 0.5)],
    "grieving": [(ArchetypeCategory.LOVER, 0.8), (ArchetypeCategory.EVERYMAN, 0.6)],
    "lonely": [(ArchetypeCategory.LOVER, 0.7), (ArchetypeCategory.EVERYMAN, 0.6)],
    
    # Complex emotional states
    "rebellious": [(ArchetypeCategory.OUTLAW, 0.9), (ArchetypeCategory.EXPLORER, 0.5)],
    "nostalgic": [(ArchetypeCategory.INNOCENT, 0.7), (ArchetypeCategory.LOVER, 0.5)],
    "determined": [(ArchetypeCategory.HERO, 0.8), (ArchetypeCategory.RULER, 0.6)],
    "vulnerable": [(ArchetypeCategory.INNOCENT, 0.7), (ArchetypeCategory.LOVER, 0.6)],
    "skeptical": [(ArchetypeCategory.SAGE, 0.7), (ArchetypeCategory.OUTLAW, 0.5)],
    "secure": [(ArchetypeCategory.RULER, 0.7), (ArchetypeCategory.EVERYMAN, 0.6)],
    "struggle": [(ArchetypeCategory.HERO, 0.8), (ArchetypeCategory.EVERYMAN, 0.6)],
    "contemplative": [(ArchetypeCategory.SAGE, 0.9), (ArchetypeCategory.MAGICIAN, 0.4)],
    "brave": [(ArchetypeCategory.HERO, 0.9), (ArchetypeCategory.EXPLORER, 0.5)],
    "empowered": [(ArchetypeCategory.MAGICIAN, 0.7), (ArchetypeCategory.HERO, 0.7)],
    "challenged": [(ArchetypeCategory.HERO, 0.7), (ArchetypeCategory.CREATOR, 0.5)],
    "ambivalent": [(ArchetypeCategory.EVERYMAN, 0.5), (ArchetypeCategory.SAGE, 0.4)],
    "transforming": [(ArchetypeCategory.MAGICIAN, 0.9), (ArchetypeCategory.HERO, 0.7)],
    "connected": [(ArchetypeCategory.LOVER, 0.8), (ArchetypeCategory.EVERYMAN, 0.7)]
}


class ArchetypeCache:
    """Cache for archetype mapping results to improve performance"""
    
    def __init__(self, redis_client=None, cache_ttl: int = 3600):
        """Initialize the cache
        
        Args:
            redis_client: Optional Redis client for distributed caching
            cache_ttl: Time to live for cache entries in seconds (default 1 hour)
        """
        self.redis = redis_client
        self.cache_ttl = cache_ttl
        self.local_cache = {}
        self.local_cache_timestamp = {}
        
    def get_cached_profile(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a cached archetype profile
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Cached profile or None if not in cache
        """
        cache_key = f"archetype:profile:{user_id}:{session_id}"
        
        # Try Redis first if available
        if self.redis:
            cached_data = self.redis.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        
        # Fall back to local cache
        if cache_key in self.local_cache:
            # Check if cache entry is still valid
            timestamp = self.local_cache_timestamp.get(cache_key, 0)
            if time.time() - timestamp < self.cache_ttl:
                return self.local_cache[cache_key]
            else:
                # Expired - remove from local cache
                self._clean_local_cache(cache_key)
        
        return None
    
    def store_profile(self, user_id: str, session_id: str, profile: Dict[str, Any]) -> None:
        """Store an archetype profile in cache
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            profile: Archetype profile to cache
        """
        cache_key = f"archetype:profile:{user_id}:{session_id}"
        serialized = json.dumps(profile, default=self._serialize_enum)
        
        # Store in Redis if available
        if self.redis:
            self.redis.setex(cache_key, self.cache_ttl, serialized)
        
        # Store in local cache
        self.local_cache[cache_key] = profile
        self.local_cache_timestamp[cache_key] = time.time()
        
    def invalidate(self, user_id: str, session_id: str) -> None:
        """Invalidate a cached profile
        
        Args:
            user_id: User identifier
            session_id: Session identifier
        """
        cache_key = f"archetype:profile:{user_id}:{session_id}"
        
        if self.redis:
            self.redis.delete(cache_key)
        
        self._clean_local_cache(cache_key)
    
    def _clean_local_cache(self, key: str) -> None:
        """Remove an entry from local cache
        
        Args:
            key: Cache key to remove
        """
        if key in self.local_cache:
            del self.local_cache[key]
        
        if key in self.local_cache_timestamp:
            del self.local_cache_timestamp[key]
    
    def _serialize_enum(self, obj):
        """Helper method to serialize Enum values for JSON"""
        if isinstance(obj, Enum):
            return obj.value
        raise TypeError(f"Type {type(obj)} not serializable")


@lru_cache(maxsize=128)
def get_archetype_description(category: ArchetypeCategory) -> str:
    """Get the description for an archetype category (cached)"""
    return ARCHETYPE_DESCRIPTIONS.get(category, "Unknown archetype")


@lru_cache(maxsize=256)
def map_emotional_state_to_archetypes(state: str) -> List[Tuple[ArchetypeCategory, float]]:
    """Map an emotional state to potential archetypes with weights
    
    Args:
        state: Emotional state string
        
    Returns:
        List of (archetype, weight) tuples
    """
    # Convert to lowercase and remove extra whitespace
    normalized_state = state.lower().strip()
    
    # Direct match in our dictionary
    if normalized_state in EMOTIONAL_STATE_ARCHETYPES:
        return EMOTIONAL_STATE_ARCHETYPES[normalized_state]
    
    # Try to find near matches using partial string matching
    partial_matches = []
    for key in EMOTIONAL_STATE_ARCHETYPES:
        # Check if the emotional state contains our key or vice versa
        if key in normalized_state or normalized_state in key:
            similarity = len(set(normalized_state) & set(key)) / len(set(normalized_state) | set(key))
            if similarity > 0.5:  # Only consider sufficiently similar matches
                for archetype, weight in EMOTIONAL_STATE_ARCHETYPES[key]:
                    # Reduce weight based on similarity
                    adjusted_weight = weight * similarity
                    partial_matches.append((archetype, adjusted_weight))
    
    # If we found partial matches, return those
    if partial_matches:
        # Merge duplicate archetypes by taking the max weight
        merged = {}
        for archetype, weight in partial_matches:
            if archetype not in merged or weight > merged[archetype]:
                merged[archetype] = weight
        
        return [(archetype, weight) for archetype, weight in merged.items()]
    
    # Fallback: return a mix of common archetypes with low weights
    return [(ArchetypeCategory.EVERYMAN, 0.3), (ArchetypeCategory.EXPLORER, 0.2)]


def create_archetype_profile(emotional_states: List[Dict[str, Any]], 
                           time_weighting: bool = True,
                           intensity_key: str = "intensity") -> Dict[ArchetypeCategory, float]:
    """
    Create an archetype profile based on emotional states with weighted contributions
    
    Args:
        emotional_states: List of emotional state entries
        time_weighting: Whether to weight recent emotions more heavily
        intensity_key: Key in emotional_states dict that contains intensity value
        
    Returns:
        Dictionary mapping archetype categories to their weighted scores
    """
    profile = {category: 0.0 for category in ArchetypeCategory}
    total_entries = len(emotional_states)
    
    if total_entries == 0:
        return profile
        
    # Calculate time weights if enabled
    time_weights = []
    if time_weighting and total_entries > 1:
        # Assign exponential decay weights based on recency
        # Most recent emotions get higher weights
        decay_factor = 0.85  # Decay rate for older emotions
        for i in range(total_entries):
            # Normalize position to 0-1 range (0 is oldest, 1 is newest)
            position = i / (total_entries - 1)
            # Apply exponential decay formula: weight = decay_factor^(1-position)
            weight = decay_factor ** (1.0 - position)
            time_weights.append(weight)
    else:
        # Equal weighting if time weighting is disabled
        time_weights = [1.0] * total_entries
    
    # Process each emotional state with its appropriate weighting
    for i, entry in enumerate(emotional_states):
        state = entry.get("state", "").lower()
        if not state:
            continue
            
        # Get intensity factor (default to 1.0 if not specified)
        intensity = entry.get(intensity_key, 1.0)
        if not isinstance(intensity, (int, float)):
            intensity = 1.0
        # Clamp intensity between 0.1 and 2.0
        intensity = max(0.1, min(2.0, intensity))
        
        # Get time weight for this entry
        time_weight = time_weights[i]
        
        # Apply weighted archetypes
        for archetype, base_weight in map_emotional_state_to_archetypes(state):
            # Combine all weighting factors
            combined_weight = base_weight * intensity * time_weight
            profile[archetype] += combined_weight
    
    # Normalize the profile to a 0-10 scale
    max_value = max(profile.values()) if any(profile.values()) else 1.0
    if max_value > 0:
        for category in profile:
            profile[category] = round((profile[category] / max_value) * 10, 2)
    
    return profile


def get_dominant_archetypes(profile: Dict[ArchetypeCategory, float], limit: int = 3) -> List[EmotionalArchetype]:
    """
    Get the dominant archetypes from a profile
    
    Args:
        profile: Archetype profile
        limit: Maximum number of archetypes to return
        
    Returns:
        List of dominant emotional archetypes
    """
    # Sort archetypes by frequency
    sorted_archetypes = sorted(
        profile.items(), 
        key=lambda x: x[1], 
        reverse=True
    )
    
    # Take top archetypes
    dominant = sorted_archetypes[:limit]
    
    # Define traits for all archetype categories
    archetype_traits = {
        ArchetypeCategory.HERO: ["courage", "perseverance", "transformation", "overcoming"],
        ArchetypeCategory.EXPLORER: ["curiosity", "independence", "discovery", "adventure"],
        ArchetypeCategory.CREATOR: ["innovation", "imagination", "expression", "originality"],
        ArchetypeCategory.CAREGIVER: ["nurturing", "compassion", "protection", "generosity"],
        ArchetypeCategory.SAGE: ["wisdom", "knowledge", "understanding", "objectivity"],
        ArchetypeCategory.INNOCENT: ["optimism", "trust", "purity", "renewal"],
        ArchetypeCategory.RULER: ["leadership", "order", "control", "responsibility"],
        ArchetypeCategory.MAGICIAN: ["transformation", "vision", "healing", "intuition"],
        ArchetypeCategory.LOVER: ["intimacy", "passion", "connection", "appreciation"],
        ArchetypeCategory.JESTER: ["joy", "humor", "playfulness", "spontaneity"],
        ArchetypeCategory.EVERYMAN: ["belonging", "realism", "empathy", "authenticity"],
        ArchetypeCategory.OUTLAW: ["rebellion", "revolution", "freedom", "disruption"]
    }
    
    # Create EmotionalArchetype objects
    result = []
    for category, score in dominant:
        if score > 0:  # Only include archetypes that have a positive score
            result.append(EmotionalArchetype(
                category=category,
                name=category.value.capitalize(),
                description=get_archetype_description(category),
                traits=archetype_traits.get(category, [])
            ))
    
    return result


def analyze_archetype_transitions(emotional_states: List[Dict[str, Any]], 
                              time_segments: int = 3) -> Dict[str, Any]:
    """
    Analyze transitions between dominant archetypes over time
    
    Args:
        emotional_states: List of emotional state entries
        time_segments: Number of time segments to divide the data into
        
    Returns:
        Dictionary with transition analysis and patterns
    """
    if not emotional_states or len(emotional_states) < 2:
        return {"transitions": [], "patterns": [], "stability": 1.0}
    
    # Sort states by timestamp if available
    if "timestamp" in emotional_states[0]:
        sorted_states = sorted(emotional_states, key=lambda x: x.get("timestamp", 0))
    else:
        # Assume states are already in chronological order
        sorted_states = emotional_states
    
    # Divide states into time segments
    segment_size = max(1, len(sorted_states) // time_segments)
    segments = []
    
    for i in range(0, len(sorted_states), segment_size):
        segment = sorted_states[i:i + segment_size]
        if segment:  # Ensure segment is not empty
            profile = create_archetype_profile(segment)
            dominant = get_dominant_archetypes(profile, limit=2)
            segments.append({
                "period": f"Segment {len(segments) + 1}",
                "dominant": [a.to_dict() for a in dominant],
                "profile": {k.value: v for k, v in profile.items()}
            })
    
    # Analyze transitions between segments
    transitions = []
    for i in range(len(segments) - 1):
        current = segments[i]
        next_segment = segments[i + 1]
        
        # Get primary archetype for each segment
        current_archetype = current["dominant"][0]["category"] if current["dominant"] else None
        next_archetype = next_segment["dominant"][0]["category"] if next_segment["dominant"] else None
        
        # Skip if either segment doesn't have a dominant archetype
        if not current_archetype or not next_archetype:
            continue
            
        # Record the transition
        transitions.append({
            "from": current_archetype,
            "to": next_archetype,
            "from_period": current["period"],
            "to_period": next_segment["period"]
        })
    
    # Calculate stability score (how consistent the dominant archetypes are)
    unique_archetypes = set()
    for segment in segments:
        if segment["dominant"]:
            unique_archetypes.add(segment["dominant"][0]["category"])
    
    stability = 1.0
    if len(segments) > 0:
        stability = 1.0 - (len(unique_archetypes) - 1) / len(segments)
        stability = max(0.0, min(1.0, stability))  # Clamp to 0-1 range
    
    # Identify patterns
    patterns = []
    if stability >= 0.8:
        patterns.append("Stable archetype expression")
    elif stability <= 0.3:
        patterns.append("Rapid archetype transitions")
    
    # Check for oscillation between specific archetypes
    if len(transitions) >= 2:
        oscillation_detected = False
        for i in range(len(transitions) - 1):
            if transitions[i]["from"] == transitions[i+1]["to"] and \
               transitions[i]["to"] == transitions[i+1]["from"]:
                oscillation_detected = True
                patterns.append(f"Oscillation between {transitions[i]['from']} and {transitions[i]['to']}")
                break
    
    return {
        "transitions": transitions,
        "segments": segments,
        "patterns": patterns,
        "stability": round(stability, 2)
    }


@lru_cache(maxsize=32)
def cached_analyze_with_context(user_id: str, 
                             session_id: str, 
                             emotional_states: Tuple[Tuple[str, float, str]], 
                             context_key: str = None) -> Dict[str, Any]:
    """
    Analyze emotional states with context and caching
    
    Args:
        user_id: User identifier for caching
        session_id: Session identifier for caching
        emotional_states: Tuple of (state, intensity, timestamp) tuples
        context_key: Optional additional context for cache key
        
    Returns:
        Dictionary with analysis results including archetypes and transitions
    """
    # Convert tuple format to list of dicts for processing
    states_dicts = [
        {"state": state, "intensity": intensity, "timestamp": timestamp}
        for state, intensity, timestamp in emotional_states
    ]
    
    # Create archetype profile
    profile = create_archetype_profile(states_dicts, time_weighting=True)
    
    # Get dominant archetypes
    dominant = get_dominant_archetypes(profile)
    
    # Analyze transitions if there are enough states
    transitions = {}
    if len(states_dicts) >= 3:
        transitions = analyze_archetype_transitions(states_dicts)
    
    return {
        "profile": {k.value: v for k, v in profile.items()},
        "dominant": [a.to_dict() for a in dominant],
        "transitions": transitions,
        "timestamp": datetime.now().isoformat(),
        "context": context_key
    }
