"""
MOSS Adapter for SYLVA Integration

This module provides the MOSS (Multi-dimensional Ontological Safety System) adapter
for integration with the SYLVA symbolic processing framework.

Key Features:
- Crisis detection and assessment
- Adaptive threshold management
- HIPAA-compliant audit logging
- Specialized prompt generation
- Safety orchestration
- Real-time intervention triggering
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Union
import json
import hashlib

from pydantic import BaseModel, Field, ConfigDict, validator
from structured_logging import get_logger

# MOSS components
from ..moss.crisis_classifier import (
    CrisisClassifier, CrisisSeverity, RiskDomain, CrisisContext, 
    RiskAssessment, create_crisis_context
)
from ..moss.detection_thresholds import (
    DetectionThresholds, ClinicalSeverity
)
from ..moss.audit_logging import MOSSAuditLogger
from ..moss.prompt_templates import (
    MOSSPromptTemplates, PromptCategory, GeneratedPrompt
)

# SYLVA components
from models.emotional_state import SymbolicMapping, SafetyStatus

logger = get_logger(__name__)

class MOSSInput(BaseModel):
    """Input model for MOSS crisis assessment."""
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    # Required inputs
    text_content: str = Field(..., description="User input text for analysis")
    
    # Optional symbolic data
    symbolic_mapping: Optional[SymbolicMapping] = Field(None, description="CANOPY symbolic analysis")
    
    # User context
    user_id: Optional[str] = Field(None, description="User identifier (will be hashed)")
    session_id: Optional[str] = Field(None, description="Session identifier")
    user_name: Optional[str] = Field(None, description="User's preferred name")
    
    # Crisis context
    time_of_day: str = Field(default="day", description="Time categorization")
    support_available: bool = Field(default=True, description="Support system availability")
    previous_episodes: int = Field(default=0, ge=0, description="Previous crisis episodes")
    therapy_engaged: bool = Field(default=False, description="Currently in therapy")
    current_medications: bool = Field(default=False, description="Currently on medication")
    recent_events: List[str] = Field(default_factory=list, description="Recent life events")
    
    # Processing options
    generate_prompts: bool = Field(default=True, description="Generate intervention prompts")
    enable_audit_logging: bool = Field(default=True, description="Enable audit logging")
    adaptive_thresholds: bool = Field(default=True, description="Use adaptive thresholds")

class MOSSOutput(BaseModel):
    """Output model for MOSS crisis assessment."""
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    # Core assessment results
    assessment: RiskAssessment = Field(..., description="Comprehensive risk assessment")
    safety_status: SafetyStatus = Field(..., description="SYLVA safety status")
    
    # Intervention recommendations
    intervention_prompts: List[GeneratedPrompt] = Field(default_factory=list, description="Generated intervention prompts")
    escalation_required: bool = Field(..., description="Whether escalation is required")
    recommended_actions: List[str] = Field(..., description="Recommended immediate actions")
    
    # Safety planning
    safety_plan_suggested: bool = Field(default=False, description="Whether safety planning is suggested")
    crisis_resources: List[str] = Field(default_factory=list, description="Crisis resource recommendations")
    
    # Audit and compliance
    audit_event_id: Optional[str] = Field(None, description="Audit log event ID")
    compliance_flags: List[str] = Field(default_factory=list, description="Compliance considerations")
    
    # Processing metadata
    processing_time_ms: float = Field(..., ge=0.0, description="Processing time in milliseconds")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence in assessment")
    moss_version: str = Field(default="1.0.0", description="MOSS version used")
    
    # Follow-up recommendations
    follow_up_recommended: bool = Field(default=False, description="Whether follow-up is recommended")
    follow_up_timeframe: Optional[str] = Field(None, description="Recommended follow-up timeframe")

class MOSSAdapter:
    """MOSS adapter for SYLVA integration."""
    
    def __init__(
        self,
        enable_audit_logging: bool = True,
        enable_adaptive_thresholds: bool = True,
        audit_log_directory: str = "logs/moss_audit",
        cache_size: int = 256
    ):
        """Initialize the MOSS adapter."""
        self.enable_audit_logging = enable_audit_logging
        self.enable_adaptive_thresholds = enable_adaptive_thresholds
        self._logger = get_logger(f"{__name__}.MOSSAdapter")
        
        # Initialize MOSS components
        self._crisis_classifier = CrisisClassifier(cache_size=cache_size)
        
        self._threshold_manager = DetectionThresholds(
            adaptation_enabled=enable_adaptive_thresholds,
            cache_size=cache_size
        ) if enable_adaptive_thresholds else None
        
        self._audit_logger = MOSSAuditLogger(
            log_directory=audit_log_directory
        ) if enable_audit_logging else None
        
        self._prompt_templates = MOSSPromptTemplates()
        
        # Processing statistics
        self._processing_stats = {
            "total_assessments": 0,
            "crisis_detections": 0,
            "interventions_triggered": 0,
            "escalations_required": 0,
            "average_processing_time": 0.0
        }
        
        self._logger.info("MOSSAdapter initialized")
    
    async def process(self, moss_input: MOSSInput) -> MOSSOutput:
        """Process input through the complete MOSS pipeline."""
        start_time = datetime.now()
        
        try:
            # Create crisis context
            context = create_crisis_context(
                user_id=moss_input.user_id,
                time_of_day=moss_input.time_of_day,
                support_available=moss_input.support_available,
                therapy_engaged=moss_input.therapy_engaged,
                previous_episodes=moss_input.previous_episodes
            )
            context.current_medications = moss_input.current_medications
            context.recent_events = moss_input.recent_events
            
            # Step 1: Crisis Risk Assessment
            assessment = await self._crisis_classifier.assess_crisis_risk(
                text=moss_input.text_content,
                context=context,
                user_id=moss_input.user_id
            )
            
            # Step 2: Create SYLVA-compatible safety status
            safety_status = self._create_safety_status(assessment)
            
            # Step 3: Generate intervention prompts
            intervention_prompts = []
            if moss_input.generate_prompts:
                intervention_prompts = await self._generate_intervention_prompts(
                    assessment, moss_input.user_name
                )
            
            # Step 4: Determine escalation and recommendations
            escalation_required = assessment.escalation_required
            recommended_actions = assessment.recommendations.copy()
            
            # Step 5: Safety planning assessment
            safety_plan_suggested = self._should_suggest_safety_plan(assessment)
            crisis_resources = self._get_crisis_resources(assessment)
            
            # Step 6: Audit logging
            audit_event_id = None
            if moss_input.enable_audit_logging and self._audit_logger:
                audit_event_id = await self._audit_logger.log_crisis_assessment(
                    assessment_id=assessment.assessment_id,
                    severity=assessment.severity.value,
                    confidence=assessment.confidence,
                    escalation_required=assessment.escalation_required,
                    user_id=moss_input.user_id,
                    session_id=moss_input.session_id,
                    processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000
                )
            
            # Step 7: Follow-up recommendations
            follow_up_recommended, follow_up_timeframe = self._determine_follow_up(assessment)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Create output
            output = MOSSOutput(
                assessment=assessment,
                safety_status=safety_status,
                intervention_prompts=intervention_prompts,
                escalation_required=escalation_required,
                recommended_actions=recommended_actions,
                safety_plan_suggested=safety_plan_suggested,
                crisis_resources=crisis_resources,
                audit_event_id=audit_event_id,
                compliance_flags=self._get_compliance_flags(assessment),
                processing_time_ms=processing_time,
                confidence_score=assessment.confidence,
                follow_up_recommended=follow_up_recommended,
                follow_up_timeframe=follow_up_timeframe
            )
            
            # Update processing statistics
            self._update_processing_stats(output)
            
            # Log intervention if escalation required
            if escalation_required and self._audit_logger:
                await self._audit_logger.log_intervention_triggered(
                    "crisis_escalation", assessment.assessment_id, 
                    moss_input.user_id, moss_input.session_id
                )
            
            return output
            
        except Exception as e:
            self._logger.error(f"Error in MOSS processing: {str(e)}")
            
            # Log error for audit
            if self._audit_logger:
                await self._audit_logger.log_system_error(
                    "moss_processing_error", str(e), "moss_adapter",
                    moss_input.user_id, moss_input.session_id
                )
            
            raise
    
    def _create_safety_status(self, assessment: RiskAssessment) -> SafetyStatus:
        """Create SYLVA-compatible safety status from MOSS assessment."""
        # Map MOSS severity to SYLVA safety level
        severity_to_level = {
            CrisisSeverity.NONE: 0,
            CrisisSeverity.LOW: 1,
            CrisisSeverity.MEDIUM: 2,
            CrisisSeverity.HIGH: 3,
            CrisisSeverity.CRITICAL: 3,
            CrisisSeverity.IMMINENT: 3
        }
        
        safety_level = severity_to_level.get(assessment.severity, 0)
        
        return SafetyStatus(
            level=safety_level,
            risk_score=assessment.urgency_score,
            metaphor_risk=0.0,  # Not applicable for MOSS
            triggers=assessment.primary_concerns,
            timestamp=assessment.created_at,
            recommended_actions=assessment.recommendations
        )
    
    async def _generate_intervention_prompts(
        self, 
        assessment: RiskAssessment, 
        user_name: Optional[str]
    ) -> List[GeneratedPrompt]:
        """Generate appropriate intervention prompts."""
        prompts = []
        
        try:
            # Convert risk domains to enum
            risk_domains = [RiskDomain(domain) for domain in assessment.primary_concerns 
                          if domain in [d.value for d in RiskDomain]]
            
            if not risk_domains:
                risk_domains = [RiskDomain.SUICIDE]  # Default
            
            # Generate primary intervention prompt
            primary_prompt = await self._prompt_templates.generate_prompt(
                severity=assessment.severity,
                risk_domains=risk_domains,
                user_name=user_name
            )
            
            if primary_prompt:
                prompts.append(primary_prompt)
            
            # Generate safety planning prompt if needed
            if assessment.severity in [CrisisSeverity.HIGH, CrisisSeverity.CRITICAL, CrisisSeverity.IMMINENT]:
                safety_prompt = await self._prompt_templates.generate_prompt(
                    severity=assessment.severity,
                    risk_domains=risk_domains,
                    preferred_category=PromptCategory.SAFETY_PLANNING,
                    user_name=user_name
                )
                
                if safety_prompt:
                    prompts.append(safety_prompt)
            
            # Generate emergency response prompt if imminent risk
            if assessment.severity == CrisisSeverity.IMMINENT:
                emergency_prompt = await self._prompt_templates.generate_prompt(
                    severity=assessment.severity,
                    risk_domains=risk_domains,
                    preferred_category=PromptCategory.EMERGENCY_RESPONSE,
                    user_name=user_name
                )
                
                if emergency_prompt:
                    prompts.append(emergency_prompt)
            
            return prompts
            
        except Exception as e:
            self._logger.error(f"Error generating intervention prompts: {str(e)}")
            return []
    
    def _should_suggest_safety_plan(self, assessment: RiskAssessment) -> bool:
        """Determine if safety planning should be suggested."""
        return (
            assessment.severity in [CrisisSeverity.MEDIUM, CrisisSeverity.HIGH, 
                                  CrisisSeverity.CRITICAL, CrisisSeverity.IMMINENT] or
            "suicide" in assessment.primary_concerns or
            "self_harm" in assessment.primary_concerns
        )
    
    def _get_crisis_resources(self, assessment: RiskAssessment) -> List[str]:
        """Get appropriate crisis resources based on assessment."""
        resources = []
        
        # Always include national resources for high severity
        if assessment.severity in [CrisisSeverity.HIGH, CrisisSeverity.CRITICAL, CrisisSeverity.IMMINENT]:
            resources.extend([
                "National Suicide Prevention Lifeline: 988",
                "Crisis Text Line: Text HOME to 741741"
            ])
        
        # Domain-specific resources
        if "substance_abuse" in assessment.primary_concerns:
            resources.append("SAMHSA National Helpline: 1-800-662-4357")
        
        # General mental health resources for lower severity
        if assessment.severity in [CrisisSeverity.LOW, CrisisSeverity.MEDIUM]:
            resources.extend([
                "Psychology Today Therapist Directory",
                "Local community mental health centers"
            ])
        
        return resources
    
    def _get_compliance_flags(self, assessment: RiskAssessment) -> List[str]:
        """Get compliance flags for the assessment."""
        flags = []
        
        # HIPAA compliance flags
        if assessment.escalation_required:
            flags.append("hipaa_emergency_disclosure_authorized")
        
        if assessment.severity in [CrisisSeverity.CRITICAL, CrisisSeverity.IMMINENT]:
            flags.append("hipaa_imminent_danger_protocol")
        
        # Data retention flags
        flags.append("7_year_retention_required")
        
        return flags
    
    def _determine_follow_up(self, assessment: RiskAssessment) -> Tuple[bool, Optional[str]]:
        """Determine follow-up recommendations."""
        if assessment.severity == CrisisSeverity.IMMINENT:
            return True, "2-4 hours"
        elif assessment.severity == CrisisSeverity.CRITICAL:
            return True, "24 hours"
        elif assessment.severity == CrisisSeverity.HIGH:
            return True, "2-3 days"
        elif assessment.severity == CrisisSeverity.MEDIUM:
            return True, "1 week"
        else:
            return False, None
    
    def _update_processing_stats(self, output: MOSSOutput) -> None:
        """Update processing statistics."""
        self._processing_stats["total_assessments"] += 1
        
        if output.assessment.severity in [CrisisSeverity.HIGH, CrisisSeverity.CRITICAL, CrisisSeverity.IMMINENT]:
            self._processing_stats["crisis_detections"] += 1
        
        if output.escalation_required:
            self._processing_stats["escalations_required"] += 1
        
        if len(output.intervention_prompts) > 0:
            self._processing_stats["interventions_triggered"] += 1
        
        # Update average processing time
        current_avg = self._processing_stats["average_processing_time"]
        total_assessments = self._processing_stats["total_assessments"]
        
        self._processing_stats["average_processing_time"] = (
            (current_avg * (total_assessments - 1) + output.processing_time_ms) / total_assessments
        )
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get MOSS processing statistics."""
        stats = self._processing_stats.copy()
        
        # Add component-specific statistics
        if self._prompt_templates:
            stats["prompt_templates"] = self._prompt_templates.get_template_statistics()
        
        return stats


# Convenience functions for direct usage
async def assess_crisis(
    text_content: str,
    user_id: Optional[str] = None,
    user_name: Optional[str] = None,
    time_of_day: str = "day",
    support_available: bool = True,
    therapy_engaged: bool = False
) -> MOSSOutput:
    """Convenience function for crisis assessment."""
    adapter = MOSSAdapter()
    
    moss_input = MOSSInput(
        text_content=text_content,
        user_id=user_id,
        user_name=user_name,
        time_of_day=time_of_day,
        support_available=support_available,
        therapy_engaged=therapy_engaged
    )
    
    return await adapter.process(moss_input)

async def emergency_assessment(
    text_content: str,
    user_id: Optional[str] = None,
    user_name: Optional[str] = None
) -> MOSSOutput:
    """Convenience function for emergency crisis assessment."""
    adapter = MOSSAdapter()
    
    moss_input = MOSSInput(
        text_content=text_content,
        user_id=user_id,
        user_name=user_name,
        time_of_day="emergency",
        support_available=False,  # Assume worst case
        generate_prompts=True,
        enable_audit_logging=True
    )
    
    return await adapter.process(moss_input) 