"""
Accessibility Configuration Module

This module provides configuration settings for accessibility features throughout the
Emotional Wellness API, compliant with WCAG 2.1 and Section 508 standards.
"""

from enum import Enum
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field


class DisabilityType(str, Enum):
    """Enumeration of disability categories for tailored accessibility adaptations."""
    VISION = "vision"
    HEARING = "hearing"
    MOTOR = "motor"
    COGNITIVE = "cognitive"
    SPEECH = "speech"
    SENSORY = "sensory"
    LEARNING = "learning"
    NEURODIVERSITY = "neurodiversity"  # Autism, ADHD, etc.


class AccessibilityLevel(str, Enum):
    """Accessibility support levels."""
    MINIMAL = "minimal"
    MODERATE = "moderate"
    COMPREHENSIVE = "comprehensive"
    PERSONALIZED = "personalized"


class AdaptationType(str, Enum):
    """Types of adaptations that can be applied."""
    TEXT_SIMPLIFICATION = "text_simplification"
    TEXT_TO_SPEECH = "text_to_speech"
    SPEECH_TO_TEXT = "speech_to_text"
    HIGH_CONTRAST = "high_contrast"
    LARGE_TEXT = "large_text"
    SCREEN_READER_COMPAT = "screen_reader_compatibility"
    ALTERNATIVE_INPUT = "alternative_input"
    CAPTIONING = "captioning"
    SYMBOLS_AND_PICTOGRAMS = "symbols_and_pictograms"
    EMOTIONAL_CUES = "emotional_cues"
    TIME_EXTENSION = "time_extension"
    MULTI_MODAL_COMMUNICATION = "multi_modal_communication"
    SIMPLIFIED_NAVIGATION = "simplified_navigation"
    SENSORY_OVERLOAD_REDUCTION = "sensory_overload_reduction"


class AccessibilityConfig(BaseModel):
    """Configuration for accessibility features."""
    
    # Global settings
    enable_accessibility_features: bool = True
    default_level: AccessibilityLevel = AccessibilityLevel.MODERATE
    
    # Compliance standards
    wcag_compliance_level: str = "AA"  # AA is the generally recommended level
    section_508_compliant: bool = True
    
    # Adaptation mappings (disability type to recommended adaptations)
    adaptation_mappings: Dict[DisabilityType, List[AdaptationType]] = Field(
        default_factory=lambda: {
            DisabilityType.VISION: [
                AdaptationType.SCREEN_READER_COMPAT,
                AdaptationType.TEXT_TO_SPEECH,
                AdaptationType.HIGH_CONTRAST,
                AdaptationType.LARGE_TEXT
            ],
            DisabilityType.HEARING: [
                AdaptationType.CAPTIONING,
                AdaptationType.SYMBOLS_AND_PICTOGRAMS,
                AdaptationType.TEXT_SIMPLIFICATION
            ],
            DisabilityType.MOTOR: [
                AdaptationType.ALTERNATIVE_INPUT,
                AdaptationType.TIME_EXTENSION,
                AdaptationType.SIMPLIFIED_NAVIGATION
            ],
            DisabilityType.COGNITIVE: [
                AdaptationType.TEXT_SIMPLIFICATION,
                AdaptationType.SYMBOLS_AND_PICTOGRAMS,
                AdaptationType.TIME_EXTENSION,
                AdaptationType.EMOTIONAL_CUES,
                AdaptationType.SIMPLIFIED_NAVIGATION
            ],
            DisabilityType.SPEECH: [
                AdaptationType.SPEECH_TO_TEXT,
                AdaptationType.ALTERNATIVE_INPUT,
                AdaptationType.SYMBOLS_AND_PICTOGRAMS
            ],
            DisabilityType.SENSORY: [
                AdaptationType.SENSORY_OVERLOAD_REDUCTION,
                AdaptationType.SIMPLIFIED_NAVIGATION,
                AdaptationType.MULTI_MODAL_COMMUNICATION
            ],
            DisabilityType.LEARNING: [
                AdaptationType.TEXT_SIMPLIFICATION,
                AdaptationType.EMOTIONAL_CUES,
                AdaptationType.TIME_EXTENSION,
                AdaptationType.SYMBOLS_AND_PICTOGRAMS
            ],
            DisabilityType.NEURODIVERSITY: [
                AdaptationType.SENSORY_OVERLOAD_REDUCTION,
                AdaptationType.EMOTIONAL_CUES,
                AdaptationType.SIMPLIFIED_NAVIGATION,
                AdaptationType.TIME_EXTENSION,
                AdaptationType.MULTI_MODAL_COMMUNICATION
            ]
        }
    )
    
    # API response adaptation defaults
    apply_to_all_responses: bool = False
    respect_user_preferences: bool = True
    
    # Timeout extensions (percentage increase for differently-abled users)
    session_timeout_extension: int = 200  # 200% longer sessions
    response_timeout_extension: int = 150  # 150% longer for responses
    
    # Feature flags
    enable_text_simplification: bool = True
    enable_text_to_speech: bool = True
    enable_emotional_cues: bool = True
    enable_alternative_inputs: bool = True
    enable_multi_modal_support: bool = True
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "enable_accessibility_features": True,
                "default_level": "comprehensive",
                "wcag_compliance_level": "AA",
                "section_508_compliant": True,
                "apply_to_all_responses": False,
                "respect_user_preferences": True
            }
        }


# Global configuration instance with defaults
# Can be overridden by settings from configuration files or environment
accessibility_config = AccessibilityConfig()


def get_adaptations_for_disabilities(disabilities: Set[DisabilityType]) -> List[AdaptationType]:
    """
    Get recommended adaptations for a set of disabilities.
    
    Args:
        disabilities: Set of disability types
        
    Returns:
        List of recommended adaptations
    """
    adaptations = set()
    for disability in disabilities:
        if disability in accessibility_config.adaptation_mappings:
            adaptations.update(accessibility_config.adaptation_mappings[disability])
    return list(adaptations)


def configure_from_settings(settings_dict: dict) -> None:
    """
    Configure accessibility settings from a dictionary.
    
    Args:
        settings_dict: Dictionary containing accessibility settings
    """
    global accessibility_config
    accessibility_config = AccessibilityConfig(**settings_dict)
