"""
VELURIA Escalation Manager

This module is responsible for handling escalations triggered by intervention
protocols. It manages communication with external entities like on-call
clinicians or emergency services.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, EmailStr

from structured_logging import get_logger

logger = get_logger(__name__)

class ContactMethod(str, Enum):
    """The method to use for contacting an escalation target."""
    EMAIL = "email"
    SMS = "sms"
    PHONE_CALL = "phone_call"
    PAGER = "pager"

class EscalationLevel(str, Enum):
    """The severity level of the escalation."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class EscalationTarget(BaseModel):
    """Represents a person or service to contact during an escalation."""
    name: str
    contact_method: ContactMethod
    contact_details: str # e.g., email address, phone number
    triggers_on_levels: List[EscalationLevel]

class EscalationRequest(BaseModel):
    """A request to trigger an escalation."""
    level: EscalationLevel
    reason: str
    user_id: str
    session_id: str
    protocol_instance_id: str
    supporting_data: Dict[str, Any] = Field(default_factory=dict)


class EscalationManager:
    """
    Manages the process of escalating a crisis to external parties.
    """

    def __init__(self, targets: List[EscalationTarget]):
        self.targets = targets
        logger.info(f"EscalationManager initialized with {len(self.targets)} targets.")

    async def trigger_escalation(self, request: EscalationRequest) -> None:
        """
        Triggers notifications to all relevant targets based on the escalation level.
        """
        logger.warning(
            f"Escalation triggered for user {request.user_id} with level '{request.level}'. "
            f"Reason: {request.reason}"
        )

        for target in self.targets:
            if request.level in target.triggers_on_levels:
                logger.info(f"Notifying target '{target.name}' via {target.contact_method.value}")
                try:
                    await self._send_notification(target, request)
                except Exception as e:
                    logger.error(
                        f"Failed to send notification to target '{target.name}'. Error: {e}",
                        exc_info=True
                    )

    async def _send_notification(self, target: EscalationTarget, request: EscalationRequest) -> None:
        """
        Dispatches the notification based on the contact method.
        This is a placeholder for real communication service integrations.
        """
        subject = f"SYLVA-WREN Escalation: {request.level.value} - User {request.user_id}"
        body = (
            f"Escalation Details:\n"
            f"- User ID: {request.user_id}\n"
            f"- Session ID: {request.session_id}\n"
            f"- Protocol Instance ID: {request.protocol_instance_id}\n"
            f"- Level: {request.level.value}\n"
            f"- Reason: {request.reason}\n\n"
            f"Supporting Data:\n{request.supporting_data}"
        )

        if target.contact_method == ContactMethod.EMAIL:
            await self._send_email(target.contact_details, subject, body)
        elif target.contact_method == ContactMethod.SMS:
            await self._send_sms(target.contact_details, f"{subject}: {request.reason}")
        else:
            logger.warning(f"Contact method '{target.contact_method.value}' is not yet implemented.")

    async def _send_email(self, to_address: EmailStr, subject: str, body: str) -> None:
        """Simulates sending an email. Replace with a real email service."""
        logger.info(f"SIMULATING EMAIL to {to_address}:\nSubject: {subject}\nBody: {body}")
        # In a real implementation:
        # from some_email_client import EmailClient
        # client = EmailClient(api_key="...")
        # await client.send(to=to_address, subject=subject, body=body)
        pass

    async def _send_sms(self, phone_number: str, message: str) -> None:
        """Simulates sending an SMS. Replace with a real SMS service like Twilio."""
        logger.info(f"SIMULATING SMS to {phone_number}: {message}")
        # In a real implementation:
        # from some_sms_client import SMSClient
        # client = SMSClient(account_sid="...", auth_token="...")
        # await client.send(to=phone_number, from_="+15005550006", body=message)
        pass

def get_default_escalation_manager() -> EscalationManager:
    """Creates an escalation manager with a default set of targets."""
    default_targets = [
        EscalationTarget(
            name="On-Call Clinician (Email)",
            contact_method=ContactMethod.EMAIL,
            contact_details="on-call-clinician@sylva-wren.com",
            triggers_on_levels=[EscalationLevel.HIGH]
        ),
        EscalationTarget(
            name="On-Call Clinician (SMS)",
            contact_method=ContactMethod.SMS,
            contact_details="+15551234567",
            triggers_on_levels=[EscalationLevel.CRITICAL]
        ),
        EscalationTarget(
            name="Clinical Supervisor (Audit)",
            contact_method=ContactMethod.EMAIL,
            contact_details="supervisor@sylva-wren.com",
            triggers_on_levels=[EscalationLevel.HIGH, EscalationLevel.CRITICAL]
        ),
    ]
    return EscalationManager(targets=default_targets) 