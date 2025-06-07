"""
Slack Operations for Crisis Management

This module provides Slack integration for crisis management workflows,
enabling coordinated team responses to crisis situations while maintaining
HIPAA compliance through de-identified data.
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from ..utils.slack_utils import default_notifier
from ..structured_logging import get_logger
from ..observability import record_span, ComponentName

# Configure logger
logger = get_logger(__name__)

# Crisis protocol configuration - defines message routing by severity level
CRISIS_PROTOCOLS = {
    1: {
        "channel": "crisis-l1",
        "message": "Low-severity situation detected - Grounding techniques may be helpful",
        "color": "#FFC107",  # Amber
        "emoji": "⚠️"
    },
    2: {
        "channel": "crisis-l2",
        "message": "Moderate-severity situation detected - Safety protocols activated",
        "color": "#FF9800",  # Orange
        "emoji": "🔔"
    },
    3: {
        "channel": "crisis-l3",
        "message": "URGENT: High-severity situation detected - Human intervention required",
        "color": "#F44336",  # Red
        "emoji": "🚨"
    }
}


@record_span("crisis.initiate_protocol", ComponentName.CRISIS)
def initiate_crisis_protocol(
    level: int,
    symbolic_pattern: str = None,
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Initiate a crisis response protocol via Slack.
    
    Args:
        level: Crisis severity level (1-3)
        symbolic_pattern: De-identified symbolic pattern that triggered the crisis detection
        metadata: Additional de-identified metadata about the crisis
    
    Returns:
        Response from the Slack webhook including thread ID for coordination
    """
    if level not in CRISIS_PROTOCOLS:
        logger.error(f"Invalid crisis level: {level}")
        return {"error": "Invalid crisis level"}
    
    protocol = CRISIS_PROTOCOLS[level]
    
    # Ensure we're not including any PHI
    safe_metadata = _sanitize_metadata(metadata or {})
    
    # Build message blocks
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text", 
                "text": f"{protocol['emoji']} Crisis Alert: Level {level}"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": protocol["message"]
            }
        }
    ]
    
    # Add symbolic pattern if provided
    if symbolic_pattern:
        blocks.append({
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Symbolic Pattern:*\n{symbolic_pattern}"
                }
            ]
        })
    
    # Add metadata fields
    if safe_metadata:
        fields = []
        for key, value in safe_metadata.items():
            fields.append({
                "type": "mrkdwn",
                "text": f"*{key}:*\n{value}"
            })
        
        if fields:
            blocks.append({
                "type": "section",
                "fields": fields[:10]  # Limit to 10 fields
            })
    
    # Add action buttons
    blocks.append({
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "I'm on it"},
                "style": "primary",
                "value": f"acknowledge_crisis_{level}"
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Need backup"},
                "value": f"escalate_crisis_{level}"
            }
        ]
    })
    
    # Add timestamp
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"Crisis detected at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
        ]
    })
    
    # Send the message
    response = default_notifier.send_message(
        blocks=blocks,
        text=f"Crisis Alert: Level {level}",
        channel=protocol["channel"],
        attachments=[{"color": protocol["color"]}]
    )
    
    # Log the notification for audit purposes
    logger.info(f"Crisis protocol level {level} initiated", 
                extra={"crisis_level": level, "channel": protocol["channel"]})
    
    return response


@record_span("crisis.update_thread", ComponentName.CRISIS)
def update_crisis_thread(
    thread_ts: str,
    channel: str,
    update_text: str,
    status: str = None
) -> Dict[str, Any]:
    """
    Update a crisis thread with new information.
    
    Args:
        thread_ts: Thread timestamp to update
        channel: Channel of the thread
        update_text: Update text to add
        status: New status of the crisis response
    
    Returns:
        Response from the Slack webhook
    """
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": update_text
            }
        }
    ]
    
    if status:
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Status: {status}"
                }
            ]
        })
    
    # In a complete implementation, we'd use the Slack Web API with thread_ts
    # For webhook-only implementation, we'll create a new message in the thread
    # Note: This is a limitation of incoming webhooks - for proper threading,
    # you'd need to use the Slack Web API with a bot token
    
    return {"message": "Webhook-only implementation doesn't support threading"}


@record_span("crisis.assign_case", ComponentName.CRISIS)
def assign_crisis_case(
    therapist_id: str,
    case_meta: Dict[str, Any],
    case_id: str = None
) -> Dict[str, Any]:
    """
    Assign a crisis case to a therapist via Slack.
    
    Args:
        therapist_id: Slack ID of the therapist
        case_meta: De-identified case metadata
        case_id: Optional case ID for reference
    
    Returns:
        Response from the Slack webhook
    """
    # Ensure we're not including any PHI
    safe_meta = _sanitize_metadata(case_meta)
    
    # Create blocks for therapist notification
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn", 
                "text": f"*New Case Assignment for <@{therapist_id}>*"
            }
        },
        {
            "type": "divider"
        }
    ]
    
    # Add case metadata fields
    fields = []
    
    # Add case ID if provided
    if case_id:
        fields.append({
            "type": "mrkdwn", 
            "text": f"*Case ID:*\n{case_id}"
        })
    
    # Add symbol patterns if available
    if "symbol_sequence" in safe_meta:
        fields.append({
            "type": "mrkdwn", 
            "text": f"*Symbol Pattern:*\n{safe_meta.get('symbol_sequence')}"
        })
        # Remove from meta to avoid duplication
        del safe_meta["symbol_sequence"]
    
    # Add urgency if available
    if "urgency" in safe_meta:
        fields.append({
            "type": "mrkdwn", 
            "text": f"*Urgency Level:*\n{safe_meta.get('urgency')}/10"
        })
        # Remove from meta to avoid duplication
        del safe_meta["urgency"]
        
    # Add remaining metadata
    for key, value in safe_meta.items():
        fields.append({
            "type": "mrkdwn", 
            "text": f"*{key}:*\n{value}"
        })
    
    # Add fields to blocks (in groups of 2 for better layout)
    for i in range(0, len(fields), 2):
        blocks.append({
            "type": "section",
            "fields": fields[i:i+2]
        })
    
    # Add action buttons
    blocks.append({
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Accept"},
                "style": "primary",
                "value": f"accept_case_{case_id or 'new'}"
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Request Consult"},
                "value": f"consult_case_{case_id or 'new'}"
            }
        ]
    })
    
    # Send direct message to therapist
    # Note: For webhook implementation limitations, we're using a channel
    # In a complete implementation with Slack API, use conversations.open
    # to create a direct message
    response = default_notifier.send_message(
        blocks=blocks,
        text="New case assignment",
        # In real implementation with Slack API: "channel": therapist_id
        channel="crisis-assignments"
    )
    
    logger.info(f"Crisis case assigned", extra={"therapist": therapist_id, "case_id": case_id})
    
    return response


def _sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize metadata to ensure HIPAA compliance by removing PHI.
    
    Args:
        metadata: Original metadata dictionary
    
    Returns:
        Sanitized metadata
    """
    # Keywords that might indicate PHI
    phi_keywords = [
        "name", "patient", "client", "ssn", "social", "address", "phone",
        "email", "dob", "birth", "age", "zip", "location", "ip_address",
        "medical_record", "record_id"
    ]
    
    # Create a new dict with sanitized data
    sanitized = {}
    
    for key, value in metadata.items():
        # Skip any keys that might contain PHI
        if any(phi_term in key.lower() for phi_term in phi_keywords):
            continue
            
        # Sanitize string values that might contain names or identifiers
        if isinstance(value, str):
            # If the value is too long or looks like it might be free text
            # containing PHI, skip it or redact it
            if len(value) > 100 or " " in value:
                # Simple redaction for demonstration - in production,
                # use a more sophisticated PHI detection algorithm
                sanitized[key] = "[Redacted]"
            else:
                sanitized[key] = value
        else:
            # Non-string values are likely safe to include
            sanitized[key] = value
            
    return sanitized
