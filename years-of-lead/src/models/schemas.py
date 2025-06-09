"""
API schema models for Years of Lead
Defines Pydantic models for request/response validation
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator, EmailStr
from enum import Enum

from models.sql_models import FactionType, IdeologyType, OperationType


# Auth schemas
class UserBase(BaseModel):
    """Base user schema"""
    username: str
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for user creation"""
    password: str


class UserLogin(BaseModel):
    """Schema for user login"""
    username: str
    password: str


class UserResponse(UserBase):
    """Schema for user response"""
    id: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    
    class Config:
        orm_mode = True


class Token(BaseModel):
    """Schema for auth token"""
    access_token: str
    token_type: str = "bearer"


# Faction schemas
class FactionBase(BaseModel):
    """Base faction schema"""
    name: str
    description: Optional[str] = None
    faction_type: FactionType
    ideology: IdeologyType
    specialties: Optional[List[str]] = []


class FactionCreate(FactionBase):
    """Schema for faction creation"""
    default_strength: int = 50


class FactionResponse(FactionBase):
    """Schema for faction response"""
    id: str
    default_strength: int
    
    class Config:
        orm_mode = True


class FactionRelationshipResponse(BaseModel):
    """Schema for faction relationship response"""
    faction_id: str
    other_faction_id: str
    relationship_value: int
    updated_at: datetime
    
    class Config:
        orm_mode = True


# District schemas
class DistrictBase(BaseModel):
    """Base district schema"""
    name: str
    description: Optional[str] = None
    default_population: int = 100000
    default_security_level: int = 5
    geo_data: Optional[Dict[str, Any]] = {}


class DistrictCreate(DistrictBase):
    """Schema for district creation"""
    pass


class DistrictResponse(DistrictBase):
    """Schema for district response"""
    id: str
    
    class Config:
        orm_mode = True


# Game schemas
class GameCreate(BaseModel):
    """Schema for creating a new game"""
    name: str
    scenario_id: Optional[str] = None
    max_turns: int = 100
    initial_player_faction: Optional[str] = None


class GameResponse(BaseModel):
    """Schema for game response"""
    id: str
    name: str
    scenario_id: Optional[str]
    created_by: str
    current_turn: int
    max_turns: int
    is_completed: bool
    created_at: datetime
    last_played_at: datetime
    
    class Config:
        orm_mode = True


class GameStateResponse(BaseModel):
    """Schema for game state response"""
    id: str
    name: str
    current_turn: int
    max_turns: int
    is_completed: bool
    created_at: datetime
    last_played_at: datetime
    
    class Config:
        orm_mode = True


class GameActionRequest(BaseModel):
    """Schema for game action request"""
    action_type: str
    target_id: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = {}


class GameActionResponse(BaseModel):
    """Schema for game action response"""
    success: bool
    message: str
    results: Optional[Dict[str, Any]] = {}


class TurnResponse(BaseModel):
    """Schema for turn processing response"""
    turn_number: int
    events: List[Dict[str, Any]]
    faction_updates: Dict[str, Dict[str, Any]]
    district_updates: Dict[str, Dict[str, Any]]
    narrative_summary: Optional[str] = None


class EventResponse(BaseModel):
    """Schema for event response"""
    id: str
    event_type: str
    turn: int
    timestamp: datetime
    name: Optional[str] = None
    description: Optional[str] = None
    data: Dict[str, Any]
    narrative_text: Optional[str] = None
    
    class Config:
        orm_mode = True


# Player schemas
class PlayerCharacterBase(BaseModel):
    """Base player character schema"""
    name: str
    background: Optional[str] = None
    skills: Optional[Dict[str, int]] = {}
    traits: Optional[List[str]] = []


class PlayerCharacterCreate(PlayerCharacterBase):
    """Schema for player character creation"""
    pass


class PlayerCharacterResponse(PlayerCharacterBase):
    """Schema for player character response"""
    id: str
    game_id: str
    heat: int
    emotional_state: Optional[Dict[str, Any]] = {}
    
    class Config:
        orm_mode = True


class CellBase(BaseModel):
    """Base cell schema"""
    name: str
    size: int = 3
    skill_levels: Optional[Dict[str, int]] = {}


class CellCreate(CellBase):
    """Schema for cell creation"""
    faction_id: str
    district_id: str
    leader_id: Optional[str] = None


class CellResponse(CellBase):
    """Schema for cell response"""
    id: str
    faction_id: str
    district_id: str
    leader_id: Optional[str] = None
    cover_strength: int
    morale: int
    heat: int
    
    class Config:
        orm_mode = True


# Operation schemas
class OperationBase(BaseModel):
    """Base operation schema"""
    name: str
    description: Optional[str] = None
    operation_type: OperationType


class OperationCreate(OperationBase):
    """Schema for operation creation"""
    faction_id: str
    district_id: str
    planning_turns: int = 1
    execution_turns: int = 1
    required_resources: Optional[Dict[str, int]] = {}
    cell_ids: List[str]


class OperationResponse(OperationBase):
    """Schema for operation response"""
    id: str
    faction_id: str
    district_id: str
    planning_turns: int
    execution_turns: int
    current_stage: str
    risk_level: int
    success_probability: float
    heat_generation: int
    required_resources: Dict[str, int]
    potential_outcomes: Optional[Dict[str, Any]] = {}
    
    class Config:
        orm_mode = True


# Journal schemas
class JournalEntryCreate(BaseModel):
    """Schema for journal entry creation"""
    title: Optional[str] = None
    content: str


class JournalEntryResponse(BaseModel):
    """Schema for journal entry response"""
    id: str
    character_id: str
    turn: int
    timestamp: datetime
    title: Optional[str] = None
    content: str
    emotional_tags: Optional[List[Dict[str, Any]]] = []
    narrative_context: Optional[Dict[str, Any]] = {}
    
    class Config:
        orm_mode = True


# AI integration schemas
class SylvaRequest(BaseModel):
    """Schema for SYLVA API requests"""
    character_id: str
    game_id: str
    content: str
    emotional_context: Optional[Dict[str, Any]] = {}
    interaction_type: str = "journal_entry"  # or "game_event", "character_reaction"


class SylvaResponse(BaseModel):
    """Schema for SYLVA API responses"""
    emotional_analysis: Dict[str, float]
    symbolic_elements: List[Dict[str, Any]]
    narrative_suggestions: Optional[Dict[str, Any]] = {}
    therapeutic_value: Optional[float] = None


class WrenRequest(BaseModel):
    """Schema for WREN API requests"""
    character_id: Optional[str] = None
    game_id: str
    content: str
    narrative_context: Optional[Dict[str, Any]] = {}
    request_type: str = "reflection"  # or "narrative_prompt", "story_arc"


class WrenResponse(BaseModel):
    """Schema for WREN API responses"""
    reflective_prompts: List[str]
    narrative_elements: Dict[str, Any]
    character_growth_suggestions: Optional[Dict[str, Any]] = {}
    therapeutic_narrative: Optional[str] = None
