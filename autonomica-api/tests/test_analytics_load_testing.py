"""
Load Testing Suite for Analytics System

This module contains comprehensive load tests that verify the analytics system
performance under various load conditions, stress scenarios, and concurrent usage patterns.
"""

import pytest
import asyncio
import time
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Generator
from unittest.mock import AsyncMock, patch, MagicMock
import statistics
import json

from app.services.analytics_service import AnalyticsService
from app.services.analytics_performance_optimizer import AnalyticsPerformanceOptimizer


class TestAnalyticsLoadTesting:
    """Load testing for the analytics system."""
    
    @pytest.fixture
    async def analytics_service(self):
        """Create a fully configured analytics service with performance optimizer."""
        service = AnalyticsService()
        await service._initialize_services()
        
        # Add performance optimizer
        service.performance_optimizer = AnalyticsPerformanceOptimizer()
        
        return service
    
    @pytest.fixture
    def load_test_config(self):
        """Configuration for load tests."""
        return {
            "concurrent_users": 50,
            "requests_per_user": 100,
            "ramp_up_time": 30,  # seconds
            "test_duration": 300,  # seconds
            "think_time": 1.0,  # seconds between requests
            "target_response_time": 2.0,  # seconds
            "target_throughput": 100,  # requests per second
            "max_error_rate": 0.05  # 5%
        }
    
    @pytest.fixture
    def test_data_generator(self):
        """Generate test data for load testing."""
        def generate_user_data(user_id: int) -> Dict[str, Any]:
            return {
                "user_id": f"load_test_user_{user_id}",
                "email": f"user{user_id}@loadtest.com",
                "role": random.choice(["Viewer", "Analyst", "Manager"]),
                "organization_id": f"org_{user_id % 10}"
            }
        
        def generate_analytics_data() -> Dict[str, Any]:
            return {
                "google_search_console": {
                    "impressions": random.randint(100, 10000),
                    "clicks": random.randint(10, 1000),
                    "ctr": random.uniform(0.01, 0.15),
                    "position": random.uniform(1.0, 50.0)
                },
                "social_media": {
                    "twitter": {
                        "followers": random.randint(100, 50000),
                        "engagement": random.uniform(0.01, 0.10)
                    },
                    "linkedin": {
                        "followers": random.randint(100, 30000),
                        "engagement": random.uniform(0.01, 0.08)
                    }
                },
                "content_analytics": {
                    "total_posts": random.randint(10, 200),
                    "total_views": random.randint(1000, 100000),
                    "avg_engagement": random.uniform(0.02, 0.08)
                }
            }
        
        return {
            "generate_user_data": generate_user_data,
            "generate_analytics_data": generate_analytics_data
        }
    
    @pytest.mark.asyncio
    async def test_concurrent_user_load(self, analytics_service, load_test_config, test_data_generator):
        """Test system performance under concurrent user load."""
        print(f"\nStarting concurrent user load test with {load_test_config['concurrent_users']} users")
        
        # Generate test users
        users = [
            test_data_generator["generate_user_data"](i)
            for i in range(load_test_config["concurrent_users"])
        ]
        
        # Track performance metrics
        response_times = []
        errors = []
        start_time = time.time()
        
        async def simulate_user_workload(user_data: Dict[str, Any]) -> Dict[str, Any]:
            """Simulate a single user's workload."""
            user_errors = []
            user_response_times = []
            
            for request_num in range(load_test_config["requests_per_user"]):
                request_start = time.time()
                
                try:
                    # Simulate different types of requests
                    request_type = request_num % 4
                    
                    if request_type == 0:
                        # KPI request
                        result = await analytics_service.get_comprehensive_kpis(
                            user_id=user_data["user_id"],
                            date_range="last_30_days"
                        )
                    elif request_type == 1:
                        # Dashboard request
                        result = await analytics_service.get_dashboard_data(
                            user_id=user_data["user_id"],
                            dashboard_id="overview",
                            date_range="last_30_days"
                        )
                    elif request_type == 2:
                        # Report generation
                        result = await analytics_service.generate_report(
                            user_id=user_data["user_id"],
                            report_type="weekly",
                            date_range="last_week",
                            format="json"
                        )
                    else:
                        # System status
                        result = await analytics_service.get_system_status()
                    
                    request_time = time.time() - request_start
                    user_response_times.append(request_time)
                    
                    # Add think time between requests
                    await asyncio.sleep(load_test_config["think_time"])
                    
                except Exception as e:
                    user_errors.append({
                        "request_num": request_num,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
            
            return {
                "user_id": user_data["user_id"],
                "response_times": user_response_times,
                "errors": user_errors,
                "total_requests": load_test_config["requests_per_user"]
            }
        
        # Execute concurrent user workloads
        print("Executing concurrent user workloads...")
        user_results = await asyncio.gather(
            *[simulate_user_workload(user) for user in users],
            return_exceptions=True
        )
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Aggregate results
        for result in user_results:
            if isinstance(result, Exception):
                errors.append({"type": "user_workload_failed", "error": str(result)})
            else:
                response_times.extend(result["response_times"])
                errors.extend(result["errors"])
        
        # Calculate performance metrics
        total_requests = len(users) * load_test_config["requests_per_user"]
        successful_requests = total_requests - len(errors)
        error_rate = len(errors) / total_requests if total_requests > 0 else 0
        
        avg_response_time = statistics.mean(response_times) if response_times else 0
        p95_response_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else 0
        p99_response_time = statistics.quantiles(response_times, n=100)[98] if len(response_times) >= 100 else 0
        
        throughput = successful_requests / total_duration if total_duration > 0 else 0
        
        # Print results
        print(f"\nLoad Test Results:")
        print(f"Total Duration: {total_duration:.2f} seconds")
        print(f"Total Requests: {total_requests}")
        print(f"Successful Requests: {successful_requests}")
        print(f"Error Rate: {error_rate:.2%}")
        print(f"Average Response Time: {avg_response_time:.3f} seconds")
        print(f"95th Percentile Response Time: {p95_response_time:.3f} seconds")
        print(f"99th Percentile Response Time: {p99_response_time:.3f} seconds")
        print(f"Throughput: {throughput:.2f} requests/second")
        
        # Assertions for load test success
        assert error_rate <= load_test_config["max_error_rate"], f"Error rate {error_rate:.2%} exceeds maximum {load_test_config['max_error_rate']:.2%}"
        assert avg_response_time <= load_test_config["target_response_time"], f"Average response time {avg_response_time:.3f}s exceeds target {load_test_config['target_response_time']}s"
        assert throughput >= load_test_config["target_throughput"], f"Throughput {throughput:.2f} rps below target {load_test_config['target_throughput']} rps"
        
        print("✅ Load test passed all performance criteria!")
    
    @pytest.mark.asyncio
    async def test_stress_testing(self, analytics_service, test_data_generator):
        """Test system behavior under extreme stress conditions."""
        print("\nStarting stress test...")
        
        # Generate extreme load
        extreme_users = 100
        extreme_requests = 500
        
        users = [
            test_data_generator["generate_user_data"](i)
            for i in range(extreme_users)
        ]
        
        # Track system behavior under stress
        response_times = []
        errors = []
        system_statuses = []
        
        async def extreme_workload(user_data: Dict[str, Any]) -> Dict[str, Any]:
            """Execute extreme workload for a user."""
            user_results = []
            
            for i in range(extreme_requests):
                try:
                    start_time = time.time()
                    
                    # Mix of different operations
                    operation = i % 5
                    
                    if operation == 0:
                        # Heavy KPI calculation
                        result = await analytics_service.get_comprehensive_kpis(
                            user_id=user_data["user_id"],
                            date_range="last_90_days"
                        )
                    elif operation == 1:
                        # Complex dashboard
                        result = await analytics_service.get_dashboard_data(
                            user_id=user_data["user_id"],
                            dashboard_id="performance",
                            date_range="last_90_days"
                        )
                    elif operation == 2:
                        # Large report
                        result = await analytics_service.generate_report(
                            user_id=user_data["user_id"],
                            report_type="monthly",
                            date_range="last_quarter",
                            format="json"
                        )
                    elif operation == 3:
                        # System metrics
                        result = await analytics_service.get_analytics_metrics()
                    else:
                        # Performance optimization
                        result = await analytics_service.performance_optimizer.optimize_performance(
                            "stress_test_operation",
                            user_id=user_data["user_id"]
                        )
                    
                    response_time = time.time() - start_time
                    user_results.append({
                        "operation": operation,
                        "response_time": response_time,
                        "success": True
                    })
                    
                except Exception as e:
                    user_results.append({
                        "operation": operation,
                        "response_time": 0,
                        "success": False,
                        "error": str(e)
                    })
            
            return {
                "user_id": user_data["user_id"],
                "results": user_results
            }
        
        # Execute extreme workloads
        print(f"Executing extreme workloads: {extreme_users} users × {extreme_requests} requests each")
        
        start_time = time.time()
        user_results = await asyncio.gather(
            *[extreme_workload(user) for user in users],
            return_exceptions=True
        )
        end_time = time.time()
        
        # Analyze results
        total_requests = 0
        successful_requests = 0
        failed_requests = 0
        
        for result in user_results:
            if isinstance(result, Exception):
                failed_requests += 1
            else:
                for op_result in result["results"]:
                    total_requests += 1
                    if op_result["success"]:
                        successful_requests += 1
                        response_times.append(op_result["response_time"])
                    else:
                        failed_requests += 1
        
        # Calculate stress test metrics
        total_duration = end_time - start_time
        success_rate = successful_requests / total_requests if total_requests > 0 else 0
        failure_rate = failed_requests / total_requests if total_requests > 0 else 0
        
        avg_response_time = statistics.mean(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        
        throughput = total_requests / total_duration if total_duration > 0 else 0
        
        # Print stress test results
        print(f"\nStress Test Results:")
        print(f"Total Duration: {total_duration:.2f} seconds")
        print(f"Total Requests: {total_requests}")
        print(f"Successful Requests: {successful_requests}")
        print(f"Failed Requests: {failed_requests}")
        print(f"Success Rate: {success_rate:.2%}")
        print(f"Failure Rate: {failure_rate:.2%}")
        print(f"Average Response Time: {avg_response_time:.3f} seconds")
        print(f"Min Response Time: {min_response_time:.3f} seconds")
        print(f"Max Response Time: {max_response_time:.3f} seconds")
        print(f"Throughput: {throughput:.2f} requests/second")
        
        # Stress test should maintain reasonable performance
        assert success_rate >= 0.8, f"Success rate {success_rate:.2%} below acceptable threshold 80%"
        assert avg_response_time <= 10.0, f"Average response time {avg_response_time:.3f}s too high under stress"
        
        print("✅ Stress test completed successfully!")
    
    @pytest.mark.asyncio
    async def test_endurance_testing(self, analytics_service, test_data_generator):
        """Test system stability over extended periods."""
        print("\nStarting endurance test...")
        
        # Test duration: 5 minutes with continuous load
        test_duration = 300  # seconds
        check_interval = 30  # seconds
        
        users = [
            test_data_generator["generate_user_data"](i)
            for i in range(20)  # Moderate number of users
        ]
        
        # Track performance over time
        performance_history = []
        start_time = time.time()
        
        async def continuous_workload(user_data: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
            """Generate continuous workload for endurance testing."""
            request_count = 0
            
            while time.time() - start_time < test_duration:
                try:
                    request_start = time.time()
                    request_count += 1
                    
                    # Rotate through different operations
                    operation = request_count % 4
                    
                    if operation == 0:
                        result = await analytics_service.get_comprehensive_kpis(
                            user_id=user_data["user_id"],
                            date_range="last_30_days"
                        )
                    elif operation == 1:
                        result = await analytics_service.get_dashboard_data(
                            user_id=user_data["user_id"],
                            dashboard_id="overview",
                            date_range="last_30_days"
                        )
                    elif operation == 2:
                        result = await analytics_service.get_system_status()
                    else:
                        result = await analytics_service.get_analytics_metrics()
                    
                    response_time = time.time() - request_start
                    
                    yield {
                        "timestamp": time.time() - start_time,
                        "user_id": user_data["user_id"],
                        "operation": operation,
                        "response_time": response_time,
                        "success": True,
                        "request_count": request_count
                    }
                    
                    # Small delay between requests
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    yield {
                        "timestamp": time.time() - start_time,
                        "user_id": user_data["user_id"],
                        "operation": operation,
                        "response_time": 0,
                        "success": False,
                        "error": str(e),
                        "request_count": request_count
                    }
        
        # Execute endurance test
        print(f"Running endurance test for {test_duration} seconds...")
        
        async def monitor_performance():
            """Monitor system performance during endurance test."""
            while time.time() - start_time < test_duration:
                await asyncio.sleep(check_interval)
                
                # Check system health
                try:
                    system_status = await analytics_service.get_system_status()
                    performance_metrics = await analytics_service.performance_optimizer.get_performance_summary()
                    
                    current_time = time.time() - start_time
                    print(f"Endurance test progress: {current_time:.0f}s / {test_duration}s - System status: {system_status.get('overall_status', 'unknown')}")
                    
                except Exception as e:
                    print(f"Health check failed at {time.time() - start_time:.0f}s: {e}")
        
        # Start performance monitoring
        monitor_task = asyncio.create_task(monitor_performance())
        
        # Execute continuous workloads
        workload_tasks = []
        for user in users:
            workload_gen = continuous_workload(user)
            task = asyncio.create_task(self._collect_workload_results(workload_gen))
            workload_tasks.append(task)
        
        # Wait for all workloads to complete
        workload_results = await asyncio.gather(*workload_tasks, return_exceptions=True)
        
        # Cancel monitoring task
        monitor_task.cancel()
        
        # Analyze endurance test results
        all_results = []
        for result in workload_results:
            if isinstance(result, Exception):
                print(f"Workload failed: {result}")
            else:
                all_results.extend(result)
        
        # Calculate endurance metrics
        total_requests = len(all_results)
        successful_requests = len([r for r in all_results if r["success"]])
        failed_requests = total_requests - successful_requests
        
        success_rate = successful_requests / total_requests if total_requests > 0 else 0
        
        # Analyze performance over time
        time_periods = []
        for i in range(0, test_duration, check_interval):
            period_results = [r for r in all_results if i <= r["timestamp"] < i + check_interval]
            if period_results:
                period_success_rate = len([r for r in period_results if r["success"]]) / len(period_results)
                avg_response_time = statistics.mean([r["response_time"] for r in period_results if r["success"]])
                
                time_periods.append({
                    "period": f"{i}-{i+check_interval}s",
                    "success_rate": period_success_rate,
                    "avg_response_time": avg_response_time,
                    "request_count": len(period_results)
                })
        
        # Print endurance test results
        print(f"\nEndurance Test Results:")
        print(f"Total Duration: {test_duration} seconds")
        print(f"Total Requests: {total_requests}")
        print(f"Successful Requests: {successful_requests}")
        print(f"Failed Requests: {failed_requests}")
        print(f"Overall Success Rate: {success_rate:.2%}")
        
        print(f"\nPerformance by Time Period:")
        for period in time_periods:
            print(f"  {period['period']}: {period['success_rate']:.2%} success, "
                  f"{period['avg_response_time']:.3f}s avg response, "
                  f"{period['request_count']} requests")
        
        # Endurance test should maintain consistent performance
        assert success_rate >= 0.9, f"Endurance test success rate {success_rate:.2%} below threshold 90%"
        
        # Check for performance degradation
        if len(time_periods) >= 2:
            first_period = time_periods[0]
            last_period = time_periods[-1]
            
            success_rate_degradation = first_period["success_rate"] - last_period["success_rate"]
            response_time_degradation = last_period["avg_response_time"] - first_period["avg_response_time"]
            
            assert success_rate_degradation <= 0.1, f"Success rate degraded by {success_rate_degradation:.2%} over time"
            assert response_time_degradation <= 2.0, f"Response time degraded by {response_time_degradation:.3f}s over time"
        
        print("✅ Endurance test completed successfully!")
    
    async def _collect_workload_results(self, workload_gen) -> List[Dict[str, Any]]:
        """Collect results from a workload generator."""
        results = []
        try:
            async for result in workload_gen:
                results.append(result)
        except Exception as e:
            print(f"Workload generator failed: {e}")
        return results
    
    @pytest.mark.asyncio
    async def test_memory_leak_detection(self, analytics_service, test_data_generator):
        """Test for memory leaks during extended usage."""
        print("\nStarting memory leak detection test...")
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Baseline memory usage
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        print(f"Baseline memory usage: {baseline_memory:.2f} MB")
        
        # Generate sustained load
        users = [
            test_data_generator["generate_user_data"](i)
            for i in range(10)
        ]
        
        memory_samples = [baseline_memory]
        
        async def memory_test_workload(user_data: Dict[str, Any]):
            """Execute workload while monitoring memory usage."""
            for i in range(100):
                try:
                    # Execute various operations
                    await analytics_service.get_comprehensive_kpis(
                        user_id=user_data["user_id"],
                        date_range="last_30_days"
                    )
                    
                    await analytics_service.get_dashboard_data(
                        user_id=user_data["user_id"],
                        dashboard_id="overview",
                        date_range="last_30_days"
                    )
                    
                    await analytics_service.get_system_status()
                    
                    # Sample memory every 10 operations
                    if i % 10 == 0:
                        current_memory = process.memory_info().rss / 1024 / 1024
                        memory_samples.append(current_memory)
                        print(f"Memory sample {len(memory_samples)}: {current_memory:.2f} MB")
                    
                    await asyncio.sleep(0.01)  # Small delay
                    
                except Exception as e:
                    print(f"Memory test workload failed: {e}")
        
        # Execute memory test workloads
        print("Executing memory test workloads...")
        await asyncio.gather(
            *[memory_test_workload(user) for user in users],
            return_exceptions=True
        )
        
        # Final memory measurement
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_samples.append(final_memory)
        
        # Analyze memory usage
        memory_increase = final_memory - baseline_memory
        memory_growth_rate = memory_increase / len(memory_samples) if len(memory_samples) > 1 else 0
        
        print(f"\nMemory Leak Detection Results:")
        print(f"Baseline memory: {baseline_memory:.2f} MB")
        print(f"Final memory: {final_memory:.2f} MB")
        print(f"Total memory increase: {memory_increase:.2f} MB")
        print(f"Memory growth rate: {memory_growth_rate:.4f} MB per sample")
        
        # Memory samples over time
        print(f"Memory samples: {[f'{m:.2f}' for m in memory_samples]}")
        
        # Check for memory leaks
        # Memory increase should be reasonable (less than 100MB for this test)
        assert memory_increase < 100.0, f"Memory increase {memory_increase:.2f}MB exceeds threshold 100MB"
        
        # Memory growth rate should be minimal
        assert memory_growth_rate < 5.0, f"Memory growth rate {memory_growth_rate:.4f}MB/sample too high"
        
        print("✅ Memory leak detection test passed!")
    
    @pytest.mark.asyncio
    async def test_concurrent_database_operations(self, analytics_service, test_data_generator):
        """Test concurrent database operations and connection handling."""
        print("\nStarting concurrent database operations test...")
        
        # Test with high concurrency
        concurrent_operations = 100
        users = [
            test_data_generator["generate_user_data"](i)
            for i in range(concurrent_operations)
        ]
        
        async def database_operation(user_data: Dict[str, Any]) -> Dict[str, Any]:
            """Execute database operations for a user."""
            start_time = time.time()
            
            try:
                # Simulate database-intensive operations
                operations = []
                
                # Store analytics data
                analytics_data = test_data_generator["generate_analytics_data"]()
                await analytics_service.vercel_kv.store_analytics_data(
                    user_id=user_data["user_id"],
                    data_type="load_test",
                    data=analytics_data,
                    timestamp=datetime.now()
                )
                operations.append("store_data")
                
                # Retrieve analytics data
                retrieved_data = await analytics_service.vercel_kv.retrieve_analytics_data(
                    user_id=user_data["user_id"],
                    data_type="load_test",
                    date_range="last_30_days"
                )
                operations.append("retrieve_data")
                
                # Calculate KPIs
                kpis = await analytics_service.get_comprehensive_kpis(
                    user_id=user_data["user_id"],
                    date_range="last_30_days"
                )
                operations.append("calculate_kpis")
                
                # Generate report
                report = await analytics_service.generate_report(
                    user_id=user_data["user_id"],
                    report_type="weekly",
                    date_range="last_week",
                    format="json"
                )
                operations.append("generate_report")
                
                response_time = time.time() - start_time
                
                return {
                    "user_id": user_data["user_id"],
                    "success": True,
                    "operations": operations,
                    "response_time": response_time
                }
                
            except Exception as e:
                response_time = time.time() - start_time
                return {
                    "user_id": user_data["user_id"],
                    "success": False,
                    "error": str(e),
                    "response_time": response_time
                }
        
        # Execute concurrent database operations
        print(f"Executing {concurrent_operations} concurrent database operations...")
        
        start_time = time.time()
        results = await asyncio.gather(
            *[database_operation(user) for user in users],
            return_exceptions=True
        )
        end_time = time.time()
        
        # Analyze results
        total_operations = len(results)
        successful_operations = len([r for r in results if isinstance(r, dict) and r.get("success", False)])
        failed_operations = total_operations - successful_operations
        
        response_times = [r["response_time"] for r in results if isinstance(r, dict) and r.get("success", False)]
        
        success_rate = successful_operations / total_operations if total_operations > 0 else 0
        avg_response_time = statistics.mean(response_times) if response_times else 0
        total_duration = end_time - start_time
        throughput = total_operations / total_duration if total_duration > 0 else 0
        
        # Print results
        print(f"\nConcurrent Database Operations Test Results:")
        print(f"Total Operations: {total_operations}")
        print(f"Successful Operations: {successful_operations}")
        print(f"Failed Operations: {failed_operations}")
        print(f"Success Rate: {success_rate:.2%}")
        print(f"Average Response Time: {avg_response_time:.3f} seconds")
        print(f"Total Duration: {total_duration:.2f} seconds")
        print(f"Throughput: {throughput:.2f} operations/second")
        
        # Assertions
        assert success_rate >= 0.95, f"Database operations success rate {success_rate:.2%} below threshold 95%"
        assert avg_response_time <= 5.0, f"Average database operation time {avg_response_time:.3f}s too high"
        
        print("✅ Concurrent database operations test passed!")


if __name__ == "__main__":
    # Run load tests
    pytest.main([__file__, "-v", "--tb=short"])



