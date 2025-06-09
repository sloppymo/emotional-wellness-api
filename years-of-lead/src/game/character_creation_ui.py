"""
Years of Lead - Character Creation UI

Interactive character creation interface that integrates with the existing
Years of Lead menu system and game state.
"""

import os
import sys
from typing import List, Tuple, Optional, Dict, Any
from .character_creation import (
    CharacterCreator, Character, BackgroundType, PersonalityTrait,
    SkillCategory, CharacterSkills, CharacterTraits, CharacterMotivation
)


class CharacterCreationUI:
    """Interactive character creation interface"""
    
    def __init__(self):
        self.creator = CharacterCreator()
        self.current_character = None
        self.creation_steps = [
            "name",
            "background", 
            "primary_trait",
            "secondary_trait",
            "skills",
            "review"
        ]
        self.current_step = 0
        self.character_data = {}
    
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def print_banner(self):
        """Print the character creation banner"""
        print("=" * 80)
        print("""
 ██████╗██╗  ██╗ █████╗ ██████╗ ███████╗ █████╗  ██████╗ ████████╗███████╗██████╗ 
██╔════╝██║  ██║██╔══██╗██╔══██╗██╔════╝██╔══██╗██╔═══██╗╚══██╔══╝██╔════╝██╔══██╗
██║     ███████║███████║██████╔╝█████╗  ███████║██║   ██║   ██║   █████╗  ██████╔╝
██║     ██╔══██║██╔══██║██╔══██╗██╔══╝  ██╔══██║██║   ██║   ██║   ██╔══╝  ██╔══██╗
╚██████╗██║  ██║██║  ██║██║  ██║███████╗██║  ██║╚██████╔╝   ██║   ███████╗██║  ██║
 ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚══════╝╚═╝  ╚═╝
                                                                                    
                           Character Creation System
""")
        print("=" * 80)
    
    def print_progress(self):
        """Print creation progress"""
        step_names = {
            "name": "Character Name",
            "background": "Background Selection", 
            "primary_trait": "Primary Personality",
            "secondary_trait": "Secondary Personality",
            "skills": "Skill Allocation",
            "review": "Final Review"
        }
        
        current_step_name = step_names.get(self.creation_steps[self.current_step], "Unknown")
        print(f"\nStep {self.current_step + 1} of {len(self.creation_steps)}: {current_step_name}")
        print("-" * 50)
    
    def get_name_input(self) -> str:
        """Get character name from user"""
        while True:
            name = input("\nEnter your character's name: ").strip()
            if name:
                return name
            print("Name cannot be empty. Please try again.")
    
    def select_background(self) -> BackgroundType:
        """Interactive background selection"""
        backgrounds = list(BackgroundType)
        
        while True:
            print("\nSelect your character's background:")
            print("-" * 40)
            
            for i, bg_type in enumerate(backgrounds, 1):
                background = self.creator.backgrounds[bg_type]
                print(f"{i:2d}. {background.name:12} - {background.description}")
            
            try:
                choice = int(input(f"\nEnter choice (1-{len(backgrounds)}): "))
                if 1 <= choice <= len(backgrounds):
                    return backgrounds[choice - 1]
                else:
                    print(f"Please enter a number between 1 and {len(backgrounds)}")
            except ValueError:
                print("Please enter a valid number")
    
    def select_trait(self, trait_type: str, exclude_trait: Optional[PersonalityTrait] = None) -> PersonalityTrait:
        """Interactive trait selection"""
        traits = list(PersonalityTrait)
        if exclude_trait:
            traits = [t for t in traits if t != exclude_trait]
        
        while True:
            print(f"\nSelect your character's {trait_type} personality trait:")
            print("-" * 50)
            
            for i, trait in enumerate(traits, 1):
                trait_desc = trait.value.replace('_', ' ').title()
                print(f"{i:2d}. {trait_desc}")
            
            try:
                choice = int(input(f"\nEnter choice (1-{len(traits)}): "))
                if 1 <= choice <= len(traits):
                    return traits[choice - 1]
                else:
                    print(f"Please enter a number between 1 and {len(traits)}")
            except ValueError:
                print("Please enter a valid number")
    
    def allocate_skills(self) -> Dict[str, int]:
        """Interactive skill allocation"""
        max_points = 20
        remaining_points = max_points
        skills = {
            'combat': 1, 'stealth': 1, 'hacking': 1, 'social': 1,
            'technical': 1, 'medical': 1, 'survival': 1, 'intelligence': 1
        }
        
        # Apply background bonuses first
        background = self.creator.backgrounds[self.character_data['background']]
        for skill_category, bonus in background.skill_bonuses.items():
            skills[skill_category.value] += bonus
        
        print(f"\nSkill Allocation - {remaining_points} points remaining")
        print("Skills start at level 1. Maximum level is 10.")
        print("-" * 50)
        
        while remaining_points > 0:
            # Display current skills
            print("\nCurrent Skills:")
            for skill_name, level in skills.items():
                print(f"  {skill_name.title():12}: {level}/10")
            
            print(f"\nPoints remaining: {remaining_points}")
            
            # Get skill to increase
            skill_names = list(skills.keys())
            print("\nSkills to increase:")
            for i, skill_name in enumerate(skill_names, 1):
                current_level = skills[skill_name]
                if current_level < 10:
                    print(f"{i:2d}. {skill_name.title()} (currently {current_level})")
            
            try:
                choice = int(input(f"\nSelect skill to increase (1-{len(skill_names)}) or 0 to finish: "))
                
                if choice == 0:
                    break
                elif 1 <= choice <= len(skill_names):
                    skill_name = skill_names[choice - 1]
                    current_level = skills[skill_name]
                    
                    if current_level >= 10:
                        print(f"{skill_name.title()} is already at maximum level!")
                        continue
                    
                    # Get number of points to invest
                    max_invest = min(remaining_points, 10 - current_level)
                    if max_invest == 1:
                        points_to_invest = 1
                    else:
                        points_input = input(f"How many points to invest in {skill_name.title()}? (1-{max_invest}): ")
                        try:
                            points_to_invest = int(points_input)
                            if not (1 <= points_to_invest <= max_invest):
                                print(f"Please enter a number between 1 and {max_invest}")
                                continue
                        except ValueError:
                            print("Please enter a valid number")
                            continue
                    
                    skills[skill_name] += points_to_invest
                    remaining_points -= points_to_invest
                    
                    if remaining_points == 0:
                        print("\nAll points allocated!")
                        break
                else:
                    print(f"Please enter a number between 0 and {len(skill_names)}")
            except ValueError:
                print("Please enter a valid number")
        
        return skills
    
    def review_character(self) -> bool:
        """Review character and confirm creation"""
        print("\n" + "=" * 60)
        print("CHARACTER REVIEW")
        print("=" * 60)
        
        # Display character summary
        if self.current_character:
            print(self.current_character.get_character_summary())
        
        print("\n" + "=" * 60)
        
        while True:
            choice = input("\nAccept this character? (y/n): ").lower().strip()
            if choice in ['y', 'yes']:
                return True
            elif choice in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' or 'n'")
    
    def create_character_from_data(self) -> Character:
        """Create character from collected data"""
        return self.creator.create_character(
            name=self.character_data['name'],
            background_type=self.character_data['background'],
            primary_trait=self.character_data['primary_trait'],
            secondary_trait=self.character_data['secondary_trait'],
            skill_points=20,
            has_trauma=True
        )
    
    def run_character_creation(self) -> Optional[Character]:
        """Run the complete character creation process"""
        self.clear_screen()
        self.print_banner()
        
        while self.current_step < len(self.creation_steps):
            step = self.creation_steps[self.current_step]
            self.print_progress()
            
            if step == "name":
                name = self.get_name_input()
                self.character_data['name'] = name
                self.current_step += 1
                
            elif step == "background":
                background = self.select_background()
                self.character_data['background'] = background
                self.current_step += 1
                
            elif step == "primary_trait":
                primary_trait = self.select_trait("primary")
                self.character_data['primary_trait'] = primary_trait
                self.current_step += 1
                
            elif step == "secondary_trait":
                secondary_trait = self.select_trait("secondary", self.character_data['primary_trait'])
                self.character_data['secondary_trait'] = secondary_trait
                self.current_step += 1
                
            elif step == "skills":
                # Create temporary character to get background bonuses
                temp_character = self.create_character_from_data()
                print(f"\nBackground: {temp_character.background.name}")
                print(f"Background skill bonuses applied automatically.")
                
                # Note: In a full implementation, you'd want to allow manual skill allocation
                # For now, we'll use the automatic allocation
                self.current_step += 1
                
            elif step == "review":
                # Create the final character
                self.current_character = self.create_character_from_data()
                
                if self.review_character():
                    print(f"\n🎉 Character '{self.current_character.name}' created successfully!")
                    return self.current_character
                else:
                    # Go back to name step to restart
                    self.current_step = 0
                    self.character_data = {}
                    self.current_character = None
                    self.clear_screen()
                    self.print_banner()
                    continue
        
        return None
    
    def quick_create_character(self, name: str = None) -> Character:
        """Quick character creation with random choices"""
        print("Creating random character...")
        return self.creator.create_random_character(name)


class CharacterManagementUI:
    """Character management interface for existing characters"""
    
    def __init__(self):
        self.characters = []
    
    def add_character(self, character: Character):
        """Add a character to the roster"""
        self.characters.append(character)
    
    def list_characters(self):
        """List all characters"""
        if not self.characters:
            print("\nNo characters created yet.")
            return
        
        print(f"\nCharacter Roster ({len(self.characters)} characters):")
        print("-" * 50)
        
        for i, character in enumerate(self.characters, 1):
            print(f"{i:2d}. {character.name:15} - {character.background.name:12} - {character.traits.primary_trait.value.replace('_', ' ').title()}")
    
    def view_character(self, character_index: int):
        """View detailed character information"""
        if 0 <= character_index < len(self.characters):
            character = self.characters[character_index]
            print(character.get_character_summary())
        else:
            print("Invalid character index")
    
    def select_character(self) -> Optional[Character]:
        """Select a character from the roster"""
        if not self.characters:
            print("\nNo characters available.")
            return None
        
        self.list_characters()
        
        while True:
            try:
                choice = int(input(f"\nSelect character (1-{len(self.characters)}): "))
                if 1 <= choice <= len(self.characters):
                    return self.characters[choice - 1]
                else:
                    print(f"Please enter a number between 1 and {len(self.characters)}")
            except ValueError:
                print("Please enter a valid number")


def integrate_with_main_menu():
    """Integration function for the main game menu"""
    def character_creation_menu():
        """Character creation submenu"""
        ui = CharacterCreationUI()
        
        while True:
            print("\n" + "=" * 50)
            print("CHARACTER CREATION")
            print("=" * 50)
            print("1. Create New Character")
            print("2. Quick Random Character")
            print("3. Back to Main Menu")
            
            choice = input("\nEnter choice: ").strip()
            
            if choice == "1":
                character = ui.run_character_creation()
                if character:
                    print(f"\nCharacter '{character.name}' created and added to roster!")
                    return character
            elif choice == "2":
                name = input("Enter character name (or press Enter for random): ").strip()
                if not name:
                    name = None
                character = ui.quick_create_character(name)
                print(f"\nRandom character '{character.name}' created!")
                print(character.get_character_summary())
                return character
            elif choice == "3":
                return None
            else:
                print("Invalid choice. Please try again.")
    
    return character_creation_menu


if __name__ == "__main__":
    # Test the character creation system
    print("Testing Character Creation UI")
    print("=" * 50)
    
    # Test quick creation
    ui = CharacterCreationUI()
    character = ui.quick_create_character("Test Character")
    print(character.get_character_summary())
    
    # Test management
    mgmt = CharacterManagementUI()
    mgmt.add_character(character)
    mgmt.list_characters() 