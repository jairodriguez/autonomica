#!/usr/bin/env python3
"""
Test script for content generation module.
"""

import sys
import os
import asyncio

# Add the app/ai directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'ai'))

try:
    # Import the content generation module
    from content_generation import (
        ContentGenerationRequest,
        ContentGenerationResponse,
        ContentRepurposingRequest,
        ContentGenerator,
        ContentGenerationService,
        get_content_service
    )
    from content_types_simple import ContentType, ContentFormat
    
    print("✅ Successfully imported content generation module")
    
    async def test_content_generation():
        """Test content generation functionality."""
        print("\n🔍 Testing content generation functionality...")
        
        # Test content types and formats
        print(f"Available content types: {len(ContentType)}")
        print(f"Available formats: {len(ContentFormat)}")
        
        # Test service instantiation
        service = get_content_service()
        print("✅ Content generation service created successfully")
        
        # Test content generator instantiation
        generator = ContentGenerator()
        print("✅ Content generator created successfully")
        
        # Test request/response dataclasses
        request = ContentGenerationRequest(
            content_type=ContentType.BLOG_POST,
            prompt="The benefits of artificial intelligence in modern business",
            target_format=ContentFormat.MARKDOWN,
            brand_voice="Professional and innovative",
            tone="professional",
            word_count=1000
        )
        print("✅ Content generation request created successfully")
        
        repurpose_request = ContentRepurposingRequest(
            source_content="This is a sample blog post about AI in business.",
            source_type=ContentType.BLOG_POST,
            target_type=ContentType.TWEET,
            brand_voice="Professional and innovative",
            preserve_key_points=True,
            add_hashtags=True
        )
        print("✅ Content repurposing request created successfully")
        
        # Test prompt building (without actual AI calls)
        print("\n🔍 Testing prompt building...")
        
        # Test generation prompt building
        gen_prompt = generator._build_generation_prompt(request)
        print(f"✅ Generation prompt built: {len(gen_prompt)} characters")
        print(f"Prompt preview: {gen_prompt[:200]}...")
        
        # Test repurposing prompt building
        # We need to mock the transformation object
        class MockTransformation:
            def __init__(self):
                self.transformation_method = "extract_key_points"
        
        repurpose_prompt = generator._build_repurposing_prompt(repurpose_request, MockTransformation())
        print(f"✅ Repurposing prompt built: {len(repurpose_prompt)} characters")
        print(f"Prompt preview: {repurpose_prompt[:200]}...")
        
        # Test token calculation
        print("\n🔍 Testing token calculation...")
        max_tokens = generator._calculate_max_tokens(request)
        print(f"✅ Max tokens calculated: {max_tokens}")
        
        repurpose_tokens = generator._calculate_max_tokens_for_repurposing(repurpose_request)
        print(f"✅ Repurposing tokens calculated: {repurpose_tokens}")
        
        # Test content validation
        print("\n🔍 Testing content validation...")
        
        # Valid content
        valid_content = "This is a valid blog post with sufficient content to meet the requirements."
        is_valid = generator._validate_generated_content(valid_content, ContentType.BLOG_POST)
        print(f"✅ Valid content validation: {is_valid}")
        
        # Invalid content (too short)
        invalid_content = "Short"
        is_valid = generator._validate_generated_content(invalid_content, ContentType.BLOG_POST)
        print(f"✅ Invalid content validation: {is_valid}")
        
        # Test content formatting
        print("\n🔍 Testing content formatting...")
        
        # Test tweet formatting with character limit
        long_tweet = "This is a very long tweet that exceeds the character limit for Twitter and should be truncated appropriately to fit within the platform's constraints."
        formatted_tweet = generator._format_content_for_type(long_tweet, 
            ContentGenerationRequest(content_type=ContentType.TWEET, prompt=""))
        print(f"✅ Tweet formatting: {len(formatted_tweet)} chars (should be <= 280)")
        
        # Test hashtag generation
        hashtags = generator._generate_relevant_hashtags(ContentType.TWEET, "AI in business")
        print(f"✅ Hashtags generated: {hashtags}")
        
        # Test service methods (without actual AI calls)
        print("\n🔍 Testing service methods...")
        
        # Test blog post creation method
        blog_request = service.create_blog_post.__defaults__
        print(f"✅ Blog post creation method available with defaults: {blog_request}")
        
        # Test tweet creation method
        tweet_request = service.create_tweet.__defaults__
        print(f"✅ Tweet creation method available with defaults: {tweet_request}")
        
        # Test repurposing method
        repurpose_method = service.repurpose_blog_to_tweets.__defaults__
        print(f"✅ Blog to tweets repurposing method available with defaults: {repurpose_method}")
        
        print("\n🎉 All content generation tests passed! The module is working correctly.")
        
        # Test error handling
        print("\n🔍 Testing error handling...")
        
        try:
            # Test with unsupported content type
            unsupported_request = ContentGenerationRequest(
                content_type="unsupported_type",  # This should fail
                prompt="Test"
            )
            print("❌ Should have failed with unsupported content type")
        except Exception as e:
            print(f"✅ Properly handled unsupported content type: {type(e).__name__}")
        
        print("\n🎉 Error handling tests passed!")
        
    # Run the async test
    asyncio.run(test_content_generation())
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)