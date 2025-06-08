"""
Accessibility Standards Compliance Module

This module provides utilities for ensuring compliance with accessibility standards
including WCAG 2.1, Section 508, ADA, and EN 301 549.
"""

from enum import Enum
from typing import Dict, List, Set, Optional
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AccessibilityStandard(str, Enum):
    """Supported accessibility standards."""
    WCAG_2_0_A = "wcag_2_0_a"
    WCAG_2_0_AA = "wcag_2_0_aa"
    WCAG_2_0_AAA = "wcag_2_0_aaa"
    WCAG_2_1_A = "wcag_2_1_a"
    WCAG_2_1_AA = "wcag_2_1_aa"
    WCAG_2_1_AAA = "wcag_2_1_aaa"
    WCAG_2_2_A = "wcag_2_2_a"
    WCAG_2_2_AA = "wcag_2_2_aa"
    WCAG_2_2_AAA = "wcag_2_2_aaa"
    SECTION_508 = "section_508"
    ADA = "ada"
    EN_301_549 = "en_301_549"
    AODA = "aoda"  # Accessibility for Ontarians with Disabilities Act


class ComplianceCategory(str, Enum):
    """Categories of accessibility compliance."""
    PERCEIVABLE = "perceivable"
    OPERABLE = "operable"
    UNDERSTANDABLE = "understandable"
    ROBUST = "robust"
    EQUIVALENT_EXPERIENCE = "equivalent_experience"
    PRIVACY = "privacy"
    DOCUMENTATION = "documentation"


class ComplianceCriterion(BaseModel):
    """Model for an accessibility compliance criterion."""
    id: str
    standard: AccessibilityStandard
    category: ComplianceCategory
    level: str  # A, AA, or AAA for WCAG
    description: str
    implementation_notes: Optional[str] = None
    verification_method: Optional[str] = None
    related_adaptations: List[str] = []


class ComplianceReport(BaseModel):
    """Model for an accessibility compliance report."""
    standards: List[AccessibilityStandard]
    timestamp: str
    compliant_criteria: List[str]
    non_compliant_criteria: List[str]
    not_applicable_criteria: List[str]
    compliance_score: float  # Percentage of applicable criteria that are compliant
    recommendations: List[str] = []


# Define WCAG 2.1 AA criteria (subset for demonstration)
WCAG_2_1_AA_CRITERIA = [
    ComplianceCriterion(
        id="1.1.1",
        standard=AccessibilityStandard.WCAG_2_1_AA,
        category=ComplianceCategory.PERCEIVABLE,
        level="A",
        description="Non-text Content: All non-text content has a text alternative",
        implementation_notes="Ensure all symbolic content has text descriptions",
        verification_method="Check that all symbolic patterns have text alternatives",
        related_adaptations=["text_alternatives", "screen_reader_compatibility"]
    ),
    ComplianceCriterion(
        id="1.3.1",
        standard=AccessibilityStandard.WCAG_2_1_AA,
        category=ComplianceCategory.PERCEIVABLE,
        level="A",
        description="Info and Relationships: Information, structure, and relationships can be programmatically determined",
        implementation_notes="Ensure structured data is properly labeled",
        verification_method="Validate JSON structure includes semantic information",
        related_adaptations=["structured_content"]
    ),
    ComplianceCriterion(
        id="1.4.3",
        standard=AccessibilityStandard.WCAG_2_1_AA,
        category=ComplianceCategory.PERCEIVABLE,
        level="AA",
        description="Contrast (Minimum): Text has a contrast ratio of at least 4.5:1",
        implementation_notes="Ensure high contrast mode meets this requirement",
        verification_method="Validate contrast ratios in high contrast mode",
        related_adaptations=["high_contrast"]
    ),
    ComplianceCriterion(
        id="2.1.1",
        standard=AccessibilityStandard.WCAG_2_1_AA,
        category=ComplianceCategory.OPERABLE,
        level="A",
        description="Keyboard: All functionality is available from a keyboard",
        implementation_notes="Ensure all interactions can be performed via keyboard",
        verification_method="Test all features with keyboard navigation",
        related_adaptations=["alternative_input"]
    ),
    ComplianceCriterion(
        id="2.2.1",
        standard=AccessibilityStandard.WCAG_2_1_AA,
        category=ComplianceCategory.OPERABLE,
        level="A",
        description="Timing Adjustable: Users can adjust or extend time limits",
        implementation_notes="Implement timeout extensions for users who need more time",
        verification_method="Verify timeout extension functionality",
        related_adaptations=["time_extension"]
    ),
    ComplianceCriterion(
        id="2.4.2",
        standard=AccessibilityStandard.WCAG_2_1_AA,
        category=ComplianceCategory.OPERABLE,
        level="A",
        description="Page Titled: Pages have titles that describe topic or purpose",
        implementation_notes="Ensure all API responses include descriptive titles",
        verification_method="Check response metadata for titles",
        related_adaptations=["structured_content"]
    ),
    ComplianceCriterion(
        id="3.1.1",
        standard=AccessibilityStandard.WCAG_2_1_AA,
        category=ComplianceCategory.UNDERSTANDABLE,
        level="A",
        description="Language of Page: Default human language can be programmatically determined",
        implementation_notes="Include language identifier in API responses",
        verification_method="Check for language metadata in responses",
        related_adaptations=["language_identification"]
    ),
    ComplianceCriterion(
        id="3.2.1",
        standard=AccessibilityStandard.WCAG_2_1_AA,
        category=ComplianceCategory.UNDERSTANDABLE,
        level="A",
        description="On Focus: When a component receives focus, it does not initiate a change of context",
        implementation_notes="Ensure focus behavior is predictable",
        verification_method="Test focus behavior in UI components",
        related_adaptations=["predictable_interaction"]
    ),
    ComplianceCriterion(
        id="3.3.1",
        standard=AccessibilityStandard.WCAG_2_1_AA,
        category=ComplianceCategory.UNDERSTANDABLE,
        level="A",
        description="Error Identification: Input errors are clearly identified",
        implementation_notes="Provide clear error messages for API requests",
        verification_method="Test error responses for clarity",
        related_adaptations=["error_identification"]
    ),
    ComplianceCriterion(
        id="4.1.1",
        standard=AccessibilityStandard.WCAG_2_1_AA,
        category=ComplianceCategory.ROBUST,
        level="A",
        description="Parsing: Content uses valid markup",
        implementation_notes="Ensure API responses are well-formed",
        verification_method="Validate JSON structure",
        related_adaptations=["structured_content"]
    ),
]

# Define Section 508 criteria (subset for demonstration)
SECTION_508_CRITERIA = [
    ComplianceCriterion(
        id="1194.22.a",
        standard=AccessibilityStandard.SECTION_508,
        category=ComplianceCategory.PERCEIVABLE,
        level="Required",
        description="Text equivalent for non-text elements",
        implementation_notes="Ensure all symbolic content has text descriptions",
        verification_method="Check that all symbolic patterns have text alternatives",
        related_adaptations=["text_alternatives"]
    ),
    ComplianceCriterion(
        id="1194.22.l",
        standard=AccessibilityStandard.SECTION_508,
        category=ComplianceCategory.ROBUST,
        level="Required",
        description="Scripts must be identified with functional text",
        implementation_notes="Ensure all interactive elements are properly labeled",
        verification_method="Check interactive element descriptions",
        related_adaptations=["screen_reader_compatibility"]
    ),
    ComplianceCriterion(
        id="1194.31.a",
        standard=AccessibilityStandard.SECTION_508,
        category=ComplianceCategory.EQUIVALENT_EXPERIENCE,
        level="Required",
        description="Functional text for blind users",
        implementation_notes="Ensure screen reader compatibility",
        verification_method="Test with screen readers",
        related_adaptations=["screen_reader_compatibility"]
    ),
    ComplianceCriterion(
        id="1194.31.b",
        standard=AccessibilityStandard.SECTION_508,
        category=ComplianceCategory.EQUIVALENT_EXPERIENCE,
        level="Required",
        description="Equivalent alternatives for audio and visual content",
        implementation_notes="Provide text alternatives for audio content",
        verification_method="Check for text alternatives",
        related_adaptations=["captioning"]
    ),
]

# Define ADA criteria (subset for demonstration)
ADA_CRITERIA = [
    ComplianceCriterion(
        id="ADA-1",
        standard=AccessibilityStandard.ADA,
        category=ComplianceCategory.EQUIVALENT_EXPERIENCE,
        level="Required",
        description="Equal access to goods and services",
        implementation_notes="Ensure all features are accessible to users with disabilities",
        verification_method="Comprehensive accessibility testing",
        related_adaptations=["multi_modal_communication"]
    ),
    ComplianceCriterion(
        id="ADA-2",
        standard=AccessibilityStandard.ADA,
        category=ComplianceCategory.PRIVACY,
        level="Required",
        description="Privacy of disability-related information",
        implementation_notes="Ensure accessibility preferences are stored securely",
        verification_method="Security audit of preference storage",
        related_adaptations=[]
    ),
]

# Combine all criteria
ALL_CRITERIA = WCAG_2_1_AA_CRITERIA + SECTION_508_CRITERIA + ADA_CRITERIA


class ComplianceChecker:
    """
    Utility for checking compliance with accessibility standards.
    """
    
    def __init__(self, standards: List[AccessibilityStandard] = None):
        """
        Initialize the compliance checker.
        
        Args:
            standards: List of standards to check against
        """
        self.standards = standards or [
            AccessibilityStandard.WCAG_2_1_AA,
            AccessibilityStandard.SECTION_508,
            AccessibilityStandard.ADA
        ]
        
        # Filter criteria by selected standards
        self.criteria = [
            criterion for criterion in ALL_CRITERIA
            if criterion.standard in self.standards
        ]
    
    def check_compliance(self, implementation_data: Dict) -> ComplianceReport:
        """
        Check compliance with selected standards.
        
        Args:
            implementation_data: Data about the implementation to check
            
        Returns:
            Compliance report
        """
        compliant = []
        non_compliant = []
        not_applicable = []
        recommendations = []
        
        # Check each criterion
        for criterion in self.criteria:
            # Check if criterion is applicable
            if not self._is_applicable(criterion, implementation_data):
                not_applicable.append(criterion.id)
                continue
            
            # Check if criterion is compliant
            if self._is_compliant(criterion, implementation_data):
                compliant.append(criterion.id)
            else:
                non_compliant.append(criterion.id)
                recommendations.append(
                    f"Implement {criterion.id}: {criterion.description}"
                )
        
        # Calculate compliance score
        applicable_count = len(compliant) + len(non_compliant)
        compliance_score = (len(compliant) / applicable_count) * 100 if applicable_count > 0 else 0
        
        # Create report
        return ComplianceReport(
            standards=self.standards,
            timestamp=implementation_data.get("timestamp", ""),
            compliant_criteria=compliant,
            non_compliant_criteria=non_compliant,
            not_applicable_criteria=not_applicable,
            compliance_score=compliance_score,
            recommendations=recommendations
        )
    
    def _is_applicable(self, criterion: ComplianceCriterion, implementation_data: Dict) -> bool:
        """
        Check if a criterion is applicable to the implementation.
        
        Args:
            criterion: Criterion to check
            implementation_data: Implementation data
            
        Returns:
            Whether the criterion is applicable
        """
        # Check if the criterion is relevant to the implementation
        # This is a simplified implementation
        features = implementation_data.get("features", [])
        adaptations = implementation_data.get("adaptations", [])
        
        # If any related adaptation is in the implementation, the criterion is applicable
        for adaptation in criterion.related_adaptations:
            if adaptation in adaptations:
                return True
        
        return False
    
    def _is_compliant(self, criterion: ComplianceCriterion, implementation_data: Dict) -> bool:
        """
        Check if a criterion is compliant in the implementation.
        
        Args:
            criterion: Criterion to check
            implementation_data: Implementation data
            
        Returns:
            Whether the criterion is compliant
        """
        # This is a simplified implementation
        # In a real implementation, this would perform actual checks
        compliant_criteria = implementation_data.get("compliant_criteria", [])
        return criterion.id in compliant_criteria


def get_compliance_checker(standards: List[AccessibilityStandard] = None) -> ComplianceChecker:
    """
    Get a compliance checker for the specified standards.
    
    Args:
        standards: List of standards to check against
        
    Returns:
        ComplianceChecker instance
    """
    return ComplianceChecker(standards)
