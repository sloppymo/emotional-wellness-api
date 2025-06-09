"""
Years of Lead - Character Creation System

This module provides a comprehensive character creation system for the Years of Lead
insurgency simulator, including detailed backgrounds, skills, traits, and emotional profiles.
"""

import random
import uuid
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from .emotional_state import EmotionalState, create_random_emotional_state


class BackgroundType(Enum):
    """Character background types"""
    ACADEMIC = "academic"
    MILITARY = "military"
    CRIMINAL = "criminal"
    CORPORATE = "corporate"
    MEDICAL = "medical"
    TECHNICAL = "technical"
    JOURNALIST = "journalist"
    RELIGIOUS = "religious"
    ACTIVIST = "activist"
    LABORER = "laborer"


class PersonalityTrait(Enum):
    """Personality traits that affect character behavior"""
    IDEALISTIC = "idealistic"
    PRAGMATIC = "pragmatic"
    CAUTIOUS = "cautious"
    RECKLESS = "reckless"
    COMPASSIONATE = "compassionate"
    RUTHLESS = "ruthless"
    ANALYTICAL = "analytical"
    INTUITIVE = "intuitive"
    LOYAL = "loyal"
    OPPORTUNISTIC = "opportunistic"
    LEADER = "leader"
    FOLLOWER = "follower"
    OPTIMISTIC = "optimistic"
    PESSIMISTIC = "pessimistic"
    CREATIVE = "creative"
    METHODICAL = "methodical"


class SkillCategory(Enum):
    """Skill categories for character creation"""
    COMBAT = "combat"
    STEALTH = "stealth"
    HACKING = "hacking"
    SOCIAL = "social"
    TECHNICAL = "technical"
    MEDICAL = "medical"
    SURVIVAL = "survival"
    INTELLIGENCE = "intelligence"


class TraumaType(Enum):
    """Types of trauma that can affect characters"""
    COMBAT_TRAUMA = "combat_trauma"
    BETRAYAL = "betrayal"
    LOSS_OF_LOVED_ONE = "loss_of_loved_one"
    IMPRISONMENT = "imprisonment"
    TORTURE = "torture"
    WITNESSING_VIOLENCE = "witnessing_violence"
    ECONOMIC_HARDSHIP = "economic_hardship"
    DISCRIMINATION = "discrimination"
    FAMILY_SEPARATION = "family_separation"
    NATURAL_DISASTER = "natural_disaster"


@dataclass
class Background:
    """Character background with associated bonuses and traits"""
    type: BackgroundType
    name: str
    description: str
    skill_bonuses: Dict[SkillCategory, int]
    trait_modifiers: List[PersonalityTrait]
    starting_resources: Dict[str, int]
    connections: List[str]  # NPC connections
    trauma_risk: List[TraumaType]
    
    def get_background_story(self, character_name: str) -> str:
        """Generate a personalized background story"""
        stories = {
            BackgroundType.ACADEMIC: f"{character_name} was once a promising academic, their research into social inequality leading them to question the system they were meant to serve.",
            BackgroundType.MILITARY: f"{character_name} served in the military, but the horrors they witnessed and the orders they followed left them disillusioned with authority.",
            BackgroundType.CRIMINAL: f"{character_name} grew up in the streets, learning to survive in a world that had already written them off as expendable.",
            BackgroundType.CORPORATE: f"{character_name} climbed the corporate ladder, only to discover the true cost of their success and the human lives it destroyed.",
            BackgroundType.MEDICAL: f"{character_name} dedicated their life to healing, but the system's failures and the suffering they couldn't prevent drove them to seek change.",
            BackgroundType.TECHNICAL: f"{character_name} was a brilliant technician, their skills used to maintain systems of control until they decided to turn those skills against them.",
            BackgroundType.JOURNALIST: f"{character_name} sought the truth as a journalist, but the stories they uncovered and the threats they faced showed them the need for direct action.",
            BackgroundType.RELIGIOUS: f"{character_name} found faith, but their spiritual journey led them to question not just the state, but the very nature of justice and morality.",
            BackgroundType.ACTIVIST: f"{character_name} has always fought for change, but peaceful protest proved insufficient against the forces arrayed against them.",
            BackgroundType.LABORER: f"{character_name} worked with their hands, building the world that others profited from, until they decided to build something different."
        }
        return stories.get(self.type, f"{character_name} has a complex past that led them to the resistance.")


@dataclass
class CharacterSkills:
    """Character skill system"""
    combat: int = 1
    stealth: int = 1
    hacking: int = 1
    social: int = 1
    technical: int = 1
    medical: int = 1
    survival: int = 1
    intelligence: int = 1
    
    def apply_background_bonuses(self, background: Background):
        """Apply background skill bonuses"""
        for skill_category, bonus in background.skill_bonuses.items():
            if hasattr(self, skill_category.value):
                current_value = getattr(self, skill_category.value)
                setattr(self, skill_category.value, current_value + bonus)
    
    def get_total_skill_points(self) -> int:
        """Get total skill points invested"""
        return sum([
            self.combat, self.stealth, self.hacking, self.social,
            self.technical, self.medical, self.survival, self.intelligence
        ])
    
    def can_increase_skill(self, skill_category: SkillCategory, current_points: int, max_points: int) -> bool:
        """Check if a skill can be increased"""
        if current_points >= max_points:
            return False
        
        current_skill = getattr(self, skill_category.value)
        return current_skill < 10  # Max skill level of 10


@dataclass
class CharacterTraits:
    """Character personality traits"""
    primary_trait: PersonalityTrait
    secondary_trait: PersonalityTrait
    background_traits: List[PersonalityTrait] = field(default_factory=list)
    
    def get_all_traits(self) -> List[PersonalityTrait]:
        """Get all character traits"""
        return [self.primary_trait, self.secondary_trait] + self.background_traits
    
    def get_trait_description(self) -> str:
        """Get a description of the character's personality"""
        trait_descriptions = {
            PersonalityTrait.IDEALISTIC: "driven by strong moral convictions",
            PersonalityTrait.PRAGMATIC: "focused on practical results",
            PersonalityTrait.CAUTIOUS: "careful and methodical in approach",
            PersonalityTrait.RECKLESS: "willing to take bold risks",
            PersonalityTrait.COMPASSIONATE: "deeply concerned with others' welfare",
            PersonalityTrait.RUTHLESS: "willing to make hard choices",
            PersonalityTrait.ANALYTICAL: "thinks through problems systematically",
            PersonalityTrait.INTUITIVE: "relies on gut feelings and instincts",
            PersonalityTrait.LOYAL: "devoted to comrades and cause",
            PersonalityTrait.OPPORTUNISTIC: "adapts quickly to changing situations",
            PersonalityTrait.LEADER: "naturally takes charge in groups",
            PersonalityTrait.FOLLOWER: "prefers to support others' leadership",
            PersonalityTrait.OPTIMISTIC: "maintains hope even in dark times",
            PersonalityTrait.PESSIMISTIC: "prepares for the worst outcomes",
            PersonalityTrait.CREATIVE: "finds innovative solutions to problems",
            PersonalityTrait.METHODICAL: "follows established procedures"
        }
        
        primary_desc = trait_descriptions.get(self.primary_trait, "complex")
        secondary_desc = trait_descriptions.get(self.secondary_trait, "multifaceted")
        
        return f"{primary_desc} and {secondary_desc}"


@dataclass
class CharacterTrauma:
    """Character trauma and its effects"""
    type: TraumaType
    severity: float  # 0.0 to 1.0
    description: str
    emotional_impact: Dict[str, float]
    triggers: List[str]
    
    def get_trauma_story(self, character_name: str) -> str:
        """Generate a trauma story for the character"""
        stories = {
            TraumaType.COMBAT_TRAUMA: f"{character_name} has seen combat and carries the psychological scars of violence.",
            TraumaType.BETRAYAL: f"{character_name} was betrayed by someone they trusted, leaving deep emotional wounds.",
            TraumaType.LOSS_OF_LOVED_ONE: f"{character_name} lost someone close to them, a loss that still haunts them.",
            TraumaType.IMPRISONMENT: f"{character_name} has experienced imprisonment, the trauma of confinement still affecting them.",
            TraumaType.TORTURE: f"{character_name} endured torture, leaving both physical and psychological scars.",
            TraumaType.WITNESSING_VIOLENCE: f"{character_name} witnessed horrific violence that changed them forever.",
            TraumaType.ECONOMIC_HARDSHIP: f"{character_name} experienced severe economic hardship that shaped their worldview.",
            TraumaType.DISCRIMINATION: f"{character_name} faced systematic discrimination that left lasting psychological impact.",
            TraumaType.FAMILY_SEPARATION: f"{character_name} was separated from their family, a loss that still affects them.",
            TraumaType.NATURAL_DISASTER: f"{character_name} survived a natural disaster that left them with trauma."
        }
        return stories.get(self.type, f"{character_name} carries trauma from their past experiences.")


@dataclass
class CharacterMotivation:
    """Character motivation and goals"""
    primary_motivation: str
    secondary_motivation: str
    personal_goal: str
    ideological_commitment: float  # 0.0 to 1.0
    willingness_to_sacrifice: float  # 0.0 to 1.0
    
    def get_motivation_description(self) -> str:
        """Get a description of the character's motivations"""
        return f"Driven by {self.primary_motivation} and {self.secondary_motivation}. Their personal goal is {self.personal_goal}."


class CharacterCreator:
    """Main character creation system"""
    
    def __init__(self):
        self.backgrounds = self._create_backgrounds()
        self.personality_traits = list(PersonalityTrait)
        self.trauma_types = list(TraumaType)
        self.skill_categories = list(SkillCategory)
    
    def _create_backgrounds(self) -> Dict[BackgroundType, Background]:
        """Create all available backgrounds"""
        backgrounds = {}
        
        # Academic Background
        backgrounds[BackgroundType.ACADEMIC] = Background(
            type=BackgroundType.ACADEMIC,
            name="Academic",
            description="Former researcher or professor",
            skill_bonuses={SkillCategory.INTELLIGENCE: 2, SkillCategory.SOCIAL: 1},
            trait_modifiers=[PersonalityTrait.ANALYTICAL, PersonalityTrait.IDEALISTIC],
            starting_resources={"money": 200, "influence": 15, "equipment": 50},
            connections=["former colleagues", "research contacts", "university staff"],
            trauma_risk=[TraumaType.BETRAYAL, TraumaType.ECONOMIC_HARDSHIP]
        )
        
        # Military Background
        backgrounds[BackgroundType.MILITARY] = Background(
            type=BackgroundType.MILITARY,
            name="Military",
            description="Former military personnel",
            skill_bonuses={SkillCategory.COMBAT: 2, SkillCategory.SURVIVAL: 1},
            trait_modifiers=[PersonalityTrait.METHODICAL, PersonalityTrait.LOYAL],
            starting_resources={"money": 150, "influence": 10, "equipment": 100},
            connections=["former comrades", "military contacts", "veterans"],
            trauma_risk=[TraumaType.COMBAT_TRAUMA, TraumaType.BETRAYAL]
        )
        
        # Criminal Background
        backgrounds[BackgroundType.CRIMINAL] = Background(
            type=BackgroundType.CRIMINAL,
            name="Criminal",
            description="Former street criminal or gang member",
            skill_bonuses={SkillCategory.STEALTH: 2, SkillCategory.SURVIVAL: 1},
            trait_modifiers=[PersonalityTrait.RECKLESS, PersonalityTrait.OPPORTUNISTIC],
            starting_resources={"money": 100, "influence": 5, "equipment": 75},
            connections=["street contacts", "criminal network", "former gang members"],
            trauma_risk=[TraumaType.IMPRISONMENT, TraumaType.WITNESSING_VIOLENCE]
        )
        
        # Corporate Background
        backgrounds[BackgroundType.CORPORATE] = Background(
            type=BackgroundType.CORPORATE,
            name="Corporate",
            description="Former corporate executive or employee",
            skill_bonuses={SkillCategory.SOCIAL: 2, SkillCategory.INTELLIGENCE: 1},
            trait_modifiers=[PersonalityTrait.PRAGMATIC, PersonalityTrait.ANALYTICAL],
            starting_resources={"money": 300, "influence": 20, "equipment": 25},
            connections=["corporate contacts", "business associates", "former colleagues"],
            trauma_risk=[TraumaType.BETRAYAL, TraumaType.ECONOMIC_HARDSHIP]
        )
        
        # Medical Background
        backgrounds[BackgroundType.MEDICAL] = Background(
            type=BackgroundType.MEDICAL,
            name="Medical",
            description="Former doctor, nurse, or medical professional",
            skill_bonuses={SkillCategory.MEDICAL: 2, SkillCategory.TECHNICAL: 1},
            trait_modifiers=[PersonalityTrait.COMPASSIONATE, PersonalityTrait.METHODICAL],
            starting_resources={"money": 250, "influence": 15, "equipment": 100},
            connections=["medical contacts", "hospital staff", "pharmaceutical contacts"],
            trauma_risk=[TraumaType.WITNESSING_VIOLENCE, TraumaType.BETRAYAL]
        )
        
        # Technical Background
        backgrounds[BackgroundType.TECHNICAL] = Background(
            type=BackgroundType.TECHNICAL,
            name="Technical",
            description="Former IT professional or engineer",
            skill_bonuses={SkillCategory.HACKING: 2, SkillCategory.TECHNICAL: 1},
            trait_modifiers=[PersonalityTrait.ANALYTICAL, PersonalityTrait.CREATIVE],
            starting_resources={"money": 200, "influence": 10, "equipment": 150},
            connections=["tech contacts", "hacker community", "former colleagues"],
            trauma_risk=[TraumaType.BETRAYAL, TraumaType.ECONOMIC_HARDSHIP]
        )
        
        # Journalist Background
        backgrounds[BackgroundType.JOURNALIST] = Background(
            type=BackgroundType.JOURNALIST,
            name="Journalist",
            description="Former reporter or media professional",
            skill_bonuses={SkillCategory.SOCIAL: 2, SkillCategory.INTELLIGENCE: 1},
            trait_modifiers=[PersonalityTrait.IDEALISTIC, PersonalityTrait.INTUITIVE],
            starting_resources={"money": 150, "influence": 25, "equipment": 50},
            connections=["media contacts", "sources", "fellow journalists"],
            trauma_risk=[TraumaType.WITNESSING_VIOLENCE, TraumaType.IMPRISONMENT]
        )
        
        # Religious Background
        backgrounds[BackgroundType.RELIGIOUS] = Background(
            type=BackgroundType.RELIGIOUS,
            name="Religious",
            description="Former religious leader or devout follower",
            skill_bonuses={SkillCategory.SOCIAL: 2, SkillCategory.INTELLIGENCE: 1},
            trait_modifiers=[PersonalityTrait.IDEALISTIC, PersonalityTrait.COMPASSIONATE],
            starting_resources={"money": 100, "influence": 20, "equipment": 25},
            connections=["religious community", "faith leaders", "charitable organizations"],
            trauma_risk=[TraumaType.DISCRIMINATION, TraumaType.BETRAYAL]
        )
        
        # Activist Background
        backgrounds[BackgroundType.ACTIVIST] = Background(
            type=BackgroundType.ACTIVIST,
            name="Activist",
            description="Former political activist or organizer",
            skill_bonuses={SkillCategory.SOCIAL: 2, SkillCategory.INTELLIGENCE: 1},
            trait_modifiers=[PersonalityTrait.IDEALISTIC, PersonalityTrait.LEADER],
            starting_resources={"money": 75, "influence": 30, "equipment": 25},
            connections=["activist network", "community organizers", "political contacts"],
            trauma_risk=[TraumaType.IMPRISONMENT, TraumaType.DISCRIMINATION]
        )
        
        # Laborer Background
        backgrounds[BackgroundType.LABORER] = Background(
            type=BackgroundType.LABORER,
            name="Laborer",
            description="Former factory worker or manual laborer",
            skill_bonuses={SkillCategory.SURVIVAL: 2, SkillCategory.TECHNICAL: 1},
            trait_modifiers=[PersonalityTrait.PRAGMATIC, PersonalityTrait.LOYAL],
            starting_resources={"money": 50, "influence": 5, "equipment": 25},
            connections=["union contacts", "fellow workers", "community members"],
            trauma_risk=[TraumaType.ECONOMIC_HARDSHIP, TraumaType.FAMILY_SEPARATION]
        )
        
        return backgrounds
    
    def create_character(self, name: str, background_type: BackgroundType, 
                        primary_trait: PersonalityTrait, secondary_trait: PersonalityTrait,
                        skill_points: int = 20, has_trauma: bool = True) -> 'Character':
        """Create a new character with the specified parameters"""
        
        # Get background
        background = self.backgrounds[background_type]
        
        # Create skills
        skills = CharacterSkills()
        skills.apply_background_bonuses(background)
        
        # Create traits
        traits = CharacterTraits(
            primary_trait=primary_trait,
            secondary_trait=secondary_trait,
            background_traits=background.trait_modifiers.copy()
        )
        
        # Create trauma (if applicable)
        trauma = None
        if has_trauma and random.random() < 0.7:  # 70% chance of trauma
            trauma_type = random.choice(background.trauma_risk)
            trauma = CharacterTrauma(
                type=trauma_type,
                severity=random.uniform(0.3, 0.8),
                description=trauma_type.value.replace('_', ' ').title(),
                emotional_impact={
                    'trust': random.uniform(-0.5, -0.1),
                    'anticipation': random.uniform(-0.3, 0.1),
                    'anger': random.uniform(0.1, 0.5)
                },
                triggers=[f"reminders of {trauma_type.value.replace('_', ' ')}"]
            )
        
        # Create motivation
        motivation = self._generate_motivation(background, traits)
        
        # Create emotional state
        emotional_state = self._create_emotional_state(traits, trauma)
        
        # Create character
        character = Character(
            id=str(uuid.uuid4()),
            name=name,
            background=background,
            skills=skills,
            traits=traits,
            trauma=trauma,
            motivation=motivation,
            emotional_state=emotional_state
        )
        
        return character
    
    def _generate_motivation(self, background: Background, traits: CharacterTraits) -> CharacterMotivation:
        """Generate character motivation based on background and traits"""
        
        # Primary motivations based on background
        background_motivations = {
            BackgroundType.ACADEMIC: ["seeking truth", "intellectual freedom", "social justice"],
            BackgroundType.MILITARY: ["protecting others", "fighting injustice", "honor and duty"],
            BackgroundType.CRIMINAL: ["survival", "revenge", "redemption"],
            BackgroundType.CORPORATE: ["exposing corruption", "economic justice", "personal redemption"],
            BackgroundType.MEDICAL: ["healing society", "preventing suffering", "medical ethics"],
            BackgroundType.TECHNICAL: ["technological freedom", "information access", "systemic change"],
            BackgroundType.JOURNALIST: ["truth and justice", "freedom of press", "exposing corruption"],
            BackgroundType.RELIGIOUS: ["spiritual justice", "moral duty", "divine purpose"],
            BackgroundType.ACTIVIST: ["social change", "political reform", "community empowerment"],
            BackgroundType.LABORER: ["workers' rights", "economic justice", "dignity and respect"]
        }
        
        # Secondary motivations based on traits
        trait_motivations = {
            PersonalityTrait.IDEALISTIC: ["creating a better world", "moral principles", "universal justice"],
            PersonalityTrait.PRAGMATIC: ["practical solutions", "measurable results", "systemic efficiency"],
            PersonalityTrait.COMPASSIONATE: ["helping others", "reducing suffering", "community welfare"],
            PersonalityTrait.RUTHLESS: ["eliminating threats", "achieving goals", "necessary sacrifices"],
            PersonalityTrait.ANALYTICAL: ["understanding systems", "logical solutions", "data-driven change"],
            PersonalityTrait.INTUITIVE: ["following instincts", "creative solutions", "gut feelings"],
            PersonalityTrait.LOYAL: ["protecting comrades", "maintaining trust", "group solidarity"],
            PersonalityTrait.OPPORTUNISTIC: ["adapting to change", "seizing opportunities", "flexible strategies"],
            PersonalityTrait.LEADER: ["guiding others", "building movements", "inspiring change"],
            PersonalityTrait.FOLLOWER: ["supporting leaders", "team contribution", "loyal service"]
        }
        
        primary_motivation = random.choice(background_motivations.get(background.type, ["change"]))
        secondary_motivation = random.choice(trait_motivations.get(traits.primary_trait, ["survival"]))
        
        # Personal goal
        personal_goals = [
            "finding a safe haven for their family",
            "proving their worth to the cause",
            "seeking redemption for past actions",
            "building a better future for their children",
            "honoring the memory of lost loved ones",
            "achieving personal freedom and autonomy",
            "protecting their community from harm",
            "exposing the truth about the system"
        ]
        
        personal_goal = random.choice(personal_goals)
        
        # Ideological commitment and willingness to sacrifice
        ideological_commitment = random.uniform(0.6, 0.95)
        willingness_to_sacrifice = random.uniform(0.4, 0.9)
        
        # Adjust based on traits
        if PersonalityTrait.IDEALISTIC in traits.get_all_traits():
            ideological_commitment += 0.1
        if PersonalityTrait.RUTHLESS in traits.get_all_traits():
            willingness_to_sacrifice += 0.1
        if PersonalityTrait.CAUTIOUS in traits.get_all_traits():
            willingness_to_sacrifice -= 0.1
        
        return CharacterMotivation(
            primary_motivation=primary_motivation,
            secondary_motivation=secondary_motivation,
            personal_goal=personal_goal,
            ideological_commitment=min(1.0, ideological_commitment),
            willingness_to_sacrifice=min(1.0, willingness_to_sacrifice)
        )
    
    def _create_emotional_state(self, traits: CharacterTraits, trauma: Optional[CharacterTrauma]) -> EmotionalState:
        """Create emotional state based on traits and trauma"""
        
        # Start with base emotional state
        emotional_state = create_random_emotional_state()
        
        # Modify based on personality traits
        for trait in traits.get_all_traits():
            if trait == PersonalityTrait.OPTIMISTIC:
                emotional_state.anticipation += 0.2
                emotional_state.joy += 0.1
            elif trait == PersonalityTrait.PESSIMISTIC:
                emotional_state.anticipation -= 0.2
                emotional_state.joy -= 0.1
            elif trait == PersonalityTrait.COMPASSIONATE:
                emotional_state.trust += 0.1
                emotional_state.joy += 0.1
            elif trait == PersonalityTrait.RUTHLESS:
                emotional_state.trust -= 0.1
                emotional_state.anger += 0.1
            elif trait == PersonalityTrait.LOYAL:
                emotional_state.trust += 0.2
            elif trait == PersonalityTrait.OPPORTUNISTIC:
                emotional_state.trust -= 0.1
                emotional_state.fear += 0.1
        
        # Apply trauma effects if present
        if trauma:
            for emotion, modifier in trauma.emotional_impact.items():
                if hasattr(emotional_state, emotion):
                    current_value = getattr(emotional_state, emotion)
                    setattr(emotional_state, emotion, current_value + modifier)
        
        # Ensure values are clamped to valid ranges
        emotional_state._clamp_values()
        
        return emotional_state


@dataclass
class Character:
    """Complete character with all creation elements"""
    id: str
    name: str
    background: Background
    skills: CharacterSkills
    traits: CharacterTraits
    trauma: Optional[CharacterTrauma]
    motivation: CharacterMotivation
    emotional_state: EmotionalState
    
    def get_character_summary(self) -> str:
        """Get a comprehensive character summary"""
        summary = f"""
CHARACTER PROFILE: {self.name.upper()}
{'=' * 50}

BACKGROUND: {self.background.name}
{self.background.get_background_story(self.name)}

PERSONALITY: {self.traits.get_trait_description()}
Primary Trait: {self.traits.primary_trait.value.replace('_', ' ').title()}
Secondary Trait: {self.traits.secondary_trait.value.replace('_', ' ').title()}

MOTIVATION: {self.motivation.get_motivation_description()}
Ideological Commitment: {self.motivation.ideological_commitment:.1%}
Willingness to Sacrifice: {self.motivation.willingness_to_sacrifice:.1%}

SKILLS:
  Combat: {self.skills.combat}/10
  Stealth: {self.skills.stealth}/10
  Hacking: {self.skills.hacking}/10
  Social: {self.skills.social}/10
  Technical: {self.skills.technical}/10
  Medical: {self.skills.medical}/10
  Survival: {self.skills.survival}/10
  Intelligence: {self.skills.intelligence}/10

STARTING RESOURCES:
  Money: ${self.background.starting_resources['money']}
  Influence: {self.background.starting_resources['influence']} points
  Equipment: {self.background.starting_resources['equipment']} points

CONNECTIONS: {', '.join(self.background.connections)}
"""
        
        if self.trauma:
            summary += f"""
TRAUMA: {self.trauma.get_trauma_story(self.name)}
Severity: {self.trauma.severity:.1%}
Triggers: {', '.join(self.trauma.triggers)}
"""
        
        summary += f"""
EMOTIONAL STATE:
  Trust: {self.emotional_state.trust:.2f}
  Anticipation: {self.emotional_state.anticipation:.2f}
  Joy: {self.emotional_state.joy:.2f}
  Anger: {self.emotional_state.anger:.2f}
  Fear: {self.emotional_state.fear:.2f}
  Sadness: {self.emotional_state.sadness:.2f}
  Surprise: {self.emotional_state.surprise:.2f}
  Disgust: {self.emotional_state.disgust:.2f}
  Trauma Level: {self.emotional_state.trauma_level:.2f}
"""
        
        return summary
    
    def get_character_story(self) -> str:
        """Get a narrative character story"""
        story = f"{self.name} is a {self.background.name.lower()} who joined the resistance. "
        story += f"They are {self.traits.get_trait_description()}. "
        story += f"{self.motivation.get_motivation_description()}"
        
        if self.trauma:
            story += f" {self.trauma.get_trauma_story(self.name)}"
        
        story += f" Their background as a {self.background.name.lower()} has given them unique skills and perspectives that they bring to the struggle."
        
        return story
    
    def serialize(self) -> Dict[str, Any]:
        """Serialize character to dictionary"""
        data = {
            'id': self.id,
            'name': self.name,
            'background': {
                'type': self.background.type.value,
                'name': self.background.name,
                'description': self.background.description,
                'skill_bonuses': {k.value: v for k, v in self.background.skill_bonuses.items()},
                'trait_modifiers': [t.value for t in self.background.trait_modifiers],
                'starting_resources': self.background.starting_resources,
                'connections': self.background.connections,
                'trauma_risk': [t.value for t in self.background.trauma_risk]
            },
            'skills': {
                'combat': self.skills.combat,
                'stealth': self.skills.stealth,
                'hacking': self.skills.hacking,
                'social': self.skills.social,
                'technical': self.skills.technical,
                'medical': self.skills.medical,
                'survival': self.skills.survival,
                'intelligence': self.skills.intelligence
            },
            'traits': {
                'primary_trait': self.traits.primary_trait.value,
                'secondary_trait': self.traits.secondary_trait.value,
                'background_traits': [t.value for t in self.traits.background_traits]
            },
            'motivation': {
                'primary_motivation': self.motivation.primary_motivation,
                'secondary_motivation': self.motivation.secondary_motivation,
                'personal_goal': self.motivation.personal_goal,
                'ideological_commitment': self.motivation.ideological_commitment,
                'willingness_to_sacrifice': self.motivation.willingness_to_sacrifice
            },
            'emotional_state': self.emotional_state.serialize()
        }
        
        if self.trauma:
            data['trauma'] = {
                'type': self.trauma.type.value,
                'severity': self.trauma.severity,
                'description': self.trauma.description,
                'emotional_impact': self.trauma.emotional_impact,
                'triggers': self.trauma.triggers
            }
        
        return data
    
    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> 'Character':
        """Deserialize character from dictionary"""
        # Reconstruct background
        background_data = data['background']
        background = Background(
            type=BackgroundType(background_data['type']),
            name=background_data['name'],
            description=background_data['description'],
            skill_bonuses={SkillCategory(k): v for k, v in background_data['skill_bonuses'].items()},
            trait_modifiers=[PersonalityTrait(t) for t in background_data['trait_modifiers']],
            starting_resources=background_data['starting_resources'],
            connections=background_data['connections'],
            trauma_risk=[TraumaType(t) for t in background_data['trauma_risk']]
        )
        
        # Reconstruct skills
        skills_data = data['skills']
        skills = CharacterSkills(
            combat=skills_data['combat'],
            stealth=skills_data['stealth'],
            hacking=skills_data['hacking'],
            social=skills_data['social'],
            technical=skills_data['technical'],
            medical=skills_data['medical'],
            survival=skills_data['survival'],
            intelligence=skills_data['intelligence']
        )
        
        # Reconstruct traits
        traits_data = data['traits']
        traits = CharacterTraits(
            primary_trait=PersonalityTrait(traits_data['primary_trait']),
            secondary_trait=PersonalityTrait(traits_data['secondary_trait']),
            background_traits=[PersonalityTrait(t) for t in traits_data['background_traits']]
        )
        
        # Reconstruct trauma
        trauma = None
        if 'trauma' in data:
            trauma_data = data['trauma']
            trauma = CharacterTrauma(
                type=TraumaType(trauma_data['type']),
                severity=trauma_data['severity'],
                description=trauma_data['description'],
                emotional_impact=trauma_data['emotional_impact'],
                triggers=trauma_data['triggers']
            )
        
        # Reconstruct motivation
        motivation_data = data['motivation']
        motivation = CharacterMotivation(
            primary_motivation=motivation_data['primary_motivation'],
            secondary_motivation=motivation_data['secondary_motivation'],
            personal_goal=motivation_data['personal_goal'],
            ideological_commitment=motivation_data['ideological_commitment'],
            willingness_to_sacrifice=motivation_data['willingness_to_sacrifice']
        )
        
        # Reconstruct emotional state
        emotional_state = EmotionalState.deserialize(data['emotional_state'])
        
        return cls(
            id=data['id'],
            name=data['name'],
            background=background,
            skills=skills,
            traits=traits,
            trauma=trauma,
            motivation=motivation,
            emotional_state=emotional_state
        )


def create_random_character(name: str = None) -> Character:
    """Create a random character with a given name or generate one"""
    if name is None:
        names = [
            "Alex", "Jordan", "Casey", "Riley", "Morgan", "Avery", "Quinn", "Blake",
            "Cameron", "Drew", "Emery", "Finley", "Harper", "Hayden", "Jamie", "Kendall",
            "Logan", "Parker", "Reese", "Sage", "Taylor", "Zion", "Adrian", "Ash",
            "Bay", "Brook", "Dakota", "Dallas", "Drew", "Eden", "Ellis", "Fallon"
        ]
        name = random.choice(names)
    
    creator = CharacterCreator()
    
    # Randomly select background and traits
    background_type = random.choice(list(BackgroundType))
    primary_trait = random.choice(list(PersonalityTrait))
    secondary_trait = random.choice([t for t in PersonalityTrait if t != primary_trait])
    
    return creator.create_character(name, background_type, primary_trait, secondary_trait)


if __name__ == "__main__":
    # Test character creation
    print("Testing Character Creation System")
    print("=" * 50)
    
    # Create a random character
    character = create_random_character("Test Character")
    print(character.get_character_summary())
    
    # Test serialization
    print("\nTesting Serialization:")
    serialized = character.serialize()
    deserialized = Character.deserialize(serialized)
    print(f"Serialization successful: {deserialized.name == character.name}") 