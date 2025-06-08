"""
Accessibility Adapters Module

This module provides content adaptation mechanisms for different accessibility needs,
implementing various strategies to modify API responses for improved accessibility.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, Union
import json
import logging
from enum import Enum

from src.accessibility.config import AdaptationType, DisabilityType, accessibility_config
from src.accessibility.preferences import UserPreferences

logger = logging.getLogger(__name__)


class ContentAdapter(ABC):
    """Base abstract class for all content adapters."""
    
    @abstractmethod
    def adapt_content(self, content: Any, preferences: UserPreferences) -> Any:
        """
        Adapt content based on user accessibility preferences.
        
        Args:
            content: The content to adapt (could be text, dict, etc.)
            preferences: User's accessibility preferences
            
        Returns:
            Adapted content
        """
        pass


class TextSimplificationAdapter(ContentAdapter):
    """Adapter for simplifying text content."""
    
    def adapt_content(self, content: str, preferences: UserPreferences) -> str:
        """
        Simplify text based on user's language complexity preference.
        
        Args:
            content: Text content to simplify
            preferences: User's accessibility preferences
            
        Returns:
            Simplified text
        """
        if not isinstance(content, str):
            return content
            
        complexity = preferences.language_complexity
        
        # Apply different simplification strategies based on complexity level
        if complexity <= 3:  # Very simple language
            return self._simplify_text_basic(content)
        elif complexity <= 6:  # Moderately simple language
            return self._simplify_text_moderate(content)
        else:
            # For higher complexity preferences, return original content
            return content
    
    def _simplify_text_basic(self, text: str) -> str:
        """
        Apply basic text simplification (for lowest complexity levels).
        
        Args:
            text: Original text
            
        Returns:
            Simplified text
        """
        # This is a placeholder implementation
        # In production, this would use NLP techniques or external APIs
        
        # Example simplification logic:
        # 1. Break long sentences
        # 2. Replace complex words with simpler alternatives
        # 3. Use active voice
        # 4. Remove unnecessary clauses
        
        # For demonstration, we'll just add a note
        return f"{text}\n[Simplified to basic reading level]"
    
    def _simplify_text_moderate(self, text: str) -> str:
        """
        Apply moderate text simplification.
        
        Args:
            text: Original text
            
        Returns:
            Simplified text
        """
        # Placeholder implementation
        return f"{text}\n[Simplified to moderate reading level]"


class SymbolsAndPictogramsAdapter(ContentAdapter):
    """Adapter for adding symbols and pictograms to content."""
    
    def adapt_content(self, content: str, preferences: UserPreferences) -> Dict:
        """
        Add symbols and pictograms to text content.
        
        Args:
            content: Text content to enhance with symbols
            preferences: User's accessibility preferences
            
        Returns:
            Dictionary with original text and symbol-enhanced version
        """
        if not preferences.use_symbols or not isinstance(content, str):
            return {"text": content}
            
        # In a real implementation, this would:
        # 1. Identify key concepts in the text
        # 2. Match appropriate symbols/pictograms
        # 3. Create a multi-modal representation
        
        # Placeholder implementation
        return {
            "text": content,
            "symbols_version": f"[Symbol-enhanced version available]",
            "has_symbols": True
        }


class EmotionalCuesAdapter(ContentAdapter):
    """Adapter for enhancing content with emotional cues."""
    
    def adapt_content(self, content: Any, preferences: UserPreferences) -> Dict:
        """
        Add emotional cues to content for users who have difficulty
        interpreting emotional context.
        
        Args:
            content: Content to enhance with emotional cues
            preferences: User's accessibility preferences
            
        Returns:
            Content with emotional cues
        """
        if isinstance(content, str):
            # Extract emotional tone from content
            # This would use sentiment analysis in a real implementation
            emotional_tone = self._extract_emotional_tone(content)
            
            return {
                "content": content,
                "emotional_cues": {
                    "primary_tone": emotional_tone,
                    "intensity": "moderate",
                    "description": f"This message conveys {emotional_tone}"
                }
            }
        elif isinstance(content, dict):
            # For dictionaries, add emotional cues metadata
            content_copy = content.copy()
            
            if "message" in content and isinstance(content["message"], str):
                emotional_tone = self._extract_emotional_tone(content["message"])
                content_copy["emotional_cues"] = {
                    "primary_tone": emotional_tone,
                    "intensity": "moderate"
                }
                
            return content_copy
        else:
            # For other types, return as is
            return content
    
    def _extract_emotional_tone(self, text: str) -> str:
        """
        Extract emotional tone from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Emotional tone description
        """
        # Placeholder implementation
        # In production, this would use sentiment analysis
        
        # Simple keyword-based approach for demonstration
        if "crisis" in text.lower() or "emergency" in text.lower():
            return "urgency"
        elif "happy" in text.lower() or "joy" in text.lower():
            return "positive"
        elif "sad" in text.lower() or "sorry" in text.lower():
            return "somber"
        else:
            return "neutral"


class SensoryLoadReducerAdapter(ContentAdapter):
    """Adapter for reducing sensory load in content."""
    
    def adapt_content(self, content: Any, preferences: UserPreferences) -> Any:
        """
        Reduce sensory load in content for users with sensory sensitivities.
        
        Args:
            content: Content to adapt
            preferences: User's accessibility preferences
            
        Returns:
            Adapted content with reduced sensory load
        """
        if not preferences.reduce_sensory_load:
            return content
            
        # For dictionary content (like API responses)
        if isinstance(content, dict):
            content_copy = content.copy()
            
            # Add sensory load metadata
            content_copy["accessibility"] = content_copy.get("accessibility", {})
            content_copy["accessibility"]["sensory_load"] = "reduced"
            
            # If there are visual elements, mark them as low-intensity
            if "visual_elements" in content_copy:
                content_copy["visual_elements_intensity"] = "low"
                
            return content_copy
        else:
            # For other content types, return as is
            return content


class ScreenReaderAdapter(ContentAdapter):
    """Adapter for enhancing screen reader compatibility."""
    
    def adapt_content(self, content: Any, preferences: UserPreferences) -> Any:
        """
        Enhance content for screen reader compatibility.
        
        Args:
            content: Content to adapt
            preferences: User's accessibility preferences
            
        Returns:
            Screen reader enhanced content
        """
        # For dictionary content
        if isinstance(content, dict):
            content_copy = content.copy()
            
            # Add ARIA attributes and screen reader metadata
            content_copy["accessibility"] = content_copy.get("accessibility", {})
            content_copy["accessibility"]["screen_reader_enhanced"] = True
            
            # Add text alternatives for any non-text content
            if "visual_elements" in content_copy:
                for i, element in enumerate(content_copy.get("visual_elements", [])):
                    if "alt_text" not in element:
                        content_copy["visual_elements"][i]["alt_text"] = f"Description for visual element {i+1}"
                        
            return content_copy
        else:
            # For other content types, return as is
            return content


class MultiModalAdapter(ContentAdapter):
    """Adapter for providing multi-modal communication options."""
    
    def adapt_content(self, content: Any, preferences: UserPreferences) -> Any:
        """
        Provide multiple modalities for content consumption.
        
        Args:
            content: Content to adapt
            preferences: User's accessibility preferences
            
        Returns:
            Content with multiple modality options
        """
        if isinstance(content, str):
            # For text content, provide alternative modalities
            return {
                "text": content,
                "modalities": {
                    "audio_available": True,
                    "symbol_version_available": preferences.use_symbols,
                    "simplified_version_available": preferences.language_complexity < 7
                }
            }
        elif isinstance(content, dict):
            # For dictionary content
            content_copy = content.copy()
            
            # Add modality options
            content_copy["accessibility"] = content_copy.get("accessibility", {})
            content_copy["accessibility"]["modalities"] = {
                "audio_available": True,
                "symbol_version_available": preferences.use_symbols,
                "simplified_version_available": preferences.language_complexity < 7
            }
                
            return content_copy
        else:
            # For other content types, return as is
            return content


# Registry of adapters by adaptation type
ADAPTER_REGISTRY: Dict[AdaptationType, Type[ContentAdapter]] = {
    AdaptationType.TEXT_SIMPLIFICATION: TextSimplificationAdapter,
    AdaptationType.SYMBOLS_AND_PICTOGRAMS: SymbolsAndPictogramsAdapter,
    AdaptationType.EMOTIONAL_CUES: EmotionalCuesAdapter,
    AdaptationType.SENSORY_OVERLOAD_REDUCTION: SensoryLoadReducerAdapter,
    AdaptationType.SCREEN_READER_COMPAT: ScreenReaderAdapter,
    AdaptationType.MULTI_MODAL_COMMUNICATION: MultiModalAdapter,
}


class AccessibilityAdapter:
    """
    Main adapter class that coordinates application of multiple
    accessibility adaptations based on user preferences.
    """
    
    def __init__(self, preferences: Optional[UserPreferences] = None):
        """
        Initialize the adapter with user preferences.
        
        Args:
            preferences: User's accessibility preferences
        """
        self.preferences = preferences
        self._adapters: Dict[AdaptationType, ContentAdapter] = {}
    
    def _get_adapter(self, adaptation_type: AdaptationType) -> Optional[ContentAdapter]:
        """
        Get or create an adapter for a specific adaptation type.
        
        Args:
            adaptation_type: Type of adaptation
            
        Returns:
            ContentAdapter instance or None if not supported
        """
        if adaptation_type not in self._adapters:
            adapter_class = ADAPTER_REGISTRY.get(adaptation_type)
            if adapter_class:
                self._adapters[adaptation_type] = adapter_class()
            else:
                return None
                
        return self._adapters[adaptation_type]
    
    def adapt_content(self, content: Any, adaptations: List[AdaptationType] = None) -> Any:
        """
        Apply multiple adaptations to content.
        
        Args:
            content: Content to adapt
            adaptations: List of adaptations to apply (if None, use preferences)
            
        Returns:
            Adapted content
        """
        if not self.preferences:
            return content
            
        if not self.preferences.enabled:
            return content
            
        # Determine which adaptations to apply
        if adaptations is None:
            adaptations = self.preferences.get_effective_adaptations()
            
        # Apply each adaptation in sequence
        adapted_content = content
        for adaptation_type in adaptations:
            adapter = self._get_adapter(adaptation_type)
            if adapter:
                try:
                    adapted_content = adapter.adapt_content(adapted_content, self.preferences)
                except Exception as e:
                    logger.error(f"Error applying {adaptation_type} adaptation: {str(e)}")
                    
        return adapted_content


def get_accessibility_adapter(preferences: Optional[UserPreferences] = None) -> AccessibilityAdapter:
    """
    Factory function to create an AccessibilityAdapter.
    
    Args:
        preferences: User's accessibility preferences
        
    Returns:
        AccessibilityAdapter instance
    """
    return AccessibilityAdapter(preferences)
