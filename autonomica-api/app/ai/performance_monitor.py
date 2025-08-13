"""
Advanced Performance Monitoring System for Autonomica AI Models

This module provides comprehensive performance monitoring capabilities including:
- Real-time metrics collection
- Resource utilization tracking
- Performance analysis and alerting
- Historical data storage
- Performance optimization recommendations
"""

import asyncio
import time
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
import json
import os
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Container for performance metrics data."""
    timestamp: datetime
    model_name: str
    provider: str
    response_time_ms: float
    tokens_generated: int
    tokens_input: int
    memory_usage_mb: float
    cpu_usage_percent: float
    gpu_usage_percent: Optional[float] = None
    error_occurred: bool = False
    error_message: Optional[str] = None
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    task_type: Optional[str] = None
    cost_usd: Optional[float] = None

@dataclass
class ResourceMetrics:
    """Container for system resource metrics."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_available_gb: float
    disk_usage_percent: float
    network_io_mb: float
    gpu_memory_percent: Optional[float] = None
    gpu_utilization_percent: Optional[float] = None

@dataclass
class ModelPerformance:
    """Aggregated performance data for a specific model."""
    model_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time_ms: float = 0.0
    total_tokens_generated: int = 0
    total_tokens_input: int = 0
    total_cost_usd: float = 0.0
    avg_response_time_ms: float = 0.0
    success_rate: float = 0.0
    cost_per_token: float = 0.0
    last_used: Optional[datetime] = None
    performance_score: float = 0.0

class PerformanceMonitor:
    """Advanced performance monitoring system for AI models."""
    
    def __init__(self, storage_path: str = ".taskmaster/performance_data"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Metrics storage
        self.performance_metrics: deque = deque(maxlen=10000)  # Keep last 10k metrics
        self.resource_metrics: deque = deque(maxlen=1000)     # Keep last 1k resource snapshots
        self.model_performance: Dict[str, ModelPerformance] = defaultdict(ModelPerformance)
        
        # Monitoring state
        self.is_monitoring = False
        self.monitoring_interval = 5.0  # seconds
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Alert thresholds
        self.alert_thresholds = {
            "response_time_ms": 10000,      # 10 seconds
            "error_rate_percent": 5.0,      # 5% error rate
            "memory_usage_percent": 90.0,   # 90% memory usage
            "cpu_usage_percent": 95.0,      # 95% CPU usage
        }
        
        # Alert callbacks
        self.alert_callbacks: List[Callable] = []
        
        # Performance optimization
        self.optimization_recommendations: List[str] = []
        
        logger.info("Performance Monitor initialized")

    async def start_monitoring(self):
        """Start continuous performance monitoring."""
        if self.is_monitoring:
            logger.warning("Performance monitoring is already running")
            return
        
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Performance monitoring started")

    async def stop_monitoring(self):
        """Stop performance monitoring."""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Performance monitoring stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                # Collect system resource metrics
                await self._collect_resource_metrics()
                
                # Analyze performance and generate alerts
                await self._analyze_performance()
                
                # Generate optimization recommendations
                await self._generate_optimization_recommendations()
                
                # Save metrics to storage
                await self._save_metrics()
                
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.monitoring_interval)

    async def _collect_resource_metrics(self):
        """Collect system resource utilization metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_gb = memory.available / (1024**3)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage_percent = disk.percent
            
            # Network I/O
            network = psutil.net_io_counters()
            network_io_mb = (network.bytes_sent + network.bytes_recv) / (1024**2)
            
            # GPU metrics (if available)
            gpu_memory_percent = None
            gpu_utilization_percent = None
            
            try:
                # Try to get GPU metrics using nvidia-ml-py if available
                import pynvml
                pynvml.nvmlInit()
                device_count = pynvml.nvmlDeviceGetCount()
                if device_count > 0:
                    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                    memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    gpu_memory_percent = (memory_info.used / memory_info.total) * 100
                    gpu_utilization_percent = pynvml.nvmlDeviceGetUtilizationRates(handle).gpu
            except ImportError:
                pass  # GPU monitoring not available
            
            metrics = ResourceMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_available_gb=memory_available_gb,
                disk_usage_percent=disk_usage_percent,
                network_io_mb=network_io_mb,
                gpu_memory_percent=gpu_memory_percent,
                gpu_utilization_percent=gpu_utilization_percent
            )
            
            self.resource_metrics.append(metrics)
            
        except Exception as e:
            logger.error(f"Error collecting resource metrics: {e}")

    async def _analyze_performance(self):
        """Analyze performance metrics and generate alerts."""
        try:
            # Check for performance issues
            recent_metrics = list(self.performance_metrics)[-100:]  # Last 100 metrics
            
            if not recent_metrics:
                return
            
            # Calculate aggregate metrics
            total_requests = len(recent_metrics)
            error_count = sum(1 for m in recent_metrics if m.error_occurred)
            error_rate = (error_count / total_requests) * 100
            
            avg_response_time = sum(m.response_time_ms for m in recent_metrics) / total_requests
            
            # Check thresholds and generate alerts
            alerts = []
            
            if avg_response_time > self.alert_thresholds["response_time_ms"]:
                alerts.append(f"High response time: {avg_response_time:.2f}ms")
            
            if error_rate > self.alert_thresholds["error_rate_percent"]:
                alerts.append(f"High error rate: {error_rate:.2f}%")
            
            # Check resource usage
            if self.resource_metrics:
                latest_resource = self.resource_metrics[-1]
                
                if latest_resource.memory_percent > self.alert_thresholds["memory_usage_percent"]:
                    alerts.append(f"High memory usage: {latest_resource.memory_percent:.1f}%")
                
                if latest_resource.cpu_percent > self.alert_thresholds["cpu_usage_percent"]:
                    alerts.append(f"High CPU usage: {latest_resource.cpu_percent:.1f}%")
            
            # Trigger alert callbacks
            for alert in alerts:
                await self._trigger_alert(alert)
                
        except Exception as e:
            logger.error(f"Error analyzing performance: {e}")

    async def _generate_optimization_recommendations(self):
        """Generate performance optimization recommendations."""
        try:
            recommendations = []
            
            # Analyze model performance
            for model_name, performance in self.model_performance.items():
                if performance.total_requests < 10:
                    continue  # Need more data
                
                # Check for slow models
                if performance.avg_response_time_ms > 5000:
                    recommendations.append(f"Consider using a faster model alternative to {model_name}")
                
                # Check for expensive models
                if performance.cost_per_token > 0.001:
                    recommendations.append(f"Model {model_name} is expensive. Consider local alternatives")
                
                # Check for high error rates
                if performance.success_rate < 0.95:
                    recommendations.append(f"Model {model_name} has high error rate. Check configuration")
            
            # Check resource usage
            if self.resource_metrics:
                latest_resource = self.resource_metrics[-1]
                
                if latest_resource.memory_percent > 80:
                    recommendations.append("High memory usage. Consider reducing model memory or adding RAM")
                
                if latest_resource.cpu_percent > 90:
                    recommendations.append("High CPU usage. Consider load balancing or reducing concurrent requests")
            
            self.optimization_recommendations = recommendations
            
        except Exception as e:
            logger.error(f"Error generating optimization recommendations: {e}")

    async def _trigger_alert(self, message: str):
        """Trigger an alert to all registered callbacks."""
        alert_data = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "severity": "warning" if "High" in message else "info"
        }
        
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert_data)
                else:
                    callback(alert_data)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")

    async def _save_metrics(self):
        """Save metrics to persistent storage."""
        try:
            # Save performance metrics
            performance_file = self.storage_path / "performance_metrics.json"
            metrics_data = [
                {
                    "timestamp": m.timestamp.isoformat(),
                    "model_name": m.model_name,
                    "provider": m.provider,
                    "response_time_ms": m.response_time_ms,
                    "tokens_generated": m.tokens_generated,
                    "tokens_input": m.tokens_input,
                    "memory_usage_mb": m.memory_usage_mb,
                    "cpu_usage_percent": m.cpu_usage_percent,
                    "gpu_usage_percent": m.gpu_usage_percent,
                    "error_occurred": m.error_occurred,
                    "error_message": m.error_message,
                    "request_id": m.request_id,
                    "user_id": m.user_id,
                    "task_type": m.task_type,
                    "cost_usd": m.cost_usd
                }
                for m in self.performance_metrics
            ]
            
            with open(performance_file, 'w') as f:
                json.dump(metrics_data, f, indent=2)
            
            # Save resource metrics
            resource_file = self.storage_path / "resource_metrics.json"
            resource_data = [
                {
                    "timestamp": m.timestamp.isoformat(),
                    "cpu_percent": m.cpu_percent,
                    "memory_percent": m.memory_percent,
                    "memory_available_gb": m.memory_available_gb,
                    "disk_usage_percent": m.disk_usage_percent,
                    "network_io_mb": m.network_io_mb,
                    "gpu_memory_percent": m.gpu_memory_percent,
                    "gpu_utilization_percent": m.gpu_utilization_percent
                }
                for m in self.resource_metrics
            ]
            
            with open(resource_file, 'w') as f:
                json.dump(resource_data, f, indent=2)
            
            # Save model performance
            model_file = self.storage_path / "model_performance.json"
            model_data = {}
            for model_name, performance in self.model_performance.items():
                model_data[model_name] = {
                    "total_requests": performance.total_requests,
                    "successful_requests": performance.successful_requests,
                    "failed_requests": performance.failed_requests,
                    "total_response_time_ms": performance.total_response_time_ms,
                    "total_tokens_generated": performance.total_tokens_generated,
                    "total_tokens_input": performance.total_tokens_input,
                    "total_cost_usd": performance.total_cost_usd,
                    "avg_response_time_ms": performance.avg_response_time_ms,
                    "success_rate": performance.success_rate,
                    "cost_per_token": performance.cost_per_token,
                    "last_used": performance.last_used.isoformat() if performance.last_used else None,
                    "performance_score": performance.performance_score
                }
            
            with open(model_file, 'w') as f:
                json.dump(model_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")

    def record_request(self, metrics: PerformanceMetrics):
        """Record a new request performance metric."""
        self.performance_metrics.append(metrics)
        
        # Update model performance
        model_name = metrics.model_name
        if model_name not in self.model_performance:
            self.model_performance[model_name] = ModelPerformance(model_name=model_name)
        
        performance = self.model_performance[model_name]
        performance.total_requests += 1
        
        if metrics.error_occurred:
            performance.failed_requests += 1
        else:
            performance.successful_requests += 1
        
        performance.total_response_time_ms += metrics.response_time_ms
        performance.total_tokens_generated += metrics.tokens_generated
        performance.total_tokens_input += metrics.tokens_input
        performance.total_cost_usd += metrics.cost_usd or 0.0
        performance.last_used = metrics.timestamp
        
        # Update calculated fields
        performance.avg_response_time_ms = performance.total_response_time_ms / performance.total_requests
        performance.success_rate = performance.successful_requests / performance.total_requests
        performance.cost_per_token = performance.total_cost_usd / max(performance.total_tokens_generated, 1)
        
        # Calculate performance score (0-10)
        response_time_score = max(0, 10 - (performance.avg_response_time_ms / 1000))  # Penalize slow responses
        success_rate_score = performance.success_rate * 10  # Reward high success rates
        cost_score = max(0, 10 - (performance.cost_per_token * 10000))  # Penalize expensive models
        
        performance.performance_score = (response_time_score + success_rate_score + cost_score) / 3

    def add_alert_callback(self, callback: Callable):
        """Add a callback function for alerts."""
        self.alert_callbacks.append(callback)

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of current performance metrics."""
        try:
            summary = {
                "monitoring_active": self.is_monitoring,
                "total_requests": len(self.performance_metrics),
                "total_models": len(self.model_performance),
                "current_alerts": len(self.optimization_recommendations),
                "resource_usage": {},
                "top_performing_models": [],
                "recent_errors": []
            }
            
            # Add resource usage if available
            if self.resource_metrics:
                latest_resource = self.resource_metrics[-1]
                summary["resource_usage"] = {
                    "cpu_percent": latest_resource.cpu_percent,
                    "memory_percent": latest_resource.memory_percent,
                    "memory_available_gb": latest_resource.memory_available_gb,
                    "disk_usage_percent": latest_resource.disk_usage_percent
                }
            
            # Add top performing models
            sorted_models = sorted(
                self.model_performance.values(),
                key=lambda x: x.performance_score,
                reverse=True
            )[:5]
            
            summary["top_performing_models"] = [
                {
                    "name": m.model_name,
                    "performance_score": m.performance_score,
                    "avg_response_time_ms": m.avg_response_time_ms,
                    "success_rate": m.success_rate
                }
                for m in sorted_models
            ]
            
            # Add recent errors
            recent_errors = [
                m for m in list(self.performance_metrics)[-50:]
                if m.error_occurred
            ][-5:]  # Last 5 errors
            
            summary["recent_errors"] = [
                {
                    "timestamp": m.timestamp.isoformat(),
                    "model_name": m.model_name,
                    "error_message": m.error_message
                }
                for m in recent_errors
            ]
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating performance summary: {e}")
            return {"error": str(e)}

    def get_model_performance(self, model_name: str) -> Optional[ModelPerformance]:
        """Get performance data for a specific model."""
        return self.model_performance.get(model_name)

    def get_resource_history(self, hours: int = 24) -> List[ResourceMetrics]:
        """Get resource metrics history for the specified time period."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            m for m in self.resource_metrics
            if m.timestamp > cutoff_time
        ]

    def get_performance_history(self, model_name: str = None, hours: int = 24) -> List[PerformanceMetrics]:
        """Get performance metrics history for the specified time period and optionally model."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        metrics = [
            m for m in self.performance_metrics
            if m.timestamp > cutoff_time
        ]
        
        if model_name:
            metrics = [m for m in metrics if m.model_name == model_name]
        
        return metrics

    def export_metrics(self, format: str = "json", filepath: str = None) -> str:
        """Export metrics in the specified format."""
        try:
            if format.lower() == "json":
                data = {
                    "performance_metrics": [
                        {
                            "timestamp": m.timestamp.isoformat(),
                            "model_name": m.model_name,
                            "provider": m.provider,
                            "response_time_ms": m.response_time_ms,
                            "tokens_generated": m.tokens_generated,
                            "tokens_input": m.tokens_input,
                            "memory_usage_mb": m.memory_usage_mb,
                            "cpu_usage_percent": m.cpu_usage_percent,
                            "error_occurred": m.error_occurred,
                            "cost_usd": m.cost_usd
                        }
                        for m in self.performance_metrics
                    ],
                    "resource_metrics": [
                        {
                            "timestamp": m.timestamp.isoformat(),
                            "cpu_percent": m.cpu_percent,
                            "memory_percent": m.memory_percent,
                            "memory_available_gb": m.memory_available_gb
                        }
                        for m in self.resource_metrics
                    ],
                    "model_performance": {
                        name: {
                            "total_requests": perf.total_requests,
                            "success_rate": perf.success_rate,
                            "avg_response_time_ms": perf.avg_response_time_ms,
                            "performance_score": perf.performance_score
                        }
                        for name, perf in self.model_performance.items()
                    }
                }
                
                if filepath:
                    with open(filepath, 'w') as f:
                        json.dump(data, f, indent=2)
                    return f"Metrics exported to {filepath}"
                else:
                    return json.dumps(data, indent=2)
            
            elif format.lower() == "csv":
                # CSV export implementation
                return "CSV export not yet implemented"
            
            else:
                return f"Unsupported format: {format}"
                
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            return f"Export failed: {e}"

# Global performance monitor instance
performance_monitor = PerformanceMonitor()
