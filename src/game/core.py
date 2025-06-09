"""
Years of Lead - Core Game State and Logic

This module provides the main GameState class and core game mechanics
for the Years of Lead insurgency simulator.
"""

from enum import Enum
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import random

# Import enhanced mission system components
from .mission_system import Mission as EnhancedMission, MissionType as EnhancedMissionType, MissionComplexity
from .mission_executor import MissionExecutor
from .legal_system import LegalSystem

# Import enhanced mission system components
from .mission_system import Mission as EnhancedMission, MissionType as EnhancedMissionType, MissionComplexity
from .mission_executor import MissionExecutor
from .legal_system import LegalSystem


class GamePhase(Enum): 