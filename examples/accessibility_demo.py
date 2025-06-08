#!/usr/bin/env python3
"""
Accessibility Features Demo for Emotional Wellness API

This script demonstrates how to use the accessibility features
to adapt content for differently abled users.
"""

import asyncio
import json
import sys
import os
from typing import Dict, List

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.accessibility.config import (
    DisabilityType, AdaptationType, AccessibilityLevel,
    get_adaptations_for_disabilities
)
from src.accessibility.preferences import UserPreferences, preference_store
from src.accessibility.adapters import get_accessibility_adapter
from src.accessibility.emotional_adaptations import (
    EmotionalSymbolAdapter, TherapistCommunicationAdapter
)


async def demo_text_simplification():
    """Demonstrate text simplification adaptation."""
    print("\n🔄 Demonstrating Text Simplification Adaptation")
    print("=" * 60)
    
    # Sample complex text
    complex_text = (
        "The symbolic manifestation of the Hero's Journey archetype represents "
        "a profound transformation of consciousness through trials and tribulations, "
        "ultimately leading to psychological integration and transcendence of "
        "previously limiting belief structures."
    )
    
    print(f"Original Text:\n{complex_text}\n")
    
    # Create preferences with different complexity levels
    for complexity in [2, 5, 8]:
        preferences = UserPreferences(
            user_id="demo_user",
            enabled=True,
            language_complexity=complexity
        )
        
        # Get adapter and adapt content
        adapter = get_accessibility_adapter(preferences)
        adapted = adapter.adapt_content(complex_text, [AdaptationType.TEXT_SIMPLIFICATION])
        
        print(f"Adapted for Complexity Level {complexity}:")
        if isinstance(adapted, dict) and "text" in adapted:
            print(adapted["text"])
        else:
            print(adapted)
        print()


async def demo_emotional_cues():
    """Demonstrate emotional cues adaptation."""
    print("\n🔄 Demonstrating Emotional Cues Adaptation")
    print("=" * 60)
    
    # Sample messages with different emotional tones
    messages = [
        "We need to discuss your recent crisis episode immediately.",
        "I'm happy to see your progress in the latest session.",
        "The pattern analysis shows concerning trends in your responses."
    ]
    
    # Create preferences for a user who benefits from emotional cues
    preferences = UserPreferences(
        user_id="demo_user",
        enabled=True,
        disabilities=[DisabilityType.COGNITIVE],
        preferred_adaptations=[AdaptationType.EMOTIONAL_CUES]
    )
    
    # Get adapter
    adapter = get_accessibility_adapter(preferences)
    
    # Adapt each message
    for message in messages:
        print(f"Original Message:\n{message}\n")
        
        adapted = adapter.adapt_content(message, [AdaptationType.EMOTIONAL_CUES])
        
        print("With Emotional Cues:")
        print(json.dumps(adapted, indent=2))
        print()


async def demo_symbolic_pattern_adaptation():
    """Demonstrate symbolic pattern adaptation for different disabilities."""
    print("\n🔄 Demonstrating Symbolic Pattern Adaptation")
    print("=" * 60)
    
    # Sample symbolic pattern
    pattern = "Water→Fire→Mountain→Star"
    print(f"Original Symbolic Pattern: {pattern}\n")
    
    # Create adapters for different disability types
    disability_types = [
        DisabilityType.VISION,
        DisabilityType.COGNITIVE,
        DisabilityType.SENSORY,
        DisabilityType.LEARNING
    ]
    
    for disability in disability_types:
        # Create preferences
        preferences = UserPreferences(
            user_id="demo_user",
            enabled=True,
            disabilities=[disability],
            use_symbols=disability == DisabilityType.LEARNING
        )
        
        # Create adapter
        adapter = EmotionalSymbolAdapter(preferences)
        
        # Adapt pattern
        adapted = adapter.adapt_symbolic_pattern(pattern)
        
        print(f"Adapted for {disability.value.title()} Disability:")
        print(json.dumps(adapted, indent=2))
        print()


async def demo_crisis_notification_adaptation():
    """Demonstrate crisis notification adaptation."""
    print("\n🔄 Demonstrating Crisis Notification Adaptation")
    print("=" * 60)
    
    # Sample crisis notification
    notification = {
        "type": "crisis_notification",
        "level": 2,
        "symbolic_pattern": "Shadow→Abyss→Light",
        "urgency": "high",
        "timestamp": "2025-06-06T19:15:00Z"
    }
    
    print("Original Crisis Notification:")
    print(json.dumps(notification, indent=2))
    print()
    
    # Create preferences for different presentation modes
    modes = ["visual", "audio", "multi_modal"]
    
    for mode in modes:
        # Create preferences
        preferences = UserPreferences(
            user_id="demo_user",
            enabled=True,
            crisis_alert_mode=mode,
            disabilities=[DisabilityType.COGNITIVE] if mode == "visual" else [],
            reduce_sensory_load=mode == "audio"
        )
        
        # Create adapter
        adapter = EmotionalSymbolAdapter(preferences)
        
        # Adapt notification
        adapted = adapter.adapt_crisis_notification(notification)
        
        print(f"Adapted for {mode.replace('_', ' ').title()} Mode:")
        print(json.dumps(adapted, indent=2))
        print()


async def demo_therapist_communication():
    """Demonstrate therapist communication adaptation."""
    print("\n🔄 Demonstrating Therapist Communication Adaptation")
    print("=" * 60)
    
    # Sample therapist message
    message = {
        "type": "therapist_message",
        "therapist_id": "T12345",
        "content": (
            "I've noticed a recurring pattern in your symbolic responses "
            "that suggests an emerging Hero's Journey archetype. This could "
            "indicate you're entering a transformative phase. Let's discuss "
            "this in our next session to explore its significance."
        ),
        "timestamp": "2025-06-06T18:30:00Z"
    }
    
    print("Original Therapist Message:")
    print(json.dumps(message, indent=2))
    print()
    
    # Create preferences for different communication formats
    formats = ["simplified", "symbol_enhanced", "multi_modal"]
    
    for format_pref in formats:
        # Create preferences
        preferences = UserPreferences(
            user_id="demo_user",
            enabled=True,
            therapist_communication_format=format_pref,
            disabilities=[DisabilityType.COGNITIVE] if format_pref == "simplified" else []
        )
        
        # Create adapter
        adapter = TherapistCommunicationAdapter(preferences)
        
        # Adapt message
        adapted = adapter.adapt_therapist_message(message)
        
        print(f"Adapted for {format_pref.replace('_', ' ').title()} Format:")
        print(json.dumps(adapted, indent=2))
        print()


async def demo_recommended_adaptations():
    """Demonstrate getting recommended adaptations for disabilities."""
    print("\n🔄 Demonstrating Recommended Adaptations")
    print("=" * 60)
    
    # Sample disability combinations
    disability_sets = [
        {DisabilityType.VISION},
        {DisabilityType.COGNITIVE, DisabilityType.LEARNING},
        {DisabilityType.SENSORY, DisabilityType.NEURODIVERSITY},
        {DisabilityType.MOTOR, DisabilityType.SPEECH}
    ]
    
    for disabilities in disability_sets:
        # Get recommended adaptations
        adaptations = get_adaptations_for_disabilities(disabilities)
        
        print(f"Recommended Adaptations for {', '.join(d.value.title() for d in disabilities)}:")
        for adaptation in adaptations:
            print(f"- {adaptation.value.replace('_', ' ').title()}")
        print()


async def main():
    """Run all demonstrations."""
    print("\n🚀 Emotional Wellness API - Accessibility Features Demo")
    print("=" * 60)
    
    # Run demos
    await demo_text_simplification()
    await demo_emotional_cues()
    await demo_symbolic_pattern_adaptation()
    await demo_crisis_notification_adaptation()
    await demo_therapist_communication()
    await demo_recommended_adaptations()
    
    print("\n✅ Accessibility Features Demo Completed")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
