"""
VELURIA Adapter

This module provides the adapter interface between the MOSS system
and the VELURIA intervention protocols.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from src.symbolic.moss.processor import get_moss_processor
from src.symbolic.moss import RiskAssessment, CrisisContext
from src.symbolic.veluria.intervention_protocol import (
    InterventionProtocol,
    ProtocolState,
    ProtocolStatus
)
from structured_logging import get_logger

logger = get_logger(__name__)

class VeluriaAdapterRequest(BaseModel):
    """Input to the VELURIA Adapter, primarily the MOSS assessment."""
    assessment: RiskAssessment
    user_id: str
    session_id: str
    user_response: Optional[str] = None # For continuing an existing protocol

class VeluriaAdapterResponse(BaseModel):
    """Output from the VELURIA Adapter."""
    protocol_state: Optional[ProtocolState] = None
    actions: List[Dict[str, Any]] = Field(default_factory=list, description="Actions for the coordinator to execute, e.g., send message.")
    is_protocol_active: bool = False

class VeluriaAdapter:
    """
    Orchestrates crisis intervention protocols based on MOSS assessments.
    """

    def __init__(self):
        # In a real application, the protocol library might be loaded from a database
        # or a configuration service.
        protocols = get_protocol_library()
        self.executor = VeluriaProtocolExecutor(protocols)
        
        # This is a simple in-memory cache for active protocol states.
        # In a production system, this would be a distributed cache like Redis
        # or a database table.
        self._active_protocols: Dict[str, ProtocolState] = {}
        logger.info(f"VeluriaAdapter initialized with {len(protocols)} protocols.")

    async def process_request(self, request: VeluriaAdapterRequest) -> VeluriaAdapterResponse:
        """
        Processes a risk assessment, starting or continuing an intervention protocol.
        """
        # Check if a protocol is already active for this user
        active_state = self._active_protocols.get(request.user_id)

        if active_state:
            logger.info(f"Continuing active protocol '{active_state.protocol_id}' for user {request.user_id}")
            # This is a simplification. Real logic would be more complex.
            # It would involve mapping the user_response to the next step.
            # For now, we don't have the logic to advance the protocol.
            return VeluriaAdapterResponse(
                protocol_state=active_state,
                is_protocol_active=True,
                actions=[] # No new actions until state transition logic is built
            )

        # If no active protocol, see if the assessment triggers a new one
        protocol_to_start = self.executor.select_protocol(request.assessment)

        if not protocol_to_start:
            logger.info(f"No new protocol triggered for user {request.user_id} based on assessment.")
            return VeluriaAdapterResponse()

        # A new protocol is triggered, start it
        logger.info(f"Starting new protocol '{protocol_to_start.name}' for user {request.user_id}")
        
        try:
            new_state = await self.executor.start_protocol(
                protocol=protocol_to_start,
                assessment=request.assessment,
                user_id=request.user_id,
                session_id=request.session_id
            )
            
            # Store the active state
            self._active_protocols[request.user_id] = new_state
            
            actions_to_execute = new_state.variables.get("last_step_results", [])
            
            return VeluriaAdapterResponse(
                protocol_state=new_state,
                is_protocol_active=new_state.status in [ProtocolStatus.ACTIVE, ProtocolStatus.PENDING_USER_RESPONSE],
                actions=actions_to_execute
            )

        except Exception as e:
            logger.error(f"Error starting protocol for user {request.user_id}: {e}", exc_info=True)
            return VeluriaAdapterResponse()

    def get_active_protocol_state(self, user_id: str) -> Optional[ProtocolState]:
        """Retrieves the current state of an active protocol for a user."""
        return self._active_protocols.get(user_id)

    def end_protocol(self, user_id: str) -> None:
        """Manually ends a protocol for a user."""
        if user_id in self._active_protocols:
            logger.info(f"Protocol for user {user_id} has been manually ended.")
            del self._active_protocols[user_id] 