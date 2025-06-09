"""
Years of Lead - Mission Execution Engine

Central engine for executing missions with event generation, legal tracking,
narrative flow, and outcome resolution.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any, Set
import random
from enum import Enum

from .mission_system import (
    Mission, MissionType, MissionPhase, MissionStatus,
    MissionComplexity, MissionPlan, MissionEvent
)
from .mission_events import MissionEventGenerator
from .legal_system import (
    LegalSystem, CrimeType, WitnessType, EvidenceType,
    IdentificationLevel
)
from .core import Agent, AgentStatus, Location, GameState, SkillType
from .narrative_generator import NarrativeGenerator  # We'll create this next


class MissionOutcome(Enum):
    """Possible mission outcomes"""
    CRITICAL_SUCCESS = "critical_success"
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    CATASTROPHIC_FAILURE = "catastrophic_failure"
    ABORTED = "aborted"


@dataclass
class MissionReport:
    """Comprehensive report of mission execution"""
    mission_id: str
    outcome: MissionOutcome
    narrative_summary: List[str]
    agents_involved: List[str]
    casualties: List[str]
    captured_agents: List[str]
    crimes_committed: List[str]  # Crime record IDs
    resources_gained: Dict[str, int]
    resources_lost: Dict[str, int]
    intel_gathered: List[Dict[str, Any]]
    political_impact: float
    faction_reputation_change: float
    events_encountered: List[MissionEvent]
    total_turns: int
    

class MissionExecutor:
    """Main mission execution engine"""
    
    def __init__(self, game_state: GameState):
        self.game_state = game_state
        self.event_generator = MissionEventGenerator()
        self.legal_system = LegalSystem()
        self.narrative_generator = None  # Will be initialized later
        
    def plan_mission(self, mission: Mission, agents: List[Agent], 
                    approach: str = "balanced") -> MissionPlan:
        """Create a mission plan based on approach and agent capabilities"""
        
        location = self.game_state.locations[mission.target_location_id]
        
        # Determine entry and exit points based on location
        entry_points = self._get_location_entry_points(location)
        exit_strategies = self._get_location_exit_strategies(location)
        
        # Assign equipment based on mission type
        equipment_loadout = self._determine_equipment_needs(mission, agents)
        
        # Create timeline based on complexity
        timeline = self._create_mission_timeline(mission.complexity)
        
        # Generate contingency plans
        contingencies = self._generate_contingency_plans(mission.mission_type, location)
        
        # Set abort conditions
        abort_conditions = [
            "50% casualties",
            "Full identification by authorities",
            "Mission objective destroyed",
            "Government crackdown initiated"
        ]
        
        plan = MissionPlan(
            mission_id=mission.id,
            approach=approach,
            entry_point=random.choice(entry_points),
            exit_strategy=random.choice(exit_strategies),
            equipment_loadout=equipment_loadout,
            contingency_plans=contingencies,
            timeline=timeline,
            abort_conditions=abort_conditions
        )
        
        mission.plan = plan
        return plan
    
    def execute_mission(self, mission: Mission) -> MissionReport:
        """Execute a complete mission from start to finish"""
        
        # Get participating agents
        agents = [
            self.game_state.agents[agent_id] 
            for agent_id in mission.participants
            if agent_id in self.game_state.agents
        ]
        
        if not agents:
            return self._create_failed_report(mission, "No agents assigned")
        
        # Get location
        location = self.game_state.locations[mission.target_location_id]
        
        # Initialize mission tracking
        narrative_events = []
        crimes_committed = []
        resources_consumed = {}
        turn_count = 0
        
        # Execute each phase
        phase_results = {}
        
        for phase in [MissionPhase.INFILTRATION, MissionPhase.EXECUTION, 
                     MissionPhase.EXTRACTION, MissionPhase.AFTERMATH]:
            
            mission.current_phase = phase
            turn_count += 1
            
            # Generate phase narrative
            phase_narrative = self._generate_phase_narrative(mission, phase, agents, location)
            narrative_events.append(phase_narrative)
            
            # Check for random events
            event = self.event_generator.generate_event(
                mission, location, agents, self.game_state.turn_number
            )
            
            if event:
                # Handle the event
                event_result = self._handle_mission_event(
                    event, mission, agents, location
                )
                narrative_events.append(f"EVENT: {event.description}")
                
                # Apply event consequences
                if "agent_captured" in event_result.get('consequences', []):
                    captured_agent = random.choice(agents)
                    mission.captured_agents.append(captured_agent.id)
                    agents.remove(captured_agent)
                    
                if "mission_compromised" in event_result.get('consequences', []):
                    mission.status = MissionStatus.COMPROMISED
                    break
            
            # Execute phase-specific actions
            phase_result = self._execute_phase_actions(
                mission, phase, agents, location
            )
            phase_results[phase] = phase_result
            
            # Track crimes if any were committed
            if phase_result.get('crimes'):
                crimes_committed.extend(phase_result['crimes'])
            
            # Check for phase failure
            if not phase_result['success']:
                if phase in [MissionPhase.INFILTRATION, MissionPhase.EXECUTION]:
                    # Critical phases - mission fails
                    mission.status = MissionStatus.FAILED
                    break
            
            # Update mission progress
            mission.progress = (list(MissionPhase).index(phase) + 1) / 4.0
        
        # Determine final outcome
        outcome = self._determine_mission_outcome(mission, phase_results)
        
        # Apply consequences
        consequences = self._apply_mission_consequences(
            mission, outcome, agents, location, crimes_committed
        )
        
        # Generate final report
        report = MissionReport(
            mission_id=mission.id,
            outcome=outcome,
            narrative_summary=narrative_events,
            agents_involved=[a.id for a in agents],
            casualties=mission.casualties,
            captured_agents=mission.captured_agents,
            crimes_committed=[c.id for c in crimes_committed],
            resources_gained=consequences.get('resources_gained', {}),
            resources_lost=mission.resources_consumed,
            intel_gathered=mission.intel_gathered,
            political_impact=mission.political_impact,
            faction_reputation_change=consequences.get('reputation_change', 0),
            events_encountered=mission.events_encountered,
            total_turns=turn_count
        )
        
        # Update game state
        self._update_game_state_after_mission(mission, report)
        
        return report
    
    def _execute_phase_actions(self, mission: Mission, phase: MissionPhase,
                              agents: List[Agent], location: Location) -> Dict[str, Any]:
        """Execute actions specific to each mission phase"""
        
        result = {
            'success': True,
            'narrative': [],
            'crimes': [],
            'resources_consumed': {}
        }
        
        if phase == MissionPhase.INFILTRATION:
            # Stealth checks for infiltration
            stealth_check = self._group_skill_check(agents, SkillType.STEALTH, location.security_level)
            
            if not stealth_check['success']:
                result['success'] = False
                result['narrative'].append("Infiltration detected by security")
                
                # Minor crime - trespassing
                crime = self._record_crime(
                    agents, CrimeType.TRESPASSING, location,
                    witnesses=stealth_check.get('witnesses', 0),
                    witness_type=WitnessType.SECURITY
                )
                result['crimes'].append(crime)
        
        elif phase == MissionPhase.EXECUTION:
            # Execute based on mission type
            execution_result = self._execute_mission_objective(mission, agents, location)
            result.update(execution_result)
        
        elif phase == MissionPhase.EXTRACTION:
            # Escape checks
            escape_difficulty = location.security_level
            if mission.status == MissionStatus.COMPROMISED:
                escape_difficulty += 3
            
            escape_check = self._group_skill_check(agents, SkillType.STEALTH, escape_difficulty)
            
            if not escape_check['success']:
                result['success'] = False
                result['narrative'].append("Difficult extraction under fire")
                
                # Possible casualties during escape
                if random.random() < 0.3:
                    casualty = random.choice(agents)
                    mission.casualties.append(casualty.id)
                    result['narrative'].append(f"{casualty.name} was lost during extraction")
        
        elif phase == MissionPhase.AFTERMATH:
            # Clean up traces, establish alibis
            intel_check = self._group_skill_check(agents, SkillType.INTELLIGENCE, 5)
            
            if intel_check['success']:
                result['narrative'].append("Traces cleaned, alibis established")
                # Reduce identification level for any crimes
                for crime in result.get('crimes', []):
                    if crime.identification_level == IdentificationLevel.PARTIAL:
                        crime.identification_level = IdentificationLevel.UNKNOWN
            else:
                result['narrative'].append("Failed to cover all tracks")
        
        return result
    
    def _execute_mission_objective(self, mission: Mission, agents: List[Agent],
                                  location: Location) -> Dict[str, Any]:
        """Execute the main mission objective based on type"""
        
        result = {
            'success': True,
            'narrative': [],
            'crimes': [],
            'resources_consumed': {}
        }
        
        # Mission type specific execution
        if mission.mission_type == MissionType.ASSASSINATION:
            # High-risk assassination
            combat_check = self._group_skill_check(agents, SkillType.COMBAT, 8)
            
            if combat_check['success']:
                result['narrative'].append("Target eliminated successfully")
                result['success'] = True
                
                # Record murder
                crime = self._record_crime(
                    agents, CrimeType.ASSASSINATION, location,
                    witnesses=random.randint(0, 5),
                    witness_type=random.choice([WitnessType.CIVILIAN, WitnessType.SECURITY]),
                    evidence={EvidenceType.PHYSICAL, EvidenceType.FORENSIC}
                )
                result['crimes'].append(crime)
            else:
                result['narrative'].append("Assassination attempt failed")
                result['success'] = False
                
                # Still record attempted murder
                crime = self._record_crime(
                    agents, CrimeType.ASSAULT, location,
                    witnesses=combat_check.get('witnesses', 3),
                    witness_type=WitnessType.SECURITY
                )
                result['crimes'].append(crime)
        
        elif mission.mission_type == MissionType.SABOTAGE:
            # Sabotage operation
            demo_check = self._group_skill_check(agents, SkillType.DEMOLITIONS, 6)
            
            if demo_check['success']:
                result['narrative'].append("Infrastructure successfully sabotaged")
                result['success'] = True
                
                # Property destruction
                crime = self._record_crime(
                    agents, CrimeType.PROPERTY_DESTRUCTION, location,
                    witnesses=0,  # Ideally no witnesses to sabotage
                    witness_type=WitnessType.NONE,
                    evidence={EvidenceType.PHYSICAL}
                )
                result['crimes'].append(crime)
            else:
                result['narrative'].append("Sabotage partially successful")
                result['success'] = False
        
        elif mission.mission_type == MissionType.INTELLIGENCE_GATHERING:
            # Intelligence operation
            intel_check = self._group_skill_check(agents, SkillType.INTELLIGENCE, 5)
            
            if intel_check['success']:
                result['narrative'].append("Valuable intelligence gathered")
                result['success'] = True
                
                # Generate intel
                intel = {
                    'type': 'government_plans',
                    'value': random.randint(1, 10),
                    'description': 'Classified government documents'
                }
                mission.intel_gathered.append(intel)
                
                # Minor crime - theft
                crime = self._record_crime(
                    agents, CrimeType.MINOR_THEFT, location,
                    witnesses=0,
                    witness_type=WitnessType.NONE,
                    evidence={EvidenceType.DIGITAL}
                )
                result['crimes'].append(crime)
        
        elif mission.mission_type == MissionType.PROPAGANDA_CAMPAIGN:
            # Propaganda operation
            persuasion_check = self._group_skill_check(agents, SkillType.PERSUASION, 4)
            
            if persuasion_check['success']:
                result['narrative'].append("Propaganda successfully distributed")
                result['success'] = True
                
                # Minor crime - vandalism/graffiti
                crime = self._record_crime(
                    agents, CrimeType.GRAFFITI, location,
                    witnesses=random.randint(1, 3),
                    witness_type=WitnessType.CIVILIAN,
                    evidence=set()
                )
                result['crimes'].append(crime)
        
        elif mission.mission_type == MissionType.BANK_ROBBERY:
            # High-stakes robbery
            combat_check = self._group_skill_check(agents, SkillType.COMBAT, 7)
            hacking_check = self._group_skill_check(agents, SkillType.HACKING, 6)
            
            if combat_check['success'] and hacking_check['success']:
                result['narrative'].append("Bank successfully robbed")
                result['success'] = True
                
                # Major crime
                crime = self._record_crime(
                    agents, CrimeType.GRAND_THEFT, location,
                    witnesses=random.randint(5, 15),
                    witness_type=WitnessType.CIVILIAN,
                    evidence={EvidenceType.PHYSICAL, EvidenceType.DIGITAL, EvidenceType.EYEWITNESS}
                )
                result['crimes'].append(crime)
                
                # Resources gained
                result['resources_gained'] = {'money': random.randint(5000, 20000)}
            else:
                result['narrative'].append("Robbery failed, heavy resistance")
                result['success'] = False
        
        elif mission.mission_type == MissionType.PRISON_BREAK:
            # Complex prison break
            combat_check = self._group_skill_check(agents, SkillType.COMBAT, 8)
            demo_check = self._group_skill_check(agents, SkillType.DEMOLITIONS, 7)
            
            if combat_check['success'] and demo_check['success']:
                result['narrative'].append("Prisoners successfully liberated")
                result['success'] = True
                
                # Multiple crimes
                crimes = [
                    self._record_crime(
                        agents, CrimeType.PROPERTY_DESTRUCTION, location,
                        witnesses=10, witness_type=WitnessType.SECURITY,
                        evidence={EvidenceType.PHYSICAL}
                    ),
                    self._record_crime(
                        agents, CrimeType.ASSAULT, location,
                        witnesses=5, witness_type=WitnessType.POLICE,
                        evidence={EvidenceType.EYEWITNESS}
                    )
                ]
                result['crimes'].extend(crimes)
            else:
                result['narrative'].append("Prison break failed")
                result['success'] = False
        
        elif mission.mission_type == MissionType.RECRUITMENT_DRIVE:
            # Recruitment operation
            persuasion_check = self._group_skill_check(agents, SkillType.PERSUASION, 5)
            
            if persuasion_check['success']:
                result['narrative'].append("New recruits gained for the cause")
                result['success'] = True
                
                # Legal activity (usually)
                if location.security_level < 7:
                    # Legal recruitment
                    crime = self._record_crime(
                        agents, CrimeType.COMMUNITY_ORGANIZING, location,
                        witnesses=20, witness_type=WitnessType.CIVILIAN
                    )
                else:
                    # Illegal in high-security areas
                    crime = self._record_crime(
                        agents, CrimeType.DISTURBING_PEACE, location,
                        witnesses=10, witness_type=WitnessType.POLICE
                    )
                result['crimes'].append(crime)
        
        return result
    
    def _group_skill_check(self, agents: List[Agent], skill: SkillType, 
                          difficulty: int) -> Dict[str, Any]:
        """Perform a skill check for a group of agents"""
        
        if not agents:
            return {'success': False, 'margin': -10}
        
        # Get best agent for the skill
        best_agent = max(agents, key=lambda a: a.skills.get(skill, 1).level)
        skill_level = best_agent.skills.get(skill, 1).level
        
        # Add bonuses for assisting agents
        assist_bonus = sum(
            0.5 for agent in agents 
            if agent != best_agent and agent.skills.get(skill, 1).level >= 3
        )
        
        # Roll check
        roll = random.randint(1, 10) + skill_level + assist_bonus
        success = roll >= difficulty
        
        result = {
            'success': success,
            'margin': roll - difficulty,
            'lead_agent': best_agent.id,
            'skill_used': skill
        }
        
        # Add witness information for failed stealth checks
        if not success and skill == SkillType.STEALTH:
            result['witnesses'] = random.randint(1, 5)
        
        return result
    
    def _record_crime(self, agents: List[Agent], crime_type: CrimeType,
                     location: Location, witnesses: int = 0,
                     witness_type: WitnessType = WitnessType.NONE,
                     evidence: Set[EvidenceType] = None) -> Any:
        """Record a crime with the legal system"""
        
        return self.legal_system.record_crime(
            agents=agents,
            crime_type=crime_type,
            location=location,
            witnesses=witnesses,
            witness_type=witness_type,
            evidence=evidence
        )
    
    def _handle_mission_event(self, event: MissionEvent, mission: Mission,
                             agents: List[Agent], location: Location) -> Dict[str, Any]:
        """Handle a random mission event"""
        
        # Add to mission events
        mission.events_encountered.append(event)
        
        # Let player make a choice (for now, pick randomly)
        choice_index = 0  # In real game, this would be player input
        
        # Resolve the event
        result = event.resolve(agents, choice_index)
        
        # Apply stress to agents based on event severity
        for agent in agents:
            agent.stress += int(event.severity * 10)
            agent.stress = min(100, agent.stress)
        
        return result
    
    def _determine_mission_outcome(self, mission: Mission, 
                                  phase_results: Dict[MissionPhase, Dict]) -> MissionOutcome:
        """Determine overall mission outcome based on phase results"""
        
        if mission.status == MissionStatus.ABORTED:
            return MissionOutcome.ABORTED
        
        # Count successful phases
        successful_phases = sum(
            1 for result in phase_results.values() 
            if result.get('success', False)
        )
        
        # Check for catastrophic indicators
        if len(mission.casualties) > len(mission.participants) / 2:
            return MissionOutcome.CATASTROPHIC_FAILURE
        
        if mission.status == MissionStatus.COMPROMISED:
            return MissionOutcome.FAILURE if successful_phases < 2 else MissionOutcome.PARTIAL_SUCCESS
        
        # Determine based on phase success
        if successful_phases == len(phase_results):
            return MissionOutcome.CRITICAL_SUCCESS
        elif successful_phases >= 3:
            return MissionOutcome.SUCCESS
        elif successful_phases >= 2:
            return MissionOutcome.PARTIAL_SUCCESS
        elif successful_phases >= 1:
            return MissionOutcome.FAILURE
        else:
            return MissionOutcome.CATASTROPHIC_FAILURE
    
    def _apply_mission_consequences(self, mission: Mission, outcome: MissionOutcome,
                                   agents: List[Agent], location: Location,
                                   crimes_committed: List[Any]) -> Dict[str, Any]:
        """Apply consequences based on mission outcome"""
        
        consequences = {
            'resources_gained': {},
            'reputation_change': 0.0,
            'location_changes': {}
        }
        
        # Outcome-based consequences
        if outcome == MissionOutcome.CRITICAL_SUCCESS:
            consequences['reputation_change'] = 0.2
            mission.political_impact = 0.5
            
        elif outcome == MissionOutcome.SUCCESS:
            consequences['reputation_change'] = 0.1
            mission.political_impact = 0.3
            
        elif outcome == MissionOutcome.PARTIAL_SUCCESS:
            consequences['reputation_change'] = 0.05
            mission.political_impact = 0.1
            
        elif outcome == MissionOutcome.FAILURE:
            consequences['reputation_change'] = -0.1
            mission.political_impact = -0.1
            
        elif outcome == MissionOutcome.CATASTROPHIC_FAILURE:
            consequences['reputation_change'] = -0.3
            mission.political_impact = -0.3
            
            # Increase location security after catastrophic failure
            location.security_level = min(10, location.security_level + 2)
        
        # Apply stress and experience to surviving agents
        for agent in agents:
            if agent.id not in mission.casualties:
                # Stress based on outcome
                stress_change = {
                    MissionOutcome.CRITICAL_SUCCESS: -5,
                    MissionOutcome.SUCCESS: -2,
                    MissionOutcome.PARTIAL_SUCCESS: 5,
                    MissionOutcome.FAILURE: 10,
                    MissionOutcome.CATASTROPHIC_FAILURE: 20
                }.get(outcome, 5)
                
                agent.stress = max(0, min(100, agent.stress + stress_change))
                
                # Experience gain
                for skill in agent.skills.values():
                    skill.experience += random.randint(1, 5)
        
        # Update location unrest based on mission type and outcome
        if mission.mission_type in [MissionType.PROPAGANDA_CAMPAIGN, MissionType.RECRUITMENT_DRIVE]:
            if outcome in [MissionOutcome.CRITICAL_SUCCESS, MissionOutcome.SUCCESS]:
                location.unrest_level = min(10, location.unrest_level + 1)
        
        return consequences
    
    def _update_game_state_after_mission(self, mission: Mission, report: MissionReport):
        """Update the game state based on mission results"""
        
        # Update faction resources
        faction = self.game_state.factions.get(mission.faction_id)
        if faction:
            # Apply resource changes
            for resource, amount in report.resources_gained.items():
                if resource in faction.resources:
                    faction.resources[resource] += amount
            
            for resource, amount in report.resources_lost.items():
                if resource in faction.resources:
                    faction.resources[resource] = max(0, faction.resources[resource] - amount)
        
        # Add to game narrative
        outcome_text = {
            MissionOutcome.CRITICAL_SUCCESS: "brilliantly succeeded in",
            MissionOutcome.SUCCESS: "successfully completed",
            MissionOutcome.PARTIAL_SUCCESS: "partially completed",
            MissionOutcome.FAILURE: "failed",
            MissionOutcome.CATASTROPHIC_FAILURE: "catastrophically failed",
            MissionOutcome.ABORTED: "aborted"
        }
        
        narrative = f"{faction.name} {outcome_text[report.outcome]} a {mission.mission_type.value} operation"
        self.game_state.recent_narrative.append(narrative)
        
        # Update mission status
        mission.status = MissionStatus.COMPLETED
        mission.completed_turn = self.game_state.turn_number
    
    def _generate_phase_narrative(self, mission: Mission, phase: MissionPhase,
                                 agents: List[Agent], location: Location) -> str:
        """Generate narrative text for a mission phase"""
        
        # Basic narrative templates by phase
        templates = {
            MissionPhase.INFILTRATION: [
                f"The team approaches {location.name} under cover of darkness",
                f"Agents move stealthily through the shadows toward {location.name}",
                f"The operation begins as operatives infiltrate {location.name}"
            ],
            MissionPhase.EXECUTION: [
                f"The team executes their {mission.mission_type.value} operation",
                f"Agents carry out the planned {mission.mission_type.value}",
                f"The critical phase begins as the team acts on their objective"
            ],
            MissionPhase.EXTRACTION: [
                f"The team begins their extraction from {location.name}",
                f"Agents move quickly to escape the area",
                f"The operation shifts to the critical extraction phase"
            ],
            MissionPhase.AFTERMATH: [
                f"The team works to cover their tracks",
                f"Agents establish alibis and clean up evidence",
                f"The final phase focuses on avoiding detection"
            ]
        }
        
        return random.choice(templates.get(phase, ["The mission continues..."]))
    
    def _get_location_entry_points(self, location: Location) -> List[str]:
        """Get possible entry points for a location"""
        
        # Basic entry points - would be more sophisticated with location data
        basic_entries = ["main entrance", "service entrance", "rooftop access", "underground tunnel"]
        
        if location.security_level < 5:
            basic_entries.extend(["window", "loading dock", "emergency exit"])
        
        return basic_entries
    
    def _get_location_exit_strategies(self, location: Location) -> List[str]:
        """Get possible exit strategies for a location"""
        
        strategies = ["blend with crowds", "vehicle escape", "underground escape", "rooftop extraction"]
        
        if location.unrest_level > 5:
            strategies.append("disappear into protest crowds")
        
        return strategies
    
    def _determine_equipment_needs(self, mission: Mission, agents: List[Agent]) -> Dict[str, List[Any]]:
        """Determine equipment needs based on mission type"""
        
        equipment_loadout = {}
        
        # Basic equipment by mission type
        equipment_by_type = {
            MissionType.ASSASSINATION: ["rifle", "pistol", "disguise"],
            MissionType.SABOTAGE: ["explosives", "tools", "timer"],
            MissionType.INTELLIGENCE_GATHERING: ["camera", "listening device", "lockpicks"],
            MissionType.PROPAGANDA_CAMPAIGN: ["leaflets", "spray paint", "posters"],
            MissionType.BANK_ROBBERY: ["weapons", "masks", "bags"],
            MissionType.PRISON_BREAK: ["explosives", "weapons", "vehicles"],
            MissionType.RECRUITMENT_DRIVE: ["pamphlets", "megaphone", "banners"]
        }
        
        # For now, assign generic equipment
        for agent in agents:
            equipment_loadout[agent.id] = equipment_by_type.get(mission.mission_type, ["basic gear"])
        
        return equipment_loadout
    
    def _create_mission_timeline(self, complexity: MissionComplexity) -> Dict[MissionPhase, int]:
        """Create expected timeline based on mission complexity"""
        
        base_timeline = {
            MissionPhase.PLANNING: 1,
            MissionPhase.INFILTRATION: 1,
            MissionPhase.EXECUTION: 2,
            MissionPhase.EXTRACTION: 1,
            MissionPhase.AFTERMATH: 1
        }
        
        # Adjust based on complexity
        difficulty_multiplier = complexity.calculate_difficulty() + 0.5
        
        adjusted_timeline = {}
        for phase, duration in base_timeline.items():
            adjusted_timeline[phase] = max(1, int(duration * difficulty_multiplier))
        
        return adjusted_timeline
    
    def _generate_contingency_plans(self, mission_type: MissionType, location: Location) -> List[str]:
        """Generate contingency plans based on mission type and location"""
        
        contingencies = [
            "Abort if cover blown during infiltration",
            "Secondary extraction route through maintenance areas",
            "Emergency rendezvous at safe house"
        ]
        
        if mission_type in [MissionType.ASSASSINATION, MissionType.SABOTAGE]:
            contingencies.append("Alternate target if primary is too heavily guarded")
        
        if location.security_level > 7:
            contingencies.append("Diversion team creates distraction if needed")
        
        return contingencies
    
    def _create_failed_report(self, mission: Mission, reason: str) -> MissionReport:
        """Create a report for a mission that failed before execution"""
        
        return MissionReport(
            mission_id=mission.id,
            outcome=MissionOutcome.FAILURE,
            narrative_summary=[f"Mission failed: {reason}"],
            agents_involved=[],
            casualties=[],
            captured_agents=[],
            crimes_committed=[],
            resources_gained={},
            resources_lost={},
            intel_gathered=[],
            political_impact=-0.1,
            faction_reputation_change=-0.1,
            events_encountered=[],
            total_turns=0
        ) 