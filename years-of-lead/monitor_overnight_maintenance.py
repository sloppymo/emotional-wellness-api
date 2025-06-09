"""
Monitor the status of overnight maintenance in the remote workspace.

This script provides a way to check the progress and health of the overnight
maintenance system running on the remote server.
"""

import json
import os
from datetime import datetime
from pathlib import Path
import time

def get_latest_log_file():
    """Find the latest overnight maintenance log file"""
    log_dir = Path("maintenance_logs")
    if not log_dir.exists():
        return None
    
    log_files = list(log_dir.glob("overnight_maintenance_*.json"))
    if not log_files:
        return None
    
    # Get the most recent log file
    return max(log_files, key=lambda f: f.stat().st_mtime)

def format_time_elapsed(start_time):
    """Format elapsed time in human-readable format"""
    elapsed = time.time() - start_time
    hours = int(elapsed // 3600)
    minutes = int((elapsed % 3600) // 60)
    seconds = int(elapsed % 60)
    return f"{hours}h {minutes}m {seconds}s"

def monitor_maintenance():
    """Monitor the overnight maintenance status"""
    log_file = get_latest_log_file()
    
    if not log_file:
        print("❌ No overnight maintenance logs found!")
        print("\nTo start overnight maintenance from your local machine:")
        print("1. Ask the AI agent to start it in the remote workspace")
        print("2. Or commit and push your changes, then have the AI pull and run it")
        return
    
    print(f"📊 Monitoring: {log_file.name}")
    print("=" * 60)
    
    try:
        with open(log_file, 'r') as f:
            data = json.load(f)
        
        # Basic info
        start_time = datetime.fromisoformat(data['session_start'])
        print(f"🕐 Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Runtime Goal: {data['max_hours']} hours")
        print(f"💰 Complexity Budget: {data['total_complexity_budget']}")
        
        # Current status
        if 'iterations' in data and data['iterations']:
            last_iter = data['iterations'][-1]['data']
            print(f"\n📈 Current Status:")
            print(f"   Iteration: {last_iter.get('iteration', 'N/A')}")
            print(f"   Health Score: {last_iter.get('post_health', 0):.3f}")
            print(f"   Improvements Made: {last_iter.get('improvements_made', 0)}")
            print(f"   Remaining Budget: {last_iter.get('remaining_total_budget', 0)}")
        
        # Health metrics
        if 'health_snapshots' in data and data['health_snapshots']:
            latest_health = data['health_snapshots'][-1]['data']
            print(f"\n🏥 Health Metrics:")
            print(f"   Narrative Coherence: {latest_health.get('narrative_coherence', 0):.2f}")
            print(f"   Emotional Consistency: {latest_health.get('emotional_consistency', 0):.2f}")
            print(f"   Performance: {latest_health.get('performance', 0):.2f}")
            print(f"   Test Coverage: {latest_health.get('test_coverage', 0):.1%}")
            print(f"   Overall Health: {latest_health.get('overall_health', 0):.3f}")
        
        # Check if still running
        last_update = None
        if data['iterations']:
            last_update_str = data['iterations'][-1]['timestamp']
            last_update = datetime.fromisoformat(last_update_str)
            time_since_update = (datetime.now() - last_update).total_seconds()
            
            if time_since_update < 120:  # Less than 2 minutes
                print(f"\n✅ Status: RUNNING (last update {int(time_since_update)}s ago)")
            else:
                print(f"\n⚠️  Status: POSSIBLY STOPPED (no updates for {int(time_since_update/60)} minutes)")
        
        # Summary
        if 'summary' in data and data['summary']:
            print(f"\n📝 Summary:")
            summary = data['summary']
            if 'total_improvements' in summary:
                print(f"   Total Improvements: {summary['total_improvements']}")
            if 'final_health' in summary:
                print(f"   Final Health: {summary['final_health']:.3f}")
            if 'completion_reason' in summary:
                print(f"   Completion: {summary['completion_reason']}")
        
    except Exception as e:
        print(f"❌ Error reading log file: {e}")

if __name__ == "__main__":
    print("🔍 Years of Lead - Overnight Maintenance Monitor")
    print("=" * 60)
    monitor_maintenance()