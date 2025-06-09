#!/usr/bin/env python3
"""
Shadowrun Interface - Automated Test Runner
===========================================

This script runs the complete automated testing suite for the Shadowrun Interface.
It combines AI test generation, GUI testing, feature testing, and QA automation.

Usage:
    python tests/run_automated_tests.py [--headless] [--generate-only] [--run-only]
"""

import argparse
import asyncio
import sys
import time
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from automated_testing_framework import ShadowrunTestFramework
from ai_test_generator import AITestGenerator


def setup_argparse():
    """Setup command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Automated Testing Suite for Shadowrun Interface"
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser tests in headless mode"
    )
    
    parser.add_argument(
        "--generate-only",
        action="store_true",
        help="Only generate tests, don't run them"
    )
    
    parser.add_argument(
        "--run-only",
        action="store_true",
        help="Only run existing tests, don't generate new ones"
    )
    
    parser.add_argument(
        "--base-url",
        default="http://localhost:3000",
        help="Base URL for the application (default: http://localhost:3000)"
    )
    
    parser.add_argument(
        "--output-dir",
        default="test_artifacts",
        help="Directory for test artifacts (default: test_artifacts)"
    )
    
    return parser


async def main():
    """Main entry point for automated testing."""
    parser = setup_argparse()
    args = parser.parse_args()
    
    print("🎮 Shadowrun Interface - Automated Testing Suite")
    print("=" * 50)
    
    start_time = time.time()
    
    # Step 1: Generate AI-powered tests (unless --run-only is specified)
    if not args.run_only:
        print("\n🤖 Step 1: AI Test Generation")
        print("-" * 30)
        
        generator = AITestGenerator()
        
        # Analyze codebase
        print("Analyzing React components...")
        components = generator.analyze_codebase()
        print(f"✅ Found {len(components)} React components")
        
        # Generate tests
        print("Generating AI-powered test cases...")
        tests = generator.generate_tests()
        print(f"✅ Generated {len(tests)} test cases")
        
        # Export tests
        print("Exporting test files...")
        generator.export_tests()
        print("✅ Tests exported to tests/generated/")
        
        # Print test summary
        test_types = {}
        for test in tests:
            test_types[test.test_type] = test_types.get(test.test_type, 0) + 1
        
        print("\nGenerated Test Summary:")
        for test_type, count in test_types.items():
            print(f"  📝 {test_type.title()}: {count}")
    
    # Step 2: Run automated tests (unless --generate-only is specified)
    if not args.generate_only:
        print("\n🚀 Step 2: Automated Test Execution")
        print("-" * 35)
        
        # Initialize test framework
        framework = ShadowrunTestFramework(
            base_url=args.base_url,
            headless=args.headless
        )
        
        # Run complete test suite
        print("Starting comprehensive test suite...")
        suite = await framework.run_full_test_suite()
        
        # Print results
        print("\n📊 Test Execution Results")
        print("-" * 25)
        print(f"Total Tests: {len(suite.tests)}")
        print(f"✅ Passed: {suite.passed_count}")
        print(f"❌ Failed: {suite.failed_count}")
        print(f"⏩ Skipped: {len(suite.tests) - suite.passed_count - suite.failed_count}")
        print(f"📈 Success Rate: {suite.success_rate:.1f}%")
        print(f"⏱️  Duration: {suite.duration:.2f} seconds")
        
        # Test type breakdown
        print("\nTest Type Breakdown:")
        test_type_results = {}
        for test in suite.tests:
            test_type = test.test_type.value
            if test_type not in test_type_results:
                test_type_results[test_type] = {"passed": 0, "failed": 0, "total": 0}
            
            test_type_results[test_type]["total"] += 1
            if test.status.value == "passed":
                test_type_results[test_type]["passed"] += 1
            elif test.status.value == "failed":
                test_type_results[test_type]["failed"] += 1
        
        for test_type, results in test_type_results.items():
            success_rate = (results["passed"] / results["total"]) * 100 if results["total"] > 0 else 0
            print(f"  🎯 {test_type.title()}: {results['passed']}/{results['total']} ({success_rate:.1f}%)")
        
        # Artifacts and reports
        print(f"\n📁 Artifacts saved to: {framework.artifacts_dir}")
        print(f"📊 Reports available at: {framework.reports_dir}/test_report.html")
        
        # Performance metrics
        if suite.tests:
            avg_duration = sum(test.duration for test in suite.tests) / len(suite.tests)
            print(f"⚡ Average test duration: {avg_duration:.2f} seconds")
    
    total_time = time.time() - start_time
    print(f"\n🏁 Total execution time: {total_time:.2f} seconds")
    
    # Exit with appropriate code
    if not args.generate_only and not args.run_only:
        # Both generation and execution happened
        sys.exit(0 if suite.failed_count == 0 else 1)
    else:
        # Only generation or execution happened
        sys.exit(0)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Fatal error: {e}")
        sys.exit(1) 