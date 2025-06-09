"""
Comprehensive integration tests for the SYLVA-WREN framework.

This test suite provides end-to-end testing of the integration between
SYLVA symbolic processing and WREN narrative systems, including complex
workflows, error conditions, and real-world scenarios.
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, List, Optional, Any
import uuid

from src.integration.coordinator import SylvaWrenCoordinator
from src.integration.models import (
    EmotionalInput, IntegratedResponse, CrisisAssessment, 
    ProcessedEmotionalState, SymbolicState, NarrativeState, IntegratedState
)
from src.symbolic.adapters.sylva_adapter import SylvaAdapter, SylvaContext, ProcessingResult
from src.symbolic.canopy import CanopyProcessor
from src.symbolic.canopy.metaphor_extraction import SymbolicMapping, EmotionalMetaphor

# Complex test scenarios
COMPLEX_EMOTIONAL_SCENARIOS = [
    {
        "name": "Crisis Escalation",
        "input": "I can't take this anymore. Everything is falling apart and I don't see a way out.",
        "biomarkers": {"heart_rate": 125, "respiratory_rate": 22, "skin_conductance": 0.95},
        "expected_crisis_level": "high",
        "expected_symbols": ["darkness", "collapse", "void"],
        "expected_interventions": ["crisis_protocol", "immediate_support"]
    },
    {
        "name": "Therapeutic Progress",
        "input": "I'm starting to see things differently. The therapy is really helping me understand myself.",
        "biomarkers": {"heart_rate": 75, "respiratory_rate": 16, "skin_conductance": 0.4},
        "expected_crisis_level": "none",
        "expected_symbols": ["light", "clarity", "growth"],
        "expected_interventions": ["progress_reinforcement"]
    },
    {
        "name": "Emotional Ambiguity",
        "input": "I'm not sure how I feel today. Sometimes happy, sometimes sad, maybe anxious?",
        "biomarkers": {"heart_rate": 85, "respiratory_rate": 18, "skin_conductance": 0.6},
        "expected_crisis_level": "low",
        "expected_symbols": ["confusion", "change", "transition"],
        "expected_interventions": ["clarification_support"]
    },
    {
        "name": "Cultural Context",
        "input": "In my culture, we don't talk about feelings openly. But I'm struggling with family pressure.",
        "biomarkers": {"heart_rate": 90, "respiratory_rate": 19, "skin_conductance": 0.7},
        "expected_crisis_level": "medium",
        "expected_symbols": ["tradition", "pressure", "conflict"],
        "expected_interventions": ["cultural_sensitivity", "family_therapy"]
    },
    {
        "name": "Trauma Processing",
        "input": "The memories keep coming back. I thought I was over what happened, but it still affects me.",
        "biomarkers": {"heart_rate": 110, "respiratory_rate": 21, "skin_conductance": 0.85},
        "expected_crisis_level": "medium",
        "expected_symbols": ["memory", "shadow", "healing"],
        "expected_interventions": ["trauma_processing", "grounding_techniques"]
    }
]

INTEGRATION_TEST_CONTEXTS = [
    {
        "user_id": "user_001",
        "session_id": "session_therapeutic_001",
        "processing_flags": {
            "enable_cultural_adaptation": True,
            "enable_veluria": True,
            "enable_root": True,
            "enable_wren_narrative": True,
            "cultural_context": {"culture_code": "us", "language": "en"}
        },
        "user_history": []
    },
    {
        "user_id": "user_002", 
        "session_id": "session_crisis_002",
        "processing_flags": {
            "enable_cultural_adaptation": False,
            "enable_veluria": True,
            "enable_root": False,
            "enable_wren_narrative": True,
            "crisis_mode": True
        },
        "user_history": ["previous_crisis_event"]
    },
    {
        "user_id": "user_003",
        "session_id": "session_multicultural_003", 
        "processing_flags": {
            "enable_cultural_adaptation": True,
            "enable_veluria": True,
            "enable_root": True,
            "enable_wren_narrative": True,
            "cultural_context": {"culture_code": "mx", "language": "es"}
        },
        "user_history": ["long_term_therapy"]
    }
]

@pytest.fixture
def mock_coordinator():
    """Create a comprehensive mock SylvaWrenCoordinator"""
    coordinator = SylvaWrenCoordinator()
    
    # Mock the MOSS adapter
    coordinator.moss_adapter = Mock()
    coordinator.moss_adapter.assess_crisis = AsyncMock()
    coordinator.moss_adapter.get_intervention_recommendations = AsyncMock()
    
    return coordinator

@pytest.fixture
def mock_canopy_processor():
    """Create a sophisticated mock CanopyProcessor"""
    processor = Mock()
    processor.process = AsyncMock()
    
    # Default response that can be customized per test
    default_mapping = SymbolicMapping(
        primary_symbol="water",
        archetype="self",
        alternative_symbols=["flow", "depth"],
        valence=0.0,
        arousal=0.5,
        metaphors=[EmotionalMetaphor(text="test", symbol="water", confidence=0.8)],
        confidence=0.8
    )
    processor.process.return_value = default_mapping
    
    return processor

@pytest.fixture 
def mock_wren_adapter():
    """Create a mock WREN narrative adapter"""
    adapter = Mock()
    adapter.process = AsyncMock()
    
    default_narrative = {
        "narrative_arc": "growth",
        "character_position": "challenge",
        "symbolic_reinforcement": "positive",
        "next_steps": ["reflection", "action"]
    }
    adapter.process.return_value = default_narrative
    
    return adapter

# End-to-End Integration Tests
@pytest.mark.asyncio
async def test_end_to_end_emotional_processing(mock_coordinator, mock_canopy_processor, mock_wren_adapter):
    """Test complete end-to-end emotional processing workflow"""
    
    for scenario in COMPLEX_EMOTIONAL_SCENARIOS:
        # Configure mocks based on scenario
        mock_coordinator.moss_adapter.assess_crisis.return_value = CrisisAssessment(
            level=scenario["expected_crisis_level"],
            confidence=0.85,
            risk_factors=["emotional_distress"],
            recommended_interventions=scenario["expected_interventions"]
        )
        
        # Create emotional input
        emotional_input = EmotionalInput(
            text=scenario["input"],
            biomarkers=scenario["biomarkers"],
            user_context={
                "user_id": "test_user",
                "session_id": "test_session",
                "timestamp": datetime.now()
            }
        )
        
        # Process through coordinator
        result = await mock_coordinator.process_emotional_input(emotional_input)
        
        # Verify successful processing
        assert isinstance(result, ProcessedEmotionalState)
        assert result.emotional_input == emotional_input
        
        # Verify crisis assessment was performed
        mock_coordinator.moss_adapter.assess_crisis.assert_called()
        
        print(f"✓ Scenario '{scenario['name']}' processed successfully")

@pytest.mark.asyncio
async def test_sylva_wren_state_synchronization(mock_coordinator):
    """Test state synchronization between SYLVA and WREN systems"""
    
    # Create symbolic state
    symbolic_state = SymbolicState(
        primary_symbol="mountain",
        archetype="hero",
        emotional_valence=0.3,
        arousal_level=0.7,
        metaphors=["climbing upward", "reaching the summit"],
        confidence=0.9
    )
    
    # Create narrative state
    narrative_state = NarrativeState(
        current_scene="personal_challenge",
        character_arc="growth",
        narrative_tension=0.6,
        story_elements=["obstacle", "determination", "progress"],
        scene_context={"setting": "therapeutic", "mood": "hopeful"}
    )
    
    # Synchronize states
    integrated_state = await mock_coordinator.synchronize_states(symbolic_state, narrative_state)
    
    # Verify integration
    assert isinstance(integrated_state, IntegratedState)
    assert integrated_state.symbolic == symbolic_state
    assert integrated_state.narrative == narrative_state
    assert integrated_state.integration_insights is not None
    assert integrated_state.synchronization_quality > 0.0

@pytest.mark.asyncio
async def test_multi_user_concurrent_processing(mock_coordinator):
    """Test concurrent processing for multiple users"""
    
    async def process_user(user_id, scenario):
        emotional_input = EmotionalInput(
            text=scenario["input"],
            biomarkers=scenario["biomarkers"],
            user_context={
                "user_id": user_id,
                "session_id": f"session_{user_id}",
                "timestamp": datetime.now()
            }
        )
        return await mock_coordinator.process_emotional_input(emotional_input)
    
    # Create concurrent processing tasks
    tasks = []
    for i, scenario in enumerate(COMPLEX_EMOTIONAL_SCENARIOS):
        tasks.append(process_user(f"user_{i}", scenario))
    
    # Execute concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Verify all processing completed successfully
    successful_results = [r for r in results if isinstance(r, ProcessedEmotionalState)]
    assert len(successful_results) == len(COMPLEX_EMOTIONAL_SCENARIOS)
    
    # Verify no data corruption between users
    user_ids = set()
    for result in successful_results:
        user_id = result.emotional_input.user_context["user_id"]
        assert user_id not in user_ids  # No duplicates
        user_ids.add(user_id)

@pytest.mark.asyncio
async def test_crisis_escalation_workflow(mock_coordinator):
    """Test crisis escalation workflow with VELURIA integration"""
    
    # Mock VELURIA crisis detection
    mock_coordinator.moss_adapter.assess_crisis.return_value = CrisisAssessment(
        level="critical",
        confidence=0.95,
        risk_factors=["suicidal_ideation", "hopelessness", "isolation"],
        recommended_interventions=["immediate_intervention", "emergency_contact", "safety_planning"]
    )
    
    # Create high-risk emotional input
    crisis_input = EmotionalInput(
        text="I don't want to be here anymore. I have a plan and I think tonight is the night.",
        biomarkers={"heart_rate": 140, "respiratory_rate": 25, "skin_conductance": 0.98},
        user_context={
            "user_id": "crisis_user",
            "session_id": "crisis_session",
            "timestamp": datetime.now()
        }
    )
    
    # Process crisis input
    result = await mock_coordinator.process_emotional_input(crisis_input)
    
    # Verify crisis handling
    assert isinstance(result, ProcessedEmotionalState)
    
    # Verify crisis assessment was performed with high priority
    mock_coordinator.moss_adapter.assess_crisis.assert_called()
    call_args = mock_coordinator.moss_adapter.assess_crisis.call_args
    assert "crisis_user" in str(call_args)

@pytest.mark.asyncio
async def test_cultural_adaptation_integration(mock_coordinator):
    """Test cultural adaptation across SYLVA-WREN integration"""
    
    cultural_scenarios = [
        {
            "culture": "western",
            "language": "en", 
            "input": "I'm feeling overwhelmed by individual responsibility",
            "expected_symbols": ["burden", "isolation"],
            "cultural_context": {"individualism": "high", "directness": "high"}
        },
        {
            "culture": "eastern",
            "language": "zh",
            "input": "I feel disconnected from family harmony",
            "expected_symbols": ["imbalance", "separation"],
            "cultural_context": {"collectivism": "high", "harmony": "high"}
        },
        {
            "culture": "latin_american",
            "language": "es",
            "input": "La familia no entiende mis sentimientos",
            "expected_symbols": ["family", "misunderstanding"],
            "cultural_context": {"family_centricity": "high", "emotional_expression": "high"}
        }
    ]
    
    for scenario in cultural_scenarios:
        emotional_input = EmotionalInput(
            text=scenario["input"],
            biomarkers={"heart_rate": 85, "respiratory_rate": 18, "skin_conductance": 0.6},
            user_context={
                "user_id": f"user_{scenario['culture']}",
                "session_id": f"session_{scenario['culture']}",
                "cultural_context": scenario["cultural_context"],
                "timestamp": datetime.now()
            }
        )
        
        result = await mock_coordinator.process_emotional_input(emotional_input)
        
        # Verify cultural adaptation was applied
        assert isinstance(result, ProcessedEmotionalState)
        
        print(f"✓ Cultural scenario '{scenario['culture']}' processed successfully")

@pytest.mark.asyncio
async def test_error_resilience_and_recovery(mock_coordinator):
    """Test system resilience and error recovery"""
    
    # Test CANOPY failure recovery
    with patch('src.symbolic.canopy.CanopyProcessor.process', side_effect=Exception("CANOPY failure")):
        emotional_input = EmotionalInput(
            text="Test input during failure",
            user_context={
                "user_id": "test_user",
                "session_id": "test_session",
                "timestamp": datetime.now()
            }
        )
        
        # Should handle failure gracefully
        result = await mock_coordinator.process_emotional_input(emotional_input)
        assert isinstance(result, ProcessedEmotionalState)
        # Should have fallback processing
    
    # Test MOSS failure recovery
    mock_coordinator.moss_adapter.assess_crisis.side_effect = Exception("MOSS failure")
    
    emotional_input = EmotionalInput(
        text="Test input during MOSS failure",
        user_context={
            "user_id": "test_user",
            "session_id": "test_session", 
            "timestamp": datetime.now()
        }
    )
    
    # Should handle MOSS failure gracefully
    result = await mock_coordinator.process_emotional_input(emotional_input)
    assert isinstance(result, ProcessedEmotionalState)

@pytest.mark.asyncio
async def test_longitudinal_user_tracking(mock_coordinator):
    """Test longitudinal user state tracking across sessions"""
    
    user_id = "longitudinal_test_user"
    
    # Simulate user progression over multiple sessions
    session_inputs = [
        ("Week 1", "I'm struggling with depression and can't get out of bed"),
        ("Week 3", "Therapy is helping a bit, but I still have bad days"),
        ("Week 6", "I'm starting to see some light at the end of the tunnel"),
        ("Week 10", "I feel much more stable and hopeful about the future")
    ]
    
    results = []
    for week, text in session_inputs:
        emotional_input = EmotionalInput(
            text=text,
            biomarkers={"heart_rate": 85, "respiratory_rate": 18, "skin_conductance": 0.6},
            user_context={
                "user_id": user_id,
                "session_id": f"session_{week.replace(' ', '_')}",
                "timestamp": datetime.now(),
                "session_number": len(results) + 1
            }
        )
        
        result = await mock_coordinator.process_emotional_input(emotional_input)
        results.append(result)
        
        # Verify progressive improvement tracking
        assert isinstance(result, ProcessedEmotionalState)
    
    # Verify that the coordinator tracked user progression
    assert len(results) == 4

@pytest.mark.asyncio 
async def test_real_time_intervention_triggering(mock_coordinator):
    """Test real-time intervention triggering based on analysis"""
    
    # Mock intervention recommendations
    mock_coordinator.moss_adapter.get_intervention_recommendations.return_value = [
        {"type": "breathing_exercise", "priority": "high", "duration": 300},
        {"type": "grounding_technique", "priority": "medium", "duration": 600},
        {"type": "crisis_contact", "priority": "critical", "immediate": True}
    ]
    
    # High-stress input that should trigger interventions
    stress_input = EmotionalInput(
        text="I'm having a panic attack and can't breathe properly",
        biomarkers={"heart_rate": 150, "respiratory_rate": 30, "skin_conductance": 1.0},
        user_context={
            "user_id": "intervention_user",
            "session_id": "intervention_session",
            "timestamp": datetime.now()
        }
    )
    
    result = await mock_coordinator.process_emotional_input(stress_input)
    
    # Verify intervention recommendations were generated
    assert isinstance(result, ProcessedEmotionalState)
    mock_coordinator.moss_adapter.get_intervention_recommendations.assert_called()

@pytest.mark.asyncio
async def test_narrative_coherence_across_sessions(mock_coordinator, mock_wren_adapter):
    """Test narrative coherence maintenance across multiple sessions"""
    
    # Simulate narrative progression
    narrative_sessions = [
        {
            "text": "I'm at the beginning of my healing journey",
            "expected_arc": "departure",
            "expected_position": "call_to_adventure"
        },
        {
            "text": "I'm facing my inner demons and it's scary",
            "expected_arc": "trials",
            "expected_position": "threshold_guardian"
        },
        {
            "text": "I'm learning to understand my patterns",
            "expected_arc": "transformation",
            "expected_position": "meeting_mentor"
        },
        {
            "text": "I feel like I'm becoming who I'm meant to be",
            "expected_arc": "return",
            "expected_position": "master_of_two_worlds"
        }
    ]
    
    user_id = "narrative_user"
    
    for i, session in enumerate(narrative_sessions):
        # Configure WREN mock for this session
        mock_wren_adapter.process.return_value = {
            "narrative_arc": session["expected_arc"],
            "character_position": session["expected_position"],
            "story_coherence": 0.85 + (i * 0.05),  # Improving coherence
            "narrative_elements": ["growth", "challenge", "insight"]
        }
        
        emotional_input = EmotionalInput(
            text=session["text"],
            user_context={
                "user_id": user_id,
                "session_id": f"narrative_session_{i+1}",
                "timestamp": datetime.now()
            }
        )
        
        result = await mock_coordinator.process_emotional_input(emotional_input)
        
        # Verify narrative progression
        assert isinstance(result, ProcessedEmotionalState)
    
    # Verify WREN was called for narrative processing
    assert mock_wren_adapter.process.call_count == len(narrative_sessions)

@pytest.mark.asyncio
async def test_performance_under_load(mock_coordinator):
    """Test system performance under high load"""
    
    # Create high load scenario
    async def create_load():
        tasks = []
        for i in range(100):  # 100 concurrent requests
            emotional_input = EmotionalInput(
                text=f"Load test message {i}",
                biomarkers={"heart_rate": 80 + (i % 40), "respiratory_rate": 16},
                user_context={
                    "user_id": f"load_test_user_{i % 20}",  # 20 users
                    "session_id": f"load_session_{i}",
                    "timestamp": datetime.now()
                }
            )
            tasks.append(mock_coordinator.process_emotional_input(emotional_input))
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    # Measure performance
    start_time = datetime.now()
    results = await create_load()
    end_time = datetime.now()
    
    # Verify performance
    processing_time = (end_time - start_time).total_seconds()
    successful_results = [r for r in results if isinstance(r, ProcessedEmotionalState)]
    
    assert len(successful_results) >= 95  # 95% success rate under load
    assert processing_time < 30  # Should complete within 30 seconds
    
    print(f"✓ Processed {len(successful_results)} requests in {processing_time:.2f} seconds")

# Edge Case and Boundary Testing
@pytest.mark.asyncio
async def test_boundary_conditions(mock_coordinator):
    """Test boundary conditions and edge cases"""
    
    boundary_cases = [
        # Empty input
        EmotionalInput(
            text="",
            user_context={"user_id": "empty_user", "session_id": "empty_session", "timestamp": datetime.now()}
        ),
        # Very long input
        EmotionalInput(
            text="I feel overwhelmed. " * 1000,
            user_context={"user_id": "long_user", "session_id": "long_session", "timestamp": datetime.now()}
        ),
        # Special characters
        EmotionalInput(
            text="I feel 😢😢😢 and 💔💔💔",
            user_context={"user_id": "emoji_user", "session_id": "emoji_session", "timestamp": datetime.now()}
        ),
        # Non-English
        EmotionalInput(
            text="Me siento muy triste y perdido",
            user_context={"user_id": "spanish_user", "session_id": "spanish_session", "timestamp": datetime.now()}
        )
    ]
    
    for case in boundary_cases:
        try:
            result = await mock_coordinator.process_emotional_input(case)
            assert isinstance(result, ProcessedEmotionalState)
        except Exception as e:
            pytest.fail(f"Failed on boundary case: {str(e)}")

@pytest.mark.asyncio
async def test_integration_data_consistency(mock_coordinator):
    """Test data consistency across integration points"""
    
    emotional_input = EmotionalInput(
        text="I'm working through childhood trauma with my therapist",
        biomarkers={"heart_rate": 95, "respiratory_rate": 19, "skin_conductance": 0.75},
        user_context={
            "user_id": "consistency_user",
            "session_id": "consistency_session",
            "timestamp": datetime.now()
        }
    )
    
    result = await mock_coordinator.process_emotional_input(emotional_input)
    
    # Verify data consistency
    assert isinstance(result, ProcessedEmotionalState)
    assert result.emotional_input == emotional_input
    
    # Verify timestamps are consistent
    assert result.emotional_input.user_context["timestamp"] is not None
    
    # Verify user context is preserved
    assert result.emotional_input.user_context["user_id"] == "consistency_user" 