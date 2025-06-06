"""Clinical analytics background tasks."""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from celery import Task
from celery.signals import task_prerun, task_postrun, task_failure
import numpy as np
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .celery_app import celery_app, TaskStatus
from ..database.session import get_async_session
from ..models.assessment import Assessment
from ..models.intervention import Intervention
from ..models.user import User
from ..structured_logging import get_logger
from ..clinical.analytics import (
    CrisisTrendAnalyzer,
    RiskStratificationEngine,
    WellnessTrajectoryAnalyzer,
    InterventionOutcomeAnalyzer
)

logger = get_logger(__name__)


class ProgressTrackingTask(Task):
    """Base task class with progress tracking."""
    
    def update_progress(self, current: int, total: int, message: str = ""):
        """Update task progress."""
        self.update_state(
            state=TaskStatus.PROGRESS,
            meta={
                'current': current,
                'total': total,
                'percent': int((current / total) * 100),
                'message': message
            }
        )


@celery_app.task(bind=True, base=ProgressTrackingTask, name='src.tasks.clinical_analytics.analyze_crisis_trends')
def analyze_crisis_trends(self, period: str = 'daily', start_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze crisis trends for the specified period.
    
    Args:
        period: Analysis period ('daily', 'weekly', 'monthly')
        start_date: Optional start date for analysis
        
    Returns:
        Dict containing trend analysis results
    """
    try:
        logger.info(f"Starting crisis trends analysis for period: {period}")
        self.update_progress(0, 100, "Initializing analysis")
        
        # Run async code in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_analyze_crisis_trends_async(self, period, start_date))
        loop.close()
        
        logger.info("Crisis trends analysis completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error in crisis trends analysis: {str(e)}", exc_info=True)
        self.update_state(
            state=TaskStatus.FAILURE,
            meta={'error': str(e)}
        )
        raise


async def _analyze_crisis_trends_async(task, period: str, start_date: Optional[str]) -> Dict[str, Any]:
    """Async implementation of crisis trends analysis."""
    async with get_async_session() as session:
        analyzer = CrisisTrendAnalyzer(session)
        
        # Calculate date range
        end_date = datetime.utcnow()
        if start_date:
            start = datetime.fromisoformat(start_date)
        else:
            if period == 'daily':
                start = end_date - timedelta(days=1)
            elif period == 'weekly':
                start = end_date - timedelta(weeks=1)
            else:  # monthly
                start = end_date - timedelta(days=30)
        
        task.update_progress(20, 100, "Fetching assessment data")
        
        # Analyze trends
        trends = await analyzer.analyze_trends(start, end_date)
        
        task.update_progress(60, 100, "Processing temporal patterns")
        
        # Process results
        results = {
            'period': period,
            'start_date': start.isoformat(),
            'end_date': end_date.isoformat(),
            'total_assessments': trends['total_assessments'],
            'crisis_events': trends['crisis_events'],
            'risk_distribution': trends['risk_distribution'],
            'temporal_patterns': trends['temporal_patterns'],
            'hotspots': trends['hotspots'],
            'recommendations': trends['recommendations']
        }
        
        task.update_progress(90, 100, "Generating report")
        
        # Store results for dashboard
        await analyzer.store_results(results)
        
        task.update_progress(100, 100, "Analysis complete")
        
        return results


@celery_app.task(bind=True, base=ProgressTrackingTask, name='src.tasks.clinical_analytics.generate_risk_stratification')
def generate_risk_stratification(self, period: str = 'weekly', cohort_size: int = 100) -> Dict[str, Any]:
    """
    Generate risk stratification analysis for patient cohorts.
    
    Args:
        period: Analysis period
        cohort_size: Size of cohorts for stratification
        
    Returns:
        Dict containing stratification results
    """
    try:
        logger.info(f"Starting risk stratification for period: {period}")
        self.update_progress(0, 100, "Initializing stratification engine")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_generate_risk_stratification_async(self, period, cohort_size))
        loop.close()
        
        logger.info("Risk stratification completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error in risk stratification: {str(e)}", exc_info=True)
        self.update_state(
            state=TaskStatus.FAILURE,
            meta={'error': str(e)}
        )
        raise


async def _generate_risk_stratification_async(task, period: str, cohort_size: int) -> Dict[str, Any]:
    """Async implementation of risk stratification."""
    async with get_async_session() as session:
        engine = RiskStratificationEngine(session)
        
        task.update_progress(10, 100, "Loading patient data")
        
        # Get active patients
        patients = await engine.get_active_patients(period)
        total_patients = len(patients)
        
        task.update_progress(30, 100, f"Stratifying {total_patients} patients")
        
        # Perform stratification
        stratification = await engine.stratify_patients(patients, cohort_size)
        
        task.update_progress(70, 100, "Calculating risk scores")
        
        # Calculate detailed risk metrics
        risk_metrics = await engine.calculate_risk_metrics(stratification)
        
        task.update_progress(85, 100, "Generating recommendations")
        
        results = {
            'period': period,
            'total_patients': total_patients,
            'stratification': {
                'high_risk': stratification['high_risk'],
                'moderate_risk': stratification['moderate_risk'],
                'low_risk': stratification['low_risk']
            },
            'risk_metrics': risk_metrics,
            'cohort_analysis': stratification['cohort_analysis'],
            'recommendations': stratification['recommendations'],
            'generated_at': datetime.utcnow().isoformat()
        }
        
        task.update_progress(95, 100, "Storing results")
        
        # Store results
        await engine.store_stratification_results(results)
        
        task.update_progress(100, 100, "Stratification complete")
        
        return results


@celery_app.task(bind=True, base=ProgressTrackingTask, name='src.tasks.clinical_analytics.compute_wellness_trajectory')
def compute_wellness_trajectory(self, user_id: str, timeframe_days: int = 30) -> Dict[str, Any]:
    """
    Compute wellness trajectory for a specific user.
    
    Args:
        user_id: User ID to analyze
        timeframe_days: Number of days to analyze
        
    Returns:
        Dict containing trajectory analysis
    """
    try:
        logger.info(f"Computing wellness trajectory for user: {user_id}")
        self.update_progress(0, 100, "Loading user data")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_compute_wellness_trajectory_async(self, user_id, timeframe_days))
        loop.close()
        
        logger.info(f"Wellness trajectory computed for user: {user_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error computing wellness trajectory: {str(e)}", exc_info=True)
        self.update_state(
            state=TaskStatus.FAILURE,
            meta={'error': str(e)}
        )
        raise


async def _compute_wellness_trajectory_async(task, user_id: str, timeframe_days: int) -> Dict[str, Any]:
    """Async implementation of wellness trajectory computation."""
    async with get_async_session() as session:
        analyzer = WellnessTrajectoryAnalyzer(session)
        
        task.update_progress(15, 100, "Fetching assessment history")
        
        # Get user's assessment history
        assessments = await analyzer.get_user_assessments(user_id, timeframe_days)
        
        if not assessments:
            return {
                'user_id': user_id,
                'timeframe_days': timeframe_days,
                'status': 'no_data',
                'message': 'No assessment data available for this user'
            }
        
        task.update_progress(30, 100, "Analyzing wellness patterns")
        
        # Compute trajectory
        trajectory = await analyzer.compute_trajectory(assessments)
        
        task.update_progress(50, 100, "Identifying trends")
        
        # Identify trends and patterns
        trends = await analyzer.identify_trends(trajectory)
        
        task.update_progress(70, 100, "Generating predictions")
        
        # Generate predictions
        predictions = await analyzer.generate_predictions(trajectory, trends)
        
        task.update_progress(85, 100, "Creating recommendations")
        
        results = {
            'user_id': user_id,
            'timeframe_days': timeframe_days,
            'trajectory': trajectory,
            'trends': trends,
            'predictions': predictions,
            'wellness_score': trajectory.get('current_wellness_score'),
            'improvement_rate': trajectory.get('improvement_rate'),
            'risk_factors': trends.get('risk_factors', []),
            'recommendations': await analyzer.generate_recommendations(trajectory, trends),
            'computed_at': datetime.utcnow().isoformat()
        }
        
        task.update_progress(95, 100, "Storing results")
        
        # Store results
        await analyzer.store_trajectory_results(user_id, results)
        
        task.update_progress(100, 100, "Analysis complete")
        
        return results


@celery_app.task(bind=True, base=ProgressTrackingTask, name='src.tasks.clinical_analytics.process_intervention_outcomes')
def process_intervention_outcomes(self, intervention_ids: List[str] = None, timeframe_days: int = 90) -> Dict[str, Any]:
    """
    Process and analyze intervention outcomes.
    
    Args:
        intervention_ids: Optional list of specific intervention IDs to analyze
        timeframe_days: Timeframe for analysis
        
    Returns:
        Dict containing outcome analysis
    """
    try:
        logger.info("Processing intervention outcomes")
        self.update_progress(0, 100, "Initializing outcome analyzer")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_process_intervention_outcomes_async(self, intervention_ids, timeframe_days))
        loop.close()
        
        logger.info("Intervention outcome processing completed")
        return result
        
    except Exception as e:
        logger.error(f"Error processing intervention outcomes: {str(e)}", exc_info=True)
        self.update_state(
            state=TaskStatus.FAILURE,
            meta={'error': str(e)}
        )
        raise


async def _process_intervention_outcomes_async(task, intervention_ids: List[str], timeframe_days: int) -> Dict[str, Any]:
    """Async implementation of intervention outcome processing."""
    async with get_async_session() as session:
        analyzer = InterventionOutcomeAnalyzer(session)
        
        task.update_progress(10, 100, "Loading intervention data")
        
        # Get interventions to analyze
        if intervention_ids:
            interventions = await analyzer.get_interventions_by_ids(intervention_ids)
        else:
            interventions = await analyzer.get_recent_interventions(timeframe_days)
        
        total_interventions = len(interventions)
        task.update_progress(25, 100, f"Analyzing {total_interventions} interventions")
        
        # Analyze outcomes
        outcomes = await analyzer.analyze_outcomes(interventions)
        
        task.update_progress(50, 100, "Calculating effectiveness metrics")
        
        # Calculate effectiveness metrics
        effectiveness = await analyzer.calculate_effectiveness(outcomes)
        
        task.update_progress(70, 100, "Identifying success patterns")
        
        # Identify patterns
        patterns = await analyzer.identify_success_patterns(outcomes, effectiveness)
        
        task.update_progress(85, 100, "Generating insights")
        
        results = {
            'timeframe_days': timeframe_days,
            'total_interventions': total_interventions,
            'outcomes': outcomes,
            'effectiveness_metrics': effectiveness,
            'success_patterns': patterns,
            'protocol_performance': await analyzer.analyze_protocol_performance(outcomes),
            'recommendations': await analyzer.generate_recommendations(patterns),
            'processed_at': datetime.utcnow().isoformat()
        }
        
        task.update_progress(95, 100, "Storing results")
        
        # Store results
        await analyzer.store_outcome_results(results)
        
        task.update_progress(100, 100, "Processing complete")
        
        return results


# Signal handlers for logging and monitoring
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kw):
    """Log task start."""
    logger.info(f"Task {task.name} [{task_id}] started", extra={
        'task_name': task.name,
        'task_id': task_id,
        'args': args,
        'kwargs': kwargs
    })


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kw):
    """Log task completion."""
    logger.info(f"Task {task.name} [{task_id}] completed with state: {state}", extra={
        'task_name': task.name,
        'task_id': task_id,
        'state': state,
        'duration': kw.get('runtime', 0)
    })


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, einfo=None, **kw):
    """Log task failure."""
    logger.error(f"Task {sender.name} [{task_id}] failed: {str(exception)}", extra={
        'task_name': sender.name,
        'task_id': task_id,
        'exception': str(exception),
        'args': args,
        'kwargs': kwargs
    }, exc_info=True) 