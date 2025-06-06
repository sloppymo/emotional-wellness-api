"""
Notification models for the Emotional Wellness API.

This module defines models for notification handling including notification
records, channels, priorities, and statuses.
"""

import uuid
from enum import Enum
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class NotificationChannel(str, Enum):
    """Channels through which notifications can be sent."""
    APP = "APP"  # In-app notification
    EMAIL = "EMAIL"  # Email notification
    SMS = "SMS"  # SMS text message


class NotificationPriority(str, Enum):
    """Priority levels for notifications."""
    LOW = "LOW"  # Low priority, non-urgent
    NORMAL = "NORMAL"  # Normal priority, default
    HIGH = "HIGH"  # High priority, important
    URGENT = "URGENT"  # Urgent priority, critical


class NotificationStatus(str, Enum):
    """Status of a notification in its lifecycle."""
    PENDING = "PENDING"  # Created but not yet sent
    PROCESSING = "PROCESSING"  # In process of sending
    DELIVERED = "DELIVERED"  # Successfully delivered
    READ = "READ"  # Read by recipient
    FAILED = "FAILED"  # Failed to deliver
    CANCELLED = "CANCELLED"  # Cancelled before delivery


class Notification:
    """
    Notification record for storing and tracking notifications in the system.
    
    This model is used for storage in the database and tracking notification
    status through its lifecycle.
    """
    
    def __init__(
        self,
        id: uuid.UUID,
        subject: str,
        message: str,
        recipients: List[str],
        priority: NotificationPriority,
        channel: NotificationChannel,
        status: NotificationStatus,
        metadata: Dict[str, Any] = None,
        created_at: Optional[datetime] = None,
        delivered_at: Optional[datetime] = None,
        read_at: Optional[datetime] = None
    ):
        self.id = id
        self.subject = subject
        self.message = message
        self.recipients = recipients
        self.priority = priority
        self.channel = channel
        self.status = status
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.utcnow()
        self.delivered_at = delivered_at
        self.read_at = read_at


# Pydantic models for API requests and responses

class NotificationCreate(BaseModel):
    """Data model for creating a new notification."""
    recipients: List[str] = Field(
        description="List of recipient user IDs"
    )
    subject: str = Field(
        description="Notification subject line"
    )
    message: str = Field(
        description="Notification message content"
    )
    priority: NotificationPriority = Field(
        default=NotificationPriority.NORMAL,
        description="Priority level of the notification"
    )
    channel: NotificationChannel = Field(
        default=NotificationChannel.APP,
        description="Channel through which to send the notification"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional metadata for the notification"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "recipients": ["user-123", "user-456"],
                "subject": "Important Clinical Update",
                "message": "Please review the patient's updated care plan.",
                "priority": "HIGH",
                "channel": "APP",
                "metadata": {"patient_id": "patient-789", "care_plan_id": "plan-101"}
            }
        }


class NotificationResponse(BaseModel):
    """Data model for notification API responses."""
    id: uuid.UUID = Field(
        description="Notification ID"
    )
    subject: str = Field(
        description="Notification subject line"
    )
    message: str = Field(
        description="Notification message content"
    )
    recipients: List[str] = Field(
        description="List of recipient user IDs"
    )
    priority: str = Field(
        description="Priority level of the notification"
    )
    channel: str = Field(
        description="Channel through which the notification was sent"
    )
    status: str = Field(
        description="Current status of the notification"
    )
    created_at: datetime = Field(
        description="Timestamp when the notification was created"
    )
    delivered_at: Optional[datetime] = Field(
        None, description="Timestamp when the notification was delivered"
    )
    read_at: Optional[datetime] = Field(
        None, description="Timestamp when the notification was read"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the notification"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "subject": "Important Clinical Update",
                "message": "Please review the patient's updated care plan.",
                "recipients": ["user-123", "user-456"],
                "priority": "HIGH",
                "channel": "APP",
                "status": "DELIVERED",
                "created_at": "2023-01-01T12:00:00Z",
                "delivered_at": "2023-01-01T12:01:00Z",
                "read_at": None,
                "metadata": {"patient_id": "patient-789", "care_plan_id": "plan-101"}
            }
        }


class NotificationDispatchResult(BaseModel):
    """Result of a notification dispatch operation."""
    status: str = Field(
        description="Status of the dispatch operation (success, failure, partial_failure)"
    )
    notification_id: str = Field(
        description="ID of the dispatched notification"
    )
    channels_dispatched: List[str] = Field(
        description="List of channels the notification was dispatched through"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="List of errors encountered during dispatch, if any"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "notification_id": "550e8400-e29b-41d4-a716-446655440000",
                "channels_dispatched": ["APP"],
                "errors": []
            }
        }


class NotificationBatchResult(BaseModel):
    """Result of a batch notification operation."""
    total_notifications: int = Field(
        description="Total number of notifications processed"
    )
    successful: int = Field(
        description="Number of successfully sent notifications"
    )
    failed: int = Field(
        description="Number of failed notifications"
    )
    notification_ids: List[str] = Field(
        description="List of created notification IDs"
    )
    errors: Dict[str, str] = Field(
        default_factory=dict,
        description="Map of notification IDs to error messages for failed notifications"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total_notifications": 2,
                "successful": 1,
                "failed": 1,
                "notification_ids": ["550e8400-e29b-41d4-a716-446655440000", "550e8400-e29b-41d4-a716-446655440001"],
                "errors": {"550e8400-e29b-41d4-a716-446655440001": "Invalid recipient ID"}
            }
        }
