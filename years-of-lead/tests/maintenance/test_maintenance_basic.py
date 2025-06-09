"""
Basic tests for the maintenance system.

These tests ensure the maintenance infrastructure works correctly.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from maintenance.maintenance_mode import MaintenanceMode, ImprovementType, Improvement
from maintenance.metrics import GameHealthMetrics

class TestMaintenanceMode:
    """Test the core maintenance functionality"""
    
    def test_initialization(self):
        """Test maintenance mode initializes correctly"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            maintenance = MaintenanceMode(project_root)
            
            assert maintenance.project_root == project_root
            assert maintenance.iteration == 0
            assert maintenance.complexity_budget == 10
            assert isinstance(maintenance.improvements_log, list)
            assert isinstance(maintenance.baseline_metrics, dict)
    
    def test_config_loading(self):
        """Test configuration loading with default values"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            maintenance = MaintenanceMode(project_root)
            
            config = maintenance.config
            assert "max_iterations" in config
            assert "min_test_coverage" in config
            assert "required_metrics" in config
            assert config["max_iterations"] == 20
    
    def test_custom_config_loading(self):
        """Test loading custom configuration"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            config_dir = project_root / "config"
            config_dir.mkdir()
            
            custom_config = {
                "max_iterations": 5,
                "min_test_coverage": 0.9,
                "max_complexity_per_change": 2
            }
            
            with open(config_dir / "maintenance.json", 'w') as f:
                json.dump(custom_config, f)
            
            maintenance = MaintenanceMode(project_root)
            assert maintenance.config["max_iterations"] == 5
            assert maintenance.config["min_test_coverage"] == 0.9
    
    def test_identify_improvement_performance(self):
        """Test performance improvement identification"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            maintenance = MaintenanceMode(project_root)
            
            # Set low performance baseline
            maintenance.baseline_metrics = {"performance": 0.5}
            
            improvement = maintenance._identify_improvement()
            
            assert improvement is not None
            assert improvement.type == ImprovementType.PERFORMANCE
            assert "performance" in improvement.description.lower()
    
    def test_identify_improvement_narrative(self):
        """Test narrative improvement identification"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            maintenance = MaintenanceMode(project_root)
            
            # Set low narrative quality baseline
            maintenance.baseline_metrics = {"narrative_quality": 0.5}
            
            improvement = maintenance._identify_improvement()
            
            assert improvement is not None
            assert improvement.type == ImprovementType.NARRATIVE
            assert "narrative" in improvement.description.lower()
    
    def test_improvement_priority_ordering(self):
        """Test that improvements are prioritized correctly"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            maintenance = MaintenanceMode(project_root)
            
            # Set multiple issues with different priorities
            maintenance.baseline_metrics = {
                "performance": 0.5,           # Priority 3
                "narrative_quality": 0.5,     # Priority 4  
                "emotional_consistency": 0.5  # Priority 5
            }
            
            improvement = maintenance._identify_improvement()
            
            # Should pick performance first (lowest priority number)
            assert improvement.type == ImprovementType.PERFORMANCE
    
    def test_complexity_budget_enforcement(self):
        """Test that complexity budget is enforced"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            maintenance = MaintenanceMode(project_root)
            maintenance.complexity_budget = 1  # Very low budget
            
            # Set up scenario that would suggest high-cost improvement
            maintenance.baseline_metrics = {"narrative_quality": 0.5}
            
            improvement = maintenance._identify_improvement()
            
            # Should either find low-cost improvement or none at all
            if improvement:
                assert improvement.complexity_cost <= 1
    
    def test_system_health_comparison(self):
        """Test system health comparison logic"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            maintenance = MaintenanceMode(project_root)
            
            baseline = {
                "test_coverage": 0.8,
                "performance": 0.7,
                "narrative_quality": 0.6,
                "emotional_consistency": 0.8
            }
            maintenance.baseline_metrics = baseline
            
            # Test improved metrics
            improved = {
                "test_coverage": 0.9,
                "performance": 0.8,
                "narrative_quality": 0.7,
                "emotional_consistency": 0.9
            }
            
            assert maintenance._is_system_healthier(improved)
            
            # Test degraded metrics
            degraded = {
                "test_coverage": 0.5,
                "performance": 0.4,
                "narrative_quality": 0.3,
                "emotional_consistency": 0.5
            }
            
            assert not maintenance._is_system_healthier(degraded)


class TestGameHealthMetrics:
    """Test the metrics collection system"""
    
    def test_initialization(self):
        """Test metrics collector initializes correctly"""
        metrics = GameHealthMetrics()
        
        assert metrics.game is None
        assert isinstance(metrics.metrics_history, list)
        assert isinstance(metrics.performance_samples, list)
    
    def test_performance_measurement_no_game(self):
        """Test performance measurement without game instance"""
        metrics = GameHealthMetrics()
        
        performance = metrics.measure_performance()
        
        assert isinstance(performance, float)
        assert 0.0 <= performance <= 1.0
    
    def test_narrative_coherence_no_game(self):
        """Test narrative coherence measurement without game instance"""
        metrics = GameHealthMetrics()
        
        coherence = metrics.measure_narrative_coherence()
        
        assert isinstance(coherence, float)
        assert 0.0 <= coherence <= 1.0
        assert coherence == 0.7  # Default value
    
    def test_emotional_consistency_no_game(self):
        """Test emotional consistency measurement without game instance"""
        metrics = GameHealthMetrics()
        
        consistency = metrics.measure_emotional_consistency()
        
        assert isinstance(consistency, float)
        assert 0.0 <= consistency <= 1.0
        assert consistency == 0.8  # Default value
    
    def test_comprehensive_metrics_collection(self):
        """Test comprehensive metrics collection"""
        metrics = GameHealthMetrics()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            collected_metrics = metrics.collect_comprehensive_metrics(project_root)
            
            required_keys = [
                "timestamp", "narrative_coherence", "emotional_consistency",
                "performance", "performance_trend", "overall_health"
            ]
            
            for key in required_keys:
                assert key in collected_metrics
            
            # Check value ranges
            assert 0.0 <= collected_metrics["overall_health"] <= 1.0
            assert isinstance(collected_metrics["performance_trend"], str)
    
    def test_performance_trend_tracking(self):
        """Test performance trend analysis"""
        metrics = GameHealthMetrics()
        
        # Add some performance samples
        metrics.performance_samples = [0.5, 0.6, 0.7, 0.8, 0.9]
        
        trend = metrics.get_performance_trend()
        assert trend in ["improving", "degrading", "stable", "insufficient_data"]
    
    def test_health_summary_no_data(self):
        """Test health summary with no historical data"""
        metrics = GameHealthMetrics()
        
        summary = metrics.get_health_summary()
        
        assert summary["status"] == "no_data"
        assert "recommendations" in summary
    
    def test_health_summary_with_data(self):
        """Test health summary with historical data"""
        metrics = GameHealthMetrics()
        
        # Add some historical data
        for i in range(5):
            fake_metrics = {
                "overall_health": 0.7 + i * 0.05,
                "performance": 0.6 + i * 0.1,
                "narrative_coherence": 0.8
            }
            metrics.metrics_history.append(fake_metrics)
        
        summary = metrics.get_health_summary()
        
        assert summary["status"] in ["improving", "stable", "declining"]
        assert "overall_health" in summary
        assert isinstance(summary["recommendations"], list)
    
    def test_metrics_export(self):
        """Test metrics export functionality"""
        metrics = GameHealthMetrics()
        
        # Add some data
        metrics.metrics_history = [
            {"overall_health": 0.8, "performance": 0.7},
            {"overall_health": 0.9, "performance": 0.8}
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = Path(temp_dir) / "test_export.json"
            
            metrics.export_metrics(export_path)
            
            assert export_path.exists()
            
            with open(export_path) as f:
                data = json.load(f)
            
            assert "export_timestamp" in data
            assert "metrics_count" in data
            assert "health_summary" in data
            assert "metrics_history" in data
            assert data["metrics_count"] == 2


class TestImprovementTypes:
    """Test improvement type definitions"""
    
    def test_improvement_priority_order(self):
        """Test that improvement types have correct priority order"""
        types = list(ImprovementType)
        values = [t.value for t in types]
        
        # Values should be in ascending order (lower value = higher priority)
        assert values == sorted(values)
        
        # Critical bugs should have highest priority (lowest value)
        assert ImprovementType.CRITICAL_BUG.value == 1
        assert ImprovementType.POLISH.value == 7
    
    def test_improvement_dataclass(self):
        """Test improvement data structure"""
        improvement = Improvement(
            type=ImprovementType.PERFORMANCE,
            description="Test improvement",
            complexity_cost=2,
            file_to_modify="test.py",
            test_to_verify="test_performance.py"
        )
        
        assert improvement.type == ImprovementType.PERFORMANCE
        assert improvement.complexity_cost == 2
        assert "test" in improvement.description.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 