"""
Ollama-Specific Performance Monitoring System

This module extends the base PerformanceMonitor with Ollama-specific features:
- Real-time Ollama model performance tracking
- GPU utilization monitoring for CUDA-enabled models
- Model-specific resource allocation tracking
- Ollama service health monitoring
- Performance optimization recommendations for local models
"""

import asyncio
import time
import psutil
import logging
import json
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
import os
from pathlib import Path

from .performance_monitor import PerformanceMonitor, PerformanceMetrics, ResourceMetrics, ModelPerformance

logger = logging.getLogger(__name__)

@dataclass
class OllamaModelMetrics:
    """Ollama-specific model performance metrics."""
    model_name: str
    timestamp: datetime
    response_time_ms: float
    tokens_generated: int
    tokens_input: int
    eval_duration_ms: float
    load_duration_ms: float
    prompt_eval_duration_ms: float
    total_duration_ms: float
    memory_usage_mb: float
    gpu_utilization_percent: Optional[float] = None
    model_size_gb: Optional[float] = None
    context_length: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    error_occurred: bool = False
    error_message: Optional[str] = None

@dataclass
class OllamaSystemMetrics:
    """System-level metrics for Ollama service."""
    timestamp: datetime
    cpu_usage_percent: float
    memory_usage_percent: float
    memory_available_gb: float
    disk_usage_percent: float
    network_io_mbps: float
    active_connections: int
    models_loaded: int
    total_models: int
    gpu_usage_percent: Optional[float] = None
    gpu_memory_used_gb: Optional[float] = None
    gpu_memory_total_gb: Optional[float] = None

@dataclass
class OllamaPerformanceAlert:
    """Performance alert for Ollama models."""
    timestamp: datetime
    alert_type: str
    severity: str  # "low", "medium", "high", "critical"
    message: str
    model_name: Optional[str] = None
    metric_value: Optional[float] = None
    threshold: Optional[float] = None
    recommendation: Optional[str] = None

class OllamaPerformanceMonitor(PerformanceMonitor):
    """Advanced performance monitoring system specifically for Ollama models."""
    
    def __init__(self, ollama_base_url: str = "http://localhost:11434", storage_path: str = ".taskmaster/ollama_performance_data"):
        super().__init__(storage_path)
        
        self.ollama_base_url = ollama_base_url
        self.ollama_client = httpx.AsyncClient(timeout=10.0)
        
        # Ollama-specific storage
        self.ollama_metrics: deque = deque(maxlen=50000)  # Keep last 50k Ollama metrics
        self.system_metrics: deque = deque(maxlen=10000)  # Keep last 10k system snapshots
        self.performance_alerts: deque = deque(maxlen=1000)  # Keep last 1k alerts
        
        # Ollama-specific thresholds
        self.ollama_alert_thresholds = {
            "response_time_ms": 30000,        # 30 seconds (local models can be slower)
            "error_rate_percent": 10.0,       # 10% error rate
            "memory_usage_percent": 95.0,     # 95% memory usage
            "cpu_usage_percent": 98.0,        # 98% CPU usage
            "gpu_usage_percent": 95.0,        # 95% GPU usage
            "model_load_time_ms": 60000,      # 60 seconds to load model
            "context_length_utilization": 90.0,  # 90% of max context length
        }
        
        # Performance optimization recommendations
        self.ollama_optimizations = {
            "high_memory": "Consider reducing model size or using quantization",
            "slow_response": "Model may be too large for available resources",
            "high_gpu": "GPU memory may be insufficient for current model",
            "context_overflow": "Input exceeds model's context window",
            "resource_contention": "Multiple models competing for resources"
        }
        
        # GPU detection
        self.gpu_available = self._detect_gpu()
        if self.gpu_available:
            logger.info("GPU detected - enabling GPU monitoring")
        else:
            logger.info("No GPU detected - CPU-only monitoring enabled")
        
        logger.info("Ollama Performance Monitor initialized")

    def _detect_gpu(self) -> bool:
        """Detect if GPU is available for monitoring."""
        try:
            # Check for NVIDIA GPU
            if os.path.exists("/proc/driver/nvidia"):
                return True
            
            # Check for CUDA environment
            if os.environ.get("CUDA_VISIBLE_DEVICES"):
                return True
                
            # Check for GPU processes
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] and 'nvidia' in proc.info['name'].lower():
                    return True
                    
            return False
        except Exception:
            return False

    async def collect_ollama_metrics(self, model_name: str, response_data: Dict[str, Any], 
                                   start_time: float, error: Optional[str] = None) -> OllamaModelMetrics:
        """Collect detailed metrics from an Ollama model response."""
        try:
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            # Extract Ollama-specific timing data
            eval_duration_ms = response_data.get("eval_duration", 0) / 1_000_000  # Convert from nanoseconds
            load_duration_ms = response_data.get("load_duration", 0) / 1_000_000
            prompt_eval_duration_ms = response_data.get("prompt_eval_duration", 0) / 1_000_000
            total_duration_ms = response_data.get("total_duration", 0) / 1_000_000
            
            # Get current system resource usage
            memory_usage_mb = psutil.virtual_memory().used / (1024 * 1024)
            gpu_utilization = await self._get_gpu_utilization() if self.gpu_available else None
            
            # Get model information
            model_info = await self._get_model_info(model_name)
            model_size_gb = model_info.get("size", 0) / (1024 * 1024 * 1024) if model_info else None
            
            metrics = OllamaModelMetrics(
                model_name=model_name,
                timestamp=datetime.now(),
                response_time_ms=response_time_ms,
                tokens_generated=response_data.get("eval_count", 0),
                tokens_input=response_data.get("prompt_eval_count", 0),
                eval_duration_ms=eval_duration_ms,
                load_duration_ms=load_duration_ms,
                prompt_eval_duration_ms=prompt_eval_duration_ms,
                total_duration_ms=total_duration_ms,
                memory_usage_mb=memory_usage_mb,
                gpu_utilization_percent=gpu_utilization,
                model_size_gb=model_size_gb,
                context_length=model_info.get("context_length") if model_info else None,
                temperature=response_data.get("temperature", 0.7),
                top_p=response_data.get("top_p", 0.9),
                error_occurred=error is not None,
                error_message=error
            )
            
            self.ollama_metrics.append(metrics)
            self._check_ollama_alerts(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting Ollama metrics: {e}")
            # Return basic metrics on error
            return OllamaModelMetrics(
                model_name=model_name,
                timestamp=datetime.now(),
                response_time_ms=0,
                tokens_generated=0,
                tokens_input=0,
                eval_duration_ms=0,
                load_duration_ms=0,
                prompt_eval_duration_ms=0,
                total_duration_ms=0,
                memory_usage_mb=0,
                error_occurred=True,
                error_message=str(e)
            )

    async def collect_system_metrics(self) -> OllamaSystemMetrics:
        """Collect comprehensive system metrics for Ollama service."""
        try:
            # Basic system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Network I/O
            net_io = psutil.net_io_counters()
            network_io_mbps = (net_io.bytes_sent + net_io.bytes_recv) / (1024 * 1024)
            
            # GPU metrics if available
            gpu_usage = None
            gpu_memory_used = None
            gpu_memory_total = None
            
            if self.gpu_available:
                gpu_usage = await self._get_gpu_utilization()
                gpu_memory_used, gpu_memory_total = await self._get_gpu_memory()
            
            # Ollama-specific metrics
            models_loaded, total_models = await self._get_ollama_model_counts()
            active_connections = await self._get_active_connections()
            
            metrics = OllamaSystemMetrics(
                timestamp=datetime.now(),
                cpu_usage_percent=cpu_percent,
                memory_usage_percent=memory.percent,
                memory_available_gb=memory.available / (1024 * 1024 * 1024),
                gpu_usage_percent=gpu_usage,
                gpu_memory_used_gb=gpu_memory_used,
                gpu_memory_total_gb=gpu_memory_total,
                disk_usage_percent=disk.percent,
                network_io_mbps=network_io_mbps,
                active_connections=active_connections,
                models_loaded=models_loaded,
                total_models=total_models
            )
            
            self.system_metrics.append(metrics)
            self._check_system_alerts(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return None

    async def _get_gpu_utilization(self) -> Optional[float]:
        """Get current GPU utilization percentage."""
        try:
            # Try using nvidia-smi if available
            result = await asyncio.create_subprocess_exec(
                "nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0 and stdout:
                utilization = float(stdout.decode().strip())
                return utilization
                
        except Exception as e:
            logger.debug(f"Could not get GPU utilization: {e}")
            
        return None

    async def _get_gpu_memory(self) -> tuple[Optional[float], Optional[float]]:
        """Get GPU memory usage in GB."""
        try:
            result = await asyncio.create_subprocess_exec(
                "nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0 and stdout:
                lines = stdout.decode().strip().split('\n')
                if lines:
                    parts = lines[0].split(', ')
                    if len(parts) >= 2:
                        used_mb = float(parts[0].replace(' MiB', ''))
                        total_mb = float(parts[1].replace(' MiB', ''))
                        return used_mb / 1024, total_mb / 1024  # Convert to GB
                        
        except Exception as e:
            logger.debug(f"Could not get GPU memory: {e}")
            
        return None, None

    async def _get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific model."""
        try:
            response = await self.ollama_client.get(f"{self.ollama_base_url}/api/show", params={"name": model_name})
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.debug(f"Could not get model info for {model_name}: {e}")
        return None

    async def _get_ollama_model_counts(self) -> tuple[int, int]:
        """Get count of loaded and total models."""
        try:
            response = await self.ollama_client.get(f"{self.ollama_base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                total_models = len(models)
                
                # Count loaded models (this is a simplified approach)
                loaded_models = 0
                for model in models:
                    try:
                        # Try to get model info to see if it's loaded
                        info_response = await self.ollama_client.get(
                            f"{self.ollama_base_url}/api/show", 
                            params={"name": model["name"]}
                        )
                        if info_response.status_code == 200:
                            loaded_models += 1
                    except:
                        continue
                        
                return loaded_models, total_models
        except Exception as e:
            logger.debug(f"Could not get Ollama model counts: {e}")
        return 0, 0

    async def _get_active_connections(self) -> int:
        """Get count of active connections to Ollama service."""
        try:
            # This is a simplified approach - in production you might want to track actual connections
            result = await asyncio.create_subprocess_exec(
                "netstat", "-an", "|", "grep", ":11434", "|", "grep", "ESTABLISHED", "|", "wc", "-l",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0 and stdout:
                return int(stdout.decode().strip())
        except Exception as e:
            logger.debug(f"Could not get active connections: {e}")
        return 0

    def _check_ollama_alerts(self, metrics: OllamaModelMetrics):
        """Check for performance alerts based on Ollama metrics."""
        alerts = []
        
        # Response time alert
        if metrics.response_time_ms > self.ollama_alert_thresholds["response_time_ms"]:
            alerts.append(OllamaPerformanceAlert(
                timestamp=datetime.now(),
                alert_type="slow_response",
                severity="high" if metrics.response_time_ms > 60000 else "medium",
                message=f"Model {metrics.model_name} response time ({metrics.response_time_ms:.0f}ms) exceeds threshold",
                model_name=metrics.model_name,
                metric_value=metrics.response_time_ms,
                threshold=self.ollama_alert_thresholds["response_time_ms"],
                recommendation="Consider using a smaller model or optimizing input length"
            ))
        
        # Model load time alert
        if metrics.load_duration_ms > self.ollama_alert_thresholds["model_load_time_ms"]:
            alerts.append(OllamaPerformanceAlert(
                timestamp=datetime.now(),
                alert_type="slow_model_load",
                severity="medium",
                message=f"Model {metrics.model_name} took {metrics.load_duration_ms:.0f}ms to load",
                model_name=metrics.model_name,
                metric_value=metrics.load_duration_ms,
                threshold=self.ollama_alert_thresholds["model_load_time_ms"],
                recommendation="Model may be too large for available resources"
            ))
        
        # Context length alert
        if metrics.context_length and metrics.tokens_input:
            utilization = (metrics.tokens_input / metrics.context_length) * 100
            if utilization > self.ollama_alert_thresholds["context_length_utilization"]:
                alerts.append(OllamaPerformanceAlert(
                    timestamp=datetime.now(),
                    alert_type="context_overflow",
                    severity="medium",
                    message=f"Input uses {utilization:.1f}% of model context window",
                    model_name=metrics.model_name,
                    metric_value=utilization,
                    threshold=self.ollama_alert_thresholds["context_length_utilization"],
                    recommendation="Consider shortening input or using a model with larger context"
                ))
        
        # Add alerts to the queue
        for alert in alerts:
            self.performance_alerts.append(alert)
            logger.warning(f"Performance alert: {alert.message}")

    def _check_system_alerts(self, metrics: OllamaSystemMetrics):
        """Check for system-level performance alerts."""
        alerts = []
        
        # Memory usage alert
        if metrics.memory_usage_percent > self.ollama_alert_thresholds["memory_usage_percent"]:
            alerts.append(OllamaPerformanceAlert(
                timestamp=datetime.now(),
                alert_type="high_memory",
                severity="high" if metrics.memory_usage_percent > 98 else "medium",
                message=f"System memory usage is {metrics.memory_usage_percent:.1f}%",
                metric_value=metrics.memory_usage_percent,
                threshold=self.ollama_alert_thresholds["memory_usage_percent"],
                recommendation="Consider reducing model size or stopping unused models"
            ))
        
        # CPU usage alert
        if metrics.cpu_usage_percent > self.ollama_alert_thresholds["cpu_usage_percent"]:
            alerts.append(OllamaPerformanceAlert(
                timestamp=datetime.now(),
                alert_type="high_cpu",
                severity="medium",
                message=f"System CPU usage is {metrics.cpu_usage_percent:.1f}%",
                metric_value=metrics.cpu_usage_percent,
                threshold=self.ollama_alert_thresholds["cpu_usage_percent"],
                recommendation="System may be overloaded, consider reducing concurrent requests"
            ))
        
        # GPU usage alert
        if metrics.gpu_usage_percent and metrics.gpu_usage_percent > self.ollama_alert_thresholds["gpu_usage_percent"]:
            alerts.append(OllamaPerformanceAlert(
                timestamp=datetime.now(),
                alert_type="high_gpu",
                severity="high" if metrics.gpu_usage_percent > 98 else "medium",
                message=f"GPU usage is {metrics.gpu_usage_percent:.1f}%",
                metric_value=metrics.gpu_usage_percent,
                threshold=self.ollama_alert_thresholds["gpu_usage_percent"],
                recommendation="GPU memory may be insufficient for current models"
            ))
        
        # Add alerts to the queue
        for alert in alerts:
            self.performance_alerts.append(alert)
            logger.warning(f"System alert: {alert.message}")

    def get_ollama_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary for Ollama models."""
        try:
            summary = {
                "monitoring_active": self.is_monitoring,
                "gpu_available": self.gpu_available,
                "total_ollama_requests": len(self.ollama_metrics),
                "total_system_snapshots": len(self.system_metrics),
                "active_alerts": len(self.performance_alerts),
                "models_performance": {},
                "system_health": {},
                "recent_alerts": [],
                "optimization_recommendations": []
            }
            
            # Model performance summary
            for model_name in set(m.model_name for m in self.ollama_metrics):
                model_metrics = [m for m in self.ollama_metrics if m.model_name == model_name]
                if model_metrics:
                    recent_metrics = model_metrics[-100:]  # Last 100 requests
                    
                    avg_response_time = sum(m.response_time_ms for m in recent_metrics) / len(recent_metrics)
                    avg_tokens_per_second = sum(m.tokens_generated for m in recent_metrics) / max(sum(m.total_duration_ms for m in recent_metrics) / 1000, 1)
                    success_rate = sum(1 for m in recent_metrics if not m.error_occurred) / len(recent_metrics)
                    
                    summary["models_performance"][model_name] = {
                        "total_requests": len(model_metrics),
                        "recent_requests": len(recent_metrics),
                        "avg_response_time_ms": avg_response_time,
                        "avg_tokens_per_second": avg_tokens_per_second,
                        "success_rate": success_rate,
                        "last_used": recent_metrics[-1].timestamp.isoformat() if recent_metrics else None
                    }
            
            # System health summary
            if self.system_metrics:
                latest_system = self.system_metrics[-1]
                summary["system_health"] = {
                    "cpu_usage_percent": latest_system.cpu_usage_percent,
                    "memory_usage_percent": latest_system.memory_usage_percent,
                    "memory_available_gb": latest_system.memory_available_gb,
                    "gpu_usage_percent": latest_system.gpu_usage_percent,
                    "gpu_memory_used_gb": latest_system.gpu_memory_used_gb,
                    "gpu_memory_total_gb": latest_system.gpu_memory_total_gb,
                    "disk_usage_percent": latest_system.disk_usage_percent,
                    "active_connections": latest_system.active_connections,
                    "models_loaded": latest_system.models_loaded,
                    "total_models": latest_system.total_models
                }
            
            # Recent alerts
            recent_alerts = list(self.performance_alerts)[-10:]  # Last 10 alerts
            summary["recent_alerts"] = [
                {
                    "timestamp": alert.timestamp.isoformat(),
                    "type": alert.alert_type,
                    "severity": alert.severity,
                    "message": alert.message,
                    "model_name": alert.model_name,
                    "recommendation": alert.recommendation
                }
                for alert in recent_alerts
            ]
            
            # Generate optimization recommendations
            summary["optimization_recommendations"] = self._generate_optimization_recommendations()
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating Ollama performance summary: {e}")
            return {"error": str(e)}

    def _generate_optimization_recommendations(self) -> List[str]:
        """Generate optimization recommendations based on current performance data."""
        recommendations = []
        
        if not self.system_metrics or not self.ollama_metrics:
            return recommendations
        
        latest_system = self.system_metrics[-1]
        recent_models = list(self.ollama_metrics)[-100:]  # Last 100 model requests
        
        # Memory optimization
        if latest_system.memory_usage_percent > 80:
            recommendations.append("High memory usage detected. Consider using quantized models or reducing concurrent model loads.")
        
        # GPU optimization
        if latest_system.gpu_usage_percent and latest_system.gpu_usage_percent > 80:
            recommendations.append("High GPU usage detected. Consider using smaller models or implementing model offloading.")
        
        # Response time optimization
        slow_responses = [m for m in recent_models if m.response_time_ms > 30000]
        if len(slow_responses) > len(recent_models) * 0.2:  # More than 20% slow responses
            recommendations.append("High number of slow responses detected. Consider using faster models or optimizing input length.")
        
        # Model efficiency
        if recent_models:
            avg_tokens_per_second = sum(m.tokens_generated for m in recent_models) / max(sum(m.total_duration_ms for m in recent_models) / 1000, 1)
            if avg_tokens_per_second < 10:  # Less than 10 tokens per second
                recommendations.append("Low token generation rate detected. Consider using more efficient models or checking system resources.")
        
        return recommendations

    async def export_ollama_metrics(self, format: str = "json", filepath: str = None) -> str:
        """Export Ollama-specific metrics in the specified format."""
        try:
            if not filepath:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filepath = f"{self.storage_path}/ollama_metrics_{timestamp}.{format}"
            
            if format.lower() == "json":
                data = {
                    "export_timestamp": datetime.now().isoformat(),
                    "ollama_metrics": [self._serialize_ollama_metrics(m) for m in self.ollama_metrics],
                    "system_metrics": [self._serialize_system_metrics(m) for m in self.system_metrics],
                    "performance_alerts": [self._serialize_alert(a) for a in self.performance_alerts]
                }
                
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
                    
            elif format.lower() == "csv":
                # CSV export implementation
                import csv
                with open(filepath, 'w', newline='') as f:
                    writer = csv.writer(f)
                    # Write headers
                    writer.writerow([
                        "timestamp", "model_name", "response_time_ms", "tokens_generated", 
                        "tokens_input", "eval_duration_ms", "memory_usage_mb", "gpu_utilization_percent"
                    ])
                    # Write data
                    for metric in self.ollama_metrics:
                        writer.writerow([
                            metric.timestamp.isoformat(),
                            metric.model_name,
                            metric.response_time_ms,
                            metric.tokens_generated,
                            metric.tokens_input,
                            metric.eval_duration_ms,
                            metric.memory_usage_mb,
                            metric.gpu_utilization_percent or 0
                        ])
            
            logger.info(f"Ollama metrics exported to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exporting Ollama metrics: {e}")
            raise

    def _serialize_ollama_metrics(self, metrics: OllamaModelMetrics) -> Dict[str, Any]:
        """Serialize OllamaModelMetrics for JSON export."""
        return {
            "timestamp": metrics.timestamp.isoformat(),
            "model_name": metrics.model_name,
            "response_time_ms": metrics.response_time_ms,
            "tokens_generated": metrics.tokens_generated,
            "tokens_input": metrics.tokens_input,
            "eval_duration_ms": metrics.eval_duration_ms,
            "load_duration_ms": metrics.load_duration_ms,
            "prompt_eval_duration_ms": metrics.prompt_eval_duration_ms,
            "total_duration_ms": metrics.total_duration_ms,
            "memory_usage_mb": metrics.memory_usage_mb,
            "gpu_utilization_percent": metrics.gpu_utilization_percent,
            "model_size_gb": metrics.model_size_gb,
            "context_length": metrics.context_length,
            "temperature": metrics.temperature,
            "top_p": metrics.top_p,
            "error_occurred": metrics.error_occurred,
            "error_message": metrics.error_message
        }

    def _serialize_system_metrics(self, metrics: OllamaSystemMetrics) -> Dict[str, Any]:
        """Serialize OllamaSystemMetrics for JSON export."""
        return {
            "timestamp": metrics.timestamp.isoformat(),
            "cpu_usage_percent": metrics.cpu_usage_percent,
            "memory_usage_percent": metrics.memory_usage_percent,
            "memory_available_gb": metrics.memory_available_gb,
            "gpu_usage_percent": metrics.gpu_usage_percent,
            "gpu_memory_used_gb": metrics.gpu_memory_used_gb,
            "gpu_memory_total_gb": metrics.gpu_memory_total_gb,
            "disk_usage_percent": metrics.disk_usage_percent,
            "network_io_mbps": metrics.network_io_mbps,
            "active_connections": metrics.active_connections,
            "models_loaded": metrics.models_loaded,
            "total_models": metrics.total_models
        }

    def _serialize_alert(self, alert: OllamaPerformanceAlert) -> Dict[str, Any]:
        """Serialize OllamaPerformanceAlert for JSON export."""
        return {
            "timestamp": alert.timestamp.isoformat(),
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "message": alert.message,
            "model_name": alert.model_name,
            "metric_value": alert.metric_value,
            "threshold": alert.threshold,
            "recommendation": alert.recommendation
        }

    async def cleanup_old_metrics(self, days_to_keep: int = 30):
        """Clean up old metrics data to prevent storage bloat."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Clean up Ollama metrics
            original_count = len(self.ollama_metrics)
            self.ollama_metrics = deque(
                [m for m in self.ollama_metrics if m.timestamp > cutoff_date],
                maxlen=self.ollama_metrics.maxlen
            )
            cleaned_count = original_count - len(self.ollama_metrics)
            
            # Clean up system metrics
            original_system_count = len(self.system_metrics)
            self.system_metrics = deque(
                [m for m in self.system_metrics if m.timestamp > cutoff_date],
                maxlen=self.system_metrics.maxlen
            )
            cleaned_system_count = original_system_count - len(self.system_metrics)
            
            # Clean up old alerts
            original_alerts_count = len(self.performance_alerts)
            self.performance_alerts = deque(
                [a for a in self.performance_alerts if a.timestamp > cutoff_date],
                maxlen=self.performance_alerts.maxlen
            )
            cleaned_alerts_count = original_alerts_count - len(self.performance_alerts)
            
            logger.info(f"Cleaned up {cleaned_count} old Ollama metrics, {cleaned_system_count} system metrics, and {cleaned_alerts_count} alerts")
            
        except Exception as e:
            logger.error(f"Error cleaning up old metrics: {e}")

    async def start_ollama_monitoring(self, interval: float = 5.0):
        """Start continuous monitoring of Ollama performance."""
        if self.is_monitoring:
            logger.warning("Ollama monitoring is already running")
            return
        
        self.monitoring_interval = interval
        await super().start_monitoring()
        
        # Start additional Ollama-specific monitoring
        asyncio.create_task(self._ollama_monitoring_loop())

    async def _ollama_monitoring_loop(self):
        """Continuous loop for Ollama-specific monitoring."""
        while self.is_monitoring:
            try:
                await self.collect_system_metrics()
                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Error in Ollama monitoring loop: {e}")
                await asyncio.sleep(self.monitoring_interval)

# Global instance for easy access
ollama_performance_monitor = OllamaPerformanceMonitor()
