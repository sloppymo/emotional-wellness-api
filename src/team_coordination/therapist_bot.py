"""
Therapist Coordination Bot for Emotional Wellness API

This module provides Slack-based coordination for therapists and clinical teams,
enabling case assignment, consultation requests, and team collaboration
while maintaining HIPAA compliance.
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import uuid
import json

from ..utils.slack_utils import default_notifier
from ..structured_logging import get_logger
from ..observability import record_span, ComponentName

# Configure logger
logger = get_logger(__name__)


@record_span("team_coordination.assign_case", ComponentName.COORDINATION)
def assign_crisis_case(
    therapist_id: str, 
    case_meta: Dict[str, Any],
    priority: int = 5,
    case_id: str = None
) -> Dict[str, Any]:
    """
    Assign a crisis case to a therapist via Slack.
    
    Args:
        therapist_id: Slack ID of the therapist
        case_meta: De-identified case metadata
        priority: Case priority (1-10)
        case_id: Optional case ID for reference
    
    Returns:
        Response from the Slack webhook
    """
    # Generate case ID if not provided
    if not case_id:
        case_id = f"case-{uuid.uuid4().hex[:8]}"
    
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
    
    # Add fields with case metadata
    fields = []
    
    # Add symbol pattern if available
    if "symbol_sequence" in case_meta:
        fields.append({
            "type": "mrkdwn", 
            "text": f"*Symbol Pattern:*\n{case_meta.get('symbol_sequence')}"
        })
    
    # Add urgency level
    fields.append({
        "type": "mrkdwn", 
        "text": f"*Urgency Level:*\n{priority}/10"
    })
    
    # Add case ID for reference
    fields.append({
        "type": "mrkdwn", 
        "text": f"*Case ID:*\n{case_id}"
    })
    
    # Add other relevant metadata
    for key, value in case_meta.items():
        if key != "symbol_sequence" and key != "urgency":
            fields.append({
                "type": "mrkdwn", 
                "text": f"*{key.replace('_', ' ').title()}:*\n{value}"
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
                "value": f"accept_{case_id}"
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Request Consult"},
                "value": f"consult_{case_id}"
            }
        ]
    })
    
    # Send direct message to therapist
    response = default_notifier.send_message(
        blocks=blocks,
        text=f"New case assignment ({priority}/10 urgency)",
        channel="therapist-assignments"  # In actual implementation with Slack API, use therapist_id
    )
    
    logger.info(f"Case assigned to therapist", 
                extra={"therapist_id": therapist_id, "case_id": case_id})
    
    return response


@record_span("team_coordination.request_consultation", ComponentName.COORDINATION)
def request_consultation(
    requester_id: str,
    case_id: str,
    consultation_type: str,
    details: str = None,
    urgency: int = 3
) -> Dict[str, Any]:
    """
    Request a consultation from the clinical team.
    
    Args:
        requester_id: ID of the requesting therapist
        case_id: ID of the case
        consultation_type: Type of consultation needed
        details: Additional details
        urgency: Urgency level (1-5)
    
    Returns:
        Response from the Slack webhook
    """
    # Determine emoji based on urgency
    urgency_emoji = ["🟢", "🟡", "🟠", "🔴", "⚠️"][min(urgency-1, 4)]
    
    # Create blocks for consultation request
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text", 
                "text": f"{urgency_emoji} Consultation Request"
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Requested by:*\n<@{requester_id}>"},
                {"type": "mrkdwn", "text": f"*Case ID:*\n{case_id}"}
            ]
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Type:*\n{consultation_type}"},
                {"type": "mrkdwn", "text": f"*Urgency:*\n{urgency}/5"}
            ]
        }
    ]
    
    # Add details if provided
    if details:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Details:*\n{details}"
            }
        })
    
    # Add action buttons
    blocks.append({
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "I can help"},
                "style": "primary",
                "value": f"help_consult_{case_id}"
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Unavailable"},
                "value": f"unavail_consult_{case_id}"
            }
        ]
    })
    
    # Send to consultation channel
    response = default_notifier.send_message(
        blocks=blocks,
        text=f"Consultation Request: {consultation_type}",
        channel="clinical-consultations"
    )
    
    logger.info(f"Consultation requested", 
                extra={"requester": requester_id, "case_id": case_id, "type": consultation_type})
    
    return response


@record_span("team_coordination.send_shift_report", ComponentName.COORDINATION)
def send_shift_report(
    shift_data: Dict[str, Any],
    shift_type: str = "day"
) -> Dict[str, Any]:
    """
    Send a shift report summary to the clinical team.
    
    Args:
        shift_data: Shift report data
        shift_type: Type of shift (day/night/weekend)
    
    Returns:
        Response from the Slack webhook
    """
    # Extract key metrics
    new_cases = shift_data.get("new_cases", 0)
    resolved_cases = shift_data.get("resolved_cases", 0)
    escalations = shift_data.get("escalations", 0)
    trend = shift_data.get("trend", "stable")
    
    # Determine trend emoji
    trend_emoji = {
        "improving": "📈",
        "stable": "📊",
        "worsening": "📉"
    }.get(trend, "📊")
    
    # Create blocks for shift report
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text", 
                "text": f"{shift_type.title()} Shift Report"
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*New Cases:*\n{new_cases}"},
                {"type": "mrkdwn", "text": f"*Resolved:*\n{resolved_cases}"}
            ]
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Escalations:*\n{escalations}"},
                {"type": "mrkdwn", "text": f"*Trend:*\n{trend_emoji} {trend.title()}"}
            ]
        }
    ]
    
    # Add notable patterns if available
    if "notable_patterns" in shift_data:
        patterns = shift_data["notable_patterns"]
        if isinstance(patterns, list) and patterns:
            patterns_text = "\n".join([f"• {pattern}" for pattern in patterns[:5]])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Notable Patterns:*\n{patterns_text}"
                }
            })
    
    # Add timestamp
    blocks.append({
        "type": "context",
        "elements": [
            {"type": "mrkdwn", "text": f"Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M')}"}
        ]
    })
    
    # Send to team channel
    response = default_notifier.send_message(
        blocks=blocks,
        text=f"{shift_type.title()} Shift Report",
        channel="clinical-team"
    )
    
    logger.info(f"Shift report sent", 
                extra={"shift_type": shift_type, "new_cases": new_cases})
    
    return response


@record_span("team_coordination.notify_pattern_change", ComponentName.COORDINATION)
def notify_pattern_change(
    pattern: str,
    change: str,
    significance: str,
    recommended_action: str = None
) -> Dict[str, Any]:
    """
    Notify therapists about a meaningful change in symbolic patterns.
    
    Args:
        pattern: The symbolic pattern changing
        change: Description of the change
        significance: Clinical significance
        recommended_action: Optional recommended action
    
    Returns:
        Response from the Slack webhook
    """
    # Create blocks for pattern change notification
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text", 
                "text": "Pattern Change Detected"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{pattern}*"
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Change:*\n{change}"},
                {"type": "mrkdwn", "text": f"*Significance:*\n{significance}"}
            ]
        }
    ]
    
    # Add recommended action if provided
    if recommended_action:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Recommended Action:*\n{recommended_action}"
            }
        })
    
    # Send to therapist channel
    response = default_notifier.send_message(
        blocks=blocks,
        text=f"Pattern Change: {pattern}",
        channel="pattern-insights"
    )
    
    logger.info(f"Pattern change notification sent", 
                extra={"pattern": pattern})
    
    return response
