"""
District repository for database operations
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_, func, text

from models.sql_models import District, GameDistrict, faction_district_control
from models.schemas import DistrictBase, DistrictCreate
from repositories.base import BaseRepository


class DistrictRepository(BaseRepository[District, DistrictCreate, DistrictBase]):
    """District repository for database operations"""
    
    def __init__(self):
        super().__init__(District)
    
    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[District]:
        """Get a district by name"""
        query = select(District).where(District.name == name)
        result = await db.execute(query)
        return result.scalars().first()


class GameDistrictRepository(BaseRepository[GameDistrict, Dict[str, Any], Dict[str, Any]]):
    """Game district repository for database operations"""
    
    def __init__(self):
        super().__init__(GameDistrict)
    
    async def get_by_game(self, db: AsyncSession, game_id: str) -> List[GameDistrict]:
        """Get all districts in a game"""
        query = select(GameDistrict).where(GameDistrict.game_id == game_id)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_by_template(self, db: AsyncSession, game_id: str, template_id: str) -> Optional[GameDistrict]:
        """Get a game district by game ID and template ID"""
        query = select(GameDistrict).where(
            and_(
                GameDistrict.game_id == game_id, 
                GameDistrict.district_template_id == template_id
            )
        )
        result = await db.execute(query)
        return result.scalars().first()
    
    async def update_metrics(
        self, 
        db: AsyncSession, 
        district_id: str, 
        security_level: Optional[int] = None,
        unrest_level: Optional[int] = None,
        prosperity_level: Optional[int] = None,
        heat: Optional[int] = None
    ) -> Optional[GameDistrict]:
        """Update district metrics"""
        district = await self.get(db, district_id)
        if not district:
            return None
        
        update_data = {}
        if security_level is not None:
            update_data["security_level"] = max(1, min(10, security_level))
        if unrest_level is not None:
            update_data["unrest_level"] = max(0, min(100, unrest_level))
        if prosperity_level is not None:
            update_data["prosperity_level"] = max(0, min(100, prosperity_level))
        if heat is not None:
            update_data["heat"] = max(0, min(100, heat))
        
        for key, value in update_data.items():
            setattr(district, key, value)
        
        db.add(district)
        await db.commit()
        await db.refresh(district)
        return district
    
    async def get_faction_control(
        self, db: AsyncSession, district_id: str
    ) -> Dict[str, float]:
        """Get faction control percentages for a district"""
        query = select(
            faction_district_control.c.faction_id,
            faction_district_control.c.control_percentage
        ).where(faction_district_control.c.district_id == district_id)
        
        result = await db.execute(query)
        
        # Convert results to dictionary
        control_dict = {}
        for faction_id, percentage in result.all():
            control_dict[faction_id] = percentage
            
        return control_dict
    
    async def update_faction_control(
        self, 
        db: AsyncSession, 
        district_id: str, 
        faction_id: str, 
        control_percentage: float,
        influence: Optional[float] = None,
        heat: Optional[float] = None
    ) -> bool:
        """Update or create faction control in a district"""
        # Check if control record already exists
        query = select(faction_district_control).where(
            and_(
                faction_district_control.c.district_id == district_id,
                faction_district_control.c.faction_id == faction_id
            )
        )
        result = await db.execute(query)
        control = result.first()
        
        update_values = {"control_percentage": max(0.0, min(100.0, control_percentage))}
        if influence is not None:
            update_values["influence"] = max(0.0, min(100.0, influence))
        if heat is not None:
            update_values["heat"] = max(0.0, min(100.0, heat))
        
        if control:
            # Update existing control
            stmt = (
                faction_district_control.update()
                .where(
                    and_(
                        faction_district_control.c.district_id == district_id,
                        faction_district_control.c.faction_id == faction_id
                    )
                )
                .values(**update_values)
            )
            await db.execute(stmt)
        else:
            # Create new control record
            default_values = {"influence": 0.0, "heat": 0.0}
            default_values.update(update_values)
            
            stmt = faction_district_control.insert().values(
                district_id=district_id,
                faction_id=faction_id,
                **default_values
            )
            await db.execute(stmt)
            
        await db.commit()
        return True
    
    async def get_high_tension_districts(
        self, db: AsyncSession, game_id: str, threshold: int = 50
    ) -> List[GameDistrict]:
        """Get districts with high tension (unrest or heat)"""
        query = select(GameDistrict).where(
            and_(
                GameDistrict.game_id == game_id,
                or_(
                    GameDistrict.unrest_level >= threshold,
                    GameDistrict.heat >= threshold
                )
            )
        )
        result = await db.execute(query)
        return result.scalars().all()


# Create singleton instances for global use
district_repository = DistrictRepository()
game_district_repository = GameDistrictRepository()
