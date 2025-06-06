"""
MOSS Adapter for SYLVA-WREN Integration

This module provides a bridge between the MOSS crisis detection system
and the SYLVA-WREN emotional wellness coordinator. It handles:
- Crisis classification and severity assessment
- Detection threshold management
- Prompt template generation
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple, Union
import logging
from datetime import datetime
import uuid

from pydantic import BaseModel, Field, ConfigDict

try:
    from symbolic.moss.crisis_classifier import (
        CrisisClassifier,
        CrisisSeverity, 
        RiskDomain,
        RiskAssessment,
        CrisisContext
    )
    from symbolic.moss.detection_thresholds import DetectionThresholds
    from symbolic.moss.prompt_templates import (
        MOSSPromptTemplates,
        PromptCategory, 
        CommunicationChannel
    )
    from structured_logging.phi_logger import log_phi_access
    MOSS_AVAILABLE = True
except ImportError:
    MOSS_AVAILABLE = False

from structured_logging import get_logger
from integration.models import (
    EmotionalInput, 
    ProcessedEmotionalState, 
    CrisisAssessment
)


logger = get_logger(__name__)


class MOSSAdapter:
    """
    Adapter that bridges MOSS crisis detection with SYLVA-WREN coordinator.
    
    This adapter:
    1. Translates SYLVA-WREN data to MOSS format
    2. Processes emotional inputs through MOSS crisis classifier
    3. Manages detection thresholds for different population groups
    4. Generates appropriate crisis intervention content
    5. Ensures all processing is logged for HIPAA compliance
    """
    
    def __init__(self, enable_cache: bool = True):
        """
        Initialize the MOSS adapter with required components.
        
        Args:
            enable_cache: Whether to enable the internal caching system
        """
        self._logger = get_logger(f"{__name__}.MOSSAdapter")
        
        if not MOSS_AVAILABLE:
            self._logger.warning("MOSS components not available - adapter will operate in limited mode")
            self.crisis_classifier = None
            self.detection_thresholds = None
            self.prompt_templates = None
            return
            
        # Initialize MOSS components
        try:
            self.crisis_classifier = CrisisClassifier()
            self.detection_thresholds = DetectionThresholds()
            self.prompt_templates = MOSSPromptTemplates()
            self._logger.info("MOSS adapter initialized with all components")
        except Exception as e:
            self._logger.error(f"Failed to initialize MOSS components: {e}")
            self.crisis_classifier = None
            self.detection_thresholds = None
            self.prompt_templates = None
            
        # Cache for quick lookups (limited size, recent results only)
        self._enable_cache = enable_cache
        self._assessment_cache = {}
            
    async def assess_crisis_risk(
            self, 
            emotional_input: EmotionalInput,
            user_id: str,
            user_context: Optional[Dict[str, Any]] = None
        ) -> CrisisAssessment:
        """
        Assess crisis risk from emotional input using MOSS crisis classifier.
        
        Args:
            emotional_input: User's emotional input to analyze
            user_id: Identifier for the user
            user_context: Additional user context (demographics, history, etc.)
            
        Returns:
            Crisis assessment with severity level and suggested interventions
        """
        if not MOSS_AVAILABLE or not self.crisis_classifier:
            # Return safe default assessment if MOSS is unavailable
            return CrisisAssessment(
                level=0,  # Lowest severity
                confidence=0.5,
                risk_factors=[],
                suggested_interventions=["refer_to_human"],
                detection_time=datetime.utcnow()
            )
            
        # Check cache for recent assessment if enabled
        cache_key = f"{user_id}:{hash(emotional_input.text)}"
        if self._enable_cache and cache_key in self._assessment_cache:
            self._logger.debug(f"Returning cached crisis assessment for user {user_id}")
            return self._assessment_cache[cache_key]
            
        # Log PHI access for crisis assessment
        await log_phi_access(
            user_id=user_id,
            action="crisis_assessment",
            system_component="MOSSAdapter",
            access_purpose="crisis_detection",
            data_elements=["emotional_text", "emotional_state"]
        )
            
        # Build MOSS context from user information
        context = self._build_crisis_context(emotional_input, user_context)
        
        # Get appropriate thresholds for this user
        thresholds = await self._get_detection_thresholds(user_id, user_context)
            
        try:
            # Perform crisis classification with MOSS
            risk_assessment = await self.crisis_classifier.assess_risk(
                text=emotional_input.text,
                emotional_indicators=emotional_input.metadata.get("emotional_indicators", []),
                context=context,
                detection_thresholds=thresholds
            )
            
            # Map MOSS risk assessment to coordinator's crisis assessment format
            crisis_assessment = self._map_to_crisis_assessment(risk_assessment)
            
            # Cache the result if enabled
            if self._enable_cache:
                self._assessment_cache[cache_key] = crisis_assessment
                
                # Limit cache size to prevent memory issues
                if len(self._assessment_cache) > 1000:
                    # Remove oldest items when cache gets too large
                    oldest_keys = list(self._assessment_cache.keys())[:100]
                    for key in oldest_keys:
                        del self._assessment_cache[key]
                
            return crisis_assessment
            
        except Exception as e:
            self._logger.error(f"Crisis assessment failed: {e}")
            # Return safe fallback assessment
            return CrisisAssessment(
                level=0,  # Lowest severity but flag for review
                confidence=0.1,
                risk_factors=["assessment_error"],
                suggested_interventions=["refer_to_human"],
                detection_time=datetime.utcnow()
            )
    
    def _build_crisis_context(
            self, 
            emotional_input: EmotionalInput,
            user_context: Optional[Dict[str, Any]]
        ) -> CrisisContext:
        """Build MOSS crisis context from user data."""
        context = {}
        
        # Extract demographic information if available
        if user_context:
            context["age_group"] = user_context.get("age_group")
            context["gender"] = user_context.get("gender")
            context["location"] = user_context.get("location")
            context["previous_crises"] = user_context.get("previous_crises", [])
            context["medical_conditions"] = user_context.get("medical_conditions", [])
            
        # Add metadata from emotional input
        if emotional_input.metadata:
            context["session_length"] = emotional_input.metadata.get("session_length")
            context["time_of_day"] = emotional_input.metadata.get("time_of_day")
            context["device_type"] = emotional_input.metadata.get("device_type")
            context["interaction_history"] = emotional_input.metadata.get("interaction_history", [])
        
        # Create MOSS CrisisContext
        try:
            from symbolic.moss.crisis_classifier import CrisisContext
            return CrisisContext(**context)
        except:
            # Fallback if MOSS is unavailable
            return context
    
    async def _get_detection_thresholds(
            self, 
            user_id: str, 
            user_context: Optional[Dict[str, Any]]
        ) -> Dict[str, float]:
        """Get appropriate detection thresholds for the user."""
        if not MOSS_AVAILABLE or not self.detection_thresholds:
            # Return default thresholds if MOSS is unavailable
            return {"suicidal": 0.5, "self_harm": 0.5, "violent": 0.5}
            
        try:
            # Get population group from user context
            population_group = None
            clinical_history = None
            
            if user_context:
                population_group = user_context.get("population_group")
                clinical_history = user_context.get("clinical_history")
                
            # Get thresholds from MOSS detection thresholds system
            thresholds = await self.detection_thresholds.get_thresholds_for_user(
                user_id=user_id,
                population_group=population_group,
                clinical_history=clinical_history
            )
            
            return thresholds
            
        except Exception as e:
            self._logger.error(f"Error getting detection thresholds: {e}")
            # Return safe default thresholds
            return {"suicidal": 0.5, "self_harm": 0.5, "violent": 0.5}
    
    def _map_to_crisis_assessment(self, risk_assessment: RiskAssessment) -> CrisisAssessment:
        """Map MOSS risk assessment to coordinator's crisis assessment format."""
        # Extract severity level from MOSS assessment
        severity_level = risk_assessment.severity.value if hasattr(risk_assessment, "severity") else 0
        
        # Extract risk factors
        risk_factors = []
        if hasattr(risk_assessment, "risk_domains"):
            for domain in risk_assessment.risk_domains:
                if domain.score > 0.3:  # Only include significant factors
                    risk_factors.append(domain.domain)
        
        # Extract interventions
        interventions = []
        if hasattr(risk_assessment, "recommended_interventions"):
            interventions = risk_assessment.recommended_interventions
        elif severity_level >= 4:
            interventions = ["immediate_safety_check", "refer_to_crisis_services"]
        elif severity_level >= 2:
            interventions = ["safety_resources", "supportive_response"]
        else:
            interventions = ["continue_monitoring"]
            
        # Create coordinator-compatible crisis assessment
        return CrisisAssessment(
            level=severity_level,
            confidence=risk_assessment.confidence if hasattr(risk_assessment, "confidence") else 0.5,
            risk_factors=risk_factors,
            suggested_interventions=interventions,
            detection_time=datetime.utcnow()
        )
        
    async def generate_crisis_response(
            self,
            crisis_assessment: CrisisAssessment,
            user_name: Optional[str] = None
        ) -> Optional[str]:
        """
        Generate appropriate crisis response using MOSS prompt templates.
        
        Args:
            crisis_assessment: The crisis assessment
            user_name: Optional user name for personalization
            
        Returns:
            Generated response text or None if unavailable
        """
        if not MOSS_AVAILABLE or not self.prompt_templates:
            return None
            
        try:
            # Map severity level to MOSS CrisisSeverity
            from symbolic.moss.crisis_classifier import CrisisSeverity
            severity_levels = list(CrisisSeverity)
            severity = severity_levels[min(crisis_assessment.level, len(severity_levels)-1)]
            
            # Map risk factors to MOSS RiskDomain
            from symbolic.moss.crisis_classifier import RiskDomain
            risk_domains = []
            for factor in crisis_assessment.risk_factors:
                try:
                    risk_domains.append(RiskDomain(factor))
                except ValueError:
                    # Skip factors that don't map to MOSS RiskDomain
                    pass
            
            # Generate appropriate prompt from MOSS templates
            generated_prompt = await self.prompt_templates.generate_prompt(
                severity=severity,
                risk_domains=risk_domains,
                channel=CommunicationChannel.CHAT,
                user_name=user_name
            )
            
            if generated_prompt:
                return generated_prompt.generated_content
                
        except Exception as e:
            self._logger.error(f"Error generating crisis response: {e}")
            
        return None


# Singleton instance for convenience
_moss_adapter = None

def get_moss_adapter() -> MOSSAdapter:
    """Get the global MOSS adapter instance."""
    global _moss_adapter
    if _moss_adapter is None:
        _moss_adapter = MOSSAdapter()
    return _moss_adapter
