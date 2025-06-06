"""
Tests for API request validation decorators

These tests verify that the validation decorators properly enforce
input requirements, data consistency, and safety checks.
"""

import json
import pytest
from fastapi import FastAPI, HTTPException, Request, status, Depends, Security
from fastapi.testclient import TestClient
from pydantic import BaseModel
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any, Callable, Union

from api.validators import (
    validate_consistent_user_data,
    validate_required_fields,
    validate_date_range,
    validate_content_safety,
    log_validation_errors,
    verify_phi_identifiers,
)

# Mark all tests in this module as asyncio tests
pytestmark = pytest.mark.asyncio

# Create test Pydantic models
class DateRangeModel(BaseModel):
    start_date: date
    end_date: date
    notes: Optional[str] = None


class UserContentModel(BaseModel):
    user_id: str
    content: str


class PHIModel(BaseModel):
    patient_id: str
    medical_notes: Optional[str] = None
    diagnosis: Optional[str] = None


# Create a custom mock User class for testing
class MockUser:
    def __init__(self, scopes=None):
        self.scopes = scopes or []
    
    def has_scope(self, scope):
        return scope in self.scopes
    
    def __str__(self):
        return f"MockUser(scopes={self.scopes})"


# Create a test FastAPI application
app = FastAPI()


# Create test endpoints using validators with unique names to avoid fixture conflicts
@app.post("/api/required-fields")
@validate_required_fields(required_fields=["name", "email"])
async def required_fields_endpoint(request: Request):
    return {"status": "ok"}


@app.post("/api/user-consistency/{user_id}")
@validate_consistent_user_data(field_name="user_id")
async def user_consistency_endpoint(user_id: str, request: Request):
    return {"status": "ok", "user_id": user_id}


@app.post("/api/date-range")
@validate_date_range(start_date_field="start_date", end_date_field="end_date", max_days=30)
async def date_range_endpoint(data: DateRangeModel):
    return {"status": "ok", "days": (data.end_date - data.start_date).days}


@app.post("/api/content-safety")
@validate_content_safety(content_field="content")
async def content_safety_endpoint(data: UserContentModel):
    return {"status": "ok", "content_length": len(data.content)}


# We won't use FastAPI routing for the PHI test since we need to
# test the decorator directly with different user scenarios


# Setup test client as a fixture
@pytest.fixture
def app_client():
    return TestClient(app)


class TestRequestValidators:
    """Test cases for request validation decorators."""
    
    async def test_required_fields_validator(self, app_client):
        """Test that required fields validator enforces fields presence."""
        # Valid request
        response = app_client.post(
            "/api/required-fields", 
            json={"name": "John", "email": "john@example.com"}
        )
        assert response.status_code == 200
        
        # Missing required field
        response = app_client.post(
            "/api/required-fields", 
            json={"name": "John"}
        )
        assert response.status_code == 400
        assert "Missing required fields" in response.text
        assert "email" in response.text
    
    async def test_user_consistency_validator(self, app_client):
        """Test that user ID in path matches user ID in body."""
        # Valid request - IDs match
        response = app_client.post(
            "/api/user-consistency/123",
            json={"user_id": "123", "data": "test"}
        )
        assert response.status_code == 200
        
        # Invalid request - IDs don't match
        response = app_client.post(
            "/api/user-consistency/123",
            json={"user_id": "456", "data": "test"}
        )
        assert response.status_code == 400
        assert "User ID in path must match" in response.text
    
    async def test_date_range_validator(self, app_client):
        """Test date range validation for chronological order and max duration."""
        today = date.today()
        
        # Valid date range
        response = app_client.post(
            "/api/date-range",
            json={
                "start_date": today.isoformat(),
                "end_date": (today + timedelta(days=10)).isoformat()
            }
        )
        assert response.status_code == 200
        
        # Invalid - end date before start date
        response = app_client.post(
            "/api/date-range",
            json={
                "start_date": today.isoformat(),
                "end_date": (today - timedelta(days=1)).isoformat()
            }
        )
        assert response.status_code == 400
        assert "End date must be after start date" in response.text
        
        # Invalid - exceeds max days
        response = app_client.post(
            "/api/date-range",
            json={
                "start_date": today.isoformat(),
                "end_date": (today + timedelta(days=40)).isoformat()
            }
        )
        assert response.status_code == 400
        assert "Date range cannot exceed 30 days" in response.text
    
    async def test_content_safety_validator(self, app_client):
        """Test content safety validation against unsafe patterns."""
        # Valid content
        response = app_client.post(
            "/api/content-safety",
            json={
                "user_id": "123",
                "content": "This is safe content with no scripts or XSS."
            }
        )
        assert response.status_code == 200
        
        # Invalid - contains script tag
        response = app_client.post(
            "/api/content-safety",
            json={
                "user_id": "123",
                "content": "This contains <script>alert('xss')</script>."
            }
        )
        assert response.status_code == 400
        assert "Unsafe content detected" in response.text
        
        # Invalid - contains javascript: URL
        response = app_client.post(
            "/api/content-safety",
            json={
                "user_id": "123",
                "content": "Click <a href='javascript:alert(1)'>here</a>."
            }
        )
        assert response.status_code == 400
        assert "Unsafe content detected" in response.text

    @pytest.mark.parametrize("has_phi_scope,expected_status", [
        (True, 200),
        (False, 403)
    ])
    async def test_phi_validation(self, has_phi_scope, expected_status):
        """Test PHI fields validation with different user scopes."""
        # Create a simple async endpoint function to decorate
        async def test_phi_function(data: PHIModel, user=None):
            return {"status": "ok", "patient_id": data.patient_id}
            
        # Create the decorated function
        decorated_function = verify_phi_identifiers(phi_fields=["medical_notes", "diagnosis"])(test_phi_function)
        
        # Create test data
        data = PHIModel(
            patient_id="P12345",
            medical_notes="Patient reports symptoms of...",
            diagnosis="Condition X"
        )
        
        # Create a mock user with appropriate scopes
        user = MockUser(scopes=["phi_access"] if has_phi_scope else ["basic"])
        
        if has_phi_scope:
            # If the user has phi_access, the function should succeed
            result = await decorated_function(data=data, user=user)
            assert result["status"] == "ok"
            assert result["patient_id"] == "P12345"
        else:
            # If the user doesn't have phi_access, the function should raise HTTPException
            with pytest.raises(HTTPException) as excinfo:
                await decorated_function(data=data, user=user)
            
            # Check the error details
            assert excinfo.value.status_code == 403
            assert "PHI access not authorized" in excinfo.value.detail
