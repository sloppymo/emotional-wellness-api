"""
MOSS Prompt Templates System

This module provides specialized prompt templates for crisis verification including:
- Crisis assessment validation prompts
- Intervention guidance templates
- Safety planning prompts
- De-escalation conversation starters
- Resource recommendation templates
- Follow-up check templates
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from enum import Enum
import uuid

from pydantic import BaseModel, Field, ConfigDict, validator
from structured_logging import get_logger

from .crisis_classifier import CrisisSeverity, RiskDomain, CrisisContext, RiskAssessment

logger = get_logger(__name__)

class PromptCategory(str, Enum):
    """Categories of crisis intervention prompts."""
    ASSESSMENT_VERIFICATION = "assessment_verification"
    SAFETY_PLANNING = "safety_planning"
    DE_ESCALATION = "de_escalation"
    RESOURCE_GUIDANCE = "resource_guidance"
    FOLLOW_UP = "follow_up"
    EMERGENCY_RESPONSE = "emergency_response"
    THERAPEUTIC_TECHNIQUES = "therapeutic_techniques"

class PromptTone(str, Enum):
    """Tone options for crisis communication."""
    EMPATHETIC = "empathetic"
    DIRECT = "direct"
    SUPPORTIVE = "supportive"
    PROFESSIONAL = "professional"
    GENTLE = "gentle"
    URGENT = "urgent"

class CommunicationChannel(str, Enum):
    """Communication channels for prompt delivery."""
    CHAT = "chat"
    VOICE = "voice"
    TEXT_MESSAGE = "text_message"
    EMAIL = "email"
    IN_PERSON = "in_person"

class PromptTemplate(BaseModel):
    """Individual prompt template for crisis intervention."""
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    template_id: str = Field(..., description="Unique template identifier")
    category: PromptCategory = Field(..., description="Prompt category")
    severity_level: CrisisSeverity = Field(..., description="Target severity level")
    tone: PromptTone = Field(..., description="Communication tone")
    channel: CommunicationChannel = Field(..., description="Target communication channel")
    
    # Template content
    title: str = Field(..., description="Template title")
    content: str = Field(..., description="Template content with placeholders")
    variables: List[str] = Field(default_factory=list, description="Template variables")
    
    # Usage guidelines
    use_cases: List[str] = Field(default_factory=list, description="Appropriate use cases")
    contraindications: List[str] = Field(default_factory=list, description="When not to use")
    follow_up_templates: List[str] = Field(default_factory=list, description="Suggested follow-up templates")
    
    # Metadata
    created_by: str = Field(default="moss_system", description="Template creator")
    clinical_reviewed: bool = Field(default=False, description="Clinical review status")
    effectiveness_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Effectiveness rating")
    usage_count: int = Field(default=0, ge=0, description="Number of times used")
    
    @validator('content')
    def validate_content(cls, v):
        """Validate template content for safety."""
        # Check for potentially harmful content
        harmful_phrases = [
            "end it all", "better off dead", "no hope", "give up"
        ]
        
        content_lower = v.lower()
        for phrase in harmful_phrases:
            if phrase in content_lower:
                raise ValueError(f"Template contains potentially harmful phrase: {phrase}")
        
        return v

class PromptPersonalization(BaseModel):
    """Personalization parameters for prompt generation."""
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    user_name: Optional[str] = Field(None, description="User's preferred name")
    age_group: Optional[str] = Field(None, description="Age group (teen, adult, elder)")
    cultural_background: Optional[str] = Field(None, description="Cultural background")
    communication_preference: Optional[str] = Field(None, description="Communication style preference")
    previous_successful_interventions: List[str] = Field(default_factory=list)
    trigger_words_to_avoid: List[str] = Field(default_factory=list)
    preferred_coping_strategies: List[str] = Field(default_factory=list)

class GeneratedPrompt(BaseModel):
    """Generated prompt ready for delivery."""
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    prompt_id: str = Field(..., description="Unique generated prompt ID")
    template_id: str = Field(..., description="Source template ID")
    generated_content: str = Field(..., description="Final generated content")
    personalization_applied: bool = Field(default=False, description="Whether personalization was applied")
    safety_validated: bool = Field(default=False, description="Safety validation status")
    
    # Context
    severity_level: CrisisSeverity = Field(..., description="Target severity")
    risk_domains: List[str] = Field(default_factory=list, description="Relevant risk domains")
    
    # Delivery info
    channel: CommunicationChannel = Field(..., description="Delivery channel")
    estimated_delivery_time: datetime = Field(default_factory=datetime.now)
    expiry_time: Optional[datetime] = Field(None, description="When prompt expires")
    
    # Tracking
    generated_at: datetime = Field(default_factory=datetime.now)
    delivered: bool = Field(default=False, description="Delivery status")
    response_received: bool = Field(default=False, description="Response received")

class MOSSPromptTemplates:
    """
    Specialized prompt template system for MOSS crisis intervention.
    
    This system provides:
    - Crisis-appropriate prompt generation
    - Personalized communication templates
    - Safety-validated intervention guidance
    - Context-aware response suggestions
    """
    
    def __init__(self):
        """Initialize the MOSS prompt template system."""
        self._logger = get_logger(f"{__name__}.MOSSPromptTemplates")
        
        # Load default templates
        self._templates: Dict[str, PromptTemplate] = {}
        self._load_default_templates()
        
        # Template usage statistics
        self._usage_stats: Dict[str, Dict[str, Any]] = {}
        
        self._logger.info("MOSSPromptTemplates initialized")
    
    def _load_default_templates(self) -> None:
        """Load default crisis intervention templates."""
        
        # Crisis Assessment Verification Templates
        self._add_template(PromptTemplate(
            template_id="assess_verify_immediate",
            category=PromptCategory.ASSESSMENT_VERIFICATION,
            severity_level=CrisisSeverity.IMMINENT,
            tone=PromptTone.URGENT,
            channel=CommunicationChannel.CHAT,
            title="Immediate Crisis Verification",
            content="I'm very concerned about what you've shared. Right now, are you thinking about hurting yourself or ending your life? I need to know so I can help keep you safe.",
            variables=["user_name"],
            use_cases=["imminent_suicide_risk", "immediate_danger"],
            contraindications=["user_in_therapy_session", "professional_present"],
            clinical_reviewed=True
        ))
        
        self._add_template(PromptTemplate(
            template_id="assess_verify_high",
            category=PromptCategory.ASSESSMENT_VERIFICATION,
            severity_level=CrisisSeverity.HIGH,
            tone=PromptTone.EMPATHETIC,
            channel=CommunicationChannel.CHAT,
            title="High Risk Assessment",
            content="It sounds like you're going through something really difficult right now. Can you tell me more about how you've been feeling? I'm here to listen and support you.",
            variables=["user_name", "specific_concern"],
            use_cases=["high_risk_depression", "severe_anxiety", "crisis_escalation"],
            follow_up_templates=["safety_plan_basic", "resource_mental_health"]
        ))
        
        # Safety Planning Templates
        self._add_template(PromptTemplate(
            template_id="safety_plan_immediate",
            category=PromptCategory.SAFETY_PLANNING,
            severity_level=CrisisSeverity.CRITICAL,
            tone=PromptTone.SUPPORTIVE,
            channel=CommunicationChannel.CHAT,
            title="Immediate Safety Planning",
            content="Let's work together to create a safety plan. First, can you remove any items that might be harmful from your immediate area? Then, let's identify someone you can call right now for support.",
            variables=["user_name", "support_person", "safe_location"],
            use_cases=["active_crisis", "safety_planning_needed"],
            follow_up_templates=["follow_up_safety_check", "resource_crisis_hotline"]
        ))
        
        self._add_template(PromptTemplate(
            template_id="safety_plan_coping",
            category=PromptCategory.SAFETY_PLANNING,
            severity_level=CrisisSeverity.MEDIUM,
            tone=PromptTone.SUPPORTIVE,
            channel=CommunicationChannel.CHAT,
            title="Coping Strategy Safety Plan",
            content="When you start feeling overwhelmed, what are some things that have helped you feel better in the past? Let's make a list of healthy coping strategies you can use.",
            variables=["user_name", "coping_strategies", "support_contacts"],
            use_cases=["moderate_risk", "coping_skill_building"],
            follow_up_templates=["follow_up_coping_check"]
        ))
        
        # De-escalation Templates
        self._add_template(PromptTemplate(
            template_id="deescalate_breathing",
            category=PromptCategory.DE_ESCALATION,
            severity_level=CrisisSeverity.HIGH,
            tone=PromptTone.GENTLE,
            channel=CommunicationChannel.CHAT,
            title="Breathing De-escalation",
            content="I can hear that you're really upset right now. Let's try to slow things down together. Can you take a deep breath with me? Breathe in slowly for 4 counts... hold for 4... and breathe out for 6.",
            variables=["user_name"],
            use_cases=["panic_attack", "acute_anxiety", "emotional_overwhelm"],
            follow_up_templates=["deescalate_grounding", "assess_verify_high"]
        ))
        
        self._add_template(PromptTemplate(
            template_id="deescalate_grounding",
            category=PromptCategory.DE_ESCALATION,
            severity_level=CrisisSeverity.MEDIUM,
            tone=PromptTone.GENTLE,
            channel=CommunicationChannel.CHAT,
            title="Grounding Technique",
            content="Let's try a grounding exercise to help you feel more present. Can you tell me 5 things you can see around you, 4 things you can touch, 3 things you can hear, 2 things you can smell, and 1 thing you can taste?",
            variables=["user_name"],
            use_cases=["anxiety", "dissociation", "overwhelm"],
            follow_up_templates=["assess_feeling_check"]
        ))
        
        # Resource Guidance Templates
        self._add_template(PromptTemplate(
            template_id="resource_crisis_hotline",
            category=PromptCategory.RESOURCE_GUIDANCE,
            severity_level=CrisisSeverity.CRITICAL,
            tone=PromptTone.PROFESSIONAL,
            channel=CommunicationChannel.CHAT,
            title="Crisis Hotline Information",
            content="I want to make sure you have immediate support available. The National Suicide Prevention Lifeline is available 24/7 at 988. You can also text 'HELLO' to 741741 for the Crisis Text Line. Would you like me to help you contact them now?",
            variables=["user_location", "local_resources"],
            use_cases=["immediate_crisis", "suicide_risk", "emergency_support_needed"],
            clinical_reviewed=True
        ))
        
        self._add_template(PromptTemplate(
            template_id="resource_professional_help",
            category=PromptCategory.RESOURCE_GUIDANCE,
            severity_level=CrisisSeverity.MEDIUM,
            tone=PromptTone.SUPPORTIVE,
            channel=CommunicationChannel.CHAT,
            title="Professional Help Resources",
            content="It sounds like talking to a mental health professional could be really helpful for you. I can help you find therapists in your area or provide information about online therapy options. What feels most comfortable for you?",
            variables=["user_location", "insurance_info", "therapy_preferences"],
            use_cases=["therapy_referral", "ongoing_support_needed"],
            follow_up_templates=["follow_up_appointment_reminder"]
        ))
        
        # Follow-up Templates
        self._add_template(PromptTemplate(
            template_id="follow_up_safety_check",
            category=PromptCategory.FOLLOW_UP,
            severity_level=CrisisSeverity.HIGH,
            tone=PromptTone.EMPATHETIC,
            channel=CommunicationChannel.CHAT,
            title="Safety Check Follow-up",
            content="Hi {user_name}, I wanted to check in and see how you're doing today. Are you feeling safer than you were yesterday? Is there anything you need right now?",
            variables=["user_name", "previous_session_date"],
            use_cases=["post_crisis_follow_up", "safety_monitoring"],
            follow_up_templates=["assess_verify_high", "resource_professional_help"]
        ))
        
        # Emergency Response Templates
        self._add_template(PromptTemplate(
            template_id="emergency_911",
            category=PromptCategory.EMERGENCY_RESPONSE,
            severity_level=CrisisSeverity.IMMINENT,
            tone=PromptTone.URGENT,
            channel=CommunicationChannel.CHAT,
            title="Emergency Services Alert",
            content="I'm very concerned about your immediate safety. I strongly encourage you to call 911 or go to your nearest emergency room right away. If you can't do that, please call 988 (Suicide & Crisis Lifeline) immediately. You don't have to go through this alone.",
            variables=["user_location", "emergency_contacts"],
            use_cases=["imminent_danger", "suicide_plan_with_means", "psychotic_break"],
            clinical_reviewed=True
        ))
        
        # Therapeutic Technique Templates
        self._add_template(PromptTemplate(
            template_id="therapy_thought_challenging",
            category=PromptCategory.THERAPEUTIC_TECHNIQUES,
            severity_level=CrisisSeverity.MEDIUM,
            tone=PromptTone.SUPPORTIVE,
            channel=CommunicationChannel.CHAT,
            title="Thought Challenging",
            content="I hear you saying {negative_thought}. Let's examine this thought together. What evidence do you have that this thought is true? What evidence do you have that it might not be completely accurate?",
            variables=["user_name", "negative_thought", "evidence_for", "evidence_against"],
            use_cases=["cognitive_distortions", "negative_thinking", "depression"],
            follow_up_templates=["therapy_alternative_thoughts"]
        ))
    
    def _add_template(self, template: PromptTemplate) -> None:
        """Add a template to the system."""
        self._templates[template.template_id] = template
        self._usage_stats[template.template_id] = {
            "usage_count": 0,
            "effectiveness_scores": [],
            "last_used": None
        }
    
    async def generate_prompt(
        self,
        severity: CrisisSeverity,
        risk_domains: List[RiskDomain],
        preferred_category: Optional[PromptCategory] = None,
        channel: CommunicationChannel = CommunicationChannel.CHAT,
        user_name: Optional[str] = None
    ) -> Optional[GeneratedPrompt]:
        """Generate an appropriate prompt for the given crisis situation."""
        try:
            # Find suitable templates
            candidate_templates = self._find_suitable_templates(
                severity, risk_domains, preferred_category, channel
            )
            
            if not candidate_templates:
                self._logger.warning(f"No suitable templates found for severity {severity}")
                return None
            
            # Select best template
            selected_template = self._select_best_template(candidate_templates)
            
            # Generate personalized content
            generated_content = self._generate_content(selected_template, user_name)
            
            # Validate safety
            if not self._validate_safety(generated_content, severity):
                self._logger.error("Generated content failed safety validation")
                return None
            
            # Create generated prompt
            prompt = GeneratedPrompt(
                prompt_id=str(uuid.uuid4())[:12],
                template_id=selected_template.template_id,
                generated_content=generated_content,
                personalization_applied=user_name is not None,
                safety_validated=True,
                severity_level=severity,
                risk_domains=[domain.value for domain in risk_domains],
                channel=channel,
                expiry_time=datetime.now() + timedelta(hours=24)
            )
            
            # Update usage statistics
            self._update_usage_stats(selected_template.template_id)
            
            return prompt
            
        except Exception as e:
            self._logger.error(f"Error generating prompt: {str(e)}")
            return None
    
    def _find_suitable_templates(
        self,
        severity: CrisisSeverity,
        risk_domains: List[RiskDomain],
        preferred_category: Optional[PromptCategory],
        channel: CommunicationChannel
    ) -> List[PromptTemplate]:
        """Find templates suitable for the given criteria."""
        candidates = []
        
        for template in self._templates.values():
            # Check severity match
            severity_match = (
                template.severity_level == severity or
                self._is_compatible_severity(template.severity_level, severity)
            )
            
            # Check channel compatibility
            channel_match = template.channel == channel or template.channel == CommunicationChannel.CHAT
            
            # Check category preference
            category_match = (
                preferred_category is None or 
                template.category == preferred_category
            )
            
            if severity_match and channel_match and category_match:
                candidates.append(template)
        
        return candidates
    
    def _is_compatible_severity(
        self, 
        template_severity: CrisisSeverity, 
        target_severity: CrisisSeverity
    ) -> bool:
        """Check if template severity is compatible with target severity."""
        severity_order = [
            CrisisSeverity.NONE,
            CrisisSeverity.LOW,
            CrisisSeverity.MEDIUM,
            CrisisSeverity.HIGH,
            CrisisSeverity.CRITICAL,
            CrisisSeverity.IMMINENT
        ]
        
        try:
            template_idx = severity_order.index(template_severity)
            target_idx = severity_order.index(target_severity)
            
            # Allow templates up to one level different
            return abs(template_idx - target_idx) <= 1
        except ValueError:
            return False
    
    def _select_best_template(self, candidates: List[PromptTemplate]) -> PromptTemplate:
        """Select the best template from candidates."""
        if len(candidates) == 1:
            return candidates[0]
        
        # Score templates based on various factors
        scored_templates = []
        
        for template in candidates:
            score = 0.0
            
            # Effectiveness score
            if template.effectiveness_score:
                score += template.effectiveness_score * 0.4
            
            # Clinical review bonus
            if template.clinical_reviewed:
                score += 0.3
            
            # Usage frequency (moderate usage is preferred)
            usage_count = self._usage_stats[template.template_id]["usage_count"]
            if 10 <= usage_count <= 100:
                score += 0.3
            elif usage_count > 0:
                score += 0.1
            
            scored_templates.append((score, template))
        
        # Return highest scoring template
        scored_templates.sort(key=lambda x: x[0], reverse=True)
        return scored_templates[0][1]
    
    def _generate_content(
        self,
        template: PromptTemplate,
        user_name: Optional[str]
    ) -> str:
        """Generate personalized content from template."""
        content = template.content
        
        # Apply personalization
        if user_name:
            content = content.replace("{user_name}", user_name)
        
        # Remove any unreplaced placeholders
        content = self._clean_placeholders(content)
        
        return content
    
    def _clean_placeholders(self, content: str) -> str:
        """Remove unreplaced placeholders from content."""
        import re
        # Remove common placeholder patterns
        content = re.sub(r'\{[^}]+\}', '', content)
        content = re.sub(r'\s+', ' ', content)  # Clean up extra spaces
        return content.strip()
    
    def _validate_safety(self, content: str, severity: CrisisSeverity) -> bool:
        """Validate generated content for safety."""
        content_lower = content.lower()
        
        # Check for harmful phrases
        harmful_phrases = [
            "end it all", "better off dead", "no hope", "give up",
            "nothing to live for", "hopeless"
        ]
        
        for phrase in harmful_phrases:
            if phrase in content_lower:
                return False
        
        # Ensure appropriate urgency for high severity
        if severity in [CrisisSeverity.CRITICAL, CrisisSeverity.IMMINENT]:
            required_elements = ["help", "support", "safe"]
            if not any(element in content_lower for element in required_elements):
                return False
        
        return True
    
    def _update_usage_stats(self, template_id: str) -> None:
        """Update template usage statistics."""
        if template_id in self._usage_stats:
            self._usage_stats[template_id]["usage_count"] += 1
            self._usage_stats[template_id]["last_used"] = datetime.now()
            
            # Update template usage count
            if template_id in self._templates:
                self._templates[template_id].usage_count += 1
    
    def get_template_by_category(self, category: PromptCategory) -> List[PromptTemplate]:
        """Get all templates for a specific category."""
        return [t for t in self._templates.values() if t.category == category]
    
    def get_template_statistics(self) -> Dict[str, Any]:
        """Get template usage statistics."""
        return {
            "total_templates": len(self._templates),
            "usage_stats": self._usage_stats.copy(),
            "most_used": max(
                self._usage_stats.items(), 
                key=lambda x: x[1]["usage_count"]
            )[0] if self._usage_stats else None,
            "clinical_reviewed_count": sum(
                1 for t in self._templates.values() if t.clinical_reviewed
            )
        }


# Convenience functions
async def generate_crisis_prompt(
    severity: CrisisSeverity,
    risk_domains: List[RiskDomain],
    user_name: Optional[str] = None,
    category: Optional[PromptCategory] = None
) -> Optional[GeneratedPrompt]:
    """Convenience function to generate a crisis intervention prompt."""
    template_system = MOSSPromptTemplates()
    
    return await template_system.generate_prompt(
        severity, risk_domains, category, user_name=user_name
    )

async def generate_safety_planning_prompt(
    severity: CrisisSeverity,
    user_name: Optional[str] = None
) -> Optional[GeneratedPrompt]:
    """Convenience function to generate a safety planning prompt."""
    template_system = MOSSPromptTemplates()
    
    return await template_system.generate_prompt(
        severity, 
        [RiskDomain.SUICIDE],  # Default for safety planning
        preferred_category=PromptCategory.SAFETY_PLANNING,
        user_name=user_name
    ) 