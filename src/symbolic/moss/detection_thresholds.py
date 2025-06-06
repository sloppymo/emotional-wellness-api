"""
MOSS Detection Thresholds System

This module provides dynamic threshold management for crisis detection including:
- Adaptive threshold adjustment based on user patterns
- Clinical severity calibration
- Context-aware threshold modulation
- Population-based threshold optimization
- Real-time threshold validation
"""

import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from functools import lru_cache
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
import uuid

from pydantic import BaseModel, Field, ConfigDict, validator
from structured_logging import get_logger

from .crisis_classifier import CrisisSeverity, RiskDomain, CrisisContext, RiskAssessment

logger = get_logger(__name__)

class ThresholdType(str, Enum):
    """Types of detection thresholds."""
    STATIC = "static"
    ADAPTIVE = "adaptive"
    CONTEXTUAL = "contextual"
    POPULATION_BASED = "population_based"
    USER_SPECIFIC = "user_specific"

class ClinicalSeverity(str, Enum):
    """Clinical severity mappings for threshold calibration."""
    MINIMAL = "minimal"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    EXTREME = "extreme"

class PopulationGroup(str, Enum):
    """Population groups for threshold optimization."""
    GENERAL = "general"
    ADOLESCENT = "adolescent"
    ELDERLY = "elderly"
    HIGH_RISK = "high_risk"
    CHRONIC_CONDITION = "chronic_condition"
    FIRST_EPISODE = "first_episode"

class ThresholdConfiguration(BaseModel):
    """Configuration for detection thresholds."""
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    config_id: str = Field(..., description="Unique configuration identifier")
    threshold_type: ThresholdType = Field(..., description="Type of threshold system")
    population_group: PopulationGroup = Field(default=PopulationGroup.GENERAL)
    domain_thresholds: Dict[str, Dict[str, float]] = Field(..., description="Thresholds by domain and severity")
    contextual_modifiers: Dict[str, float] = Field(default_factory=dict)
    adaptation_parameters: Dict[str, Any] = Field(default_factory=dict)
    calibration_data: Dict[str, Any] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.now)
    version: str = Field(default="1.0.0")
    
    @validator('domain_thresholds')
    def validate_thresholds(cls, v):
        """Validate threshold structure and values."""
        required_severities = ['low', 'medium', 'high', 'critical', 'imminent']
        for domain, thresholds in v.items():
            for severity, threshold in thresholds.items():
                if severity not in required_severities:
                    raise ValueError(f"Invalid severity level: {severity}")
                if not (0.0 <= threshold <= 1.0):
                    raise ValueError(f"Threshold must be between 0.0 and 1.0: {threshold}")
        return v

class ThresholdAdjustment(BaseModel):
    """Individual threshold adjustment record."""
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    adjustment_id: str = Field(..., description="Unique adjustment identifier")
    user_id: Optional[str] = Field(None, description="User identifier (hashed)")
    domain: RiskDomain = Field(..., description="Risk domain")
    severity_level: ClinicalSeverity = Field(..., description="Severity level")
    original_threshold: float = Field(..., ge=0.0, le=1.0)
    adjusted_threshold: float = Field(..., ge=0.0, le=1.0)
    adjustment_factor: float = Field(..., description="Multiplier applied")
    reason: str = Field(..., description="Reason for adjustment")
    effective_from: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = Field(None, description="When adjustment expires")
    validation_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DetectionThresholds:
    """
    Advanced threshold management system for crisis detection.
    
    This system provides:
    - Dynamic threshold adjustment based on user patterns
    - Population-based threshold optimization
    - Clinical severity calibration
    - Context-aware threshold modulation
    - Real-time validation and adaptation
    """
    
    def __init__(
        self,
        default_config: Optional[ThresholdConfiguration] = None,
        adaptation_enabled: bool = True,
        cache_size: int = 512
    ):
        """Initialize the detection thresholds system."""
        self.adaptation_enabled = adaptation_enabled
        self.cache_size = cache_size
        self._logger = get_logger(f"{__name__}.DetectionThresholds")
        
        # Load default configuration
        self._default_config = default_config or self._create_default_configuration()
        
        # Active configurations by population group
        self._population_configs: Dict[PopulationGroup, ThresholdConfiguration] = {
            PopulationGroup.GENERAL: self._default_config
        }
        
        # User-specific threshold adjustments
        self._user_adjustments: Dict[str, List[ThresholdAdjustment]] = defaultdict(list)
        
        # Threshold performance tracking
        self._performance_metrics: Dict[str, Dict[str, float]] = defaultdict(dict)
        
        # Adaptation history
        self._adaptation_history: deque = deque(maxlen=1000)
        
        # Cache for computed thresholds
        self._threshold_cache: Dict[str, Dict[str, float]] = {}
        
        # Population statistics
        self._population_stats = self._initialize_population_stats()
        
        self._logger.info(f"DetectionThresholds initialized (adaptation: {adaptation_enabled})")
    
    def _create_default_configuration(self) -> ThresholdConfiguration:
        """Create default threshold configuration."""
        default_thresholds = {
            RiskDomain.SUICIDE.value: {
                "low": 0.2,
                "medium": 0.4,
                "high": 0.6,
                "critical": 0.8,
                "imminent": 0.9
            },
            RiskDomain.SELF_HARM.value: {
                "low": 0.25,
                "medium": 0.45,
                "high": 0.65,
                "critical": 0.8,
                "imminent": 0.9
            },
            RiskDomain.VIOLENCE.value: {
                "low": 0.3,
                "medium": 0.5,
                "high": 0.7,
                "critical": 0.85,
                "imminent": 0.95
            },
            RiskDomain.SUBSTANCE_ABUSE.value: {
                "low": 0.3,
                "medium": 0.5,
                "high": 0.7,
                "critical": 0.85,
                "imminent": 0.95
            },
            RiskDomain.TRAUMA.value: {
                "low": 0.35,
                "medium": 0.55,
                "high": 0.7,
                "critical": 0.85,
                "imminent": 0.95
            },
            RiskDomain.EATING_DISORDER.value: {
                "low": 0.35,
                "medium": 0.55,
                "high": 0.7,
                "critical": 0.85,
                "imminent": 0.95
            },
            RiskDomain.NEGLECT.value: {
                "low": 0.4,
                "medium": 0.6,
                "high": 0.75,
                "critical": 0.85,
                "imminent": 0.95
            }
        }
        
        return ThresholdConfiguration(
            config_id="default_v1.0",
            threshold_type=ThresholdType.STATIC,
            domain_thresholds=default_thresholds,
            contextual_modifiers={
                "late_night": 0.9,
                "early_morning": 0.9,
                "weekend": 0.95,
                "holiday": 0.85,
                "no_support": 0.8,
                "therapy_engaged": 1.1,
                "medication_compliant": 1.1
            },
            adaptation_parameters={
                "learning_rate": 0.01,
                "adaptation_window_days": 30,
                "min_samples_for_adaptation": 10,
                "max_adjustment_factor": 0.3
            }
        )
    
    def _initialize_population_stats(self) -> Dict[PopulationGroup, Dict[str, Any]]:
        """Initialize population statistics for threshold optimization."""
        return {
            PopulationGroup.GENERAL: {
                "sample_size": 0,
                "mean_risk_scores": {},
                "threshold_accuracy": {},
                "false_positive_rate": {},
                "false_negative_rate": {},
                "last_updated": datetime.now()
            },
            PopulationGroup.ADOLESCENT: {
                "sample_size": 0,
                "mean_risk_scores": {},
                "threshold_accuracy": {},
                "false_positive_rate": {},
                "false_negative_rate": {},
                "last_updated": datetime.now(),
                "age_range": (13, 18),
                "risk_factors": ["academic_pressure", "social_media", "identity_formation"]
            },
            PopulationGroup.ELDERLY: {
                "sample_size": 0,
                "mean_risk_scores": {},
                "threshold_accuracy": {},
                "false_positive_rate": {},
                "false_negative_rate": {},
                "last_updated": datetime.now(),
                "age_range": (65, 100),
                "risk_factors": ["isolation", "health_decline", "loss_of_independence"]
            },
            PopulationGroup.HIGH_RISK: {
                "sample_size": 0,
                "mean_risk_scores": {},
                "threshold_accuracy": {},
                "false_positive_rate": {},
                "false_negative_rate": {},
                "last_updated": datetime.now(),
                "criteria": ["previous_attempts", "chronic_mental_illness", "substance_abuse"]
            }
        }
    
    async def get_thresholds_for_assessment(
        self,
        user_id: Optional[str] = None,
        context: Optional[CrisisContext] = None,
        population_group: Optional[PopulationGroup] = None
    ) -> Dict[RiskDomain, Dict[str, float]]:
        """Get appropriate thresholds for crisis assessment."""
        try:
            # Determine population group
            target_group = population_group or self._determine_population_group(context)
            
            # Get base configuration
            base_config = self._population_configs.get(target_group, self._default_config)
            
            # Generate cache key
            cache_key = self._generate_cache_key(user_id, context, target_group)
            
            # Check cache
            if cache_key in self._threshold_cache:
                cached_thresholds = self._threshold_cache[cache_key]
                return {RiskDomain(domain): thresholds 
                       for domain, thresholds in cached_thresholds.items()}
            
            # Start with base thresholds
            computed_thresholds = {}
            for domain_str, severity_thresholds in base_config.domain_thresholds.items():
                domain = RiskDomain(domain_str)
                computed_thresholds[domain] = severity_thresholds.copy()
            
            # Apply user-specific adjustments
            if user_id and self.adaptation_enabled:
                computed_thresholds = await self._apply_user_adjustments(
                    computed_thresholds, user_id
                )
            
            # Apply contextual modifiers
            if context:
                computed_thresholds = await self._apply_contextual_modifiers(
                    computed_thresholds, context, base_config
                )
            
            # Cache results
            cache_data = {domain.value: thresholds 
                         for domain, thresholds in computed_thresholds.items()}
            self._threshold_cache[cache_key] = cache_data
            
            # Maintain cache size
            if len(self._threshold_cache) > self.cache_size:
                oldest_key = min(self._threshold_cache.keys())
                del self._threshold_cache[oldest_key]
            
            return computed_thresholds
            
        except Exception as e:
            self._logger.error(f"Error getting thresholds: {str(e)}")
            # Return default thresholds as fallback
            return {RiskDomain(domain): thresholds 
                   for domain, thresholds in self._default_config.domain_thresholds.items()}
    
    def _determine_population_group(self, context: Optional[CrisisContext]) -> PopulationGroup:
        """Determine appropriate population group based on context."""
        if not context:
            return PopulationGroup.GENERAL
        
        # High-risk indicators
        if context.previous_episodes > 2:
            return PopulationGroup.HIGH_RISK
        
        # First episode indicators
        if context.previous_episodes == 0 and not context.therapy_engaged:
            return PopulationGroup.FIRST_EPISODE
        
        # Chronic condition indicators
        if context.current_medications and context.therapy_engaged:
            return PopulationGroup.CHRONIC_CONDITION
        
        return PopulationGroup.GENERAL
    
    async def _apply_user_adjustments(
        self,
        base_thresholds: Dict[RiskDomain, Dict[str, float]],
        user_id: str
    ) -> Dict[RiskDomain, Dict[str, float]]:
        """Apply user-specific threshold adjustments."""
        hashed_user_id = self._hash_user_id(user_id)
        user_adjustments = self._user_adjustments.get(hashed_user_id, [])
        
        if not user_adjustments:
            return base_thresholds
        
        adjusted_thresholds = {}
        
        for domain, severity_thresholds in base_thresholds.items():
            adjusted_thresholds[domain] = severity_thresholds.copy()
            
            # Apply relevant adjustments
            for adjustment in user_adjustments:
                if adjustment.domain == domain and self._is_adjustment_active(adjustment):
                    # Find matching severity level
                    for severity, threshold in severity_thresholds.items():
                        if severity == adjustment.severity_level.value:
                            adjusted_thresholds[domain][severity] = adjustment.adjusted_threshold
                            break
        
        return adjusted_thresholds
    
    def _is_adjustment_active(self, adjustment: ThresholdAdjustment) -> bool:
        """Check if a threshold adjustment is currently active."""
        now = datetime.now()
        
        # Check if adjustment has started
        if adjustment.effective_from > now:
            return False
        
        # Check if adjustment has expired
        if adjustment.expires_at and adjustment.expires_at <= now:
            return False
        
        return True
    
    async def _apply_contextual_modifiers(
        self,
        base_thresholds: Dict[RiskDomain, Dict[str, float]],
        context: CrisisContext,
        config: ThresholdConfiguration
    ) -> Dict[RiskDomain, Dict[str, float]]:
        """Apply contextual modifiers to thresholds."""
        modifiers = config.contextual_modifiers
        
        # Determine active modifiers
        active_modifiers = []
        
        if context.time_of_day in ["late_night", "early_morning"]:
            active_modifiers.append(context.time_of_day)
        
        if not context.support_available:
            active_modifiers.append("no_support")
        
        if context.therapy_engaged:
            active_modifiers.append("therapy_engaged")
        
        if context.current_medications:
            active_modifiers.append("medication_compliant")
        
        # Calculate combined modifier
        combined_modifier = 1.0
        for modifier_key in active_modifiers:
            if modifier_key in modifiers:
                combined_modifier *= modifiers[modifier_key]
        
        # Apply modifier to thresholds
        modified_thresholds = {}
        for domain, severity_thresholds in base_thresholds.items():
            modified_thresholds[domain] = {}
            for severity, threshold in severity_thresholds.items():
                modified_threshold = threshold * combined_modifier
                # Ensure threshold stays within valid range
                modified_thresholds[domain][severity] = max(0.05, min(0.95, modified_threshold))
        
        return modified_thresholds
    
    async def adapt_thresholds_from_outcome(
        self,
        assessment: RiskAssessment,
        actual_outcome: ClinicalSeverity,
        user_id: Optional[str] = None
    ) -> bool:
        """Adapt thresholds based on assessment outcome validation."""
        if not self.adaptation_enabled:
            return False
        
        try:
            # Map assessment severity to clinical severity
            predicted_severity = self._map_crisis_to_clinical_severity(assessment.severity)
            
            # Check if adjustment is needed
            severity_difference = self._calculate_severity_difference(
                predicted_severity, actual_outcome
            )
            
            if abs(severity_difference) < 1:  # No significant difference
                return False
            
            # Determine adjustment direction
            adjustment_needed = severity_difference > 0  # Over-predicted
            
            # Calculate adjustment parameters
            adjustment_factor = self._calculate_adjustment_factor(severity_difference)
            
            # Create threshold adjustments for relevant domains
            adjustments_made = False
            
            for domain_str, risk_score in assessment.risk_domains.items():
                domain = RiskDomain(domain_str)
                
                # Only adjust domains with significant risk scores
                if risk_score >= 0.3:
                    adjustment = await self._create_threshold_adjustment(
                        domain=domain,
                        severity_level=predicted_severity,
                        adjustment_factor=adjustment_factor,
                        increase_threshold=adjustment_needed,
                        user_id=user_id,
                        validation_score=abs(severity_difference) / 4.0
                    )
                    
                    if adjustment:
                        hashed_user_id = self._hash_user_id(user_id) if user_id else "global"
                        self._user_adjustments[hashed_user_id].append(adjustment)
                        adjustments_made = True
            
            # Record adaptation in history
            if adjustments_made:
                self._adaptation_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "assessment_id": assessment.assessment_id,
                    "predicted_severity": predicted_severity.value,
                    "actual_severity": actual_outcome.value,
                    "severity_difference": severity_difference,
                    "adjustment_factor": adjustment_factor,
                    "user_id": user_id
                })
                
                self._logger.info(
                    f"Adapted thresholds based on outcome",
                    extra={
                        "assessment_id": assessment.assessment_id,
                        "predicted": predicted_severity.value,
                        "actual": actual_outcome.value,
                        "adjustment_factor": adjustment_factor
                    }
                )
            
            return adjustments_made
            
        except Exception as e:
            self._logger.error(f"Error adapting thresholds: {str(e)}")
            return False
    
    def _map_crisis_to_clinical_severity(self, crisis_severity: CrisisSeverity) -> ClinicalSeverity:
        """Map crisis severity to clinical severity."""
        mapping = {
            CrisisSeverity.NONE: ClinicalSeverity.MINIMAL,
            CrisisSeverity.LOW: ClinicalSeverity.MILD,
            CrisisSeverity.MEDIUM: ClinicalSeverity.MODERATE,
            CrisisSeverity.HIGH: ClinicalSeverity.SEVERE,
            CrisisSeverity.CRITICAL: ClinicalSeverity.EXTREME,
            CrisisSeverity.IMMINENT: ClinicalSeverity.EXTREME
        }
        return mapping.get(crisis_severity, ClinicalSeverity.MINIMAL)
    
    def _calculate_severity_difference(
        self, 
        predicted: ClinicalSeverity, 
        actual: ClinicalSeverity
    ) -> float:
        """Calculate numerical difference between severity levels."""
        severity_values = {
            ClinicalSeverity.MINIMAL: 0,
            ClinicalSeverity.MILD: 1,
            ClinicalSeverity.MODERATE: 2,
            ClinicalSeverity.SEVERE: 3,
            ClinicalSeverity.EXTREME: 4
        }
        
        predicted_value = severity_values.get(predicted, 0)
        actual_value = severity_values.get(actual, 0)
        
        return predicted_value - actual_value
    
    def _calculate_adjustment_factor(self, severity_difference: float) -> float:
        """Calculate threshold adjustment factor based on severity difference."""
        # Base adjustment factor on the magnitude of the difference
        base_factor = min(0.3, abs(severity_difference) * 0.1)
        
        # Add some randomness to prevent over-adjustment
        noise_factor = np.random.uniform(-0.02, 0.02)
        
        return base_factor + noise_factor
    
    async def _create_threshold_adjustment(
        self,
        domain: RiskDomain,
        severity_level: ClinicalSeverity,
        adjustment_factor: float,
        increase_threshold: bool,
        user_id: Optional[str],
        validation_score: float
    ) -> Optional[ThresholdAdjustment]:
        """Create a new threshold adjustment."""
        try:
            # Get current threshold
            current_thresholds = await self.get_thresholds_for_assessment(user_id)
            current_threshold = current_thresholds.get(domain, {}).get(
                severity_level.value, 0.5
            )
            
            # Calculate new threshold
            if increase_threshold:
                new_threshold = current_threshold * (1 + adjustment_factor)
            else:
                new_threshold = current_threshold * (1 - adjustment_factor)
            
            # Ensure threshold is within valid range
            new_threshold = max(0.05, min(0.95, new_threshold))
            
            # Don't create adjustment if change is too small
            if abs(new_threshold - current_threshold) < 0.01:
                return None
            
            adjustment = ThresholdAdjustment(
                adjustment_id=str(uuid.uuid4())[:16],
                user_id=user_id,
                domain=domain,
                severity_level=severity_level,
                original_threshold=current_threshold,
                adjusted_threshold=new_threshold,
                adjustment_factor=adjustment_factor if increase_threshold else -adjustment_factor,
                reason=f"Outcome validation: {'over' if increase_threshold else 'under'}-predicted",
                expires_at=datetime.now() + timedelta(days=30),
                validation_score=validation_score
            )
            
            return adjustment
            
        except Exception as e:
            self._logger.error(f"Error creating threshold adjustment: {str(e)}")
            return None
    
    async def validate_threshold_performance(
        self,
        assessments: List[RiskAssessment],
        outcomes: List[ClinicalSeverity],
        population_group: Optional[PopulationGroup] = None
    ) -> Dict[str, float]:
        """Validate threshold performance against actual outcomes."""
        if len(assessments) != len(outcomes):
            raise ValueError("Assessments and outcomes must have same length")
        
        metrics = {
            "accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
            "false_positive_rate": 0.0,
            "false_negative_rate": 0.0,
            "threshold_calibration": 0.0
        }
        
        if not assessments:
            return metrics
        
        # Convert to binary classification (high risk vs low risk)
        high_risk_threshold = ClinicalSeverity.SEVERE
        
        predicted_high_risk = []
        actual_high_risk = []
        
        for assessment, outcome in zip(assessments, outcomes):
            predicted_severity = self._map_crisis_to_clinical_severity(assessment.severity)
            
            predicted_high_risk.append(
                self._severity_to_numeric(predicted_severity) >= 
                self._severity_to_numeric(high_risk_threshold)
            )
            actual_high_risk.append(
                self._severity_to_numeric(outcome) >= 
                self._severity_to_numeric(high_risk_threshold)
            )
        
        # Calculate confusion matrix
        tp = sum(1 for p, a in zip(predicted_high_risk, actual_high_risk) if p and a)
        fp = sum(1 for p, a in zip(predicted_high_risk, actual_high_risk) if p and not a)
        tn = sum(1 for p, a in zip(predicted_high_risk, actual_high_risk) if not p and not a)
        fn = sum(1 for p, a in zip(predicted_high_risk, actual_high_risk) if not p and a)
        
        total = len(assessments)
        
        # Calculate metrics
        if total > 0:
            metrics["accuracy"] = (tp + tn) / total
        
        if tp + fp > 0:
            metrics["precision"] = tp / (tp + fp)
        
        if tp + fn > 0:
            metrics["recall"] = tp / (tp + fn)
        
        if metrics["precision"] + metrics["recall"] > 0:
            metrics["f1_score"] = (2 * metrics["precision"] * metrics["recall"]) / (
                metrics["precision"] + metrics["recall"]
            )
        
        if fp + tn > 0:
            metrics["false_positive_rate"] = fp / (fp + tn)
        
        if fn + tp > 0:
            metrics["false_negative_rate"] = fn / (fn + tp)
        
        # Calculate threshold calibration
        calibration_errors = []
        for assessment, outcome in zip(assessments, outcomes):
            predicted_prob = assessment.confidence
            actual_binary = self._severity_to_numeric(outcome) >= self._severity_to_numeric(high_risk_threshold)
            calibration_errors.append(abs(predicted_prob - (1.0 if actual_binary else 0.0)))
        
        metrics["threshold_calibration"] = 1.0 - np.mean(calibration_errors)
        
        return metrics
    
    def _severity_to_numeric(self, severity: ClinicalSeverity) -> int:
        """Convert clinical severity to numeric value."""
        return {
            ClinicalSeverity.MINIMAL: 0,
            ClinicalSeverity.MILD: 1,
            ClinicalSeverity.MODERATE: 2,
            ClinicalSeverity.SEVERE: 3,
            ClinicalSeverity.EXTREME: 4
        }.get(severity, 0)
    
    def _generate_cache_key(
        self, 
        user_id: Optional[str], 
        context: Optional[CrisisContext],
        population_group: PopulationGroup
    ) -> str:
        """Generate cache key for threshold lookup."""
        key_parts = [
            user_id or "anonymous",
            population_group.value,
            context.time_of_day if context else "default",
            str(context.support_available) if context else "true",
            str(context.therapy_engaged) if context else "false"
        ]
        return "|".join(key_parts)
    
    def _hash_user_id(self, user_id: str) -> str:
        """Hash user ID for privacy compliance."""
        return hashlib.sha256(user_id.encode()).hexdigest()[:16]
    
    def get_population_statistics(self) -> Dict[str, Any]:
        """Get current population statistics."""
        return self._population_stats.copy()
    
    def get_adaptation_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get threshold adaptation history."""
        return list(self._adaptation_history)[-limit:]


# Convenience functions
async def get_crisis_thresholds(
    user_id: Optional[str] = None,
    context: Optional[CrisisContext] = None
) -> Dict[RiskDomain, Dict[str, float]]:
    """Convenience function to get crisis detection thresholds."""
    threshold_manager = DetectionThresholds()
    return await threshold_manager.get_thresholds_for_assessment(user_id, context)

async def validate_thresholds(
    assessments: List[RiskAssessment],
    outcomes: List[ClinicalSeverity]
) -> Dict[str, float]:
    """Convenience function to validate threshold performance."""
    threshold_manager = DetectionThresholds()
    return await threshold_manager.validate_threshold_performance(assessments, outcomes) 