# Years of Lead - Automated Maintenance System

## Overview

The automated maintenance system for Years of Lead acts like a careful gardener, tending to your codebase by making small, targeted improvements while ensuring nothing breaks. This system implements several important software engineering concepts:

- **Regression testing** - Making sure old features still work
- **Metrics-driven development** - Measuring quality objectively  
- **Complexity budgeting** - Preventing feature creep
- **Automated refactoring** - Improving code systematically

## Quick Start

### Basic Health Check
```bash
# Check current system health
python run_maintenance.py --health-check
```

### Run Maintenance
```bash
# Run 1 maintenance iteration
python run_maintenance.py

# Run 5 iterations with higher complexity budget
python run_maintenance.py --iterations 5 --complexity-budget 15

# Export current metrics to file
python run_maintenance.py --export-metrics
```

## How It Works

### The Maintenance Cycle

Each maintenance iteration follows these steps:

1. **📋 Baseline Assessment** - Measure current system health
2. **🧪 Comprehensive Testing** - Run all test suites
3. **🔍 Issue Identification** - Find the highest-priority improvement opportunity
4. **🛠️ Implementation** - Make one small, careful change
5. **✅ Verification** - Ensure the change helped and didn't break anything
6. **📝 Documentation** - Record what was done

### Improvement Priorities

The system prioritizes improvements by urgency:

1. **🔴 Critical Bug** - Game crashes or corrupts data
2. **🟡 Major Bug** - Features don't work as intended
3. **⚡ Performance** - Slow or inefficient code
4. **📚 Narrative** - Repetitive or incoherent story
5. **❤️ Emotional** - Emotional states behaving oddly
6. **🎨 Variety** - Adding more content variety
7. **✨ Polish** - Small quality improvements

### Complexity Budget

The maintenance system uses a "complexity budget" to prevent endless tinkering:

- Each improvement has a complexity cost (1-3 points typically)
- Budget starts at 10 points per session
- When budget is exhausted, maintenance stops
- This ensures focused, high-impact changes

## System Health Metrics

### Core Metrics

| Metric | Description | Good Score |
|--------|-------------|------------|
| **Test Coverage** | Percentage of code covered by tests | > 80% |
| **Performance** | Game initialization and operation speed | > 80% |
| **Narrative Quality** | Variety and coherence of story content | > 70% |
| **Emotional Consistency** | Believable emotional state behavior | > 80% |

### Health Status Indicators

- 🟢 **Excellent** (80%+) - System is healthy
- 🟡 **Good** (60-80%) - System is stable  
- 🟠 **Needs Attention** (40-60%) - Issues detected
- 🔴 **Critical** (<40%) - Immediate attention required

## Configuration

### Main Configuration File

Edit `config/maintenance.json` to customize behavior:

```json
{
  "max_iterations": 20,
  "min_test_coverage": 0.8,
  "max_complexity_per_change": 3,
  "required_metrics": {
    "all_tests_pass": true,
    "narrative_coherence": 0.7,
    "emotional_consistency": 0.8,
    "performance_baseline": 1.0
  }
}
```

### Key Settings

- **max_iterations**: Maximum iterations per maintenance session
- **min_test_coverage**: Minimum acceptable test coverage
- **max_complexity_per_change**: Maximum complexity cost per improvement
- **required_metrics**: Target values for each health metric

## Command Line Options

### Basic Usage
```bash
python run_maintenance.py [OPTIONS]
```

### Available Options

| Option | Description | Example |
|--------|-------------|---------|
| `-i, --iterations N` | Run N maintenance iterations | `--iterations 3` |
| `--health-check` | Only check health, make no changes | `--health-check` |
| `--export-metrics` | Export metrics to timestamped file | `--export-metrics` |
| `--complexity-budget N` | Set complexity budget | `--complexity-budget 15` |
| `--verbose` | Enable detailed output | `--verbose` |

## Understanding the Output

### Health Check Output
```
📊 System Health Report - 2024-01-15 14:30:22
----------------------------------------
Overall Health: 🟢 EXCELLENT (0.85)

📋 Test Coverage     🟢 0.82
⚡ Performance       🟡 0.75
📚 Narrative Quality 🟢 0.88
❤️ Emotional Consistency 🟢 0.95

💡 Recommendations:
   • Consider performance optimization
```

### Maintenance Summary
```
📈 Maintenance Summary:
========================================
   Iterations completed: 3
   Remaining complexity budget: 4
   Improvements made: 2
   Health change: 📈 +0.123 (IMPROVED)

🔧 Improvements Applied:
   ✅ Optimize slow game loop operations (cost: 2)
   ✅ Reduce narrative repetition (cost: 4)
```

## Logs and Monitoring

### Log Files

The system creates several types of logs in `maintenance_logs/`:

- **Daily Metrics**: `metrics_YYYYMMDD.json` - Daily health measurements
- **Iteration Logs**: `iteration_XXX.json` - Detailed iteration results
- **Backups**: `backups/` - File backups before changes
- **Exports**: `metrics_export_TIMESTAMP.json` - Manual metric exports

### Monitoring Health Trends

```bash
# Check trends over time
ls -la maintenance_logs/metrics_*.json

# View specific day's metrics
cat maintenance_logs/metrics_20240115.json | jq '.[] | {timestamp, overall_health}'
```

## Integration with Development Workflow

### Daily Development
```bash
# Start each day with a health check
python run_maintenance.py --health-check

# After making changes, run light maintenance
python run_maintenance.py --iterations 1
```

### Weekly Maintenance
```bash
# Weekly deep maintenance session
python run_maintenance.py --iterations 10 --complexity-budget 20
```

### Before Releases
```bash
# Comprehensive pre-release check
python run_maintenance.py --health-check --export-metrics
python run_maintenance.py --iterations 5
```

## Advanced Usage

### Custom Improvement Strategies

To add custom improvement types, edit `src/maintenance/maintenance_mode.py`:

```python
# Add new improvement type
class ImprovementType(Enum):
    # ... existing types ...
    DOCUMENTATION = 8  # New type with lower priority

# Add implementation method
def _implement_documentation_improvement(self, improvement: Improvement) -> bool:
    """Implement documentation improvements"""
    # Your custom improvement logic here
    return True
```

### Integration with CI/CD

Add to your CI pipeline:

```yaml
# .github/workflows/maintenance.yml
- name: Run Automated Maintenance
  run: |
    python run_maintenance.py --health-check
    if [ $? -ne 0 ]; then
      echo "Health check failed, running maintenance..."
      python run_maintenance.py --iterations 3
    fi
```

### Custom Metrics

Extend the metrics system in `src/maintenance/metrics.py`:

```python
def measure_custom_quality(self) -> float:
    """Measure your custom quality metric"""
    # Implementation here
    return score

# Add to comprehensive metrics collection
def collect_comprehensive_metrics(self, project_root: Path = None) -> Dict:
    metrics = {
        # ... existing metrics ...
        "custom_quality": self.measure_custom_quality()
    }
    return metrics
```

## Troubleshooting

### Common Issues

**Maintenance won't start**
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Verify Python path includes `src` directory
- Check file permissions on `run_maintenance.py`

**Tests failing during maintenance** 
- Run tests manually: `python -m pytest tests/ -v`
- Check for missing test dependencies
- Review test output in maintenance logs

**Performance metrics show poor scores**
- Profile your code: `python -m cProfile play_years_of_lead.py`
- Check for memory leaks or infinite loops
- Review recent changes that might impact performance

**Health checks returning errors**
- Verify project structure matches expected layout
- Check that game modules can be imported properly
- Review error messages in verbose mode: `--verbose`

### Debug Mode

Enable detailed debugging:

```bash
# Run with maximum verbosity
python run_maintenance.py --verbose --iterations 1

# Check specific log files
tail -f maintenance_logs/iteration_001.json
```

## Best Practices

### Development Guidelines

1. **Run health checks frequently** - Check health after each major change
2. **Keep complexity budget reasonable** - Don't try to fix everything at once
3. **Review maintenance logs** - Understand what changes are being made
4. **Test manually after maintenance** - Automated tests can't catch everything
5. **Backup before major sessions** - Maintenance creates backups, but be safe

### Maintenance Schedule

**Daily**: Health check and light maintenance (1-2 iterations)
**Weekly**: Deep maintenance session (5-10 iterations)  
**Monthly**: Full system optimization and metric export
**Before releases**: Comprehensive health check and targeted fixes

### Team Workflow

**For Individual Developers**:
- Run health check before starting work
- Quick maintenance after completing features
- Export metrics weekly for trend analysis

**For Teams**:
- Designate a "maintenance owner" for each sprint
- Include health metrics in code reviews
- Run maintenance in CI/CD pipeline
- Share weekly health reports with team

## Example Scenarios

### Scenario 1: New Developer Onboarding
```bash
# Check project health
python run_maintenance.py --health-check

# Run initial cleanup
python run_maintenance.py --iterations 3

# Export baseline metrics
python run_maintenance.py --export-metrics
```

### Scenario 2: Pre-Release Preparation
```bash
# Comprehensive health assessment
python run_maintenance.py --health-check --verbose

# Address any critical issues
python run_maintenance.py --iterations 10 --complexity-budget 25

# Final verification
python run_maintenance.py --health-check
```

### Scenario 3: Performance Investigation
```bash
# Export current metrics for baseline
python run_maintenance.py --export-metrics

# Focus on performance improvements
# Edit config/maintenance.json to prioritize performance

# Run targeted maintenance
python run_maintenance.py --iterations 5

# Compare before/after metrics
python run_maintenance.py --export-metrics
```

## Future Enhancements

The maintenance system is designed to be extensible. Potential future enhancements include:

- **ML-driven improvement suggestions** - Use machine learning to identify patterns
- **Integration with version control** - Automatically create branches for improvements
- **Advanced narrative analysis** - Deeper understanding of story quality
- **Performance profiling integration** - Automatic performance bottleneck detection
- **Custom improvement workflows** - User-defined improvement strategies
- **Team collaboration features** - Share maintenance results across team members

## Contributing

To contribute to the maintenance system:

1. Add tests for new features in `tests/maintenance/`
2. Update configuration schema if adding new settings
3. Document new metrics in this guide
4. Follow the complexity budget principles in your improvements

---

*The automated maintenance system helps keep Years of Lead healthy and improving over time. Like a good gardener, it makes small, careful changes that compound into significant improvements while keeping the system stable and reliable.* 