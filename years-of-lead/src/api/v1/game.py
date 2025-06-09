"""
Game management routes for Years of Lead
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional, Dict, Any
from loguru import logger

from core.database import get_db, get_mongodb
from models.schemas import (
    GameCreate, GameResponse, GameStateResponse,
    GameActionRequest, GameActionResponse, GameEventResponse
)
from services.game_service import GameService
from api.v1.auth import get_current_user
from models.schemas import UserResponse

router = APIRouter()

async def get_game_service(
    mongodb: AsyncIOMotorDatabase = Depends(get_mongodb)
) -> GameService:
    """Get game service instance with MongoDB dependency"""
    return GameService(mongodb)

@router.post("/new", response_model=GameResponse)
async def create_new_game(
    game_data: GameCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    game_service: GameService = Depends(get_game_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new game session"""
    try:
        game = await game_service.create_game(db, game_data, current_user.id)
        return game
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/list", response_model=List[GameResponse])
async def list_games(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    game_service: GameService = Depends(get_game_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """List all games for current user"""
    games = await game_service.get_user_games(db, current_user.id, skip, limit)
    return games

@router.get("/{game_id}", response_model=GameResponse)
async def get_game(
    game_id: str,
    db: AsyncSession = Depends(get_db),
    game_service: GameService = Depends(get_game_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get game information"""
    game = await game_service.get_game(db, game_id)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game {game_id} not found"
        )
    # Check if current user has access to this game
    if game.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this game"
        )
    return game

@router.get("/{game_id}/state", response_model=Dict[str, Any])
async def get_game_state(
    game_id: str,
    db: AsyncSession = Depends(get_db),
    game_service: GameService = Depends(get_game_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get current state of a game"""
    # First ensure user has access to this game
    game = await game_service.get_game(db, game_id)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game {game_id} not found"
        )
    if game.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this game"
        )
        
    # Get full game state including factions, districts, etc.
    # For MVP, we'll implement a simplified state response
    # This should be expanded for a full implementation
    return {
        "game": game.dict(),
        "state": {
            "current_turn": game.current_turn,
            "is_completed": game.is_completed,
            "last_played_at": game.last_played_at
        }
    }

@router.post("/{game_id}/turn", response_model=GameResponse)
async def process_game_turn(
    game_id: str,
    db: AsyncSession = Depends(get_db),
    game_service: GameService = Depends(get_game_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """Process a game turn"""
    # First ensure user has access to this game
    game = await game_service.get_game(db, game_id)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game {game_id} not found"
        )
    if game.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this game"
        )
    
    # Check if game is completed
    if game.is_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Game is already completed"
        )
    
    # Advance turn
    updated_game = await game_service.advance_turn(db, game_id)
    if not updated_game:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to advance game turn"
        )
        
    return updated_game

@router.post("/{game_id}/action", response_model=GameActionResponse)
async def perform_game_action(
    game_id: str,
    action: GameActionRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    game_service: GameService = Depends(get_game_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """Perform an action in the game"""
    # For MVP, we'll just accept actions and log them
    # In a full implementation, we would process these actions through
    # the game engine and return the results
    
    # First ensure user has access to this game
    game = await game_service.get_game(db, game_id)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game {game_id} not found"
        )
    if game.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this game"
        )
    
    # Basic MVP response - this would be expanded in the full implementation
    return GameActionResponse(
        success=True,
        action_type=action.action_type,
        message=f"Action {action.action_type} acknowledged",
        effects=["Detailed effects would be listed here in full implementation"]
    )

@router.get("/{game_id}/events", response_model=List[Dict[str, Any]])
async def list_game_events(
    game_id: str,
    db: AsyncSession = Depends(get_db),
    game_service: GameService = Depends(get_game_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """List events that have occurred in the game"""
    # First ensure user has access to this game
    game = await game_service.get_game(db, game_id)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game {game_id} not found"
        )
    if game.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this game"
        )
    
    # For MVP, return simplified mock events
    # This would be replaced with actual events from the database
    return [
        {
            "id": "evt1",
            "turn": 1,
            "event_type": "game_start",
            "title": "Game Started",
            "description": "A new game session has begun."
        },
        {
            "id": "evt2",
            "turn": game.current_turn,
            "event_type": "turn_completed",
            "title": f"Turn {game.current_turn-1} Completed",
            "description": "The latest game turn has been processed."
        }
    ]
