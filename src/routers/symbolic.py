"""
Symbolic Subsystems API Router
Provides endpoints for ROOT, GROVE, and MARROW symbolic analysis.
"""
from fastapi import APIRouter, HTTPException, Depends, Security, Request
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime

from security.auth import get_current_user_with_scope, verify_phi_scope
from symbolic.root.analysis import analyze_emotional_timeline, identify_archetypes, map_journey_pattern
from symbolic.grove import analyze_group_emotional_states
from symbolic.marrow import extract_deep_symbolism
from api.validators import (
    validate_required_fields,
    validate_content_safety,
    log_validation_errors,
    verify_phi_identifiers
)

# Define router without prefix - prefix will be added in main.py
router = APIRouter(tags=["Symbolic Subsystems"])

# --- Request/Response Models ---
class EmotionalStateEntry(BaseModel):
    timestamp: str
    state: str
    meta: Dict[str, Any] = Field(default_factory=dict)

class SessionStates(BaseModel):
    emotional_states: List[EmotionalStateEntry]

class GroupSessionsRequest(BaseModel):
    sessions: List[SessionStates]

# --- ROOT Endpoints ---
@router.post("/root/analyze_timeline", summary="Analyze emotional timeline (ROOT)")
@validate_required_fields(["emotional_states"])
@validate_content_safety(["emotional_states.*.state", "emotional_states.*.meta.*"])
@verify_phi_identifiers(phi_fields=["emotional_states.*.meta"])
async def root_analyze_timeline(
    request: Request,
    data: SessionStates,
    user=Depends(get_current_user_with_scope(["phi_access"])),
    phi=Security(verify_phi_scope)
):
    # Convert Pydantic models to dicts using model_dump() for Pydantic v2 compatibility
    result = analyze_emotional_timeline([e.model_dump() for e in data.emotional_states])
    return result

@router.post("/root/archetypes", summary="Identify emotional archetypes (ROOT)")
@validate_required_fields(["emotional_states"])
@validate_content_safety(["emotional_states.*.state", "emotional_states.*.meta.*"])
@verify_phi_identifiers(phi_fields=["emotional_states.*.meta"])
async def root_identify_archetypes(
    request: Request,
    data: SessionStates,
    user=Depends(get_current_user_with_scope(["phi_access"])),
    phi=Security(verify_phi_scope)
):
    result = identify_archetypes([e.model_dump() for e in data.emotional_states])
    return {"archetypes": [a.value for a in result]}

@router.post("/root/journey_pattern", summary="Map emotional journey pattern (ROOT)")
@validate_required_fields(["emotional_states"])
@validate_content_safety(["emotional_states.*.state", "emotional_states.*.meta.*"])
@verify_phi_identifiers(phi_fields=["emotional_states.*.meta"])
async def root_map_journey_pattern(
    request: Request,
    data: SessionStates,
    user=Depends(get_current_user_with_scope(["phi_access"])),
    phi=Security(verify_phi_scope)
):
    result = map_journey_pattern([e.model_dump() for e in data.emotional_states])
    return result

# --- GROVE Endpoint ---
@router.post("/grove/group_analysis", summary="Analyze group emotional states (GROVE)")
@validate_required_fields(["sessions", "sessions.*.emotional_states"])
@validate_content_safety(["sessions.*.emotional_states.*.state", "sessions.*.emotional_states.*.meta.*"])
@verify_phi_identifiers(phi_fields=["sessions.*.emotional_states.*.meta"])
async def grove_group_analysis(
    request: Request,
    data: GroupSessionsRequest,
    user=Depends(get_current_user_with_scope(["phi_access"])),
    phi=Security(verify_phi_scope)
):
    session_dicts = [
        {"emotional_states": [e.model_dump() for e in s.emotional_states]} for s in data.sessions
    ]
    result = analyze_group_emotional_states(session_dicts)
    return result

# --- MARROW Endpoint ---
@router.post("/marrow/deep_symbolism", summary="Extract deep symbolism (MARROW)")
@validate_required_fields(["emotional_states"])
@validate_content_safety(["emotional_states.*.state", "emotional_states.*.meta.*"])
@verify_phi_identifiers(phi_fields=["emotional_states.*.meta"])
async def marrow_deep_symbolism(
    request: Request,
    data: SessionStates,
    user=Depends(get_current_user_with_scope(["phi_access"])),
    phi=Security(verify_phi_scope)
):
    result = extract_deep_symbolism([e.model_dump() for e in data.emotional_states])
    return result
