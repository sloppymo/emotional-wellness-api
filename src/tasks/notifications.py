"""
Notification tasks for the Emotional Wellness API.

This module contains Celery tasks for sending notifications to users and 
clinicians based on analysis results, early warnings, and system events.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from celery import Task
import json

from .celery_app import celery_app, TaskStatus
from .clinical_analytics import ProgressTrackingTask
from ..database.session import get_async_session
from ..structured_logging import get_logger
from ..clinical.longitudinal import EarlyWarningLevel
from ..models.user import User
from ..models.notification import NotificationChannel, NotificationPriority

# Configure logger
logger = get_logger(__name__)


@celery_app.task(bind=True, base=ProgressTrackingTask, name='src.tasks.notifications.send_clinical_notification')
def send_clinical_notification(
    self,
    recipient_ids: List[str],
    subject: str,
    message: str,
    priority: str = NotificationPriority.NORMAL.name,
    channel: str = NotificationChannel.APP.name,
    data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Send notifications to clinical staff.
    
    Args:
        recipient_ids: List of recipient user IDs
        subject: Notification subject
        message: Notification message
        priority: Notification priority (LOW, NORMAL, HIGH, URGENT)
        channel: Notification channel (APP, EMAIL, SMS)
        data: Optional additional data for the notification
        
    Returns:
        Dict containing notification results
    """
    try:
        logger.info(f"Sending clinical notification to {len(recipient_ids)} recipients")
        self.update_progress(0, 100, "Preparing notification")
        
        # Run async code in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_send_clinical_notification_async(
            self, recipient_ids, subject, message, priority, channel, data
        ))
        loop.close()
        
        logger.info(f"Clinical notification sent successfully to {len(recipient_ids)} recipients")
        return result
        
    except Exception as e:
        logger.error(f"Error sending clinical notification: {str(e)}", exc_info=True)
        self.update_state(
            state=TaskStatus.FAILURE,
            meta={'error': str(e)}
        )
        raise


async def _send_clinical_notification_async(
    task, recipient_ids, subject, message, priority, channel, data
) -> Dict[str, Any]:
    """Async implementation of clinical notification sending."""
    async with get_async_session() as session:
        from ..services.notification import NotificationService
        notification_service = NotificationService(session)
        
        task.update_progress(20, 100, "Validating recipients")
        
        # Validate recipients
        valid_recipients = []
        for user_id in recipient_ids:
            user = await session.get(User, user_id)
            if user and user.is_active:
                valid_recipients.append(user_id)
        
        if not valid_recipients:
            logger.warning("No valid recipients found for notification")
            return {
                "status": "failure",
                "message": "No valid recipients found",
                "notification_id": None
            }
        
        task.update_progress(50, 100, f"Sending to {len(valid_recipients)} recipients")
        
        # Create notification
        notification = await notification_service.create_notification(
            recipients=valid_recipients,
            subject=subject,
            message=message,
            priority=priority,
            channel=channel,
            metadata=data or {}
        )
        
        task.update_progress(80, 100, "Dispatching via channels")
        
        # Dispatch via appropriate channels
        results = await notification_service.dispatch_notification(notification.id)
        
        task.update_progress(100, 100, "Notification sent")
        
        return {
            "status": "success",
            "notification_id": str(notification.id),
            "recipients": len(valid_recipients),
            "channels_dispatched": results.get("channels_dispatched", []),
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(bind=True, base=ProgressTrackingTask, name='src.tasks.notifications.send_early_warning_notifications')
def send_early_warning_notifications(self, early_warning_scan_id: str) -> Dict[str, Any]:
    """
    Send notifications for early warning scan results.
    
    Args:
        early_warning_scan_id: ID of the early warning scan results
        
    Returns:
        Dict containing notification dispatch results
    """
    try:
        logger.info(f"Processing notifications for early warning scan {early_warning_scan_id}")
        self.update_progress(0, 100, "Retrieving scan results")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_send_early_warning_notifications_async(
            self, early_warning_scan_id
        ))
        loop.close()
        
        logger.info(f"Early warning notifications processed for scan {early_warning_scan_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error sending early warning notifications: {str(e)}", exc_info=True)
        self.update_state(
            state=TaskStatus.FAILURE,
            meta={'error': str(e)}
        )
        raise


async def _send_early_warning_notifications_async(task, early_warning_scan_id) -> Dict[str, Any]:
    """Async implementation of early warning notification sending."""
    async with get_async_session() as session:
        from ..services.notification import NotificationService
        from ..clinical.longitudinal import LongitudinalAnalyzer
        
        notification_service = NotificationService(session)
        longitudinal_analyzer = LongitudinalAnalyzer(session=session)
        
        task.update_progress(20, 100, "Retrieving scan results")
        
        # Get scan results
        scan_results = await longitudinal_analyzer.get_early_warning_scan(early_warning_scan_id)
        if not scan_results:
            raise ValueError(f"Early warning scan {early_warning_scan_id} not found")
        
        # Get clinical staff to notify
        task.update_progress(40, 100, "Identifying clinical staff to notify")
        clinical_staff = await notification_service.get_clinical_staff()
        
        # Group warnings by severity
        high_warnings = []
        moderate_warnings = []
        
        for warning in scan_results.get("warnings", []):
            if warning["warning_status"] == EarlyWarningLevel.HIGH.name.lower():
                high_warnings.append(warning)
            elif warning["warning_status"] == EarlyWarningLevel.MODERATE.name.lower():
                moderate_warnings.append(warning)
        
        notifications_sent = 0
        task.update_progress(60, 100, "Processing high-risk warnings")
        
        # Send high-risk notifications individually
        for warning in high_warnings:
            patient_id = warning["patient_id"]
            patient = await session.get(User, patient_id)
            
            if patient:
                subject = f"HIGH RISK ALERT: Early Warning for {patient.full_name}"
                message = (
                    f"A high-risk early warning has been detected for patient {patient.full_name}. "
                    f"Warning level: {warning['warning_level']}. "
                    f"Warning factors: {', '.join(warning['warning_factors'][:3])}... "
                    f"Please review the patient's status immediately."
                )
                
                # Send high priority notification
                await notification_service.create_notification(
                    recipients=[staff.id for staff in clinical_staff],
                    subject=subject,
                    message=message,
                    priority=NotificationPriority.URGENT.name,
                    channel=NotificationChannel.APP.name,
                    metadata={
                        "warning_id": warning.get("id"),
                        "patient_id": patient_id,
                        "warning_status": warning["warning_status"],
                        "warning_level": warning["warning_level"]
                    }
                )
                notifications_sent += 1
        
        # Send summary notification for moderate risks if any
        task.update_progress(80, 100, "Processing moderate-risk warnings")
        if moderate_warnings:
            subject = f"Moderate Risk Alert: {len(moderate_warnings)} patients require attention"
            message = (
                f"Moderate risk early warnings have been detected for {len(moderate_warnings)} patients. "
                f"Please review the clinical dashboard for details."
            )
            
            await notification_service.create_notification(
                recipients=[staff.id for staff in clinical_staff],
                subject=subject,
                message=message,
                priority=NotificationPriority.HIGH.name,
                channel=NotificationChannel.APP.name,
                metadata={
                    "scan_id": early_warning_scan_id,
                    "moderate_warnings_count": len(moderate_warnings)
                }
            )
            notifications_sent += 1
        
        # Send overall summary notification
        task.update_progress(90, 100, "Sending summary notification")
        summary_subject = f"Early Warning Scan Summary: {scan_results['high_risk_count']} high, {scan_results['moderate_risk_count']} moderate risks"
        summary_message = (
            f"Early warning scan complete. "
            f"Results: {scan_results['high_risk_count']} high-risk patients, {scan_results['moderate_risk_count']} moderate-risk patients "
            f"out of {scan_results['patients_scanned']} patients scanned."
        )
        
        await notification_service.create_notification(
            recipients=[staff.id for staff in clinical_staff],
            subject=summary_subject,
            message=summary_message,
            priority=NotificationPriority.NORMAL.name,
            channel=NotificationChannel.APP.name,
            metadata={
                "scan_id": early_warning_scan_id,
                "scan_date": scan_results.get("scan_date"),
                "high_risk_count": scan_results['high_risk_count'],
                "moderate_risk_count": scan_results['moderate_risk_count'],
                "patients_scanned": scan_results['patients_scanned']
            }
        )
        notifications_sent += 1
        
        task.update_progress(100, 100, "Notifications sent")
        
        return {
            "status": "success",
            "scan_id": early_warning_scan_id,
            "notifications_sent": notifications_sent,
            "high_risk_warnings": len(high_warnings),
            "moderate_risk_warnings": len(moderate_warnings),
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(bind=True, base=ProgressTrackingTask, name='src.tasks.notifications.send_task_completion_notification')
def send_task_completion_notification(
    self,
    task_id: str,
    task_name: str,
    status: str,
    result: Optional[Dict[str, Any]] = None,
    recipient_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Send notification about task completion.
    
    Args:
        task_id: ID of the completed task
        task_name: Name of the task (human-readable)
        status: Task status (success, failure, etc.)
        result: Optional task result data
        recipient_ids: Optional list of recipient IDs (if None, notifies task creator/owner)
        
    Returns:
        Dict containing notification results
    """
    try:
        logger.info(f"Sending task completion notification for task {task_id}")
        self.update_progress(0, 100, "Preparing notification")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_send_task_completion_notification_async(
            self, task_id, task_name, status, result, recipient_ids
        ))
        loop.close()
        
        logger.info(f"Task completion notification sent for task {task_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error sending task completion notification: {str(e)}", exc_info=True)
        self.update_state(
            state=TaskStatus.FAILURE,
            meta={'error': str(e)}
        )
        raise


async def _send_task_completion_notification_async(
    task, task_id, task_name, status, result, recipient_ids
) -> Dict[str, Any]:
    """Async implementation of task completion notification sending."""
    async with get_async_session() as session:
        from ..services.notification import NotificationService
        notification_service = NotificationService(session)
        
        task.update_progress(50, 100, "Creating notification")
        
        # Determine notification priority based on task status
        priority = NotificationPriority.NORMAL.name
        if status == TaskStatus.FAILURE:
            priority = NotificationPriority.HIGH.name
        
        # Create notification subject and message
        subject = f"Task {task_name}: {status.capitalize()}"
        message = f"The task '{task_name}' (ID: {task_id}) has completed with status: {status}."
        
        if status == TaskStatus.SUCCESS and result and isinstance(result, dict):
            # Add summary of successful results
            if "total_patients" in result:
                message += f" Processed {result['total_patients']} patients."
            elif "notifications_sent" in result:
                message += f" Sent {result['notifications_sent']} notifications."
        
        if status == TaskStatus.FAILURE and result and isinstance(result, dict):
            # Add error information
            if "error" in result:
                message += f" Error: {result['error']}"
        
        # If no recipients specified, get system administrators
        if not recipient_ids or not recipient_ids:
            admins = await notification_service.get_system_admins()
            recipient_ids = [admin.id for admin in admins]
        
        if not recipient_ids:
            logger.warning("No recipients found for task notification")
            return {
                "status": "failure",
                "message": "No recipients found",
                "notification_id": None
            }
        
        # Create and send notification
        notification = await notification_service.create_notification(
            recipients=recipient_ids,
            subject=subject,
            message=message,
            priority=priority,
            channel=NotificationChannel.APP.name,
            metadata={
                "task_id": task_id,
                "task_name": task_name,
                "task_status": status,
                "task_result_summary": result
            }
        )
        
        task.update_progress(100, 100, "Notification sent")
        
        return {
            "status": "success",
            "notification_id": str(notification.id),
            "recipients": len(recipient_ids),
            "timestamp": datetime.utcnow().isoformat()
        }
