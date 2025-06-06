"""API endpoints for background task management."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from celery.result import AsyncResult
from pydantic import BaseModel, Field
import socketio

from ..tasks import celery_app
from ..tasks.clinical_analytics import (
    analyze_crisis_trends,
    generate_risk_stratification,
    compute_wellness_trajectory,
    process_intervention_outcomes
)
from ..tasks.longitudinal import (
    analyze_patient_history,
    early_warning_check,
    scan_for_early_warnings
)
from ..tasks.notifications import (
    send_clinical_notification,
    send_early_warning_notifications,
    send_task_completion_notification
)
from ..security.auth import get_current_user, require_role
from ..models.user import User
from ..structured_logging import get_logger
from ..clinical.longitudinal import TrendDirection, EarlyWarningLevel

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])

# Socket.IO for real-time updates
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins=[])


# Request/Response models
class TaskRequest(BaseModel):
    """Base task request model."""
    task_name: str
    kwargs: Dict[str, Any] = Field(default_factory=dict)


class CrisisTrendsRequest(BaseModel):
    """Request model for crisis trends analysis."""
    period: str = Field(default='daily', pattern='^(daily|weekly|monthly)$')
    start_date: Optional[str] = None


class RiskStratificationRequest(BaseModel):
    """Request model for risk stratification."""
    period: str = Field(default='weekly', pattern='^(daily|weekly|monthly)$')
    cohort_size: int = Field(default=100, ge=10, le=1000)


class WellnessTrajectoryRequest(BaseModel):
    """Request model for wellness trajectory."""
    user_id: str
    timeframe_days: int = Field(default=30, ge=7, le=365)


class InterventionOutcomesRequest(BaseModel):
    """Request model for intervention outcomes."""
    intervention_ids: Optional[List[str]] = None
    timeframe_days: int = Field(default=90, ge=7, le=365)


class PatientHistoryRequest(BaseModel):
    """Request model for patient history analysis."""
    patient_id: str
    days: int = Field(default=90, ge=7, le=365)


class EarlyWarningRequest(BaseModel):
    """Request model for early warning check."""
    patient_id: str


class EarlyWarningScanRequest(BaseModel):
    """Request model for early warning scan."""
    max_patients: int = Field(default=100, ge=10, le=1000)


class NotificationRequest(BaseModel):
    """Request model for sending notifications."""
    recipient_ids: List[str]
    subject: str
    message: str
    priority: str = Field(default="NORMAL", pattern='^(LOW|NORMAL|HIGH|URGENT)$')
    channel: str = Field(default="APP", pattern='^(APP|EMAIL|SMS)$')
    data: Optional[Dict[str, Any]] = None


class TaskResponse(BaseModel):
    """Task submission response."""
    task_id: str
    status: str
    message: str
    created_at: datetime


class TaskStatusResponse(BaseModel):
    """Task status response."""
    task_id: str
    status: str
    current: Optional[int] = None
    total: Optional[int] = None
    percent: Optional[int] = None
    message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# Task management endpoints
@router.post("/analyze/crisis-trends", response_model=TaskResponse)
async def submit_crisis_trends_analysis(
    request: CrisisTrendsRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> TaskResponse:
    """
    Submit a crisis trends analysis task.
    
    Requires authentication.
    """
    try:
        # Submit task to Celery
        task = analyze_crisis_trends.delay(
            period=request.period,
            start_date=request.start_date
        )
        
        logger.info(f"Crisis trends analysis task submitted: {task.id}", extra={
            'user_id': current_user.id,
            'task_id': task.id,
            'period': request.period
        })
        
        # Schedule WebSocket notification
        background_tasks.add_task(
            notify_task_update,
            current_user.id,
            task.id,
            'submitted'
        )
        
        return TaskResponse(
            task_id=task.id,
            status='submitted',
            message='Crisis trends analysis task submitted successfully',
            created_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error submitting crisis trends analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/risk-stratification", response_model=TaskResponse)
async def submit_risk_stratification(
    request: RiskStratificationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(['clinician', 'admin']))
) -> TaskResponse:
    """
    Submit a risk stratification analysis task.
    
    Requires clinician or admin role.
    """
    try:
        task = generate_risk_stratification.delay(
            period=request.period,
            cohort_size=request.cohort_size
        )
        
        logger.info(f"Risk stratification task submitted: {task.id}", extra={
            'user_id': current_user.id,
            'task_id': task.id,
            'period': request.period,
            'cohort_size': request.cohort_size
        })
        
        background_tasks.add_task(
            notify_task_update,
            current_user.id,
            task.id,
            'submitted'
        )
        
        return TaskResponse(
            task_id=task.id,
            status='submitted',
            message='Risk stratification task submitted successfully',
            created_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error submitting risk stratification: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/wellness-trajectory", response_model=TaskResponse)
async def submit_wellness_trajectory(
    request: WellnessTrajectoryRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> TaskResponse:
    """
    Submit a wellness trajectory analysis task.
    
    Users can only analyze their own trajectory unless they have clinician/admin role.
    """
    try:
        # Check authorization
        if request.user_id != str(current_user.id) and current_user.role not in ['clinician', 'admin']:
            raise HTTPException(
                status_code=403,
                detail="You can only analyze your own wellness trajectory"
            )
        
        task = compute_wellness_trajectory.delay(
            user_id=request.user_id,
            timeframe_days=request.timeframe_days
        )
        
        logger.info(f"Wellness trajectory task submitted: {task.id}", extra={
            'user_id': current_user.id,
            'task_id': task.id,
            'target_user_id': request.user_id,
            'timeframe_days': request.timeframe_days
        })
        
        background_tasks.add_task(
            notify_task_update,
            current_user.id,
            task.id,
            'submitted'
        )
        
        return TaskResponse(
            task_id=task.id,
            status='submitted',
            message='Wellness trajectory analysis task submitted successfully',
            created_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error submitting wellness trajectory: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/intervention-outcomes", response_model=TaskResponse)
async def submit_intervention_outcomes(
    request: InterventionOutcomesRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(['clinician', 'admin']))
) -> TaskResponse:
    """
    Submit an intervention outcomes analysis task.
    
    Requires clinician or admin role.
    """
    try:
        task = process_intervention_outcomes.delay(
            intervention_ids=request.intervention_ids,
            timeframe_days=request.timeframe_days
        )
        
        logger.info(f"Intervention outcomes task submitted: {task.id}", extra={
            'user_id': current_user.id,
            'task_id': task.id,
            'intervention_count': len(request.intervention_ids) if request.intervention_ids else 'all',
            'timeframe_days': request.timeframe_days
        })
        
        background_tasks.add_task(
            notify_task_update,
            current_user.id,
            task.id,
            'submitted'
        )
        
        return TaskResponse(
            task_id=task.id,
            status='submitted',
            message='Intervention outcomes analysis task submitted successfully',
            created_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error submitting intervention outcomes analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/patient-history", response_model=TaskResponse)
async def submit_patient_history(
    request: PatientHistoryRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(['clinician', 'admin']))
) -> TaskResponse:
    """
    Submit a patient history analysis task.
    
    Requires clinician or admin role.
    """
    try:
        task = analyze_patient_history.delay(
            patient_id=request.patient_id,
            days=request.days
        )
        
        logger.info(f"Patient history analysis task submitted: {task.id}", extra={
            'user_id': current_user.id,
            'task_id': task.id,
            'patient_id': request.patient_id,
            'days': request.days
        })
        
        background_tasks.add_task(
            notify_task_update,
            current_user.id,
            task.id,
            'submitted'
        )
        
        return TaskResponse(
            task_id=task.id,
            status='submitted',
            message='Patient history analysis task submitted successfully',
            created_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error submitting patient history analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/early-warning", response_model=TaskResponse)
async def submit_early_warning(
    request: EarlyWarningRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(['clinician', 'admin']))
) -> TaskResponse:
    """
    Submit an early warning check task for a specific patient.
    
    Requires clinician or admin role.
    """
    try:
        task = early_warning_check.delay(
            patient_id=request.patient_id
        )
        
        logger.info(f"Early warning check task submitted: {task.id}", extra={
            'user_id': current_user.id,
            'task_id': task.id,
            'patient_id': request.patient_id
        })
        
        background_tasks.add_task(
            notify_task_update,
            current_user.id,
            task.id,
            'submitted'
        )
        
        return TaskResponse(
            task_id=task.id,
            status='submitted',
            message='Early warning check task submitted successfully',
            created_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error submitting early warning check: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/early-warning-scan", response_model=TaskResponse)
async def submit_early_warning_scan(
    request: EarlyWarningScanRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(['clinician', 'admin']))
) -> TaskResponse:
    """
    Submit a scan for early warnings across all active patients.
    
    Requires clinician or admin role.
    """
    try:
        task = scan_for_early_warnings.delay(
            max_patients=request.max_patients
        )
        
        logger.info(f"Early warning scan task submitted: {task.id}", extra={
            'user_id': current_user.id,
            'task_id': task.id,
            'max_patients': request.max_patients
        })
        
        background_tasks.add_task(
            notify_task_update,
            current_user.id,
            task.id,
            'submitted'
        )
        
        # After scan completes, process notifications asynchronously
        send_early_warning_notifications.apply_async(
            args=[task.id],
            countdown=10  # Wait a bit for scan to progress
        )
        
        return TaskResponse(
            task_id=task.id,
            status='submitted',
            message='Early warning scan task submitted successfully',
            created_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error submitting early warning scan: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/notifications/send', response_model=TaskResponse)
async def submit_notification(
    request: NotificationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(['clinician', 'admin']))
) -> TaskResponse:
    """
    Submit a notification task to send notifications to users.
    
    Requires clinician or admin role.
    """
    try:
        task = send_clinical_notification.delay(
            recipient_ids=request.recipient_ids,
            subject=request.subject,
            message=request.message,
            priority=request.priority,
            channel=request.channel,
            data=request.data
        )
        
        logger.info(f"Notification task submitted: {task.id}", extra={
            'user_id': current_user.id,
            'task_id': task.id,
            'recipient_count': len(request.recipient_ids)
        })
        
        background_tasks.add_task(
            notify_task_update,
            current_user.id,
            task.id,
            'submitted'
        )
        
        return TaskResponse(
            task_id=task.id,
            status='submitted',
            message='Notification task submitted successfully',
            created_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error submitting notification task: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
) -> TaskStatusResponse:
    """Get the status of a specific task."""
    try:
        result = AsyncResult(task_id, app=celery_app)
        
        if not result:
            raise HTTPException(status_code=404, detail="Task not found")
        
        response = TaskStatusResponse(
            task_id=task_id,
            status=result.state
        )
        
        if result.state == 'PENDING':
            response.message = 'Task is waiting to be processed'
        elif result.state == 'STARTED':
            response.message = 'Task has started processing'
        elif result.state == 'PROGRESS':
            meta = result.info or {}
            response.current = meta.get('current', 0)
            response.total = meta.get('total', 100)
            response.percent = meta.get('percent', 0)
            response.message = meta.get('message', 'Processing...')
        elif result.state == 'SUCCESS':
            response.result = result.result
            response.message = 'Task completed successfully'
            response.completed_at = datetime.utcnow()
        elif result.state == 'FAILURE':
            response.error = str(result.info)
            response.message = 'Task failed'
        elif result.state == 'RETRY':
            response.message = 'Task is being retried'
        elif result.state == 'REVOKED':
            response.message = 'Task was cancelled'
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting task status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{task_id}")
async def cancel_task(
    task_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Cancel a running task."""
    try:
        result = AsyncResult(task_id, app=celery_app)
        
        if not result:
            raise HTTPException(status_code=404, detail="Task not found")
        
        result.revoke(terminate=True)
        
        logger.info(f"Task cancelled: {task_id}", extra={
            'user_id': current_user.id,
            'task_id': task_id
        })
        
        return {
            "task_id": task_id,
            "status": "cancelled",
            "message": "Task has been cancelled"
        }
        
    except Exception as e:
        logger.error(f"Error cancelling task: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_tasks(
    status: Optional[str] = Query(None, pattern='^(PENDING|STARTED|PROGRESS|SUCCESS|FAILURE|RETRY|REVOKED)$'),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_role(['clinician', 'admin']))
) -> Dict[str, Any]:
    """
    List tasks with optional status filter.
    
    Requires clinician or admin role.
    """
    try:
        # Get active tasks from Celery
        active = celery_app.control.inspect().active()
        scheduled = celery_app.control.inspect().scheduled()
        reserved = celery_app.control.inspect().reserved()
        
        tasks = []
        
        # Combine all task lists
        for worker, task_list in (active or {}).items():
            for task in task_list:
                task['status'] = 'STARTED'
                task['worker'] = worker
                tasks.append(task)
        
        for worker, task_list in (scheduled or {}).items():
            for task in task_list:
                task['status'] = 'PENDING'
                task['worker'] = worker
                tasks.append(task)
        
        for worker, task_list in (reserved or {}).items():
            for task in task_list:
                task['status'] = 'PENDING'
                task['worker'] = worker
                tasks.append(task)
        
        # Filter by status if provided
        if status:
            tasks = [t for t in tasks if t.get('status') == status]
        
        # Apply pagination
        total = len(tasks)
        tasks = tasks[offset:offset + limit]
        
        return {
            "tasks": tasks,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error listing tasks: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint for real-time task updates
@sio.event
async def connect(sid, environ):
    """Handle WebSocket connection."""
    logger.info(f"WebSocket client connected: {sid}")


@sio.event
async def disconnect(sid):
    """Handle WebSocket disconnection."""
    logger.info(f"WebSocket client disconnected: {sid}")


@sio.event
async def subscribe_task(sid, data):
    """Subscribe to task updates."""
    task_id = data.get('task_id')
    if task_id:
        await sio.enter_room(sid, f"task:{task_id}")
        logger.info(f"Client {sid} subscribed to task {task_id}")


async def notify_task_update(user_id: str, task_id: str, status: str):
    """Send task update notification via WebSocket."""
    await sio.emit(
        'task_update',
        {
            'task_id': task_id,
            'status': status,
            'timestamp': datetime.utcnow().isoformat()
        },
        room=f"task:{task_id}"
    ) 