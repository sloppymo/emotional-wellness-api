"""
Longitudinal analysis background tasks.

This module contains Celery tasks for performing long-running longitudinal
analysis operations that should be executed asynchronously.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from celery import Task
import numpy as np

from .celery_app import celery_app, TaskStatus
from .clinical_analytics import ProgressTrackingTask
from ..database.session import get_async_session
from ..structured_logging import get_logger
from ..clinical.longitudinal import (
    LongitudinalAnalyzer,
    TrendDirection,
    EarlyWarningLevel
)
from ..models.assessment import Assessment
from ..models.intervention import Intervention
from ..models.user import User
from ..models.crisis_alert import CrisisAlert

# Configure logger
logger = get_logger(__name__)


@celery_app.task(bind=True, base=ProgressTrackingTask, name='src.tasks.longitudinal.analyze_patient_history')
def analyze_patient_history(self, patient_id: str, days: int = 90) -> Dict[str, Any]:
    """
    Analyze a patient's history over the specified time period.
    
    Args:
        patient_id: Patient ID to analyze
        days: Number of days to look back in patient history
        
    Returns:
        Dict containing patient history analysis
    """
    try:
        logger.info(f"Starting longitudinal analysis for patient {patient_id}")
        self.update_progress(0, 100, "Initializing analysis")
        
        # Run async code in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_analyze_patient_history_async(self, patient_id, days))
        loop.close()
        
        logger.info(f"Longitudinal analysis for patient {patient_id} completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error in patient history analysis: {str(e)}", exc_info=True)
        self.update_state(
            state=TaskStatus.FAILURE,
            meta={'error': str(e)}
        )
        raise


async def _analyze_patient_history_async(task, patient_id: str, days: int) -> Dict[str, Any]:
    """Async implementation of patient history analysis."""
    async with get_async_session() as session:
        analyzer = LongitudinalAnalyzer(session=session)
        
        task.update_progress(10, 100, "Retrieving patient history")
        
        # Get patient data
        patient = await analyzer.get_patient(patient_id)
        if not patient:
            raise ValueError(f"Patient {patient_id} not found")
        
        task.update_progress(20, 100, "Analyzing emotional trends")
        
        # Analyze emotional trends
        history = await analyzer.get_patient_history(patient_id, days)
        emotional_trends = analyzer.analyze_emotional_trends(history)
        
        task.update_progress(40, 100, "Detecting patterns")
        
        # Detect patterns
        patterns = analyzer.detect_patterns(history)
        
        task.update_progress(60, 100, "Identifying risk factors")
        
        # Identify risk factors
        risk_factors = analyzer.identify_risk_factors(history, emotional_trends)
        
        task.update_progress(80, 100, "Determining trend direction")
        
        # Determine trend and confidence
        trend, confidence = analyzer.determine_trend(history, emotional_trends)
        
        task.update_progress(90, 100, "Identifying warning signs")
        
        # Identify warning signs
        warning_signs = analyzer.identify_warning_signs(history, patterns, emotional_trends)
        
        # Prepare result
        result = {
            "patient_id": patient_id,
            "analysis_date": datetime.utcnow().isoformat(),
            "period_days": days,
            "data_points": len(history),
            "trend": trend.name,
            "confidence": confidence,
            "emotional_trends": emotional_trends,
            "patterns": patterns,
            "risk_factors": risk_factors,
            "warning_signs": warning_signs,
            "critical_events": [
                event for event in history 
                if event.get("type") == "crisis_alert" and 
                event.get("severity") in ["SEVERE", "CRITICAL"]
            ]
        }
        
        # Store analysis results
        await analyzer.store_analysis_results(patient_id, result)
        
        task.update_progress(100, 100, "Analysis complete")
        
        return result


@celery_app.task(bind=True, base=ProgressTrackingTask, name='src.tasks.longitudinal.early_warning_check')
def early_warning_check(self, patient_id: str) -> Dict[str, Any]:
    """
    Perform an early warning check for a patient.
    
    Args:
        patient_id: Patient ID to check
        
    Returns:
        Dict containing early warning results
    """
    try:
        logger.info(f"Starting early warning check for patient {patient_id}")
        self.update_progress(0, 100, "Initializing check")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_early_warning_check_async(self, patient_id))
        loop.close()
        
        logger.info(f"Early warning check for patient {patient_id} completed")
        return result
        
    except Exception as e:
        logger.error(f"Error in early warning check: {str(e)}", exc_info=True)
        self.update_state(
            state=TaskStatus.FAILURE,
            meta={'error': str(e)}
        )
        raise


async def _early_warning_check_async(task, patient_id: str) -> Dict[str, Any]:
    """Async implementation of early warning check."""
    async with get_async_session() as session:
        analyzer = LongitudinalAnalyzer(session=session)
        
        task.update_progress(20, 100, "Running short-term analysis")
        
        # Analyze recent history (last 30 days)
        recent_analysis = await analyzer.analyze_patient_history(patient_id, 30)
        
        task.update_progress(50, 100, "Running long-term analysis")
        
        # Analyze longer history (last 90 days)
        longer_analysis = await analyzer.analyze_patient_history(patient_id, 90)
        
        task.update_progress(80, 100, "Evaluating warning status")
        
        # Calculate warning factors
        warning_factors = []
        warning_level = 0
        
        # Check recent trend direction
        recent_trend = TrendDirection[recent_analysis["trend"]]
        if recent_trend == TrendDirection.DECREASING:
            warning_factors.append("declining_recent_trend")
            warning_level += 2
        
        # Check for warning signs in recent analysis
        if recent_analysis["warning_signs"]:
            for sign in recent_analysis["warning_signs"]:
                warning_factors.append(sign)
                warning_level += 1
        
        # Check patterns
        if recent_analysis["patterns"]:
            for pattern in recent_analysis["patterns"]:
                if pattern["type"] == "recurring_crisis":
                    warning_factors.append(f"recurring_crisis_{pattern['domain']}")
                    warning_level += 2
        
        # Check risk factors
        if recent_analysis["risk_factors"]:
            for factor in recent_analysis["risk_factors"]:
                warning_factors.append(factor)
                warning_level += 1
        
        # Determine warning status
        warning_status = EarlyWarningLevel.LOW
        if warning_level >= 5:
            warning_status = EarlyWarningLevel.HIGH
        elif warning_level >= 3:
            warning_status = EarlyWarningLevel.MODERATE
        
        # Generate recommendations based on warning status
        recommendations = []
        if warning_status == EarlyWarningLevel.HIGH:
            recommendations = [
                "Immediate clinical intervention recommended",
                "Consider safety assessment",
                "Increase contact frequency",
                "Review medications and treatment plan"
            ]
        elif warning_status == EarlyWarningLevel.MODERATE:
            recommendations = [
                "Schedule check-in within 48 hours",
                "Monitor emotional state more frequently",
                "Review coping strategies"
            ]
        else:
            recommendations = [
                "Maintain regular monitoring",
                "Routine follow-up as scheduled"
            ]
        
        # Prepare result
        result = {
            "patient_id": patient_id,
            "check_date": datetime.utcnow().isoformat(),
            "warning_status": warning_status.name.lower(),
            "warning_level": warning_level,
            "warning_factors": warning_factors,
            "recent_trend": recent_trend.name,
            "longer_trend": TrendDirection[longer_analysis["trend"]].name,
            "recommendations": recommendations
        }
        
        # Store early warning result
        await analyzer.store_early_warning(patient_id, result)
        
        task.update_progress(100, 100, "Check complete")
        
        return result


@celery_app.task(bind=True, base=ProgressTrackingTask, name='src.tasks.longitudinal.scan_for_early_warnings')
def scan_for_early_warnings(self, max_patients: int = 100) -> Dict[str, Any]:
    """
    Scan all active patients for early warning signs.
    
    Args:
        max_patients: Maximum number of patients to scan
        
    Returns:
        Dict containing scan results
    """
    try:
        logger.info(f"Starting early warning scan for up to {max_patients} patients")
        self.update_progress(0, 100, "Initializing scan")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_scan_for_early_warnings_async(self, max_patients))
        loop.close()
        
        logger.info("Early warning scan completed")
        return result
        
    except Exception as e:
        logger.error(f"Error in early warning scan: {str(e)}", exc_info=True)
        self.update_state(
            state=TaskStatus.FAILURE,
            meta={'error': str(e)}
        )
        raise


async def _scan_for_early_warnings_async(task, max_patients: int) -> Dict[str, Any]:
    """Async implementation of early warning scan."""
    async with get_async_session() as session:
        analyzer = LongitudinalAnalyzer(session=session)
        
        task.update_progress(10, 100, "Getting active patients")
        
        # Get active patients (those with recent activity)
        patients = await analyzer.get_active_patients(max_patients)
        total_patients = len(patients)
        
        if total_patients == 0:
            return {
                "scan_date": datetime.utcnow().isoformat(),
                "patients_scanned": 0,
                "warnings_detected": 0,
                "high_risk_count": 0,
                "moderate_risk_count": 0,
                "warnings": []
            }
        
        task.update_progress(20, 100, f"Found {total_patients} active patients")
        
        # Process patients in batches to update progress
        warnings = []
        high_risk_count = 0
        moderate_risk_count = 0
        
        # Process each patient
        for i, patient_id in enumerate(patients):
            # Update progress periodically
            if i % 10 == 0:
                progress = 20 + int(70 * (i / total_patients))
                task.update_progress(
                    progress, 100, 
                    f"Checking patient {i+1} of {total_patients}"
                )
            
            # Check for early warnings
            try:
                warning = await analyzer.early_warning_check(patient_id)
                
                # Count by risk level
                if warning["warning_status"] == EarlyWarningLevel.HIGH.name.lower():
                    high_risk_count += 1
                    warnings.append(warning)
                elif warning["warning_status"] == EarlyWarningLevel.MODERATE.name.lower():
                    moderate_risk_count += 1
                    warnings.append(warning)
                
            except Exception as e:
                logger.error(f"Error checking patient {patient_id}: {str(e)}")
                # Continue with next patient
        
        # Sort warnings by severity (highest first)
        warnings.sort(
            key=lambda w: 0 if w["warning_status"] == EarlyWarningLevel.HIGH.name.lower() 
            else (1 if w["warning_status"] == EarlyWarningLevel.MODERATE.name.lower() else 2)
        )
        
        # Prepare result
        result = {
            "scan_date": datetime.utcnow().isoformat(),
            "patients_scanned": total_patients,
            "warnings_detected": len(warnings),
            "high_risk_count": high_risk_count,
            "moderate_risk_count": moderate_risk_count,
            "warnings": warnings
        }
        
        # Store scan results
        await analyzer.store_early_warning_scan(result)
        
        task.update_progress(100, 100, "Scan complete")
        
        return result
