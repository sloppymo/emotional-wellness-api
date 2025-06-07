#!/usr/bin/env python3
"""
Advanced Debug CLI Tool for Emotional Wellness API

A comprehensive command-line interface for diagnosing system problems,
running tests, and monitoring system health in real-time.

Usage:
    python scripts/debug_cli.py health                    # System health check
    python scripts/debug_cli.py diagnose [component]      # Run diagnostics
    python scripts/debug_cli.py test [test_type]         # Run tests
    python scripts/debug_cli.py monitor                   # Real-time monitoring
    python scripts/debug_cli.py crisis-debug             # Crisis intervention debugging
    python scripts/debug_cli.py performance             # Performance analysis
    python scripts/debug_cli.py logs [component]        # View component logs
"""

import asyncio
import argparse
import sys
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from structured_logging import get_logger, setup_logging
    from config.settings import get_settings
    from monitoring.moss_health import check_moss_health
    from monitoring.celery_health import check_celery_health
    from monitoring.integration_health import check_integration_health
    from routers.health import system_status
    from symbolic.moss.crisis_classifier import CrisisClassifier
    from symbolic.veluria.intervention_protocol import VeluriaProtocolExecutor
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running from the project root and dependencies are installed")
    sys.exit(1)


class DebugCLI:
    """Advanced debugging CLI with comprehensive diagnostic capabilities."""
    
    def __init__(self):
        self.logger = get_logger("debug_cli")
        self.settings = get_settings()
        
        # Color codes for output
        self.colors = {
            'green': '\033[92m',
            'yellow': '\033[93m', 
            'red': '\033[91m',
            'blue': '\033[94m',
            'purple': '\033[95m',
            'cyan': '\033[96m',
            'white': '\033[97m',
            'bold': '\033[1m',
            'end': '\033[0m'
        }
    
    def print_colored(self, text: str, color: str = 'white', bold: bool = False):
        """Print colored text to terminal."""
        color_code = self.colors.get(color, self.colors['white'])
        bold_code = self.colors['bold'] if bold else ''
        end_code = self.colors['end']
        print(f"{bold_code}{color_code}{text}{end_code}")
    
    def print_header(self, title: str):
        """Print a formatted header."""
        print("\n" + "="*60)
        self.print_colored(f"  {title}", 'cyan', bold=True)
        print("="*60)
    
    def print_status(self, component: str, status: str, details: str = ""):
        """Print component status with colored indicators."""
        if status.lower() in ['healthy', 'ok', 'success', 'operational']:
            indicator = f"{self.colors['green']}✓{self.colors['end']}"
        elif status.lower() in ['degraded', 'warning', 'elevated']:
            indicator = f"{self.colors['yellow']}⚠{self.colors['end']}"
        elif status.lower() in ['failing', 'critical', 'error', 'unhealthy']:
            indicator = f"{self.colors['red']}✗{self.colors['end']}"
        else:
            indicator = f"{self.colors['blue']}?{self.colors['end']}"
        
        print(f"  {indicator} {component:20} {status:15} {details}")
    
    async def health_check(self):
        """Comprehensive system health check."""
        self.print_header("SYSTEM HEALTH CHECK")
        
        start_time = time.time()
        
        # Check basic connectivity
        self.print_colored("\n🔍 Checking basic connectivity...", 'blue')
        
        # Database check
        try:
            from database.session import get_async_session
            from sqlalchemy import text
            
            async with get_async_session() as session:
                await session.execute(text("SELECT 1"))
            self.print_status("Database", "Healthy", "Connection successful")
        except Exception as e:
            self.print_status("Database", "Failed", str(e)[:50])
        
        # Redis check
        try:
            from cache.redis_client import get_redis_client
            redis = await get_redis_client()
            await redis.ping()
            self.print_status("Redis", "Healthy", "Connection successful")
        except Exception as e:
            self.print_status("Redis", "Failed", str(e)[:50])
        
        # MOSS system check
        self.print_colored("\n🧠 Checking MOSS system...", 'blue')
        try:
            moss_health = await check_moss_health()
            self.print_status("MOSS", moss_health.overall_status, 
                            f"{len(moss_health.components)} components checked")
            
            for component in moss_health.components:
                self.print_status(f"  └─ {component.component.value}", 
                                component.status.value, 
                                f"{component.response_time_ms:.1f}ms")
        except Exception as e:
            self.print_status("MOSS", "Failed", str(e)[:50])
        
        # VELURIA system check
        self.print_colored("\n🚨 Checking VELURIA system...", 'blue')
        try:
            executor = VeluriaProtocolExecutor()
            self.print_status("VELURIA", "Healthy", "Protocol executor ready")
        except Exception as e:
            self.print_status("VELURIA", "Failed", str(e)[:50])
        
        # Integration health check  
        self.print_colored("\n🔗 Checking integrations...", 'blue')
        try:
            integration_health = await check_integration_health()
            healthy_count = sum(1 for i in integration_health.integrations 
                              if i.status.value == "healthy")
            total_count = len(integration_health.integrations)
            
            self.print_status("Integrations", integration_health.overall_status,
                            f"{healthy_count}/{total_count} healthy")
            
            for integration in integration_health.integrations:
                self.print_status(f"  └─ {integration.integration_type.value}",
                                integration.status.value,
                                f"{integration.latency_ms:.1f}ms" if integration.latency_ms else "")
        except Exception as e:
            self.print_status("Integrations", "Failed", str(e)[:50])
        
        # Task system check
        self.print_colored("\n⚙️  Checking task system...", 'blue')
        try:
            celery_health = await check_celery_health()
            self.print_status("Celery", celery_health.status,
                            f"{celery_health.total_active_tasks} active tasks")
            
            for worker in celery_health.workers:
                self.print_status(f"  └─ {worker.name}", worker.status,
                                f"{worker.active_tasks} active")
        except Exception as e:
            self.print_status("Celery", "Failed", str(e)[:50])
        
        total_time = time.time() - start_time
        self.print_colored(f"\n✨ Health check completed in {total_time:.2f}s", 'green')
    
    async def diagnose_component(self, component: str = None):
        """Run detailed diagnostics on specific component or all components."""
        if component:
            self.print_header(f"DIAGNOSING COMPONENT: {component.upper()}")
        else:
            self.print_header("COMPREHENSIVE SYSTEM DIAGNOSTICS")
        
        components_to_check = [component] if component else [
            'moss', 'veluria', 'database', 'redis', 'integrations', 'tasks'
        ]
        
        for comp in components_to_check:
            await self._diagnose_single_component(comp)
    
    async def _diagnose_single_component(self, component: str):
        """Diagnose a single component with detailed analysis."""
        self.print_colored(f"\n🔬 Analyzing {component}...", 'blue')
        
        start_time = time.time()
        
        if component == 'moss':
            await self._diagnose_moss()
        elif component == 'veluria':
            await self._diagnose_veluria()
        elif component == 'database':
            await self._diagnose_database()
        elif component == 'redis':
            await self._diagnose_redis()
        elif component == 'integrations':
            await self._diagnose_integrations()
        elif component == 'tasks':
            await self._diagnose_tasks()
        else:
            self.print_colored(f"Unknown component: {component}", 'red')
        
        elapsed = time.time() - start_time
        self.print_colored(f"  └─ Analysis completed in {elapsed:.2f}s", 'cyan')
    
    async def _diagnose_moss(self):
        """Detailed MOSS system diagnostics."""
        try:
            # Test crisis classifier
            classifier = CrisisClassifier()
            test_text = "I'm feeling a bit overwhelmed today"
            
            start_time = time.time()
            result = await classifier.assess_crisis_risk(
                text=test_text,
                user_id="debug_test_user"
            )
            response_time = (time.time() - start_time) * 1000
            
            self.print_status("Crisis Classification", "Working", 
                            f"{response_time:.1f}ms response")
            self.print_status("  └─ Test Assessment", f"Severity: {result.severity.value}",
                            f"Confidence: {result.confidence:.2f}")
            
            # Test threshold system
            from symbolic.moss.detection_thresholds import DetectionThresholds
            thresholds = DetectionThresholds()
            
            self.print_status("Detection Thresholds", "Working",
                            "Threshold configuration loaded")
            
            # Test audit logging
            from symbolic.moss.audit_logging import MOSSAuditLogger
            audit_logger = MOSSAuditLogger()
            
            test_event = await audit_logger.log_system_error(
                error_type="debug_test",
                error_message="Diagnostic test event",
                component="debug_cli"
            )
            
            self.print_status("Audit Logging", "Working",
                            f"Test event: {test_event[:8]}...")
            
        except Exception as e:
            self.print_status("MOSS Diagnostics", "Failed", str(e)[:50])
    
    async def _diagnose_veluria(self):
        """Detailed VELURIA system diagnostics."""
        try:
            from symbolic.veluria.intervention_protocol import VeluriaProtocolExecutor
            from symbolic.veluria.protocol_library import get_protocol_library
            from symbolic.veluria.escalation_manager import EscalationManager
            
            # Test protocol executor
            executor = VeluriaProtocolExecutor()
            self.print_status("Protocol Executor", "Working", "Instance created")
            
            # Test protocol library
            protocols = get_protocol_library()
            protocol_count = len(protocols)
            self.print_status("Protocol Library", "Working", 
                            f"{protocol_count} protocols loaded")
            
            # Test escalation manager
            escalation_manager = EscalationManager()
            self.print_status("Escalation Manager", "Working", "Instance created")
            
            # Test pattern detection
            from symbolic.veluria.pattern_detection import PatternDetector
            detector = PatternDetector()
            self.print_status("Pattern Detection", "Working", "Detector ready")
            
        except Exception as e:
            self.print_status("VELURIA Diagnostics", "Failed", str(e)[:50])
    
    async def _diagnose_database(self):
        """Detailed database diagnostics."""
        try:
            from database.session import get_async_session
            from sqlalchemy import text
            
            async with get_async_session() as session:
                # Test basic connectivity
                start_time = time.time()
                await session.execute(text("SELECT 1"))
                basic_time = (time.time() - start_time) * 1000
                
                self.print_status("Basic Query", "Working", f"{basic_time:.1f}ms")
                
                # Test table access
                tables_to_test = ['users', 'sessions', 'emotional_states']
                for table in tables_to_test:
                    try:
                        start_time = time.time()
                        result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        count = result.scalar()
                        query_time = (time.time() - start_time) * 1000
                        
                        self.print_status(f"Table: {table}", "Accessible",
                                        f"{count} rows, {query_time:.1f}ms")
                    except Exception as e:
                        self.print_status(f"Table: {table}", "Error", str(e)[:30])
                
        except Exception as e:
            self.print_status("Database Diagnostics", "Failed", str(e)[:50])
    
    async def _diagnose_redis(self):
        """Detailed Redis diagnostics."""
        try:
            from cache.redis_client import get_redis_client
            redis = await get_redis_client()
            
            # Test basic operations
            start_time = time.time()
            await redis.ping()
            ping_time = (time.time() - start_time) * 1000
            
            self.print_status("Ping", "Working", f"{ping_time:.1f}ms")
            
            # Test set/get operations
            test_key = f"debug_test_{int(time.time())}"
            
            start_time = time.time()
            await redis.set(test_key, "test_value", ex=60)
            set_time = (time.time() - start_time) * 1000
            
            start_time = time.time()
            value = await redis.get(test_key)
            get_time = (time.time() - start_time) * 1000
            
            await redis.delete(test_key)
            
            self.print_status("Set Operation", "Working", f"{set_time:.1f}ms")
            self.print_status("Get Operation", "Working", f"{get_time:.1f}ms")
            
            # Get Redis info
            info = await redis.info()
            memory_usage = info.get('used_memory_human', 'unknown')
            connected_clients = info.get('connected_clients', 0)
            
            self.print_status("Memory Usage", memory_usage, f"{connected_clients} clients")
            
        except Exception as e:
            self.print_status("Redis Diagnostics", "Failed", str(e)[:50])
    
    async def _diagnose_integrations(self):
        """Detailed integration diagnostics."""
        try:
            integration_health = await check_integration_health()
            
            for integration in integration_health.integrations:
                status = integration.status.value
                details = ""
                
                if integration.latency_ms:
                    details += f"{integration.latency_ms:.1f}ms"
                
                if integration.error_message:
                    details += f" Error: {integration.error_message[:30]}"
                
                if integration.last_success:
                    time_diff = datetime.utcnow() - integration.last_success
                    details += f" Last success: {time_diff.total_seconds():.0f}s ago"
                
                self.print_status(integration.integration_type.value, status, details)
                
        except Exception as e:
            self.print_status("Integration Diagnostics", "Failed", str(e)[:50])
    
    async def _diagnose_tasks(self):
        """Detailed task system diagnostics."""
        try:
            celery_health = await check_celery_health()
            
            self.print_status("Broker Status", celery_health.broker_status, "")
            self.print_status("Backend Status", celery_health.backend_status, "")
            
            self.print_status("Active Tasks", str(celery_health.total_active_tasks), "")
            self.print_status("Pending Tasks", str(celery_health.total_pending_tasks), "")
            
            for worker in celery_health.workers:
                self.print_status(f"Worker: {worker.name}", worker.status,
                                f"{worker.active_tasks} active")
            
            for queue in celery_health.queues:
                self.print_status(f"Queue: {queue.name}", queue.status,
                                f"{queue.pending_tasks} pending")
                
        except Exception as e:
            self.print_status("Task System Diagnostics", "Failed", str(e)[:50])
    
    async def test_crisis_workflow(self):
        """Test crisis intervention workflow end-to-end."""
        self.print_header("CRISIS WORKFLOW TEST")
        
        try:
            # Test data
            test_scenarios = [
                {
                    "text": "I don't want to live anymore",
                    "expected_severity": "critical",
                    "description": "High-risk suicide ideation"
                },
                {
                    "text": "I've been cutting myself recently",
                    "expected_severity": "high",
                    "description": "Self-harm behavior"
                },
                {
                    "text": "I'm feeling a bit sad today",
                    "expected_severity": "low",
                    "description": "Normal sadness"
                }
            ]
            
            for i, scenario in enumerate(test_scenarios, 1):
                self.print_colored(f"\n📋 Test Scenario {i}: {scenario['description']}", 'blue')
                
                # Step 1: Crisis detection
                classifier = CrisisClassifier()
                start_time = time.time()
                
                assessment = await classifier.assess_crisis_risk(
                    text=scenario['text'],
                    user_id=f"test_user_{i}"
                )
                
                detection_time = (time.time() - start_time) * 1000
                
                self.print_status("Crisis Detection", "Complete",
                                f"Severity: {assessment.severity.value}, {detection_time:.1f}ms")
                
                # Step 2: Protocol selection (if needed)
                if assessment.severity.value in ['high', 'critical']:
                    executor = VeluriaProtocolExecutor()
                    
                    # This would normally trigger intervention protocols
                    self.print_status("Protocol Selection", "Ready",
                                    f"Would trigger intervention for {assessment.severity.value}")
                else:
                    self.print_status("Protocol Selection", "Skipped",
                                    "Low severity - no intervention needed")
                
                # Step 3: Audit logging
                from symbolic.moss.audit_logging import MOSSAuditLogger
                audit_logger = MOSSAuditLogger()
                
                event_id = await audit_logger.log_crisis_assessment(
                    assessment_id=f"test_assessment_{i}",
                    severity=assessment.severity.value,
                    confidence=assessment.confidence,
                    escalation_required=assessment.severity.value in ['high', 'critical'],
                    user_id=f"test_user_{i}",
                    session_id=f"test_session_{i}"
                )
                
                self.print_status("Audit Logging", "Complete", f"Event: {event_id[:8]}...")
                
        except Exception as e:
            self.print_colored(f"❌ Crisis workflow test failed: {e}", 'red')
    
    async def monitor_system(self, duration: int = 60):
        """Real-time system monitoring."""
        self.print_header(f"REAL-TIME MONITORING ({duration}s)")
        
        start_time = time.time()
        iteration = 0
        
        try:
            while time.time() - start_time < duration:
                iteration += 1
                current_time = datetime.now().strftime("%H:%M:%S")
                
                print(f"\n⏰ {current_time} - Monitoring Iteration {iteration}")
                
                # Quick health checks
                checks = []
                
                # Database check
                try:
                    from database.session import get_async_session
                    from sqlalchemy import text
                    
                    check_start = time.time()
                    async with get_async_session() as session:
                        await session.execute(text("SELECT 1"))
                    db_time = (time.time() - check_start) * 1000
                    checks.append(("Database", "OK", f"{db_time:.1f}ms"))
                except Exception as e:
                    checks.append(("Database", "ERROR", str(e)[:30]))
                
                # Redis check
                try:
                    from cache.redis_client import get_redis_client
                    check_start = time.time()
                    redis = await get_redis_client()
                    await redis.ping()
                    redis_time = (time.time() - check_start) * 1000
                    checks.append(("Redis", "OK", f"{redis_time:.1f}ms"))
                except Exception as e:
                    checks.append(("Redis", "ERROR", str(e)[:30]))
                
                # Display results
                for component, status, details in checks:
                    self.print_status(component, status, details)
                
                # Wait for next iteration
                await asyncio.sleep(5)
                
        except KeyboardInterrupt:
            self.print_colored("\n⏹️  Monitoring stopped by user", 'yellow')
    
    def view_logs(self, component: str = None):
        """View recent logs for a component."""
        self.print_header(f"LOGS: {component.upper() if component else 'ALL'}")
        
        # This would implement log viewing functionality
        # For now, show placeholder
        self.print_colored("📋 Log viewing functionality would be implemented here", 'blue')
        self.print_colored("    - Real-time log streaming", 'cyan')
        self.print_colored("    - Log filtering by component/level", 'cyan')
        self.print_colored("    - Log search and analysis", 'cyan')


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Advanced Debug CLI for Emotional Wellness API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/debug_cli.py health              # Full health check
  python scripts/debug_cli.py diagnose moss       # Diagnose MOSS system
  python scripts/debug_cli.py test crisis         # Test crisis workflow
  python scripts/debug_cli.py monitor 30          # Monitor for 30 seconds
        """
    )
    
    parser.add_argument('command', choices=[
        'health', 'diagnose', 'test', 'monitor', 'logs'
    ], help='Command to execute')
    
    parser.add_argument('target', nargs='?', 
                       help='Target component or test type')
    
    parser.add_argument('--duration', type=int, default=60,
                       help='Duration for monitoring (seconds)')
    
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging("development", log_level)
    
    # Create CLI instance
    cli = DebugCLI()
    
    try:
        # Execute command
        if args.command == 'health':
            await cli.health_check()
        elif args.command == 'diagnose':
            await cli.diagnose_component(args.target)
        elif args.command == 'test':
            if args.target == 'crisis':
                await cli.test_crisis_workflow()
            else:
                cli.print_colored("Available tests: crisis", 'yellow')
        elif args.command == 'monitor':
            await cli.monitor_system(args.duration)
        elif args.command == 'logs':
            cli.view_logs(args.target)
    
    except KeyboardInterrupt:
        cli.print_colored("\n👋 Debug session interrupted by user", 'yellow')
    except Exception as e:
        cli.print_colored(f"\n❌ Error: {e}", 'red')
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 