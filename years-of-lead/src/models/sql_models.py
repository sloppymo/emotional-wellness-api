"""
SQLAlchemy models for Years of Lead PostgreSQL database
"""

from sqlalchemy import (
    Boolean, Column, ForeignKey, Integer, String, 
    Float, DateTime, Text, Enum, JSON, Table
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid
import enum
from datetime import datetime

from core.database import Base


class FactionType(enum.Enum):
    """Types of factions available in the game"""
    ANARCHIST = "anarchist"
    THINKTANK = "thinktank"
    CORPORATE = "corporate"
    RELIGIOUS = "religious"
    SEPARATIST = "separatist"


class IdeologyType(enum.Enum):
    """Types of ideologies available in the game"""
    RADICAL_LEFT = "radical_left"
    CENTRIST = "centrist"
    CORPORATIST = "corporatist"
    RELIGIOUS_RIGHT = "religious_right" 
    REGIONALIST = "regionalist"


class OperationType(enum.Enum):
    """Types of operations available in the game"""
    RECRUITMENT = "recruitment"
    PROTEST = "protest"
    SABOTAGE = "sabotage"
    INFILTRATION = "infiltration"
    PROPAGANDA = "propaganda"
    FUNDRAISING = "fundraising"
    HACKING = "hacking"
    DIRECT_ACTION = "direct_action"


# Many-to-many relationship tables
faction_district_control = Table(
    "faction_district_control",
    Base.metadata,
    Column("faction_id", String, ForeignKey("factions.id"), primary_key=True),
    Column("district_id", String, ForeignKey("districts.id"), primary_key=True),
    Column("control_percentage", Float, default=0.0),
    Column("influence", Float, default=0.0),
    Column("heat", Float, default=0.0),
    Column("updated_at", DateTime, default=func.now(), onupdate=func.now())
)

faction_relationships = Table(
    "faction_relationships",
    Base.metadata,
    Column("faction_id", String, ForeignKey("factions.id"), primary_key=True),
    Column("other_faction_id", String, ForeignKey("factions.id"), primary_key=True),
    Column("relationship_value", Integer, default=0),  # -100 to 100
    Column("updated_at", DateTime, default=func.now(), onupdate=func.now())
)


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    games = relationship("Game", back_populates="user")


class Game(Base):
    """Game session model"""
    __tablename__ = "games"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    scenario_id = Column(String, ForeignKey("scenarios.id"))
    current_turn = Column(Integer, default=0)
    max_turns = Column(Integer, default=100)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_played_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="games")
    scenario = relationship("Scenario")
    game_factions = relationship("GameFaction", back_populates="game")
    game_districts = relationship("GameDistrict", back_populates="game")
    player_characters = relationship("PlayerCharacter", back_populates="game")
    events = relationship("GameEvent", back_populates="game")


class Scenario(Base):
    """Game scenario model"""
    __tablename__ = "scenarios"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    difficulty = Column(Integer, default=1)  # 1-10
    initial_conditions = Column(JSON)  # JSON configuration
    faction_settings = Column(JSON)
    district_settings = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    games = relationship("Game", back_populates="scenario")


class Faction(Base):
    """Faction template model"""
    __tablename__ = "factions"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    faction_type = Column(Enum(FactionType), nullable=False)
    ideology = Column(Enum(IdeologyType), nullable=False)
    default_strength = Column(Integer, default=50)  # 0-100
    specialties = Column(JSON)  # List of specialties
    
    # Relationships
    game_factions = relationship("GameFaction", back_populates="faction_template")


class GameFaction(Base):
    """Instance of a faction in a specific game"""
    __tablename__ = "game_factions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    game_id = Column(String, ForeignKey("games.id"), nullable=False)
    faction_template_id = Column(String, ForeignKey("factions.id"), nullable=False)
    name = Column(String, nullable=False)
    strength = Column(Integer, default=50)
    resources = Column(JSON)  # Dictionary of resources
    is_player_faction = Column(Boolean, default=False)
    
    # Relationships
    game = relationship("Game", back_populates="game_factions")
    faction_template = relationship("Faction", back_populates="game_factions")
    cells = relationship("Cell", back_populates="faction")
    operations = relationship("Operation", back_populates="faction")


class District(Base):
    """District template model"""
    __tablename__ = "districts"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    default_population = Column(Integer, default=100000)
    default_security_level = Column(Integer, default=5)  # 1-10
    geo_data = Column(JSON)  # Geographic information
    
    # Relationships
    game_districts = relationship("GameDistrict", back_populates="district_template")


class GameDistrict(Base):
    """Instance of a district in a specific game"""
    __tablename__ = "game_districts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    game_id = Column(String, ForeignKey("games.id"), nullable=False)
    district_template_id = Column(String, ForeignKey("districts.id"), nullable=False)
    name = Column(String, nullable=False)
    population = Column(Integer, default=100000)
    security_level = Column(Integer, default=5)  # 1-10
    unrest_level = Column(Integer, default=0)  # 0-100
    prosperity_level = Column(Integer, default=50)  # 0-100
    heat = Column(Integer, default=0)  # How much attention from authorities
    
    # Relationships
    game = relationship("Game", back_populates="game_districts")
    district_template = relationship("District", back_populates="game_districts")
    operations = relationship("Operation", back_populates="district")
    cells = relationship("Cell", back_populates="district")


class PlayerCharacter(Base):
    """Player character model"""
    __tablename__ = "player_characters"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    game_id = Column(String, ForeignKey("games.id"), nullable=False)
    name = Column(String, nullable=False)
    background = Column(Text)
    skills = Column(JSON)  # Character skills
    traits = Column(JSON)  # Character traits
    heat = Column(Integer, default=0)  # Personal heat level
    emotional_state = Column(JSON)  # SYLVA emotional data
    
    # Relationships
    game = relationship("Game", back_populates="player_characters")
    cells = relationship("Cell", back_populates="leader")
    journal_entries = relationship("JournalEntry", back_populates="character")


class Cell(Base):
    """Cell model - small group of operatives"""
    __tablename__ = "cells"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    faction_id = Column(String, ForeignKey("game_factions.id"), nullable=False)
    district_id = Column(String, ForeignKey("game_districts.id"), nullable=False)
    leader_id = Column(String, ForeignKey("player_characters.id"))
    name = Column(String, nullable=False)
    size = Column(Integer, default=3)  # Number of members
    cover_strength = Column(Integer, default=50)  # How well hidden, 0-100
    morale = Column(Integer, default=50)  # 0-100
    skill_levels = Column(JSON)  # Various skill ratings
    heat = Column(Integer, default=0)  # How much attention from authorities
    
    # Relationships
    faction = relationship("GameFaction", back_populates="cells")
    district = relationship("GameDistrict", back_populates="cells")
    leader = relationship("PlayerCharacter", back_populates="cells")
    operations = relationship("Operation", secondary="cell_operations")


class Operation(Base):
    """Operation model - activities conducted by cells"""
    __tablename__ = "operations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    faction_id = Column(String, ForeignKey("game_factions.id"), nullable=False)
    district_id = Column(String, ForeignKey("game_districts.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    operation_type = Column(Enum(OperationType), nullable=False)
    planning_turns = Column(Integer, default=1)  # Turns needed for planning
    execution_turns = Column(Integer, default=1)  # Turns needed for execution
    current_stage = Column(String, default="planning")  # planning, executing, completed, failed
    risk_level = Column(Integer, default=50)  # 0-100
    success_probability = Column(Float, default=0.5)  # 0-1
    heat_generation = Column(Integer, default=10)  # Heat generated on success
    required_resources = Column(JSON)  # Resources needed
    potential_outcomes = Column(JSON)  # Possible results
    
    # Relationships
    faction = relationship("GameFaction", back_populates="operations")
    district = relationship("GameDistrict", back_populates="operations")


# Many-to-many relationship for cells and operations
cell_operations = Table(
    "cell_operations",
    Base.metadata,
    Column("cell_id", String, ForeignKey("cells.id"), primary_key=True),
    Column("operation_id", String, ForeignKey("operations.id"), primary_key=True)
)


class GameEvent(Base):
    """Game event model"""
    __tablename__ = "game_events"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    game_id = Column(String, ForeignKey("games.id"), nullable=False)
    event_type = Column(String, nullable=False)
    turn = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=func.now())
    data = Column(JSON)  # Event data
    narrative_text = Column(Text)  # SYLVA/WREN generated narrative
    
    # Relationships
    game = relationship("Game", back_populates="events")


class JournalEntry(Base):
    """Player character journal entries"""
    __tablename__ = "journal_entries"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    character_id = Column(String, ForeignKey("player_characters.id"), nullable=False)
    turn = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=func.now())
    title = Column(String)
    content = Column(Text, nullable=False)
    emotional_tags = Column(JSON)  # SYLVA emotional tags
    narrative_context = Column(JSON)  # WREN narrative context
    
    # Relationships
    character = relationship("PlayerCharacter", back_populates="journal_entries")
