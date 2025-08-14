#!/usr/bin/env python3
"""
Metrics Collector Component for Rollback Service
Handles collection and storage of rollback metrics
"""

import time
import logging
import json
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import threading
import queue

logger = logging.getLogger(__name__)

@dataclass
class RollbackMetric:
    """Rollback metric data structure"""
    rollback_id: str
    deployment_id: str
    trigger: str
    severity: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    success: Optional[bool] = None
    strategy_used: Optional[str] = None
    actions_performed: Optional[List[str]] = None
    error_message: Optional[str] = None
    metrics_before: Optional[Dict[str, Any]] = None
    metrics_after: Optional[Dict[str, Any]] = None

class MetricsCollector:
    """Collects and stores rollback metrics for monitoring and analysis"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.metrics_enabled = config['rollback']['metrics']['enabled']
        self.prometheus_endpoint = config['rollback']['metrics']['prometheus_endpoint']
        self.metrics_storage = {}
        self.metrics_queue = queue.Queue()
        self.storage_thread = None
        self.running = False
        
        # Initialize custom metrics
        self.custom_metrics = {
            'rollback_count': 0,
            'rollback_duration_sum': 0.0,
            'rollback_success_count': 0,
            'deployment_failure_count': 0
        }
        
        logger.info("Metrics collector initialized")
    
    def start(self):
        """Start the metrics collector"""
        if self.running:
            logger.warning("Metrics collector is already running")
            return
        
        if not self.metrics_enabled:
            logger.info("Metrics collection is disabled")
            return
        
        self.running = True
        logger.info("Starting metrics collector...")
        
        # Start storage thread
        self.storage_thread = threading.Thread(target=self._storage_loop)
        self.storage_thread.daemon = True
        self.storage_thread.start()
        
        logger.info("Metrics collector started successfully")
    
    def stop(self):
        """Stop the metrics collector"""
        self.running = False
        logger.info("Stopping metrics collector...")
        
        if self.storage_thread:
            self.storage_thread.join(timeout=10)
        
        logger.info("Metrics collector stopped")
    
    def store_metrics(self, health_metrics: Dict[str, Any]):
        """Store health metrics for analysis"""
        try:
            if not self.metrics_enabled:
                return
            
            timestamp = datetime.now()
            
            for service_name, metrics in health_metrics.items():
                if service_name not in self.metrics_storage:
                    self.metrics_storage[service_name] = []
                
                # Store metrics with timestamp
                metric_entry = {
                    'timestamp': timestamp.isoformat(),
                    'service_name': service_name,
                    'metrics': metrics
                }
                
                self.metrics_storage[service_name].append(metric_entry)
                
                # Keep only last 1000 entries per service
                if len(self.metrics_storage[service_name]) > 1000:
                    self.metrics_storage[service_name] = self.metrics_storage[service_name][-1000:]
            
        except Exception as e:
            logger.error(f"Error storing health metrics: {e}")
    
    def capture_metrics(self, rollback_event: 'RollbackEvent', action: Dict[str, Any]) -> bool:
        """Capture metrics before and after rollback"""
        try:
            if not self.metrics_enabled:
                return True
            
            logger.info(f"Capturing metrics for rollback {rollback_event.id}")
            
            # Capture metrics before rollback
            metrics_before = self._capture_current_metrics()
            
            # Store rollback metric
            rollback_metric = RollbackMetric(
                rollback_id=rollback_event.id,
                deployment_id=rollback_event.deployment_id,
                trigger=rollback_event.trigger.value,
                severity=rollback_event.severity,
                start_time=rollback_event.timestamp,
                metrics_before=metrics_before,
                actions_performed=[]
            )
            
            # Add to metrics queue for processing
            self.metrics_queue.put(rollback_metric)
            
            return True
            
        except Exception as e:
            logger.error(f"Error capturing metrics for rollback: {e}")
            return False
    
    def update_rollback_metric(self, rollback_id: str, **kwargs):
        """Update rollback metric with additional information"""
        try:
            if not self.metrics_enabled:
                return
            
            # Find the metric in the queue and update it
            # This is a simplified approach - in production, you'd use a proper database
            logger.info(f"Updating rollback metric {rollback_id}")
            
        except Exception as e:
            logger.error(f"Error updating rollback metric: {e}")
    
    def finalize_rollback_metric(self, rollback_id: str, success: bool, duration: float, 
                                strategy_used: str, actions_performed: List[str], 
                                error_message: Optional[str] = None):
        """Finalize rollback metric with completion data"""
        try:
            if not self.metrics_enabled:
                return
            
            logger.info(f"Finalizing rollback metric {rollback_id}")
            
            # Update custom metrics
            self.custom_metrics['rollback_count'] += 1
            self.custom_metrics['rollback_duration_sum'] += duration
            
            if success:
                self.custom_metrics['rollback_success_count'] += 1
            
            # Send metrics to Prometheus
            self._send_metrics_to_prometheus(rollback_id, success, duration, strategy_used)
            
        except Exception as e:
            logger.error(f"Error finalizing rollback metric: {e}")
    
    def _capture_current_metrics(self) -> Dict[str, Any]:
        """Capture current system metrics"""
        try:
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'system': self._get_system_metrics(),
                'services': self._get_service_metrics(),
                'infrastructure': self._get_infrastructure_metrics()
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error capturing current metrics: {e}")
            return {}
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get system-level metrics"""
        try:
            # This would typically query system metrics from your monitoring system
            # For now, we'll return placeholder data
            return {
                'cpu_usage': 0.0,
                'memory_usage': 0.0,
                'disk_usage': 0.0,
                'network_io': 0.0
            }
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}
    
    def _get_service_metrics(self) -> Dict[str, Any]:
        """Get service-level metrics"""
        try:
            # This would typically query service metrics from your monitoring system
            # For now, we'll return placeholder data
            return {
                'frontend': {
                    'error_rate': 0.0,
                    'response_time_p95': 0.0,
                    'requests_per_second': 0.0
                },
                'api': {
                    'error_rate': 0.0,
                    'response_time_p95': 0.0,
                    'requests_per_second': 0.0
                },
                'worker': {
                    'error_rate': 0.0,
                    'response_time_p95': 0.0,
                    'tasks_per_second': 0.0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting service metrics: {e}")
            return {}
    
    def _get_infrastructure_metrics(self) -> Dict[str, Any]:
        """Get infrastructure metrics"""
        try:
            # This would typically query infrastructure metrics from your monitoring system
            # For now, we'll return placeholder data
            return {
                'database': {
                    'connection_count': 0,
                    'query_performance': 0.0,
                    'disk_usage': 0.0
                },
                'redis': {
                    'memory_usage': 0.0,
                    'operations_per_second': 0.0,
                    'connection_count': 0
                },
                'load_balancer': {
                    'requests_per_second': 0.0,
                    'error_rate': 0.0,
                    'response_time': 0.0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting infrastructure metrics: {e}")
            return {}
    
    def _send_metrics_to_prometheus(self, rollback_id: str, success: bool, duration: float, strategy_used: str):
        """Send rollback metrics to Prometheus"""
        try:
            if not self.prometheus_endpoint:
                logger.warning("Prometheus endpoint not configured")
                return
            
            # Prepare metrics for Prometheus
            metrics_data = [
                {
                    'name': 'rollback_count_total',
                    'type': 'counter',
                    'help': 'Total number of rollbacks',
                    'value': self.custom_metrics['rollback_count']
                },
                {
                    'name': 'rollback_duration_seconds',
                    'type': 'histogram',
                    'help': 'Time taken for rollbacks',
                    'value': duration,
                    'labels': {
                        'rollback_id': rollback_id,
                        'strategy': strategy_used,
                        'success': str(success).lower()
                    }
                },
                {
                    'name': 'rollback_success_rate',
                    'type': 'gauge',
                    'help': 'Success rate of rollbacks',
                    'value': self.custom_metrics['rollback_success_count'] / max(self.custom_metrics['rollback_count'], 1)
                }
            ]
            
            # Send metrics to Prometheus
            for metric in metrics_data:
                self._send_prometheus_metric(metric)
            
        except Exception as e:
            logger.error(f"Error sending metrics to Prometheus: {e}")
    
    def _send_prometheus_metric(self, metric: Dict[str, Any]):
        """Send a single metric to Prometheus"""
        try:
            # This would typically use the Prometheus client library
            # For now, we'll simulate the process
            
            logger.debug(f"Sending metric to Prometheus: {metric['name']} = {metric['value']}")
            
        except Exception as e:
            logger.error(f"Error sending Prometheus metric: {e}")
    
    def _storage_loop(self):
        """Main storage loop for processing metrics"""
        while self.running:
            try:
                # Get metric from queue
                try:
                    metric = self.metrics_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                # Process metric
                self._process_metric(metric)
                
            except Exception as e:
                logger.error(f"Error in metrics storage loop: {e}")
                time.sleep(5)
    
    def _process_metric(self, metric: RollbackMetric):
        """Process a single metric"""
        try:
            logger.debug(f"Processing metric for rollback {metric.rollback_id}")
            
            # Store metric in persistent storage
            self._store_rollback_metric(metric)
            
            # Update aggregated metrics
            self._update_aggregated_metrics(metric)
            
        except Exception as e:
            logger.error(f"Error processing metric: {e}")
    
    def _store_rollback_metric(self, metric: RollbackMetric):
        """Store rollback metric in persistent storage"""
        try:
            # This would typically store in a database
            # For now, we'll store in memory
            metric_key = f"rollback_{metric.rollback_id}"
            
            # Convert to dictionary for storage
            metric_dict = asdict(metric)
            
            # Store in memory (in production, this would be a database)
            self.metrics_storage[metric_key] = metric_dict
            
            logger.debug(f"Stored rollback metric: {metric_key}")
            
        except Exception as e:
            logger.error(f"Error storing rollback metric: {e}")
    
    def _update_aggregated_metrics(self, metric: RollbackMetric):
        """Update aggregated metrics"""
        try:
            # Update rollback count
            self.custom_metrics['rollback_count'] += 1
            
            # Update duration metrics if available
            if metric.duration:
                self.custom_metrics['rollback_duration_sum'] += metric.duration
            
            # Update success metrics if available
            if metric.success is not None:
                if metric.success:
                    self.custom_metrics['rollback_success_count'] += 1
            
            logger.debug("Updated aggregated metrics")
            
        except Exception as e:
            logger.error(f"Error updating aggregated metrics: {e}")
    
    def get_rollback_metrics(self, rollback_id: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific rollback"""
        try:
            metric_key = f"rollback_{rollback_id}"
            return self.metrics_storage.get(metric_key)
            
        except Exception as e:
            logger.error(f"Error getting rollback metrics: {e}")
            return None
    
    def get_rollback_statistics(self, time_period: str = '24h') -> Dict[str, Any]:
        """Get rollback statistics for a time period"""
        try:
            if not self.metrics_enabled:
                return {}
            
            # Calculate time range
            end_time = datetime.now()
            if time_period == '1h':
                start_time = end_time - timedelta(hours=1)
            elif time_period == '24h':
                start_time = end_time - timedelta(days=1)
            elif time_period == '7d':
                start_time = end_time - timedelta(days=7)
            elif time_period == '30d':
                start_time = end_time - timedelta(days=30)
            else:
                start_time = end_time - timedelta(days=1)
            
            # Filter metrics by time range
            filtered_metrics = []
            for metric_key, metric_data in self.metrics_storage.items():
                if metric_key.startswith('rollback_'):
                    metric_timestamp = datetime.fromisoformat(metric_data['start_time'])
                    if start_time <= metric_timestamp <= end_time:
                        filtered_metrics.append(metric_data)
            
            # Calculate statistics
            total_rollbacks = len(filtered_metrics)
            successful_rollbacks = sum(1 for m in filtered_metrics if m.get('success', False))
            failed_rollbacks = total_rollbacks - successful_rollbacks
            
            durations = [m.get('duration', 0) for m in filtered_metrics if m.get('duration')]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            # Group by trigger
            triggers = {}
            for metric in filtered_metrics:
                trigger = metric.get('trigger', 'unknown')
                if trigger not in triggers:
                    triggers[trigger] = 0
                triggers[trigger] += 1
            
            # Group by strategy
            strategies = {}
            for metric in filtered_metrics:
                strategy = metric.get('strategy_used', 'unknown')
                if strategy not in strategies:
                    strategies[strategy] = 0
                strategies[strategy] += 1
            
            statistics = {
                'time_period': time_period,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'total_rollbacks': total_rollbacks,
                'successful_rollbacks': successful_rollbacks,
                'failed_rollbacks': failed_rollbacks,
                'success_rate': (successful_rollbacks / total_rollbacks * 100) if total_rollbacks > 0 else 0,
                'average_duration': avg_duration,
                'triggers': triggers,
                'strategies': strategies
            }
            
            return statistics
            
        except Exception as e:
            logger.error(f"Error getting rollback statistics: {e}")
            return {}
    
    def export_metrics(self, format: str = 'json') -> str:
        """Export metrics in specified format"""
        try:
            if format == 'json':
                return json.dumps(self.metrics_storage, indent=2, default=str)
            elif format == 'csv':
                return self._export_csv()
            else:
                logger.warning(f"Unsupported export format: {format}")
                return ""
                
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            return ""
    
    def _export_csv(self) -> str:
        """Export metrics as CSV"""
        try:
            csv_lines = []
            
            # Header
            csv_lines.append("rollback_id,deployment_id,trigger,severity,start_time,end_time,duration,success,strategy_used")
            
            # Data rows
            for metric_key, metric_data in self.metrics_storage.items():
                if metric_key.startswith('rollback_'):
                    row = [
                        metric_data.get('rollback_id', ''),
                        metric_data.get('deployment_id', ''),
                        metric_data.get('trigger', ''),
                        metric_data.get('severity', ''),
                        metric_data.get('start_time', ''),
                        metric_data.get('end_time', ''),
                        metric_data.get('duration', ''),
                        metric_data.get('success', ''),
                        metric_data.get('strategy_used', '')
                    ]
                    csv_lines.append(','.join(str(field) for field in row))
            
            return '\n'.join(csv_lines)
            
        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            return ""
    
    def cleanup_old_metrics(self, retention_days: int = 90):
        """Clean up old metrics based on retention policy"""
        try:
            if not self.metrics_enabled:
                return
            
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            metrics_to_remove = []
            
            for metric_key, metric_data in self.metrics_storage.items():
                if metric_key.startswith('rollback_'):
                    metric_timestamp = datetime.fromisoformat(metric_data['start_time'])
                    if metric_timestamp < cutoff_date:
                        metrics_to_remove.append(metric_key)
            
            # Remove old metrics
            for metric_key in metrics_to_remove:
                del self.metrics_storage[metric_key]
            
            logger.info(f"Cleaned up {len(metrics_to_remove)} old metrics")
            
        except Exception as e:
            logger.error(f"Error cleaning up old metrics: {e}")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        try:
            if not self.metrics_enabled:
                return {'enabled': False}
            
            summary = {
                'enabled': True,
                'total_metrics_stored': len(self.metrics_storage),
                'rollback_metrics': len([k for k in self.metrics_storage.keys() if k.startswith('rollback_')]),
                'custom_metrics': self.custom_metrics.copy(),
                'storage_size_mb': len(json.dumps(self.metrics_storage)) / (1024 * 1024),
                'last_updated': datetime.now().isoformat()
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting metrics summary: {e}")
            return {'enabled': False, 'error': str(e)}