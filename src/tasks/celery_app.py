"""
Celery configuration for background task processing.

This module sets up the Celery instance for processing background tasks
related to clinical analytics, longitudinal analysis, and other
computationally intensive operations.
"""

import os
from celery import Celery
from kombu import Exchange, Queue
from datetime import timedelta
from structured_logging import get_logger
from config.settings import get_settings

# Get application settings
settings = get_settings()

# Configure logger
logger = get_logger(__name__)

# Get Redis URL from environment or use default
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/1')

# Create Celery instance
celery_app = Celery(
    'emotional_wellness',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['src.tasks.clinical_analytics']
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_persistent=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Task routing
    task_routes={
        # Clinical analytics tasks
        'src.tasks.clinical_analytics.analyze_crisis_trends': {'queue': 'analytics'},
        'src.tasks.clinical_analytics.generate_risk_stratification': {'queue': 'analytics'},
        'src.tasks.clinical_analytics.compute_wellness_trajectory': {'queue': 'analytics'},
        'src.tasks.clinical_analytics.process_intervention_outcomes': {'queue': 'analytics'},
        
        # Longitudinal analysis tasks
        'src.tasks.longitudinal.analyze_patient_history': {'queue': 'analytics'},
        'src.tasks.longitudinal.early_warning_check': {'queue': 'analytics'},
        'src.tasks.longitudinal.scan_for_early_warnings': {'queue': 'analytics'},
        
        # Notification tasks
        'src.tasks.notifications.send_clinical_notification': {'queue': 'notifications'},
        'src.tasks.notifications.send_early_warning_notifications': {'queue': 'notifications'},
        'src.tasks.notifications.send_task_completion_notification': {'queue': 'notifications'},
    },
    
    # Queue configuration
    task_queues=(
        Queue('default', Exchange('default'), routing_key='default'),
        Queue('analytics', Exchange('analytics'), routing_key='analytics'),
        Queue('notifications', Exchange('notifications'), routing_key='notifications'),
    ),
    
    # Beat schedule for periodic tasks
    beat_schedule={
        # Daily clinical analytics tasks
        'daily-crisis-trends-analysis': {
            'task': 'src.tasks.clinical_analytics.analyze_crisis_trends',
            'schedule': timedelta(hours=24),
            'kwargs': {'period': 'daily'}
        },
        'weekly-risk-stratification': {
            'task': 'src.tasks.clinical_analytics.generate_risk_stratification',
            'schedule': timedelta(days=7),
            'kwargs': {'period': 'weekly'}
        },
        
        # Longitudinal analysis periodic tasks
        'daily-early-warning-scan': {
            'task': 'src.tasks.longitudinal.scan_for_early_warnings',
            'schedule': timedelta(hours=24),
            'kwargs': {'max_patients': 500}
        },
    },
    
    # Task time limits
    task_soft_time_limit=300,  # 5 minutes soft limit
    task_time_limit=600,  # 10 minutes hard limit
    
    # Task result tracking
    task_track_started=True,
    task_send_sent_event=True,
)

# Auto-discover tasks in the specified modules
celery_app.autodiscover_tasks(
    [
        "tasks.clinical_analytics",
        "tasks.longitudinal",
        "tasks.notifications",
        "tasks.security"
    ],
    force=True
)

def get_celery_app() -> Celery:
    """
    Get the global Celery application instance.
    
    Returns:
        Celery: Configured Celery application
    """
    return celery_app

# Task status tracking
class TaskStatus:
    PENDING = 'PENDING'
    STARTED = 'STARTED'
    PROGRESS = 'PROGRESS'
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'
    RETRY = 'RETRY'
    REVOKED = 'REVOKED'
