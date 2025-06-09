# 🎮 Shadowrun Interface - Automated Testing Framework

## 🚀 Complete GUI, Feature & QA Testing Automation

This repository contains a comprehensive automated testing framework specifically designed for the Shadowrun Interface. The framework provides full automation for GUI testing, feature validation, accessibility compliance, visual regression testing, and performance monitoring.

## ✅ Framework Capabilities

### 🖥️ **GUI Component Testing**
- **Automated Element Detection**: Intelligent detection of React components and interactive elements
- **Form Interaction**: Automatic form filling, validation, and submission testing
- **Navigation Testing**: Menu navigation, routing, and page transitions
- **Interactive Elements**: Button clicks, dropdowns, modals, and dynamic content

### ⚡ **Feature Testing**
- **Character Sheet Functionality**: Attribute updates, skill calculations, derived values
- **Dice Rolling Mechanics**: Shadowrun dice system validation, hit counting, glitch detection
- **Combat System**: Initiative tracking, damage calculation, status effects
- **Matrix Interface**: Cyberdeck operations, ICE interactions, data streams

### ♿ **Accessibility Testing**
- **WCAG Compliance**: Automated scanning for accessibility violations
- **Screen Reader Compatibility**: Semantic markup and ARIA label validation
- **Keyboard Navigation**: Tab order and keyboard-only operation testing
- **Color Contrast**: Automated color contrast ratio checking

### 👀 **Visual Regression Testing**
- **Screenshot Comparison**: Pixel-perfect comparison with baseline images
- **Layout Consistency**: Component positioning and responsive design validation
- **Cross-Browser Rendering**: Visual consistency across different browsers
- **Theme Testing**: Dark/light mode and styling verification

### 🚀 **Performance Testing**
- **Page Load Metrics**: Load time, first paint, DOM content loaded
- **Resource Monitoring**: Memory usage, CPU utilization, network requests
- **Performance Budgets**: Automated alerts for performance regressions
- **Bundle Size Analysis**: Asset optimization and loading efficiency

### 🎭 **Cross-Browser Testing**
- **Multi-Browser Support**: Chromium, Firefox, WebKit automated testing
- **Mobile Testing**: Responsive design across different viewport sizes
- **Device Emulation**: Testing on various device configurations
- **Browser Compatibility**: Feature support across browser versions

### 🎲 **Shadowrun-Specific Testing**
- **Game Rules Validation**: Shadowrun 6th Edition rule compliance
- **Character Attributes**: Valid ranges (1-6), racial modifiers, augmentations
- **Dice Pool Calculations**: Attribute + skill combinations, situational modifiers
- **Combat Mechanics**: Initiative, damage resistance, overflow damage
- **Matrix Operations**: Attack/Sleaze/Data Processing/Firewall validation

## 🛠️ Technical Stack

### Core Dependencies
- **Playwright** - Browser automation and testing
- **pytest** - Test framework and execution
- **NumPy** - Image processing for visual testing
- **Pillow (PIL)** - Image manipulation and comparison
- **psutil** - System performance monitoring
- **axe-playwright-python** - Accessibility testing

### AI-Powered Features
- **Intelligent Test Generation**: Automatic test case creation from component analysis
- **Pattern Recognition**: Shadowrun-specific element detection
- **Smart Assertions**: Context-aware validation rules
- **Adaptive Testing**: Self-healing tests that adapt to UI changes

## 📁 Project Structure

```
tests/
├── automated_testing_framework.py    # Main testing framework
├── ai_test_generator.py              # AI-powered test generation
├── run_automated_tests.py            # CLI test runner
├── pytest.ini                       # Pytest configuration
├── requirements-testing.txt          # Testing dependencies
├── test_automation_ready.py          # Framework verification
├── generated/                        # AI-generated test files
├── test_artifacts/
│   ├── screenshots/                  # Visual test results
│   ├── reports/                      # HTML and JSON reports
│   └── videos/                       # Test execution recordings
└── components/                       # Component-specific tests
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# Activate virtual environment
source venv/bin/activate

# Install testing dependencies
pip install -r requirements-testing.txt

# Install Playwright browsers
playwright install
```

### 2. Verify Framework Setup
```bash
# Check framework status
python tests/framework_status.py

# Run verification tests
python -m pytest tests/test_automation_ready.py -v
```

### 3. Start Your Shadowrun App
```bash
# Start the development server
npm run dev
```

### 4. Run Automated Tests

#### Basic Test Suite
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test types
python -m pytest tests/ -m "gui" -v
python -m pytest tests/ -m "accessibility" -v
python -m pytest tests/ -m "shadowrun" -v
```

#### Full Automation Suite
```bash
# Run complete automated testing framework
python tests/run_automated_tests.py

# Run in headless mode
python tests/run_automated_tests.py --headless

# Generate only (no execution)
python tests/run_automated_tests.py --generate-only
```

#### AI Test Generation
```bash
# Generate AI-powered tests
python tests/ai_test_generator.py

# Generated tests will be in tests/generated/
```

## 📊 Test Reports

After running tests, comprehensive reports are generated:

- **HTML Report**: `test_artifacts/reports/test_report.html`
- **JSON Report**: `test_artifacts/reports/test_report.json`
- **Screenshots**: `test_artifacts/screenshots/`
- **Videos**: `test_artifacts/videos/`
- **Accessibility Report**: `test_artifacts/reports/accessibility_report.json`

## 🎯 Testing Strategies

### Component Testing
- **Smoke Tests**: Basic rendering and mounting verification
- **Integration Tests**: Component interaction and data flow
- **Regression Tests**: Prevention of functionality breaks

### Feature Testing
- **User Workflows**: Complete user journey testing
- **Business Logic**: Game rule and calculation validation
- **Error Handling**: Edge cases and error state testing

### Performance Testing
- **Load Testing**: Application behavior under load
- **Stress Testing**: Breaking point identification
- **Endurance Testing**: Long-running session stability

## 🔧 Configuration

### Pytest Configuration (`pytest.ini`)
```ini
[tool:pytest]
markers =
    gui: GUI component tests
    feature: Feature-specific tests
    accessibility: Accessibility tests
    visual: Visual regression tests
    performance: Performance tests
    shadowrun: Shadowrun game-specific tests
```

### Environment Variables
```bash
TESTING=1                    # Enable testing mode
NODE_ENV=test               # Set environment
SHADOWRUN_BASE_URL=http://localhost:3000
```

## 🎮 Shadowrun-Specific Features

### Character System Testing
- **Attribute Validation**: Body, Agility, Reaction, Strength, Willpower, Logic, Intuition, Charisma
- **Skill Testing**: Active skills, knowledge skills, language skills
- **Derived Attributes**: Condition monitors, initiative, limits

### Dice System Testing
- **Standard Rolls**: Attribute + skill dice pools
- **Edge Usage**: Edge mechanics and re-rolling
- **Glitch Detection**: Critical glitches and normal glitches
- **Extended Tests**: Multiple roll sequences

### Combat System Testing
- **Initiative Tracking**: Initiative order and passes
- **Damage Application**: Physical and stun damage
- **Armor Calculation**: Damage resistance and penetration
- **Status Effects**: Conditions and their impacts

### Matrix System Testing
- **Cyberdeck Operations**: Attack, Sleaze, Data Processing, Firewall
- **Program Management**: Running and loaded programs
- **Host Interactions**: Icon manipulation and file operations
- **Overwatch Score**: Heat tracking and convergence

## 🚀 Advanced Features

### AI-Powered Test Generation
The framework includes an AI component that:
- Analyzes React component structure
- Generates appropriate test cases
- Identifies Shadowrun-specific patterns
- Creates context-aware assertions

### Visual Testing
- Baseline image management
- Pixel-perfect comparison
- Responsive design validation
- Cross-browser consistency

### Performance Monitoring
- Real-time metrics collection
- Performance regression detection
- Resource usage optimization
- Load time analysis

## 🎯 Next Steps

1. **Start Development Server**: `npm run dev`
2. **Run Framework Verification**: `python tests/framework_status.py`
3. **Execute Full Test Suite**: `python tests/run_automated_tests.py`
4. **Review Test Reports**: Open `test_artifacts/reports/test_report.html`
5. **Generate AI Tests**: `python tests/ai_test_generator.py`

## 🤝 Contributing

When adding new tests:
1. Use appropriate pytest markers
2. Follow Shadowrun-specific naming conventions
3. Include accessibility considerations
4. Add visual regression baselines
5. Document game rule validations

## 📝 License

This testing framework is designed specifically for the Shadowrun Interface project.

---

**🎮 Ready to fully automate your Shadowrun Interface testing!** 