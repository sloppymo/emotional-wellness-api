"""
Unit tests for longitudinal analysis module.
"""

import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from clinical.longitudinal import LongitudinalAnalyzer, TrendDirection
from symbolic.moss.crisis_classifier import CrisisSeverity, RiskDomain


class TestLongitudinalAnalyzer:
    """Test suite for longitudinal analysis module."""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis instance."""
        redis = AsyncMock()
        redis.keys = AsyncMock(return_value=[])
        redis.get = AsyncMock(return_value=None)
        return redis
    
    @pytest.fixture
    def analyzer(self, mock_redis):
        """Create a LongitudinalAnalyzer instance with mock Redis."""
        return LongitudinalAnalyzer(redis=mock_redis)
    
    @pytest.fixture
    def sample_history(self):
        """Sample patient history data for testing."""
        now = datetime.utcnow()
        return [
            {
                "type": "assessment",
                "timestamp": now - timedelta(days=30),
                "wellness_score": 80,
                "emotional_state": {"anxiety": 2, "depression": 1}
            },
            {
                "type": "assessment",
                "timestamp": now - timedelta(days=25),
                "wellness_score": 75,
                "emotional_state": {"anxiety": 3, "depression": 2}
            },
            {
                "type": "crisis_alert",
                "timestamp": now - timedelta(days=23),
                "severity": CrisisSeverity.MODERATE.name,
                "domain": RiskDomain.ANXIETY.name,
                "acknowledged": True
            },
            {
                "type": "intervention",
                "timestamp": now - timedelta(days=22),
                "intervention_type": "COPING_SKILLS",
                "status": "IN_PROGRESS"
            },
            {
                "type": "assessment",
                "timestamp": now - timedelta(days=20),
                "wellness_score": 70,
                "emotional_state": {"anxiety": 4, "depression": 3}
            },
            {
                "type": "assessment",
                "timestamp": now - timedelta(days=15),
                "wellness_score": 65,
                "emotional_state": {"anxiety": 4, "depression": 4}
            },
            {
                "type": "crisis_alert",
                "timestamp": now - timedelta(days=14),
                "severity": CrisisSeverity.MODERATE.name,
                "domain": RiskDomain.ANXIETY.name,
                "acknowledged": True
            },
            {
                "type": "intervention",
                "timestamp": now - timedelta(days=13),
                "intervention_type": "COPING_SKILLS",
                "status": "COMPLETED",
                "completed_at": (now - timedelta(days=10)).isoformat()
            },
            {
                "type": "assessment",
                "timestamp": now - timedelta(days=10),
                "wellness_score": 72,
                "emotional_state": {"anxiety": 3, "depression": 3}
            },
            {
                "type": "assessment",
                "timestamp": now - timedelta(days=5),
                "wellness_score": 78,
                "emotional_state": {"anxiety": 2, "depression": 2}
            },
            {
                "type": "assessment",
                "timestamp": now - timedelta(days=1),
                "wellness_score": 82,
                "emotional_state": {"anxiety": 1, "depression": 1}
            }
        ]
    
    async def test_analyze_patient_history_empty(self, analyzer):
        """Test analyzing patient history with no data."""
        # Mock the _get_patient_history method to return empty list
        analyzer._get_patient_history = AsyncMock(return_value=[])
        
        # Call the method
        result = await analyzer.analyze_patient_history(patient_id="test_patient", days=90)
        
        # Verify the result
        assert result["patient_id"] == "test_patient"
        assert result["trend"] == TrendDirection.STABLE
        assert result["confidence"] == 0.0
        assert result["data_points"] == 0
    
    async def test_analyze_patient_history(self, analyzer, sample_history):
        """Test analyzing patient history with sample data."""
        # Mock the _get_patient_history method to return sample data
        analyzer._get_patient_history = AsyncMock(return_value=sample_history)
        
        # Mock the helper methods
        emotional_trends = {
            "trend": TrendDirection.INCREASING,
            "wellness_slope": 0.5,
            "r_squared": 0.8,
            "p_value": 0.01,
            "volatility": 5,
            "data_points": 6
        }
        analyzer._analyze_emotional_trends = MagicMock(return_value=emotional_trends)
        
        patterns = [
            {
                "domain": RiskDomain.ANXIETY.name,
                "type": "recurring_crisis",
                "interval_days": 9.0,
                "occurrences": 2,
                "last_occurrence": datetime.utcnow().isoformat()
            }
        ]
        analyzer._detect_patterns = MagicMock(return_value=patterns)
        
        risk_factors = ["emotional_instability", "multiple_crisis_events"]
        analyzer._identify_risk_factors = MagicMock(return_value=risk_factors)
        
        analyzer._determine_trend = MagicMock(return_value=(TrendDirection.INCREASING, 0.85))
        
        warning_signs = ["approaching_predicted_crisis_ANXIETY"]
        analyzer._identify_warning_signs = MagicMock(return_value=warning_signs)
        
        # Call the method
        result = await analyzer.analyze_patient_history(patient_id="test_patient", days=90)
        
        # Verify the result
        assert result["patient_id"] == "test_patient"
        assert result["trend"] == TrendDirection.INCREASING
        assert result["confidence"] == 0.85
        assert result["data_points"] == len(sample_history)
        assert result["period_days"] == 90
        assert result["patterns"] == patterns
        assert result["warning_signs"] == warning_signs
        assert result["risk_factors"] == risk_factors
    
    async def test_early_warning_check(self, analyzer):
        """Test early warning check functionality."""
        # Mock analyze_patient_history to return different results for different day ranges
        async def mock_analyze(patient_id, days):
            if days == 30:
                return {
                    "patient_id": patient_id,
                    "trend": TrendDirection.INCREASING,
                    "confidence": 0.7,
                    "warning_signs": ["declining_emotional_trend", "high_emotional_volatility"],
                    "risk_factors": ["emotional_instability"]
                }
            else:  # 90 days
                return {
                    "patient_id": patient_id,
                    "trend": TrendDirection.STABLE,
                    "confidence": 0.6,
                    "warning_signs": [],
                    "risk_factors": []
                }
        
        analyzer.analyze_patient_history = AsyncMock(side_effect=mock_analyze)
        
        # Call the method
        result = await analyzer.early_warning_check(patient_id="test_patient")
        
        # Verify the result
        assert result["patient_id"] == "test_patient"
        assert result["warning_status"] == "moderate"  # Based on warning level calculation in the method
        assert result["warning_level"] >= 3  # Should have several warning factors
        assert len(result["warning_factors"]) == 2
        assert result["recent_trend"] == TrendDirection.INCREASING
        assert result["longer_trend"] == TrendDirection.STABLE
    
    def test_analyze_emotional_trends_decreasing(self, analyzer):
        """Test emotional trend analysis with decreasing trend."""
        now = datetime.utcnow()
        history = [
            {
                "type": "assessment",
                "timestamp": now - timedelta(days=30),
                "wellness_score": 85
            },
            {
                "type": "assessment",
                "timestamp": now - timedelta(days=20),
                "wellness_score": 75
            },
            {
                "type": "assessment",
                "timestamp": now - timedelta(days=10),
                "wellness_score": 65
            },
            {
                "type": "assessment",
                "timestamp": now - timedelta(days=5),
                "wellness_score": 60
            },
        ]
        
        result = analyzer._analyze_emotional_trends(history)
        
        assert result["trend"] == TrendDirection.DECREASING
        assert result["wellness_slope"] < 0
        assert result["data_points"] == 4
    
    def test_analyze_emotional_trends_increasing(self, analyzer):
        """Test emotional trend analysis with increasing trend."""
        now = datetime.utcnow()
        history = [
            {
                "type": "assessment",
                "timestamp": now - timedelta(days=30),
                "wellness_score": 60
            },
            {
                "type": "assessment",
                "timestamp": now - timedelta(days=20),
                "wellness_score": 65
            },
            {
                "type": "assessment",
                "timestamp": now - timedelta(days=10),
                "wellness_score": 75
            },
            {
                "type": "assessment",
                "timestamp": now - timedelta(days=5),
                "wellness_score": 85
            },
        ]
        
        result = analyzer._analyze_emotional_trends(history)
        
        assert result["trend"] == TrendDirection.INCREASING
        assert result["wellness_slope"] > 0
        assert result["data_points"] == 4
    
    def test_detect_patterns(self, analyzer):
        """Test pattern detection in patient history."""
        now = datetime.utcnow()
        
        # Create history with recurring crises at regular intervals
        history = []
        
        # Add recurring anxiety crises every 7 days
        for i in range(4):
            history.append({
                "type": "crisis_alert",
                "timestamp": now - timedelta(days=28 - (i * 7)),
                "severity": CrisisSeverity.MODERATE.name,
                "domain": RiskDomain.ANXIETY.name
            })
        
        # Add some assessments before crises to test emotional triggers
        for i in range(4):
            history.append({
                "type": "assessment",
                "timestamp": now - timedelta(days=29 - (i * 7)),
                "wellness_score": 65
            })
        
        result = analyzer._detect_patterns(history)
        
        # Should detect the recurring anxiety pattern
        assert len(result) > 0
        recurring_patterns = [p for p in result if p["type"] == "recurring_crisis"]
        assert len(recurring_patterns) > 0
        assert recurring_patterns[0]["domain"] == RiskDomain.ANXIETY.name
        assert abs(recurring_patterns[0]["interval_days"] - 7.0) < 0.5  # Should be close to 7 days
    
    def test_identify_risk_factors(self, analyzer):
        """Test risk factor identification."""
        now = datetime.utcnow()
        
        # Create history with multiple crisis events including a severe one
        history = [
            {
                "type": "crisis_alert",
                "timestamp": now - timedelta(days=30),
                "severity": CrisisSeverity.MODERATE.name,
                "domain": RiskDomain.ANXIETY.name
            },
            {
                "type": "crisis_alert",
                "timestamp": now - timedelta(days=20),
                "severity": CrisisSeverity.SEVERE.name,
                "domain": RiskDomain.DEPRESSION.name
            },
            {
                "type": "crisis_alert",
                "timestamp": now - timedelta(days=10),
                "severity": CrisisSeverity.MODERATE.name,
                "domain": RiskDomain.SELF_HARM.name
            }
        ]
        
        # Create emotional trends with high volatility
        emotional_trends = {
            "trend": TrendDirection.DECREASING,
            "r_squared": 0.7,
            "volatility": 30
        }
        
        result = analyzer._identify_risk_factors(history, emotional_trends)
        
        # Should identify multiple risk factors
        assert "multiple_crisis_events" in result
        assert "history_of_severe_crisis" in result
        assert "declining_emotional_wellbeing" in result
        assert "emotional_instability" in result
        assert "history_of_self_harm_ideation" in result
