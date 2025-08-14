#!/usr/bin/env python3
"""
Health Checker Component for Rollback Service
Monitors service health and provides metrics for rollback decisions
"""

import time
import logging
import requests
import docker
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import statistics

logger = logging.getLogger(__name__)

@dataclass
class HealthMetrics:
    """Health metrics for a service"""
    error_rate: float
    response_time_p95: float
    cpu_usage: float
    memory_usage: float
    database_connections: int
    service_status: str
    timestamp: datetime

@dataclass
class ServiceHealth:
    """Service health information"""
    service_name: str
    status: str
    error_rate: float
    response_time_p95: float
    cpu_usage: float
    memory_usage: float
    database_connections: int
    last_check: datetime
    consecutive_failures: int
    health_score: float

class HealthChecker:
    """Health checker for monitoring service health"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.docker_client = docker.from_env()
        self.health_history = {}
        self.baseline_metrics = {}
        self.check_interval = config['rollback']['health_check']['health_check_interval']
        
        # Health check endpoints
        self.health_endpoints = {
            'frontend': 'http://localhost:3000/health',
            'api': 'http://localhost:8000/health',
            'worker': 'http://localhost:8001/health'
        }
        
        # Prometheus endpoints for metrics
        self.prometheus_endpoint = 'http://localhost:9090'
        
        logger.info("Health checker initialized")
    
    def get_all_health_metrics(self) -> Dict[str, 'HealthMetrics']:
        """Get health metrics for all monitored services"""
        try:
            health_metrics = {}
            
            for service_name in self.health_endpoints.keys():
                metrics = self._get_service_health_metrics(service_name)
                if metrics:
                    health_metrics[service_name] = metrics
            
            return health_metrics
            
        except Exception as e:
            logger.error(f"Error getting all health metrics: {e}")
            return {}
    
    def _get_service_health_metrics(self, service_name: str) -> Optional['HealthMetrics']:
        """Get health metrics for a specific service"""
        try:
            # Get basic health status
            health_status = self._check_service_health(service_name)
            
            # Get performance metrics
            error_rate = self._get_error_rate(service_name)
            response_time = self._get_response_time(service_name)
            
            # Get infrastructure metrics
            cpu_usage = self._get_cpu_usage(service_name)
            memory_usage = self._get_memory_usage(service_name)
            db_connections = self._get_database_connections(service_name)
            
            # Create health metrics
            metrics = HealthMetrics(
                error_rate=error_rate,
                response_time_p95=response_time,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                database_connections=db_connections,
                service_status=health_status,
                timestamp=datetime.now()
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting health metrics for {service_name}: {e}")
            return None
    
    def _check_service_health(self, service_name: str) -> str:
        """Check basic health status of a service"""
        try:
            endpoint = self.health_endpoints.get(service_name)
            if not endpoint:
                return 'unknown'
            
            response = requests.get(endpoint, timeout=5)
            if response.status_code == 200:
                return 'healthy'
            else:
                return 'unhealthy'
                
        except requests.exceptions.RequestException:
            return 'down'
        except Exception as e:
            logger.error(f"Error checking health for {service_name}: {e}")
            return 'unknown'
    
    def _get_error_rate(self, service_name: str) -> float:
        """Get error rate for a service from Prometheus"""
        try:
            # Query Prometheus for error rate
            query = f'rate(http_requests_total{{job="{service_name}",status=~"5.."}}[5m]) / rate(http_requests_total{{job="{service_name}"}}[5m])'
            
            response = requests.get(
                f"{self.prometheus_endpoint}/api/v1/query",
                params={'query': query},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['data']['result']:
                    return float(data['data']['result'][0]['value'][1])
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error getting error rate for {service_name}: {e}")
            return 0.0
    
    def _get_response_time(self, service_name: str) -> float:
        """Get 95th percentile response time from Prometheus"""
        try:
            # Query Prometheus for response time
            query = f'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{{job="{service_name}"}}[5m]))'
            
            response = requests.get(
                f"{self.prometheus_endpoint}/api/v1/query",
                params={'query': query},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['data']['result']:
                    return float(data['data']['result'][0]['value'][1]) * 1000  # Convert to milliseconds
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error getting response time for {service_name}: {e}")
            return 0.0
    
    def _get_cpu_usage(self, service_name: str) -> float:
        """Get CPU usage for a service container"""
        try:
            # Get container stats from Docker
            containers = self.docker_client.containers.list(
                filters={'name': f'autonomica-{service_name}'}
            )
            
            if containers:
                container = containers[0]
                stats = container.stats(stream=False)
                
                # Calculate CPU usage percentage
                cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
                system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
                
                if system_delta > 0:
                    cpu_usage = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage'])
                    return min(cpu_usage, 1.0)  # Cap at 100%
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error getting CPU usage for {service_name}: {e}")
            return 0.0
    
    def _get_memory_usage(self, service_name: str) -> float:
        """Get memory usage for a service container"""
        try:
            # Get container stats from Docker
            containers = self.docker_client.containers.list(
                filters={'name': f'autonomica-{service_name}'}
            )
            
            if containers:
                container = containers[0]
                stats = container.stats(stream=False)
                
                # Calculate memory usage percentage
                memory_usage = stats['memory_stats']['usage']
                memory_limit = stats['memory_stats']['limit']
                
                if memory_limit > 0:
                    return memory_usage / memory_limit
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error getting memory usage for {service_name}: {e}")
            return 0.0
    
    def _get_database_connections(self, service_name: str) -> int:
        """Get database connection count for a service"""
        try:
            # Query Prometheus for database connections
            query = 'pg_stat_activity_count'
            
            response = requests.get(
                f"{self.prometheus_endpoint}/api/v1/query",
                params={'query': query},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['data']['result']:
                    return int(float(data['data']['result'][0]['value'][1]))
            
            return 0
            
        except Exception as e:
            logger.error(f"Error getting database connections: {e}")
            return 0
    
    def get_service_health_score(self, service_name: str) -> float:
        """Calculate overall health score for a service (0-100)"""
        try:
            metrics = self._get_service_health_metrics(service_name)
            if not metrics:
                return 0.0
            
            # Calculate health score based on various metrics
            score = 100.0
            
            # Deduct points for high error rate
            if metrics.error_rate > 0.05:
                score -= (metrics.error_rate * 100)
            
            # Deduct points for high response time
            if metrics.response_time_p95 > 2000:
                score -= min((metrics.response_time_p95 - 2000) / 100, 20)
            
            # Deduct points for high CPU usage
            if metrics.cpu_usage > 0.8:
                score -= (metrics.cpu_usage - 0.8) * 50
            
            # Deduct points for high memory usage
            if metrics.memory_usage > 0.9:
                score -= (metrics.memory_usage - 0.9) * 50
            
            # Deduct points for service being down
            if metrics.service_status == 'down':
                score = 0.0
            
            return max(score, 0.0)
            
        except Exception as e:
            logger.error(f"Error calculating health score for {service_name}: {e}")
            return 0.0
    
    def is_service_healthy(self, service_name: str) -> bool:
        """Check if a service is considered healthy"""
        try:
            health_score = self.get_service_health_score(service_name)
            return health_score >= 70.0  # 70% threshold for healthy
            
        except Exception as e:
            logger.error(f"Error checking if {service_name} is healthy: {e}")
            return False
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get summary of all services health"""
        try:
            summary = {
                'timestamp': datetime.now().isoformat(),
                'services': {},
                'overall_health': 'healthy',
                'unhealthy_services': [],
                'critical_issues': []
            }
            
            total_score = 0
            service_count = 0
            
            for service_name in self.health_endpoints.keys():
                health_score = self.get_service_health_score(service_name)
                is_healthy = self.is_service_healthy(service_name)
                
                service_info = {
                    'health_score': health_score,
                    'status': 'healthy' if is_healthy else 'unhealthy',
                    'last_check': datetime.now().isoformat()
                }
                
                summary['services'][service_name] = service_info
                total_score += health_score
                service_count += 1
                
                if not is_healthy:
                    summary['unhealthy_services'].append(service_name)
                
                if health_score < 30:
                    summary['critical_issues'].append(f"{service_name}: Critical health score ({health_score})")
            
            # Calculate overall health
            if service_count > 0:
                overall_score = total_score / service_count
                if overall_score >= 90:
                    summary['overall_health'] = 'excellent'
                elif overall_score >= 70:
                    summary['overall_health'] = 'healthy'
                elif overall_score >= 50:
                    summary['overall_health'] = 'degraded'
                else:
                    summary['overall_health'] = 'critical'
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting health summary: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'overall_health': 'unknown'
            }
    
    def get_baseline_metrics(self, service_name: str) -> Dict[str, float]:
        """Get baseline metrics for a service (used for comparison)"""
        try:
            if service_name not in self.baseline_metrics:
                # Calculate baseline from historical data
                self.baseline_metrics[service_name] = self._calculate_baseline(service_name)
            
            return self.baseline_metrics[service_name]
            
        except Exception as e:
            logger.error(f"Error getting baseline metrics for {service_name}: {e}")
            return {}
    
    def _calculate_baseline(self, service_name: str) -> Dict[str, float]:
        """Calculate baseline metrics from historical data"""
        try:
            # This would typically query historical metrics from your monitoring system
            # For now, we'll use reasonable defaults
            baseline = {
                'error_rate': 0.01,  # 1% baseline error rate
                'response_time_p95': 500,  # 500ms baseline response time
                'cpu_usage': 0.3,  # 30% baseline CPU usage
                'memory_usage': 0.5,  # 50% baseline memory usage
                'database_connections': 10  # 10 baseline database connections
            }
            
            return baseline
            
        except Exception as e:
            logger.error(f"Error calculating baseline for {service_name}: {e}")
            return {}
    
    def detect_anomalies(self, service_name: str) -> List[str]:
        """Detect anomalies in service metrics"""
        try:
            anomalies = []
            current_metrics = self._get_service_health_metrics(service_name)
            baseline = self.get_baseline_metrics(service_name)
            
            if not current_metrics or not baseline:
                return anomalies
            
            # Check for significant deviations from baseline
            if current_metrics.error_rate > baseline['error_rate'] * 5:
                anomalies.append(f"Error rate {current_metrics.error_rate:.2%} is significantly higher than baseline {baseline['error_rate']:.2%}")
            
            if current_metrics.response_time_p95 > baseline['response_time_p95'] * 3:
                anomalies.append(f"Response time {current_metrics.response_time_p95:.0f}ms is significantly higher than baseline {baseline['response_time_p95']:.0f}ms")
            
            if current_metrics.cpu_usage > baseline['cpu_usage'] * 2:
                anomalies.append(f"CPU usage {current_metrics.cpu_usage:.1%} is significantly higher than baseline {baseline['cpu_usage']:.1%}")
            
            if current_metrics.memory_usage > baseline['memory_usage'] * 1.5:
                anomalies.append(f"Memory usage {current_metrics.memory_usage:.1%} is significantly higher than baseline {baseline['memory_usage']:.1%}")
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting anomalies for {service_name}: {e}")
            return []
    
    def should_trigger_rollback(self, service_name: str) -> bool:
        """Determine if rollback should be triggered for a service"""
        try:
            # Check if service is healthy
            if self.is_service_healthy(service_name):
                return False
            
            # Check for critical issues
            health_score = self.get_service_health_score(service_name)
            if health_score < 30:
                logger.warning(f"Critical health score for {service_name}: {health_score}")
                return True
            
            # Check for consecutive failures
            if service_name in self.health_history:
                consecutive_failures = self.health_history[service_name].get('consecutive_failures', 0)
                if consecutive_failures >= 3:
                    logger.warning(f"Consecutive failures for {service_name}: {consecutive_failures}")
                    return True
            
            # Check for anomalies
            anomalies = self.detect_anomalies(service_name)
            if anomalies:
                logger.warning(f"Anomalies detected for {service_name}: {anomalies}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error determining rollback trigger for {service_name}: {e}")
            return False
    
    def update_health_history(self, service_name: str, metrics: 'HealthMetrics'):
        """Update health history for a service"""
        try:
            if service_name not in self.health_history:
                self.health_history[service_name] = {
                    'consecutive_failures': 0,
                    'last_healthy': None,
                    'health_trend': []
                }
            
            history = self.health_history[service_name]
            
            # Update consecutive failures
            if metrics.service_status == 'healthy':
                history['consecutive_failures'] = 0
                history['last_healthy'] = datetime.now()
            else:
                history['consecutive_failures'] += 1
            
            # Update health trend
            health_score = self.get_service_health_score(service_name)
            history['health_trend'].append({
                'timestamp': datetime.now().isoformat(),
                'health_score': health_score,
                'status': metrics.service_status
            })
            
            # Keep only last 100 entries
            if len(history['health_trend']) > 100:
                history['health_trend'] = history['health_trend'][-100:]
            
        except Exception as e:
            logger.error(f"Error updating health history for {service_name}: {e}")