#!/usr/bin/env python3
"""
Slack Webhooks Demo for Emotional Wellness API

This script demonstrates all the Slack webhook integrations implemented
for the Emotional Wellness API. It provides examples of each notification
type and how to use the notification dashboard.
"""

import os
import sys
import json
import argparse
import time
from datetime import datetime

# Configure environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ["SLACK_WEBHOOK_URL"] = os.environ.get("SLACK_WEBHOOK_URL", "")

# Import modules
from src.utils.slack_alerts import (
    SymbolicAlert, 
    send_symbolic_alert,
    send_test_results_notification,
    send_deployment_notification
)
from src.monitoring.health_metaphors import (
    send_metaphorical_alert,
    send_system_health_summary
)
from src.analytics.archetype_visualizer import (
    generate_archetype_heatmap,
    generate_archetype_trend_report
)
from src.crisis_management.slack_ops import (
    initiate_crisis_protocol, 
    assign_crisis_case
)
from src.reporting.weather_report import (
    send_emotional_weather_report,
    send_weekly_emotional_forecast
)
from src.team_coordination.therapist_bot import (
    assign_crisis_case as assign_therapist_case,
    request_consultation,
    send_shift_report
)
from src.dashboard.notification_bot import dashboard


def check_webhook_url():
    """Check if webhook URL is configured."""
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "")
    if not webhook_url:
        print("\n⚠️  No Slack webhook URL configured!")
        print("Please set the SLACK_WEBHOOK_URL environment variable:")
        print("  export SLACK_WEBHOOK_URL='https://hooks.slack.com/services/your/webhook/url'")
        return False
    return True


def demo_symbolic_alert():
    """Demo symbolic emotional state alerts."""
    print("\n🔄 Sending symbolic emotional state alert...")
    
    alert = SymbolicAlert(
        archetype="Hero's Journey",
        symbol_pattern="Water→Fire→Mountain→Star",
        valence_trend="rising",
        timestamp=datetime.now()
    )
    
    response = send_symbolic_alert(alert)
    print(f"✅ Response: {json.dumps(response, indent=2)}")


def demo_system_health():
    """Demo metaphorical system health alerts."""
    print("\n🔄 Sending metaphorical system health alert...")
    
    response = send_metaphorical_alert(
        metric="high_cpu",
        value=0.89,
        additional_info={
            "Duration": "15 minutes",
            "Affected Services": "Analysis Engine, Crisis Detection"
        }
    )
    print(f"✅ Response: {json.dumps(response, indent=2)}")
    
    print("\n🔄 Sending system health summary...")
    metrics = {
        "high_cpu": 0.89,
        "high_memory": 0.75,
        "high_latency": 0.43,
        "crisis_events": 0.12,
        "normal_operation": 0.65
    }
    response = send_system_health_summary(metrics)
    print(f"✅ Response: {json.dumps(response, indent=2)}")


def demo_archetype_visualization():
    """Demo archetype distribution heatmap."""
    print("\n🔄 Generating archetype distribution heatmap...")
    
    response = generate_archetype_heatmap()
    print(f"✅ Response: {json.dumps(response, indent=2)}")
    
    print("\n🔄 Generating archetype trend report...")
    response = generate_archetype_trend_report(days=7)
    print(f"✅ Response: {json.dumps(response, indent=2)}")


def demo_crisis_protocols():
    """Demo crisis intervention protocols."""
    print("\n🔄 Initiating crisis protocol (level 1)...")
    
    response = initiate_crisis_protocol(
        level=1,
        symbolic_pattern="Shadow→Abyss→Light",
        metadata={
            "pattern_intensity": "Medium",
            "symbol_frequency": "Increasing",
            "archetype_shift": "Shadow→Hero"
        }
    )
    print(f"✅ Response: {json.dumps(response, indent=2)}")
    
    print("\n🔄 Assigning crisis case...")
    response = assign_crisis_case(
        therapist_id="U123456",
        case_meta={
            "symbol_sequence": "Shadow→Abyss→Light",
            "urgency": 7,
            "archetype": "Shadow Confrontation",
            "valence_trend": "rising"
        }
    )
    print(f"✅ Response: {json.dumps(response, indent=2)}")


def demo_weather_reports():
    """Demo emotional weather reports."""
    print("\n🔄 Sending emotional weather report...")
    
    response = send_emotional_weather_report()
    print(f"✅ Response: {json.dumps(response, indent=2)}")
    
    print("\n🔄 Sending weekly emotional forecast...")
    response = send_weekly_emotional_forecast()
    print(f"✅ Response: {json.dumps(response, indent=2)}")


def demo_therapist_coordination():
    """Demo therapist coordination tools."""
    print("\n🔄 Sending case assignment to therapist...")
    
    response = assign_therapist_case(
        therapist_id="U123456",
        case_meta={
            "symbol_sequence": "Mountain→River→Bridge",
            "archetype": "Hero's Journey",
            "intensity": "Medium",
            "duration": "3 days"
        },
        priority=6
    )
    print(f"✅ Response: {json.dumps(response, indent=2)}")
    
    print("\n🔄 Sending consultation request...")
    response = request_consultation(
        requester_id="U123456",
        case_id="case-12345678",
        consultation_type="Pattern Interpretation",
        details="Unusual mix of Water and Fire symbols within Hero's Journey",
        urgency=3
    )
    print(f"✅ Response: {json.dumps(response, indent=2)}")
    
    print("\n🔄 Sending shift report...")
    response = send_shift_report(
        shift_data={
            "new_cases": 12,
            "resolved_cases": 9,
            "escalations": 2,
            "trend": "stable",
            "notable_patterns": [
                "Increased Hero's Journey transitions",
                "Decreased Shadow confrontations",
                "Stable Caregiver patterns"
            ]
        },
        shift_type="day"
    )
    print(f"✅ Response: {json.dumps(response, indent=2)}")


def demo_notification_dashboard():
    """Demo notification dashboard/bot."""
    print("\n🔄 Sending notification preferences dashboard...")
    
    # Note: In a real Slack app integration, user_id would be a real Slack user ID
    # For webhook demonstrations, we need to use a channel name instead
    response = dashboard.send_settings_message("notification-settings")
    print(f"✅ Response: {json.dumps(response, indent=2)}")
    
    print("\n🔄 Simulating user interaction with dashboard...")
    response = dashboard.handle_interaction(
        user_id="notification-settings",
        action_id="toggle_symbolic_alerts_true"
    )
    print(f"✅ Response: {json.dumps(response, indent=2)}")


def demo_deployment_notification():
    """Demo deployment notification."""
    print("\n🔄 Sending deployment notification...")
    
    response = send_deployment_notification(
        environment="production",
        status="success",
        version="v1.2.3",
        changes=[
            "Added symbolic emotional alerts",
            "Improved crisis detection",
            "Fixed memory leak in pattern analysis",
            "Updated HIPAA compliance logging"
        ],
        triggered_by="GitHub Actions CI/CD"
    )
    print(f"✅ Response: {json.dumps(response, indent=2)}")


def demo_test_results():
    """Demo test results notification."""
    print("\n🔄 Sending test results notification...")
    
    response = send_test_results_notification({
        "success": True,
        "total": 153,
        "passed": 153,
        "failed": 0,
        "duration": "42.3s"
    }, test_type="HIPAA Compliance Tests")
    print(f"✅ Response: {json.dumps(response, indent=2)}")


def main():
    """Run demos based on command line arguments."""
    parser = argparse.ArgumentParser(
        description="Demo Slack webhook integrations for Emotional Wellness API"
    )
    
    parser.add_argument(
        "--all", 
        action="store_true",
        help="Run all demos"
    )
    
    parser.add_argument(
        "--symbolic", 
        action="store_true",
        help="Demo symbolic emotional state alerts"
    )
    
    parser.add_argument(
        "--health", 
        action="store_true",
        help="Demo metaphorical system health alerts"
    )
    
    parser.add_argument(
        "--archetypes", 
        action="store_true",
        help="Demo archetype visualization"
    )
    
    parser.add_argument(
        "--crisis", 
        action="store_true",
        help="Demo crisis intervention protocols"
    )
    
    parser.add_argument(
        "--weather", 
        action="store_true",
        help="Demo emotional weather reports"
    )
    
    parser.add_argument(
        "--therapist", 
        action="store_true",
        help="Demo therapist coordination"
    )
    
    parser.add_argument(
        "--dashboard", 
        action="store_true",
        help="Demo notification dashboard/bot"
    )
    
    parser.add_argument(
        "--deployment", 
        action="store_true",
        help="Demo deployment notification"
    )
    
    parser.add_argument(
        "--tests", 
        action="store_true",
        help="Demo test results notification"
    )
    
    args = parser.parse_args()
    
    # Check webhook URL
    if not check_webhook_url():
        sys.exit(1)
    
    print("\n🚀 Emotional Wellness API - Slack Webhook Demo")
    print("=================================================")
    
    # Run selected demos or all if none specified
    run_all = args.all or not any([
        args.symbolic, args.health, args.archetypes, args.crisis,
        args.weather, args.therapist, args.dashboard, args.deployment,
        args.tests
    ])
    
    if run_all or args.symbolic:
        demo_symbolic_alert()
        
    if run_all or args.health:
        demo_system_health()
        
    if run_all or args.archetypes:
        demo_archetype_visualization()
        
    if run_all or args.crisis:
        demo_crisis_protocols()
        
    if run_all or args.weather:
        demo_weather_reports()
        
    if run_all or args.therapist:
        demo_therapist_coordination()
        
    if run_all or args.dashboard:
        demo_notification_dashboard()
        
    if run_all or args.deployment:
        demo_deployment_notification()
        
    if run_all or args.tests:
        demo_test_results()
    
    print("\n✅ Demo completed!")
    print("=================================================")
    print("To customize which notifications you receive:")
    print("1. Go to your Slack workspace")
    print("2. Find the 'notification-settings' channel")
    print("3. Use the interactive buttons to configure your preferences")
    print("=================================================\n")


if __name__ == "__main__":
    main()
