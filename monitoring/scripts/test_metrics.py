#!/usr/bin/env python3
"""
Autonomica Metrics Testing Script
This script tests all metrics endpoints and validates metrics collection.

Implements part of Subtask 8.2: Set up performance metrics collection
"""

import requests
import time
import json
import sys
from pathlib import Path
import subprocess
import threading
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MetricsTester:
    """Tests metrics collection and endpoints."""
    
    def __init__(self):
        self.test_results = {}
        self.metrics_collector_process = None
        
    def test_prometheus_endpoint(self, host="localhost", port=9090):
        """Test Prometheus endpoint."""
        logger.info("🔍 Testing Prometheus endpoint...")
        
        try:
            # Test health endpoint
            health_url = f"http://{host}:{port}/-/healthy"
            response = requests.get(health_url, timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ Prometheus health endpoint is accessible")
                
                # Test targets endpoint
                targets_url = f"http://{host}:{port}/api/v1/targets"
                response = requests.get(targets_url, timeout=10)
                
                if response.status_code == 200:
                    targets_data = response.json()
                    active_targets = targets_data.get('data', {}).get('activeTargets', [])
                    logger.info(f"✅ Prometheus targets endpoint accessible. Found {len(active_targets)} active targets")
                    
                    # Check target health
                    healthy_targets = [t for t in active_targets if t.get('health') == 'up']
                    logger.info(f"📊 Target health: {len(healthy_targets)}/{len(active_targets)} healthy")
                    
                    self.test_results['prometheus'] = {
                        'status': 'success',
                        'health': 'up',
                        'targets_count': len(active_targets),
                        'healthy_targets': len(healthy_targets)
                    }
                else:
                    logger.warning(f"⚠️  Prometheus targets endpoint returned {response.status_code}")
                    self.test_results['prometheus'] = {'status': 'partial', 'health': 'up'}
            else:
                logger.error(f"❌ Prometheus health endpoint returned {response.status_code}")
                self.test_results['prometheus'] = {'status': 'failed', 'health': 'down'}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to connect to Prometheus: {e}")
            self.test_results['prometheus'] = {'status': 'failed', 'error': str(e)}
    
    def test_grafana_endpoint(self, host="localhost", port=3001):
        """Test Grafana endpoint."""
        logger.info("🔍 Testing Grafana endpoint...")
        
        try:
            # Test health endpoint
            health_url = f"http://{host}:{port}/api/health"
            response = requests.get(health_url, timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                logger.info("✅ Grafana health endpoint is accessible")
                logger.info(f"📊 Grafana status: {health_data.get('database', 'unknown')}")
                
                self.test_results['grafana'] = {
                    'status': 'success',
                    'database': health_data.get('database', 'unknown')
                }
            else:
                logger.error(f"❌ Grafana health endpoint returned {response.status_code}")
                self.test_results['grafana'] = {'status': 'failed'}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to connect to Grafana: {e}")
            self.test_results['grafana'] = {'status': 'failed', 'error': str(e)}
    
    def test_alertmanager_endpoint(self, host="localhost", port=9093):
        """Test Alertmanager endpoint."""
        logger.info("🔍 Testing Alertmanager endpoint...")
        
        try:
            # Test health endpoint
            health_url = f"http://{host}:{port}/-/healthy"
            response = requests.get(health_url, timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ Alertmanager health endpoint is accessible")
                
                # Test status endpoint
                status_url = f"http://{host}:{port}/api/v1/status"
                response = requests.get(status_url, timeout=10)
                
                if response.status_code == 200:
                    status_data = response.json()
                    logger.info("✅ Alertmanager status endpoint accessible")
                    
                    self.test_results['alertmanager'] = {
                        'status': 'success',
                        'health': 'up'
                    }
                else:
                    logger.warning(f"⚠️  Alertmanager status endpoint returned {response.status_code}")
                    self.test_results['alertmanager'] = {'status': 'partial', 'health': 'up'}
            else:
                logger.error(f"❌ Alertmanager health endpoint returned {response.status_code}")
                self.test_results['alertmanager'] = {'status': 'failed', 'health': 'down'}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to connect to Alertmanager: {e}")
            self.test_results['alertmanager'] = {'status': 'failed', 'error': str(e)}
    
    def test_metrics_endpoint(self, host="localhost", port=8000):
        """Test custom metrics endpoint."""
        logger.info("🔍 Testing custom metrics endpoint...")
        
        try:
            # Test metrics endpoint
            metrics_url = f"http://{host}:{port}/metrics"
            response = requests.get(metrics_url, timeout=10)
            
            if response.status_code == 200:
                metrics_content = response.text
                logger.info("✅ Custom metrics endpoint is accessible")
                
                # Check for expected metrics
                expected_metrics = [
                    'system_cpu_usage_percent',
                    'system_memory_usage_bytes',
                    'system_disk_usage_bytes',
                    'system_network_bytes_sent_total'
                ]
                
                found_metrics = []
                for metric in expected_metrics:
                    if metric in metrics_content:
                        found_metrics.append(metric)
                
                logger.info(f"📊 Found {len(found_metrics)}/{len(expected_metrics)} expected metrics")
                
                self.test_results['custom_metrics'] = {
                    'status': 'success',
                    'metrics_found': len(found_metrics),
                    'total_expected': len(expected_metrics)
                }
            else:
                logger.error(f"❌ Custom metrics endpoint returned {response.status_code}")
                self.test_results['custom_metrics'] = {'status': 'failed'}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to connect to custom metrics endpoint: {e}")
            self.test_results['custom_metrics'] = {'status': 'failed', 'error': str(e)}
    
    def start_metrics_collector(self):
        """Start the metrics collector in background."""
        logger.info("🚀 Starting metrics collector in background...")
        
        try:
            script_path = Path(__file__).parent / "start_metrics_collector.sh"
            self.metrics_collector_process = subprocess.Popen(
                [str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait a bit for the service to start
            time.sleep(5)
            
            if self.metrics_collector_process.poll() is None:
                logger.info("✅ Metrics collector started successfully")
                return True
            else:
                logger.error("❌ Metrics collector failed to start")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start metrics collector: {e}")
            return False
    
    def stop_metrics_collector(self):
        """Stop the metrics collector."""
        if self.metrics_collector_process:
            logger.info("🛑 Stopping metrics collector...")
            self.metrics_collector_process.terminate()
            try:
                self.metrics_collector_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.metrics_collector_process.kill()
            logger.info("✅ Metrics collector stopped")
    
    def test_alert_rules(self, host="localhost", port=9090):
        """Test Prometheus alert rules."""
        logger.info("🔍 Testing alert rules...")
        
        try:
            # Test rules endpoint
            rules_url = f"http://{host}:{port}/api/v1/rules"
            response = requests.get(rules_url, timeout=10)
            
            if response.status_code == 200:
                rules_data = response.json()
                alerting_rules = rules_data.get('data', {}).get('groups', [])
                
                total_rules = 0
                for group in alerting_rules:
                    total_rules += len(group.get('rules', []))
                
                logger.info(f"✅ Alert rules endpoint accessible. Found {total_rules} rules")
                
                self.test_results['alert_rules'] = {
                    'status': 'success',
                    'rules_count': total_rules
                }
            else:
                logger.warning(f"⚠️  Alert rules endpoint returned {response.status_code}")
                self.test_results['alert_rules'] = {'status': 'partial'}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to test alert rules: {e}")
            self.test_results['alert_rules'] = {'status': 'failed', 'error': str(e)}
    
    def test_metrics_ingestion(self, host="localhost", port=9090):
        """Test that metrics are being ingested by Prometheus."""
        logger.info("🔍 Testing metrics ingestion...")
        
        try:
            # Query for a specific metric
            query_url = f"http://{host}:{port}/api/v1/query"
            params = {'query': 'up'}
            response = requests.get(query_url, params=params, timeout=10)
            
            if response.status_code == 200:
                query_data = response.json()
                results = query_data.get('data', {}).get('result', [])
                
                if results:
                    logger.info(f"✅ Metrics ingestion working. Found {len(results)} targets")
                    
                    # Check for specific metrics
                    test_queries = [
                        'system_cpu_usage_percent',
                        'system_memory_usage_bytes',
                        'up'
                    ]
                    
                    ingested_metrics = 0
                    for query in test_queries:
                        try:
                            params = {'query': query}
                            response = requests.get(query_url, params=params, timeout=10)
                            if response.status_code == 200:
                                data = response.json()
                                if data.get('data', {}).get('result'):
                                    ingested_metrics += 1
                        except:
                            pass
                    
                    logger.info(f"📊 {ingested_metrics}/{len(test_queries)} test metrics found")
                    
                    self.test_results['metrics_ingestion'] = {
                        'status': 'success',
                        'targets_found': len(results),
                        'test_metrics_found': ingested_metrics
                    }
                else:
                    logger.warning("⚠️  No metrics targets found")
                    self.test_results['metrics_ingestion'] = {'status': 'partial'}
            else:
                logger.error(f"❌ Metrics query endpoint returned {response.status_code}")
                self.test_results['metrics_ingestion'] = {'status': 'failed'}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to test metrics ingestion: {e}")
            self.test_results['metrics_ingestion'] = {'status': 'failed', 'error': str(e)}
    
    def run_all_tests(self):
        """Run all tests."""
        logger.info("🚀 Starting comprehensive metrics testing...")
        logger.info("=" * 60)
        
        # Start metrics collector if not already running
        if not self.test_metrics_endpoint():
            logger.info("📊 Starting metrics collector for testing...")
            if not self.start_metrics_collector():
                logger.error("❌ Cannot proceed without metrics collector")
                return
        
        # Wait for metrics to be available
        time.sleep(10)
        
        # Run all tests
        self.test_prometheus_endpoint()
        self.test_grafana_endpoint()
        self.test_alertmanager_endpoint()
        self.test_metrics_endpoint()
        self.test_alert_rules()
        self.test_metrics_ingestion()
        
        # Stop metrics collector if we started it
        if self.metrics_collector_process:
            self.stop_metrics_collector()
        
        # Print summary
        self.print_test_summary()
    
    def print_test_summary(self):
        """Print test results summary."""
        logger.info("=" * 60)
        logger.info("📊 TEST RESULTS SUMMARY")
        logger.info("=" * 60)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results.values() if result.get('status') == 'success')
        partial_tests = sum(1 for result in self.test_results.values() if result.get('status') == 'partial')
        failed_tests = sum(1 for result in self.test_results.values() if result.get('status') == 'failed')
        
        logger.info(f"📋 Total Tests: {total_tests}")
        logger.info(f"✅ Successful: {successful_tests}")
        logger.info(f"⚠️  Partial: {partial_tests}")
        logger.info(f"❌ Failed: {failed_tests}")
        logger.info("")
        
        for test_name, result in self.test_results.items():
            status_emoji = "✅" if result.get('status') == 'success' else "⚠️" if result.get('status') == 'partial' else "❌"
            logger.info(f"{status_emoji} {test_name}: {result.get('status', 'unknown')}")
            
            # Print additional details
            for key, value in result.items():
                if key != 'status':
                    logger.info(f"   {key}: {value}")
        
        logger.info("")
        
        if failed_tests == 0:
            logger.info("🎉 All tests completed successfully!")
        elif failed_tests < total_tests:
            logger.info("⚠️  Some tests failed, but the system is partially functional")
        else:
            logger.error("❌ Critical failures detected in the monitoring system")
    
    def cleanup(self):
        """Cleanup resources."""
        if self.metrics_collector_process:
            self.stop_metrics_collector()

def main():
    """Main function."""
    tester = MetricsTester()
    
    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        logger.info("🛑 Testing interrupted by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error during testing: {e}")
    finally:
        tester.cleanup()

if __name__ == "__main__":
    main()