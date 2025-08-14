#!/usr/bin/env python3
"""
Test script for enhanced content generation module with templates.
"""

import sys
import os
import asyncio

# Add the app/ai directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'ai'))

try:
    # Import the enhanced modules
    from content_generation import (
        ContentGenerationRequest, ContentGenerationResponse, ContentRepurposingRequest,
        ContentGenerator, ContentGenerationService, get_content_service
    )
    from content_types_simple import ContentType, ContentFormat
    from content_templates import ContentTemplates, ContentTemplateEngine, get_template_engine
    
    print("✅ Successfully imported enhanced content generation modules")
    
    async def test_enhanced_content_generation():
        """Test enhanced content generation functionality with templates."""
        print("\n🔍 Testing enhanced content generation functionality...")
        
        # Test template engine
        template_engine = get_template_engine()
        print("✅ Template engine created successfully")
        
        # Test content templates
        templates = ContentTemplates()
        print("✅ Content templates created successfully")
        
        # Test template retrieval
        blog_template = templates.get_blog_post_template()
        print(f"✅ Blog post template retrieved: {len(blog_template)} characters")
        print(f"Template preview: {blog_template[:100]}...")
        
        tweet_template = templates.get_tweet_template()
        print(f"✅ Tweet template retrieved: {len(tweet_template)} characters")
        
        # Test formatting instructions
        blog_instructions = templates.get_formatting_instructions(ContentType.BLOG_POST, ContentFormat.MARKDOWN)
        print(f"✅ Blog formatting instructions retrieved: {len(blog_instructions)} characters")
        
        tweet_instructions = templates.get_formatting_instructions(ContentType.TWEET, ContentFormat.PLAIN_TEXT)
        print(f"✅ Tweet formatting instructions retrieved: {len(tweet_instructions)} characters")
        
        # Test quality checklists
        blog_checklist = templates.get_quality_checklist(ContentType.BLOG_POST)
        print(f"✅ Blog quality checklist retrieved: {len(blog_checklist)} items")
        
        tweet_checklist = templates.get_quality_checklist(ContentType.TWEET)
        print(f"✅ Tweet quality checklist retrieved: {len(tweet_checklist)} items")
        
        # Test brand voice guidelines
        brand_voices = templates.get_brand_voice_guidelines()
        print(f"✅ Brand voice guidelines retrieved: {len(brand_voices)} voices")
        
        # Test tone modifiers
        tone_modifiers = templates.get_tone_modifiers()
        print(f"✅ Tone modifiers retrieved: {len(tone_modifiers)} tones")
        
        # Test template application
        print("\n🔍 Testing template application...")
        
        # Test section extraction
        sample_content = """
        Introduction: This is an introduction to AI in business.
        
        Main Content: AI is transforming how businesses operate.
        
        Conclusion: AI will continue to shape the future of business.
        """
        
        sections = template_engine._extract_sections(sample_content, ContentType.BLOG_POST)
        print(f"✅ Sections extracted: {list(sections.keys())}")
        
        # Test template application
        applied_template = template_engine.apply_template(
            sample_content, 
            ContentType.BLOG_POST, 
            ContentFormat.MARKDOWN,
            title="AI in Business"
        )
        print(f"✅ Template applied: {len(applied_template)} characters")
        print(f"Applied template preview: {applied_template[:200]}...")
        
        # Test enhanced prompt generation
        print("\n🔍 Testing enhanced prompt generation...")
        
        base_prompt = "Write about artificial intelligence in business"
        enhanced_prompt = template_engine.get_enhanced_prompt(
            base_prompt, 
            ContentType.BLOG_POST, 
            ContentFormat.MARKDOWN
        )
        print(f"✅ Enhanced prompt generated: {len(enhanced_prompt)} characters")
        print(f"Enhanced prompt preview: {enhanced_prompt[:300]}...")
        
        # Test content generation with enhanced prompts
        print("\n🔍 Testing content generation with enhanced prompts...")
        
        generator = ContentGenerator()
        print("✅ Content generator created successfully")
        
        # Test blog post generation request
        blog_request = ContentGenerationRequest(
            content_type=ContentType.BLOG_POST,
            prompt="The benefits of artificial intelligence in modern business",
            target_format=ContentFormat.MARKDOWN,
            brand_voice="Professional and innovative",
            tone="professional",
            word_count=1000
        )
        print("✅ Blog post generation request created successfully")
        
        # Test prompt building with templates
        enhanced_prompt = generator._build_generation_prompt(blog_request)
        print(f"✅ Enhanced prompt built: {len(enhanced_prompt)} characters")
        print(f"Enhanced prompt preview: {enhanced_prompt[:400]}...")
        
        # Test tweet generation request
        tweet_request = ContentGenerationRequest(
            content_type=ContentType.TWEET,
            prompt="AI transforming business operations",
            target_format=ContentFormat.PLAIN_TEXT,
            brand_voice="Innovative and forward-thinking",
            tone="conversational",
            include_hashtags=True
        )
        print("✅ Tweet generation request created successfully")
        
        # Test prompt building for tweet
        tweet_prompt = generator._build_generation_prompt(tweet_request)
        print(f"✅ Tweet prompt built: {len(tweet_prompt)} characters")
        print(f"Tweet prompt preview: {tweet_prompt[:300]}...")
        
        # Test video script generation request
        video_request = ContentGenerationRequest(
            content_type=ContentType.VIDEO_SCRIPT,
            prompt="How AI is changing business",
            target_format=ContentFormat.PLAIN_TEXT,
            brand_voice="Expert and engaging",
            tone="conversational",
            word_count=500
        )
        print("✅ Video script generation request created successfully")
        
        # Test prompt building for video script
        video_prompt = generator._build_generation_prompt(video_request)
        print(f"✅ Video script prompt built: {len(video_prompt)} characters")
        print(f"Video script prompt preview: {video_prompt[:400]}...")
        
        # Test content repurposing with templates
        print("\n🔍 Testing content repurposing with templates...")
        
        repurpose_request = ContentRepurposingRequest(
            source_content="This is a comprehensive blog post about artificial intelligence transforming business operations.",
            source_type=ContentType.BLOG_POST,
            target_type=ContentType.TWEET_THREAD,
            brand_voice="Professional and innovative",
            preserve_key_points=True,
            add_hashtags=True
        )
        print("✅ Content repurposing request created successfully")
        
        # Test repurposing prompt building
        class MockTransformation:
            def __init__(self):
                self.transformation_method = "summarize_sections"
        
        repurpose_prompt = generator._build_repurposing_prompt(repurpose_request, MockTransformation())
        print(f"✅ Repurposing prompt built: {len(repurpose_prompt)} characters")
        print(f"Repurposing prompt preview: {repurpose_prompt[:400]}...")
        
        # Test service layer
        print("\n🔍 Testing service layer...")
        
        service = get_content_service()
        print("✅ Content generation service created successfully")
        
        # Test service method availability
        methods = [method for method in dir(service) if not method.startswith('_')]
        print(f"✅ Service methods available: {len(methods)} methods")
        print(f"Service methods: {', '.join(methods[:5])}...")
        
        print("\n🎉 All enhanced content generation tests passed! The module with templates is working correctly.")
        
    # Run the async test
    asyncio.run(test_enhanced_content_generation())
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)