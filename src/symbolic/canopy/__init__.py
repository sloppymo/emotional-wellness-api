"""
CANOPY: Enhanced metaphor extraction and symbolic processing package.
"""

from .metaphor_extraction import (
    EnhancedMetaphorExtractor,
    MetaphorCache,
    FallbackMetaphorExtractor,
    PromptTemplates,
    MetaphorDomain,
    MetaphorTheme
)

__all__ = [
    "EnhancedMetaphorExtractor",
    "MetaphorCache", 
    "FallbackMetaphorExtractor",
    "PromptTemplates",
    "MetaphorDomain",
    "MetaphorTheme"
] 