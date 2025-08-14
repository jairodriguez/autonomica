#!/usr/bin/env python3
"""
System Integration Test for Content Generation and Repurposing Pipeline

This test script verifies that all components work together correctly:
- Content types and formats
- Content generation
- Content repurposing
- Quality checking
- Versioning
- Analytics
- CLI interface
"""

import sys
import os
import tempfile
import json
from datetime import datetime, timezone

# Add the app/ai directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'ai'))

from content_types_simple import ContentType, ContentFormat, get_content_registry
from content_generation import ContentGenerator, ContentGenerationRequest, ContentRepurposingRequest
from content_repurposing import get_repurposing_engine
from content_quality import get_quality_checker
from content_versioning import get_versioning_system, VersionStatus
from content_analytics import get_analytics, MetricType, EngagementMetric, PerformanceMetric

def test_content_type_registry():
    """Test content type registry functionality"""
    print("Testing content type registry...")
    
    registry = get_content_registry()
    
    # Test content structures
    blog_structure = registry.get_content_structure(ContentType.BLOG_POST)
    if blog_structure:
        print(f"✓ Blog post structure: {len(blog_structure.required_sections)} required sections")
        print(f"  Word count range: {blog_structure.word_count_range}")
    else:
        print("✗ Blog post structure not found")
        return False
    
    # Test transformations
    transformations = registry.get_available_transformations(ContentType.BLOG_POST)
    print(f"✓ Available transformations from blog post: {len(transformations)}")
    
    # Test transformation path
    transformation = registry.get_transformation_path(ContentType.BLOG_POST, ContentType.TWEET)
    if transformation:
        print(f"✓ Blog to tweet transformation: {transformation.transformation_method}")
    else:
        print("✗ Blog to tweet transformation not found")
        return False
    
    return True

def test_content_generation_pipeline():
    """Test the complete content generation pipeline"""
    print("\nTesting content generation pipeline...")
    
    generator = ContentGenerator()
    
    # Test content generation
    request = ContentGenerationRequest(
        content_type=ContentType.BLOG_POST,
        target_format=ContentFormat.MARKDOWN,
        prompt="Write a short blog post about AI content generation",
        brand_voice="Professional and informative",
        custom_instructions="Include a call-to-action at the end"
    )
    
    try:
        response = generator.generate_content_sync(request)
        print(f"✓ Generated content successfully")
        print(f"  Content type: {response.content_type.value}")
        print(f"  Format: {response.format.value}")
        print(f"  Word count: {response.word_count}")
        print(f"  Generation time: {response.generation_time:.2f}s")
        
        # Verify content structure
        if "AI content generation" in response.content:
            print("✓ Content contains expected topic")
        else:
            print("✗ Content missing expected topic")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Content generation failed: {e}")
        return False

def test_content_repurposing_pipeline():
    """Test the content repurposing pipeline"""
    print("\nTesting content repurposing pipeline...")
    
    generator = ContentGenerator()
    repurposing_engine = get_repurposing_engine()
    
    # Test source content
    source_content = """
    AI Content Generation: The Future of Marketing
    
    Artificial Intelligence is revolutionizing how we create content. 
    From blog posts to social media updates, AI tools are helping 
    marketers produce high-quality content faster than ever before.
    
    Key benefits include:
    - Increased productivity
    - Consistent quality
    - Data-driven insights
    - Personalized content
    
    The future of content marketing lies in the synergy between 
    human creativity and AI capabilities.
    """
    
    # Test repurposing request
    request = ContentRepurposingRequest(
        source_content=source_content,
        source_type=ContentType.BLOG_POST,
        target_type=ContentType.TWEET,
        brand_voice="Professional and engaging"
    )
    
    try:
        response = generator.repurpose_content_sync(request)
        print(f"✓ Content repurposing successful")
        print(f"  Target type: {response.content_type.value}")
        print(f"  Word count: {response.word_count}")
        print(f"  Repurposing time: {response.generation_time:.2f}s")
        
        # Verify repurposed content
        if len(response.content) <= 280:  # Tweet character limit
            print("✓ Repurposed content fits tweet format")
        else:
            print("✗ Repurposed content too long for tweet")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Content repurposing failed: {e}")
        return False

def test_quality_checking_pipeline():
    """Test the quality checking pipeline"""
    print("\nTesting quality checking pipeline...")
    
    quality_checker = get_quality_checker()
    
    # Test content for quality check
    test_content = """
    AI Content Generation: A Comprehensive Guide
    
    Artificial Intelligence has transformed the landscape of content creation.
    This technology enables marketers to produce engaging, relevant content
    that resonates with their target audience.
    
    Key advantages include:
    - Enhanced productivity and efficiency
    - Consistent quality across all content
    - Data-driven insights for optimization
    - Personalized content delivery
    
    The integration of AI in content marketing represents a paradigm shift
    that combines human creativity with machine intelligence.
    """
    
    try:
        report = quality_checker.assess_content_quality(
            content=test_content,
            content_type=ContentType.BLOG_POST,
            target_format=ContentFormat.PLAIN_TEXT,
            brand_voice="Professional and authoritative"
        )
        
        print(f"✓ Quality check completed successfully")
        print(f"  Overall score: {report.overall_score:.1f}/100")
        print(f"  Overall level: {report.overall_level.value}")
        print(f"  Recommendations: {len(report.recommendations)}")
        
        # Verify report structure
        if report.metric_scores and report.summary and report.recommendations:
            print("✓ Quality report structure is complete")
        else:
            print("✗ Quality report structure incomplete")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Quality check failed: {e}")
        return False

def test_versioning_pipeline():
    """Test the content versioning pipeline"""
    print("\nTesting content versioning pipeline...")
    
    versioning_system = get_versioning_system()
    
    try:
        # Create initial content
        content_id = versioning_system.create_content(
            content="Initial version of test content",
            content_type=ContentType.BLOG_POST,
            format=ContentFormat.PLAIN_TEXT,
            metadata={"title": "Version Test", "status": "draft"},
            user_id="test_user"
        )
        print(f"✓ Created initial content: {content_id}")
        
        # Create new version
        version_id = versioning_system.create_version(
            content_id=content_id,
            content="Updated version with improvements",
            user_id="test_user",
            change_summary="Added more details and improved structure"
        )
        print(f"✓ Created new version: {version_id}")
        
        # Update status
        versioning_system.update_version_status(
            version_id=version_id,
            new_status=VersionStatus.IN_REVIEW,
            user_id="test_user",
            notes="Ready for review"
        )
        print("✓ Updated version status")
        
        # Get version history
        versions = versioning_system.get_version_history(content_id)
        print(f"✓ Version history: {len(versions)} versions")
        
        # Test rollback
        rollback_id = versioning_system.rollback_to_version(
            content_id=content_id,
            target_version_id=versions[0].version_id,
            user_id="test_user",
            reason="Testing rollback functionality"
        )
        print(f"✓ Created rollback version: {rollback_id}")
        
        return True
        
    except Exception as e:
        print(f"✗ Versioning test failed: {e}")
        return False

def test_analytics_pipeline():
    """Test the analytics pipeline"""
    print("\nTesting analytics pipeline...")
    
    analytics = get_analytics()
    versioning_system = get_versioning_system()
    
    try:
        # Create test content for analytics
        content_id = versioning_system.create_content(
            content="Analytics test content",
            content_type=ContentType.BLOG_POST,
            format=ContentFormat.PLAIN_TEXT,
            metadata={"title": "Analytics Test"},
            user_id="test_user"
        )
        
        versions = versioning_system.get_version_history(content_id)
        version_id = versions[0].version_id
        
        # Track various metrics
        analytics.track_metric(
            content_id=content_id,
            version_id=version_id,
            metric_type=MetricType.ENGAGEMENT,
            metric_name=EngagementMetric.VIEWS.value,
            value=100,
            unit="views"
        )
        
        analytics.track_metric(
            content_id=content_id,
            version_id=version_id,
            metric_type=MetricType.ENGAGEMENT,
            metric_name=EngagementMetric.LIKES.value,
            value=15,
            unit="likes"
        )
        
        analytics.track_metric(
            content_id=content_id,
            version_id=version_id,
            metric_type=MetricType.QUALITY,
            metric_name=PerformanceMetric.QUALITY_SCORE.value,
            value=82.5,
            unit="score"
        )
        
        print("✓ Tracked multiple metrics successfully")
        
        # Test performance data
        performance = analytics.get_content_performance(content_id)
        if performance:
            print(f"✓ Retrieved performance data")
            print(f"  Views: {performance.total_views}")
            print(f"  Engagement rate: {performance.engagement_rate:.2f}%")
        else:
            print("✗ No performance data found")
            return False
        
        # Test report generation
        report = analytics.generate_content_report(content_id)
        print(f"✓ Generated analytics report: {report.report_id}")
        
        return True
        
    except Exception as e:
        print(f"✗ Analytics test failed: {e}")
        return False

def test_cli_integration():
    """Test CLI integration with all components"""
    print("\nTesting CLI integration...")
    
    try:
        # Test CLI help
        import subprocess
        result = subprocess.run(
            ['python3', 'app/ai/content_cli.py', '--help'],
            capture_output=True,
            text=True,
            cwd='/workspace/autonomica-api'
        )
        
        if result.returncode == 0:
            print("✓ CLI help command works")
        else:
            print("✗ CLI help command failed")
            return False
        
        # Test content types listing
        result = subprocess.run(
            ['python3', 'app/ai/content_cli.py', 'types'],
            capture_output=True,
            text=True,
            cwd='/workspace/autonomica-api'
        )
        
        if result.returncode == 0 and "blog_post" in result.stdout:
            print("✓ CLI types command works")
        else:
            print("✗ CLI types command failed")
            return False
        
        # Test strategies listing
        result = subprocess.run(
            ['python3', 'app/ai/content_cli.py', 'strategies'],
            capture_output=True,
            text=True,
            cwd='/workspace/autonomica-api'
        )
        
        if result.returncode == 0 and "blog_to_tweet" in result.stdout:
            print("✓ CLI strategies command works")
        else:
            print("✗ CLI strategies command failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ CLI integration test failed: {e}")
        return False

def test_end_to_end_workflow():
    """Test complete end-to-end workflow"""
    print("\nTesting end-to-end workflow...")
    
    try:
        # 1. Generate content
        generator = ContentGenerator()
        request = ContentGenerationRequest(
            content_type=ContentType.BLOG_POST,
            target_format=ContentFormat.PLAIN_TEXT,
            prompt="Write about the benefits of AI in marketing",
            brand_voice="Professional and engaging"
        )
        
        response = generator.generate_content_sync(request)
        print("✓ Step 1: Content generation completed")
        
        # 2. Check quality
        quality_checker = get_quality_checker()
        quality_report = quality_checker.assess_content_quality(
            content=response.content,
            content_type=ContentType.BLOG_POST,
            target_format=ContentFormat.PLAIN_TEXT
        )
        print("✓ Step 2: Quality check completed")
        
        # 3. Create version
        versioning_system = get_versioning_system()
        content_id = versioning_system.create_content(
            content=response.content,
            content_type=ContentType.BLOG_POST,
            format=ContentFormat.PLAIN_TEXT,
            metadata={"title": "AI Marketing Benefits", "quality_score": quality_report.overall_score},
            user_id="test_user"
        )
        print("✓ Step 3: Version creation completed")
        
        # 4. Repurpose content
        repurpose_request = ContentRepurposingRequest(
            source_content=response.content,
            source_type=ContentType.BLOG_POST,
            target_type=ContentType.TWEET
        )
        
        repurpose_response = generator.repurpose_content_sync(repurpose_request)
        print("✓ Step 4: Content repurposing completed")
        
        # 5. Track analytics
        analytics = get_analytics()
        versions = versioning_system.get_version_history(content_id)
        version_id = versions[0].version_id
        
        analytics.track_metric(
            content_id=content_id,
            version_id=version_id,
            metric_type=MetricType.ENGAGEMENT,
            metric_name=EngagementMetric.VIEWS.value,
            value=200,
            unit="views"
        )
        print("✓ Step 5: Analytics tracking completed")
        
        # 6. Generate report
        analytics_report = analytics.generate_content_report(content_id)
        print("✓ Step 6: Analytics report generated")
        
        print("✓ Complete end-to-end workflow successful!")
        return True
        
    except Exception as e:
        print(f"✗ End-to-end workflow failed: {e}")
        return False

def test_error_handling():
    """Test error handling across components"""
    print("\nTesting error handling...")
    
    try:
        # Test invalid content type
        generator = ContentGenerator()
        invalid_request = ContentGenerationRequest(
            content_type="invalid_type",  # This should cause an error
            target_format=ContentFormat.PLAIN_TEXT,
            prompt="Test prompt"
        )
        
        try:
            response = generator.generate_content_sync(invalid_request)
            print("✗ Should have failed with invalid content type")
            return False
        except Exception as e:
            print(f"✓ Correctly handled invalid content type: {e}")
        
        # Test invalid repurposing transformation
        repurpose_request = ContentRepurposingRequest(
            source_content="Test content",
            source_type=ContentType.TWEET,
            target_type=ContentType.BLOG_POST  # This transformation might not exist
        )
        
        try:
            response = generator.repurpose_content_sync(repurpose_request)
            print("✓ Repurposing transformation available")
        except Exception as e:
            print(f"✓ Correctly handled unavailable transformation: {e}")
        
        # Test analytics with non-existent content
        analytics = get_analytics()
        performance = analytics.get_content_performance("non_existent_id")
        if performance is None:
            print("✓ Correctly handled non-existent content ID")
        else:
            print("✗ Should return None for non-existent content")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False

def main():
    """Run all system integration tests"""
    print("🧪 System Integration Testing for Content Pipeline\n")
    print("=" * 60)
    
    tests = [
        ("Content Type Registry", test_content_type_registry),
        ("Content Generation Pipeline", test_content_generation_pipeline),
        ("Content Repurposing Pipeline", test_content_repurposing_pipeline),
        ("Quality Checking Pipeline", test_quality_checking_pipeline),
        ("Versioning Pipeline", test_versioning_pipeline),
        ("Analytics Pipeline", test_analytics_pipeline),
        ("CLI Integration", test_cli_integration),
        ("End-to-End Workflow", test_end_to_end_workflow),
        ("Error Handling", test_error_handling)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"📊 System Integration Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All system integration tests passed!")
        print("✅ The content generation and repurposing pipeline is working correctly")
        return 0
    else:
        print("⚠️  Some system integration tests failed")
        print("🔧 Please review the failed components")
        return 1

if __name__ == "__main__":
    sys.exit(main())