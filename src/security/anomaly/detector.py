"""
Anomaly Detection Core

This module provides the core functionality for detecting anomalies
in PHI access patterns and other security-related events.
"""

import json
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set, Union, Tuple
from collections import defaultdict, deque

import numpy as np
from redis.asyncio import Redis

from .models import (
    Anomaly,
    AnomalyEvent,
    AnomalyType,
    AnomalySeverity,
    AnomalyRule
)
from ..structured_logging.phi_logger import get_phi_logger
from ...utils.structured_logging import get_logger

logger = get_logger(__name__)


class AnomalyDetector:
    """
    Anomaly detector for security monitoring.
    
    Features:
    - Real-time detection of unusual PHI access patterns
    - Configurable detection rules
    - Historical baseline comparison
    - Multi-factor anomaly correlation
    - Notification and alerting capabilities
    """
    
    def __init__(self, redis: Redis):
        """
        Initialize the anomaly detector.
        
        Args:
            redis: Redis connection for storing state and baselines
        """
        self.redis = redis
        self.redis_prefix = "anomaly:"
        
        # Short-term memory cache with recent events (for correlation)
        self.recent_events = deque(maxlen=1000)
        
        # Active rules
        self.rules: Dict[str, AnomalyRule] = {}
        
        # Last detection timestamps to enforce cooldown
        self.last_detection: Dict[str, Dict[str, float]] = defaultdict(dict)
        
        # Background tasks
        self._baseline_update_task = None
        self._process_events_task = None
        
        logger.info("AnomalyDetector initialized")
        
    async def start(self):
        """Start the anomaly detector background tasks."""
        # Load rules
        await self.load_rules()
        
        # Start background tasks
        if self._baseline_update_task is None or self._baseline_update_task.done():
            self._baseline_update_task = asyncio.create_task(self._periodic_baseline_update())
            
        if self._process_events_task is None or self._process_events_task.done():
            self._process_events_task = asyncio.create_task(self._process_phi_events())
            
    async def load_rules(self):
        """Load anomaly detection rules."""
        try:
            # Get rules from Redis
            rule_keys = await self.redis.keys(f"{self.redis_prefix}rule:*")
            
            for key in rule_keys:
                rule_data = await self.redis.get(key)
                if rule_data:
                    rule = AnomalyRule.model_validate_json(rule_data)
                    if rule.enabled:
                        self.rules[rule.rule_id] = rule
            
            if not self.rules:
                # Load default rules if none exist
                default_rules = self._get_default_rules()
                for rule in default_rules:
                    await self.add_rule(rule)
                    
            logger.info(f"Loaded {len(self.rules)} anomaly detection rules")
            
        except Exception as e:
            logger.error(f"Error loading anomaly detection rules: {e}")
            # Load default rules on error
            self.rules = {r.rule_id: r for r in self._get_default_rules()}
    
    def _get_default_rules(self) -> List[AnomalyRule]:
        """
        Get default anomaly detection rules.
        
        Returns:
            List of default rules
        """
        return [
            AnomalyRule(
                rule_id="unusual-access-time",
                name="Unusual Access Time",
                description="Detects PHI access outside normal business hours",
                anomaly_type=AnomalyType.UNUSUAL_ACCESS_TIME,
                default_severity=AnomalySeverity.MEDIUM,
                conditions={
                    "business_hours_start": 8,  # 8am
                    "business_hours_end": 18,   # 6pm
                    "weekend_factor": 2.0       # Higher threshold on weekends
                },
                min_confidence=0.7
            ),
            AnomalyRule(
                rule_id="unusual-access-volume",
                name="Unusual Access Volume",
                description="Detects unusually high volume of PHI access",
                anomaly_type=AnomalyType.UNUSUAL_ACCESS_VOLUME,
                default_severity=AnomalySeverity.HIGH,
                conditions={
                    "time_window_minutes": 60,
                    "threshold_factor": 2.0,  # 2x normal volume
                    "min_access_count": 10    # Minimum to trigger
                },
                min_confidence=0.8
            ),
            AnomalyRule(
                rule_id="unusual-access-pattern",
                name="Unusual Access Pattern",
                description="Detects unusual patterns in PHI access",
                anomaly_type=AnomalyType.UNUSUAL_ACCESS_PATTERN,
                default_severity=AnomalySeverity.MEDIUM,
                conditions={
                    "pattern_diversity_threshold": 0.7,
                    "min_unique_records": 5
                },
                min_confidence=0.75
            ),
            AnomalyRule(
                rule_id="multiple-failed-auth",
                name="Multiple Failed Authentications",
                description="Detects multiple failed authentication attempts",
                anomaly_type=AnomalyType.MULTIPLE_FAILED_AUTHENTICATIONS,
                default_severity=AnomalySeverity.HIGH,
                conditions={
                    "time_window_minutes": 10,
                    "threshold_count": 5
                },
                min_confidence=0.9
            )
        ]
    
    async def add_rule(self, rule: AnomalyRule) -> bool:
        """
        Add a new anomaly detection rule.
        
        Args:
            rule: Rule to add
            
        Returns:
            True if successful
        """
        try:
            # Save to Redis
            rule_key = f"{self.redis_prefix}rule:{rule.rule_id}"
            await self.redis.set(rule_key, rule.model_dump_json())
            
            # Add to active rules
            if rule.enabled:
                self.rules[rule.rule_id] = rule
                
            logger.info(f"Added anomaly detection rule: {rule.name}")
            return True
        except Exception as e:
            logger.error(f"Error adding anomaly rule: {e}")
            return False
    
    async def process_phi_access_event(self, 
                                     user_id: str, 
                                     action: str,
                                     data_elements: List[str],
                                     context: Dict[str, Any]) -> Optional[AnomalyEvent]:
        """
        Process a PHI access event for anomalies.
        
        Args:
            user_id: User performing the access
            action: Action being performed
            data_elements: PHI elements being accessed
            context: Additional context information
            
        Returns:
            AnomalyEvent if anomaly detected, None otherwise
        """
        # Create event record for analysis
        event = {
            "timestamp": datetime.utcnow(),
            "user_id": user_id,
            "action": action,
            "data_elements": data_elements,
            "context": context
        }
        
        # Add to recent events for correlation
        self.recent_events.append(event)
        
        # Process through each rule
        detected_anomalies = []
        
        for rule_id, rule in self.rules.items():
            # Check cooldown period
            user_rule_key = f"{user_id}:{rule_id}"
            last_time = self.last_detection.get(rule_id, {}).get(user_id)
            
            if last_time and (time.time() - last_time < rule.cooldown_minutes * 60):
                continue
                
            # Apply rule
            anomaly = await self._apply_rule(rule, event)
            if anomaly:
                # Update cooldown timestamp
                self.last_detection.setdefault(rule_id, {})[user_id] = time.time()
                detected_anomalies.append(anomaly)
                
        # Return highest severity anomaly if multiple detected
        if detected_anomalies:
            # Sort by severity (critical > high > medium > low)
            severity_order = {
                AnomalySeverity.CRITICAL: 0,
                AnomalySeverity.HIGH: 1,
                AnomalySeverity.MEDIUM: 2,
                AnomalySeverity.LOW: 3
            }
            detected_anomalies.sort(key=lambda a: (severity_order[a.severity], -a.confidence_score))
            return detected_anomalies[0]
            
        return None
        
    async def _apply_rule(self, 
                         rule: AnomalyRule, 
                         event: Dict[str, Any]) -> Optional[AnomalyEvent]:
        """
        Apply a rule to an event to detect anomalies.
        
        Args:
            rule: Rule to apply
            event: Event to check
            
        Returns:
            AnomalyEvent if anomaly detected, None otherwise
        """
        # Apply appropriate detector based on rule type
        if rule.anomaly_type == AnomalyType.UNUSUAL_ACCESS_TIME:
            return await self._detect_unusual_access_time(rule, event)
        elif rule.anomaly_type == AnomalyType.UNUSUAL_ACCESS_VOLUME:
            return await self._detect_unusual_access_volume(rule, event)
        elif rule.anomaly_type == AnomalyType.UNUSUAL_ACCESS_PATTERN:
            return await self._detect_unusual_access_pattern(rule, event)
        elif rule.anomaly_type == AnomalyType.MULTIPLE_FAILED_AUTHENTICATIONS:
            return await self._detect_multiple_failed_auth(rule, event)
        else:
            logger.warning(f"No detector implemented for rule type: {rule.anomaly_type}")
            return None
    
    async def _detect_unusual_access_time(self, 
                                        rule: AnomalyRule, 
                                        event: Dict[str, Any]) -> Optional[AnomalyEvent]:
        """Detect unusual access times."""
        # Extract time components
        timestamp = event["timestamp"]
        hour = timestamp.hour
        is_weekend = timestamp.weekday() >= 5  # 5=Saturday, 6=Sunday
        
        # Get rule conditions
        conditions = rule.conditions
        business_hours_start = conditions.get("business_hours_start", 8)
        business_hours_end = conditions.get("business_hours_end", 18)
        weekend_factor = conditions.get("weekend_factor", 1.0)
        
        # Calculate base confidence
        confidence = 0.0
        
        if is_weekend:
            # Higher confidence for weekend access
            confidence = 0.5
            
            # Even higher during night hours on weekend
            if hour < 6 or hour > 22:  # Before 6am or after 10pm
                confidence = 0.8
        else:
            # Weekday outside business hours
            if hour < business_hours_start or hour >= business_hours_end:
                # Early morning or late night
                if hour < 6 or hour > 22:
                    confidence = 0.7
                else:
                    # Evening or early morning
                    confidence = 0.5
        
        # Apply weekend factor
        if is_weekend:
            confidence *= weekend_factor
            
        # Check if confidence meets threshold
        if confidence >= rule.min_confidence:
            time_desc = f"{hour:02d}:00"
            day_type = "weekend" if is_weekend else "weekday"
            
            return AnomalyEvent(
                event_type=rule.anomaly_type,
                user_id=event["user_id"],
                system_component="phi_access",
                severity=rule.default_severity,
                confidence_score=confidence,
                description=f"Unusual access time detected: {time_desc} on {day_type}",
                raw_data={
                    "access_time": timestamp.isoformat(),
                    "hour": hour,
                    "is_weekend": is_weekend,
                    "action": event["action"],
                    "data_elements": event["data_elements"]
                }
            )
            
        return None
        
    async def _detect_unusual_access_volume(self,
                                          rule: AnomalyRule, 
                                          event: Dict[str, Any]) -> Optional[AnomalyEvent]:
        """Detect unusual volume of PHI access."""
        user_id = event["user_id"]
        
        # Get rule conditions
        conditions = rule.conditions
        time_window_minutes = conditions.get("time_window_minutes", 60)
        threshold_factor = conditions.get("threshold_factor", 2.0)
        min_access_count = conditions.get("min_access_count", 10)
        
        # Get user's historical baseline
        baseline_key = f"{self.redis_prefix}baseline:volume:{user_id}"
        baseline_data = await self.redis.get(baseline_key)
        
        baseline = None
        if baseline_data:
            baseline = json.loads(baseline_data)
        
        # Count recent accesses by this user in the time window
        window_start = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        access_count = 0
        
        for recent_event in self.recent_events:
            if recent_event["user_id"] == user_id and recent_event["timestamp"] >= window_start:
                access_count += 1
        
        # Compute the daily average baseline if we have one
        if baseline and "daily_average" in baseline:
            # Calculate hourly rate from daily average
            hourly_rate = baseline["daily_average"] / 24
            
            # Expected count for this window
            expected_count = hourly_rate * (time_window_minutes / 60)
            
            # Actual exceeds expected by factor
            if access_count >= min_access_count and access_count > (expected_count * threshold_factor):
                # Calculate confidence based on how much it exceeds
                confidence = min(0.95, 0.5 + (access_count / expected_count) * 0.1)
                
                if confidence >= rule.min_confidence:
                    return AnomalyEvent(
                        event_type=rule.anomaly_type,
                        user_id=user_id,
                        system_component="phi_access",
                        severity=rule.default_severity,
                        confidence_score=confidence,
                        description=f"Unusual access volume detected: {access_count} accesses in {time_window_minutes} minutes",
                        raw_data={
                            "access_count": access_count,
                            "time_window_minutes": time_window_minutes,
                            "expected_count": expected_count,
                            "threshold_factor": threshold_factor,
                            "ratio": access_count / expected_count if expected_count > 0 else 0
                        }
                    )
        
        # First-time baseline or not enough data
        elif access_count >= min_access_count * 2:  # Higher threshold for first detection
            # Set moderate confidence for first detection
            confidence = 0.7
            
            if confidence >= rule.min_confidence:
                return AnomalyEvent(
                    event_type=rule.anomaly_type,
                    user_id=user_id,
                    system_component="phi_access",
                    severity=rule.default_severity,
                    confidence_score=confidence,
                    description=f"High access volume detected without baseline: {access_count} accesses in {time_window_minutes} minutes",
                    raw_data={
                        "access_count": access_count,
                        "time_window_minutes": time_window_minutes,
                        "first_detection": True
                    }
                )
        
        return None
        
    async def _detect_unusual_access_pattern(self,
                                           rule: AnomalyRule, 
                                           event: Dict[str, Any]) -> Optional[AnomalyEvent]:
        """Detect unusual patterns in PHI access."""
        user_id = event["user_id"]
        
        # Get rule conditions
        conditions = rule.conditions
        pattern_diversity_threshold = conditions.get("pattern_diversity_threshold", 0.7)
        min_unique_records = conditions.get("min_unique_records", 5)
        
        # Get records accessed in the last hour
        window_start = datetime.utcnow() - timedelta(hours=1)
        accessed_elements = set()
        access_actions = []
        
        for recent_event in self.recent_events:
            if recent_event["user_id"] == user_id and recent_event["timestamp"] >= window_start:
                # Add elements to set to count unique records
                accessed_elements.update(recent_event.get("data_elements", []))
                access_actions.append(recent_event["action"])
        
        # Check if enough unique records
        if len(accessed_elements) < min_unique_records:
            return None
            
        # Check action diversity
        unique_actions = len(set(access_actions))
        action_diversity = unique_actions / len(access_actions) if access_actions else 0
        
        # Get user's historical pattern baseline
        baseline_key = f"{self.redis_prefix}baseline:pattern:{user_id}"
        baseline_data = await self.redis.get(baseline_key)
        
        if baseline_data:
            baseline = json.loads(baseline_data)
            
            # Check for unusual access pattern
            common_elements = baseline.get("common_elements", [])
            
            # Calculate how many accessed elements are not in common elements
            unusual_elements = [e for e in accessed_elements if e not in common_elements]
            unusual_ratio = len(unusual_elements) / len(accessed_elements) if accessed_elements else 0
            
            if unusual_ratio >= pattern_diversity_threshold:
                confidence = min(0.95, unusual_ratio - 0.1)
                
                if confidence >= rule.min_confidence:
                    return AnomalyEvent(
                        event_type=rule.anomaly_type,
                        user_id=user_id,
                        system_component="phi_access",
                        severity=rule.default_severity,
                        confidence_score=confidence,
                        description=f"Unusual access pattern detected: {len(unusual_elements)} uncommon data elements accessed",
                        raw_data={
                            "unusual_elements": unusual_elements,
                            "unusual_ratio": unusual_ratio,
                            "action_diversity": action_diversity,
                            "unique_actions": unique_actions
                        }
                    )
        
        return None
        
    async def _detect_multiple_failed_auth(self,
                                          rule: AnomalyRule, 
                                          event: Dict[str, Any]) -> Optional[AnomalyEvent]:
        """Detect multiple failed authentication attempts."""
        # This detector would normally work with auth log events
        # For the purpose of this example implementation, we'll just return None
        # as authentication events are handled separately from PHI access events
        return None
        
    async def _periodic_baseline_update(self):
        """Periodically update user baselines for anomaly detection."""
        try:
            while True:
                # Update baselines once per day
                await asyncio.sleep(86400)  # 24 hours
                
                # In a real implementation, this would analyze historical PHI access
                # logs and update baseline statistics for each user
                
                # For this example, we'll just log that we would do this
                logger.info("Would update user baselines for anomaly detection")
                
        except asyncio.CancelledError:
            logger.info("Baseline update task cancelled")
        except Exception as e:
            logger.error(f"Error in baseline update task: {e}")
            
    async def _process_phi_events(self):
        """Process PHI access events from logs."""
        try:
            while True:
                # In a real implementation, this would subscribe to a stream of PHI access events
                # For this example, we'll just sleep and log that we would do this
                await asyncio.sleep(60)  # Check every minute
                logger.debug("Would process new PHI access events for anomaly detection")
        except asyncio.CancelledError:
            logger.info("PHI event processing task cancelled")
        except Exception as e:
            logger.error(f"Error in PHI event processing task: {e}")
            
    async def report_anomaly(self, anomaly_event: AnomalyEvent) -> str:
        """Report and store an anomaly event."""
        try:
            # Create a unique ID for this anomaly
            anomaly_id = str(anomaly_event.event_id)
            
            # Store the anomaly event
            anomaly_key = f"{self.redis_prefix}event:{anomaly_id}"
            await self.redis.set(anomaly_key, anomaly_event.model_dump_json())
            
            # Add to user's anomaly list
            if anomaly_event.user_id:
                user_anomaly_key = f"{self.redis_prefix}user:{anomaly_event.user_id}"
                await self.redis.lpush(user_anomaly_key, anomaly_id)
                await self.redis.ltrim(user_anomaly_key, 0, 99)  # Keep last 100
            
            # Add to recent anomalies list
            recent_key = f"{self.redis_prefix}recent"
            await self.redis.lpush(recent_key, anomaly_id)
            await self.redis.ltrim(recent_key, 0, 99)  # Keep last 100
            
            # Log based on severity
            if anomaly_event.severity == AnomalySeverity.HIGH or anomaly_event.severity == AnomalySeverity.CRITICAL:
                logger.warning(f"High severity anomaly detected: {anomaly_event.description}", extra={
                    "anomaly_id": anomaly_id,
                    "user_id": anomaly_event.user_id,
                    "type": anomaly_event.event_type,
                    "severity": anomaly_event.severity
                })
            else:
                logger.info(f"Anomaly detected: {anomaly_event.description}", extra={
                    "anomaly_id": anomaly_id,
                    "user_id": anomaly_event.user_id,
                    "type": anomaly_event.event_type,
                    "severity": anomaly_event.severity
                })
            
            return anomaly_id
        except Exception as e:
            logger.error(f"Error reporting anomaly: {e}")
            return ""
    
    async def get_anomalies(self, 
                          user_id: Optional[str] = None, 
                          event_type: Optional[AnomalyType] = None,
                          severity: Optional[AnomalySeverity] = None,
                          limit: int = 20) -> List[AnomalyEvent]:
        """Get recent anomalies, filtered by criteria."""
        try:
            anomalies = []
            
            if user_id:
                # Get anomalies for specific user
                key = f"{self.redis_prefix}user:{user_id}"
                anomaly_ids = await self.redis.lrange(key, 0, limit - 1)
            else:
                # Get recent anomalies
                key = f"{self.redis_prefix}recent"
                anomaly_ids = await self.redis.lrange(key, 0, limit - 1)
            
            for anomaly_id in anomaly_ids:
                anomaly_key = f"{self.redis_prefix}event:{anomaly_id}"
                anomaly_data = await self.redis.get(anomaly_key)
                
                if anomaly_data:
                    anomaly = AnomalyEvent.model_validate_json(anomaly_data)
                    
                    # Apply filters
                    if event_type and anomaly.event_type != event_type:
                        continue
                    if severity and anomaly.severity != severity:
                        continue
                        
                    anomalies.append(anomaly)
                    
            return anomalies
        except Exception as e:
            logger.error(f"Error getting anomalies: {e}")
            return []

    async def shutdown(self):
        """Shutdown anomaly detector tasks."""
        # Cancel background tasks
        if self._baseline_update_task and not self._baseline_update_task.done():
            self._baseline_update_task.cancel()
            try:
                await self._baseline_update_task
            except asyncio.CancelledError:
                pass
                
        if self._process_events_task and not self._process_events_task.done():
            self._process_events_task.cancel()
            try:
                await self._process_events_task
            except asyncio.CancelledError:
                pass
                
        logger.info("Anomaly detector shutdown complete")


# Global instance
_anomaly_detector = None

async def get_anomaly_detector(redis_url: Optional[str] = None) -> AnomalyDetector:
    """
    Get the global anomaly detector instance.
    
    Args:
        redis_url: Redis URL (only used on first initialization)
        
    Returns:
        The global anomaly detector instance
    """
    global _anomaly_detector
    
    if _anomaly_detector is None:
        if redis_url is None:
            from ...config.settings import get_settings
            settings = get_settings()
            redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
        
        redis_client = Redis.from_url(redis_url)
        _anomaly_detector = AnomalyDetector(redis_client)
        await _anomaly_detector.start()
    
    return _anomaly_detector
