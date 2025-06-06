import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from redis import Redis
import json
import ipaddress
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient

from src.api.middleware.rate_limit_advanced import (
    RateLimitAdvanced,
    CircuitBreakerState,
    TokenBucketState,
    GeographicRule,
    MLFeatures,
    APITier,
    ComplianceRule,
    DynamicRule
)
from src.api.middleware.rate_limit_types import RateLimitCategory

@pytest.fixture
def redis_mock():
    """Mock Redis client."""
    return Mock(spec=Redis)

@pytest.fixture
def rate_limit_advanced(redis_mock):
    """Create RateLimitAdvanced instance with mocked Redis."""
    return RateLimitAdvanced(
        redis_client=redis_mock,
        enable_circuit_breaker=True,
        enable_token_bucket=True,
        enable_geographic=True,
        enable_ml=True
    )

@pytest.fixture
def app():
    """Create FastAPI test app."""
    return FastAPI()

class TestCircuitBreaker:
    """Test circuit breaker functionality."""
    
    def test_circuit_breaker_initial_state(self, rate_limit_advanced):
        """Test initial circuit breaker state."""
        assert rate_limit_advanced.check_circuit_breaker("/test", "public") is True
    
    def test_circuit_breaker_trip(self, rate_limit_advanced, redis_mock):
        """Test circuit breaker tripping after failures."""
        endpoint = "/test"
        category = "public"
        
        # Simulate failures
        for _ in range(5):  # Default failure threshold
            rate_limit_advanced.record_circuit_breaker_failure(endpoint, category)
        
        # Circuit should be open
        assert rate_limit_advanced.check_circuit_breaker(endpoint, category) is False
    
    def test_circuit_breaker_half_open(self, rate_limit_advanced, redis_mock):
        """Test circuit breaker half-open state."""
        endpoint = "/test"
        category = "public"
        
        # Trip circuit breaker
        for _ in range(5):
            rate_limit_advanced.record_circuit_breaker_failure(endpoint, category)
        
        # Move time forward past half-open timeout
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime.now() + timedelta(seconds=31)
            assert rate_limit_advanced.check_circuit_breaker(endpoint, category) is True
    
    def test_circuit_breaker_recovery(self, rate_limit_advanced, redis_mock):
        """Test circuit breaker recovery after success."""
        endpoint = "/test"
        category = "public"
        
        # Trip circuit breaker
        for _ in range(5):
            rate_limit_advanced.record_circuit_breaker_failure(endpoint, category)
        
        # Move to half-open
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime.now() + timedelta(seconds=31)
            
            # Record successes
            for _ in range(3):  # Default success threshold
                rate_limit_advanced.record_circuit_breaker_success(endpoint, category)
            
            # Circuit should be closed
            assert rate_limit_advanced.check_circuit_breaker(endpoint, category) is True

class TestTokenBucket:
    """Test token bucket functionality."""
    
    def test_token_bucket_initial_state(self, rate_limit_advanced):
        """Test initial token bucket state."""
        allowed, remaining = rate_limit_advanced.check_token_bucket("test_client", "public")
        assert allowed is True
        assert remaining > 0
    
    def test_token_bucket_consumption(self, rate_limit_advanced, redis_mock):
        """Test token consumption."""
        client_id = "test_client"
        category = "public"
        
        # Consume all tokens
        for _ in range(100):  # Default capacity
            allowed, _ = rate_limit_advanced.check_token_bucket(client_id, category)
            assert allowed is True
        
        # Next request should be rejected
        allowed, remaining = rate_limit_advanced.check_token_bucket(client_id, category)
        assert allowed is False
        assert remaining == 0
    
    def test_token_bucket_refill(self, rate_limit_advanced, redis_mock):
        """Test token bucket refill."""
        client_id = "test_client"
        category = "public"
        
        # Consume all tokens
        for _ in range(100):
            rate_limit_advanced.check_token_bucket(client_id, category)
        
        # Move time forward to allow refill
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime.now() + timedelta(seconds=10)
            allowed, remaining = rate_limit_advanced.check_token_bucket(client_id, category)
            assert allowed is True
            assert remaining > 0
    
    def test_token_bucket_burst(self, rate_limit_advanced, redis_mock):
        """Test token bucket burst handling."""
        client_id = "test_client"
        category = "public"
        
        # Update bucket config with burst multiplier
        rate_limit_advanced.update_token_bucket_config(
            client_id,
            category,
            capacity=100,
            refill_rate=10,
            burst_multiplier=2.0
        )
        
        # Should allow burst up to 200 tokens
        for _ in range(200):
            allowed, _ = rate_limit_advanced.check_token_bucket(client_id, category)
            assert allowed is True
        
        # Next request should be rejected
        allowed, remaining = rate_limit_advanced.check_token_bucket(client_id, category)
        assert allowed is False
        assert remaining == 0

class TestGeographicControls:
    """Test geographic rate limiting functionality."""
    
    def test_geographic_rule_creation(self, rate_limit_advanced):
        """Test creating geographic rules."""
        rule = GeographicRule(
            country_code="US",
            rate_limit=1000,
            burst_limit=1500,
            quota=10000,
            timezone="America/New_York"
        )
        
        rate_limit_advanced.update_geographic_rule("US", rule)
        
        # Verify rule was stored
        redis_mock = rate_limit_advanced.redis
        rules_data = redis_mock.get(rate_limit_advanced.geographic_rules_key)
        rules = json.loads(rules_data)
        assert "US" in rules
        assert rules["US"]["rate_limit"] == 1000
    
    def test_geographic_blacklist(self, rate_limit_advanced):
        """Test geographic blacklisting."""
        rule = GeographicRule(
            country_code="XX",
            rate_limit=0,
            burst_limit=0,
            is_blacklisted=True
        )
        
        rate_limit_advanced.update_geographic_rule("XX", rule)
        
        # Check blacklisted country
        allowed, reason = rate_limit_advanced.check_geographic_limits("1.2.3.4", "public")
        assert allowed is False
        assert "blacklisted" in reason.lower()
    
    def test_geographic_quota(self, rate_limit_advanced, redis_mock):
        """Test geographic quota enforcement."""
        rule = GeographicRule(
            country_code="US",
            rate_limit=1000,
            burst_limit=1500,
            quota=100
        )
        
        rate_limit_advanced.update_geographic_rule("US", rule)
        
        # Simulate quota usage
        quota_key = rate_limit_advanced.geographic_quotas_key.format("US:public")
        redis_mock.set(quota_key, "100")
        
        # Check quota exceeded
        allowed, reason = rate_limit_advanced.check_geographic_limits("1.2.3.4", "public")
        assert allowed is False
        assert "quota exceeded" in reason.lower()

class TestMachineLearning:
    """Test machine learning anomaly detection."""
    
    def test_feature_extraction(self, rate_limit_advanced):
        """Test ML feature extraction."""
        features = rate_limit_advanced.extract_features({
            "request_rate": 10.0,
            "error_rate": 0.1,
            "avg_response_time": 0.5,
            "unique_ips": 5,
            "payload_size": 1000,
            "time_of_day": 12.5,
            "day_of_week": 1
        })
        
        assert isinstance(features, MLFeatures)
        assert features.request_rate == 10.0
        assert features.error_rate == 0.1
        assert features.unique_ips == 5
    
    def test_anomaly_detection(self, rate_limit_advanced):
        """Test anomaly detection."""
        # Normal features
        normal_features = MLFeatures(
            request_rate=10.0,
            error_rate=0.1,
            avg_response_time=0.5,
            unique_ips=5,
            payload_size=1000,
            time_of_day=12.5,
            day_of_week=1
        )
        
        # Anomalous features
        anomalous_features = MLFeatures(
            request_rate=1000.0,  # Very high request rate
            error_rate=0.9,       # High error rate
            avg_response_time=5.0, # Slow response time
            unique_ips=100,       # Many unique IPs
            payload_size=10000,   # Large payload
            time_of_day=3.5,      # Unusual time
            day_of_week=6         # Weekend
        )
        
        # Train model with normal data
        rate_limit_advanced.update_ml_model([normal_features] * 100)
        
        # Check normal features
        is_anomaly, score = rate_limit_advanced.detect_anomaly(normal_features, "public")
        assert is_anomaly is False
        
        # Check anomalous features
        is_anomaly, score = rate_limit_advanced.detect_anomaly(anomalous_features, "public")
        assert is_anomaly is True

class TestAPIManagement:
    """Test API key management functionality."""
    
    def test_api_key_validation(self, rate_limit_advanced, redis_mock):
        """Test API key validation."""
        # Setup test tier
        tier = APITier(
            name="test",
            rate_limit=1000,
            burst_limit=1500,
            quota=10000,
            cost_multiplier=1.0,
            features=["test"],
            price=99.99
        )
        
        # Store tier
        tiers_data = {tier.name: tier.__dict__}
        redis_mock.get.return_value = json.dumps(tiers_data)
        
        # Store API key
        key_data = {"tier": tier.name, "created_at": datetime.now().isoformat()}
        redis_mock.get.return_value = json.dumps(key_data)
        
        # Validate key
        valid, returned_tier = rate_limit_advanced.validate_api_key("test_key")
        assert valid is True
        assert returned_tier.name == tier.name
    
    def test_api_usage_tracking(self, rate_limit_advanced, redis_mock):
        """Test API usage tracking."""
        tier = APITier(
            name="test",
            rate_limit=1000,
            burst_limit=1500,
            quota=10000,
            cost_multiplier=1.5,
            features=["test"],
            price=99.99
        )
        
        # Track usage
        rate_limit_advanced.track_api_usage("test_key", tier, 10.0)
        
        # Verify usage was recorded with cost multiplier
        redis_mock.set.assert_called_with(
            rate_limit_advanced.api_usage_key.format("test_key"),
            "15.0"  # 10.0 * 1.5
        )

class TestCompliance:
    """Test compliance functionality."""
    
    def test_compliance_check(self, rate_limit_advanced):
        """Test compliance rule checking."""
        results = rate_limit_advanced.check_compliance()
        
        assert isinstance(results, list)
        for result in results:
            assert "rule" in result
            assert "compliant" in result
            assert "severity" in result
            assert "required" in result
            assert "documentation" in result
    
    def test_required_compliance_failure(self, rate_limit_advanced):
        """Test required compliance rule failure."""
        # Mock a required rule to fail
        with patch.object(
            rate_limit_advanced,
            '_check_audit_logging',
            return_value=False
        ):
            results = rate_limit_advanced.check_compliance()
            
            # Find the audit logging rule
            audit_rule = next(r for r in results if r["rule"] == "rate_limit_audit_logging")
            assert audit_rule["compliant"] is False
            assert audit_rule["required"] is True

class TestDynamicRules:
    """Test dynamic rule functionality."""
    
    def test_rule_creation(self, rate_limit_advanced):
        """Test creating dynamic rules."""
        rule = DynamicRule(
            name="test_rule",
            condition="request.method == 'POST' and request.path.startswith('/api/v1/phi')",
            action="block",
            priority=1,
            enabled=True,
            version=1,
            metadata={"description": "Test rule"}
        )
        
        success = rate_limit_advanced.add_dynamic_rule(rule)
        assert success is True
    
    def test_rule_evaluation(self, rate_limit_advanced):
        """Test rule evaluation."""
        # Add a test rule
        rule = DynamicRule(
            name="test_rule",
            condition="request.method == 'POST'",
            action="block",
            priority=1,
            enabled=True,
            version=1,
            metadata={}
        )
        
        rate_limit_advanced.add_dynamic_rule(rule)
        
        # Evaluate rules
        context = {
            "request": {
                "method": "POST",
                "path": "/test",
                "headers": {},
                "query_params": {}
            }
        }
        
        results = rate_limit_advanced.evaluate_dynamic_rules(context)
        assert len(results) > 0
        assert results[0]["rule"] == "test_rule"
        assert results[0]["action"] == "block"
    
    def test_rule_priority(self, rate_limit_advanced):
        """Test rule priority handling."""
        # Add rules with different priorities
        rules = [
            DynamicRule(
                name="low_priority",
                condition="True",
                action="allow",
                priority=1,
                enabled=True,
                version=1,
                metadata={}
            ),
            DynamicRule(
                name="high_priority",
                condition="True",
                action="block",
                priority=2,
                enabled=True,
                version=1,
                metadata={}
            )
        ]
        
        for rule in rules:
            rate_limit_advanced.add_dynamic_rule(rule)
        
        # Evaluate rules
        context = {"request": {"method": "GET", "path": "/test"}}
        results = rate_limit_advanced.evaluate_dynamic_rules(context)
        
        # High priority rule should be first
        assert results[0]["rule"] == "high_priority"
        assert results[0]["action"] == "block"

class TestIntegration:
    """Integration tests for rate limiting features."""
    
    @pytest.fixture
    def client(self, app, rate_limit_advanced):
        """Create test client with rate limiting middleware."""
        app.add_middleware(
            RateLimiterMiddleware,
            redis_client=rate_limit_advanced.redis,
            enable_analytics=True,
            enable_caching=True,
            enable_cost_limits=True,
            enable_circuit_breaker=True,
            enable_token_bucket=True,
            enable_geographic=True,
            enable_ml=True,
            enable_tracing=True
        )
        
        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}
        
        return TestClient(app)
    
    def test_integrated_rate_limiting(self, client, rate_limit_advanced, redis_mock):
        """Test integrated rate limiting features."""
        # Setup geographic rule
        rule = GeographicRule(
            country_code="US",
            rate_limit=1000,
            burst_limit=1500,
            quota=100
        )
        rate_limit_advanced.update_geographic_rule("US", rule)
        
        # Setup API tier
        tier = APITier(
            name="test",
            rate_limit=1000,
            burst_limit=1500,
            quota=10000,
            cost_multiplier=1.0,
            features=["test"],
            price=99.99
        )
        tiers_data = {tier.name: tier.__dict__}
        redis_mock.get.return_value = json.dumps(tiers_data)
        
        # Make requests
        headers = {
            "X-API-Key": "test_key",
            "X-Forwarded-For": "1.2.3.4"  # US IP
        }
        
        # Should succeed
        response = client.get("/test", headers=headers)
        assert response.status_code == 200
        
        # Simulate rate limit exceeded
        redis_mock.zcard.return_value = 1000
        
        # Should be rate limited
        response = client.get("/test", headers=headers)
        assert response.status_code == 429
        assert "Retry-After" in response.headers
    
    def test_circuit_breaker_integration(self, client, rate_limit_advanced, redis_mock):
        """Test circuit breaker integration."""
        # Trip circuit breaker
        for _ in range(5):
            rate_limit_advanced.record_circuit_breaker_failure("/test", "public")
        
        # Request should be blocked
        response = client.get("/test")
        assert response.status_code == 403
        assert "circuit breaker" in response.json()["detail"].lower()
    
    def test_geographic_integration(self, client, rate_limit_advanced, redis_mock):
        """Test geographic controls integration."""
        # Setup blacklisted country
        rule = GeographicRule(
            country_code="XX",
            rate_limit=0,
            burst_limit=0,
            is_blacklisted=True
        )
        rate_limit_advanced.update_geographic_rule("XX", rule)
        
        # Request from blacklisted country
        headers = {"X-Forwarded-For": "1.1.1.1"}  # XX IP
        response = client.get("/test", headers=headers)
        assert response.status_code == 403
        assert "blacklisted" in response.json()["detail"].lower()
    
    def test_ml_integration(self, client, rate_limit_advanced, redis_mock):
        """Test ML anomaly detection integration."""
        # Setup anomalous features
        anomalous_features = MLFeatures(
            request_rate=1000.0,
            error_rate=0.9,
            avg_response_time=5.0,
            unique_ips=100,
            payload_size=10000,
            time_of_day=3.5,
            day_of_week=6
        )
        
        # Train model with normal data
        normal_features = MLFeatures(
            request_rate=10.0,
            error_rate=0.1,
            avg_response_time=0.5,
            unique_ips=5,
            payload_size=1000,
            time_of_day=12.5,
            day_of_week=1
        )
        rate_limit_advanced.update_ml_model([normal_features] * 100)
        
        # Simulate anomalous request
        redis_mock.get.side_effect = lambda key: json.dumps({
            "request_rate": 1000.0,
            "error_rate": 0.9,
            "avg_response_time": 5.0,
            "unique_ips": 100,
            "payload_size": 10000
        })
        
        # Request should be blocked
        response = client.get("/test")
        assert response.status_code == 403
        assert "anomaly" in response.json()["detail"].lower() 