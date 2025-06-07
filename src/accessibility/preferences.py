"""
User Accessibility Preferences Module

This module provides models and functionality for storing and retrieving 
user-specific accessibility preferences in the Emotional Wellness API.
"""

from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field
from datetime import datetime

from src.accessibility.config import DisabilityType, AdaptationType, AccessibilityLevel


class UserPreferences(BaseModel):
    """
    User-specific accessibility preferences model.
    
    Stores individual accessibility settings including disability types,
    preferred adaptations, and communication preferences.
    """
    user_id: str
    enabled: bool = True
    disabilities: Set[DisabilityType] = Field(default_factory=set)
    preferred_adaptations: List[AdaptationType] = Field(default_factory=list)
    excluded_adaptations: List[AdaptationType] = Field(default_factory=list)
    preferred_level: AccessibilityLevel = AccessibilityLevel.MODERATE
    
    # Communication preferences
    communication_mode: Optional[str] = None  # e.g., "text", "audio", "symbol-based"
    language_complexity: int = Field(5, ge=1, le=10)  # 1=simplest, 10=complex
    use_symbols: bool = False
    reduce_sensory_load: bool = False
    extend_timeouts: bool = True
    high_contrast_mode: bool = False
    large_text_mode: bool = False
    
    # Application-specific preferences
    metaphor_usage: Optional[str] = "standard"  # "reduced", "concrete", "standard"
    crisis_alert_mode: Optional[str] = "multi-modal"  # "visual", "audio", "multi-modal"
    therapist_communication_format: Optional[str] = None
    
    # Metadata
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "user_id": "usr123456",
                "enabled": True,
                "disabilities": ["vision", "cognitive"],
                "preferred_adaptations": ["screen_reader_compatibility", "text_simplification"],
                "language_complexity": 3,
                "use_symbols": True,
                "metaphor_usage": "concrete"
            }
        }
    
    def get_effective_adaptations(self) -> List[AdaptationType]:
        """
        Get effective adaptations list, considering preferences and exclusions.
        
        Returns:
            List of adaptation types to apply
        """
        # Start with user's explicit preferences
        adaptations = set(self.preferred_adaptations)
        
        # Remove any explicitly excluded adaptations
        adaptations = adaptations - set(self.excluded_adaptations)
        
        return list(adaptations)


class PreferenceStore:
    """
    Storage and retrieval for user accessibility preferences.
    
    This class provides an abstraction over the underlying storage mechanism,
    which could be a database, cache, or other persistent storage.
    """
    
    async def get_user_preferences(self, user_id: str) -> UserPreferences:
        """
        Retrieve accessibility preferences for a user.
        
        Args:
            user_id: The unique identifier for the user
            
        Returns:
            UserPreferences object with the user's accessibility settings
        """
        # TODO: Replace with actual database retrieval
        # This is a placeholder implementation
        from src.accessibility.config import get_adaptations_for_disabilities
        
        # Default preferences - in production would fetch from database
        prefs = UserPreferences(
            user_id=user_id,
            enabled=True,
            disabilities=set(),  # No disabilities by default
            preferred_adaptations=[],
            preferred_level=AccessibilityLevel.MODERATE
        )
        
        return prefs
    
    async def save_user_preferences(self, preferences: UserPreferences) -> bool:
        """
        Save user accessibility preferences.
        
        Args:
            preferences: UserPreferences object to save
            
        Returns:
            True if save was successful, False otherwise
        """
        # TODO: Replace with actual database save
        # This is a placeholder implementation
        preferences.last_updated = datetime.utcnow()
        return True
    
    async def update_user_preferences(
        self, user_id: str, updates: Dict
    ) -> UserPreferences:
        """
        Update specific fields of user preferences.
        
        Args:
            user_id: The unique identifier for the user
            updates: Dictionary of fields to update
            
        Returns:
            Updated UserPreferences object
        """
        # Get current preferences
        prefs = await self.get_user_preferences(user_id)
        
        # Apply updates
        for k, v in updates.items():
            if hasattr(prefs, k):
                setattr(prefs, k, v)
        
        # Save updated preferences
        await self.save_user_preferences(prefs)
        
        return prefs


# Global instance for use throughout the application
preference_store = PreferenceStore()
