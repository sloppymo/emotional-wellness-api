"""
Unit and integration tests for Symbolic Subsystems API endpoints (ROOT, GROVE, MARROW)
"""
import os
from typing import List, Dict, Any

import pytest
from fastapi import Depends, Security, Request
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

# Import app and security components
from main import app
from security.auth import User, get_current_user_with_scope, verify_phi_scope, get_api_key, api_key_header, oauth2_scheme, get_current_user

# Create a test user with PHI access scope
test_user = User(
    id="test123", 
    username="testuser", 
    email="test@example.com",
    scopes=["phi_access", "emotional_processing"]
)

# Create specific mock functions that match the dependency signature patterns FastAPI expects

# Create more precise mocks that better match the FastAPI dependency injection system

# Mock for OAuth token extraction
async def mock_oauth2_scheme(request: Request = None):
    return "fake-valid-token"

# Mock for user validation from token
async def mock_get_current_user(security_scopes=None, token: str = None):
    return test_user

# Mock for scope-based user validation - this is the key function that needs to be fixed
def mock_get_current_user_with_scope(required_scopes=None):
    # This is a factory function that needs to return a dependency function
    # that correctly handles security_scopes and token extraction
    async def inner(token: str = Depends(mock_oauth2_scheme)):
        # Here we correctly ignore the token and just return the test user
        # This bypasses all authentication for testing
        return test_user
    return inner

# Mock for PHI access verification
async def mock_verify_phi_scope(user: User = Depends(mock_get_current_user)):
    # Simply pass through the user - no additional validation
    return user

# Mock for API key header extraction
async def mock_api_key_header(request: Request = None):
    return "test-api-key"

# Mock for API key validation - removed the circular dependency
async def mock_api_key(api_key: str = None):
    return "test-api-key"

# Apply all dependency overrides - the key here is that we're providing mocks
# that have the correct parameter signatures to match what FastAPI expects
app.dependency_overrides[oauth2_scheme] = mock_oauth2_scheme
app.dependency_overrides[get_current_user] = mock_get_current_user
app.dependency_overrides[get_current_user_with_scope] = mock_get_current_user_with_scope
app.dependency_overrides[verify_phi_scope] = mock_verify_phi_scope
app.dependency_overrides[get_api_key] = mock_api_key
app.dependency_overrides[api_key_header] = mock_api_key_header

client = TestClient(app)

# Example test data - using the structure expected by the API
EMOTIONAL_STATES = [
    {"timestamp": "2025-06-01T10:00:00Z", "state": "struggle", "meta": {}},
    {"timestamp": "2025-06-02T10:00:00Z", "state": "resilient", "meta": {}},
    {"timestamp": "2025-06-03T10:00:00Z", "state": "confident", "meta": {}}
]

# Authentication headers with both Bearer token and API key
HEADERS = {
    "Authorization": "Bearer testtoken", 
    "X-API-Key": "test-api-key",
    "X-Request-ID": "test-req-1"
}

def test_root_analyze_timeline():
    # Create request payload
    payload = {"emotional_states": EMOTIONAL_STATES}
    
    # Make the request
    resp = client.post(
        "/symbolic/root/analyze_timeline",
        json=payload,
        headers=HEADERS
    )
    
    # Print response for debugging
    if resp.status_code != 200:
        print(f"Response: {resp.status_code} - {resp.text}")
    
    # Assert expected results
    assert resp.status_code == 200
    assert "arc" in resp.json()

def test_root_archetypes():
    resp = client.post(
        "/symbolic/root/archetypes",
        json={"emotional_states": EMOTIONAL_STATES},
        headers=HEADERS
    )
    # Print response for debugging
    if resp.status_code != 200:
        print(f"Root archetypes response: {resp.status_code} - {resp.text}")
    assert resp.status_code == 200
    assert "archetypes" in resp.json()

def test_root_journey_pattern():
    resp = client.post(
        "/symbolic/root/journey_pattern",
        json={"emotional_states": EMOTIONAL_STATES},
        headers=HEADERS
    )
    # Print response for debugging
    if resp.status_code != 200:
        print(f"Journey pattern response: {resp.status_code} - {resp.text}")
    assert resp.status_code == 200
    assert "pattern" in resp.json()

def test_grove_group_analysis():
    resp = client.post(
        "/symbolic/grove/group_analysis",
        json={"sessions": [
            {"emotional_states": EMOTIONAL_STATES},
            {"emotional_states": [
                {"timestamp": "2025-06-01T10:00:00Z", "state": "curious", "meta": {}},
                {"timestamp": "2025-06-02T10:00:00Z", "state": "reflective", "meta": {}}
            ]}
        ]},
        headers=HEADERS
    )
    # Print response for debugging
    if resp.status_code != 200:
        print(f"Group analysis response: {resp.status_code} - {resp.text}")
    assert resp.status_code == 200
    assert "group_state_frequencies" in resp.json()

def test_marrow_deep_symbolism():
    resp = client.post(
        "/symbolic/marrow/deep_symbolism",
        json={"emotional_states": EMOTIONAL_STATES},
        headers=HEADERS
    )
    # Print response for debugging
    if resp.status_code != 200:
        print(f"Deep symbolism response: {resp.status_code} - {resp.text}")
    assert resp.status_code == 200
    assert "latent_patterns" in resp.json()
