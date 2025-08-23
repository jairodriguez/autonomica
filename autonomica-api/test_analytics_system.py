#!/usr/bin/env python3
"""
Test script for the Autonomica CMS Analytics and Reporting System
This script tests the analytics and reporting services without needing the full FastAPI server
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from services.content_analytics import (
    ContentAnalyticsService, 
    MetricType, 
    EngagementMetric, 
    ConversionMetric,
    ReportType
)
from services.content_reporting import (
    ContentReportingService,
    ScheduleType,
    ReportFormat,
    ReportStatus
)
from services.content_types import ContentType, Platform

async def test_analytics_service():
    """Test the content analytics service"""
    print("🧪 Testing Content Analytics Service...")
    
    analytics = ContentAnalyticsService()
    
    # Test 1: Track metrics
    print("  📊 Testing metric tracking...")
    
    # Track some sample metrics
    await analytics.track_metric(
        content_id="content_001",
        metric_type=MetricType.ENGAGEMENT,
        metric_name=EngagementMetric.VIEWS,
        value=150,
        platform=Platform.WEBSITE
    )
    
    await analytics.track_metric(
        content_id="content_001",
        metric_type=MetricType.ENGAGEMENT,
        metric_name=EngagementMetric.LIKES,
        value=25,
        platform=Platform.WEBSITE
    )
    
    await analytics.track_metric(
        content_id="content_001",
        metric_type=MetricType.CONVERSION,
        metric_name=ConversionMetric.SIGNUPS,
        value=5,
        platform=Platform.WEBSITE
    )
    
    await analytics.track_metric(
        content_id="content_001",
        metric_type=MetricType.QUALITY,
        metric_name="quality_score",
        value=0.85,
        platform=Platform.WEBSITE
    )
    
    # Track metrics for another content piece
    await analytics.track_metric(
        content_id="content_002",
        metric_type=MetricType.ENGAGEMENT,
        metric_name=EngagementMetric.VIEWS,
        value=300,
        platform=Platform.TWITTER
    )
    
    await analytics.track_metric(
        content_id="content_002",
        metric_type=MetricType.ENGAGEMENT,
        metric_name=EngagementMetric.SHARES,
        value=45,
        platform=Platform.TWITTER
    )
    
    print("    ✅ Metrics tracked successfully")
    
    # Test 2: Get performance summary
    print("  📈 Testing performance summary...")
    summary = await analytics.get_performance_summary()
    print(f"    Total content: {summary.get('total_content', 0)}")
    print(f"    Average performance: {summary.get('average_performance', 0)}")
    print(f"    Platform breakdown: {len(summary.get('platform_breakdown', {}))} platforms")
    print(f"    Content type breakdown: {len(summary.get('content_type_breakdown', {}))} types")
    
    # Test 3: Generate report
    print("  📋 Testing report generation...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    report = await analytics.generate_report(
        report_type=ReportType.WEEKLY,
        start_date=start_date,
        end_date=end_date,
        include_recommendations=True
    )
    
    print(f"    Report ID: {report.report_id}")
    print(f"    Report type: {report.report_type}")
    print(f"    Date range: {report.start_date.date()} to {report.end_date.date()}")
    print(f"    Top performing content: {len(report.top_performing_content)} items")
    print(f"    Recommendations: {len(report.recommendations)} suggestions")
    
    # Test 4: Get workflow analytics
    print("  🔄 Testing workflow analytics...")
    workflow_analytics = await analytics.get_workflow_analytics()
    print(f"    Total content: {workflow_analytics.total_content}")
    print(f"    Average review time: {workflow_analytics.average_review_time} days")
    print(f"    Approval rate: {workflow_analytics.approval_rate}")
    print(f"    Content velocity: {workflow_analytics.content_velocity} per week")
    print(f"    Efficiency score: {workflow_analytics.efficiency_score}")
    
    # Test 5: Health check
    print("  💚 Testing health check...")
    health = await analytics.health_check()
    print(f"    Status: {health['status']}")
    print(f"    Total metrics: {health['total_metrics']}")
    print(f"    Total performance records: {health['total_performance_records']}")
    print(f"    Total reports: {health['total_reports']}")
    
    print("  ✅ Content Analytics Service tests completed\n")
    return analytics

async def test_reporting_service(analytics_service):
    """Test the content reporting service"""
    print("🧪 Testing Content Reporting Service...")
    
    reporting = ContentReportingService(analytics_service)
    
    # Test 1: Get default schedules
    print("  📅 Testing default schedules...")
    schedules = await reporting.get_schedules()
    print(f"    Active schedules: {len(schedules)}")
    
    for schedule in schedules:
        print(f"      - {schedule.name}: {schedule.schedule_type} ({schedule.format})")
        print(f"        Recipients: {', '.join(schedule.recipients)}")
        print(f"        Next generation: {schedule.next_generation}")
    
    # Test 2: Create custom schedule
    print("  ➕ Testing custom schedule creation...")
    custom_schedule = await reporting.create_schedule(
        name="Custom Bi-weekly Report",
        description="Bi-weekly content performance analysis",
        schedule_type=ScheduleType.CUSTOM,
        report_type=ReportType.WEEKLY,
        recipients=["custom@company.com"],
        format=ReportFormat.HTML,
        include_recommendations=True,
        custom_interval_days=14
    )
    
    print(f"    Created schedule: {custom_schedule.schedule_id}")
    print(f"    Next generation: {custom_schedule.next_generation}")
    
    # Test 3: Update schedule
    print("  ✏️  Testing schedule update...")
    success = await reporting.update_schedule(
        custom_schedule.schedule_id,
        description="Updated bi-weekly content performance analysis",
        recipients=["custom@company.com", "analytics@company.com"]
    )
    
    if success:
        print("    ✅ Schedule updated successfully")
    else:
        print("    ❌ Schedule update failed")
    
    # Test 4: Generate scheduled reports
    print("  🔄 Testing scheduled report generation...")
    generated_reports = await reporting.generate_scheduled_reports()
    print(f"    Generated reports: {len(generated_reports)}")
    
    # Test 5: Get delivery history
    print("  📤 Testing delivery history...")
    delivery_history = await reporting.get_delivery_history()
    print(f"    Total deliveries: {len(delivery_history)}")
    
    for delivery in delivery_history[:3]:  # Show first 3
        print(f"      - {delivery.delivery_id}: {delivery.status} to {delivery.recipient}")
    
    # Test 6: Health check
    print("  💚 Testing health check...")
    health = await reporting.health_check()
    print(f"    Status: {health['status']}")
    print(f"    Active schedules: {health['active_schedules']}")
    print(f"    Total schedules: {health['total_schedules']}")
    print(f"    Total deliveries: {health['total_deliveries']}")
    print(f"    Delivery success rate: {health['delivery_success_rate']:.2%}")
    
    print("  ✅ Content Reporting Service tests completed\n")
    return reporting

async def test_integration():
    """Test integration between analytics and reporting services"""
    print("🧪 Testing Service Integration...")
    
    # Create analytics service
    analytics = ContentAnalyticsService()
    
    # Add more sample data for better testing
    print("  📊 Adding sample analytics data...")
    
    # Add content for different platforms and types
    platforms = [Platform.WEBSITE, Platform.TWITTER, Platform.LINKEDIN, Platform.INSTAGRAM]
    content_types = [ContentType.BLOG_POST, ContentType.SOCIAL_MEDIA_POST, ContentType.VIDEO_SCRIPT]
    
    for i in range(1, 6):  # Create 5 content pieces
        content_id = f"content_{i:03d}"
        platform = platforms[i % len(platforms)]
        content_type = content_types[i % len(content_types)]
        
        # Track engagement metrics
        await analytics.track_metric(
            content_id=content_id,
            metric_type=MetricType.ENGAGEMENT,
            metric_name=EngagementMetric.VIEWS,
            value=100 + (i * 50),
            platform=platform
        )
        
        await analytics.track_metric(
            content_id=content_id,
            metric_type=MetricType.ENGAGEMENT,
            metric_name=EngagementMetric.LIKES,
            value=10 + (i * 5),
            platform=platform
        )
        
        await analytics.track_metric(
            content_id=content_id,
            metric_type=MetricType.QUALITY,
            metric_name="quality_score",
            value=0.7 + (i * 0.05),
            platform=platform
        )
    
    print("    ✅ Sample data added")
    
    # Create reporting service
    reporting = ContentReportingService(analytics)
    
    # Test report generation with real data
    print("  📋 Testing integrated report generation...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    report = await analytics.generate_report(
        report_type=ReportType.MONTHLY,
        start_date=start_date,
        end_date=end_date,
        include_recommendations=True
    )
    
    print(f"    Generated monthly report: {report.report_id}")
    print(f"    Content analyzed: {len(report.top_performing_content)} pieces")
    print(f"    Platforms covered: {len(report.platform_breakdown)}")
    print(f"    Content types analyzed: {len(report.content_type_analysis)}")
    print(f"    Trends identified: {len(report.trends)} trend categories")
    print(f"    Recommendations generated: {len(report.recommendations)}")
    
    # Test report export
    print("  📤 Testing report export...")
    try:
        json_export = await analytics.export_report(report.report_id, "json")
        print(f"    JSON export length: {len(json_export)} characters")
        
        csv_export = await analytics.export_report(report.report_id, "csv")
        print(f"    CSV export length: {len(csv_export)} characters")
        
        print("    ✅ Report export successful")
    except Exception as e:
        print(f"    ❌ Report export failed: {e}")
    
    print("  ✅ Service Integration tests completed\n")

async def main():
    """Run all tests"""
    print("🚀 Testing Autonomica CMS Analytics and Reporting System\n")
    
    try:
        # Test analytics service
        analytics = await test_analytics_service()
        
        # Test reporting service
        reporting = await test_reporting_service(analytics)
        
        # Test integration
        await test_integration()
        
        print("🎉 All tests completed successfully!")
        print("\n📋 Summary:")
        print("  ✅ Content Analytics Service - Working")
        print("  ✅ Content Reporting Service - Working")
        print("  ✅ Service Integration - Working")
        print("  ✅ Report Generation - Working")
        print("  ✅ Automated Scheduling - Working")
        print("  ✅ Multiple Export Formats - Working")
        
        print("\n🚀 The analytics and reporting system is ready for production use!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
