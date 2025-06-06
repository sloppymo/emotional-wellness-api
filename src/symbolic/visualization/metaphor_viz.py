"""
Visualization module for CANOPY metaphor and symbol visualization.

This module provides tools for creating various visualizations of
metaphorical and symbolic content, including:
1. Network diagrams of symbol relationships
2. Temporal evolution of symbols
3. Archetypal constellations
4. Cultural symbol mappings
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from models.emotional_state import SymbolicMapping, EmotionalMetaphor

class MetaphorVisualizer:
    """Generator for metaphor and symbol visualizations."""
    
    def __init__(self):
        """Initialize the visualizer."""
        self.color_map = {
            "water": "#4A90E2",
            "fire": "#E25B4A",
            "earth": "#8B572A",
            "air": "#B8E986",
            "path": "#9013FE",
            "mountain": "#50E3C2",
            "light": "#F8E71C",
            "shadow": "#4A4A4A"
        }
        
        self.archetype_colors = {
            "hero": "#FF6B6B",
            "shadow": "#4A4A4A",
            "anima": "#FF9ECD",
            "animus": "#4A90E2",
            "mentor": "#F8E71C",
            "trickster": "#9013FE",
            "self": "#50E3C2"
        }
    
    def create_network_visualization(
        self,
        mapping: SymbolicMapping,
        include_alternatives: bool = True
    ) -> Dict[str, Any]:
        """
        Create a network visualization of symbols and their relationships.
        
        Args:
            mapping: The symbolic mapping to visualize
            include_alternatives: Whether to include alternative symbols
            
        Returns:
            Dictionary containing visualization data
        """
        viz_data = {
            "format": "network",
            "elements": [],
            "relationships": [],
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "primary_symbol": mapping.primary_symbol,
                "archetype": mapping.archetype
            }
        }
        
        # Add primary symbol node
        primary_node = {
            "id": "primary",
            "type": "symbol",
            "label": mapping.primary_symbol,
            "size": 1.0,
            "color": self.color_map.get(mapping.primary_symbol, "#7A7A7A")
        }
        viz_data["elements"].append(primary_node)
        
        # Add archetype node
        archetype_node = {
            "id": "archetype",
            "type": "archetype",
            "label": mapping.archetype,
            "size": 0.8,
            "color": self.archetype_colors.get(mapping.archetype, "#7A7A7A")
        }
        viz_data["elements"].append(archetype_node)
        
        # Connect primary symbol to archetype
        viz_data["relationships"].append({
            "source": "primary",
            "target": "archetype",
            "type": "expresses",
            "weight": mapping.confidence
        })
        
        # Add metaphor nodes
        for i, metaphor in enumerate(mapping.metaphors):
            node = {
                "id": f"metaphor_{i}",
                "type": "metaphor",
                "label": metaphor.text,
                "size": metaphor.confidence,
                "color": self.color_map.get(metaphor.symbol, "#7A7A7A")
            }
            viz_data["elements"].append(node)
            
            # Connect to primary symbol
            viz_data["relationships"].append({
                "source": "primary",
                "target": f"metaphor_{i}",
                "type": "expresses",
                "weight": metaphor.confidence
            })
        
        # Add alternative symbols if requested
        if include_alternatives:
            for i, alt_symbol in enumerate(mapping.alternative_symbols):
                node = {
                    "id": f"alt_{i}",
                    "type": "alternative",
                    "label": alt_symbol,
                    "size": 0.6,
                    "color": self.color_map.get(alt_symbol, "#7A7A7A")
                }
                viz_data["elements"].append(node)
                
                # Connect to primary symbol
                viz_data["relationships"].append({
                    "source": "primary",
                    "target": f"alt_{i}",
                    "type": "alternative",
                    "weight": 0.5
                })
        
        return viz_data
    
    def create_temporal_visualization(
        self,
        history: List[SymbolicMapping]
    ) -> Dict[str, Any]:
        """
        Create a temporal visualization of symbol evolution.
        
        Args:
            history: List of symbolic mappings in chronological order
            
        Returns:
            Dictionary containing visualization data
        """
        viz_data = {
            "format": "temporal",
            "elements": [],
            "metadata": {
                "start_time": history[0].timestamp.isoformat() if history else None,
                "end_time": history[-1].timestamp.isoformat() if history else None,
                "num_points": len(history)
            }
        }
        
        for mapping in history:
            element = {
                "timestamp": mapping.timestamp.isoformat(),
                "symbol": mapping.primary_symbol,
                "archetype": mapping.archetype,
                "valence": mapping.valence,
                "arousal": mapping.arousal,
                "color": self.color_map.get(mapping.primary_symbol, "#7A7A7A"),
                "archetype_color": self.archetype_colors.get(mapping.archetype, "#7A7A7A")
            }
            viz_data["elements"].append(element)
        
        return viz_data
    
    def create_cultural_visualization(
        self,
        mapping: SymbolicMapping,
        cultural_interpretations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a visualization of cultural symbol interpretations.
        
        Args:
            mapping: The symbolic mapping to visualize
            cultural_interpretations: Cultural interpretation data
            
        Returns:
            Dictionary containing visualization data
        """
        viz_data = {
            "format": "cultural",
            "elements": [],
            "relationships": [],
            "metadata": {
                "primary_symbol": mapping.primary_symbol,
                "cultural_context": cultural_interpretations.get("context", "unknown")
            }
        }
        
        # Add original symbol node
        original_node = {
            "id": "original",
            "type": "symbol",
            "label": mapping.primary_symbol,
            "size": 1.0,
            "color": self.color_map.get(mapping.primary_symbol, "#7A7A7A")
        }
        viz_data["elements"].append(original_node)
        
        # Add cultural meaning node
        if "cultural_meaning" in cultural_interpretations.get("primary_symbol", {}):
            meaning_node = {
                "id": "meaning",
                "type": "meaning",
                "label": cultural_interpretations["primary_symbol"]["cultural_meaning"],
                "size": 0.8,
                "color": "#9B9B9B"
            }
            viz_data["elements"].append(meaning_node)
            
            viz_data["relationships"].append({
                "source": "original",
                "target": "meaning",
                "type": "means",
                "weight": 1.0
            })
        
        # Add cultural associations
        for i, assoc in enumerate(
            cultural_interpretations.get("primary_symbol", {}).get("cultural_associations", [])
        ):
            node = {
                "id": f"assoc_{i}",
                "type": "association",
                "label": assoc,
                "size": 0.6,
                "color": "#B8E986"
            }
            viz_data["elements"].append(node)
            
            viz_data["relationships"].append({
                "source": "original",
                "target": f"assoc_{i}",
                "type": "associates",
                "weight": 0.7
            })
        
        # Add taboos if any
        for i, taboo in enumerate(
            cultural_interpretations.get("primary_symbol", {}).get("taboos", [])
        ):
            node = {
                "id": f"taboo_{i}",
                "type": "taboo",
                "label": taboo,
                "size": 0.6,
                "color": "#E25B4A"
            }
            viz_data["elements"].append(node)
            
            viz_data["relationships"].append({
                "source": "original",
                "target": f"taboo_{i}",
                "type": "avoids",
                "weight": 0.7
            })
        
        return viz_data
    
    def create_archetype_constellation(
        self,
        mapping: SymbolicMapping,
        related_archetypes: List[str]
    ) -> Dict[str, Any]:
        """
        Create a visualization of archetypal relationships.
        
        Args:
            mapping: The symbolic mapping to visualize
            related_archetypes: List of related archetypal patterns
            
        Returns:
            Dictionary containing visualization data
        """
        viz_data = {
            "format": "constellation",
            "elements": [],
            "relationships": [],
            "metadata": {
                "primary_archetype": mapping.archetype,
                "num_related": len(related_archetypes)
            }
        }
        
        # Add primary archetype node
        primary_node = {
            "id": "primary",
            "type": "archetype",
            "label": mapping.archetype,
            "size": 1.0,
            "color": self.archetype_colors.get(mapping.archetype, "#7A7A7A")
        }
        viz_data["elements"].append(primary_node)
        
        # Add related archetypes
        for i, archetype in enumerate(related_archetypes):
            node = {
                "id": f"related_{i}",
                "type": "archetype",
                "label": archetype,
                "size": 0.7,
                "color": self.archetype_colors.get(archetype, "#7A7A7A")
            }
            viz_data["elements"].append(node)
            
            viz_data["relationships"].append({
                "source": "primary",
                "target": f"related_{i}",
                "type": "relates",
                "weight": 0.6
            })
        
        return viz_data 