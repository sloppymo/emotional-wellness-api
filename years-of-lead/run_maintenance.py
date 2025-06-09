#!/usr/bin/env python3
"""
Run maintenance mode on Years of Lead.

This script is like pressing the "auto-improve" button. It will:
1. Check the current health of your game
2. Make small, targeted improvements
3. Verify nothing broke
4. Report what was done

Usage:
    python run_maintenance.py                    # Run 1 iteration
    python run_maintenance.py --iterations 5    # Run 5 iterations
    python run_maintenance.py --health-check    # Just check health
    python run_maintenance.py --export-metrics  # Export metrics to file
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from maintenance.maintenance_mode import MaintenanceMode
from maintenance.metrics import GameHealthMetrics

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Years of Lead Maintenance Mode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_maintenance.py                    # Run 1 maintenance iteration
  python run_maintenance.py -i 3              # Run 3 iterations
  python run_maintenance.py --health-check    # Check system health only
  python run_maintenance.py --export-metrics  # Export metrics to file
        """
    )
    
    parser.add_argument(
        "-i", "--iterations",
        type=int,
        default=1,
        help="Number of maintenance iterations to run (default: 1)"
    )
    
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Only perform health check without making changes"
    )
    
    parser.add_argument(
        "--export-metrics",
        action="store_true",
        help="Export current metrics to file"
    )
    
    parser.add_argument(
        "--complexity-budget",
        type=int,
        default=10,
        help="Complexity budget for improvements (default: 10)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    return parser.parse_args()

def print_banner():
    """Print the maintenance mode banner"""
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║                    Years of Lead                              ║")
    print("║                  Maintenance Mode                             ║") 
    print("║                                                               ║")
    print("║  Automated system health monitoring and improvement           ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()

def run_health_check(project_root: Path):
    """Run a comprehensive health check"""
    print("🔍 Running comprehensive health check...")
    print("=" * 60)
    
    # Initialize metrics collector
    metrics = GameHealthMetrics()
    
    # Collect metrics
    current_metrics = metrics.collect_comprehensive_metrics(project_root)
    
    # Display results
    print(f"\n📊 System Health Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 40)
    
    health_score = current_metrics.get("overall_health", 0)
    
    if health_score >= 0.8:
        status_icon = "🟢"
        status_text = "EXCELLENT"
    elif health_score >= 0.6:
        status_icon = "🟡"
        status_text = "GOOD"
    elif health_score >= 0.4:
        status_icon = "🟠"
        status_text = "NEEDS ATTENTION"
    else:
        status_icon = "🔴"
        status_text = "CRITICAL"
    
    print(f"Overall Health: {status_icon} {status_text} ({health_score:.2f})")
    print()
    
    # Individual metrics
    metrics_display = [
        ("Test Coverage", current_metrics.get("test_coverage", 0), "📋"),
        ("Performance", current_metrics.get("performance", 0), "⚡"),
        ("Narrative Quality", current_metrics.get("narrative_coherence", 0), "📚"),
        ("Emotional Consistency", current_metrics.get("emotional_consistency", 0), "❤️")
    ]
    
    for name, value, icon in metrics_display:
        if value >= 0.8:
            color_icon = "🟢"
        elif value >= 0.6:
            color_icon = "🟡"
        else:
            color_icon = "🔴"
        print(f"{icon} {name:20} {color_icon} {value:.2f}")
    
    # Get health summary with recommendations
    summary = metrics.get_health_summary()
    if summary.get("recommendations"):
        print(f"\n💡 Recommendations:")
        for rec in summary["recommendations"]:
            print(f"   • {rec}")
    
    return current_metrics

def export_metrics(project_root: Path):
    """Export metrics to file"""
    print("📤 Exporting metrics...")
    
    metrics = GameHealthMetrics()
    current_metrics = metrics.collect_comprehensive_metrics(project_root)
    
    # Create export filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_path = project_root / "maintenance_logs" / f"metrics_export_{timestamp}.json"
    
    metrics.export_metrics(export_path)
    
    print(f"✅ Metrics exported to: {export_path}")

def main():
    """Main maintenance runner function"""
    args = parse_arguments()
    project_root = Path(".")
    
    print_banner()
    
    # Handle different modes
    if args.health_check:
        run_health_check(project_root)
        return
    
    if args.export_metrics:
        export_metrics(project_root)
        return
    
    # Regular maintenance mode
    print(f"🔧 Starting maintenance mode...")
    print(f"   Iterations: {args.iterations}")
    print(f"   Complexity Budget: {args.complexity_budget}")
    if args.verbose:
        print(f"   Verbose: Enabled")
    print()
    
    # Initialize maintenance mode
    maintenance = MaintenanceMode(project_root=project_root)
    maintenance.complexity_budget = args.complexity_budget
    
    try:
        # Run initial health check
        print("📋 Initial Health Assessment:")
        initial_metrics = run_health_check(project_root)
        
        print(f"\n🚀 Beginning {args.iterations} maintenance iteration(s)...")
        
        # Run maintenance cycle
        maintenance.run_maintenance_cycle(iterations=args.iterations)
        
        # Final health check
        print(f"\n📋 Final Health Assessment:")
        final_metrics = run_health_check(project_root)
        
        # Show summary
        print(f"\n📈 Maintenance Summary:")
        print("=" * 40)
        print(f"   Iterations completed: {maintenance.iteration}")
        print(f"   Remaining complexity budget: {maintenance.complexity_budget}")
        print(f"   Improvements made: {len(maintenance.improvements_log)}")
        
        # Show health change
        initial_health = initial_metrics.get("overall_health", 0)
        final_health = final_metrics.get("overall_health", 0)
        health_change = final_health - initial_health
        
        if health_change > 0.01:
            print(f"   Health change: 📈 +{health_change:.3f} (IMPROVED)")
        elif health_change < -0.01:
            print(f"   Health change: 📉 {health_change:.3f} (DEGRADED)")
        else:
            print(f"   Health change: ➡️  {health_change:.3f} (STABLE)")
        
        if maintenance.improvements_log:
            print(f"\n🔧 Improvements Applied:")
            for imp in maintenance.improvements_log:
                if "REVERTED" in imp['improvement']:
                    print(f"   ↩️  {imp['improvement']}")
                else:
                    print(f"   ✅ {imp['improvement']} (cost: {imp['complexity_cost']})")
        
        print(f"\n✨ Maintenance complete! System health: {final_health:.2f}")
        
    except KeyboardInterrupt:
        print(f"\n⚠️  Maintenance interrupted by user")
        print(f"   Progress saved to logs")
    except Exception as e:
        print(f"\n❌ Error during maintenance: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 