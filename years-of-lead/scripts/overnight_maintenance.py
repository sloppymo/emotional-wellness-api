#!/usr/bin/env python3
"""
Overnight Maintenance Automation Script

This script runs continuous maintenance iterations overnight, making
incremental improvements while monitoring system health and stability.
It automatically manages complexity budgets, performs rollbacks when
needed, and provides comprehensive logging.

Usage:
    python scripts/overnight_maintenance.py --hours 8    # Run for 8 hours
    python scripts/overnight_maintenance.py --budget 50  # Use budget of 50
    python scripts/overnight_maintenance.py --dry-run    # Test mode only
"""

import argparse
import time
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
import signal
import traceback

# Add src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from maintenance.maintenance_mode import MaintenanceMode
from maintenance.metrics import GameHealthMetrics

class OvernightMaintenanceManager:
    """Manages automated overnight maintenance operations"""
    
    def __init__(self, max_hours: float = 8.0, complexity_budget: int = 50, dry_run: bool = False):
        self.max_hours = max_hours
        self.total_complexity_budget = complexity_budget
        self.dry_run = dry_run
        self.project_root = project_root
        
        # State tracking
        self.start_time = None
        self.iterations_completed = 0
        self.total_improvements = 0
        self.health_history = []
        self.error_count = 0
        self.should_stop = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Initialize logging
        self.log_file = self._setup_logging()
        
        print(f"🌙 Overnight Maintenance Manager Initialized")
        print(f"   Max Duration: {max_hours} hours")
        print(f"   Complexity Budget: {complexity_budget}")
        print(f"   Dry Run: {dry_run}")
        print(f"   Log File: {self.log_file}")
        print()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n⚠️  Received signal {signum}, shutting down gracefully...")
        self.should_stop = True
    
    def _setup_logging(self) -> Path:
        """Set up comprehensive logging for the overnight run"""
        logs_dir = self.project_root / "maintenance_logs"
        logs_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = logs_dir / f"overnight_maintenance_{timestamp}.json"
        
        # Initialize log file
        initial_log = {
            "session_start": datetime.now().isoformat(),
            "max_hours": self.max_hours,
            "total_complexity_budget": self.total_complexity_budget,
            "dry_run": self.dry_run,
            "iterations": [],
            "health_snapshots": [],
            "errors": [],
            "summary": {}
        }
        
        with open(log_file, 'w') as f:
            json.dump(initial_log, f, indent=2)
        
        return log_file
    
    def _log_event(self, event_type: str, data: dict):
        """Log an event to the overnight maintenance log"""
        try:
            with open(self.log_file, 'r') as f:
                log_data = json.load(f)
            
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "type": event_type,
                "data": data
            }
            
            if event_type == "iteration":
                log_data["iterations"].append(log_entry)
            elif event_type == "health_snapshot":
                log_data["health_snapshots"].append(log_entry)
            elif event_type == "error":
                log_data["errors"].append(log_entry)
            
            with open(self.log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not write to log file: {e}")
    
    def _take_health_snapshot(self) -> dict:
        """Take a comprehensive health snapshot"""
        try:
            metrics = GameHealthMetrics()
            health_data = metrics.collect_comprehensive_metrics(self.project_root)
            
            self.health_history.append(health_data)
            self._log_event("health_snapshot", health_data)
            
            return health_data
            
        except Exception as e:
            error_data = {"error": str(e), "traceback": traceback.format_exc()}
            self._log_event("error", error_data)
            return {"overall_health": 0.0, "error": str(e)}
    
    def _should_continue(self) -> bool:
        """Check if we should continue running"""
        if self.should_stop:
            return False
        
        # Check time limit
        if self.start_time:
            elapsed = time.time() - self.start_time
            if elapsed >= self.max_hours * 3600:
                print(f"⏰ Time limit reached ({self.max_hours} hours)")
                return False
        
        # Check error threshold
        if self.error_count >= 5:
            print(f"❌ Too many errors ({self.error_count}), stopping for safety")
            return False
        
        # Check if system health is degrading consistently
        if len(self.health_history) >= 3:
            recent_health = [h.get("overall_health", 0) for h in self.health_history[-3:]]
            if all(h < 0.4 for h in recent_health):
                print(f"🏥 System health consistently low, stopping maintenance")
                return False
        
        return True
    
    def _run_single_iteration(self) -> bool:
        """Run a single maintenance iteration"""
        try:
            print(f"\n{'='*60}")
            print(f"Overnight Iteration {self.iterations_completed + 1}")
            print(f"Time Elapsed: {time.time() - self.start_time:.1f}s")
            print(f"{'='*60}")
            
            # Take health snapshot before iteration
            pre_health = self._take_health_snapshot()
            print(f"Pre-iteration health: {pre_health.get('overall_health', 0):.3f}")
            
            if self.dry_run:
                print("🧪 DRY RUN MODE - Simulating maintenance iteration")
                time.sleep(2)  # Simulate processing time
                iteration_data = {
                    "iteration": self.iterations_completed + 1,
                    "dry_run": True,
                    "simulated_improvement": "Example optimization",
                    "complexity_cost": 2
                }
                success = True
            else:
                # Initialize maintenance mode for this iteration
                maintenance = MaintenanceMode(project_root=self.project_root)
                maintenance.complexity_budget = min(10, self.total_complexity_budget)
                
                # Run one iteration
                maintenance.run_maintenance_cycle(iterations=1)
                
                # Collect results
                iteration_data = {
                    "iteration": maintenance.iteration,
                    "improvements_made": len(maintenance.improvements_log),
                    "remaining_budget": maintenance.complexity_budget,
                    "improvements": maintenance.improvements_log
                }
                
                # Update our budget
                budget_used = 10 - maintenance.complexity_budget
                self.total_complexity_budget -= budget_used
                
                success = True
            
            # Take health snapshot after iteration
            post_health = self._take_health_snapshot()
            health_change = post_health.get('overall_health', 0) - pre_health.get('overall_health', 0)
            
            iteration_data.update({
                "pre_health": pre_health.get('overall_health', 0),
                "post_health": post_health.get('overall_health', 0),
                "health_change": health_change,
                "remaining_total_budget": self.total_complexity_budget
            })
            
            self._log_event("iteration", iteration_data)
            
            print(f"✅ Iteration completed")
            print(f"   Health change: {health_change:+.3f}")
            print(f"   Remaining budget: {self.total_complexity_budget}")
            
            if not self.dry_run and iteration_data.get("improvements_made", 0) > 0:
                self.total_improvements += iteration_data["improvements_made"]
                print(f"   Improvements applied: {iteration_data['improvements_made']}")
            
            self.iterations_completed += 1
            return success
            
        except Exception as e:
            self.error_count += 1
            error_data = {
                "iteration": self.iterations_completed + 1,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
            self._log_event("error", error_data)
            print(f"❌ Error in iteration {self.iterations_completed + 1}: {e}")
            return False
    
    def _generate_final_report(self):
        """Generate a comprehensive final report"""
        end_time = time.time()
        total_duration = end_time - self.start_time
        
        # Calculate health trend
        if len(self.health_history) >= 2:
            initial_health = self.health_history[0].get("overall_health", 0)
            final_health = self.health_history[-1].get("overall_health", 0)
            health_trend = final_health - initial_health
        else:
            health_trend = 0
            initial_health = 0
            final_health = 0
        
        summary = {
            "session_end": datetime.now().isoformat(),
            "total_duration_hours": total_duration / 3600,
            "iterations_completed": self.iterations_completed,
            "total_improvements": self.total_improvements,
            "error_count": self.error_count,
            "complexity_budget_used": self.total_complexity_budget,
            "initial_health": initial_health,
            "final_health": final_health,
            "health_trend": health_trend,
            "avg_iteration_time": total_duration / max(self.iterations_completed, 1),
            "success_rate": (self.iterations_completed - self.error_count) / max(self.iterations_completed, 1)
        }
        
        # Update log file with summary
        try:
            with open(self.log_file, 'r') as f:
                log_data = json.load(f)
            log_data["summary"] = summary
            with open(self.log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not update log summary: {e}")
        
        # Print report
        print(f"\n{'='*80}")
        print(f"                    OVERNIGHT MAINTENANCE COMPLETE")
        print(f"{'='*80}")
        print(f"Duration: {total_duration/3600:.2f} hours")
        print(f"Iterations: {self.iterations_completed}")
        print(f"Improvements: {self.total_improvements}")
        print(f"Errors: {self.error_count}")
        print(f"Success Rate: {summary['success_rate']:.2%}")
        print()
        print(f"Health Trend: {initial_health:.3f} → {final_health:.3f} ({health_trend:+.3f})")
        
        if health_trend > 0.05:
            print("📈 System health IMPROVED significantly")
        elif health_trend > 0.01:
            print("📊 System health improved modestly")
        elif health_trend > -0.01:
            print("➡️  System health remained stable")
        else:
            print("📉 System health declined - manual review recommended")
        
        print(f"\nDetailed log: {self.log_file}")
        print(f"{'='*80}")
    
    def run_overnight_maintenance(self):
        """Run the main overnight maintenance loop"""
        print(f"🚀 Starting overnight maintenance at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.start_time = time.time()
        
        # Initial health check
        print("\n🔍 Initial system health check...")
        initial_health = self._take_health_snapshot()
        print(f"Initial health score: {initial_health.get('overall_health', 0):.3f}")
        
        if initial_health.get('overall_health', 0) < 0.3:
            print("⚠️  WARNING: Initial system health is very low!")
            print("   Consider manual intervention before automated maintenance")
            if not self.dry_run:
                response = input("Continue anyway? (y/N): ")
                if response.lower() != 'y':
                    print("Maintenance cancelled by user")
                    return
        
        iteration_count = 0
        max_iterations = int(self.max_hours * 10)  # Reasonable limit
        
        # Main maintenance loop
        try:
            while self._should_continue() and iteration_count < max_iterations and self.total_complexity_budget > 0:
                success = self._run_single_iteration()
                
                if not success:
                    print("⚠️  Iteration failed, waiting before retry...")
                    time.sleep(30)  # Wait before retrying
                
                iteration_count += 1
                
                # Brief pause between iterations
                time.sleep(5)
        
        except KeyboardInterrupt:
            print("\n⚠️  Maintenance interrupted by user")
        except Exception as e:
            print(f"\n❌ Fatal error in maintenance loop: {e}")
            traceback.print_exc()
        
        finally:
            # Always generate final report
            self._generate_final_report()

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Years of Lead Overnight Maintenance Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/overnight_maintenance.py                 # Run for 8 hours with budget 50
  python scripts/overnight_maintenance.py --hours 4      # Run for 4 hours
  python scripts/overnight_maintenance.py --budget 100   # Use larger complexity budget
  python scripts/overnight_maintenance.py --dry-run      # Test mode only
        """
    )
    
    parser.add_argument(
        "--hours",
        type=float,
        default=8.0,
        help="Maximum hours to run maintenance (default: 8.0)"
    )
    
    parser.add_argument(
        "--budget",
        type=int,
        default=50,
        help="Total complexity budget for all improvements (default: 50)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in test mode without making actual changes"
    )
    
    return parser.parse_args()

def main():
    """Main entry point for overnight maintenance"""
    args = parse_arguments()
    
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║                    Years of Lead                              ║")
    print("║              Overnight Maintenance Mode                       ║")
    print("║                                                               ║")
    print("║     Automated continuous improvement while you sleep          ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()
    
    # Validate arguments
    if args.hours <= 0 or args.hours > 24:
        print("❌ Error: Hours must be between 0 and 24")
        sys.exit(1)
    
    if args.budget <= 0 or args.budget > 1000:
        print("❌ Error: Budget must be between 1 and 1000")
        sys.exit(1)
    
    try:
        manager = OvernightMaintenanceManager(
            max_hours=args.hours,
            complexity_budget=args.budget,
            dry_run=args.dry_run
        )
        
        manager.run_overnight_maintenance()
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 