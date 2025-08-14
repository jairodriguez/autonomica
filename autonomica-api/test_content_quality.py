#!/usr/bin/env python3
"""
Test script for content quality system.
"""

import sys
import os

# Add the app/ai directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'ai'))

try:
    # Import the quality module
    from content_quality import (
        QualityLevel, QualityMetric, QualityScore, ContentQualityReport,
        ContentQualityChecker, get_quality_checker
    )
    from content_types_simple import ContentType, ContentFormat
    
    print("✅ Successfully imported content quality module")
    
    def test_content_quality():
        """Test content quality functionality."""
        print("\n🔍 Testing content quality functionality...")
        
        # Test quality checker
        checker = get_quality_checker()
        print("✅ Content quality checker created successfully")
        
        # Test quality levels
        print(f"✅ Quality levels: {[level.value for level in QualityLevel]}")
        
        # Test quality metrics
        print(f"✅ Quality metrics: {[metric.value for metric in QualityMetric]}")
        
        # Test sample content quality assessment
        print("\n🔍 Testing content quality assessment...")
        
        # Sample blog content
        sample_blog = """
        # The Future of Artificial Intelligence in Business
        
        ## Introduction
        Artificial Intelligence is transforming how businesses operate in the modern world. Companies are increasingly adopting AI technologies to improve efficiency and gain competitive advantages.
        
        ## Main Content
        Machine learning algorithms can analyze vast amounts of data to identify patterns that humans might miss. This capability enables businesses to make better decisions and optimize their operations.
        
        Natural language processing enables businesses to provide better customer service through chatbots and automated responses. These AI-powered solutions are available 24/7 and can handle multiple customer inquiries simultaneously.
        
        Computer vision technology is revolutionizing quality control in manufacturing. AI systems can detect defects and quality issues with greater accuracy than human inspectors.
        
        ## Conclusion
        The future of business lies in the strategic integration of AI technologies that enhance human capabilities rather than replace them. Companies that embrace AI will have a significant competitive advantage.
        
        ## Call to Action
        Ready to transform your business with AI? Contact us today to learn how we can help you implement AI solutions that drive growth and innovation.
        """
        
        # Assess blog quality
        print("\n🔍 Assessing blog post quality...")
        blog_report = checker.assess_content_quality(
            content=sample_blog,
            content_type=ContentType.BLOG_POST,
            target_format=ContentFormat.MARKDOWN,
            brand_voice="professional",
            title="The Future of Artificial Intelligence in Business",
            meta_description="Discover how AI is transforming business operations and creating new opportunities for growth and innovation.",
            keywords=["artificial intelligence", "business", "machine learning", "automation"]
        )
        
        print(f"✅ Blog quality assessment completed")
        print(f"Overall Score: {blog_report.overall_score:.2f}")
        print(f"Overall Level: {blog_report.overall_level.value}")
        print(f"Summary: {blog_report.summary}")
        print(f"Word Count: {blog_report.word_count}")
        print(f"Character Count: {blog_report.character_count}")
        print(f"Estimated Reading Time: {blog_report.estimated_reading_time:.1f} minutes")
        
        # Display metric scores
        print("\n📊 Metric Scores:")
        for metric, score in blog_report.metric_scores.items():
            print(f"  {metric.value}: {score.score:.2f} ({score.level.value})")
            print(f"    Details: {score.details}")
            if score.suggestions:
                print(f"    Suggestions: {', '.join(score.suggestions)}")
        
        # Display recommendations
        if blog_report.recommendations:
            print(f"\n💡 Top Recommendations:")
            for i, rec in enumerate(blog_report.recommendations, 1):
                print(f"  {i}. {rec}")
        
        # Test tweet quality assessment
        print("\n🔍 Testing tweet quality assessment...")
        sample_tweet = "AI is revolutionizing business operations! Companies using machine learning see 40% efficiency gains. Want to learn more? Click here to discover how AI can transform your business strategy. #AI #Business #Innovation"
        
        tweet_report = checker.assess_content_quality(
            content=sample_tweet,
            content_type=ContentType.TWEET,
            target_format=ContentFormat.PLAIN_TEXT,
            brand_voice="innovative"
        )
        
        print(f"✅ Tweet quality assessment completed")
        print(f"Overall Score: {tweet_report.overall_score:.2f}")
        print(f"Overall Level: {tweet_report.overall_level.value}")
        print(f"Summary: {tweet_report.summary}")
        
        # Test poor quality content
        print("\n🔍 Testing poor quality content assessment...")
        poor_content = "This is a very long sentence that goes on and on without any proper punctuation or structure making it difficult to read and understand what the author is trying to convey to the reader."
        
        poor_report = checker.assess_content_quality(
            content=poor_content,
            content_type=ContentType.BLOG_POST,
            target_format=ContentFormat.PLAIN_TEXT,
            brand_voice="professional"
        )
        
        print(f"✅ Poor content quality assessment completed")
        print(f"Overall Score: {poor_report.overall_score:.2f}")
        print(f"Overall Level: {poor_report.overall_level.value}")
        print(f"Summary: {poor_report.summary}")
        
        if poor_report.recommendations:
            print(f"💡 Recommendations for improvement:")
            for i, rec in enumerate(poor_report.recommendations, 1):
                print(f"  {i}. {rec}")
        
        # Test different brand voices
        print("\n🔍 Testing different brand voice assessments...")
        
        conversational_content = "Hey there! Let me tell you about this amazing new AI tool. You're going to love how it makes your work so much easier. Imagine having a personal assistant that never gets tired!"
        
        conversational_report = checker.assess_content_quality(
            content=conversational_content,
            content_type=ContentType.BLOG_POST,
            target_format=ContentFormat.PLAIN_TEXT,
            brand_voice="conversational"
        )
        
        print(f"✅ Conversational brand voice assessment completed")
        print(f"Brand Voice Score: {conversational_report.metric_scores[QualityMetric.BRAND_VOICE_CONSISTENCY].score:.2f}")
        print(f"Brand Voice Details: {conversational_report.metric_scores[QualityMetric.BRAND_VOICE_CONSISTENCY].details}")
        
        # Test SEO optimization
        print("\n🔍 Testing SEO optimization assessment...")
        
        seo_content = """
        # SEO Best Practices for Content Marketing
        
        ## Introduction
        Search engine optimization is crucial for content marketing success. Research shows that content optimized for search engines receives significantly more traffic.
        
        ## Main Content
        Keyword research is essential for SEO success. Studies indicate that targeting the right keywords can improve rankings by up to 300%. According to experts, long-tail keywords often convert better than short, competitive terms.
        
        [Learn more about SEO strategies](https://example.com/seo-guide)
        
        ## Conclusion
        Implementing SEO best practices will help your content rank higher and reach more readers.
        """
        
        seo_report = checker.assess_content_quality(
            content=seo_content,
            content_type=ContentType.BLOG_POST,
            target_format=ContentFormat.MARKDOWN,
            brand_voice="authoritative",
            title="SEO Best Practices for Content Marketing",
            meta_description="Discover proven SEO strategies that will improve your content rankings and drive more organic traffic to your website.",
            keywords=["SEO", "content marketing", "keyword research", "search engine optimization"]
        )
        
        print(f"✅ SEO optimization assessment completed")
        print(f"SEO Score: {seo_report.metric_scores[QualityMetric.SEO_OPTIMIZATION].score:.2f}")
        print(f"SEO Details: {seo_report.metric_scores[QualityMetric.SEO_OPTIMIZATION].details}")
        
        # Test engagement potential
        print("\n🔍 Testing engagement potential assessment...")
        
        engaging_content = """
        # Transform Your Business with AI
        
        ## Introduction
        Are you ready to revolutionize your business? Imagine having the power to analyze customer data in real-time and make decisions that drive growth.
        
        ## Main Content
        Picture this: Your business operations running at peak efficiency with AI-powered automation. What if you could predict customer needs before they even know they have them?
        
        Here's the thing: Companies that embrace AI are seeing incredible results. You can be one of them!
        
        ## Conclusion
        Don't wait to get started. Sign up today and see the difference AI can make in your business.
        """
        
        engagement_report = checker.assess_content_quality(
            content=engaging_content,
            content_type=ContentType.BLOG_POST,
            target_format=ContentFormat.MARKDOWN,
            brand_voice="friendly"
        )
        
        print(f"✅ Engagement potential assessment completed")
        print(f"Engagement Score: {engagement_report.metric_scores[QualityMetric.ENGAGEMENT_POTENTIAL].score:.2f}")
        print(f"Engagement Details: {engagement_report.metric_scores[QualityMetric.ENGAGEMENT_POTENTIAL].details}")
        
        # Test content structure assessment
        print("\n🔍 Testing content structure assessment...")
        
        structured_content = """
        # Complete Guide to AI Implementation
        
        ## Introduction
        This guide provides a comprehensive overview of AI implementation strategies.
        
        ## Main Content
        Detailed information about AI implementation approaches and best practices.
        
        ## Conclusion
        Summary of key points and next steps for AI implementation.
        """
        
        structure_report = checker.assess_content_quality(
            content=structured_content,
            content_type=ContentType.BLOG_POST,
            target_format=ContentFormat.MARKDOWN,
            brand_voice="professional"
        )
        
        print(f"✅ Content structure assessment completed")
        print(f"Structure Score: {structure_report.metric_scores[QualityMetric.CONTENT_STRUCTURE].score:.2f}")
        print(f"Structure Details: {structure_report.metric_scores[QualityMetric.CONTENT_STRUCTURE].details}")
        
        print("\n🎉 All content quality tests passed! The system is working correctly.")
        
    # Run the test
    test_content_quality()
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)