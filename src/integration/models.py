"""
Integration models for SYLVA-WREN coordination.
"""
from enum import Enum, auto
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime


class EmotionalState(BaseModel):
    """User's emotional state representation."""
    primary_emotion: str = Field(..., description="Primary emotion experienced")
    secondary_emotions: List[str] = Field(default_factory=list, description="Secondary emotions experienced")
    intensity: float = Field(..., ge=0, le=10, description="Intensity level (0-10)")
    valence: float = Field(..., ge=-1, le=1, description="Emotional valence (-1 to 1)")
    arousal: float = Field(..., ge=0, le=10, description="Emotional arousal level (0-10)")
    context: Dict[str, str] = Field(default_factory=dict, description="Contextual factors")
    timestamp: datetime = Field(default_factory=datetime.now, description="When this emotional state was recorded")


class Metaphor(BaseModel):
    """Extracted metaphor from user text."""
    content: str = Field(..., description="Actual metaphor text")
    source_domain: str = Field(..., description="Source domain of the metaphor")
    target_domain: str = Field(..., description="Target domain of the metaphor")
    emotions: List[str] = Field(default_factory=list, description="Associated emotions")
    confidence: float = Field(..., ge=0, le=1, description="Confidence level of extraction")


class Theme(BaseModel):
    """Thematic classification for metaphors."""
    name: str = Field(..., description="Theme name")
    description: str = Field(..., description="Theme description")
    metaphors: List[Metaphor] = Field(default_factory=list, description="Associated metaphors")
    relevance: float = Field(..., ge=0, le=1, description="Relevance score")


class ColorSymbol(BaseModel):
    """Color symbolism extracted from text."""
    color: str = Field(..., description="Color name")
    context: str = Field(..., description="Usage context")
    symbolic_meaning: str = Field(..., description="Interpreted symbolic meaning")
    emotional_association: List[str] = Field(default_factory=list, description="Associated emotions")


class NatureElement(BaseModel):
    """Nature element symbolism extracted from text."""
    element: str = Field(..., description="Nature element name")
    context: str = Field(..., description="Usage context")
    symbolic_meaning: str = Field(..., description="Interpreted symbolic meaning")
    archetypal_association: str = Field(..., description="Associated archetype if applicable")


class ArchetypeMapping(BaseModel):
    """Mapping between emotional state and archetypes."""
    emotional_state_id: str = Field(..., description="Reference to emotional state")
    archetypes: Dict[str, float] = Field(..., description="Archetype to weight mapping")
    dominant_archetype: str = Field(..., description="Name of dominant archetype")
    timestamp: datetime = Field(default_factory=datetime.now, description="When this mapping was created")


class DominantArchetype(BaseModel):
    """Dominant archetype with additional information."""
    name: str = Field(..., description="Archetype name")
    weight: float = Field(..., ge=0, le=1, description="Weight of this archetype in the mapping")
    description: str = Field(..., description="Description of this archetype")
    traits: List[str] = Field(default_factory=list, description="Traits associated with this archetype")


class ArchetypeTransitionAnalysis(BaseModel):
    """Analysis of transitions between dominant archetypes over time."""
    stability_score: float = Field(..., ge=0, le=1, description="Stability of archetype presence")
    oscillation_patterns: List[Dict[str, str]] = Field(default_factory=list, 
                                                    description="Detected oscillation patterns")
    major_shifts: List[Dict[str, str]] = Field(default_factory=list, 
                                            description="Major archetype shifts")
    timeline_insight: str = Field(..., description="Textual insight about archetype timeline")


class ArchetypeAnalysis(BaseModel):
    """Complete archetype analysis result."""
    dominant_archetypes: List[DominantArchetype] = Field(default_factory=list, 
                                                      description="Dominant archetypes")
    archetype_mapping: ArchetypeMapping = Field(..., description="Full mapping to archetypes")
    contextual_factors: Dict[str, str] = Field(default_factory=dict, 
                                             description="Contextual factors influencing analysis")
    source_emotional_state: EmotionalState = Field(..., description="Source emotional state")


class UserContext(BaseModel):
    """User context for personalized processing."""
    user_id: str = Field(..., description="Unique user identifier")
    preferences: Dict[str, str] = Field(default_factory=dict, description="User preferences")
    history_summary: Optional[str] = Field(None, description="Summary of relevant history")
    session_id: str = Field(..., description="Current session identifier")
    cultural_context: Dict[str, str] = Field(default_factory=dict, description="Cultural context factors")


class EmotionalInput(BaseModel):
    """Emotional input from user."""
    text_content: str = Field(..., description="Raw text content from user")
    detected_emotions: List[str] = Field(default_factory=list, description="Pre-detected emotions if any")
    context_factors: Dict[str, str] = Field(default_factory=dict, description="Contextual factors")
    user_context: UserContext = Field(..., description="User context information")


class CrisisLevel(Enum):
    """Crisis severity levels."""
    NONE = auto()
    LOW = auto()
    MODERATE = auto()
    ELEVATED = auto()
    SEVERE = auto()


class CrisisAssessment(BaseModel):
    """Assessment of potential crisis indicators in user content."""
    level: CrisisLevel = Field(..., description="Assessed crisis level")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in assessment")
    indicators: List[Dict[str, Union[str, float]]] = Field(default_factory=list, 
                                                         description="Detected crisis indicators")
    recommended_response: str = Field(..., description="Recommended response approach")
    escalation_needed: bool = Field(False, description="Whether professional escalation is needed")


class SceneType(Enum):
    """Types of narrative scenes."""
    EXPLORATORY = auto()
    REFLECTIVE = auto()
    TRANSFORMATIVE = auto()
    GROUNDING = auto()
    RESTORATIVE = auto()
    EDUCATIONAL = auto()


class TransitionTrigger(Enum):
    """Triggers for scene transitions."""
    USER_CHOICE = auto()
    EMOTIONAL_SHIFT = auto()
    CRISIS_RESPONSE = auto()
    NARRATIVE_PROGRESSION = auto()
    REGULATION_NEED = auto()
    SYSTEM_INITIATED = auto()


class AvailableAction(BaseModel):
    """Action available to user in current scene."""
    id: str = Field(..., description="Action identifier")
    description: str = Field(..., description="Action description")
    emotional_impact: Dict[str, float] = Field(default_factory=dict, 
                                             description="Expected emotional impact")
    archetypal_alignment: List[str] = Field(default_factory=list, 
                                          description="Aligned archetypes")


class UserAction(BaseModel):
    """Action taken by user."""
    action_id: str = Field(..., description="ID of the selected action")
    timestamp: datetime = Field(default_factory=datetime.now, description="When action was taken")
    context_data: Dict[str, str] = Field(default_factory=dict, description="Additional context")


class SceneOutcome(BaseModel):
    """Outcome of a narrative scene based on user actions."""
    narrative_text: str = Field(..., description="Narrative outcome text")
    emotional_impact: Dict[str, float] = Field(default_factory=dict, 
                                             description="Actual emotional impact")
    next_scene_options: List[Dict[str, str]] = Field(default_factory=list, 
                                                   description="Next scene options")


class NarrativeScene(BaseModel):
    """Narrative scene in user's emotional journey."""
    id: str = Field(..., description="Scene identifier")
    type: SceneType = Field(..., description="Scene type")
    current_state: Dict[str, str] = Field(..., description="Current scene state")
    available_actions: List[AvailableAction] = Field(default_factory=list, 
                                                   description="Available actions")
    narrative_content: str = Field(..., description="Narrative content of scene")
    symbolic_elements: List[Dict[str, str]] = Field(default_factory=list, 
                                                  description="Symbolic elements in scene")
    emotional_targets: Dict[str, float] = Field(default_factory=dict, 
                                              description="Target emotional outcomes")


class RegulationTechnique(BaseModel):
    """Emotional regulation technique."""
    name: str = Field(..., description="Technique name")
    description: str = Field(..., description="Technique description")
    instructions: List[str] = Field(..., description="Step-by-step instructions")
    suitable_emotions: List[str] = Field(..., description="Emotions this technique is suitable for")
    expected_outcome: str = Field(..., description="Expected outcome of technique")


class EffectivenessReport(BaseModel):
    """Report on effectiveness of regulation technique."""
    technique_id: str = Field(..., description="ID of applied technique")
    emotional_shift: Dict[str, float] = Field(..., description="Measured emotional shift")
    user_feedback: Optional[str] = Field(None, description="User feedback if any")
    effectiveness_score: float = Field(..., ge=0, le=10, description="Overall effectiveness score")
    recommendations: List[str] = Field(default_factory=list, description="Future recommendations")


class GroundingExercise(BaseModel):
    """Grounding exercise for emotional regulation."""
    title: str = Field(..., description="Exercise title")
    intensity_level: int = Field(..., ge=1, le=5, description="Intensity level (1-5)")
    focus_area: str = Field(..., description="Primary focus area")
    steps: List[str] = Field(..., description="Exercise steps")
    estimated_duration_minutes: int = Field(..., description="Estimated duration in minutes")


class RegulationNarrative(BaseModel):
    """Narrative designed to support emotional regulation."""
    narrative_text: str = Field(..., description="Full narrative text")
    emotional_targets: Dict[str, float] = Field(..., description="Target emotional states")
    modality: str = Field(..., description="Narrative modality (e.g., guided imagery)")
    symbolic_elements: List[str] = Field(default_factory=list, description="Key symbolic elements")


class SymbolicState(BaseModel):
    """Symbolic processing state from SYLVA framework."""
    metaphors: List[Metaphor] = Field(default_factory=list, description="Active metaphors")
    dominant_archetypes: List[DominantArchetype] = Field(default_factory=list, 
                                                      description="Current dominant archetypes")
    themes: List[Theme] = Field(default_factory=list, description="Active themes")
    crisis_indicators: Optional[CrisisAssessment] = Field(None, description="Crisis assessment if any")


class NarrativeState(BaseModel):
    """Narrative state from WREN framework."""
    current_scene: NarrativeScene = Field(..., description="Current narrative scene")
    scene_history: List[str] = Field(default_factory=list, description="Previous scene IDs")
    regulation_techniques: List[str] = Field(default_factory=list, 
                                           description="Applied regulation technique IDs")


class IntegratedState(BaseModel):
    """Integrated state combining symbolic and narrative information."""
    symbolic: SymbolicState = Field(..., description="Symbolic state")
    narrative: NarrativeState = Field(..., description="Narrative state")
    integration_insights: Dict[str, str] = Field(default_factory=dict, 
                                              description="Insights from integration")


class SymbolicResponse(BaseModel):
    """Response based on symbolic processing."""
    response_text: str = Field(..., description="Text response")
    metaphors_used: List[Dict[str, str]] = Field(default_factory=list, description="Metaphors used")
    archetype_influences: List[Dict[str, float]] = Field(default_factory=list, 
                                                      description="Influencing archetypes")


class IntegratedResponse(BaseModel):
    """Complete integrated response from SYLVA-WREN coordinator."""
    response_text: str = Field(..., description="Final response text")
    symbolic_elements: Dict[str, str] = Field(default_factory=dict, description="Symbolic elements used")
    narrative_elements: Dict[str, str] = Field(default_factory=dict, description="Narrative elements used")
    emotional_guidance: Optional[Dict[str, str]] = Field(None, description="Emotional guidance if any")
    crisis_response: Optional[Dict[str, str]] = Field(None, description="Crisis response if needed")
    next_actions: List[Dict[str, str]] = Field(default_factory=list, description="Suggested next actions")
