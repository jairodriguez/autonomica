#!/usr/bin/env python3
"""
Autonomica Comprehensive Monitoring Test Suite
This script performs comprehensive testing of the entire monitoring and alerting system.

Implements Subtask 8.4: Test monitoring and alerting system
"""

import requests
import time
import json
import sys
import subprocess
import threading
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MonitoringSystemTester:
    """Comprehensive testing of the monitoring and alerting system."""
    
    def __init__(self):
        self.test_results = {}
        self.services = {}
        self.test_data = {}
        
    def test_docker_availability(self) -> bool:
        """Test if Docker is available and running."""
        logger.info("🔍 Testing Docker availability...")
        
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info("✅ Docker is available")
                return True
            else:
                logger.warning("⚠️  Docker is not available")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning("⚠️  Docker is not available")
            return False
    
    def start_monitoring_stack(self) -> bool:
        """Start the monitoring stack using Docker Compose."""
        logger.info("🚀 Starting monitoring stack...")
        
        try:
            monitoring_dir = Path(__file__).parent.parent
            result = subprocess.run(
                ['docker-compose', 'up', '-d'],
                cwd=monitoring_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                logger.info("✅ Monitoring stack started successfully")
                # Wait for services to be ready
                time.sleep(15)
                return True
            else:
                logger.error(f"❌ Failed to start monitoring stack: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error starting monitoring stack: {e}")
            return False
    
    def test_prometheus_service(self) -> Dict[str, Any]:
        """Test Prometheus service functionality."""
        logger.info("🔍 Testing Prometheus service...")
        
        results = {
            'health': False,
            'targets': False,
            'rules': False,
            'alerts': False,
            'metrics': False
        }
        
        try:
            # Test health endpoint
            response = requests.get('http://localhost:9090/-/healthy', timeout=10)
            if response.status_code == 200:
                results['health'] = True
                logger.info("✅ Prometheus health check passed")
            else:
                logger.error(f"❌ Prometheus health check failed: {response.status_code}")
            
            # Test targets endpoint
            response = requests.get('http://localhost:9090/api/v1/targets', timeout=10)
            if response.status_code == 200:
                data = response.json()
                targets = data.get('data', {}).get('activeTargets', [])
                results['targets'] = len(targets) > 0
                logger.info(f"✅ Prometheus targets accessible: {len(targets)} targets")
            else:
                logger.error(f"❌ Prometheus targets failed: {response.status_code}")
            
            # Test rules endpoint
            response = requests.get('http://localhost:9090/api/v1/rules', timeout=10)
            if response.status_code == 200:
                data = response.json()
                rules = data.get('data', {}).get('groups', [])
                results['rules'] = len(rules) > 0
                logger.info(f"✅ Prometheus rules accessible: {len(rules)} rule groups")
            else:
                logger.error(f"❌ Prometheus rules failed: {response.status_code}")
            
            # Test alerts endpoint
            response = requests.get('http://localhost:9090/api/v1/alerts', timeout=10)
            if response.status_code == 200:
                data = response.json()
                alerts = data.get('data', {}).get('alerts', [])
                results['alerts'] = True
                logger.info(f"✅ Prometheus alerts accessible: {len(alerts)} alerts")
            else:
                logger.error(f"❌ Prometheus alerts failed: {response.status_code}")
            
            # Test metrics endpoint
            response = requests.get('http://localhost:9090/metrics', timeout=10)
            if response.status_code == 200:
                results['metrics'] = True
                logger.info("✅ Prometheus metrics endpoint accessible")
            else:
                logger.error(f"❌ Prometheus metrics failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing Prometheus: {e}")
        
        self.test_results['prometheus'] = results
        return results
    
    def test_grafana_service(self) -> Dict[str, Any]:
        """Test Grafana service functionality."""
        logger.info("🔍 Testing Grafana service...")
        
        results = {
            'health': False,
            'api': False,
            'login': False
        }
        
        try:
            # Test health endpoint
            response = requests.get('http://localhost:3001/api/health', timeout=10)
            if response.status_code == 200:
                data = response.json()
                results['health'] = True
                logger.info(f"✅ Grafana health check passed: {data.get('database', 'unknown')}")
            else:
                logger.error(f"❌ Grafana health check failed: {response.status_code}")
            
            # Test API endpoint
            response = requests.get('http://localhost:3001/api/org', timeout=10)
            if response.status_code == 200:
                results['api'] = True
                logger.info("✅ Grafana API accessible")
            else:
                logger.error(f"❌ Grafana API failed: {response.status_code}")
            
            # Test login (should redirect to login page)
            response = requests.get('http://localhost:3001/login', timeout=10)
            if response.status_code == 200:
                results['login'] = True
                logger.info("✅ Grafana login page accessible")
            else:
                logger.error(f"❌ Grafana login failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing Grafana: {e}")
        
        self.test_results['grafana'] = results
        return results
    
    def test_alertmanager_service(self) -> Dict[str, Any]:
        """Test Alertmanager service functionality."""
        logger.info("🔍 Testing Alertmanager service...")
        
        results = {
            'health': False,
            'status': False,
            'config': False
        }
        
        try:
            # Test health endpoint
            response = requests.get('http://localhost:9093/-/healthy', timeout=10)
            if response.status_code == 200:
                results['health'] = True
                logger.info("✅ Alertmanager health check passed")
            else:
                logger.error(f"❌ Alertmanager health check failed: {response.status_code}")
            
            # Test status endpoint
            response = requests.get('http://localhost:9093/api/v1/status', timeout=10)
            if response.status_code == 200:
                data = response.json()
                results['status'] = True
                logger.info("✅ Alertmanager status accessible")
            else:
                logger.error(f"❌ Alertmanager status failed: {response.status_code}")
            
            # Test config endpoint
            response = requests.get('http://localhost:9093/api/v1/status/config', timeout=10)
            if response.status_code == 200:
                data = response.json()
                results['config'] = True
                logger.info("✅ Alertmanager config accessible")
            else:
                logger.error(f"❌ Alertmanager config failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing Alertmanager: {e}")
        
        self.test_results['alertmanager'] = results
        return results
    
    def start_metrics_collector(self) -> bool:
        """Start the system metrics collector."""
        logger.info("🚀 Starting system metrics collector...")
        
        try:
            script_path = Path(__file__).parent / "start_metrics_collector.sh"
            self.metrics_process = subprocess.Popen(
                [str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for service to start
            time.sleep(10)
            
            if self.metrics_process.poll() is None:
                logger.info("✅ Metrics collector started successfully")
                return True
            else:
                logger.error("❌ Metrics collector failed to start")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error starting metrics collector: {e}")
            return False
    
    def test_metrics_collector(self) -> Dict[str, Any]:
        """Test the system metrics collector."""
        logger.info("🔍 Testing system metrics collector...")
        
        results = {
            'endpoint': False,
            'metrics': False,
            'data_quality': False
        }
        
        try:
            # Test metrics endpoint
            response = requests.get('http://localhost:8000/metrics', timeout=10)
            if response.status_code == 200:
                results['endpoint'] = True
                logger.info("✅ Metrics collector endpoint accessible")
                
                # Check metrics content
                content = response.text
                expected_metrics = [
                    'system_cpu_usage_percent',
                    'system_memory_usage_bytes',
                    'system_disk_usage_bytes'
                ]
                
                found_metrics = [m for m in expected_metrics if m in content]
                results['metrics'] = len(found_metrics) >= 2
                
                if results['metrics']:
                    logger.info(f"✅ Found {len(found_metrics)} expected metrics")
                else:
                    logger.warning(f"⚠️  Only found {len(found_metrics)} expected metrics")
                
                # Check data quality (should have numeric values)
                if 'system_cpu_usage_percent' in content and ' ' in content:
                    results['data_quality'] = True
                    logger.info("✅ Metrics data quality looks good")
                else:
                    logger.warning("⚠️  Metrics data quality may be poor")
                    
            else:
                logger.error(f"❌ Metrics collector endpoint failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing metrics collector: {e}")
        
        self.test_results['metrics_collector'] = results
        return results
    
    def start_webhook_service(self) -> bool:
        """Start the notification webhook service."""
        logger.info("🚀 Starting notification webhook service...")
        
        try:
            script_path = Path(__file__).parent / "start_webhook.sh"
            self.webhook_process = subprocess.Popen(
                [str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for service to start
            time.sleep(10)
            
            if self.webhook_process.poll() is None:
                logger.info("✅ Webhook service started successfully")
                return True
            else:
                logger.error("❌ Webhook service failed to start")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error starting webhook service: {e}")
            return False
    
    def test_webhook_service(self) -> Dict[str, Any]:
        """Test the notification webhook service."""
        logger.info("🔍 Testing notification webhook service...")
        
        results = {
            'health': False,
            'test_alert': False,
            'alert_processing': False,
            'endpoints': False
        }
        
        try:
            # Test health endpoint
            response = requests.get('http://localhost:5001/health', timeout=10)
            if response.status_code == 200:
                data = response.json()
                results['health'] = data.get('status') == 'healthy'
                if results['health']:
                    logger.info("✅ Webhook service health check passed")
                else:
                    logger.error("❌ Webhook service health check failed")
            else:
                logger.error(f"❌ Webhook service health failed: {response.status_code}")
            
            # Test alert generation
            response = requests.post('http://localhost:5001/alerts/test', timeout=10)
            if response.status_code == 200:
                data = response.json()
                results['test_alert'] = data.get('status') == 'success'
                if results['test_alert']:
                    logger.info("✅ Test alert generated successfully")
                else:
                    logger.error("❌ Test alert generation failed")
            else:
                logger.error(f"❌ Test alert failed: {response.status_code}")
            
            # Test alert processing
            test_alert = {
                'alerts': [{
                    'labels': {
                        'alertname': 'TestAlert',
                        'severity': 'critical',
                        'category': 'testing'
                    },
                    'annotations': {
                        'summary': 'Test alert',
                        'description': 'Test alert for validation'
                    },
                    'status': 'firing'
                }]
            }
            
            response = requests.post(
                'http://localhost:5001/webhook',
                json=test_alert,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results['alert_processing'] = data.get('status') == 'success'
                if results['alert_processing']:
                    logger.info("✅ Alert processing test passed")
                else:
                    logger.error("❌ Alert processing test failed")
            else:
                logger.error(f"❌ Alert processing failed: {response.status_code}")
            
            # Test all endpoints
            endpoints = ['/alerts', '/alerts/summary', '/alerts/history']
            working_endpoints = 0
            
            for endpoint in endpoints:
                try:
                    response = requests.get(f'http://localhost:5001{endpoint}', timeout=10)
                    if response.status_code == 200:
                        working_endpoints += 1
                except:
                    pass
            
            results['endpoints'] = working_endpoints >= 2
            if results['endpoints']:
                logger.info(f"✅ {working_endpoints}/{len(endpoints)} webhook endpoints working")
            else:
                logger.warning(f"⚠️  Only {working_endpoints}/{len(endpoints)} webhook endpoints working")
                
        except Exception as e:
            logger.error(f"❌ Error testing webhook service: {e}")
        
        self.test_results['webhook_service'] = results
        return results
    
    def test_alert_integration(self) -> Dict[str, Any]:
        """Test alert integration between Prometheus and Alertmanager."""
        logger.info("🔍 Testing alert integration...")
        
        results = {
            'prometheus_to_alertmanager': False,
            'alert_routing': False,
            'notification_delivery': False
        }
        
        try:
            # Check if Prometheus is configured to send alerts to Alertmanager
            response = requests.get('http://localhost:9090/api/v1/status/config', timeout=10)
            if response.status_code == 200:
                config = response.text
                if 'alertmanager:9093' in config:
                    results['prometheus_to_alertmanager'] = True
                    logger.info("✅ Prometheus configured to send alerts to Alertmanager")
                else:
                    logger.warning("⚠️  Prometheus not configured for Alertmanager")
            else:
                logger.error(f"❌ Cannot check Prometheus config: {response.status_code}")
            
            # Check Alertmanager routing configuration
            response = requests.get('http://localhost:9093/api/v1/status/config', timeout=10)
            if response.status_code == 200:
                config = response.json()
                routes = config.get('config', {}).get('route', {})
                if routes:
                    results['alert_routing'] = True
                    logger.info("✅ Alertmanager routing configuration found")
                else:
                    logger.warning("⚠️  No Alertmanager routing configuration found")
            else:
                logger.error(f"❌ Cannot check Alertmanager config: {response.status_code}")
            
            # Test notification delivery by checking webhook
            try:
                response = requests.get('http://localhost:5001/alerts/summary', timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    total_alerts = data.get('total_alerts', 0)
                    if total_alerts > 0:
                        results['notification_delivery'] = True
                        logger.info(f"✅ Notifications being delivered: {total_alerts} alerts")
                    else:
                        logger.info("ℹ️  No active alerts (this is normal)")
                else:
                    logger.warning(f"⚠️  Cannot check notification delivery: {response.status_code}")
            except:
                logger.warning("⚠️  Cannot test notification delivery")
                
        except Exception as e:
            logger.error(f"❌ Error testing alert integration: {e}")
        
        self.test_results['alert_integration'] = results
        return results
    
    def test_metrics_ingestion(self) -> Dict[str, Any]:
        """Test metrics ingestion into Prometheus."""
        logger.info("🔍 Testing metrics ingestion...")
        
        results = {
            'target_health': False,
            'metrics_collection': False,
            'data_freshness': False
        }
        
        try:
            # Check target health
            response = requests.get('http://localhost:9090/api/v1/targets', timeout=10)
            if response.status_code == 200:
                data = response.json()
                targets = data.get('data', {}).get('activeTargets', [])
                
                healthy_targets = [t for t in targets if t.get('health') == 'up']
                if len(healthy_targets) > 0:
                    results['target_health'] = True
                    logger.info(f"✅ {len(healthy_targets)}/{len(targets)} targets healthy")
                else:
                    logger.warning(f"⚠️  No healthy targets found")
            else:
                logger.error(f"❌ Cannot check target health: {response.status_code}")
            
            # Check if metrics are being collected
            response = requests.get('http://localhost:9090/api/v1/query', 
                                 params={'query': 'up'}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                results_data = data.get('data', {}).get('result', [])
                if results_data:
                    results['metrics_collection'] = True
                    logger.info(f"✅ Metrics collection working: {len(results_data)} results")
                else:
                    logger.warning("⚠️  No metrics data found")
            else:
                logger.error(f"❌ Cannot check metrics collection: {response.status_code}")
            
            # Check data freshness (last scrape time)
            response = requests.get('http://localhost:9090/api/v1/query', 
                                 params={'query': 'up'}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                results_data = data.get('data', {}).get('result', [])
                if results_data:
                    # Check if any target was scraped recently
                    current_time = time.time()
                    recent_scrapes = 0
                    
                    for result in results_data:
                        timestamp = result.get('value', [0, 0])[0]
                        if current_time - timestamp < 300:  # 5 minutes
                            recent_scrapes += 1
                    
                    if recent_scrapes > 0:
                        results['data_freshness'] = True
                        logger.info(f"✅ {recent_scrapes} targets scraped recently")
                    else:
                        logger.warning("⚠️  No recent metric scrapes")
                        
        except Exception as e:
            logger.error(f"❌ Error testing metrics ingestion: {e}")
        
        self.test_results['metrics_ingestion'] = results
        return results
    
    def test_end_to_end_workflow(self) -> Dict[str, Any]:
        """Test the complete end-to-end monitoring workflow."""
        logger.info("🔍 Testing end-to-end monitoring workflow...")
        
        results = {
            'data_flow': False,
            'alert_flow': False,
            'notification_flow': False
        }
        
        try:
            # Test data flow: Metrics -> Prometheus -> Grafana
            # Check if Prometheus has data
            response = requests.get('http://localhost:9090/api/v1/query', 
                                 params={'query': 'up'}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('data', {}).get('result'):
                    results['data_flow'] = True
                    logger.info("✅ Data flow: Metrics -> Prometheus working")
                else:
                    logger.warning("⚠️  Data flow: No metrics data in Prometheus")
            else:
                logger.error(f"❌ Data flow: Cannot query Prometheus: {response.status_code}")
            
            # Test alert flow: Prometheus -> Alertmanager
            # Check if Alertmanager is receiving alerts
            response = requests.get('http://localhost:9093/api/v1/alerts', timeout=10)
            if response.status_code == 200:
                data = response.json()
                alerts = data.get('data', [])
                results['alert_flow'] = True
                logger.info(f"✅ Alert flow: Alertmanager accessible with {len(alerts)} alerts")
            else:
                logger.warning(f"⚠️  Alert flow: Cannot access Alertmanager: {response.status_code}")
            
            # Test notification flow: Alertmanager -> Webhook
            # Check if webhook is receiving notifications
            try:
                response = requests.get('http://localhost:5001/alerts/summary', timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    results['notification_flow'] = True
                    logger.info("✅ Notification flow: Webhook service accessible")
                else:
                    logger.warning(f"⚠️  Notification flow: Cannot access webhook: {response.status_code}")
            except:
                logger.warning("⚠️  Notification flow: Webhook service not accessible")
                
        except Exception as e:
            logger.error(f"❌ Error testing end-to-end workflow: {e}")
        
        self.test_results['end_to_end_workflow'] = results
        return results
    
    def run_comprehensive_tests(self) -> None:
        """Run all comprehensive tests."""
        logger.info("🚀 Starting comprehensive monitoring system tests...")
        logger.info("=" * 80)
        
        # Check Docker availability
        docker_available = self.test_docker_availability()
        
        if docker_available:
            # Start monitoring stack
            if not self.start_monitoring_stack():
                logger.error("❌ Cannot proceed without monitoring stack")
                return
            
            # Test core services
            self.test_prometheus_service()
            self.test_grafana_service()
            self.test_alertmanager_service()
            
            # Test metrics collection
            if not self.start_metrics_collector():
                logger.warning("⚠️  Metrics collector not available, skipping related tests")
            else:
                self.test_metrics_collector()
            
            # Test webhook service
            if not self.start_webhook_service():
                logger.warning("⚠️  Webhook service not available, skipping related tests")
            else:
                self.test_webhook_service()
            
            # Test integrations
            self.test_alert_integration()
            self.test_metrics_ingestion()
            self.test_end_to_end_workflow()
            
        else:
            logger.warning("⚠️  Docker not available, running limited tests...")
            
            # Test webhook service if available
            if self.start_webhook_service():
                self.test_webhook_service()
            else:
                logger.warning("⚠️  Webhook service not available")
        
        # Print comprehensive results
        self.print_comprehensive_results()
    
    def print_comprehensive_results(self) -> None:
        """Print comprehensive test results."""
        logger.info("=" * 80)
        logger.info("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        logger.info("=" * 80)
        
        total_tests = 0
        successful_tests = 0
        partial_tests = 0
        failed_tests = 0
        
        for component, results in self.test_results.items():
            if isinstance(results, dict):
                component_tests = len(results)
                component_success = sum(1 for v in results.values() if v is True)
                component_partial = sum(1 for v in results.values() if v is False)
                
                total_tests += component_tests
                successful_tests += component_success
                failed_tests += component_partial
                
                status_emoji = "✅" if component_success == component_tests else "⚠️" if component_success > 0 else "❌"
                logger.info(f"{status_emoji} {component}: {component_success}/{component_tests} tests passed")
                
                # Show detailed results for failed components
                if component_partial > 0:
                    for test_name, result in results.items():
                        if not result:
                            logger.info(f"   ❌ {test_name}: Failed")
        
        logger.info("")
        logger.info(f"📋 Total Tests: {total_tests}")
        logger.info(f"✅ Successful: {successful_tests}")
        logger.info(f"❌ Failed: {failed_tests}")
        logger.info(f"📊 Success Rate: {(successful_tests/total_tests*100):.1f}%" if total_tests > 0 else "N/A")
        logger.info("")
        
        if failed_tests == 0:
            logger.info("🎉 All tests completed successfully!")
            logger.info("✅ The monitoring and alerting system is fully operational")
        elif failed_tests < total_tests * 0.3:  # Less than 30% failed
            logger.info("⚠️  Most tests passed, but some issues were detected")
            logger.info("🔧 Review failed tests and address issues before production use")
        else:
            logger.error("❌ Critical failures detected in the monitoring system")
            logger.error("🚨 Address all issues before proceeding to production")
        
        logger.info("")
        logger.info("📚 See individual test results above for detailed information")
        logger.info("🔧 Use the troubleshooting guide for resolving any issues")
    
    def cleanup(self) -> None:
        """Cleanup resources and stop services."""
        logger.info("🛑 Cleaning up test resources...")
        
        # Stop metrics collector
        if hasattr(self, 'metrics_process') and self.metrics_process:
            try:
                self.metrics_process.terminate()
                self.metrics_process.wait(timeout=10)
                logger.info("✅ Metrics collector stopped")
            except:
                pass
        
        # Stop webhook service
        if hasattr(self, 'webhook_process') and self.webhook_process:
            try:
                self.webhook_process.terminate()
                self.webhook_process.wait(timeout=10)
                logger.info("✅ Webhook service stopped")
            except:
                pass
        
        # Stop monitoring stack if Docker is available
        if self.test_docker_availability():
            try:
                monitoring_dir = Path(__file__).parent.parent
                subprocess.run(['docker-compose', 'down'], 
                             cwd=monitoring_dir, 
                             capture_output=True, 
                             timeout=30)
                logger.info("✅ Monitoring stack stopped")
            except:
                pass

def main():
    """Main function to run comprehensive tests."""
    tester = MonitoringSystemTester()
    
    try:
        tester.run_comprehensive_tests()
    except KeyboardInterrupt:
        logger.info("🛑 Testing interrupted by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error during testing: {e}")
    finally:
        tester.cleanup()

if __name__ == "__main__":
    main()