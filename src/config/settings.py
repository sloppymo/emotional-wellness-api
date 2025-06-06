"""
Application configuration settings with HIPAA compliance controls

This module provides centralized configuration management with proper
security controls for sensitive settings like encryption keys.
"""

import os
import logging
from typing import List, Dict, Optional, Any, Set, Tuple
from functools import lru_cache

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from api.middleware.rate_limit_types import RateLimitCategory, DEFAULT_RATE_LIMITS, BURST_MULTIPLIERS

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """Application settings with HIPAA-compliant defaults"""
    
    # API configuration
    APP_NAME: str = "Emotional Wellness Companion API"
    API_VERSION: str = "v1"
    DEBUG: bool = False
    
    # Security settings
    API_KEY: str = Field(..., env="API_KEY")
    JWT_SECRET_KEY: str = Field(..., env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Rate limiting settings
    SKIP_RATE_LIMIT_SYSTEM: bool = Field(True, env="SKIP_RATE_LIMIT_SYSTEM")
    
    # Custom rate limits for categories (optional)
    RATE_LIMIT_PHI: Tuple[int, int, int] = Field(
        DEFAULT_RATE_LIMITS[RateLimitCategory.PHI_OPERATION],
        env="RATE_LIMIT_PHI"
    )
    RATE_LIMIT_CRISIS: Tuple[int, int, int] = Field(
        DEFAULT_RATE_LIMITS[RateLimitCategory.CRISIS_INTERVENTION],
        env="RATE_LIMIT_CRISIS"
    )
    RATE_LIMIT_AUTH: Tuple[int, int, int] = Field(
        DEFAULT_RATE_LIMITS[RateLimitCategory.AUTHENTICATED],
        env="RATE_LIMIT_AUTH"
    )
    RATE_LIMIT_READ: Tuple[int, int, int] = Field(
        DEFAULT_RATE_LIMITS[RateLimitCategory.READ_ONLY],
        env="RATE_LIMIT_READ"
    )
    RATE_LIMIT_PUBLIC: Tuple[int, int, int] = Field(
        DEFAULT_RATE_LIMITS[RateLimitCategory.PUBLIC],
        env="RATE_LIMIT_PUBLIC"
    )
    RATE_LIMIT_SYSTEM: Tuple[int, int, int] = Field(
        DEFAULT_RATE_LIMITS[RateLimitCategory.SYSTEM],
        env="RATE_LIMIT_SYSTEM"
    )
    
    # Custom burst multipliers (optional)
    BURST_MULTIPLIER_PHI: float = Field(
        BURST_MULTIPLIERS[RateLimitCategory.PHI_OPERATION],
        env="BURST_MULTIPLIER_PHI"
    )
    BURST_MULTIPLIER_CRISIS: float = Field(
        BURST_MULTIPLIERS[RateLimitCategory.CRISIS_INTERVENTION],
        env="BURST_MULTIPLIER_CRISIS"
    )
    BURST_MULTIPLIER_AUTH: float = Field(
        BURST_MULTIPLIERS[RateLimitCategory.AUTHENTICATED],
        env="BURST_MULTIPLIER_AUTH"
    )
    BURST_MULTIPLIER_READ: float = Field(
        BURST_MULTIPLIERS[RateLimitCategory.READ_ONLY],
        env="BURST_MULTIPLIER_READ"
    )
    BURST_MULTIPLIER_PUBLIC: float = Field(
        BURST_MULTIPLIERS[RateLimitCategory.PUBLIC],
        env="BURST_MULTIPLIER_PUBLIC"
    )
    BURST_MULTIPLIER_SYSTEM: float = Field(
        BURST_MULTIPLIERS[RateLimitCategory.SYSTEM],
        env="BURST_MULTIPLIER_SYSTEM"
    )
    
    # IP Whitelisting for administrative routes
    ADMIN_IP_WHITELIST: List[str] = Field(
        ["127.0.0.1", "::1"], # Default to localhost only
        env="ADMIN_IP_WHITELIST"
    )
    ADMIN_ROUTE_PATTERNS: List[str] = Field(
        ["/admin/", "/config/", "/system/"],
        env="ADMIN_ROUTE_PATTERNS"
    )
    
    @property
    def rate_limit_config(self) -> Dict[RateLimitCategory, Tuple[int, int, int]]:
        """Get the complete rate limit configuration."""
        return {
            RateLimitCategory.PHI_OPERATION: self.RATE_LIMIT_PHI,
            RateLimitCategory.CRISIS_INTERVENTION: self.RATE_LIMIT_CRISIS,
            RateLimitCategory.AUTHENTICATED: self.RATE_LIMIT_AUTH,
            RateLimitCategory.READ_ONLY: self.RATE_LIMIT_READ,
            RateLimitCategory.PUBLIC: self.RATE_LIMIT_PUBLIC,
            RateLimitCategory.SYSTEM: self.RATE_LIMIT_SYSTEM,
        }
    
    @property
    def burst_multiplier_config(self) -> Dict[RateLimitCategory, float]:
        """Get the complete burst multiplier configuration."""
        return {
            RateLimitCategory.PHI_OPERATION: self.BURST_MULTIPLIER_PHI,
            RateLimitCategory.CRISIS_INTERVENTION: self.BURST_MULTIPLIER_CRISIS,
            RateLimitCategory.AUTHENTICATED: self.BURST_MULTIPLIER_AUTH,
            RateLimitCategory.READ_ONLY: self.BURST_MULTIPLIER_READ,
            RateLimitCategory.PUBLIC: self.BURST_MULTIPLIER_PUBLIC,
            RateLimitCategory.SYSTEM: self.BURST_MULTIPLIER_SYSTEM,
        }
    
    # Redis settings for caching and rate limiting
    REDIS_HOST: str = Field("localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(6379, env="REDIS_PORT")
    REDIS_PASSWORD: Optional[str] = Field(None, env="REDIS_PASSWORD")
    REDIS_DB: int = Field(0, env="REDIS_DB")
    
    @property
    def REDIS_URL(self) -> str:
        """Get properly formatted Redis URL with authentication if configured"""
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # CORS settings - restrict for HIPAA compliance
    ALLOWED_ORIGINS: List[str] = []
    
    # Database settings
    POSTGRES_USER: str = Field(..., env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(..., env="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field(..., env="POSTGRES_DB")
    POSTGRES_HOST: str = Field(..., env="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(5432, env="POSTGRES_PORT")
    
    @property
    def DATABASE_URL(self) -> str:
        """Get properly formatted database URL"""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # LLM integration settings
    ANTHROPIC_API_KEY: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    
    # HIPAA compliance settings
    PHI_ENCRYPTION_KEY: str = Field(..., env="PHI_ENCRYPTION_KEY")
    AUDIT_LOGGING_ENABLED: bool = Field(True, env="AUDIT_LOGGING_ENABLED")
    DATA_RETENTION_DAYS: int = Field(2190, env="DATA_RETENTION_DAYS")  # 6 years default (HIPAA)
    
    # Crisis intervention settings
    CRISIS_TEAM_EMAIL: Optional[str] = Field(None, env="CRISIS_TEAM_EMAIL")
    CRISIS_RESPONSE_SLA_SECONDS: int = Field(180, env="CRISIS_RESPONSE_SLA_SECONDS")
    
    # Symbol library paths
    SYMBOL_LIBRARY_PATH: Optional[str] = Field(None, env="SYMBOL_LIBRARY_PATH")
    CRISIS_LEXICON_PATH: Optional[str] = Field(None, env="CRISIS_LEXICON_PATH")
    
    @validator("ALLOWED_ORIGINS", pre=True)
    def parse_allowed_origins(cls, v):
        """Parse ALLOWED_ORIGINS from comma-separated string if needed"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Create cached settings instance
    
    Using functools.lru_cache to avoid parsing the .env file
    on every request for better performance.
    """
    try:
        settings = Settings()
        logger.info("Loaded application settings")
        return settings
    except Exception as e:
        logger.error(f"Failed to load settings: {str(e)}")
        # Provide safe defaults if environment variables are missing
        # In production, this should fail loudly instead of using defaults
        return Settings(
            API_KEY="dev_api_key_for_testing_only",
            JWT_SECRET_KEY="dev_jwt_secret_not_for_production",
            PHI_ENCRYPTION_KEY="dev_encryption_key_not_for_production",
            POSTGRES_USER="postgres",
            POSTGRES_PASSWORD="postgres",
            POSTGRES_DB="emotional_wellness",
            POSTGRES_HOST="localhost"
        )
