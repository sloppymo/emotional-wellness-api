"""
Years of Lead - Core Game Loop MVP
Turn-based game engine with agents, factions, and locations
"""

import random
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from loguru import logger


class Phase(Enum):
    """Game phases within each day"""
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"


class TaskType(Enum):
    """Types of tasks agents can perform"""
    MOVE = "move"
    GATHER_INFO = "gather_info"
    RECRUIT = "recruit"
    SABOTAGE = "sabotage"
    PROPAGANDA = "propaganda"
    REST = "rest"
    RESCUE = "rescue"  # New: rescue captured agents
    INFILTRATE = "infiltrate"  # New: deep cover operations
    EXFILTRATE = "exfiltrate"  # New: escape missions


class SkillType(Enum):
    """Types of skills agents can develop"""
    COMBAT = "combat"
    STEALTH = "stealth"
    PERSUASION = "persuasion"
    TECHNICAL = "technical"
    MEDICAL = "medical"
    DRIVING = "driving"
    LEADERSHIP = "leadership"
    SURVIVAL = "survival"


class EquipmentType(Enum):
    """Types of equipment agents can use"""
    WEAPON = "weapon"
    ARMOR = "armor"
    VEHICLE = "vehicle"
    TOOL = "tool"
    MEDICAL = "medical"
    ELECTRONIC = "electronic"


class MissionType(Enum):
    """Types of multi-agent missions"""
    ASSAULT = "assault"  # Direct attack on a target
    INFILTRATION = "infiltration"  # Stealth infiltration with multiple roles
    RESCUE_OPERATION = "rescue_operation"  # Complex rescue with support
    SABOTAGE_RAID = "sabotage_raid"  # Coordinated sabotage
    INTELLIGENCE_GATHERING = "intelligence_gathering"  # Multi-agent intel op
    PROPAGANDA_CAMPAIGN = "propaganda_campaign"  # Coordinated propaganda


class AgentRole(Enum):
    """Roles agents can take in multi-agent missions"""
    LEADER = "leader"  # Mission commander, coordinates others
    INFILTRATOR = "infiltrator"  # Stealth specialist
    SUPPORT = "support"  # Provides backup and resources
    SPECIALIST = "specialist"  # Technical or combat specialist
    SCOUT = "scout"  # Reconnaissance and early warning
    MEDIC = "medic"  # Medical support and recovery
    TECHNICIAN = "technician"  # Technical operations
    COMBAT = "combat"  # Direct combat role


class EventType(Enum):
    """Types of random events that can occur"""
    SECURITY_CRACKDOWN = "security_crackdown"
    CIVIL_UNREST = "civil_unrest"
    INFORMANT_BETRAYAL = "informant_betrayal"
    SUPPLY_DROP = "supply_drop"
    AGENT_ESCAPE = "agent_escape"
    GOVERNMENT_ANNOUNCEMENT = "government_announcement"
    WEATHER_EVENT = "weather_event"
    BLACKOUT = "blackout"
    MASS_ARREST = "mass_arrest"
    PROTEST_ERUPTS = "protest_erupts"


@dataclass
class GameEvent:
    """A random event that affects the game world"""
    event_type: EventType
    location_id: Optional[str] = None
    affected_faction: Optional[str] = None
    description: str = ""
    duration: int = 1  # How many phases the event lasts
    effects: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MissionParticipant:
    """An agent participating in a multi-agent mission"""
    agent_id: str
    role: AgentRole
    assigned_task: Optional[str] = None  # Specific task within the mission
    coordination_bonus: int = 0  # Bonus from working with others
    risk_level: int = 1  # 1-5 scale of risk for this role


@dataclass
class Mission:
    """A multi-agent mission with coordination mechanics"""
    id: str
    mission_type: MissionType
    target_location_id: str
    participants: List[MissionParticipant] = field(default_factory=list)
    difficulty: int = 5  # 1-10 scale
    description: str = ""
    priority: int = 1  # 1-5 scale
    faction_id: str = ""
    phase_created: int = 0
    coordination_level: int = 0  # How well agents work together
    success_threshold: int = 50  # Percentage needed for success
    failure_penalty: int = 10  # Penalty for failure
    
    def add_participant(self, agent_id: str, role: AgentRole, risk_level: int = 1):
        """Add an agent to the mission"""
        participant = MissionParticipant(
            agent_id=agent_id,
            role=role,
            risk_level=risk_level
        )
        self.participants.append(participant)
        self._update_coordination()
    
    def remove_participant(self, agent_id: str):
        """Remove an agent from the mission"""
        self.participants = [p for p in self.participants if p.agent_id != agent_id]
        self._update_coordination()
    
    def _update_coordination(self):
        """Update coordination level based on participants and roles"""
        if len(self.participants) < 2:
            self.coordination_level = 0
            return
        
        # Base coordination from number of participants
        base_coordination = min(len(self.participants) * 10, 50)
        
        # Role synergy bonuses
        role_bonus = 0
        roles = [p.role for p in self.participants]
        
        # Leader provides coordination bonus
        if AgentRole.LEADER in roles:
            role_bonus += 20
        
        # Good role combinations
        if AgentRole.SCOUT in roles and AgentRole.INFILTRATOR in roles:
            role_bonus += 15  # Scout + Infiltrator synergy
        
        if AgentRole.MEDIC in roles and AgentRole.COMBAT in roles:
            role_bonus += 15  # Medic + Combat synergy
        
        if AgentRole.TECHNICIAN in roles and AgentRole.SPECIALIST in roles:
            role_bonus += 15  # Technical synergy
        
        # Support role provides general bonus
        support_count = roles.count(AgentRole.SUPPORT)
        role_bonus += support_count * 10
        
        self.coordination_level = min(base_coordination + role_bonus, 100)
    
    def get_mission_success_chance(self, agents: Dict[str, 'Agent']) -> int:
        """Calculate overall mission success chance"""
        if not self.participants:
            return 0
        
        # Base success from agent skills
        total_skill = sum(agents[p.agent_id].get_skill_level(p.role) for p in self.participants)
        avg_skill = total_skill / len(self.participants)
        
        # Coordination bonus
        coordination_bonus = self.coordination_level // 2
        
        # Role-specific bonuses
        role_bonus = 0
        for participant in self.participants:
            if participant.role == AgentRole.LEADER:
                role_bonus += 10
            elif participant.role == AgentRole.SPECIALIST:
                role_bonus += 5
            elif participant.role == AgentRole.SUPPORT:
                role_bonus += 3
        
        # Location modifier
        location = None  # Will be set by game state
        location_modifier = 0
        if location:
            location_modifier = location.get_task_modifier(TaskType.SABOTAGE)  # Use sabotage as base
        
        success_chance = int(avg_skill * 5 + coordination_bonus + role_bonus - location_modifier)
        return max(0, min(100, success_chance))


@dataclass
class Skill:
    """A skill that an agent can develop"""
    skill_type: SkillType
    level: int = 1  # 1-10 scale
    experience: int = 0  # Current experience points
    experience_to_next: int = 100  # Experience needed for next level
    
    def gain_experience(self, amount: int) -> bool:
        """Gain experience and return True if leveled up"""
        self.experience += amount
        if self.experience >= self.experience_to_next and self.level < 10:
            self.level += 1
            self.experience = 0
            self.experience_to_next = int(self.experience_to_next * 1.5)
            return True
        return False


@dataclass
class Task:
    """A task that an agent can perform"""
    task_type: TaskType
    target_location_id: Optional[str] = None
    difficulty: int = 5  # 1-10 scale
    description: str = ""
    priority: int = 1  # 1-5 scale, higher = more urgent
    faction_goal: str = ""  # What faction goal this serves
    mission_id: Optional[str] = None  # If this task is part of a mission


@dataclass
class Equipment:
    """Equipment that agents can use"""
    id: str
    name: str
    equipment_type: EquipmentType
    quality: int = 5  # 1-10 scale
    condition: int = 100  # 0-100, degrades with use
    skill_bonus: Dict[SkillType, int] = field(default_factory=dict)
    cost: int = 0
    description: str = ""
    
    def use(self, intensity: int = 1):
        """Use equipment and degrade its condition"""
        self.condition = max(0, self.condition - intensity)
    
    def repair(self, amount: int = 20):
        """Repair equipment"""
        self.condition = min(100, self.condition + amount)
    
    def get_effectiveness(self) -> float:
        """Get effectiveness based on condition and quality"""
        return (self.condition / 100.0) * (self.quality / 10.0)


@dataclass
class Agent:
    """An agent operating in the game world"""
    id: str
    name: str
    faction_id: str
    location_id: str
    task_queue: List[Task] = field(default_factory=list)
    skill_level: int = 5  # 1-10 scale (legacy, now use skills)
    status: str = "active"  # active, injured, captured, dead
    last_task_phase: int = 0  # Track when they last had a task
    
    # New LCS-inspired features
    skills: Dict[SkillType, Skill] = field(default_factory=dict)
    equipment: List[Equipment] = field(default_factory=list)
    background: str = "civilian"  # civilian, military, criminal, student, etc.
    loyalty: int = 75  # 0-100, affects reliability
    stress: int = 0  # 0-100, affects performance
    experience_points: int = 0  # General experience for background skills
    
    def __post_init__(self):
        """Initialize default skills for the agent"""
        # Ensure all skills are present, even if some were already assigned
        for skill_type in SkillType:
            if skill_type not in self.skills:
                self.skills[skill_type] = Skill(skill_type=skill_type, level=1)
    
    def add_task(self, task: Task):
        """Add a task to the agent's queue"""
        self.task_queue.append(task)
    
    def get_next_task(self) -> Optional[Task]:
        """Get the next task from the queue"""
        return self.task_queue.pop(0) if self.task_queue else None
    
    def has_tasks(self) -> bool:
        """Check if agent has any tasks"""
        return len(self.task_queue) > 0
    
    def get_skill_level(self, skill_type: SkillType) -> int:
        """Get effective skill level including equipment bonuses"""
        base_level = self.skills[skill_type].level
        
        # Add equipment bonuses
        equipment_bonus = 0
        for equipment in self.equipment:
            if skill_type in equipment.skill_bonus:
                equipment_bonus += int(equipment.skill_bonus[skill_type] * equipment.get_effectiveness())
        
        return min(10, base_level + equipment_bonus)
    
    def gain_skill_experience(self, skill_type: SkillType, amount: int):
        """Gain experience in a specific skill"""
        if skill_type in self.skills:
            leveled_up = self.skills[skill_type].gain_experience(amount)
            if leveled_up:
                logger.info(f"{self.name} improved {skill_type.value} to level {self.skills[skill_type].level}")
    
    def add_equipment(self, equipment: Equipment):
        """Add equipment to the agent"""
        self.equipment.append(equipment)
        logger.info(f"{self.name} acquired {equipment.name}")
    
    def remove_equipment(self, equipment_id: str) -> Optional[Equipment]:
        """Remove equipment from the agent"""
        for i, equipment in enumerate(self.equipment):
            if equipment.id == equipment_id:
                return self.equipment.pop(i)
        return None
    
    def use_equipment(self, equipment_id: str, intensity: int = 1):
        """Use equipment and degrade its condition"""
        for equipment in self.equipment:
            if equipment.id == equipment_id:
                equipment.use(intensity)
                if equipment.condition <= 0:
                    logger.info(f"{self.name}'s {equipment.name} is broken!")
                break
    
    def update_stress(self, change: int):
        """Update agent's stress level"""
        self.stress = max(0, min(100, self.stress + change))
        if self.stress > 80:
            logger.warning(f"{self.name} is under high stress!")
    
    def update_loyalty(self, change: int):
        """Update agent's loyalty"""
        self.loyalty = max(0, min(100, self.loyalty + change))
        if self.loyalty < 30:
            logger.warning(f"{self.name}'s loyalty is dangerously low!")


@dataclass
class Faction:
    """A faction in the game world"""
    id: str
    name: str
    resources: Dict[str, int] = field(default_factory=lambda: {
        "money": 100,
        "influence": 50, 
        "personnel": 10
    })
    goals: List[str] = field(default_factory=lambda: [
        "expand_influence", "recruit_members", "gather_intelligence", 
        "disrupt_government", "protect_territory"
    ])
    current_goal: str = "expand_influence"
    
    def can_afford(self, cost: Dict[str, int]) -> bool:
        """Check if faction can afford a cost"""
        for resource, amount in cost.items():
            if self.resources.get(resource, 0) < amount:
                return False
        return True
    
    def spend_resources(self, cost: Dict[str, int]):
        """Spend resources if available"""
        if self.can_afford(cost):
            for resource, amount in cost.items():
                self.resources[resource] -= amount
            return True
        return False
    
    def gain_resources(self, gain: Dict[str, int]):
        """Gain resources"""
        for resource, amount in gain.items():
            self.resources[resource] = self.resources.get(resource, 0) + amount
    
    def update_goal(self):
        """Update faction's current goal based on resources and situation"""
        if self.resources.get("influence", 0) < 30:
            self.current_goal = "expand_influence"
        elif self.resources.get("personnel", 0) < 8:
            self.current_goal = "recruit_members"
        elif self.resources.get("money", 0) < 100:
            self.current_goal = "gather_intelligence"
        else:
            self.current_goal = "disrupt_government"


@dataclass
class Location:
    """A location in the game world"""
    id: str
    name: str
    security_level: int = 5  # 1-10 scale (higher = more secure)
    unrest_level: int = 5   # 1-10 scale (higher = more unrest)
    active_events: List[GameEvent] = field(default_factory=list)
    
    def get_task_modifier(self, task_type: TaskType) -> int:
        """Get difficulty modifier for tasks in this location"""
        if task_type == TaskType.SABOTAGE:
            return self.security_level - 5  # High security makes sabotage harder
        elif task_type == TaskType.PROPAGANDA:
            return 5 - self.unrest_level   # High unrest makes propaganda easier
        elif task_type == TaskType.GATHER_INFO:
            return (self.security_level - 3) // 2  # Moderate security impact
        return 0
    
    def add_event(self, event: GameEvent):
        """Add an event to this location"""
        self.active_events.append(event)
    
    def remove_expired_events(self):
        """Remove events that have expired"""
        self.active_events = [e for e in self.active_events if e.duration > 0]
    
    def update_events(self):
        """Update event durations"""
        for event in self.active_events:
            event.duration -= 1


class GameState:
    """Core game state managing turns, phases, and world state"""
    
    def __init__(self):
        self.turn_number: int = 1
        self.current_phase: Phase = Phase.MORNING
        self.agents: Dict[str, Agent] = {}
        self.factions: Dict[str, Faction] = {}
        self.locations: Dict[str, Location] = {}
        self.narrative_log: List[str] = []
        self.phase_actions: List[Dict[str, Any]] = []
        self.active_events: List[GameEvent] = []
        self.active_missions: Dict[str, Mission] = {}  # New: active multi-agent missions
        self.mission_counter: int = 0  # For generating unique mission IDs
        self.task_generation_cooldown: int = 0  # Prevent too frequent task generation
        
        # New LCS/Dwarf Fortress inspired systems
        self.public_opinion: PublicOpinion = PublicOpinion()
        self.equipment_database: Dict[str, Equipment] = {}  # Available equipment templates
        self.weather_conditions: Dict[str, str] = {}  # Weather by location
        self.supply_chains: Dict[str, List[str]] = {}  # Resource flow tracking
        
        logger.info("Game state initialized")
    
    def add_agent(self, agent: Agent):
        """Add an agent to the game"""
        self.agents[agent.id] = agent
        logger.info(f"Added agent {agent.name} to {agent.location_id}")
    
    def add_faction(self, faction: Faction):
        """Add a faction to the game"""
        self.factions[faction.id] = faction
        logger.info(f"Added faction {faction.name}")
    
    def add_location(self, location: Location):
        """Add a location to the game"""
        self.locations[location.id] = location
        logger.info(f"Added location {location.name}")
    
    def create_mission(self, mission_type: MissionType, target_location_id: str, 
                      faction_id: str, difficulty: int = 5, description: str = "") -> Mission:
        """Create a new multi-agent mission"""
        self.mission_counter += 1
        mission_id = f"mission_{self.mission_counter}"
        
        mission = Mission(
            id=mission_id,
            mission_type=mission_type,
            target_location_id=target_location_id,
            faction_id=faction_id,
            difficulty=difficulty,
            description=description,
            phase_created=self.turn_number
        )
        
        self.active_missions[mission_id] = mission
        logger.info(f"Created mission {mission_id}: {mission_type.value} at {target_location_id}")
        return mission
    
    def add_agent_to_mission(self, mission_id: str, agent_id: str, role: AgentRole, risk_level: int = 1) -> bool:
        """Add an agent to a mission with a specific role"""
        if mission_id not in self.active_missions:
            logger.warning(f"Mission {mission_id} not found")
            return False
        
        if agent_id not in self.agents:
            logger.warning(f"Agent {agent_id} not found")
            return False
        
        mission = self.active_missions[mission_id]
        agent = self.agents[agent_id]
        
        # Check if agent is available and from the same faction
        if agent.status != "active":
            logger.warning(f"Agent {agent.name} is not active (status: {agent.status})")
            return False
        
        if agent.faction_id != mission.faction_id:
            logger.warning(f"Agent {agent.name} is not from the same faction as mission")
            return False
        
        # Check if agent is already in this mission
        existing_participant = next((p for p in mission.participants if p.agent_id == agent_id), None)
        if existing_participant:
            logger.warning(f"Agent {agent.name} is already in mission {mission_id}")
            return False
        
        mission.add_participant(agent_id, role, risk_level)
        logger.info(f"Added {agent.name} to mission {mission_id} as {role.value}")
        return True
    
    def execute_mission(self, mission_id: str) -> Dict[str, Any]:
        """Execute a multi-agent mission and return results"""
        if mission_id not in self.active_missions:
            return {"success": False, "error": "Mission not found"}
        
        mission = self.active_missions[mission_id]
        
        if len(mission.participants) < 2:
            return {"success": False, "error": "Mission needs at least 2 participants"}
        
        # Calculate success chance
        success_chance = mission.get_mission_success_chance(self.agents)
        
        # Apply location modifier
        if mission.target_location_id in self.locations:
            location = self.locations[mission.target_location_id]
            location_modifier = location.get_task_modifier(TaskType.SABOTAGE)
            success_chance = max(0, min(100, success_chance - location_modifier))
        
        # Roll for success
        roll = random.randint(1, 100)
        success = roll <= success_chance
        
        # Generate mission narrative
        narrative = self._generate_mission_narrative(mission, success, roll, success_chance)
        self._log_narrative(narrative)
        
        # Apply mission outcomes
        results = self._apply_mission_outcomes(mission, success, roll, success_chance)
        
        # Remove completed mission
        del self.active_missions[mission_id]
        
        return results
    
    def _generate_mission_narrative(self, mission: Mission, success: bool, roll: int, success_chance: int) -> str:
        """Generate narrative for mission execution"""
        location_name = self.locations[mission.target_location_id].name
        participant_names = [self.agents[p.agent_id].name for p in mission.participants]
        
        if success:
            narratives = {
                MissionType.ASSAULT: f"🎯 {', '.join(participant_names)} launch a coordinated assault on {location_name}",
                MissionType.INFILTRATION: f"🕵️ {', '.join(participant_names)} execute a stealth infiltration of {location_name}",
                MissionType.RESCUE_OPERATION: f"🚨 {', '.join(participant_names)} conduct a daring rescue operation in {location_name}",
                MissionType.SABOTAGE_RAID: f"💥 {', '.join(participant_names)} carry out coordinated sabotage in {location_name}",
                MissionType.INTELLIGENCE_GATHERING: f"📊 {', '.join(participant_names)} gather intelligence from {location_name}",
                MissionType.PROPAGANDA_CAMPAIGN: f"📢 {', '.join(participant_names)} launch a propaganda campaign in {location_name}"
            }
            base_narrative = narratives.get(mission.mission_type, f"{', '.join(participant_names)} complete their mission in {location_name}")
            
            # Add coordination details
            if mission.coordination_level > 70:
                base_narrative += " - Perfect coordination!"
            elif mission.coordination_level > 50:
                base_narrative += " - Good teamwork!"
            else:
                base_narrative += " - Basic coordination."
                
        else:
            narratives = {
                MissionType.ASSAULT: f"💥 {', '.join(participant_names)}'s assault on {location_name} is repelled",
                MissionType.INFILTRATION: f"🚨 {', '.join(participant_names)}'s infiltration of {location_name} is discovered",
                MissionType.RESCUE_OPERATION: f"❌ {', '.join(participant_names)}'s rescue operation in {location_name} fails",
                MissionType.SABOTAGE_RAID: f"💥 {', '.join(participant_names)}'s sabotage raid on {location_name} is foiled",
                MissionType.INTELLIGENCE_GATHERING: f"📊 {', '.join(participant_names)}'s intelligence gathering in {location_name} yields nothing",
                MissionType.PROPAGANDA_CAMPAIGN: f"📢 {', '.join(participant_names)}'s propaganda campaign in {location_name} backfires"
            }
            base_narrative = narratives.get(mission.mission_type, f"{', '.join(participant_names)}'s mission in {location_name} fails")
        
        return f"{base_narrative} (Roll: {roll}/{success_chance})"
    
    def _apply_mission_outcomes(self, mission: Mission, success: bool, roll: int, success_chance: int) -> Dict[str, Any]:
        """Apply the outcomes of a mission to game state"""
        results = {
            "mission_id": mission.id,
            "success": success,
            "roll": roll,
            "success_chance": success_chance,
            "participants": [p.agent_id for p in mission.participants],
            "coordination_level": mission.coordination_level
        }
        
        if success:
            # Mission success rewards
            faction = self.factions[mission.faction_id]
            
            rewards = {
                MissionType.ASSAULT: {"influence": 10, "money": 20},
                MissionType.INFILTRATION: {"influence": 15, "money": 15},
                MissionType.RESCUE_OPERATION: {"influence": 20, "money": 10},
                MissionType.SABOTAGE_RAID: {"influence": 12, "money": 18},
                MissionType.INTELLIGENCE_GATHERING: {"influence": 8, "money": 25},
                MissionType.PROPAGANDA_CAMPAIGN: {"influence": 18, "money": 8}
            }
            
            reward = rewards.get(mission.mission_type, {"influence": 10, "money": 10})
            faction.gain_resources(reward)
            results["rewards"] = reward
            
            # Location effects
            if mission.target_location_id in self.locations:
                location = self.locations[mission.target_location_id]
                if mission.mission_type in [MissionType.ASSAULT, MissionType.SABOTAGE_RAID]:
                    location.security_level = max(1, location.security_level - 1)
                    location.unrest_level = min(10, location.unrest_level + 2)
                elif mission.mission_type == MissionType.PROPAGANDA_CAMPAIGN:
                    location.unrest_level = min(10, location.unrest_level + 3)
            
            # Participant experience gains
            for participant in mission.participants:
                agent = self.agents[participant.agent_id]
                if agent.skill_level < 10 and random.randint(1, 100) <= 30:  # 30% chance to gain skill
                    agent.skill_level += 1
                    self._log_narrative(f"🎯 {agent.name} gains experience from the mission!")
            
        else:
            # Mission failure consequences
            results["penalties"] = {"influence": -5, "money": -10}
            faction = self.factions[mission.faction_id]
            faction.gain_resources({"influence": -5, "money": -10})
            
            # Risk of injury/capture for participants
            for participant in mission.participants:
                agent = self.agents[participant.agent_id]
                risk_roll = random.randint(1, 100)
                risk_threshold = participant.risk_level * 15  # Higher risk roles = higher chance of consequences
                
                if risk_roll <= risk_threshold:
                    if random.choice([True, False]):
                        agent.status = "injured"
                        self._log_narrative(f"💥 {agent.name} is injured during the failed mission!")
                    else:
                        agent.status = "captured"
                        self._log_narrative(f"🚨 {agent.name} is captured during the failed mission!")
        
        return results
    
    def advance_turn(self):
        """Advance to the next phase/turn"""
        # Process current phase
        self._process_current_phase()
        
        # Generate random events
        self._generate_random_events()
        
        # Generate new tasks for agents
        self._generate_agent_tasks()
        
        # Update faction goals
        self._update_faction_goals()
        
        # Update and clean up events
        self._update_events()
        
        # Advance phase
        phases = list(Phase)
        current_index = phases.index(self.current_phase)
        
        if current_index < len(phases) - 1:
            # Move to next phase in same turn
            self.current_phase = phases[current_index + 1]
        else:
            # Start new turn
            self.turn_number += 1
            self.current_phase = Phase.MORNING
            self._log_narrative(f"--- Day {self.turn_number} begins ---")
        
        logger.info(f"Advanced to Turn {self.turn_number}, {self.current_phase.value}")
    
    def _process_current_phase(self):
        """Process all agent tasks for the current phase"""
        self.phase_actions = []
        
        self._log_narrative(f"=== {self.current_phase.value.title()} Phase ===")
        
        # Process one task per agent
        for agent in self.agents.values():
            if agent.status == "active":
                self._process_agent_task(agent)
        
        # Update faction resources based on outcomes
        self._update_faction_resources()
    
    def _process_agent_task(self, agent: Agent):
        """Process a single agent's task for this phase"""
        task = agent.get_next_task()
        
        if not task:
            # Agent rests if no tasks
            self._rest_agent(agent)
            return
        
        # Calculate success probability
        success = self._resolve_task(agent, task)
        
        # Generate narrative and apply outcomes
        narrative = self._generate_task_narrative(agent, task, success)
        self._log_narrative(narrative)
        
        # Record action for faction resource updates
        self.phase_actions.append({
            "agent_id": agent.id,
            "faction_id": agent.faction_id,
            "task_type": task.task_type,
            "success": success,
            "location_id": agent.location_id
        })
        
        # Apply task outcomes
        self._apply_task_outcomes(agent, task, success)
    
    def _resolve_task(self, agent: Agent, task: Task) -> bool:
        """Resolve a task and return success/failure"""
        # Get base skill level for the task type
        skill_type = self._get_skill_for_task(task.task_type)
        base_skill = agent.get_skill_level(skill_type)
        
        # Apply location modifiers
        location = self.locations.get(agent.location_id)
        location_modifier = 0
        if location:
            location_modifier = location.get_task_modifier(task.task_type)
        
        # Apply equipment bonuses
        equipment_bonus = self._calculate_equipment_bonus(agent, task.task_type)
        
        # Apply stress penalty
        stress_penalty = agent.stress // 20  # High stress reduces effectiveness
        
        # Calculate final success chance
        effective_skill = base_skill + equipment_bonus - location_modifier - stress_penalty
        success_chance = max(0, min(100, effective_skill * 10 - task.difficulty * 5))
        
        # Roll for success
        roll = random.randint(1, 100)
        success = roll <= success_chance
        
        # Log the resolution
        logger.debug(f"Task resolution: {agent.name} - {task.task_type.value} - Chance: {success_chance}%, Roll: {roll}, Success: {success}")
        
        # Generate narrative
        narrative = self._generate_task_narrative(agent, task, success)
        self._log_narrative(narrative)
        
        # Apply outcomes
        self._apply_task_outcomes(agent, task, success)
        
        # Update skills and equipment
        self._update_agent_progression(agent, task, success, skill_type)
        
        # Update public opinion
        self._update_public_opinion(task, agent.faction_id, success)
        
        return success
    
    def _get_skill_for_task(self, task_type: TaskType) -> SkillType:
        """Get the primary skill used for a task type"""
        skill_mapping = {
            TaskType.MOVE: SkillType.SURVIVAL,
            TaskType.GATHER_INFO: SkillType.STEALTH,
            TaskType.RECRUIT: SkillType.PERSUASION,
            TaskType.SABOTAGE: SkillType.TECHNICAL,
            TaskType.PROPAGANDA: SkillType.PERSUASION,
            TaskType.RESCUE: SkillType.COMBAT,
            TaskType.INFILTRATE: SkillType.STEALTH,
            TaskType.EXFILTRATE: SkillType.SURVIVAL,
            TaskType.REST: SkillType.SURVIVAL
        }
        return skill_mapping.get(task_type, SkillType.SURVIVAL)
    
    def _calculate_equipment_bonus(self, agent: Agent, task_type: TaskType) -> int:
        """Calculate equipment bonus for a task"""
        skill_type = self._get_skill_for_task(task_type)
        bonus = 0
        
        for equipment in agent.equipment:
            if skill_type in equipment.skill_bonus:
                effectiveness = equipment.get_effectiveness()
                bonus += int(equipment.skill_bonus[skill_type] * effectiveness)
        
        return bonus
    
    def _update_agent_progression(self, agent: Agent, task: Task, success: bool, skill_type: SkillType):
        """Update agent skills, equipment, and stress based on task outcome"""
        # Gain skill experience
        base_experience = 10 if success else 5
        agent.gain_skill_experience(skill_type, base_experience)
        
        # Update stress
        stress_change = -5 if success else 10  # Success reduces stress, failure increases it
        agent.update_stress(stress_change)
        
        # Use equipment (degrade condition)
        for equipment in agent.equipment:
            if skill_type in equipment.skill_bonus:
                intensity = 2 if not success else 1  # Failed tasks use equipment more intensely
                agent.use_equipment(equipment.id, intensity)
        
        # Update loyalty based on task type
        if task.task_type == TaskType.RESCUE and success:
            agent.update_loyalty(5)  # Successful rescues increase loyalty
        elif not success and random.randint(1, 100) <= 20:  # 20% chance of loyalty loss on failure
            agent.update_loyalty(-5)
    
    def _update_public_opinion(self, task: Task, faction_id: str, success: bool):
        """Update public opinion based on task outcome"""
        action_type = task.task_type.value
        casualties = 0  # Could be calculated based on task type and outcome
        
        self.public_opinion.update_from_action(action_type, faction_id, success, casualties)
    
    def _generate_task_narrative(self, agent: Agent, task: Task, success: bool) -> str:
        """Generate narrative description for the task"""
        location_name = self.locations.get(agent.location_id, type('obj', (object,), {'name': 'unknown location'})).name
        
        narratives = {
            TaskType.MOVE: {
                True: [
                    f"{agent.name} slips through the shadows, reaching the target area undetected",
                    f"{agent.name} navigates the checkpoints with false papers, blending into the crowd",
                    f"{agent.name} takes the long route through backstreets, avoiding the patrols"
                ],
                False: [
                    f"{agent.name} is stopped at a checkpoint and forced to turn back",
                    f"{agent.name} loses their way in the maze of side streets",
                    f"{agent.name} draws unwanted attention and must abort the mission"
                ]
            },
            TaskType.GATHER_INFO: {
                True: [
                    f"{agent.name} overhears crucial intelligence at a café in {location_name}",
                    f"{agent.name} befriends a talkative guard, learning about security protocols",
                    f"{agent.name} finds discarded documents that reveal enemy plans"
                ],
                False: [
                    f"{agent.name} asks too many questions and arouses suspicion in {location_name}",
                    f"{agent.name} gets nothing but rumors and misinformation",
                    f"{agent.name} is nearly caught eavesdropping and must flee"
                ]
            },
            TaskType.SABOTAGE: {
                True: [
                    f"{agent.name} plants explosives in a key facility in {location_name}",
                    f"{agent.name} cuts power lines, plunging the district into darkness",
                    f"{agent.name} derails a supply train, disrupting enemy logistics"
                ],
                False: [
                    f"{agent.name} triggers an alarm while attempting sabotage in {location_name}",
                    f"{agent.name}'s bomb fails to detonate properly",
                    f"{agent.name} is spotted by security and must abandon the mission"
                ]
            },
            TaskType.PROPAGANDA: {
                True: [
                    f"{agent.name} distributes leaflets that inspire the people of {location_name}",
                    f"{agent.name} gives a rousing speech that wins new supporters",
                    f"{agent.name} spreads word of recent victories, boosting morale"
                ],
                False: [
                    f"{agent.name}'s propaganda is dismissed as extremist nonsense",
                    f"{agent.name} is shouted down by hostile crowds in {location_name}",
                    f"{agent.name}'s leaflets are confiscated before distribution"
                ]
            },
            TaskType.RECRUIT: {
                True: [
                    f"{agent.name} convinces a sympathetic civilian to join the cause",
                    f"{agent.name} recruits a disillusioned government worker",
                    f"{agent.name} finds volunteers among the unemployed youth"
                ],
                False: [
                    f"{agent.name}'s recruitment attempt backfires, alerting authorities",
                    f"{agent.name} misjudges their contact, who reports them",
                    f"{agent.name} finds only fear and apathy among potential recruits"
                ]
            },
            TaskType.RESCUE: {
                True: [
                    f"{agent.name} successfully breaks a captured comrade out of custody",
                    f"{agent.name} orchestrates a daring prison break under cover of darkness",
                    f"{agent.name} bribes guards to secure a comrade's release"
                ],
                False: [
                    f"{agent.name}'s rescue attempt is discovered and foiled",
                    f"{agent.name} arrives too late - the prisoner has been moved",
                    f"{agent.name} is captured during the rescue operation"
                ]
            },
            TaskType.INFILTRATE: {
                True: [
                    f"{agent.name} successfully infiltrates the target facility",
                    f"{agent.name} assumes a false identity and gains access",
                    f"{agent.name} uses forged credentials to enter restricted areas"
                ],
                False: [
                    f"{agent.name}'s cover is blown during infiltration",
                    f"{agent.name} is denied access at the security checkpoint",
                    f"{agent.name} is recognized and forced to flee"
                ]
            },
            TaskType.EXFILTRATE: {
                True: [
                    f"{agent.name} successfully extracts sensitive information",
                    f"{agent.name} escapes with valuable intelligence",
                    f"{agent.name} completes the mission and evades pursuit"
                ],
                False: [
                    f"{agent.name} is caught while trying to escape",
                    f"{agent.name} loses the intelligence during the escape",
                    f"{agent.name} is pursued and must abandon the mission"
                ]
            },
            TaskType.REST: {
                True: [
                    f"{agent.name} finds a safe house to recover and plan",
                    f"{agent.name} tends to their wounds and regains strength",
                    f"{agent.name} uses the quiet time to study enemy patterns"
                ],
                False: [
                    f"{agent.name} is pursued even while trying to rest",
                    f"{agent.name}'s safe house has been compromised",
                    f"{agent.name} remains on edge, unable to truly rest"
                ]
            }
        }
        
        options = narratives.get(task.task_type, {}).get(success, [f"{agent.name} attempts {task.task_type.value}"])
        return random.choice(options) if options else f"{agent.name} attempts {task.task_type.value}"
    
    def _apply_task_outcomes(self, agent: Agent, task: Task, success: bool):
        """Apply the outcomes of a task to game state"""
        if task.task_type == TaskType.MOVE and success and task.target_location_id:
            agent.location_id = task.target_location_id
            logger.debug(f"{agent.name} moved to {task.target_location_id}")
        
        # Handle rescue missions
        if task.task_type == TaskType.RESCUE and success:
            # Check if a specific target is mentioned in the task description
            target_agent = None
            if task.description and task.description.startswith("Rescue "):
                target_name = task.description[7:]  # Remove "Rescue " prefix
                target_agent = next((a for a in self.agents.values() 
                                   if a.name == target_name and a.status == "captured"), None)
            
            # If no specific target or target not found, find any captured agent from same faction
            if not target_agent:
                captured_agents = [a for a in self.agents.values() 
                                 if a.faction_id == agent.faction_id and a.status == "captured"]
                if captured_agents:
                    target_agent = random.choice(captured_agents)
            
            if target_agent:
                target_agent.status = "active"
                # Move rescued agent to the rescuer's location
                target_agent.location_id = agent.location_id
                self._log_narrative(f"🎉 {target_agent.name} has been rescued by {agent.name} and is now in {self.locations[agent.location_id].name}!")
                logger.debug(f"Rescue successful: {target_agent.name} status changed from captured to active")
            else:
                self._log_narrative(f"{agent.name} searches for captured comrades but finds none to rescue")
        
        # Failure consequences
        if not success:
            # Small chance of injury or capture on failure
            if random.randint(1, 100) <= 10:  # 10% chance
                if random.choice([True, False]):
                    agent.status = "injured"
                    self._log_narrative(f"{agent.name} is injured in the attempt!")
                else:
                    agent.status = "captured"
                    self._log_narrative(f"{agent.name} has been captured!")
    
    def _rest_agent(self, agent: Agent):
        """Agent rests when no tasks available"""
        rest_narrative = random.choice([
            f"{agent.name} keeps a low profile, watching and waiting",
            f"{agent.name} uses the quiet time to maintain equipment",
            f"{agent.name} studies local patterns and routines"
        ])
        self._log_narrative(rest_narrative)
        
        # Resting heals injured agents
        if agent.status == "injured" and random.randint(1, 100) <= 50:  # 50% chance to heal
            agent.status = "active"
            self._log_narrative(f"{agent.name} has recovered from their injuries")
    
    def _update_faction_resources(self):
        """Update faction resources based on phase actions"""
        for faction in self.factions.values():
            # Count successful actions by faction
            faction_actions = [a for a in self.phase_actions if a["faction_id"] == faction.id]
            successful_actions = [a for a in faction_actions if a["success"]]
            
            # Gain resources from successful actions
            for action in successful_actions:
                if action["task_type"] == TaskType.RECRUIT:
                    faction.gain_resources({"personnel": 1})
                elif action["task_type"] == TaskType.GATHER_INFO:
                    faction.gain_resources({"influence": 2})
                elif action["task_type"] == TaskType.SABOTAGE:
                    faction.gain_resources({"influence": 3})
                elif action["task_type"] == TaskType.PROPAGANDA:
                    faction.gain_resources({"influence": 1})
                elif action["task_type"] == TaskType.INFILTRATE:
                    faction.gain_resources({"influence": 4, "money": 10})
                elif action["task_type"] == TaskType.EXFILTRATE:
                    faction.gain_resources({"influence": 5, "money": 15})
            
            # Basic resource generation
            faction.gain_resources({"money": 5})  # Basic income
    
    def _log_narrative(self, message: str):
        """Add a narrative entry to the log"""
        self.narrative_log.append(message)
        logger.info(f"[NARRATIVE] {message}")
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get current game status summary"""
        active_agents = sum(1 for agent in self.agents.values() if agent.status == "active")
        
        # Get active events
        active_events = []
        for event in self.active_events:
            if event.duration > 0:
                active_events.append(f"{event.description} ({event.duration} phases left)")
        
        # Get location events
        location_events = {}
        for location in self.locations.values():
            if location.active_events:
                location_events[location.id] = [e.description for e in location.active_events if e.duration > 0]
        
        return {
            "turn": self.turn_number,
            "phase": self.current_phase.value,
            "active_agents": active_agents,
            "total_agents": len(self.agents),
            "factions": {fid: f.resources for fid, f in self.factions.items()},
            "recent_narrative": self.narrative_log[-5:] if self.narrative_log else [],
            "active_events": active_events,
            "location_events": location_events
        }
    
    def get_agent_locations(self) -> Dict[str, List[str]]:
        """Get agents organized by location"""
        locations = {}
        for agent in self.agents.values():
            if agent.location_id not in locations:
                locations[agent.location_id] = []
            locations[agent.location_id].append(f"{agent.name} ({agent.status})")
        return locations

    def _generate_random_events(self):
        """Generate random events based on current game state"""
        # 15% chance of a random event each phase
        if random.random() < 0.15:
            event = self._create_random_event()
            if event:
                self.active_events.append(event)
                self._log_narrative(f"🚨 {event.description}")
                self._apply_event_effects(event)
    
    def _create_random_event(self) -> Optional[GameEvent]:
        """Create a random event based on current game state"""
        event_type = random.choice(list(EventType))
        location = random.choice(list(self.locations.values()))
        
        events = {
            EventType.SECURITY_CRACKDOWN: {
                "description": f"Security forces launch a crackdown in {location.name}",
                "effects": {"security_increase": 2, "unrest_increase": 1}
            },
            EventType.CIVIL_UNREST: {
                "description": f"Civil unrest erupts in {location.name}",
                "effects": {"unrest_increase": 3, "security_increase": 1}
            },
            EventType.INFORMANT_BETRAYAL: {
                "description": f"An informant betrays the resistance in {location.name}",
                "effects": {"security_increase": 1, "agent_risk": True}
            },
            EventType.SUPPLY_DROP: {
                "description": f"Allied forces drop supplies in {location.name}",
                "effects": {"faction_resources": {"money": 20, "influence": 5}}
            },
            EventType.AGENT_ESCAPE: {
                "description": f"A captured agent escapes from custody",
                "effects": {"free_captured_agent": True}
            },
            EventType.GOVERNMENT_ANNOUNCEMENT: {
                "description": "Government announces new security measures",
                "effects": {"global_security_increase": 1}
            },
            EventType.WEATHER_EVENT: {
                "description": f"Severe weather affects operations in {location.name}",
                "effects": {"task_difficulty_increase": 2}
            },
            EventType.BLACKOUT: {
                "description": f"Power blackout plunges {location.name} into darkness",
                "effects": {"security_decrease": 1, "sabotage_bonus": True}
            },
            EventType.MASS_ARREST: {
                "description": f"Mass arrests sweep through {location.name}",
                "effects": {"agent_risk": True, "unrest_increase": 2}
            },
            EventType.PROTEST_ERUPTS: {
                "description": f"Spontaneous protests erupt in {location.name}",
                "effects": {"unrest_increase": 2, "propaganda_bonus": True}
            }
        }
        
        event_data = events.get(event_type, {})
        if event_data:
            return GameEvent(
                event_type=event_type,
                location_id=location.id,
                description=event_data["description"],
                effects=event_data.get("effects", {}),
                duration=random.randint(1, 3)  # Events last 1-3 phases
            )
        return None
    
    def _apply_event_effects(self, event: GameEvent):
        """Apply the effects of an event to the game state"""
        effects = event.effects
        
        # Apply location-specific effects
        if event.location_id and event.location_id in self.locations:
            location = self.locations[event.location_id]
            
            if "security_increase" in effects:
                location.security_level = min(10, location.security_level + effects["security_increase"])
            if "security_decrease" in effects:
                location.security_level = max(1, location.security_level - effects["security_decrease"])
            if "unrest_increase" in effects:
                location.unrest_level = min(10, location.unrest_level + effects["unrest_increase"])
            
            location.add_event(event)
        
        # Apply global effects
        if "global_security_increase" in effects:
            for loc in self.locations.values():
                loc.security_level = min(10, loc.security_level + effects["global_security_increase"])
        
        # Apply faction resource effects
        if "faction_resources" in effects:
            for faction in self.factions.values():
                faction.gain_resources(effects["faction_resources"])
        
        # Handle agent escape
        if "free_captured_agent" in effects:
            captured_agents = [a for a in self.agents.values() if a.status == "captured"]
            if captured_agents:
                agent = random.choice(captured_agents)
                agent.status = "active"
                self._log_narrative(f"🎉 {agent.name} has escaped from captivity!")
    
    def _generate_agent_tasks(self):
        """Generate new tasks for agents based on faction goals and current situation"""
        # Only generate tasks every 2-3 phases to avoid overwhelming
        self.task_generation_cooldown -= 1
        if self.task_generation_cooldown > 0:
            return
        
        self.task_generation_cooldown = random.randint(2, 3)
        
        for faction in self.factions.values():
            faction.update_goal()
            faction_agents = [a for a in self.agents.values() if a.faction_id == faction.id and a.status == "active"]
            
            # Generate tasks based on faction goal
            for agent in faction_agents:
                if not agent.has_tasks() and random.random() < 0.7:  # 70% chance to get new task
                    task = self._create_task_for_goal(faction.current_goal, agent)
                    if task:
                        agent.add_task(task)
                        self._log_narrative(f"📋 {agent.name} receives new mission: {task.description}")
    
    def _create_task_for_goal(self, goal: str, agent: Agent) -> Optional[Task]:
        """Create a task based on faction goal and agent capabilities"""
        tasks_by_goal = {
            "expand_influence": [
                (TaskType.PROPAGANDA, "Spread revolutionary ideas", 4),
                (TaskType.RECRUIT, "Recruit new supporters", 5),
                (TaskType.GATHER_INFO, "Learn about local sentiment", 3)
            ],
            "recruit_members": [
                (TaskType.RECRUIT, "Recruit from local population", 5),
                (TaskType.PROPAGANDA, "Inspire potential recruits", 4),
                (TaskType.GATHER_INFO, "Identify recruitment targets", 4)
            ],
            "gather_intelligence": [
                (TaskType.GATHER_INFO, "Monitor government activities", 5),
                (TaskType.INFILTRATE, "Infiltrate government facility", 7),
                (TaskType.MOVE, "Reconnaissance mission", 4)
            ],
            "disrupt_government": [
                (TaskType.SABOTAGE, "Sabotage government operations", 7),
                (TaskType.INFILTRATE, "Infiltrate secure facility", 8),
                (TaskType.EXFILTRATE, "Extract sensitive information", 6)
            ],
            "protect_territory": [
                (TaskType.GATHER_INFO, "Monitor security threats", 4),
                (TaskType.PROPAGANDA, "Maintain local support", 3),
                (TaskType.RECRUIT, "Strengthen local network", 4)
            ]
        }
        
        if goal in tasks_by_goal:
            task_type, description, difficulty = random.choice(tasks_by_goal[goal])
            
            # Adjust difficulty based on agent skill and location
            location = self.locations.get(agent.location_id)
            if location:
                difficulty += location.get_task_modifier(task_type)
            
            difficulty = max(1, min(10, difficulty))  # Clamp between 1-10
            
            # For movement tasks, pick a target location
            target_location = None
            if task_type == TaskType.MOVE:
                available_locations = [loc for loc in self.locations.values() if loc.id != agent.location_id]
                if available_locations:
                    target_location = random.choice(available_locations).id
            
            return Task(
                task_type=task_type,
                target_location_id=target_location,
                difficulty=difficulty,
                description=description,
                priority=random.randint(1, 3),
                faction_goal=goal
            )
        
        return None
    
    def _update_faction_goals(self):
        """Update faction goals based on current situation"""
        for faction in self.factions.values():
            # Check if faction needs to rescue captured agents
            captured_agents = [a for a in self.agents.values() if a.faction_id == faction.id and a.status == "captured"]
            if captured_agents and random.random() < 0.3:  # 30% chance to prioritize rescue
                faction.current_goal = "protect_territory"
                # Add rescue tasks
                active_agents = [a for a in self.agents.values() if a.faction_id == faction.id and a.status == "active"]
                for agent in active_agents[:2]:  # Limit to 2 rescue attempts
                    if not agent.has_tasks():
                        rescue_task = Task(
                            task_type=TaskType.RESCUE,
                            difficulty=6,
                            description="Rescue captured comrade",
                            priority=5,
                            faction_goal="protect_territory"
                        )
                        agent.add_task(rescue_task)
                        self._log_narrative(f"🆘 {agent.name} is assigned a rescue mission")
    
    def _update_events(self):
        """Update and clean up expired events"""
        # Update global events
        self.active_events = [e for e in self.active_events if e.duration > 0]
        for event in self.active_events:
            event.duration -= 1
        
        # Update location events
        for location in self.locations.values():
            location.update_events()
            location.remove_expired_events()

@dataclass
class PublicOpinion:
    """Public opinion tracking system"""
    general_support: int = 50  # 0-100, general public support
    faction_support: Dict[str, int] = field(default_factory=lambda: {"resistance": 50, "students": 50, "workers": 50})
    media_coverage: List[str] = field(default_factory=list)  # Recent news events
    political_influence: int = 0  # -100 to 100, influence with government
    community_relations: Dict[str, int] = field(default_factory=dict)  # Support from different communities
    
    def update_from_action(self, action_type: str, faction_id: str, success: bool, casualties: int = 0):
        """Update public opinion based on an action"""
        base_change = 5 if success else -10
        
        # Adjust based on action type
        if action_type == "propaganda":
            base_change += 10
        elif action_type == "sabotage":
            base_change -= 5
        elif action_type == "rescue":
            base_change += 15
        
        # Casualties reduce support
        base_change -= casualties * 2
        
        # Update faction support
        if faction_id in self.faction_support:
            self.faction_support[faction_id] = max(0, min(100, 
                self.faction_support[faction_id] + base_change))
        
        # Update general support
        self.general_support = max(0, min(100, self.general_support + base_change // 2))
        
        # Generate media coverage
        if abs(base_change) > 10:
            self.media_coverage.append(f"{'Positive' if base_change > 0 else 'Negative'} coverage of {action_type} operation")
            if len(self.media_coverage) > 5:
                self.media_coverage.pop(0)  # Keep only recent events 