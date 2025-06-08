"""
Unit tests for accessibility features
"""

import pytest
import json
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

from src.accessibility.config import DisabilityType, AdaptationType
from src.accessibility.preferences import UserPreferences, preference_store
from src.accessibility.middleware import AccessibilityMiddleware
from src.accessibility.adapters import get_accessibility_adapter
from src.accessibility.emotional_adaptations import EmotionalSymbolAdapter, TherapistCommunicationAdapter
from src.accessibility.integration import AccessibilityService, register_accessibility_features


@pytest.fixture
def mock_preferences():
    """Create mock user preferences for testing."""
    return UserPreferences(
        user_id="test_user",
        enabled=True,
        disabilities=[DisabilityType.COGNITIVE, DisabilityType.VISION],
        preferred_adaptations=[
            AdaptationType.TEXT_SIMPLIFICATION,
            AdaptationType.SCREEN_READER_COMPATIBILITY
        ],
        language_complexity=3,
        use_symbols=True,
        high_contrast_mode=True,
        large_text_mode=True,
        extend_timeouts=True,
        reduce_sensory_load=True
    )


@pytest.fixture
def mock_preference_store():
    """Create a mock preference store."""
    store = MagicMock()
    store.get_user_preferences = AsyncMock()
    store.save_user_preferences = AsyncMock()
    store.update_user_preferences = AsyncMock()
    return store


@pytest.fixture
def app():
    """Create a test FastAPI app."""
    app = FastAPI()
    register_accessibility_features(app)
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


@pytest.mark.asyncio
async def test_emotional_symbol_adapter(mock_preferences):
    """Test the EmotionalSymbolAdapter."""
    # Create adapter
    adapter = EmotionalSymbolAdapter(mock_preferences)
    
    # Test symbolic pattern adaptation
    pattern = "Water→Fire→Mountain→Star"
    result = adapter.adapt_symbolic_pattern(pattern)
    
    # Check result structure
    assert "original_pattern" in result
    assert "accessible_versions" in result
    assert "descriptive" in result["accessible_versions"]
    assert "simplified" in result["accessible_versions"]
    
    # Test crisis notification adaptation
    notification = {
        "type": "crisis_notification",
        "level": 2,
        "symbolic_pattern": "Shadow→Abyss→Light",
        "urgency": "high",
        "timestamp": "2025-06-06T19:15:00Z"
    }
    
    adapted_notification = adapter.adapt_crisis_notification(notification)
    assert "simplified_explanation" in adapted_notification
    assert "presentation_mode" in adapted_notification


@pytest.mark.asyncio
async def test_therapist_communication_adapter(mock_preferences):
    """Test the TherapistCommunicationAdapter."""
    # Create adapter
    adapter = TherapistCommunicationAdapter(mock_preferences)
    
    # Test message adaptation
    message = {
        "type": "therapist_message",
        "therapist_id": "T12345",
        "content": "Let's discuss your progress with the symbolic exercises."
    }
    
    adapted_message = adapter.adapt_therapist_message(message)
    assert "content" in adapted_message
    assert "format" in adapted_message
    assert "emotional_cues" in adapted_message


@pytest.mark.asyncio
async def test_accessibility_service(mock_preferences, monkeypatch):
    """Test the AccessibilityService."""
    # Mock preference store
    async def mock_get_preferences(user_id):
        return mock_preferences
    
    monkeypatch.setattr(preference_store, "get_user_preferences", mock_get_preferences)
    
    # Create service
    service = AccessibilityService()
    
    # Test getting user preferences
    preferences = await service.get_user_preferences("test_user")
    assert preferences.user_id == "test_user"
    assert preferences.enabled is True
    
    # Test adapting symbolic content
    content = {
        "symbolic_pattern": "Water→Fire→Mountain→Star",
        "type": "emotional_weather"
    }
    
    adapted_content = await service.adapt_symbolic_content("test_user", content)
    assert "symbolic_pattern" in adapted_content
    assert "type" in adapted_content
    
    # Test session timeout extension
    extension = await service.get_session_timeout_extension("test_user")
    assert extension > 100  # Should be extended


@pytest.mark.asyncio
async def test_middleware_response_adaptation():
    """Test the AccessibilityMiddleware."""
    # Create app with middleware
    app = FastAPI()
    app.add_middleware(AccessibilityMiddleware)
    
    # Mock endpoint that returns JSON
    @app.get("/test")
    async def test_endpoint():
        return {"message": "This is a complex message that should be simplified."}
    
    # Create test client
    client = TestClient(app)
    
    # Mock getting user preferences
    with patch("src.accessibility.middleware.get_user_from_request") as mock_get_user:
        mock_get_user.return_value = {"id": "test_user"}
        
        with patch("src.accessibility.middleware.preference_store.get_user_preferences") as mock_get_prefs:
            mock_get_prefs.return_value = UserPreferences(
                user_id="test_user",
                enabled=True,
                disabilities=[DisabilityType.COGNITIVE],
                preferred_adaptations=[AdaptationType.TEXT_SIMPLIFICATION]
            )
            
            # Test response
            response = client.get("/test")
            assert response.status_code == 200
            assert "X-Accessibility-Adapted" in response.headers


@pytest.mark.asyncio
async def test_router_endpoints(client):
    """Test the accessibility router endpoints."""
    # Mock authentication
    with patch("src.accessibility.router.get_current_user") as mock_auth:
        mock_auth.return_value = {"id": "test_user"}
        
        # Mock preference store
        with patch("src.accessibility.router.preference_store") as mock_store:
            mock_store.get_user_preferences.return_value = UserPreferences(
                user_id="test_user",
                enabled=True,
                disabilities=[DisabilityType.COGNITIVE],
                preferred_adaptations=[AdaptationType.TEXT_SIMPLIFICATION]
            )
            
            # Test get preferences
            response = client.get("/accessibility/preferences")
            assert response.status_code == 200
            data = response.json()
            assert data["user_id"] == "test_user"
            assert data["enabled"] is True
            
            # Test update preferences
            response = client.put(
                "/accessibility/preferences",
                json={"enabled": True, "disabilities": ["vision"]}
            )
            assert response.status_code == 200
            
            # Test test adaptation
            response = client.get(
                "/accessibility/test-adaptation",
                params={"adaptation_type": "text_simplification", "sample_text": "Complex text"}
            )
            assert response.status_code == 200


def test_register_accessibility_features():
    """Test registering accessibility features with the app."""
    app = FastAPI()
    register_accessibility_features(app)
    
    # Check that middleware was added
    assert any(isinstance(m, AccessibilityMiddleware) for m in app.user_middleware)
    
    # Check that router was included
    routes = [route.path for route in app.routes]
    assert "/accessibility/preferences" in routes or any("/accessibility" in route for route in routes)
