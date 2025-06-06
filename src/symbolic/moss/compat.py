"""
Compatibility module for MOSS package.

This module provides backward compatibility for renamed types and functions.
"""

from .crisis_classifier import CrisisSeverity

# Re-export CrisisSeverity as RiskSeverity for backward compatibility
RiskSeverity = CrisisSeverity

__all__ = ["RiskSeverity"] 