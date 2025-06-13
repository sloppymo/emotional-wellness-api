"""
CANOPY: Cognitive Analysis and Natural Observation Processing sYstem
A symbolic processing system for emotional wellness analysis.
"""

from typing import Optional
from functools import lru_cache

from .metaphor_extraction import (
    MetaphorExtractor,
    EmotionalMetaphor,
    SymbolicMapping
)
from .processor import CanopyProcessor
from config.settings import get_settings

@lru_cache()
def get_canopy_processor() -> CanopyProcessor:
    """
    Get a cached instance of the CanopyProcessor.
    
    Returns:
        CanopyProcessor: A singleton instance of the CANOPY processor.
    """
    settings = get_settings()
    return CanopyProcessor(
        api_key=settings.ANTHROPIC_API_KEY or "dummy_key",
        symbol_library_path=settings.SYMBOL_LIBRARY_PATH
    )

__all__ = [
    'MetaphorExtractor',
    'EmotionalMetaphor',
    'SymbolicMapping',
    'CanopyProcessor',
    'get_canopy_processor'
]