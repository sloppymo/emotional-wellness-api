"""
Unit tests for clinical analytics module.
"""

import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from clinical.analytics import ClinicalAnalytics, TrendDirection
from symbolic.moss.crisis_classifier import CrisisSeverity


class TestClinicalAnalytics:
    """Test suite for clinical analytics module."""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis instance."""
        redis = AsyncMock()
        # Mock the keys and get methods
        redis.keys = AsyncMock(return_value=[])
        redis.get = AsyncMock(return_value=None)
        return redis
    
    @pytest.fixture
    def analytics(self, mock_redis):
        """Create a ClinicalAnalytics instance with mock Redis."""
        return ClinicalAnalytics(redis=mock_redis)
    
    async def test_get_crisis_trends_empty(self, analytics):
        """Test getting crisis trends with no data."""
        result = await analytics.get_crisis_trends(days=30)
        assert "time_periods" in result
        assert "alert_counts" in result
        assert len(result["time_periods"]) == 0
        assert len(result["alert_counts"]) == 0
    
    @pytest.mark.parametrize("alert_data, expected_trend", [
        # No alerts case
        ([], TrendDirection.STABLE),
        
        # Increasing trend
        ([
            {"timestamp": (datetime.utcnow() - timedelta(days=10)).isoformat(), "severity": "MILD", "priority": "LOW"},
            {"timestamp": (datetime.utcnow() - timedelta(days=8)).isoformat(), "severity": "MODERATE", "priority": "MEDIUM"},
            {"timestamp": (datetime.utcnow() - timedelta(days=6)).isoformat(), "severity": "MODERATE", "priority": "MEDIUM"},
            {"timestamp": (datetime.utcnow() - timedelta(days=4)).isoformat(), "severity": "SEVERE", "priority": "HIGH"},
            {"timestamp": (datetime.utcnow() - timedelta(days=2)).isoformat(), "severity": "SEVERE", "priority": "HIGH"},
        ], TrendDirection.UP),
        
        # Decreasing trend
        ([
            {"timestamp": (datetime.utcnow() - timedelta(days=10)).isoformat(), "severity": "SEVERE", "priority": "HIGH"},
            {"timestamp": (datetime.utcnow() - timedelta(days=8)).isoformat(), "severity": "SEVERE", "priority": "HIGH"}, 
            {"timestamp": (datetime.utcnow() - timedelta(days=6)).isoformat(), "severity": "MODERATE", "priority": "MEDIUM"},
            {"timestamp": (datetime.utcnow() - timedelta(days=4)).isoformat(), "severity": "MILD", "priority": "LOW"},
        ], TrendDirection.DOWN),
        
        # Stable trend (few alerts, evenly distributed)
        ([
            {"timestamp": (datetime.utcnow() - timedelta(days=28)).isoformat(), "severity": "MILD", "priority": "LOW"},
            {"timestamp": (datetime.utcnow() - timedelta(days=14)).isoformat(), "severity": "MILD", "priority": "LOW"},
            {"timestamp": (datetime.utcnow() - timedelta(days=1)).isoformat(), "severity": "MILD", "priority": "LOW"},
        ], TrendDirection.STABLE),
    ])
    async def test_get_crisis_trends(self, analytics, mock_redis, alert_data, expected_trend):
        """Test getting crisis trends with various data patterns."""
        # Setup mock alert data
        mock_keys = [f"clinical:alert:{i}" for i in range(len(alert_data))]
        mock_redis.keys.return_value = mock_keys
        
        # Mock Redis get method to return different values for different keys
        async def mock_get(key):
            index = int(key.split(":")[-1])
            if index < len(alert_data):
                return json.dumps(alert_data[index])
            return None
        
        mock_redis.get.side_effect = mock_get
        
        # Call the function
        result = await analytics.get_crisis_trends(days=30)
        
        # Verify the result
        assert "trend" in result
        assert result["trend"] == expected_trend
    
    async def test_get_intervention_outcomes(self, analytics, mock_redis):
        """Test getting intervention outcomes."""
        # Setup mock data
        interventions = [
            {
                "intervention_type": "SAFETY_PLAN", 
                "status": "COMPLETED", 
                "created_at": (datetime.utcnow() - timedelta(days=5)).isoformat(),
                "completed_at": (datetime.utcnow() - timedelta(days=3)).isoformat()
            },
            {
                "intervention_type": "SAFETY_PLAN",
                "status": "CANCELED",
                "created_at": (datetime.utcnow() - timedelta(days=10)).isoformat()
            },
            {
                "intervention_type": "REFERRAL",
                "status": "COMPLETED",
                "created_at": (datetime.utcnow() - timedelta(days=15)).isoformat(),
                "completed_at": (datetime.utcnow() - timedelta(days=12)).isoformat()
            }
        ]
        
        # Mock Redis
        mock_keys = [f"clinical:intervention:{i}" for i in range(len(interventions))]
        mock_redis.keys.return_value = mock_keys
        
        async def mock_get(key):
            index = int(key.split(":")[-1])
            if index < len(interventions):
                return json.dumps(interventions[index])
            return None
        
        mock_redis.get.side_effect = mock_get
        
        # Call the function
        result = await analytics.get_intervention_outcomes()
        
        # Verify the result
        assert "outcomes_by_type" in result
        assert "SAFETY_PLAN" in result["outcomes_by_type"]
        assert "REFERRAL" in result["outcomes_by_type"]
        assert result["outcomes_by_type"]["SAFETY_PLAN"]["total"] == 2
        assert result["outcomes_by_type"]["SAFETY_PLAN"]["completed"] == 1
        assert result["outcomes_by_type"]["SAFETY_PLAN"]["canceled"] == 1
        assert result["outcomes_by_type"]["REFERRAL"]["total"] == 1
        assert result["outcomes_by_type"]["REFERRAL"]["completed"] == 1
        
    async def test_get_patient_risk_stratification(self, analytics, mock_redis):
        """Test getting patient risk stratification."""
        # Setup mock data
        profiles = [
            {"risk_level": "MILD", "risk_factors": ["stress", "insomnia"], "protective_factors": ["social_support"]},
            {"risk_level": "MODERATE", "risk_factors": ["depression", "anxiety"], "protective_factors": ["therapy"]},
            {"risk_level": "SEVERE", "risk_factors": ["suicidal_ideation", "hopelessness"], "protective_factors": []}
        ]
        
        # Mock Redis
        mock_keys = [f"clinical:patient:{i}:risk_profile" for i in range(len(profiles))]
        mock_redis.keys.return_value = mock_keys
        
        async def mock_get(key):
            index = int(key.split(":")[-2])
            if index < len(profiles):
                return json.dumps(profiles[index])
            return None
        
        mock_redis.get.side_effect = mock_get
        
        # Call the function
        result = await analytics.get_patient_risk_stratification()
        
        # Verify the result
        assert "risk_distribution" in result
        assert "top_risk_factors" in result
        assert "top_protective_factors" in result
        assert result["total_patients_analyzed"] == 3
        assert result["risk_distribution"]["MILD"] == 1
        assert result["risk_distribution"]["MODERATE"] == 1
        assert result["risk_distribution"]["SEVERE"] == 1
        
        # Check that risk factors were counted correctly
        risk_factors_dict = {item["factor"]: item["count"] for item in result["top_risk_factors"]}
        assert "suicidal_ideation" in risk_factors_dict
        assert "depression" in risk_factors_dict
        
        # Check that protective factors were counted correctly
        protective_factors_dict = {item["factor"]: item["count"] for item in result["top_protective_factors"]}
        assert "social_support" in protective_factors_dict
        assert "therapy" in protective_factors_dict
