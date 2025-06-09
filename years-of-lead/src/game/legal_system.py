"""
Years of Lead - Legal Tracking and Imprisonment System

Comprehensive legal system that tracks crimes, witnesses, evidence,
and manages arrests, trials, and imprisonment.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime
import random

from .core import Agent, AgentStatus, Location


class CrimeType(Enum):
    """Classification of crimes by severity"""
    # Legal Activities
    PEACEFUL_PROTEST = "peaceful_protest"
    LEGAL_ADVOCACY = "legal_advocacy"
    COMMUNITY_ORGANIZING = "community_organizing"
    
    # Minor Crimes (Misdemeanors)
    VANDALISM = "vandalism"
    TRESPASSING = "trespassing"
    DISTURBING_PEACE = "disturbing_peace"
    MINOR_THEFT = "minor_theft"
    GRAFFITI = "graffiti"
    
    # Major Crimes (Felonies)
    ASSAULT = "assault"
    BURGLARY = "burglary" 
    GRAND_THEFT = "grand_theft"
    PROPERTY_DESTRUCTION = "property_destruction"
    ARSON = "arson"
    KIDNAPPING = "kidnapping"
    
    # Capital Crimes
    MURDER = "murder"
    TERRORISM = "terrorism"
    TREASON = "treason"
    ASSASSINATION = "assassination"
    MASS_DESTRUCTION = "mass_destruction"


class WitnessType(Enum):
    """Types of witnesses"""
    NONE = "none"
    CIVILIAN = "civilian"
    POLICE = "police"
    SECURITY = "security"
    GOVERNMENT = "government"
    MEDIA = "media"
    INFORMANT = "informant"


class IdentificationLevel(Enum):
    """Level of agent identification"""
    UNKNOWN = "unknown"
    PARTIAL = "partial"  # Height, build, general description
    DETAILED = "detailed"  # Face seen, distinguishing features
    FULL = "full"  # Name known, complete identification


class EvidenceType(Enum):
    """Types of evidence"""
    NONE = "none"
    CIRCUMSTANTIAL = "circumstantial"
    PHYSICAL = "physical"
    FORENSIC = "forensic"
    DIGITAL = "digital"
    EYEWITNESS = "eyewitness"
    CONFESSION = "confession"
    DOCUMENTARY = "documentary"


class LegalStatus(Enum):
    """Legal status of an agent"""
    CLEAN = "clean"
    SUSPECTED = "suspected"
    WANTED = "wanted"
    ARRESTED = "arrested"
    ON_TRIAL = "on_trial"
    CONVICTED = "convicted"
    IMPRISONED = "imprisoned"
    RELEASED = "released"
    FUGITIVE = "fugitive"


class PrisonSecurity(Enum):
    """Prison security levels"""
    MINIMUM = "minimum"
    MEDIUM = "medium"
    MAXIMUM = "maximum"
    SUPERMAX = "supermax"


@dataclass
class CrimeRecord:
    """Record of a committed crime"""
    id: str
    crime_type: CrimeType
    date_committed: int  # Turn number
    location_id: str
    agent_ids: List[str]  # Agents involved
    witness_type: WitnessType = WitnessType.NONE
    witness_count: int = 0
    identification_level: IdentificationLevel = IdentificationLevel.UNKNOWN
    evidence_types: Set[EvidenceType] = field(default_factory=set)
    reported: bool = False
    report_turn: Optional[int] = None
    media_coverage: bool = False
    government_attention: bool = False
    description: str = ""
    
    def calculate_severity_score(self) -> float:
        """Calculate a severity score for the crime"""
        # Base severity by crime type
        severity_scores = {
            CrimeType.PEACEFUL_PROTEST: 0.1,
            CrimeType.VANDALISM: 0.3,
            CrimeType.ASSAULT: 0.6,
            CrimeType.BURGLARY: 0.7,
            CrimeType.MURDER: 1.0,
            CrimeType.TERRORISM: 1.0
        }
        
        base_score = severity_scores.get(self.crime_type, 0.5)
        
        # Modifiers
        if self.witness_type != WitnessType.NONE:
            base_score += 0.1
        if self.identification_level == IdentificationLevel.FULL:
            base_score += 0.2
        if self.media_coverage:
            base_score += 0.1
        if self.government_attention:
            base_score += 0.2
        
        return min(1.0, base_score)


@dataclass
class ArrestRecord:
    """Record of an arrest"""
    id: str
    agent_id: str
    crime_record_id: str
    arrest_turn: int
    arresting_authority: str  # "police", "military", "intelligence"
    violence_used: bool = False
    escape_attempted: bool = False
    escape_successful: bool = False
    
    
@dataclass
class TrialRecord:
    """Record of a legal trial"""
    id: str
    agent_id: str
    crime_records: List[str]  # Crime record IDs
    trial_start_turn: int
    trial_end_turn: Optional[int] = None
    verdict: Optional[str] = None  # "guilty", "not_guilty", "mistrial"
    sentence_years: Optional[int] = None
    defense_quality: float = 0.5  # 0.0 to 1.0
    public_support: float = 0.0  # -1.0 to 1.0
    media_circus: bool = False
    

@dataclass
class PrisonRecord:
    """Record of imprisonment"""
    id: str
    agent_id: str
    facility_name: str
    security_level: PrisonSecurity
    sentence_start: int
    sentence_length: int  # In turns
    time_served: int = 0
    behavior_score: float = 0.5  # 0.0 to 1.0
    escape_attempts: int = 0
    parole_eligible: bool = False
    activities: List[str] = field(default_factory=list)
    connections_made: List[str] = field(default_factory=list)
    

@dataclass
class LegalProfile:
    """Complete legal profile for an agent"""
    agent_id: str
    legal_status: LegalStatus = LegalStatus.CLEAN
    crime_records: List[CrimeRecord] = field(default_factory=list)
    arrest_records: List[ArrestRecord] = field(default_factory=list)
    trial_records: List[TrialRecord] = field(default_factory=list)
    prison_records: List[PrisonRecord] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)
    known_associates: Set[str] = field(default_factory=set)
    surveillance_level: int = 0  # 0-10
    
    def get_total_crimes(self) -> int:
        """Get total number of crimes committed"""
        return len(self.crime_records)
    
    def get_conviction_rate(self) -> float:
        """Calculate conviction rate"""
        if not self.trial_records:
            return 0.0
        
        convictions = sum(1 for trial in self.trial_records if trial.verdict == "guilty")
        return convictions / len(self.trial_records)
    
    def is_wanted(self) -> bool:
        """Check if agent is currently wanted"""
        return self.legal_status in [LegalStatus.WANTED, LegalStatus.FUGITIVE]
    
    def is_imprisoned(self) -> bool:
        """Check if agent is currently imprisoned"""
        return self.legal_status == LegalStatus.IMPRISONED


class LegalSystem:
    """Main legal system manager"""
    
    def __init__(self):
        self.legal_profiles: Dict[str, LegalProfile] = {}
        self.crime_counter = 0
        self.arrest_counter = 0
        self.trial_counter = 0
        self.prison_counter = 0
        
        # System configuration
        self.witness_report_chance = {
            WitnessType.CIVILIAN: 0.3,
            WitnessType.POLICE: 0.9,
            WitnessType.SECURITY: 0.8,
            WitnessType.GOVERNMENT: 0.95,
            WitnessType.MEDIA: 0.7,
            WitnessType.INFORMANT: 0.85
        }
        
        self.identification_degradation = 0.1  # Per turn
        self.surveillance_decay = 0.05  # Per turn
    
    def record_crime(self, agents: List[Agent], crime_type: CrimeType, 
                    location: Location, witnesses: int = 0, 
                    witness_type: WitnessType = WitnessType.NONE,
                    evidence: Set[EvidenceType] = None) -> CrimeRecord:
        """Record a crime committed by agents"""
        
        self.crime_counter += 1
        crime_id = f"crime_{self.crime_counter}"
        
        # Determine identification level based on circumstances
        identification = self._determine_identification(
            agents, location, witnesses, witness_type
        )
        
        # Create crime record
        crime = CrimeRecord(
            id=crime_id,
            crime_type=crime_type,
            date_committed=0,  # Should be passed current turn
            location_id=location.id,
            agent_ids=[agent.id for agent in agents],
            witness_type=witness_type,
            witness_count=witnesses,
            identification_level=identification,
            evidence_types=evidence or set()
        )
        
        # Update agent profiles
        for agent in agents:
            profile = self._get_or_create_profile(agent.id)
            profile.crime_records.append(crime)
            
            # Update legal status
            if crime_type in [CrimeType.MURDER, CrimeType.TERRORISM, CrimeType.ASSASSINATION]:
                profile.legal_status = LegalStatus.WANTED
                profile.surveillance_level = min(10, profile.surveillance_level + 3)
            elif crime_type in [CrimeType.ASSAULT, CrimeType.BURGLARY, CrimeType.ARSON]:
                if identification == IdentificationLevel.FULL:
                    profile.legal_status = LegalStatus.WANTED
                else:
                    profile.legal_status = LegalStatus.SUSPECTED
                profile.surveillance_level = min(10, profile.surveillance_level + 2)
        
        # Check if crime is reported
        if self._is_crime_reported(crime):
            crime.reported = True
            crime.report_turn = 0  # Should be current turn
            
            # Check for media coverage
            if crime_type in [CrimeType.MURDER, CrimeType.TERRORISM, CrimeType.ASSASSINATION]:
                crime.media_coverage = True
                crime.government_attention = True
        
        return crime
    
    def attempt_arrest(self, agent: Agent, location: Location, 
                      force_level: str = "normal") -> Tuple[bool, Optional[ArrestRecord]]:
        """Attempt to arrest an agent"""
        
        profile = self._get_or_create_profile(agent.id)
        
        # Can't arrest if not wanted
        if not profile.is_wanted():
            return False, None
        
        # Calculate arrest success chance
        base_chance = 0.5
        
        # Location security modifier
        security_modifier = location.security_level / 20.0
        
        # Agent skill modifier (stealth and combat)
        agent_evasion = (
            agent.skills.get(SkillType.STEALTH, 1).level + 
            agent.skills.get(SkillType.COMBAT, 1).level
        ) / 20.0
        
        # Force level modifier
        force_modifiers = {
            "minimal": -0.1,
            "normal": 0.0,
            "heavy": 0.2,
            "overwhelming": 0.4
        }
        force_modifier = force_modifiers.get(force_level, 0.0)
        
        # Calculate final chance
        arrest_chance = base_chance + security_modifier - agent_evasion + force_modifier
        arrest_chance = max(0.1, min(0.9, arrest_chance))
        
        # Attempt arrest
        if random.random() < arrest_chance:
            # Successful arrest
            self.arrest_counter += 1
            arrest_id = f"arrest_{self.arrest_counter}"
            
            # Find most recent crime
            recent_crime = max(
                profile.crime_records, 
                key=lambda c: c.date_committed
            ) if profile.crime_records else None
            
            arrest = ArrestRecord(
                id=arrest_id,
                agent_id=agent.id,
                crime_record_id=recent_crime.id if recent_crime else "unknown",
                arrest_turn=0,  # Should be current turn
                arresting_authority="police",
                violence_used=force_level in ["heavy", "overwhelming"]
            )
            
            # Update agent status
            agent.status = AgentStatus.ARRESTED
            profile.legal_status = LegalStatus.ARRESTED
            profile.arrest_records.append(arrest)
            
            return True, arrest
        else:
            # Failed arrest - agent might escape
            if force_level in ["heavy", "overwhelming"]:
                # Agent becomes fugitive
                profile.legal_status = LegalStatus.FUGITIVE
                profile.surveillance_level = 10
            
            return False, None
    
    def conduct_trial(self, agent: Agent, crimes: List[CrimeRecord],
                     defense_quality: float = 0.5) -> TrialRecord:
        """Conduct a trial for an agent"""
        
        self.trial_counter += 1
        trial_id = f"trial_{self.trial_counter}"
        
        profile = self._get_or_create_profile(agent.id)
        
        # Create trial record
        trial = TrialRecord(
            id=trial_id,
            agent_id=agent.id,
            crime_records=[crime.id for crime in crimes],
            trial_start_turn=0,  # Should be current turn
            defense_quality=defense_quality
        )
        
        # Calculate verdict probability
        conviction_chance = self._calculate_conviction_chance(
            crimes, defense_quality
        )
        
        # Determine verdict
        if random.random() < conviction_chance:
            trial.verdict = "guilty"
            
            # Calculate sentence
            total_severity = sum(crime.calculate_severity_score() for crime in crimes)
            base_sentence = int(total_severity * 10)  # Base 10 turns per severity point
            
            # Adjust for defense quality
            sentence_modifier = 1.0 - (defense_quality * 0.3)
            trial.sentence_years = max(1, int(base_sentence * sentence_modifier))
            
            # Update legal status
            profile.legal_status = LegalStatus.CONVICTED
        else:
            trial.verdict = "not_guilty"
            profile.legal_status = LegalStatus.CLEAN
            
            # Clear surveillance if acquitted
            profile.surveillance_level = max(0, profile.surveillance_level - 3)
        
        profile.trial_records.append(trial)
        return trial
    
    def imprison_agent(self, agent: Agent, sentence_length: int, 
                       facility: str = "State Prison") -> PrisonRecord:
        """Imprison a convicted agent"""
        
        self.prison_counter += 1
        prison_id = f"prison_{self.prison_counter}"
        
        profile = self._get_or_create_profile(agent.id)
        
        # Determine security level based on crimes
        security_level = self._determine_prison_security(profile)
        
        # Create prison record
        prison = PrisonRecord(
            id=prison_id,
            agent_id=agent.id,
            facility_name=facility,
            security_level=security_level,
            sentence_start=0,  # Should be current turn
            sentence_length=sentence_length
        )
        
        # Update agent status
        agent.status = AgentStatus.ARRESTED  # Could add IMPRISONED status
        profile.legal_status = LegalStatus.IMPRISONED
        profile.prison_records.append(prison)
        
        return prison
    
    def update_prisoners(self, current_turn: int):
        """Update all imprisoned agents"""
        
        for profile in self.legal_profiles.values():
            if profile.legal_status == LegalStatus.IMPRISONED:
                # Find active prison record
                active_prison = next(
                    (p for p in profile.prison_records 
                     if p.time_served < p.sentence_length),
                    None
                )
                
                if active_prison:
                    active_prison.time_served += 1
                    
                    # Check for release
                    if active_prison.time_served >= active_prison.sentence_length:
                        self._release_prisoner(profile.agent_id, active_prison)
                    
                    # Check for parole eligibility
                    elif active_prison.time_served >= active_prison.sentence_length * 0.5:
                        active_prison.parole_eligible = True
    
    def _get_or_create_profile(self, agent_id: str) -> LegalProfile:
        """Get or create a legal profile for an agent"""
        if agent_id not in self.legal_profiles:
            self.legal_profiles[agent_id] = LegalProfile(agent_id=agent_id)
        return self.legal_profiles[agent_id]
    
    def _determine_identification(self, agents: List[Agent], location: Location,
                                 witnesses: int, witness_type: WitnessType) -> IdentificationLevel:
        """Determine how well agents were identified"""
        
        if witness_type == WitnessType.NONE or witnesses == 0:
            return IdentificationLevel.UNKNOWN
        
        # Base identification chance by witness type
        id_chances = {
            WitnessType.CIVILIAN: 0.3,
            WitnessType.POLICE: 0.7,
            WitnessType.SECURITY: 0.6,
            WitnessType.GOVERNMENT: 0.8,
            WitnessType.MEDIA: 0.5,
            WitnessType.INFORMANT: 0.9
        }
        
        base_chance = id_chances.get(witness_type, 0.5)
        
        # Modify by location lighting/visibility
        if location.id in ["night_market", "underground", "sewers"]:
            base_chance *= 0.5
        
        # Modify by number of witnesses
        if witnesses > 5:
            base_chance *= 1.3
        
        # Roll for identification
        roll = random.random()
        
        if roll < base_chance * 0.3:
            return IdentificationLevel.PARTIAL
        elif roll < base_chance * 0.7:
            return IdentificationLevel.DETAILED
        elif roll < base_chance:
            return IdentificationLevel.FULL
        else:
            return IdentificationLevel.UNKNOWN
    
    def _is_crime_reported(self, crime: CrimeRecord) -> bool:
        """Determine if a crime is reported to authorities"""
        
        if crime.witness_type == WitnessType.NONE:
            return False
        
        report_chance = self.witness_report_chance.get(
            crime.witness_type, 0.5
        )
        
        # Modify by crime severity
        if crime.crime_type in [CrimeType.MURDER, CrimeType.TERRORISM]:
            report_chance = min(1.0, report_chance * 1.5)
        
        return random.random() < report_chance
    
    def _calculate_conviction_chance(self, crimes: List[CrimeRecord], 
                                   defense_quality: float) -> float:
        """Calculate chance of conviction in trial"""
        
        base_chance = 0.5
        
        # Evidence quality
        all_evidence = set()
        for crime in crimes:
            all_evidence.update(crime.evidence_types)
        
        evidence_modifier = len(all_evidence) * 0.1
        
        # Witness testimony
        witness_modifier = sum(
            0.1 if crime.witness_type != WitnessType.NONE else 0
            for crime in crimes
        )
        
        # Identification quality
        id_modifier = sum(
            0.2 if crime.identification_level == IdentificationLevel.FULL else
            0.1 if crime.identification_level == IdentificationLevel.DETAILED else 0
            for crime in crimes
        ) / len(crimes)
        
        # Defense quality reduction
        defense_reduction = defense_quality * 0.4
        
        conviction_chance = base_chance + evidence_modifier + witness_modifier + id_modifier - defense_reduction
        
        return max(0.1, min(0.9, conviction_chance))
    
    def _determine_prison_security(self, profile: LegalProfile) -> PrisonSecurity:
        """Determine appropriate prison security level"""
        
        # Check for capital crimes
        capital_crimes = [
            crime for crime in profile.crime_records
            if crime.crime_type in [CrimeType.MURDER, CrimeType.TERRORISM, CrimeType.ASSASSINATION]
        ]
        
        if capital_crimes:
            return PrisonSecurity.SUPERMAX if len(capital_crimes) > 1 else PrisonSecurity.MAXIMUM
        
        # Check for violent crimes
        violent_crimes = [
            crime for crime in profile.crime_records
            if crime.crime_type in [CrimeType.ASSAULT, CrimeType.KIDNAPPING, CrimeType.ARSON]
        ]
        
        if violent_crimes:
            return PrisonSecurity.MAXIMUM if len(violent_crimes) > 2 else PrisonSecurity.MEDIUM
        
        # Default to minimum for non-violent crimes
        return PrisonSecurity.MINIMUM
    
    def _release_prisoner(self, agent_id: str, prison_record: PrisonRecord):
        """Release a prisoner who has served their sentence"""
        
        profile = self.legal_profiles.get(agent_id)
        if profile:
            profile.legal_status = LegalStatus.RELEASED
            
            # Maintain some surveillance on released prisoners
            profile.surveillance_level = max(3, profile.surveillance_level) 