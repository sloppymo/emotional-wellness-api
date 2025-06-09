"""
Player-related routes for Years of Lead
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Dict, Any, Optional
from loguru import logger

from core.database import get_db, get_mongodb
from models.schemas import (
    PlayerCharacterCreate, PlayerCharacterResponse,
    CellCreate, CellResponse, JournalEntryCreate, JournalEntryResponse
)
from services.faction_service import FactionService
from api.v1.auth import get_current_user
from models.schemas import UserResponse

router = APIRouter()

@router.get("/game/{game_id}/characters", response_model=List[Dict[str, Any]])
async def list_player_characters(
    game_id: str,
    db: AsyncSession = Depends(get_db),
    mongodb: AsyncIOMotorDatabase = Depends(get_mongodb),
    current_user: UserResponse = Depends(get_current_user)
):
    """List all player characters in a game"""
    # For MVP, we'll return simplified player characters
    # In a full implementation, we would fetch from database
    return [
        {
            "id": "char1",
            "name": "Eduardo Silva",
            "faction": "anarchists",
            "background": "Former union organizer turned radical",
            "heat": 25,
            "skills": {
                "rhetoric": 8,
                "infiltration": 6,
                "tactical": 4
            }
        },
        {
            "id": "char2",
            "name": "Maria Contreras",
            "faction": "separatists",
            "background": "Regional independence advocate",
            "heat": 15,
            "skills": {
                "command": 7,
                "intelligence": 8,
                "diplomacy": 5
            }
        }
    ]

@router.post("/game/{game_id}/character", response_model=Dict[str, Any])
async def create_player_character(
    game_id: str,
    character_data: PlayerCharacterCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    mongodb: AsyncIOMotorDatabase = Depends(get_mongodb),
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new player character for a game"""
    # For MVP, we'll return a mock response
    # In a full implementation, we would create in the database
    return {
        "id": "new_char_id",
        "game_id": game_id,
        "name": character_data.name,
        "background": character_data.background,
        "skills": character_data.skills if character_data.skills else {},
        "traits": character_data.traits if character_data.traits else [],
        "heat": 0,
        "created_at": "2023-06-08T00:00:00Z"
    }

@router.get("/character/{character_id}", response_model=Dict[str, Any])
async def get_player_character(
    character_id: str,
    db: AsyncSession = Depends(get_db),
    mongodb: AsyncIOMotorDatabase = Depends(get_mongodb),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get specific player character details"""
    # For MVP, return mock data
    # In a full implementation, we would fetch from database
    if character_id == "char1":
        return {
            "id": "char1",
            "name": "Eduardo Silva",
            "faction": "anarchists",
            "background": "Former union organizer turned radical",
            "heat": 25,
            "skills": {
                "rhetoric": 8,
                "infiltration": 6,
                "tactical": 4
            },
            "traits": ["Charismatic", "Paranoid"],
            "cells_commanded": 2,
            "operations_led": 5
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Character with ID {character_id} not found"
        )

@router.post("/character/{character_id}/cell", response_model=Dict[str, Any])
async def create_cell(
    character_id: str,
    cell_data: CellCreate = Body(...),
    faction_id: str = Query(..., description="Faction ID for the new cell"),
    district_id: str = Query(..., description="District ID for the new cell"),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new cell for a player character"""
    # For MVP, return mock data
    # In a full implementation, we would create in the database
    faction_service = FactionService(db)
    
    # Simple validation
    faction = await faction_service.get_faction(faction_id)
    if not faction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Faction with ID {faction_id} not found"
        )
    
    return {
        "id": "new_cell_id",
        "name": cell_data.name,
        "faction_id": faction_id,
        "district_id": district_id,
        "leader_id": character_id,
        "size": cell_data.size,
        "cover_strength": 5,
        "morale": 7,
        "heat": 0,
        "skill_levels": cell_data.skill_levels if cell_data.skill_levels else {}
    }

@router.get("/character/{character_id}/journal", response_model=List[Dict[str, Any]])
async def get_player_journal(
    character_id: str,
    game_id: str,
    mongodb: AsyncIOMotorDatabase = Depends(get_mongodb),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get player's journal entries (SYLVA integration)"""
    # For MVP, return mock journal entries
    # In a full implementation, we would fetch from MongoDB and integrate with SYLVA
    return [
        {
            "id": "journal1",
            "character_id": character_id,
            "game_id": game_id,
            "turn": 1,
            "timestamp": "2023-06-08T10:00:00Z",
            "title": "First Steps",
            "content": "Today I begin the struggle for our cause. The government cannot continue to ignore us.",
            "emotional_tags": [
                {"name": "determination", "value": 0.8},
                {"name": "anger", "value": 0.6}
            ]
        },
        {
            "id": "journal2",
            "character_id": character_id,
            "game_id": game_id,
            "turn": 2,
            "timestamp": "2023-06-09T10:00:00Z",
            "title": "Growing Concern",
            "content": "Our cell was almost discovered today. We need to be more careful about our movements.",
            "emotional_tags": [
                {"name": "fear", "value": 0.7},
                {"name": "anxiety", "value": 0.8}
            ]
        }
    ]

@router.post("/character/{character_id}/journal", response_model=Dict[str, Any])
async def create_journal_entry(
    character_id: str,
    game_id: str,
    entry_data: JournalEntryCreate = Body(...),
    mongodb: AsyncIOMotorDatabase = Depends(get_mongodb),
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new journal entry for a player character (with SYLVA integration)"""
    # For MVP, return mock data without actual SYLVA integration
    # In a full implementation, we would integrate with SYLVA API
    return {
        "id": "new_journal_id",
        "character_id": character_id,
        "game_id": game_id,
        "turn": 3,  # Would be determined from game state
        "timestamp": "2023-06-10T10:00:00Z",
        "title": entry_data.title if entry_data.title else "Untitled Entry",
        "content": entry_data.content,
        "emotional_tags": [
            {"name": "determination", "value": 0.6},
            {"name": "hope", "value": 0.5}
        ],
        "narrative_context": {
            "suggestion": "Consider how your character's paranoia might affect their leadership decisions."
        }
    }
