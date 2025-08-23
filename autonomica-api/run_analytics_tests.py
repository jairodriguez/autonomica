#!/usr/bin/env python3
"""
Analytics System Test Runner

This script orchestrates comprehensive testing of the analytics system including:
- Unit tests
- Integration tests
- Load tests
- Performance tests
- System optimization tests

Usage:
    python run_analytics_tests.py [--unit] [--integration] [--load] [--performance] [--all]
"""

import asyncio
import sys
import time
import argparse
import subprocess
from pathlib import Path
from typing import List, Dict, Any
import json
import os

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))


class AnalyticsTestRunner:
    """Comprehensive test runner for the analytics system."""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()
        self.test_suites = {
            "unit": "tests/test_analytics_system.py",
            "integration": "tests/test_analytics_system_integration.py",
            "load": "tests/test_analytics_load_testing.py",
            "performance": "tests/test_analytics_system.py::TestAnalyticsSystemPerformance"
        }
        
        # Test configuration
        self.test_config = {
            "unit": {
                "enabled": True,
                "timeout": 300,  # 5 minutes
                "parallel": True,
                "verbose": True
            },
            "integration": {
                "enabled": True,
                "timeout": 600,  # 10 minutes
                "parallel": False,  # Integration tests should run sequentially
                "verbose": True
            },
            "load": {
                "enabled": False,  # Disabled by default due to resource requirements
                "timeout": 1800,  # 30 minutes
                "parallel": False,
                "verbose": True
            },
            "performance": {
                "enabled": True,
                "timeout": 900,  # 15 minutes
                "parallel": True,
                "verbose": True
            }
        }
    
    async def run_tests(self, test_types: List[str] = None) -> Dict[str, Any]:
        """Run the specified test types."""
        if test_types is None:
            test_types = ["unit", "integration", "performance"]
        
        print(f"🚀 Starting Analytics System Test Suite")
        print(f"📅 Test started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Test types: {', '.join(test_types)}")
        print("=" * 80)
        
        results = {}
        
        for test_type in test_types:
            if test_type in self.test_suites and self.test_config[test_type]["enabled"]:
                print(f"\n🔍 Running {test_type.upper()} tests...")
                try:
                    result = await self._run_test_suite(test_type)
                    results[test_type] = result
                    print(f"✅ {test_type.upper()} tests completed: {result['status']}")
                except Exception as e:
                    print(f"❌ {test_type.upper()} tests failed: {e}")
                    results[test_type] = {
                        "status": "failed",
                        "error": str(e),
                        "duration": 0
                    }
            else:
                print(f"⚠️  {test_type.upper()} tests are disabled or not found")
        
        # Generate comprehensive report
        await self._generate_test_report(results)
        
        return results
    
    async def _run_test_suite(self, test_type: str) -> Dict[str, Any]:
        """Run a specific test suite."""
        test_file = self.test_suites[test_type]
        config = self.test_config[test_type]
        
        if not Path(test_file).exists():
            return {
                "status": "skipped",
                "reason": f"Test file not found: {test_file}",
                "duration": 0
            }
        
        start_time = time.time()
        
        # Build pytest command
        cmd = [
            "python", "-m", "pytest",
            test_file,
            "-v" if config["verbose"] else "",
            "--tb=short",
            "--timeout", str(config["timeout"]),
            "--durations=10",  # Show top 10 slowest tests
            "--maxfail=5",  # Stop after 5 failures
        ]
        
        if config["parallel"]:
            cmd.extend(["-n", "auto"])  # Use auto-detected number of workers
        
        # Filter out empty strings
        cmd = [arg for arg in cmd if arg]
        
        print(f"Running command: {' '.join(cmd)}")
        
        try:
            # Run the test suite
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=Path(__file__).parent
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=config["timeout"]
            )
            
            duration = time.time() - start_time
            
            # Parse test results
            result = self._parse_test_output(stdout.decode(), stderr.decode(), process.returncode)
            result["duration"] = duration
            result["command"] = " ".join(cmd)
            
            return result
            
        except asyncio.TimeoutError:
            return {
                "status": "timeout",
                "error": f"Test suite exceeded {config['timeout']} second timeout",
                "duration": config["timeout"]
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "duration": time.time() - start_time
            }
    
    def _parse_test_output(self, stdout: str, stderr: str, return_code: int) -> Dict[str, Any]:
        """Parse pytest output to extract test results."""
        lines = stdout.split('\n')
        
        # Extract test summary
        test_summary = {}
        for line in lines:
            if "passed" in line and "failed" in line:
                # Parse line like "10 passed, 2 failed, 1 skipped in 45.67s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.isdigit():
                        if "passed" in parts[i+1]:
                            test_summary["passed"] = int(part)
                        elif "failed" in parts[i+1]:
                            test_summary["failed"] = int(part)
                        elif "skipped" in parts[i+1]:
                            test_summary["skipped"] = int(part)
                break
        
        # Determine overall status
        if return_code == 0:
            status = "passed"
        elif return_code == 1:
            status = "failed"
        elif return_code == 2:
            status = "error"
        else:
            status = "unknown"
        
        # Extract error details if any
        errors = []
        if stderr:
            error_lines = stderr.split('\n')
            for line in error_lines:
                if line.strip() and "Error" in line:
                    errors.append(line.strip())
        
        return {
            "status": status,
            "return_code": return_code,
            "test_summary": test_summary,
            "stdout": stdout,
            "stderr": stderr,
            "errors": errors
        }
    
    async def _generate_test_report(self, results: Dict[str, Any]):
        """Generate a comprehensive test report."""
        print("\n" + "=" * 80)
        print("📊 ANALYTICS SYSTEM TEST REPORT")
        print("=" * 80)
        
        total_duration = time.time() - self.start_time
        
        # Summary statistics
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        skipped_tests = 0
        
        for test_type, result in results.items():
            if result["status"] == "passed":
                summary = result.get("test_summary", {})
                total_tests += summary.get("passed", 0) + summary.get("failed", 0) + summary.get("skipped", 0)
                passed_tests += summary.get("passed", 0)
                failed_tests += summary.get("failed", 0)
                skipped_tests += summary.get("skipped", 0)
        
        # Print summary
        print(f"📈 Test Summary:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Skipped: {skipped_tests} ⏭️")
        print(f"   Total Duration: {total_duration:.2f} seconds")
        
        # Detailed results by test type
        print(f"\n🔍 Detailed Results:")
        for test_type, result in results.items():
            status_emoji = "✅" if result["status"] == "passed" else "❌" if result["status"] == "failed" else "⚠️"
            print(f"   {test_type.upper()}: {status_emoji} {result['status'].upper()}")
            
            if result["status"] == "passed" and "test_summary" in result:
                summary = result["test_summary"]
                print(f"      Passed: {summary.get('passed', 0)}, Failed: {summary.get('failed', 0)}, Skipped: {summary.get('skipped', 0)}")
                print(f"      Duration: {result['duration']:.2f}s")
            
            if result["status"] == "failed" and "errors" in result:
                print(f"      Errors: {len(result['errors'])}")
                for error in result["errors"][:3]:  # Show first 3 errors
                    print(f"        - {error}")
        
        # Performance insights
        print(f"\n⚡ Performance Insights:")
        for test_type, result in results.items():
            if result["status"] == "passed" and result["duration"] > 0:
                if test_type == "unit":
                    expected_duration = 60  # 1 minute
                elif test_type == "integration":
                    expected_duration = 300  # 5 minutes
                elif test_type == "performance":
                    expected_duration = 600  # 10 minutes
                else:
                    expected_duration = 300
                
                if result["duration"] <= expected_duration:
                    print(f"   {test_type.upper()}: 🚀 Fast execution ({result['duration']:.2f}s)")
                elif result["duration"] <= expected_duration * 1.5:
                    print(f"   {test_type.upper()}: ⚡ Good performance ({result['duration']:.2f}s)")
                else:
                    print(f"   {test_type.upper()}: 🐌 Slow execution ({result['duration']:.2f}s) - consider optimization")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if failed_tests > 0:
            print("   🔧 Fix failing tests before deployment")
        
        if total_duration > 600:  # More than 10 minutes
            print("   ⚡ Consider parallelizing tests or optimizing slow test cases")
        
        if any(r["status"] == "timeout" for r in results.values()):
            print("   ⏰ Increase timeout values for long-running tests")
        
        if all(r["status"] == "passed" for r in results.values()):
            print("   🎉 All tests passed! Ready for deployment")
        
        # Save detailed report to file
        report_file = Path(__file__).parent / "test_report.json"
        with open(report_file, 'w') as f:
            json.dump({
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
                "total_duration": total_duration,
                "summary": {
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "skipped": skipped_tests
                },
                "results": results
            }, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        print("=" * 80)
    
    async def run_quick_health_check(self) -> Dict[str, Any]:
        """Run a quick health check of the analytics system."""
        print("🏥 Running Quick Health Check...")
        
        try:
            # Import and test core services
            from app.services.analytics_service import AnalyticsService
            from app.services.analytics_performance_optimizer import AnalyticsPerformanceOptimizer
            
            # Test service initialization
            service = AnalyticsService()
            await service._initialize_services()
            
            # Test basic functionality
            status = await service.get_system_status()
            
            return {
                "status": "healthy",
                "system_status": status,
                "message": "Core services are operational"
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "message": "Core services are not operational"
            }
    
    async def run_performance_benchmark(self) -> Dict[str, Any]:
        """Run a quick performance benchmark."""
        print("📊 Running Performance Benchmark...")
        
        try:
            from app.services.analytics_service import AnalyticsService
            from app.services.analytics_performance_optimizer import AnalyticsPerformanceOptimizer
            
            service = AnalyticsService()
            await service._initialize_services()
            
            # Benchmark KPI calculation
            start_time = time.time()
            kpis = await service.get_comprehensive_kpis(
                user_id="benchmark_user",
                date_range="last_30_days"
            )
            kpi_time = time.time() - start_time
            
            # Benchmark dashboard generation
            start_time = time.time()
            dashboard = await service.get_dashboard_data(
                user_id="benchmark_user",
                dashboard_id="overview",
                date_range="last_30_days"
            )
            dashboard_time = time.time() - start_time
            
            # Benchmark system status
            start_time = time.time()
            status = await service.get_system_status()
            status_time = time.time() - start_time
            
            return {
                "status": "completed",
                "benchmarks": {
                    "kpi_calculation": f"{kpi_time:.3f}s",
                    "dashboard_generation": f"{dashboard_time:.3f}s",
                    "system_status": f"{status_time:.3f}s"
                },
                "performance_score": "good" if max(kpi_time, dashboard_time, status_time) < 1.0 else "needs_optimization"
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }


async def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(description="Analytics System Test Runner")
    parser.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--load", action="store_true", help="Run load tests")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--health-check", action="store_true", help="Run quick health check")
    parser.add_argument("--benchmark", action="store_true", help="Run performance benchmark")
    
    args = parser.parse_args()
    
    runner = AnalyticsTestRunner()
    
    if args.health_check:
        result = await runner.run_quick_health_check()
        print(f"Health Check Result: {result}")
        return
    
    if args.benchmark:
        result = await runner.run_performance_benchmark()
        print(f"Benchmark Result: {result}")
        return
    
    # Determine which tests to run
    if args.all:
        test_types = ["unit", "integration", "performance"]
        if args.load:
            test_types.append("load")
    else:
        test_types = []
        if args.unit:
            test_types.append("unit")
        if args.integration:
            test_types.append("integration")
        if args.load:
            test_types.append("load")
        if args.performance:
            test_types.append("performance")
    
    # Default to unit and integration tests if none specified
    if not test_types:
        test_types = ["unit", "integration"]
    
    # Run the tests
    results = await runner.run_tests(test_types)
    
    # Exit with appropriate code
    if any(r["status"] == "failed" for r in results.values()):
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())



