"""
Models for the SYLVA framework.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime

from src.symbolic.canopy.metaphor_extraction import SymbolicMapping

@dataclass
class SylvaContext:
    """Context for SYLVA processing."""
    user_id: str
    session_id: str
    timestamp: datetime
    processing_flags: Dict[str, Any]

@dataclass
class ProcessingResult:
    """Result of SYLVA processing."""
    success: bool
    output: Optional[SymbolicMapping] = None
    error: Optional[str] = None
    processing_time: float = 0.0 