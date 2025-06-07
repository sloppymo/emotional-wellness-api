"""
Security and compliance tests for the CANOPY symbolic processing system.

Tests cover:
1. HIPAA compliance
2. Data privacy
3. Access control
4. Input validation
5. Secure communication
6. Audit logging
"""

import pytest
import json
import re
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import logging

from src.symbolic.canopy import CanopyProcessor
from src.models.emotional_state import SymbolicMapping, EmotionalMetaphor
from src.utils.hipaa import HIPAACompliance

# Security test constants
PHI_PATTERNS = [
    r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b',  # SSN
    r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
    r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',  # Dates
    r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'  # Names
]

@pytest.fixture
def security_setup():
    """Set up the system for security testing"""
    processor = CanopyProcessor(api_key="test_key")
    return processor

@pytest.fixture
def mock_audit_logger():
    """Create a mock audit logger"""
    logger = logging.getLogger("audit")
    logger.setLevel(logging.INFO)
    return logger

# HIPAA Compliance Tests
@pytest.mark.asyncio
async def test_phi_detection(security_setup):
    """Test detection and handling of PHI"""
    processor = security_setup
    
    # Test with PHI in input
    test_inputs = [
        "My SSN is 123-45-6789",
        "Call me at 555-123-4567",
        "Email me at john.doe@example.com",
        "My birthday is 01/01/1990",
        "I spoke with Dr. John Smith"
    ]
    
    for input_text in test_inputs:
        result = await processor.process(
            text=input_text,
            user_id="test_user",
            context={"session_id": "test_session"}
        )
        
        # Verify PHI is not in output
        assert not any(re.search(pattern, str(result)) for pattern in PHI_PATTERNS)
        assert not any(re.search(pattern, result.metaphors[0].text) for pattern in PHI_PATTERNS)

@pytest.mark.asyncio
async def test_hipaa_logging(security_setup, mock_audit_logger):
    """Test HIPAA-compliant logging"""
    processor = security_setup
    
    with patch("logging.getLogger", return_value=mock_audit_logger) as mock_logger:
        # Process with potential PHI
        await processor.process(
            text="I feel anxious about my appointment with Dr. Smith",
            user_id="test_user",
            context={"session_id": "test_session"}
        )
        
        # Verify logging
        log_calls = mock_logger.return_value.info.call_args_list
        assert any("PHI detected" in str(call) for call in log_calls)
        assert any("HIPAA compliance" in str(call) for call in log_calls)

# Data Privacy Tests
@pytest.mark.asyncio
async def test_data_encryption(security_setup):
    """Test data encryption and privacy"""
    processor = security_setup
    
    # Test sensitive data handling
    result = await processor.process(
        text="I'm feeling very depressed about my recent diagnosis",
        user_id="test_user",
        context={"session_id": "test_session"}
    )
    
    # Verify data is properly encrypted/stripped
    assert not any(phi in str(result) for phi in ["diagnosis", "depressed"])
    assert result.metaphors[0].text != "feeling very depressed about my recent diagnosis"

@pytest.mark.asyncio
async def test_data_retention(security_setup):
    """Test data retention policies"""
    processor = security_setup
    
    # Add old data
    old_timestamp = datetime.now() - timedelta(days=31)
    processor._symbolic_history["test_user"] = [
        SymbolicMapping(
            primary_symbol="test",
            archetype="self",
            alternative_symbols=[],
            valence=0.0,
            arousal=0.0,
            metaphors=[],
            confidence=1.0,
            timestamp=old_timestamp
        )
    ]
    
    # Force cleanup
    processor._cleanup_old_states()
    
    # Verify old data is removed
    assert "test_user" not in processor._symbolic_history

# Access Control Tests
@pytest.mark.asyncio
async def test_access_control(security_setup):
    """Test access control mechanisms"""
    processor = security_setup
    
    # Test unauthorized access
    with pytest.raises(Exception):
        await processor.process(
            text="test",
            user_id="unauthorized_user",
            context={"session_id": "test_session"}
        )
    
    # Test invalid API key
    with pytest.raises(Exception):
        processor = CanopyProcessor(api_key="invalid_key")
        await processor.process(
            text="test",
            user_id="test_user",
            context={"session_id": "test_session"}
        )

@pytest.mark.asyncio
async def test_session_management(security_setup):
    """Test session management and security"""
    processor = security_setup
    
    # Test session expiration
    old_session = {
        "session_id": "old_session",
        "timestamp": datetime.now() - timedelta(hours=2)
    }
    
    with pytest.raises(Exception):
        await processor.process(
            text="test",
            user_id="test_user",
            context=old_session
        )

# Input Validation Tests
@pytest.mark.asyncio
async def test_input_validation(security_setup):
    """Test input validation and sanitization"""
    processor = security_setup
    
    # Test malicious input
    malicious_inputs = [
        "<script>alert('xss')</script>",
        "'; DROP TABLE users; --",
        "../../../etc/passwd",
        "eval('malicious_code')"
    ]
    
    for input_text in malicious_inputs:
        result = await processor.process(
            text=input_text,
            user_id="test_user",
            context={"session_id": "test_session"}
        )
        
        # Verify input is sanitized
        assert "<script>" not in str(result)
        assert "DROP TABLE" not in str(result)
        assert "../../../" not in str(result)
        assert "eval(" not in str(result)

# Secure Communication Tests
@pytest.mark.asyncio
async def test_secure_communication(security_setup):
    """Test secure communication channels"""
    processor = security_setup
    
    # Test API communication
    with patch("src.symbolic.canopy.processor.requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"success": True}
        
        result = await processor.process(
            text="test",
            user_id="test_user",
            context={"session_id": "test_session"}
        )
        
        # Verify secure communication
        assert mock_post.call_args[1]["verify"] is True  # SSL verification
        assert "https://" in mock_post.call_args[0][0]  # HTTPS protocol

# Audit Logging Tests
@pytest.mark.asyncio
async def test_audit_logging(security_setup, mock_audit_logger):
    """Test audit logging functionality"""
    processor = security_setup
    
    with patch("logging.getLogger", return_value=mock_audit_logger) as mock_logger:
        # Perform various operations
        await processor.process(
            text="test",
            user_id="test_user",
            context={"session_id": "test_session"}
        )
        
        # Verify audit logging
        log_calls = mock_logger.return_value.info.call_args_list
        assert any("User access" in str(call) for call in log_calls)
        assert any("Processing request" in str(call) for call in log_calls)
        assert any("Operation complete" in str(call) for call in log_calls)

@pytest.mark.asyncio
async def test_compliance_checks(security_setup):
    """Test compliance checking mechanisms"""
    processor = security_setup
    
    # Test HIPAA compliance
    assert HIPAACompliance.check_processor(processor)
    
    # Test data handling compliance
    result = await processor.process(
        text="I'm feeling anxious about my medical condition",
        user_id="test_user",
        context={"session_id": "test_session"}
    )
    
    assert HIPAACompliance.check_output(result)
    assert HIPAACompliance.check_storage(processor._symbolic_history)
    assert HIPAACompliance.check_transmission(result) 