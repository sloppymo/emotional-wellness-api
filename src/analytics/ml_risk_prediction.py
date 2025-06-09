"""
ML-Driven Risk Prediction Models for Emotional Wellness

This module provides machine learning models for:
- Crisis risk prediction and early warning systems
- Therapeutic progress prediction and outcome forecasting
- Personalized intervention recommendation systems
- Longitudinal emotional state modeling
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
import asyncio
from enum import Enum
import joblib
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, mean_squared_error, r2_score
import warnings
warnings.filterwarnings('ignore')

from src.utils.structured_logging import get_logger
from src.models.emotional_state import SymbolicMapping, EmotionalMetaphor

logger = get_logger(__name__)

class RiskLevel(Enum):
    """Risk level enumeration for crisis prediction"""
    MINIMAL = "minimal"
    LOW = "low" 
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"

class ProgressDirection(Enum):
    """Direction of therapeutic progress"""
    SIGNIFICANT_IMPROVEMENT = "significant_improvement"
    MODERATE_IMPROVEMENT = "moderate_improvement"
    STABLE = "stable"
    MILD_DECLINE = "mild_decline"
    SIGNIFICANT_DECLINE = "significant_decline"

@dataclass
class RiskPrediction:
    """Risk prediction result with confidence and contributing factors"""
    risk_level: RiskLevel
    confidence: float
    probability_scores: Dict[str, float]
    contributing_factors: List[str]
    recommended_actions: List[str]
    prediction_timestamp: datetime
    model_version: str
    feature_importance: Dict[str, float] = field(default_factory=dict)

@dataclass
class ProgressPrediction:
    """Therapeutic progress prediction result"""
    predicted_direction: ProgressDirection
    confidence: float
    expected_timeline_days: int
    progress_score: float  # -1.0 to 1.0 scale
    contributing_factors: List[str]
    recommended_interventions: List[str]
    prediction_timestamp: datetime
    model_version: str

@dataclass
class InterventionRecommendation:
    """Personalized intervention recommendation"""
    intervention_type: str
    priority: str  # "low", "medium", "high", "urgent"
    confidence: float
    expected_effectiveness: float
    rationale: str
    recommended_timing: str
    duration_estimate: Optional[int] = None  # minutes
    prerequisites: List[str] = field(default_factory=list)
    contraindications: List[str] = field(default_factory=list)

class EmotionalFeatureExtractor:
    """Extract features from emotional state data for ML models"""
    
    def __init__(self):
        self.feature_names = [
            # Symbolic features
            'primary_symbol_encoded', 'archetype_encoded', 'num_alternative_symbols',
            'num_metaphors', 'avg_metaphor_confidence', 'symbol_diversity',
            
            # Emotional features
            'valence', 'arousal', 'confidence', 'emotional_intensity',
            'emotional_stability', 'valence_arousal_interaction',
            
            # Temporal features
            'session_number', 'days_since_start', 'time_of_day_encoded',
            'day_of_week_encoded', 'session_frequency',
            
            # Biomarker features
            'heart_rate_norm', 'respiratory_rate_norm', 'skin_conductance_norm',
            'biomarker_stress_index', 'biomarker_consistency',
            
            # Historical features
            'valence_trend_7d', 'arousal_trend_7d', 'symbol_change_frequency',
            'crisis_history_count', 'progress_velocity',
            
            # Linguistic features
            'text_length', 'sentiment_polarity', 'emotional_word_count',
            'crisis_keywords_count', 'hope_keywords_count'
        ]
        
        # Encoding mappings
        self.symbol_encoder = {
            'water': 0, 'fire': 1, 'earth': 2, 'air': 3, 'light': 4,
            'darkness': 5, 'mountain': 6, 'forest': 7, 'ocean': 8, 'path': 9
        }
        
        self.archetype_encoder = {
            'hero': 0, 'shadow': 1, 'anima': 2, 'animus': 3, 'mentor': 4,
            'trickster': 5, 'self': 6, 'persona': 7, 'caregiver': 8, 'sage': 9
        }
    
    def extract_features(
        self,
        current_mapping: SymbolicMapping,
        user_history: List[SymbolicMapping],
        biomarkers: Optional[Dict[str, float]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> np.ndarray:
        """Extract feature vector from emotional state data"""
        
        features = {}
        
        # Symbolic features
        features['primary_symbol_encoded'] = self.symbol_encoder.get(current_mapping.primary_symbol, -1)
        features['archetype_encoded'] = self.archetype_encoder.get(current_mapping.archetype, -1)
        features['num_alternative_symbols'] = len(current_mapping.alternative_symbols)
        features['num_metaphors'] = len(current_mapping.metaphors)
        features['avg_metaphor_confidence'] = np.mean([m.confidence for m in current_mapping.metaphors]) if current_mapping.metaphors else 0
        features['symbol_diversity'] = len(set([current_mapping.primary_symbol] + current_mapping.alternative_symbols))
        
        # Emotional features
        features['valence'] = current_mapping.valence
        features['arousal'] = current_mapping.arousal
        features['confidence'] = current_mapping.confidence
        features['emotional_intensity'] = abs(current_mapping.valence) + current_mapping.arousal
        features['valence_arousal_interaction'] = current_mapping.valence * current_mapping.arousal
        
        # Emotional stability (variance over recent history)
        if len(user_history) >= 3:
            recent_valences = [m.valence for m in user_history[-5:]]
            features['emotional_stability'] = 1.0 / (1.0 + np.var(recent_valences))
        else:
            features['emotional_stability'] = 0.5
        
        # Temporal features
        features['session_number'] = len(user_history) + 1
        features['days_since_start'] = self._calculate_days_since_start(user_history)
        features['time_of_day_encoded'] = self._encode_time_of_day(current_mapping.timestamp)
        features['day_of_week_encoded'] = current_mapping.timestamp.weekday()
        features['session_frequency'] = self._calculate_session_frequency(user_history)
        
        # Biomarker features
        if biomarkers:
            features['heart_rate_norm'] = self._normalize_heart_rate(biomarkers.get('heart_rate', 70))
            features['respiratory_rate_norm'] = self._normalize_respiratory_rate(biomarkers.get('respiratory_rate', 16))
            features['skin_conductance_norm'] = biomarkers.get('skin_conductance', 0.5)
            features['biomarker_stress_index'] = self._calculate_stress_index(biomarkers)
            features['biomarker_consistency'] = 0.8  # Placeholder
        else:
            features.update({
                'heart_rate_norm': 0.5, 'respiratory_rate_norm': 0.5,
                'skin_conductance_norm': 0.5, 'biomarker_stress_index': 0.5,
                'biomarker_consistency': 0.5
            })
        
        # Historical trend features
        if len(user_history) >= 7:
            features['valence_trend_7d'] = self._calculate_valence_trend(user_history[-7:])
            features['arousal_trend_7d'] = self._calculate_arousal_trend(user_history[-7:])
            features['symbol_change_frequency'] = self._calculate_symbol_change_frequency(user_history[-7:])
        else:
            features.update({'valence_trend_7d': 0, 'arousal_trend_7d': 0, 'symbol_change_frequency': 0})
        
        features['crisis_history_count'] = self._count_crisis_history(user_history)
        features['progress_velocity'] = self._calculate_progress_velocity(user_history)
        
        # Linguistic features (would be extracted from input text in real implementation)
        features['text_length'] = 100  # Placeholder
        features['sentiment_polarity'] = current_mapping.valence  # Simplified
        features['emotional_word_count'] = 5  # Placeholder
        features['crisis_keywords_count'] = 0  # Placeholder
        features['hope_keywords_count'] = 1 if current_mapping.valence > 0 else 0
        
        # Convert to numpy array in consistent order
        return np.array([features[name] for name in self.feature_names])
    
    def _calculate_days_since_start(self, history: List[SymbolicMapping]) -> float:
        """Calculate days since first session"""
        if not history:
            return 0
        first_session = min(history, key=lambda x: x.timestamp)
        return (datetime.now() - first_session.timestamp).days
    
    def _encode_time_of_day(self, timestamp: datetime) -> float:
        """Encode time of day as cyclic feature"""
        hour = timestamp.hour
        return np.sin(2 * np.pi * hour / 24)
    
    def _calculate_session_frequency(self, history: List[SymbolicMapping]) -> float:
        """Calculate session frequency (sessions per week)"""
        if len(history) < 2:
            return 0
        
        time_span = (history[-1].timestamp - history[0].timestamp).days
        if time_span == 0:
            return 7  # Multiple sessions in one day
        
        return len(history) / (time_span / 7)
    
    def _normalize_heart_rate(self, hr: float) -> float:
        """Normalize heart rate (50-150 bpm range)"""
        return (hr - 50) / 100
    
    def _normalize_respiratory_rate(self, rr: float) -> float:
        """Normalize respiratory rate (8-25 bpm range)"""
        return (rr - 8) / 17
    
    def _calculate_stress_index(self, biomarkers: Dict[str, float]) -> float:
        """Calculate composite stress index from biomarkers"""
        hr_stress = max(0, (biomarkers.get('heart_rate', 70) - 70) / 50)
        rr_stress = max(0, (biomarkers.get('respiratory_rate', 16) - 16) / 9)
        sc_stress = biomarkers.get('skin_conductance', 0.5)
        
        return (hr_stress + rr_stress + sc_stress) / 3
    
    def _calculate_valence_trend(self, recent_history: List[SymbolicMapping]) -> float:
        """Calculate valence trend over recent sessions"""
        valences = [m.valence for m in recent_history]
        if len(valences) < 2:
            return 0
        
        # Simple linear trend
        x = np.arange(len(valences))
        slope = np.polyfit(x, valences, 1)[0]
        return slope
    
    def _calculate_arousal_trend(self, recent_history: List[SymbolicMapping]) -> float:
        """Calculate arousal trend over recent sessions"""
        arousals = [m.arousal for m in recent_history]
        if len(arousals) < 2:
            return 0
        
        x = np.arange(len(arousals))
        slope = np.polyfit(x, arousals, 1)[0]
        return slope
    
    def _calculate_symbol_change_frequency(self, recent_history: List[SymbolicMapping]) -> float:
        """Calculate how frequently primary symbols change"""
        if len(recent_history) < 2:
            return 0
        
        changes = 0
        for i in range(1, len(recent_history)):
            if recent_history[i].primary_symbol != recent_history[i-1].primary_symbol:
                changes += 1
        
        return changes / (len(recent_history) - 1)
    
    def _count_crisis_history(self, history: List[SymbolicMapping]) -> int:
        """Count crisis-related symbols in history"""
        crisis_symbols = {'darkness', 'void', 'abyss', 'storm', 'collapse'}
        count = 0
        for mapping in history:
            if mapping.primary_symbol in crisis_symbols:
                count += 1
            if any(symbol in crisis_symbols for symbol in mapping.alternative_symbols):
                count += 1
        return count
    
    def _calculate_progress_velocity(self, history: List[SymbolicMapping]) -> float:
        """Calculate rate of emotional progress"""
        if len(history) < 3:
            return 0
        
        # Calculate progress as improvement in valence over time
        recent_valences = [m.valence for m in history[-5:]]
        if len(recent_valences) < 2:
            return 0
        
        # Calculate acceleration in valence improvement
        improvements = []
        for i in range(1, len(recent_valences)):
            improvements.append(recent_valences[i] - recent_valences[i-1])
        
        return np.mean(improvements) if improvements else 0

class CrisisRiskPredictor:
    """ML model for predicting crisis risk levels"""
    
    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        self.scaler = StandardScaler()
        self.feature_extractor = EmotionalFeatureExtractor()
        self.is_trained = False
        self.model_version = "1.0.0"
    
    def train(self, training_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Train the crisis risk prediction model"""
        
        logger.info("Training crisis risk prediction model")
        
        # Extract features and labels
        X = []
        y = []
        
        for sample in training_data:
            features = self.feature_extractor.extract_features(
                current_mapping=sample['mapping'],
                user_history=sample.get('history', []),
                biomarkers=sample.get('biomarkers'),
                context=sample.get('context')
            )
            X.append(features)
            y.append(sample['risk_level'].value)
        
        X = np.array(X)
        y = np.array(y)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate model
        train_score = self.model.score(X_train_scaled, y_train)
        test_score = self.model.score(X_test_scaled, y_test)
        
        self.is_trained = True
        
        logger.info(f"Crisis risk model trained: train_score={train_score:.3f}, test_score={test_score:.3f}")
        
        return {
            'train_accuracy': train_score,
            'test_accuracy': test_score,
            'model_version': self.model_version
        }
    
    async def predict_risk(
        self,
        current_mapping: SymbolicMapping,
        user_history: List[SymbolicMapping],
        biomarkers: Optional[Dict[str, float]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> RiskPrediction:
        """Predict crisis risk level for current emotional state"""
        
        if not self.is_trained:
            # Use rule-based fallback if model not trained
            return self._rule_based_risk_assessment(current_mapping, user_history, biomarkers)
        
        # Extract features
        features = self.feature_extractor.extract_features(
            current_mapping=current_mapping,
            user_history=user_history,
            biomarkers=biomarkers,
            context=context
        )
        
        # Scale features
        features_scaled = self.scaler.transform(features.reshape(1, -1))
        
        # Predict
        risk_probabilities = self.model.predict_proba(features_scaled)[0]
        predicted_class = self.model.predict(features_scaled)[0]
        
        # Get class labels
        classes = self.model.classes_
        probability_scores = dict(zip(classes, risk_probabilities))
        
        # Get feature importance
        feature_importance = dict(zip(
            self.feature_extractor.feature_names,
            self.model.feature_importances_
        ))
        
        # Determine contributing factors
        contributing_factors = self._identify_contributing_factors(features, feature_importance)
        
        # Generate recommendations
        recommended_actions = self._generate_risk_recommendations(RiskLevel(predicted_class))
        
        return RiskPrediction(
            risk_level=RiskLevel(predicted_class),
            confidence=max(risk_probabilities),
            probability_scores=probability_scores,
            contributing_factors=contributing_factors,
            recommended_actions=recommended_actions,
            prediction_timestamp=datetime.now(),
            model_version=self.model_version,
            feature_importance=feature_importance
        )
    
    def _rule_based_risk_assessment(
        self,
        current_mapping: SymbolicMapping,
        user_history: List[SymbolicMapping],
        biomarkers: Optional[Dict[str, float]]
    ) -> RiskPrediction:
        """Fallback rule-based risk assessment"""
        
        risk_score = 0
        contributing_factors = []
        
        # Valence-based risk
        if current_mapping.valence < -0.7:
            risk_score += 3
            contributing_factors.append("Very negative emotional valence")
        elif current_mapping.valence < -0.3:
            risk_score += 1
            contributing_factors.append("Negative emotional valence")
        
        # Arousal-based risk
        if current_mapping.arousal > 0.8:
            risk_score += 2
            contributing_factors.append("High emotional arousal")
        
        # Symbol-based risk
        crisis_symbols = {'darkness', 'void', 'abyss', 'collapse', 'storm'}
        if current_mapping.primary_symbol in crisis_symbols:
            risk_score += 4
            contributing_factors.append(f"Crisis-related symbol: {current_mapping.primary_symbol}")
        
        # Archetype-based risk
        if current_mapping.archetype == 'shadow':
            risk_score += 2
            contributing_factors.append("Shadow archetype indicates inner conflict")
        
        # Biomarker risk
        if biomarkers:
            if biomarkers.get('heart_rate', 70) > 100:
                risk_score += 2
                contributing_factors.append("Elevated heart rate")
            if biomarkers.get('skin_conductance', 0.5) > 0.8:
                risk_score += 1
                contributing_factors.append("High stress indicators")
        
        # Historical risk
        if len(user_history) >= 3:
            recent_valences = [m.valence for m in user_history[-3:]]
            if all(v < -0.5 for v in recent_valences):
                risk_score += 3
                contributing_factors.append("Persistent negative emotional trend")
        
        # Determine risk level
        if risk_score >= 8:
            risk_level = RiskLevel.CRITICAL
        elif risk_score >= 6:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 4:
            risk_level = RiskLevel.MODERATE
        elif risk_score >= 2:
            risk_level = RiskLevel.LOW
        else:
            risk_level = RiskLevel.MINIMAL
        
        return RiskPrediction(
            risk_level=risk_level,
            confidence=0.7,  # Rule-based confidence
            probability_scores={risk_level.value: 0.7},
            contributing_factors=contributing_factors,
            recommended_actions=self._generate_risk_recommendations(risk_level),
            prediction_timestamp=datetime.now(),
            model_version="rule_based_1.0"
        )
    
    def _identify_contributing_factors(
        self,
        features: np.ndarray,
        feature_importance: Dict[str, float]
    ) -> List[str]:
        """Identify key contributing factors for risk prediction"""
        
        # Get top contributing features
        sorted_importance = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        top_features = sorted_importance[:5]
        
        factors = []
        for feature_name, importance in top_features:
            if importance > 0.05:  # Only include significant features
                factors.append(f"{feature_name} (importance: {importance:.2f})")
        
        return factors
    
    def _generate_risk_recommendations(self, risk_level: RiskLevel) -> List[str]:
        """Generate recommendations based on risk level"""
        
        recommendations = {
            RiskLevel.CRITICAL: [
                "Immediate crisis intervention required",
                "Contact emergency mental health services",
                "Ensure safety planning is in place",
                "Consider emergency hospitalization",
                "Activate crisis response team"
            ],
            RiskLevel.HIGH: [
                "Increase therapy session frequency",
                "Implement safety monitoring",
                "Contact support network",
                "Consider medication review",
                "Daily check-ins recommended"
            ],
            RiskLevel.MODERATE: [
                "Schedule additional therapy session",
                "Implement coping strategies",
                "Increase self-monitoring",
                "Consider support group participation",
                "Review current treatment plan"
            ],
            RiskLevel.LOW: [
                "Continue current treatment",
                "Practice mindfulness techniques",
                "Maintain regular therapy schedule",
                "Monitor emotional patterns",
                "Engage in self-care activities"
            ],
            RiskLevel.MINIMAL: [
                "Continue wellness maintenance",
                "Regular self-reflection",
                "Maintain healthy habits",
                "Consider growth-oriented activities",
                "Schedule routine check-in"
            ]
        }
        
        return recommendations[risk_level]

class ProgressPredictor:
    """ML model for predicting therapeutic progress"""
    
    def __init__(self):
        self.model = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=8,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.feature_extractor = EmotionalFeatureExtractor()
        self.is_trained = False
        self.model_version = "1.0.0"
    
    async def predict_progress(
        self,
        current_mapping: SymbolicMapping,
        user_history: List[SymbolicMapping],
        biomarkers: Optional[Dict[str, float]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ProgressPrediction:
        """Predict therapeutic progress direction and timeline"""
        
        if not self.is_trained:
            return self._rule_based_progress_assessment(current_mapping, user_history)
        
        # Extract features
        features = self.feature_extractor.extract_features(
            current_mapping=current_mapping,
            user_history=user_history,
            biomarkers=biomarkers,
            context=context
        )
        
        # Scale features
        features_scaled = self.scaler.transform(features.reshape(1, -1))
        
        # Predict progress score
        progress_score = self.model.predict(features_scaled)[0]
        
        # Convert to direction and timeline
        direction = self._score_to_direction(progress_score)
        timeline = self._estimate_timeline(progress_score, user_history)
        
        # Generate recommendations
        interventions = self._generate_progress_interventions(direction, progress_score)
        contributing_factors = self._identify_progress_factors(features, progress_score)
        
        return ProgressPrediction(
            predicted_direction=direction,
            confidence=0.8,  # Model confidence
            expected_timeline_days=timeline,
            progress_score=progress_score,
            contributing_factors=contributing_factors,
            recommended_interventions=interventions,
            prediction_timestamp=datetime.now(),
            model_version=self.model_version
        )
    
    def _rule_based_progress_assessment(
        self,
        current_mapping: SymbolicMapping,
        user_history: List[SymbolicMapping]
    ) -> ProgressPrediction:
        """Rule-based progress assessment fallback"""
        
        progress_score = 0
        factors = []
        
        # Analyze valence trend
        if len(user_history) >= 3:
            recent_valences = [m.valence for m in user_history[-5:]]
            current_valence = current_mapping.valence
            
            valence_trend = (current_valence - np.mean(recent_valences))
            progress_score += valence_trend * 0.5
            
            if valence_trend > 0.2:
                factors.append("Improving emotional valence")
            elif valence_trend < -0.2:
                factors.append("Declining emotional valence")
        
        # Analyze symbol progression
        growth_symbols = {'light', 'mountain', 'tree', 'path', 'river'}
        if current_mapping.primary_symbol in growth_symbols:
            progress_score += 0.3
            factors.append("Growth-oriented symbolic content")
        
        # Analyze confidence trends
        if current_mapping.confidence > 0.8:
            progress_score += 0.2
            factors.append("High processing confidence")
        
        direction = self._score_to_direction(progress_score)
        timeline = self._estimate_timeline(progress_score, user_history)
        
        return ProgressPrediction(
            predicted_direction=direction,
            confidence=0.6,
            expected_timeline_days=timeline,
            progress_score=progress_score,
            contributing_factors=factors,
            recommended_interventions=self._generate_progress_interventions(direction, progress_score),
            prediction_timestamp=datetime.now(),
            model_version="rule_based_1.0"
        )
    
    def _score_to_direction(self, score: float) -> ProgressDirection:
        """Convert numeric score to progress direction"""
        if score > 0.6:
            return ProgressDirection.SIGNIFICANT_IMPROVEMENT
        elif score > 0.2:
            return ProgressDirection.MODERATE_IMPROVEMENT
        elif score > -0.2:
            return ProgressDirection.STABLE
        elif score > -0.6:
            return ProgressDirection.MILD_DECLINE
        else:
            return ProgressDirection.SIGNIFICANT_DECLINE
    
    def _estimate_timeline(self, score: float, history: List[SymbolicMapping]) -> int:
        """Estimate timeline for progress changes"""
        base_timeline = 14  # 2 weeks base
        
        # Adjust based on progress score
        if abs(score) > 0.5:
            timeline = base_timeline // 2  # Faster change for high scores
        elif abs(score) < 0.2:
            timeline = base_timeline * 2  # Slower change for low scores
        else:
            timeline = base_timeline
        
        # Adjust based on history length (more data = more precise estimates)
        if len(history) > 10:
            timeline = int(timeline * 0.8)  # More confident with more data
        
        return max(7, min(90, timeline))  # Clamp between 1 week and 3 months
    
    def _identify_progress_factors(self, features: np.ndarray, score: float) -> List[str]:
        """Identify factors contributing to progress prediction"""
        factors = []
        
        if score > 0.3:
            factors.append("Positive therapeutic momentum")
        elif score < -0.3:
            factors.append("Concerning therapeutic trajectory")
        
        factors.append("Based on emotional pattern analysis")
        factors.append("Incorporating biomarker trends")
        
        return factors
    
    def _generate_progress_interventions(
        self,
        direction: ProgressDirection,
        score: float
    ) -> List[str]:
        """Generate intervention recommendations based on predicted progress"""
        
        interventions = {
            ProgressDirection.SIGNIFICANT_IMPROVEMENT: [
                "Continue current therapeutic approach",
                "Consider reducing session frequency gradually",
                "Introduce maintenance strategies",
                "Focus on relapse prevention"
            ],
            ProgressDirection.MODERATE_IMPROVEMENT: [
                "Maintain current therapeutic intensity",
                "Reinforce positive coping strategies",
                "Address remaining challenges",
                "Consider skills consolidation"
            ],
            ProgressDirection.STABLE: [
                "Review current treatment approach",
                "Consider alternative interventions",
                "Explore potential barriers",
                "Maintain therapeutic engagement"
            ],
            ProgressDirection.MILD_DECLINE: [
                "Increase therapeutic support",
                "Review medication if applicable",
                "Address emerging stressors",
                "Consider intensive interventions"
            ],
            ProgressDirection.SIGNIFICANT_DECLINE: [
                "Immediate therapeutic review required",
                "Consider crisis intervention",
                "Increase monitoring frequency",
                "Review safety planning"
            ]
        }
        
        return interventions[direction]

class InterventionRecommender:
    """ML-based intervention recommendation system"""
    
    def __init__(self):
        self.risk_predictor = CrisisRiskPredictor()
        self.progress_predictor = ProgressPredictor()
        
        # Intervention database
        self.interventions = {
            "breathing_exercise": {
                "type": "immediate_coping",
                "duration": 5,
                "effectiveness": 0.7,
                "contraindications": ["respiratory_issues"]
            },
            "grounding_technique": {
                "type": "anxiety_management", 
                "duration": 10,
                "effectiveness": 0.8,
                "contraindications": []
            },
            "mindfulness_meditation": {
                "type": "emotional_regulation",
                "duration": 15,
                "effectiveness": 0.75,
                "contraindications": ["severe_dissociation"]
            },
            "crisis_contact": {
                "type": "safety_intervention",
                "duration": 30,
                "effectiveness": 0.9,
                "contraindications": []
            },
            "cognitive_restructuring": {
                "type": "therapeutic_technique",
                "duration": 45,
                "effectiveness": 0.85,
                "contraindications": ["cognitive_impairment"]
            }
        }
    
    async def recommend_interventions(
        self,
        current_mapping: SymbolicMapping,
        user_history: List[SymbolicMapping],
        biomarkers: Optional[Dict[str, float]] = None,
        context: Optional[Dict[str, Any]] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> List[InterventionRecommendation]:
        """Generate personalized intervention recommendations"""
        
        # Get predictions
        risk_prediction = await self.risk_predictor.predict_risk(
            current_mapping, user_history, biomarkers, context
        )
        
        progress_prediction = await self.progress_predictor.predict_progress(
            current_mapping, user_history, biomarkers, context
        )
        
        recommendations = []
        
        # Risk-based interventions
        if risk_prediction.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recommendations.append(InterventionRecommendation(
                intervention_type="crisis_contact",
                priority="urgent",
                confidence=0.9,
                expected_effectiveness=0.9,
                rationale="High crisis risk detected",
                recommended_timing="immediate"
            ))
        
        # Emotional state-based interventions
        if current_mapping.arousal > 0.7:
            recommendations.append(InterventionRecommendation(
                intervention_type="grounding_technique",
                priority="high",
                confidence=0.8,
                expected_effectiveness=0.8,
                rationale="High arousal requires grounding",
                recommended_timing="within_5_minutes",
                duration_estimate=10
            ))
        
        if current_mapping.valence < -0.5:
            recommendations.append(InterventionRecommendation(
                intervention_type="cognitive_restructuring",
                priority="medium",
                confidence=0.75,
                expected_effectiveness=0.85,
                rationale="Negative emotional state",
                recommended_timing="within_24_hours",
                duration_estimate=45
            ))
        
        # Progress-based interventions
        if progress_prediction.predicted_direction == ProgressDirection.SIGNIFICANT_DECLINE:
            recommendations.append(InterventionRecommendation(
                intervention_type="mindfulness_meditation",
                priority="high",
                confidence=0.8,
                expected_effectiveness=0.75,
                rationale="Declining progress trend",
                recommended_timing="within_12_hours",
                duration_estimate=15
            ))
        
        # Filter and rank recommendations
        filtered_recommendations = self._filter_by_contraindications(
            recommendations, context, user_preferences
        )
        
        ranked_recommendations = self._rank_recommendations(filtered_recommendations)
        
        return ranked_recommendations[:5]  # Return top 5 recommendations
    
    def _filter_by_contraindications(
        self,
        recommendations: List[InterventionRecommendation],
        context: Optional[Dict[str, Any]],
        user_preferences: Optional[Dict[str, Any]]
    ) -> List[InterventionRecommendation]:
        """Filter recommendations based on contraindications"""
        
        user_conditions = context.get('medical_conditions', []) if context else []
        user_dislikes = user_preferences.get('disliked_interventions', []) if user_preferences else []
        
        filtered = []
        for rec in recommendations:
            intervention_info = self.interventions.get(rec.intervention_type, {})
            contraindications = intervention_info.get('contraindications', [])
            
            # Check medical contraindications
            if any(condition in contraindications for condition in user_conditions):
                continue
            
            # Check user preferences
            if rec.intervention_type in user_dislikes:
                continue
            
            filtered.append(rec)
        
        return filtered
    
    def _rank_recommendations(
        self,
        recommendations: List[InterventionRecommendation]
    ) -> List[InterventionRecommendation]:
        """Rank recommendations by priority and effectiveness"""
        
        priority_weights = {"urgent": 4, "high": 3, "medium": 2, "low": 1}
        
        def rank_score(rec):
            priority_score = priority_weights.get(rec.priority, 1)
            effectiveness_score = rec.expected_effectiveness
            confidence_score = rec.confidence
            
            return priority_score * 0.5 + effectiveness_score * 0.3 + confidence_score * 0.2
        
        return sorted(recommendations, key=rank_score, reverse=True) 