#!/usr/bin/env python3
"""
Update script to integrate the new mission system with core.py
"""

import re

def update_core_file():
    """Update core.py to use the new mission system"""
    
    # Read the current core.py
    with open('src/game/core.py', 'r') as f:
        content = f.read()
    
    # Add imports at the beginning (after the module docstring and standard imports)
    import_insert = """

# Import enhanced mission system components
from .mission_system import Mission as EnhancedMission, MissionType as EnhancedMissionType, MissionComplexity
from .mission_executor import MissionExecutor
from .legal_system import LegalSystem
"""
    
    # Find where to insert (after the standard imports)
    import_pattern = r'(import random\n)'
    content = re.sub(import_pattern, r'\1' + import_insert + '\n', content)
    
    # Remove the old MissionType enum
    mission_type_pattern = r'class MissionType\(Enum\):\s*"""Mission types"""[\s\S]*?(?=\n\n)'
    content = re.sub(mission_type_pattern, '# MissionType moved to mission_system.py', content)
    
    # Remove the old Mission dataclass
    mission_dataclass_pattern = r'@dataclass\s*\nclass Mission:\s*"""Active mission"""[\s\S]*?(?=\n\n)'
    content = re.sub(mission_dataclass_pattern, '# Mission class moved to mission_system.py', content)
    
    # Add new SkillTypes if not present
    if 'TECHNICAL = "technical"' not in content:
        skill_pattern = r'(DEMOLITIONS = "demolitions")'
        skill_addition = '''DEMOLITIONS = "demolitions"
    TECHNICAL = "technical"  # Added for equipment repair
    MEDICAL = "medical"      # Added for medical treatment
    SURVIVAL = "survival"    # Added for environmental events'''
        content = re.sub(skill_pattern, skill_addition, content)
    
    # Update GameState __init__ to include subsystems
    init_pattern = r'(self\.active_events: List\[str\] = \[\])'
    init_addition = '''self.active_events: List[str] = []
        self.mission_counter = 0
        
        # Initialize subsystems
        self.mission_executor = None  # Will be initialized after GameState
        self.legal_system = None     # Will be initialized after GameState'''
    content = re.sub(init_pattern, init_addition, content)
    
    # Add initialize_subsystems method after __init__
    if 'def initialize_subsystems' not in content:
        init_method_pattern = r'(def initialize_game\(self\):)'
        subsystems_method = '''
    def initialize_subsystems(self):
        """Initialize subsystems that depend on GameState"""
        from .mission_executor import MissionExecutor
        from .legal_system import LegalSystem
        
        self.mission_executor = MissionExecutor(self)
        self.legal_system = LegalSystem()
    
    def initialize_game(self):'''
        content = re.sub(init_method_pattern, subsystems_method, content)
    
    # Update initialize_game to call initialize_subsystems
    if 'self.initialize_subsystems()' not in content:
        init_game_pattern = r'(self\._add_initial_narrative\(\))'
        content = re.sub(init_game_pattern, r'\1\n        self.initialize_subsystems()', content)
    
    # Add create_mission method if not present
    if 'def create_mission' not in content:
        create_mission_method = '''
    def create_mission(self, mission_type: 'EnhancedMissionType', target_location_id: str, 
                      faction_id: str, difficulty: int = 5, description: str = "") -> 'EnhancedMission':
        """Create a new multi-agent mission using the enhanced mission system"""
        
        self.mission_counter += 1
        mission_id = f"mission_{self.mission_counter}"
        
        # Create mission complexity based on location and difficulty
        location = self.locations[target_location_id]
        complexity = MissionComplexity(
            security_level=location.security_level,
            target_hardening=difficulty / 10.0,
            time_pressure=0.5,
            resource_requirements={'money': 100, 'equipment': 5},
            required_skills={SkillType.STEALTH: 3, SkillType.COMBAT: 2},
            political_sensitivity=0.7,
            minimum_agents=2,
            maximum_agents=4
        )
        
        mission = EnhancedMission(
            id=mission_id,
            mission_type=mission_type,
            faction_id=faction_id,
            target_location_id=target_location_id,
            complexity=complexity,
            created_turn=self.turn_number
        )
        
        self.active_missions[mission_id] = mission
        return mission
    
    def execute_mission(self, mission_id: str) -> Optional[Dict[str, Any]]:
        """Execute a mission using the mission executor"""
        if mission_id not in self.active_missions:
            return None
        
        mission = self.active_missions[mission_id]
        
        # Plan the mission first
        agents = [self.agents[aid] for aid in mission.participants if aid in self.agents]
        self.mission_executor.plan_mission(mission, agents)
        
        # Execute the mission
        report = self.mission_executor.execute_mission(mission)
        
        # Remove from active missions if complete
        if mission.is_complete():
            del self.active_missions[mission_id]
        
        return report.__dict__
'''
        # Add before get_status_summary
        pattern = r'(def get_status_summary\(self\))'
        content = re.sub(pattern, create_mission_method + '\n    ' + r'\1', content)
    
    # Add imports to top of add_agent method
    if 'Optional[Dict[str, Any]]' not in content:
        typing_pattern = r'(from typing import Dict, List, Any)'
        content = re.sub(typing_pattern, r'from typing import Dict, List, Any, Optional', content)
    
    # Write the updated content back
    with open('src/game/core.py', 'w') as f:
        f.write(content)
    
    print("✅ Successfully updated core.py to integrate with the new mission system!")
    print("\nChanges made:")
    print("- Added imports for mission_system, mission_executor, and legal_system")
    print("- Removed old MissionType enum and Mission dataclass")
    print("- Added new skill types (TECHNICAL, MEDICAL, SURVIVAL)")
    print("- Added subsystem initialization")
    print("- Added create_mission and execute_mission methods")
    print("\nThe game is now ready to use the enhanced mission system!")


if __name__ == "__main__":
    try:
        update_core_file()
    except Exception as e:
        print(f"❌ Error updating core.py: {e}")
        import traceback
        traceback.print_exc() 