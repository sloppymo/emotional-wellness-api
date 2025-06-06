"""
SYLVA Adapter System for Emotional Wellness API

This package provides adapters that bridge between the existing symbolic components
(CANOPY, ROOT, MOSS, MARROW) and the SYLVA symbolic processing framework.
"""

from .base import SylvaAdapter, AdapterError, AdapterRegistry
from .canopy_adapter import CanopyAdapter
from .root_adapter import RootAdapter
from .moss_adapter import MossAdapter
from .marrow_adapter import MarrowAdapter
from .factory import SylvaAdapterFactory

__all__ = [
    "SylvaAdapter",
    "AdapterError", 
    "AdapterRegistry",
    "CanopyAdapter",
    "RootAdapter",
    "MossAdapter",
    "MarrowAdapter",
    "SylvaAdapterFactory",
] 