"""
Years of Lead - Random Events and Encounters System

This module provides a comprehensive random events system that generates
dynamic encounters and events affecting players, factions, and the environment.
"""

import random
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from .emotional_state import EmotionalState


class EventType(Enum):
    """Types of random events"""
    ENCOUNTER = "encounter"           # Direct player interaction
    ENVIRONMENTAL = "environmental"   # Weather, disasters, etc.
    POLITICAL = "political"           # Government actions, policy changes
    SOCIAL = "social"                 # Community events, protests
    ECONOMIC = "economic"             # Market changes, resource availability
    SECURITY = "security"             # Police actions, surveillance
    FACTION = "faction"               # Other faction activities
    PERSONAL = "personal"             # Character-specific events


class EventSeverity(Enum):
    """Event severity levels"""
    MINOR = "minor"       # Slight inconvenience or opportunity
    MODERATE = "moderate" # Noticeable impact
    MAJOR = "major"       # Significant consequences
    CRITICAL = "critical" # Game-changing events


class EncounterType(Enum):
    """Types of encounters"""
    FRIENDLY = "friendly"         # Helpful NPCs, allies
    NEUTRAL = "neutral"          # Bystanders, informants
    HOSTILE = "hostile"          # Enemies, authorities
    AMBIGUOUS = "ambiguous"      # Uncertain intentions
    MYSTERIOUS = "mysterious"    # Unknown entities


@dataclass
class EventOutcome:
    """Possible outcome of an event"""
    description: str
    probability: float  # 0.0 to 1.0
    effects: Dict[str, Any]  # Effects on game state
    emotional_impact: Dict[str, float]  # Emotional effects
    narrative_text: str


@dataclass
class RandomEvent:
    """A random event that can occur"""
    id: str
    name: str
    description: str
    event_type: EventType
    severity: EventSeverity
    trigger_conditions: Dict[str, Any]  # When this event can occur
    outcomes: List[EventOutcome]
    duration: int = 1  # How many turns the event lasts
    cooldown: int = 0  # Turns before event can repeat
    
    def get_random_outcome(self) -> EventOutcome:
        """Get a random outcome based on probabilities"""
        roll = random.random()
        cumulative_prob = 0.0
        
        for outcome in self.outcomes:
            cumulative_prob += outcome.probability
            if roll <= cumulative_prob:
                return outcome
        
        # Fallback to first outcome
        return self.outcomes[0] if self.outcomes else None


@dataclass
class Encounter:
    """A direct encounter with an NPC or situation"""
    id: str
    name: str
    description: str
    encounter_type: EncounterType
    location_restrictions: List[str] = field(default_factory=list)
    time_restrictions: Dict[str, Any] = field(default_factory=dict)
    required_skills: Dict[str, int] = field(default_factory=dict)
    choices: List[Dict[str, Any]] = field(default_factory=list)
    consequences: Dict[str, Any] = field(default_factory=dict)


class EventGenerator:
    """Main class for generating random events and encounters"""
    
    def __init__(self):
        self.events = self._create_events()
        self.encounters = self._create_encounters()
        self.active_events = {}
        self.event_cooldowns = {}
    
    def _create_events(self) -> Dict[str, RandomEvent]:
        """Create all available random events"""
        events = {}
        
        # ENVIRONMENTAL EVENTS
        events["storm_approaching"] = RandomEvent(
            id="storm_approaching",
            name="Storm Approaching",
            description="A severe storm is moving into the area, bringing heavy rain and strong winds.",
            event_type=EventType.ENVIRONMENTAL,
            severity=EventSeverity.MODERATE,
            trigger_conditions={"weather": "clear", "season": ["spring", "summer"]},
            outcomes=[
                EventOutcome(
                    description="The storm passes quickly with minimal damage.",
                    probability=0.6,
                    effects={"visibility": -1, "movement_speed": -1},
                    emotional_impact={"fear": 0.1},
                    narrative_text="The storm brings heavy rain but passes without incident."
                ),
                EventOutcome(
                    description="The storm causes flooding and infrastructure damage.",
                    probability=0.3,
                    effects={"visibility": -2, "movement_speed": -2, "security_level": -1},
                    emotional_impact={"fear": 0.3, "sadness": 0.2},
                    narrative_text="Flooding disrupts normal operations and creates chaos."
                ),
                EventOutcome(
                    description="The storm provides excellent cover for operations.",
                    probability=0.1,
                    effects={"stealth_bonus": 2, "security_level": -2},
                    emotional_impact={"anticipation": 0.2},
                    narrative_text="The storm's chaos provides perfect cover for covert activities."
                )
            ]
        )
        
        events["power_outage"] = RandomEvent(
            id="power_outage",
            name="Power Outage",
            description="A widespread power outage affects the district.",
            event_type=EventType.ENVIRONMENTAL,
            severity=EventSeverity.MODERATE,
            trigger_conditions={"infrastructure": "unstable"},
            outcomes=[
                EventOutcome(
                    description="Limited power outage, mostly inconvenience.",
                    probability=0.5,
                    effects={"hacking_difficulty": 1, "security_systems": -1},
                    emotional_impact={"fear": 0.1},
                    narrative_text="The power outage creates minor disruptions."
                ),
                EventOutcome(
                    description="Extended blackout causes widespread chaos.",
                    probability=0.3,
                    effects={"hacking_difficulty": 2, "security_systems": -2, "unrest": 2},
                    emotional_impact={"fear": 0.4, "anger": 0.2},
                    narrative_text="The blackout plunges the district into darkness and chaos."
                ),
                EventOutcome(
                    description="The outage provides opportunities for infiltration.",
                    probability=0.2,
                    effects={"stealth_bonus": 3, "security_systems": -3},
                    emotional_impact={"anticipation": 0.3},
                    narrative_text="The darkness provides perfect cover for operations."
                )
            ]
        )
        
        # POLITICAL EVENTS
        events["government_crackdown"] = RandomEvent(
            id="government_crackdown",
            name="Government Crackdown",
            description="Authorities launch a major crackdown on suspected resistance activity.",
            event_type=EventType.POLITICAL,
            severity=EventSeverity.MAJOR,
            trigger_conditions={"heat_level": "high", "unrest": "high"},
            outcomes=[
                EventOutcome(
                    description="Increased patrols and surveillance.",
                    probability=0.4,
                    effects={"security_level": 2, "heat_generation": 1},
                    emotional_impact={"fear": 0.3, "anger": 0.2},
                    narrative_text="Police presence increases dramatically across the district."
                ),
                EventOutcome(
                    description="Mass arrests and raids on suspected locations.",
                    probability=0.3,
                    effects={"security_level": 3, "heat_generation": 2, "faction_resources": -1},
                    emotional_impact={"fear": 0.5, "anger": 0.4, "trust": -0.2},
                    narrative_text="Authorities conduct widespread raids and arrests."
                ),
                EventOutcome(
                    description="The crackdown backfires, increasing public support.",
                    probability=0.3,
                    effects={"security_level": 1, "public_support": 2, "recruitment": 1},
                    emotional_impact={"anger": 0.3, "anticipation": 0.2},
                    narrative_text="The heavy-handed response turns public opinion against the government."
                )
            ]
        )
        
        events["policy_change"] = RandomEvent(
            id="policy_change",
            name="New Government Policy",
            description="The government announces new policies affecting the district.",
            event_type=EventType.POLITICAL,
            severity=EventSeverity.MODERATE,
            trigger_conditions={"turn_number": "any"},
            outcomes=[
                EventOutcome(
                    description="Restrictive new policies increase public discontent.",
                    probability=0.4,
                    effects={"unrest": 2, "public_support": 1},
                    emotional_impact={"anger": 0.3, "disgust": 0.2},
                    narrative_text="New restrictions on civil liberties spark public outrage."
                ),
                EventOutcome(
                    description="Economic policies create hardship for residents.",
                    probability=0.3,
                    effects={"unrest": 3, "economic_stability": -2},
                    emotional_impact={"anger": 0.4, "sadness": 0.2},
                    narrative_text="Economic policies create widespread hardship and resentment."
                ),
                EventOutcome(
                    description="The policies are relatively benign.",
                    probability=0.3,
                    effects={"unrest": 0, "public_support": 0},
                    emotional_impact={"anticipation": 0.1},
                    narrative_text="The new policies have minimal impact on daily life."
                )
            ]
        )
        
        # SOCIAL EVENTS
        events["protest_movement"] = RandomEvent(
            id="protest_movement",
            name="Protest Movement",
            description="A spontaneous protest movement emerges in the district.",
            event_type=EventType.SOCIAL,
            severity=EventSeverity.MODERATE,
            trigger_conditions={"unrest": "high", "public_support": "medium"},
            outcomes=[
                EventOutcome(
                    description="Peaceful protest draws attention to issues.",
                    probability=0.4,
                    effects={"public_support": 2, "heat_generation": 1},
                    emotional_impact={"anticipation": 0.2, "joy": 0.1},
                    narrative_text="A peaceful protest draws attention to social issues."
                ),
                EventOutcome(
                    description="Protest turns violent, creating chaos.",
                    probability=0.3,
                    effects={"unrest": 3, "security_level": 2, "heat_generation": 2},
                    emotional_impact={"fear": 0.3, "anger": 0.3},
                    narrative_text="The protest turns violent, creating chaos in the streets."
                ),
                EventOutcome(
                    description="Protest is brutally suppressed by authorities.",
                    probability=0.3,
                    effects={"unrest": 4, "public_support": 3, "security_level": 3},
                    emotional_impact={"anger": 0.5, "fear": 0.2, "disgust": 0.3},
                    narrative_text="Authorities brutally suppress the protest, creating martyrs."
                )
            ]
        )
        
        events["community_support"] = RandomEvent(
            id="community_support",
            name="Community Support",
            description="Local community members offer support to the resistance.",
            event_type=EventType.SOCIAL,
            severity=EventSeverity.MINOR,
            trigger_conditions={"public_support": "high"},
            outcomes=[
                EventOutcome(
                    description="Community provides supplies and information.",
                    probability=0.6,
                    effects={"resources": 1, "intelligence": 1},
                    emotional_impact={"trust": 0.2, "joy": 0.1},
                    narrative_text="Community members provide supplies and valuable information."
                ),
                EventOutcome(
                    description="Community offers safe houses and hiding places.",
                    probability=0.3,
                    effects={"safe_houses": 1, "stealth_bonus": 1},
                    emotional_impact={"trust": 0.3, "joy": 0.2},
                    narrative_text="Community members offer safe houses and hiding places."
                ),
                EventOutcome(
                    description="Community organizes fundraising and recruitment.",
                    probability=0.1,
                    effects={"resources": 2, "recruitment": 2},
                    emotional_impact={"trust": 0.4, "joy": 0.3},
                    narrative_text="The community organizes fundraising and recruitment efforts."
                )
            ]
        )
        
        # ECONOMIC EVENTS
        events["market_crash"] = RandomEvent(
            id="market_crash",
            name="Market Crash",
            description="A sudden economic downturn affects the district.",
            event_type=EventType.ECONOMIC,
            severity=EventSeverity.MAJOR,
            trigger_conditions={"economic_stability": "unstable"},
            outcomes=[
                EventOutcome(
                    description="Economic hardship increases public discontent.",
                    probability=0.5,
                    effects={"unrest": 2, "economic_stability": -2},
                    emotional_impact={"anger": 0.3, "sadness": 0.2},
                    narrative_text="Economic hardship creates widespread discontent."
                ),
                EventOutcome(
                    description="The crash creates opportunities for recruitment.",
                    probability=0.3,
                    effects={"recruitment": 2, "public_support": 1},
                    emotional_impact={"anticipation": 0.2},
                    narrative_text="Economic hardship makes people more receptive to resistance."
                ),
                EventOutcome(
                    description="The crash affects faction resources.",
                    probability=0.2,
                    effects={"faction_resources": -2, "unrest": 1},
                    emotional_impact={"fear": 0.2},
                    narrative_text="The economic crash impacts faction funding and resources."
                )
            ]
        )
        
        events["resource_shortage"] = RandomEvent(
            id="resource_shortage",
            name="Resource Shortage",
            description="Essential resources become scarce in the district.",
            event_type=EventType.ECONOMIC,
            severity=EventSeverity.MODERATE,
            trigger_conditions={"supply_lines": "disrupted"},
            outcomes=[
                EventOutcome(
                    description="Shortage creates minor inconvenience.",
                    probability=0.5,
                    effects={"resource_cost": 1},
                    emotional_impact={"fear": 0.1},
                    narrative_text="Resource shortages create minor inconveniences."
                ),
                EventOutcome(
                    description="Severe shortage affects operations.",
                    probability=0.3,
                    effects={"resource_cost": 2, "operation_difficulty": 1},
                    emotional_impact={"fear": 0.2, "anger": 0.1},
                    narrative_text="Severe shortages make operations more difficult."
                ),
                EventOutcome(
                    description="Shortage creates black market opportunities.",
                    probability=0.2,
                    effects={"black_market": 1, "stealth_bonus": 1},
                    emotional_impact={"anticipation": 0.2},
                    narrative_text="The shortage creates opportunities in the black market."
                )
            ]
        )
        
        # SECURITY EVENTS
        events["surveillance_increase"] = RandomEvent(
            id="surveillance_increase",
            name="Increased Surveillance",
            description="Authorities increase surveillance and monitoring.",
            event_type=EventType.SECURITY,
            severity=EventSeverity.MODERATE,
            trigger_conditions={"heat_level": "medium"},
            outcomes=[
                EventOutcome(
                    description="More cameras and patrols, but manageable.",
                    probability=0.5,
                    effects={"stealth_difficulty": 1, "security_level": 1},
                    emotional_impact={"fear": 0.2},
                    narrative_text="Increased surveillance makes operations more challenging."
                ),
                EventOutcome(
                    description="Heavy surveillance with informant network.",
                    probability=0.3,
                    effects={"stealth_difficulty": 2, "security_level": 2, "heat_generation": 1},
                    emotional_impact={"fear": 0.3, "trust": -0.1},
                    narrative_text="Heavy surveillance and informant networks create paranoia."
                ),
                EventOutcome(
                    description="Surveillance system has vulnerabilities.",
                    probability=0.2,
                    effects={"hacking_opportunity": 1, "intelligence": 1},
                    emotional_impact={"anticipation": 0.2},
                    narrative_text="The surveillance system has exploitable vulnerabilities."
                )
            ]
        )
        
        events["police_raid"] = RandomEvent(
            id="police_raid",
            name="Police Raid",
            description="Police conduct a raid on a suspected resistance location.",
            event_type=EventType.SECURITY,
            severity=EventSeverity.MAJOR,
            trigger_conditions={"heat_level": "high"},
            outcomes=[
                EventOutcome(
                    description="Raid finds nothing, but increases tension.",
                    probability=0.4,
                    effects={"heat_generation": 1, "security_level": 1},
                    emotional_impact={"fear": 0.3, "anger": 0.2},
                    narrative_text="The raid finds nothing but increases tension in the community."
                ),
                EventOutcome(
                    description="Raid captures some operatives.",
                    probability=0.3,
                    effects={"heat_generation": 2, "faction_resources": -1, "morale": -1},
                    emotional_impact={"fear": 0.4, "sadness": 0.3, "anger": 0.3},
                    narrative_text="The raid captures several operatives, dealing a blow to the resistance."
                ),
                EventOutcome(
                    description="Raid is successfully evaded.",
                    probability=0.3,
                    effects={"heat_generation": 0, "morale": 1},
                    emotional_impact={"joy": 0.2, "anticipation": 0.1},
                    narrative_text="Operatives successfully evade the raid, boosting morale."
                )
            ]
        )
        
        # FACTION EVENTS
        events["faction_conflict"] = RandomEvent(
            id="faction_conflict",
            name="Faction Conflict",
            description="Tensions between resistance factions escalate.",
            event_type=EventType.FACTION,
            severity=EventSeverity.MODERATE,
            trigger_conditions={"faction_relations": "tense"},
            outcomes=[
                EventOutcome(
                    description="Minor disagreement, easily resolved.",
                    probability=0.5,
                    effects={"faction_cooperation": -1},
                    emotional_impact={"anger": 0.1},
                    narrative_text="A minor disagreement between factions is quickly resolved."
                ),
                EventOutcome(
                    description="Serious conflict affects operations.",
                    probability=0.3,
                    effects={"faction_cooperation": -2, "operation_difficulty": 1},
                    emotional_impact={"anger": 0.3, "trust": -0.2},
                    narrative_text="Serious conflict between factions hampers operations."
                ),
                EventOutcome(
                    description="Conflict leads to faction split.",
                    probability=0.2,
                    effects={"faction_resources": -1, "public_support": -1},
                    emotional_impact={"anger": 0.4, "sadness": 0.2},
                    narrative_text="The conflict leads to a faction split, weakening the resistance."
                )
            ]
        )
        
        events["allied_support"] = RandomEvent(
            id="allied_support",
            name="Allied Support",
            description="Allied factions provide unexpected support.",
            event_type=EventType.FACTION,
            severity=EventSeverity.MINOR,
            trigger_conditions={"faction_relations": "good"},
            outcomes=[
                EventOutcome(
                    description="Allies provide intelligence and resources.",
                    probability=0.6,
                    effects={"intelligence": 1, "resources": 1},
                    emotional_impact={"trust": 0.2, "joy": 0.1},
                    narrative_text="Allied factions provide valuable intelligence and resources."
                ),
                EventOutcome(
                    description="Allies offer specialized training.",
                    probability=0.3,
                    effects={"skill_bonus": 1, "morale": 1},
                    emotional_impact={"anticipation": 0.2, "joy": 0.1},
                    narrative_text="Allied factions provide specialized training to operatives."
                ),
                EventOutcome(
                    description="Allies coordinate joint operations.",
                    probability=0.1,
                    effects={"operation_bonus": 2, "faction_cooperation": 1},
                    emotional_impact={"anticipation": 0.3, "trust": 0.2},
                    narrative_text="Allied factions coordinate joint operations for maximum impact."
                )
            ]
        )
        
        # PERSONAL EVENTS
        events["personal_crisis"] = RandomEvent(
            id="personal_crisis",
            name="Personal Crisis",
            description="A character faces a personal crisis or dilemma.",
            event_type=EventType.PERSONAL,
            severity=EventSeverity.MODERATE,
            trigger_conditions={"character_stress": "high"},
            outcomes=[
                EventOutcome(
                    description="Character overcomes the crisis with support.",
                    probability=0.5,
                    effects={"character_growth": 1, "team_bonding": 1},
                    emotional_impact={"trust": 0.2, "joy": 0.1},
                    narrative_text="With support from comrades, the character overcomes their crisis."
                ),
                EventOutcome(
                    description="Crisis affects character's effectiveness.",
                    probability=0.3,
                    effects={"character_effectiveness": -1, "stress": 1},
                    emotional_impact={"sadness": 0.2, "fear": 0.1},
                    narrative_text="The personal crisis affects the character's effectiveness."
                ),
                EventOutcome(
                    description="Crisis leads to character growth.",
                    probability=0.2,
                    effects={"character_growth": 2, "skill_bonus": 1},
                    emotional_impact={"anticipation": 0.2, "joy": 0.1},
                    narrative_text="The crisis becomes a catalyst for character growth."
                )
            ]
        )
        
        return events
    
    def _create_encounters(self) -> Dict[str, Encounter]:
        """Create all available encounters"""
        encounters = {}
        
        # FRIENDLY ENCOUNTERS
        encounters["helpful_civilian"] = Encounter(
            id="helpful_civilian",
            name="Helpful Civilian",
            description="A sympathetic civilian offers assistance.",
            encounter_type=EncounterType.FRIENDLY,
            choices=[
                {"text": "Accept their help", "effects": {"resources": 1, "heat": -1}},
                {"text": "Decline politely", "effects": {"heat": 0}},
                {"text": "Recruit them", "effects": {"recruitment": 1, "heat": 1}}
            ]
        )
        
        encounters["former_comrade"] = Encounter(
            id="former_comrade",
            name="Former Comrade",
            description="You encounter a former resistance member who left the struggle.",
            encounter_type=EncounterType.AMBIGUOUS,
            choices=[
                {"text": "Reconnect and recruit", "effects": {"recruitment": 1, "intelligence": 1}},
                {"text": "Respect their choice", "effects": {"heat": -1}},
                {"text": "Question their loyalty", "effects": {"heat": 1, "trust": -1}}
            ]
        )
        
        # NEUTRAL ENCOUNTERS
        encounters["informant"] = Encounter(
            id="informant",
            name="Potential Informant",
            description="Someone approaches with information to sell.",
            encounter_type=EncounterType.NEUTRAL,
            required_skills={"social": 2},
            choices=[
                {"text": "Buy the information", "effects": {"intelligence": 2, "resources": -1}},
                {"text": "Negotiate the price", "effects": {"intelligence": 1, "resources": -1}},
                {"text": "Decline", "effects": {"heat": 0}}
            ]
        )
        
        encounters["street_vendor"] = Encounter(
            id="street_vendor",
            name="Street Vendor",
            description="A street vendor offers unusual goods.",
            encounter_type=EncounterType.NEUTRAL,
            choices=[
                {"text": "Browse their wares", "effects": {"equipment": 1, "resources": -1}},
                {"text": "Ask about rumors", "effects": {"intelligence": 1}},
                {"text": "Move on", "effects": {"heat": 0}}
            ]
        )
        
        # HOSTILE ENCOUNTERS
        encounters["police_patrol"] = Encounter(
            id="police_patrol",
            name="Police Patrol",
            description="You encounter a police patrol while moving through the district.",
            encounter_type=EncounterType.HOSTILE,
            required_skills={"stealth": 3},
            choices=[
                {"text": "Try to hide", "effects": {"heat": -1, "stealth_test": True}},
                {"text": "Act natural", "effects": {"heat": 0, "social_test": True}},
                {"text": "Run", "effects": {"heat": 2, "escape_test": True}}
            ]
        )
        
        encounters["corporate_security"] = Encounter(
            id="corporate_security",
            name="Corporate Security",
            description="Corporate security forces are conducting surveillance.",
            encounter_type=EncounterType.HOSTILE,
            required_skills={"stealth": 2, "hacking": 1},
            choices=[
                {"text": "Avoid detection", "effects": {"heat": -1, "stealth_test": True}},
                {"text": "Jam their systems", "effects": {"heat": 1, "hacking_test": True}},
                {"text": "Create a diversion", "effects": {"heat": 2, "combat_test": True}}
            ]
        )
        
        # AMBIGUOUS ENCOUNTERS
        encounters["mysterious_stranger"] = Encounter(
            id="mysterious_stranger",
            name="Mysterious Stranger",
            description="A mysterious figure approaches with an offer.",
            encounter_type=EncounterType.AMBIGUOUS,
            required_skills={"intelligence": 2},
            choices=[
                {"text": "Hear them out", "effects": {"intelligence": 1, "risk": 1}},
                {"text": "Be cautious", "effects": {"heat": 0, "intelligence": 0}},
                {"text": "Reject immediately", "effects": {"heat": -1, "opportunity": -1}}
            ]
        )
        
        encounters["double_agent"] = Encounter(
            id="double_agent",
            name="Suspected Double Agent",
            description="You suspect someone in your network is working for the authorities.",
            encounter_type=EncounterType.AMBIGUOUS,
            required_skills={"intelligence": 3, "social": 2},
            choices=[
                {"text": "Confront them", "effects": {"heat": 2, "trust": -1, "intelligence": 1}},
                {"text": "Gather evidence", "effects": {"intelligence": 2, "heat": 0}},
                {"text": "Monitor them", "effects": {"heat": 0, "intelligence": 1}}
            ]
        )
        
        # MYSTERIOUS ENCOUNTERS
        encounters["strange_signal"] = Encounter(
            id="strange_signal",
            name="Strange Signal",
            description="Your equipment picks up an unusual signal or transmission.",
            encounter_type=EncounterType.MYSTERIOUS,
            required_skills={"technical": 2, "hacking": 1},
            choices=[
                {"text": "Investigate the signal", "effects": {"intelligence": 2, "risk": 2}},
                {"text": "Trace its source", "effects": {"intelligence": 1, "heat": 1}},
                {"text": "Ignore it", "effects": {"heat": 0, "opportunity": -1}}
            ]
        )
        
        encounters["hidden_cache"] = Encounter(
            id="hidden_cache",
            name="Hidden Cache",
            description="You discover a hidden cache of supplies or information.",
            encounter_type=EncounterType.MYSTERIOUS,
            required_skills={"survival": 2},
            choices=[
                {"text": "Take everything", "effects": {"resources": 2, "heat": 1}},
                {"text": "Take only what you need", "effects": {"resources": 1, "heat": 0}},
                {"text": "Leave it for others", "effects": {"heat": -1, "morale": 1}}
            ]
        )
        
        return encounters
    
    def generate_random_event(self, game_state: Dict[str, Any]) -> Optional[RandomEvent]:
        """Generate a random event based on current game state"""
        available_events = []
        
        for event_id, event in self.events.items():
            # Check if event is on cooldown
            if event_id in self.event_cooldowns:
                if self.event_cooldowns[event_id] > 0:
                    continue
            
            # Check trigger conditions
            if self._check_event_conditions(event, game_state):
                available_events.append(event)
        
        if not available_events:
            return None
        
        # Weight events by severity and current game state
        weighted_events = []
        for event in available_events:
            weight = self._calculate_event_weight(event, game_state)
            weighted_events.extend([event] * weight)
        
        if not weighted_events:
            return None
        
        return random.choice(weighted_events)
    
    def generate_random_encounter(self, character: Any, location: str) -> Optional[Encounter]:
        """Generate a random encounter for a character"""
        available_encounters = []
        
        for encounter_id, encounter in self.encounters.items():
            # Check location restrictions
            if encounter.location_restrictions and location not in encounter.location_restrictions:
                continue
            
            # Check skill requirements
            if self._check_encounter_requirements(encounter, character):
                available_encounters.append(encounter)
        
        if not available_encounters:
            return None
        
        return random.choice(available_encounters)
    
    def _check_event_conditions(self, event: RandomEvent, game_state: Dict[str, Any]) -> bool:
        """Check if event conditions are met"""
        conditions = event.trigger_conditions
        
        for condition, value in conditions.items():
            if condition == "turn_number" and value == "any":
                continue
            
            if condition in game_state:
                if isinstance(value, list):
                    if game_state[condition] not in value:
                        return False
                elif game_state[condition] != value:
                    return False
            else:
                return False
        
        return True
    
    def _calculate_event_weight(self, event: RandomEvent, game_state: Dict[str, Any]) -> int:
        """Calculate event weight based on severity and game state"""
        base_weight = {
            EventSeverity.MINOR: 1,
            EventSeverity.MODERATE: 2,
            EventSeverity.MAJOR: 3,
            EventSeverity.CRITICAL: 4
        }
        
        weight = base_weight.get(event.severity, 1)
        
        # Adjust weight based on game state
        if "unrest" in game_state and game_state["unrest"] > 5:
            weight += 1
        
        if "heat_level" in game_state and game_state["heat_level"] > 5:
            weight += 1
        
        return weight
    
    def _check_encounter_requirements(self, encounter: Encounter, character: Any) -> bool:
        """Check if character meets encounter requirements"""
        if not encounter.required_skills:
            return True
        
        for skill, level in encounter.required_skills.items():
            if hasattr(character, 'skills') and hasattr(character.skills, skill):
                if getattr(character.skills, skill) < level:
                    return False
        
        return True
    
    def apply_event_outcome(self, event: RandomEvent, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Apply an event outcome to the game state"""
        outcome = event.get_random_outcome()
        
        # Apply effects
        for effect, value in outcome.effects.items():
            if effect in game_state:
                if isinstance(game_state[effect], (int, float)):
                    game_state[effect] += value
                elif isinstance(game_state[effect], str):
                    game_state[effect] = value
        
        # Set cooldown
        self.event_cooldowns[event.id] = event.cooldown
        
        return outcome
    
    def update_cooldowns(self):
        """Update event cooldowns"""
        for event_id in list(self.event_cooldowns.keys()):
            if self.event_cooldowns[event_id] > 0:
                self.event_cooldowns[event_id] -= 1
            else:
                del self.event_cooldowns[event_id]


def create_event_generator() -> EventGenerator:
    """Create and return an event generator instance"""
    return EventGenerator()


if __name__ == "__main__":
    # Test the event system
    print("Testing Random Events System")
    print("=" * 50)
    
    generator = create_event_generator()
    
    # Test event generation
    game_state = {
        "weather": "clear",
        "season": "summer",
        "unrest": 6,
        "heat_level": 7
    }
    
    event = generator.generate_random_event(game_state)
    if event:
        print(f"Generated event: {event.name}")
        print(f"Description: {event.description}")
        print(f"Severity: {event.severity.value}")
        
        outcome = generator.apply_event_outcome(event, game_state)
        print(f"Outcome: {outcome.description}")
        print(f"Effects: {outcome.effects}")
    else:
        print("No events available for current game state")
    
    print(f"\nUpdated game state: {game_state}") 