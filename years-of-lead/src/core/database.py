"""
Database connection management for Years of Lead
Handles connections to PostgreSQL and MongoDB
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger

from core.config import settings, get_db_uri, get_mongo_client_settings

# SQLAlchemy setup for PostgreSQL
engine = create_engine(get_db_uri())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# MongoDB setup
mongodb_client = None


async def init_db():
    """Initialize database connections"""
    global mongodb_client
    
    try:
        # PostgreSQL connection
        conn = engine.connect()
        conn.close()
        logger.info("Successfully connected to PostgreSQL")
        
        # MongoDB connection
        mongodb_client = AsyncIOMotorClient(**get_mongo_client_settings())
        await mongodb_client.server_info()  # Verify connection
        logger.info("Successfully connected to MongoDB")
        
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False


def get_db():
    """Get PostgreSQL database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_mongodb():
    """Get MongoDB database connection"""
    global mongodb_client
    if mongodb_client is None:
        mongodb_client = AsyncIOMotorClient(**get_mongo_client_settings())
    
    db = mongodb_client[settings.MONGO_DB]
    return db


def shutdown_db():
    """Close database connections"""
    global mongodb_client
    if mongodb_client:
        mongodb_client.close()
        logger.info("MongoDB connection closed")
