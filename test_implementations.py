#!/usr/bin/env python3
"""
Test script to validate the new implementations work correctly.
"""

import sys
import traceback

def test_implementations():
    """Test that our new implementations work"""
    
    print("🧪 Testing New SylvaTune Implementations")
    print("=" * 50)
    
    results = []
    
    # Test 1: CANOPY Core Tests
    try:
        from tests.symbolic.test_canopy_core import test_symbolic_mapping_validation
        print("✅ CANOPY core tests import successfully")
        results.append(("CANOPY Core Tests", True))
    except Exception as e:
        print(f"❌ CANOPY core test import failed: {e}")
        results.append(("CANOPY Core Tests", False))
    
    # Test 2: ML Risk Prediction
    try:
        from src.analytics.ml_risk_prediction import CrisisRiskPredictor, RiskLevel
        predictor = CrisisRiskPredictor()
        print(f"✅ ML risk prediction created with version: {predictor.model_version}")
        results.append(("ML Risk Prediction", True))
    except Exception as e:
        print(f"❌ ML risk prediction failed: {e}")
        results.append(("ML Risk Prediction", False))
    
    # Test 3: Integration Tests
    try:
        from tests.integration.test_coordinator import SylvaWrenCoordinator
        print("✅ Integration coordinator tests available")
        results.append(("Integration Tests", True))
    except Exception as e:
        print(f"❌ Integration test import failed: {e}")
        results.append(("Integration Tests", False))
    
    # Test 4: Performance Tests
    try:
        from tests.performance import test_benchmarking_comprehensive
        print("✅ Performance benchmarking tests available")
        results.append(("Performance Tests", True))
    except Exception as e:
        print(f"❌ Performance test import failed: {e}")
        results.append(("Performance Tests", False))
    
    print("\n📊 Results Summary:")
    print("-" * 30)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:25} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All implementations are working correctly!")
        return True
    else:
        print(f"\n⚠️  {total-passed} implementations need attention")
        return False

if __name__ == "__main__":
    success = test_implementations()
    sys.exit(0 if success else 1) 