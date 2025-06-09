"""
AI-Powered Test Generator for Shadowrun Interface
=================================================

This module automatically analyzes React components and generates intelligent test cases
using pattern recognition and component analysis.
"""

import ast
import json
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging


@dataclass
class ComponentInfo:
    """Information about a React component."""
    name: str
    file_path: str
    props: List[str]
    state_variables: List[str]
    event_handlers: List[str]
    child_components: List[str]
    test_ids: List[str]
    css_classes: List[str]
    complexity_score: int


@dataclass
class GeneratedTest:
    """A generated test case."""
    test_name: str
    test_type: str
    component: str
    test_code: str
    priority: int  # 1-5, 5 being highest
    description: str


class AITestGenerator:
    """
    AI-powered test generator that analyzes React components and creates intelligent test cases.
    """
    
    def __init__(self, src_dir: str = "src", pages_dir: str = "pages"):
        self.src_dir = Path(src_dir)
        self.pages_dir = Path(pages_dir)
        self.components: List[ComponentInfo] = []
        self.generated_tests: List[GeneratedTest] = []
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    def analyze_codebase(self) -> List[ComponentInfo]:
        """Analyze the entire codebase to find and analyze React components."""
        self.logger.info("🔍 Analyzing React components...")
        
        # Find all TypeScript/JavaScript React files
        react_files = []
        for pattern in ["**/*.tsx", "**/*.ts", "**/*.jsx", "**/*.js"]:
            react_files.extend(self.src_dir.glob(pattern))
            if self.pages_dir.exists():
                react_files.extend(self.pages_dir.glob(pattern))
        
        for file_path in react_files:
            if self._is_react_component_file(file_path):
                component_info = self._analyze_component_file(file_path)
                if component_info:
                    self.components.append(component_info)
        
        self.logger.info(f"Found {len(self.components)} React components")
        return self.components
    
    def generate_tests(self) -> List[GeneratedTest]:
        """Generate intelligent test cases for all components."""
        self.logger.info("🤖 Generating AI-powered test cases...")
        
        for component in self.components:
            # Generate different types of tests based on component analysis
            self.generated_tests.extend(self._generate_component_tests(component))
            self.generated_tests.extend(self._generate_interaction_tests(component))
            self.generated_tests.extend(self._generate_accessibility_tests(component))
            self.generated_tests.extend(self._generate_visual_tests(component))
            
            # Generate Shadowrun-specific tests
            if self._is_shadowrun_component(component):
                self.generated_tests.extend(self._generate_shadowrun_tests(component))
        
        # Sort by priority
        self.generated_tests.sort(key=lambda t: t.priority, reverse=True)
        
        self.logger.info(f"Generated {len(self.generated_tests)} test cases")
        return self.generated_tests
    
    def _is_react_component_file(self, file_path: Path) -> bool:
        """Check if a file contains React components."""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Look for React patterns
            react_patterns = [
                r'import.*React',
                r'export.*function.*\(',
                r'export.*const.*=.*\(',
                r'const.*=.*\(\)',
                r'function.*\(\)',
                r'<[A-Z][a-zA-Z]*',  # JSX components
                r'\.tsx?$',  # TypeScript React files
            ]
            
            return any(re.search(pattern, content, re.IGNORECASE) for pattern in react_patterns)
            
        except Exception:
            return False
    
    def _analyze_component_file(self, file_path: Path) -> Optional[ComponentInfo]:
        """Analyze a React component file to extract information."""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Extract component name
            component_name = self._extract_component_name(content, file_path)
            if not component_name:
                return None
            
            # Extract props
            props = self._extract_props(content)
            
            # Extract state variables
            state_variables = self._extract_state_variables(content)
            
            # Extract event handlers
            event_handlers = self._extract_event_handlers(content)
            
            # Extract child components
            child_components = self._extract_child_components(content)
            
            # Extract test IDs
            test_ids = self._extract_test_ids(content)
            
            # Extract CSS classes
            css_classes = self._extract_css_classes(content)
            
            # Calculate complexity score
            complexity_score = self._calculate_complexity(content)
            
            return ComponentInfo(
                name=component_name,
                file_path=str(file_path),
                props=props,
                state_variables=state_variables,
                event_handlers=event_handlers,
                child_components=child_components,
                test_ids=test_ids,
                css_classes=css_classes,
                complexity_score=complexity_score
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to analyze {file_path}: {e}")
            return None
    
    def _extract_component_name(self, content: str, file_path: Path) -> Optional[str]:
        """Extract the main component name from the file."""
        # Try different patterns
        patterns = [
            r'export\s+default\s+function\s+(\w+)',
            r'export\s+default\s+(\w+)',
            r'export\s+const\s+(\w+)\s*=',
            r'function\s+(\w+)\s*\(',
            r'const\s+(\w+)\s*=.*=>'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        # Fallback to filename
        return file_path.stem.replace('.', '')
    
    def _extract_props(self, content: str) -> List[str]:
        """Extract component props."""
        props = []
        
        # Look for TypeScript interface props
        interface_match = re.search(r'interface\s+\w*Props\s*{([^}]+)}', content, re.DOTALL)
        if interface_match:
            prop_section = interface_match.group(1)
            prop_matches = re.findall(r'(\w+)\s*[?:]', prop_section)
            props.extend(prop_matches)
        
        # Look for destructured props
        destructure_matches = re.findall(r'{\s*([^}]+)\s*}\s*[:=]', content)
        for match in destructure_matches:
            prop_names = [p.strip() for p in match.split(',') if p.strip()]
            props.extend(prop_names)
        
        return list(set(props))
    
    def _extract_state_variables(self, content: str) -> List[str]:
        """Extract state variables (useState, etc.)."""
        state_vars = []
        
        # useState pattern
        use_state_matches = re.findall(r'const\s*\[\s*(\w+)\s*,\s*set\w+\s*\]\s*=\s*useState', content)
        state_vars.extend(use_state_matches)
        
        # useReducer pattern
        use_reducer_matches = re.findall(r'const\s*\[\s*(\w+)\s*,\s*\w+\s*\]\s*=\s*useReducer', content)
        state_vars.extend(use_reducer_matches)
        
        return list(set(state_vars))
    
    def _extract_event_handlers(self, content: str) -> List[str]:
        """Extract event handler functions."""
        handlers = []
        
        # Look for handler functions
        handler_patterns = [
            r'const\s+(handle\w+)\s*=',
            r'function\s+(handle\w+)\s*\(',
            r'const\s+(on\w+)\s*=',
            r'function\s+(on\w+)\s*\(',
            r'(\w*Click\w*)',
            r'(\w*Submit\w*)',
            r'(\w*Change\w*)'
        ]
        
        for pattern in handler_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            handlers.extend(matches)
        
        return list(set(handlers))
    
    def _extract_child_components(self, content: str) -> List[str]:
        """Extract child React components used in JSX."""
        components = []
        
        # Find JSX component tags
        jsx_matches = re.findall(r'<([A-Z][a-zA-Z]*)', content)
        components.extend(jsx_matches)
        
        return list(set(components))
    
    def _extract_test_ids(self, content: str) -> List[str]:
        """Extract data-testid attributes."""
        test_ids = []
        
        # Find data-testid attributes
        testid_matches = re.findall(r'data-testid=["\']([^"\']+)["\']', content)
        test_ids.extend(testid_matches)
        
        return list(set(test_ids))
    
    def _extract_css_classes(self, content: str) -> List[str]:
        """Extract CSS classes."""
        classes = []
        
        # Find className attributes
        class_matches = re.findall(r'className=["\']([^"\']+)["\']', content)
        for match in class_matches:
            classes.extend(match.split())
        
        return list(set(classes))
    
    def _calculate_complexity(self, content: str) -> int:
        """Calculate component complexity score."""
        score = 0
        
        # Count various complexity indicators
        score += len(re.findall(r'useState|useReducer|useEffect', content)) * 2
        score += len(re.findall(r'if\s*\(|switch\s*\(', content))
        score += len(re.findall(r'\.map\s*\(|\.filter\s*\(', content))
        score += len(re.findall(r'async\s+|await\s+', content))
        score += len(re.findall(r'<[A-Z][a-zA-Z]*', content)) // 2  # Child components
        
        return min(score, 10)  # Cap at 10
    
    def _is_shadowrun_component(self, component: ComponentInfo) -> bool:
        """Check if component is Shadowrun-specific."""
        shadowrun_keywords = [
            'character', 'dice', 'roll', 'combat', 'matrix', 'shadowrun',
            'cyberpunk', 'attribute', 'skill', 'spell', 'gear', 'weapon'
        ]
        
        component_text = (component.name + ' ' + ' '.join(component.css_classes) + 
                         ' '.join(component.test_ids)).lower()
        
        return any(keyword in component_text for keyword in shadowrun_keywords)
    
    def _generate_component_tests(self, component: ComponentInfo) -> List[GeneratedTest]:
        """Generate basic component tests."""
        tests = []
        
        # Rendering test
        tests.append(GeneratedTest(
            test_name=f"{component.name} - Renders correctly",
            test_type="component",
            component=component.name,
            priority=5,
            description=f"Verify that {component.name} renders without crashing",
            test_code=f"""
async def test_{component.name.lower()}_renders(page: Page):
    \"\"\"Test that {component.name} renders correctly.\"\"\"
    await page.goto('/path-to-component')  # Update with actual path
    
    # Check if component exists
    {'await page.wait_for_selector("[data-testid=\\"' + component.test_ids[0] + '\\"]")' if component.test_ids else 'pass'}
    
    # Verify component is visible
    assert await page.is_visible('body')
    
    # Take screenshot for visual verification
    await page.screenshot(path='test_artifacts/screenshots/{component.name.lower()}_render.png')
"""
        ))
        
        # Props test
        if component.props:
            tests.append(GeneratedTest(
                test_name=f"{component.name} - Props handling",
                test_type="component",
                component=component.name,
                priority=4,
                description=f"Test prop handling for {component.name}",
                test_code=f"""
async def test_{component.name.lower()}_props(page: Page):
    \"\"\"Test {component.name} prop handling.\"\"\"
    # Test with different prop values
    # Props: {', '.join(component.props[:5])}
    
    await page.goto('/path-to-component')
    
    # Verify component responds to prop changes
    # This would need component-specific implementation
    pass
"""
            ))
        
        return tests
    
    def _generate_interaction_tests(self, component: ComponentInfo) -> List[GeneratedTest]:
        """Generate interaction tests based on event handlers."""
        tests = []
        
        for handler in component.event_handlers[:3]:  # Limit to top 3
            tests.append(GeneratedTest(
                test_name=f"{component.name} - {handler} interaction",
                test_type="interaction",
                component=component.name,
                priority=4,
                description=f"Test {handler} interaction in {component.name}",
                test_code=f"""
async def test_{component.name.lower()}_{handler.lower()}_interaction(page: Page):
    \"\"\"Test {handler} interaction in {component.name}.\"\"\"
    await page.goto('/path-to-component')
    
    # Find and click the element that triggers {handler}
    {'await page.click("[data-testid=\\"' + component.test_ids[0] + '\\"]")' if component.test_ids else 'pass'}
    
    # Wait for interaction to complete
    await page.wait_for_timeout(500)
    
    # Verify expected behavior
    # Add specific assertions based on expected behavior
    pass
"""
            ))
        
        return tests
    
    def _generate_accessibility_tests(self, component: ComponentInfo) -> List[GeneratedTest]:
        """Generate accessibility tests."""
        tests = []
        
        tests.append(GeneratedTest(
            test_name=f"{component.name} - Accessibility check",
            test_type="accessibility",
            component=component.name,
            priority=3,
            description=f"Verify {component.name} meets accessibility standards",
            test_code=f"""
async def test_{component.name.lower()}_accessibility(page: Page):
    \"\"\"Test accessibility of {component.name}.\"\"\"
    from axe_playwright_python import Axe
    
    await page.goto('/path-to-component')
    
    # Run accessibility scan
    axe = Axe()
    await axe.inject(page)
    results = await axe.run(page)
    
    # Check for violations
    violations = results.get('violations', [])
    assert len(violations) == 0, f"Accessibility violations found: {{violations}}"
"""
        ))
        
        return tests
    
    def _generate_visual_tests(self, component: ComponentInfo) -> List[GeneratedTest]:
        """Generate visual regression tests."""
        tests = []
        
        tests.append(GeneratedTest(
            test_name=f"{component.name} - Visual regression",
            test_type="visual",
            component=component.name,
            priority=2,
            description=f"Visual regression test for {component.name}",
            test_code=f"""
async def test_{component.name.lower()}_visual_regression(page: Page):
    \"\"\"Visual regression test for {component.name}.\"\"\"
    await page.goto('/path-to-component')
    
    # Wait for component to load
    await page.wait_for_load_state('networkidle')
    
    # Take screenshot
    await page.screenshot(
        path='test_artifacts/screenshots/{component.name.lower()}_visual.png',
        full_page=True
    )
    
    # Compare with baseline (implement comparison logic)
    # This would need baseline images and comparison logic
    pass
"""
        ))
        
        return tests
    
    def _generate_shadowrun_tests(self, component: ComponentInfo) -> List[GeneratedTest]:
        """Generate Shadowrun-specific tests."""
        tests = []
        
        if 'dice' in component.name.lower() or any('dice' in cls for cls in component.css_classes):
            tests.append(GeneratedTest(
                test_name=f"{component.name} - Dice rolling mechanics",
                test_type="shadowrun",
                component=component.name,
                priority=5,
                description=f"Test dice rolling functionality in {component.name}",
                test_code=f"""
async def test_{component.name.lower()}_dice_rolling(page: Page):
    \"\"\"Test dice rolling mechanics in {component.name}.\"\"\"
    await page.goto('/path-to-component')
    
    # Find dice roll button
    roll_button = page.locator('button:has-text("Roll"), [data-testid*="roll"]')
    await roll_button.click()
    
    # Verify dice animation/result
    await page.wait_for_selector('.dice-result, [data-testid*="result"]', timeout=5000)
    
    # Check that result is within valid range
    result_text = await page.text_content('.dice-result, [data-testid*="result"]')
    # Add validation for Shadowrun dice mechanics (hits, glitches, etc.)
    pass
"""
            ))
        
        if 'character' in component.name.lower():
            tests.append(GeneratedTest(
                test_name=f"{component.name} - Character data handling",
                test_type="shadowrun",
                component=component.name,
                priority=5,
                description=f"Test character data management in {component.name}",
                test_code=f"""
async def test_{component.name.lower()}_character_data(page: Page):
    \"\"\"Test character data handling in {component.name}.\"\"\"
    await page.goto('/path-to-component')
    
    # Test character attribute updates
    attribute_inputs = page.locator('input[type="number"]')
    await attribute_inputs.first.fill('6')
    
    # Verify derived values update (like dice pools)
    await page.wait_for_timeout(500)
    
    # Check for valid Shadowrun character constraints
    # (attributes 1-6, skills 0-6, etc.)
    pass
"""
            ))
        
        return tests
    
    def export_tests(self, output_dir: str = "tests/generated"):
        """Export generated tests to pytest files."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True, parents=True)
        
        # Group tests by component
        component_tests = {}
        for test in self.generated_tests:
            if test.component not in component_tests:
                component_tests[test.component] = []
            component_tests[test.component].append(test)
        
        # Generate test files
        for component, tests in component_tests.items():
            file_content = self._generate_test_file(component, tests)
            file_path = output_path / f"test_{component.lower()}_generated.py"
            
            with open(file_path, 'w') as f:
                f.write(file_content)
        
        self.logger.info(f"Exported {len(component_tests)} test files to {output_path}")
    
    def _generate_test_file(self, component: str, tests: List[GeneratedTest]) -> str:
        """Generate a complete pytest file for a component."""
        imports = """
import pytest
from playwright.async_api import Page
import asyncio
from pathlib import Path

"""
        
        test_code = f"""
# Auto-generated tests for {component}
# Generated by AI Test Generator

"""
        
        for test in tests:
            test_code += f"""
{test.test_code}

"""
        
        return imports + test_code


# CLI interface
def main():
    """Main entry point for AI test generation."""
    generator = AITestGenerator()
    
    # Analyze codebase
    components = generator.analyze_codebase()
    print(f"Found {len(components)} React components")
    
    # Generate tests
    tests = generator.generate_tests()
    print(f"Generated {len(tests)} test cases")
    
    # Export tests
    generator.export_tests()
    print("Tests exported to tests/generated/")
    
    # Print summary
    test_types = {}
    for test in tests:
        test_types[test.test_type] = test_types.get(test.test_type, 0) + 1
    
    print("\nTest Summary:")
    for test_type, count in test_types.items():
        print(f"  {test_type}: {count}")


if __name__ == "__main__":
    main() 