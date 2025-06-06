import pytest
import asyncio
from unittest.mock import AsyncMock, patch

# Mock Redis before importing coordinator which depends on it
sys_modules_patcher = patch.dict('sys.modules', {'redis.asyncio': AsyncMock()})
sys_modules_patcher.start()

from integration.coordinator import SylvaWrenCoordinator
from integration.models import EmotionalInput, UserContext, IntegratedResponse, SceneType

@pytest.mark.asyncio
async def test_process_emotional_input_happy_path():
    coordinator = SylvaWrenCoordinator()
    user_ctx = UserContext(user_id="testuser", preferences={}, session_id="sess1", cultural_context={})
    input_data = EmotionalInput(
        text_content="I feel hopeful about tomorrow.",
        detected_emotions=["hopeful"],
        context_factors={},
        user_context=user_ctx
    )
    response = await coordinator.process_emotional_input(input_data)
    assert isinstance(response, IntegratedResponse)
    assert "wellness journey" in response.response_text

@pytest.mark.asyncio
async def test_process_emotional_input_validation_error():
    coordinator = SylvaWrenCoordinator()
    # Missing required user_context
    with pytest.raises(Exception):
        input_data = EmotionalInput(
            text_content="I feel anxious.",
            detected_emotions=["anxious"],
            context_factors={},
            user_context=None # type: ignore
        )
        await coordinator.process_emotional_input(input_data)
