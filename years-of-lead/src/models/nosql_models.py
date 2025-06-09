"""
MongoDB schemas for Years of Lead
These models define the structure for MongoDB collections
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field


class GameStateSnapshot(BaseModel):
    """
    Game state snapshot for saving game history and allowing rollbacks
    Stored in MongoDB for efficient serialization of complex state
    """
    game_id: str = Field(..., description="UUID of the game")
    turn: int = Field(..., description="Turn number when snapshot was created")
    timestamp: datetime = Field(default_factory=datetime.now, description="When snapshot was created")
    snapshot_type: str = Field(..., description="Type of snapshot (e.g., 'turn_start', 'turn_end', 'manual_save')")
    
    # Core game state
    current_turn: int = Field(..., description="Current turn number")
    game_status: str = Field(..., description="Game status (running, paused, completed)")
    
    # Resources and metrics
    resources: Dict[str, int] = Field(..., description="Resource amounts (money, influence, etc.)")
    global_metrics: Dict[str, float] = Field({}, description="Global game metrics")
    
    # State snapshots for game entities
    factions: Dict[str, Dict[str, Any]] = Field(..., description="Faction states")
    districts: Dict[str, Dict[str, Any]] = Field(..., description="District states")
    cells: Dict[str, Dict[str, Any]] = Field(..., description="Cell states")
    player_characters: Dict[str, Dict[str, Any]] = Field(..., description="Player character states")
    operations: Dict[str, Dict[str, Any]] = Field(..., description="Operation states")
    
    # Relationships
    faction_relationships: Dict[str, Dict[str, int]] = Field(..., description="Faction relationship values")
    district_control: Dict[str, Dict[str, float]] = Field(..., description="Faction control in districts")
    
    # SYLVA/WREN integration data
    emotional_states: Dict[str, Any] = Field({}, description="SYLVA emotional state data")
    narrative_context: Dict[str, Any] = Field({}, description="WREN narrative context data")
    symbolic_markers: List[Dict[str, Any]] = Field([], description="Symbolic elements for storytelling")
    
    class Config:
        schema_extra = {
            "collection": "game_state_snapshots"
        }


class GameEventLog(BaseModel):
    """
    Detailed event log for game events
    Used for event history, analytics, and narrative generation
    """
    game_id: str = Field(..., description="UUID of the game")
    event_id: str = Field(..., description="UUID of the event")
    event_type: str = Field(..., description="Type of event")
    turn: int = Field(..., description="Turn number when event occurred")
    timestamp: datetime = Field(default_factory=datetime.now, description="When event occurred")
    
    # Event details
    name: Optional[str] = Field(None, description="Event name if applicable")
    description: Optional[str] = Field(None, description="Event description")
    
    # Entities involved
    affected_entities: Dict[str, List[str]] = Field({}, description="IDs of entities affected by event")
    initiator: Optional[Dict[str, str]] = Field(None, description="Entity that initiated the event")
    
    # Event data
    data: Dict[str, Any] = Field({}, description="Event-specific data")
    outcomes: List[Dict[str, Any]] = Field([], description="Event outcomes")
    
    # Narrative elements
    narrative_text: Optional[str] = Field(None, description="Generated narrative text")
    emotional_impact: Dict[str, Any] = Field({}, description="SYLVA emotional impact data")
    symbolic_elements: List[Dict[str, Any]] = Field([], description="Symbolic elements from event")
    
    class Config:
        schema_extra = {
            "collection": "game_event_logs"
        }


class PlayerJournal(BaseModel):
    """
    Player character journal entry
    Used for SYLVA emotional modeling and WREN narrative integration
    """
    id: str = Field(..., description="UUID of journal entry")
    game_id: str = Field(..., description="UUID of the game")
    character_id: str = Field(..., description="UUID of the character")
    turn: int = Field(..., description="Turn number when entry was created")
    timestamp: datetime = Field(default_factory=datetime.now, description="When entry was created")
    
    # Journal content
    title: str = Field(..., description="Journal entry title")
    content: str = Field(..., description="Journal entry content")
    is_private: bool = Field(True, description="Whether entry is private to character")
    
    # SYLVA/WREN integration
    emotional_tags: List[Dict[str, Any]] = Field([], description="Emotional tags from SYLVA")
    emotional_state: Dict[str, Any] = Field({}, description="Emotional state snapshot")
    narrative_context: Dict[str, Any] = Field({}, description="Narrative context from WREN")
    symbolic_elements: List[Dict[str, Any]] = Field([], description="Symbolic narrative elements")
    character_growth_markers: List[Dict[str, Any]] = Field([], description="Character development indicators")
    
    class Config:
        schema_extra = {
            "collection": "player_journals"
        }


class FactionAnalytics(BaseModel):
    """
    Analytics data for faction performance and behavior
    Used for game balance, AI training, and player insights
    """
    game_id: str = Field(..., description="UUID of the game")
    faction_id: str = Field(..., description="UUID of the faction")
    turn: int = Field(..., description="Turn number")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp")
    
    # Resource metrics
    resources: Dict[str, int] = Field(..., description="Resource amounts")
    resource_delta: Dict[str, int] = Field({}, description="Resource changes this turn")
    
    # Influence metrics
    total_influence: float = Field(0.0, description="Total faction influence")
    influence_by_district: Dict[str, float] = Field({}, description="Influence per district")
    
    # Operation metrics
    operations_total: int = Field(0, description="Total operations")
    operations_success_rate: float = Field(0.0, description="Operation success rate")
    operations_by_type: Dict[str, int] = Field({}, description="Count of operations by type")
    
    # Relationship metrics
    average_relationship: float = Field(0.0, description="Average relationship with other factions")
    relationships_delta: Dict[str, int] = Field({}, description="Relationship changes this turn")
    
    # AI behavior data
    decision_factors: Dict[str, float] = Field({}, description="Factors affecting AI decisions")
    strategy_focus: Dict[str, float] = Field({}, description="Strategic focus areas")
    
    class Config:
        schema_extra = {
            "collection": "faction_analytics"
        }


class WorldState(BaseModel):
    """
    Global world state model
    Tracks global events, news, and world conditions
    """
    game_id: str = Field(..., description="UUID of the game")
    turn: int = Field(..., description="Current turn number")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp")
    
    # Global conditions
    world_tension: float = Field(0.0, description="Global tension level (0-1)")
    economic_stability: float = Field(0.5, description="Economic stability (0-1)")
    public_unrest: float = Field(0.0, description="Public unrest level (0-1)")
    media_focus: List[Dict[str, Any]] = Field([], description="Current media focus areas")
    
    # News and headlines
    headlines: List[Dict[str, Any]] = Field([], description="Current news headlines")
    major_events: List[Dict[str, Any]] = Field([], description="Major world events")
    
    # Government response
    security_level: int = Field(0, description="Global security level (0-10)")
    policy_changes: List[Dict[str, Any]] = Field([], description="Recent policy changes")
    
    # Environmental factors
    season: str = Field("spring", description="Current season")
    weather_conditions: Dict[str, Any] = Field({}, description="Weather conditions by district")
    
    class Config:
        schema_extra = {
            "collection": "world_states"
        }


class AITrainingData(BaseModel):
    """
    Training data collection for AI modules
    Used to improve faction AI and narrative generation
    """
    game_id: str = Field(..., description="UUID of the game")
    collection_time: datetime = Field(default_factory=datetime.now, description="When data was collected")
    data_type: str = Field(..., description="Type of AI training data")
    
    # Training examples
    examples: List[Dict[str, Any]] = Field(..., description="Training examples")
    
    # Metadata
    source_module: str = Field(..., description="Module that generated the data")
    labels: List[str] = Field([], description="Classification labels")
    quality_score: Optional[float] = Field(None, description="Quality score if evaluated")
    
    class Config:
        schema_extra = {
            "collection": "ai_training_data"
        }


class SylvaIntegrationData(BaseModel):
    """
    SYLVA integration data
    Stores emotional modeling data and symbolic patterns
    """
    game_id: str = Field(..., description="UUID of the game")
    character_id: str = Field(..., description="UUID of character if applicable")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp")
    
    # Emotional data
    emotional_state: Dict[str, float] = Field(..., description="Current emotional state values")
    emotional_trajectory: List[Dict[str, Any]] = Field([], description="Recent emotional changes")
    psychological_profile: Dict[str, Any] = Field({}, description="Character psychological profile")
    
    # Symbolic elements
    symbolic_patterns: List[Dict[str, Any]] = Field([], description="Detected symbolic patterns")
    narrative_dissonance: Dict[str, Any] = Field({}, description="Narrative dissonance metrics")
    dream_elements: List[Dict[str, Any]] = Field([], description="Elements for dream sequences")
    
    # Therapeutic data
    therapy_suggestions: List[Dict[str, Any]] = Field([], description="Suggested therapeutic narratives")
    emotional_regulation_metrics: Dict[str, float] = Field({}, description="Emotional regulation metrics")
    
    class Config:
        schema_extra = {
            "collection": "sylva_integration_data"
        }


class WrenIntegrationData(BaseModel):
    """
    WREN integration data
    Stores narrative scaffolding and character development data
    """
    game_id: str = Field(..., description="UUID of the game")
    character_id: Optional[str] = Field(None, description="UUID of character if applicable")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp")
    
    # Narrative elements
    active_narrative_arcs: List[Dict[str, Any]] = Field([], description="Active narrative arcs")
    character_arcs: Dict[str, Dict[str, Any]] = Field({}, description="Character development arcs")
    world_narrative_threads: List[Dict[str, Any]] = Field([], description="World narrative threads")
    
    # Reflective elements
    reflective_prompts: List[Dict[str, Any]] = Field([], description="Reflective roleplay prompts")
    narrative_reflections: List[Dict[str, Any]] = Field([], description="Narrative reflections")
    character_growth_opportunities: List[Dict[str, Any]] = Field([], description="Character growth opportunities")
    
    # Therapeutic narratives
    therapeutic_narratives: List[Dict[str, Any]] = Field([], description="Generated therapeutic narratives")
    trauma_informed_contexts: Dict[str, Any] = Field({}, description="Trauma-informed narrative contexts")
    
    class Config:
        schema_extra = {
            "collection": "wren_integration_data"
        }
