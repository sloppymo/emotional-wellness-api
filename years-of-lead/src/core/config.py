"""
Configuration settings for Years of Lead
"""

import os
from typing import Dict, Any
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    # API settings
    API_HOST: str = Field(default="0.0.0.0", env="API_HOST")
    API_PORT: int = Field(default=8000, env="API_PORT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Environment settings
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    
    # Database settings
    POSTGRES_USER: str = Field(default="postgres", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(default="postgres", env="POSTGRES_PASSWORD")
    POSTGRES_HOST: str = Field(default="localhost", env="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(default=5432, env="POSTGRES_PORT")
    POSTGRES_DB: str = Field(default="years_of_lead", env="POSTGRES_DB")
    
    # MongoDB settings
    MONGO_URI: str = Field(default="mongodb://localhost:27017", env="MONGO_URI")
    MONGO_DB: str = Field(default="years_of_lead", env="MONGO_DB")
    
    # Security settings
    SECRET_KEY: str = Field(default="development_secret_key", env="SECRET_KEY")
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # SYLVA API settings
    SYLVA_API_KEY: str = Field(default="", env="SYLVA_API_KEY")
    SYLVA_API_URL: str = Field(default="", env="SYLVA_API_URL")
    
    # WREN API settings
    WREN_API_KEY: str = Field(default="", env="WREN_API_KEY")
    WREN_API_URL: str = Field(default="", env="WREN_API_URL")
    
    # Game settings
    MAX_TURNS: int = Field(default=100, env="MAX_TURNS")
    INITIAL_RESOURCES: int = Field(default=1000, env="INITIAL_RESOURCES")
    
    # Logging settings
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

def get_db_uri() -> str:
    """Get the PostgreSQL database URI"""
    return f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"

def get_mongo_client_settings() -> Dict[str, Any]:
    """Get the MongoDB client settings"""
    return {
        "host": settings.MONGO_URI,
        "serverSelectionTimeoutMS": 5000,
    }
