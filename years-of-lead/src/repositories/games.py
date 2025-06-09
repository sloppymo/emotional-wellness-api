"""
Game repository for database operations
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, and_

from models.sql_models import Game, GameFaction, GameDistrict
from models.schemas import NewGameRequest, GameStateResponse
from repositories.base import BaseRepository


class GameRepository(BaseRepository[Game, NewGameRequest, GameStateResponse]):
    """Game repository for database operations"""
    
    def __init__(self):
        super().__init__(Game)
    
    async def get_games_by_user(
        self, db: AsyncSession, user_id: str, skip: int = 0, limit: int = 100
    ) -> List[Game]:
        """Get games by user ID"""
        query = select(Game).where(Game.user_id == user_id).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_active_games_by_user(
        self, db: AsyncSession, user_id: str, skip: int = 0, limit: int = 100
    ) -> List[Game]:
        """Get active (not completed) games by user ID"""
        query = (
            select(Game)
            .where(and_(Game.user_id == user_id, Game.is_completed == False))
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_latest_game_by_user(self, db: AsyncSession, user_id: str) -> Optional[Game]:
        """Get the latest game by user ID"""
        query = (
            select(Game)
            .where(Game.user_id == user_id)
            .order_by(desc(Game.last_played_at))
            .limit(1)
        )
        result = await db.execute(query)
        return result.scalars().first()
    
    async def increment_turn(self, db: AsyncSession, game_id: str) -> Optional[Game]:
        """Increment the turn counter for a game"""
        game = await self.get(db, game_id)
        if not game:
            return None
        
        game.current_turn += 1
        db.add(game)
        await db.commit()
        await db.refresh(game)
        return game
    
    async def update_last_played(self, db: AsyncSession, game_id: str) -> Optional[Game]:
        """Update the last_played_at timestamp for a game"""
        game = await self.get(db, game_id)
        if not game:
            return None
        
        from datetime import datetime
        game.last_played_at = datetime.now()
        db.add(game)
        await db.commit()
        await db.refresh(game)
        return game
    
    async def complete_game(self, db: AsyncSession, game_id: str) -> Optional[Game]:
        """Mark a game as completed"""
        game = await self.get(db, game_id)
        if not game:
            return None
        
        game.is_completed = True
        db.add(game)
        await db.commit()
        await db.refresh(game)
        return game


# Create singleton instance for global use
game_repository = GameRepository()
