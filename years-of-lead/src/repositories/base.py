"""
Base repository for database operations
"""

from typing import Generic, TypeVar, Type, List, Optional, Any, Dict, Union
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update as sql_update, delete as sql_delete

from core.database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base repository for database operations"""
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    async def get(self, db: AsyncSession, id: str) -> Optional[ModelType]:
        """Get a single record by ID"""
        query = select(self.model).where(self.model.id == id)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """Get multiple records"""
        query = select(self.model).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def create(
        self, db: AsyncSession, *, obj_in: Union[CreateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """Create a new record"""
        if isinstance(obj_in, dict):
            obj_data = obj_in
        else:
            obj_data = obj_in.dict(exclude_unset=True)
            
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def update(
        self, 
        db: AsyncSession, 
        *, 
        db_obj: ModelType, 
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """Update a record"""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
            
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
                
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def bulk_update(
        self,
        db: AsyncSession,
        *,
        ids: List[str],
        obj_in: Dict[str, Any]
    ) -> bool:
        """Update multiple records by ID"""
        stmt = (
            sql_update(self.model)
            .where(self.model.id.in_(ids))
            .values(**obj_in)
        )
        
        await db.execute(stmt)
        await db.commit()
        return True
    
    async def delete(self, db: AsyncSession, *, id: str) -> bool:
        """Delete a record by ID"""
        obj = await self.get(db, id)
        if obj:
            await db.delete(obj)
            await db.commit()
            return True
        return False
    
    async def bulk_delete(self, db: AsyncSession, *, ids: List[str]) -> bool:
        """Delete multiple records by ID"""
        stmt = sql_delete(self.model).where(self.model.id.in_(ids))
        await db.execute(stmt)
        await db.commit()
        return True
    
    async def exists(self, db: AsyncSession, *, id: str) -> bool:
        """Check if a record exists by ID"""
        query = select(self.model.id).where(self.model.id == id)
        result = await db.execute(query)
        return result.scalar() is not None
