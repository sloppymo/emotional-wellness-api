"""
Data models for emotional state processing and symbolic mapping.

These models define the core data structures used throughout the API,
including the symbolic representations, emotional states, safety status,
and intervention records.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, UUID4
from uuid import uuid4

class EmotionalMetaphor(BaseModel):
    """Represents an emotional metaphor extracted from text."""
    text: str
    symbol: str
    confidence: float

class SymbolicMapping(BaseModel):
    """Represents a symbolic mapping of emotional content."""
    primary_symbol: str
    archetype: str
    alternative_symbols: List[str]
    valence: float  # -1.0 to 1.0
    arousal: float  # 0.0 to 1.0
    metaphors: List[EmotionalMetaphor]
    confidence: float = 1.0
    timestamp: Optional[datetime] = None

    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.utcnow()
        super().__init__(**data)

class SafetyStatus(BaseModel):
    """Evaluation of potential crisis indicators and safety concerns"""
    level: int = Field(..., description="Safety level: 0=safe, 1=mild concern, 2=moderate, 3=critical")
    risk_score: float = Field(..., description="Overall risk assessment score from 0.0 to 1.0")
    metaphor_risk: float = Field(..., description="Risk score derived from metaphor analysis")
    triggers: List[str] = Field(default_factory=list, description="List of triggers that contributed to risk assessment")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the assessment was made")
    recommended_actions: List[str] = Field(default_factory=list, description="Recommended response actions")

class InterventionRecord(BaseModel):
    """Record of a VELURIA protocol intervention"""
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier for the intervention")
    user_id: str = Field(..., description="User who received the intervention")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the intervention occurred")
    level: int = Field(..., description="VELURIA intervention level applied")
    triggers: List[str] = Field(default_factory=list, description="Triggers that initiated the intervention")
    risk_score: float = Field(..., description="Risk score at time of intervention")
    actions_taken: List[str] = Field(default_factory=list, description="Actions taken during intervention")
    resources_provided: List[str] = Field(default_factory=list, description="Resources provided to the user")
    state_before: int = Field(..., description="VELURIA state before intervention")
    state_after: int = Field(..., description="VELURIA state after intervention")
    intervener_id: Optional[str] = Field(None, description="ID of human intervener (if applicable)")
    outcome: Optional[str] = Field(None, description="Outcome of the intervention")

class EmotionalStateInput(BaseModel):
    """Input for emotional state processing endpoint"""
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    text: str = Field(..., description="User's emotional text input")
    biomarkers: Optional[Dict[str, float]] = Field(None, description="Optional biometric measurements")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context information")

class EmotionalStateResponse(BaseModel):
    """Response from emotional state processing endpoint"""
    symbolic_anchor: str = Field(..., description="Primary symbolic anchor identified")
    alternatives: List[str] = Field(..., description="Alternative symbolic representations")
    archetype: str = Field(..., description="Jungian archetype identified")
    drift_index: float = Field(..., description="Symbolic drift from previous states")
    safety_status: Dict[str, Any] = Field(..., description="Current safety assessment")
    content: Optional[Dict[str, Any]] = Field(None, description="Additional content for response")

class EmotionalState(BaseModel):
    """Complete emotional state record for storage"""
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier")
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the state was recorded")
    valence: float = Field(..., description="Emotional valence from -1.0 to 1.0")
    arousal: float = Field(..., description="Emotional arousal from 0.0 to 1.0")
    primary_symbol: str = Field(..., description="Primary symbolic representation")
    alternative_symbols: List[str] = Field(..., description="Alternative symbolic representations")
    archetype: str = Field(..., description="Identified archetype")
    drift_index: float = Field(..., description="Calculated drift from previous states")
    safety_level: int = Field(..., description="Safety level assessment")
    input_text_hash: str = Field(..., description="Hashed version of input text for reference")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context and metadata")
    
    class Config:
        orm_mode = True
