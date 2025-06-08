"""
Accessibility Middleware Module

This module provides FastAPI middleware for automatically applying accessibility
adaptations to API responses based on user preferences.
"""

from typing import Callable, Dict, Optional
import json
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.accessibility.preferences import preference_store, UserPreferences
from src.accessibility.adapters import get_accessibility_adapter
from src.accessibility.config import accessibility_config

logger = logging.getLogger(__name__)


class AccessibilityMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for applying accessibility adaptations to responses.
    
    This middleware intercepts API responses and applies appropriate
    accessibility adaptations based on the user's preferences.
    """
    
    def __init__(self, app: ASGIApp):
        """
        Initialize the middleware.
        
        Args:
            app: The ASGI application
        """
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and response.
        
        Args:
            request: The incoming request
            call_next: Function to call the next middleware or route handler
            
        Returns:
            The adapted response
        """
        # Check if accessibility features are enabled globally
        if not accessibility_config.enable_accessibility_features:
            return await call_next(request)
        
        # Get user ID from request (e.g., from auth token)
        user_id = self._get_user_id_from_request(request)
        
        # Process the request normally first
        response = await call_next(request)
        
        # Only adapt responses if we have a user ID and it's a JSON response
        if user_id and response.headers.get("content-type") == "application/json":
            try:
                # Get user preferences
                preferences = await preference_store.get_user_preferences(user_id)
                
                # Only proceed if accessibility features are enabled for this user
                if preferences.enabled:
                    # Apply adaptations to the response
                    adapted_response = await self._adapt_response(response, preferences)
                    return adapted_response
            except Exception as e:
                # Log error but don't block the response
                logger.error(f"Error applying accessibility adaptations: {str(e)}")
        
        return response
    
    def _get_user_id_from_request(self, request: Request) -> Optional[str]:
        """
        Extract user ID from the request.
        
        Args:
            request: The incoming request
            
        Returns:
            User ID if available, None otherwise
        """
        # This is a placeholder implementation
        # In a real application, this would extract the user ID from:
        # - Authentication token
        # - Session cookie
        # - Request headers
        
        # Try to get from authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # In a real app, this would decode and validate the token
            # For now, we'll just return a placeholder
            return "user123"
        
        # Try to get from session cookie
        session = request.cookies.get("session")
        if session:
            # In a real app, this would validate and decode the session
            return "user123"
        
        return None
    
    async def _adapt_response(
        self, response: Response, preferences: UserPreferences
    ) -> Response:
        """
        Apply accessibility adaptations to the response.
        
        Args:
            response: The original response
            preferences: User's accessibility preferences
            
        Returns:
            Adapted response
        """
        # Read response body
        body = await response.body()
        
        try:
            # Parse JSON content
            content = json.loads(body)
            
            # Get adapter and apply adaptations
            adapter = get_accessibility_adapter(preferences)
            adapted_content = adapter.adapt_content(content)
            
            # Create new response with adapted content
            new_response = Response(
                content=json.dumps(adapted_content),
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type="application/json"
            )
            
            # Add accessibility headers
            new_response.headers["X-Accessibility-Adapted"] = "true"
            new_response.headers["X-Accessibility-Level"] = preferences.preferred_level
            
            return new_response
        except json.JSONDecodeError:
            # If not valid JSON, return original response
            logger.warning("Non-JSON response, skipping accessibility adaptations")
            return response
        except Exception as e:
            # Log error but return original response
            logger.error(f"Error adapting response: {str(e)}")
            return response
