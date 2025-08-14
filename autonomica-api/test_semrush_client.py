#!/usr/bin/env python3
"""
Test script for SEMrush API client functionality.

This script tests the SEMrush client without requiring actual API keys,
focusing on the client structure and error handling.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.services.semrush_client import (
    SEMrushClient, 
    KeywordData, 
    DomainData, 
    CompetitorData,
    SEMrushAPIError,
    SEMrushAuthenticationError,
    SEMrushRateLimitError
)


async def test_client_initialization():
    """Test client initialization with and without API key."""
    print("Testing client initialization...")
    
    # Test without API key (should raise error)
    try:
        client = SEMrushClient(api_key="")
        print("❌ Should have raised error for empty API key")
    except ValueError as e:
        print(f"✅ Correctly raised error for empty API key: {e}")
    
    # Test with dummy API key
    try:
        client = SEMrushClient(api_key="dummy_key_for_testing")
        print("✅ Client initialized with dummy API key")
        return client
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return None


async def test_data_models():
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


async def test_csv_parsing():
    """Test CSV response parsing functionality."""
    print("\nTesting CSV parsing...")
    
    client = SEMrushClient(api_key="dummy_key")
    
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


async def test_rate_limiting():
    """Test rate limiting functionality."""
    print("\nTesting rate limiting...")
    
    client = SEMrushClient(api_key="dummy_key")
    
    # Test rate limit status
    try:
        rate_limit = await client.get_rate_limit_status()
        print("✅ Rate limit status retrieved")
        print(f"   Requests remaining: {rate_limit['requests_remaining']}")
        print(f"   Daily limit: {rate_limit['daily_limit']}")
    except Exception as e:
        print(f"❌ Rate limit status failed: {e}")


async def test_error_handling():
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


async def test_client_context_manager():
    """Test async context manager functionality."""
    print("\nTesting async context manager...")
    
    try:
        async with SEMrushClient(api_key="dummy_key") as client:
            print("✅ Context manager entered successfully")
            print(f"   Session created: {client.session is not None}")
    except Exception as e:
        print(f"❌ Context manager failed: {e}")


async def test_methods_structure():
    """Test that all required methods exist and are callable."""
    print("\nTesting method structure...")
    
    client = SEMrushClient(api_key="dummy_key")
    
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


async def main():
    """Run all tests."""
    print("🧪 SEMrush Client Test Suite")
    print("=" * 50)
    
    # Run all tests
    await test_client_initialization()
    await test_data_models()
    await test_csv_parsing()
    await test_rate_limiting()
    await test_error_handling()
    await test_client_context_manager()
    await test_methods_structure()
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")
    
    # Summary
    print("\n📋 Test Summary:")
    print("   - Client initialization and configuration")
    print("   - Pydantic data models")
    print("   - CSV response parsing")
    print("   - Rate limiting functionality")
    print("   - Error handling and custom exceptions")
    print("   - Async context manager")
    print("   - Method structure validation")


if __name__ == "__main__":
    # Set environment variable for testing
    os.environ["SEMRUSH_API_KEY"] = "dummy_key_for_testing"
    
    # Run tests
    asyncio.run(main())