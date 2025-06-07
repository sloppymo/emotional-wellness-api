"""
VELURIA: Crisis intervention protocol implementation

This module implements the state machine for crisis detection and response
with three progressive intervention levels:
- Level 1: Symbolic grounding - talk them through it
- Level 2: Automated safety protocol - give them resources
- Level 3: Human intervention escalation - get real help involved

basically the "oh shit someone needs help" system
"""

import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

from models.emotional_state import SafetyStatus, InterventionRecord

logger = logging.getLogger(__name__)

class VeluriaState(Enum):
    """Enumeration of VELURIA protocol states - how worried we are"""
    SAFE = 0        # everything's fine
    LEVEL_1 = 1     # mild concern - symbolic grounding
    LEVEL_2 = 2     # moderate concern - automated safety protocol  
    LEVEL_3 = 3     # crisis - human intervention needed
    MONITORING = 4  # post-intervention monitoring


class VeluriaProtocol:
    """VELURIA crisis detection and intervention protocol - the crisis response system"""
    
    def __init__(self):
        """Initialize the VELURIA protocol - set up tracking"""
        # Cache of current states for active users - who's in what state
        self.user_states: Dict[str, VeluriaState] = {}
        # Track intervention records for audit and continuity - what we did for who
        self.intervention_history: Dict[str, List[InterventionRecord]] = {}
        # Crisis team notification function (to be set by application) - how to call for help
        self.notify_crisis_team = None
        
    def register_crisis_team_notifier(self, notify_function):
        """Register a function to notify crisis team for Level 3 interventions - set up the emergency contact"""
        self.notify_crisis_team = notify_function
    
    def execute_protocol(self, 
                       user_id: str, 
                       safety_status: SafetyStatus,
                       additional_context: Optional[Dict[str, Any]] = None) -> InterventionRecord:
        """
        Execute VELURIA protocol based on safety status
        
        this is the main function - decides what to do when someone needs help
        
        Args:
            user_id: Identifier for the user
            safety_status: Safety evaluation from MOSS - how bad is it
            additional_context: Optional context information
            
        Returns:
            InterventionRecord with details about the protocol execution
        """
        logger.info(f"Executing VELURIA protocol for user {user_id} at level {safety_status.level}")
        
        # figure out what state they should be in based on current state and new assessment
        current_state = self.user_states.get(user_id, VeluriaState.SAFE)
        new_state = self._determine_state(current_state, safety_status)
        
        # Record state transition - track where they are
        self.user_states[user_id] = new_state
        
        # Execute appropriate intervention based on state - actually help them
        intervention_record = self._execute_intervention(user_id, new_state, safety_status, additional_context)
        
        # Store intervention record - keep track of what we did
        if user_id not in self.intervention_history:
            self.intervention_history[user_id] = []
        self.intervention_history[user_id].append(intervention_record)
        
        return intervention_record
    
    def _determine_state(self, current_state: VeluriaState, safety_status: SafetyStatus) -> VeluriaState:
        """Determine the new state based on current state and safety status - state machine logic"""
        requested_level = safety_status.level
        
        # State transition logic - the protocol can escalate quickly but recovers gradually
        # once you're in crisis mode, we don't let you drop back down immediately
        if requested_level == 3:
            return VeluriaState.LEVEL_3  # immediate escalation to crisis
        elif requested_level == 2:
            # Can only reduce from LEVEL_3 to LEVEL_2 after an explicit recovery
            if current_state == VeluriaState.LEVEL_3:
                return current_state  # stay in crisis mode
            return VeluriaState.LEVEL_2
        elif requested_level == 1:
            # Can only reduce from higher levels after explicit recovery
            if current_state in (VeluriaState.LEVEL_2, VeluriaState.LEVEL_3):
                return current_state  # don't drop down too fast
            return VeluriaState.LEVEL_1
        else:  # requested_level == 0
            # Only return to SAFE state gradually - step down slowly
            if current_state == VeluriaState.LEVEL_3:
                return VeluriaState.LEVEL_2  # gradual step-down from crisis
            elif current_state == VeluriaState.LEVEL_2:
                return VeluriaState.LEVEL_1  # gradual step-down from moderate
            elif current_state == VeluriaState.LEVEL_1:
                return VeluriaState.SAFE     # finally back to safe
            else:
                return VeluriaState.SAFE
    
    def _execute_intervention(self, 
                           user_id: str, 
                           state: VeluriaState, 
                           safety_status: SafetyStatus,
                           additional_context: Optional[Dict[str, Any]] = None) -> InterventionRecord:
        """Execute intervention actions based on the determined state - actually do something helpful"""
        intervention_id = str(uuid.uuid4())
        timestamp = datetime.now()
        actions_taken = []
        resources_provided = []
        
        # Execute actions based on state - different help for different levels
        if state == VeluriaState.LEVEL_1:
            actions_taken, resources_provided = self._level1_intervention()  # talk them through it
        elif state == VeluriaState.LEVEL_2:
            actions_taken, resources_provided = self._level2_intervention()  # give them resources
        elif state == VeluriaState.LEVEL_3:
            actions_taken, resources_provided = self._level3_intervention(user_id, safety_status, additional_context)  # get real help
        
        # Create and return intervention record - document what we did
        return InterventionRecord(
            id=intervention_id,
            user_id=user_id,
            timestamp=timestamp,
            level=state.value,
            triggers=safety_status.triggers,
            risk_score=safety_status.risk_score,
            actions_taken=actions_taken,
            resources_provided=resources_provided,
            state_before=getattr(self.user_states.get(user_id, VeluriaState.SAFE), "value", 0),
            state_after=state.value
        )
    
    def _level1_intervention(self) -> tuple[List[str], List[str]]:
        """Execute Level 1 intervention: Symbolic grounding - talk them through it with gentle techniques"""
        actions_taken = ["symbolic_grounding", "emotional_acknowledgment"]
        
        resources_provided = [
            "grounding_techniques",      # breathing exercises, 5-4-3-2-1 technique
            "alternative_perspectives",  # reframe their situation
            "symbolic_reflection"        # help them understand their metaphors
        ]
        
        return actions_taken, resources_provided
    
    def _level2_intervention(self) -> tuple[List[str], List[str]]:
        """Execute Level 2 intervention: Automated safety protocol - give them real resources"""
        actions_taken = [
            "safety_resources_provided",     # crisis hotlines, etc
            "grounding_techniques_suggested", # specific techniques
            "support_options_presented"      # who they can talk to
        ]
        
        resources_provided = [
            "crisis_text_line",         # 741741
            "breathing_exercises",      # specific techniques
            "local_support_options",    # therapists, support groups
            "self_care_strategies"      # immediate things they can do
        ]
        
        return actions_taken, resources_provided
    
    def _level3_intervention(self, 
                          user_id: str, 
                          safety_status: SafetyStatus,
                          additional_context: Optional[Dict[str, Any]]) -> tuple[List[str], List[str]]:
        """Execute Level 3 intervention: Human intervention escalation - get real help involved immediately"""
        actions_taken = [
            "crisis_team_notification",              # alert human responders
            "emergency_resources_provided",          # 911, crisis hotlines
            "continued_support_during_transition"    # don't abandon them
        ]
        
        resources_provided = [
            "crisis_hotline_information",            # 988 suicide prevention lifeline
            "emergency_services_contact",            # 911 or local emergency
            "immediate_professional_support_options", # crisis counselors
            "safety_planning_resources"              # help them make a safety plan
        ]
        
        # Notify crisis team if handler is registered - actually call for help
        if self.notify_crisis_team:
            # Sanitize the context to ensure no PHI is transmitted unnecessarily
            # only send what's needed for crisis response
            safe_context = {
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "risk_level": safety_status.level,
                "risk_score": safety_status.risk_score,
                "triggers": safety_status.triggers  # what set off the alarms
            }
            
            if additional_context:
                # Only include safe fields from additional context - no personal info
                safe_fields = ["session_id", "platform", "location_type", "has_support_contact"]
                for field in safe_fields:
                    if field in additional_context:
                        safe_context[field] = additional_context[field]
            
            try:
                self.notify_crisis_team(safe_context)
                actions_taken.append("crisis_team_notification_sent")
                logger.info(f"Crisis team notification sent for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to notify crisis team: {str(e)}")
                actions_taken.append("crisis_team_notification_failed")
        
        return actions_taken, resources_provided
    
    def record_manual_intervention(self, 
                                user_id: str, 
                                intervener_id: str,
                                notes: str,
                                outcome: str) -> InterventionRecord:
        """
        Record a manual intervention by crisis team or clinician
        
        Args:
            user_id: ID of the user who received intervention
            intervener_id: ID of the person who performed intervention
            notes: Clinical notes about the intervention (PHI-sensitive)
            outcome: Outcome of the intervention
            
        Returns:
            InterventionRecord with details about the manual intervention
        """
        intervention_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        # Set user state to monitoring after manual intervention
        self.user_states[user_id] = VeluriaState.MONITORING
        
        # Create intervention record with anonymized notes
        record = InterventionRecord(
            id=intervention_id,
            user_id=user_id,
            timestamp=timestamp,
            level=4,  # Manual intervention level
            triggers=["manual_intervention"],
            risk_score=1.0,  # Default high for manual
            actions_taken=["manual_clinical_intervention"],
            resources_provided=[],  # Clinician determined
            state_before=3,  # Assume was in crisis
            state_after=4,  # Monitoring
            intervener_id=intervener_id,
            outcome=outcome
        )
        
        # Store in history
        if user_id not in self.intervention_history:
            self.intervention_history[user_id] = []
        self.intervention_history[user_id].append(record)
        
        return record
    
    def get_user_state(self, user_id: str) -> VeluriaState:
        """Get the current VELURIA state for a user"""
        return self.user_states.get(user_id, VeluriaState.SAFE)
    
    def get_intervention_history(self, user_id: str) -> List[InterventionRecord]:
        """Get intervention history for a user"""
        return self.intervention_history.get(user_id, [])
    
    def reset_user_state(self, user_id: str) -> None:
        """Reset user to SAFE state (for testing or administrative purposes)"""
        if user_id in self.user_states:
            self.user_states[user_id] = VeluriaState.SAFE
            logger.info(f"Reset VELURIA state for user {user_id}")


# Singleton instance for application-wide use
_instance = None

def get_veluria_protocol():
    """Get or create the singleton instance of VeluriaProtocol"""
    global _instance
    if _instance is None:
        _instance = VeluriaProtocol()
    return _instance
