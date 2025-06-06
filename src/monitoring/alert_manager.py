"""
Alert Manager Module

Manages alert evaluation, notification dispatch, and alert state tracking.
Provides HIPAA-compliant alerting for system monitoring.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable
from enum import Enum
import json

from pydantic import BaseModel, Field

from ..structured_logging import get_logger
from .alert_rules import AlertRule, AlertSeverity, AlertRuleSet
from ..config import settings

logger = get_logger(__name__)

class NotificationChannel(str, Enum):
    """Available notification channels for alerts."""
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    WEBHOOK = "webhook"
    PAGERDUTY = "pagerduty"
    CONSOLE = "console"  # For development/testing

class NotificationConfig(BaseModel):
    """Configuration for a notification channel."""
    channel: NotificationChannel
    recipients: List[str] = Field(default_factory=list)
    template: Optional[str] = None
    enabled: bool = True
    min_severity: AlertSeverity = AlertSeverity.WARNING
    
    # Channel-specific configuration
    config: Dict[str, Any] = Field(default_factory=dict)

class AlertState(str, Enum):
    """Possible states for an alert."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SILENCED = "silenced"

class AlertInstance(BaseModel):
    """An instance of a triggered alert."""
    id: str
    rule_id: str
    name: str
    description: str
    severity: AlertSeverity
    state: AlertState = AlertState.ACTIVE
    value: float
    threshold: float
    labels: Dict[str, str] = Field(default_factory=dict)
    first_detected: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    notification_sent: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    silenced_until: Optional[datetime] = None
    
    def acknowledge(self, user: str) -> None:
        """Acknowledge this alert."""
        self.state = AlertState.ACKNOWLEDGED
        self.acknowledged_by = user
        self.acknowledged_at = datetime.utcnow()
        self.last_updated = datetime.utcnow()
    
    def resolve(self) -> None:
        """Mark this alert as resolved."""
        self.state = AlertState.RESOLVED
        self.resolved_at = datetime.utcnow()
        self.last_updated = datetime.utcnow()
    
    def silence(self, duration_minutes: int = 60) -> None:
        """Silence this alert for a specified duration."""
        self.state = AlertState.SILENCED
        self.silenced_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        self.last_updated = datetime.utcnow()
    
    def is_silenced(self) -> bool:
        """Check if this alert is currently silenced."""
        if self.state != AlertState.SILENCED:
            return False
        
        if not self.silenced_until:
            return False
            
        return datetime.utcnow() < self.silenced_until

class AlertHistory(BaseModel):
    """History of an alert over time."""
    rule_id: str
    instances: List[AlertInstance] = Field(default_factory=list)
    
    def add_instance(self, instance: AlertInstance) -> None:
        """Add an alert instance to history."""
        self.instances.append(instance)
        
        # Keep only the last 100 instances to avoid unbounded growth
        if len(self.instances) > 100:
            self.instances = self.instances[-100:]

class AlertManager:
    """
    Manages alert evaluation, notification, and state tracking.
    
    This class is responsible for:
    1. Evaluating alert rules against current metrics
    2. Tracking alert state (active, acknowledged, resolved)
    3. Sending notifications through configured channels
    4. Providing alert history and status information
    """
    
    def __init__(self):
        """Initialize the alert manager."""
        self._logger = get_logger(f"{__name__}.AlertManager")
        self._rule_sets: Dict[str, AlertRuleSet] = {}
        self._active_alerts: Dict[str, AlertInstance] = {}
        self._alert_history: Dict[str, AlertHistory] = {}
        self._notification_configs: List[NotificationConfig] = []
        
        # Register default notification channels
        self._register_default_notification_channels()
        
        # Alert deduplication
        self._recently_notified: Set[str] = set()
        
        # Notification handlers
        self._notification_handlers: Dict[NotificationChannel, Callable] = {
            NotificationChannel.EMAIL: self._send_email_notification,
            NotificationChannel.SMS: self._send_sms_notification,
            NotificationChannel.SLACK: self._send_slack_notification,
            NotificationChannel.WEBHOOK: self._send_webhook_notification,
            NotificationChannel.PAGERDUTY: self._send_pagerduty_notification,
            NotificationChannel.CONSOLE: self._send_console_notification
        }
    
    def register_rule_set(self, rule_set: AlertRuleSet) -> None:
        """Register a set of alert rules."""
        self._rule_sets[rule_set.name] = rule_set
        self._logger.info(f"Registered alert rule set: {rule_set.name} with {len(rule_set.rules)} rules")
    
    def add_notification_config(self, config: NotificationConfig) -> None:
        """Add a notification channel configuration."""
        self._notification_configs.append(config)
        self._logger.info(f"Added notification channel: {config.channel}")
    
    async def evaluate_alerts(self, metrics: Dict[str, float]) -> List[AlertInstance]:
        """
        Evaluate all registered rules against the provided metrics.
        
        Args:
            metrics: Dictionary of metric names to current values
            
        Returns:
            List of triggered alert instances
        """
        triggered_alerts = []
        
        for rule_set_name, rule_set in self._rule_sets.items():
            triggered_rules = rule_set.evaluate_all(metrics)
            
            for rule in triggered_rules:
                # Create alert instance
                alert_id = f"{rule.id}_{int(time.time())}"
                alert = AlertInstance(
                    id=alert_id,
                    rule_id=rule.id,
                    name=rule.name,
                    description=rule.description,
                    severity=rule.severity,
                    value=metrics[rule.metric_name],
                    threshold=rule.threshold,
                    labels=rule.labels
                )
                
                # Store active alert
                self._active_alerts[alert_id] = alert
                
                # Add to history
                if rule.id not in self._alert_history:
                    self._alert_history[rule.id] = AlertHistory(rule_id=rule.id)
                self._alert_history[rule.id].add_instance(alert)
                
                # Add to triggered alerts
                triggered_alerts.append(alert)
        
        # Process notifications for triggered alerts
        await self._process_notifications(triggered_alerts)
        
        return triggered_alerts
    
    async def _process_notifications(self, alerts: List[AlertInstance]) -> None:
        """Process notifications for triggered alerts."""
        for alert in alerts:
            # Skip if already notified
            if alert.notification_sent:
                continue
                
            # Skip if silenced
            if alert.is_silenced():
                continue
            
            # Deduplicate alerts
            dedup_key = f"{alert.rule_id}_{alert.severity}"
            if dedup_key in self._recently_notified:
                continue
                
            # Send notifications
            await self._send_notifications(alert)
            
            # Mark as notified
            alert.notification_sent = True
            
            # Add to recently notified set with expiration
            self._recently_notified.add(dedup_key)
            asyncio.create_task(self._expire_notification_key(dedup_key, 300))  # 5 minutes
    
    async def _expire_notification_key(self, key: str, seconds: int) -> None:
        """Expire a notification deduplication key after a delay."""
        await asyncio.sleep(seconds)
        if key in self._recently_notified:
            self._recently_notified.remove(key)
    
    async def _send_notifications(self, alert: AlertInstance) -> None:
        """Send notifications for an alert through all configured channels."""
        for config in self._notification_configs:
            # Skip if channel is disabled
            if not config.enabled:
                continue
                
            # Skip if alert severity is below channel's minimum severity
            severity_values = {
                AlertSeverity.INFO: 0,
                AlertSeverity.WARNING: 1,
                AlertSeverity.CRITICAL: 2,
                AlertSeverity.EMERGENCY: 3
            }
            
            if severity_values[alert.severity] < severity_values[config.min_severity]:
                continue
            
            # Send notification through appropriate handler
            handler = self._notification_handlers.get(config.channel)
            if handler:
                try:
                    await handler(alert, config)
                except Exception as e:
                    self._logger.error(f"Failed to send {config.channel} notification: {e}")
    
    def acknowledge_alert(self, alert_id: str, user: str) -> bool:
        """
        Acknowledge an active alert.
        
        Args:
            alert_id: ID of the alert to acknowledge
            user: User acknowledging the alert
            
        Returns:
            bool: True if acknowledged successfully
        """
        if alert_id not in self._active_alerts:
            return False
            
        alert = self._active_alerts[alert_id]
        alert.acknowledge(user)
        return True
    
    def resolve_alert(self, alert_id: str) -> bool:
        """
        Resolve an active alert.
        
        Args:
            alert_id: ID of the alert to resolve
            
        Returns:
            bool: True if resolved successfully
        """
        if alert_id not in self._active_alerts:
            return False
            
        alert = self._active_alerts[alert_id]
        alert.resolve()
        
        # Remove from active alerts
        del self._active_alerts[alert_id]
        
        return True
    
    def silence_alert(self, alert_id: str, duration_minutes: int = 60) -> bool:
        """
        Silence an active alert for a specified duration.
        
        Args:
            alert_id: ID of the alert to silence
            duration_minutes: Duration to silence in minutes
            
        Returns:
            bool: True if silenced successfully
        """
        if alert_id not in self._active_alerts:
            return False
            
        alert = self._active_alerts[alert_id]
        alert.silence(duration_minutes)
        return True
    
    def get_active_alerts(self) -> List[AlertInstance]:
        """Get all currently active alerts."""
        return list(self._active_alerts.values())
    
    def get_alert_history(self, rule_id: str) -> Optional[AlertHistory]:
        """Get history for a specific alert rule."""
        return self._alert_history.get(rule_id)
    
    def _register_default_notification_channels(self) -> None:
        """Register default notification channels."""
        # Console notifications (always enabled for logging)
        self.add_notification_config(
            NotificationConfig(
                channel=NotificationChannel.CONSOLE,
                enabled=True,
                min_severity=AlertSeverity.INFO
            )
        )
        
        # Email notifications (if configured)
        if hasattr(settings, "ALERT_EMAIL_RECIPIENTS") and settings.ALERT_EMAIL_RECIPIENTS:
            self.add_notification_config(
                NotificationConfig(
                    channel=NotificationChannel.EMAIL,
                    recipients=settings.ALERT_EMAIL_RECIPIENTS,
                    enabled=True,
                    min_severity=AlertSeverity.WARNING
                )
            )
    
    # Notification channel handlers
    async def _send_email_notification(self, alert: AlertInstance, config: NotificationConfig) -> None:
        """Send email notification."""
        self._logger.info(f"Would send email notification for alert {alert.id} to {config.recipients}")
        # In a real implementation, this would use an email service
    
    async def _send_sms_notification(self, alert: AlertInstance, config: NotificationConfig) -> None:
        """Send SMS notification."""
        self._logger.info(f"Would send SMS notification for alert {alert.id} to {config.recipients}")
        # In a real implementation, this would use an SMS service
    
    async def _send_slack_notification(self, alert: AlertInstance, config: NotificationConfig) -> None:
        """Send Slack notification."""
        self._logger.info(f"Would send Slack notification for alert {alert.id}")
        # In a real implementation, this would use the Slack API
    
    async def _send_webhook_notification(self, alert: AlertInstance, config: NotificationConfig) -> None:
        """Send webhook notification."""
        self._logger.info(f"Would send webhook notification for alert {alert.id}")
        # In a real implementation, this would make an HTTP request
    
    async def _send_pagerduty_notification(self, alert: AlertInstance, config: NotificationConfig) -> None:
        """Send PagerDuty notification."""
        self._logger.info(f"Would send PagerDuty notification for alert {alert.id}")
        # In a real implementation, this would use the PagerDuty API
    
    async def _send_console_notification(self, alert: AlertInstance, config: NotificationConfig) -> None:
        """Send console notification (for development/testing)."""
        self._logger.warning(
            f"ALERT [{alert.severity.upper()}]: {alert.name} - {alert.description} "
            f"(value: {alert.value}, threshold: {alert.threshold})"
        )

# Global instance
_alert_manager: Optional[AlertManager] = None

def get_alert_manager() -> AlertManager:
    """Get the global AlertManager instance."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager

async def evaluate_system_alerts(metrics: Dict[str, float]) -> List[AlertInstance]:
    """
    Evaluate all system alerts against the provided metrics.
    
    Args:
        metrics: Dictionary of metric names to current values
        
    Returns:
        List of triggered alert instances
    """
    alert_manager = get_alert_manager()
    return await alert_manager.evaluate_alerts(metrics)
