"""
Emotional State Router

This module provides API endpoints for processing emotional state inputs,
extracting symbolic mappings, and executing the VELURIA protocol when needed.
"""

import hashlib
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse

from models.emotional_state import (
    EmotionalStateInput, 
    EmotionalStateResponse,
    EmotionalState,
    SafetyStatus
)
from symbolic.canopy import get_canopy_processor
from symbolic.moss import get_moss_processor
from symbolic.veluria import get_veluria_protocol
from security.auth import get_current_user_with_scope

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory cache of recent emotional states per user
# In production, this would use Redis or another distributed cache
user_emotional_history: Dict[str, List[EmotionalState]] = {}

@router.post("/emotional-state", response_model=EmotionalStateResponse)
async def process_emotional_state(
    input_data: EmotionalStateInput,
    background_tasks: BackgroundTasks,
    request: Request,
    user = Depends(get_current_user_with_scope(["emotional_processing"]))
):
    """
    Process emotional input text, extract symbolic meaning, and evaluate safety
    
    This endpoint:
    1. Processes text through CANOPY to extract symbolic meaning
    2. Checks previous emotional states to calculate drift
    3. Evaluates safety with MOSS
    4. Executes VELURIA protocol if necessary
    5. Returns symbolic representation and safety status
    """
    logger.info(f"Processing emotional state for user {input_data.user_id}, session {input_data.session_id}")
    
    # Get processors
    canopy = get_canopy_processor()
    moss = get_moss_processor()
    veluria = get_veluria_protocol()
    
    try:
        # Process through CANOPY
        symbolic_mapping = await canopy.extract(
            input_data.text,
            input_data.biomarkers,
            input_data.context
        )
        
        # Get previous emotional states for this user
        previous_states = get_user_emotional_history(input_data.user_id)
        
        # Calculate drift if we have previous states
        drift_index = 0.0
        if previous_states:
            drift_index = canopy.calculate_drift(symbolic_mapping, previous_states)
        
        # Evaluate safety with MOSS
        safety_status = moss.evaluate(
            symbolic_mapping,
            input_data.text,
            input_data.biomarkers
        )
        
        # Execute VELURIA protocol based on safety status
        if safety_status.level > 0:
            background_tasks.add_task(
                execute_veluria,
                input_data.user_id,
                safety_status,
                {"session_id": input_data.session_id}
            )
        
        # Create response object
        response = EmotionalStateResponse(
            symbolic_anchor=symbolic_mapping.primary_symbol,
            alternatives=symbolic_mapping.alternative_symbols,
            archetype=symbolic_mapping.archetype,
            drift_index=drift_index,
            safety_status={
                "level": safety_status.level,
                "triggers": safety_status.triggers,
                "recommended_actions": safety_status.recommended_actions
            },
            content=generate_response_content(symbolic_mapping, safety_status, drift_index)
        )
        
        # Store emotional state in history (in background)
        background_tasks.add_task(
            store_emotional_state,
            input_data,
            symbolic_mapping,
            safety_status,
            drift_index
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing emotional state: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing emotional input")

@router.get("/emotional-state/history/{user_id}", response_model=List[Dict[str, Any]])
async def get_emotional_history(
    user_id: str,
    limit: int = 10,
    user = Depends(get_current_user_with_scope(["emotional_history"]))
):
    """
    Retrieve emotional state history for a user
    
    This endpoint returns a sanitized version of emotional state history,
    with all PHI removed for HIPAA compliance.
    """
    # Authorization check - user can only see their own data
    # unless they have admin privileges
    if user.id != user_id and "admin" not in user.scopes:
        raise HTTPException(status_code=403, detail="Not authorized to access this data")
    
    history = get_user_emotional_history(user_id)
    
    # Return most recent entries first, limited to requested amount
    sanitized_history = []
    for state in sorted(history, key=lambda x: x.timestamp, reverse=True)[:limit]:
        sanitized_history.append({
            "timestamp": state.timestamp,
            "primary_symbol": state.primary_symbol,
            "archetype": state.archetype,
            "valence": state.valence,
            "arousal": state.arousal,
            "drift_index": state.drift_index,
            "safety_level": state.safety_level
        })
    
    return sanitized_history

def get_user_emotional_history(user_id: str) -> List[EmotionalState]:
    """Get emotional state history for a user from cache"""
    return user_emotional_history.get(user_id, [])

async def execute_veluria(user_id: str, safety_status: SafetyStatus, context: Dict[str, Any]):
    """Execute VELURIA protocol in background task"""
    veluria = get_veluria_protocol()
    intervention = veluria.execute_protocol(user_id, safety_status, context)
    logger.info(f"VELURIA protocol executed for user {user_id} at level {intervention.level}")

async def store_emotional_state(
    input_data: EmotionalStateInput,
    symbolic_mapping: Any,
    safety_status: SafetyStatus,
    drift_index: float
):
    """Store emotional state in history and database"""
    # Hash the input text for reference without storing raw text
    # In production, use a secure salted hash with proper key management
    text_hash = hashlib.sha256(input_data.text.encode()).hexdigest()
    
    # Create emotional state record
    state = EmotionalState(
        user_id=input_data.user_id,
        session_id=input_data.session_id,
        valence=symbolic_mapping.valence,
        arousal=symbolic_mapping.arousal,
        primary_symbol=symbolic_mapping.primary_symbol,
        alternative_symbols=symbolic_mapping.alternative_symbols,
        archetype=symbolic_mapping.archetype,
        drift_index=drift_index,
        safety_level=safety_status.level,
        input_text_hash=text_hash,
        metadata={
            "triggers": safety_status.triggers,
            "risk_score": safety_status.risk_score,
        }
    )
    
    # Update in-memory cache
    if input_data.user_id not in user_emotional_history:
        user_emotional_history[input_data.user_id] = []
    
    # Add to front of list to keep most recent first
    user_emotional_history[input_data.user_id].insert(0, state)
    
    # Limit cache size per user
    MAX_HISTORY = 50
    if len(user_emotional_history[input_data.user_id]) > MAX_HISTORY:
        user_emotional_history[input_data.user_id] = user_emotional_history[input_data.user_id][:MAX_HISTORY]
    
    # In production, also store in database
    # await db.emotional_states.insert(state.dict())

def generate_response_content(symbolic_mapping, safety_status, drift_index):
    """Generate appropriate content for response based on safety level"""
    content = {
        "symbolic_reflection": f"The {symbolic_mapping.primary_symbol} symbol connects to the {symbolic_mapping.archetype} archetype, representing a core emotional pattern."
    }
    
    # Add safety level specific content
    if safety_status.level == 1:
        content["grounding_suggestions"] = [
            f"Explore what the {symbolic_mapping.primary_symbol} means to you personally",
            f"Consider how the {symbolic_mapping.archetype} archetype appears in your life"
        ]
    elif safety_status.level == 2:
        content["support_resources"] = [
            "Breathing techniques for emotional regulation",
            "Grounding exercises for present-moment awareness",
            "Connection with supportive individuals"
        ]
    elif safety_status.level == 3:
        content["safety_resources"] = [
            "Crisis support is available to help navigate this challenging moment",
            "Professional resources are being activated to provide support"
        ]
    
    # Add drift-related insights if significant
    if drift_index > 0.5:
        content["drift_insights"] = f"There appears to be a significant shift in your emotional landscape."
    elif drift_index > 0.3:
        content["drift_insights"] = f"There's a moderate change in your emotional patterns."
    
    return content
