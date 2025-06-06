"""Dashboard router for clinical interface."""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
import json

from ..database.session import get_async_session
from ..security.auth import get_current_user, require_role
from ..models.user import User
from ..clinical.analytics import (
    CrisisTrendAnalyzer,
    RiskStratificationEngine,
    WellnessTrajectoryAnalyzer,
    InterventionOutcomeAnalyzer
)
from ..structured_logging import get_logger

logger = get_logger(__name__)

# Setup templates and static files
templates = Jinja2Templates(directory="src/dashboard/templates")

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Mount static files
router.mount("/static", StaticFiles(directory="src/dashboard/static"), name="static")


# Dashboard pages
@router.get("/", response_class=HTMLResponse)
async def dashboard_home(
    request: Request,
    current_user: User = Depends(require_role(['clinician', 'admin']))
):
    """Main dashboard page."""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": current_user,
        "page_title": "Clinical Dashboard"
    })


@router.get("/crisis-trends", response_class=HTMLResponse)
async def crisis_trends_page(
    request: Request,
    current_user: User = Depends(require_role(['clinician', 'admin']))
):
    """Crisis trends visualization page."""
    return templates.TemplateResponse("crisis_trends.html", {
        "request": request,
        "user": current_user,
        "page_title": "Crisis Trends Analysis"
    })


@router.get("/risk-stratification", response_class=HTMLResponse)
async def risk_stratification_page(
    request: Request,
    current_user: User = Depends(require_role(['clinician', 'admin']))
):
    """Risk stratification visualization page."""
    return templates.TemplateResponse("risk_stratification.html", {
        "request": request,
        "user": current_user,
        "page_title": "Risk Stratification"
    })


@router.get("/wellness-trajectories", response_class=HTMLResponse)
async def wellness_trajectories_page(
    request: Request,
    current_user: User = Depends(require_role(['clinician', 'admin']))
):
    """Wellness trajectories visualization page."""
    return templates.TemplateResponse("wellness_trajectories.html", {
        "request": request,
        "user": current_user,
        "page_title": "Wellness Trajectories"
    })


@router.get("/intervention-outcomes", response_class=HTMLResponse)
async def intervention_outcomes_page(
    request: Request,
    current_user: User = Depends(require_role(['clinician', 'admin']))
):
    """Intervention outcomes visualization page."""
    return templates.TemplateResponse("intervention_outcomes.html", {
        "request": request,
        "user": current_user,
        "page_title": "Intervention Outcomes"
    })


# API endpoints for dashboard data
@router.get("/api/crisis-trends/data")
async def get_crisis_trends_data(
    period: str = Query('weekly', pattern='^(daily|weekly|monthly)$'),
    days: int = Query(30, ge=7, le=365),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role(['clinician', 'admin']))
) -> Dict[str, Any]:
    """Get crisis trends data for visualization."""
    try:
        analyzer = CrisisTrendAnalyzer(session)
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        trends = await analyzer.analyze_trends(start_date, end_date)
        
        # Format data for charts
        return {
            "period": period,
            "timeRange": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "summary": {
                "totalAssessments": trends['total_assessments'],
                "crisisEvents": trends['crisis_events'],
                "averageRiskScore": trends.get('average_risk_score', 0)
            },
            "riskDistribution": trends['risk_distribution'],
            "temporalPatterns": {
                "hourly": trends['temporal_patterns'].get('hourly', []),
                "daily": trends['temporal_patterns'].get('daily', []),
                "weekly": trends['temporal_patterns'].get('weekly', [])
            },
            "hotspots": trends['hotspots'],
            "trendAnalysis": {
                "direction": trends.get('trend_direction', 'stable'),
                "changePercent": trends.get('change_percent', 0),
                "projection": trends.get('projection', {})
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching crisis trends data: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/risk-stratification/data")
async def get_risk_stratification_data(
    cohort_size: int = Query(100, ge=10, le=1000),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role(['clinician', 'admin']))
) -> Dict[str, Any]:
    """Get risk stratification data for visualization."""
    try:
        engine = RiskStratificationEngine(session)
        
        # Get latest stratification results
        stratification = await engine.get_latest_stratification()
        
        if not stratification:
            # Generate new stratification if none exists
            patients = await engine.get_active_patients('weekly')
            stratification = await engine.stratify_patients(patients, cohort_size)
            await engine.store_stratification_results(stratification)
        
        # Format data for visualization
        return {
            "generatedAt": stratification.get('generated_at', datetime.utcnow().isoformat()),
            "totalPatients": stratification.get('total_patients', 0),
            "riskLevels": {
                "high": {
                    "count": len(stratification.get('high_risk', [])),
                    "percentage": stratification.get('high_risk_percentage', 0),
                    "avgScore": stratification.get('high_risk_avg_score', 0)
                },
                "moderate": {
                    "count": len(stratification.get('moderate_risk', [])),
                    "percentage": stratification.get('moderate_risk_percentage', 0),
                    "avgScore": stratification.get('moderate_risk_avg_score', 0)
                },
                "low": {
                    "count": len(stratification.get('low_risk', [])),
                    "percentage": stratification.get('low_risk_percentage', 0),
                    "avgScore": stratification.get('low_risk_avg_score', 0)
                }
            },
            "cohortAnalysis": stratification.get('cohort_analysis', {}),
            "riskFactors": stratification.get('top_risk_factors', []),
            "recommendations": stratification.get('recommendations', [])
        }
        
    except Exception as e:
        logger.error(f"Error fetching risk stratification data: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/wellness-trajectories/data")
async def get_wellness_trajectories_data(
    user_id: Optional[str] = None,
    cohort: Optional[str] = Query(None, pattern='^(all|high_risk|moderate_risk|low_risk)$'),
    days: int = Query(30, ge=7, le=365),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role(['clinician', 'admin']))
) -> Dict[str, Any]:
    """Get wellness trajectory data for visualization."""
    try:
        analyzer = WellnessTrajectoryAnalyzer(session)
        
        if user_id:
            # Get specific user trajectory
            trajectory = await analyzer.get_user_trajectory(user_id, days)
            return {
                "type": "individual",
                "userId": user_id,
                "trajectory": trajectory
            }
        else:
            # Get cohort trajectories
            trajectories = await analyzer.get_cohort_trajectories(cohort or 'all', days)
            return {
                "type": "cohort",
                "cohort": cohort or 'all',
                "timeframeDays": days,
                "trajectories": trajectories,
                "aggregateMetrics": {
                    "averageImprovement": trajectories.get('avg_improvement', 0),
                    "successRate": trajectories.get('success_rate', 0),
                    "adherenceRate": trajectories.get('adherence_rate', 0)
                }
            }
        
    except Exception as e:
        logger.error(f"Error fetching wellness trajectories: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/intervention-outcomes/data")
async def get_intervention_outcomes_data(
    protocol_id: Optional[str] = None,
    days: int = Query(90, ge=7, le=365),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role(['clinician', 'admin']))
) -> Dict[str, Any]:
    """Get intervention outcomes data for visualization."""
    try:
        analyzer = InterventionOutcomeAnalyzer(session)
        
        # Get intervention outcomes
        if protocol_id:
            outcomes = await analyzer.get_protocol_outcomes(protocol_id, days)
        else:
            outcomes = await analyzer.get_all_outcomes(days)
        
        # Calculate effectiveness metrics
        effectiveness = await analyzer.calculate_effectiveness(outcomes)
        
        return {
            "timeframeDays": days,
            "totalInterventions": len(outcomes),
            "overallEffectiveness": effectiveness.get('overall_effectiveness', 0),
            "protocolPerformance": effectiveness.get('protocol_performance', {}),
            "outcomeDistribution": {
                "successful": effectiveness.get('successful_count', 0),
                "partial": effectiveness.get('partial_count', 0),
                "unsuccessful": effectiveness.get('unsuccessful_count', 0)
            },
            "averageTimeToResolution": effectiveness.get('avg_time_to_resolution', 0),
            "escalationRate": effectiveness.get('escalation_rate', 0),
            "topPerformingProtocols": effectiveness.get('top_protocols', []),
            "improvementAreas": effectiveness.get('improvement_areas', [])
        }
        
    except Exception as e:
        logger.error(f"Error fetching intervention outcomes: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/early-warning-indicators")
async def get_early_warning_indicators(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role(['clinician', 'admin']))
) -> Dict[str, Any]:
    """Get early warning indicators for at-risk patients."""
    try:
        # Combine data from multiple analyzers
        crisis_analyzer = CrisisTrendAnalyzer(session)
        risk_engine = RiskStratificationEngine(session)
        
        # Get patients with deteriorating trajectories
        warnings = await crisis_analyzer.get_early_warnings()
        
        # Get high-risk patients requiring attention
        high_risk_patients = await risk_engine.get_high_risk_patients_requiring_attention()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "warningCount": len(warnings) + len(high_risk_patients),
            "criticalAlerts": [
                {
                    "patientId": w['patient_id'],
                    "riskLevel": w['risk_level'],
                    "indicator": w['indicator'],
                    "change": w['change'],
                    "recommendedAction": w['recommended_action'],
                    "urgency": w['urgency']
                }
                for w in warnings[:10]  # Top 10 most urgent
            ],
            "riskEscalations": [
                {
                    "patientId": p['patient_id'],
                    "previousRisk": p['previous_risk'],
                    "currentRisk": p['current_risk'],
                    "escalationRate": p['escalation_rate'],
                    "lastAssessment": p['last_assessment']
                }
                for p in high_risk_patients[:10]
            ],
            "systemRecommendations": await crisis_analyzer.get_system_recommendations()
        }
        
    except Exception as e:
        logger.error(f"Error fetching early warning indicators: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/dashboard/summary")
async def get_dashboard_summary(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role(['clinician', 'admin']))
) -> Dict[str, Any]:
    """Get summary data for main dashboard."""
    try:
        # Initialize analyzers
        crisis_analyzer = CrisisTrendAnalyzer(session)
        risk_engine = RiskStratificationEngine(session)
        outcome_analyzer = InterventionOutcomeAnalyzer(session)
        
        # Get summary metrics
        today = datetime.utcnow().date()
        week_ago = today - timedelta(days=7)
        
        return {
            "lastUpdated": datetime.utcnow().isoformat(),
            "metrics": {
                "activePatients": await risk_engine.count_active_patients(),
                "todayAssessments": await crisis_analyzer.count_assessments_today(),
                "weeklyTrend": await crisis_analyzer.get_weekly_trend_percentage(),
                "interventionSuccessRate": await outcome_analyzer.get_success_rate_last_30_days()
            },
            "alerts": {
                "critical": await crisis_analyzer.count_critical_alerts(),
                "warning": await crisis_analyzer.count_warning_alerts(),
                "info": await crisis_analyzer.count_info_alerts()
            },
            "recentActivity": await get_recent_activity(session, limit=10)
        }
        
    except Exception as e:
        logger.error(f"Error fetching dashboard summary: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def get_recent_activity(session: AsyncSession, limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent system activity for dashboard."""
    # This would query recent assessments, interventions, and other activities
    # Implementation depends on your specific models and requirements
    return [] 