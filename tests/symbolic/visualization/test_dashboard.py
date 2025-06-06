"""
Tests for visualization dashboard.
"""

import pytest
from datetime import datetime, timedelta
import plotly.graph_objects as go
from typing import List, Dict, Any

from src.symbolic.visualization.dashboard import Dashboard
from src.symbolic.veluria.pattern_detection import PatternAnalysis, RiskPrediction
from src.symbolic.root import TrendAnalysis, PatternRecognitionResult
from models.emotional_state import EmotionalState, InterventionRecord

# Test data generators
def create_pattern_analysis() -> PatternAnalysis:
    """Create test pattern analysis data"""
    return PatternAnalysis(
        detected_patterns=[
            {"type": "rapid_change", "timestamp": datetime.now(), "magnitude": 0.5},
            {"type": "persistent_high_risk", "start": datetime.now(), "end": datetime.now()}
        ],
        temporal_trends={"risk_trend": "increasing"},
        risk_factors=[
            {"factor": "stress", "frequency": 0.7, "average_risk": 0.8, "importance": 0.75},
            {"factor": "anxiety", "frequency": 0.5, "average_risk": 0.6, "importance": 0.55}
        ],
        cyclical_patterns={"daily": {"morning": 0.3, "evening": 0.7}},
        intervention_effectiveness={
            "grounding": 0.8,
            "crisis_team": 0.9,
            "safety_plan": 0.7
        }
    )

def create_risk_prediction() -> RiskPrediction:
    """Create test risk prediction data"""
    return RiskPrediction(
        risk_score=0.7,
        confidence=0.8,
        contributing_factors=["stress", "anxiety"],
        recommended_actions=["increase_monitoring", "alert_support"],
        prediction_horizon=timedelta(hours=24),
        warning_signs=[
            {"type": "escalation", "severity": "high"},
            {"type": "isolation", "severity": "medium"}
        ]
    )

def create_intervention_history() -> List[InterventionRecord]:
    """Create test intervention history"""
    now = datetime.now()
    return [
        InterventionRecord(
            id="test1",
            user_id="user1",
            timestamp=now - timedelta(days=3),
            level=2,
            triggers=["stress"],
            risk_score=0.7,
            actions_taken=["grounding"],
            resources_provided=["hotline"],
            state_before=1,
            state_after=2
        ),
        InterventionRecord(
            id="test2",
            user_id="user1",
            timestamp=now - timedelta(days=1),
            level=3,
            triggers=["anxiety"],
            risk_score=0.8,
            actions_taken=["crisis_team"],
            resources_provided=["emergency"],
            state_before=2,
            state_after=3
        )
    ]

def create_trend_analysis() -> TrendAnalysis:
    """Create test trend analysis data"""
    return TrendAnalysis(
        primary_trends=[
            {
                "type": "valence",
                "direction": "increasing",
                "magnitude": 0.6,
                "confidence": 0.8
            },
            {
                "type": "arousal",
                "direction": "decreasing",
                "magnitude": 0.4,
                "confidence": 0.7
            }
        ],
        seasonal_patterns={
            "daily": {"morning": 0.3, "evening": 0.7},
            "weekly": {"weekday": 0.6, "weekend": 0.4}
        },
        change_points=[
            {
                "timestamp": datetime.now() - timedelta(days=2),
                "valence_change": 0.3,
                "arousal_change": -0.2,
                "magnitude": 0.3
            }
        ],
        stability_metrics={
            "valence_stability": 0.8,
            "arousal_stability": 0.7,
            "emotional_entropy": 0.4,
            "trend_consistency": 0.6
        },
        forecast={
            "valence": [0.5, 0.6, 0.7, 0.8, 0.9],
            "arousal": [0.7, 0.6, 0.5, 0.4, 0.3]
        }
    )

def create_pattern_recognition() -> PatternRecognitionResult:
    """Create test pattern recognition data"""
    return PatternRecognitionResult(
        detected_patterns=[
            {"type": "cycle", "confidence": 0.8},
            {"type": "transition", "confidence": 0.7}
        ],
        pattern_significance={
            "cycle": 0.8,
            "transition": 0.7,
            "stability": 0.6
        },
        temporal_distribution={
            "emotional": {"morning": 0.3, "evening": 0.7},
            "symbolic": {"weekday": 0.6, "weekend": 0.4}
        },
        correlations={
            "temporal": 0.7,
            "symbolic": 0.6,
            "emotional": 0.8
        },
        recommendations=[
            "Track emotional cycles",
            "Monitor transitions"
        ]
    )

def create_emotional_history() -> List[EmotionalState]:
    """Create test emotional history"""
    now = datetime.now()
    return [
        EmotionalState(
            valence=0.3,
            arousal=0.4,
            timestamp=now - timedelta(days=3)
        ),
        EmotionalState(
            valence=0.5,
            arousal=0.6,
            timestamp=now - timedelta(days=2)
        ),
        EmotionalState(
            valence=0.7,
            arousal=0.8,
            timestamp=now - timedelta(days=1)
        )
    ]

@pytest.fixture
def dashboard():
    """Create dashboard instance"""
    return Dashboard()

def test_dashboard_initialization(dashboard):
    """Test dashboard initialization"""
    assert isinstance(dashboard, Dashboard)
    assert dashboard.color_scheme is not None
    assert dashboard.theme is not None

def test_crisis_dashboard_creation(dashboard):
    """Test crisis dashboard creation"""
    # Create test data
    pattern_analysis = create_pattern_analysis()
    risk_prediction = create_risk_prediction()
    intervention_history = create_intervention_history()
    
    # Create dashboard
    fig = dashboard.create_crisis_dashboard(
        pattern_analysis,
        risk_prediction,
        intervention_history
    )
    
    # Verify dashboard
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0
    assert fig.layout.title.text == "Crisis Intervention Analytics Dashboard"

def test_longitudinal_dashboard_creation(dashboard):
    """Test longitudinal dashboard creation"""
    # Create test data
    trend_analysis = create_trend_analysis()
    pattern_recognition = create_pattern_recognition()
    emotional_history = create_emotional_history()
    
    # Create dashboard
    fig = dashboard.create_longitudinal_dashboard(
        trend_analysis,
        pattern_recognition,
        emotional_history
    )
    
    # Verify dashboard
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0
    assert fig.layout.title.text == "Longitudinal Analysis Dashboard"

def test_risk_timeline_plot(dashboard):
    """Test risk timeline plot creation"""
    # Create figure
    fig = go.Figure()
    intervention_history = create_intervention_history()
    
    # Add plot
    dashboard._add_risk_timeline(fig, intervention_history, 1, 1)
    
    # Verify plot
    assert len(fig.data) > 0
    for trace in fig.data:
        assert isinstance(trace, go.Scatter)

def test_intervention_effectiveness_plot(dashboard):
    """Test intervention effectiveness plot creation"""
    # Create figure
    fig = go.Figure()
    pattern_analysis = create_pattern_analysis()
    
    # Add plot
    dashboard._add_intervention_effectiveness(fig, pattern_analysis, 1, 1)
    
    # Verify plot
    assert len(fig.data) > 0
    assert isinstance(fig.data[0], go.Bar)

def test_pattern_distribution_plot(dashboard):
    """Test pattern distribution plot creation"""
    # Create figure
    fig = go.Figure()
    pattern_analysis = create_pattern_analysis()
    
    # Add plot
    dashboard._add_pattern_distribution(fig, pattern_analysis, 1, 1)
    
    # Verify plot
    assert len(fig.data) > 0
    assert isinstance(fig.data[0], go.Pie)

def test_warning_signs_plot(dashboard):
    """Test warning signs plot creation"""
    # Create figure
    fig = go.Figure()
    risk_prediction = create_risk_prediction()
    
    # Add plot
    dashboard._add_warning_signs(fig, risk_prediction, 1, 1)
    
    # Verify plot
    assert len(fig.data) > 0
    assert isinstance(fig.data[0], go.Scatter)

def test_risk_factors_plot(dashboard):
    """Test risk factors plot creation"""
    # Create figure
    fig = go.Figure()
    pattern_analysis = create_pattern_analysis()
    
    # Add plot
    dashboard._add_risk_factors(fig, pattern_analysis, 1, 1)
    
    # Verify plot
    assert len(fig.data) > 0
    assert isinstance(fig.data[0], go.Bar)

def test_predicted_risk_plot(dashboard):
    """Test predicted risk plot creation"""
    # Create figure
    fig = go.Figure()
    risk_prediction = create_risk_prediction()
    
    # Add plot
    dashboard._add_predicted_risk(fig, risk_prediction, 1, 1)
    
    # Verify plot
    assert len(fig.data) > 0
    assert isinstance(fig.data[0], go.Indicator)

def test_emotional_timeline_plot(dashboard):
    """Test emotional timeline plot creation"""
    # Create figure
    fig = go.Figure()
    emotional_history = create_emotional_history()
    
    # Add plot
    dashboard._add_emotional_timeline(fig, emotional_history, 1, 1)
    
    # Verify plot
    assert len(fig.data) > 0
    for trace in fig.data:
        assert isinstance(trace, go.Scatter)

def test_pattern_recognition_plot(dashboard):
    """Test pattern recognition plot creation"""
    # Create figure
    fig = go.Figure()
    pattern_recognition = create_pattern_recognition()
    
    # Add plot
    dashboard._add_pattern_recognition(fig, pattern_recognition, 1, 1)
    
    # Verify plot
    assert len(fig.data) > 0
    assert isinstance(fig.data[0], go.Scatterpolar)

def test_trend_analysis_plot(dashboard):
    """Test trend analysis plot creation"""
    # Create figure
    fig = go.Figure()
    trend_analysis = create_trend_analysis()
    
    # Add plot
    dashboard._add_trend_analysis(fig, trend_analysis, 1, 1)
    
    # Verify plot
    assert len(fig.data) > 0
    for trace in fig.data:
        assert isinstance(trace, go.Scatter)

def test_stability_metrics_plot(dashboard):
    """Test stability metrics plot creation"""
    # Create figure
    fig = go.Figure()
    trend_analysis = create_trend_analysis()
    
    # Add plot
    dashboard._add_stability_metrics(fig, trend_analysis, 1, 1)
    
    # Verify plot
    assert len(fig.data) > 0
    assert isinstance(fig.data[0], go.Bar)

def test_correlations_plot(dashboard):
    """Test correlations plot creation"""
    # Create figure
    fig = go.Figure()
    pattern_recognition = create_pattern_recognition()
    
    # Add plot
    dashboard._add_correlations(fig, pattern_recognition, 1, 1)
    
    # Verify plot
    assert len(fig.data) > 0
    assert isinstance(fig.data[0], go.Heatmap)

def test_forecasting_plot(dashboard):
    """Test forecasting plot creation"""
    # Create figure
    fig = go.Figure()
    trend_analysis = create_trend_analysis()
    
    # Add plot
    dashboard._add_forecasting(fig, trend_analysis, 1, 1)
    
    # Verify plot
    assert len(fig.data) > 0
    for trace in fig.data:
        assert isinstance(trace, go.Scatter)

def test_empty_data_handling(dashboard):
    """Test handling of empty data"""
    # Create empty data
    pattern_analysis = PatternAnalysis([], {}, [], None, {})
    risk_prediction = RiskPrediction(0.0, 0.0, [], [], timedelta(), [])
    intervention_history = []
    trend_analysis = TrendAnalysis([], None, [], {}, {})
    pattern_recognition = PatternRecognitionResult([], {}, {}, {}, [])
    emotional_history = []
    
    # Create dashboards
    crisis_fig = dashboard.create_crisis_dashboard(
        pattern_analysis,
        risk_prediction,
        intervention_history
    )
    longitudinal_fig = dashboard.create_longitudinal_dashboard(
        trend_analysis,
        pattern_recognition,
        emotional_history
    )
    
    # Verify dashboards
    assert isinstance(crisis_fig, go.Figure)
    assert isinstance(longitudinal_fig, go.Figure)

def test_color_scheme_usage(dashboard):
    """Test color scheme application"""
    # Create test data
    pattern_analysis = create_pattern_analysis()
    risk_prediction = create_risk_prediction()
    intervention_history = create_intervention_history()
    
    # Create dashboard
    fig = dashboard.create_crisis_dashboard(
        pattern_analysis,
        risk_prediction,
        intervention_history
    )
    
    # Verify color usage
    for trace in fig.data:
        if hasattr(trace, "marker") and trace.marker:
            if isinstance(trace.marker.color, str):
                assert trace.marker.color in dashboard.color_scheme.values()
        if hasattr(trace, "line") and trace.line:
            if isinstance(trace.line.color, str):
                assert trace.line.color in dashboard.color_scheme.values()

def test_layout_configuration(dashboard):
    """Test dashboard layout configuration"""
    # Create test data
    trend_analysis = create_trend_analysis()
    pattern_recognition = create_pattern_recognition()
    emotional_history = create_emotional_history()
    
    # Create dashboard
    fig = dashboard.create_longitudinal_dashboard(
        trend_analysis,
        pattern_recognition,
        emotional_history
    )
    
    # Verify layout
    assert fig.layout.height == 900
    assert fig.layout.showlegend is True
    assert fig.layout.template == "plotly_white"
    assert fig.layout.paper_bgcolor == dashboard.theme["background"]
    assert fig.layout.plot_bgcolor == dashboard.theme["background"]
    assert fig.layout.font.color == dashboard.theme["text"] 