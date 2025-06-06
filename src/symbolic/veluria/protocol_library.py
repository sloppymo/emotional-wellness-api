"""
VELURIA Protocol Library

This module contains a library of pre-defined, clinically-informed
intervention protocols for various crisis situations. Each protocol is a
structured workflow designed to guide a user towards safety.
"""

from typing import List
from .intervention_protocol import InterventionProtocol, ProtocolStep, InterventionAction, ActionType

# --- Protocol for High-Risk Suicidal Ideation ---

high_risk_suicide_protocol = InterventionProtocol(
    protocol_id="high_risk_suicide_v1",
    name="High-Risk Suicide Intervention Protocol",
    description="A protocol for immediate intervention when a user expresses high-risk suicidal ideation with a plan.",
    trigger_conditions={"severity": "high", "domain": "suicide"},
    initial_step_id="step_1_acknowledge_and_validate",
    steps={
        "step_1_acknowledge_and_validate": ProtocolStep(
            step_id="step_1_acknowledge_and_validate",
            description="Acknowledge the user's pain and validate their feelings directly and empathetically.",
            actions=[
                InterventionAction(action_type=ActionType.LOG_EVENT, parameters={"name": "protocol_started", "details": {"protocol_id": "high_risk_suicide_v1"}}),
                InterventionAction(
                    action_type=ActionType.SEND_MESSAGE,
                    parameters={"content": "Thank you for telling me. It sounds like you are in a lot of pain, and I'm taking what you're saying very seriously."}
                ),
                InterventionAction(
                    action_type=ActionType.SEND_MESSAGE,
                    parameters={"content": "I want to make sure you are safe. Are you able to talk with me for a few minutes?"}
                )
            ],
            next_step_logic={"default": "step_2_assess_immediate_danger"}
        ),
        "step_2_assess_immediate_danger": ProtocolStep(
            step_id="step_2_assess_immediate_danger",
            description="Assess the user's immediate physical safety and intent.",
            actions=[
                InterventionAction(
                    action_type=ActionType.REQUEST_USER_INPUT,
                    parameters={"prompt": "To help me understand, are you thinking of ending your life right now?"}
                ),
                InterventionAction(action_type=ActionType.WAIT_FOR_RESPONSE, parameters={"timeout_seconds": 300})
            ],
            next_step_logic={"user_confirms_immediate_danger": "step_3a_emergency_escalation", "user_denies_immediate_danger": "step_3b_explore_safety", "timeout": "step_escalate_no_response"}
        ),
        "step_3a_emergency_escalation": ProtocolStep(
            step_id="step_3a_emergency_escalation",
            description="Immediately escalate to emergency services.",
            actions=[
                InterventionAction(
                    action_type=ActionType.SEND_MESSAGE,
                    parameters={"content": "Because you've indicated you are in immediate danger, I am connecting you to emergency help. Please call 911 or the National Suicide Prevention Lifeline at 988."}
                ),
                InterventionAction(
                    action_type=ActionType.SUGGEST_RESOURCE,
                    parameters={"resource_type": "emergency_services"}
                ),
                InterventionAction(
                    action_type=ActionType.TRIGGER_ESCALATION,
                    parameters={"level": "critical", "reason": "User confirmed immediate suicidal intent."}
                )
            ],
            next_step_logic={"default": "step_protocol_complete"}
        ),
        "step_3b_explore_safety": ProtocolStep(
            step_id="step_3b_explore_safety",
            description="Explore safety resources and initiate safety planning.",
            actions=[
                InterventionAction(
                    action_type=ActionType.SEND_MESSAGE,
                    parameters={"content": "I'm glad you're still talking with me. Let's think about what can keep you safe right now."}
                ),
                InterventionAction(
                    action_type=ActionType.INITIATE_SAFETY_PLAN
                )
            ],
            next_step_logic={"safety_plan_started": "step_4_safety_planning", "user_refuses": "step_escalate_refusal"}
        ),
        "step_4_safety_planning": ProtocolStep(
            step_id="step_4_safety_planning",
            description="Guide the user through creating a simple safety plan.",
            actions=[
                InterventionAction(
                    action_type=ActionType.REQUEST_USER_INPUT,
                    parameters={"prompt": "Can you think of one thing that could help you feel even a little bit safer right now? It could be anything, big or small."}
                )
            ],
            next_step_logic={"user_provides_idea": "step_5_reinforce_and_close", "no_idea": "step_5_suggest_resources"}
        ),
        "step_5_reinforce_and_close": ProtocolStep(
            step_id="step_5_reinforce_and_close",
            description="Reinforce the user's coping strategy and provide resources.",
            actions=[
                InterventionAction(
                    action_type=ActionType.SEND_MESSAGE,
                    parameters={"content": "That's a great idea. Holding onto that can make a real difference. Please remember you can always reach out to the Crisis Text Line by texting HOME to 741741."}
                ),
                InterventionAction(
                    action_type=ActionType.SUGGEST_RESOURCE,
                    parameters={"resource_type": "crisis_text_line"}
                )
            ],
            next_step_logic={"default": "step_protocol_complete"}
        ),
        "step_5_suggest_resources": ProtocolStep(
            step_id="step_5_suggest_resources",
            description="Provide resources when user cannot identify a coping strategy.",
            actions=[
                InterventionAction(
                    action_type=ActionType.SEND_MESSAGE,
                    parameters={"content": "That's okay. Sometimes it's hard to think of something. A helpful resource is the National Suicide Prevention Lifeline, which you can reach by dialing 988. They are available 24/7."}
                ),
                 InterventionAction(
                    action_type=ActionType.SUGGEST_RESOURCE,
                    parameters={"resource_type": "national_suicide_lifeline"}
                )
            ],
            next_step_logic={"default": "step_protocol_complete"}
        ),
        "step_escalate_no_response": ProtocolStep(
            step_id="step_escalate_no_response",
            description="Escalate if the user stops responding.",
            actions=[
                 InterventionAction(
                    action_type=ActionType.TRIGGER_ESCALATION,
                    parameters={"level": "high", "reason": "User became unresponsive during a high-risk protocol."}
                )
            ],
            next_step_logic={"default": "step_protocol_complete"}
        ),
        "step_escalate_refusal": ProtocolStep(
            step_id="step_escalate_refusal",
            description="Escalate if the user refuses to engage in safety planning.",
            actions=[
                 InterventionAction(
                    action_type=ActionType.TRIGGER_ESCALATION,
                    parameters={"level": "high", "reason": "User refused to engage in safety planning during a high-risk protocol."}
                )
            ],
            next_step_logic={"default": "step_protocol_complete"}
        ),
        "step_protocol_complete": ProtocolStep(
            step_id="step_protocol_complete",
            description="Log the completion of the protocol.",
            actions=[
                InterventionAction(action_type=ActionType.LOG_EVENT, parameters={"name": "protocol_completed", "details": {"protocol_id": "high_risk_suicide_v1"}}),
                InterventionAction(action_type=ActionType.UPDATE_STATE, parameters={"updates": {"status": "completed"}})
            ],
            next_step_logic={}
        )
    }
)

# --- Protocol for Moderate Self-Harm ---

moderate_self_harm_protocol = InterventionProtocol(
    protocol_id="moderate_self_harm_v1",
    name="Moderate Self-Harm Intervention Protocol",
    description="A protocol for users who have urges to self-harm but are not in immediate danger.",
    trigger_conditions={"severity": "medium", "domain": "self_harm"},
    initial_step_id="step_1_validate_and_open",
    steps={
        "step_1_validate_and_open": ProtocolStep(
            step_id="step_1_validate_and_open",
            description="Validate the user's feelings and open a dialogue about their urges.",
            actions=[
                InterventionAction(
                    action_type=ActionType.SEND_MESSAGE,
                    parameters={"content": "It takes a lot of strength to talk about urges to self-harm. Thank you for sharing that with me."}
                ),
                InterventionAction(
                    action_type=ActionType.REQUEST_USER_INPUT,
                    parameters={"prompt": "Can you tell me a little bit about what's bringing up these feelings for you right now?"}
                )
            ],
            next_step_logic={"user_responds": "step_2_introduce_alternatives", "no_response": "step_3_offer_resources"}
        ),
        "step_2_introduce_alternatives": ProtocolStep(
            step_id="step_2_introduce_alternatives",
            description="Introduce the concept of alternative coping strategies.",
            actions=[
                InterventionAction(
                    action_type=ActionType.SEND_MESSAGE,
                    parameters={"content": "That sounds incredibly difficult to hold. Many people find it helpful to have alternatives to self-harm for when the urges get strong. Is that something you'd be open to exploring?"}
                )
            ],
            next_step_logic={"user_agrees": "step_4_explore_alternatives", "user_declines": "step_3_offer_resources"}
        ),
        "step_3_offer_resources": ProtocolStep(
            step_id="step_3_offer_resources",
            description="Offer resources for self-harm support.",
            actions=[
                InterventionAction(
                    action_type=ActionType.SEND_MESSAGE,
                    parameters={"content": "I understand. If you'd like to learn more on your own time, a great resource is the Self-Injury Outreach and Support website. They have information and tools that can help."}
                ),
                 InterventionAction(
                    action_type=ActionType.SUGGEST_RESOURCE,
                    parameters={"resource_type": "self_injury_support"}
                )
            ],
            next_step_logic={"default": "step_protocol_complete"}
        ),
        "step_4_explore_alternatives": ProtocolStep(
            step_id="step_4_explore_alternatives",
            description="Explore specific alternative coping skills.",
            actions=[
                InterventionAction(
                    action_type=ActionType.SEND_MESSAGE,
                    parameters={"content": "One common technique is the 'TIPP' skill: Temperature (splashing cold water on your face), Intense exercise, Paced breathing, and Paired muscle relaxation. Do any of those sound like something you could try?"}
                )
            ],
            next_step_logic={"default": "step_protocol_complete"}
        ),
         "step_protocol_complete": ProtocolStep(
            step_id="step_protocol_complete",
            description="Log the completion of the protocol.",
            actions=[
                InterventionAction(action_type=ActionType.LOG_EVENT, parameters={"name": "protocol_completed", "details": {"protocol_id": "moderate_self_harm_v1"}})
            ],
            next_step_logic={}
        )
    }
)


# --- Master List of All Protocols ---

all_protocols = [
    high_risk_suicide_protocol,
    moderate_self_harm_protocol,
    # Add other protocols here as they are developed
]

def get_protocol_library() -> List[InterventionProtocol]:
    """Returns the master list of all available intervention protocols."""
    return all_protocols