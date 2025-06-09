"""
Years of Lead - Game Setup

This module provides functions to initialize the game with default content.
"""

from .core import (
    GameState, Agent, Faction, Location, 
    SkillType, Skill, Equipment, EquipmentType
)


def create_default_game() -> GameState:
    """Create a game with default factions, locations, and agents"""
    gs = GameState()
    
    # Create default locations
    locations = [
        Location(
            id="university",
            name="University District",
            security_level=3,
            unrest_level=7
        ),
        Location(
            id="downtown",
            name="Downtown",
            security_level=6,
            unrest_level=4
        ),
        Location(
            id="industrial",
            name="Industrial Zone",
            security_level=4,
            unrest_level=6
        ),
        Location(
            id="suburbs",
            name="Suburban Area",
            security_level=2,
            unrest_level=3
        ),
        Location(
            id="government",
            name="Government Quarter",
            security_level=9,
            unrest_level=2
        )
    ]
    
    for location in locations:
        gs.add_location(location)
    
    # Create default factions
    factions = [
        Faction(
            id="resistance",
            name="The Resistance",
            resources={"money": 150, "influence": 60, "personnel": 12}
        ),
        Faction(
            id="students",
            name="Student Movement",
            resources={"money": 80, "influence": 70, "personnel": 15}
        ),
        Faction(
            id="workers",
            name="Workers Union",
            resources={"money": 120, "influence": 55, "personnel": 10}
        )
    ]
    
    for faction in factions:
        gs.add_faction(faction)
    
    # Create default agents
    agents = [
        # Resistance agents
        Agent(
            id="maria",
            name="Maria Santos",
            faction_id="resistance",
            location_id="university",
            background="student"
        ),
        Agent(
            id="carlos",
            name="Carlos Rivera",
            faction_id="resistance", 
            location_id="downtown",
            background="military"
        ),
        Agent(
            id="elena",
            name="Elena Vasquez",
            faction_id="resistance",
            location_id="industrial",
            background="civilian"
        ),
        
        # Student movement agents
        Agent(
            id="david",
            name="David Chen",
            faction_id="students",
            location_id="university",
            background="student"
        ),
        Agent(
            id="sofia",
            name="Sofia Martinez",
            faction_id="students",
            location_id="university",
            background="student"
        ),
        
        # Workers union agents
        Agent(
            id="miguel",
            name="Miguel Torres",
            faction_id="workers",
            location_id="industrial",
            background="civilian"
        ),
        Agent(
            id="ana",
            name="Ana Rodriguez",
            faction_id="workers",
            location_id="suburbs",
            background="civilian"
        )
    ]
    
    # Set up agent skills based on background
    for agent in agents:
        if agent.background == "military":
            agent.skills[SkillType.COMBAT] = Skill(SkillType.COMBAT, level=6)
            agent.skills[SkillType.STEALTH] = Skill(SkillType.STEALTH, level=5)
            agent.skills[SkillType.SURVIVAL] = Skill(SkillType.SURVIVAL, level=5)
        elif agent.background == "student":
            agent.skills[SkillType.PERSUASION] = Skill(SkillType.PERSUASION, level=5)
            agent.skills[SkillType.TECHNICAL] = Skill(SkillType.TECHNICAL, level=4)
            agent.skills[SkillType.STEALTH] = Skill(SkillType.STEALTH, level=3)
        else:  # civilian
            agent.skills[SkillType.PERSUASION] = Skill(SkillType.PERSUASION, level=4)
            agent.skills[SkillType.SURVIVAL] = Skill(SkillType.SURVIVAL, level=4)
            agent.skills[SkillType.STEALTH] = Skill(SkillType.STEALTH, level=3)
        
        gs.add_agent(agent)
    
    # Create some basic equipment
    equipment_templates = [
        Equipment(
            id="radio",
            name="Two-way Radio",
            equipment_type=EquipmentType.ELECTRONIC,
            quality=6,
            skill_bonus={SkillType.LEADERSHIP: 1},
            description="Encrypted communication device"
        ),
        Equipment(
            id="medkit",
            name="First Aid Kit",
            equipment_type=EquipmentType.MEDICAL,
            quality=5,
            skill_bonus={SkillType.MEDICAL: 2},
            description="Basic medical supplies"
        ),
        Equipment(
            id="toolkit",
            name="Technical Toolkit",
            equipment_type=EquipmentType.TOOL,
            quality=5,
            skill_bonus={SkillType.TECHNICAL: 2},
            description="Electronics and mechanical tools"
        )
    ]
    
    # Give some agents equipment
    if "carlos" in gs.agents:
        gs.agents["carlos"].add_equipment(equipment_templates[0])  # Radio
    if "elena" in gs.agents:
        gs.agents["elena"].add_equipment(equipment_templates[1])  # Medkit
    if "david" in gs.agents:
        gs.agents["david"].add_equipment(equipment_templates[2])  # Toolkit
    
    return gs


def create_sandbox_game() -> GameState:
    """Create a minimal sandbox game for testing"""
    gs = GameState()
    
    # Single location
    gs.add_location(Location(
        id="test_city",
        name="Test City",
        security_level=5,
        unrest_level=5
    ))
    
    # Single faction
    gs.add_faction(Faction(
        id="test_faction",
        name="Test Faction",
        resources={"money": 100, "influence": 50, "personnel": 5}
    ))
    
    # Single agent
    gs.add_agent(Agent(
        id="test_agent",
        name="Test Agent",
        faction_id="test_faction",
        location_id="test_city"
    ))
    
    return gs 