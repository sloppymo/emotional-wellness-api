"""
User repository for database operations
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.sql_models import User
from models.schemas import UserCreate, UserBase
from repositories.base import BaseRepository


class UserRepository(BaseRepository[User, UserCreate, UserBase]):
    """User repository for database operations"""
    
    def __init__(self):
        super().__init__(User)
    
    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        """Get a user by username"""
        query = select(User).where(User.username == username)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Get a user by email"""
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def is_superuser(self, db: AsyncSession, user_id: str) -> bool:
        """Check if a user is a superuser"""
        user = await self.get(db, user_id)
        return user is not None and user.is_superuser
    
    async def get_active_users(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
        """Get active users"""
        query = select(User).where(User.is_active == True).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()


# Create singleton instance for global use
user_repository = UserRepository()
