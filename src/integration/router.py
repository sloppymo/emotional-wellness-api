"""
FastAPI router for SYLVA-WREN integration endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends
from src.integration.models import EmotionalInput, IntegratedResponse
from src.integration.coordinator import SylvaWrenCoordinator
from redis.asyncio import Redis
import asyncio

router = APIRouter(prefix="/integration", tags=["SYLVA-WREN Integration"])

# Dependency for coordinator instance (expand as needed)
async def get_coordinator() -> SylvaWrenCoordinator:
    redis = Redis()
    return SylvaWrenCoordinator(redis=redis)

@router.post("/process", response_model=IntegratedResponse)
async def process_emotional_input(
    input_data: EmotionalInput,
    coordinator: SylvaWrenCoordinator = Depends(get_coordinator)
):
    """
    Process user emotional input and return integrated symbolic-narrative response.
    """
    try:
        return await coordinator.process_emotional_input(input_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
