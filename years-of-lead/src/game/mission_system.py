"""
Years of Lead - Advanced Mission System

Comprehensive mission mechanics with planning, execution, and resolution phases.
Includes expanded mission types, random events, and complex success calculations.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set
import random
import math
from datetime import datetime

from .core import Agent, AgentStatus, SkillType, Location, Equipment


class MissionType(Enum):
    """Expanded mission types with varied objectives and mechanics"""
    # Intelligence Operations
    INTELLIGENCE_GATHERING = "intelligence_gathering"
    SURVEILLANCE = "surveillance"
    INFORMANT_RECRUITMENT = "informant_recruitment"
    DOCUMENT_THEFT = "document_theft"
    
    # Propaganda Operations
    PROPAGANDA_CAMPAIGN = "propaganda_campaign"
    LEAFLET_DISTRIBUTION = "leaflet_distribution"
    RADIO_BROADCAST = "radio_broadcast"
    GRAFFITI_CAMPAIGN = "graffiti_campaign"
    
    # Direct Action
    SABOTAGE = "sabotage"
    INFRASTRUCTURE_DISRUPTION = "infrastructure_disruption"
    SUPPLY_LINE_ATTACK = "supply_line_attack"
    EQUIPMENT_DESTRUCTION = "equipment_destruction"
    
    # Personnel Operations
    RECRUITMENT_DRIVE = "recruitment_drive"
    IDEOLOGICAL_CONVERSION = "ideological_conversion"
    SKILL_TRAINING = "skill_training"
    
    # High-Risk Operations
    RESCUE_OPERATION = "rescue_operation"
    PRISONER_EXTRACTION = "prisoner_extraction"
    DEFECTOR_PROTECTION = "defector_protection"
    ASSASSINATION = "assassination"
    BANK_ROBBERY = "bank_robbery"
    PRISON_BREAK = "prison_break"


class MissionPhase(Enum):
    """Mission execution phases"""
    PLANNING = "planning"
    INFILTRATION = "infiltration"
    EXECUTION = "execution"
    EXTRACTION = "extraction"
    AFTERMATH = "aftermath"


class MissionStatus(Enum):
    """Mission status states"""
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"
    COMPROMISED = "compromised"


class EventCategory(Enum):
    """Categories of random events during missions"""
    SECURITY = "security"
    ENVIRONMENTAL = "environmental"
    SOCIAL = "social"
    POLITICAL = "political"
    PERSONAL = "personal"
    EQUIPMENT = "equipment"
    INTELLIGENCE = "intelligence"


@dataclass
class MissionEvent:
    """Random event that occurs during a mission"""
    id: str
    category: EventCategory
    phase: MissionPhase
    description: str
    severity: float  # 0.0 to 1.0
    skill_checks: List[SkillType]
    success_modifier: float  # Positive or negative impact on success
    potential_consequences: List[str]
    choices: List[Dict[str, Any]] = field(default_factory=list)
    
    def resolve(self, agents: List[Agent], choice_index: int = 0) -> Dict[str, Any]:
        """Resolve the event based on agent skills and player choice"""
        result = {
            'event_id': self.id,
            'success': False,
            'consequences': [],
            'skill_results': {},
            'casualties': []
        }
        
        # Get the chosen option
        choice = self.choices[choice_index] if self.choices else None
        
        # Perform skill checks
        for skill_type in self.skill_checks:
            # Find best agent for this skill
            best_agent = max(agents, key=lambda a: a.skills.get(skill_type, SkillType(1)).level)
            skill_level = best_agent.skills.get(skill_type, SkillType(1)).level
            
            # Basic skill check with randomness
            difficulty = 5 + (self.severity * 5)  # 5-10 difficulty based on severity
            roll = random.randint(1, 10) + skill_level
            
            skill_success = roll >= difficulty
            result['skill_results'][skill_type.value] = {
                'agent': best_agent.name,
                'success': skill_success,
                'roll': roll,
                'difficulty': difficulty
            }
            
            if skill_success:
                result['success'] = True
        
        # Apply consequences based on success/failure
        if result['success']:
            if choice and 'success_consequences' in choice:
                result['consequences'] = choice['success_consequences']
        else:
            if choice and 'failure_consequences' in choice:
                result['consequences'] = choice['failure_consequences']
            else:
                result['consequences'] = self.potential_consequences
        
        return result


@dataclass
class MissionComplexity:
    """Factors affecting mission difficulty and planning"""
    security_level: int  # 1-10
    target_hardening: float  # 0.0-1.0 (bodyguards, security systems, etc.)
    time_pressure: float  # 0.0-1.0 (urgency)
    resource_requirements: Dict[str, int] = field(default_factory=dict)
    required_skills: Dict[SkillType, int] = field(default_factory=dict)
    political_sensitivity: float = 0.5  # 0.0-1.0
    minimum_agents: int = 1
    maximum_agents: int = 4
    
    def calculate_difficulty(self) -> float:
        """Calculate overall mission difficulty"""
        base_difficulty = self.security_level / 10.0
        
        # Factor in other complexity elements
        difficulty = base_difficulty * (1 + self.target_hardening * 0.5)
        difficulty *= (1 + self.time_pressure * 0.3)
        difficulty *= (1 + self.political_sensitivity * 0.2)
        
        return min(1.0, difficulty)


@dataclass
class MissionPlan:
    """Detailed mission planning information"""
    mission_id: str
    approach: str  # "stealth", "direct", "deception", "hybrid"
    entry_point: str
    exit_strategy: str
    equipment_loadout: Dict[str, List[Equipment]]
    contingency_plans: List[str]
    timeline: Dict[MissionPhase, int]  # Expected duration in turns
    abort_conditions: List[str]
    
    def validate_plan(self, agents: List[Agent], location: Location) -> Tuple[bool, List[str]]:
        """Validate if the plan is feasible"""
        issues = []
        
        # Check if agents have required equipment
        for agent_id, equipment_list in self.equipment_loadout.items():
            agent = next((a for a in agents if a.id == agent_id), None)
            if not agent:
                issues.append(f"Agent {agent_id} not found")
                continue
            
            agent_equipment_names = [e.name for e in agent.equipment]
            for equipment in equipment_list:
                if equipment.name not in agent_equipment_names:
                    issues.append(f"{agent.name} missing required equipment: {equipment.name}")
        
        # Check timeline feasibility
        total_phases = sum(self.timeline.values())
        if total_phases > 10:
            issues.append("Mission timeline too long - high risk of discovery")
        
        return len(issues) == 0, issues


@dataclass
class Mission:
    """Enhanced mission with comprehensive mechanics"""
    id: str
    mission_type: MissionType
    faction_id: str
    target_location_id: str
    complexity: MissionComplexity
    participants: List[str] = field(default_factory=list)
    plan: Optional[MissionPlan] = None
    status: MissionStatus = MissionStatus.PLANNING
    current_phase: MissionPhase = MissionPhase.PLANNING
    progress: float = 0.0  # 0.0 to 1.0
    success_probability: float = 0.5
    events_encountered: List[MissionEvent] = field(default_factory=list)
    casualties: List[str] = field(default_factory=list)
    captured_agents: List[str] = field(default_factory=list)
    resources_consumed: Dict[str, int] = field(default_factory=dict)
    intel_gathered: List[Dict[str, Any]] = field(default_factory=list)
    political_impact: float = 0.0  # -1.0 to 1.0
    created_turn: int = 0
    completed_turn: Optional[int] = None
    
    def calculate_success_probability(self, agents: List[Agent], location: Location) -> float:
        """Calculate mission success probability based on various factors"""
        if not agents:
            return 0.0
        
        # Base probability from mission difficulty
        base_prob = 1.0 - self.complexity.calculate_difficulty()
        
        # Agent skill factor
        skill_factor = 0.0
        for skill_type, required_level in self.complexity.required_skills.items():
            best_agent_skill = max(
                agent.skills.get(skill_type, SkillType(1)).level 
                for agent in agents
            )
            skill_factor += min(1.0, best_agent_skill / required_level) / len(self.complexity.required_skills)
        
        # Location factor
        location_factor = 1.0 - (location.security_level / 10.0)
        
        # Equipment factor
        equipment_factor = 0.8  # Default if no special equipment needed
        if self.plan and self.plan.equipment_loadout:
            equipped_agents = sum(
                1 for agent_id in self.plan.equipment_loadout
                if any(a.id == agent_id for a in agents)
            )
            equipment_factor = equipped_agents / len(agents) if agents else 0.5
        
        # Agent status factor (stress, injuries, etc.)
        status_factor = sum(
            0.8 if agent.stress < 50 else 0.6
            for agent in agents
        ) / len(agents)
        
        # Combine all factors
        success_prob = base_prob * 0.3 + skill_factor * 0.3 + location_factor * 0.2 + equipment_factor * 0.1 + status_factor * 0.1
        
        # Apply approach modifier if planned
        if self.plan:
            if self.plan.approach == "stealth" and self.mission_type in [
                MissionType.INTELLIGENCE_GATHERING, MissionType.DOCUMENT_THEFT
            ]:
                success_prob *= 1.2
            elif self.plan.approach == "direct" and self.mission_type in [
                MissionType.SABOTAGE, MissionType.ASSASSINATION
            ]:
                success_prob *= 1.1
        
        return min(0.95, max(0.05, success_prob))  # Cap between 5% and 95%
    
    def advance_phase(self) -> bool:
        """Advance to the next mission phase"""
        phase_order = [
            MissionPhase.PLANNING,
            MissionPhase.INFILTRATION,
            MissionPhase.EXECUTION,
            MissionPhase.EXTRACTION,
            MissionPhase.AFTERMATH
        ]
        
        current_index = phase_order.index(self.current_phase)
        if current_index < len(phase_order) - 1:
            self.current_phase = phase_order[current_index + 1]
            return True
        return False
    
    def is_complete(self) -> bool:
        """Check if mission is complete"""
        return self.status in [
            MissionStatus.COMPLETED, 
            MissionStatus.FAILED, 
            MissionStatus.ABORTED,
            MissionStatus.COMPROMISED
        ]
    
    def abort_mission(self, reason: str):
        """Abort the mission"""
        self.status = MissionStatus.ABORTED
        self.political_impact = -0.1  # Minor negative impact for aborting
        
    def complete_mission(self, success: bool, turn_number: int):
        """Complete the mission with success or failure"""
        self.status = MissionStatus.COMPLETED if success else MissionStatus.FAILED
        self.completed_turn = turn_number
        
        # Calculate political impact
        if success:
            impact_multiplier = {
                MissionType.ASSASSINATION: 1.5,
                MissionType.PRISON_BREAK: 1.3,
                MissionType.BANK_ROBBERY: 1.2,
                MissionType.SABOTAGE: 1.0,
                MissionType.PROPAGANDA_CAMPAIGN: 0.8,
                MissionType.RECRUITMENT_DRIVE: 0.6
            }.get(self.mission_type, 1.0)
            
            self.political_impact = 0.3 * impact_multiplier
        else:
            self.political_impact = -0.2 