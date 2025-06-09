"""
Years of Lead - Core Game State and Logic

This module provides the main GameState class and core game mechanics
for the Years of Lead insurgency simulator.
"""

from enum import Enum
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import random


class GamePhase(Enum):
    """Game turn phases"""
    PLANNING = "planning"
    ACTION = "action" 
    RESOLUTION = "resolution"


class AgentStatus(Enum):
    """Agent status types"""
    ACTIVE = "active"
    INJURED = "injured"
    ARRESTED = "arrested"
    DEAD = "dead"


class SkillType(Enum):
    """Agent skill types"""
    COMBAT = "combat"
    STEALTH = "stealth"
    HACKING = "hacking"
    PERSUASION = "persuasion"
    INTELLIGENCE = "intelligence"
    DEMOLITIONS = "demolitions"


class MissionType(Enum):
    """Mission types"""
    PROPAGANDA = "propaganda"
    SABOTAGE = "sabotage"
    RECRUITMENT = "recruitment"
    INTELLIGENCE = "intelligence"
    FINANCING = "financing"


@dataclass
class Skill:
    """Agent skill with level"""
    level: int = 1
    experience: int = 0


@dataclass  
class Equipment:
    """Equipment item"""
    name: str
    type: str
    effectiveness: int = 1


@dataclass
class Agent:
    """Game agent/operative"""
    id: str
    name: str
    faction_id: str
    location_id: str
    status: AgentStatus = AgentStatus.ACTIVE
    background: str = "civilian"
    loyalty: int = 50
    stress: int = 0
    skills: Dict[SkillType, Skill] = field(default_factory=dict)
    equipment: List[Equipment] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize default skills"""
        if not self.skills:
            for skill_type in SkillType:
                self.skills[skill_type] = Skill(level=random.randint(1, 3))


@dataclass
class Faction:
    """Political faction"""
    id: str
    name: str
    current_goal: str = "recruitment"
    resources: Dict[str, int] = field(default_factory=lambda: {
        "money": 100,
        "influence": 10, 
        "personnel": 5
    })


@dataclass
class Location:
    """Game location"""
    id: str
    name: str
    security_level: int = 5
    unrest_level: int = 3
    active_events: List[str] = field(default_factory=list)


@dataclass
class Mission:
    """Active mission"""
    id: str
    mission_type: MissionType
    faction_id: str
    target_location_id: str
    participants: List[str] = field(default_factory=list)
    progress: int = 0


class GameState:
    """Main game state manager"""
    
    def __init__(self):
        self.turn_number = 1
        self.current_phase = GamePhase.PLANNING
        self.agents: Dict[str, Agent] = {}
        self.factions: Dict[str, Faction] = {}
        self.locations: Dict[str, Location] = {}
        self.active_missions: Dict[str, Mission] = {}
        self.recent_narrative: List[str] = []
        self.active_events: List[str] = []
    
    def initialize_game(self):
        """Initialize the game with default content"""
        self._create_default_factions()
        self._create_default_locations()
        self._create_default_agents()
        self._add_initial_narrative()
    
    def _create_default_factions(self):
        """Create the default resistance factions"""
        self.factions = {
            "resistance": Faction(
                id="resistance",
                name="The Resistance",
                current_goal="military_operations",
                resources={"money": 150, "influence": 15, "personnel": 8}
            ),
            "urban_liberation": Faction(
                id="urban_liberation", 
                name="Urban Liberation Front",
                current_goal="propaganda",
                resources={"money": 80, "influence": 25, "personnel": 12}
            ),
            "underground": Faction(
                id="underground",
                name="Underground Network", 
                current_goal="intelligence",
                resources={"money": 200, "influence": 8, "personnel": 4}
            )
        }
    
    def _create_default_locations(self):
        """Create the default game locations"""
        self.locations = {
            "safehouse_alpha": Location(
                id="safehouse_alpha",
                name="Safehouse Alpha",
                security_level=2,
                unrest_level=1
            ),
            "university_district": Location(
                id="university_district",
                name="University District",
                security_level=4,
                unrest_level=6
            ),
            "industrial_zone": Location(
                id="industrial_zone", 
                name="Industrial Zone",
                security_level=6,
                unrest_level=8
            ),
            "government_quarter": Location(
                id="government_quarter",
                name="Government Quarter",
                security_level=9,
                unrest_level=2
            ),
            "old_town": Location(
                id="old_town",
                name="Old Town Market",
                security_level=5,
                unrest_level=5
            )
        }
    
    def _create_default_agents(self):
        """Create the default operative agents"""
        agent_configs = [
            ("agent_maria", "Maria Santos", "urban_liberation", "university_district", "student"),
            ("agent_carlos", "Carlos Mendez", "resistance", "safehouse_alpha", "veteran"),
            ("agent_ana", "Ana Rodriguez", "underground", "old_town", "journalist"),
            ("agent_luis", "Luis Garcia", "resistance", "industrial_zone", "worker"),
            ("agent_sofia", "Sofia Vargas", "urban_liberation", "university_district", "organizer"),
            ("agent_miguel", "Miguel Torres", "underground", "government_quarter", "insider")
        ]
        
        for agent_id, name, faction_id, location_id, background in agent_configs:
            self.agents[agent_id] = Agent(
                id=agent_id,
                name=name,
                faction_id=faction_id,
                location_id=location_id,
                background=background,
                loyalty=random.randint(60, 90),
                stress=random.randint(10, 30)
            )
    
    def _add_initial_narrative(self):
        """Add initial narrative events"""
        self.recent_narrative = [
            "Resistance cells established across the city",
            "Government increases security patrols in university district", 
            "Underground network reports increased surveillance",
            "Worker strikes spread through industrial zones",
            "Student protests gain momentum in university district",
            "Government announces new emergency powers",
            "Resistance recruitment drives begin in safe areas",
            "Intelligence reports government infiltration attempts"
        ]
    
    def advance_turn(self):
        """Advance the game to the next phase/turn"""
        if self.current_phase == GamePhase.PLANNING:
            self.current_phase = GamePhase.ACTION
            self._process_planning_phase()
        elif self.current_phase == GamePhase.ACTION:
            self.current_phase = GamePhase.RESOLUTION
            self._process_action_phase()
        else:  # RESOLUTION
            self.current_phase = GamePhase.PLANNING
            self.turn_number += 1
            self._process_resolution_phase()
    
    def _process_planning_phase(self):
        """Process planning phase actions"""
        self.recent_narrative.append(f"Turn {self.turn_number}: Planning phase - Factions coordinate operations")
    
    def _process_action_phase(self):
        """Process action phase operations"""
        self.recent_narrative.append(f"Turn {self.turn_number}: Action phase - Operatives execute missions")
        
        # Simulate some mission results
        for faction in self.factions.values():
            if random.random() < 0.3:  # 30% chance of event
                self._generate_faction_event(faction)
    
    def _process_resolution_phase(self):
        """Process resolution phase outcomes"""
        self.recent_narrative.append(f"Turn {self.turn_number}: Resolution phase - Assessing operation outcomes")
        
        # Update faction resources
        for faction in self.factions.values():
            self._update_faction_resources(faction)
    
    def _generate_faction_event(self, faction: Faction):
        """Generate a random event for a faction"""
        events = [
            f"{faction.name} successfully recruits new operatives",
            f"{faction.name} operation encounters government resistance", 
            f"{faction.name} discovers valuable intelligence",
            f"{faction.name} faces internal loyalty challenges",
            f"{faction.name} establishes new safe house location"
        ]
        
        event = random.choice(events)
        self.recent_narrative.append(event)
    
    def _update_faction_resources(self, faction: Faction):
        """Update faction resources based on activities"""
        # Small random resource changes
        money_change = random.randint(-10, 20)
        influence_change = random.randint(-2, 5)
        personnel_change = random.randint(-1, 2)
        
        faction.resources["money"] = max(0, faction.resources["money"] + money_change)
        faction.resources["influence"] = max(0, faction.resources["influence"] + influence_change)
        faction.resources["personnel"] = max(1, faction.resources["personnel"] + personnel_change)
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get current game status summary"""
        active_agents = len([a for a in self.agents.values() if a.status == AgentStatus.ACTIVE])
        
        faction_resources = {}
        for faction_id, faction in self.factions.items():
            faction_resources[faction_id] = faction.resources.copy()
        
        return {
            "turn": self.turn_number,
            "phase": self.current_phase.value,
            "active_agents": active_agents,
            "total_agents": len(self.agents),
            "factions": faction_resources,
            "recent_narrative": self.recent_narrative[-10:],  # Last 10 events
            "active_events": self.active_events
        }
    
    def get_agent_locations(self) -> Dict[str, List[str]]:
        """Get agents grouped by location"""
        locations = {}
        
        for agent in self.agents.values():
            if agent.status == AgentStatus.ACTIVE:
                if agent.location_id not in locations:
                    locations[agent.location_id] = []
                
                faction_name = self.factions[agent.faction_id].name
                locations[agent.location_id].append(f"{agent.name} ({faction_name})")
        
        return locations 