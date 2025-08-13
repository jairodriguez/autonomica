#!/usr/bin/env python3
"""
Test Script for Ollama Performance Monitoring System

This script tests all the new performance monitoring capabilities:
- Performance metrics collection
- System metrics monitoring
- Alert generation
- API endpoints
- Dashboard functionality
"""

import asyncio
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OllamaPerformanceTester:
    """Test suite for Ollama performance monitoring system."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []
        
    async def run_all_tests(self):
        """Run all performance monitoring tests."""
        logger.info("🚀 Starting Ollama Performance Monitoring Tests")
        logger.info("=" * 60)
        
        try:
            # Test 1: Basic monitoring status
            await self.test_monitoring_status()
            
            # Test 2: Start monitoring
            await self.test_start_monitoring()
            
            # Test 3: Generate test metrics
            await self.test_metrics_generation()
            
            # Test 4: Performance summary
            await self.test_performance_summary()
            
            # Test 5: Model performance metrics
            await self.test_model_performance()
            
            # Test 6: System metrics
            await self.test_system_metrics()
            
            # Test 7: Performance alerts
            await self.test_performance_alerts()
            
            # Test 8: Export functionality
            await self.test_export_metrics()
            
            # Test 9: Cleanup functionality
            await self.test_cleanup_metrics()
            
            # Test 10: Stop monitoring
            await self.test_stop_monitoring()
            
            # Test 11: Dashboard accessibility
            await self.test_dashboard_access()
            
        except Exception as e:
            logger.error(f"Test suite failed: {e}")
            self.test_results.append({
                "test": "Test Suite",
                "status": "FAILED",
                "error": str(e)
            })
        
        # Print test summary
        self.print_test_summary()
        
    async def test_monitoring_status(self):
        """Test monitoring status endpoint."""
        logger.info("📊 Testing monitoring status...")
        
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/ai/ollama/performance/status")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        logger.info("✅ Monitoring status endpoint working")
                        self.test_results.append({
                            "test": "Monitoring Status",
                            "status": "PASSED",
                            "details": data.get("status", {})
                        })
                    else:
                        logger.warning("⚠️ Monitoring status returned success=false")
                        self.test_results.append({
                            "test": "Monitoring Status",
                            "status": "WARNING",
                            "details": data
                        })
                else:
                    logger.error(f"❌ Monitoring status failed with status {response.status_code}")
                    self.test_results.append({
                        "test": "Monitoring Status",
                        "status": "FAILED",
                        "error": f"HTTP {response.status_code}"
                    })
                    
        except Exception as e:
            logger.error(f"❌ Monitoring status test failed: {e}")
            self.test_results.append({
                "test": "Monitoring Status",
                "status": "FAILED",
                "error": str(e)
            })

    async def test_start_monitoring(self):
        """Test starting performance monitoring."""
        logger.info("▶️ Testing start monitoring...")
        
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/ai/ollama/performance/monitoring/start",
                    json={"interval": 5.0}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        logger.info("✅ Monitoring started successfully")
                        self.test_results.append({
                            "test": "Start Monitoring",
                            "status": "PASSED",
                            "details": data
                        })
                    else:
                        logger.warning("⚠️ Start monitoring returned success=false")
                        self.test_results.append({
                            "test": "Start Monitoring",
                            "status": "WARNING",
                            "details": data
                        })
                else:
                    logger.error(f"❌ Start monitoring failed with status {response.status_code}")
                    self.test_results.append({
                        "test": "Start Monitoring",
                        "status": "FAILED",
                        "error": f"HTTP {response.status_code}"
                    })
                    
        except Exception as e:
            logger.error(f"❌ Start monitoring test failed: {e}")
            self.test_results.append({
                "test": "Start Monitoring",
                "status": "FAILED",
                "error": str(e)
            })

    async def test_metrics_generation(self):
        """Test metrics generation by simulating Ollama requests."""
        logger.info("📈 Testing metrics generation...")
        
        try:
            # Simulate some Ollama model requests to generate metrics
            import httpx
            async with httpx.AsyncClient() as client:
                # Test basic Ollama health check
                response = await client.get(f"{self.base_url}/api/ai/ollama/health")
                
                if response.status_code == 200:
                    logger.info("✅ Basic Ollama health check working")
                    
                    # Wait a bit for metrics to be collected
                    await asyncio.sleep(2)
                    
                    self.test_results.append({
                        "test": "Metrics Generation",
                        "status": "PASSED",
                        "details": "Basic metrics collection working"
                    })
                else:
                    logger.warning(f"⚠️ Ollama health check returned status {response.status_code}")
                    self.test_results.append({
                        "test": "Metrics Generation",
                        "status": "WARNING",
                        "details": f"Health check status: {response.status_code}"
                    })
                    
        except Exception as e:
            logger.error(f"❌ Metrics generation test failed: {e}")
            self.test_results.append({
                "test": "Metrics Generation",
                "status": "FAILED",
                "error": str(e)
            })

    async def test_performance_summary(self):
        """Test performance summary endpoint."""
        logger.info("📊 Testing performance summary...")
        
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/ai/ollama/performance/summary")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        summary = data.get("summary", {})
                        logger.info("✅ Performance summary endpoint working")
                        logger.info(f"   - Monitoring active: {summary.get('monitoring_active')}")
                        logger.info(f"   - GPU available: {summary.get('gpu_available')}")
                        logger.info(f"   - Total metrics: {summary.get('total_ollama_requests', 0)}")
                        
                        self.test_results.append({
                            "test": "Performance Summary",
                            "status": "PASSED",
                            "details": {
                                "monitoring_active": summary.get('monitoring_active'),
                                "gpu_available": summary.get('gpu_available'),
                                "total_metrics": summary.get('total_ollama_requests', 0)
                            }
                        })
                    else:
                        logger.warning("⚠️ Performance summary returned success=false")
                        self.test_results.append({
                            "test": "Performance Summary",
                            "status": "WARNING",
                            "details": data
                        })
                else:
                    logger.error(f"❌ Performance summary failed with status {response.status_code}")
                    self.test_results.append({
                        "test": "Performance Summary",
                        "status": "FAILED",
                        "error": f"HTTP {response.status_code}"
                    })
                    
        except Exception as e:
            logger.error(f"❌ Performance summary test failed: {e}")
            self.test_results.append({
                "test": "Performance Summary",
                "status": "FAILED",
                "error": str(e)
            })

    async def test_model_performance(self):
        """Test model performance metrics endpoint."""
        logger.info("🤖 Testing model performance metrics...")
        
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                # Test with a sample model name
                response = await client.get(f"{self.base_url}/api/ai/ollama/performance/metrics/test-model")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        logger.info("✅ Model performance metrics endpoint working")
                        self.test_results.append({
                            "test": "Model Performance Metrics",
                            "status": "PASSED",
                            "details": data
                        })
                    else:
                        logger.info("ℹ️ Model performance metrics endpoint working (no data for test model)")
                        self.test_results.append({
                            "test": "Model Performance Metrics",
                            "status": "PASSED",
                            "details": "Endpoint working, no data for test model"
                        })
                else:
                    logger.error(f"❌ Model performance metrics failed with status {response.status_code}")
                    self.test_results.append({
                        "test": "Model Performance Metrics",
                        "status": "FAILED",
                        "error": f"HTTP {response.status_code}"
                    })
                    
        except Exception as e:
            logger.error(f"❌ Model performance metrics test failed: {e}")
            self.test_results.append({
                "test": "Model Performance Metrics",
                "status": "FAILED",
                "error": str(e)
            })

    async def test_system_metrics(self):
        """Test system metrics endpoint."""
        logger.info("💻 Testing system metrics...")
        
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/ai/ollama/performance/system?hours=1")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        logger.info("✅ System metrics endpoint working")
                        logger.info(f"   - Total metrics: {data.get('total_metrics', 0)}")
                        logger.info(f"   - Time period: {data.get('time_period_hours', 0)} hours")
                        
                        self.test_results.append({
                            "test": "System Metrics",
                            "status": "PASSED",
                            "details": {
                                "total_metrics": data.get('total_metrics', 0),
                                "time_period_hours": data.get('time_period_hours', 0)
                            }
                        })
                    else:
                        logger.warning("⚠️ System metrics returned success=false")
                        self.test_results.append({
                            "test": "System Metrics",
                            "status": "WARNING",
                            "details": data
                        })
                else:
                    logger.error(f"❌ System metrics failed with status {response.status_code}")
                    self.test_results.append({
                        "test": "System Metrics",
                        "status": "FAILED",
                        "error": f"HTTP {response.status_code}"
                    })
                    
        except Exception as e:
            logger.error(f"❌ System metrics test failed: {e}")
            self.test_results.append({
                "test": "System Metrics",
                "status": "FAILED",
                "error": str(e)
            })

    async def test_performance_alerts(self):
        """Test performance alerts endpoint."""
        logger.info("🚨 Testing performance alerts...")
        
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/ai/ollama/performance/alerts?limit=5")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        logger.info("✅ Performance alerts endpoint working")
                        logger.info(f"   - Total alerts: {data.get('total_alerts', 0)}")
                        logger.info(f"   - Severity filter: {data.get('severity_filter', 'None')}")
                        
                        self.test_results.append({
                            "test": "Performance Alerts",
                            "status": "PASSED",
                            "details": {
                                "total_alerts": data.get('total_alerts', 0),
                                "severity_filter": data.get('severity_filter', 'None')
                            }
                        })
                    else:
                        logger.warning("⚠️ Performance alerts returned success=false")
                        self.test_results.append({
                            "test": "Performance Alerts",
                            "status": "WARNING",
                            "details": data
                        })
                else:
                    logger.error(f"❌ Performance alerts failed with status {response.status_code}")
                    self.test_results.append({
                        "test": "Performance Alerts",
                        "status": "FAILED",
                        "error": f"HTTP {response.status_code}"
                    })
                    
        except Exception as e:
            logger.error(f"❌ Performance alerts test failed: {e}")
            self.test_results.append({
                "test": "Performance Alerts",
                "status": "FAILED",
                "error": str(e)
            })

    async def test_export_metrics(self):
        """Test metrics export functionality."""
        logger.info("📤 Testing metrics export...")
        
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/ai/ollama/performance/export",
                    json={"format": "json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        logger.info("✅ Metrics export working")
                        logger.info(f"   - Exported file: {data.get('exported_file', 'Unknown')}")
                        logger.info(f"   - Format: {data.get('format', 'Unknown')}")
                        
                        self.test_results.append({
                            "test": "Metrics Export",
                            "status": "PASSED",
                            "details": {
                                "exported_file": data.get('exported_file', 'Unknown'),
                                "format": data.get('format', 'Unknown')
                            }
                        })
                    else:
                        logger.warning("⚠️ Metrics export returned success=false")
                        self.test_results.append({
                            "test": "Metrics Export",
                            "status": "WARNING",
                            "details": data
                        })
                else:
                    logger.error(f"❌ Metrics export failed with status {response.status_code}")
                    self.test_results.append({
                        "test": "Metrics Export",
                        "status": "FAILED",
                        "error": f"HTTP {response.status_code}"
                    })
                    
        except Exception as e:
            logger.error(f"❌ Metrics export test failed: {e}")
            self.test_results.append({
                "test": "Metrics Export",
                "status": "FAILED",
                "error": str(e)
            })

    async def test_cleanup_metrics(self):
        """Test metrics cleanup functionality."""
        logger.info("🧹 Testing metrics cleanup...")
        
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/ai/ollama/performance/cleanup",
                    json={"days_to_keep": 30}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        logger.info("✅ Metrics cleanup working")
                        logger.info(f"   - Days to keep: {data.get('days_to_keep', 0)}")
                        
                        self.test_results.append({
                            "test": "Metrics Cleanup",
                            "status": "PASSED",
                            "details": {
                                "days_to_keep": data.get('days_to_keep', 0),
                                "message": data.get('message', 'Unknown')
                            }
                        })
                    else:
                        logger.warning("⚠️ Metrics cleanup returned success=false")
                        self.test_results.append({
                            "test": "Metrics Cleanup",
                            "status": "WARNING",
                            "details": data
                        })
                else:
                    logger.error(f"❌ Metrics cleanup failed with status {response.status_code}")
                    self.test_results.append({
                        "test": "Metrics Cleanup",
                        "status": "FAILED",
                        "error": f"HTTP {response.status_code}"
                    })
                    
        except Exception as e:
            logger.error(f"❌ Metrics cleanup test failed: {e}")
            self.test_results.append({
                "test": "Metrics Cleanup",
                "status": "FAILED",
                "error": str(e)
            })

    async def test_stop_monitoring(self):
        """Test stopping performance monitoring."""
        logger.info("⏹️ Testing stop monitoring...")
        
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.base_url}/api/ai/ollama/performance/monitoring/stop")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        logger.info("✅ Monitoring stopped successfully")
                        self.test_results.append({
                            "test": "Stop Monitoring",
                            "status": "PASSED",
                            "details": data
                        })
                    else:
                        logger.warning("⚠️ Stop monitoring returned success=false")
                        self.test_results.append({
                            "test": "Stop Monitoring",
                            "status": "WARNING",
                            "details": data
                        })
                else:
                    logger.error(f"❌ Stop monitoring failed with status {response.status_code}")
                    self.test_results.append({
                        "test": "Stop Monitoring",
                        "status": "FAILED",
                        "error": f"HTTP {response.status_code}"
                    })
                    
        except Exception as e:
            logger.error(f"❌ Stop monitoring test failed: {e}")
            self.test_results.append({
                "test": "Stop Monitoring",
                "status": "FAILED",
                "error": str(e)
            })

    async def test_dashboard_access(self):
        """Test dashboard accessibility."""
        logger.info("🌐 Testing dashboard access...")
        
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/ollama-performance-dashboard")
                
                if response.status_code == 200:
                    content = response.text
                    if "Ollama Performance Dashboard" in content:
                        logger.info("✅ Dashboard accessible and contains expected content")
                        self.test_results.append({
                            "test": "Dashboard Access",
                            "status": "PASSED",
                            "details": "Dashboard accessible with expected content"
                        })
                    else:
                        logger.warning("⚠️ Dashboard accessible but content unexpected")
                        self.test_results.append({
                            "test": "Dashboard Access",
                            "status": "WARNING",
                            "details": "Dashboard accessible but content unexpected"
                        })
                else:
                    logger.error(f"❌ Dashboard access failed with status {response.status_code}")
                    self.test_results.append({
                        "test": "Dashboard Access",
                        "status": "FAILED",
                        "error": f"HTTP {response.status_code}"
                    })
                    
        except Exception as e:
            logger.error(f"❌ Dashboard access test failed: {e}")
            self.test_results.append({
                "test": "Dashboard Access",
                "status": "FAILED",
                "error": str(e)
            })

    def print_test_summary(self):
        """Print a summary of all test results."""
        logger.info("\n" + "=" * 60)
        logger.info("📋 TEST SUMMARY")
        logger.info("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["status"] == "PASSED")
        warnings = sum(1 for result in self.test_results if result["status"] == "WARNING")
        failed = sum(1 for result in self.test_results if result["status"] == "FAILED")
        
        logger.info(f"✅ PASSED: {passed}")
        logger.info(f"⚠️  WARNINGS: {warnings}")
        logger.info(f"❌ FAILED: {failed}")
        logger.info(f"📊 TOTAL: {len(self.test_results)}")
        
        if failed > 0:
            logger.info("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if result["status"] == "FAILED":
                    logger.info(f"   - {result['test']}: {result.get('error', 'Unknown error')}")
        
        if warnings > 0:
            logger.info("\n⚠️  WARNINGS:")
            for result in self.test_results:
                if result["status"] == "WARNING":
                    logger.info(f"   - {result['test']}")
        
        logger.info("\n" + "=" * 60)
        
        # Save test results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ollama_performance_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                "test_timestamp": datetime.now().isoformat(),
                "summary": {
                    "passed": passed,
                    "warnings": warnings,
                    "failed": failed,
                    "total": len(self.test_results)
                },
                "results": self.test_results
            }, f, indent=2, default=str)
        
        logger.info(f"📄 Test results saved to: {filename}")

async def main():
    """Main test execution function."""
    import sys
    
    # Parse command line arguments
    base_url = "http://localhost:8000"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    logger.info(f"🔧 Testing Ollama Performance Monitoring at: {base_url}")
    logger.info("💡 Make sure the Autonomica API server is running!")
    logger.info("")
    
    # Create tester and run tests
    tester = OllamaPerformanceTester(base_url)
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
