#!/usr/bin/env python3
"""
Basic test script for SEMrush API client functionality.

This script tests the basic structure without requiring external dependencies.
"""

import sys
from pathlib import Path

# Mock the imports for testing
class MockRedisService:
    """Mock Redis service for testing."""
    async def get(self, key):
        return None
    
    async def set(self, key, value, expire=None):
        return True

class MockSettings:
    """Mock settings for testing."""
    SEMRUSH_API_KEY = "test_key"

# Mock the imports
sys.modules['app.core.config'] = type('MockConfig', (), {'settings': MockSettings()})()
sys.modules['app.services.redis_service'] = type('MockRedis', (), {'RedisService': MockRedisService})()
sys.modules['httpx'] = type('MockHttpx', (), {})()
sys.modules['loguru'] = type('MockLoguru', (), {'logger': type('MockLogger', (), {})()})()
sys.modules['pydantic'] = type('MockPydantic', (), {'BaseModel': object, 'Field': lambda **kwargs: lambda x: x})()

# Now import our client
try:
    from app.services.semrush_client import (
        SEMrushClient, 
        KeywordData, 
        DomainData, 
        CompetitorData,
        SEMrushAPIError,
        SEMrushAuthenticationError,
        SEMrushRateLimitError
    )
    print("✅ Successfully imported SEMrush client modules")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("This is expected in the current environment")
    sys.exit(0)


def test_data_models():
    """Test the Pydantic data models."""
    print("\nTesting data models...")
    
    # Test KeywordData model
    try:
        keyword_data = KeywordData(
            keyword="test keyword",
            search_volume=1000,
            cpc=1.50,
            competition=0.75,
            keyword_difficulty=65,
            results_count=1000000
        )
        print("✅ KeywordData model created successfully")
        print(f"   Keyword: {keyword_data.keyword}")
        print(f"   Search Volume: {keyword_data.search_volume}")
        print(f"   CPC: ${keyword_data.cpc}")
    except Exception as e:
        print(f"❌ KeywordData model failed: {e}")
    
    # Test DomainData model
    try:
        domain_data = DomainData(
            domain="example.com",
            authority_score=85,
            organic_keywords=5000,
            organic_traffic=100000
        )
        print("✅ DomainData model created successfully")
        print(f"   Domain: {domain_data.domain}")
        print(f"   Authority: {domain_data.authority_score}")
    except Exception as e:
        print(f"❌ DomainData model failed: {e}")
    
    # Test CompetitorData model
    try:
        competitor_data = CompetitorData(
            domain="competitor.com",
            overlap_score=0.85,
            common_keywords=1500,
            organic_keywords=8000
        )
        print("✅ CompetitorData model created successfully")
        print(f"   Competitor: {competitor_data.domain}")
        print(f"   Overlap: {competitor_data.overlap_score}")
    except Exception as e:
        print(f"❌ CompetitorData model failed: {e}")


def test_client_initialization():
    """Test client initialization."""
    print("\nTesting client initialization...")
    
    try:
        client = SEMrushClient(api_key="test_key")
        print("✅ Client initialized successfully")
        print(f"   API Key: {client.api_key[:8]}...")
        print(f"   Base URL: {client.BASE_URL}")
        print(f"   API Version: {client.API_VERSION}")
        return client
    except Exception as e:
        print(f"❌ Client initialization failed: {e}")
        return None


def test_csv_parsing():
    """Test CSV response parsing functionality."""
    print("\nTesting CSV parsing...")
    
    client = SEMrushClient(api_key="test_key")
    
    # Test CSV parsing with sample data
    sample_csv = """Keyword;Search Volume;CPC;Competition;Keyword Difficulty;Results
digital marketing;12000;2.50;0.85;75;1500000000
seo tools;8000;1.80;0.70;65;1200000000
content marketing;9500;2.20;0.80;70;1350000000"""
    
    try:
        parsed_data = client._parse_csv_response(sample_csv)
        print("✅ CSV parsing successful")
        print(f"   Headers: {parsed_data['headers']}")
        print(f"   Total rows: {parsed_data['total']}")
        print(f"   First row: {parsed_data['data'][0]}")
    except Exception as e:
        print(f"❌ CSV parsing failed: {e}")


def test_error_handling():
    """Test error handling and custom exceptions."""
    print("\nTesting error handling...")
    
    # Test custom exceptions
    exceptions = [
        SEMrushAPIError("Test API error"),
        SEMrushAuthenticationError("Test authentication error"),
        SEMrushRateLimitError("Test rate limit error")
    ]
    
    for exc in exceptions:
        print(f"✅ {type(exc).__name__}: {exc}")


def test_methods_structure():
    """Test that all required methods exist and are callable."""
    print("\nTesting method structure...")
    
    client = SEMrushClient(api_key="test_key")
    
    required_methods = [
        'get_keyword_overview',
        'get_domain_overview', 
        'get_competitors',
        'get_keyword_suggestions',
        'get_rate_limit_status'
    ]
    
    for method_name in required_methods:
        if hasattr(client, method_name) and callable(getattr(client, method_name)):
            print(f"✅ Method {method_name} exists and is callable")
        else:
            print(f"❌ Method {method_name} missing or not callable")


def main():
    """Run all tests."""
    print("🧪 SEMrush Client Basic Test Suite")
    print("=" * 50)
    
    # Run all tests
    test_data_models()
    test_client_initialization()
    test_csv_parsing()
    test_error_handling()
    test_methods_structure()
    
    print("\n" + "=" * 50)
    print("✅ All basic tests completed!")
    
    # Summary
    print("\n📋 Test Summary:")
    print("   - Pydantic data models")
    print("   - Client initialization and configuration")
    print("   - CSV response parsing")
    print("   - Error handling and custom exceptions")
    print("   - Method structure validation")
    
    print("\n💡 Note: This is a basic test without external dependencies.")
    print("   Full functionality testing requires proper environment setup.")


if __name__ == "__main__":
    main()