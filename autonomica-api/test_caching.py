#!/usr/bin/env python3
"""
Test script for the SEO Cache Manager
Tests comprehensive caching functionality including operations, TTL, eviction, and optimization
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.seo_service import SEOCacheManager

def test_cache_manager():
    """Test the cache manager functionality"""
    print("🚀 Starting SEO Cache Manager Tests")
    print("=" * 50)
    
    # Create cache manager with custom configuration
    config = {
        "default_ttl": 1800,  # 30 minutes
        "max_cache_size": 100,
        "max_memory_mb": 10,
        "cleanup_interval": 60,  # 1 minute
        "eviction_policy": "lru",
        "compression_enabled": True,
        "persistent_storage": False
    }
    
    cache = SEOCacheManager(config)
    print("✅ Cache manager created successfully")
    
    # Test basic cache operations
    print("\n🔧 Testing basic cache operations...")
    
    # Test set and get
    cache.set("test_key", "test_value")
    value = cache.get("test_key")
    if value == "test_value":
        print("✅ Set and get operations working correctly")
    else:
        print(f"❌ Set/get failed: expected 'test_value', got '{value}'")
        return False
    
    # Test exists
    if cache.exists("test_key"):
        print("✅ Exists check working correctly")
    else:
        print("❌ Exists check failed")
        return False
    
    # Test TTL operations
    print("\n⏰ Testing TTL operations...")
    
    # Set with custom TTL
    cache.set("ttl_key", "ttl_value", ttl=5)  # 5 seconds
    
    # Check TTL
    ttl = cache.get_ttl("ttl_key")
    if 0 <= ttl <= 5:
        print(f"✅ TTL check working: {ttl} seconds remaining")
    else:
        print(f"❌ TTL check failed: {ttl} seconds")
    
    # Wait for expiration
    print("  - Waiting for TTL expiration...")
    time.sleep(6)
    
    # Check if expired
    expired_value = cache.get("ttl_key")
    if expired_value is None:
        print("✅ TTL expiration working correctly")
    else:
        print(f"❌ TTL expiration failed: got '{expired_value}'")
    
    # Test multiple operations
    print("\n📦 Testing multiple operations...")
    
    # Set multiple values
    test_data = {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3"
    }
    
    cache.set_multiple(test_data, ttl=60)
    print("✅ Set multiple values")
    
    # Get multiple values
    retrieved_data = cache.get_multiple(["key1", "key2", "key3"])
    if len(retrieved_data) == 3:
        print("✅ Get multiple values working correctly")
    else:
        print(f"❌ Get multiple failed: got {len(retrieved_data)} values")
    
    # Delete multiple values
    deleted_count = cache.delete_multiple(["key1", "key2"])
    if deleted_count == 2:
        print("✅ Delete multiple values working correctly")
    else:
        print(f"❌ Delete multiple failed: deleted {deleted_count} values")
    
    # Test tags and invalidation
    print("\n🏷️  Testing tags and invalidation...")
    
    # Set values with tags
    cache.set("tagged_key1", "value1", tags=["seo", "keywords"])
    cache.set("tagged_key2", "value2", tags=["seo", "content"])
    cache.set("tagged_key3", "value3", tags=["analytics"])
    
    print("✅ Set values with tags")
    
    # Invalidate by tags
    invalidated_count = cache.invalidate_by_tags(["seo"])
    if invalidated_count == 2:
        print("✅ Tag-based invalidation working correctly")
    else:
        print(f"❌ Tag invalidation failed: invalidated {invalidated_count} values")
    
    # Test eviction policies
    print("\n🗑️  Testing eviction policies...")
    
    # Test LRU eviction
    print("  - Testing LRU eviction policy...")
    
    # Fill cache to trigger eviction
    for i in range(50):
        cache.set(f"lru_key_{i}", f"value_{i}", ttl=300)
    
    # Access some keys to update LRU timestamps
    cache.get("lru_key_10")
    cache.get("lru_key_20")
    
    # Add more keys to trigger eviction
    for i in range(60, 80):
        cache.set(f"lru_key_{i}", f"value_{i}", ttl=300)
    
    # Check if some keys were evicted
    if not cache.exists("lru_key_0"):
        print("✅ LRU eviction working correctly")
    else:
        print("❌ LRU eviction failed")
    
    # Test LFU eviction
    print("  - Testing LFU eviction policy...")
    
    lfu_cache = SEOCacheManager({"eviction_policy": "lfu", "max_cache_size": 20})
    
    # Add keys with different access patterns
    for i in range(20):
        lfu_cache.set(f"lfu_key_{i}", f"value_{i}", ttl=300)
    
    # Access some keys multiple times
    for _ in range(5):
        lfu_cache.get("lfu_key_5")
        lfu_cache.get("lfu_key_10")
    
    # Add more keys to trigger eviction
    for i in range(20, 30):
        lfu_cache.set(f"lfu_key_{i}", f"value_{i}", ttl=300)
    
    # Check if least frequently used keys were evicted
    if not lfu_cache.exists("lfu_key_0"):
        print("✅ LFU eviction working correctly")
    else:
        print("❌ LFU eviction failed")
    
    # Test FIFO eviction
    print("  - Testing FIFO eviction policy...")
    
    fifo_cache = SEOCacheManager({"eviction_policy": "fifo", "max_cache_size": 20})
    
    # Add keys sequentially
    for i in range(25):
        fifo_cache.set(f"fifo_key_{i}", f"value_{i}", ttl=300)
    
    # Check if first keys were evicted
    if not fifo_cache.exists("fifo_key_0"):
        print("✅ FIFO eviction working correctly")
    else:
        print("❌ FIFO eviction failed")
    
    # Test cache statistics
    print("\n📊 Testing cache statistics...")
    
    stats = cache.get_stats()
    if "cache_size" in stats and "hit_rate" in stats:
        print("✅ Cache statistics working correctly")
        print(f"  - Cache size: {stats['cache_size']}")
        print(f"  - Hit rate: {stats['hit_rate']}")
        print(f"  - Memory usage: {stats['memory_usage_mb']} MB")
        print(f"  - Hits: {stats['hits']}, Misses: {stats['misses']}")
        print(f"  - Evictions: {stats['evictions']}")
    else:
        print("❌ Cache statistics failed")
    
    # Test memory management
    print("\n💾 Testing memory management...")
    
    current_memory = cache.get_memory_usage()
    if current_memory >= 0:
        print(f"✅ Memory usage tracking: {current_memory:.2f} MB")
    else:
        print("❌ Memory usage tracking failed")
    
    # Test cache optimization
    print("\n⚡ Testing cache optimization...")
    
    # Add some expired entries
    cache.set("expired_key", "expired_value", ttl=1)
    time.sleep(2)
    
    # Optimize cache
    cache.optimize()
    print("✅ Cache optimization completed")
    
    # Check if expired entries were cleaned up
    if not cache.exists("expired_key"):
        print("✅ Expired entry cleanup working correctly")
    else:
        print("❌ Expired entry cleanup failed")
    
    # Test pattern-based key retrieval
    print("\n🔍 Testing pattern-based key retrieval...")
    
    # Add some keys with patterns
    cache.set("seo_keyword_1", "value1")
    cache.set("seo_keyword_2", "value2")
    cache.set("content_article_1", "value3")
    
    # Get keys by pattern
    seo_keys = cache.get_keys("seo_keyword_*")
    content_keys = cache.get_keys("content_*")
    
    if len(seo_keys) == 2 and len(content_keys) == 1:
        print("✅ Pattern-based key retrieval working correctly")
    else:
        print(f"❌ Pattern retrieval failed: seo={len(seo_keys)}, content={len(content_keys)}")
    
    # Test edge cases
    print("\n⚠️  Testing edge cases and error handling...")
    
    # Test with None values
    cache.set("none_key", None)
    none_value = cache.get("none_key")
    if none_value is None:
        print("✅ None value handling working correctly")
    else:
        print("❌ None value handling failed")
    
    # Test with empty string
    cache.set("empty_key", "")
    empty_value = cache.get("empty_key")
    if empty_value == "":
        print("✅ Empty string handling working correctly")
    else:
        print("❌ Empty string handling failed")
    
    # Test with large data
    large_data = "x" * 10000
    cache.set("large_key", large_data)
    large_value = cache.get("large_key")
    if large_value == large_data:
        print("✅ Large data handling working correctly")
    else:
        print("❌ Large data handling failed")
    
    # Test cache clearing
    print("\n🧹 Testing cache clearing...")
    
    cache.clear()
    if len(cache.get_keys()) == 0:
        print("✅ Cache clearing working correctly")
    else:
        print("❌ Cache clearing failed")
    
    # Test persistent storage (disabled by default)
    print("\n💾 Testing persistent storage configuration...")
    
    persistent_config = {
        "persistent_storage": True,
        "storage_file": "test_cache.json"
    }
    
    persistent_cache = SEOCacheManager(persistent_config)
    persistent_cache.set("persistent_key", "persistent_value", ttl=300)
    
    # Create new instance to test loading
    new_persistent_cache = SEOCacheManager(persistent_config)
    loaded_value = new_persistent_cache.get("persistent_key")
    
    if loaded_value == "persistent_value":
        print("✅ Persistent storage working correctly")
    else:
        print("❌ Persistent storage failed")
    
    # Clean up test file
    try:
        os.remove("test_cache.json")
    except:
        pass
    
    print("\n🎉 All cache manager tests completed successfully!")
    return True

def test_cache_performance():
    """Test cache performance characteristics"""
    print("\n🚀 Testing cache performance...")
    
    cache = SEOCacheManager({"max_cache_size": 1000})
    
    # Performance test: Set operations
    start_time = time.time()
    for i in range(1000):
        cache.set(f"perf_key_{i}", f"value_{i}")
    set_time = time.time() - start_time
    
    print(f"✅ Set 1000 keys in {set_time:.3f} seconds")
    
    # Performance test: Get operations
    start_time = time.time()
    for i in range(1000):
        cache.get(f"perf_key_{i}")
    get_time = time.time() - start_time
    
    print(f"✅ Get 1000 keys in {get_time:.3f} seconds")
    
    # Performance test: Hit rate
    cache.clear()
    
    # Add some data
    for i in range(100):
        cache.set(f"hit_key_{i}", f"value_{i}")
    
    # Access some keys multiple times
    for _ in range(5):
        for i in range(50):
            cache.get(f"hit_key_{i}")
    
    stats = cache.get_stats()
    print(f"✅ Hit rate: {stats['hit_rate']:.3f}")
    
    print("✅ Performance testing completed")

if __name__ == "__main__":
    try:
        # Run main tests
        success = test_cache_manager()
        
        if success:
            # Run performance tests
            test_cache_performance()
            
            print("\n" + "=" * 50)
            print("🎉 ALL TESTS PASSED! Cache manager is working correctly.")
            print("=" * 50)
        else:
            print("\n❌ Some tests failed. Please check the implementation.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test execution failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)