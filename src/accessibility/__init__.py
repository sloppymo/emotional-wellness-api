"""
Accessibility Module for Emotional Wellness API

This module provides comprehensive accessibility features for differently abled users,
ensuring inclusive access to emotional wellness services in compliance with WCAG 2.1 
and section 508 standards.
"""

from src.accessibility.config import AccessibilityConfig
from src.accessibility.adapters import get_accessibility_adapter
from src.accessibility.preferences import UserPreferences

__all__ = ['AccessibilityConfig', 'get_accessibility_adapter', 'UserPreferences']
