"""
Accessibility API Router

This module provides API endpoints for managing accessibility preferences
and settings in the Emotional Wellness API.
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from pydantic import BaseModel

from src.accessibility.config import (
    DisabilityType, AdaptationType, AccessibilityLevel, 
    get_adaptations_for_disabilities
)
from src.accessibility.preferences import UserPreferences, preference_store
from src.security.auth import get_current_user

# Create router
router = APIRouter(
    prefix="/accessibility",
    tags=["accessibility"],
    responses={404: {"description": "Not found"}},
)


class AccessibilityPreferencesUpdate(BaseModel):
    """Model for updating accessibility preferences."""
    enabled: Optional[bool] = None
    disabilities: Optional[List[DisabilityType]] = None
    preferred_adaptations: Optional[List[AdaptationType]] = None
    excluded_adaptations: Optional[List[AdaptationType]] = None
    preferred_level: Optional[AccessibilityLevel] = None
    communication_mode: Optional[str] = None
    language_complexity: Optional[int] = None
    use_symbols: Optional[bool] = None
    reduce_sensory_load: Optional[bool] = None
    extend_timeouts: Optional[bool] = None
    high_contrast_mode: Optional[bool] = None
    large_text_mode: Optional[bool] = None
    metaphor_usage: Optional[str] = None
    crisis_alert_mode: Optional[str] = None
    therapist_communication_format: Optional[str] = None


@router.get("/preferences", response_model=UserPreferences)
async def get_preferences(
    request: Request,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get accessibility preferences for the current user.
    
    Returns:
        UserPreferences object with the user's accessibility settings
    """
    user_id = current_user["id"]
    preferences = await preference_store.get_user_preferences(user_id)
    return preferences


@router.put("/preferences", response_model=UserPreferences)
async def update_preferences(
    updates: AccessibilityPreferencesUpdate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Update accessibility preferences for the current user.
    
    Args:
        updates: Fields to update in the user's preferences
        
    Returns:
        Updated UserPreferences object
    """
    user_id = current_user["id"]
    
    # Convert to dict and remove None values
    updates_dict = {k: v for k, v in updates.dict().items() if v is not None}
    
    # Update preferences
    updated_preferences = await preference_store.update_user_preferences(
        user_id, updates_dict
    )
    
    return updated_preferences


@router.post("/disabilities", response_model=List[AdaptationType])
async def get_recommended_adaptations(
    disabilities: List[DisabilityType],
    current_user: Dict = Depends(get_current_user)
):
    """
    Get recommended adaptations for specific disabilities.
    
    Args:
        disabilities: List of disability types
        
    Returns:
        List of recommended adaptation types
    """
    return get_adaptations_for_disabilities(set(disabilities))


@router.get("/test-adaptation", response_model=Dict)
async def test_adaptation(
    adaptation_type: AdaptationType,
    sample_text: str = Query(..., description="Sample text to adapt"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Test a specific adaptation on sample text.
    
    Args:
        adaptation_type: Type of adaptation to test
        sample_text: Text to adapt
        
    Returns:
        Adapted content
    """
    from src.accessibility.adapters import get_accessibility_adapter
    
    # Get user preferences
    user_id = current_user["id"]
    preferences = await preference_store.get_user_preferences(user_id)
    
    # Create adapter and apply adaptation
    adapter = get_accessibility_adapter(preferences)
    adapted_content = adapter.adapt_content(sample_text, [adaptation_type])
    
    return {
        "original": sample_text,
        "adapted": adapted_content,
        "adaptation_type": adaptation_type
    }


@router.post("/bulk-enable", response_model=UserPreferences)
async def enable_for_disability_profile(
    disabilities: List[DisabilityType],
    current_user: Dict = Depends(get_current_user)
):
    """
    Enable recommended adaptations for a set of disabilities.
    
    This is a convenience endpoint that automatically configures
    all recommended adaptations for the specified disabilities.
    
    Args:
        disabilities: List of disability types
        
    Returns:
        Updated UserPreferences object
    """
    user_id = current_user["id"]
    
    # Get recommended adaptations
    adaptations = get_adaptations_for_disabilities(set(disabilities))
    
    # Update user preferences
    updates = {
        "enabled": True,
        "disabilities": list(set(disabilities)),
        "preferred_adaptations": adaptations,
        "preferred_level": AccessibilityLevel.COMPREHENSIVE
    }
    
    # Apply disability-specific settings
    if DisabilityType.VISION in disabilities:
        updates["high_contrast_mode"] = True
        updates["large_text_mode"] = True
    
    if DisabilityType.COGNITIVE in disabilities:
        updates["language_complexity"] = 3
        updates["use_symbols"] = True
    
    if DisabilityType.SENSORY in disabilities:
        updates["reduce_sensory_load"] = True
    
    # Update preferences
    updated_preferences = await preference_store.update_user_preferences(
        user_id, updates
    )
    
    return updated_preferences
