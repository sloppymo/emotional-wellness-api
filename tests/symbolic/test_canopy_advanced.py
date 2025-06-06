"""
Tests for advanced CANOPY features including pattern analysis,
cultural adaptations, and visualization capabilities.
"""

import pytest
from datetime import datetime, timedelta
import json
from unittest.mock import Mock, patch, AsyncMock

from src.symbolic.adapters.canopy_adapter import CanopyAdapter
from src.symbolic.canopy import CanopyProcessor
from src.models.emotional_state import SymbolicMapping, EmotionalMetaphor

# Test data
SAMPLE_HISTORY = [
    SymbolicMapping(
        primary_symbol="water",
        archetype="shadow",
        alternative_symbols=["ocean", "depth"],
        valence=-0.7,
        arousal=0.8,
        metaphors=[
            EmotionalMetaphor(text="drowning", symbol="water", confidence=0.9)
        ],
        confidence=0.9,
        timestamp=datetime.now() - timedelta(days=3)
    ),
    SymbolicMapping(
        primary_symbol="fire",
        archetype="hero",
        alternative_symbols=["flame", "light"],
        valence=0.6,
        arousal=0.7,
        metaphors=[
            EmotionalMetaphor(text="burning bright", symbol="fire", confidence=0.85)
        ],
        confidence=0.85,
        timestamp=datetime.now() - timedelta(days=2)
    ),
    SymbolicMapping(
        primary_symbol="path",
        archetype="explorer",
        alternative_symbols=["road", "journey"],
        valence=0.3,
        arousal=0.4,
        metaphors=[
            EmotionalMetaphor(text="finding my way", symbol="path", confidence=0.95)
        ],
        confidence=0.95,
        timestamp=datetime.now() - timedelta(days=1)
    )
]

@pytest.fixture
def canopy_adapter():
    """Create a CANOPY adapter instance for testing"""
    adapter = CanopyAdapter()
    adapter._symbolic_history["test_user"] = SAMPLE_HISTORY
    return adapter

@pytest.mark.asyncio
async def test_pattern_analysis(canopy_adapter):
    """Test pattern analysis functionality"""
    current_mapping = SymbolicMapping(
        primary_symbol="mountain",
        archetype="hero",
        alternative_symbols=["peak", "climb"],
        valence=0.5,
        arousal=0.6,
        metaphors=[
            EmotionalMetaphor(text="climbing higher", symbol="mountain", confidence=0.9)
        ],
        confidence=0.9
    )
    
    patterns = await canopy_adapter._analyze_patterns(current_mapping, "test_user")
    
    # Test recurring symbols analysis
    assert "recurring_symbols" in patterns
    assert len(patterns["recurring_symbols"]) > 0
    assert all(isinstance(item["count"], int) for item in patterns["recurring_symbols"])
    
    # Test archetypal progression
    assert "archetypal_progression" in patterns
    assert "sequence" in patterns["archetypal_progression"]
    assert "current" in patterns["archetypal_progression"]
    assert "suggested_next" in patterns["archetypal_progression"]
    assert patterns["archetypal_progression"]["current"] == "hero"
    
    # Test symbol clusters
    assert "symbol_clusters" in patterns
    clusters = patterns["symbol_clusters"]
    assert len(clusters) > 0
    assert all("name" in cluster and "symbols" in cluster for cluster in clusters)
    
    # Test emotional patterns
    assert "emotional_patterns" in patterns
    assert "valence_trend" in patterns["emotional_patterns"]
    assert "arousal_trend" in patterns["emotional_patterns"]
    assert all(key in patterns["emotional_patterns"]["valence_trend"] 
              for key in ["mean", "variance", "direction"])

@pytest.mark.asyncio
async def test_cultural_adaptations(canopy_adapter):
    """Test cultural adaptation functionality"""
    mapping = SymbolicMapping(
        primary_symbol="water",
        archetype="self",
        alternative_symbols=["river", "flow"],
        valence=0.4,
        arousal=0.3,
        metaphors=[
            EmotionalMetaphor(text="flowing like water", symbol="water", confidence=0.9)
        ],
        confidence=0.9
    )
    
    # Test with different cultural contexts
    contexts = ["western", "eastern", "indigenous"]
    for context in contexts:
        adaptations = await canopy_adapter._apply_cultural_adaptations(mapping, context)
        
        assert "primary_symbol" in adaptations
        assert "archetype" in adaptations
        assert adaptations["primary_symbol"]["original"] == "water"
        assert isinstance(adaptations["primary_symbol"]["cultural_meaning"], str)
        assert isinstance(adaptations["primary_symbol"]["cultural_associations"], list)
        assert isinstance(adaptations["primary_symbol"]["alternatives"], list)
    
    # Test caching
    cache_key = f"water:western"
    assert cache_key in canopy_adapter._cultural_cache

@pytest.mark.asyncio
async def test_visualization_generation(canopy_adapter):
    """Test visualization data generation"""
    mapping = SymbolicMapping(
        primary_symbol="path",
        archetype="hero",
        alternative_symbols=["journey", "quest"],
        valence=0.5,
        arousal=0.6,
        metaphors=[
            EmotionalMetaphor(text="walking the path", symbol="path", confidence=0.9),
            EmotionalMetaphor(text="finding direction", symbol="path", confidence=0.8)
        ],
        confidence=0.9
    )
    
    # Test network visualization
    network_viz = await canopy_adapter._generate_visualization(mapping, "network")
    assert network_viz["format"] == "network"
    assert len(network_viz["elements"]) == 3  # Primary + 2 metaphors
    assert len(network_viz["relationships"]) == 2  # Two metaphor relationships
    
    # Test temporal visualization
    temporal_viz = await canopy_adapter._generate_visualization(mapping, "temporal")
    assert temporal_viz["format"] == "temporal"
    assert len(temporal_viz["elements"]) == 1
    assert all(key in temporal_viz["elements"][0] 
              for key in ["timestamp", "symbol", "archetype", "valence", "arousal"])

@pytest.mark.asyncio
async def test_archetype_prediction(canopy_adapter):
    """Test archetype prediction functionality"""
    # Test with empty sequence
    assert canopy_adapter._predict_next_archetype([]) == "self"
    
    # Test with single archetype
    assert isinstance(canopy_adapter._predict_next_archetype(["hero"]), str)
    
    # Test with sequence
    sequence = ["hero", "shadow", "mentor", "hero"]
    prediction = canopy_adapter._predict_next_archetype(sequence)
    assert isinstance(prediction, str)
    assert prediction in ["hero", "shadow", "mentor", "self"]  # Common transitions

@pytest.mark.asyncio
async def test_symbol_clustering(canopy_adapter):
    """Test symbol clustering functionality"""
    history = [
        SymbolicMapping(
            primary_symbol="water",
            archetype="self",
            alternative_symbols=[],
            valence=0.0,
            arousal=0.0,
            metaphors=[],
            confidence=1.0
        ),
        SymbolicMapping(
            primary_symbol="fire",
            archetype="self",
            alternative_symbols=[],
            valence=0.0,
            arousal=0.0,
            metaphors=[],
            confidence=1.0
        ),
        SymbolicMapping(
            primary_symbol="path",
            archetype="self",
            alternative_symbols=[],
            valence=0.0,
            arousal=0.0,
            metaphors=[],
            confidence=1.0
        )
    ]
    
    clusters = canopy_adapter._identify_symbol_clusters(history)
    assert len(clusters) == 2  # Should find both elemental and journey clusters
    
    # Verify cluster structure
    for cluster in clusters:
        assert "name" in cluster
        assert "symbols" in cluster
        assert "count" in cluster
        assert cluster["count"] > 0

@pytest.mark.asyncio
async def test_emotional_pattern_analysis(canopy_adapter):
    """Test emotional pattern analysis"""
    history = [
        SymbolicMapping(
            primary_symbol="test",
            archetype="self",
            alternative_symbols=[],
            valence=-0.5,  # Increasing trend
            arousal=0.8,   # Decreasing trend
            metaphors=[],
            confidence=1.0
        ),
        SymbolicMapping(
            primary_symbol="test",
            archetype="self",
            alternative_symbols=[],
            valence=0.0,
            arousal=0.5,
            metaphors=[],
            confidence=1.0
        ),
        SymbolicMapping(
            primary_symbol="test",
            archetype="self",
            alternative_symbols=[],
            valence=0.5,
            arousal=0.2,
            metaphors=[],
            confidence=1.0
        )
    ]
    
    patterns = canopy_adapter._analyze_emotional_patterns(history)
    
    # Check valence analysis
    assert patterns["valence_trend"]["direction"] == "increasing"
    assert -1.0 <= patterns["valence_trend"]["mean"] <= 1.0
    assert patterns["valence_trend"]["variance"] >= 0
    
    # Check arousal analysis
    assert patterns["arousal_trend"]["direction"] == "decreasing"
    assert 0.0 <= patterns["arousal_trend"]["mean"] <= 1.0
    assert patterns["arousal_trend"]["variance"] >= 0

@pytest.mark.asyncio
async def test_cultural_symbol_retrieval(canopy_adapter):
    """Test cultural symbol retrieval"""
    symbols = await canopy_adapter._get_cultural_symbols("western")
    
    assert "water" in symbols
    assert "fire" in symbols
    
    # Check symbol structure
    for symbol_data in symbols.values():
        assert "cultural_meaning" in symbol_data
        assert "cultural_associations" in symbol_data
        assert "taboos" in symbol_data
        assert "alternatives" in symbol_data
        assert isinstance(symbol_data["cultural_associations"], list)
        assert isinstance(symbol_data["alternatives"], list)

@pytest.mark.asyncio
async def test_integration_flow(canopy_adapter):
    """Test the complete integration flow with all features"""
    request = Mock()
    request.user_id = "test_user"
    request.input_data = {
        "text": "I feel like I'm climbing a mountain of challenges",
        "cultural_context": "western",
        "visualization_format": "network"
    }
    
    result = await canopy_adapter._process_request(request)
    
    # Verify all advanced features are present
    assert "pattern_analysis" in result
    assert "cultural_interpretations" in result
    assert "visualization_data" in result
    
    # Verify pattern analysis
    assert all(key in result["pattern_analysis"] 
              for key in ["recurring_symbols", "archetypal_progression", 
                         "symbol_clusters", "emotional_patterns"])
    
    # Verify cultural interpretations
    if result["cultural_interpretations"]:
        assert "primary_symbol" in result["cultural_interpretations"]
        assert "archetype" in result["cultural_interpretations"]
    
    # Verify visualization
    if result["visualization_data"]:
        assert "format" in result["visualization_data"]
        assert "elements" in result["visualization_data"]
        assert "relationships" in result["visualization_data"] 