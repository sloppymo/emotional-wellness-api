"""
VELURIA: Virtual Emotional Learning and Understanding Response Intervention Architecture

This package provides the core intervention protocol framework for the SYLVA
emotional wellness platform, enabling structured, multi-step crisis interventions.
"""

from .intervention_protocol import (
    InterventionProtocol,
    ProtocolStep,
    ProtocolState,
    ProtocolStatus,
    ActionType,
    VeluriaProtocolExecutor,
    ProtocolExecutionError,
    InterventionAction
)
from .protocol_library import get_protocol_library
from .escalation_manager import (
    EscalationManager,
    EscalationRequest,
    EscalationLevel,
    get_default_escalation_manager
)

__all__ = [
    "InterventionProtocol",
    "ProtocolStep",
    "ProtocolState",
    "ProtocolStatus",
    "ActionType",
    "InterventionAction",
    "VeluriaProtocolExecutor",
    "ProtocolExecutionError",
    "EscalationManager",
    "EscalationRequest",
    "EscalationLevel",
    "get_default_escalation_manager",
    "get_protocol_library",
] 