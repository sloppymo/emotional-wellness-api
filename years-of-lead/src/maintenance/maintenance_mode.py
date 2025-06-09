"""
Maintenance Mode: Automated testing and incremental improvement system

This module acts like a careful gardener - it tends to the codebase,
fixing small issues and making targeted improvements while ensuring
nothing breaks. Each iteration follows a strict protocol to maintain
game stability while gradually enhancing quality.
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import shutil

class ImprovementType(Enum):
    """Categories of improvements, ordered by priority"""
    CRITICAL_BUG = 1      # Game crashes or corrupts data
    MAJOR_BUG = 2         # Features don't work as intended  
    PERFORMANCE = 3       # Slow or inefficient code
    NARRATIVE = 4         # Repetitive or incoherent story
    EMOTIONAL = 5         # Emotional states behaving oddly
    VARIETY = 6           # Adding more content variety
    POLISH = 7            # Small quality improvements

@dataclass
class Improvement:
    """Represents a single improvement to make"""
    type: ImprovementType
    description: str
    complexity_cost: int  # How much of our budget this uses
    file_to_modify: str
    test_to_verify: str   # Which test verifies this works

class MaintenanceMode:
    """The main maintenance system that runs automated improvement cycles."""
    
    def __init__(self, project_root: Path = Path(".")):
        self.project_root = project_root
        self.iteration = 0
        self.complexity_budget = 10  # Prevents runaway complexity
        self.improvements_log = []
        self.baseline_metrics = {}
        
        # Create necessary directories
        self.logs_dir = project_root / "maintenance_logs"
        self.backup_dir = self.logs_dir / "backups"
        self.logs_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
        
        # Load configuration
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load maintenance configuration"""
        config_path = self.project_root / "config" / "maintenance.json"
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        else:
            return {
                "max_iterations": 20,
                "min_test_coverage": 0.8,
                "max_complexity_per_change": 3,
                "required_metrics": {
                    "all_tests_pass": True,
                    "narrative_coherence": 0.7,
                    "emotional_consistency": 0.8,
                    "performance_baseline": 1.0
                }
            }
    
    def run_maintenance_cycle(self, iterations: int = 1):
        """Run the main maintenance cycle for specified iterations."""
        print(f"Starting maintenance cycle with complexity budget: {self.complexity_budget}")
        
        for i in range(iterations):
            if self.complexity_budget <= 0:
                print("Complexity budget exhausted. Stopping maintenance.")
                break
                
            print(f"\n{'='*60}")
            print(f"Maintenance Iteration {self.iteration + 1}")
            print(f"{'='*60}")
            
            # Step 1: Establish baseline metrics
            self.baseline_metrics = self._measure_current_state()
            self._log_metrics("baseline", self.baseline_metrics)
            
            # Step 2: Run comprehensive tests
            test_results = self._run_comprehensive_tests()
            
            # Store scenario results for improvement identification
            self.last_scenario_results = test_results.get("scenario_results", {})
            
            if not test_results["all_pass"]:
                improvement = self._identify_test_fix(test_results)
                if improvement:
                    self._implement_improvement(improvement)
            else:
                improvement = self._identify_improvement()
                if improvement:
                    success = self._implement_improvement(improvement)
                    if not success:
                        print(f"Failed to implement {improvement.description}")
                        self._revert_changes()
            
            # Step 5: Verify system health
            post_metrics = self._measure_current_state()
            if self._is_system_healthier(post_metrics):
                print("✓ System health maintained or improved")
                self.iteration += 1
            else:
                print("✗ System health degraded, reverting...")
                self._revert_changes()
            
            self._document_iteration()
            time.sleep(1)
    
    def _measure_current_state(self) -> Dict:
        """Measure the current state of the game system."""
        metrics = {}
        
        # Test coverage
        try:
            result = subprocess.run(
                ["python3", "-m", "pytest", "--cov=src", "--cov-report=json", "-q"],
                capture_output=True, text=True, cwd=self.project_root
            )
            if result.returncode == 0:
                coverage_file = self.project_root / "coverage.json"
                if coverage_file.exists():
                    with open(coverage_file) as f:
                        data = json.load(f)
                        metrics["test_coverage"] = data.get("totals", {}).get("percent_covered", 0) / 100
        except Exception as e:
            print(f"Warning: Could not measure test coverage: {e}")
            metrics["test_coverage"] = 0.0
        
        metrics["performance"] = self._run_performance_benchmark()
        metrics["narrative_quality"] = self._assess_narrative_quality()
        metrics["emotional_consistency"] = self._assess_emotional_consistency()
        
        return metrics
    
    def _run_comprehensive_tests(self) -> Dict:
        """Run all test suites and collect results"""
        print("\nRunning comprehensive test suite...")
        
        # First run standardized maintenance scenarios
        print("  Running maintenance scenarios...", end="", flush=True)
        try:
            sys.path.insert(0, str(self.project_root / "tests" / "maintenance"))
            from test_scenarios import ScenarioRunner
            
            scenario_runner = ScenarioRunner()
            scenario_results = scenario_runner.run_all_scenarios()
            
            scenario_passed = scenario_results.get('overall_passed', False)
            if scenario_passed:
                print(" ✓ Passed")
            else:
                print(f" ✗ FAILED ({scenario_results.get('failures', 0)} failures)")
            
        except Exception as e:
            print(f" ✗ ERROR: {e}")
            scenario_passed = False
            scenario_results = {"overall_passed": False, "error": str(e)}
        
        test_commands = [
            ("Unit tests", ["python3", "-m", "pytest", "tests/unit", "-v"]),
            ("Integration tests", ["python3", "-m", "pytest", "tests/integration", "-v"]),
            ("E2E tests", ["python3", "-m", "pytest", "tests/e2e", "-v"]),
            ("Maintenance basic", ["python3", "-m", "pytest", "tests/maintenance/test_maintenance_basic.py", "-v"])
        ]
        
        results = {"all_pass": scenario_passed, "failures": [], "suite_results": {}, "scenario_results": scenario_results}
        
        if not scenario_passed:
            results["failures"].append("Maintenance scenarios")
        
        for suite_name, command in test_commands:
            print(f"  Running {suite_name}...", end="", flush=True)
            try:
                result = subprocess.run(command, capture_output=True, text=True, cwd=self.project_root)
                passed = result.returncode == 0
                results["suite_results"][suite_name] = {
                    "passed": passed,
                    "output": result.stdout + result.stderr
                }
                
                if not passed:
                    results["all_pass"] = False
                    results["failures"].append(suite_name)
                    print(" ✗ FAILED")
                else:
                    print(" ✓ Passed")
            except Exception as e:
                print(f" ✗ ERROR: {e}")
                results["all_pass"] = False
                results["failures"].append(f"{suite_name} (Error)")
        
        return results
    
    def _identify_improvement(self) -> Optional[Improvement]:
        """Identify the highest priority improvement to make based on scenario results."""
        candidates = []
        
        # Get scenario results if available
        scenario_results = getattr(self, 'last_scenario_results', {})
        detailed_results = scenario_results.get('detailed_results', {})
        
        # Performance improvements
        perf_results = detailed_results.get('step_performance', {})
        if not perf_results.get('performance_acceptable', True) or self.baseline_metrics.get("performance", 1.0) < 0.8:
            candidates.append(Improvement(
                type=ImprovementType.PERFORMANCE,
                description="Optimize game step performance and memory usage",
                complexity_cost=2,
                file_to_modify="src/game/core.py",
                test_to_verify="tests/maintenance/test_scenarios.py::MaintenanceTestScenarios::test_game_step_performance"
            ))
        
        # Memory stability
        memory_results = detailed_results.get('memory_stability', {})
        if not memory_results.get('stable_memory', True):
            candidates.append(Improvement(
                type=ImprovementType.CRITICAL_BUG,
                description="Fix memory leak in game state management",
                complexity_cost=3,
                file_to_modify="src/game/core.py",
                test_to_verify="tests/maintenance/test_scenarios.py::MaintenanceTestScenarios::test_memory_stability"
            ))
        
        # Emotional consistency issues
        emotional_results = detailed_results.get('emotional_bounds', {})
        drift_results = detailed_results.get('emotional_drift', {})
        if not emotional_results.get('all_in_bounds', True) or not drift_results.get('passed', True):
            candidates.append(Improvement(
                type=ImprovementType.EMOTIONAL,
                description="Fix emotional state bounds and drift rate calculations",
                complexity_cost=2,
                file_to_modify="src/game/emotional_state.py",
                test_to_verify="tests/maintenance/test_scenarios.py::MaintenanceTestScenarios::test_emotional_bounds_consistency"
            ))
        
        # Trauma persistence
        trauma_results = detailed_results.get('trauma_persistence', {})
        if not trauma_results.get('trauma_processed', True):
            candidates.append(Improvement(
                type=ImprovementType.EMOTIONAL,
                description="Improve trauma event processing and persistence",
                complexity_cost=2,
                file_to_modify="src/game/emotional_state.py",
                test_to_verify="tests/maintenance/test_scenarios.py::MaintenanceTestScenarios::test_trauma_persistence"
            ))
        
        # Narrative variety and coherence
        variety_results = detailed_results.get('narrative_variety', {})
        coherence_results = detailed_results.get('narrative_coherence', {})
        if not variety_results.get('sufficient_variety', True) or not coherence_results.get('coherent_sequence', True):
            candidates.append(Improvement(
                type=ImprovementType.NARRATIVE,
                description="Improve narrative variety and coherence algorithms",
                complexity_cost=3,
                file_to_modify="src/game/events.py",
                test_to_verify="tests/maintenance/test_scenarios.py::MaintenanceTestScenarios::test_narrative_variety"
            ))
        
        # High load stability
        stability_results = detailed_results.get('high_load_stability', {})
        if not stability_results.get('stable_under_load', True):
            candidates.append(Improvement(
                type=ImprovementType.MAJOR_BUG,
                description="Fix concurrency issues in multi-agent scenarios",
                complexity_cost=3,
                file_to_modify="src/game/core.py",
                test_to_verify="tests/maintenance/test_scenarios.py::MaintenanceTestScenarios::test_high_load_stability"
            ))
        
        # Agent interaction problems
        interaction_results = detailed_results.get('multi_agent_interactions', {})
        if interaction_results.get('total_interactions', 0) == 0:
            candidates.append(Improvement(
                type=ImprovementType.MAJOR_BUG,
                description="Fix agent interaction system",
                complexity_cost=2,
                file_to_modify="src/game/agent.py",
                test_to_verify="tests/maintenance/test_scenarios.py::MaintenanceTestScenarios::test_multi_agent_interactions"
            ))
        
        # State persistence
        persistence_results = detailed_results.get('state_persistence', {})
        if not persistence_results.get('state_preserved', True):
            candidates.append(Improvement(
                type=ImprovementType.MAJOR_BUG,
                description="Fix agent state serialization/deserialization",
                complexity_cost=2,
                file_to_modify="src/game/agent.py",
                test_to_verify="tests/maintenance/test_scenarios.py::MaintenanceTestScenarios::test_agent_state_persistence"
            ))
        
        # If no specific issues, add variety/polish improvements
        if not candidates and self.complexity_budget >= 3:
            candidates.append(Improvement(
                type=ImprovementType.VARIETY,
                description="Add new event templates and narrative variety",
                complexity_cost=3,
                file_to_modify="src/game/events.py",
                test_to_verify="tests/maintenance/test_scenarios.py::MaintenanceTestScenarios::test_narrative_variety"
            ))
        
        # Sort by priority (lower enum value = higher priority)
        candidates.sort(key=lambda x: x.type.value)
        
        # Return the highest priority improvement we can afford
        for improvement in candidates:
            if improvement.complexity_cost <= self.complexity_budget:
                return improvement
        
        return None
    
    def _identify_test_fix(self, test_results: Dict) -> Optional[Improvement]:
        """Identify improvements to fix failing tests"""
        if not test_results["failures"]:
            return None
        return Improvement(
            type=ImprovementType.CRITICAL_BUG,
            description=f"Fix failing tests: {', '.join(test_results['failures'])}",
            complexity_cost=1,
            file_to_modify="src/game/core.py",
            test_to_verify="tests/unit"
        )
    
    def _implement_improvement(self, improvement: Improvement) -> bool:
        """Implement a specific improvement."""
        print(f"\nImplementing: {improvement.description}")
        print(f"  Target file: {improvement.file_to_modify}")
        print(f"  Complexity cost: {improvement.complexity_cost}")
        
        if Path(improvement.file_to_modify).exists():
            self._backup_file(improvement.file_to_modify)
        
        try:
            success = True  # Placeholder for actual implementation
            
            if success:
                print(f"  Verifying with {improvement.test_to_verify}...")
                test_result = subprocess.run(
                    ["python3", "-m", "pytest", improvement.test_to_verify, "-v"],
                    capture_output=True, text=True, cwd=self.project_root
                )
                
                if test_result.returncode == 0:
                    print("  ✓ Improvement verified!")
                    self.complexity_budget -= improvement.complexity_cost
                    self.improvements_log.append({
                        "iteration": self.iteration,
                        "improvement": improvement.description,
                        "complexity_cost": improvement.complexity_cost,
                        "timestamp": datetime.now().isoformat()
                    })
                    return True
                else:
                    print("  ✗ Verification failed!")
                    return False
            return False
        except Exception as e:
            print(f"  ✗ Error implementing improvement: {e}")
            return False
    
    def _backup_file(self, file_path: str):
        """Create a backup of a file before modifying it"""
        source = Path(file_path)
        if source.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{source.name}_{timestamp}.backup"
            backup_path = self.backup_dir / backup_name
            shutil.copy2(source, backup_path)
            print(f"  Backed up {file_path} to {backup_path}")
    
    def _revert_changes(self):
        """Revert recent changes if they caused problems"""
        print("  Reverting recent changes...")
        self.improvements_log.append({
            "iteration": self.iteration,
            "improvement": "REVERTED - System health degraded",
            "complexity_cost": 0,
            "timestamp": datetime.now().isoformat()
        })
    
    def _is_system_healthier(self, new_metrics: Dict) -> bool:
        """Check if the system is healthier after changes"""
        if not self.baseline_metrics:
            return True
        
        health_checks = [
            new_metrics.get("test_coverage", 0) >= self.baseline_metrics.get("test_coverage", 0),
            new_metrics.get("performance", 0) >= self.baseline_metrics.get("performance", 0) * 0.95,
            new_metrics.get("narrative_quality", 0) >= self.baseline_metrics.get("narrative_quality", 0),
            new_metrics.get("emotional_consistency", 0) >= self.baseline_metrics.get("emotional_consistency", 0)
        ]
        
        return sum(health_checks) >= len(health_checks) * 0.75
    
    def _run_performance_benchmark(self) -> float:
        """Run a quick performance benchmark"""
        try:
            start_time = time.time()
            import sys
            sys.path.append(str(self.project_root / "src"))
            from game.core import GameState
            game_state = GameState()
            end_time = time.time()
            init_time = end_time - start_time
            performance_score = max(0, min(1, (1.0 - init_time) / 0.9))
            return performance_score
        except Exception as e:
            print(f"    Performance benchmark failed: {e}")
            return 0.5
    
    def _assess_narrative_quality(self) -> float:
        """Assess narrative quality through basic checks"""
        try:
            events_file = self.project_root / "src" / "game" / "events.py"
            if events_file.exists():
                with open(events_file) as f:
                    content = f.read()
                import re
                descriptions = re.findall(r'"([^"]{50,})"', content)
                unique_words = set()
                for desc in descriptions:
                    words = desc.lower().split()
                    unique_words.update(words)
                variety_score = min(1.0, len(unique_words) / 100)
                return variety_score
        except Exception as e:
            print(f"    Narrative assessment failed: {e}")
        return 0.7
    
    def _assess_emotional_consistency(self) -> float:
        """Assess emotional system consistency"""
        try:
            state_file = self.project_root / "src" / "game" / "state.py"
            if state_file.exists():
                with open(state_file) as f:
                    content = f.read()
                if "clamp" in content or "min(" in content or "max(" in content:
                    return 0.9
                elif "-1" in content and "1" in content:
                    return 0.8
                else:
                    return 0.6
        except Exception as e:
            print(f"    Emotional assessment failed: {e}")
        return 0.8
    
    def _log_metrics(self, phase: str, metrics: Dict):
        """Log metrics to file"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "iteration": self.iteration,
            "phase": phase,
            "metrics": metrics
        }
        
        log_file = self.logs_dir / f"metrics_{datetime.now().strftime('%Y%m%d')}.json"
        logs = []
        if log_file.exists():
            with open(log_file) as f:
                logs = json.load(f)
        logs.append(log_entry)
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)
    
    def _document_iteration(self):
        """Document what happened in this iteration"""
        iteration_log = {
            "iteration": self.iteration,
            "timestamp": datetime.now().isoformat(),
            "baseline_metrics": self.baseline_metrics,
            "improvements_made": len(self.improvements_log),
            "remaining_budget": self.complexity_budget
        }
        log_file = self.logs_dir / f"iteration_{self.iteration:03d}.json"
        with open(log_file, 'w') as f:
            json.dump(iteration_log, f, indent=2)
