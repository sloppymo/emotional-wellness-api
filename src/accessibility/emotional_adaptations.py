"""
Emotional Wellness Accessibility Adaptations

This module provides specialized accessibility adaptations for emotional wellness content,
integrating with the symbolic processing system to provide appropriate adaptations
for users with different disabilities.
"""

from typing import Dict, List, Optional, Any
import logging

from src.accessibility.config import DisabilityType, AdaptationType
from src.accessibility.preferences import UserPreferences

logger = logging.getLogger(__name__)


class EmotionalSymbolAdapter:
    """
    Adapter for making emotional symbolic content accessible to users with different needs.
    
    This class provides specialized adaptations for the symbolic emotional content
    used throughout the Emotional Wellness API.
    """
    
    def __init__(self, preferences: UserPreferences):
        """
        Initialize the adapter with user preferences.
        
        Args:
            preferences: User's accessibility preferences
        """
        self.preferences = preferences
    
    def adapt_symbolic_pattern(self, pattern: str) -> Dict:
        """
        Adapt a symbolic pattern for accessibility.
        
        Args:
            pattern: Symbolic pattern (e.g., "Water→Fire→Mountain→Star")
            
        Returns:
            Dictionary with adapted representations of the pattern
        """
        result = {
            "original_pattern": pattern,
            "accessible_versions": {}
        }
        
        # Check for vision disabilities
        if DisabilityType.VISION in self.preferences.disabilities:
            result["accessible_versions"]["descriptive"] = self._create_descriptive_version(pattern)
            
        # Check for cognitive disabilities
        if DisabilityType.COGNITIVE in self.preferences.disabilities:
            result["accessible_versions"]["simplified"] = self._create_simplified_version(pattern)
            
        # Check for sensory sensitivities
        if DisabilityType.SENSORY in self.preferences.disabilities:
            result["accessible_versions"]["low_sensory"] = self._create_low_sensory_version(pattern)
            
        # Add emotional cues if needed
        if self.preferences.use_symbols or DisabilityType.LEARNING in self.preferences.disabilities:
            result["accessible_versions"]["emotional_cues"] = self._add_emotional_cues(pattern)
            
        return result
    
    def adapt_archetype(self, archetype: str) -> Dict:
        """
        Adapt an archetype for accessibility.
        
        Args:
            archetype: Archetype name (e.g., "Hero's Journey")
            
        Returns:
            Dictionary with adapted representations of the archetype
        """
        result = {
            "original_archetype": archetype,
            "accessible_versions": {}
        }
        
        # Add concrete explanation for cognitive disabilities
        if DisabilityType.COGNITIVE in self.preferences.disabilities:
            result["accessible_versions"]["concrete_explanation"] = self._get_concrete_archetype_explanation(archetype)
            
        # Add emotional cues
        if self.preferences.use_symbols or DisabilityType.LEARNING in self.preferences.disabilities:
            result["accessible_versions"]["emotional_meaning"] = self._get_archetype_emotional_meaning(archetype)
            
        return result
    
    def adapt_crisis_notification(self, notification: Dict) -> Dict:
        """
        Adapt a crisis notification for accessibility.
        
        Args:
            notification: Crisis notification data
            
        Returns:
            Adapted crisis notification
        """
        adapted = notification.copy()
        
        # Determine appropriate adaptation based on user preferences
        if self.preferences.crisis_alert_mode == "visual":
            adapted["presentation_mode"] = "visual"
            adapted["use_high_contrast"] = self.preferences.high_contrast_mode
            adapted["use_large_text"] = self.preferences.large_text_mode
            
        elif self.preferences.crisis_alert_mode == "audio":
            adapted["presentation_mode"] = "audio"
            adapted["include_text_transcript"] = True
            
        else:  # multi-modal is the default
            adapted["presentation_mode"] = "multi_modal"
            adapted["include_text"] = True
            adapted["include_audio"] = True
            adapted["include_symbols"] = self.preferences.use_symbols
            
        # Add simplified explanation for cognitive disabilities
        if DisabilityType.COGNITIVE in self.preferences.disabilities:
            adapted["simplified_explanation"] = self._create_simplified_crisis_explanation(notification)
            
        # Reduce sensory load if needed
        if self.preferences.reduce_sensory_load:
            adapted["reduced_sensory_load"] = True
            adapted["use_gentle_notifications"] = True
            
        return adapted
    
    def adapt_emotional_weather(self, weather_report: Dict) -> Dict:
        """
        Adapt an emotional weather report for accessibility.
        
        Args:
            weather_report: Emotional weather report data
            
        Returns:
            Adapted emotional weather report
        """
        adapted = weather_report.copy()
        
        # Adapt metaphor usage based on preferences
        if self.preferences.metaphor_usage == "reduced":
            # Replace metaphorical weather with more direct descriptions
            adapted["report_style"] = "direct"
            adapted["weather_metaphors_removed"] = True
            
        elif self.preferences.metaphor_usage == "concrete":
            # Keep metaphors but add concrete explanations
            adapted["report_style"] = "concrete_metaphors"
            adapted["includes_explanations"] = True
            
        # Add symbols if preferred
        if self.preferences.use_symbols:
            adapted["includes_symbols"] = True
            
        # Simplify language if needed
        if self.preferences.language_complexity < 5:
            adapted["language_level"] = "simplified"
            
        return adapted
    
    def _create_descriptive_version(self, pattern: str) -> str:
        """
        Create a descriptive version of a symbolic pattern for vision impaired users.
        
        Args:
            pattern: Symbolic pattern
            
        Returns:
            Descriptive version
        """
        # Replace arrow with "followed by" for screen readers
        descriptive = pattern.replace("→", " followed by ")
        return f"Symbolic pattern: {descriptive}"
    
    def _create_simplified_version(self, pattern: str) -> str:
        """
        Create a simplified version of a symbolic pattern.
        
        Args:
            pattern: Symbolic pattern
            
        Returns:
            Simplified version
        """
        # Count symbols
        symbols = pattern.split("→")
        
        # Create simplified description
        return f"A {len(symbols)}-part pattern: {', '.join(symbols)}"
    
    def _create_low_sensory_version(self, pattern: str) -> str:
        """
        Create a low-sensory version of a symbolic pattern.
        
        Args:
            pattern: Symbolic pattern
            
        Returns:
            Low-sensory version
        """
        # For sensory sensitivities, provide a gentler description
        symbols = pattern.split("→")
        return f"Gentle transition between {len(symbols)} elements"
    
    def _add_emotional_cues(self, pattern: str) -> Dict:
        """
        Add emotional cues to a symbolic pattern.
        
        Args:
            pattern: Symbolic pattern
            
        Returns:
            Pattern with emotional cues
        """
        # This would use the symbolic system to interpret emotional meaning
        # Placeholder implementation
        symbols = pattern.split("→")
        
        return {
            "pattern": pattern,
            "emotional_tone": "transformative" if "Water" in symbols and "Fire" in symbols else "stable",
            "intensity": "moderate",
            "common_feeling": "This pattern often represents personal growth through challenge"
        }
    
    def _get_concrete_archetype_explanation(self, archetype: str) -> str:
        """
        Get a concrete explanation of an archetype.
        
        Args:
            archetype: Archetype name
            
        Returns:
            Concrete explanation
        """
        # Placeholder implementation with a few examples
        explanations = {
            "Hero's Journey": "A pattern where someone faces a challenge, overcomes it, and grows stronger",
            "Shadow": "The parts of ourselves we don't want to see or acknowledge",
            "Caregiver": "Someone who helps and protects others",
            "Trickster": "Someone who breaks rules and challenges normal ways of thinking"
        }
        
        return explanations.get(archetype, f"A pattern of emotions and behaviors called '{archetype}'")
    
    def _get_archetype_emotional_meaning(self, archetype: str) -> Dict:
        """
        Get the emotional meaning of an archetype.
        
        Args:
            archetype: Archetype name
            
        Returns:
            Emotional meaning
        """
        # Placeholder implementation
        meanings = {
            "Hero's Journey": {
                "primary_emotions": ["courage", "determination", "growth"],
                "common_experience": "Overcoming a difficult challenge"
            },
            "Shadow": {
                "primary_emotions": ["fear", "shame", "hidden strength"],
                "common_experience": "Facing parts of yourself you find difficult"
            },
            "Caregiver": {
                "primary_emotions": ["compassion", "responsibility", "concern"],
                "common_experience": "Taking care of others' needs"
            }
        }
        
        return meanings.get(archetype, {
            "primary_emotions": ["various"],
            "common_experience": f"Experiences related to the {archetype} pattern"
        })
    
    def _create_simplified_crisis_explanation(self, notification: Dict) -> str:
        """
        Create a simplified explanation of a crisis notification.
        
        Args:
            notification: Crisis notification data
            
        Returns:
            Simplified explanation
        """
        # Extract relevant information
        level = notification.get("level", 0)
        pattern = notification.get("symbolic_pattern", "")
        
        # Create simple explanation based on level
        if level == 3:
            return "This is an urgent alert that needs immediate attention."
        elif level == 2:
            return "This is an important alert that needs attention soon."
        else:
            return "This is an alert that someone may need help."


class TherapistCommunicationAdapter:
    """
    Adapter for making therapist communications accessible.
    
    This class provides adaptations for communications between
    therapists and users with different accessibility needs.
    """
    
    def __init__(self, preferences: UserPreferences):
        """
        Initialize the adapter with user preferences.
        
        Args:
            preferences: User's accessibility preferences
        """
        self.preferences = preferences
    
    def adapt_therapist_message(self, message: Dict) -> Dict:
        """
        Adapt a therapist message for accessibility.
        
        Args:
            message: Therapist message data
            
        Returns:
            Adapted therapist message
        """
        adapted = message.copy()
        
        # Apply adaptations based on communication format preference
        format_pref = self.preferences.therapist_communication_format
        
        if format_pref == "simplified":
            adapted["content"] = self._simplify_message(message.get("content", ""))
            adapted["format"] = "simplified"
            
        elif format_pref == "symbol_enhanced":
            adapted["content"] = message.get("content", "")
            adapted["symbols"] = self._add_symbols_to_message(message.get("content", ""))
            adapted["format"] = "symbol_enhanced"
            
        elif format_pref == "multi_modal":
            adapted["content"] = message.get("content", "")
            adapted["audio_version"] = True
            adapted["symbol_version"] = True
            adapted["format"] = "multi_modal"
            
        # Add emotional cues if needed
        if DisabilityType.COGNITIVE in self.preferences.disabilities or \
           DisabilityType.LEARNING in self.preferences.disabilities:
            adapted["emotional_cues"] = self._extract_emotional_cues(message.get("content", ""))
            
        return adapted
    
    def _simplify_message(self, content: str) -> str:
        """
        Simplify a therapist message.
        
        Args:
            content: Message content
            
        Returns:
            Simplified message
        """
        # Placeholder implementation
        # In production, this would use NLP techniques
        return f"{content}\n\n[Simplified version available]"
    
    def _add_symbols_to_message(self, content: str) -> List[Dict]:
        """
        Add symbols to a therapist message.
        
        Args:
            content: Message content
            
        Returns:
            List of symbols to include
        """
        # Placeholder implementation
        # In production, this would analyze the message and select appropriate symbols
        return [
            {"position": "start", "symbol": "communication", "meaning": "Message from therapist"},
            {"position": "end", "symbol": "response_requested", "meaning": "Please respond when ready"}
        ]
    
    def _extract_emotional_cues(self, content: str) -> Dict:
        """
        Extract emotional cues from a message.
        
        Args:
            content: Message content
            
        Returns:
            Emotional cues
        """
        # Placeholder implementation
        # In production, this would use sentiment analysis
        return {
            "primary_tone": "supportive",
            "emotional_intent": "to provide guidance and support",
            "response_expectation": "sharing your thoughts when ready"
        }
