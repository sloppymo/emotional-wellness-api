"""
Health Metaphors for Emotional Wellness API

This module provides metaphorical visualization of system health metrics,
creating intuitive representations of technical state for non-technical users.
"""

from typing import Dict, Tuple, Any, List, Optional
from datetime import datetime

from ..utils.slack_utils import default_notifier
from ..structured_logging import get_logger

# Configure logger
logger = get_logger(__name__)

# Metaphorical representations of system states
SYSTEM_METAPHORS = {
    "high_cpu": ("Overwhelmed Phoenix", "🔥 System rising from ashes", "danger"),
    "high_memory": ("Memory Labyrinth", "🧠 Pathways filling up", "warning"),
    "high_latency": ("Sloth Journey", "🦥 Moving through molasses", "warning"),
    "low_resources": ("Parched Desert", "🏜️ Resources running dry", "danger"),
    "normal_operation": ("Balanced Garden", "🌱 Flourishing and stable", "good"),
    "burst_traffic": ("Sudden Storm", "⚡ Lightning crowd surge", "warning"),
    "crisis_events": ("Storm Alert", "⛈️ Emotional weather intensifying", "danger"),
    "error_spike": ("Thorny Path", "🌵 Unexpected obstacles rising", "danger"),
    "low_utilization": ("Sleeping Forest", "🌲 Quiet and underused", "warning"),
}

# Color mapping for Slack attachments
COLOR_MAP = {
    "danger": "#FF0000",   # Red
    "warning": "#FFA500",  # Orange/amber
    "info": "#0000FF",     # Blue
    "good": "#36A64F",     # Green
}


def send_metaphorical_alert(metric: str, value: float, additional_info: Dict[str, Any] = None):
    """
    Send a metaphorical system health alert to Slack.
    
    Args:
        metric: The system metric to visualize
        value: The current metric value
        additional_info: Optional additional information to include
    """
    # Default to normal operation if metric not found
    title, desc, severity = SYSTEM_METAPHORS.get(
        metric, 
        ("Unknown Territory", "📍 Wandering in new land", "info")
    )
    
    color = COLOR_MAP.get(severity, "#808080")  # Default to gray if severity not found
    
    # Build attachment
    attachment = {
        "color": color,
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": title}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"{desc}\n*Current Value:* {value}"}
            }
        ]
    }
    
    # Add additional info if provided
    if additional_info:
        fields = []
        for key, val in additional_info.items():
            fields.append({"type": "mrkdwn", "text": f"*{key}:*\n{val}"})
        
        if fields:
            attachment["blocks"].append({
                "type": "section",
                "fields": fields[:10]  # Limit to 10 fields
            })
    
    # Add timestamp
    now = datetime.now().strftime("%H:%M:%S")
    attachment["blocks"].append({
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": f"Observed at {now}"}]
    })
    
    return default_notifier.send_message(
        blocks=[],
        text=f"System Alert: {title}",
        attachments=[attachment]
    )


def send_system_health_summary(metrics: Dict[str, float]):
    """
    Send a comprehensive system health summary with metaphorical representations.
    
    Args:
        metrics: Dictionary of system metrics and their values
    """
    # Determine overall system health
    critical_metrics = ["high_cpu", "high_latency", "crisis_events", "error_spike"]
    warning_metrics = ["high_memory", "low_resources", "burst_traffic"]
    
    # Count issues by severity
    critical_count = sum(1 for m in critical_metrics if m in metrics and metrics[m] > 0.7)
    warning_count = sum(1 for m in warning_metrics if m in metrics and metrics[m] > 0.5)
    
    # Determine overall system metaphor
    if critical_count > 0:
        overall = "System Storm" if critical_count > 1 else "System Challenge"
        emoji = "🌩️" if critical_count > 1 else "⚡"
        color = COLOR_MAP["danger"]
    elif warning_count > 0:
        overall = "System Tension"
        emoji = "🌤️"
        color = COLOR_MAP["warning"]
    else:
        overall = "System Harmony"
        emoji = "☀️"
        color = COLOR_MAP["good"]
    
    # Create blocks for the message
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"{emoji} {overall}"}
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*System Health Summary*\n{critical_count} critical issues, {warning_count} warnings"
            }
        },
        {
            "type": "divider"
        }
    ]
    
    # Add metaphorical representations for each metric
    for metric, value in metrics.items():
        if metric in SYSTEM_METAPHORS:
            title, desc, _ = SYSTEM_METAPHORS[metric]
            blocks.append({
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*{title}*"},
                    {"type": "mrkdwn", "text": f"{desc}\n{int(value * 100)}%"}
                ]
            })
    
    attachment = {
        "color": color,
        "blocks": blocks
    }
    
    return default_notifier.send_message(
        blocks=[],
        text=f"System Health: {overall}",
        attachments=[attachment]
    )
