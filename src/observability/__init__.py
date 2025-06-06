"""
Observability package for the Emotional Wellness API.

Provides telemetry, metrics, and distributed tracing functionality.
"""

from .telemetry import (
    get_telemetry_manager,
    ComponentName,
    record_span
)

__all__ = [
    "get_telemetry_manager",
    "ComponentName", 
    "record_span"
]
