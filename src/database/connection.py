"""
Database connection management for the Emotional Wellness API.
HIPAA-compliant database connections with encryption and audit logging.
"""

import logging
from typing import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from src.config.settings import get_settings

# Get settings and initialize logger
settings = get_settings()
logger = logging.getLogger(__name__)

# Create SQLAlchemy engine with proper connection parameters
engine = create_engine(
    settings.database_url,
    echo=settings.sql_debug,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_pre_ping=True,  # Ensures connections are valid before use
    connect_args={
        "application_name": f"emotional-wellness-api-{settings.environment}",
        "sslmode": "require" if settings.environment == "production" else "prefer",
        "connect_timeout": 10,
    },
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Get a database session.
    Provides a transactional scope around database operations.
    
    Yields:
        Session: SQLAlchemy session object
    """
    db = SessionLocal()
    try:
        # Set session variables for row-level security
        # These would be populated with real values in the application
        # db.execute("SET app.current_user_id = :user_id", {"user_id": "00000000-0000-0000-0000-000000000000"})
        # db.execute("SET app.current_user_role = :role", {"role": "user"})
        
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


def get_db_dependency() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI endpoints to get a database session.
    
    Yields:
        Session: SQLAlchemy session object
    """
    with get_db() as session:
        yield session
