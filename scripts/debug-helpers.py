#!/usr/bin/env python3
"""
Debug helpers for Emotional Wellness API development
Makes debugging and testing easier with pre-built utilities
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List

def test_crisis_detection():
    """Test crisis detection with sample inputs - see if the AI works"""
    print("🧠 Testing Crisis Detection")
    print("=" * 40)
    
    # Sample crisis texts to test
    crisis_texts = [
        "I want to hurt myself",
        "I'm thinking about ending it all", 
        "I can't go on anymore",
        "I'm fine, just having a normal day",  # should be safe
        "I'm feeling a bit down but okay",     # should be low risk
    ]
    
    async def run_tests():
        from src.symbolic.crisis.vectorized_detector import VectorizedCrisisDetector
        detector = VectorizedCrisisDetector()
        
        for text in crisis_texts:
            print(f"\nText: '{text}'")
            result = await detector.detect_crisis_patterns(text)
            print(f"  Crisis: {result.detected}")
            print(f"  Severity: {result.severity}")
            print(f"  Confidence: {result.confidence:.2f}")
            print(f"  Patterns: {result.patterns}")
    
    asyncio.run(run_tests())

def test_symbolic_processing():
    """Test symbolic processing pipeline - see what symbols we get"""
    print("\n🎭 Testing Symbolic Processing")
    print("=" * 40)
    
    # Sample emotional texts
    texts = [
        "I feel like I'm drowning in sadness",
        "I'm walking on sunshine today",
        "My world is falling apart",
        "I'm stuck in a dark tunnel",
        "Everything feels gray and empty"
    ]
    
    async def run_tests():
        from src.symbolic.canopy import get_canopy_processor
        canopy = get_canopy_processor()
        
        for text in texts:
            print(f"\nText: '{text}'")
            try:
                result = await canopy.extract(text, None, None)
                print(f"  Symbol: {result.primary_symbol}")
                print(f"  Archetype: {result.archetype}")
                print(f"  Valence: {result.valence:.2f}")
                print(f"  Arousal: {result.arousal:.2f}")
            except Exception as e:
                print(f"  Error: {e}")
    
    asyncio.run(run_tests())

def test_veluria_protocol():
    """Test VELURIA intervention protocol - see what actions it takes"""
    print("\n🚨 Testing VELURIA Protocol") 
    print("=" * 40)
    
    from src.symbolic.veluria import get_veluria_protocol, VeluriaState
    from src.models.emotional_state import SafetyStatus
    
    veluria = get_veluria_protocol()
    
    # Test different safety levels
    safety_levels = [
        (0, "safe - just checking in"),
        (1, "mild concern - feeling down"),
        (2, "moderate concern - having bad thoughts"),
        (3, "crisis - immediate danger")
    ]
    
    for level, description in safety_levels:
        print(f"\nLevel {level}: {description}")
        
        safety_status = SafetyStatus(
            level=level,
            risk_score=level * 0.3,
            metaphor_risk=level * 0.25,
            triggers=[f"trigger_{level}"],
            recommended_actions=[f"action_{level}"]
        )
        
        intervention = veluria.execute_protocol(
            user_id="test_user",
            safety_status=safety_status
        )
        
        print(f"  Actions: {intervention.actions_taken}")
        print(f"  Resources: {intervention.resources_provided}")
        print(f"  State: {intervention.state_after}")

def test_auth_system():
    """Test authentication system - make sure security works"""
    print("\n🔐 Testing Authentication")
    print("=" * 40)
    
    from src.security.auth import create_access_token, get_api_key
    from datetime import timedelta
    
    # Test token creation
    test_data = {"sub": "test_user", "scopes": ["emotional_processing"]}
    token = create_access_token(test_data, timedelta(minutes=30))
    print(f"Generated token: {token[:50]}...")
    
    # Test API key validation (would need actual request context in real use)
    print("API key validation requires request context")

def check_database_connection():
    """Check if database is accessible"""
    print("\n🗄️  Checking Database Connection")
    print("=" * 40)
    
    try:
        from src.config.settings import get_settings
        settings = get_settings()
        print(f"Database URL: {settings.DATABASE_URL[:30]}...")
        
        # Try to connect (simplified check)
        import sqlalchemy
        engine = sqlalchemy.create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(sqlalchemy.text("SELECT 1"))
            print("✅ Database connection successful")
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

def check_redis_connection():
    """Check if Redis is accessible"""
    print("\n📦 Checking Redis Connection")
    print("=" * 40)
    
    try:
        from src.config.settings import get_settings
        import redis
        
        settings = get_settings()
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        print("✅ Redis connection successful")
        
        # Test basic operations
        r.set("test_key", "test_value")
        value = r.get("test_key")
        print(f"Test value: {value.decode() if value else 'None'}")
        r.delete("test_key")
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")

def generate_test_data():
    """Generate sample test data for development"""
    print("\n🧪 Generating Test Data")
    print("=" * 40)
    
    sample_data = {
        "emotional_states": [
            {
                "user_id": "test_user_1",
                "text": "I'm feeling really anxious about work",
                "valence": -0.3,
                "arousal": 0.7
            },
            {
                "user_id": "test_user_2", 
                "text": "Having a great day with friends",
                "valence": 0.8,
                "arousal": 0.6
            }
        ],
        "crisis_scenarios": [
            {
                "text": "I can't take this anymore",
                "expected_level": 2
            },
            {
                "text": "I want to hurt myself",
                "expected_level": 3
            }
        ]
    }
    
    with open("tmp/test_data.json", "w") as f:
        json.dump(sample_data, f, indent=2)
    
    print("✅ Test data generated in tmp/test_data.json")

def main():
    """Run all debug tests"""
    print("🏥 Emotional Wellness API - Debug Helper")
    print("=" * 50)
    
    # Check connections first
    check_database_connection()
    check_redis_connection()
    
    # Test core functionality
    test_crisis_detection()
    test_symbolic_processing()
    test_veluria_protocol()
    test_auth_system()
    
    # Generate test data
    generate_test_data()
    
    print("\n🎉 Debug tests complete!")
    print("\nUseful commands:")
    print("  python scripts/debug-helpers.py          - Run all tests")
    print("  make test-crisis                         - Run crisis tests")
    print("  make debug-crisis                        - Quick crisis debug")

if __name__ == "__main__":
    main() 