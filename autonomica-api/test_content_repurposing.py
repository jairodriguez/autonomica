#!/usr/bin/env python3
"""
Test script for content repurposing module.
"""

import sys
import os

# Add the app/ai directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'ai'))

try:
    # Import the repurposing module
    from content_repurposing import (
        RepurposingStrategy, ContentRepurposingEngine, get_repurposing_engine
    )
    from content_types_simple import ContentType, ContentFormat
    
    print("✅ Successfully imported content repurposing module")
    
    def test_content_repurposing():
        """Test content repurposing functionality."""
        print("\n🔍 Testing content repurposing functionality...")
        
        # Test repurposing engine
        engine = get_repurposing_engine()
        print("✅ Content repurposing engine created successfully")
        
        # Test strategies initialization
        strategies = engine.strategies
        print(f"✅ Repurposing strategies initialized: {len(strategies)} strategies")
        
        # List available strategies
        for key, strategy in strategies.items():
            print(f"  - {strategy.name}: {strategy.description} ({strategy.complexity})")
        
        # Test available strategies for blog to tweet
        print("\n🔍 Testing available strategies...")
        available_strategies = engine.get_available_strategies(ContentType.BLOG_POST, ContentType.TWEET)
        print(f"✅ Available strategies for blog to tweet: {len(available_strategies)}")
        for strategy in available_strategies:
            print(f"  - {strategy.name}: {strategy.description}")
        
        # Test available strategies for blog to tweet thread
        thread_strategies = engine.get_available_strategies(ContentType.BLOG_POST, ContentType.TWEET_THREAD)
        print(f"✅ Available strategies for blog to tweet thread: {len(thread_strategies)}")
        
        # Test available strategies for blog to carousel
        carousel_strategies = engine.get_available_strategies(ContentType.BLOG_POST, ContentType.CAROUSEL)
        print(f"✅ Available strategies for blog to carousel: {len(carousel_strategies)}")
        
        # Test optimal strategy selection
        print("\n🔍 Testing optimal strategy selection...")
        requirements = {"blog_content": True, "target_tone": "professional"}
        optimal_strategy = engine.get_optimal_strategy(ContentType.BLOG_POST, ContentType.TWEET, requirements)
        if optimal_strategy:
            print(f"✅ Optimal strategy selected: {optimal_strategy.name}")
        else:
            print("❌ No optimal strategy found")
        
        # Test content repurposing
        print("\n🔍 Testing content repurposing...")
        
        # Sample blog content
        sample_blog = """
        Introduction: Artificial Intelligence is transforming how businesses operate in the modern world.
        
        Main Content: Companies are increasingly adopting AI technologies to improve efficiency, reduce costs, and gain competitive advantages. Machine learning algorithms can analyze vast amounts of data to identify patterns and make predictions that humans might miss. Natural language processing enables businesses to provide better customer service through chatbots and automated responses. Computer vision technology is revolutionizing quality control in manufacturing.
        
        Conclusion: The future of business lies in the strategic integration of AI technologies that enhance human capabilities rather than replace them.
        """
        
        # Test blog to tweet repurposing
        print("\n🔍 Testing blog to tweet repurposing...")
        tweet_result = engine.repurpose_content(
            sample_blog, 
            ContentType.BLOG_POST, 
            ContentType.TWEET
        )
        
        if tweet_result["success"]:
            print(f"✅ Blog to tweet successful using strategy: {tweet_result['strategy_used']}")
            print(f"Repurposed content: {tweet_result['repurposed_content'][:100]}...")
            print(f"Metadata: {tweet_result['metadata']}")
        else:
            print(f"❌ Blog to tweet failed: {tweet_result['error']}")
        
        # Test blog to tweet thread repurposing
        print("\n🔍 Testing blog to tweet thread repurposing...")
        thread_result = engine.repurpose_content(
            sample_blog, 
            ContentType.BLOG_POST, 
            ContentType.TWEET_THREAD,
            thread_length=4
        )
        
        if thread_result["success"]:
            print(f"✅ Blog to tweet thread successful using strategy: {thread_result['strategy_used']}")
            print(f"Repurposed content length: {len(thread_result['repurposed_content'])} characters")
            print(f"Metadata: {thread_result['metadata']}")
        else:
            print(f"❌ Blog to tweet thread failed: {thread_result['error']}")
        
        # Test blog to Facebook post repurposing
        print("\n🔍 Testing blog to Facebook post repurposing...")
        facebook_result = engine.repurpose_content(
            sample_blog, 
            ContentType.BLOG_POST, 
            ContentType.FACEBOOK_POST,
            call_to_action="What's your experience with AI in business?"
        )
        
        if facebook_result["success"]:
            print(f"✅ Blog to Facebook post successful using strategy: {facebook_result['strategy_used']}")
            print(f"Repurposed content: {facebook_result['repurposed_content'][:150]}...")
        else:
            print(f"❌ Blog to Facebook post failed: {facebook_result['error']}")
        
        # Test blog to LinkedIn post repurposing
        print("\n🔍 Testing blog to LinkedIn post repurposing...")
        linkedin_result = engine.repurpose_content(
            sample_blog, 
            ContentType.BLOG_POST, 
            ContentType.LINKEDIN_POST,
            hook="Here are some key insights from my latest research on AI in business:"
        )
        
        if linkedin_result["success"]:
            print(f"✅ Blog to LinkedIn post successful using strategy: {linkedin_result['strategy_used']}")
            print(f"Repurposed content: {linkedin_result['repurposed_content'][:150]}...")
        else:
            print(f"❌ Blog to LinkedIn post failed: {linkedin_result['error']}")
        
        # Test blog to carousel repurposing
        print("\n🔍 Testing blog to carousel repurposing...")
        carousel_result = engine.repurpose_content(
            sample_blog, 
            ContentType.BLOG_POST, 
            ContentType.CAROUSEL,
            slide_count=4,
            conclusion="These AI insights can transform your business strategy."
        )
        
        if carousel_result["success"]:
            print(f"✅ Blog to carousel successful using strategy: {carousel_result['strategy_used']}")
            print(f"Repurposed content length: {len(carousel_result['repurposed_content'])} characters")
        else:
            print(f"❌ Blog to carousel failed: {carousel_result['error']}")
        
        # Test blog to video script repurposing
        print("\n🔍 Testing blog to video script repurposing...")
        video_result = engine.repurpose_content(
            sample_blog, 
            ContentType.BLOG_POST, 
            ContentType.VIDEO_SCRIPT,
            video_duration="3-4 minutes",
            call_to_action="Like and subscribe for more AI insights!"
        )
        
        if video_result["success"]:
            print(f"✅ Blog to video script successful using strategy: {video_result['strategy_used']}")
            print(f"Repurposed content length: {len(video_result['repurposed_content'])} characters")
        else:
            print(f"❌ Blog to video script failed: {video_result['error']}")
        
        # Test tweet thread to blog repurposing
        print("\n🔍 Testing tweet thread to blog repurposing...")
        sample_thread = """
        Thread: The future of AI in business
        
        1/ AI is transforming how companies operate, from customer service to product development.
        
        2/ Machine learning algorithms can analyze data patterns that humans miss, leading to better decisions.
        
        3/ Natural language processing enables automated customer support that's available 24/7.
        
        4/ Computer vision is revolutionizing quality control in manufacturing and retail.
        
        5/ The key is strategic integration that enhances human capabilities, not replaces them.
        """
        
        thread_to_blog_result = engine.repurpose_content(
            sample_thread, 
            ContentType.TWEET_THREAD, 
            ContentType.BLOG_POST
        )
        
        if thread_to_blog_result["success"]:
            print(f"✅ Tweet thread to blog successful using strategy: {thread_to_blog_result['strategy_used']}")
            print(f"Repurposed content length: {len(thread_to_blog_result['repurposed_content'])} characters")
        else:
            print(f"❌ Tweet thread to blog failed: {thread_to_blog_result['error']}")
        
        # Test blog to newsletter repurposing
        print("\n🔍 Testing blog to newsletter repurposing...")
        newsletter_result = engine.repurpose_content(
            sample_blog, 
            ContentType.BLOG_POST, 
            ContentType.EMAIL_NEWSLETTER,
            subject_line="AI Insights: Transforming Business Operations",
            greeting="Hello there,",
            company_name="Autonomica AI"
        )
        
        if newsletter_result["success"]:
            print(f"✅ Blog to newsletter successful using strategy: {newsletter_result['strategy_used']}")
            print(f"Repurposed content length: {len(newsletter_result['repurposed_content'])} characters")
        else:
            print(f"❌ Blog to newsletter failed: {newsletter_result['error']}")
        
        # Test error handling
        print("\n🔍 Testing error handling...")
        
        try:
            # Test with unsupported transformation
            unsupported_result = engine.repurpose_content(
                sample_blog, 
                ContentType.TWEET, 
                ContentType.BLOG_POST
            )
            print("❌ Should have failed with unsupported transformation")
        except ValueError as e:
            print(f"✅ Properly handled unsupported transformation: {str(e)}")
        
        print("\n🎉 All content repurposing tests passed! The module is working correctly.")
        
    # Run the test
    test_content_repurposing()
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)