"""
Years of Lead - Emotional State System

This module implements the emotional state mechanics for agents,
tracking how traumatic events and experiences affect their psychological well-being.
Based on Plutchik's Wheel of Emotions with trauma persistence modeling.
"""

import math
import random
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from copy import deepcopy


@dataclass
class EmotionalState:
    """
    Represents an agent's emotional state using Plutchik's 8 basic emotions.
    All values are normalized between -1.0 and 1.0.
    """
    fear: float = 0.0           # Fear of danger, government, discovery
    anger: float = 0.0          # Anger at injustice, system, betrayal  
    sadness: float = 0.0        # Grief, loss, despair
    joy: float = 0.0            # Hope, satisfaction, triumph
    trust: float = 0.0          # Faith in cause, comrades, leadership
    anticipation: float = 0.0   # Expectation, planning, future focus
    surprise: float = 0.0       # Shock, unexpected events
    disgust: float = 0.0        # Revulsion at system, betrayal, corruption
    
    # Trauma tracking
    trauma_level: float = 0.0   # Overall accumulated trauma (0.0 to 1.0)
    last_trauma_intensity: float = 0.0  # Intensity of most recent trauma
    trauma_decay_rate: float = 0.02     # How quickly trauma fades
    
    def __post_init__(self):
        """Ensure all emotional values are within bounds after initialization"""
        self._clamp_values()
    
    def _clamp_values(self):
        """Ensure all emotional values stay within -1.0 to 1.0 bounds"""
        emotions = ['fear', 'anger', 'sadness', 'joy', 'trust', 'anticipation', 'surprise', 'disgust']
        for emotion in emotions:
            value = getattr(self, emotion)
            setattr(self, emotion, max(-1.0, min(1.0, float(value))))
        
        # Clamp trauma values
        self.trauma_level = max(0.0, min(1.0, self.trauma_level))
        self.last_trauma_intensity = max(0.0, min(1.0, self.last_trauma_intensity))
    
    def copy(self):
        """Create a deep copy of this emotional state"""
        return deepcopy(self)
    
    def apply_drift(self, time_delta: float = 1.0):
        """
        Apply natural emotional drift over time.
        Emotions gradually return toward neutral unless reinforced.
        """
        drift_rate = 0.05 * time_delta  # Base drift rate per time unit
        
        # Emotions drift toward zero (neutral) unless trauma is high
        trauma_resistance = 1.0 - (self.trauma_level * 0.5)  # High trauma slows positive drift
        
        emotions = ['fear', 'anger', 'sadness', 'joy', 'trust', 'anticipation', 'surprise', 'disgust']
        
        for emotion in emotions:
            current_value = getattr(self, emotion)
            
            if current_value > 0:
                # Positive emotions drift down
                drift_amount = min(current_value, drift_rate * trauma_resistance)
                new_value = current_value - drift_amount
            elif current_value < 0:
                # Negative emotions also drift toward neutral, but slower if trauma is high
                if emotion in ['fear', 'sadness'] and self.trauma_level > 0.3:
                    # Fear and sadness persist longer when traumatized
                    effective_drift = drift_rate * trauma_resistance * 0.5
                else:
                    effective_drift = drift_rate * trauma_resistance
                
                drift_amount = min(abs(current_value), effective_drift)
                new_value = current_value + drift_amount
            else:
                new_value = current_value
            
            setattr(self, emotion, new_value)
        
        # Gradually reduce trauma over time
        if self.trauma_level > 0:
            self.trauma_level = max(0.0, self.trauma_level - self.trauma_decay_rate * time_delta)
        
        self._clamp_values()
    
    def apply_emotional_impact(self, impact: Dict[str, float], intensity: float = 1.0):
        """
        Apply an emotional impact from an event.
        
        Args:
            impact: Dictionary mapping emotion names to impact values
            intensity: Multiplier for the impact strength (0.0 to 1.0)
        """
        intensity = max(0.0, min(1.0, intensity))
        
        for emotion, value in impact.items():
            if hasattr(self, emotion):
                current_value = getattr(self, emotion)
                impact_value = value * intensity
                
                # Apply diminishing returns for extreme values
                if abs(current_value) > 0.7:
                    impact_value *= 0.5
                
                new_value = current_value + impact_value
                setattr(self, emotion, new_value)
        
        self._clamp_values()
    
    def apply_trauma(self, trauma_intensity: float, event_type: str = "general"):
        """
        Apply traumatic impact with persistent effects.
        
        Args:
            trauma_intensity: How traumatic the event was (0.0 to 1.0)
            event_type: Type of traumatic event for specialized handling
        """
        trauma_intensity = max(0.0, min(1.0, trauma_intensity))
        
        # Update trauma tracking
        self.last_trauma_intensity = trauma_intensity
        self.trauma_level = min(1.0, self.trauma_level + trauma_intensity * 0.3)
        
        # Base trauma impacts
        trauma_impact = {
            'fear': trauma_intensity * 0.8,
            'sadness': trauma_intensity * 0.6,
            'anger': trauma_intensity * 0.4,
            'trust': -trauma_intensity * 0.5
        }
        
        # Event-specific trauma modifications
        if event_type == "violence_witnessed":
            trauma_impact['fear'] += trauma_intensity * 0.4
            trauma_impact['disgust'] = trauma_intensity * 0.3
        elif event_type == "betrayal":
            trauma_impact['trust'] -= trauma_intensity * 0.8
            trauma_impact['anger'] += trauma_intensity * 0.6
        elif event_type == "loss_of_comrade":
            trauma_impact['sadness'] += trauma_intensity * 0.7
            trauma_impact['anger'] += trauma_intensity * 0.3
        
        self.apply_emotional_impact(trauma_impact, intensity=1.0)
    
    def get_dominant_emotion(self) -> tuple[str, float]:
        """Get the currently dominant emotion and its intensity"""
        emotions = {
            'fear': self.fear,
            'anger': self.anger, 
            'sadness': self.sadness,
            'joy': self.joy,
            'trust': self.trust,
            'anticipation': self.anticipation,
            'surprise': self.surprise,
            'disgust': self.disgust
        }
        
        # Find emotion with highest absolute value
        dominant_emotion = max(emotions.items(), key=lambda x: abs(x[1]))
        return dominant_emotion
    
    def get_emotional_stability(self) -> float:
        """
        Calculate emotional stability (0.0 = very unstable, 1.0 = very stable).
        Based on how extreme the emotions are and trauma level.
        """
        emotions = [self.fear, self.anger, self.sadness, self.joy, 
                   self.trust, self.anticipation, self.surprise, self.disgust]
        
        # Calculate volatility (how extreme emotions are)
        volatility = sum(abs(emotion) for emotion in emotions) / len(emotions)
        
        # Factor in trauma level
        trauma_impact = self.trauma_level * 0.5
        
        # Stability is inverse of volatility and trauma
        stability = max(0.0, 1.0 - volatility - trauma_impact)
        return stability
    
    def get_combat_effectiveness(self) -> float:
        """
        Calculate how emotions affect combat effectiveness.
        Some emotions help, others hinder.
        """
        # Helpful emotions for combat
        helpful = self.anger * 0.3 + self.anticipation * 0.2
        
        # Hindering emotions
        hindering = self.fear * 0.4 + self.sadness * 0.3 + abs(self.surprise) * 0.2
        
        # Trauma reduces effectiveness
        trauma_penalty = self.trauma_level * 0.3
        
        effectiveness = max(0.0, min(1.0, 0.5 + helpful - hindering - trauma_penalty))
        return effectiveness
    
    def get_social_effectiveness(self) -> float:
        """
        Calculate how emotions affect social interactions and recruitment.
        """
        # Helpful emotions for social interactions
        helpful = self.trust * 0.4 + self.joy * 0.3 + self.anticipation * 0.2
        
        # Hindering emotions  
        hindering = self.fear * 0.2 + self.anger * 0.3 + self.sadness * 0.3 + self.disgust * 0.2
        
        # High trauma makes social interaction difficult
        trauma_penalty = self.trauma_level * 0.4
        
        effectiveness = max(0.0, min(1.0, 0.5 + helpful - hindering - trauma_penalty))
        return effectiveness
    
    def is_psychologically_stable(self) -> bool:
        """Check if the agent is psychologically stable enough to operate"""
        # Check for extreme emotional states
        emotions = [abs(self.fear), abs(self.anger), abs(self.sadness), 
                   abs(self.joy), abs(self.trust), abs(self.anticipation), 
                   abs(self.surprise), abs(self.disgust)]
        
        max_emotion = max(emotions)
        
        # Unstable if any emotion is too extreme or trauma is too high
        if max_emotion > 0.9 or self.trauma_level > 0.8:
            return False
        
        # Unstable if too many emotions are highly negative
        negative_count = sum(1 for emotion in [self.fear, self.anger, self.sadness, self.disgust] 
                           if emotion > 0.6)
        
        return negative_count < 3
    
    def serialize(self) -> Dict[str, Any]:
        """Serialize emotional state to dictionary"""
        return {
            'fear': self.fear,
            'anger': self.anger,
            'sadness': self.sadness, 
            'joy': self.joy,
            'trust': self.trust,
            'anticipation': self.anticipation,
            'surprise': self.surprise,
            'disgust': self.disgust,
            'trauma_level': self.trauma_level,
            'last_trauma_intensity': self.last_trauma_intensity,
            'trauma_decay_rate': self.trauma_decay_rate
        }
    
    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> 'EmotionalState':
        """Deserialize emotional state from dictionary"""
        return cls(**data)
    
    def __str__(self) -> str:
        """String representation of emotional state"""
        dominant, intensity = self.get_dominant_emotion()
        stability = self.get_emotional_stability()
        
        return (f"EmotionalState(dominant={dominant}:{intensity:.2f}, "
                f"stability={stability:.2f}, trauma={self.trauma_level:.2f})")


def create_random_emotional_state(trauma_range: tuple[float, float] = (0.0, 0.3)) -> EmotionalState:
    """
    Create a random emotional state within reasonable bounds.
    Useful for generating initial agent states.
    """
    state = EmotionalState()
    
    # Generate random but balanced emotions
    emotions = ['fear', 'anger', 'sadness', 'joy', 'trust', 'anticipation', 'surprise', 'disgust']
    
    for emotion in emotions:
        # Most emotions start near neutral with some variation
        value = random.gauss(0.0, 0.3)
        setattr(state, emotion, value)
    
    # Set random trauma level within specified range
    min_trauma, max_trauma = trauma_range
    state.trauma_level = random.uniform(min_trauma, max_trauma)
    
    state._clamp_values()
    return state 