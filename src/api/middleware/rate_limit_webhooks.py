from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import asyncio
import httpx
import smtplib
import json
import hashlib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from redis.asyncio import Redis
from prometheus_client import Counter, Histogram
import jinja2

# Prometheus metrics
webhook_requests = Counter(
    'rate_limit_webhook_requests_total',
    'Total webhook requests sent',
    ['webhook_type', 'status']
)
webhook_latency = Histogram(
    'rate_limit_webhook_latency_seconds',
    'Webhook request latency',
    ['webhook_type']
)
alert_triggers = Counter(
    'rate_limit_alert_triggers_total',
    'Total alert triggers',
    ['alert_type', 'severity']
)

class AlertSeverity(Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class WebhookType(Enum):
    """Types of webhooks."""
    SLACK = "slack"
    DISCORD = "discord"
    TEAMS = "teams"
    PAGERDUTY = "pagerduty"
    CUSTOM = "custom"

class AlertType(Enum):
    """Types of alerts."""
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    CIRCUIT_BREAKER_TRIPPED = "circuit_breaker_tripped"
    ANOMALY_DETECTED = "anomaly_detected"
    QUOTA_EXCEEDED = "quota_exceeded"
    GEOGRAPHIC_VIOLATION = "geographic_violation"
    COMPLIANCE_VIOLATION = "compliance_violation"
    SYSTEM_ERROR = "system_error"

@dataclass
class AlertEvent:
    """Alert event data structure."""
    id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    description: str
    client_id: str
    endpoint: str
    category: str
    timestamp: datetime
    metadata: Dict[str, Any]
    fingerprint: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat(),
            'alert_type': self.alert_type.value,
            'severity': self.severity.value
        }

@dataclass
class WebhookConfig:
    """Webhook configuration."""
    name: str
    webhook_type: WebhookType
    url: str
    enabled: bool = True
    retry_count: int = 3
    timeout: int = 30
    headers: Dict[str, str] = None
    template: str = None
    filters: Dict[str, Any] = None
    rate_limit: Optional[int] = None  # max requests per minute
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}
        if self.filters is None:
            self.filters = {}

@dataclass
class EscalationPolicy:
    """Alert escalation policy."""
    name: str
    rules: List[Dict[str, Any]]
    cooldown_minutes: int = 60
    max_escalations: int = 3
    
class RateLimitWebhooks:
    """Webhooks and alerting system for rate limiting events."""
    
    def __init__(
        self,
        redis_client: Redis,
        smtp_host: Optional[str] = None,
        smtp_port: int = 587,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        default_from_email: Optional[str] = None
    ):
        self.redis = redis_client
        self.logger = logging.getLogger(__name__)
        
        # Email configuration
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.default_from_email = default_from_email
        
        # Redis keys
        self.webhooks_key = "rate_limit:webhooks"
        self.alerts_key = "rate_limit:alerts"
        self.escalations_key = "rate_limit:escalations"
        self.alert_history_key = "rate_limit:alert_history:{}"
        self.webhook_queue_key = "rate_limit:webhook_queue"
        
        # Template engine
        self.jinja_env = jinja2.Environment(
            loader=jinja2.DictLoader(self._get_default_templates())
        )
        
        # HTTP client
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Alert deduplication
        self.alert_fingerprints = {}
        self.dedup_window = 300  # 5 minutes
        
        # Initialize default configs
        asyncio.create_task(self._initialize_defaults())
    
    def _get_default_templates(self) -> Dict[str, str]:
        """Get default notification templates."""
        return {
            "slack": """
{
    "text": "Rate Limit Alert: {{ alert.title }}",
    "attachments": [
        {
            "color": "{% if alert.severity.value == 'critical' %}danger{% elif alert.severity.value == 'high' %}warning{% else %}good{% endif %}",
            "fields": [
                {
                    "title": "Severity",
                    "value": "{{ alert.severity.value.upper() }}",
                    "short": true
                },
                {
                    "title": "Client",
                    "value": "{{ alert.client_id }}",
                    "short": true
                },
                {
                    "title": "Endpoint",
                    "value": "{{ alert.endpoint }}",
                    "short": true
                },
                {
                    "title": "Category",
                    "value": "{{ alert.category }}",
                    "short": true
                },
                {
                    "title": "Description",
                    "value": "{{ alert.description }}",
                    "short": false
                },
                {
                    "title": "Timestamp",
                    "value": "{{ alert.timestamp }}",
                    "short": true
                }
            ]
        }
    ]
}
            """,
            "discord": """
{
    "content": "🚨 **Rate Limit Alert**",
    "embeds": [
        {
            "title": "{{ alert.title }}",
            "description": "{{ alert.description }}",
            "color": {% if alert.severity.value == 'critical' %}16711680{% elif alert.severity.value == 'high' %}16776960{% else %}65280{% endif %},
            "fields": [
                {
                    "name": "Severity",
                    "value": "{{ alert.severity.value.upper() }}",
                    "inline": true
                },
                {
                    "name": "Client",
                    "value": "{{ alert.client_id }}",
                    "inline": true
                },
                {
                    "name": "Endpoint",
                    "value": "{{ alert.endpoint }}",
                    "inline": true
                }
            ],
            "timestamp": "{{ alert.timestamp }}"
        }
    ]
}
            """,
            "email": """
Subject: Rate Limit Alert - {{ alert.title }}

<html>
<body>
    <h2>Rate Limit Alert</h2>
    <h3>{{ alert.title }}</h3>
    
    <table border="1" cellpadding="5">
        <tr><td><strong>Severity</strong></td><td>{{ alert.severity.value.upper() }}</td></tr>
        <tr><td><strong>Client ID</strong></td><td>{{ alert.client_id }}</td></tr>
        <tr><td><strong>Endpoint</strong></td><td>{{ alert.endpoint }}</td></tr>
        <tr><td><strong>Category</strong></td><td>{{ alert.category }}</td></tr>
        <tr><td><strong>Timestamp</strong></td><td>{{ alert.timestamp }}</td></tr>
    </table>
    
    <h4>Description</h4>
    <p>{{ alert.description }}</p>
    
    <h4>Metadata</h4>
    <pre>{{ alert.metadata | tojson(indent=2) }}</pre>
</body>
</html>
            """,
            "pagerduty": """
{
    "routing_key": "{{ routing_key }}",
    "event_action": "trigger",
    "payload": {
        "summary": "{{ alert.title }}",
        "source": "rate-limiter",
        "severity": "{{ alert.severity.value }}",
        "component": "rate-limiting",
        "group": "{{ alert.category }}",
        "class": "{{ alert.alert_type.value }}",
        "custom_details": {
            "client_id": "{{ alert.client_id }}",
            "endpoint": "{{ alert.endpoint }}",
            "description": "{{ alert.description }}",
            "metadata": {{ alert.metadata | tojson }}
        }
    },
    "dedup_key": "{{ alert.fingerprint }}"
}
            """
        }
    
    async def _initialize_defaults(self):
        """Initialize default webhook and escalation configurations."""
        # Check if configurations exist
        if not await self.redis.exists(self.webhooks_key):
            await self.redis.set(self.webhooks_key, json.dumps({}))
        
        if not await self.redis.exists(self.escalations_key):
            default_escalation = EscalationPolicy(
                name="default",
                rules=[
                    {
                        "severity": ["medium", "high", "critical"],
                        "delay_minutes": 0,
                        "webhooks": ["default_slack"]
                    },
                    {
                        "severity": ["high", "critical"],
                        "delay_minutes": 15,
                        "webhooks": ["pagerduty"]
                    },
                    {
                        "severity": ["critical"],
                        "delay_minutes": 30,
                        "webhooks": ["email_admin"]
                    }
                ]
            )
            await self.redis.set(
                self.escalations_key,
                json.dumps({default_escalation.name: asdict(default_escalation)})
            )
    
    async def add_webhook(self, config: WebhookConfig) -> bool:
        """Add a new webhook configuration."""
        try:
            webhooks_data = await self.redis.get(self.webhooks_key)
            webhooks = json.loads(webhooks_data) if webhooks_data else {}
            
            webhooks[config.name] = asdict(config)
            await self.redis.set(self.webhooks_key, json.dumps(webhooks))
            
            self.logger.info(f"Added webhook configuration: {config.name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add webhook {config.name}: {e}")
            return False
    
    async def remove_webhook(self, name: str) -> bool:
        """Remove a webhook configuration."""
        try:
            webhooks_data = await self.redis.get(self.webhooks_key)
            webhooks = json.loads(webhooks_data) if webhooks_data else {}
            
            if name in webhooks:
                del webhooks[name]
                await self.redis.set(self.webhooks_key, json.dumps(webhooks))
                self.logger.info(f"Removed webhook configuration: {name}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to remove webhook {name}: {e}")
            return False
    
    async def create_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        description: str,
        client_id: str,
        endpoint: str,
        category: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AlertEvent:
        """Create a new alert event."""
        if metadata is None:
            metadata = {}
        
        # Generate alert ID and fingerprint
        alert_id = f"{alert_type.value}_{client_id}_{endpoint}_{int(datetime.now().timestamp())}"
        fingerprint_data = f"{alert_type.value}_{client_id}_{endpoint}_{title}"
        fingerprint = hashlib.md5(fingerprint_data.encode()).hexdigest()
        
        alert = AlertEvent(
            id=alert_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
            client_id=client_id,
            endpoint=endpoint,
            category=category,
            timestamp=datetime.now(),
            metadata=metadata,
            fingerprint=fingerprint
        )
        
        # Check for deduplication
        if await self._should_deduplicate(alert):
            self.logger.debug(f"Alert deduplicated: {alert.fingerprint}")
            return alert
        
        # Store alert
        await self._store_alert(alert)
        
        # Trigger notifications
        await self._trigger_notifications(alert)
        
        # Update metrics
        alert_triggers.labels(
            alert_type=alert_type.value,
            severity=severity.value
        ).inc()
        
        return alert
    
    async def _should_deduplicate(self, alert: AlertEvent) -> bool:
        """Check if alert should be deduplicated."""
        fingerprint_key = f"alert_fingerprint:{alert.fingerprint}"
        last_alert = await self.redis.get(fingerprint_key)
        
        if last_alert:
            last_timestamp = datetime.fromisoformat(last_alert)
            if (alert.timestamp - last_timestamp).total_seconds() < self.dedup_window:
                return True
        
        # Store new fingerprint
        await self.redis.setex(
            fingerprint_key,
            self.dedup_window,
            alert.timestamp.isoformat()
        )
        return False
    
    async def _store_alert(self, alert: AlertEvent):
        """Store alert in Redis."""
        # Store in alert history
        history_key = self.alert_history_key.format(alert.client_id)
        await self.redis.lpush(history_key, json.dumps(alert.to_dict()))
        await self.redis.ltrim(history_key, 0, 999)  # Keep last 1000 alerts
        await self.redis.expire(history_key, 86400 * 30)  # 30 days
        
        # Store in global alerts
        await self.redis.lpush(self.alerts_key, json.dumps(alert.to_dict()))
        await self.redis.ltrim(self.alerts_key, 0, 9999)  # Keep last 10000 alerts
    
    async def _trigger_notifications(self, alert: AlertEvent):
        """Trigger notifications based on escalation policies."""
        escalations_data = await self.redis.get(self.escalations_key)
        if not escalations_data:
            return
        
        escalations = json.loads(escalations_data)
        
        for policy_name, policy_data in escalations.items():
            policy = EscalationPolicy(**policy_data)
            await self._process_escalation_policy(alert, policy)
    
    async def _process_escalation_policy(self, alert: AlertEvent, policy: EscalationPolicy):
        """Process an escalation policy for an alert."""
        for rule in policy.rules:
            if alert.severity.value in rule.get("severity", []):
                delay_minutes = rule.get("delay_minutes", 0)
                webhooks = rule.get("webhooks", [])
                
                if delay_minutes > 0:
                    # Schedule delayed notification
                    await self._schedule_delayed_notification(
                        alert,
                        webhooks,
                        delay_minutes
                    )
                else:
                    # Send immediate notification
                    await self._send_notifications(alert, webhooks)
    
    async def _schedule_delayed_notification(
        self,
        alert: AlertEvent,
        webhooks: List[str],
        delay_minutes: int
    ):
        """Schedule a delayed notification."""
        # Add to webhook queue with delay
        notification_data = {
            "alert": alert.to_dict(),
            "webhooks": webhooks,
            "scheduled_time": (datetime.now() + timedelta(minutes=delay_minutes)).isoformat()
        }
        
        await self.redis.lpush(
            self.webhook_queue_key,
            json.dumps(notification_data)
        )
    
    async def _send_notifications(self, alert: AlertEvent, webhook_names: List[str]):
        """Send notifications to specified webhooks."""
        webhooks_data = await self.redis.get(self.webhooks_key)
        if not webhooks_data:
            return
        
        webhooks = json.loads(webhooks_data)
        
        for webhook_name in webhook_names:
            if webhook_name in webhooks:
                webhook_config = WebhookConfig(**webhooks[webhook_name])
                if webhook_config.enabled:
                    await self._send_webhook_notification(alert, webhook_config)
    
    async def _send_webhook_notification(self, alert: AlertEvent, config: WebhookConfig):
        """Send a single webhook notification."""
        try:
            # Check rate limiting
            if config.rate_limit:
                rate_key = f"webhook_rate:{config.name}"
                current_count = await self.redis.incr(rate_key)
                if current_count == 1:
                    await self.redis.expire(rate_key, 60)
                elif current_count > config.rate_limit:
                    self.logger.warning(f"Webhook {config.name} rate limited")
                    return
            
            # Apply filters
            if not self._passes_filters(alert, config.filters):
                return
            
            # Render template
            template_name = config.webhook_type.value
            if config.template:
                template_name = config.template
            
            template = self.jinja_env.get_template(template_name)
            payload = template.render(alert=alert, **config.headers)
            
            # Send webhook
            start_time = datetime.now()
            
            if config.webhook_type == WebhookType.PAGERDUTY:
                await self._send_pagerduty_webhook(alert, config, payload)
            elif config.webhook_type in [WebhookType.SLACK, WebhookType.DISCORD, WebhookType.TEAMS, WebhookType.CUSTOM]:
                await self._send_http_webhook(config, payload)
            
            # Record metrics
            duration = (datetime.now() - start_time).total_seconds()
            webhook_latency.labels(webhook_type=config.webhook_type.value).observe(duration)
            webhook_requests.labels(
                webhook_type=config.webhook_type.value,
                status="success"
            ).inc()
            
        except Exception as e:
            self.logger.error(f"Failed to send webhook {config.name}: {e}")
            webhook_requests.labels(
                webhook_type=config.webhook_type.value,
                status="error"
            ).inc()
            
            # Retry logic
            if config.retry_count > 0:
                await self._retry_webhook(alert, config, config.retry_count - 1)
    
    async def _send_http_webhook(self, config: WebhookConfig, payload: str):
        """Send HTTP webhook."""
        headers = {
            "Content-Type": "application/json",
            **config.headers
        }
        
        response = await self.http_client.post(
            config.url,
            content=payload,
            headers=headers,
            timeout=config.timeout
        )
        response.raise_for_status()
    
    async def _send_pagerduty_webhook(self, alert: AlertEvent, config: WebhookConfig, payload: str):
        """Send PagerDuty webhook."""
        headers = {
            "Content-Type": "application/json",
            **config.headers
        }
        
        response = await self.http_client.post(
            "https://events.pagerduty.com/v2/enqueue",
            content=payload,
            headers=headers,
            timeout=config.timeout
        )
        response.raise_for_status()
    
    async def _retry_webhook(self, alert: AlertEvent, config: WebhookConfig, retries_left: int):
        """Retry webhook with exponential backoff."""
        if retries_left <= 0:
            return
        
        delay = 2 ** (config.retry_count - retries_left)
        await asyncio.sleep(delay)
        
        retry_config = WebhookConfig(
            **{**asdict(config), "retry_count": retries_left}
        )
        await self._send_webhook_notification(alert, retry_config)
    
    def _passes_filters(self, alert: AlertEvent, filters: Dict[str, Any]) -> bool:
        """Check if alert passes webhook filters."""
        if not filters:
            return True
        
        for filter_key, filter_value in filters.items():
            if filter_key == "severity":
                if alert.severity.value not in filter_value:
                    return False
            elif filter_key == "alert_type":
                if alert.alert_type.value not in filter_value:
                    return False
            elif filter_key == "category":
                if alert.category not in filter_value:
                    return False
            elif filter_key == "client_pattern":
                import re
                if not re.match(filter_value, alert.client_id):
                    return False
        
        return True
    
    async def send_email_alert(
        self,
        alert: AlertEvent,
        to_emails: List[str],
        subject_template: Optional[str] = None,
        body_template: Optional[str] = None
    ):
        """Send email alert."""
        if not self.smtp_host:
            self.logger.warning("SMTP not configured, cannot send email alerts")
            return
        
        try:
            # Render templates
            if not subject_template:
                subject_template = "Rate Limit Alert - {{ alert.title }}"
            if not body_template:
                body_template = self.jinja_env.get_template("email").render(alert=alert)
            
            subject = jinja2.Template(subject_template).render(alert=alert)
            
            # Create message
            msg = MimeMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.default_from_email
            msg["To"] = ", ".join(to_emails)
            
            # Add HTML part
            html_part = MimeText(body_template, "html")
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_username and self.smtp_password:
                    server.starttls()
                    server.login(self.smtp_username, self.smtp_password)
                
                server.send_message(msg)
            
            self.logger.info(f"Email alert sent to {to_emails}")
            
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
    
    async def get_alert_history(
        self,
        client_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get alert history."""
        if client_id:
            history_key = self.alert_history_key.format(client_id)
        else:
            history_key = self.alerts_key
        
        alerts_data = await self.redis.lrange(history_key, offset, offset + limit - 1)
        return [json.loads(alert_data) for alert_data in alerts_data]
    
    async def process_webhook_queue(self):
        """Process delayed webhook notifications."""
        while True:
            try:
                # Get queued notifications
                queue_data = await self.redis.lpop(self.webhook_queue_key)
                if not queue_data:
                    await asyncio.sleep(10)
                    continue
                
                notification = json.loads(queue_data)
                scheduled_time = datetime.fromisoformat(notification["scheduled_time"])
                
                if datetime.now() >= scheduled_time:
                    # Time to send notification
                    alert_data = notification["alert"]
                    alert = AlertEvent(**{
                        **alert_data,
                        "timestamp": datetime.fromisoformat(alert_data["timestamp"]),
                        "alert_type": AlertType(alert_data["alert_type"]),
                        "severity": AlertSeverity(alert_data["severity"])
                    })
                    
                    await self._send_notifications(alert, notification["webhooks"])
                else:
                    # Put back in queue
                    await self.redis.rpush(self.webhook_queue_key, queue_data)
                    await asyncio.sleep(60)  # Check again in 1 minute
                    
            except Exception as e:
                self.logger.error(f"Error processing webhook queue: {e}")
                await asyncio.sleep(10)
    
    async def cleanup(self):
        """Cleanup resources."""
        await self.http_client.aclose() 