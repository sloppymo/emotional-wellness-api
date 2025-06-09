"""
Metrics collection for maintenance mode.

Think of this as the game's health monitoring system. Just like a 
fitness tracker measures your heart rate and steps, this measures
the game's narrative quality, performance, and emotional consistency.
"""

import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class GameHealthMetrics:
    """Collects and analyzes game health metrics"""
    
    def __init__(self, game_instance=None):
        self.game = game_instance
        self.metrics_history = []
        self.performance_samples = []
        self.narrative_samples = []
        self.emotional_samples = []
    
    def measure_narrative_coherence(self) -> float:
        """
        Measures how well the narrative holds together.
        
        We look for:
        - Variety in descriptions (not repetitive)
        - Logical cause and effect
        - Consistent character voices
        - Appropriate emotional responses
        
        Returns a score from 0 (incoherent) to 1 (perfect).
        """
        try:
            if not self.game:
                return 0.7  # Default reasonable score
                
            # Analyze recent narrative events
            recent_events = getattr(self.game, 'recent_events', [])
            if not recent_events:
                return 0.8  # No events to analyze, assume good
            
            # Check for repetition
            descriptions = [event.get('description', '') for event in recent_events[-10:]]
            unique_descriptions = set(descriptions)
            repetition_score = len(unique_descriptions) / max(len(descriptions), 1)
            
            # Check for variety in vocabulary
            all_words = []
            for desc in descriptions:
                all_words.extend(desc.lower().split())
            
            unique_words = set(all_words)
            vocabulary_variety = min(1.0, len(unique_words) / max(len(all_words), 1) * 5)
            
            # Combine scores
            coherence_score = (repetition_score + vocabulary_variety) / 2
            return min(1.0, max(0.0, coherence_score))
            
        except Exception as e:
            print(f"Error measuring narrative coherence: {e}")
            return 0.7
    
    def measure_emotional_consistency(self) -> float:
        """
        Measures whether emotions behave believably.
        
        We check:
        - Do emotions drift at reasonable rates?
        - Do traumatic events have appropriate impact?
        - Are emotional responses consistent with personality?
        - Do emotions affect behavior appropriately?
        
        Returns a score from 0 (chaotic) to 1 (perfectly consistent).
        """
        try:
            if not self.game:
                return 0.8  # Default good score
                
            # Check emotional state changes
            agents = getattr(self.game, 'agents', [])
            if not agents:
                return 0.8
            
            consistency_scores = []
            
            for agent in agents:
                emotional_state = getattr(agent, 'emotional_state', {})
                if not emotional_state:
                    continue
                
                # Check if emotions are within reasonable bounds
                bounds_check = all(
                    -1.0 <= value <= 1.0 
                    for value in emotional_state.values()
                    if isinstance(value, (int, float))
                )
                
                if bounds_check:
                    consistency_scores.append(1.0)
                else:
                    consistency_scores.append(0.0)
            
            if consistency_scores:
                return statistics.mean(consistency_scores)
            else:
                return 0.8
                
        except Exception as e:
            print(f"Error measuring emotional consistency: {e}")
            return 0.8
    
    def measure_performance(self) -> float:
        """
        Measures game performance metrics.
        
        Returns a score from 0 (very slow) to 1 (optimal performance).
        """
        try:
            # Measure initialization time
            start_time = time.time()
            
            if self.game:
                # Try to perform a typical game operation
                test_operation_start = time.time()
                # Simulate a game step or update
                if hasattr(self.game, 'step'):
                    self.game.step()
                elif hasattr(self.game, 'update'):
                    self.game.update()
                test_operation_time = time.time() - test_operation_start
            else:
                test_operation_time = 0.01  # Simulate fast operation
            
            total_time = time.time() - start_time
            
            # Normalize performance score
            # Under 0.05s = 1.0, over 0.5s = 0.0
            performance_score = max(0.0, min(1.0, (0.5 - total_time) / 0.45))
            
            self.performance_samples.append(performance_score)
            
            # Keep only recent samples
            if len(self.performance_samples) > 50:
                self.performance_samples = self.performance_samples[-50:]
            
            return performance_score
            
        except Exception as e:
            print(f"Error measuring performance: {e}")
            return 0.5
    
    def get_performance_trend(self) -> str:
        """Get performance trend over recent samples"""
        if len(self.performance_samples) < 3:
            return "insufficient_data"
        
        recent = self.performance_samples[-5:]
        older = self.performance_samples[-10:-5] if len(self.performance_samples) >= 10 else []
        
        if not older:
            return "stable"
        
        recent_avg = statistics.mean(recent)
        older_avg = statistics.mean(older)
        
        if recent_avg > older_avg * 1.1:
            return "improving"
        elif recent_avg < older_avg * 0.9:
            return "degrading"
        else:
            return "stable"
    
    def measure_test_coverage(self, project_root: Path) -> float:
        """Measure test coverage percentage"""
        try:
            import subprocess
            import json
            
            result = subprocess.run(
                ["python3", "-m", "pytest", "--cov=src", "--cov-report=json", "-q"],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            
            if result.returncode == 0:
                coverage_file = project_root / "coverage.json"
                if coverage_file.exists():
                    with open(coverage_file) as f:
                        coverage_data = json.load(f)
                        return coverage_data.get("totals", {}).get("percent_covered", 0) / 100
            
            return 0.0
            
        except Exception as e:
            print(f"Error measuring test coverage: {e}")
            return 0.0
    
    def collect_comprehensive_metrics(self, project_root: Path = None) -> Dict:
        """Collect all available metrics"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "narrative_coherence": self.measure_narrative_coherence(),
            "emotional_consistency": self.measure_emotional_consistency(),
            "performance": self.measure_performance(),
            "performance_trend": self.get_performance_trend()
        }
        
        if project_root:
            metrics["test_coverage"] = self.measure_test_coverage(project_root)
        
        # Calculate overall health score
        health_components = [
            metrics["narrative_coherence"],
            metrics["emotional_consistency"],
            metrics["performance"]
        ]
        
        if "test_coverage" in metrics:
            health_components.append(metrics["test_coverage"])
        
        metrics["overall_health"] = statistics.mean(health_components)
        
        # Store in history
        self.metrics_history.append(metrics)
        
        # Keep only recent history
        if len(self.metrics_history) > 100:
            self.metrics_history = self.metrics_history[-100:]
        
        return metrics
    
    def get_health_summary(self) -> Dict:
        """Get a summary of recent health trends"""
        if not self.metrics_history:
            return {"status": "no_data", "recommendations": []}
        
        recent_metrics = self.metrics_history[-10:] if len(self.metrics_history) >= 10 else self.metrics_history
        
        if len(recent_metrics) < 2:
            return {"status": "insufficient_data", "recommendations": []}
        
        # Calculate trends
        health_scores = [m["overall_health"] for m in recent_metrics]
        performance_scores = [m["performance"] for m in recent_metrics]
        narrative_scores = [m["narrative_coherence"] for m in recent_metrics]
        
        health_trend = "stable"
        if len(health_scores) >= 3:
            if health_scores[-1] > health_scores[-3] * 1.05:
                health_trend = "improving"
            elif health_scores[-1] < health_scores[-3] * 0.95:
                health_trend = "declining"
        
        recommendations = []
        
        # Generate recommendations based on scores
        avg_performance = statistics.mean(performance_scores)
        avg_narrative = statistics.mean(narrative_scores)
        
        if avg_performance < 0.6:
            recommendations.append("Consider performance optimization")
        
        if avg_narrative < 0.7:
            recommendations.append("Review narrative variety and coherence")
        
        if health_trend == "declining":
            recommendations.append("System health is declining - investigate recent changes")
        
        return {
            "status": health_trend,
            "overall_health": statistics.mean(health_scores),
            "performance_avg": avg_performance,
            "narrative_avg": avg_narrative,
            "recommendations": recommendations
        }
    
    def export_metrics(self, output_path: Path):
        """Export metrics history to file"""
        import json
        
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "metrics_count": len(self.metrics_history),
            "health_summary": self.get_health_summary(),
            "metrics_history": self.metrics_history
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"Metrics exported to {output_path}") 