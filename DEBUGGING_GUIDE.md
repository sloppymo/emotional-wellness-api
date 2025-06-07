# Debugging & Testing Guide

## 🎯 **Making Debugging as Easy as Humanly Possible**

This guide provides comprehensive tools and techniques for diagnosing any problem in the Emotional Wellness API system.

---

## 🚀 **Quick Start - Problem Diagnosis**

### 1. **Immediate Health Check**
```bash
# Quick system overview
make debug-health

# Or run directly
python scripts/debug_cli.py health
```

### 2. **Component-Specific Diagnosis**
```bash
# Diagnose specific components
make debug-moss      # MOSS crisis detection system
make debug-veluria   # VELURIA intervention protocols
python scripts/debug_cli.py diagnose database
python scripts/debug_cli.py diagnose redis
```

### 3. **Real-Time Monitoring**
```bash
# Monitor system in real-time
make debug-monitor

# Or with custom duration
python scripts/debug_cli.py monitor 60
```

---

## 🧪 **Enhanced Testing Infrastructure**

### **Test Categories**
```bash
# Run all tests with coverage
make test

# Component-specific tests
make test-moss       # MOSS system tests
make test-veluria    # VELURIA protocol tests
make test-crisis     # Crisis intervention tests

# Test types
pytest tests/ -m unit           # Unit tests only
pytest tests/ -m integration    # Integration tests
pytest tests/ -m performance    # Performance tests
pytest tests/ -m critical       # Critical functionality
```

### **Advanced Test Features**
```bash
# Watch mode (auto-rerun on changes)
make test-watch

# Performance benchmarking
make test-performance

# Coverage with detailed reporting
make coverage-full
```

---

## 🔍 **Debugging Tools & Features**

### **1. Interactive Debug CLI**
```bash
# Launch interactive debugging session
make debug

# Available commands:
python scripts/debug_cli.py health              # System health check
python scripts/debug_cli.py diagnose [component] # Component diagnostics
python scripts/debug_cli.py test crisis         # Crisis workflow test
python scripts/debug_cli.py monitor [duration]  # Real-time monitoring
```

### **2. Enhanced Error Context Capture**
- **Automatic error context capture** with system state
- **Local variable inspection** at error time
- **Call stack analysis** with code context
- **Error pattern detection** and frequency tracking
- **Automated debugging suggestions**

### **3. Comprehensive Health Monitoring**
- **Component health checks** for all major systems
- **Performance metrics** with response time tracking
- **Integration status** monitoring
- **Resource usage** monitoring (CPU, memory, disk)

### **4. Advanced Logging**
```bash
# View recent logs
make debug-logs

# Component-specific logs
tail -f logs/moss.log
tail -f logs/veluria.log
tail -f logs/app.log

# Error logs only
grep -i error logs/app.log | tail -20
```

---

## 🎛️ **Debug Session Features**

### **Context-Aware Debugging**
```python
from src.debugging import create_debug_session

# Create debug session
debug_session = create_debug_session(
    debug_level=DebugLevel.COMPREHENSIVE,
    auto_diagnose=True,
    capture_performance=True
)

# Use debug context
async with debug_session.debug_context(
    component="moss",
    operation="crisis_assessment",
    user_id="user123"
) as context:
    # Your code here - automatic error capture and diagnostics
    result = await crisis_classifier.assess_risk(text)
```

### **Automatic Diagnostics**
- **Real-time component health checks**
- **Performance monitoring** with automatic bottleneck detection
- **Error context capture** with system state snapshots
- **Recovery suggestions** based on error patterns

---

## 🚨 **Crisis Intervention Debugging**

### **Crisis Workflow Testing**
```bash
# Test complete crisis intervention workflow
make debug-crisis

# Or run specific crisis tests
python scripts/debug_cli.py test crisis
```

### **MOSS System Debugging**
```bash
# Comprehensive MOSS diagnostics
make debug-moss

# Test specific MOSS components
pytest tests/symbolic/moss/ -v --tb=long
```

### **VELURIA Protocol Debugging**
```bash
# VELURIA system diagnostics
python scripts/debug_cli.py diagnose veluria

# Test protocol execution
pytest tests/symbolic/veluria/ -v --tb=long
```

---

## 📊 **Performance Analysis**

### **Performance Profiling**
```bash
# Run performance tests
make test-performance

# Profile specific components
python scripts/profile_component.py moss
python scripts/profile_component.py veluria
```

### **Memory Analysis**
```bash
# Memory usage monitoring
python scripts/memory_analysis.py

# Memory leak detection
pytest tests/ --memray
```

### **Load Testing**
```bash
# Stress testing
make stress-test

# Load testing with Locust
make load-test
```

---

## 🔧 **Development Debugging**

### **Code Quality Checks**
```bash
# Linting and formatting
make lint

# Fix formatting issues
make lint-fix

# Security checks
make security
```

### **Database Debugging**
```bash
# Database health check
python scripts/debug_cli.py diagnose database

# Reset database for testing
make db-reset

# Run migrations
make db-migrate
```

### **Integration Debugging**
```bash
# Check all integrations
python scripts/debug_cli.py diagnose integration

# Test specific integrations
pytest tests/integration/ -v
```

---

## 📈 **Monitoring & Observability**

### **Real-Time Monitoring**
```bash
# System monitoring dashboard
make debug-monitor

# Component-specific monitoring
python scripts/monitor_component.py moss
python scripts/monitor_component.py veluria
```

### **Health Dashboards**
- **System Health**: http://localhost:8000/health
- **Admin Dashboard**: http://localhost:8000/dashboard
- **Metrics**: http://localhost:8000/metrics

### **Log Analysis**
```bash
# Structured log analysis
python scripts/analyze_logs.py --component moss --hours 24

# Error pattern detection
python scripts/error_patterns.py --since yesterday
```

---

## 🛠️ **Troubleshooting Common Issues**

### **Database Connection Issues**
```bash
# Check database connectivity
python scripts/debug_cli.py diagnose database

# Common fixes:
make db-migrate          # Run pending migrations
make db-reset           # Reset database (dev only)
docker-compose restart postgres  # Restart database
```

### **Redis Connection Issues**
```bash
# Check Redis connectivity
python scripts/debug_cli.py diagnose redis

# Common fixes:
docker-compose restart redis  # Restart Redis
redis-cli ping               # Test Redis directly
```

### **MOSS System Issues**
```bash
# Comprehensive MOSS diagnostics
make debug-moss

# Check specific components:
pytest tests/symbolic/moss/test_crisis_classifier.py -v
pytest tests/symbolic/moss/test_audit_logging.py -v
```

### **VELURIA Protocol Issues**
```bash
# VELURIA system diagnostics
python scripts/debug_cli.py diagnose veluria

# Test protocol execution:
pytest tests/symbolic/veluria/test_intervention_protocol.py -v
```

### **Performance Issues**
```bash
# Performance analysis
make test-performance

# Memory profiling
python scripts/memory_profiler.py

# CPU profiling
python scripts/cpu_profiler.py
```

---

## 🎯 **Best Practices for Debugging**

### **1. Start with Health Check**
Always begin with a comprehensive health check:
```bash
make debug-health
```

### **2. Use Component-Specific Diagnostics**
Focus on the specific component having issues:
```bash
make debug-moss      # For crisis detection issues
make debug-veluria   # For intervention protocol issues
```

### **3. Monitor in Real-Time**
Use real-time monitoring for intermittent issues:
```bash
make debug-monitor
```

### **4. Check Error Patterns**
Look for recurring error patterns:
```bash
python scripts/error_analysis.py --pattern-detection
```

### **5. Use Debug Context**
Wrap problematic code in debug context for automatic error capture:
```python
async with debug_session.debug_context("component", "operation"):
    # Problematic code here
    pass
```

---

## 📚 **Additional Resources**

### **Configuration Files**
- `pytest_enhanced.ini` - Enhanced pytest configuration
- `DEBUGGING_GUIDE.md` - This comprehensive guide
- `Makefile` - All debugging commands

### **Debug Scripts**
- `scripts/debug_cli.py` - Interactive debug CLI
- `scripts/simple_debug.py` - Quick system check
- `scripts/debug-helpers.py` - Legacy debug helpers

### **Test Infrastructure**
- `src/debugging/` - Advanced debugging infrastructure
- `src/testing/` - Enhanced testing utilities
- `tests/` - Comprehensive test suite

---

## 🚀 **Quick Reference Commands**

```bash
# Essential debugging commands
make debug-health     # System health check
make debug-moss       # MOSS system diagnostics
make debug-crisis     # Crisis workflow test
make debug-monitor    # Real-time monitoring
make test-crisis      # Crisis intervention tests
make coverage-full    # Detailed coverage report

# Development helpers
make lint-fix         # Fix code formatting
make db-reset         # Reset database (dev)
make clean           # Clean build artifacts
```

---

*This guide is designed to make debugging as straightforward as possible. Start with the health check, use component-specific diagnostics, and leverage the comprehensive monitoring tools for any system issue.* 