"""
MOSS Crisis Classifier System

This module provides advanced crisis assessment and classification with:
- Multi-dimensional risk analysis
- Machine learning-enhanced detection
- PHI protection and anonymization
- Real-time severity categorization
- Contextual risk evaluation
- Intervention recommendation engine
"""

import asyncio
import hashlib
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from functools import lru_cache
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
import re

from pydantic import BaseModel, Field, ConfigDict, validator
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
import joblib

from ..moss import MossProcessor, get_moss_processor
from models.emotional_state import SymbolicMapping, SafetyStatus
from structured_logging import get_logger

logger = get_logger(__name__)

class CrisisSeverity(str, Enum):
    """Crisis severity levels with clinical definitions."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    IMMINENT = "imminent"

class RiskDomain(str, Enum):
    """Risk assessment domains."""
    SELF_HARM = "self_harm"
    SUICIDE = "suicide"
    SUBSTANCE_ABUSE = "substance_abuse"
    PSYCHOSIS = "psychosis"
    VIOLENCE = "violence"
    NEGLECT = "neglect"
    TRAUMA = "trauma"
    EATING_DISORDER = "eating_disorder"

class InterventionType(str, Enum):
    """Types of interventions available."""
    IMMEDIATE_SAFETY = "immediate_safety"
    PROFESSIONAL_REFERRAL = "professional_referral"
    CRISIS_HOTLINE = "crisis_hotline"
    EMERGENCY_SERVICES = "emergency_services"
    PEER_SUPPORT = "peer_support"
    THERAPEUTIC_TECHNIQUES = "therapeutic_techniques"
    SAFETY_PLANNING = "safety_planning"
    MONITORING = "monitoring"

class CrisisContext(BaseModel):
    """Contextual information for crisis assessment."""
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    user_id: Optional[str] = Field(None, description="User identifier (hashed)")
    session_id: Optional[str] = Field(None, description="Session identifier")
    timestamp: datetime = Field(default_factory=datetime.now)
    location: Optional[str] = Field(None, description="General location context")
    time_of_day: str = Field(..., description="Time categorization")
    recent_events: List[str] = Field(default_factory=list, description="Recent life events")
    support_available: bool = Field(default=True, description="Support system availability")
    previous_episodes: int = Field(default=0, ge=0, description="Previous crisis episodes")
    current_medications: bool = Field(default=False, description="Currently on medication")
    therapy_engaged: bool = Field(default=False, description="Currently in therapy")

class RiskAssessment(BaseModel):
    """Comprehensive risk assessment result."""
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    assessment_id: str = Field(..., description="Unique assessment identifier")
    severity: CrisisSeverity = Field(..., description="Overall crisis severity")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Assessment confidence")
    risk_domains: Dict[str, float] = Field(..., description="Risk scores by domain")
    primary_concerns: List[str] = Field(..., description="Primary risk factors")
    protective_factors: List[str] = Field(default_factory=list, description="Protective factors identified")
    urgency_score: float = Field(..., ge=0.0, le=1.0, description="Urgency of intervention needed")
    recommendations: List[str] = Field(..., description="Recommended interventions")
    escalation_required: bool = Field(..., description="Whether escalation is required")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)

class CrisisClassifier:
    """
    Advanced crisis classification system with machine learning capabilities.
    
    This classifier provides:
    - Multi-dimensional risk assessment
    - Context-aware severity determination
    - PHI-protected analysis
    - Real-time intervention recommendations
    - Continuous learning from outcomes
    """
    
    def __init__(self, cache_size: int = 256):
        """Initialize the crisis classifier."""
        self.cache_size = cache_size
        self._logger = get_logger(f"{__name__}.CrisisClassifier")
        
        # Enhanced lexicons
        self._enhanced_lexicons = self._load_enhanced_lexicons()
        self._contextual_modifiers = self._load_contextual_modifiers()
        
        # Assessment cache and history
        self._assessment_cache: Dict[str, RiskAssessment] = {}
        self._user_histories: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Risk domain weights
        self._domain_weights = self._initialize_domain_weights()
        
        self._logger.info("CrisisClassifier initialized")
    
    def _load_enhanced_lexicons(self) -> Dict[RiskDomain, Dict[str, Set[str]]]:
        """Load enhanced crisis lexicons organized by risk domain."""
        return {
            RiskDomain.SUICIDE: {
                "critical": {
                    "suicide", "kill myself", "end my life", "better off dead",
                    "no reason to live", "can't go on", "want to die", "plan to die",
                    "suicide plan", "method", "when I die", "after I'm gone"
                },
                "high": {
                    "hopeless", "worthless", "no future", "pointless", 
                    "burden to everyone", "they'd be better without me",
                    "nothing matters", "no way out", "trapped forever"
                },
                "medium": {
                    "don't want to be here", "tired of living", "what's the point",
                    "everything hurts", "can't see tomorrow", "feel empty inside"
                }
            },
            RiskDomain.SELF_HARM: {
                "critical": {
                    "cut myself", "hurt myself", "punish myself", "deserve pain",
                    "cutting", "burning", "hitting myself", "self injury"
                },
                "high": {
                    "want to hurt", "need to feel pain", "deserve to suffer",
                    "hate my body", "ugly scars", "relief through pain"
                },
                "medium": {
                    "angry at myself", "frustrated with me", "can't control anger",
                    "need release", "physical pain helps", "deserve bad things"
                }
            },
            RiskDomain.SUBSTANCE_ABUSE: {
                "critical": {
                    "overdose", "too much", "don't care anymore", "blackout",
                    "can't stop using", "need more", "dangerous amounts"
                },
                "high": {
                    "drinking too much", "using to cope", "can't function without",
                    "hiding my use", "lying about drinking", "out of control"
                },
                "medium": {
                    "need a drink", "helps me forget", "only way to relax",
                    "self medicating", "numbing the pain", "escape reality"
                }
            },
            RiskDomain.VIOLENCE: {
                "critical": {
                    "hurt someone", "kill them", "violence", "weapon", "attack",
                    "revenge", "make them pay", "they deserve to die"
                },
                "high": {
                    "so angry", "rage", "want to hit", "lose control",
                    "fantasize about hurting", "they'll be sorry", "teach them"
                },
                "medium": {
                    "frustrated with people", "angry at world", "fight back",
                    "stand up for myself", "had enough", "show them"
                }
            }
        }
    
    def _load_contextual_modifiers(self) -> Dict[str, float]:
        """Load contextual factors that modify risk scores."""
        return {
            "late_night": 1.3,
            "early_morning": 1.2,
            "weekend": 1.1,
            "holiday": 1.4,
            "anniversary": 1.5,
            "isolated": 1.5,
            "no_support": 1.6,
            "family_conflict": 1.3,
            "relationship_issues": 1.2,
            "loss": 1.4,
            "trauma": 1.6,
            "job_loss": 1.3,
            "financial_stress": 1.2,
            "health_crisis": 1.4,
            "therapy_engaged": 0.7,
            "strong_support": 0.6,
            "coping_skills": 0.8,
            "medication_compliant": 0.8,
            "future_plans": 0.7,
            "religious_beliefs": 0.8
        }
    
    def _initialize_domain_weights(self) -> Dict[RiskDomain, float]:
        """Initialize relative weights for different risk domains."""
        return {
            RiskDomain.SUICIDE: 1.0,
            RiskDomain.SELF_HARM: 0.8,
            RiskDomain.VIOLENCE: 0.9,
            RiskDomain.PSYCHOSIS: 0.85,
            RiskDomain.SUBSTANCE_ABUSE: 0.7,
            RiskDomain.TRAUMA: 0.6,
            RiskDomain.EATING_DISORDER: 0.65,
            RiskDomain.NEGLECT: 0.5
        }
    
    async def assess_crisis_risk(
        self,
        text: str,
        context: Optional[CrisisContext] = None,
        user_id: Optional[str] = None
    ) -> RiskAssessment:
        """
        Perform comprehensive crisis risk assessment.
        
        Args:
            text: Input text for analysis (will be hashed for PHI protection)
            context: Optional contextual information
            user_id: Optional user identifier (will be hashed)
            
        Returns:
            RiskAssessment with comprehensive analysis
        """
        start_time = datetime.now()
        
        try:
            # Hash user_id for privacy
            hashed_user_id = self._hash_user_id(user_id) if user_id else None
            
            # Generate assessment ID
            assessment_id = self._generate_assessment_id(text, hashed_user_id)
            
            # Check cache first
            cached_assessment = self._get_cached_assessment(assessment_id)
            if cached_assessment:
                self._logger.debug(f"Returning cached assessment: {assessment_id}")
                return cached_assessment
            
            # Enhanced multi-dimensional risk analysis
            domain_risks = await self._analyze_risk_domains(text, context)
            
            # Apply contextual modifiers
            modified_risks = await self._apply_contextual_modifiers(domain_risks, context)
            
            # Calculate overall severity
            severity = self._determine_overall_severity(modified_risks)
            
            # Calculate confidence
            confidence = self._calculate_assessment_confidence(text, modified_risks, context)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(severity, modified_risks, context)
            
            # Identify protective factors
            protective_factors = await self._identify_protective_factors(text, context)
            
            # Determine if escalation is required
            escalation_required = self._requires_escalation(severity, modified_risks)
            
            # Calculate urgency score
            urgency_score = self._calculate_urgency_score(severity, modified_risks, context)
            
            # Extract primary concerns
            primary_concerns = self._extract_primary_concerns(modified_risks)
            
            # Create assessment
            assessment = RiskAssessment(
                assessment_id=assessment_id,
                severity=severity,
                confidence=confidence,
                risk_domains={domain.value: score for domain, score in modified_risks.items()},
                primary_concerns=primary_concerns,
                protective_factors=protective_factors,
                urgency_score=urgency_score,
                recommendations=recommendations,
                escalation_required=escalation_required,
                metadata={
                    "processing_time": (datetime.now() - start_time).total_seconds(),
                    "context_provided": context is not None
                }
            )
            
            # Store assessment
            await self._store_assessment(hashed_user_id, assessment)
            
            # Cache assessment
            self._cache_assessment(assessment)
            
            self._logger.info(
                f"Crisis assessment completed",
                extra={
                    "assessment_id": assessment_id,
                    "user_id": hashed_user_id,
                    "severity": severity.value,
                    "confidence": confidence,
                    "escalation_required": escalation_required,
                    "processing_time": assessment.metadata["processing_time"]
                }
            )
            
            return assessment
            
        except Exception as e:
            self._logger.error(f"Error in crisis assessment: {str(e)}")
            raise
    
    async def _analyze_risk_domains(
        self, 
        text: str, 
        context: Optional[CrisisContext]
    ) -> Dict[RiskDomain, float]:
        """Analyze risk across different domains."""
        domain_risks = {}
        text_lower = text.lower()
        
        for domain, lexicon_levels in self._enhanced_lexicons.items():
            domain_score = 0.0
            
            # Check critical terms
            for term in lexicon_levels.get("critical", set()):
                if self._find_term_in_text(term, text_lower):
                    domain_score = max(domain_score, 0.9)
                    break
            
            # Check high risk terms
            if domain_score < 0.9:
                for term in lexicon_levels.get("high", set()):
                    if self._find_term_in_text(term, text_lower):
                        domain_score = max(domain_score, 0.7)
                        break
            
            # Check medium risk terms
            if domain_score < 0.7:
                medium_matches = 0
                for term in lexicon_levels.get("medium", set()):
                    if self._find_term_in_text(term, text_lower):
                        medium_matches += 1
                
                if medium_matches > 0:
                    domain_score = min(0.6, 0.3 + (medium_matches * 0.1))
            
            # Apply domain weight
            weighted_score = domain_score * self._domain_weights.get(domain, 1.0)
            domain_risks[domain] = min(1.0, weighted_score)
        
        return domain_risks
    
    def _find_term_in_text(self, term: str, text: str) -> bool:
        """Find term in text with fuzzy matching."""
        pattern = r'\b' + re.escape(term) + r'\b'
        return bool(re.search(pattern, text))
    
    async def _apply_contextual_modifiers(
        self, 
        domain_risks: Dict[RiskDomain, float],
        context: Optional[CrisisContext]
    ) -> Dict[RiskDomain, float]:
        """Apply contextual modifiers to risk scores."""
        if not context:
            return domain_risks
        
        modified_risks = domain_risks.copy()
        
        # Time-based modifiers
        if context.time_of_day in ["late_night", "early_morning"]:
            modifier = self._contextual_modifiers.get(context.time_of_day, 1.0)
            for domain in modified_risks:
                modified_risks[domain] *= modifier
        
        # Support system modifiers
        if not context.support_available:
            for domain in modified_risks:
                modified_risks[domain] *= self._contextual_modifiers.get("no_support", 1.0)
        
        # Protective factors
        protective_modifier = 1.0
        if context.therapy_engaged:
            protective_modifier *= self._contextual_modifiers.get("therapy_engaged", 1.0)
        if context.current_medications:
            protective_modifier *= self._contextual_modifiers.get("medication_compliant", 1.0)
        
        if protective_modifier < 1.0:
            for domain in modified_risks:
                modified_risks[domain] *= protective_modifier
        
        # Cap all scores at 1.0
        for domain in modified_risks:
            modified_risks[domain] = min(1.0, modified_risks[domain])
        
        return modified_risks
    
    def _determine_overall_severity(self, domain_risks: Dict[RiskDomain, float]) -> CrisisSeverity:
        """Determine overall crisis severity."""
        max_risk = max(domain_risks.values()) if domain_risks else 0.0
        
        if max_risk >= 0.9:
            return CrisisSeverity.IMMINENT
        elif max_risk >= 0.8:
            return CrisisSeverity.CRITICAL
        elif max_risk >= 0.6:
            return CrisisSeverity.HIGH
        elif max_risk >= 0.4:
            return CrisisSeverity.MEDIUM
        elif max_risk >= 0.2:
            return CrisisSeverity.LOW
        else:
            return CrisisSeverity.NONE
    
    def _calculate_assessment_confidence(
        self,
        text: str,
        domain_risks: Dict[RiskDomain, float],
        context: Optional[CrisisContext]
    ) -> float:
        """Calculate confidence in the assessment."""
        confidence_factors = []
        
        # Text quality factor
        text_length = len(text.split())
        if text_length >= 20:
            confidence_factors.append(0.9)
        elif text_length >= 10:
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(0.5)
        
        # Domain consistency factor
        domain_scores = list(domain_risks.values())
        if domain_scores:
            domain_variance = np.var(domain_scores)
            consistency_factor = max(0.5, 1.0 - (domain_variance * 2))
            confidence_factors.append(consistency_factor)
        
        # Context availability factor
        if context:
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.6)
        
        return np.mean(confidence_factors)
    
    async def _generate_recommendations(
        self,
        severity: CrisisSeverity,
        domain_risks: Dict[RiskDomain, float],
        context: Optional[CrisisContext]
    ) -> List[str]:
        """Generate intervention recommendations based on assessment."""
        recommendations = []
        
        # Severity-based recommendations
        if severity in [CrisisSeverity.IMMINENT, CrisisSeverity.CRITICAL]:
            recommendations.extend([
                "Immediate safety assessment required",
                "Contact emergency services if imminent danger",
                "Crisis hotline intervention",
                "Emergency mental health evaluation"
            ])
        elif severity == CrisisSeverity.HIGH:
            recommendations.extend([
                "Urgent professional mental health referral",
                "Crisis safety planning",
                "Increased monitoring and support"
            ])
        elif severity == CrisisSeverity.MEDIUM:
            recommendations.extend([
                "Mental health professional consultation",
                "Safety planning discussion",
                "Peer support resources"
            ])
        
        # Domain-specific recommendations
        high_risk_domains = [domain for domain, score in domain_risks.items() if score >= 0.6]
        
        for domain in high_risk_domains:
            if domain == RiskDomain.SUICIDE:
                recommendations.append("Suicide risk assessment and safety planning")
            elif domain == RiskDomain.SELF_HARM:
                recommendations.append("Self-harm reduction strategies and alternatives")
            elif domain == RiskDomain.SUBSTANCE_ABUSE:
                recommendations.append("Substance abuse evaluation and treatment resources")
            elif domain == RiskDomain.VIOLENCE:
                recommendations.append("Violence risk assessment and anger management")
        
        return list(set(recommendations))
    
    async def _identify_protective_factors(
        self, 
        text: str, 
        context: Optional[CrisisContext]
    ) -> List[str]:
        """Identify protective factors in the assessment."""
        protective_factors = []
        text_lower = text.lower()
        
        # Text-based protective factors
        protective_indicators = {
            "hope": ["hope", "hopeful", "looking forward", "future", "tomorrow"],
            "support": ["family", "friends", "support", "help", "there for me"],
            "coping": ["meditation", "therapy", "exercise", "music", "art"],
            "meaning": ["purpose", "meaning", "important", "goal", "dream"]
        }
        
        for factor, indicators in protective_indicators.items():
            if any(indicator in text_lower for indicator in indicators):
                protective_factors.append(factor)
        
        # Context-based protective factors
        if context:
            if context.support_available:
                protective_factors.append("available_support_system")
            if context.therapy_engaged:
                protective_factors.append("therapeutic_engagement")
            if context.current_medications:
                protective_factors.append("medication_compliance")
        
        return protective_factors
    
    def _requires_escalation(
        self, 
        severity: CrisisSeverity, 
        domain_risks: Dict[RiskDomain, float]
    ) -> bool:
        """Determine if the case requires escalation."""
        if severity in [CrisisSeverity.IMMINENT, CrisisSeverity.CRITICAL]:
            return True
        
        critical_domains = [RiskDomain.SUICIDE, RiskDomain.VIOLENCE]
        for domain in critical_domains:
            if domain_risks.get(domain, 0.0) >= 0.8:
                return True
        
        return False
    
    def _calculate_urgency_score(
        self,
        severity: CrisisSeverity,
        domain_risks: Dict[RiskDomain, float],
        context: Optional[CrisisContext]
    ) -> float:
        """Calculate urgency score for intervention timing."""
        base_urgency = {
            CrisisSeverity.IMMINENT: 1.0,
            CrisisSeverity.CRITICAL: 0.9,
            CrisisSeverity.HIGH: 0.7,
            CrisisSeverity.MEDIUM: 0.5,
            CrisisSeverity.LOW: 0.3,
            CrisisSeverity.NONE: 0.1
        }.get(severity, 0.1)
        
        # Adjust based on specific risks
        max_domain_risk = max(domain_risks.values()) if domain_risks else 0.0
        adjusted_urgency = (base_urgency * 0.7) + (max_domain_risk * 0.3)
        
        # Context modifiers
        if context and not context.support_available:
            adjusted_urgency *= 1.2
        
        return min(1.0, adjusted_urgency)
    
    def _extract_primary_concerns(self, domain_risks: Dict[RiskDomain, float]) -> List[str]:
        """Extract primary concerns from domain analysis."""
        concerns = []
        sorted_domains = sorted(domain_risks.items(), key=lambda x: x[1], reverse=True)
        
        for domain, risk_score in sorted_domains:
            if risk_score >= 0.4:
                concerns.append(domain.value)
            if len(concerns) >= 3:
                break
        
        return concerns
    
    def _generate_assessment_id(self, text: str, user_id: Optional[str]) -> str:
        """Generate unique assessment ID."""
        content = {
            "text_hash": hashlib.sha256(text.encode()).hexdigest()[:16],
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        return hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()[:16]
    
    def _hash_user_id(self, user_id: str) -> str:
        """Hash user ID for privacy compliance."""
        return hashlib.sha256(user_id.encode()).hexdigest()[:16]
    
    def _get_cached_assessment(self, assessment_id: str) -> Optional[RiskAssessment]:
        """Get cached assessment if available."""
        return self._assessment_cache.get(assessment_id)
    
    def _cache_assessment(self, assessment: RiskAssessment) -> None:
        """Cache assessment for performance."""
        self._assessment_cache[assessment.assessment_id] = assessment
        
        if len(self._assessment_cache) > self.cache_size:
            oldest_key = min(self._assessment_cache.keys(), 
                           key=lambda k: self._assessment_cache[k].created_at)
            del self._assessment_cache[oldest_key]
    
    async def _store_assessment(
        self, 
        user_id: Optional[str], 
        assessment: RiskAssessment
    ) -> None:
        """Store assessment in user history."""
        if not user_id:
            return
        
        history_entry = {
            "assessment_id": assessment.assessment_id,
            "severity": assessment.severity.value,
            "confidence": assessment.confidence,
            "urgency_score": assessment.urgency_score,
            "escalation_required": assessment.escalation_required,
            "primary_concerns": assessment.primary_concerns,
            "timestamp": assessment.created_at.isoformat()
        }
        
        self._user_histories[user_id].append(history_entry)


# Convenience functions
async def assess_crisis_risk(
    text: str,
    user_id: Optional[str] = None,
    context: Optional[CrisisContext] = None
) -> RiskAssessment:
    """Convenience function for crisis risk assessment."""
    classifier = CrisisClassifier()
    return await classifier.assess_crisis_risk(text, user_id=user_id, context=context)

def create_crisis_context(
    user_id: Optional[str] = None,
    time_of_day: str = "day",
    support_available: bool = True,
    therapy_engaged: bool = False,
    previous_episodes: int = 0
) -> CrisisContext:
    """Convenience function to create crisis context."""
    return CrisisContext(
        user_id=user_id,
        time_of_day=time_of_day,
        support_available=support_available,
        therapy_engaged=therapy_engaged,
        previous_episodes=previous_episodes
    ) 