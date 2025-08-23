#!/usr/bin/env python3
"""
Comprehensive System Integration Test for Autonomica CMS
This script tests the entire content generation and repurposing pipeline end-to-end
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from services.content_types import ContentType, ContentFormat, Platform
from services.content_generation_standalone import StandaloneContentGenerationService
from services.langchain_content_generation import LangChainContentGenerator
from services.content_repurposing import ContentRepurposingService
from services.content_quality_checker import ContentQualityChecker
from services.content_review_workflow import ContentReviewWorkflow
from services.content_quality_orchestrator import ContentQualityOrchestrator
from services.content_versioning import ContentVersioningService
from services.content_lifecycle_manager import ContentLifecycleManager
from services.content_analytics import ContentAnalyticsService
from services.content_reporting import ContentReportingService

class SystemIntegrationTester:
    def __init__(self):
        self.test_results = []
        self.errors = []
        
    async def run_full_system_test(self):
        """Run comprehensive end-to-end system testing"""
        print("🚀 Starting Comprehensive System Integration Test")
        print("=" * 60)
        
        try:
            # Test 1: Content Generation Pipeline
            await self.test_content_generation_pipeline()
            
            # Test 2: Content Repurposing Pipeline
            await self.test_content_repurposing_pipeline()
            
            # Test 3: Quality Check System
            await self.test_quality_check_system()
            
            # Test 4: Review Workflow
            await self.test_review_workflow()
            
            # Test 5: Versioning System
            await self.test_versioning_system()
            
            # Test 6: Lifecycle Management
            await self.test_lifecycle_management()
            
            # Test 7: Analytics and Reporting
            await self.test_analytics_reporting()
            
            # Test 8: End-to-End Workflow
            await self.test_end_to_end_workflow()
            
            # Test 9: Error Handling and Edge Cases
            await self.test_error_handling()
            
            # Test 10: Performance and Load Testing
            await self.test_performance()
            
        except Exception as e:
            self.errors.append(f"System test failed: {e}")
            print(f"❌ System test failed: {e}")
        
        # Generate test report
        await self.generate_test_report()
    
    async def test_content_generation_pipeline(self):
        """Test the content generation pipeline"""
        print("\n🧪 Test 1: Content Generation Pipeline")
        print("-" * 40)
        
        try:
            # Test standalone content generation
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
            
            # Test LangChain content generation
            langchain_service = LangChainContentGenerator()
            
            # Test video script generation
            video_content = await langchain_service.generate_video_script(
                blog_content="AI in Content Marketing is revolutionizing how we create and distribute content.",
                target_duration=60,
                style="casual",
                include_visual_cues=True
            )
            
            if video_content and video_content.get("script"):
                print("  ✅ LangChain video script generation: PASSED")
                self.test_results.append(("LangChain Video Script Generation", "PASSED"))
            else:
                print("  ❌ LangChain video script generation: FAILED")
                self.test_results.append(("LangChain Video Script Generation", "FAILED"))
                
        except Exception as e:
            print(f"  ❌ Content generation pipeline test failed: {e}")
            self.test_results.append(("Content Generation Pipeline", "FAILED"))
            self.errors.append(f"Content generation pipeline: {e}")
    
    async def test_content_repurposing_pipeline(self):
        """Test the content repurposing pipeline"""
        print("\n🧪 Test 2: Content Repurposing Pipeline")
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
            
            # Test blog to tweet conversion
            tweets = await repurposing_service.repurpose_to_tweets(sample_blog, "professional")
            if tweets and len(tweets) > 0:
                print("  ✅ Blog to tweet conversion: PASSED")
                self.test_results.append(("Blog to Tweet Conversion", "PASSED"))
            else:
                print("  ❌ Blog to tweet conversion: FAILED")
                self.test_results.append(("Blog to Tweet Conversion", "FAILED"))
            
            # Test blog to video script conversion
            video_script = await repurposing_service.repurpose_to_video_script(sample_blog, "casual")
            if video_script and len(video_script) > 100:
                print("  ✅ Blog to video script conversion: PASSED")
                self.test_results.append(("Blog to Video Script", "PASSED"))
            else:
                print("  ❌ Blog to video script conversion: FAILED")
                self.test_results.append(("Blog to Video Script", "FAILED"))
                
        except Exception as e:
            print(f"  ❌ Content repurposing pipeline test failed: {e}")
            self.test_results.append(("Content Repurposing Pipeline", "FAILED"))
            self.errors.append(f"Content repurposing pipeline: {e}")
    
    async def test_quality_check_system(self):
        """Test the content quality check system"""
        print("\n🧪 Test 3: Content Quality Check System")
        print("-" * 40)
        
        try:
            quality_checker = ContentQualityChecker()
            
            # Sample content for quality checking
            sample_content = "This is a sample content for testing quality checks. It should pass basic validation."
            
            # Test grammar check
            grammar_result = await quality_checker.check_grammar(sample_content)
            if grammar_result.is_valid:
                print("  ✅ Grammar check: PASSED")
                self.test_results.append(("Grammar Check", "PASSED"))
            else:
                print("  ❌ Grammar check: FAILED")
                self.test_results.append(("Grammar Check", "FAILED"))
            
            # Test readability scoring
            readability_result = await quality_checker.calculate_readability_score(sample_content)
            if readability_result.score > 0:
                print("  ✅ Readability scoring: PASSED")
                self.test_results.append(("Readability Scoring", "PASSED"))
            else:
                print("  ❌ Readability scoring: FAILED")
                self.test_results.append(("Readability Scoring", "FAILED"))
                
        except Exception as e:
            print(f"  ❌ Quality check system test failed: {e}")
            self.test_results.append(("Quality Check System", "FAILED"))
            self.errors.append(f"Quality check system: {e}")
    
    async def test_review_workflow(self):
        """Test the content review workflow"""
        print("\n🧪 Test 4: Content Review Workflow")
        print("-" * 40)
        
        try:
            review_service = ContentReviewWorkflow()
            
            # Test submitting content for review
            review_request = await review_service.submit_for_review(
                content_id="test_content_001",
                content_type=ContentType.BLOG_POST,
                submitter_id="user_001",
                priority="medium"
            )
            
            if review_request and review_request.status == "pending":
                print("  ✅ Content submission for review: PASSED")
                self.test_results.append(("Content Review Submission", "PASSED"))
            else:
                print("  ❌ Content submission for review: FAILED")
                self.test_results.append(("Content Review Submission", "FAILED"))
            
            # Test assigning reviewer
            assignment = await review_service.assign_reviewer(
                review_request_id=review_request.review_request_id,
                reviewer_id="reviewer_001"
            )
            
            if assignment:
                print("  ✅ Reviewer assignment: PASSED")
                self.test_results.append(("Reviewer Assignment", "PASSED"))
            else:
                print("  ❌ Reviewer assignment: FAILED")
                self.test_results.append(("Reviewer Assignment", "FAILED"))
                
        except Exception as e:
            print(f"  ❌ Review workflow test failed: {e}")
            self.test_results.append(("Review Workflow", "FAILED"))
            self.errors.append(f"Review workflow: {e}")
    
    async def test_versioning_system(self):
        """Test the content versioning system"""
        print("\n🧪 Test 5: Content Versioning System")
        print("-" * 40)
        
        try:
            versioning_service = ContentVersioningService()
            
            # Test creating initial version
            initial_version = await versioning_service.create_version(
                content_id="test_content_001",
                content="Initial content version",
                metadata={"author": "test_user", "status": "draft"}
            )
            
            if initial_version and initial_version.version == "1.0.0":
                print("  ✅ Initial version creation: PASSED")
                self.test_results.append(("Initial Version Creation", "PASSED"))
            else:
                print("  ❌ Initial version creation: FAILED")
                self.test_results.append(("Initial Version Creation", "FAILED"))
            
            # Test updating content
            updated_version = await versioning_service.update_content(
                content_id="test_content_001",
                new_content="Updated content version",
                change_type="content_update"
            )
            
            if updated_version and updated_version.version == "1.1.0":
                print("  ✅ Content update: PASSED")
                self.test_results.append(("Content Update", "PASSED"))
            else:
                print("  ❌ Content update: FAILED")
                self.test_results.append(("Content Update", "FAILED"))
                
        except Exception as e:
            print(f"  ❌ Versioning system test failed: {e}")
            self.test_results.append(("Versioning System", "FAILED"))
            self.errors.append(f"Versioning system: {e}")
    
    async def test_lifecycle_management(self):
        """Test the content lifecycle management"""
        print("\n🧪 Test 6: Content Lifecycle Management")
        print("-" * 40)
        
        try:
            lifecycle_manager = ContentLifecycleManager()
            
            # Test lifecycle initialization
            lifecycle = await lifecycle_manager.initialize_lifecycle(
                content_id="test_content_001",
                content_type=ContentType.BLOG_POST
            )
            
            if lifecycle and lifecycle.current_state == "DRAFT":
                print("  ✅ Lifecycle initialization: PASSED")
                self.test_results.append(("Lifecycle Initialization", "PASSED"))
            else:
                print("  ❌ Lifecycle initialization: FAILED")
                self.test_results.append(("Lifecycle Initialization", "FAILED"))
            
            # Test state transition
            transition = await lifecycle_manager.transition_state(
                content_id="test_content_001",
                new_state="IN_REVIEW",
                reason="Submitted for review"
            )
            
            if transition and transition.success:
                print("  ✅ State transition: PASSED")
                self.test_results.append(("State Transition", "PASSED"))
            else:
                print("  ❌ State transition: FAILED")
                self.test_results.append(("State Transition", "FAILED"))
                
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
    
    async def test_end_to_end_workflow(self):
        """Test the complete end-to-end workflow"""
        print("\n🧪 Test 8: End-to-End Workflow")
        print("-" * 40)
        
        try:
            # Create a complete workflow: generate → repurpose → quality check → review → version → lifecycle
            print("  🔄 Testing complete content workflow...")
            
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
            tweets = await repurposing_service.repurpose_to_tweets(blog_content, "professional")
            
            if not tweets:
                raise Exception("Content repurposing failed")
            
            # 3. Quality check
            quality_checker = ContentQualityChecker()
            quality_result = await quality_checker.check_grammar(blog_content)
            
            if not quality_result.is_valid:
                print("  ⚠️  Quality check warnings (expected for generated content)")
            
            # 4. Submit for review
            review_service = ContentReviewWorkflow()
            review_request = await review_service.submit_for_review(
                content_id="workflow_test_001",
                content_type=ContentType.BLOG_POST,
                submitter_id="test_user",
                priority="high"
            )
            
            if review_request:
                print("  ✅ End-to-end workflow: PASSED")
                self.test_results.append(("End-to-End Workflow", "PASSED"))
            else:
                print("  ❌ End-to-end workflow: FAILED")
                self.test_results.append(("End-to-End Workflow", "FAILED"))
                
        except Exception as e:
            print(f"  ❌ End-to-end workflow test failed: {e}")
            self.test_results.append(("End-to-End Workflow", "FAILED"))
            self.errors.append(f"End-to-end workflow: {e}")
    
    async def test_error_handling(self):
        """Test error handling and edge cases"""
        print("\n🧪 Test 9: Error Handling and Edge Cases")
        print("-" * 40)
        
        try:
            # Test with invalid content ID
            versioning_service = ContentVersioningService()
            
            try:
                await versioning_service.get_version_history("invalid_id")
                print("  ❌ Invalid ID handling: FAILED (should have raised error)")
                self.test_results.append(("Invalid ID Handling", "FAILED"))
            except Exception:
                print("  ✅ Invalid ID handling: PASSED")
                self.test_results.append(("Invalid ID Handling", "PASSED"))
            
            # Test with empty content
            try:
                await versioning_service.create_version("test_001", "", {})
                print("  ❌ Empty content handling: FAILED (should have raised error)")
                self.test_results.append(("Empty Content Handling", "FAILED"))
            except Exception:
                print("  ✅ Empty content handling: PASSED")
                self.test_results.append(("Empty Content Handling", "PASSED"))
                
        except Exception as e:
            print(f"  ❌ Error handling test failed: {e}")
            self.test_results.append(("Error Handling", "FAILED"))
            self.errors.append(f"Error handling: {e}")
    
    async def test_performance(self):
        """Test performance and load handling"""
        print("\n🧪 Test 10: Performance and Load Testing")
        print("-" * 40)
        
        try:
            # Test concurrent operations
            analytics_service = ContentAnalyticsService()
            
            # Create multiple concurrent metric tracking operations
            tasks = []
            for i in range(10):
                task = analytics_service.track_metric(
                    content_id=f"perf_test_{i:03d}",
                    metric_type="engagement",
                    metric_name="views",
                    value=i * 10
                )
                tasks.append(task)
            
            # Execute concurrently
            start_time = datetime.now()
            results = await asyncio.gather(*tasks)
            end_time = datetime.now()
            
            duration = (end_time - start_time).total_seconds()
            success_count = sum(1 for r in results if r)
            
            if success_count == 10 and duration < 5.0:
                print(f"  ✅ Concurrent operations: PASSED ({success_count}/10 in {duration:.2f}s)")
                self.test_results.append(("Concurrent Operations", "PASSED"))
            else:
                print(f"  ❌ Concurrent operations: FAILED ({success_count}/10 in {duration:.2f}s)")
                self.test_results.append(("Concurrent Operations", "FAILED"))
                
        except Exception as e:
            print(f"  ❌ Performance test failed: {e}")
            self.test_results.append(("Performance Testing", "FAILED"))
            self.errors.append(f"Performance testing: {e}")
    
    async def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📋 SYSTEM INTEGRATION TEST REPORT")
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
        
        print(f"\n🚀 System Integration Testing Complete!")

async def main():
    """Main test execution function"""
    tester = SystemIntegrationTester()
    await tester.run_full_system_test()

if __name__ == "__main__":
    asyncio.run(main())
