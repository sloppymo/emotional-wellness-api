#!/usr/bin/env python3
"""
Test script for the Years of Lead Character Creation System

This script demonstrates the comprehensive character creation system
with detailed backgrounds, skills, traits, and emotional profiles.
"""

import sys
import os
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from game.character_creation import (
    CharacterCreator, create_random_character, 
    BackgroundType, PersonalityTrait, SkillCategory
)
from game.character_creation_ui import CharacterCreationUI, CharacterManagementUI


def test_character_creation():
    """Test the character creation system"""
    print("🧪 Testing Years of Lead Character Creation System")
    print("=" * 60)
    
    # Test 1: Create a random character
    print("\n1️⃣ Creating a random character...")
    random_char = create_random_character("Alex")
    print(random_char.get_character_summary())
    
    # Test 2: Create character with specific parameters
    print("\n2️⃣ Creating a character with specific parameters...")
    creator = CharacterCreator()
    specific_char = creator.create_character(
        name="Jordan",
        background_type=BackgroundType.MILITARY,
        primary_trait=PersonalityTrait.LOYAL,
        secondary_trait=PersonalityTrait.PRAGMATIC
    )
    print(specific_char.get_character_summary())
    
    # Test 3: Test character management
    print("\n3️⃣ Testing character management...")
    mgmt = CharacterManagementUI()
    mgmt.add_character(random_char)
    mgmt.add_character(specific_char)
    mgmt.list_characters()
    
    # Test 4: Test serialization
    print("\n4️⃣ Testing character serialization...")
    serialized = random_char.serialize()
    deserialized = random_char.__class__.deserialize(serialized)
    print(f"Serialization test: {'✅ PASS' if deserialized.name == random_char.name else '❌ FAIL'}")
    
    # Test 5: Test all backgrounds
    print("\n5️⃣ Testing all available backgrounds...")
    for bg_type in BackgroundType:
        bg = creator.backgrounds[bg_type]
        print(f"  • {bg.name:12} - {bg.description}")
    
    # Test 6: Test all personality traits
    print("\n6️⃣ Testing all personality traits...")
    for trait in PersonalityTrait:
        print(f"  • {trait.value.replace('_', ' ').title()}")
    
    print("\n✅ Character creation system tests completed!")
    return True


def test_character_stories():
    """Test character story generation"""
    print("\n📖 Testing Character Story Generation")
    print("=" * 50)
    
    # Create a few different characters
    characters = [
        create_random_character("Casey"),
        create_random_character("Riley"),
        create_random_character("Morgan")
    ]
    
    for i, character in enumerate(characters, 1):
        print(f"\nCharacter {i}: {character.name}")
        print("-" * 30)
        print(character.get_character_story())
        print()
    
    return True


def test_skill_system():
    """Test the skill system"""
    print("\n⚔️ Testing Skill System")
    print("=" * 30)
    
    creator = CharacterCreator()
    
    # Test different backgrounds and their skill bonuses
    for bg_type in [BackgroundType.MILITARY, BackgroundType.TECHNICAL, BackgroundType.MEDICAL]:
        char = creator.create_character(
            name=f"Test_{bg_type.value}",
            background_type=bg_type,
            primary_trait=PersonalityTrait.ANALYTICAL,
            secondary_trait=PersonalityTrait.METHODICAL
        )
        
        print(f"\n{char.background.name} Background:")
        print(f"  Combat: {char.skills.combat}")
        print(f"  Stealth: {char.skills.stealth}")
        print(f"  Hacking: {char.skills.hacking}")
        print(f"  Social: {char.skills.social}")
        print(f"  Technical: {char.skills.technical}")
        print(f"  Medical: {char.skills.medical}")
        print(f"  Survival: {char.skills.survival}")
        print(f"  Intelligence: {char.skills.intelligence}")
    
    return True


def test_emotional_system():
    """Test the emotional system integration"""
    print("\n😊 Testing Emotional System Integration")
    print("=" * 40)
    
    # Create characters with different traits and see how they affect emotions
    test_cases = [
        (PersonalityTrait.OPTIMISTIC, PersonalityTrait.COMPASSIONATE),
        (PersonalityTrait.PESSIMISTIC, PersonalityTrait.RUTHLESS),
        (PersonalityTrait.LOYAL, PersonalityTrait.IDEALISTIC)
    ]
    
    for primary, secondary in test_cases:
        char = create_random_character(f"Test_{primary.value}")
        char.traits.primary_trait = primary
        char.traits.secondary_trait = secondary
        
        print(f"\n{char.name} - {primary.value.replace('_', ' ').title()} & {secondary.value.replace('_', ' ').title()}:")
        print(f"  Trust: {char.emotional_state.trust:.2f}")
        print(f"  Anticipation: {char.emotional_state.anticipation:.2f}")
        print(f"  Joy: {char.emotional_state.joy:.2f}")
        print(f"  Anger: {char.emotional_state.anger:.2f}")
        print(f"  Fear: {char.emotional_state.fear:.2f}")
    
    return True


def test_trauma_system():
    """Test the trauma system"""
    print("\n💔 Testing Trauma System")
    print("=" * 30)
    
    creator = CharacterCreator()
    
    # Create a character with trauma
    char = creator.create_character(
        name="Trauma_Test",
        background_type=BackgroundType.MILITARY,
        primary_trait=PersonalityTrait.LOYAL,
        secondary_trait=PersonalityTrait.CAUTIOUS,
        has_trauma=True
    )
    
    if char.trauma:
        print(f"Character: {char.name}")
        print(f"Trauma Type: {char.trauma.type.value.replace('_', ' ').title()}")
        print(f"Severity: {char.trauma.severity:.1%}")
        print(f"Description: {char.trauma.description}")
        print(f"Triggers: {', '.join(char.trauma.triggers)}")
        print(f"Emotional Impact: {char.trauma.emotional_impact}")
        print(f"Trauma Story: {char.trauma.get_trauma_story(char.name)}")
    else:
        print("No trauma generated for this character")
    
    return True


def main():
    """Run all character creation tests"""
    print("🎮 YEARS OF LEAD - CHARACTER CREATION SYSTEM TEST")
    print("=" * 60)
    
    tests = [
        ("Basic Character Creation", test_character_creation),
        ("Character Stories", test_character_stories),
        ("Skill System", test_skill_system),
        ("Emotional System", test_emotional_system),
        ("Trauma System", test_trauma_system)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running: {test_name}")
            print("-" * 40)
            result = test_func()
            results.append((test_name, True))
            print(f"✅ {test_name} - PASSED")
        except Exception as e:
            print(f"❌ {test_name} - FAILED: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:25} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All character creation system tests passed!")
        print("The system is ready for integration with the main game.")
    else:
        print(f"\n⚠️  {total-passed} tests failed. Please check the implementation.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 