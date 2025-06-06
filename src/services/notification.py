"""
Notification service for the Emotional Wellness API.

This module provides services for creating and dispatching notifications
through various channels (app, email, SMS) to users and clinical staff.
"""

import enum
import uuid
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..structured_logging import get_logger
from ..observability import record_span, ComponentName
from ..models.user import User, UserRole
from ..models.notification import Notification, NotificationChannel, NotificationPriority, NotificationStatus


# Configure logger
logger = get_logger(__name__)


class NotificationService:
    """
    Service for handling notifications in the Emotional Wellness system.
    
    Provides methods for creating, dispatching, and managing notifications
    to various recipients through different channels.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize the notification service.
        
        Args:
            session: SQLAlchemy async session for database access
        """
        self.session = session
        self._logger = get_logger(f"{__name__}.NotificationService")
    
    @record_span("notification.create_notification", ComponentName.NOTIFICATION)
    async def create_notification(
        self,
        recipients: List[str],
        subject: str,
        message: str,
        priority: str = "NORMAL",
        channel: str = "APP",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """
        Create a new notification for the specified recipients.
        
        Args:
            recipients: List of recipient user IDs
            subject: Notification subject
            message: Notification message
            priority: Priority level (LOW, NORMAL, HIGH, URGENT)
            channel: Notification channel (APP, EMAIL, SMS)
            metadata: Optional additional data for the notification
            
        Returns:
            Created Notification object
        """
        if not recipients:
            raise ValueError("Recipients list cannot be empty")
        
        # Validate priority and channel
        try:
            priority_enum = NotificationPriority[priority]
            channel_enum = NotificationChannel[channel]
        except KeyError:
            raise ValueError(f"Invalid priority ({priority}) or channel ({channel})")
        
        # Create notification
        notification = Notification(
            id=uuid.uuid4(),
            subject=subject,
            message=message,
            recipients=recipients,
            priority=priority_enum,
            channel=channel_enum,
            status=NotificationStatus.PENDING,
            metadata=metadata or {},
            created_at=datetime.utcnow()
        )
        
        # Save to database
        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)
        
        self._logger.info(
            f"Created notification {notification.id}: {priority} priority via {channel}",
            extra={"notification_id": str(notification.id), "recipient_count": len(recipients)}
        )
        
        return notification
    
    @record_span("notification.dispatch_notification", ComponentName.NOTIFICATION)
    async def dispatch_notification(self, notification_id: uuid.UUID) -> Dict[str, Any]:
        """
        Dispatch a notification through its designated channel.
        
        Args:
            notification_id: ID of the notification to dispatch
            
        Returns:
            Dict with dispatch results
        """
        # Retrieve notification
        notification = await self.session.get(Notification, notification_id)
        if not notification:
            raise ValueError(f"Notification {notification_id} not found")
        
        if notification.status != NotificationStatus.PENDING:
            return {
                "status": "skipped",
                "message": f"Notification already in status {notification.status}",
                "channels_dispatched": []
            }
        
        # Update status to processing
        notification.status = NotificationStatus.PROCESSING
        await self.session.commit()
        
        channels_dispatched = []
        errors = []
        
        try:
            # Dispatch based on channel
            if notification.channel == NotificationChannel.APP:
                await self._dispatch_app_notification(notification)
                channels_dispatched.append("APP")
                
            elif notification.channel == NotificationChannel.EMAIL:
                await self._dispatch_email_notification(notification)
                channels_dispatched.append("EMAIL")
                
            elif notification.channel == NotificationChannel.SMS:
                await self._dispatch_sms_notification(notification)
                channels_dispatched.append("SMS")
                
            else:
                errors.append(f"Unsupported channel: {notification.channel}")
            
            # Update notification status based on results
            if errors:
                notification.status = NotificationStatus.FAILED
                notification.metadata["errors"] = errors
            else:
                notification.status = NotificationStatus.DELIVERED
                notification.delivered_at = datetime.utcnow()
            
            await self.session.commit()
            
            return {
                "status": "success" if not errors else "partial_failure",
                "notification_id": str(notification_id),
                "channels_dispatched": channels_dispatched,
                "errors": errors
            }
            
        except Exception as e:
            self._logger.error(
                f"Error dispatching notification {notification_id}: {str(e)}",
                exc_info=True
            )
            
            # Update notification status
            notification.status = NotificationStatus.FAILED
            notification.metadata["error"] = str(e)
            await self.session.commit()
            
            return {
                "status": "failure",
                "notification_id": str(notification_id),
                "error": str(e),
                "channels_dispatched": channels_dispatched
            }
    
    async def _dispatch_app_notification(self, notification: Notification) -> None:
        """Dispatch notification to in-app notification center."""
        self._logger.info(
            f"Dispatching in-app notification {notification.id} to {len(notification.recipients)} recipients"
        )
        
        # In a real implementation, this might push to a real-time notification system
        # For now, we'll just mark it as delivered since the database record serves as the app notification
        pass
    
    async def _dispatch_email_notification(self, notification: Notification) -> None:
        """Dispatch notification via email."""
        self._logger.info(
            f"Dispatching email notification {notification.id} to {len(notification.recipients)} recipients"
        )
        
        # Get recipient email addresses
        recipient_emails = []
        for recipient_id in notification.recipients:
            user = await self.session.get(User, recipient_id)
            if user and user.email:
                recipient_emails.append(user.email)
        
        if not recipient_emails:
            raise ValueError("No valid email addresses found for recipients")
        
        # In a real implementation, this would connect to an email service
        # For now, we'll just log it
        self._logger.info(
            f"Would send email to {len(recipient_emails)} recipients: {notification.subject}"
        )
    
    async def _dispatch_sms_notification(self, notification: Notification) -> None:
        """Dispatch notification via SMS."""
        self._logger.info(
            f"Dispatching SMS notification {notification.id} to {len(notification.recipients)} recipients"
        )
        
        # Get recipient phone numbers
        recipient_phones = []
        for recipient_id in notification.recipients:
            user = await self.session.get(User, recipient_id)
            if user and user.phone_number:
                recipient_phones.append(user.phone_number)
        
        if not recipient_phones:
            raise ValueError("No valid phone numbers found for recipients")
        
        # In a real implementation, this would connect to an SMS service
        # For now, we'll just log it
        self._logger.info(
            f"Would send SMS to {len(recipient_phones)} recipients: {notification.subject}"
        )
    
    @record_span("notification.get_clinical_staff", ComponentName.NOTIFICATION)
    async def get_clinical_staff(self) -> List[User]:
        """
        Get all active clinical staff users.
        
        Returns:
            List of User objects
        """
        # Query for users with clinical roles
        query = (
            select(User)
            .where(
                User.role.in_([UserRole.CLINICIAN, UserRole.SUPERVISOR, UserRole.ADMINISTRATOR]),
                User.is_active == True
            )
        )
        
        result = await self.session.execute(query)
        users = result.scalars().all()
        
        return list(users)
    
    @record_span("notification.get_system_admins", ComponentName.NOTIFICATION)
    async def get_system_admins(self) -> List[User]:
        """
        Get all active system administrators.
        
        Returns:
            List of User objects
        """
        # Query for users with admin role
        query = (
            select(User)
            .where(
                User.role == UserRole.ADMINISTRATOR,
                User.is_active == True
            )
        )
        
        result = await self.session.execute(query)
        admins = result.scalars().all()
        
        return list(admins)
    
    @record_span("notification.get_pending_notifications", ComponentName.NOTIFICATION)
    async def get_pending_notifications(self, recipient_id: str) -> List[Notification]:
        """
        Get pending notifications for a specific recipient.
        
        Args:
            recipient_id: User ID of the recipient
            
        Returns:
            List of pending Notification objects
        """
        # Query for notifications where the recipient is included
        query = (
            select(Notification)
            .where(Notification.recipients.contains([recipient_id]))
            .order_by(Notification.created_at.desc())
        )
        
        result = await self.session.execute(query)
        notifications = result.scalars().all()
        
        return list(notifications)
    
    @record_span("notification.mark_as_read", ComponentName.NOTIFICATION)
    async def mark_as_read(self, notification_id: uuid.UUID, user_id: str) -> bool:
        """
        Mark a notification as read by a specific user.
        
        Args:
            notification_id: Notification ID
            user_id: User ID who read the notification
            
        Returns:
            True if successful, False otherwise
        """
        notification = await self.session.get(Notification, notification_id)
        if not notification:
            return False
        
        if user_id not in notification.recipients:
            return False
        
        # In a real implementation, this would update a junction table
        # For our simplified model, we'll track in metadata
        if "read_by" not in notification.metadata:
            notification.metadata["read_by"] = []
            
        if user_id not in notification.metadata["read_by"]:
            notification.metadata["read_by"].append(user_id)
            await self.session.commit()
        
        return True
