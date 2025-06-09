"""
API Routes for Years of Lead
"""

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

api_router = APIRouter()

# Import and include routers from other modules
from api.v1.auth import router as auth_router
from api.v1.factions import router as factions_router
from api.v1.game import router as game_router
from api.v1.players import router as players_router

# Include all routers
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(factions_router, prefix="/factions", tags=["Factions"])
api_router.include_router(game_router, prefix="/game", tags=["Game"])
api_router.include_router(players_router, prefix="/players", tags=["Players"])

@api_router.get("/")
async def root():
    """Root endpoint for API verification"""
    return {"message": "Welcome to Years of Lead API"}
