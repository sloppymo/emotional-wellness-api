#!/usr/bin/env python3
"""Quick debug utilities for development"""

import asyncio
import sys
import os

# Add src to path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_crisis_detection():
    """Test crisis detection with sample text"""
    print("🧠 Testing Crisis Detection")
    print("=" * 30)
    
    async def run_test():
        try:
            from symbolic.crisis.vectorized_detector import VectorizedCrisisDetector
            detector = VectorizedCrisisDetector()
            
            test_cases = [
                "I want to hurt myself",
                "I'm having a great day",
                "I can't take this anymore",
                "Everything is fine"
            ]
            
            for text in test_cases:
                result = await detector.detect_crisis_patterns(text)
                print(f"Text: '{text}'")
                print(f"  Crisis: {result.detected}")
                print(f"  Severity: {result.severity}")
                print(f"  Confidence: {result.confidence:.2f}")
                print()
                
        except Exception as e:
            print(f"Error: {e}")
    
    asyncio.run(run_test())

def test_database():
    """Test database connection"""
    print("🗄️ Testing Database")
    print("=" * 20)
    
    try:
        from config.settings import get_settings
        settings = get_settings()
        print(f"Database URL: {settings.DATABASE_URL[:30]}...")
        print("✅ Database config loaded")
    except Exception as e:
        print(f"❌ Database error: {e}")

def test_redis():
    """Test Redis connection"""
    print("📦 Testing Redis")
    print("=" * 15)
    
    try:
        from config.settings import get_settings
        settings = get_settings()
        print(f"Redis URL: {settings.REDIS_URL}")
        print("✅ Redis config loaded")
    except Exception as e:
        print(f"❌ Redis error: {e}")

def main():
    """Run all debug tests"""
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        if test_name == "crisis":
            test_crisis_detection()
        elif test_name == "db":
            test_database()
        elif test_name == "redis":
            test_redis()
        else:
            print(f"Unknown test: {test_name}")
    else:
        print("🏥 Debug Utilities")
        print("=" * 20)
        test_database()
        test_redis()
        test_crisis_detection()

if __name__ == "__main__":
    main() 