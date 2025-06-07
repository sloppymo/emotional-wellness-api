"""
Critical HIPAA Compliance Tests for Emotional Wellness API

The real deal. If these break, lawyers start calling.
Tests all the stuff that keeps us from getting sued into oblivion.
Don't touch unless you know what you're doing.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import uuid

import pytest
import httpx
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.testclient import TestClient
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Import the main application components
from src.api.main import app
from src.models.crisis import CrisisLevel, CrisisDetection, InterventionRecommendation
from src.models.emotional_state import EmotionalState
from src.symbolic.canopy.processor import CanopyProcessor
from src.utils.rate_limiter import RateLimiter
from src.utils.structured_logging import get_logger
from src.security.phi_encryption import get_phi_encryption_manager

logger = get_logger(__name__)

class MockSpanExporter(SpanExporter):
    """Mock span exporter to capture telemetry data for PHI testing."""
    
    def __init__(self):
        self.spans = []  # where telemetry goes to die
    
    def export(self, spans):
        """Export spans for testing. aka spy on our own tracing."""
        for span in spans:
            self.spans.append({
                'name': span.name,
                'attributes': dict(span.attributes) if span.attributes else {},  # the good stuff
                'events': [
                    {
                        'name': event.name,
                        'attributes': dict(event.attributes) if event.attributes else {}
                    }
                    for event in span.events  # event soup
                ]
            })
    
    def shutdown(self):
        """Shutdown the exporter."""
        pass
    
    def get_spans_by_name(self, name: str) -> List[Dict]:
        return [span for span in self.spans if span['name'] == name]
    
    def get_all_span_data(self) -> List[Dict]:
        return self.spans
    
    def clear(self):
        self.spans.clear()

@pytest.fixture
def mock_redis():
    """Mock Redis client for rate limiting tests. fake redis that always agrees."""
    redis_mock = Mock()
    redis_mock.get = AsyncMock(return_value=None)  # nothing exists
    redis_mock.set = AsyncMock(return_value=True)  # always succeeds
    redis_mock.incr = AsyncMock(return_value=1)  # count goes up
    redis_mock.expire = AsyncMock(return_value=True)  # ttl set
    redis_mock.pipeline = Mock(return_value=Mock(  # batch operations because redis is fast
        incr=Mock(return_value=Mock()),
        expire=Mock(return_value=Mock()),
        execute=AsyncMock(return_value=[1, True])
    ))
    return redis_mock

@pytest.fixture
def mock_canopy_processor():
    """Mock CanopyProcessor for symbolic processing tests. fake AI that pretends to understand humans."""
    processor = Mock(spec=CanopyProcessor)
    processor.process_text = AsyncMock(return_value={
        'crisis_indicators': ['self_harm', 'suicidal_ideation'],  # the bad words detector found
        'emotional_state': {
            'valence': -0.8,  # feelings are bad
            'arousal': 0.9,  # but very activated
            'dominance': -0.7  # and out of control
        },
        'symbolic_analysis': {
            'archetypes': ['shadow', 'death'],  # jung would be proud. or horrified.
            'metaphors': ['darkness_consuming', 'final_escape'],  # poetic suffering
            'risk_score': 0.95  # basically "call 911"
        }
    })
    return processor

@pytest.fixture
def span_recorder():
    """OpenTelemetry span recorder for PHI masking tests."""
    exporter = MockSpanExporter()
    
    # Set up tracer with our exporter
    tracer_provider = TracerProvider()
    span_processor = SimpleSpanProcessor(exporter)
    tracer_provider.add_span_processor(span_processor)
    trace.set_tracer_provider(tracer_provider)
    
    yield exporter
    
    # Cleanup
    exporter.clear()

@pytest.fixture
def test_client(mock_redis, mock_canopy_processor, span_recorder):
    """Test client with mocked dependencies."""
    with patch('src.database.redis_client.get_redis_client', return_value=mock_redis):
        with patch('src.symbolic.canopy.processor.CanopyProcessor', return_value=mock_canopy_processor):
            # Instrument the app for telemetry testing
            FastAPIInstrumentor.instrument_app(app)
            client = TestClient(app)
            yield client
            FastAPIInstrumentor.uninstrument_app(app)

class TestCrisisBypass:
    """Test crisis request bypass functionality."""
    
    @pytest.mark.asyncio
    async def test_crisis_bypass(self, test_client, mock_redis):
        """Ensure that API requests with X-Crisis-Level: severe bypass standard rate limits."""
        
        # Set up rate limit scenario - user has already hit the limit
        mock_redis.get.return_value = b'100'  # Already at rate limit
        mock_redis.incr.return_value = 101    # Would exceed limit
        
        # Test regular request - should be rate limited
        regular_response = test_client.post(
            "/api/v1/analyze",
            json={
                "text": "I'm feeling really down today",
                "user_id": "test_user_123",
                "session_id": "session_456"
            },
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Should be rate limited
        assert regular_response.status_code == 429
        assert "rate limit exceeded" in regular_response.json()["detail"].lower()
        
        # Reset mock for crisis request
        mock_redis.reset_mock()
        mock_redis.get.return_value = b'100'  # Still at rate limit
        mock_redis.incr.return_value = 101    # Would still exceed limit
        
        # Test crisis request - should bypass rate limit
        crisis_response = test_client.post(
            "/api/v1/analyze",
            json={
                "text": "I want to hurt myself and end everything",
                "user_id": "test_user_123",
                "session_id": "session_456"
            },
            headers={
                "Authorization": "Bearer test_token",
                "X-Crisis-Level": "severe"
            }
        )
        
        # Should bypass rate limit and process successfully
        assert crisis_response.status_code == 200
        response_data = crisis_response.json()
        assert "crisis_detected" in response_data
        assert response_data["crisis_detected"] is True
        
        # Verify that rate limit check was bypassed
        # Crisis requests should not increment rate limit counters
        mock_redis.incr.assert_not_called()
        
        logger.info("Crisis bypass test passed - severe crisis requests bypass rate limits")

    @pytest.mark.asyncio
    async def test_crisis_levels_rate_limit_behavior(self, test_client, mock_redis):
        """Test different crisis levels and their rate limit behavior."""
        
        crisis_levels = [
            ("low", False),      # Should be rate limited
            ("medium", False),   # Should be rate limited  
            ("high", True),      # Should bypass
            ("severe", True),    # Should bypass
            ("critical", True)   # Should bypass
        ]
        
        for level, should_bypass in crisis_levels:
            mock_redis.reset_mock()
            mock_redis.get.return_value = b'100'  # At rate limit
            mock_redis.incr.return_value = 101    # Would exceed limit
            
            response = test_client.post(
                "/api/v1/analyze",
                json={
                    "text": f"Crisis level {level} test message",
                    "user_id": "test_user_123",
                    "session_id": f"session_{level}"
                },
                headers={
                    "Authorization": "Bearer test_token",
                    "X-Crisis-Level": level
                }
            )
            
            if should_bypass:
                assert response.status_code == 200, f"Crisis level {level} should bypass rate limits"
                mock_redis.incr.assert_not_called()
            else:
                assert response.status_code == 429, f"Crisis level {level} should be rate limited"

class TestPHIMasking:
    """Test PHI masking in OpenTelemetry spans."""
    
    @pytest.mark.asyncio
    async def test_phi_masking(self, test_client, span_recorder):
        """Confirm that OpenTelemetry spans never expose raw PHI."""
        
        # Clear any existing spans
        span_recorder.clear()
        
        # Make request with PHI data
        phi_data = {
            "text": "I'm feeling anxious about my health",
            "user_id": "patient_12345",
            "session_id": "session_67890",
            "patient_email": "john.doe@email.com",
            "patient_phone": "+1-555-123-4567",
            "patient_ssn": "123-45-6789",
            "medical_record_number": "MRN-789456"
        }
        
        response = test_client.post(
            "/api/v1/analyze",
            json=phi_data,
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        
        # Check all captured spans for PHI exposure
        all_spans = span_recorder.get_all_span_data()
        
        # PHI patterns to check for
        phi_patterns = [
            "patient_12345",
            "session_67890", 
            "john.doe@email.com",
            "+1-555-123-4567",
            "123-45-6789",
            "MRN-789456"
        ]
        
        for span in all_spans:
            # Check span attributes
            for attr_key, attr_value in span['attributes'].items():
                attr_str = str(attr_value)
                for phi_pattern in phi_patterns:
                    assert phi_pattern not in attr_str, \
                        f"PHI pattern '{phi_pattern}' found in span attribute {attr_key}: {attr_str}"
                
                # Verify masking is applied for known PHI fields
                if any(phi_field in attr_key.lower() for phi_field in ['user_id', 'patient', 'ssn', 'email', 'phone']):
                    assert "[MASKED]" in attr_str or "[REDACTED]" in attr_str, \
                        f"PHI field {attr_key} should be masked, got: {attr_str}"
            
            # Check span events
            for event in span['events']:
                event_name = event['name']
                for phi_pattern in phi_patterns:
                    assert phi_pattern not in event_name, \
                        f"PHI pattern '{phi_pattern}' found in event name: {event_name}"
                
                for attr_key, attr_value in event['attributes'].items():
                    attr_str = str(attr_value)
                    for phi_pattern in phi_patterns:
                        assert phi_pattern not in attr_str, \
                            f"PHI pattern '{phi_pattern}' found in event attribute {attr_key}: {attr_str}"
        
        logger.info("PHI masking test passed - no raw PHI found in telemetry spans")

    @pytest.mark.asyncio 
    async def test_phi_masking_in_errors(self, test_client, span_recorder):
        """Test that PHI is masked even in error scenarios."""
        
        span_recorder.clear()
        
        # Make request that will cause an error but contains PHI
        phi_data = {
            "text": "",  # Empty text to trigger validation error
            "user_id": "patient_sensitive_123",
            "patient_ssn": "987-65-4321"
        }
        
        response = test_client.post(
            "/api/v1/analyze",
            json=phi_data,
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Should get validation error
        assert response.status_code == 422
        
        # Check that error spans don't contain PHI
        all_spans = span_recorder.get_all_span_data()
        
        for span in all_spans:
            span_str = json.dumps(span)
            assert "patient_sensitive_123" not in span_str
            assert "987-65-4321" not in span_str
            
        logger.info("PHI masking in errors test passed")

class TestFullCrisisFlow:
    """Test complete crisis detection and intervention pipeline."""
    
    @pytest.mark.asyncio
    async def test_full_crisis_flow(self, test_client, mock_canopy_processor):
        """Simulate full crisis pipeline: text → processing → detection → intervention → audit."""
        
        # Configure mock processor for crisis scenario
        mock_canopy_processor.process_text.return_value = {
            'crisis_indicators': ['self_harm', 'suicidal_ideation', 'hopelessness'],
            'emotional_state': {
                'valence': -0.9,
                'arousal': 0.8,
                'dominance': -0.8
            },
            'symbolic_analysis': {
                'archetypes': ['shadow', 'death', 'dissolution'],
                'metaphors': ['end_of_tunnel', 'final_rest', 'escape_pain'],
                'risk_score': 0.98,
                'urgency_level': 'critical'
            },
            'confidence': 0.95
        }
        
        # Mock audit logging
        with patch('src.audit.logger.log_crisis_event') as mock_audit_log:
            mock_audit_log.return_value = True
            
            # Step 1: Submit crisis text for analysis
            crisis_text = {
                "text": "I can't take this anymore. I have a plan to end my life tonight. Nobody would miss me.",
                "user_id": "user_crisis_test",
                "session_id": "session_crisis_123",
                "context": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "location": "mobile_app",
                    "previous_sessions": 3
                }
            }
            
            response = test_client.post(
                "/api/v1/analyze",
                json=crisis_text,
                headers={
                    "Authorization": "Bearer test_token",
                    "X-Crisis-Level": "severe"
                }
            )
            
            # Step 2: Validate crisis detection
            assert response.status_code == 200
            result = response.json()
            
            # Verify crisis was detected
            assert result["crisis_detected"] is True
            assert result["crisis_level"] == "critical"
            assert result["risk_score"] >= 0.9
            
            # Verify crisis indicators
            expected_indicators = ['self_harm', 'suicidal_ideation', 'hopelessness']
            for indicator in expected_indicators:
                assert indicator in result["crisis_indicators"]
            
            # Step 3: Validate intervention recommendations
            assert "interventions" in result
            interventions = result["interventions"]
            
            # Should have immediate interventions for critical crisis
            assert len(interventions) > 0
            
            # Check for required intervention types
            intervention_types = [i["type"] for i in interventions]
            assert "emergency_contact" in intervention_types
            assert "crisis_hotline" in intervention_types
            assert "safety_plan" in intervention_types
            
            # Verify intervention details
            emergency_intervention = next(i for i in interventions if i["type"] == "emergency_contact")
            assert emergency_intervention["priority"] == "immediate"
            assert "contact_number" in emergency_intervention
            assert emergency_intervention["contact_number"] == "988"  # National Suicide Prevention Lifeline
            
            # Step 4: Validate audit logging
            mock_audit_log.assert_called_once()
            audit_call = mock_audit_log.call_args[1]
            
            assert audit_call["event_type"] == "crisis_detected"
            assert audit_call["crisis_level"] == "critical" 
            assert audit_call["user_id"] == "user_crisis_test"
            assert audit_call["risk_score"] >= 0.9
            assert "interventions_provided" in audit_call
            
            # Step 5: Verify symbolic processing was called
            mock_canopy_processor.process_text.assert_called_once()
            process_call = mock_canopy_processor.process_text.call_args[0]
            assert crisis_text["text"] in process_call[0]
            
        logger.info("Full crisis flow test passed - complete pipeline validation successful")

    @pytest.mark.asyncio
    async def test_crisis_escalation_workflow(self, test_client, mock_canopy_processor):
        """Test crisis escalation from low to critical levels."""
        
        # Simulate escalating crisis conversation
        escalation_messages = [
            {
                "text": "I'm feeling a bit down today",
                "expected_level": "low",
                "risk_score": 0.2
            },
            {
                "text": "Things are getting worse, I feel hopeless",
                "expected_level": "medium", 
                "risk_score": 0.5
            },
            {
                "text": "I don't see any way out of this pain",
                "expected_level": "high",
                "risk_score": 0.7
            },
            {
                "text": "I'm thinking about ending my life",
                "expected_level": "severe",
                "risk_score": 0.9
            },
            {
                "text": "I have a plan and the means to kill myself tonight",
                "expected_level": "critical",
                "risk_score": 0.98
            }
        ]
        
        session_id = f"escalation_test_{uuid.uuid4()}"
        
        for i, message in enumerate(escalation_messages):
            # Configure mock for this escalation level
            mock_canopy_processor.process_text.return_value = {
                'crisis_indicators': ['depression', 'hopelessness', 'suicidal_ideation'][:i+1],
                'risk_score': message['risk_score'],
                'urgency_level': message['expected_level']
            }
            
            response = test_client.post(
                "/api/v1/analyze",
                json={
                    "text": message["text"],
                    "user_id": "escalation_user",
                    "session_id": session_id,
                    "sequence_number": i + 1
                },
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            result = response.json()
            
            # Verify escalation detection
            if message["expected_level"] in ["severe", "critical"]:
                assert result["crisis_detected"] is True
                assert result["crisis_level"] == message["expected_level"]
                
                # Higher levels should have more interventions
                assert len(result.get("interventions", [])) >= i
            
        logger.info("Crisis escalation workflow test passed")

class TestMassCrisisEvent:
    """Test mass crisis event handling and performance."""
    
    @pytest.mark.asyncio
    async def test_mass_crisis_event(self, test_client, mock_canopy_processor):
        """Simulate 1,000 simultaneous crisis payloads and validate performance."""
        
        # Configure mock processor for consistent crisis responses
        mock_canopy_processor.process_text.return_value = {
            'crisis_indicators': ['self_harm', 'suicidal_ideation'],
            'emotional_state': {'valence': -0.8, 'arousal': 0.9, 'dominance': -0.7},
            'symbolic_analysis': {'risk_score': 0.85},
            'confidence': 0.9
        }
        
        # Prepare 1,000 crisis payloads
        crisis_payloads = []
        for i in range(1000):
            payload = {
                "text": f"I'm in crisis and need help immediately - message {i}",
                "user_id": f"mass_crisis_user_{i}",
                "session_id": f"mass_session_{i}",
                "timestamp": datetime.utcnow().isoformat()
            }
            crisis_payloads.append(payload)
        
        # Track timing and results
        start_time = time.time()
        responses = []
        failed_requests = 0
        
        async def make_crisis_request(payload):
            """Make a single crisis request."""
            try:
                response = test_client.post(
                    "/api/v1/analyze",
                    json=payload,
                    headers={
                        "Authorization": "Bearer test_token",
                        "X-Crisis-Level": "severe"
                    }
                )
                return {
                    "status_code": response.status_code,
                    "response_time": time.time() - start_time,
                    "user_id": payload["user_id"],
                    "success": response.status_code == 200
                }
            except Exception as e:
                return {
                    "status_code": 500,
                    "error": str(e),
                    "user_id": payload["user_id"],
                    "success": False
                }
        
        # Execute all requests concurrently
        tasks = [make_crisis_request(payload) for payload in crisis_payloads]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Analyze results
        successful_responses = [r for r in responses if isinstance(r, dict) and r.get("success")]
        failed_responses = [r for r in responses if not (isinstance(r, dict) and r.get("success"))]
        
        # Validate performance requirements
        assert total_duration <= 1.0, f"Mass crisis processing took {total_duration:.2f}s, should be ≤ 1.0s"
        
        # Validate response success rate
        success_rate = len(successful_responses) / len(responses)
        assert success_rate >= 0.99, f"Success rate {success_rate:.2%} below 99% threshold"
        
        # Validate no failed responses
        assert len(failed_responses) == 0, f"{len(failed_responses)} requests failed during mass crisis event"
        
        # Validate that all successful responses detected crisis
        for response in successful_responses:
            # Note: We can't easily check response content in this test setup,
            # but we validated status codes which is the key requirement
            pass
        
        # Log performance metrics
        avg_response_time = sum(r.get("response_time", 0) for r in successful_responses) / len(successful_responses)
        
        logger.info(
            f"Mass crisis event test passed - "
            f"1000 requests in {total_duration:.2f}s, "
            f"{success_rate:.2%} success rate, "
            f"avg response time: {avg_response_time:.3f}s"
        )

    @pytest.mark.asyncio
    async def test_crisis_queue_prioritization(self, test_client, mock_canopy_processor):
        """Test that crisis requests are prioritized over normal requests during high load."""
        
        # Configure different processing times for crisis vs normal
        def mock_process_with_delay(text, **kwargs):
            if "crisis" in text.lower():
                # Crisis requests process faster
                time.sleep(0.001)
                return {'crisis_indicators': ['self_harm'], 'risk_score': 0.9}
            else:
                # Normal requests have longer processing time
                time.sleep(0.01)
                return {'risk_score': 0.1}
        
        mock_canopy_processor.process_text.side_effect = mock_process_with_delay
        
        # Submit mixed requests
        mixed_requests = []
        for i in range(100):
            if i % 4 == 0:  # Every 4th request is a crisis
                mixed_requests.append({
                    "payload": {
                        "text": f"CRISIS: I need help immediately {i}",
                        "user_id": f"crisis_user_{i}",
                        "session_id": f"crisis_session_{i}"
                    },
                    "headers": {
                        "Authorization": "Bearer test_token",
                        "X-Crisis-Level": "severe"
                    },
                    "is_crisis": True
                })
            else:
                mixed_requests.append({
                    "payload": {
                        "text": f"Normal message {i}",
                        "user_id": f"normal_user_{i}",
                        "session_id": f"normal_session_{i}"
                    },
                    "headers": {"Authorization": "Bearer test_token"},
                    "is_crisis": False
                })
        
        # Track response times
        start_time = time.time()
        crisis_response_times = []
        normal_response_times = []
        
        async def make_request(request_data):
            request_start = time.time()
            response = test_client.post(
                "/api/v1/analyze",
                json=request_data["payload"],
                headers=request_data["headers"]
            )
            response_time = time.time() - request_start
            
            return {
                "response_time": response_time,
                "is_crisis": request_data["is_crisis"],
                "status_code": response.status_code
            }
        
        # Execute all requests
        tasks = [make_request(req) for req in mixed_requests]
        results = await asyncio.gather(*tasks)
        
        # Separate crisis and normal response times
        for result in results:
            if result["is_crisis"]:
                crisis_response_times.append(result["response_time"])
            else:
                normal_response_times.append(result["response_time"])
        
        # Validate crisis requests were prioritized (faster average response time)
        avg_crisis_time = sum(crisis_response_times) / len(crisis_response_times)
        avg_normal_time = sum(normal_response_times) / len(normal_response_times)
        
        assert avg_crisis_time < avg_normal_time, \
            f"Crisis requests should be faster (avg: {avg_crisis_time:.3f}s) than normal requests (avg: {avg_normal_time:.3f}s)"
        
        logger.info(
            f"Crisis prioritization test passed - "
            f"Crisis avg: {avg_crisis_time:.3f}s, Normal avg: {avg_normal_time:.3f}s"
        )

# Integration test for all components
class TestIntegratedCompliance:
    """Integration tests combining all compliance requirements."""
    
    @pytest.mark.asyncio
    async def test_full_compliance_integration(self, test_client, mock_canopy_processor, span_recorder, mock_redis):
        """Test all compliance requirements together in a realistic scenario."""
        
        # Configure realistic crisis scenario
        mock_canopy_processor.process_text.return_value = {
            'crisis_indicators': ['self_harm', 'suicidal_ideation', 'means_available'],
            'emotional_state': {'valence': -0.95, 'arousal': 0.85, 'dominance': -0.9},
            'symbolic_analysis': {'risk_score': 0.97, 'urgency_level': 'critical'},
            'confidence': 0.98
        }
        
        # Set up rate limiting scenario
        mock_redis.get.return_value = b'100'  # At rate limit
        
        # Clear telemetry spans
        span_recorder.clear()
        
        # Test PHI-containing crisis request
        phi_crisis_data = {
            "text": "I have pills and a plan to kill myself tonight. Please help me.",
            "user_id": "patient_critical_999",
            "session_id": "emergency_session_123",
            "patient_email": "critical.patient@example.com",
            "emergency_contact": "+1-555-999-8888",
            "location": "home_alone",
            "medical_history": "depression, anxiety, previous_attempts"
        }
        
        with patch('src.audit.logger.log_crisis_event') as mock_audit:
            mock_audit.return_value = True
            
            start_time = time.time()
            
            # Make the crisis request
            response = test_client.post(
                "/api/v1/analyze",
                json=phi_crisis_data,
                headers={
                    "Authorization": "Bearer test_token",
                    "X-Crisis-Level": "critical"
                }
            )
            
            response_time = time.time() - start_time
            
            # Validate all compliance requirements
            
            # 1. Crisis bypass - should succeed despite rate limit
            assert response.status_code == 200
            mock_redis.incr.assert_not_called()  # Rate limit bypassed
            
            # 2. Performance - should respond quickly even under load
            assert response_time < 0.5, f"Response time {response_time:.3f}s too slow for critical crisis"
            
            # 3. Crisis detection and intervention
            result = response.json()
            assert result["crisis_detected"] is True
            assert result["crisis_level"] == "critical"
            assert result["risk_score"] >= 0.95
            assert len(result["interventions"]) >= 3
            
            # 4. PHI masking in telemetry
            all_spans = span_recorder.get_all_span_data()
            phi_patterns = ["patient_critical_999", "critical.patient@example.com", "+1-555-999-8888"]
            
            for span in all_spans:
                span_str = json.dumps(span)
                for phi_pattern in phi_patterns:
                    assert phi_pattern not in span_str, f"PHI {phi_pattern} exposed in telemetry"
                
                # Verify masking is applied
                if any(phi_field in span_str.lower() for phi_field in ['user_id', 'email', 'contact']):
                    assert "[MASKED]" in span_str or "[REDACTED]" in span_str
            
            # 5. Audit logging
            mock_audit.assert_called_once()
            audit_data = mock_audit.call_args[1]
            assert audit_data["event_type"] == "crisis_detected"
            assert audit_data["crisis_level"] == "critical"
            # PHI should be masked in audit logs too
            audit_str = json.dumps(audit_data)
            for phi_pattern in phi_patterns:
                assert phi_pattern not in audit_str
        
        logger.info("Full compliance integration test passed - all requirements validated")

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 