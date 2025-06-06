"""
Tests for ROOT longitudinal analysis system.
"""

import pytest
from datetime import datetime, timedelta
import numpy as np
from typing import List, Dict, Any

from src.symbolic.root import (
    ROOTAnalyzer,
    EmotionalBaseline,
    TrendAnalysis,
    PatternRecognitionResult
)
from models.emotional_state import EmotionalState, SymbolicMapping

# Test data generators
def create_emotional_state(
    valence: float,
    arousal: float,
    timestamp: datetime
) -> EmotionalState:
    """Create a test emotional state"""
    return EmotionalState(
        valence=valence,
        arousal=arousal,
        timestamp=timestamp
    )

def create_symbolic_mapping(
    symbols: List[str],
    archetypes: List[str],
    timestamp: datetime
) -> SymbolicMapping:
    """Create a test symbolic mapping"""
    return SymbolicMapping(
        symbols=symbols,
        archetypes=archetypes,
        timestamp=timestamp
    )

# Generate test data
now = datetime.now()
SAMPLE_EMOTIONAL_HISTORY = [
    create_emotional_state(0.3, 0.4, now - timedelta(days=7)),
    create_emotional_state(0.4, 0.5, now - timedelta(days=6)),
    create_emotional_state(0.6, 0.6, now - timedelta(days=5)),
    create_emotional_state(0.7, 0.7, now - timedelta(days=4)),
    create_emotional_state(0.8, 0.8, now - timedelta(days=3)),
    create_emotional_state(0.6, 0.6, now - timedelta(days=2)),
    create_emotional_state(0.4, 0.4, now - timedelta(days=1))
]

SAMPLE_SYMBOLIC_HISTORY = [
    create_symbolic_mapping(
        ["water", "moon"],
        ["mother", "shadow"],
        now - timedelta(days=7)
    ),
    create_symbolic_mapping(
        ["fire", "sun"],
        ["hero", "sage"],
        now - timedelta(days=5)
    ),
    create_symbolic_mapping(
        ["earth", "mountain"],
        ["warrior", "magician"],
        now - timedelta(days=3)
    ),
    create_symbolic_mapping(
        ["air", "wind"],
        ["trickster", "innocent"],
        now - timedelta(days=1)
    )
]

@pytest.fixture
def root_analyzer():
    """Create a ROOT analyzer instance"""
    return ROOTAnalyzer()

def test_baseline_calculation(root_analyzer):
    """Test emotional baseline calculation"""
    baseline = root_analyzer.calculate_baseline(SAMPLE_EMOTIONAL_HISTORY)
    
    assert isinstance(baseline, EmotionalBaseline)
    assert 0 <= baseline.valence_baseline <= 1
    assert 0 <= baseline.arousal_baseline <= 1
    assert 0 <= baseline.confidence <= 1
    assert 0 <= baseline.stability_score <= 1
    assert isinstance(baseline.variability, dict)
    assert isinstance(baseline.timeframe, timedelta)
    
    # Test empty history
    empty_baseline = root_analyzer.calculate_baseline([])
    assert empty_baseline.valence_baseline == 0.0
    assert empty_baseline.confidence == 0.0

def test_trend_analysis(root_analyzer):
    """Test emotional trend analysis"""
    analysis = root_analyzer.analyze_trends(SAMPLE_EMOTIONAL_HISTORY)
    
    assert isinstance(analysis, TrendAnalysis)
    assert isinstance(analysis.primary_trends, list)
    assert isinstance(analysis.stability_metrics, dict)
    assert isinstance(analysis.forecast, dict)
    
    # Check trend detection
    assert len(analysis.primary_trends) > 0
    for trend in analysis.primary_trends:
        assert "type" in trend
        assert "direction" in trend
        assert "magnitude" in trend
        assert "confidence" in trend
    
    # Check forecasting
    if analysis.forecast:
        assert "valence" in analysis.forecast
        assert "arousal" in analysis.forecast
        assert len(analysis.forecast["valence"]) > 0
        assert len(analysis.forecast["arousal"]) > 0

def test_pattern_recognition(root_analyzer):
    """Test pattern recognition"""
    result = root_analyzer.recognize_patterns(
        SAMPLE_EMOTIONAL_HISTORY,
        SAMPLE_SYMBOLIC_HISTORY
    )
    
    assert isinstance(result, PatternRecognitionResult)
    assert isinstance(result.detected_patterns, list)
    assert isinstance(result.pattern_significance, dict)
    assert isinstance(result.temporal_distribution, dict)
    assert isinstance(result.correlations, dict)
    assert isinstance(result.recommendations, list)
    
    # Check pattern detection
    assert len(result.detected_patterns) > 0
    for pattern in result.detected_patterns:
        assert "type" in pattern
    
    # Check recommendations
    assert len(result.recommendations) > 0
    assert all(isinstance(r, str) for r in result.recommendations)

def test_stability_calculation(root_analyzer):
    """Test stability calculation"""
    valences = [0.3, 0.4, 0.6, 0.7, 0.6]
    arousals = [0.4, 0.5, 0.6, 0.7, 0.6]
    
    stability = root_analyzer._calculate_stability(valences, arousals)
    assert 0 <= stability <= 1
    
    # Test empty input
    assert root_analyzer._calculate_stability([], []) == 0.0

def test_variability_calculation(root_analyzer):
    """Test variability calculations"""
    daily_var = root_analyzer._calculate_daily_variability(SAMPLE_EMOTIONAL_HISTORY)
    weekly_var = root_analyzer._calculate_weekly_variability(SAMPLE_EMOTIONAL_HISTORY)
    
    assert 0 <= daily_var <= 2  # Max range is 2 (1 for valence + 1 for arousal)
    assert 0 <= weekly_var <= 2
    
    # Test empty input
    assert root_analyzer._calculate_daily_variability([]) == 0.0
    assert root_analyzer._calculate_weekly_variability([]) == 0.0

def test_trend_identification(root_analyzer):
    """Test trend identification"""
    trends = root_analyzer._identify_primary_trends(SAMPLE_EMOTIONAL_HISTORY)
    
    assert isinstance(trends, list)
    for trend in trends:
        assert "type" in trend
        assert trend["type"] in ["valence", "arousal"]
        assert "direction" in trend
        assert trend["direction"] in ["increasing", "decreasing"]
        assert 0 <= trend["magnitude"] <= 1
        assert 0 <= trend["confidence"] <= 1

def test_change_point_detection(root_analyzer):
    """Test change point detection"""
    change_points = root_analyzer._identify_change_points(SAMPLE_EMOTIONAL_HISTORY)
    
    assert isinstance(change_points, list)
    for point in change_points:
        assert "timestamp" in point
        assert "valence_change" in point
        assert "arousal_change" in point
        assert "magnitude" in point
        assert isinstance(point["timestamp"], datetime)

def test_pattern_significance(root_analyzer):
    """Test pattern significance calculation"""
    emotional_patterns = [
        {"type": "cycle", "confidence": 0.8},
        {"type": "transition", "magnitude": 0.6}
    ]
    symbolic_patterns = [
        {"type": "symbol_sequence", "confidence": 0.7},
        {"type": "archetype_transition", "magnitude": 0.9}
    ]
    
    significance = root_analyzer._calculate_pattern_significance(
        emotional_patterns,
        symbolic_patterns
    )
    
    assert isinstance(significance, dict)
    assert all(0 <= score <= 1 for score in significance.values())
    assert "cycle" in significance
    assert "transition" in significance
    assert "symbol_sequence" in significance
    assert "archetype_transition" in significance

def test_correlation_calculation(root_analyzer):
    """Test correlation calculations"""
    correlations = root_analyzer._calculate_correlations(
        SAMPLE_EMOTIONAL_HISTORY,
        SAMPLE_SYMBOLIC_HISTORY
    )
    
    assert isinstance(correlations, dict)
    if correlations:
        assert all(0 <= abs(corr) <= 1 for corr in correlations.values())

def test_recommendation_generation(root_analyzer):
    """Test recommendation generation"""
    emotional_patterns = [
        {"type": "cycle", "confidence": 0.8},
        {"type": "transition", "confidence": 0.9}
    ]
    symbolic_patterns = [
        {"type": "symbol_sequence", "confidence": 0.7},
        {"type": "archetype_transition", "confidence": 0.8}
    ]
    significance = {
        "cycle": 0.8,
        "transition": 0.9,
        "symbol_sequence": 0.7,
        "archetype_transition": 0.8
    }
    
    recommendations = root_analyzer._generate_pattern_recommendations(
        emotional_patterns,
        symbolic_patterns,
        significance
    )
    
    assert isinstance(recommendations, list)
    assert len(recommendations) > 0
    assert all(isinstance(r, str) for r in recommendations)

def test_forecast_generation(root_analyzer):
    """Test forecast generation"""
    forecast = root_analyzer._generate_forecast(SAMPLE_EMOTIONAL_HISTORY)
    
    assert isinstance(forecast, dict)
    if forecast:  # Only test if we have enough data for forecasting
        assert "valence" in forecast
        assert "arousal" in forecast
        assert len(forecast["valence"]) > 0
        assert len(forecast["arousal"]) > 0
        assert all(0 <= v <= 1 for v in forecast["valence"])
        assert all(0 <= a <= 1 for a in forecast["arousal"])

def test_empty_input_handling(root_analyzer):
    """Test handling of empty input data"""
    # Test baseline calculation
    empty_baseline = root_analyzer.calculate_baseline([])
    assert isinstance(empty_baseline, EmotionalBaseline)
    assert empty_baseline.valence_baseline == 0.0
    
    # Test trend analysis
    empty_trends = root_analyzer.analyze_trends([])
    assert isinstance(empty_trends, TrendAnalysis)
    assert len(empty_trends.primary_trends) == 0
    
    # Test pattern recognition
    empty_patterns = root_analyzer.recognize_patterns([], [])
    assert isinstance(empty_patterns, PatternRecognitionResult)
    assert len(empty_patterns.detected_patterns) == 0

def test_edge_cases(root_analyzer):
    """Test edge cases and boundary conditions"""
    # Single data point
    single_state = [SAMPLE_EMOTIONAL_HISTORY[0]]
    baseline = root_analyzer.calculate_baseline(single_state)
    assert isinstance(baseline, EmotionalBaseline)
    assert baseline.valence_baseline == SAMPLE_EMOTIONAL_HISTORY[0].valence
    
    # Very short history
    short_history = SAMPLE_EMOTIONAL_HISTORY[:2]
    analysis = root_analyzer.analyze_trends(short_history)
    assert isinstance(analysis, TrendAnalysis)
    
    # Future timestamp
    future_state = create_emotional_state(
        0.5, 0.5,
        now + timedelta(days=1)
    )
    future_history = SAMPLE_EMOTIONAL_HISTORY + [future_state]
    future_analysis = root_analyzer.analyze_trends(future_history)
    assert isinstance(future_analysis, TrendAnalysis) 