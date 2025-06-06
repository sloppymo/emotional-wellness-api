"""
MOSS: Multi-dimensional Ontological Safety System

This package provides comprehensive crisis detection and intervention capabilities
for the SYLVA emotional wellness platform.

Components:
- Crisis Classifier: Multi-dimensional risk assessment
- Detection Thresholds: Adaptive threshold management  
- Audit Logging: HIPAA-compliant activity tracking
- Prompt Templates: Crisis intervention guidance

Key Features:
- Real-time crisis detection
- Personalized intervention prompts
- Adaptive threshold learning
- Comprehensive audit trails
- HIPAA compliance
- Safety orchestration
"""

# Core processor
from .processor import MossProcessor, get_moss_processor

# Core crisis detection
from .crisis_classifier import (
    CrisisClassifier,
    CrisisSeverity,
    RiskDomain,
    CrisisContext,
    RiskAssessment,
    assess_crisis_risk,
    create_crisis_context
)

# For backward compatibility
RiskSeverity = CrisisSeverity  # Alias for backward compatibility

# Threshold management
from .detection_thresholds import (
    DetectionThresholds,
    ThresholdConfiguration,
    ThresholdAdjustment,
    ClinicalSeverity,
    PopulationGroup,
    ThresholdType,
    get_crisis_thresholds,
    validate_thresholds
)

# Audit logging
from .audit_logging import (
    MOSSAuditLogger,
    AuditEvent,
    AuditEventType,
    AuditSeverity,
    AuditQuery,
    AuditStatistics,
    ComplianceFramework,
    PHICategory,
    log_crisis_assessment,
    log_crisis_intervention
)

# Prompt templates
from .prompt_templates import (
    MOSSPromptTemplates,
    PromptTemplate,
    PromptCategory,
    PromptTone,
    CommunicationChannel,
    GeneratedPrompt,
    generate_crisis_prompt,
    generate_safety_planning_prompt
)

__all__ = [
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier
    "CrisisClassifier",
    "CrisisSeverity",
    "RiskSeverity",  # Added for backward compatibility
    "RiskDomain",
    "CrisisContext",
    "RiskAssessment",
    "assess_crisis_risk",
    "create_crisis_context",
    
    # Detection thresholds
    "DetectionThresholds",
    "ThresholdConfiguration",
    "ThresholdAdjustment", 
    "ClinicalSeverity",
    "PopulationGroup",
    "ThresholdType",
    "get_crisis_thresholds",
    "validate_thresholds",
    
    # Audit logging
    "MOSSAuditLogger",
    "AuditEvent",
    "AuditEventType",
    "AuditSeverity",
    "AuditQuery", 
    "AuditStatistics",
    "ComplianceFramework",
    "PHICategory",
    "log_crisis_assessment",
    "log_crisis_intervention",
    
    # Prompt templates
    "MOSSPromptTemplates",
    "PromptTemplate",
    "PromptCategory",
    "PromptTone",
    "CommunicationChannel", 
    "GeneratedPrompt",
    "generate_crisis_prompt",
    "generate_safety_planning_prompt"
]

# Version information
__version__ = "1.0.0"
__author__ = "SYLVA-WREN Development Team"
__description__ = "Multi-dimensional Ontological Safety System for Crisis Detection" 