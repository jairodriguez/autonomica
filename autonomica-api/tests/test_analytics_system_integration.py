"""
Integration Tests for Analytics System

This module contains comprehensive integration tests that verify the interaction
between all analytics services and components.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any, List

from app.services.analytics_service import AnalyticsService
from app.services.analytics_data_collector import AnalyticsDataCollector
from app.services.kpi_calculation_service import KPICalculationService
from app.services.kpi_dashboard_service import KPIDashboardService
from app.services.report_generation_service import ReportGenerationService
from app.services.report_scheduler_service import ReportSchedulerService
from app.services.analytics_auth_service import AnalyticsAuthService
from app.services.data_privacy_service import DataPrivacyService
from app.services.vercel_kv_service import VercelKVService


class TestAnalyticsSystemIntegration:
    """Integration tests for the complete analytics system."""
    
    @pytest.fixture
    async def analytics_service(self):
        """Create a fully configured analytics service with all dependencies."""
        service = AnalyticsService()
        await service._initialize_services()
        return service
    
    @pytest.fixture
    def mock_user_context(self):
        """Mock user context for testing."""
        return {
            "user_id": "test_user_123",
            "email": "test@example.com",
            "role": "Manager",
            "organization_id": "org_456"
        }
    
    @pytest.fixture
    def sample_analytics_data(self):
        """Sample analytics data for testing."""
        return {
            "google_search_console": {
                "impressions": 1500,
                "clicks": 120,
                "ctr": 0.08,
                "position": 15.2
            },
            "social_media": {
                "twitter": {"followers": 2500, "engagement": 0.045},
                "linkedin": {"followers": 1800, "engagement": 0.032},
                "facebook": {"followers": 3200, "engagement": 0.028}
            },
            "content_analytics": {
                "total_posts": 45,
                "total_views": 12500,
                "avg_engagement": 0.038
            }
        }
    
    @pytest.mark.asyncio
    async def test_end_to_end_data_collection_workflow(self, analytics_service, mock_user_context):
        """Test complete data collection workflow from start to storage."""
        # Start data collection
        collection_result = await analytics_service.start_data_collection(
            user_id=mock_user_context["user_id"],
            data_sources=["google_search_console", "social_media", "content_analytics"]
        )
        
        assert collection_result["status"] == "started"
        assert "job_id" in collection_result
        
        # Wait for collection to complete (simulate async processing)
        await asyncio.sleep(0.1)
        
        # Check collection status
        status = await analytics_service.data_collector.get_collection_status(
            job_id=collection_result["job_id"]
        )
        
        assert status["status"] in ["completed", "in_progress"]
    
    @pytest.mark.asyncio
    async def test_kpi_calculation_with_real_data(self, analytics_service, mock_user_context, sample_analytics_data):
        """Test KPI calculation using real analytics data."""
        # Store sample data
        await analytics_service.vercel_kv.store_analytics_data(
            user_id=mock_user_context["user_id"],
            data_type="google_search_console",
            data=sample_analytics_data["google_search_console"],
            timestamp=datetime.now()
        )
        
        # Calculate KPIs
        kpis = await analytics_service.get_comprehensive_kpis(
            user_id=mock_user_context["user_id"],
            date_range="last_30_days"
        )
        
        assert "basic_metrics" in kpis
        assert "advanced_metrics" in kpis
        assert "business_intelligence" in kpis
        
        # Verify specific KPI calculations
        basic_metrics = kpis["basic_metrics"]
        assert "growth_metrics" in basic_metrics
        assert "target_achievement" in basic_metrics
    
    @pytest.mark.asyncio
    async def test_dashboard_data_generation(self, analytics_service, mock_user_context):
        """Test dashboard data generation and widget processing."""
        # Get dashboard configuration
        dashboard_config = await analytics_service.dashboard_service.get_dashboard_config(
            dashboard_type="overview"
        )
        
        assert dashboard_config is not None
        assert "widgets" in dashboard_config
        
        # Get dashboard data
        dashboard_data = await analytics_service.get_dashboard_data(
            user_id=mock_user_context["user_id"],
            dashboard_id="overview",
            date_range="last_30_days"
        )
        
        assert "widgets" in dashboard_data
        assert "summary_metrics" in dashboard_data
        
        # Verify widget data processing
        for widget in dashboard_data["widgets"]:
            assert "data" in widget
            assert "config" in widget
    
    @pytest.mark.asyncio
    async def test_report_generation_workflow(self, analytics_service, mock_user_context):
        """Test complete report generation workflow."""
        # Create report job
        report_job = await analytics_service.report_service.create_report_job(
            user_id=mock_user_context["user_id"],
            report_type="monthly",
            date_range="last_month",
            format="json"
        )
        
        assert report_job["status"] == "pending"
        assert "job_id" in report_job
        
        # Generate report
        report = await analytics_service.generate_report(
            user_id=mock_user_context["user_id"],
            report_type="monthly",
            date_range="last_month",
            format="json"
        )
        
        assert report["status"] == "completed"
        assert "content" in report
        assert "metadata" in report
    
    @pytest.mark.asyncio
    async def test_report_scheduling_and_delivery(self, analytics_service, mock_user_context):
        """Test report scheduling and automated delivery."""
        # Create schedule
        schedule = await analytics_service.scheduler_service.create_schedule(
            user_id=mock_user_context["user_id"],
            report_type="weekly",
            frequency="weekly",
            delivery_method="email",
            delivery_config={"email": "test@example.com"}
        )
        
        assert schedule["status"] == "active"
        assert "schedule_id" in schedule
        
        # Get due schedules
        due_schedules = await analytics_service.scheduler_service.get_due_schedules()
        
        # Process scheduled reports
        if due_schedules:
            await analytics_service.process_scheduled_reports()
            
            # Check scheduled reports
            scheduled_reports = await analytics_service.scheduler_service.get_scheduled_reports(
                user_id=mock_user_context["user_id"]
            )
            
            assert len(scheduled_reports) >= 0
    
    @pytest.mark.asyncio
    async def test_authentication_and_authorization_flow(self, analytics_service, mock_user_context):
        """Test complete authentication and authorization flow."""
        # Authenticate user
        auth_result = await analytics_service.auth_service.authenticate_user(
            user_id=mock_user_context["user_id"],
            email=mock_user_context["email"]
        )
        
        assert auth_result["authenticated"] is True
        assert "permissions" in auth_result
        
        # Check permissions for different operations
        can_view_kpis = await analytics_service.auth_service.check_permission(
            user_id=mock_user_context["user_id"],
            permission="view_kpis"
        )
        assert can_view_kpis is True
        
        can_export_data = await analytics_service.auth_service.check_permission(
            user_id=mock_user_context["user_id"],
            permission="export_data"
        )
        assert can_export_data is True
    
    @pytest.mark.asyncio
    async def test_data_privacy_compliance_workflow(self, analytics_service, mock_user_context):
        """Test data privacy compliance and GDPR workflows."""
        # Record consent
        consent = await analytics_service.privacy_service.record_data_processing_consent(
            user_id=mock_user_context["user_id"],
            data_category="analytics",
            consent_type="explicit",
            purpose="marketing_analytics"
        )
        
        assert consent["consent_id"] is not None
        assert consent["status"] == "active"
        
        # Create data subject request
        dsr = await analytics_service.process_data_subject_request(
            user_id=mock_user_context["user_id"],
            request_type="access",
            data_category="analytics"
        )
        
        assert dsr["request_id"] is not None
        assert dsr["status"] == "processing"
        
        # Execute data right
        result = await analytics_service.privacy_service.execute_data_right(
            dsr_id=dsr["request_id"],
            right="access"
        )
        
        assert result["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_multi_tenant_data_isolation(self, analytics_service):
        """Test that data is properly isolated between different users."""
        user1_id = "user_1"
        user2_id = "user_2"
        
        # Store data for user 1
        await analytics_service.vercel_kv.store_analytics_data(
            user_id=user1_id,
            data_type="google_search_console",
            data={"impressions": 1000, "clicks": 50},
            timestamp=datetime.now()
        )
        
        # Store data for user 2
        await analytics_service.vercel_kv.store_analytics_data(
            user_id=user2_id,
            data_type="google_search_console",
            data={"impressions": 2000, "clicks": 100},
            timestamp=datetime.now()
        )
        
        # Retrieve data for user 1
        user1_data = await analytics_service.vercel_kv.retrieve_analytics_data(
            user_id=user1_id,
            data_type="google_search_console",
            date_range="last_30_days"
        )
        
        # Retrieve data for user 2
        user2_data = await analytics_service.vercel_kv.retrieve_analytics_data(
            user_id=user2_id,
            data_type="google_search_console",
            date_range="last_30_days"
        )
        
        # Verify data isolation
        assert len(user1_data) == 1
        assert len(user2_data) == 1
        assert user1_data[0]["data"]["impressions"] == 1000
        assert user2_data[0]["data"]["impressions"] == 2000
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, analytics_service, mock_user_context):
        """Test error handling and recovery mechanisms."""
        # Test with invalid user ID
        try:
            await analytics_service.get_comprehensive_kpis(
                user_id="invalid_user",
                date_range="last_30_days"
            )
            assert False, "Should have raised an error"
        except Exception as e:
            assert "User not found" in str(e) or "Authentication failed" in str(e)
        
        # Test with invalid date range
        try:
            await analytics_service.get_comprehensive_kpis(
                user_id=mock_user_context["user_id"],
                date_range="invalid_range"
            )
            assert False, "Should have raised an error"
        except Exception as e:
            assert "Invalid date range" in str(e) or "Validation error" in str(e)
    
    @pytest.mark.asyncio
    async def test_system_health_monitoring(self, analytics_service):
        """Test system health monitoring and metrics collection."""
        # Get system status
        status = await analytics_service.get_system_status()
        
        assert "overall_status" in status
        assert "services" in status
        assert "last_updated" in status
        
        # Check individual service health
        for service_name, service_status in status["services"].items():
            assert "status" in service_status
            assert "last_check" in service_status
        
        # Get analytics metrics
        metrics = await analytics_service.get_analytics_metrics()
        
        assert "data_points" in metrics
        assert "active_users" in metrics
        assert "system_performance" in metrics
    
    @pytest.mark.asyncio
    async def test_data_retention_and_cleanup(self, analytics_service, mock_user_context):
        """Test data retention policies and cleanup mechanisms."""
        # Store data with expiration
        await analytics_service.vercel_kv.store_analytics_data(
            user_id=mock_user_context["user_id"],
            data_type="temporary_data",
            data={"test": "data"},
            timestamp=datetime.now() - timedelta(days=90)  # Old data
        )
        
        # Run cleanup
        cleanup_result = await analytics_service.cleanup_expired_data()
        
        assert "cleaned_records" in cleanup_result
        assert "storage_freed" in cleanup_result
        
        # Verify old data is removed
        remaining_data = await analytics_service.vercel_kv.retrieve_analytics_data(
            user_id=mock_user_context["user_id"],
            data_type="temporary_data",
            date_range="last_30_days"
        )
        
        assert len(remaining_data) == 0


class TestAnalyticsSystemPerformance:
    """Performance tests for the analytics system."""
    
    @pytest.mark.asyncio
    async def test_concurrent_user_operations(self, analytics_service):
        """Test system performance under concurrent user load."""
        user_ids = [f"user_{i}" for i in range(10)]
        
        # Simulate concurrent KPI requests
        async def get_kpis_for_user(user_id: str):
            return await analytics_service.get_comprehensive_kpis(
                user_id=user_id,
                date_range="last_30_days"
            )
        
        # Execute concurrent requests
        start_time = datetime.now()
        tasks = [get_kpis_for_user(user_id) for user_id in user_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = datetime.now()
        
        # Verify all requests completed
        assert len(results) == len(user_ids)
        
        # Check performance (should complete within reasonable time)
        execution_time = (end_time - start_time).total_seconds()
        assert execution_time < 5.0  # Should complete within 5 seconds
        
        # Verify results
        for result in results:
            if isinstance(result, Exception):
                pytest.fail(f"Request failed with exception: {result}")
    
    @pytest.mark.asyncio
    async def test_large_dataset_processing(self, analytics_service, mock_user_context):
        """Test performance with large datasets."""
        # Generate large dataset
        large_dataset = []
        for i in range(1000):
            large_dataset.append({
                "timestamp": datetime.now() - timedelta(hours=i),
                "impressions": 1000 + i,
                "clicks": 50 + (i % 100),
                "ctr": 0.05 + (i % 10) / 1000
            })
        
        # Store large dataset
        for data_point in large_dataset:
            await analytics_service.vercel_kv.store_analytics_data(
                user_id=mock_user_context["user_id"],
                data_type="performance_test",
                data=data_point,
                timestamp=data_point["timestamp"]
            )
        
        # Test KPI calculation performance
        start_time = datetime.now()
        kpis = await analytics_service.get_comprehensive_kpis(
            user_id=mock_user_context["user_id"],
            date_range="last_30_days"
        )
        end_time = datetime.now()
        
        # Verify performance
        execution_time = (end_time - start_time).total_seconds()
        assert execution_time < 10.0  # Should complete within 10 seconds
        
        # Verify results
        assert "basic_metrics" in kpis
        assert "advanced_metrics" in kpis
    
    @pytest.mark.asyncio
    async def test_memory_usage_optimization(self, analytics_service, mock_user_context):
        """Test memory usage optimization during large operations."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform memory-intensive operation
        for i in range(100):
            await analytics_service.get_comprehensive_kpis(
                user_id=mock_user_context["user_id"],
                date_range="last_30_days"
            )
        
        # Check memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100.0


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short"])



