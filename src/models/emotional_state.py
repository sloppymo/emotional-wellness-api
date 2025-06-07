"""
Emotional state models.

This module defines the data models for emotional state tracking and symbolic mappings.
"""

#      ▄████▄
#     ▄██████▄
#    ▄██▄██▄██▄
#    ███▀██▀███
#    ▀███████▀
#      ▀█ █▀
#   HELLO WORLD

from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, UUID4
from uuid import uuid4


class EmotionalMetaphor(BaseModel):
    """Represents an emotional metaphor extracted from text - when people say "I feel like drowning" """

    text: str  # the original metaphor text
    symbol: str  # simplified symbol we assign to it
    confidence: float  # how sure we are this is actually a metaphor (0-1)


class SymbolicMapping(BaseModel):
    """Represents a symbolic mapping of emotional content - the heart of the system"""

    primary_symbol: str  # main symbol we think represents their state
    archetype: str  # jungian archetype (hero, shadow, etc)
    alternative_symbols: List[str]  # other symbols that could fit
    valence: float  # happy/sad scale from -1.0 to 1.0
    arousal: float  # energy level from 0.0 to 1.0
    metaphors: List[EmotionalMetaphor]  # metaphors we found in their text
    confidence: float = 1.0  # how confident we are overall
    timestamp: Optional[datetime] = None  # when we processed this

    def __init__(self, **data):
        # auto-timestamp if not provided - useful for tracking
        if "timestamp" not in data:
            data["timestamp"] = datetime.utcnow()
        super().__init__(**data)


class SafetyStatus(BaseModel):
    """Evaluation of potential crisis indicators and safety concerns - the important stuff"""

    level: int = Field(
        ..., description="Safety level: 0=safe, 1=mild concern, 2=moderate, 3=critical"
    )  # how worried we should be
    risk_score: float = Field(
        ..., description="Overall risk assessment score from 0.0 to 1.0"
    )  # computed risk level
    metaphor_risk: float = Field(
        ..., description="Risk score derived from metaphor analysis"
    )  # risk from their metaphors specifically
    triggers: List[str] = Field(
        default_factory=list, description="List of triggers that contributed to risk assessment"
    )  # what set off the alarms
    timestamp: datetime = Field(
        default_factory=datetime.now, description="When the assessment was made"
    )  # for audit trails
    recommended_actions: List[str] = Field(
        default_factory=list, description="Recommended response actions"
    )  # what to do about it


class InterventionRecord(BaseModel):
    """Record of a VELURIA protocol intervention - when we actually helped someone"""

    id: str = Field(
        default_factory=lambda: str(uuid4()), description="Unique identifier for the intervention"
    )
    user_id: str = Field(..., description="User who received the intervention")  # who got help
    timestamp: datetime = Field(
        default_factory=datetime.now, description="When the intervention occurred"
    )  # when we helped
    level: int = Field(
        ..., description="VELURIA intervention level applied"
    )  # how serious the intervention was
    triggers: List[str] = Field(
        default_factory=list, description="Triggers that initiated the intervention"
    )  # what made us act
    risk_score: float = Field(
        ..., description="Risk score at time of intervention"
    )  # how bad it was
    actions_taken: List[str] = Field(
        default_factory=list, description="Actions taken during intervention"
    )  # what we did
    resources_provided: List[str] = Field(
        default_factory=list, description="Resources provided to the user"
    )  # what help we gave
    state_before: int = Field(
        ..., description="VELURIA state before intervention"
    )  # their state before
    state_after: int = Field(
        ..., description="VELURIA state after intervention"
    )  # their state after
    intervener_id: Optional[str] = Field(
        None, description="ID of human intervener (if applicable)"
    )  # who helped (if human)
    outcome: Optional[str] = Field(None, description="Outcome of the intervention")  # how it went


class EmotionalStateInput(BaseModel):
    """Input for emotional state processing endpoint - what users send us"""

    user_id: str = Field(..., description="User identifier")  # who is this
    session_id: str = Field(..., description="Session identifier")  # what conversation
    text: str = Field(..., description="User's emotional text input")  # what they said
    biomarkers: Optional[Dict[str, float]] = Field(
        None, description="Optional biometric measurements"
    )  # heart rate, etc if available
    context: Optional[Dict[str, Any]] = Field(
        None, description="Additional context information"
    )  # time of day, location, etc


class EmotionalStateResponse(BaseModel):
    """Response from emotional state processing endpoint - what we send back"""

    symbolic_anchor: str = Field(
        ..., description="Primary symbolic anchor identified"
    )  # main symbol we picked
    alternatives: List[str] = Field(
        ..., description="Alternative symbolic representations"
    )  # other options
    archetype: str = Field(..., description="Jungian archetype identified")  # which archetype fits
    drift_index: float = Field(
        ..., description="Symbolic drift from previous states"
    )  # how much they've changed
    safety_status: Dict[str, Any] = Field(
        ..., description="Current safety assessment"
    )  # are they safe
    content: Optional[Dict[str, Any]] = Field(
        None, description="Additional content for response"
    )  # extra stuff for frontend


class EmotionalState(BaseModel):
    """Complete emotional state record for storage - everything we keep"""

    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier")
    user_id: str = Field(..., description="User identifier")  # who this belongs to
    session_id: str = Field(..., description="Session identifier")  # what conversation
    timestamp: datetime = Field(
        default_factory=datetime.now, description="When the state was recorded"
    )  # when we processed it
    valence: float = Field(..., description="Emotional valence from -1.0 to 1.0")  # happy/sad score
    arousal: float = Field(..., description="Emotional arousal from 0.0 to 1.0")  # energy level
    primary_symbol: str = Field(..., description="Primary symbolic representation")  # main symbol
    alternative_symbols: List[str] = Field(
        ..., description="Alternative symbolic representations"
    )  # backup symbols
    archetype: str = Field(..., description="Identified archetype")  # jungian archetype
    drift_index: float = Field(
        ..., description="Calculated drift from previous states"
    )  # change metric
    safety_level: int = Field(..., description="Safety level assessment")  # how worried we are
    input_text_hash: str = Field(
        ..., description="Hashed version of input text for reference"
    )  # we never store the actual text
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional context and metadata"
    )  # extra stuff

    class Config:
        orm_mode = True  # works with sqlalchemy
