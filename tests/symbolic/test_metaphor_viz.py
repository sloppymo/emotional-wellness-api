"""
Tests for the metaphor visualization module.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, List, Any

from src.symbolic.visualization.metaphor_viz import MetaphorVisualizer
from src.models.emotional_state import SymbolicMapping, EmotionalMetaphor

# Test data
SAMPLE_MAPPING = SymbolicMapping(
    primary_symbol="water",
    archetype="self",
    alternative_symbols=["river", "ocean", "flow"],
    valence=0.3,
    arousal=0.4,
    metaphors=[
        EmotionalMetaphor(text="flowing freely", symbol="water", confidence=0.9),
        EmotionalMetaphor(text="deep as the ocean", symbol="water", confidence=0.85)
    ],
    confidence=0.9,
    timestamp=datetime.now()
)

SAMPLE_HISTORY = [
    SymbolicMapping(
        primary_symbol="fire",
        archetype="hero",
        alternative_symbols=["flame", "light"],
        valence=0.7,
        arousal=0.8,
        metaphors=[
            EmotionalMetaphor(text="burning bright", symbol="fire", confidence=0.9)
        ],
        confidence=0.9,
        timestamp=datetime.now() - timedelta(days=2)
    ),
    SymbolicMapping(
        primary_symbol="path",
        archetype="explorer",
        alternative_symbols=["road", "journey"],
        valence=0.5,
        arousal=0.6,
        metaphors=[
            EmotionalMetaphor(text="finding my way", symbol="path", confidence=0.85)
        ],
        confidence=0.85,
        timestamp=datetime.now() - timedelta(days=1)
    ),
    SAMPLE_MAPPING
]

SAMPLE_CULTURAL_INTERPRETATIONS = {
    "context": "western",
    "primary_symbol": {
        "cultural_meaning": "purification and emotional depth",
        "cultural_associations": ["cleansing", "healing", "unconscious"],
        "taboos": [],
        "alternatives": ["river", "ocean", "rain"]
    },
    "archetype": {
        "cultural_equivalent": "self",
        "cultural_variations": ["healer", "sage"]
    }
}

@pytest.fixture
def visualizer():
    """Create a MetaphorVisualizer instance."""
    return MetaphorVisualizer()

def test_network_visualization_basic(visualizer):
    """Test basic network visualization creation."""
    viz_data = visualizer.create_network_visualization(SAMPLE_MAPPING)
    
    assert viz_data["format"] == "network"
    assert len(viz_data["elements"]) > 0
    assert len(viz_data["relationships"]) > 0
    assert "metadata" in viz_data
    
    # Check primary symbol node
    primary_node = next(
        (node for node in viz_data["elements"] if node["id"] == "primary"),
        None
    )
    assert primary_node is not None
    assert primary_node["label"] == "water"
    assert primary_node["type"] == "symbol"
    
    # Check metaphor nodes
    metaphor_nodes = [
        node for node in viz_data["elements"]
        if node["type"] == "metaphor"
    ]
    assert len(metaphor_nodes) == len(SAMPLE_MAPPING.metaphors)

def test_network_visualization_alternatives(visualizer):
    """Test network visualization with alternatives."""
    viz_data = visualizer.create_network_visualization(
        SAMPLE_MAPPING,
        include_alternatives=True
    )
    
    # Check alternative symbol nodes
    alt_nodes = [
        node for node in viz_data["elements"]
        if node["type"] == "alternative"
    ]
    assert len(alt_nodes) == len(SAMPLE_MAPPING.alternative_symbols)
    
    # Check relationships
    alt_relationships = [
        rel for rel in viz_data["relationships"]
        if rel["type"] == "alternative"
    ]
    assert len(alt_relationships) == len(SAMPLE_MAPPING.alternative_symbols)

def test_temporal_visualization(visualizer):
    """Test temporal visualization creation."""
    viz_data = visualizer.create_temporal_visualization(SAMPLE_HISTORY)
    
    assert viz_data["format"] == "temporal"
    assert len(viz_data["elements"]) == len(SAMPLE_HISTORY)
    assert "metadata" in viz_data
    assert viz_data["metadata"]["num_points"] == len(SAMPLE_HISTORY)
    
    # Check elements
    for element in viz_data["elements"]:
        assert "timestamp" in element
        assert "symbol" in element
        assert "archetype" in element
        assert "valence" in element
        assert "arousal" in element
        assert "color" in element
        assert "archetype_color" in element

def test_cultural_visualization(visualizer):
    """Test cultural visualization creation."""
    viz_data = visualizer.create_cultural_visualization(
        SAMPLE_MAPPING,
        SAMPLE_CULTURAL_INTERPRETATIONS
    )
    
    assert viz_data["format"] == "cultural"
    assert len(viz_data["elements"]) > 0
    assert len(viz_data["relationships"]) > 0
    
    # Check original symbol node
    original_node = next(
        (node for node in viz_data["elements"] if node["id"] == "original"),
        None
    )
    assert original_node is not None
    assert original_node["label"] == "water"
    
    # Check cultural meaning node
    meaning_node = next(
        (node for node in viz_data["elements"] if node["id"] == "meaning"),
        None
    )
    assert meaning_node is not None
    assert meaning_node["label"] == SAMPLE_CULTURAL_INTERPRETATIONS["primary_symbol"]["cultural_meaning"]
    
    # Check associations
    assoc_nodes = [
        node for node in viz_data["elements"]
        if node["type"] == "association"
    ]
    assert len(assoc_nodes) == len(
        SAMPLE_CULTURAL_INTERPRETATIONS["primary_symbol"]["cultural_associations"]
    )

def test_archetype_constellation(visualizer):
    """Test archetype constellation visualization."""
    related_archetypes = ["hero", "mentor", "shadow"]
    viz_data = visualizer.create_archetype_constellation(
        SAMPLE_MAPPING,
        related_archetypes
    )
    
    assert viz_data["format"] == "constellation"
    assert len(viz_data["elements"]) == len(related_archetypes) + 1  # +1 for primary
    assert len(viz_data["relationships"]) == len(related_archetypes)
    
    # Check primary archetype node
    primary_node = next(
        (node for node in viz_data["elements"] if node["id"] == "primary"),
        None
    )
    assert primary_node is not None
    assert primary_node["label"] == SAMPLE_MAPPING.archetype
    
    # Check related archetype nodes
    related_nodes = [
        node for node in viz_data["elements"]
        if node["type"] == "archetype" and node["id"] != "primary"
    ]
    assert len(related_nodes) == len(related_archetypes)
    assert all(node["label"] in related_archetypes for node in related_nodes)

def test_color_consistency(visualizer):
    """Test color consistency across visualizations."""
    network_viz = visualizer.create_network_visualization(SAMPLE_MAPPING)
    temporal_viz = visualizer.create_temporal_visualization([SAMPLE_MAPPING])
    cultural_viz = visualizer.create_cultural_visualization(
        SAMPLE_MAPPING,
        SAMPLE_CULTURAL_INTERPRETATIONS
    )
    
    # Get color of water symbol in each visualization
    network_color = next(
        (node["color"] for node in network_viz["elements"]
         if node["id"] == "primary"),
        None
    )
    temporal_color = temporal_viz["elements"][0]["color"]
    cultural_color = next(
        (node["color"] for node in cultural_viz["elements"]
         if node["id"] == "original"),
        None
    )
    
    # Colors should be consistent
    assert network_color == temporal_color == cultural_color
    assert network_color == visualizer.color_map["water"]

def test_metadata_completeness(visualizer):
    """Test completeness of metadata in visualizations."""
    network_viz = visualizer.create_network_visualization(SAMPLE_MAPPING)
    temporal_viz = visualizer.create_temporal_visualization(SAMPLE_HISTORY)
    cultural_viz = visualizer.create_cultural_visualization(
        SAMPLE_MAPPING,
        SAMPLE_CULTURAL_INTERPRETATIONS
    )
    constellation_viz = visualizer.create_archetype_constellation(
        SAMPLE_MAPPING,
        ["hero", "mentor"]
    )
    
    # Check network metadata
    assert "timestamp" in network_viz["metadata"]
    assert "primary_symbol" in network_viz["metadata"]
    assert "archetype" in network_viz["metadata"]
    
    # Check temporal metadata
    assert "start_time" in temporal_viz["metadata"]
    assert "end_time" in temporal_viz["metadata"]
    assert "num_points" in temporal_viz["metadata"]
    
    # Check cultural metadata
    assert "primary_symbol" in cultural_viz["metadata"]
    assert "cultural_context" in cultural_viz["metadata"]
    
    # Check constellation metadata
    assert "primary_archetype" in constellation_viz["metadata"]
    assert "num_related" in constellation_viz["metadata"]

def test_relationship_validity(visualizer):
    """Test validity of relationships in visualizations."""
    network_viz = visualizer.create_network_visualization(SAMPLE_MAPPING)
    cultural_viz = visualizer.create_cultural_visualization(
        SAMPLE_MAPPING,
        SAMPLE_CULTURAL_INTERPRETATIONS
    )
    
    # Check network relationships
    for rel in network_viz["relationships"]:
        assert "source" in rel
        assert "target" in rel
        assert "type" in rel
        assert "weight" in rel
        assert 0.0 <= rel["weight"] <= 1.0
        
        # Verify source and target exist
        assert any(node["id"] == rel["source"] for node in network_viz["elements"])
        assert any(node["id"] == rel["target"] for node in network_viz["elements"])
    
    # Check cultural relationships
    for rel in cultural_viz["relationships"]:
        assert "source" in rel
        assert "target" in rel
        assert "type" in rel
        assert "weight" in rel
        assert 0.0 <= rel["weight"] <= 1.0
        
        # Verify source and target exist
        assert any(node["id"] == rel["source"] for node in cultural_viz["elements"])
        assert any(node["id"] == rel["target"] for node in cultural_viz["elements"]) 