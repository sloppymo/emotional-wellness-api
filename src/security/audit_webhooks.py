"""
Audit Webhook Security Module for Emotional Wellness API

This module provides HIPAA-compliant audit logging for Slack webhook
communications, ensuring all data transmitted is properly tracked and redacted.
"""

import json
from copy import deepcopy
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..structured_logging import get_logger
from ..structured_logging.phi_logger import log_to_hipaa_audit_log
from ..observability import record_span, ComponentName

# Configure logger
logger = get_logger(__name__)


@record_span("security.audit_webhook", ComponentName.SECURITY)
def log_webhook_delivery(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Redact and log all Slack-bound data for HIPAA compliance.
    
    Args:
        payload: The raw payload to audit
    
    Returns:
        Audited payload with sensitive data redacted
    """
    # Make a deep copy to avoid modifying the original
    audited = deepcopy(payload)
    
    # Redact any potentially sensitive data
    redact_keys(audited, [
        "user_id", "patient_id", "ip_address", "email", "phone", 
        "address", "name", "ssn", "dob", "medical_id"
    ])
    
    # Log delivery to HIPAA audit log
    log_to_hipaa_audit_log(
        event_type="EXTERNAL_COMMUNICATION",
        component="slack_webhook",
        action="message_sent",
        status="success",
        metadata={
            "destination_type": "slack",
            "message_type": _determine_message_type(payload),
            "contains_phi": False,  # Should be false after redaction
            "timestamp": datetime.now().isoformat()
        }
    )
    
    logger.info("Webhook delivery audited", 
                extra={"destination": "slack", "redacted": True})
    
    return audited


def redact_keys(obj: Any, keys_to_redact: List[str]) -> None:
    """
    Recursively redact sensitive keys from a dictionary.
    
    Args:
        obj: Object to redact (dict, list, or other)
        keys_to_redact: List of key names to redact
    """
    if isinstance(obj, dict):
        for key in list(obj.keys()):
            if any(k.lower() in key.lower() for k in keys_to_redact):
                obj[key] = "[REDACTED]"
            else:
                redact_keys(obj[key], keys_to_redact)
    elif isinstance(obj, list):
        for item in obj:
            redact_keys(item, keys_to_redact)


def _determine_message_type(payload: Dict[str, Any]) -> str:
    """
    Determine the message type for audit purposes.
    
    Args:
        payload: The Slack message payload
        
    Returns:
        String describing the message type
    """
    if "attachments" in payload:
        return "rich_attachment"
    elif "blocks" in payload and payload.get("blocks"):
        block_types = set()
        for block in payload["blocks"]:
            if isinstance(block, dict) and "type" in block:
                block_types.add(block["type"])
        
        if "header" in block_types:
            return "header_blocks"
        elif "actions" in block_types:
            return "interactive_blocks"
        else:
            return "standard_blocks"
    else:
        return "simple_text"


@record_span("security.audit_timeout_policy", ComponentName.SECURITY)
def apply_message_timeout_policies(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply HIPAA-compliant timeout policies to messages.
    
    Args:
        payload: The message payload to process
        
    Returns:
        Updated payload with timeout metadata
    """
    # Make a deep copy to avoid modifying the original
    processed = deepcopy(payload)
    
    # Determine sensitivity level based on content
    sensitivity = _assess_content_sensitivity(payload)
    
    # Set appropriate timeouts based on sensitivity
    if sensitivity == "high":
        # For clinical alerts, crisis responses
        timeout = 24  # hours
    elif sensitivity == "medium":
        # For general clinical coordination
        timeout = 72  # hours
    else:
        # For system notifications, non-sensitive
        timeout = 168  # hours (7 days)
    
    # Add timeout metadata if blocks exist
    if "blocks" in processed and processed["blocks"] and isinstance(processed["blocks"], list):
        # Add expiration note to context block
        expires_at = datetime.now().timestamp() + (timeout * 3600)
        
        # Look for existing context block to append to
        has_context = False
        for block in processed["blocks"]:
            if isinstance(block, dict) and block.get("type") == "context":
                if "elements" in block and isinstance(block["elements"], list):
                    block["elements"].append({
                        "type": "mrkdwn",
                        "text": f"_Message expires in {timeout} hours_"
                    })
                    has_context = True
                    break
        
        # Add new context block if none exists
        if not has_context:
            processed["blocks"].append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"_Message expires in {timeout} hours_"
                    }
                ]
            })
        
        # Log application of timeout policy
        logger.info(f"Applied message timeout policy", 
                    extra={"timeout_hours": timeout, "sensitivity": sensitivity})
    
    return processed


def _assess_content_sensitivity(payload: Dict[str, Any]) -> str:
    """
    Assess the sensitivity of message content.
    
    Args:
        payload: The message payload
        
    Returns:
        Sensitivity level: 'high', 'medium', or 'low'
    """
    # Look for indicators of sensitivity
    indicators = {
        "high": ["crisis", "emergency", "urgent", "level 3", "immediate", "alert"],
        "medium": ["case", "patient", "client", "therapist", "assign", "consult"]
    }
    
    # Convert payload to string for simple text search
    payload_str = json.dumps(payload).lower()
    
    # Check for high sensitivity indicators
    for term in indicators["high"]:
        if term in payload_str:
            return "high"
    
    # Check for medium sensitivity indicators
    for term in indicators["medium"]:
        if term in payload_str:
            return "medium"
    
    # Default to low sensitivity
    return "low"
