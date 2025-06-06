"""
SYLVA Adapter Package

This package provides standardized adapters for integrating existing symbolic
components with the SYLVA framework.
"""

from .base import (
    SylvaAdapter,
    AdapterError,
    SymbolicData,
    SylvaRequest,
    SylvaResponse,
    AdapterRegistry,
    adapter_registry
)

from .canopy_adapter import (
    CanopyAdapter,
    CanopyInput,
    CanopyOutput
)

from .root_adapter import (
    ROOTAdapter,
    ROOTInput,
    ROOTOutput,
    EmotionalStateData,
    ArchetypeResult,
    PatternResult,
    TransitionResult,
    TimelineResult,
    analyze_emotional_archetypes,
    analyze_journey_patterns
)

from .moss_adapter import (
    MOSSAdapter,
    MOSSInput,
    MOSSOutput,
    assess_crisis,
    emergency_assessment
)

__all__ = [
    # Base adapter components
    "SylvaAdapter",
    "AdapterError", 
    "SymbolicData",
    "SylvaRequest",
    "SylvaResponse",
    "AdapterRegistry",
    "adapter_registry",
    
    # CANOPY adapter
    "CanopyAdapter",
    "CanopyInput",
    "CanopyOutput",
    
    # ROOT adapter
    "ROOTAdapter",
    "ROOTInput", 
    "ROOTOutput",
    "EmotionalStateData",
    "ArchetypeResult",
    "PatternResult",
    "TransitionResult",
    "TimelineResult",
    "analyze_emotional_archetypes",
    "analyze_journey_patterns",
    
    # MOSS adapter
    "MOSSAdapter",
    "MOSSInput",
    "MOSSOutput", 
    "assess_crisis",
    "emergency_assessment"
]

# Register default adapters
def register_default_adapters():
    """Register default SYLVA adapters."""
    from .canopy_adapter import CanopyAdapter
    from .root_adapter import ROOTAdapter
    from .moss_adapter import MOSSAdapter
    
    # Register CANOPY adapter
    canopy_adapter = CanopyAdapter()
    adapter_registry.register("CANOPY", canopy_adapter)
    
    # Register ROOT adapter
    root_adapter = ROOTAdapter()
    adapter_registry.register("ROOT", root_adapter)
    
    # Register MOSS adapter
    moss_adapter = MOSSAdapter()
    adapter_registry.register("MOSS", moss_adapter)

# Auto-register adapters on import
register_default_adapters() 