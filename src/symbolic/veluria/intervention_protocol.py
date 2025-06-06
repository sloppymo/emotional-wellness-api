"""
VELURIA Intervention Protocol Framework

This module defines the core data structures and logic for executing
multi-step crisis intervention protocols. It is the heart of the VELURIA system,
orchestrating responses based on the severity and nature of a crisis.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Awaitable
from enum import Enum
import uuid

from pydantic import BaseModel, Field, ConfigDict
from structured_logging import get_logger

from src.symbolic.moss.processor import MossProcessor, get_moss_processor
from src.symbolic.moss import RiskAssessment, GeneratedPrompt
from .escalation_manager import EscalationManager, EscalationRequest, EscalationLevel, get_default_escalation_manager

logger = get_logger(__name__)

# --- Enums for Protocol State and Actions ---

class ProtocolStatus(str, Enum):
    """Represents the current status of an intervention protocol."""
    NOT_STARTED = "not_started"
    ACTIVE = "active"
    PENDING_USER_RESPONSE = "pending_user_response"
    PENDING_EXTERNAL_ACTION = "pending_external_action"
    ESCALATED = "escalated"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"

class ActionType(str, Enum):
    """Defines the types of actions a protocol can execute."""
    SEND_MESSAGE = "send_message"
    REQUEST_USER_INPUT = "request_user_input"
    SUGGEST_RESOURCE = "suggest_resource"
    INITIATE_SAFETY_PLAN = "initiate_safety_plan"
    TRIGGER_ESCALATION = "trigger_escalation"
    UPDATE_STATE = "update_state"
    WAIT_FOR_RESPONSE = "wait_for_response"
    LOG_EVENT = "log_event"

# --- Core Data Models ---

class InterventionAction(BaseModel):
    """Represents a single action to be taken within a protocol step."""
    action_id: str = Field(default_factory=lambda: f"action-{uuid.uuid4()}")
    action_type: ActionType
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the action, e.g., message content, resource details")
    timeout_seconds: Optional[int] = Field(None, description="Optional timeout for this action")

class ProtocolStep(BaseModel):
    """Represents one step in an intervention protocol."""
    step_id: str = Field(..., description="Unique identifier for the step, e.g., 'step_1_grounding'")
    description: str = Field(..., description="Description of the purpose of this step")
    actions: List[InterventionAction]
    next_step_logic: Dict[str, str] = Field(..., description="Logic for transitioning to the next step, e.g., {'user_confirms': 'step_2', 'timeout': 'escalate'}")

class InterventionProtocol(BaseModel):
    """Defines a complete, multi-step crisis intervention protocol."""
    protocol_id: str
    name: str
    description: str
    trigger_conditions: Dict[str, Any] = Field(..., description="Conditions under which this protocol should be triggered, e.g., {'severity': 'HIGH', 'domain': 'suicide'}")
    steps: Dict[str, ProtocolStep]
    initial_step_id: str
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )

class ProtocolState(BaseModel):
    """Tracks the dynamic state of a running intervention protocol for a user."""
    instance_id: str = Field(default_factory=lambda: f"instance-{uuid.uuid4()}")
    protocol_id: str
    user_id: str
    session_id: str
    status: ProtocolStatus = ProtocolStatus.NOT_STARTED
    current_step_id: str
    history: List[Dict[str, Any]] = Field(default_factory=list, description="Record of executed steps and user responses")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Stateful variables for this protocol instance, e.g., user name, safety contacts")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

# --- Protocol Execution Logic ---

class ProtocolExecutionError(Exception):
    """Custom exception for errors during protocol execution."""
    pass

class VeluriaProtocolExecutor:
    """
    Executes and manages the lifecycle of intervention protocols.
    This is a stateless executor; protocol state is passed in and returned.
    """

    def __init__(self, protocols: List[InterventionProtocol], escalation_manager: Optional[EscalationManager] = None):
        self.protocols = {p.protocol_id: p for p in protocols}
        self.escalation_manager = escalation_manager or get_default_escalation_manager()
        self._action_handlers: Dict[ActionType, Callable[..., Awaitable[Dict[str, Any]]]] = self._register_action_handlers()
        logger.info(f"VeluriaProtocolExecutor initialized with {len(self.protocols)} protocols.")

    def _register_action_handlers(self) -> Dict[ActionType, Callable[..., Awaitable[Dict[str, Any]]]]:
        """Maps action types to their handler methods."""
        return {
            ActionType.SEND_MESSAGE: self._handle_send_message,
            ActionType.REQUEST_USER_INPUT: self._handle_request_user_input,
            ActionType.SUGGEST_RESOURCE: self._handle_suggest_resource,
            ActionType.INITIATE_SAFETY_PLAN: self._handle_initiate_safety_plan,
            ActionType.TRIGGER_ESCALATION: self._handle_trigger_escalation,
            ActionType.LOG_EVENT: self._handle_log_event,
            ActionType.UPDATE_STATE: self._handle_update_state,
            ActionType.WAIT_FOR_RESPONSE: self._handle_wait_for_response,
        }

    def select_protocol(self, assessment: RiskAssessment) -> Optional[InterventionProtocol]:
        """Selects the most appropriate protocol based on a MOSS risk assessment."""
        # This logic can be enhanced to be more sophisticated.
        # For now, it finds the first matching protocol.
        for protocol in self.protocols.values():
            conditions = protocol.trigger_conditions
            severity_match = conditions.get("severity") == assessment.severity.value
            domain_match = conditions.get("domain") in assessment.primary_concerns
            
            if severity_match and domain_match:
                logger.info(f"Selected protocol '{protocol.name}' for assessment {assessment.assessment_id}")
                return protocol
        logger.warning(f"No suitable protocol found for assessment {assessment.assessment_id}")
        return None

    async def start_protocol(self, protocol: InterventionProtocol, assessment: RiskAssessment, user_id: str, session_id: str) -> ProtocolState:
        """Initializes a new state for a selected protocol."""
        initial_step = protocol.steps.get(protocol.initial_step_id)
        if not initial_step:
            raise ProtocolExecutionError(f"Initial step '{protocol.initial_step_id}' not found in protocol '{protocol.protocol_id}'")
            
        state = ProtocolState(
            protocol_id=protocol.protocol_id,
            user_id=user_id,
            session_id=session_id,
            status=ProtocolStatus.ACTIVE,
            current_step_id=protocol.initial_step_id,
            variables={
                "user_id": user_id,
                "session_id": session_id,
                "assessment": assessment.model_dump(),
            },
            expires_at=datetime.utcnow() + timedelta(hours=24) # Protocols expire after 24 hours
        )
        logger.info(f"Starting protocol '{protocol.name}' instance {state.instance_id} for user {user_id}")
        return await self.execute_step(state)

    async def execute_step(self, state: ProtocolState) -> ProtocolState:
        """Executes the actions for the current step in the protocol."""
        protocol = self.protocols.get(state.protocol_id)
        if not protocol:
            raise ProtocolExecutionError(f"Protocol '{state.protocol_id}' not found.")
            
        step = protocol.steps.get(state.current_step_id)
        if not step:
            raise ProtocolExecutionError(f"Step '{state.current_step_id}' not found.")

        logger.info(f"Executing step '{step.step_id}' for instance {state.instance_id}")
        state.history.append({
            "step_id": step.step_id,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "started"
        })

        step_results = []
        for action in step.actions:
            handler = self._action_handlers.get(action.action_type)
            if not handler:
                raise ProtocolExecutionError(f"No handler for action type '{action.action_type}'")
            
            # Pass state and action to the handler
            action_result = await handler(action, state)
            step_results.append(action_result)
        
        # Here, we would update the state based on results and determine the next step.
        # This is simplified for now. The main output is the list of actions for the coordinator to perform.
        state.variables["last_step_results"] = step_results
        state.last_updated_at = datetime.utcnow()
        
        # For actions that require waiting, the status will be updated accordingly.
        if any(r.get("status") == "pending" for r in step_results):
             state.status = ProtocolStatus.PENDING_USER_RESPONSE
        
        state.history[-1]["status"] = "completed"
        state.history[-1]["results"] = step_results
        
        return state

    # --- Action Handlers (Simulated) ---
    # In a real system, these would interact with other services (messaging, DB, etc.)

    async def _handle_send_message(self, action: InterventionAction, state: ProtocolState) -> Dict:
        content = action.parameters.get("content", "").format(**state.variables)
        logger.info(f"ACTION: Send message - '{content}'")
        return {"action": "send_message", "content": content, "status": "completed"}

    async def _handle_request_user_input(self, action: InterventionAction, state: ProtocolState) -> Dict:
        prompt = action.parameters.get("prompt", "").format(**state.variables)
        logger.info(f"ACTION: Request user input - '{prompt}'")
        return {"action": "request_user_input", "prompt": prompt, "status": "pending"}

    async def _handle_suggest_resource(self, action: InterventionAction, state: ProtocolState) -> Dict:
        resource_type = action.parameters.get("resource_type")
        logger.info(f"ACTION: Suggest resource - '{resource_type}'")
        # Logic to fetch actual resource details would go here
        return {"action": "suggest_resource", "resource_type": resource_type, "details": {"name": "National Suicide Prevention Lifeline", "contact": "988"}, "status": "completed"}

    async def _handle_initiate_safety_plan(self, action: InterventionAction, state: ProtocolState) -> Dict:
        logger.info("ACTION: Initiate safety plan")
        # This would trigger a more complex safety planning flow
        return {"action": "initiate_safety_plan", "status": "pending"}

    async def _handle_trigger_escalation(self, action: InterventionAction, state: ProtocolState) -> Dict:
        level_str = action.parameters.get("level", "high")
        level = EscalationLevel(level_str)
        reason = action.parameters.get("reason", "No response from user").format(**state.variables)
        logger.warning(f"ACTION: Trigger escalation - Level: {level}, Reason: {reason}")
        
        if self.escalation_manager:
            escalation_request = EscalationRequest(
                level=level,
                reason=reason,
                user_id=state.user_id,
                session_id=state.session_id,
                protocol_instance_id=state.instance_id,
                supporting_data=state.variables
            )
            await self.escalation_manager.trigger_escalation(escalation_request)
            return {"action": "trigger_escalation", "level": level, "reason": reason, "status": "completed"}
        
        logger.error("Escalation triggered, but no EscalationManager is configured.")
        return {"action": "trigger_escalation", "level": level, "reason": reason, "status": "failed", "error": "EscalationManager not configured."}

    async def _handle_log_event(self, action: InterventionAction, state: ProtocolState) -> Dict:
        event_name = action.parameters.get("name")
        details = action.parameters.get("details", {})
        logger.info(f"ACTION: Log event - '{event_name}', Details: {details}")
        # This would integrate with the MOSS Audit Logger
        return {"action": "log_event", "name": event_name, "status": "completed"}
        
    async def _handle_update_state(self, action: InterventionAction, state: ProtocolState) -> Dict:
        updates = action.parameters.get("updates", {})
        logger.info(f"ACTION: Update state with {updates}")
        state.variables.update(updates)
        return {"action": "update_state", "updated_keys": list(updates.keys()), "status": "completed"}

    async def _handle_wait_for_response(self, action: InterventionAction, state: ProtocolState) -> Dict:
        timeout = action.parameters.get("timeout_seconds", 300)
        logger.info(f"ACTION: Wait for user response (timeout: {timeout}s)")
        return {"action": "wait_for_response", "timeout": timeout, "status": "pending"} 