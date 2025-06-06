"""
Alert Rules Module

Defines the rule structure and comparison logic for system monitoring alerts.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from ..structured_logging import get_logger

logger = get_logger(__name__)

class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning" 
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class ComparisonOperator(str, Enum):
    """Comparison operators for alert conditions."""
    GREATER_THAN = ">"
    GREATER_EQUAL = ">="
    LESS_THAN = "<"
    LESS_EQUAL = "<="
    EQUAL = "=="
    NOT_EQUAL = "!="

class MetricType(str, Enum):
    """Types of metrics that can be monitored."""
    GAUGE = "gauge"
    COUNTER = "counter"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"
    
    # System-specific metric types
    QUEUE_DEPTH = "queue_depth"
    TASK_LATENCY = "task_latency"
    ERROR_RATE = "error_rate"
    INTEGRATION_AVAILABILITY = "integration_availability"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    ACTIVE_REQUESTS = "active_requests"
    AUTH_FAILURES = "auth_failures"

class AlertRule(BaseModel):
    """
    Definition of an alert rule that monitors a specific metric against a threshold.
    """
    id: str
    name: str
    description: str
    metric_name: str
    metric_type: MetricType
    operator: ComparisonOperator
    threshold: float
    duration_seconds: int = Field(default=60, description="Duration the condition must be true before alerting")
    severity: AlertSeverity
    enabled: bool = True
    labels: Dict[str, str] = Field(default_factory=dict)
    
    # Alert suppression
    cooldown_seconds: int = Field(default=300, description="Minimum time between repeated alerts")
    last_triggered: Optional[datetime] = None
    
    # Advanced options
    aggregation_function: Optional[str] = None  # e.g., "avg", "max", "min", "sum", "count"
    
    def evaluate(self, current_value: float, timestamp: datetime = None) -> bool:
        """
        Evaluate if the current value triggers this alert rule.
        
        Args:
            current_value: The current metric value to evaluate
            timestamp: The timestamp of the evaluation (defaults to now)
            
        Returns:
            bool: True if the alert should be triggered
        """
        if not self.enabled:
            return False
            
        # Check cooldown period
        if self.last_triggered:
            cooldown_end = self.last_triggered + timedelta(seconds=self.cooldown_seconds)
            if datetime.utcnow() < cooldown_end:
                logger.debug(f"Alert {self.id} in cooldown period until {cooldown_end}")
                return False
        
        # Evaluate condition
        triggered = False
        
        if self.operator == ComparisonOperator.GREATER_THAN:
            triggered = current_value > self.threshold
        elif self.operator == ComparisonOperator.GREATER_EQUAL:
            triggered = current_value >= self.threshold
        elif self.operator == ComparisonOperator.LESS_THAN:
            triggered = current_value < self.threshold
        elif self.operator == ComparisonOperator.LESS_EQUAL:
            triggered = current_value <= self.threshold
        elif self.operator == ComparisonOperator.EQUAL:
            triggered = current_value == self.threshold
        elif self.operator == ComparisonOperator.NOT_EQUAL:
            triggered = current_value != self.threshold
        
        if triggered:
            # In a real implementation, we would check if the condition has been true
            # for the specified duration before triggering
            self.last_triggered = datetime.utcnow()
            logger.info(f"Alert rule {self.id} triggered: {self.name}")
            
        return triggered

class AlertRuleSet(BaseModel):
    """A collection of alert rules, typically for a specific component or subsystem."""
    name: str
    description: str
    rules: List[AlertRule] = Field(default_factory=list)
    
    def add_rule(self, rule: AlertRule) -> None:
        """Add a rule to this ruleset."""
        self.rules.append(rule)
    
    def evaluate_all(self, metrics: Dict[str, float]) -> List[AlertRule]:
        """
        Evaluate all rules against the provided metrics.
        
        Args:
            metrics: Dictionary of metric names to current values
            
        Returns:
            List of triggered alert rules
        """
        triggered_rules = []
        
        for rule in self.rules:
            if rule.metric_name in metrics:
                current_value = metrics[rule.metric_name]
                if rule.evaluate(current_value):
                    triggered_rules.append(rule)
        
        return triggered_rules

# Predefined rule templates
def create_high_queue_depth_rule(queue_name: str, threshold: int = 100) -> AlertRule:
    """Create a rule for monitoring queue depth."""
    return AlertRule(
        id=f"queue_depth_{queue_name}",
        name=f"High queue depth for {queue_name}",
        description=f"Queue {queue_name} has accumulated too many pending tasks",
        metric_name=f"background_task_queue_size_{queue_name}",
        metric_type=MetricType.QUEUE_DEPTH,
        operator=ComparisonOperator.GREATER_THAN,
        threshold=threshold,
        duration_seconds=300,  # 5 minutes
        severity=AlertSeverity.WARNING,
        labels={"queue": queue_name, "component": "celery"}
    )

def create_integration_availability_rule(integration_name: str) -> AlertRule:
    """Create a rule for monitoring integration availability."""
    return AlertRule(
        id=f"integration_availability_{integration_name}",
        name=f"{integration_name} integration unavailable",
        description=f"The {integration_name} integration is not responding",
        metric_name=f"integration_availability_{integration_name}",
        metric_type=MetricType.INTEGRATION_AVAILABILITY,
        operator=ComparisonOperator.EQUAL,
        threshold=0,  # 0 = unavailable
        duration_seconds=180,  # 3 minutes
        severity=AlertSeverity.CRITICAL,
        labels={"integration": integration_name, "component": "external"}
    )

def create_high_error_rate_rule(endpoint: str, threshold: float = 0.05) -> AlertRule:
    """Create a rule for monitoring API error rates."""
    return AlertRule(
        id=f"error_rate_{endpoint}",
        name=f"High error rate on {endpoint}",
        description=f"The error rate on {endpoint} exceeds {threshold*100}%",
        metric_name=f"api_error_rate_{endpoint}",
        metric_type=MetricType.ERROR_RATE,
        operator=ComparisonOperator.GREATER_THAN,
        threshold=threshold,
        duration_seconds=300,  # 5 minutes
        severity=AlertSeverity.WARNING,
        labels={"endpoint": endpoint, "component": "api"}
    )

def create_high_memory_usage_rule(threshold_percent: float = 85.0) -> AlertRule:
    """Create a rule for monitoring memory usage."""
    return AlertRule(
        id="high_memory_usage",
        name="High memory usage",
        description=f"System memory usage exceeds {threshold_percent}%",
        metric_name="memory_usage_percent",
        metric_type=MetricType.MEMORY_USAGE,
        operator=ComparisonOperator.GREATER_THAN,
        threshold=threshold_percent,
        duration_seconds=300,  # 5 minutes
        severity=AlertSeverity.WARNING,
        labels={"component": "system"}
    )

def create_auth_failure_spike_rule(threshold: int = 10) -> AlertRule:
    """Create a rule for monitoring authentication failure spikes."""
    return AlertRule(
        id="auth_failure_spike",
        name="Authentication failure spike",
        description=f"More than {threshold} authentication failures in 5 minutes",
        metric_name="authentication_failures_total",
        metric_type=MetricType.AUTH_FAILURES,
        operator=ComparisonOperator.GREATER_THAN,
        threshold=threshold,
        duration_seconds=300,  # 5 minutes
        severity=AlertSeverity.CRITICAL,
        labels={"component": "security"}
    )
