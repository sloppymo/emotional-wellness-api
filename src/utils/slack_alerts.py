"""
Slack Alerts for Emotional Wellness API

This module provides specialized alert functions for sending notifications
via Slack about symbolic emotional states and system events.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional, Literal

from pydantic import BaseModel

from .slack_utils import default_notifier
from ..structured_logging import get_logger

# Configure logger
logger = get_logger(__name__)


class SymbolicAlert(BaseModel):
    """Model for symbolic emotional state alerts."""
    archetype: str  # e.g., "Hero's Journey"
    symbol_pattern: str  # e.g., "Water→Fire→Mountain"
    valence_trend: Literal["rising", "falling", "stable"]
    timestamp: datetime


def send_symbolic_alert(alert: SymbolicAlert):
    """
    Send an alert about symbolic emotional patterns.
    
    Args:
        alert: The symbolic alert to send
    """
    blocks = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*{alert.archetype} Pattern Detected*"}
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Symbol Sequence:*\n{alert.symbol_pattern}"},
                {"type": "mrkdwn", "text": f"*Emotional Trend:*\n{alert.valence_trend}"}
            ]
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"Detected at {alert.timestamp.strftime('%H:%M')}"}]
        }
    ]
    
    return default_notifier.send_message(
        blocks=blocks,
        text=f"{alert.archetype} Pattern: {alert.symbol_pattern} ({alert.valence_trend})"
    )


def send_test_results_notification(
    test_results: Dict[str, Any], 
    test_type: str = "Unit Tests"
):
    """
    Send notification about test results.
    
    Args:
        test_results: Dictionary of test results
        test_type: Type of tests run
    """
    success = test_results.get("success", False)
    total = test_results.get("total", 0)
    passed = test_results.get("passed", 0)
    failed = test_results.get("failed", 0)
    
    color = "#36a64f" if success else "#ff0000"
    status = "✅ Passed" if success else "❌ Failed"
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"Test Results: {status}"
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Type:*\n{test_type}"},
                {"type": "mrkdwn", "text": f"*Total:*\n{total}"}
            ]
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Passed:*\n{passed}"},
                {"type": "mrkdwn", "text": f"*Failed:*\n{failed}"}
            ]
        }
    ]
    
    # Add details about failures if any
    failures = test_results.get("failures", [])
    if failures:
        failure_details = "\n".join([f"• {failure}" for failure in failures[:5]])
        if len(failures) > 5:
            failure_details += f"\n• ...and {len(failures) - 5} more"
            
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Failures:*\n{failure_details}"
            }
        })
    
    attachment = [{
        "color": color,
        "blocks": blocks
    }]
    
    return default_notifier.send_message(
        blocks=[],
        text=f"Test Results: {status}",
        attachments=attachment
    )


def send_deployment_notification(
    environment: str,
    status: str,
    version: str,
    changes: List[str] = None,
    triggered_by: str = "CI/CD"
):
    """
    Send notification about a deployment.
    
    Args:
        environment: The environment deployed to
        status: Status of the deployment
        version: Version deployed
        changes: List of changes in this deployment
        triggered_by: Who or what triggered this deployment
    """
    success = status.lower() in ["success", "successful", "completed"]
    color = "#36a64f" if success else "#ff0000"
    status_emoji = "✅" if success else "❌"
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"Deployment to {environment}"
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Status:*\n{status_emoji} {status}"},
                {"type": "mrkdwn", "text": f"*Version:*\n{version}"}
            ]
        },
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": f"Triggered by: {triggered_by}"}
            ]
        }
    ]
    
    # Add changes if provided
    if changes:
        change_text = "\n".join([f"• {change}" for change in changes[:5]])
        if len(changes) > 5:
            change_text += f"\n• ...and {len(changes) - 5} more"
            
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Changes:*\n{change_text}"
            }
        })
    
    attachment = [{
        "color": color,
        "blocks": blocks
    }]
    
    return default_notifier.send_message(
        blocks=[],
        text=f"Deployment to {environment}: {status}",
        attachments=attachment
    )
