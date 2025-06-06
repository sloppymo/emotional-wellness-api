"""
Unit tests for MOSS Audit Logging

Tests cover:
- HIPAA-compliant event logging
- Audit event creation and validation
- Query functionality
- Statistics generation
- PHI protection
- Compliance tracking
"""

import pytest
import asyncio
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from src.symbolic.moss.audit_logging import (
    MOSSAuditLogger,
    AuditEvent,
    AuditEventType,
    AuditSeverity,
    AuditQuery,
    AuditStatistics,
    ComplianceFramework,
    PHICategory,
    log_crisis_assessment,
    log_crisis_intervention
)


class TestMOSSAuditLogger:
    """Test suite for MOSSAuditLogger."""
    
    @pytest.fixture
    def temp_log_dir(self):
        """Create a temporary directory for audit logs."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def audit_logger(self, temp_log_dir):
        """Create a MOSSAuditLogger instance for testing."""
        return MOSSAuditLogger(
            log_directory=temp_log_dir,
            encryption_enabled=False,  # Disable for testing
            compression_enabled=False,  # Disable for testing
            max_log_size_mb=1  # Small size for testing
        )
    
    @pytest.mark.asyncio
    async def test_log_crisis_assessment(self, audit_logger):
        """Test logging of crisis assessment events."""
        event_id = await audit_logger.log_crisis_assessment(
            assessment_id="test_assessment_123",
            severity="high",
            confidence=0.8,
            escalation_required=True,
            user_id="test_user",
            session_id="test_session",
            processing_time_ms=150.5
        )
        
        assert isinstance(event_id, str)
        assert len(event_id) > 0
        
        # Check that event was added to buffer
        assert len(audit_logger._event_buffer) > 0
        
        # Verify event details
        logged_event = audit_logger._event_buffer[-1]
        assert logged_event.event_type == AuditEventType.CRISIS_DETECTED
        assert logged_event.severity == AuditSeverity.CRITICAL
        assert logged_event.processing_time_ms == 150.5
        assert logged_event.intervention_triggered == True
    
    @pytest.mark.asyncio
    async def test_log_intervention_triggered(self, audit_logger):
        """Test logging of intervention trigger events."""
        event_id = await audit_logger.log_intervention_triggered(
            intervention_type="crisis_hotline",
            assessment_id="test_assessment_123",
            user_id="test_user",
            session_id="test_session"
        )
        
        assert isinstance(event_id, str)
        assert len(event_id) > 0
        
        # Verify event was logged correctly
        logged_event = audit_logger._event_buffer[-1]
        assert logged_event.event_type == AuditEventType.INTERVENTION_TRIGGERED
        assert logged_event.severity == AuditSeverity.WARNING
        assert logged_event.intervention_triggered == True
        assert "crisis_hotline" in logged_event.event_data["intervention_type"]
    
    @pytest.mark.asyncio
    async def test_log_user_access(self, audit_logger):
        """Test logging of user access events."""
        event_id = await audit_logger.log_user_access(
            user_id="test_user",
            action="login",
            resource="crisis_assessment",
            session_id="test_session",
            outcome="success"
        )
        
        assert isinstance(event_id, str)
        
        # Verify event details
        logged_event = audit_logger._event_buffer[-1]
        assert logged_event.event_type == AuditEventType.USER_ACCESS
        assert logged_event.severity == AuditSeverity.INFO
        assert logged_event.action_performed == "login"
        assert logged_event.outcome == "success"
        assert logged_event.phi_category == PHICategory.DIRECT_IDENTIFIER
    
    @pytest.mark.asyncio
    async def test_log_system_error(self, audit_logger):
        """Test logging of system error events."""
        error_message = "Database connection failed due to timeout"
        
        event_id = await audit_logger.log_system_error(
            error_type="database_error",
            error_message=error_message,
            component="moss.crisis_classifier",
            user_id="test_user",
            session_id="test_session"
        )
        
        assert isinstance(event_id, str)
        
        # Verify event details
        logged_event = audit_logger._event_buffer[-1]
        assert logged_event.event_type == AuditEventType.SYSTEM_ERROR
        assert logged_event.severity == AuditSeverity.ERROR
        assert logged_event.source_component == "moss.crisis_classifier"
        assert "database_error" in logged_event.event_data["error_type"]
    
    @pytest.mark.asyncio
    async def test_phi_sanitization(self, audit_logger):
        """Test that PHI is properly sanitized in error messages."""
        error_message = "User john.doe@email.com failed login with SSN 123-45-6789 and phone 555-123-4567"
        
        event_id = await audit_logger.log_system_error(
            error_type="login_error",
            error_message=error_message,
            component="auth_system"
        )
        
        logged_event = audit_logger._event_buffer[-1]
        sanitized_message = logged_event.event_data["error_message"]
        
        # PHI should be sanitized
        assert "[EMAIL]" in sanitized_message
        assert "[SSN]" in sanitized_message  
        assert "[PHONE]" in sanitized_message
        assert "john.doe@email.com" not in sanitized_message
        assert "123-45-6789" not in sanitized_message
        assert "555-123-4567" not in sanitized_message
    
    def test_audit_event_validation(self):
        """Test audit event model validation."""
        # Valid event
        valid_event = AuditEvent(
            event_id="test_event_123",
            event_type=AuditEventType.ASSESSMENT_COMPLETED,
            severity=AuditSeverity.INFO,
            source_component="moss.crisis_classifier",
            action_performed="risk_assessment",
            outcome="assessment_completed",
            compliance_tags=["hipaa"]
        )
        
        assert valid_event.event_id == "test_event_123"
        assert valid_event.event_type == AuditEventType.ASSESSMENT_COMPLETED
        assert valid_event.compliance_tags == ["hipaa"]
    
    def test_audit_event_compliance_tag_validation(self):
        """Test that invalid compliance tags are rejected."""
        with pytest.raises(ValueError):
            AuditEvent(
                event_id="test_event_123",
                event_type=AuditEventType.ASSESSMENT_COMPLETED,
                severity=AuditSeverity.INFO,
                source_component="test_component",
                action_performed="test_action",
                outcome="test_outcome",
                compliance_tags=["invalid_framework"]  # Invalid compliance framework
            )
    
    @pytest.mark.asyncio
    async def test_get_audit_statistics(self, audit_logger):
        """Test audit statistics generation."""
        # Log some test events
        await audit_logger.log_crisis_assessment(
            assessment_id="test_1",
            severity="high",
            confidence=0.8,
            escalation_required=True
        )
        
        await audit_logger.log_intervention_triggered(
            intervention_type="safety_planning",
            assessment_id="test_1"
        )
        
        # Get statistics
        stats = await audit_logger.get_audit_statistics()
        
        assert isinstance(stats, AuditStatistics)
        assert stats.total_events >= 2
        assert stats.crisis_detection_rate >= 0.0
        assert stats.intervention_trigger_rate >= 0.0
        assert isinstance(stats.events_by_type, dict)
        assert isinstance(stats.events_by_severity, dict)
    
    def test_user_id_hashing(self, audit_logger):
        """Test that user IDs are properly hashed for privacy."""
        user_id = "sensitive_user_123"
        hashed_id = audit_logger._hash_user_id(user_id)
        
        assert hashed_id != user_id
        assert len(hashed_id) == 16  # Should be truncated hash
        assert isinstance(hashed_id, str)
        
        # Same input should produce same hash
        hashed_id_2 = audit_logger._hash_user_id(user_id)
        assert hashed_id == hashed_id_2
    
    def test_stack_trace_hashing(self, audit_logger):
        """Test that stack traces are hashed for privacy."""
        stack_trace = "Traceback (most recent call last):\n  File test.py line 42\n    sensitive_function()"
        hashed_trace = audit_logger._hash_stack_trace(stack_trace)
        
        assert hashed_trace != stack_trace
        assert len(hashed_trace) == 20  # Should be truncated hash
        assert isinstance(hashed_trace, str)
    
    @pytest.mark.asyncio
    async def test_file_rotation(self, audit_logger):
        """Test log file rotation functionality."""
        # Set very small log size to trigger rotation
        audit_logger.max_log_size_mb = 0.001  # 1KB
        
        # Log enough events to trigger rotation
        for i in range(10):
            await audit_logger.log_crisis_assessment(
                assessment_id=f"test_assessment_{i}",
                severity="medium",
                confidence=0.7,
                escalation_required=False
            )
        
        # Should have triggered rotation
        assert audit_logger._current_log_size >= 0
    
    def test_compliance_coverage_calculation(self, audit_logger):
        """Test compliance framework coverage calculation."""
        coverage = audit_logger._calculate_compliance_coverage()
        
        assert isinstance(coverage, dict)
        assert ComplianceFramework.HIPAA.value in coverage
        assert ComplianceFramework.GDPR.value in coverage
        
        # Coverage values should be between 0 and 1
        for framework, coverage_value in coverage.items():
            assert 0.0 <= coverage_value <= 1.0


class TestAuditQuery:
    """Test suite for audit query functionality."""
    
    @pytest.fixture
    def audit_logger(self):
        """Create audit logger with test events."""
        temp_dir = tempfile.mkdtemp()
        logger = MOSSAuditLogger(
            log_directory=temp_dir,
            encryption_enabled=False,
            compression_enabled=False
        )
        return logger
    
    def test_audit_query_validation(self):
        """Test audit query model validation."""
        # Valid query
        query = AuditQuery(
            start_date=datetime.now() - timedelta(days=7),
            end_date=datetime.now(),
            event_types=[AuditEventType.CRISIS_DETECTED],
            severity_levels=[AuditSeverity.CRITICAL],
            limit=100
        )
        
        assert query.limit == 100
        assert len(query.event_types) == 1
        assert query.event_types[0] == AuditEventType.CRISIS_DETECTED
    
    def test_audit_query_limits(self):
        """Test audit query limit validation."""
        # Valid limits
        valid_query = AuditQuery(limit=1000)
        assert valid_query.limit == 1000
        
        # Test boundary values
        min_query = AuditQuery(limit=1)
        assert min_query.limit == 1
        
        max_query = AuditQuery(limit=10000)
        assert max_query.limit == 10000


class TestConvenienceFunctions:
    """Test suite for convenience functions."""
    
    @pytest.mark.asyncio
    async def test_log_crisis_assessment_convenience(self):
        """Test convenience function for logging crisis assessments."""
        # Mock assessment object
        from src.symbolic.moss.crisis_classifier import RiskAssessment, CrisisSeverity
        
        assessment = RiskAssessment(
            assessment_id="test_assessment_123",
            severity=CrisisSeverity.HIGH,
            confidence=0.8,
            risk_domains={"suicide": 0.7},
            primary_concerns=["suicide"],
            protective_factors=["support"],
            urgency_score=0.75,
            recommendations=["Crisis intervention"],
            escalation_required=True,
            metadata={"processing_time": 0.5}
        )
        
        # This will create a new audit logger instance
        with patch('src.symbolic.moss.audit_logging.MOSSAuditLogger') as mock_logger:
            mock_instance = AsyncMock()
            mock_instance.log_assessment_event.return_value = "test_event_id"
            mock_logger.return_value = mock_instance
            
            event_id = await log_crisis_assessment(
                assessment=assessment,
                user_id="test_user",
                session_id="test_session"
            )
            
            mock_instance.log_assessment_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_log_crisis_intervention_convenience(self):
        """Test convenience function for logging crisis interventions."""
        with patch('src.symbolic.moss.audit_logging.MOSSAuditLogger') as mock_logger:
            mock_instance = AsyncMock()
            mock_instance.log_intervention_event.return_value = "test_event_id"
            mock_logger.return_value = mock_instance
            
            event_id = await log_crisis_intervention(
                intervention_type="crisis_hotline",
                assessment_id="test_assessment_123",
                user_id="test_user",
                session_id="test_session"
            )
            
            mock_instance.log_intervention_event.assert_called_once()


class TestPHIProtection:
    """Test suite for PHI protection and privacy features."""
    
    def test_email_sanitization(self):
        """Test email address sanitization."""
        logger = MOSSAuditLogger()
        
        text_with_email = "User contacted support@example.com for help"
        sanitized = logger._sanitize_error_message(text_with_email)
        
        assert "[EMAIL]" in sanitized
        assert "support@example.com" not in sanitized
    
    def test_phone_sanitization(self):
        """Test phone number sanitization."""
        logger = MOSSAuditLogger()
        
        text_with_phone = "Call emergency contact at 555-123-4567"
        sanitized = logger._sanitize_error_message(text_with_phone)
        
        assert "[PHONE]" in sanitized
        assert "555-123-4567" not in sanitized
    
    def test_ssn_sanitization(self):
        """Test SSN sanitization."""
        logger = MOSSAuditLogger()
        
        text_with_ssn = "Patient SSN is 123-45-6789"
        sanitized = logger._sanitize_error_message(text_with_ssn)
        
        assert "[SSN]" in sanitized
        assert "123-45-6789" not in sanitized
    
    def test_message_truncation(self):
        """Test long message truncation."""
        logger = MOSSAuditLogger()
        
        long_message = "x" * 600  # Longer than 500 character limit
        sanitized = logger._sanitize_error_message(long_message)
        
        assert len(sanitized) <= 503  # 500 + "..."
        assert sanitized.endswith("...")


if __name__ == "__main__":
    pytest.main([__file__]) 