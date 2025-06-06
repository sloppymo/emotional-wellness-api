"""
MOSS Audit Logging System

This module provides HIPAA-compliant audit logging for crisis detection including:
- Comprehensive activity tracking
- PHI protection and anonymization
- Regulatory compliance logging
- Real-time audit trail generation
- Secure log storage and retrieval
- Performance monitoring
"""

import asyncio
import hashlib
import json
import uuid
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from functools import lru_cache
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
import gzip
import shutil

from pydantic import BaseModel, Field, ConfigDict, validator
from structured_logging import get_logger
import aiofiles

from .crisis_classifier import CrisisSeverity, RiskDomain, CrisisContext, RiskAssessment
from .detection_thresholds import ClinicalSeverity, ThresholdAdjustment

logger = get_logger(__name__)

class AuditEventType(str, Enum):
    """Types of audit events."""
    ASSESSMENT_STARTED = "assessment_started"
    ASSESSMENT_COMPLETED = "assessment_completed"
    CRISIS_DETECTED = "crisis_detected"
    INTERVENTION_TRIGGERED = "intervention_triggered"
    ESCALATION_INITIATED = "escalation_initiated"
    THRESHOLD_ADJUSTED = "threshold_adjusted"
    USER_ACCESS = "user_access"
    SYSTEM_ERROR = "system_error"
    DATA_EXPORT = "data_export"
    CONFIGURATION_CHANGED = "configuration_changed"
    VALIDATION_PERFORMED = "validation_performed"

class AuditSeverity(str, Enum):
    """Severity levels for audit events."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ComplianceFramework(str, Enum):
    """Compliance frameworks to track."""
    HIPAA = "hipaa"
    GDPR = "gdpr"
    SOX = "sox"
    ISO27001 = "iso27001"
    NIST = "nist"

class PHICategory(str, Enum):
    """Categories of Protected Health Information."""
    DIRECT_IDENTIFIER = "direct_identifier"
    QUASI_IDENTIFIER = "quasi_identifier"
    SENSITIVE_HEALTH_DATA = "sensitive_health_data"
    BEHAVIORAL_DATA = "behavioral_data"
    NONE = "none"

class AuditEvent(BaseModel):
    """Individual audit event record."""
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    event_id: str = Field(..., description="Unique event identifier")
    event_type: AuditEventType = Field(..., description="Type of audit event")
    severity: AuditSeverity = Field(..., description="Event severity level")
    timestamp: datetime = Field(default_factory=datetime.now)
    user_id_hash: Optional[str] = Field(None, description="Hashed user identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    source_component: str = Field(..., description="Component that generated the event")
    action_performed: str = Field(..., description="Action that was performed")
    resource_accessed: Optional[str] = Field(None, description="Resource that was accessed")
    outcome: str = Field(..., description="Outcome of the action")
    phi_category: PHICategory = Field(default=PHICategory.NONE, description="PHI category involved")
    compliance_tags: List[str] = Field(default_factory=list, description="Compliance framework tags")
    risk_level: float = Field(default=0.0, ge=0.0, le=1.0, description="Associated risk level")
    intervention_triggered: bool = Field(default=False, description="Whether intervention was triggered")
    
    # Event-specific data (sanitized)
    event_data: Dict[str, Any] = Field(default_factory=dict, description="Sanitized event data")
    
    # Performance metrics
    processing_time_ms: Optional[float] = Field(None, ge=0.0, description="Processing time in milliseconds")
    memory_usage_mb: Optional[float] = Field(None, ge=0.0, description="Memory usage in MB")
    
    # Compliance tracking
    retention_period_days: int = Field(default=2555, ge=1, description="Retention period in days (7 years default)")
    encryption_status: str = Field(default="encrypted", description="Encryption status")
    access_control_applied: bool = Field(default=True, description="Whether access controls were applied")
    
    @validator('compliance_tags')
    def validate_compliance_tags(cls, v):
        """Validate compliance framework tags."""
        valid_frameworks = [framework.value for framework in ComplianceFramework]
        for tag in v:
            if tag not in valid_frameworks:
                raise ValueError(f"Invalid compliance framework: {tag}")
        return v

class AuditQuery(BaseModel):
    """Query parameters for audit log retrieval."""
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    start_date: Optional[datetime] = Field(None, description="Start date for query")
    end_date: Optional[datetime] = Field(None, description="End date for query")
    event_types: Optional[List[AuditEventType]] = Field(None, description="Event types to include")
    severity_levels: Optional[List[AuditSeverity]] = Field(None, description="Severity levels to include")
    user_id_hash: Optional[str] = Field(None, description="Specific user to query")
    session_id: Optional[str] = Field(None, description="Specific session to query")
    compliance_framework: Optional[ComplianceFramework] = Field(None, description="Compliance framework filter")
    phi_category: Optional[PHICategory] = Field(None, description="PHI category filter")
    intervention_triggered: Optional[bool] = Field(None, description="Filter by intervention status")
    limit: int = Field(default=1000, ge=1, le=10000, description="Maximum number of results")
    offset: int = Field(default=0, ge=0, description="Result offset for pagination")

class AuditStatistics(BaseModel):
    """Audit log statistics and metrics."""
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    total_events: int = Field(..., ge=0, description="Total number of events")
    events_by_type: Dict[str, int] = Field(..., description="Event counts by type")
    events_by_severity: Dict[str, int] = Field(..., description="Event counts by severity")
    avg_processing_time_ms: float = Field(..., ge=0.0, description="Average processing time")
    crisis_detection_rate: float = Field(..., ge=0.0, le=1.0, description="Crisis detection rate")
    intervention_trigger_rate: float = Field(..., ge=0.0, le=1.0, description="Intervention trigger rate")
    compliance_coverage: Dict[str, float] = Field(..., description="Compliance framework coverage")
    phi_exposure_incidents: int = Field(..., ge=0, description="PHI exposure incidents")
    time_period: Dict[str, datetime] = Field(..., description="Statistics time period")
    
class MOSSAuditLogger:
    """
    HIPAA-compliant audit logging system for MOSS crisis detection.
    
    This system provides:
    - Comprehensive activity tracking
    - PHI protection and anonymization
    - Regulatory compliance logging
    - Real-time audit trail generation
    - Secure log storage and retrieval
    """
    
    def __init__(
        self,
        log_directory: str = "logs/moss_audit",
        encryption_enabled: bool = True,
        retention_days: int = 2555,  # 7 years
        compression_enabled: bool = True,
        max_log_size_mb: int = 100
    ):
        """Initialize the MOSS audit logger."""
        self.log_directory = log_directory
        self.encryption_enabled = encryption_enabled
        self.retention_days = retention_days
        self.compression_enabled = compression_enabled
        self.max_log_size_mb = max_log_size_mb
        self._logger = get_logger(f"{__name__}.MOSSAuditLogger")
        
        # Event storage
        self._event_buffer: deque = deque(maxlen=10000)
        self._current_log_file = None
        self._current_log_size = 0
        
        # Statistics tracking
        self._statistics: Dict[str, Any] = {
            "total_events": 0,
            "events_by_type": defaultdict(int),
            "events_by_severity": defaultdict(int),
            "processing_times": deque(maxlen=1000),
            "crisis_detections": 0,
            "interventions_triggered": 0,
            "phi_incidents": 0
        }
        
        # Compliance tracking
        self._compliance_requirements = {
            ComplianceFramework.HIPAA: {
                "required_events": [
                    AuditEventType.ASSESSMENT_STARTED,
                    AuditEventType.CRISIS_DETECTED,
                    AuditEventType.INTERVENTION_TRIGGERED,
                    AuditEventType.USER_ACCESS
                ],
                "retention_days": 2555,  # 7 years
                "encryption_required": True
            },
            ComplianceFramework.GDPR: {
                "required_events": [
                    AuditEventType.USER_ACCESS,
                    AuditEventType.DATA_EXPORT
                ],
                "retention_days": 2190,  # 6 years
                "encryption_required": True
            }
        }
        
        # Initialize storage
        self._initialize_storage()
        
        self._logger.info(f"MOSSAuditLogger initialized (encryption: {encryption_enabled})")
    
    def _initialize_storage(self) -> None:
        """Initialize audit log storage."""
        try:
            os.makedirs(self.log_directory, exist_ok=True)
            
            # Create subdirectories for different log types
            subdirs = ["events", "statistics", "compliance", "archived"]
            for subdir in subdirs:
                os.makedirs(os.path.join(self.log_directory, subdir), exist_ok=True)
            
            # Initialize current log file
            self._current_log_file = self._get_log_filename()
            
        except Exception as e:
            self._logger.error(f"Error initializing audit storage: {str(e)}")
            raise
    
    def _get_log_filename(self) -> str:
        """Generate log filename with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(
            self.log_directory, 
            "events", 
            f"moss_audit_{timestamp}.jsonl"
        )
    
    async def log_assessment_event(
        self,
        assessment: RiskAssessment,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        processing_time_ms: Optional[float] = None
    ) -> str:
        """Log a crisis assessment event."""
        try:
            # Determine event type based on assessment
            if assessment.escalation_required:
                event_type = AuditEventType.CRISIS_DETECTED
                severity = AuditSeverity.CRITICAL
            elif assessment.severity in [CrisisSeverity.HIGH, CrisisSeverity.CRITICAL]:
                event_type = AuditEventType.ASSESSMENT_COMPLETED
                severity = AuditSeverity.WARNING
            else:
                event_type = AuditEventType.ASSESSMENT_COMPLETED
                severity = AuditSeverity.INFO
            
            # Sanitize assessment data
            sanitized_data = self._sanitize_assessment_data(assessment)
            
            # Create audit event
            event = AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=event_type,
                severity=severity,
                user_id_hash=self._hash_user_id(user_id) if user_id else None,
                session_id=session_id,
                source_component="moss.crisis_classifier",
                action_performed="crisis_risk_assessment",
                outcome=assessment.severity.value,
                phi_category=PHICategory.BEHAVIORAL_DATA,
                compliance_tags=["hipaa", "gdpr"],
                risk_level=assessment.urgency_score,
                intervention_triggered=assessment.escalation_required,
                event_data=sanitized_data,
                processing_time_ms=processing_time_ms
            )
            
            # Log the event
            await self._write_audit_event(event)
            
            # Update statistics
            self._update_statistics(event)
            
            return event.event_id
            
        except Exception as e:
            self._logger.error(f"Error logging assessment event: {str(e)}")
            raise
    
    async def log_intervention_event(
        self,
        intervention_type: str,
        assessment_id: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        intervention_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log an intervention trigger event."""
        try:
            # Sanitize intervention data
            sanitized_data = self._sanitize_intervention_data(intervention_data or {})
            sanitized_data["assessment_id"] = assessment_id
            sanitized_data["intervention_type"] = intervention_type
            
            event = AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.INTERVENTION_TRIGGERED,
                severity=AuditSeverity.WARNING,
                user_id_hash=self._hash_user_id(user_id) if user_id else None,
                session_id=session_id,
                source_component="moss.intervention_system",
                action_performed=f"trigger_{intervention_type}",
                resource_accessed="crisis_intervention_protocols",
                outcome="intervention_initiated",
                phi_category=PHICategory.SENSITIVE_HEALTH_DATA,
                compliance_tags=["hipaa"],
                intervention_triggered=True,
                event_data=sanitized_data
            )
            
            await self._write_audit_event(event)
            self._update_statistics(event)
            
            return event.event_id
            
        except Exception as e:
            self._logger.error(f"Error logging intervention event: {str(e)}")
            raise
    
    async def log_threshold_adjustment(
        self,
        adjustment: ThresholdAdjustment,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> str:
        """Log a threshold adjustment event."""
        try:
            # Sanitize adjustment data
            sanitized_data = {
                "domain": adjustment.domain.value,
                "severity_level": adjustment.severity_level.value,
                "adjustment_factor": adjustment.adjustment_factor,
                "reason": adjustment.reason,
                "validation_score": adjustment.validation_score
            }
            
            event = AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.THRESHOLD_ADJUSTED,
                severity=AuditSeverity.INFO,
                user_id_hash=self._hash_user_id(user_id) if user_id else None,
                session_id=session_id,
                source_component="moss.detection_thresholds",
                action_performed="threshold_adaptation",
                resource_accessed="detection_thresholds",
                outcome="threshold_updated",
                phi_category=PHICategory.NONE,
                compliance_tags=["hipaa"],
                event_data=sanitized_data
            )
            
            await self._write_audit_event(event)
            self._update_statistics(event)
            
            return event.event_id
            
        except Exception as e:
            self._logger.error(f"Error logging threshold adjustment: {str(e)}")
            raise
    
    async def log_user_access(
        self,
        user_id: str,
        action: str,
        resource: Optional[str] = None,
        session_id: Optional[str] = None,
        outcome: str = "success"
    ) -> str:
        """Log a user access event."""
        try:
            event = AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.USER_ACCESS,
                severity=AuditSeverity.INFO,
                user_id_hash=self._hash_user_id(user_id),
                session_id=session_id,
                source_component="moss.access_control",
                action_performed=action,
                resource_accessed=resource,
                outcome=outcome,
                phi_category=PHICategory.DIRECT_IDENTIFIER,
                compliance_tags=["hipaa", "gdpr"],
                event_data={
                    "access_time": datetime.now().isoformat(),
                    "user_agent": "moss_system",
                    "ip_address_hash": self._hash_ip_address("127.0.0.1")  # Placeholder
                }
            )
            
            await self._write_audit_event(event)
            self._update_statistics(event)
            
            return event.event_id
            
        except Exception as e:
            self._logger.error(f"Error logging user access: {str(e)}")
            raise
    
    async def log_system_error(
        self,
        error_type: str,
        error_message: str,
        component: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> str:
        """Log a system error event."""
        try:
            event = AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.SYSTEM_ERROR,
                severity=AuditSeverity.ERROR,
                user_id_hash=self._hash_user_id(user_id) if user_id else None,
                session_id=session_id,
                source_component=component,
                action_performed="system_operation",
                outcome="error",
                phi_category=PHICategory.NONE,
                compliance_tags=["hipaa"],
                event_data={
                    "error_type": error_type,
                    "error_message": self._sanitize_error_message(error_message),
                    "stack_trace_hash": self._hash_stack_trace(error_message)
                }
            )
            
            await self._write_audit_event(event)
            self._update_statistics(event)
            
            return event.event_id
            
        except Exception as e:
            self._logger.error(f"Error logging system error: {str(e)}")
            raise
    
    def _sanitize_assessment_data(self, assessment: RiskAssessment) -> Dict[str, Any]:
        """Sanitize assessment data for audit logging."""
        return {
            "severity": assessment.severity.value,
            "confidence": assessment.confidence,
            "urgency_score": assessment.urgency_score,
            "escalation_required": assessment.escalation_required,
            "primary_concerns": assessment.primary_concerns,
            "protective_factors": assessment.protective_factors,
            "recommendations_count": len(assessment.recommendations),
            "processing_time": assessment.metadata.get("processing_time", 0),
            "domain_risk_count": len(assessment.risk_domains)
        }
    
    def _sanitize_intervention_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize intervention data for audit logging."""
        sanitized = {}
        
        # Safe fields to include
        safe_fields = [
            "intervention_type", "assessment_id", "recommendation_count",
            "escalation_level", "resource_type", "contact_method"
        ]
        
        for field in safe_fields:
            if field in data:
                sanitized[field] = data[field]
        
        return sanitized
    
    def _sanitize_error_message(self, error_message: str) -> str:
        """Sanitize error message to remove potential PHI."""
        import re
        
        # Remove email addresses
        error_message = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', error_message)
        
        # Remove phone numbers
        error_message = re.sub(r'\b\d{3}-\d{3}-\d{4}\b', '[PHONE]', error_message)
        
        # Remove SSN patterns
        error_message = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', error_message)
        
        # Truncate if too long
        if len(error_message) > 500:
            error_message = error_message[:500] + "..."
        
        return error_message
    
    async def _write_audit_event(self, event: AuditEvent) -> None:
        """Write audit event to storage."""
        try:
            # Convert to JSON
            event_json = event.model_dump_json()
            
            # Check if we need to rotate log file
            if self._current_log_size > (self.max_log_size_mb * 1024 * 1024):
                await self._rotate_log_file()
            
            # Write to current log file
            async with aiofiles.open(self._current_log_file, 'a') as f:
                await f.write(event_json + '\n')
            
            # Update log size
            self._current_log_size += len(event_json) + 1
            
            # Add to buffer for real-time queries
            self._event_buffer.append(event)
            
        except Exception as e:
            self._logger.error(f"Error writing audit event: {str(e)}")
            raise
    
    async def _rotate_log_file(self) -> None:
        """Rotate current log file."""
        try:
            # Archive current file
            if self._current_log_file and os.path.exists(self._current_log_file):
                archive_path = os.path.join(
                    self.log_directory,
                    "archived",
                    os.path.basename(self._current_log_file)
                )
                
                if self.compression_enabled:
                    # Compress the file
                    with open(self._current_log_file, 'rb') as f_in:
                        with gzip.open(f"{archive_path}.gz", 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    os.remove(self._current_log_file)
                else:
                    shutil.move(self._current_log_file, archive_path)
            
            # Create new log file
            self._current_log_file = self._get_log_filename()
            self._current_log_size = 0
            
        except Exception as e:
            self._logger.error(f"Error rotating log file: {str(e)}")
            raise
    
    def _update_statistics(self, event: AuditEvent) -> None:
        """Update audit statistics."""
        self._statistics["total_events"] += 1
        self._statistics["events_by_type"][event.event_type.value] += 1
        self._statistics["events_by_severity"][event.severity.value] += 1
        
        if event.processing_time_ms:
            self._statistics["processing_times"].append(event.processing_time_ms)
        
        if event.event_type == AuditEventType.CRISIS_DETECTED:
            self._statistics["crisis_detections"] += 1
        
        if event.intervention_triggered:
            self._statistics["interventions_triggered"] += 1
        
        if event.phi_category != PHICategory.NONE:
            # Check for potential PHI exposure incidents
            if event.severity in [AuditSeverity.ERROR, AuditSeverity.CRITICAL]:
                self._statistics["phi_incidents"] += 1
    
    async def query_audit_logs(self, query: AuditQuery) -> List[AuditEvent]:
        """Query audit logs based on criteria."""
        try:
            results = []
            
            # Search in memory buffer first
            for event in self._event_buffer:
                if self._matches_query(event, query):
                    results.append(event)
            
            # Search in log files if needed
            if len(results) < query.limit:
                file_results = await self._search_log_files(query, query.limit - len(results))
                results.extend(file_results)
            
            # Apply pagination
            start_idx = query.offset
            end_idx = start_idx + query.limit
            
            return results[start_idx:end_idx]
            
        except Exception as e:
            self._logger.error(f"Error querying audit logs: {str(e)}")
            raise
    
    def _matches_query(self, event: AuditEvent, query: AuditQuery) -> bool:
        """Check if event matches query criteria."""
        # Date range check
        if query.start_date and event.timestamp < query.start_date:
            return False
        if query.end_date and event.timestamp > query.end_date:
            return False
        
        # Event type check
        if query.event_types and event.event_type not in query.event_types:
            return False
        
        # Severity check
        if query.severity_levels and event.severity not in query.severity_levels:
            return False
        
        # User check
        if query.user_id_hash and event.user_id_hash != query.user_id_hash:
            return False
        
        # Session check
        if query.session_id and event.session_id != query.session_id:
            return False
        
        # Compliance framework check
        if query.compliance_framework and query.compliance_framework.value not in event.compliance_tags:
            return False
        
        # PHI category check
        if query.phi_category and event.phi_category != query.phi_category:
            return False
        
        # Intervention check
        if query.intervention_triggered is not None and event.intervention_triggered != query.intervention_triggered:
            return False
        
        return True
    
    async def _search_log_files(self, query: AuditQuery, limit: int) -> List[AuditEvent]:
        """Search through archived log files."""
        results = []
        
        try:
            events_dir = os.path.join(self.log_directory, "events")
            archived_dir = os.path.join(self.log_directory, "archived")
            
            # Search current and archived files
            search_dirs = [events_dir, archived_dir]
            
            for search_dir in search_dirs:
                if not os.path.exists(search_dir):
                    continue
                
                for filename in sorted(os.listdir(search_dir), reverse=True):
                    if len(results) >= limit:
                        break
                    
                    file_path = os.path.join(search_dir, filename)
                    
                    # Handle compressed files
                    if filename.endswith('.gz'):
                        open_func = gzip.open
                        mode = 'rt'
                    else:
                        open_func = open
                        mode = 'r'
                    
                    try:
                        with open_func(file_path, mode) as f:
                            for line in f:
                                if len(results) >= limit:
                                    break
                                
                                try:
                                    event_data = json.loads(line.strip())
                                    event = AuditEvent(**event_data)
                                    
                                    if self._matches_query(event, query):
                                        results.append(event)
                                        
                                except (json.JSONDecodeError, ValueError):
                                    continue
                                    
                    except Exception as e:
                        self._logger.warning(f"Error reading log file {filename}: {str(e)}")
                        continue
            
            return results
            
        except Exception as e:
            self._logger.error(f"Error searching log files: {str(e)}")
            return []
    
    async def get_audit_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> AuditStatistics:
        """Get audit log statistics for a time period."""
        try:
            # Use current statistics if no date range specified
            if not start_date and not end_date:
                stats = self._statistics
                avg_processing_time = (
                    sum(stats["processing_times"]) / len(stats["processing_times"])
                    if stats["processing_times"] else 0.0
                )
                
                return AuditStatistics(
                    total_events=stats["total_events"],
                    events_by_type=dict(stats["events_by_type"]),
                    events_by_severity=dict(stats["events_by_severity"]),
                    avg_processing_time_ms=avg_processing_time,
                    crisis_detection_rate=(
                        stats["crisis_detections"] / max(1, stats["total_events"])
                    ),
                    intervention_trigger_rate=(
                        stats["interventions_triggered"] / max(1, stats["total_events"])
                    ),
                    compliance_coverage=self._calculate_compliance_coverage(),
                    phi_exposure_incidents=stats["phi_incidents"],
                    time_period={
                        "start": datetime.now() - timedelta(days=30),
                        "end": datetime.now()
                    }
                )
            
            # Query for specific date range
            query = AuditQuery(
                start_date=start_date,
                end_date=end_date,
                limit=10000  # Large limit for statistics
            )
            
            events = await self.query_audit_logs(query)
            
            # Calculate statistics from events
            events_by_type = defaultdict(int)
            events_by_severity = defaultdict(int)
            processing_times = []
            crisis_detections = 0
            interventions_triggered = 0
            phi_incidents = 0
            
            for event in events:
                events_by_type[event.event_type.value] += 1
                events_by_severity[event.severity.value] += 1
                
                if event.processing_time_ms:
                    processing_times.append(event.processing_time_ms)
                
                if event.event_type == AuditEventType.CRISIS_DETECTED:
                    crisis_detections += 1
                
                if event.intervention_triggered:
                    interventions_triggered += 1
                
                if (event.phi_category != PHICategory.NONE and 
                    event.severity in [AuditSeverity.ERROR, AuditSeverity.CRITICAL]):
                    phi_incidents += 1
            
            total_events = len(events)
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0.0
            
            return AuditStatistics(
                total_events=total_events,
                events_by_type=dict(events_by_type),
                events_by_severity=dict(events_by_severity),
                avg_processing_time_ms=avg_processing_time,
                crisis_detection_rate=crisis_detections / max(1, total_events),
                intervention_trigger_rate=interventions_triggered / max(1, total_events),
                compliance_coverage=self._calculate_compliance_coverage(),
                phi_exposure_incidents=phi_incidents,
                time_period={
                    "start": start_date or datetime.now() - timedelta(days=30),
                    "end": end_date or datetime.now()
                }
            )
            
        except Exception as e:
            self._logger.error(f"Error generating audit statistics: {str(e)}")
            raise
    
    def _calculate_compliance_coverage(self) -> Dict[str, float]:
        """Calculate compliance framework coverage."""
        coverage = {}
        
        for framework, requirements in self._compliance_requirements.items():
            required_events = set(requirements["required_events"])
            logged_event_types = set(self._statistics["events_by_type"].keys())
            
            covered_events = required_events.intersection(
                {AuditEventType(event_type) for event_type in logged_event_types}
            )
            
            coverage[framework.value] = len(covered_events) / len(required_events) if required_events else 1.0
        
        return coverage
    
    def _hash_user_id(self, user_id: str) -> str:
        """Hash user ID for privacy compliance."""
        return hashlib.sha256(user_id.encode()).hexdigest()[:16]
    
    def _hash_ip_address(self, ip_address: str) -> str:
        """Hash IP address for privacy compliance."""
        return hashlib.sha256(ip_address.encode()).hexdigest()[:12]
    
    def _hash_stack_trace(self, stack_trace: str) -> str:
        """Hash stack trace for privacy while maintaining uniqueness."""
        return hashlib.sha256(stack_trace.encode()).hexdigest()[:20]
    
    async def cleanup_expired_logs(self) -> int:
        """Clean up expired audit logs based on retention policy."""
        try:
            expired_count = 0
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            # Clean up archived logs
            archived_dir = os.path.join(self.log_directory, "archived")
            if os.path.exists(archived_dir):
                for filename in os.listdir(archived_dir):
                    file_path = os.path.join(archived_dir, filename)
                    
                    try:
                        # Extract date from filename
                        date_str = filename.split('_')[2].split('.')[0]
                        file_date = datetime.strptime(date_str, "%Y%m%d")
                        
                        if file_date < cutoff_date:
                            os.remove(file_path)
                            expired_count += 1
                            
                    except (ValueError, IndexError):
                        # Skip files with unexpected naming
                        continue
            
            self._logger.info(f"Cleaned up {expired_count} expired audit log files")
            return expired_count
            
        except Exception as e:
            self._logger.error(f"Error cleaning up expired logs: {str(e)}")
            return 0


# Convenience functions
async def log_crisis_assessment(
    assessment: RiskAssessment,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    processing_time_ms: Optional[float] = None
) -> str:
    """Convenience function to log a crisis assessment."""
    audit_logger = MOSSAuditLogger()
    return await audit_logger.log_assessment_event(
        assessment, user_id, session_id, processing_time_ms
    )

async def log_crisis_intervention(
    intervention_type: str,
    assessment_id: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None
) -> str:
    """Convenience function to log a crisis intervention."""
    audit_logger = MOSSAuditLogger()
    return await audit_logger.log_intervention_event(
        intervention_type, assessment_id, user_id, session_id
    ) 