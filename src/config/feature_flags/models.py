"""
Feature Flag Models

This module defines the data models for feature flags.
"""

from enum import Enum
from typing import Dict, Any, Optional, Union, List
from datetime import datetime

from pydantic import BaseModel, Field, validator


class FeatureFlagType(str, Enum):
    """Type of feature flag value."""
    BOOLEAN = "boolean"
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    JSON = "json"


class FeatureFlagValue(BaseModel):
    """Model for feature flag value with metadata."""
    
    value: Any = Field(..., description="The flag value")
    type: FeatureFlagType = Field(..., description="Type of the flag value")
    description: Optional[str] = Field(None, description="Description of this value")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="When this value was last updated")
    updated_by: Optional[str] = Field(None, description="Who updated this value")
    
    @validator('value')
    def validate_value_type(cls, v, values):
        """Validate that value matches the specified type."""
        if 'type' not in values:
            return v
            
        flag_type = values['type']
        
        if flag_type == FeatureFlagType.BOOLEAN and not isinstance(v, bool):
            raise ValueError(f"Value must be boolean for type {flag_type}")
        elif flag_type == FeatureFlagType.INTEGER and not isinstance(v, int):
            raise ValueError(f"Value must be integer for type {flag_type}")
        elif flag_type == FeatureFlagType.FLOAT and not isinstance(v, (int, float)):
            raise ValueError(f"Value must be float for type {flag_type}")
        elif flag_type == FeatureFlagType.STRING and not isinstance(v, str):
            raise ValueError(f"Value must be string for type {flag_type}")
        elif flag_type == FeatureFlagType.JSON and not isinstance(v, (dict, list)):
            raise ValueError(f"Value must be JSON-serializable for type {flag_type}")
            
        return v


class FeatureFlag(BaseModel):
    """Model for feature flag definition."""
    
    key: str = Field(..., description="Unique identifier for this flag")
    name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Description of what this flag controls")
    value: FeatureFlagValue = Field(..., description="Current value of the flag")
    default_value: Any = Field(..., description="Default value if not specified")
    category: str = Field("general", description="Category for organizing flags")
    tags: List[str] = Field(default_factory=list, description="Tags for filtering flags")
    enabled: bool = Field(True, description="Whether this flag is active")
    
    # Optional metadata
    owner: Optional[str] = Field(None, description="Team/person responsible for this flag")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When this flag was created")
    expiration_date: Optional[datetime] = Field(None, description="When this flag expires (if temporary)")
    
    # Rollout settings
    percentage_rollout: Optional[float] = Field(None, description="Percentage of users for rollout (0-100)")
    target_users: Optional[List[str]] = Field(None, description="Specific user IDs for targeting")
    
    class Config:
        """Model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
