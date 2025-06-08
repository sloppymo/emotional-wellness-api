"""
Accessibility Integration Module

This module provides integration points for the accessibility features
with the main Emotional Wellness API application.
"""

from typing import Callable, Dict, List, Optional, Type
import logging
from fastapi import FastAPI, Request, Response

from src.accessibility.config import accessibility_config
from src.accessibility.middleware import AccessibilityMiddleware
from src.accessibility.router import router as accessibility_router
from src.accessibility.preferences import preference_store, UserPreferences
from src.accessibility.emotional_adaptations import EmotionalSymbolAdapter, TherapistCommunicationAdapter

logger = logging.getLogger(__name__)


def register_accessibility_features(app: FastAPI) -> None:
    """
    Register all accessibility features with the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    # Register middleware
    app.add_middleware(AccessibilityMiddleware)
    
    # Register router
    app.include_router(accessibility_router)
    
    # Log successful registration
    logger.info("Accessibility features registered with application")


class AccessibilityService:
    """
    Service class for accessibility-related operations.
    
    This class provides a centralized interface for accessing
    accessibility features throughout the application.
    """
    
    async def get_user_preferences(self, user_id: str) -> UserPreferences:
        """
        Get accessibility preferences for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            User's accessibility preferences
        """
        return await preference_store.get_user_preferences(user_id)
    
    async def adapt_symbolic_content(
        self, user_id: str, content: Dict
    ) -> Dict:
        """
        Adapt symbolic content for a user's accessibility needs.
        
        Args:
            user_id: User ID
            content: Symbolic content to adapt
            
        Returns:
            Adapted content
        """
        # Get user preferences
        preferences = await self.get_user_preferences(user_id)
        
        # Create adapter and adapt content
        adapter = EmotionalSymbolAdapter(preferences)
        
        # Adapt different types of content
        if "symbolic_pattern" in content:
            content["symbolic_pattern"] = adapter.adapt_symbolic_pattern(
                content["symbolic_pattern"]
            )
            
        if "archetype" in content:
            content["archetype"] = adapter.adapt_archetype(
                content["archetype"]
            )
            
        if content.get("type") == "crisis_notification":
            content = adapter.adapt_crisis_notification(content)
            
        if content.get("type") == "emotional_weather":
            content = adapter.adapt_emotional_weather(content)
            
        return content
    
    async def adapt_therapist_message(
        self, user_id: str, message: Dict
    ) -> Dict:
        """
        Adapt a therapist message for a user's accessibility needs.
        
        Args:
            user_id: User ID
            message: Therapist message to adapt
            
        Returns:
            Adapted message
        """
        # Get user preferences
        preferences = await self.get_user_preferences(user_id)
        
        # Create adapter and adapt message
        adapter = TherapistCommunicationAdapter(preferences)
        return adapter.adapt_therapist_message(message)
    
    async def get_session_timeout_extension(self, user_id: str) -> int:
        """
        Get session timeout extension for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Timeout extension percentage (e.g., 200 for 200% longer)
        """
        # Get user preferences
        preferences = await self.get_user_preferences(user_id)
        
        # Return extension if accessibility features are enabled
        if preferences.enabled and preferences.extend_timeouts:
            return accessibility_config.session_timeout_extension
        else:
            return 100  # No extension (100% of normal timeout)


# Global instance for use throughout the application
accessibility_service = AccessibilityService()


def get_accessibility_service() -> AccessibilityService:
    """
    Get the global accessibility service instance.
    
    Returns:
        AccessibilityService instance
    """
    return accessibility_service
