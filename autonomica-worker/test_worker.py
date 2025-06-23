#!/usr/bin/env python3
"""
Simple test script for the Autonomica Worker Pod
"""

import asyncio
import requests
import time
from loguru import logger

async def test_worker_health():
    """Test the worker health endpoint"""
    try:
        logger.info("🧪 Testing worker health endpoint...")
        response = requests.get("http://localhost:8080/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            logger.success(f"✅ Health check passed: {data}")
            return True
        else:
            logger.error(f"❌ Health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Health check error: {e}")
        return False

async def test_redis_connection():
    """Test Redis connection"""
    try:
        import redis
        logger.info("🧪 Testing Redis connection...")
        
        client = redis.from_url("redis://localhost:6379/0", decode_responses=True)
        client.ping()
        
        # Test set/get
        client.set("test:worker", "hello", ex=60)
        value = client.get("test:worker")
        
        if value == "hello":
            logger.success("✅ Redis connection working")
            return True
        else:
            logger.error("❌ Redis set/get failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Redis connection error: {e}")
        return False

async def main():
    """Run all tests"""
    logger.info("🚀 Starting Autonomica Worker Pod Tests")
    
    tests = [
        ("Worker Health", test_worker_health()),
        ("Redis Connection", test_redis_connection()),
    ]
    
    results = []
    for test_name, test_coro in tests:
        logger.info(f"Running {test_name}...")
        result = await test_coro
        results.append((test_name, result))
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    logger.info("\n📊 Test Results:")
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    total = len(results)
    logger.info(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.success("🎉 All tests passed! Worker pod is ready.")
    else:
        logger.error("💥 Some tests failed. Check the configuration.")

if __name__ == "__main__":
    asyncio.run(main())
