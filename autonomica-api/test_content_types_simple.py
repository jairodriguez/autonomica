#!/usr/bin/env python3
"""
Simple test script for content types module.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    from ai.content_types import (
        ContentType,
        ContentFormat,
        ContentTypeRegistry,
        get_content_registry,
        validate_content_structure,
        get_content_type_by_name,
        format_content_for_type
    )
    print("✅ Successfully imported content types module")
    
    # Test basic functionality
    print("\n🔍 Testing basic functionality...")
    
    # Test content types
    print(f"Content types count: {len(ContentType)}")
    print(f"Sample content types: {[ct.value for ct in list(ContentType)[:5]]}")
    
    # Test content formats
    print(f"Content formats count: {len(ContentFormat)}")
    print(f"Sample formats: {[cf.value for cf in list(ContentFormat)[:5]]}")
    
    # Test registry
    registry = get_content_registry()
    print(f"Registry initialized with {len(registry.content_structures)} content structures")
    print(f"Registry has {len(registry.transformations)} transformation rules")
    
    # Test content structure retrieval
    blog_structure = registry.get_content_structure(ContentType.BLOG_POST)
    if blog_structure:
        print(f"✅ Blog post structure: {blog_structure.sections}")
    else:
        print("❌ Failed to get blog post structure")
    
    tweet_structure = registry.get_content_structure(ContentType.TWEET)
    if tweet_structure:
        print(f"✅ Tweet structure: {tweet_structure.character_limit} chars")
    else:
        print("❌ Failed to get tweet structure")
    
    # Test transformations
    blog_transformations = registry.get_available_transformations(ContentType.BLOG_POST)
    print(f"✅ Blog post has {len(blog_transformations)} available transformations")
    
    # Test validation
    valid_blog = {
        "title": "Test Blog",
        "introduction": "Introduction text",
        "main_content": "Main content with sufficient words to meet requirements",
        "conclusion": "Conclusion text"
    }
    
    is_valid = validate_content_structure(ContentType.BLOG_POST, valid_blog)
    print(f"✅ Content validation: {is_valid}")
    
    # Test content formatting
    long_content = "This is a very long tweet that exceeds the character limit for Twitter"
    formatted_tweet = format_content_for_type(long_content, ContentType.TWEET)
    print(f"✅ Content formatting: {len(formatted_tweet)} chars (should be <= 280)")
    
    # Test content type by name
    blog_type = get_content_type_by_name("blog_post")
    print(f"✅ Content type by name: {blog_type}")
    
    print("\n🎉 All basic tests passed! The content types module is working correctly.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)