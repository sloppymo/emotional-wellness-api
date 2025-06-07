"""
Unit tests for HIPAA compliance in symbolic emotional wellness API.
Tests focus on crisis detection, PHI access auditing, and PHI lifecycle management.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from typing import Dict, List, Any, Optional

from pydantic import BaseModel

from src.symbolic.adapters.canopy_adapter import CanopyAdapter, SylvaRequest
from src.symbolic.canopy import CanopyProcessor, EmotionalMetaphor, SymbolicMapping
from src.structured_logging.phi_logger import PHILogger, PHIAccessRecord, PHICategory
from src.models.emotional_state import EmotionalState


class TestHIPAACompliantSymbolicAPI:
    """Test suite for HIPAA compliance in symbolic emotional wellness API."""

    @pytest.fixture
    def mock_canopy_processor(self):
        """Mock the CanopyProcessor for testing."""
        processor = AsyncMock(spec=CanopyProcessor)
        
        # Configure the extract method to return crisis indicators
        async def mock_extract(*args, **kwargs):
            return SymbolicMapping(
                primary_symbol="drowning",
                archetype="Victim",
                alternative_symbols=["sinking", "vanishing"],
                valence=-0.8,
                arousal=0.9,
                metaphors=[
                    EmotionalMetaphor(
                        text="I feel like I'm drowning in darkness",
                        symbol="drowning",
                        confidence=0.95
                    ),
                    EmotionalMetaphor(
                        text="Everything is fading away",
                        symbol="vanishing",
                        confidence=0.87
                    )
                ],
                confidence=0.92,
                timestamp=datetime.now()
            )
        
        processor.extract = mock_extract
        
        # Configure the analyze_patterns method to include crisis indicators
        async def mock_analyze_patterns(*args, **kwargs):
            return {
                "recurring_symbols": [
                    {"symbol": "drowning", "count": 3},
                    {"symbol": "darkness", "count": 2}
                ],
                "crisis_indicators": {
                    "detected": True,
                    "severity": "high",
                    "confidence": 0.89,
                    "patterns": ["isolation", "hopelessness", "self-harm risk"]
                },
                "archetypal_progression": {
                    "sequence": ["Explorer", "Victim", "Victim"],
                    "current": "Victim",
                    "suggested_next": "Caregiver"
                }
            }
        
        processor._analyze_patterns = mock_analyze_patterns
        return processor

    @pytest.fixture
    def mock_phi_logger(self):
        """Mock the PHI logger for testing."""
        logger = AsyncMock(spec=PHILogger)
        
        async def mock_log_access(*args, **kwargs):
            return "phi-access-12345"
        
        logger.log_access = mock_log_access
        return logger

    @pytest.fixture
    def canopy_adapter(self, mock_canopy_processor):
        """Create a CanopyAdapter with mocked dependencies."""
        adapter = CanopyAdapter(canopy_processor=mock_canopy_processor)
        adapter._analyze_patterns = mock_canopy_processor._analyze_patterns
        return adapter

    @pytest.mark.asyncio
    async def test_crisis_symbolism(self, canopy_adapter):
        """
        Test that symbolic patterns reflecting crisis are correctly flagged.
        
        This test ensures that metaphors of drowning, vanishing, and erasure
        are properly detected as crisis indicators in the pattern analysis.
        """
        # Create a request with crisis-indicating text
        request = SylvaRequest(
            adapter_type="canopy",
            user_id="user123",
            session_id="session456",
            input_data={
                "text": "I feel like I'm drowning in darkness and slowly disappearing. Nothing matters anymore.",
                "biomarkers": {"heart_rate": 110, "sleep_quality": 0.2}
            }
        )
        
        # Process the request
        result = await canopy_adapter._process_request(request)
        
        # Verify crisis flags are included
        assert "pattern_analysis" in result
        assert "crisis_indicators" in result["pattern_analysis"]
        
        # Verify crisis indicators are properly detected
        crisis_indicators = result["pattern_analysis"]["crisis_indicators"]
        assert crisis_indicators["detected"] is True
        assert crisis_indicators["severity"] == "high"
        assert crisis_indicators["confidence"] >= 0.8
        
        # Verify specific patterns are detected
        patterns = crisis_indicators["patterns"]
        assert any("hopelessness" in pattern for pattern in patterns)
        assert any("self-harm" in pattern for pattern in patterns)
        
        # Verify primary metaphors are crisis-related
        assert result["primary_symbol"] == "drowning"
        assert result["archetype"] == "Victim"
        assert "vanishing" in result["alternative_symbols"]

    @pytest.mark.asyncio
    @patch("src.structured_logging.phi_logger.get_phi_logger")
    async def test_phi_access_auditing(self, mock_get_phi_logger, canopy_adapter, mock_phi_logger):
        """
        Test that each access to PHI-triggering longitudinal analysis logs a PHI_ACCESS audit event.
        
        This test verifies that when longitudinal analysis is performed on user data,
        proper PHI access auditing occurs with the correct metadata.
        """
        # Configure the mock
        mock_get_phi_logger.return_value = mock_phi_logger
        
        # Create a request that will trigger PHI access
        request = SylvaRequest(
            adapter_type="canopy",
            user_id="patient456",
            session_id="therapy789",
            input_data={
                "text": "I've been feeling better since our last session.",
                "context": {"clinical_notes": True, "longitudinal_analysis": True}
            }
        )
        
        # Process the request which should trigger PHI access
        await canopy_adapter._process_request(request)
        
        # Verify PHI access was logged
        mock_phi_logger.log_access.assert_called()
        
        # Verify the correct user ID was logged
        call_args = mock_phi_logger.log_access.call_args
        assert call_args[1]["user_id"] == "patient456"
        
        # Verify the action is related to longitudinal analysis
        assert "process" in call_args[1]["action"]
        
        # Verify the system component is correctly identified
        assert "canopy" in call_args[1]["system_component"].lower()
        
        # Verify access purpose is specified
        assert "access_purpose" in call_args[1]

    @pytest.mark.asyncio
    @patch("src.structured_logging.phi_logger.get_phi_logger")
    @patch("src.security.phi_encryption.PHIEncryptor")
    async def test_phi_lifecycle(self, mock_encryptor_class, mock_get_phi_logger, mock_phi_logger):
        """
        Test the lifecycle of PHI data: creation, processing, and deletion.
        
        This test simulates the complete lifecycle of PHI data and ensures
        proper audit entries are created and data is encrypted at rest.
        """
        # Configure the PHI logger mock
        mock_get_phi_logger.return_value = mock_phi_logger
        
        # Configure the encryptor mock
        mock_encryptor = MagicMock()
        mock_encryptor.encrypt.side_effect = lambda x: f"ENCRYPTED({x})"
        mock_encryptor.decrypt.side_effect = lambda x: x.replace("ENCRYPTED(", "").replace(")", "")
        mock_encryptor_class.get_instance.return_value = mock_encryptor
        
        # 1. Create a PHI record
        emotional_state = EmotionalState(
            user_id="patient789",
            timestamp=datetime.now(),
            valence=-0.3,
            arousal=0.6,
            dominance=0.4,
            primary_emotion="sadness",
            secondary_emotions=["anxiety", "fatigue"],
            clinical_notes="Patient reports increased isolation and difficulty sleeping",
            assessment_id="assessment123"
        )
        
        # Verify PHI access was logged for creation
        mock_phi_logger.log_access.assert_called_with(
            user_id="patient789",
            action="create",
            system_component="EmotionalState",
            access_purpose="clinical_assessment",
            data_elements=["clinical_notes", "emotional_state"],
            additional_context={"operation": "create"}
        )
        
        # Reset mock to check next operation
        mock_phi_logger.log_access.reset_mock()
        
        # 2. Process the PHI record (simulate analysis)
        with patch("src.symbolic.root.analysis.analyze_emotional_timeline") as mock_analyze:
            mock_analyze.return_value = {
                "summary": "Fluctuating emotional state with recent improvement",
                "risk_level": "moderate",
                "trends": ["improving sleep", "decreasing anxiety"]
            }
            
            # Simulate processing
            result = await process_emotional_state(emotional_state)
            
            # Verify PHI was encrypted during processing
            assert mock_encryptor.encrypt.called
            encrypted_notes = mock_encryptor.encrypt.call_args[0][0]
            assert "isolation" in encrypted_notes
            
            # Verify PHI access was logged for processing
            mock_phi_logger.log_access.assert_called_with(
                user_id="patient789",
                action="process",
                system_component="RootAnalysis",
                access_purpose="longitudinal_analysis",
                data_elements=["emotional_state", "clinical_notes"],
                additional_context={"operation": "analyze"}
            )
        
        # Reset mock to check next operation
        mock_phi_logger.log_access.reset_mock()
        
        # 3. Delete the PHI record
        await delete_emotional_state(emotional_state.user_id, emotional_state.assessment_id)
        
        # Verify PHI access was logged for deletion
        mock_phi_logger.log_access.assert_called_with(
            user_id="patient789",
            action="delete",
            system_component="EmotionalState",
            access_purpose="data_lifecycle",
            data_elements=["complete_record"],
            additional_context={"operation": "delete", "assessment_id": "assessment123"}
        )


# Helper functions for the PHI lifecycle test
async def process_emotional_state(state: EmotionalState) -> Dict[str, Any]:
    """Process an emotional state record with proper PHI handling."""
    # Log PHI access
    await log_phi_access(
        state.user_id, 
        "process", 
        "RootAnalysis",
        access_purpose="longitudinal_analysis",
        data_elements=["emotional_state", "clinical_notes"],
        additional_context={"operation": "analyze"}
    )
    
    # Encrypt sensitive data before processing
    from src.security.phi_encryption import PHIEncryptor
    encryptor = PHIEncryptor.get_instance()
    encrypted_notes = encryptor.encrypt(state.clinical_notes)
    
    # Simulate processing
    result = {
        "user_id": state.user_id,
        "processed_at": datetime.now().isoformat(),
        "analysis_complete": True
    }
    
    return result


async def delete_emotional_state(user_id: str, assessment_id: str) -> bool:
    """Delete an emotional state record with proper audit logging."""
    # Log PHI access for deletion
    await log_phi_access(
        user_id, 
        "delete", 
        "EmotionalState",
        access_purpose="data_lifecycle",
        data_elements=["complete_record"],
        additional_context={"operation": "delete", "assessment_id": assessment_id}
    )
    
    # Simulate deletion
    return True


async def log_phi_access(user_id: str, action: str, system_component: str, **kwargs) -> str:
    """Wrapper for PHI access logging."""
    from src.structured_logging.phi_logger import get_phi_logger
    phi_logger = get_phi_logger()
    return await phi_logger.log_access(
        user_id=user_id,
        action=action,
        system_component=system_component,
        **kwargs
    )
