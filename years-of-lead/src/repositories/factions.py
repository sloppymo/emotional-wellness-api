"""
Faction repository for database operations
"""

from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_, func, text

from models.sql_models import Faction, GameFaction, faction_relationships
from models.schemas import FactionBase, FactionCreate
from repositories.base import BaseRepository


class FactionRepository(BaseRepository[Faction, FactionCreate, FactionBase]):
    """Faction repository for database operations"""
    
    def __init__(self):
        super().__init__(Faction)
    
    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Faction]:
        """Get a faction by name"""
        query = select(Faction).where(Faction.name == name)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_by_type(self, db: AsyncSession, faction_type: str) -> List[Faction]:
        """Get factions by type"""
        query = select(Faction).where(Faction.faction_type == faction_type)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_by_ideology(self, db: AsyncSession, ideology: str) -> List[Faction]:
        """Get factions by ideology"""
        query = select(Faction).where(Faction.ideology == ideology)
        result = await db.execute(query)
        return result.scalars().all()


class GameFactionRepository(BaseRepository[GameFaction, Dict[str, Any], Dict[str, Any]]):
    """Game faction repository for database operations"""
    
    def __init__(self):
        super().__init__(GameFaction)
    
    async def get_by_game(self, db: AsyncSession, game_id: str) -> List[GameFaction]:
        """Get all factions in a game"""
        query = select(GameFaction).where(GameFaction.game_id == game_id)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_player_faction(self, db: AsyncSession, game_id: str) -> Optional[GameFaction]:
        """Get the player's faction in a game"""
        query = select(GameFaction).where(
            and_(GameFaction.game_id == game_id, GameFaction.is_player_faction == True)
        )
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_by_template(self, db: AsyncSession, game_id: str, template_id: str) -> Optional[GameFaction]:
        """Get a game faction by game ID and template ID"""
        query = select(GameFaction).where(
            and_(
                GameFaction.game_id == game_id, 
                GameFaction.faction_template_id == template_id
            )
        )
        result = await db.execute(query)
        return result.scalars().first()
    
    async def update_resources(
        self, db: AsyncSession, faction_id: str, resources: Dict[str, int]
    ) -> Optional[GameFaction]:
        """Update faction resources"""
        faction = await self.get(db, faction_id)
        if not faction:
            return None
        
        # Merge the existing resources with the new resources
        current_resources = faction.resources or {}
        for resource_type, amount in resources.items():
            if resource_type in current_resources:
                current_resources[resource_type] += amount
            else:
                current_resources[resource_type] = amount
        
        # Ensure no resource is negative
        for resource_type in current_resources:
            if current_resources[resource_type] < 0:
                current_resources[resource_type] = 0
                
        faction.resources = current_resources
        db.add(faction)
        await db.commit()
        await db.refresh(faction)
        return faction
    
    async def get_relationships(
        self, db: AsyncSession, faction_id: str
    ) -> Dict[str, int]:
        """Get all relationships for a faction"""
        # Query for relationships where this faction is the primary faction
        query1 = select(
            faction_relationships.c.other_faction_id, 
            faction_relationships.c.relationship_value
        ).where(faction_relationships.c.faction_id == faction_id)
        
        # Query for relationships where this faction is the other faction
        query2 = select(
            faction_relationships.c.faction_id, 
            faction_relationships.c.relationship_value
        ).where(faction_relationships.c.other_faction_id == faction_id)
        
        result1 = await db.execute(query1)
        result2 = await db.execute(query2)
        
        # Combine results into a dictionary
        relationships = {}
        for other_id, value in result1.all():
            relationships[other_id] = value
            
        for other_id, value in result2.all():
            # For reciprocal relationships, we use the same value
            relationships[other_id] = value
            
        return relationships
    
    async def update_relationship(
        self, db: AsyncSession, faction_id: str, other_faction_id: str, value: int
    ) -> bool:
        """Update or create a relationship between factions"""
        # Check if relationship already exists
        query = select(faction_relationships).where(
            and_(
                faction_relationships.c.faction_id == faction_id,
                faction_relationships.c.other_faction_id == other_faction_id
            )
        )
        result = await db.execute(query)
        relationship = result.first()
        
        if relationship:
            # Update existing relationship
            stmt = (
                faction_relationships.update()
                .where(
                    and_(
                        faction_relationships.c.faction_id == faction_id,
                        faction_relationships.c.other_faction_id == other_faction_id
                    )
                )
                .values(relationship_value=value)
            )
            await db.execute(stmt)
        else:
            # Create new relationship
            stmt = faction_relationships.insert().values(
                faction_id=faction_id,
                other_faction_id=other_faction_id,
                relationship_value=value
            )
            await db.execute(stmt)
            
        await db.commit()
        return True


# Create singleton instances for global use
faction_repository = FactionRepository()
game_faction_repository = GameFactionRepository()
