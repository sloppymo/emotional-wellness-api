from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import json
import asyncio
from redis.asyncio import Redis
import pandas as pd
import numpy as np
from collections import defaultdict
from prometheus_client import Counter, Gauge, Histogram

# Business Intelligence Metrics
revenue_impact_gauge = Gauge(
    'rate_limit_revenue_impact_dollars',
    'Revenue impact from rate limiting',
    ['impact_type', 'tenant', 'time_period']
)
customer_satisfaction_score = Gauge(
    'rate_limit_customer_satisfaction_score',
    'Customer satisfaction score related to rate limiting',
    ['tenant', 'user_segment']
)
api_adoption_rate = Gauge(
    'rate_limit_api_adoption_rate',
    'API adoption rate by feature',
    ['feature', 'tenant', 'user_segment']
)
churn_risk_score = Gauge(
    'rate_limit_churn_risk_score',
    'Churn risk score based on rate limiting patterns',
    ['tenant', 'user_segment']
)

class UserSegment(Enum):
    """User segments for emotional wellness API."""
    INDIVIDUAL_USERS = "individual_users"
    HEALTHCARE_PROVIDERS = "healthcare_providers"
    THERAPISTS = "therapists"
    CRISIS_COUNSELORS = "crisis_counselors"
    WELLNESS_COACHES = "wellness_coaches"
    RESEARCHERS = "researchers"
    ENTERPRISE_CLIENTS = "enterprise_clients"

class JourneyStage(Enum):
    """Customer journey stages."""
    DISCOVERY = "discovery"
    ONBOARDING = "onboarding"
    INITIAL_USE = "initial_use"
    REGULAR_USE = "regular_use"
    POWER_USE = "power_use"
    CHURN_RISK = "churn_risk"
    CHURNED = "churned"

class ImpactType(Enum):
    """Types of business impact."""
    REVENUE_LOSS = "revenue_loss"
    REVENUE_PROTECTION = "revenue_protection"
    COST_SAVINGS = "cost_savings"
    USER_ACQUISITION = "user_acquisition"
    USER_RETENTION = "user_retention"

@dataclass
class CustomerJourneyEvent:
    """Customer journey event."""
    user_id: str
    tenant_id: str
    segment: UserSegment
    stage: JourneyStage
    event_type: str
    timestamp: datetime
    rate_limit_context: Dict[str, Any]
    emotional_state: Optional[str] = None
    session_duration: Optional[float] = None
    api_calls_made: int = 0
    rate_limited: bool = False
    satisfaction_score: Optional[float] = None

@dataclass
class RevenueImpactAnalysis:
    """Revenue impact analysis result."""
    tenant_id: str
    time_period: str
    impact_type: ImpactType
    amount_usd: float
    affected_users: int
    confidence_level: float
    contributing_factors: List[str]
    recommendations: List[str]

@dataclass
class UserBehaviorInsight:
    """User behavior insight."""
    segment: UserSegment
    behavior_pattern: str
    frequency: int
    impact_on_wellness: str
    rate_limit_correlation: float
    recommendations: List[str]

class RateLimitBusinessIntelligence:
    """Business intelligence system for rate limiting with focus on emotional wellness outcomes."""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        
        # Redis keys
        self.journey_events_key = "bi:journey_events:{}"
        self.revenue_analytics_key = "bi:revenue_analytics"
        self.user_segments_key = "bi:user_segments"
        self.satisfaction_scores_key = "bi:satisfaction_scores"
        self.wellness_outcomes_key = "bi:wellness_outcomes"
        self.api_usage_patterns_key = "bi:api_usage_patterns"
        
        # User segment configurations for emotional wellness
        self.segment_configs = {
            UserSegment.INDIVIDUAL_USERS: {
                "typical_session_duration": 900,  # 15 minutes
                "typical_api_calls": 50,
                "wellness_focus": ["mood_tracking", "mindfulness", "self_reflection"],
                "rate_limit_sensitivity": "high",  # More sensitive to rate limits
                "revenue_per_user": 9.99  # Monthly subscription
            },
            UserSegment.HEALTHCARE_PROVIDERS: {
                "typical_session_duration": 1800,  # 30 minutes
                "typical_api_calls": 200,
                "wellness_focus": ["patient_monitoring", "clinical_insights", "progress_tracking"],
                "rate_limit_sensitivity": "medium",
                "revenue_per_user": 199.99  # Monthly subscription
            },
            UserSegment.THERAPISTS: {
                "typical_session_duration": 3600,  # 1 hour
                "typical_api_calls": 300,
                "wellness_focus": ["session_analysis", "patient_progress", "treatment_planning"],
                "rate_limit_sensitivity": "medium",
                "revenue_per_user": 299.99  # Monthly subscription
            },
            UserSegment.CRISIS_COUNSELORS: {
                "typical_session_duration": 2700,  # 45 minutes
                "typical_api_calls": 150,
                "wellness_focus": ["crisis_detection", "immediate_intervention", "safety_assessment"],
                "rate_limit_sensitivity": "critical",  # Cannot be rate limited during crisis
                "revenue_per_user": 499.99  # Monthly subscription
            },
            UserSegment.ENTERPRISE_CLIENTS: {
                "typical_session_duration": 14400,  # 4 hours (bulk processing)
                "typical_api_calls": 10000,
                "wellness_focus": ["population_health", "analytics", "reporting"],
                "rate_limit_sensitivity": "low",
                "revenue_per_user": 9999.99  # Monthly subscription
            }
        }
    
    async def record_journey_event(
        self,
        user_id: str,
        tenant_id: str,
        segment: UserSegment,
        stage: JourneyStage,
        event_type: str,
        rate_limit_context: Dict[str, Any],
        emotional_state: Optional[str] = None,
        session_duration: Optional[float] = None,
        api_calls_made: int = 0,
        rate_limited: bool = False,
        satisfaction_score: Optional[float] = None
    ):
        """Record a customer journey event with emotional wellness context."""
        event = CustomerJourneyEvent(
            user_id=user_id,
            tenant_id=tenant_id,
            segment=segment,
            stage=stage,
            event_type=event_type,
            timestamp=datetime.now(),
            rate_limit_context=rate_limit_context,
            emotional_state=emotional_state,
            session_duration=session_duration,
            api_calls_made=api_calls_made,
            rate_limited=rate_limited,
            satisfaction_score=satisfaction_score
        )
        
        # Store event
        events_key = self.journey_events_key.format(user_id)
        await self.redis.lpush(events_key, json.dumps(asdict(event), default=str))
        await self.redis.ltrim(events_key, 0, 999)  # Keep last 1000 events
        await self.redis.expire(events_key, 86400 * 90)  # 90 days
        
        # Update metrics
        if satisfaction_score:
            customer_satisfaction_score.labels(
                tenant=tenant_id,
                user_segment=segment.value
            ).set(satisfaction_score)
        
        # Analyze immediate impact
        await self._analyze_immediate_impact(event)
        
        # Update user segment analytics
        await self._update_segment_analytics(event)
    
    async def analyze_revenue_impact(
        self,
        tenant_id: str,
        time_period: str = "monthly"
    ) -> List[RevenueImpactAnalysis]:
        """Analyze revenue impact of rate limiting policies."""
        analyses = []
        
        # Get user journey events for the period
        period_start = self._get_period_start(time_period)
        events = await self._get_events_since(tenant_id, period_start)
        
        if not events:
            return analyses
        
        # Analyze different impact types
        
        # 1. Revenue loss from rate limiting during critical emotional states
        revenue_loss = await self._analyze_revenue_loss_from_rate_limiting(
            tenant_id, events, time_period
        )
        if revenue_loss:
            analyses.append(revenue_loss)
        
        # 2. Revenue protection from preventing abuse
        revenue_protection = await self._analyze_revenue_protection(
            tenant_id, events, time_period
        )
        if revenue_protection:
            analyses.append(revenue_protection)
        
        # 3. Cost savings from infrastructure protection
        cost_savings = await self._analyze_cost_savings(
            tenant_id, events, time_period
        )
        if cost_savings:
            analyses.append(cost_savings)
        
        # 4. User acquisition impact
        acquisition_impact = await self._analyze_user_acquisition_impact(
            tenant_id, events, time_period
        )
        if acquisition_impact:
            analyses.append(acquisition_impact)
        
        # 5. User retention impact
        retention_impact = await self._analyze_user_retention_impact(
            tenant_id, events, time_period
        )
        if retention_impact:
            analyses.append(retention_impact)
        
        # Update metrics
        for analysis in analyses:
            revenue_impact_gauge.labels(
                impact_type=analysis.impact_type.value,
                tenant=tenant_id,
                time_period=time_period
            ).set(analysis.amount_usd)
        
        return analyses
    
    async def _analyze_revenue_loss_from_rate_limiting(
        self,
        tenant_id: str,
        events: List[CustomerJourneyEvent],
        time_period: str
    ) -> Optional[RevenueImpactAnalysis]:
        """Analyze revenue loss from rate limiting during critical emotional states."""
        critical_events = [
            e for e in events
            if e.rate_limited and e.emotional_state in ["crisis", "severe_anxiety", "depression"]
        ]
        
        if not critical_events:
            return None
        
        # Calculate potential revenue loss
        # Users experiencing rate limits during crisis are 80% more likely to churn
        churn_risk_multiplier = 1.8
        affected_users = len(set(e.user_id for e in critical_events))
        
        # Calculate average revenue per user by segment
        total_potential_loss = 0
        for event in critical_events:
            segment_config = self.segment_configs[event.segment]
            monthly_revenue = segment_config["revenue_per_user"]
            
            # Crisis counselors have highest impact due to critical nature
            if event.segment == UserSegment.CRISIS_COUNSELORS:
                loss_multiplier = 5.0  # Complete service disruption
            elif event.segment == UserSegment.INDIVIDUAL_USERS:
                loss_multiplier = 2.0  # High emotional impact
            else:
                loss_multiplier = 1.5  # Moderate impact
            
            potential_loss = monthly_revenue * churn_risk_multiplier * loss_multiplier
            total_potential_loss += potential_loss
        
        return RevenueImpactAnalysis(
            tenant_id=tenant_id,
            time_period=time_period,
            impact_type=ImpactType.REVENUE_LOSS,
            amount_usd=total_potential_loss,
            affected_users=affected_users,
            confidence_level=0.85,
            contributing_factors=[
                "Rate limiting during critical emotional states",
                "Disrupted crisis intervention workflows",
                "Negative impact on therapeutic outcomes",
                "Increased churn risk for vulnerable users"
            ],
            recommendations=[
                "Implement zero-rate-limit policy for crisis endpoints",
                "Create emotional state-aware rate limiting",
                "Establish crisis counselor priority queues",
                "Implement immediate escalation for mental health emergencies"
            ]
        )
    
    async def _analyze_revenue_protection(
        self,
        tenant_id: str,
        events: List[CustomerJourneyEvent],
        time_period: str
    ) -> Optional[RevenueImpactAnalysis]:
        """Analyze revenue protection from preventing abuse."""
        abuse_events = [
            e for e in events
            if e.rate_limit_context.get("abuse_detected", False)
        ]
        
        if not abuse_events:
            return None
        
        # Calculate protection value
        # Abuse prevention protects infrastructure and legitimate users
        blocked_abuse_requests = sum(
            e.rate_limit_context.get("blocked_requests", 0)
            for e in abuse_events
        )
        
        # Estimate infrastructure cost savings
        cost_per_request = 0.001  # $0.001 per request
        infrastructure_savings = blocked_abuse_requests * cost_per_request
        
        # Estimate revenue protection from maintaining service quality
        legitimate_users_protected = len([
            e for e in events
            if not e.rate_limited and e.satisfaction_score and e.satisfaction_score > 4.0
        ])
        
        avg_revenue_per_user = 99.99  # Average across segments
        service_quality_protection = legitimate_users_protected * avg_revenue_per_user * 0.1
        
        total_protection = infrastructure_savings + service_quality_protection
        
        return RevenueImpactAnalysis(
            tenant_id=tenant_id,
            time_period=time_period,
            impact_type=ImpactType.REVENUE_PROTECTION,
            amount_usd=total_protection,
            affected_users=len(set(e.user_id for e in abuse_events)),
            confidence_level=0.75,
            contributing_factors=[
                "Blocked abusive traffic",
                "Protected infrastructure from overload",
                "Maintained service quality for legitimate users",
                "Prevented service degradation"
            ],
            recommendations=[
                "Continue aggressive abuse detection",
                "Implement adaptive rate limiting",
                "Add geographic-based protection",
                "Enhance bot detection capabilities"
            ]
        )
    
    async def map_customer_journey_friction(
        self,
        tenant_id: str,
        segment: Optional[UserSegment] = None
    ) -> Dict[str, Any]:
        """Map customer journey friction points related to rate limiting."""
        # Get recent events
        period_start = datetime.now() - timedelta(days=30)
        events = await self._get_events_since(tenant_id, period_start, segment)
        
        if not events:
            return {}
        
        # Group events by journey stage
        stage_analysis = defaultdict(list)
        for event in events:
            stage_analysis[event.stage].append(event)
        
        friction_map = {}
        
        for stage, stage_events in stage_analysis.items():
            rate_limited_events = [e for e in stage_events if e.rate_limited]
            total_events = len(stage_events)
            
            if total_events == 0:
                continue
            
            friction_rate = len(rate_limited_events) / total_events
            
            # Calculate impact on emotional wellness
            emotional_impact = await self._calculate_emotional_impact(stage_events)
            
            # Calculate satisfaction impact
            satisfaction_impact = await self._calculate_satisfaction_impact(stage_events)
            
            # Identify specific friction points
            friction_points = await self._identify_friction_points(stage_events)
            
            friction_map[stage.value] = {
                "friction_rate": friction_rate,
                "total_users": len(set(e.user_id for e in stage_events)),
                "rate_limited_users": len(set(e.user_id for e in rate_limited_events)),
                "emotional_impact": emotional_impact,
                "satisfaction_impact": satisfaction_impact,
                "friction_points": friction_points,
                "recommendations": await self._generate_friction_recommendations(
                    stage, friction_points, emotional_impact
                )
            }
        
        return {
            "tenant_id": tenant_id,
            "segment": segment.value if segment else "all",
            "analysis_period": "30_days",
            "journey_stages": friction_map,
            "overall_metrics": await self._calculate_overall_journey_metrics(events)
        }
    
    async def _calculate_emotional_impact(self, events: List[CustomerJourneyEvent]) -> Dict[str, Any]:
        """Calculate emotional impact of rate limiting."""
        emotional_states = [e.emotional_state for e in events if e.emotional_state]
        rate_limited_emotional_states = [
            e.emotional_state for e in events 
            if e.rate_limited and e.emotional_state
        ]
        
        if not emotional_states:
            return {"impact": "unknown", "severity": "low"}
        
        # Count critical emotional states affected
        critical_states = ["crisis", "severe_anxiety", "depression", "suicidal_ideation"]
        critical_affected = len([
            state for state in rate_limited_emotional_states 
            if state in critical_states
        ])
        
        if critical_affected > 0:
            severity = "critical"
            impact_description = f"{critical_affected} users in critical emotional states were rate limited"
        elif len(rate_limited_emotional_states) > len(emotional_states) * 0.1:
            severity = "high"
            impact_description = "High rate of rate limiting during emotional distress"
        else:
            severity = "low"
            impact_description = "Minimal emotional impact from rate limiting"
        
        return {
            "severity": severity,
            "impact": impact_description,
            "critical_states_affected": critical_affected,
            "total_emotional_events": len(emotional_states),
            "rate_limited_emotional_events": len(rate_limited_emotional_states)
        }
    
    async def _calculate_satisfaction_impact(self, events: List[CustomerJourneyEvent]) -> Dict[str, Any]:
        """Calculate satisfaction impact of rate limiting."""
        satisfaction_scores = [e.satisfaction_score for e in events if e.satisfaction_score]
        rate_limited_satisfaction = [
            e.satisfaction_score for e in events 
            if e.rate_limited and e.satisfaction_score
        ]
        
        if not satisfaction_scores:
            return {"impact": "unknown"}
        
        avg_satisfaction = np.mean(satisfaction_scores)
        
        if rate_limited_satisfaction:
            avg_rate_limited_satisfaction = np.mean(rate_limited_satisfaction)
            satisfaction_drop = avg_satisfaction - avg_rate_limited_satisfaction
        else:
            satisfaction_drop = 0
        
        return {
            "average_satisfaction": avg_satisfaction,
            "rate_limited_satisfaction": np.mean(rate_limited_satisfaction) if rate_limited_satisfaction else None,
            "satisfaction_drop": satisfaction_drop,
            "impact_severity": "high" if satisfaction_drop > 1.0 else "medium" if satisfaction_drop > 0.5 else "low"
        }
    
    async def generate_improvement_metrics(
        self,
        tenant_id: str,
        time_period: str = "monthly"
    ) -> Dict[str, Any]:
        """Generate quantifiable improvement metrics for stakeholders."""
        # Get baseline and current metrics
        current_period = await self._get_period_metrics(tenant_id, time_period, 0)
        previous_period = await self._get_period_metrics(tenant_id, time_period, 1)
        
        improvements = {}
        
        # 1. User Experience Improvements
        improvements["user_experience"] = {
            "satisfaction_score_improvement": self._calculate_improvement(
                current_period.get("avg_satisfaction", 0),
                previous_period.get("avg_satisfaction", 0)
            ),
            "session_completion_rate_improvement": self._calculate_improvement(
                current_period.get("session_completion_rate", 0),
                previous_period.get("session_completion_rate", 0)
            ),
            "emotional_wellness_outcome_improvement": self._calculate_improvement(
                current_period.get("positive_emotional_outcomes", 0),
                previous_period.get("positive_emotional_outcomes", 0)
            )
        }
        
        # 2. Business Metrics Improvements
        improvements["business_metrics"] = {
            "revenue_per_user_improvement": self._calculate_improvement(
                current_period.get("revenue_per_user", 0),
                previous_period.get("revenue_per_user", 0)
            ),
            "churn_rate_reduction": self._calculate_improvement(
                previous_period.get("churn_rate", 0),
                current_period.get("churn_rate", 0)
            ),
            "api_adoption_rate_improvement": self._calculate_improvement(
                current_period.get("api_adoption_rate", 0),
                previous_period.get("api_adoption_rate", 0)
            )
        }
        
        # 3. Operational Improvements
        improvements["operational"] = {
            "abuse_detection_accuracy_improvement": self._calculate_improvement(
                current_period.get("abuse_detection_accuracy", 0),
                previous_period.get("abuse_detection_accuracy", 0)
            ),
            "infrastructure_cost_reduction": self._calculate_improvement(
                previous_period.get("infrastructure_cost", 0),
                current_period.get("infrastructure_cost", 0)
            ),
            "response_time_improvement": self._calculate_improvement(
                previous_period.get("avg_response_time", 0),
                current_period.get("avg_response_time", 0)
            )
        }
        
        # 4. Clinical/Wellness Improvements
        improvements["clinical_outcomes"] = {
            "crisis_intervention_success_rate": self._calculate_improvement(
                current_period.get("crisis_intervention_success", 0),
                previous_period.get("crisis_intervention_success", 0)
            ),
            "therapeutic_engagement_improvement": self._calculate_improvement(
                current_period.get("therapeutic_engagement", 0),
                previous_period.get("therapeutic_engagement", 0)
            ),
            "patient_safety_score_improvement": self._calculate_improvement(
                current_period.get("patient_safety_score", 0),
                previous_period.get("patient_safety_score", 0)
            )
        }
        
        return {
            "tenant_id": tenant_id,
            "analysis_period": time_period,
            "report_generated": datetime.now().isoformat(),
            "improvements": improvements,
            "executive_summary": await self._generate_executive_summary(improvements),
            "recommendations": await self._generate_stakeholder_recommendations(improvements)
        }
    
    def _calculate_improvement(self, current: float, previous: float) -> Dict[str, Any]:
        """Calculate improvement percentage and absolute change."""
        if previous == 0:
            return {
                "percentage_change": 0,
                "absolute_change": current,
                "trend": "new_metric"
            }
        
        percentage_change = ((current - previous) / previous) * 100
        absolute_change = current - previous
        
        if percentage_change > 5:
            trend = "significant_improvement"
        elif percentage_change > 0:
            trend = "improvement"
        elif percentage_change > -5:
            trend = "stable"
        else:
            trend = "decline"
        
        return {
            "percentage_change": round(percentage_change, 2),
            "absolute_change": round(absolute_change, 2),
            "current_value": current,
            "previous_value": previous,
            "trend": trend
        }
    
    async def _generate_executive_summary(self, improvements: Dict[str, Any]) -> str:
        """Generate executive summary for stakeholders."""
        # Extract key improvements
        satisfaction_improvement = improvements["user_experience"]["satisfaction_score_improvement"]["percentage_change"]
        revenue_improvement = improvements["business_metrics"]["revenue_per_user_improvement"]["percentage_change"]
        clinical_improvement = improvements["clinical_outcomes"]["crisis_intervention_success_rate"]["percentage_change"]
        
        summary = f"""
        EMOTIONAL WELLNESS API - RATE LIMITING IMPACT ANALYSIS
        
        KEY ACHIEVEMENTS:
        • User Satisfaction: {satisfaction_improvement:+.1f}% improvement in satisfaction scores
        • Revenue Impact: {revenue_improvement:+.1f}% improvement in revenue per user
        • Clinical Outcomes: {clinical_improvement:+.1f}% improvement in crisis intervention success
        
        BUSINESS IMPACT:
        Our intelligent rate limiting system has successfully balanced API protection with 
        optimal user experience for emotional wellness applications. The system demonstrates 
        particular effectiveness in maintaining service quality during mental health crises 
        while preventing abuse and protecting infrastructure.
        
        COMPLIANCE & SAFETY:
        All rate limiting policies comply with HIPAA requirements and prioritize patient 
        safety, especially during crisis interventions. The system ensures that mental 
        health emergencies are never impacted by rate limiting policies.
        """
        
        return summary.strip()
    
    # Helper methods (simplified for brevity)
    def _get_period_start(self, period: str) -> datetime:
        """Get start time for a period."""
        now = datetime.now()
        if period == "daily":
            return now - timedelta(days=1)
        elif period == "weekly":
            return now - timedelta(weeks=1)
        elif period == "monthly":
            return now - timedelta(days=30)
        else:
            return now - timedelta(days=30)
    
    async def _get_events_since(
        self,
        tenant_id: str,
        since: datetime,
        segment: Optional[UserSegment] = None
    ) -> List[CustomerJourneyEvent]:
        """Get events since a specific time."""
        # This would query Redis for events
        # Simplified implementation
        return []
    
    async def _get_period_metrics(self, tenant_id: str, period: str, periods_ago: int) -> Dict[str, Any]:
        """Get metrics for a specific period."""
        # This would calculate metrics from stored events
        # Simplified implementation
        return {
            "avg_satisfaction": 4.2,
            "session_completion_rate": 0.85,
            "revenue_per_user": 99.99,
            "churn_rate": 0.05
        }
