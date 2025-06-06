"""
CANOPY: Cognitive Analysis and Natural Observation Processing sYstem
A symbolic processing system for emotional wellness analysis.
"""

from .metaphor_extraction import (
    MetaphorExtractor,
    EmotionalMetaphor,
    SymbolicMapping
)
from .processor import CanopyProcessor

__all__ = [
    'MetaphorExtractor',
    'EmotionalMetaphor',
    'SymbolicMapping',
    'CanopyProcessor'
]