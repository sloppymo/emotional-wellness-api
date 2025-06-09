#!/usr/bin/env python3
"""
Years of Lead - Game Launcher

A Liberal Crime Squad inspired insurgency simulator.
"""

import sys
import os
import termios
import tty
from pathlib import Path
from typing import Optional, List, Tuple

# Add src to Python path so we can import the game modules
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Import character creation system
from game.character_creation_ui import CharacterCreationUI, CharacterManagementUI

class MenuSystem:
    """Liberal Crime Squad style menu system with arrow key navigation"""
    
    def __init__(self):
        self.old_settings = None
        self.use_fallback = False
        # Test if termios works
        try:
            termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, termios.tcgetattr(sys.stdin))
        except (AttributeError, OSError):
            self.use_fallback = True
    
    def getch(self):
        """Get a single character from stdin without pressing Enter"""
        if self.use_fallback:
            # Simple fallback - just get input with Enter
            return input().strip()[:1] if input().strip() else ' '
        
        try:
            self.old_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
            ch = sys.stdin.read(1)
            return ch
        finally:
            if self.old_settings:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
    
    def get_arrow_key(self):
        """Detect arrow key sequences"""
        first = self.getch()
        if first == '\x1b':  # ESC sequence
            second = self.getch()
            if second == '[':
                third = self.getch()
                if third == 'A':
                    return 'UP'
                elif third == 'B':
                    return 'DOWN'
                elif third == 'C':
                    return 'RIGHT'
                elif third == 'D':
                    return 'LEFT'
        return first
    
    def display_menu(self, title: str, options: List[Tuple[str, str]], selected: int = 0, show_numbers: bool = True):
        """Display a menu with highlighting"""
        print(f"\n┌─ {title} " + "─" * (78 - len(title) - 4) + "┐")
        print(f"│{' ' * 76}│")
        
        for i, (key, desc) in enumerate(options):
            if show_numbers:
                prefix = f"  {i+1}) " if i < 9 else f" {i+1}) "
            else:
                prefix = f"  {key}) "
            
            if i == selected:
                # Highlighted item
                print(f"│{prefix}► {desc:<{70-len(prefix)}}│")
            else:
                # Normal item
                print(f"│{prefix}  {desc:<{70-len(prefix)}}│")
        
        print(f"│{' ' * 76}│")
        print(f"└{'─' * 76}┘")
    
    def select_from_menu(self, title: str, options: List[Tuple[str, str]], show_numbers: bool = True) -> str:
        """Handle menu selection with arrow keys and numbers"""
        selected = 0
        
        while True:
            os.system('clear' if os.name == 'posix' else 'cls')
            
            # Show the menu with current selection
            self.display_menu(title, options, selected, show_numbers)
            
            if self.use_fallback:
                if show_numbers:
                    print(f"\n[Enter number 1-{len(options)} or letter key]: ", end="")
                else:
                    print(f"\n[Enter letter key]: ", end="")
            else:
                if show_numbers:
                    print(f"\n[Use ↑↓ arrows, numbers 1-{len(options)}, or ENTER to select]")
                else:
                    print(f"\n[Use ↑↓ arrows, letter keys, or ENTER to select]")
            
            # Get user input
            if self.use_fallback:
                # In fallback mode, just get direct input
                key = self.getch()
                if key.isdigit() and show_numbers:
                    num = int(key)
                    if 1 <= num <= len(options):
                        return options[num - 1][0]
                elif not show_numbers or not key.isdigit():
                    # Letter selection
                    for option_key, _ in options:
                        if key.upper() == option_key.upper():
                            return option_key
                # Invalid input in fallback mode
                continue
            else:
                # Full arrow key support
                key = self.get_arrow_key()
                
                if key == 'UP':
                    selected = (selected - 1) % len(options)
                elif key == 'DOWN':
                    selected = (selected + 1) % len(options)
                elif key == '\r' or key == '\n':  # Enter key
                    return options[selected][0]
                elif key.isdigit() and show_numbers:
                    # Direct number selection
                    num = int(key)
                    if 1 <= num <= len(options):
                        return options[num - 1][0]
                elif not show_numbers:
                    # Letter selection for non-numbered menus
                    for i, (option_key, _) in enumerate(options):
                        if key.upper() == option_key.upper():
                            return option_key
                elif key == '\x03':  # Ctrl+C
                    return 'QUIT'

class LCSInterface:
    """Liberal Crime Squad style interface for Years of Lead"""
    
    def __init__(self, game_state):
        self.gs = game_state
        self.running = True
        self.menu = MenuSystem()
        self.character_manager = CharacterManagementUI()
        self.player_characters = []
    
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def print_banner(self):
        """Print the main game banner"""
        print("=" * 80)
        print("""
 ██╗   ██╗███████╗ █████╗ ██████╗ ███████╗     ██████╗ ███████╗    ██╗     ███████╗ █████╗ ██████╗ 
 ╚██╗ ██╔╝██╔════╝██╔══██╗██╔══██╗██╔════╝    ██╔═══██╗██╔════╝    ██║     ██╔════╝██╔══██╗██╔══██╗
  ╚████╔╝ █████╗  ███████║██████╔╝███████╗    ██║   ██║█████╗      ██║     █████╗  ███████║██║  ██║
   ╚██╔╝  ██╔══╝  ██╔══██║██╔══██╗╚════██║    ██║   ██║██╔══╝      ██║     ██╔══╝  ██╔══██║██║  ██║
    ██║   ███████╗██║  ██║██║  ██║███████║    ╚██████╔╝██║         ███████╗███████╗██║  ██║██████╔╝
    ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝     ╚═════╝ ╚═╝         ╚══════╝╚══════╝╚═╝  ╚═╝╚═════╝ 
                                                                                                        
                           Turn-Based Insurgency Simulator
""")
        print("=" * 80)
        print(f"Turn {self.gs.turn_number} - {self.gs.current_phase.value.upper()} PHASE")
        print("=" * 80)
    
    def print_status_bar(self):
        """Print current game status"""
        status = self.gs.get_status_summary()
        print(f"\n┌─ SITUATION REPORT ─────────────────────────────────────────────────────────┐")
        print(f"│ Active Operatives: {status['active_agents']:2d}/{status['total_agents']:2d}  │  Phase: {status['phase'].upper():>8s}  │  Turn: {status['turn']:3d} │")
        print(f"└────────────────────────────────────────────────────────────────────────────┘")
    
    def main_menu(self):
        """Display the main game menu"""
        while self.running:
            self.clear_screen()
            self.print_banner()
            self.print_status_bar()
            
            # Main menu options
            options = [
                ("A", "ADVANCE TIME      - Progress to next phase"),
                ("S", "SITUATION REPORT  - Review faction status and agent locations"), 
                ("O", "OPERATIONS        - Manage missions and agent assignments"),
                ("I", "INTELLIGENCE      - View recent events and enemy activity"),
                ("L", "LOCATIONS         - Survey areas under faction control"),
                ("R", "RESOURCES         - Review faction finances and assets"),
                ("C", "CHARACTERS        - Create and manage player characters"),
                ("X", "EXIT              - Abandon the struggle")
            ]
            
            choice = self.menu.select_from_menu("COMMAND CENTER", options, show_numbers=False)
            
            if choice == 'A':
                self.advance_time()
            elif choice == 'S':
                self.situation_report()
            elif choice == 'O':
                self.operations_menu()
            elif choice == 'I':
                self.intelligence_report()
            elif choice == 'L':
                self.locations_report()
            elif choice == 'R':
                self.resources_report()
            elif choice == 'C':
                self.character_menu()
            elif choice == 'X':
                if self.confirm_quit():
                    self.running = False
            elif choice == 'QUIT':
                self.running = False
    
    def advance_time(self):
        """Advance the game to next phase"""
        self.clear_screen()
        self.print_banner()
        
        print(f"\n┌─ TIME ADVANCE ─────────────────────────────────────────────────────────────┐")
        print(f"│                                                                            │")
        print(f"│  Advancing from {self.gs.current_phase.value.upper()} phase...                      │")
        print(f"│                                                                            │")
        print(f"└────────────────────────────────────────────────────────────────────────────┘")
        
        print("\n🕐 Time advances...")
        print("📋 Issuing new orders to operatives...")
        print("🎭 Analyzing government response...")
        print("📊 Updating intelligence reports...")
        
        self.gs.advance_turn()
        
        print(f"\n✓ Now in {self.gs.current_phase.value.upper()} phase of Turn {self.gs.turn_number}")
        print("\n[Press any key to continue...]")
        self.menu.getch()
    
    def situation_report(self):
        """Display detailed faction and agent status"""
        self.clear_screen()
        self.print_banner()
        
        status = self.gs.get_status_summary()
        agent_locations = self.gs.get_agent_locations()
        
        print(f"\n┌─ SITUATION REPORT ─────────────────────────────────────────────────────────┐")
        print(f"│                                                                            │")
        print(f"│  FACTION STATUS:                                                           │")
        
        for faction_id, resources in status['factions'].items():
            faction = self.gs.factions[faction_id]
            goal = faction.current_goal.replace('_', ' ').title()
            print(f"│                                                                            │")
            print(f"│  • {faction.name:<25} Current Focus: {goal:<20} │")
            print(f"│    Funds: ${resources['money']:<6} Influence: {resources['influence']:<3} Personnel: {resources['personnel']:<3}        │")
        
        print(f"│                                                                            │")
        print(f"│  OPERATIVE DEPLOYMENT:                                                     │")
        
        for location_id, agents in agent_locations.items():
            location_name = self.gs.locations[location_id].name
            location = self.gs.locations[location_id]
            print(f"│                                                                            │")
            print(f"│  • {location_name:<25} (Security: {location.security_level}/10, Unrest: {location.unrest_level}/10)     │")
            for agent_info in agents:
                print(f"│    - {agent_info:<60}        │")
        
        print(f"│                                                                            │")
        print(f"└────────────────────────────────────────────────────────────────────────────┘")
        
        print("\n[Press any key to continue...]")
        self.menu.getch()
    
    def operations_menu(self):
        """Operations and missions submenu"""
        while True:
            self.clear_screen()
            self.print_banner()
            
            options = [
                ("1", "ACTIVE MISSIONS   - Review ongoing operations"),
                ("2", "PLAN OPERATION    - Coordinate new multi-agent missions"),
                ("3", "AGENT STATUS      - Review individual operative capabilities"),
                ("4", "EQUIPMENT         - Manage weapons and resources"),
                ("B", "BACK              - Return to command center")
            ]
            
            choice = self.menu.select_from_menu("OPERATIONS CENTER", options, show_numbers=True)
            
            if choice == '1':
                self.active_missions()
            elif choice == '2':
                self.plan_operation()
            elif choice == '3':
                self.agent_status()
            elif choice == '4':
                self.equipment_status()
            elif choice == 'B' or choice == 'QUIT':
                break
    
    def intelligence_report(self):
        """Display recent events and intelligence"""
        self.clear_screen()
        self.print_banner()
        
        status = self.gs.get_status_summary()
        
        print(f"\n┌─ INTELLIGENCE REPORT ──────────────────────────────────────────────────────┐")
        print(f"│                                                                            │")
        print(f"│  RECENT ACTIVITY:                                                          │")
        
        if status['recent_narrative']:
            for i, event in enumerate(status['recent_narrative'][-8:], 1):
                # Clean up the event text
                clean_event = event.replace('[NARRATIVE] ', '').replace('📋 ', '• ').replace('🎯 ', '• ').replace('💥 ', '• ')
                if len(clean_event) > 70:
                    clean_event = clean_event[:67] + "..."
                print(f"│  {i:2d}) {clean_event:<68} │")
        else:
            print(f"│     No recent intelligence available.                                      │")
        
        print(f"│                                                                            │")
        
        if status['active_events']:
            print(f"│  ONGOING EVENTS:                                                           │")
            for event in status['active_events']:
                print(f"│  • {event:<70} │")
            print(f"│                                                                            │")
        
        print(f"└────────────────────────────────────────────────────────────────────────────┘")
        
        print("\n[Press any key to continue...]")
        self.menu.getch()
    
    def locations_report(self):
        """Display location information"""
        self.clear_screen()
        self.print_banner()
        
        print(f"\n┌─ LOCATION INTELLIGENCE ────────────────────────────────────────────────────┐")
        print(f"│                                                                            │")
        
        for location_id, location in self.gs.locations.items():
            agent_count = len([a for a in self.gs.agents.values() if a.location_id == location_id])
            
            # Security level description
            if location.security_level <= 3:
                security_desc = "LOW"
            elif location.security_level <= 6:
                security_desc = "MODERATE"
            else:
                security_desc = "HIGH"
            
            # Unrest level description  
            if location.unrest_level <= 3:
                unrest_desc = "CALM"
            elif location.unrest_level <= 6:
                unrest_desc = "TENSE"
            else:
                unrest_desc = "VOLATILE"
            
            print(f"│  • {location.name:<25}                                    │")
            print(f"│    Security: {security_desc:<8} ({location.security_level}/10)  Unrest: {unrest_desc:<8} ({location.unrest_level}/10)     │")
            print(f"│    Operatives Present: {agent_count}                                          │")
            
            if location.active_events:
                print(f"│    Active Events: {len(location.active_events)} ongoing                              │")
            
            print(f"│                                                                            │")
        
        print(f"└────────────────────────────────────────────────────────────────────────────┘")
        
        print("\n[Press any key to continue...]")
        self.menu.getch()
    
    def resources_report(self):
        """Display detailed resource information"""
        self.clear_screen()
        self.print_banner()
        
        status = self.gs.get_status_summary()
        
        print(f"\n┌─ RESOURCE ASSESSMENT ──────────────────────────────────────────────────────┐")
        print(f"│                                                                            │")
        
        total_money = sum(r['money'] for r in status['factions'].values())
        total_influence = sum(r['influence'] for r in status['factions'].values())
        total_personnel = sum(r['personnel'] for r in status['factions'].values())
        
        print(f"│  COMBINED RESISTANCE ASSETS:                                              │")
        print(f"│    Total Funds: ${total_money:<10} Total Influence: {total_influence:<10} Total Personnel: {total_personnel:<6} │")
        print(f"│                                                                            │")
        print(f"│  FACTION BREAKDOWN:                                                        │")
        
        for faction_id, resources in status['factions'].items():
            faction = self.gs.factions[faction_id]
            goal = faction.current_goal.replace('_', ' ').title()
            
            # Calculate faction strength
            strength = (resources['money'] + resources['influence'] + resources['personnel'] * 5) // 10
            if strength <= 15:
                strength_desc = "WEAK"
            elif strength <= 25:
                strength_desc = "STABLE"
            else:
                strength_desc = "STRONG"
            
            print(f"│                                                                            │")
            print(f"│  • {faction.name:<25} Status: {strength_desc:<8}                 │")
            print(f"│    Funds: ${resources['money']:<8} Influence: {resources['influence']:<8} Personnel: {resources['personnel']:<8}   │")
            print(f"│    Current Focus: {goal:<35}                    │")
        
        print(f"│                                                                            │")
        print(f"└────────────────────────────────────────────────────────────────────────────┘")
        
        print("\n[Press any key to continue...]")
        self.menu.getch()
    
    def active_missions(self):
        """Display active missions"""
        self.clear_screen()
        self.print_banner()
        
        print(f"\n┌─ ACTIVE MISSIONS ──────────────────────────────────────────────────────────┐")
        print(f"│                                                                            │")
        
        if self.gs.active_missions:
            for mission_id, mission in self.gs.active_missions.items():
                location_name = self.gs.locations[mission.target_location_id].name
                faction_name = self.gs.factions[mission.faction_id].name
                
                print(f"│  Mission: {mission_id:<15} Type: {mission.mission_type.value.title():<20} │")
                print(f"│  Target: {location_name:<20} Faction: {faction_name:<25}   │")
                print(f"│  Participants: {len(mission.participants)} operatives                               │")
                print(f"│                                                                            │")
        else:
            print(f"│  No active multi-agent missions.                                          │")
            print(f"│  Operatives are conducting individual assignments.                        │")
            print(f"│                                                                            │")
        
        print(f"└────────────────────────────────────────────────────────────────────────────┘")
        
        print("\n[Press any key to continue...]")
        self.menu.getch()
    
    def plan_operation(self):
        """Plan new operations (placeholder)"""
        self.clear_screen()
        self.print_banner()
        
        print(f"\n┌─ OPERATION PLANNING ───────────────────────────────────────────────────────┐")
        print(f"│                                                                            │")
        print(f"│  MISSION PLANNING SYSTEM OFFLINE                                           │")
        print(f"│                                                                            │")
        print(f"│  Currently, operatives receive assignments automatically based on         │")
        print(f"│  faction priorities and operational requirements.                          │")
        print(f"│                                                                            │")
        print(f"│  Advanced mission coordination will be available in future updates.       │")
        print(f"│                                                                            │")
        print(f"└────────────────────────────────────────────────────────────────────────────┘")
        
        print("\n[Press any key to continue...]")
        self.menu.getch()
    
    def agent_status(self):
        """Display detailed agent information"""
        self.clear_screen()
        self.print_banner()
        
        print(f"\n┌─ OPERATIVE ROSTER ─────────────────────────────────────────────────────────┐")
        print(f"│                                                                            │")
        
        for agent_id, agent in self.gs.agents.items():
            faction_name = self.gs.factions[agent.faction_id].name
            location_name = self.gs.locations[agent.location_id].name
            
            # Get agent's best skills
            best_skills = sorted(agent.skills.items(), key=lambda x: x[1].level, reverse=True)[:3]
            skills_text = ', '.join([f"{skill.value.title()}({level.level})" for skill, level in best_skills])
            
            # Fix: Use agent.status.value to get the string value of the enum
            status_text = agent.status.value.upper()
            
            print(f"│  • {agent.name:<20} [{status_text}]                          │")
            print(f"│    Faction: {faction_name:<15} Location: {location_name:<20}       │")
            print(f"│    Background: {agent.background.title():<12} Loyalty: {agent.loyalty}% Stress: {agent.stress}%      │")
            print(f"│    Top Skills: {skills_text[:50]:<50}                     │")
            if agent.equipment:
                equipment_list = ', '.join([eq.name for eq in agent.equipment])
                print(f"│    Equipment: {equipment_list[:52]:<52}               │")
            else:
                print(f"│    Equipment: None                                                     │")
            print(f"│                                                                            │")
        
        print(f"└────────────────────────────────────────────────────────────────────────────┘")
        
        print("\n[Press any key to continue...]")
        self.menu.getch()
    
    def equipment_status(self):
        """Display equipment information (placeholder)"""
        self.clear_screen()
        self.print_banner()
        
        print(f"\n┌─ EQUIPMENT INVENTORY ──────────────────────────────────────────────────────┐")
        print(f"│                                                                            │")
        print(f"│  EQUIPMENT MANAGEMENT SYSTEM OFFLINE                                       │")
        print(f"│                                                                            │")
        print(f"│  Currently, equipment is managed automatically based on faction           │")
        print(f"│  resources and operational requirements.                                   │")
        print(f"│                                                                            │")
        print(f"│  Advanced equipment customization will be available in future updates.    │")
        print(f"│                                                                            │")
        print(f"└────────────────────────────────────────────────────────────────────────────┘")
        
        print("\n[Press any key to continue...]")
        self.menu.getch()
    
    def character_menu(self):
        """Display character management menu"""
        while True:
            self.clear_screen()
            self.print_banner()
            
            print(f"\n┌─ CHARACTER MANAGEMENT ──────────────────────────────────────────────────┐")
            print(f"│                                                                            │")
            
            # Show current character count
            character_count = len(self.player_characters)
            print(f"│  Current Characters: {character_count}                                                    │")
            print(f"│                                                                            │")
            
            options = [
                ("1", "CREATE NEW CHARACTER"),
                ("2", "VIEW CHARACTER ROSTER"),
                ("3", "SELECT ACTIVE CHARACTER"),
                ("B", "BACK TO MAIN MENU")
            ]
            
            choice = self.menu.select_from_menu("CHARACTER MANAGEMENT", options, show_numbers=True)
            
            if choice == '1':
                self.create_new_character()
            elif choice == '2':
                self.view_character_roster()
            elif choice == '3':
                self.select_active_character()
            elif choice == 'B' or choice == 'QUIT':
                break
    
    def create_new_character(self):
        """Create a new character"""
        self.clear_screen()
        self.print_banner()
        
        print(f"\n┌─ CREATE NEW CHARACTER ──────────────────────────────────────────────────┐")
        print(f"│                                                                            │")
        
        # Use the character creation UI
        creation_ui = CharacterCreationUI()
        
        while True:
            print("\n" + "=" * 50)
            print("CHARACTER CREATION")
            print("=" * 50)
            print("1. Create New Character (Step-by-step)")
            print("2. Quick Random Character")
            print("3. Back to Character Menu")
            
            choice = input("\nEnter choice: ").strip()
            
            if choice == "1":
                character = creation_ui.run_character_creation()
                if character:
                    self.player_characters.append(character)
                    print(f"\n🎉 Character '{character.name}' created and added to roster!")
                    print("\n[Press any key to continue...]")
                    self.menu.getch()
                    break
            elif choice == "2":
                name = input("Enter character name (or press Enter for random): ").strip()
                if not name:
                    name = None
                character = creation_ui.quick_create_character(name)
                self.player_characters.append(character)
                print(f"\n🎉 Random character '{character.name}' created!")
                print(character.get_character_summary())
                print("\n[Press any key to continue...]")
                self.menu.getch()
                break
            elif choice == "3":
                break
            else:
                print("Invalid choice. Please try again.")
    
    def view_character_roster(self):
        """View all created characters"""
        self.clear_screen()
        self.print_banner()
        
        print(f"\n┌─ CHARACTER ROSTER ───────────────────────────────────────────────────────┐")
        print(f"│                                                                            │")
        
        if not self.player_characters:
            print(f"│  No characters created yet.                                                │")
            print(f"│  Create your first character to begin the struggle!                      │")
        else:
            print(f"│  Character Roster ({len(self.player_characters)} characters):                              │")
            print(f"│                                                                            │")
            
            for i, character in enumerate(self.player_characters, 1):
                background_name = character.background.name
                primary_trait = character.traits.primary_trait.value.replace('_', ' ').title()
                print(f"│  {i:2d}. {character.name:15} - {background_name:12} - {primary_trait:15} │")
        
        print(f"│                                                                            │")
        print(f"└────────────────────────────────────────────────────────────────────────────┘")
        
        print("\n[Press any key to continue...]")
        self.menu.getch()
    
    def select_active_character(self):
        """Select and view a specific character"""
        if not self.player_characters:
            self.clear_screen()
            self.print_banner()
            print(f"\n┌─ NO CHARACTERS ─────────────────────────────────────────────────────────┐")
            print(f"│                                                                            │")
            print(f"│  No characters available. Create a character first!                       │")
            print(f"│                                                                            │")
            print(f"└────────────────────────────────────────────────────────────────────────────┘")
            print("\n[Press any key to continue...]")
            self.menu.getch()
            return
        
        while True:
            self.clear_screen()
            self.print_banner()
            
            print(f"\n┌─ SELECT CHARACTER ──────────────────────────────────────────────────────┐")
            print(f"│                                                                            │")
            print(f"│  Choose a character to view details:                                      │")
            print(f"│                                                                            │")
            
            for i, character in enumerate(self.player_characters, 1):
                background_name = character.background.name
                primary_trait = character.traits.primary_trait.value.replace('_', ' ').title()
                print(f"│  {i:2d}. {character.name:15} - {background_name:12} - {primary_trait:15} │")
            
            print(f"│  0. Back to Character Menu                                                │")
            print(f"│                                                                            │")
            print(f"└────────────────────────────────────────────────────────────────────────────┘")
            
            try:
                choice = int(input("\nEnter choice: "))
                if choice == 0:
                    break
                elif 1 <= choice <= len(self.player_characters):
                    self.view_character_details(choice - 1)
                else:
                    print(f"Please enter a number between 0 and {len(self.player_characters)}")
                    input("Press Enter to continue...")
            except ValueError:
                print("Please enter a valid number")
                input("Press Enter to continue...")
    
    def view_character_details(self, character_index: int):
        """View detailed character information"""
        character = self.player_characters[character_index]
        
        self.clear_screen()
        self.print_banner()
        
        print(f"\n┌─ CHARACTER DETAILS ───────────────────────────────────────────────────────┐")
        print(f"│                                                                            │")
        
        # Display character summary
        summary_lines = character.get_character_summary().split('\n')
        for line in summary_lines:
            if line.strip():
                # Format the line to fit in the box
                if len(line) > 76:
                    line = line[:73] + "..."
                print(f"│  {line:<76} │")
            else:
                print(f"│                                                                            │")
        
        print(f"│                                                                            │")
        print(f"└────────────────────────────────────────────────────────────────────────────┘")
        
        print("\n[Press any key to continue...]")
        self.menu.getch()
    
    def confirm_quit(self):
        """Confirm quit with dramatic message"""
        self.clear_screen()
        self.print_banner()
        
        print(f"\n┌─ ABANDON THE RESISTANCE? ──────────────────────────────────────────────────┐")
        print(f"│                                                                            │")
        print(f"│  The struggle continues even without your leadership...                    │")
        print(f"│                                                                            │")
        print(f"│  The resistance will continue without your leadership, but progress       │")
        print(f"│  will be slower. Your operatives will continue their missions, but        │")
        print(f"│  coordination between factions will suffer.                               │")
        print(f"│                                                                            │")
        print(f"│  Are you sure you want to step down from command?                         │")
        print(f"│                                                                            │")
        print(f"└────────────────────────────────────────────────────────────────────────────┘")
        
        options = [
            ("Y", "YES - Step down and end the session"),
            ("N", "NO  - Continue the fight")
        ]
        
        choice = self.menu.select_from_menu("CONFIRMATION", options, show_numbers=False)
        return choice == 'Y'

def main():
    """Main game entry point"""
    try:
        # Import the game core from the Years of Lead project
        from game.core import GameState
        
        print("Initializing Years of Lead...")
        print("Loading operatives, factions, and locations...")
        
        # Initialize the game state
        gs = GameState()
        gs.initialize_game()
        
        print(f"✓ Loaded {len(gs.factions)} resistance factions")
        print(f"✓ Deployed {len(gs.agents)} operatives")
        print(f"✓ Identified {len(gs.locations)} operational areas")
        
        # Start the interface
        interface = LCSInterface(gs)
        
        print("\n" + "=" * 80)
        print("OPERATIONAL STATUS: READY")
        print("RESISTANCE COMMAND INITIALIZED")
        print("=" * 80)
        print("\n[Press any key to assume command...]")
        interface.menu.getch()
        
        # Run the main game loop
        interface.main_menu()
        
        # Game ended
        print("\n" + "=" * 80)
        print("The Years of Lead continue...")
        print("Your struggle is recorded in history.")
        print("Thank you for leading the resistance.")
        print("=" * 80)
        
    except ImportError as e:
        print(f"Failed to load game modules: {e}")
        print("Make sure you're running this from the years-of-lead project directory.")
        print("Also ensure all dependencies are installed: pip install -r requirements.txt")
        return 1
    
    except KeyboardInterrupt:
        print("\n\nOperation terminated by user.")
        return 0
    
    except Exception as e:
        print(f"Critical error: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 