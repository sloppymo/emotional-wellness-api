# Years of Lead - Automated Maintenance System Setup Guide

## 🎯 Overview

The Years of Lead Automated Maintenance System is a sophisticated self-improvement system that continuously monitors, tests, and enhances your game while you sleep. Think of it as having a careful robot assistant that makes small, targeted improvements without breaking anything.

## ✅ What's Included

### Core Infrastructure ✅
- **MaintenanceMode** (`src/maintenance/maintenance_mode.py`) - Core maintenance engine
- **GameHealthMetrics** (`src/maintenance/metrics.py`) - Health monitoring and metrics collection
- **Test Scenarios** (`tests/maintenance/test_scenarios.py`) - Comprehensive standardized test suite
- **Configuration** (`config/maintenance.json`) - Configurable settings and thresholds

### Automation Scripts ✅
- **Main Runner** (`run_maintenance.py`) - Interactive maintenance runner
- **Overnight Automation** (`scripts/overnight_maintenance.py`) - Unattended overnight operation
- **Health Monitoring** - Real-time system health assessment

### Testing Infrastructure ✅
- **Emotional Consistency Tests** - Validate emotional state behavior
- **Narrative Coherence Tests** - Ensure story quality and variety
- **Performance Benchmarks** - Monitor system performance
- **Agent Interaction Tests** - Multi-agent scenario validation
- **Memory and Stability Tests** - Resource usage and stability monitoring

## 🚀 Quick Start

### 1. Health Check
```bash
python3 run_maintenance.py --health-check
```
This gives you an immediate overview of your system's health across all metrics.

### 2. Single Iteration
```bash
python3 run_maintenance.py --iterations 1
```
Runs one maintenance cycle to make targeted improvements.

### 3. Overnight Automation
```bash
python3 scripts/overnight_maintenance.py --hours 8 --budget 50
```
Runs automated maintenance overnight with a complexity budget of 50.

### 4. Dry Run Testing
```bash
python3 scripts/overnight_maintenance.py --dry-run --hours 1
```
Tests the system without making actual changes.

## 📊 Understanding Health Metrics

### Overall Health Score (0.0 - 1.0)
- **🟢 0.8+** Excellent - System running optimally
- **🟡 0.6-0.8** Good - Minor issues, stable operation
- **🟠 0.4-0.6** Needs Attention - Some problems detected
- **🔴 0.0-0.4** Critical - Immediate attention required

### Individual Metrics
- **📋 Test Coverage** - Percentage of code covered by tests
- **⚡ Performance** - System responsiveness and efficiency
- **📚 Narrative Quality** - Story coherence and variety
- **❤️ Emotional Consistency** - Believable emotional behavior

## 🔧 Improvement Types (Priority Order)

1. **CRITICAL_BUG** - Game crashes or data corruption
2. **MAJOR_BUG** - Features not working as intended
3. **PERFORMANCE** - Slow or inefficient operations
4. **NARRATIVE** - Repetitive or incoherent storytelling
5. **EMOTIONAL** - Unrealistic emotional behavior
6. **VARIETY** - Adding content and feature variety
7. **POLISH** - Small quality-of-life improvements

## ⚙️ Configuration Options

Edit `config/maintenance.json` to customize:

```json
{
  "max_iterations": 20,
  "min_test_coverage": 0.8,
  "max_complexity_per_change": 3,
  "required_metrics": {
    "narrative_coherence": 0.7,
    "emotional_consistency": 0.8,
    "performance_baseline": 1.0
  }
}
```

### Key Settings:
- **max_complexity_per_change** - Limits how big each improvement can be
- **required_metrics** - Minimum thresholds for each health metric
- **performance_thresholds** - Timing limits for operations

## 🌙 Overnight Automation Features

### Safety Mechanisms
- **Complexity Budget** - Prevents runaway changes
- **Health Monitoring** - Stops if system health degrades
- **Error Threshold** - Halts after too many failures
- **Graceful Shutdown** - Responds to CTRL+C properly

### Logging & Reporting
- **Detailed JSON logs** in `maintenance_logs/`
- **Health snapshots** before/after each iteration
- **Comprehensive final report** with trends and recommendations

### Command Line Options
```bash
# Basic overnight run (8 hours, budget 50)
python3 scripts/overnight_maintenance.py

# Custom duration and budget
python3 scripts/overnight_maintenance.py --hours 4 --budget 100

# Test mode without changes
python3 scripts/overnight_maintenance.py --dry-run
```

## 📁 Directory Structure

```
years-of-lead/
├── src/maintenance/           # Core maintenance system
│   ├── maintenance_mode.py    # Main maintenance logic
│   ├── metrics.py            # Health metrics collection
│   └── __init__.py
├── tests/maintenance/         # Maintenance test suite
│   ├── test_scenarios.py     # Comprehensive scenarios
│   └── test_maintenance_basic.py
├── config/
│   └── maintenance.json      # Configuration settings
├── scripts/
│   └── overnight_maintenance.py  # Overnight automation
├── maintenance_logs/          # Generated logs and backups
│   └── backups/              # File backups before changes
├── run_maintenance.py         # Main runner script
└── MAINTENANCE_SETUP_GUIDE.md # This guide
```

## 🔍 Test Scenarios Explained

### Emotional Consistency Scenarios
- **Drift Rate Testing** - Emotions change at believable speeds
- **Bounds Checking** - Values stay within -1.0 to 1.0 range
- **Trauma Persistence** - Traumatic events have lasting effects

### Narrative Coherence Scenarios
- **Variety Testing** - Descriptions aren't repetitive
- **Sequence Logic** - Events follow logical progression
- **Context Awareness** - Events fit the current situation

### Performance Scenarios
- **Initialization Speed** - Game starts quickly
- **Step Performance** - Game operations are responsive
- **Memory Stability** - No memory leaks during operation

### Multi-Agent Scenarios
- **Interaction Testing** - Agents can interact properly
- **State Persistence** - Agent states save/load correctly
- **High Load Stability** - System handles many agents

## 🔄 Maintenance Workflow

### Phase 1: Observation
1. Collect comprehensive health metrics
2. Run standardized test scenarios
3. Identify highest-priority issues

### Phase 2: Diagnosis
1. Analyze test results and metrics
2. Determine root causes of problems
3. Select appropriate improvement strategy

### Phase 3: Treatment
1. Make minimal, targeted changes
2. Verify improvements with tests
3. Monitor for unintended side effects

### Phase 4: Verification
1. Re-run all tests after changes
2. Compare health metrics before/after
3. Roll back if system health degrades

### Phase 5: Documentation
1. Log all changes and results
2. Update complexity budget
3. Plan next iteration if needed

## 🛡️ Safety Features

### Complexity Budget System
- Prevents feature creep and over-engineering
- Limits changes to manageable increments
- Automatically decreases as improvements are made

### Automatic Rollback
- Reverts changes if tests fail
- Monitors health degradation
- Maintains system stability

### Comprehensive Logging
- Every change is documented
- Health trends are tracked
- Error patterns are recorded

## 📈 Monitoring and Trends

### Real-Time Health Monitoring
```bash
# Check current health
python3 run_maintenance.py --health-check

# Export detailed metrics
python3 run_maintenance.py --export-metrics
```

### Log Analysis
- Health trends over time
- Improvement effectiveness
- Error patterns and frequency
- Performance degradation detection

## 🚨 Troubleshooting

### Common Issues

**"No module named 'game.emotional_state'"**
- This is expected for new projects
- The maintenance system will identify and help implement missing components

**Test coverage at 0%**
- Install pytest-cov: `pip install pytest-cov`
- Add tests to the appropriate directories

**Health score consistently low**
- Review recent changes in `maintenance_logs/`
- Consider manual intervention before automated maintenance
- Check for fundamental architectural issues

### Recovery Procedures

**If overnight maintenance fails:**
1. Check `maintenance_logs/` for error details
2. Review backups in `maintenance_logs/backups/`
3. Run health check to assess current state
4. Consider restoring from backup if needed

**If system becomes unstable:**
1. Stop automated maintenance immediately
2. Run `--health-check` to assess damage
3. Review recent improvements in logs
4. Manually revert problematic changes

## 🎓 Best Practices

### Before Running Overnight Maintenance
1. Commit your current work to git
2. Run a health check to establish baseline
3. Start with a small complexity budget (10-20)
4. Use `--dry-run` first to test the system

### Monitoring During Operation
- Check logs periodically for errors
- Monitor health trends for degradation
- Ensure adequate disk space for logs
- Have a rollback plan ready

### After Maintenance Sessions
1. Review the final report
2. Analyze health trends and improvements
3. Commit beneficial changes to git
4. Document any manual fixes needed

## 🚀 Advanced Usage

### Custom Scenarios
Add new test scenarios to `tests/maintenance/test_scenarios.py`:
```python
def test_custom_behavior(self):
    """Test your specific game behavior"""
    # Your test implementation
    pass
```

### Custom Improvements
Extend the improvement identification in `maintenance_mode.py`:
```python
# Add custom improvement detection logic
if self.detect_custom_issue():
    candidates.append(Improvement(
        type=ImprovementType.CUSTOM,
        description="Fix custom issue",
        complexity_cost=2,
        file_to_modify="src/custom/module.py",
        test_to_verify="tests/custom/test_module.py"
    ))
```

### Integration with CI/CD
```yaml
# .github/workflows/maintenance.yml
- name: Run Maintenance Health Check
  run: python3 run_maintenance.py --health-check
```

## 📞 Support and Feedback

The maintenance system is designed to be conservative and safe, but if you encounter issues:

1. Check the comprehensive logs in `maintenance_logs/`
2. Review this guide for troubleshooting steps
3. Start with smaller complexity budgets
4. Use dry-run mode to test changes

Remember: The system is designed to make your game better gradually and safely. Trust the process, monitor the results, and enjoy watching your game improve while you sleep! 🌙✨ 