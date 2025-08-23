#!/usr/bin/env python3
"""
Simplified System Integration Test for Autonomica CMS
This script tests the actual implemented services with their real method signatures
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from services.content_types import ContentType, ContentFormat, Platform
from services.content_generation_standalone import StandaloneContentGenerationService
from services.content_repurposing import ContentRepurposingService
from services.content_quality_checker import ContentQualityChecker
from services.content_review_workflow import ContentReviewWorkflow
from services.content_versioning import ContentVersioningService
from services.content_lifecycle_manager import ContentLifecycleManager
from services.content_analytics import ContentAnalyticsService
from services.content_reporting import ContentReportingService

class SimpleSystemIntegrationTester:
    def __init__(self):
        self.test_results = []
        self.errors = []
        
    async def run_simple_system_test(self):
        """Run simplified system integration testing with actual service implementations"""
        print("🚀 Starting Simplified System Integration Test")
        print("=" * 60)
        
        try:
            # Test 1: Content Generation (Standalone)
            await self.test_content_generation()
            
            # Test 2: Content Repurposing
            await self.test_content_repurposing()
            
            # Test 3: Quality Checking
            await self.test_quality_checking()
            
            # Test 4: Review Workflow
            await self.test_review_workflow()
            
            # Test 5: Versioning System
            await self.test_versioning_system()
            
            # Test 6: Lifecycle Management
            await self.test_lifecycle_management()
            
            # Test 7: Analytics and Reporting
            await self.test_analytics_reporting()
            
            # Test 8: Simple End-to-End Workflow
            await self.test_simple_workflow()
            
        except Exception as e:
            self.errors.append(f"System test failed: {e}")
            print(f"❌ System test failed: {e}")
        
        # Generate test report
        await self.generate_test_report()
    
    async def test_content_generation(self):
        """Test the standalone content generation service"""
        print("\n🧪 Test 1: Content Generation (Standalone)")
        print("-" * 40)
        
        try:
            standalone_service = StandaloneContentGenerationService()
            
            # Test blog post generation
            blog_content = await standalone_service.generate_content(
                content_type=ContentType.BLOG_POST,
                prompt="AI in Content Marketing",
                target_platforms=[Platform.WEBSITE],
                brand_voice="professional"
            )
            
            if blog_content and blog_content.get("content", {}).get("raw"):
                print("  ✅ Standalone blog generation: PASSED")
                self.test_results.append(("Standalone Blog Generation", "PASSED"))
            else:
                print("  ❌ Standalone blog generation: FAILED")
                self.test_results.append(("Standalone Blog Generation", "FAILED"))
                
        except Exception as e:
            print(f"  ❌ Content generation test failed: {e}")
            self.test_results.append(("Content Generation", "FAILED"))
            self.errors.append(f"Content generation: {e}")
    
    async def test_content_repurposing(self):
        """Test the content repurposing service"""
        print("\n🧪 Test 2: Content Repurposing")
        print("-" * 40)
        
        try:
            repurposing_service = ContentRepurposingService()
            
            # Sample blog content for repurposing
            sample_blog = """
            Artificial Intelligence is revolutionizing content marketing in unprecedented ways. 
            From automated content generation to personalized user experiences, AI tools are 
            helping marketers create more engaging and effective content than ever before.
            
            The key benefits include increased efficiency, better targeting, and improved 
            ROI. Companies that embrace AI-driven content strategies are seeing significant 
            improvements in their marketing performance.
            """
            
            # Test blog to social media conversion
            result = await repurposing_service.repurpose_content(
                source_content=sample_blog,
                source_type=ContentType.BLOG_POST,
                target_type=ContentType.SOCIAL_MEDIA_POST,
                target_platforms=[Platform.TWITTER],
                brand_voice="professional"
            )
            
            if result and result.repurposed_content:
                print("  ✅ Blog to social media conversion: PASSED")
                self.test_results.append(("Blog to Social Media Conversion", "PASSED"))
            else:
                print("  ❌ Blog to social media conversion: FAILED")
                self.test_results.append(("Blog to Social Media Conversion", "FAILED"))
                
        except Exception as e:
            print(f"  ❌ Content repurposing test failed: {e}")
            self.test_results.append(("Content Repurposing", "FAILED"))
            self.errors.append(f"Content repurposing: {e}")
    
    async def test_quality_checking(self):
        """Test the content quality checker service"""
        print("\n🧪 Test 3: Content Quality Checking")
        print("-" * 40)
        
        try:
            quality_checker = ContentQualityChecker()
            
            # Sample content for quality checking
            sample_content = "This is a sample content for testing quality checks. It should pass basic validation."
            
            # Test content quality check
            quality_result = await quality_checker.check_content_quality(
                content=sample_content,
                content_type=ContentType.BLOG_POST,
                target_platforms=[Platform.WEBSITE]
            )
            
            if quality_result and hasattr(quality_result, 'overall_score'):
                print("  ✅ Content quality check: PASSED")
                self.test_results.append(("Content Quality Check", "PASSED"))
            else:
                print("  ❌ Content quality check: FAILED")
                self.test_results.append(("Content Quality Check", "FAILED"))
                
        except Exception as e:
            print(f"  ❌ Quality checking test failed: {e}")
            self.test_results.append(("Quality Checking", "FAILED"))
            self.errors.append(f"Quality checking: {e}")
    
    async def test_review_workflow(self):
        """Test the content review workflow service"""
        print("\n🧪 Test 4: Content Review Workflow")
        print("-" * 40)
        
        try:
            review_service = ContentReviewWorkflow()
            
            # Add a reviewer to the system
            from services.content_review_workflow import Reviewer, ReviewPriority
            reviewer = Reviewer(
                reviewer_id="test_reviewer_001",
                name="Test Reviewer",
                email="reviewer@test.com",
                expertise=[ContentType.BLOG_POST],
                is_active=True,
                max_reviews_per_day=10,
                current_reviews=0
            )
            review_service.reviewers["test_reviewer_001"] = reviewer
            
            # First create a quality check result
            quality_checker = ContentQualityChecker()
            quality_result = await quality_checker.check_content_quality(
                content="Sample blog content for review",
                content_type=ContentType.BLOG_POST,
                target_platforms=[Platform.WEBSITE]
            )
            
            # Test creating a review request (using actual method signature)
            review_request = await review_service.submit_for_review(
                content_id="test_content_001",
                content_type=ContentType.BLOG_POST,
                content_preview="Sample blog content for review",
                target_platforms=[Platform.WEBSITE],
                brand_voice="professional",
                quality_check_result=quality_result,
                requested_by="test_user",
                priority="medium"
            )
            
            if review_request and review_request.status == "pending":
                print("  ✅ Content submission for review: PASSED")
                self.test_results.append(("Content Review Submission", "PASSED"))
            else:
                print("  ❌ Content submission for review: FAILED")
                self.test_results.append(("Content Review Submission", "FAILED"))
                
        except Exception as e:
            print(f"  ❌ Review workflow test failed: {e}")
            self.test_results.append(("Review Workflow", "FAILED"))
            self.errors.append(f"Review workflow: {e}")
    
    async def test_versioning_system(self):
        """Test the content versioning service"""
        print("\n🧪 Test 5: Content Versioning System")
        print("-" * 40)
        
        try:
            versioning_service = ContentVersioningService()
            
            # Test creating initial version (using actual method signature)
            initial_version = await versioning_service.create_version(
                content_id="test_content_001",
                content_data="Initial content version",
                content_type=ContentType.BLOG_POST,
                content_format=ContentFormat.ARTICLE,
                author_id="test_user",
                change_log="Initial version creation"
            )
            
            if initial_version and initial_version.version_number == "1.0.0":
                print("  ✅ Initial version creation: PASSED")
                self.test_results.append(("Initial Version Creation", "PASSED"))
            else:
                print("  ❌ Initial version creation: FAILED")
                self.test_results.append(("Initial Version Creation", "FAILED"))
                
        except Exception as e:
            print(f"  ❌ Versioning system test failed: {e}")
            self.test_results.append(("Versioning System", "FAILED"))
            self.errors.append(f"Versioning system: {e}")
    
    async def test_lifecycle_management(self):
        """Test the content lifecycle management service"""
        print("\n🧪 Test 6: Content Lifecycle Management")
        print("-" * 40)
        
        try:
            lifecycle_manager = ContentLifecycleManager()
            
            # Test creating content (using actual method signature)
            result = await lifecycle_manager.create_content(
                content_id="test_content_001",
                content_type=ContentType.BLOG_POST,
                content_data="Sample blog content",
                content_format=ContentFormat.ARTICLE,
                author_id="test_user",
                target_platforms=[Platform.WEBSITE]
            )
            
            # The method returns a tuple (version, lifecycle_state)
            version, lifecycle_state = result
            
            if lifecycle_state and lifecycle_state.current_stage == "DRAFT":
                print("  ✅ Lifecycle creation: PASSED")
                self.test_results.append(("Lifecycle Creation", "PASSED"))
            else:
                print("  ❌ Lifecycle creation: FAILED")
                self.test_results.append(("Lifecycle Creation", "FAILED"))
                
        except Exception as e:
            print(f"  ❌ Lifecycle management test failed: {e}")
            self.test_results.append(("Lifecycle Management", "FAILED"))
            self.errors.append(f"Lifecycle management: {e}")
    
    async def test_analytics_reporting(self):
        """Test the analytics and reporting system"""
        print("\n🧪 Test 7: Analytics and Reporting System")
        print("-" * 40)
        
        try:
            analytics_service = ContentAnalyticsService()
            reporting_service = ContentReportingService(analytics_service)
            
            # Test metric tracking
            success = await analytics_service.track_metric(
                content_id="test_content_001",
                metric_type="engagement",
                metric_name="views",
                value=100
            )
            
            if success:
                print("  ✅ Metric tracking: PASSED")
                self.test_results.append(("Metric Tracking", "PASSED"))
            else:
                print("  ❌ Metric tracking: FAILED")
                self.test_results.append(("Metric Tracking", "FAILED"))
            
            # Test report generation
            report = await reporting_service.generate_scheduled_reports()
            
            if report and len(report) >= 0:
                print("  ✅ Report generation: PASSED")
                self.test_results.append(("Report Generation", "PASSED"))
            else:
                print("  ❌ Report generation: FAILED")
                self.test_results.append(("Report Generation", "FAILED"))
                
        except Exception as e:
            print(f"  ❌ Analytics and reporting test failed: {e}")
            self.test_results.append(("Analytics and Reporting", "FAILED"))
            self.errors.append(f"Analytics and reporting: {e}")
    
    async def test_simple_workflow(self):
        """Test a simple end-to-end workflow"""
        print("\n🧪 Test 8: Simple End-to-End Workflow")
        print("-" * 40)
        
        try:
            print("  🔄 Testing simple content workflow...")
            
            # 1. Generate content
            standalone_service = StandaloneContentGenerationService()
            blog_content = await standalone_service.generate_content(
                content_type=ContentType.BLOG_POST,
                prompt="AI Content Marketing",
                target_platforms=[Platform.WEBSITE],
                brand_voice="professional"
            )
            
            if not blog_content or not blog_content.get("content", {}).get("raw"):
                raise Exception("Content generation failed")
            
            # 2. Repurpose content
            repurposing_service = ContentRepurposingService()
            result = await repurposing_service.repurpose_content(
                source_content=blog_content["content"]["raw"],
                source_type=ContentType.BLOG_POST,
                target_type=ContentType.SOCIAL_MEDIA_POST,
                target_platforms=[Platform.TWITTER],
                brand_voice="professional"
            )
            
            if not result:
                raise Exception("Content repurposing failed")
            
            # 3. Quality check
            quality_checker = ContentQualityChecker()
            quality_result = await quality_checker.check_content_quality(
                content=blog_content["content"]["raw"],
                content_type=ContentType.BLOG_POST,
                target_platforms=[Platform.WEBSITE]
            )
            
            if quality_result:
                print("  ✅ Simple end-to-end workflow: PASSED")
                self.test_results.append(("Simple End-to-End Workflow", "PASSED"))
            else:
                print("  ❌ Simple end-to-end workflow: FAILED")
                self.test_results.append(("Simple End-to-End Workflow", "FAILED"))
                
        except Exception as e:
            print(f"  ❌ Simple end-to-end workflow test failed: {e}")
            self.test_results.append(("Simple End-to-End Workflow", "FAILED"))
            self.errors.append(f"Simple end-to-end workflow: {e}")
    
    async def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📋 SIMPLIFIED SYSTEM INTEGRATION TEST REPORT")
        print("=" * 60)
        
        # Calculate statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, status in self.test_results if status == "PASSED")
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Display results
        print(f"\n📊 Test Results Summary:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {passed_tests}")
        print(f"  Failed: {failed_tests}")
        print(f"  Success Rate: {success_rate:.1f}%")
        
        print(f"\n✅ Passed Tests:")
        for test_name, status in self.test_results:
            if status == "PASSED":
                print(f"  ✓ {test_name}")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for test_name, status in self.test_results:
                if status == "FAILED":
                    print(f"  ✗ {test_name}")
        
        if self.errors:
            print(f"\n🚨 Errors Encountered:")
            for error in self.errors:
                print(f"  • {error}")
        
        # Overall assessment
        if success_rate >= 90:
            print(f"\n🎉 EXCELLENT! System is highly reliable and ready for production.")
        elif success_rate >= 75:
            print(f"\n✅ GOOD! System is mostly reliable with minor issues to address.")
        elif success_rate >= 50:
            print(f"\n⚠️  FAIR! System has significant issues that need attention.")
        else:
            print(f"\n❌ POOR! System has critical issues requiring immediate attention.")
        
        print(f"\n🚀 Simplified System Integration Testing Complete!")

async def main():
    """Main test execution function"""
    tester = SimpleSystemIntegrationTester()
    await tester.run_simple_system_test()

if __name__ == "__main__":
    asyncio.run(main())
