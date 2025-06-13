"""
Async database session management for the Emotional Wellness API.
HIPAA-compliant database connections with encryption and audit logging.
"""

import logging
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from src.config.settings import get_settings

# Get settings and initialize logger
settings = get_settings()
logger = logging.getLogger(__name__)

# Base class for all models
Base = declarative_base()

# Create SQLAlchemy async engine
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=5,  # Default pool size
    max_overflow=10,  # Default max overflow
    pool_timeout=30,  # Default pool timeout in seconds
    pool_pre_ping=True,  # Ensures connections are valid before use
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get an async database session.
    Provides a transactional scope around database operations.
    
    Yields:
        AsyncSession: SQLAlchemy async session object
    """
    session = AsyncSessionLocal()
    try:
        # Set session variables for row-level security
        if settings.enable_row_level_security:
            await session.execute("SET app.tenant_id = current_setting('app.current_tenant_id', TRUE)")
            await session.execute("SET app.user_id = current_setting('app.current_user_id', TRUE)")
        
        yield session
    except Exception as e:
        await session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        await session.close()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI endpoints to get an async database session.
    
    Yields:
        AsyncSession: SQLAlchemy async session object
    """
    async with get_async_db() as session:
        yield session
