"""
Adapters for integrating symbolic processing with other subsystems.
"""

from .sylva_adapter import SylvaAdapter, SylvaContext, ProcessingResult

__all__ = ['SylvaAdapter', 'SylvaContext', 'ProcessingResult']