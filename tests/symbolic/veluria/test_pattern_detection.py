"""
Tests for VELURIA crisis pattern detection and risk prediction.
"""

import pytest
from datetime import datetime, timedelta
import numpy as np
from typing import List, Dict, Any

from src.symbolic.veluria.pattern_detection import (
    CrisisPatternDetector,
    RiskPrediction,
    PatternAnalysis
)
from models.emotional_state import SafetyStatus, InterventionRecord

# Test data
def create_safety_status(
    risk_score: float,
    triggers: List[str],
    timestamp: datetime
) -> SafetyStatus:
    """Create a test safety status"""
    return SafetyStatus(
        level=int(risk_score * 3),
        risk_score=risk_score,
        triggers=triggers,
        timestamp=timestamp
    )

def create_intervention_record(
    risk_score: float,
    level: int,
    actions: List[str],
    timestamp: datetime
) -> InterventionRecord:
    """Create a test intervention record"""
    return InterventionRecord(
        id=f"test_{timestamp.isoformat()}",
        user_id="test_user",
        timestamp=timestamp,
        level=level,
        triggers=["test_trigger"],
        risk_score=risk_score,
        actions_taken=actions,
        resources_provided=["test_resource"],
        state_before=level-1,
        state_after=level
    )

# Generate test history
now = datetime.now()
SAMPLE_SAFETY_HISTORY = [
    create_safety_status(0.3, ["stress"], now - timedelta(days=7)),
    create_safety_status(0.4, ["stress", "anxiety"], now - timedelta(days=6)),
    create_safety_status(0.6, ["anxiety", "depression"], now - timedelta(days=5)),
    create_safety_status(0.7, ["depression", "self_harm"], now - timedelta(days=4)),
    create_safety_status(0.8, ["self_harm", "suicide"], now - timedelta(days=3)),
    create_safety_status(0.6, ["depression"], now - timedelta(days=2)),
    create_safety_status(0.4, ["anxiety"], now - timedelta(days=1))
]

SAMPLE_INTERVENTION_HISTORY = [
    create_intervention_record(0.7, 2, ["safety_resources_provided"], now - timedelta(days=4)),
    create_intervention_record(0.8, 3, ["crisis_team_notification"], now - timedelta(days=3)),
    create_intervention_record(0.6, 2, ["grounding_techniques_suggested"], now - timedelta(days=2))
]

@pytest.fixture
def pattern_detector():
    """Create a pattern detector instance"""
    return CrisisPatternDetector()

def test_pattern_analysis(pattern_detector):
    """Test pattern analysis functionality"""
    analysis = pattern_detector.analyze_patterns(
        SAMPLE_SAFETY_HISTORY,
        SAMPLE_INTERVENTION_HISTORY
    )
    
    assert isinstance(analysis, PatternAnalysis)
    assert len(analysis.detected_patterns) > 0
    assert "risk_trend" in analysis.temporal_trends
    assert len(analysis.risk_factors) > 0
    
    # Check temporal patterns
    patterns = [p for p in analysis.detected_patterns if p["type"] == "rapid_change"]
    assert len(patterns) > 0
    
    # Check risk factors
    assert any(f["factor"] == "self_harm" for f in analysis.risk_factors)
    assert any(f["factor"] == "suicide" for f in analysis.risk_factors)
    
    # Check intervention effectiveness
    assert len(analysis.intervention_effectiveness) > 0
    assert all(0 <= score <= 1 for score in analysis.intervention_effectiveness.values())

def test_risk_prediction(pattern_detector):
    """Test risk prediction functionality"""
    current_status = create_safety_status(0.5, ["anxiety", "depression"], now)
    
    prediction = pattern_detector.predict_risk(
        current_status,
        SAMPLE_SAFETY_HISTORY,
        {"stress_level": 0.7, "sleep_quality": 0.4}
    )
    
    assert isinstance(prediction, RiskPrediction)
    assert 0 <= prediction.risk_score <= 1
    assert 0 <= prediction.confidence <= 1
    assert len(prediction.contributing_factors) > 0
    assert len(prediction.recommended_actions) > 0
    assert len(prediction.warning_signs) > 0
    assert isinstance(prediction.prediction_horizon, timedelta)

def test_temporal_pattern_detection(pattern_detector):
    """Test temporal pattern detection"""
    patterns = pattern_detector._analyze_temporal_patterns(SAMPLE_SAFETY_HISTORY)
    
    assert "patterns" in patterns
    assert "trends" in patterns
    assert isinstance(patterns["patterns"], list)
    assert isinstance(patterns["trends"], dict)
    
    # Check for rapid changes
    rapid_changes = [p for p in patterns["patterns"] if p["type"] == "rapid_change"]
    assert len(rapid_changes) > 0
    
    # Check for high risk periods
    high_risk = [p for p in patterns["patterns"] if p["type"] == "persistent_high_risk"]
    assert len(high_risk) > 0

def test_risk_factor_identification(pattern_detector):
    """Test risk factor identification"""
    factors = pattern_detector._identify_risk_factors(
        SAMPLE_SAFETY_HISTORY,
        SAMPLE_INTERVENTION_HISTORY
    )
    
    assert isinstance(factors, list)
    assert len(factors) > 0
    
    for factor in factors:
        assert "factor" in factor
        assert "frequency" in factor
        assert "average_risk" in factor
        assert "importance" in factor
        assert 0 <= factor["frequency"] <= 1
        assert 0 <= factor["average_risk"] <= 1
        assert 0 <= factor["importance"] <= 1

def test_cyclical_pattern_detection(pattern_detector):
    """Test cyclical pattern detection"""
    patterns = pattern_detector._detect_cyclical_patterns(SAMPLE_SAFETY_HISTORY)
    
    assert patterns is not None
    assert "daily" in patterns
    assert "weekly" in patterns
    assert "monthly" in patterns

def test_intervention_evaluation(pattern_detector):
    """Test intervention effectiveness evaluation"""
    effectiveness = pattern_detector._evaluate_interventions(
        SAMPLE_INTERVENTION_HISTORY,
        SAMPLE_SAFETY_HISTORY
    )
    
    assert isinstance(effectiveness, dict)
    assert len(effectiveness) > 0
    assert all(0 <= score <= 1 for score in effectiveness.values())

def test_anomaly_detection(pattern_detector):
    """Test anomaly detection"""
    features = pattern_detector._extract_prediction_features(
        SAMPLE_SAFETY_HISTORY[-1],
        SAMPLE_SAFETY_HISTORY[:-1],
        {"stress_level": 0.8}
    )
    
    score = pattern_detector._detect_anomalies(features)
    assert isinstance(score, float)
    assert 0 <= score <= 1

def test_warning_sign_identification(pattern_detector):
    """Test warning sign identification"""
    warnings = pattern_detector._identify_warning_signs(
        SAMPLE_SAFETY_HISTORY[-1],
        SAMPLE_SAFETY_HISTORY[:-1],
        0.8
    )
    
    assert isinstance(warnings, list)
    assert len(warnings) > 0
    
    for warning in warnings:
        assert "type" in warning
        assert "severity" in warning
        assert warning["severity"] in ["low", "medium", "high", "critical"]

def test_recommendation_generation(pattern_detector):
    """Test recommendation generation"""
    recommendations = pattern_detector._generate_recommendations(
        0.8,
        ["rapid_escalation", "unusual_pattern"],
        SAMPLE_SAFETY_HISTORY[-1]
    )
    
    assert isinstance(recommendations, list)
    assert len(recommendations) > 0
    assert "immediate_crisis_team_notification" in recommendations

def test_trigger_severity_calculation(pattern_detector):
    """Test trigger severity calculation"""
    high_severity = pattern_detector._calculate_trigger_severity(["suicide", "self_harm"])
    medium_severity = pattern_detector._calculate_trigger_severity(["anxiety", "depression"])
    low_severity = pattern_detector._calculate_trigger_severity(["stress"])
    
    assert high_severity > medium_severity > low_severity
    assert all(0 <= score <= 1 for score in [high_severity, medium_severity, low_severity])

def test_temporal_risk_calculation(pattern_detector):
    """Test temporal risk calculation"""
    increasing_risk = pattern_detector._calculate_temporal_risk(SAMPLE_SAFETY_HISTORY[:3])
    decreasing_risk = pattern_detector._calculate_temporal_risk(SAMPLE_SAFETY_HISTORY[-3:])
    
    assert increasing_risk > 0.5  # Risk is increasing
    assert decreasing_risk < 0.5  # Risk is decreasing
    assert all(0 <= risk <= 1 for risk in [increasing_risk, decreasing_risk]) 