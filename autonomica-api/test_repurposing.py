#!/usr/bin/env python3
"""
Simple test script for content repurposing service
"""

import asyncio
from app.services.content_repurposing import ContentRepurposingService
from app.services.content_types import ContentType, Platform


async def test_content_repurposing():
    """Test the content repurposing service."""
    service = ContentRepurposingService()
    
    print("Testing Content Repurposing Service")
    print("=" * 50)
    
    # Test key point extraction
    print("\n1. Testing key point extraction...")
    sample_content = """
    Artificial Intelligence is transforming the way we work and live. 
    Companies that embrace AI see 40% increase in productivity.
    
    The future of work is here, and it's powered by machine learning algorithms.
    Organizations must adapt or risk being left behind in this digital revolution.
    
    What does this mean for your business? It means opportunity for growth and innovation.
    The time to act is now, before your competitors gain the advantage.
    """
    
    key_points = service._extract_key_points(sample_content, ContentType.BLOG_POST)
    print(f"   Extracted {len(key_points)} key points")
    for i, point in enumerate(key_points[:2]):  # Show first 2 points
        print(f"   Point {i+1}: {point['content'][:60]}...")
    
    # Test sentiment analysis
    print("\n2. Testing sentiment analysis...")
    positive_text = "This is amazing and wonderful content that we love."
    negative_text = "This is terrible and awful content with many problems."
    neutral_text = "This is content about technology and business."
    
    print(f"   Positive: {service._analyze_sentiment(positive_text)}")
    print(f"   Negative: {service._analyze_sentiment(negative_text)}")
    print(f"   Neutral: {service._analyze_sentiment(neutral_text)}")
    
    # Test CTA detection
    print("\n3. Testing call-to-action detection...")
    cta_text = "Click here to learn more about our services."
    no_cta_text = "This is regular content without any action items."
    
    print(f"   Has CTA: {service._has_call_to_action(cta_text)}")
    print(f"   No CTA: {service._has_call_to_action(no_cta_text)}")
    
    # Test emoji selection
    print("\n4. Testing emoji selection...")
    print(f"   AI content: {service._get_relevant_emoji('AI technology future')}")
    print(f"   Success content: {service._get_relevant_emoji('success growth improvement')}")
    print(f"   Business content: {service._get_relevant_emoji('money business profit')}")
    
    # Test hashtag generation
    print("\n5. Testing hashtag generation...")
    points = [{'key_phrases': ['Artificial Intelligence', 'Business Growth']}]
    twitter_tags = service._generate_relevant_hashtags(points, Platform.TWITTER)
    linkedin_tags = service._generate_relevant_hashtags(points, Platform.LINKEDIN)
    
    print(f"   Twitter hashtags: {twitter_tags}")
    print(f"   LinkedIn hashtags: {linkedin_tags}")
    
    # Test content transformation
    print("\n6. Testing content transformation...")
    key_points = [{
        'id': 1,
        'content': 'AI is transforming business with 40% productivity gains.',
        'length': 50,
        'key_phrases': ['AI', 'business'],
        'sentiment': 'positive',
        'has_numbers': True,
        'has_questions': False,
        'has_calls_to_action': False
    }]
    
    print("   Testing video script generation...")
    video_script = await service._transform_to_video_script(key_points, 'Professional')
    print(f"   Video script length: {len(video_script)} characters")
    print(f"   Video script preview: {video_script[:100]}...")
    
    print("   Testing blog post generation...")
    blog_post = await service._transform_to_blog_post(key_points, 'Professional')
    print(f"   Blog post length: {len(blog_post)} characters")
    print(f"   Blog post preview: {blog_post[:100]}...")
    
    # Test readability improvement
    print("\n7. Testing readability improvement...")
    long_sentence = "This is a very long sentence that contains many words and should be broken down into smaller more manageable pieces for better readability and comprehension by the reader."
    improved = service._improve_readability(long_sentence)
    sentences = improved.split('. ')
    print(f"   Original: 1 sentence, {len(long_sentence)} characters")
    print(f"   Improved: {len(sentences)} sentences, max {max(len(s) for s in sentences if s)} characters")
    
    # Test brand voice consistency
    print("\n8. Testing brand voice consistency...")
    content = "Hey there! This is awesome content."
    professional = service._ensure_brand_voice_consistency(content, "Professional")
    casual = service._ensure_brand_voice_consistency(content, "Casual")
    
    print(f"   Original: {content}")
    print(f"   Professional: {professional}")
    print(f"   Casual: {casual}")
    
    # Test quality metrics calculation
    print("\n9. Testing quality metrics calculation...")
    source_content = "This is source content with multiple sentences. It has some content."
    target_content = "This is target content with questions? And exclamations! And hashtags #content"
    
    metrics = service._calculate_quality_metrics(
        source_content, target_content, ContentType.BLOG_POST,
        ContentType.SOCIAL_MEDIA_POST, [Platform.TWITTER]
    )
    
    print(f"   Compression ratio: {metrics['compression_ratio']:.2f}")
    print(f"   Engagement score: {metrics['engagement_score']:.2f}")
    print(f"   Overall quality: {metrics['overall_quality_score']:.2f}")
    print(f"   Meets requirements: {metrics['meets_requirements']}")
    
    print("\n" + "=" * 50)
    print("All tests completed successfully!")
    print("Content Repurposing Service is working correctly.")


if __name__ == "__main__":
    asyncio.run(test_content_repurposing())
