"""
Slack Integration Utilities for Emotional Wellness API

This module provides core functionality for sending messages to Slack
via webhooks while maintaining HIPAA compliance through data minimization.
"""

import json
import logging
import os
from copy import deepcopy
from datetime import datetime
from typing import Dict, List, Any, Optional, Literal

import requests

from ..structured_logging import get_logger
from ..observability import record_span, ComponentName

# Configure logger
logger = get_logger(__name__)

# Get webhook URL from environment
DEFAULT_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")


class SlackNotifier:
    """
    Core class for Slack notifications with HIPAA compliance controls.
    Handles webhook communication, audit logging, and message formatting.
    """
    
    def __init__(self, webhook_url: str = None):
        """
        Initialize the Slack notifier.
        
        Args:
            webhook_url: Optional webhook URL override. If not provided, 
                         uses the SLACK_WEBHOOK_URL environment variable.
        """
        self.webhook_url = webhook_url or DEFAULT_WEBHOOK_URL
        self._logger = get_logger(f"{__name__}.SlackNotifier")
    
    @record_span("slack.send_message", ComponentName.NOTIFICATION)
    def send_message(self, blocks: List[Dict[str, Any]], 
                     text: str = None, 
                     channel: str = None,
                     attachments: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send a message to Slack via webhook.
        
        Args:
            blocks: Slack blocks for formatting
            text: Fallback text
            channel: Optional channel override
            attachments: Optional attachments
            
        Returns:
            Response JSON or error dict
        """
        if not self.webhook_url:
            self._logger.warning("No Slack webhook URL configured")
            return {"error": "No webhook URL configured"}
        
        # Prepare payload
        payload = {"blocks": blocks}
        
        if text:
            payload["text"] = text
            
        if channel:
            payload["channel"] = channel
            
        if attachments:
            payload["attachments"] = attachments
        
        # Audit logging (HIPAA)
        audited_payload = self._audit_payload(payload)
        
        try:
            response = requests.post(
                self.webhook_url,
                json=audited_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                self._logger.error(f"Slack webhook error: {response.status_code} - {response.text}")
                return {"error": f"Status code {response.status_code}", "details": response.text}
            
            return response.json()
            
        except Exception as e:
            self._logger.exception(f"Failed to send Slack message: {str(e)}")
            return {"error": str(e)}
    
    def _audit_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Audit and redact payload for HIPAA compliance.
        
        Args:
            payload: The Slack payload to audit
            
        Returns:
            Audited payload with sensitive data redacted
        """
        audited = deepcopy(payload)
        
        # Redact any potentially sensitive keys
        keys_to_redact = ["user_id", "patient_id", "phi", "medical_info", "ip_address"]
        self._redact_keys_recursive(audited, keys_to_redact)
        
        # Log the webhook delivery for audit purposes
        from ..security.audit_log import log_to_hipaa_audit_log
        log_to_hipaa_audit_log(
            event_type="SLACK_WEBHOOK",
            message="Slack webhook message sent",
            metadata={"payload_type": self._get_payload_type(audited)}
        )
        
        return audited
    
    def _redact_keys_recursive(self, obj: Any, keys_to_redact: List[str]) -> None:
        """
        Recursively redact sensitive keys from a dictionary.
        
        Args:
            obj: Object to redact (dict, list, or other)
            keys_to_redact: List of key names to redact
        """
        if isinstance(obj, dict):
            for key in list(obj.keys()):
                if key.lower() in [k.lower() for k in keys_to_redact]:
                    obj[key] = "[REDACTED]"
                else:
                    self._redact_keys_recursive(obj[key], keys_to_redact)
        elif isinstance(obj, list):
            for item in obj:
                self._redact_keys_recursive(item, keys_to_redact)
    
    def _get_payload_type(self, payload: Dict[str, Any]) -> str:
        """Determine the payload type for audit purposes."""
        if "attachments" in payload:
            return "rich_attachment"
        elif "blocks" in payload:
            return "block_kit"
        else:
            return "simple_message"


# Singleton instance for app-wide use
default_notifier = SlackNotifier()
