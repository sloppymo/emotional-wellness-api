"""
Authentication and authorization service
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from repositories.users import user_repository
from models.schemas import UserCreate, UserResponse, Token


class AuthService:
    """Authentication service for user management and authentication"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.settings = get_settings()
        
    def _create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            self.settings.SECRET_KEY, 
            algorithm=self.settings.ALGORITHM
        )
        return encoded_jwt
        
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
        
    def _get_password_hash(self, password: str) -> str:
        """Hash password"""
        return self.pwd_context.hash(password)
        
    async def authenticate_user(
        self, db: AsyncSession, username: str, password: str
    ) -> Optional[UserResponse]:
        """Authenticate a user by username and password"""
        user = await user_repository.get_by_username(db, username)
        
        if not user:
            return None
        if not self._verify_password(password, user.hashed_password):
            return None
            
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at
        )
        
    async def create_user(
        self, db: AsyncSession, user_data: UserCreate
    ) -> UserResponse:
        """Create a new user"""
        # Check if user already exists
        if await user_repository.get_by_username(db, user_data.username):
            raise ValueError(f"Username '{user_data.username}' already registered")
            
        if await user_repository.get_by_email(db, user_data.email):
            raise ValueError(f"Email '{user_data.email}' already registered")
            
        # Create user with hashed password
        hashed_password = self._get_password_hash(user_data.password)
        user_in_db = await user_repository.create(db, obj_in={
            **user_data.dict(exclude={"password"}),
            "hashed_password": hashed_password
        })
        
        return UserResponse(
            id=user_in_db.id,
            username=user_in_db.username,
            email=user_in_db.email,
            full_name=user_in_db.full_name,
            is_active=user_in_db.is_active,
            is_superuser=user_in_db.is_superuser,
            created_at=user_in_db.created_at
        )
        
    async def login(
        self, db: AsyncSession, username: str, password: str
    ) -> Optional[Token]:
        """Login user and return access token"""
        user = await self.authenticate_user(db, username, password)
        
        if not user:
            return None
            
        access_token = self._create_access_token({"sub": user.id})
        
        return Token(access_token=access_token)
        
    async def get_current_user(
        self, db: AsyncSession, token: str
    ) -> Optional[UserResponse]:
        """Get current user from JWT token"""
        try:
            payload = jwt.decode(
                token, 
                self.settings.SECRET_KEY, 
                algorithms=[self.settings.ALGORITHM]
            )
            user_id: str = payload.get("sub")
            
            if user_id is None:
                return None
        except jwt.PyJWTError:
            return None
            
        user = await user_repository.get(db, user_id)
        
        if user is None:
            return None
            
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at
        )
        
    async def is_active(self, user: UserResponse) -> bool:
        """Check if user is active"""
        return user.is_active
        
    async def is_superuser(self, user: UserResponse) -> bool:
        """Check if user is superuser"""
        return user.is_superuser


# Create singleton instance for global use
auth_service = AuthService()
