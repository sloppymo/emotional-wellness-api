#!/usr/bin/env python3
"""
Years of Lead - CLI Interface for Core Game Loop MVP
A turn-based insurgency simulator with symbolic narrative logging
"""

import sys
import os
from typing import Dict, List

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from game.core import (
    GameState, Agent, Faction, Location, Task, TaskType, 
    MissionType, AgentRole, Phase, SkillType, EquipmentType, 
    Skill, Equipment, PublicOpinion
)
from loguru import logger

def main():
    # Try to use the new blessed UI if available
    use_blessed = '--no-ui' not in sys.argv
    try:
        if use_blessed:
            from ui.blessed_ui import BlessedUI
            gs = GameState()
            # Optionally: setup_sample_game() here if needed
            BlessedUI(gs).run()
            return
    except ImportError as e:
        print("Blessed UI not available, falling back to text CLI.")
        logger.warning(f"Blessed UI not available: {e}")

    # Fallback: run the old CLI
    class GameCLI:
        """CLI interface for the Years of Lead game"""
        
        def __init__(self):
            self.game_state = GameState()
            self.setup_sample_game()
        
        def setup_sample_game(self):
            """Set up a sample game with locations, factions, and agents"""
            
            # Set up sample equipment database
            self._setup_sample_equipment()
            
            # Create locations
            locations = [
                Location("university", "University District", security_level=3, unrest_level=7),
                Location("downtown", "Downtown", security_level=8, unrest_level=4),
                Location("industrial", "Industrial Zone", security_level=5, unrest_level=6),
                Location("suburbs", "Suburbs", security_level=6, unrest_level=3),
                Location("government", "Government Quarter", security_level=10, unrest_level=2)
            ]
            
            for location in locations:
                self.game_state.add_location(location)
            
            # Create factions
            factions = [
                Faction("resistance", "The Resistance", {"money": 150, "influence": 30, "personnel": 8}),
                Faction("students", "Student Movement", {"money": 50, "influence": 70, "personnel": 15}),
                Faction("workers", "Workers Union", {"money": 200, "influence": 40, "personnel": 12})
            ]
            
            for faction in factions:
                self.game_state.add_faction(faction)
            
            # Create agents with backgrounds and skills
            agents = [
                Agent("maria", "Maria Gonzalez", "resistance", "university", 
                      background="student", skills={SkillType.PERSUASION: Skill(SkillType.PERSUASION, level=7),
                                                   SkillType.STEALTH: Skill(SkillType.STEALTH, level=5)}),
                Agent("carlos", "Carlos Mendez", "resistance", "downtown", 
                      background="military", skills={SkillType.COMBAT: Skill(SkillType.COMBAT, level=6),
                                                    SkillType.LEADERSHIP: Skill(SkillType.LEADERSHIP, level=4)}),
                Agent("ana", "Ana Torres", "students", "university", 
                      background="student", skills={SkillType.PERSUASION: Skill(SkillType.PERSUASION, level=5),
                                                   SkillType.TECHNICAL: Skill(SkillType.TECHNICAL, level=3)}),
                Agent("jorge", "Jorge Silva", "students", "industrial", 
                      background="civilian", skills={SkillType.SURVIVAL: Skill(SkillType.SURVIVAL, level=4),
                                                    SkillType.STEALTH: Skill(SkillType.STEALTH, level=3)}),
                Agent("elena", "Elena Rodriguez", "workers", "industrial", 
                      background="worker", skills={SkillType.TECHNICAL: Skill(SkillType.TECHNICAL, level=6),
                                                  SkillType.COMBAT: Skill(SkillType.COMBAT, level=4)}),
                Agent("pedro", "Pedro Vargas", "workers", "suburbs", 
                      background="civilian", skills={SkillType.SURVIVAL: Skill(SkillType.SURVIVAL, level=5),
                                                    SkillType.MEDICAL: Skill(SkillType.MEDICAL, level=2)})
            ]
            
            # Assign equipment to agents
            self._assign_sample_equipment(agents)
            
            # Set some agents as captured/injured
            agents[2].status = "captured"  # Ana Torres
            agents[3].status = "captured"  # Jorge Silva
            agents[4].status = "injured"   # Elena Rodriguez
            agents[5].status = "captured"  # Pedro Vargas
            
            for agent in agents:
                self.game_state.add_agent(agent)
            
            # Add some initial tasks
            self._add_sample_tasks()
            
            logger.info("Sample game initialized with 6 agents across 3 factions")
        
        def _setup_sample_equipment(self):
            """Set up sample equipment database"""
            equipment_templates = [
                Equipment(id="pistol", name="Handgun", equipment_type=EquipmentType.WEAPON,
                         quality=6, skill_bonus={SkillType.COMBAT: 2}, cost=50),
                Equipment(id="rifle", name="Assault Rifle", equipment_type=EquipmentType.WEAPON,
                         quality=8, skill_bonus={SkillType.COMBAT: 3}, cost=100),
                Equipment(id="vest", name="Bulletproof Vest", equipment_type=EquipmentType.ARMOR,
                         quality=7, skill_bonus={SkillType.SURVIVAL: 1}, cost=75),
                Equipment(id="laptop", name="Laptop", equipment_type=EquipmentType.ELECTRONIC,
                         quality=5, skill_bonus={SkillType.TECHNICAL: 2}, cost=30),
                Equipment(id="medkit", name="Medical Kit", equipment_type=EquipmentType.MEDICAL,
                         quality=6, skill_bonus={SkillType.MEDICAL: 2}, cost=25),
                Equipment(id="binoculars", name="Binoculars", equipment_type=EquipmentType.TOOL,
                         quality=4, skill_bonus={SkillType.STEALTH: 1}, cost=15),
                Equipment(id="car", name="Sedan", equipment_type=EquipmentType.VEHICLE,
                         quality=5, skill_bonus={SkillType.DRIVING: 1}, cost=200),
                Equipment(id="radio", name="Radio", equipment_type=EquipmentType.ELECTRONIC,
                         quality=3, skill_bonus={SkillType.TECHNICAL: 1}, cost=10)
            ]
            
            for equipment in equipment_templates:
                self.game_state.equipment_database[equipment.id] = equipment
        
        def _assign_sample_equipment(self, agents: List[Agent]):
            """Assign sample equipment to agents"""
            # Maria - Student with persuasion skills
            agents[0].add_equipment(Equipment(
                id="maria_laptop", name="Maria's Laptop", equipment_type=EquipmentType.ELECTRONIC,
                quality=5, skill_bonus={SkillType.TECHNICAL: 2}, cost=30
            ))
            
            # Carlos - Military background
            agents[1].add_equipment(Equipment(
                id="carlos_rifle", name="Carlos's Rifle", equipment_type=EquipmentType.WEAPON,
                quality=8, skill_bonus={SkillType.COMBAT: 3}, cost=100
            ))
            agents[1].add_equipment(Equipment(
                id="carlos_vest", name="Carlos's Vest", equipment_type=EquipmentType.ARMOR,
                quality=7, skill_bonus={SkillType.SURVIVAL: 1}, cost=75
            ))
            
            # Ana - Student with technical skills
            agents[2].add_equipment(Equipment(
                id="ana_laptop", name="Ana's Laptop", equipment_type=EquipmentType.ELECTRONIC,
                quality=5, skill_bonus={SkillType.TECHNICAL: 2}, cost=30
            ))
            
            # Elena - Worker with technical skills
            agents[4].add_equipment(Equipment(
                id="elena_medkit", name="Elena's Medkit", equipment_type=EquipmentType.MEDICAL,
                quality=6, skill_bonus={SkillType.MEDICAL: 2}, cost=25
            ))
            
            # Pedro - Civilian with survival skills
            agents[5].add_equipment(Equipment(
                id="pedro_binoculars", name="Pedro's Binoculars", equipment_type=EquipmentType.TOOL,
                quality=4, skill_bonus={SkillType.STEALTH: 1}, cost=15
            ))
        
        def _add_sample_tasks(self):
            """Add sample tasks to agents"""
            # Maria (skilled operative) - sabotage mission
            maria = self.game_state.agents["maria"]
            maria.add_task(Task(TaskType.GATHER_INFO, difficulty=4, description="Scout government facility"))
            maria.add_task(Task(TaskType.MOVE, target_location_id="government", difficulty=6, description="Infiltrate government quarter"))
            maria.add_task(Task(TaskType.SABOTAGE, difficulty=8, description="Plant explosives in communications center"))
            
            # Carlos - recruitment drive
            carlos = self.game_state.agents["carlos"]
            carlos.add_task(Task(TaskType.PROPAGANDA, difficulty=5, description="Distribute leaflets in downtown"))
            carlos.add_task(Task(TaskType.RECRUIT, difficulty=6, description="Recruit sympathizers"))
            
            # Ana - student organization
            ana = self.game_state.agents["ana"]
            ana.add_task(Task(TaskType.PROPAGANDA, difficulty=3, description="Organize student protest"))
            ana.add_task(Task(TaskType.RECRUIT, difficulty=4, description="Rally student supporters"))
            
            # Jorge - intelligence gathering
            jorge = self.game_state.agents["jorge"]
            jorge.add_task(Task(TaskType.GATHER_INFO, difficulty=5, description="Monitor factory security"))
            jorge.add_task(Task(TaskType.MOVE, target_location_id="downtown", difficulty=4, description="Report to headquarters"))
            
            # Elena - labor organization
            elena = self.game_state.agents["elena"]
            elena.add_task(Task(TaskType.RECRUIT, difficulty=5, description="Organize factory workers"))
            elena.add_task(Task(TaskType.PROPAGANDA, difficulty=4, description="Spread strike plans"))
            
            # Pedro - support operations
            pedro = self.game_state.agents["pedro"]
            pedro.add_task(Task(TaskType.GATHER_INFO, difficulty=3, description="Monitor police patrols"))
            pedro.add_task(Task(TaskType.MOVE, target_location_id="industrial", difficulty=3, description="Coordinate with workers"))
        
        def display_header(self):
            """Display the game header"""
            print("\n" + "="*60)
            print("           YEARS OF LEAD - Insurgency Simulator")
            print("="*60)
        
        def display_current_status(self):
            """Display the current game status"""
            status = self.game_state.get_status_summary()
            
            print(f"\n📅 Day {status['turn']} - {status['phase'].title()} Phase")
            print(f"👥 Active Agents: {status['active_agents']}/{status['total_agents']}")
            
            print("\n" + "="*50)
            print("💰 FACTION RESOURCES")
            print("="*50)
            for faction_id, resources in status['factions'].items():
                faction_name = self.game_state.factions[faction_id].name
                money = resources['money']
                influence = resources['influence']
                personnel = resources['personnel']
                print(f"  {faction_name}: ${money} | Influence: {influence} | Personnel: {personnel}")
            
            # Display active events
            if status['active_events']:
                print("\n" + "="*50)
                print("🚨 ACTIVE EVENTS")
                print("="*50)
                for event in status['active_events']:
                    print(f"  ⚡ {event}")
        
        def display_agent_locations(self):
            """Display agents organized by location"""
            locations = self.game_state.get_agent_locations()
            status = self.game_state.get_status_summary()
            
            print("\n" + "="*50)
            print("🗺️  AGENT LOCATIONS")
            print("="*50)
            for location_id, agent_list in locations.items():
                location_name = self.game_state.locations[location_id].name
                security = self.game_state.locations[location_id].security_level
                unrest = self.game_state.locations[location_id].unrest_level
                print(f"\n📍 {location_name} (Security: {security}, Unrest: {unrest}):")
                
                # Show location events
                if location_id in status['location_events']:
                    for event in status['location_events'][location_id]:
                        print(f"    🚨 {event}")
                
                for agent_info in agent_list:
                    print(f"    • {agent_info}")
        
        def display_recent_narrative(self):
            """Display recent narrative events"""
            status = self.game_state.get_status_summary()
            recent_events = status['recent_narrative']
            
            print("\n" + "="*50)
            print("📖 RECENT EVENTS")
            print("="*50)
            if recent_events:
                for event in recent_events:
                    print(f"  📝 {event}")
            else:
                print("  No recent events to display")
        
        def display_menu(self):
            """Display the main menu with both numbers and keywords"""
            print("\n" + "-"*40)
            print("📍 Main Menu")
            print("-"*40)
            print("Commands:")
            print("  [1] advance      - Advance Turn/Phase")
            print("  [2] agents       - Show Agent Details")
            print("  [3] narrative    - Show Full Narrative Log")
            print("  [4] addtask      - Add Task to Agent")
            print("  [5] locations    - Show Location Details")
            print("  [6] events       - Show Active Events")
            print("  [7] missions     - Show Active Missions")
            print("  [8] createmission- Create New Mission")
            print("  [9] addtomission - Add Agent to Mission")
            print("  [10] execmission - Execute Mission")
            print("  [p] opinion      - Show Public Opinion")
            print("  [q] quit         - Quit Game")
            print("-"*40)
        
        def show_agent_details(self):
            """Show detailed information about all agents"""
            print("\n" + "-"*40)
            print("📍 Main Menu > Agent Details")
            print("-"*40)
            
            # Show condensed overview first
            print("👥 AGENT OVERVIEW:")
            print("-" * 60)
            print(f"{'Name':<15} {'Status':<10} {'Location':<15} {'Tasks':<8} {'Skills'}")
            print("-" * 60)
            
            for agent in self.game_state.agents.values():
                faction_name = self.game_state.factions[agent.faction_id].name
                location_name = self.game_state.locations[agent.location_id].name
                task_count = len(agent.task_queue)
                
                # Get top 2 skills above level 1
                top_skills = []
                for skill_type, skill in agent.skills.items():
                    if skill.level > 1:
                        top_skills.append(f"{skill_type.value}:{skill.level}")
                top_skills = top_skills[:2]  # Show only top 2
                skills_str = ", ".join(top_skills) if top_skills else "None"
                
                # Status indicator
                status_icon = "🟢" if agent.status == "active" else "🔴" if agent.status == "captured" else "🟡"
                
                print(f"{agent.name:<15} {status_icon}{agent.status:<9} {location_name:<15} {task_count:<8} {skills_str}")
            
            print("-" * 60)
            
            # Ask if user wants detailed view
            choice = input("\nEnter agent name for details (or press Enter to return): ").strip()
            if choice:
                # Find the agent
                selected_agent = None
                for agent in self.game_state.agents.values():
                    if agent.name.lower() == choice.lower():
                        selected_agent = agent
                        break
                
                if selected_agent:
                    self._show_agent_detail(selected_agent)
                else:
                    print("❌ Agent not found.")
        
        def _show_agent_detail(self, agent):
            """Show detailed information for a specific agent"""
            print(f"\n" + "="*50)
            print(f"🧑 DETAILED AGENT INFO: {agent.name}")
            print("="*50)
            
            faction_name = self.game_state.factions[agent.faction_id].name
            location_name = self.game_state.locations[agent.location_id].name
            
            print(f"Faction: {faction_name}")
            print(f"Location: {location_name}")
            print(f"Status: {agent.status}")
            print(f"Background: {agent.background}")
            print(f"Loyalty: {agent.loyalty}/100")
            print(f"Stress: {agent.stress}/100")
            print(f"Queued Tasks: {len(agent.task_queue)}")
            
            # Show all skills
            print("\nSkills:")
            for skill_type, skill in agent.skills.items():
                effective_level = agent.get_skill_level(skill_type)
                if skill.level > 1:
                    print(f"  • {skill_type.value}: {skill.level} (effective: {effective_level})")
                else:
                    print(f"  • {skill_type.value}: {skill.level} (effective: {effective_level}) - Basic")
            
            # Show equipment
            if agent.equipment:
                print("\nEquipment:")
                for equipment in agent.equipment:
                    condition_status = "🟢" if equipment.condition > 70 else "🟡" if equipment.condition > 30 else "🔴"
                    print(f"  {condition_status} {equipment.name} (condition: {equipment.condition}%)")
            
            # Show tasks
            if agent.task_queue:
                print("\nQueued Tasks:")
                for i, task in enumerate(agent.task_queue[:5]):  # Show first 5 tasks
                    print(f"  {i+1}. {task.task_type.value} (difficulty: {task.difficulty}, priority: {task.priority})")
                    if task.description:
                        print(f"     {task.description}")
                    if task.faction_goal:
                        print(f"     Goal: {task.faction_goal}")
            else:
                print("\nNo queued tasks.")
        
        def show_full_narrative(self):
            """Show the complete narrative log"""
            print("\n" + "-"*40)
            print("📍 Main Menu > Narrative Log")
            print("-"*40)
            print("📜 Complete Narrative Log:")
            if self.game_state.narrative_log:
                for i, entry in enumerate(self.game_state.narrative_log, 1):
                    print(f"  {i:2}. {entry}")
            else:
                print("  No narrative entries yet.")
        
        def show_active_events(self):
            """Show detailed information about active events"""
            print("\n" + "-"*40)
            print("📍 Main Menu > Active Events")
            print("-"*40)
            status = self.game_state.get_status_summary()
            
            print("🚨 Active Events:")
            if status['active_events']:
                for i, event in enumerate(status['active_events'], 1):
                    print(f"  {i}. {event}")
            else:
                print("  No active events at this time.")
            
            print("\n📍 Location Events:")
            if status['location_events']:
                for location_id, events in status['location_events'].items():
                    location_name = self.game_state.locations[location_id].name
                    print(f"  📍 {location_name}:")
                    for event in events:
                        print(f"    • {event}")
            else:
                print("  No location-specific events.")
        
        def add_task_to_agent(self):
            """Interactive menu to add a task to an agent"""
            print("\n" + "-"*40)
            print("📍 Main Menu > Add Task to Agent")
            print("-"*40)
            print("➕ Add Task to Agent")
            
            # Show available agents
            print("Available agents:")
            agent_list = list(self.game_state.agents.values())
            active_agents = [agent for agent in agent_list if agent.status == "active"]
            
            if not active_agents:
                print("❌ No active agents available for task assignment.")
                return
            
            for i, agent in enumerate(active_agents, 1):
                print(f"  {i}. {agent.name} ({agent.status})")
            
            try:
                agent_choice = int(input("Select agent (number): ")) - 1
                if agent_choice < 0 or agent_choice >= len(active_agents):
                    print("❌ Invalid agent selection. Please choose a valid number.")
                    return
                
                selected_agent = active_agents[agent_choice]
                
                # Check if agent can perform tasks
                if selected_agent.status != "active":
                    print(f"❌ Cannot assign task: {selected_agent.name} is {selected_agent.status}.")
                    return
                
                # Show task types
                print("\nTask types:")
                task_types = list(TaskType)
                for i, task_type in enumerate(task_types, 1):
                    print(f"  {i}. {task_type.value}")
                
                task_choice = int(input("Select task type (number): ")) - 1
                if task_choice < 0 or task_choice >= len(task_types):
                    print("❌ Invalid task selection. Please choose a valid number.")
                    return
                
                selected_task_type = task_types[task_choice]
                
                # Get difficulty
                try:
                    difficulty = int(input("Enter difficulty (1-10): "))
                    difficulty = max(1, min(10, difficulty))
                except ValueError:
                    print("❌ Invalid difficulty. Using default difficulty 5.")
                    difficulty = 5
                
                # Get description
                description = input("Enter task description (optional): ").strip()
                
                # Get priority
                try:
                    priority = int(input("Enter priority (1-5, higher = more urgent): "))
                    priority = max(1, min(5, priority))
                except ValueError:
                    print("❌ Invalid priority. Using default priority 1.")
                    priority = 1
                
                # Handle movement tasks
                target_location_id = None
                if selected_task_type == TaskType.MOVE:
                    print("\nAvailable locations:")
                    location_list = list(self.game_state.locations.values())
                    available_locations = [loc for loc in location_list if loc.id != selected_agent.location_id]
                    
                    if not available_locations:
                        print("❌ No other locations available for movement.")
                        return
                    
                    for i, location in enumerate(available_locations, 1):
                        print(f"  {i}. {location.name}")
                    
                    try:
                        loc_choice = int(input("Select target location (number): ")) - 1
                        if loc_choice < 0 or loc_choice >= len(available_locations):
                            print("❌ Invalid location selection.")
                            return
                        target_location_id = available_locations[loc_choice].id
                    except ValueError:
                        print("❌ Invalid location selection.")
                        return
                
                # Create and add the task
                task = Task(
                    task_type=selected_task_type,
                    target_location_id=target_location_id,
                    difficulty=difficulty,
                    description=description,
                    priority=priority
                )
                
                selected_agent.add_task(task)
                print(f"✅ Task '{selected_task_type.value}' assigned to {selected_agent.name} successfully!")
                
            except ValueError:
                print("❌ Invalid input. Please enter a valid number.")
            except Exception as e:
                print(f"❌ An error occurred: {e}")
        
        def show_location_details(self):
            """Show detailed information about all locations"""
            print("\n🗺️  Location Details:")
            status = self.game_state.get_status_summary()
            
            for location in self.game_state.locations.values():
                print(f"\n  📍 {location.name}")
                print(f"    Security Level: {location.security_level}/10")
                print(f"    Unrest Level: {location.unrest_level}/10")
                
                # Show active events in this location
                if location.id in status['location_events']:
                    print("    Active Events:")
                    for event in status['location_events'][location.id]:
                        print(f"      🚨 {event}")
                
                # Show agents in this location
                agents_here = [agent.name for agent in self.game_state.agents.values() 
                              if agent.location_id == location.id]
                if agents_here:
                    print(f"    Agents: {', '.join(agents_here)}")
                else:
                    print("    Agents: None")
        
        def show_active_missions(self):
            """Show detailed information about active missions"""
            print("\n🎯 Active Missions:")
            
            if not self.game_state.active_missions:
                print("  No active missions.")
                return
            
            for mission_id, mission in self.game_state.active_missions.items():
                location_name = self.game_state.locations[mission.target_location_id].name
                faction_name = self.game_state.factions[mission.faction_id].name
                
                print(f"\n  📋 Mission {mission_id}")
                print(f"    Type: {mission.mission_type.value}")
                print(f"    Target: {location_name}")
                print(f"    Faction: {faction_name}")
                print(f"    Difficulty: {mission.difficulty}/10")
                print(f"    Coordination: {mission.coordination_level}%")
                print(f"    Participants: {len(mission.participants)}")
                
                if mission.description:
                    print(f"    Description: {mission.description}")
                
                # Show participants and their roles
                if mission.participants:
                    print("    Team:")
                    for participant in mission.participants:
                        agent = self.game_state.agents[participant.agent_id]
                        print(f"      • {agent.name} ({participant.role.value}) - Risk: {participant.risk_level}/5")
                
                # Show success chance
                success_chance = mission.get_mission_success_chance(self.game_state.agents)
                print(f"    Success Chance: {success_chance}%")
        
        def create_mission(self):
            """Interactive menu to create a new multi-agent mission"""
            print("\n🎯 Create New Mission")
            
            # Select faction
            print("Select faction:")
            faction_list = list(self.game_state.factions.values())
            for i, faction in enumerate(faction_list, 1):
                print(f"  {i}. {faction.name}")
            
            try:
                faction_choice = int(input("Select faction (number): ")) - 1
                if faction_choice < 0 or faction_choice >= len(faction_list):
                    print("Invalid faction selection.")
                    return
                
                selected_faction = faction_list[faction_choice]
                
                # Select mission type
                print("\nMission types:")
                mission_types = list(MissionType)
                for i, mission_type in enumerate(mission_types, 1):
                    print(f"  {i}. {mission_type.value}")
                
                mission_choice = int(input("Select mission type (number): ")) - 1
                if mission_choice < 0 or mission_choice >= len(mission_types):
                    print("Invalid mission type selection.")
                    return
                
                selected_mission_type = mission_types[mission_choice]
                
                # Select target location
                print("\nTarget locations:")
                location_list = list(self.game_state.locations.values())
                for i, location in enumerate(location_list, 1):
                    print(f"  {i}. {location.name} (Security: {location.security_level}, Unrest: {location.unrest_level})")
                
                location_choice = int(input("Select target location (number): ")) - 1
                if location_choice < 0 or location_choice >= len(location_list):
                    print("Invalid location selection.")
                    return
                
                selected_location = location_list[location_choice]
                
                # Get difficulty and description
                difficulty = int(input("Enter difficulty (1-10): "))
                difficulty = max(1, min(10, difficulty))
                
                description = input("Enter mission description (optional): ").strip()
                
                # Create mission
                mission = self.game_state.create_mission(
                    mission_type=selected_mission_type,
                    target_location_id=selected_location.id,
                    faction_id=selected_faction.id,
                    difficulty=difficulty,
                    description=description
                )
                
                print(f"✅ Mission created: {mission.id}")
                print(f"Now add agents to the mission using command 8.")
                
            except (ValueError, IndexError):
                print("Invalid input. Mission not created.")
        
        def add_agent_to_mission(self):
            """Interactive menu to add agents to missions with roles"""
            print("\n👥 Add Agent to Mission")
            
            # Show active missions
            if not self.game_state.active_missions:
                print("No active missions. Create a mission first using command 7.")
                return
            
            print("Active missions:")
            mission_list = list(self.game_state.active_missions.values())
            for i, mission in enumerate(mission_list, 1):
                location_name = self.game_state.locations[mission.target_location_id].name
                faction_name = self.game_state.factions[mission.faction_id].name
                print(f"  {i}. {mission.mission_type.value} at {location_name} ({faction_name}) - {len(mission.participants)} agents")
            
            try:
                mission_choice = int(input("Select mission (number): ")) - 1
                if mission_choice < 0 or mission_choice >= len(mission_list):
                    print("Invalid mission selection.")
                    return
                
                selected_mission = mission_list[mission_choice]
                
                # Show available agents from the same faction
                available_agents = [agent for agent in self.game_state.agents.values() 
                                  if agent.faction_id == selected_mission.faction_id and agent.status == "active"]
                
                # Filter out agents already in the mission
                mission_agent_ids = [p.agent_id for p in selected_mission.participants]
                available_agents = [agent for agent in available_agents if agent.id not in mission_agent_ids]
                
                if not available_agents:
                    print("No available agents from this faction to add to the mission.")
                    return
                
                print(f"\nAvailable agents for {self.game_state.factions[selected_mission.faction_id].name}:")
                for i, agent in enumerate(available_agents, 1):
                    print(f"  {i}. {agent.name} (Skill: {agent.skill_level}/10)")
                
                agent_choice = int(input("Select agent (number): ")) - 1
                if agent_choice < 0 or agent_choice >= len(available_agents):
                    print("Invalid agent selection.")
                    return
                
                selected_agent = available_agents[agent_choice]
                
                # Select role
                print("\nAgent roles:")
                roles = list(AgentRole)
                for i, role in enumerate(roles, 1):
                    print(f"  {i}. {role.value}")
                
                role_choice = int(input("Select role (number): ")) - 1
                if role_choice < 0 or role_choice >= len(roles):
                    print("Invalid role selection.")
                    return
                
                selected_role = roles[role_choice]
                
                # Get risk level
                risk_level = int(input("Enter risk level (1-5, higher = more dangerous): "))
                risk_level = max(1, min(5, risk_level))
                
                # Add agent to mission
                success = self.game_state.add_agent_to_mission(
                    selected_mission.id, 
                    selected_agent.id, 
                    selected_role, 
                    risk_level
                )
                
                if success:
                    print(f"✅ Added {selected_agent.name} to mission as {selected_role.value}")
                    print(f"Mission coordination: {selected_mission.coordination_level}%")
                else:
                    print("❌ Failed to add agent to mission.")
                
            except (ValueError, IndexError):
                print("Invalid input. Agent not added to mission.")
        
        def execute_mission(self):
            """Execute a multi-agent mission"""
            print("\n🚀 Execute Mission")
            
            # Show missions ready for execution (at least 2 participants)
            ready_missions = [mission for mission in self.game_state.active_missions.values() 
                            if len(mission.participants) >= 2]
            
            if not ready_missions:
                print("No missions ready for execution. Missions need at least 2 participants.")
                return
            
            print("Missions ready for execution:")
            for i, mission in enumerate(ready_missions, 1):
                location_name = self.game_state.locations[mission.target_location_id].name
                faction_name = self.game_state.factions[mission.faction_id].name
                success_chance = mission.get_mission_success_chance(self.game_state.agents)
                print(f"  {i}. {mission.mission_type.value} at {location_name} ({faction_name})")
                print(f"     Participants: {len(mission.participants)}, Success: {success_chance}%")
            
            try:
                mission_choice = int(input("Select mission to execute (number): ")) - 1
                if mission_choice < 0 or mission_choice >= len(ready_missions):
                    print("Invalid mission selection.")
                    return
                
                selected_mission = ready_missions[mission_choice]
                
                # Confirm execution
                confirm = input(f"Execute {selected_mission.mission_type.value} mission? (y/n): ").strip().lower()
                if confirm != 'y':
                    print("Mission execution cancelled.")
                    return
                
                # Execute mission
                results = self.game_state.execute_mission(selected_mission.id)
                
                if results["success"]:
                    print(f"🎉 Mission successful!")
                    if "rewards" in results:
                        print(f"Rewards: {results['rewards']}")
                else:
                    print(f"❌ Mission failed!")
                    if "penalties" in results:
                        print(f"Penalties: {results['penalties']}")
                
                print(f"Roll: {results['roll']}/{results['success_chance']}")
                print(f"Coordination: {results['coordination_level']}%")
                
            except (ValueError, IndexError):
                print("Invalid input. Mission not executed.")
        
        def show_public_opinion(self):
            """Show public opinion and media coverage"""
            opinion = self.game_state.public_opinion
            
            print("\n📊 Public Opinion & Media Coverage:")
            
            # General support
            support_emoji = "🟢" if opinion.general_support > 60 else "🟡" if opinion.general_support > 40 else "🔴"
            print(f"\n  {support_emoji} General Public Support: {opinion.general_support}/100")
            
            # Faction support
            print("\n  📈 Faction Support:")
            for faction_id, support in opinion.faction_support.items():
                faction_name = self.game_state.factions[faction_id].name
                support_emoji = "🟢" if support > 60 else "🟡" if support > 40 else "🔴"
                print(f"    {support_emoji} {faction_name}: {support}/100")
            
            # Political influence
            influence_emoji = "🟢" if opinion.political_influence > 20 else "🟡" if opinion.political_influence > -20 else "🔴"
            print(f"\n  🏛️  Political Influence: {influence_emoji} {opinion.political_influence}/100")
            
            # Media coverage
            if opinion.media_coverage:
                print("\n  📰 Recent Media Coverage:")
                for i, coverage in enumerate(opinion.media_coverage, 1):
                    print(f"    {i}. {coverage}")
            else:
                print("\n  📰 No recent media coverage")
            
            # Community relations
            if opinion.community_relations:
                print("\n  🏘️  Community Relations:")
                for community, support in opinion.community_relations.items():
                    support_emoji = "🟢" if support > 60 else "🟡" if support > 40 else "🔴"
                    print(f"    {support_emoji} {community}: {support}/100")
        
        def run(self):
            """Main game loop with number/keyword menu selection"""
            self.display_header()
            while True:
                self.display_current_status()
                self.display_menu()
                choice = input("Select command (number or keyword): ").strip().lower()
                action_map = {
                    '1': 'advance', 'advance': 'advance',
                    '2': 'agents', 'agents': 'agents',
                    '3': 'narrative', 'narrative': 'narrative',
                    '4': 'addtask', 'addtask': 'addtask',
                    '5': 'locations', 'locations': 'locations',
                    '6': 'events', 'events': 'events',
                    '7': 'missions', 'missions': 'missions',
                    '8': 'createmission', 'createmission': 'createmission',
                    '9': 'addtomission', 'addtomission': 'addtomission',
                    '10': 'execmission', 'execmission': 'execmission',
                    'p': 'opinion', 'opinion': 'opinion',
                    'q': 'quit', 'quit': 'quit',
                }
                action = action_map.get(choice, None)
                if action == 'advance':
                    print("\n⏭️  Advancing turn...")
                    self.game_state.advance_turn()
                    print("✅ Turn advanced successfully!")
                elif action == 'agents':
                    self.show_agent_details()
                    print("\n✅ Agent details displayed.")
                elif action == 'narrative':
                    self.show_full_narrative()
                    print("\n✅ Narrative log displayed.")
                elif action == 'addtask':
                    self.add_task_to_agent()
                    print("\n✅ Task assignment completed.")
                elif action == 'locations':
                    self.show_location_details()
                    print("\n✅ Location details displayed.")
                elif action == 'events':
                    self.show_active_events()
                    print("\n✅ Active events displayed.")
                elif action == 'missions':
                    self.show_active_missions()
                    print("\n✅ Active missions displayed.")
                elif action == 'createmission':
                    self.create_mission()
                    print("\n✅ Mission creation completed.")
                elif action == 'addtomission':
                    self.add_agent_to_mission()
                    print("\n✅ Agent added to mission.")
                elif action == 'execmission':
                    self.execute_mission()
                    print("\n✅ Mission execution completed.")
                elif action == 'opinion':
                    self.show_public_opinion()
                    print("\n✅ Public opinion displayed.")
                elif action == 'quit':
                    print("👋 Exiting game. Goodbye!")
                    break
                else:
                    print("❌ Invalid command. Please enter a number or keyword from the menu.")

    GameCLI().run()

if __name__ == "__main__":
    main()
