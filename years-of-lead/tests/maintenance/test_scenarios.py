"""
Comprehensive test scenarios for Years of Lead maintenance.
Tests actual implemented features in the game system.
"""

import pytest
import time
import random
import numpy as np
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import gc
import psutil
import os

from src.game.core import GameState, Agent, AgentStatus, SkillType


@pytest.fixture
def game():
    """Set up test environment"""
    game = GameState()
    game.initialize_game()
    return game


def test_narrative_coherence(game):
    """Test narrative event generation maintains coherence"""
    narratives = []
    
    # Generate multiple turns of narrative
    for _ in range(10):
        game.advance_turn()
        narratives.extend(game.recent_narrative[-3:])
    
    # Check for basic coherence - events should reference game entities
    faction_names = [f.name for f in game.factions.values()]
    coherent_count = 0
    
    for narrative in narratives:
        if any(faction in narrative for faction in faction_names):
            coherent_count += 1
    
    coherence_ratio = coherent_count / len(narratives) if narratives else 0
    assert coherence_ratio > 0.05, f"Low narrative coherence: {coherence_ratio:.2f}"


def test_agent_loyalty_consistency(game):
    """Test agent loyalty values remain consistent"""
    initial_loyalties = {
        agent_id: agent.loyalty 
        for agent_id, agent in game.agents.items()
    }
    
    # Run several game turns
    for _ in range(20):
        game.advance_turn()
    
    # Check loyalty hasn't changed drastically without events
    for agent_id, agent in game.agents.items():
        initial = initial_loyalties[agent_id]
        assert 0 <= agent.loyalty <= 100, f"Invalid loyalty value: {agent.loyalty}"
        # Loyalty shouldn't change in basic game flow
        assert agent.loyalty == initial, f"Unexpected loyalty change for {agent.name}"


def test_stress_bounds_consistency(game):
    """Test agent stress values stay within bounds"""
    # Manually adjust stress values
    for agent in game.agents.values():
        agent.stress = random.randint(0, 100)
    
    # Run game turns
    for _ in range(10):
        game.advance_turn()
        
        # Verify stress bounds
        for agent in game.agents.values():
            assert 0 <= agent.stress <= 100, f"Stress out of bounds: {agent.stress}"


def test_faction_resource_persistence(game):
    """Test faction resources persist correctly"""
    # Track initial resources
    initial_resources = {}
    for faction_id, faction in game.factions.items():
        initial_resources[faction_id] = faction.resources.copy()
    
    # Run game turns
    for _ in range(5):
        game.advance_turn()
    
    # Resources should change but remain valid
    for faction_id, faction in game.factions.items():
        for resource, value in faction.resources.items():
            assert value >= 0, f"Negative resource {resource}: {value}"
            # Resources should have changed
            if resource in initial_resources[faction_id]:
                # Allow for some change
                diff = abs(value - initial_resources[faction_id][resource])
                assert diff <= 100, f"Extreme resource change for {resource}"


def test_multi_agent_locations(game):
    """Test multiple agents can occupy same location"""
    # Move multiple agents to same location
    target_location = "safehouse_alpha"
    moved_agents = []
    
    for i, agent in enumerate(list(game.agents.values())[:3]):
        agent.location_id = target_location
        moved_agents.append(agent.id)
    
    # Verify location tracking
    agent_locations = game.get_agent_locations()
    assert target_location in agent_locations
    assert len(agent_locations[target_location]) >= 3


def test_skill_persistence(game):
    """Test agent skills persist and remain valid"""
    # Track initial skills
    initial_skills = {}
    for agent_id, agent in game.agents.items():
        initial_skills[agent_id] = {}
        for skill_type, skill in agent.skills.items():
            initial_skills[agent_id][skill_type] = skill.level
    
    # Run game turns
    for _ in range(10):
        game.advance_turn()
    
    # Verify skills unchanged (no progression system yet)
    for agent_id, agent in game.agents.items():
        for skill_type, skill in agent.skills.items():
            assert skill.level == initial_skills[agent_id][skill_type]
            assert 1 <= skill.level <= 10, f"Invalid skill level: {skill.level}"


def test_narrative_variety(game):
    """Test narrative events show variety"""
    narratives = set()
    
    # Generate many turns
    for _ in range(20):
        game.advance_turn()
        narratives.update(game.recent_narrative[-5:])
    
    # Should have reasonable variety
    assert len(narratives) >= 10, f"Low narrative variety: {len(narratives)} unique events"


def test_game_initialization_speed():
    """Test game initialization performance"""
    start_time = time.time()
    
    # Initialize multiple games
    for _ in range(10):
        game = GameState()
        game.initialize_game()
    
    elapsed = time.time() - start_time
    assert elapsed < 1.0, f"Slow initialization: {elapsed:.2f}s for 10 games"


def test_memory_stability(game):
    """Test memory usage remains stable"""
    import gc
    gc.collect()
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Run many game cycles
    for _ in range(100):
        game.advance_turn()
        if len(game.recent_narrative) > 1000:
            # Trim to prevent unbounded growth
            game.recent_narrative = game.recent_narrative[-100:]
    
    gc.collect()
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_growth = final_memory - initial_memory
    
    assert memory_growth < 50, f"Excessive memory growth: {memory_growth:.1f}MB"


def test_game_phase_cycles(game):
    """Test game phases cycle correctly"""
    from src.game.core import GamePhase
    
    expected_cycle = [
        GamePhase.PLANNING,
        GamePhase.ACTION,
        GamePhase.RESOLUTION
    ]
    
    phase_history = []
    for _ in range(9):  # 3 complete cycles
        phase_history.append(game.current_phase)
        game.advance_turn()
    
    # Verify correct cycling
    for i, phase in enumerate(phase_history):
        expected = expected_cycle[i % 3]
        assert phase == expected, f"Phase mismatch at {i}: {phase} != {expected}"


def test_agent_status_stability(game):
    """Test agent status values remain valid"""
    valid_statuses = {status for status in AgentStatus}
    
    # Run game and check statuses
    for _ in range(10):
        game.advance_turn()
        
        for agent in game.agents.values():
            assert agent.status in valid_statuses, f"Invalid status: {agent.status}"


def test_high_load_stability(game):
    """Test system stability under high load"""
    # Create many agents
    for i in range(50):
        agent = Agent(
            id=f"stress_agent_{i}",
            name=f"Stress Test Agent {i}",
            faction_id="resistance",
            location_id="safehouse_alpha"
        )
        game.agents[agent.id] = agent
    
    # Run intensive operations
    start_time = time.time()
    for _ in range(20):
        game.advance_turn()
        _ = game.get_status_summary()
        _ = game.get_agent_locations()
    
    elapsed = time.time() - start_time
    assert elapsed < 5.0, f"Poor performance under load: {elapsed:.2f}s"
    
    # Verify game still functional
    status = game.get_status_summary()
    assert status["turn"] == 21
    assert len(game.agents) > 50
