"""
Years of Lead - Mission Event Generator

Generates contextual random events during mission execution based on
mission type, location, phase, and current conditions.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import random

from .mission_system import (
    MissionType, MissionPhase, EventCategory, MissionEvent,
    Mission
)
from .core import SkillType, Location, Agent


class MissionEventGenerator:
    """Generates contextual random events during missions"""
    
    def __init__(self):
        self.event_templates = self._initialize_event_templates()
        self.event_counter = 0
    
    def _initialize_event_templates(self) -> Dict[EventCategory, List[Dict[str, Any]]]:
        """Initialize event templates by category"""
        return {
            EventCategory.SECURITY: [
                {
                    'name': 'patrol_encounter',
                    'description': "A security patrol approaches your position",
                    'phases': [MissionPhase.INFILTRATION, MissionPhase.EXECUTION],
                    'severity_range': (0.3, 0.8),
                    'skill_checks': [SkillType.STEALTH, SkillType.COMBAT],
                    'choices': [
                        {
                            'description': "Hide and wait for them to pass",
                            'required_skill': SkillType.STEALTH,
                            'success_consequences': ["Patrol passes without incident"],
                            'failure_consequences': ["Discovered by patrol", "alarm_raised"]
                        },
                        {
                            'description': "Attempt to neutralize them quietly",
                            'required_skill': SkillType.COMBAT,
                            'success_consequences': ["Patrol eliminated silently"],
                            'failure_consequences': ["Combat alerts nearby units", "agent_injured"]
                        },
                        {
                            'description': "Create a diversion elsewhere",
                            'required_skill': SkillType.INTELLIGENCE,
                            'success_consequences': ["Patrol diverted to false alarm"],
                            'failure_consequences': ["Diversion fails, security heightened"]
                        }
                    ]
                },
                {
                    'name': 'alarm_triggered',
                    'description': "An alarm has been triggered!",
                    'phases': [MissionPhase.EXECUTION, MissionPhase.EXTRACTION],
                    'severity_range': (0.6, 0.9),
                    'skill_checks': [SkillType.HACKING, SkillType.DEMOLITIONS],
                    'choices': [
                        {
                            'description': "Hack the security system to disable it",
                            'required_skill': SkillType.HACKING,
                            'success_consequences': ["Alarm disabled, security confused"],
                            'failure_consequences': ["Lockdown initiated", "escape_routes_blocked"]
                        },
                        {
                            'description': "Destroy the alarm system",
                            'required_skill': SkillType.DEMOLITIONS,
                            'success_consequences': ["Alarm destroyed, brief window to escape"],
                            'failure_consequences': ["Explosion alerts entire facility", "heavy_response"]
                        }
                    ]
                },
                {
                    'name': 'unexpected_witness',
                    'description': "A civilian unexpectedly witnesses your activities",
                    'phases': [MissionPhase.EXECUTION],
                    'severity_range': (0.2, 0.5),
                    'skill_checks': [SkillType.PERSUASION, SkillType.STEALTH],
                    'choices': [
                        {
                            'description': "Convince them you're authorized personnel",
                            'required_skill': SkillType.PERSUASION,
                            'success_consequences': ["Witness believes cover story"],
                            'failure_consequences': ["Witness reports suspicious activity", "partial_identification"]
                        },
                        {
                            'description': "Quickly hide before being clearly seen",
                            'required_skill': SkillType.STEALTH,
                            'success_consequences': ["Identity remains unknown"],
                            'failure_consequences': ["Partially identified", "witness_escapes"]
                        }
                    ]
                }
            ],
            
            EventCategory.ENVIRONMENTAL: [
                {
                    'name': 'weather_change',
                    'description': "Sudden weather change affects visibility and movement",
                    'phases': [MissionPhase.INFILTRATION, MissionPhase.EXTRACTION],
                    'severity_range': (0.2, 0.6),
                    'skill_checks': [SkillType.SURVIVAL],
                    'choices': [
                        {
                            'description': "Use weather as cover to advance",
                            'required_skill': SkillType.SURVIVAL,
                            'success_consequences': ["Weather provides excellent cover"],
                            'failure_consequences': ["Disoriented by conditions", "equipment_damaged"]
                        },
                        {
                            'description': "Wait for conditions to improve",
                            'required_skill': None,
                            'success_consequences': ["Safe but time lost"],
                            'failure_consequences': ["Mission window closing", "increased_patrols"]
                        }
                    ]
                },
                {
                    'name': 'equipment_malfunction',
                    'description': "Critical equipment malfunctions at a crucial moment",
                    'phases': [MissionPhase.EXECUTION],
                    'severity_range': (0.3, 0.7),
                    'skill_checks': [SkillType.TECHNICAL, SkillType.INTELLIGENCE],
                    'choices': [
                        {
                            'description': "Attempt field repair",
                            'required_skill': SkillType.TECHNICAL,
                            'success_consequences': ["Equipment repaired"],
                            'failure_consequences': ["Repair fails, must abort objective", "time_wasted"]
                        },
                        {
                            'description': "Improvise alternative solution",
                            'required_skill': SkillType.INTELLIGENCE,
                            'success_consequences': ["Creative solution works"],
                            'failure_consequences': ["Improvisation backfires", "partial_success"]
                        }
                    ]
                }
            ],
            
            EventCategory.SOCIAL: [
                {
                    'name': 'informant_betrayal',
                    'description': "Your informant has betrayed you to the authorities",
                    'phases': [MissionPhase.PLANNING, MissionPhase.INFILTRATION],
                    'severity_range': (0.7, 0.9),
                    'skill_checks': [SkillType.INTELLIGENCE, SkillType.PERSUASION],
                    'choices': [
                        {
                            'description': "Confront the informant",
                            'required_skill': SkillType.PERSUASION,
                            'success_consequences': ["Informant reveals double agent status", "new_intel"],
                            'failure_consequences': ["Walking into trap", "ambush_waiting"]
                        },
                        {
                            'description': "Abort and investigate",
                            'required_skill': SkillType.INTELLIGENCE,
                            'success_consequences': ["Trap avoided, alternative found"],
                            'failure_consequences': ["Mission window lost", "informant_escapes"]
                        }
                    ]
                },
                {
                    'name': 'unexpected_ally',
                    'description': "A sympathizer offers unexpected assistance",
                    'phases': [MissionPhase.EXECUTION, MissionPhase.EXTRACTION],
                    'severity_range': (0.1, 0.3),
                    'skill_checks': [SkillType.INTELLIGENCE],
                    'choices': [
                        {
                            'description': "Accept their help",
                            'required_skill': SkillType.INTELLIGENCE,
                            'success_consequences': ["Ally provides crucial assistance", "new_escape_route"],
                            'failure_consequences': ["Ally is government plant", "ambush"]
                        },
                        {
                            'description': "Politely decline and continue",
                            'required_skill': None,
                            'success_consequences': ["Mission continues as planned"],
                            'failure_consequences': ["Missed opportunity", "harder_extraction"]
                        }
                    ]
                }
            ],
            
            EventCategory.POLITICAL: [
                {
                    'name': 'media_presence',
                    'description': "Media crews arrive at the scene",
                    'phases': [MissionPhase.EXECUTION, MissionPhase.EXTRACTION],
                    'severity_range': (0.3, 0.6),
                    'skill_checks': [SkillType.PERSUASION, SkillType.STEALTH],
                    'choices': [
                        {
                            'description': "Use media presence to your advantage",
                            'required_skill': SkillType.PERSUASION,
                            'success_consequences': ["Public opinion boost", "government_embarrassed"],
                            'failure_consequences': ["Identified on camera", "public_backlash"]
                        },
                        {
                            'description': "Avoid all cameras",
                            'required_skill': SkillType.STEALTH,
                            'success_consequences': ["Identity protected"],
                            'failure_consequences': ["Suspicious behavior noted", "partial_footage"]
                        }
                    ]
                },
                {
                    'name': 'government_crackdown',
                    'description': "Government initiates emergency crackdown protocols",
                    'phases': [MissionPhase.EXTRACTION, MissionPhase.AFTERMATH],
                    'severity_range': (0.6, 0.9),
                    'skill_checks': [SkillType.INTELLIGENCE, SkillType.STEALTH],
                    'choices': [
                        {
                            'description': "Use pre-planned safe houses",
                            'required_skill': SkillType.INTELLIGENCE,
                            'success_consequences': ["Safe extraction to secure location"],
                            'failure_consequences': ["Safe house compromised", "narrow_escape"]
                        },
                        {
                            'description': "Blend with civilian population",
                            'required_skill': SkillType.STEALTH,
                            'success_consequences': ["Successfully hidden among civilians"],
                            'failure_consequences': ["Checkpoints everywhere", "detained_for_questioning"]
                        }
                    ]
                }
            ],
            
            EventCategory.PERSONAL: [
                {
                    'name': 'agent_breakdown',
                    'description': "An agent suffers emotional breakdown from stress",
                    'phases': [MissionPhase.EXECUTION, MissionPhase.EXTRACTION],
                    'severity_range': (0.4, 0.7),
                    'skill_checks': [SkillType.PERSUASION, SkillType.MEDICAL],
                    'choices': [
                        {
                            'description': "Talk them through it",
                            'required_skill': SkillType.PERSUASION,
                            'success_consequences': ["Agent recovers composure"],
                            'failure_consequences': ["Agent becomes liability", "mission_compromised"]
                        },
                        {
                            'description': "Administer emergency sedative",
                            'required_skill': SkillType.MEDICAL,
                            'success_consequences': ["Agent stabilized but impaired"],
                            'failure_consequences': ["Wrong dosage", "agent_unconscious"]
                        }
                    ]
                },
                {
                    'name': 'moral_crisis',
                    'description': "Agent questions the morality of the mission",
                    'phases': [MissionPhase.PLANNING, MissionPhase.EXECUTION],
                    'severity_range': (0.3, 0.6),
                    'skill_checks': [SkillType.PERSUASION],
                    'choices': [
                        {
                            'description': "Remind them of the cause",
                            'required_skill': SkillType.PERSUASION,
                            'success_consequences': ["Agent recommits to mission"],
                            'failure_consequences': ["Agent refuses to continue", "morale_impact"]
                        },
                        {
                            'description': "Offer to take their place",
                            'required_skill': None,
                            'success_consequences': ["Mission continues with substitute"],
                            'failure_consequences': ["Team cohesion damaged", "efficiency_reduced"]
                        }
                    ]
                }
            ]
        }
    
    def generate_event(self, mission: Mission, location: Location, 
                      agents: List[Agent], turn_number: int) -> Optional[MissionEvent]:
        """Generate a contextual event based on mission state"""
        
        # Determine event probability based on mission phase and location
        event_chance = self._calculate_event_probability(mission, location)
        
        if random.random() > event_chance:
            return None
        
        # Select appropriate event category
        category = self._select_event_category(mission, location, agents)
        
        # Get possible events for this category and phase
        possible_events = [
            template for template in self.event_templates[category]
            if mission.current_phase in template['phases']
        ]
        
        if not possible_events:
            return None
        
        # Select and create event
        template = random.choice(possible_events)
        return self._create_event_from_template(template, category, mission, location, agents)
    
    def _calculate_event_probability(self, mission: Mission, location: Location) -> float:
        """Calculate probability of an event occurring"""
        base_probability = 0.3
        
        # Increase probability based on location security
        security_modifier = location.security_level / 20.0
        
        # Increase probability based on mission type risk
        risk_modifiers = {
            MissionType.ASSASSINATION: 0.3,
            MissionType.PRISON_BREAK: 0.25,
            MissionType.BANK_ROBBERY: 0.2,
            MissionType.SABOTAGE: 0.15,
            MissionType.INTELLIGENCE_GATHERING: 0.1,
            MissionType.PROPAGANDA_CAMPAIGN: 0.05
        }
        risk_modifier = risk_modifiers.get(mission.mission_type, 0.1)
        
        # Phase modifiers
        phase_modifiers = {
            MissionPhase.PLANNING: 0.1,
            MissionPhase.INFILTRATION: 0.2,
            MissionPhase.EXECUTION: 0.3,
            MissionPhase.EXTRACTION: 0.25,
            MissionPhase.AFTERMATH: 0.15
        }
        phase_modifier = phase_modifiers.get(mission.current_phase, 0.2)
        
        return min(0.8, base_probability + security_modifier + risk_modifier + phase_modifier)
    
    def _select_event_category(self, mission: Mission, location: Location, 
                              agents: List[Agent]) -> EventCategory:
        """Select appropriate event category based on context"""
        
        # Weight categories based on mission context
        weights = {
            EventCategory.SECURITY: location.security_level,
            EventCategory.ENVIRONMENTAL: 5,
            EventCategory.SOCIAL: location.unrest_level,
            EventCategory.POLITICAL: mission.complexity.political_sensitivity * 10,
            EventCategory.PERSONAL: sum(agent.stress for agent in agents) / (len(agents) * 10)
        }
        
        # Special weights for certain mission types
        if mission.mission_type in [MissionType.ASSASSINATION, MissionType.SABOTAGE]:
            weights[EventCategory.SECURITY] *= 1.5
        elif mission.mission_type in [MissionType.PROPAGANDA_CAMPAIGN, MissionType.RECRUITMENT_DRIVE]:
            weights[EventCategory.SOCIAL] *= 1.5
        
        # Random weighted selection
        categories = list(weights.keys())
        category_weights = list(weights.values())
        
        return random.choices(categories, weights=category_weights)[0]
    
    def _create_event_from_template(self, template: Dict[str, Any], 
                                   category: EventCategory,
                                   mission: Mission, 
                                   location: Location,
                                   agents: List[Agent]) -> MissionEvent:
        """Create an event instance from a template"""
        
        self.event_counter += 1
        event_id = f"event_{self.event_counter}_{template['name']}"
        
        # Determine severity based on template range and context
        min_severity, max_severity = template['severity_range']
        severity = random.uniform(min_severity, max_severity)
        
        # Adjust severity based on mission progress
        if mission.progress > 0.7:  # Near completion
            severity *= 1.2
        
        # Create the event
        event = MissionEvent(
            id=event_id,
            category=category,
            phase=mission.current_phase,
            description=template['description'],
            severity=min(1.0, severity),
            skill_checks=template['skill_checks'],
            success_modifier=-severity * 0.2,  # Negative impact on mission success
            potential_consequences=self._generate_consequences(template, severity),
            choices=template['choices']
        )
        
        return event
    
    def _generate_consequences(self, template: Dict[str, Any], severity: float) -> List[str]:
        """Generate potential consequences based on event template and severity"""
        
        base_consequences = []
        
        # Add severity-based consequences
        if severity > 0.7:
            base_consequences.extend([
                "mission_compromised",
                "heavy_security_response",
                "agent_captured"
            ])
        elif severity > 0.4:
            base_consequences.extend([
                "increased_security",
                "time_pressure",
                "partial_exposure"
            ])
        else:
            base_consequences.extend([
                "minor_delay",
                "stress_increase",
                "resource_loss"
            ])
        
        return base_consequences 