"""Integration tests for complete clinical workflows."""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.models.assessment import Assessment
from src.models.intervention import Intervention
from src.clinical.risk_assessment import RiskAssessmentEngine, RiskLevel
from src.symbolic.veluria import VeluriaProtocolExecutor, ProtocolState, ProtocolStatus
from src.tasks.clinical_analytics import analyze_crisis_trends, compute_wellness_trajectory


class TestClinicalWorkflow:
    """Test complete clinical workflow from assessment to intervention."""
    
    @pytest.mark.asyncio
    async def test_complete_crisis_response_workflow(
        self,
        async_client: AsyncClient,
        test_user: User,
        db_session: AsyncSession,
        auth_headers: Dict[str, str]
    ):
        """Test the complete crisis response workflow."""
        
        # Step 1: Submit crisis assessment
        assessment_data = {
            "user_responses": {
                "suicide_ideation": 8,
                "self_harm_urges": 7,
                "hopelessness": 9,
                "support_system": 2,
                "coping_ability": 1
            },
            "context": {
                "recent_loss": True,
                "isolation": True,
                "previous_attempts": False
            }
        }
        
        response = await async_client.post(
            "/api/v1/assessments/submit",
            json=assessment_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        assessment_result = response.json()
        assessment_id = assessment_result["assessment_id"]
        
        # Verify high risk assessment
        assert assessment_result["risk_level"] == "HIGH"
        assert assessment_result["risk_score"] >= 0.8
        
        # Step 2: Verify protocol was triggered
        await asyncio.sleep(1)  # Allow async processing
        
        response = await async_client.get(
            f"/api/v1/interventions/active?user_id={test_user.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        interventions = response.json()
        assert len(interventions) > 0
        
        intervention = interventions[0]
        assert intervention["protocol_id"] == "crisis_stabilization_v1"
        assert intervention["status"] == "IN_PROGRESS"
        
        # Step 3: Interact with intervention protocol
        intervention_id = intervention["id"]
        
        # Submit user response to protocol
        response = await async_client.post(
            f"/api/v1/interventions/{intervention_id}/respond",
            json={"response": "I need help", "rating": 9},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Step 4: Verify escalation was triggered
        response = await async_client.get(
            f"/api/v1/interventions/{intervention_id}/escalations",
            headers=auth_headers
        )
        assert response.status_code == 200
        escalations = response.json()
        assert len(escalations) > 0
        assert escalations[0]["level"] == "CRITICAL"
        
        # Step 5: Verify notifications were sent
        response = await async_client.get(
            f"/api/v1/notifications/user/{test_user.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        notifications = response.json()
        assert any(n["type"] == "CRISIS_ALERT" for n in notifications)
        
        # Step 6: Submit follow-up assessment
        await asyncio.sleep(2)  # Simulate time passing
        
        followup_data = {
            "user_responses": {
                "suicide_ideation": 5,
                "self_harm_urges": 4,
                "hopelessness": 6,
                "support_system": 4,
                "coping_ability": 3
            },
            "context": {
                "received_help": True,
                "feeling_supported": True
            }
        }
        
        response = await async_client.post(
            "/api/v1/assessments/submit",
            json=followup_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        followup_result = response.json()
        
        # Verify risk reduction
        assert followup_result["risk_level"] == "MODERATE"
        assert followup_result["risk_score"] < assessment_result["risk_score"]
        
        # Step 7: Complete intervention
        response = await async_client.post(
            f"/api/v1/interventions/{intervention_id}/complete",
            json={"outcome": "STABILIZED", "notes": "User engaged with support"},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Step 8: Verify intervention outcome
        response = await async_client.get(
            f"/api/v1/interventions/{intervention_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        completed_intervention = response.json()
        assert completed_intervention["status"] == "COMPLETED"
        assert completed_intervention["outcome"]["effectiveness"] >= 0.6
    
    @pytest.mark.asyncio
    async def test_longitudinal_monitoring_workflow(
        self,
        async_client: AsyncClient,
        test_user: User,
        db_session: AsyncSession,
        auth_headers: Dict[str, str]
    ):
        """Test longitudinal monitoring and early warning detection."""
        
        # Create assessment history
        assessment_history = []
        base_date = datetime.utcnow() - timedelta(days=30)
        
        # Simulate declining wellness trajectory
        for day in range(30):
            date = base_date + timedelta(days=day)
            
            # Gradually increasing risk scores
            risk_score = 0.3 + (day * 0.02)  # Goes from 0.3 to 0.88
            
            assessment = Assessment(
                id=str(uuid4()),
                user_id=test_user.id,
                risk_score=min(risk_score, 0.95),
                risk_level=RiskLevel.HIGH if risk_score > 0.7 else RiskLevel.MODERATE,
                created_at=date,
                data={
                    "responses": {
                        "mood": 7 - (day * 0.2),
                        "anxiety": 3 + (day * 0.2),
                        "sleep_quality": 6 - (day * 0.15)
                    }
                }
            )
            db_session.add(assessment)
            assessment_history.append(assessment)
        
        await db_session.commit()
        
        # Step 1: Request wellness trajectory analysis
        response = await async_client.post(
            "/api/v1/tasks/analyze/wellness-trajectory",
            json={
                "user_id": str(test_user.id),
                "timeframe_days": 30
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        task_result = response.json()
        task_id = task_result["task_id"]
        
        # Step 2: Wait for analysis to complete
        max_attempts = 30
        attempts = 0
        
        while attempts < max_attempts:
            response = await async_client.get(
                f"/api/v1/tasks/status/{task_id}",
                headers=auth_headers
            )
            assert response.status_code == 200
            status = response.json()
            
            if status["status"] == "SUCCESS":
                break
                
            await asyncio.sleep(1)
            attempts += 1
        
        assert status["status"] == "SUCCESS"
        trajectory_result = status["result"]
        
        # Verify trajectory analysis
        assert trajectory_result["trends"]["direction"] == "DECLINING"
        assert trajectory_result["improvement_rate"] < -0.5  # Negative improvement
        assert len(trajectory_result["risk_factors"]) > 0
        
        # Step 3: Check early warning detection
        response = await async_client.post(
            "/api/v1/tasks/analyze/early-warning",
            json={"patient_id": str(test_user.id)},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Step 4: Verify early warning alerts
        response = await async_client.get(
            "/dashboard/api/early-warning-indicators",
            headers=auth_headers
        )
        assert response.status_code == 200
        warnings = response.json()
        
        user_warnings = [w for w in warnings["criticalAlerts"] 
                        if w["patientId"] == str(test_user.id)]
        assert len(user_warnings) > 0
        assert user_warnings[0]["urgency"] == "HIGH"
        
        # Step 5: Trigger preventive intervention
        response = await async_client.post(
            "/api/v1/interventions/preventive",
            json={
                "user_id": str(test_user.id),
                "reason": "EARLY_WARNING_DETECTION",
                "protocol_id": "preventive_support_v1"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        preventive_intervention = response.json()
        
        assert preventive_intervention["type"] == "PREVENTIVE"
        assert preventive_intervention["status"] == "SCHEDULED"
    
    @pytest.mark.asyncio
    async def test_multi_modal_intervention_workflow(
        self,
        async_client: AsyncClient,
        test_user: User,
        auth_headers: Dict[str, str]
    ):
        """Test workflow with multiple intervention modalities."""
        
        # Step 1: Submit moderate risk assessment
        assessment_data = {
            "user_responses": {
                "depression_score": 6,
                "anxiety_score": 7,
                "stress_level": 8,
                "functioning": 4
            },
            "context": {
                "work_stress": True,
                "relationship_issues": True
            }
        }
        
        response = await async_client.post(
            "/api/v1/assessments/submit",
            json=assessment_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        assessment = response.json()
        
        # Step 2: Request multi-modal intervention
        response = await async_client.post(
            "/api/v1/interventions/multi-modal",
            json={
                "assessment_id": assessment["assessment_id"],
                "modalities": ["CBT", "MINDFULNESS", "PEER_SUPPORT"]
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        intervention_plan = response.json()
        
        assert len(intervention_plan["interventions"]) == 3
        
        # Step 3: Engage with each modality
        for intervention in intervention_plan["interventions"]:
            intervention_id = intervention["id"]
            
            # Start intervention
            response = await async_client.post(
                f"/api/v1/interventions/{intervention_id}/start",
                headers=auth_headers
            )
            assert response.status_code == 200
            
            # Submit progress
            response = await async_client.post(
                f"/api/v1/interventions/{intervention_id}/progress",
                json={
                    "completed_activities": 3,
                    "engagement_score": 8,
                    "subjective_improvement": 7
                },
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Step 4: Get aggregated outcomes
        response = await async_client.get(
            f"/api/v1/interventions/outcomes/aggregate?user_id={test_user.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        outcomes = response.json()
        
        assert outcomes["overall_effectiveness"] >= 0.6
        assert outcomes["modality_effectiveness"]["CBT"] >= 0.5
        assert outcomes["modality_effectiveness"]["MINDFULNESS"] >= 0.5
        
    @pytest.mark.asyncio
    async def test_crisis_to_recovery_workflow(
        self,
        async_client: AsyncClient,
        test_user: User,
        auth_headers: Dict[str, str]
    ):
        """Test complete journey from crisis to recovery."""
        
        # Phase 1: Crisis
        crisis_assessment = {
            "user_responses": {
                "crisis_severity": 9,
                "immediate_danger": True,
                "support_available": False
            }
        }
        
        response = await async_client.post(
            "/api/v1/assessments/crisis",
            json=crisis_assessment,
            headers=auth_headers
        )
        assert response.status_code == 200
        crisis_response = response.json()
        
        # Verify immediate response
        assert crisis_response["immediate_action"] == "EMERGENCY_PROTOCOL"
        assert crisis_response["escalation_triggered"] == True
        
        # Phase 2: Stabilization (after 24 hours)
        await asyncio.sleep(2)  # Simulate time passing
        
        stabilization_assessment = {
            "user_responses": {
                "crisis_severity": 5,
                "immediate_danger": False,
                "engaged_support": True
            }
        }
        
        response = await async_client.post(
            "/api/v1/assessments/submit",
            json=stabilization_assessment,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Phase 3: Recovery planning
        response = await async_client.post(
            "/api/v1/recovery/plan",
            json={
                "user_id": str(test_user.id),
                "goals": [
                    "Establish daily routine",
                    "Reconnect with support system",
                    "Develop coping strategies"
                ],
                "duration_weeks": 12
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        recovery_plan = response.json()
        
        assert recovery_plan["status"] == "ACTIVE"
        assert len(recovery_plan["milestones"]) > 0
        
        # Phase 4: Track recovery progress
        for week in range(4):
            response = await async_client.post(
                f"/api/v1/recovery/progress",
                json={
                    "plan_id": recovery_plan["id"],
                    "week": week + 1,
                    "mood_average": 5 + (week * 0.5),
                    "goals_completed": week + 1,
                    "setbacks": max(0, 2 - week)
                },
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Phase 5: Evaluate recovery
        response = await async_client.get(
            f"/api/v1/recovery/evaluate/{recovery_plan['id']}",
            headers=auth_headers
        )
        assert response.status_code == 200
        evaluation = response.json()
        
        assert evaluation["recovery_trajectory"] == "POSITIVE"
        assert evaluation["risk_reduction"] >= 0.4
        assert evaluation["recommendation"] == "CONTINUE_MONITORING"


class TestErrorHandling:
    """Test error handling in clinical workflows."""
    
    @pytest.mark.asyncio
    async def test_assessment_validation_errors(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str]
    ):
        """Test various assessment validation error scenarios."""
        
        # Missing required fields
        response = await async_client.post(
            "/api/v1/assessments/submit",
            json={"user_responses": {}},
            headers=auth_headers
        )
        assert response.status_code == 422
        error = response.json()
        assert error["error"] == "VALIDATION_ERROR"
        
        # Invalid score ranges
        response = await async_client.post(
            "/api/v1/assessments/submit",
            json={
                "user_responses": {
                    "mood": 15,  # Should be 0-10
                    "anxiety": -5  # Should be positive
                }
            },
            headers=auth_headers
        )
        assert response.status_code == 422
        
        # Invalid data types
        response = await async_client.post(
            "/api/v1/assessments/submit",
            json={
                "user_responses": {
                    "mood": "very bad",  # Should be numeric
                    "anxiety": [1, 2, 3]  # Should be single value
                }
            },
            headers=auth_headers
        )
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_intervention_state_errors(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str]
    ):
        """Test intervention state transition errors."""
        
        # Try to complete non-existent intervention
        response = await async_client.post(
            "/api/v1/interventions/fake-id/complete",
            json={"outcome": "SUCCESS"},
            headers=auth_headers
        )
        assert response.status_code == 404
        error = response.json()
        assert error["error"] == "RESOURCE_NOT_FOUND"
        
        # Try invalid state transition
        # First create an intervention
        response = await async_client.post(
            "/api/v1/interventions/create",
            json={
                "protocol_id": "test_protocol",
                "user_id": "test-user"
            },
            headers=auth_headers
        )
        intervention_id = response.json()["id"]
        
        # Try to complete before starting
        response = await async_client.post(
            f"/api/v1/interventions/{intervention_id}/complete",
            json={"outcome": "SUCCESS"},
            headers=auth_headers
        )
        assert response.status_code == 400
        error = response.json()
        assert error["error"] == "INVALID_STATE_TRANSITION"
    
    @pytest.mark.asyncio
    async def test_rate_limiting(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str]
    ):
        """Test rate limiting on sensitive endpoints."""
        
        # Spam assessment submissions
        for i in range(15):  # Assuming limit is 10 per minute
            response = await async_client.post(
                "/api/v1/assessments/submit",
                json={
                    "user_responses": {"mood": 5, "anxiety": 5}
                },
                headers=auth_headers
            )
            
            if i < 10:
                assert response.status_code == 200
            else:
                assert response.status_code == 429
                error = response.json()
                assert error["error"] == "RATE_LIMIT_EXCEEDED"
                assert "retry_after" in error["details"]
    
    @pytest.mark.asyncio 
    async def test_concurrent_intervention_handling(
        self,
        async_client: AsyncClient,
        test_user: User,
        auth_headers: Dict[str, str]
    ):
        """Test handling of concurrent interventions."""
        
        # Try to create multiple crisis interventions simultaneously
        tasks = []
        for i in range(5):
            task = async_client.post(
                "/api/v1/interventions/crisis",
                json={
                    "user_id": str(test_user.id),
                    "severity": "HIGH"
                },
                headers=auth_headers
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Only one crisis intervention should succeed
        success_count = sum(1 for r in responses 
                          if not isinstance(r, Exception) and r.status_code == 200)
        assert success_count == 1
        
        # Others should get conflict error
        conflict_count = sum(1 for r in responses 
                           if not isinstance(r, Exception) and r.status_code == 409)
        assert conflict_count == 4 