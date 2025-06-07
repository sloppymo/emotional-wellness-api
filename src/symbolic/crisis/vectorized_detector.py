"""
Vectorized Crisis Detection Module

This module provides efficient crisis pattern detection using vectorization
and machine learning techniques for improved performance.

basically fancy keyword matching with math behind it. works surprisingly well
"""

import os
import json
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import pickle
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer  # turn words into numbers
from sklearn.metrics.pairwise import cosine_similarity      # measure how similar things are
from pydantic import BaseModel, Field

from ...structured_logging.phi_logger import log_phi_access
from ...utils.structured_logging import get_logger

logger = get_logger(__name__)


class CrisisPattern(BaseModel):
    """Model for crisis pattern definition - what counts as a crisis"""
    pattern_id: str = Field(..., description="Unique identifier for this pattern")
    name: str = Field(..., description="Name of the pattern")
    description: str = Field(..., description="Description of the pattern")
    keywords: List[str] = Field(..., description="Keywords associated with this pattern")
    severity_scale: float = Field(..., description="Base severity scale (0-1)")  # how bad is this
    category: str = Field(..., description="Pattern category")
    example_phrases: List[str] = Field(..., description="Example phrases that match this pattern")


class CrisisDetectionResult(BaseModel):
    """Model for crisis detection result - what we found and how bad it is"""
    detected: bool = Field(..., description="Whether crisis was detected")
    severity: str = Field(..., description="Crisis severity level")  # low/moderate/high/severe
    confidence: float = Field(..., description="Confidence score (0-1)")  # how sure we are
    patterns: List[str] = Field(..., description="Detected patterns")
    top_matches: List[Dict[str, Any]] = Field(..., description="Top matching patterns with scores")
    risk_factors: Dict[str, Any] = Field(default_factory=dict, description="Risk factors")
    recommendations: List[str] = Field(default_factory=list, description="Recommended actions")


class VectorizedCrisisDetector:
    """
    Crisis detector using vectorization for efficiency.
    
    Features:
    - TF-IDF vectorization for fast pattern matching - turns words into math
    - Cosine similarity for semantic matching - figures out if things mean the same thing
    - Pre-computed vectors for common crisis patterns - we already know the dangerous phrases
    - Pluggable crisis pattern definitions - can add new patterns without rewriting code
    
    this is where we catch people who need help immediately
    """
    
    def __init__(self, patterns_path: Optional[str] = None):
        """
        Initialize the vectorized crisis detector.
        
        set up all the ML stuff and load the crisis patterns
        
        Args:
            patterns_path: Optional path to crisis pattern definitions
        """
        # TF-IDF magic - converts text to numbers for comparison
        self.vectorizer = TfidfVectorizer(
            max_features=1000,     # keep only the 1000 most important words
            stop_words="english",  # ignore "the", "and", etc
            ngram_range=(1, 3)     # look at 1-3 word phrases
        )
        
        # Load patterns - the list of things we're looking for
        if patterns_path:
            self.patterns_file = patterns_path
        else:
            # Default to package location - crisis_patterns.json in data folder
            module_dir = os.path.dirname(os.path.abspath(__file__))
            self.patterns_file = os.path.join(module_dir, "data", "crisis_patterns.json")
            
        self.crisis_patterns = self._load_crisis_patterns()
        
        # Prepare vectorizer - teach it what words matter
        self._prepare_vectorizer()
        
        # Pre-compute pattern vectors - convert all patterns to numbers ahead of time
        self.pattern_vectors = self._vectorize_patterns()
        
        # Crisis severity thresholds - made-up numbers that seem to work
        self.severity_thresholds = {
            "low": 0.3,      # barely a crisis
            "moderate": 0.5,  # definitely concerning
            "high": 0.7,     # get help now
            "severe": 0.85   # emergency level
        }
        
        logger.info(f"Vectorized crisis detector initialized with {len(self.crisis_patterns)} patterns")
    
    def _load_crisis_patterns(self) -> List[CrisisPattern]:
        """
        Load crisis pattern definitions from file.
        
        read the json file with all the dangerous phrases and their severity levels
        
        Returns:
            List of crisis patterns
        """
        try:
            patterns_path = Path(self.patterns_file)
            
            # Create default patterns file if it doesn't exist - first run setup
            if not patterns_path.exists():
                self._create_default_patterns_file(patterns_path)
                
            # Load patterns from file
            with open(patterns_path, "r") as f:
                patterns_data = json.load(f)
                
            # Parse into models - convert json to python objects
            patterns = [CrisisPattern(**pattern) for pattern in patterns_data]
            logger.info(f"Loaded {len(patterns)} crisis patterns from {self.patterns_file}")
            return patterns
            
        except Exception as e:
            logger.error(f"Error loading crisis patterns: {e}")
            # Return default patterns - fallback if file is broken
            return self._get_default_patterns()
    
    def _create_default_patterns_file(self, path: Path):
        """Create default patterns file if it doesn't exist - first run initialization"""
        # Ensure directory exists
        os.makedirs(path.parent, exist_ok=True)
        
        # Write default patterns - save the hardcoded patterns to a file
        with open(path, "w") as f:
            json.dump(
                [pattern.model_dump() for pattern in self._get_default_patterns()],
                f, 
                indent=2
            )
        
        logger.info(f"Created default crisis patterns file at {path}")
    
    def _get_default_patterns(self) -> List[CrisisPattern]:
        """
        Get default crisis patterns.
        
        the hardcoded list of things that indicate someone needs help immediately
        these patterns come from clinical literature and experience
        
        Returns:
            List of default crisis patterns
        """
        default_patterns = [
            CrisisPattern(
                pattern_id="suicide-ideation",
                name="Suicide Ideation",
                description="Expressions of suicidal thoughts or intentions",  # the big one
                keywords=["suicide", "kill myself", "end my life", "better off dead", "no reason to live"],
                severity_scale=0.9,  # extremely serious
                category="self-harm",
                example_phrases=[
                    "I want to kill myself",
                    "I'm thinking about ending it all",
                    "Everyone would be better off without me",
                    "I can't go on anymore"
                ]
            ),
            CrisisPattern(
                pattern_id="hopelessness",
                name="Hopelessness", 
                description="Expressions of deep hopelessness and despair",  # precursor to suicide
                keywords=["hopeless", "pointless", "never get better", "no future", "trapped"],
                severity_scale=0.7,  # high concern but not immediate emergency
                category="depression",
                example_phrases=[
                    "There's no point to anything anymore",
                    "Things will never get better",
                    "I'm trapped and can't escape",
                    "I see no future for myself"
                ]
            ),
            CrisisPattern(
                pattern_id="severe-anxiety",
                name="Severe Anxiety",
                description="Expressions of overwhelming anxiety or panic",  # can be debilitating
                keywords=["panic", "can't breathe", "heart racing", "terrified", "overwhelming anxiety"],
                severity_scale=0.6,  # moderate severity
                category="anxiety",
                example_phrases=[
                    "I can't breathe and my heart is racing",
                    "I'm having a panic attack",
                    "The anxiety is completely overwhelming me",
                    "I'm terrified and can't function"
                ]
            ),
            CrisisPattern(
                pattern_id="self-harm",
                name="Self-Harm",
                description="Expressions of self-harming behaviors or intentions",  # immediate danger
                keywords=["cut myself", "harm myself", "self-harm", "hurt myself", "burning myself"],
                severity_scale=0.8,  # very serious
                category="self-harm",
                example_phrases=[
                    "I've been cutting myself",
                    "I want to hurt myself",
                    "I'm having urges to self-harm",
                    "I burned myself last night"
                ]
            ),
            CrisisPattern(
                pattern_id="violence",
                name="Violent Thoughts",
                description="Expressions of violent thoughts or intentions toward others",
                keywords=["hurt them", "want to kill", "make them pay", "violent thoughts", "revenge"],
                severity_scale=0.85,
                category="violence",
                example_phrases=[
                    "I want to make them pay for what they did",
                    "I'm having violent thoughts toward my boss",
                    "Sometimes I think about hurting people who hurt me",
                    "I'm afraid I might hurt someone"
                ]
            )
        ]
        
        return default_patterns
    
    def _prepare_vectorizer(self):
        """Prepare the TF-IDF vectorizer with example phrases."""
        # Gather all example phrases from patterns
        all_examples = []
        for pattern in self.crisis_patterns:
            all_examples.extend(pattern.example_phrases)
            all_examples.extend(pattern.keywords)
            
        # Fit vectorizer on examples
        if all_examples:
            self.vectorizer.fit(all_examples)
        else:
            # Fit on empty list as fallback
            self.vectorizer.fit([""])
    
    def _vectorize_patterns(self) -> Dict[str, np.ndarray]:
        """
        Pre-compute vectors for all patterns.
        
        Returns:
            Dictionary mapping pattern IDs to vectors
        """
        pattern_vectors = {}
        
        for pattern in self.crisis_patterns:
            # Combine keywords and examples for better representation
            pattern_text = " ".join(pattern.keywords + pattern.example_phrases)
            
            # Vectorize
            pattern_vector = self.vectorizer.transform([pattern_text])
            
            # Store
            pattern_vectors[pattern.pattern_id] = pattern_vector
            
        return pattern_vectors
    
    def _score_to_severity(self, score: float) -> str:
        """
        Convert similarity score to severity level.
        
        Args:
            score: Similarity score (0-1)
            
        Returns:
            Severity level string
        """
        if score >= self.severity_thresholds["severe"]:
            return "severe"
        elif score >= self.severity_thresholds["high"]:
            return "high"
        elif score >= self.severity_thresholds["moderate"]:
            return "moderate"
        elif score >= self.severity_thresholds["low"]:
            return "low"
        else:
            return "none"
            
    async def detect_crisis_patterns(self, 
                                   text: str, 
                                   user_id: Optional[str] = None, 
                                   context: Optional[Dict[str, Any]] = None) -> CrisisDetectionResult:
        """
        Detect crisis patterns using vector similarity.
        
        Args:
            text: Text to analyze
            user_id: Optional user ID for logging
            context: Optional additional context
            
        Returns:
            Crisis detection result
        """
        # Log PHI access
        if user_id:
            await log_phi_access(
                user_id=user_id,
                action="analyze_crisis_risk",
                system_component="VectorizedCrisisDetector",
                access_purpose="crisis_detection",
                data_elements=["text_input"],
                additional_context={
                    "operation": "detect_crisis_patterns",
                    "text_length": len(text)
                }
            )
        
        # Vectorize input text
        text_vector = self.vectorizer.transform([text])
        
        # Calculate similarity scores with all patterns
        scores = {}
        for pattern_id, pattern_vector in self.pattern_vectors.items():
            # Calculate cosine similarity
            similarity = cosine_similarity(text_vector, pattern_vector)[0][0]
            scores[pattern_id] = float(similarity)
            
        # Get top matching patterns
        top_patterns = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Extract pattern details for top matches
        top_matches = []
        for pattern_id, score in top_patterns:
            # Find pattern by ID
            pattern = next((p for p in self.crisis_patterns if p.pattern_id == pattern_id), None)
            if pattern and score > 0.1:  # Only include non-trivial matches
                top_matches.append({
                    "pattern_id": pattern_id,
                    "name": pattern.name,
                    "score": score,
                    "category": pattern.category,
                    "severity_contribution": score * pattern.severity_scale
                })
        
        # Calculate overall metrics
        if top_matches:
            # Use highest individual severity contribution as main score
            max_severity = max(m["severity_contribution"] for m in top_matches)
            
            # Determine overall severity
            severity = self._score_to_severity(max_severity)
            
            # Get detected pattern names
            patterns = [m["name"] for m in top_matches if m["score"] > self.severity_thresholds["low"]]
            
            # Set detected flag
            detected = max_severity >= self.severity_thresholds["low"]
        else:
            max_severity = 0.0
            severity = "none"
            patterns = []
            detected = False
        
        # Generate recommendations based on severity
        recommendations = self._generate_recommendations(severity, top_matches)
        
        # Create result
        result = CrisisDetectionResult(
            detected=detected,
            severity=severity,
            confidence=float(max_severity),
            patterns=patterns,
            top_matches=top_matches,
            recommendations=recommendations
        )
        
        return result
    
    def _generate_recommendations(self, severity: str, top_matches: List[Dict[str, Any]]) -> List[str]:
        """
        Generate recommendations based on severity and patterns.
        
        Args:
            severity: Detected severity level
            top_matches: Top matching patterns
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Basic recommendations by severity
        if severity == "severe":
            recommendations.append("Immediate intervention may be required")
            recommendations.append("Consider emergency services referral")
        elif severity == "high":
            recommendations.append("Prompt clinical assessment recommended")
            recommendations.append("Follow crisis protocol")
        elif severity == "moderate":
            recommendations.append("Schedule follow-up assessment")
            recommendations.append("Offer additional support resources")
        elif severity == "low":
            recommendations.append("Monitor for changes in status")
            recommendations.append("Provide self-care resources")
            
        # Pattern-specific recommendations
        categories = set(match["category"] for match in top_matches)
        
        if "self-harm" in categories:
            recommendations.append("Assess self-harm risk factors")
            recommendations.append("Review safety planning")
            
        if "violence" in categories:
            recommendations.append("Evaluate risk to others")
            recommendations.append("Consider duty to warn/protect obligations")
            
        if "depression" in categories:
            recommendations.append("Screen for additional depression symptoms")
            
        if "anxiety" in categories:
            recommendations.append("Provide anxiety management techniques")
            
        return recommendations
        
    def save_vectorizer(self, path: str):
        """
        Save the trained vectorizer for future use.
        
        Args:
            path: Path to save the vectorizer
        """
        with open(path, "wb") as f:
            pickle.dump(self.vectorizer, f)
            
    @classmethod
    def load_with_vectorizer(cls, vectorizer_path: str, patterns_path: Optional[str] = None):
        """
        Load detector with pre-trained vectorizer.
        
        Args:
            vectorizer_path: Path to saved vectorizer
            patterns_path: Optional path to patterns file
            
        Returns:
            Initialized detector
        """
        detector = cls(patterns_path)
        
        # Load vectorizer
        with open(vectorizer_path, "rb") as f:
            detector.vectorizer = pickle.load(f)
            
        # Re-compute pattern vectors with loaded vectorizer
        detector.pattern_vectors = detector._vectorize_patterns()
        
        return detector


# Global instance
_crisis_detector = None

async def get_crisis_detector() -> VectorizedCrisisDetector:
    """
    Get the global crisis detector instance.
    
    Returns:
        The global crisis detector instance
    """
    global _crisis_detector
    
    if _crisis_detector is None:
        _crisis_detector = VectorizedCrisisDetector()
    
    return _crisis_detector
