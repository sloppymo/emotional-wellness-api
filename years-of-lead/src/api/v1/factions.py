"""
Faction-related routes for Years of Lead
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from loguru import logger

from core.database import get_db
from models.schemas import FactionResponse, FactionCreate, FactionRelationshipResponse, OperationResponse
from services.faction_service import FactionService
from api.v1.auth import get_current_user
from models.schemas import UserResponse
from models.sql_models import FactionType, IdeologyType

router = APIRouter()

@router.get("/", response_model=List[FactionResponse])
async def list_factions(
    faction_type: Optional[FactionType] = None,
    ideology: Optional[IdeologyType] = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """List all available factions with optional filtering"""
    faction_service = FactionService(db)
    
    if faction_type and ideology:
        factions = await faction_service.get_factions_by_type_and_ideology(faction_type, ideology)
    elif faction_type:
        factions = await faction_service.get_factions_by_type(faction_type)
    elif ideology:
        factions = await faction_service.get_factions_by_ideology(ideology)
    else:
        factions = await faction_service.get_all_factions()
        
    return factions

@router.get("/{faction_id}", response_model=FactionResponse)
async def get_faction(
    faction_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get specific faction details"""
    faction_service = FactionService(db)
    faction = await faction_service.get_faction(faction_id)
    
    if not faction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Faction with ID {faction_id} not found"
        )
        
    return faction

@router.get("/game/{game_id}/factions", response_model=List[Dict[str, Any]])
async def get_game_factions(
    game_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get all factions in a specific game"""
    faction_service = FactionService(db)
    game_factions = await faction_service.get_factions_by_game(game_id)
    
    # For MVP, we'll return simplified faction information
    result = []
    for gf in game_factions:
        faction = await faction_service.get_faction(gf.faction_id)
        if faction:
            result.append({
                "id": gf.faction_id,
                "name": faction.name,
                "faction_type": faction.faction_type,
                "ideology": faction.ideology,
                "game_specific": {
                    "is_player_faction": gf.is_player_faction,
                    "influence": gf.influence,
                    "resources": gf.resources,
                    "support": gf.support
                }
            })
    
    return result

@router.get("/{faction_id}/relationships", response_model=List[FactionRelationshipResponse])
async def get_faction_relationships(
    faction_id: str,
    game_id: Optional[str] = Query(None, description="Filter by game ID"),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get faction relationships with other factions"""
    faction_service = FactionService(db)
    
    # Check if faction exists
    faction = await faction_service.get_faction(faction_id)
    if not faction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Faction with ID {faction_id} not found"
        )
    
    if game_id:
        # Get relationships in specific game
        relationships = await faction_service.get_faction_relationships_in_game(game_id, faction_id)
    else:
        # Get default faction relationships
        relationships = await faction_service.get_faction_relationships(faction_id)
    
    return relationships

@router.get("/{faction_id}/operations", response_model=List[Dict[str, Any]])
async def get_faction_operations(
    faction_id: str,
    game_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get operations associated with a faction in a specific game"""
    faction_service = FactionService(db)
    
    # Check if faction exists in the game
    game_faction = await faction_service.get_game_faction(game_id, faction_id)
    if not game_faction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Faction with ID {faction_id} not found in game {game_id}"
        )
    
    # For MVP, we'll return simplified operations data
    # In a full implementation, we would fetch actual operations from the database
    return [
        {
            "id": "op1",
            "name": "Urban Recruitment",
            "type": "RECRUITMENT",
            "district": "Downtown",
            "stage": "PLANNING",
            "turns_remaining": 2,
            "success_probability": 0.75
        },
        {
            "id": "op2",
            "name": "Media Infiltration",
            "type": "INFLUENCE",
            "district": "Media District",
            "stage": "EXECUTION",
            "turns_remaining": 1,
            "success_probability": 0.6
        }
    ]
