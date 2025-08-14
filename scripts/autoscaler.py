#!/usr/bin/env python3
"""
Autonomica Production Auto-scaling Service
Monitors production services and automatically scales them based on resource usage
"""

import os
import time
import json
import logging
import subprocess
import docker
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/autoscaler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ScalingConfig:
    """Configuration for auto-scaling"""
    min_instances: int = 2
    max_instances: int = 10
    cpu_threshold: float = 70.0
    memory_threshold: float = 80.0
    scale_up_cooldown: int = 300  # 5 minutes
    scale_down_cooldown: int = 600  # 10 minutes
    check_interval: int = 30  # 30 seconds

@dataclass
class ServiceMetrics:
    """Service performance metrics"""
    service_name: str
    cpu_percent: float
    memory_percent: float
    current_replicas: int
    target_replicas: int
    last_scale_time: Optional[datetime] = None

class ProductionAutoScaler:
    """Production environment auto-scaler"""
    
    def __init__(self):
        self.config = ScalingConfig(
            min_instances=int(os.getenv('MIN_INSTANCES', 2)),
            max_instances=int(os.getenv('MAX_INSTANCES', 10)),
            cpu_threshold=float(os.getenv('SCALE_CPU_THRESHOLD', 70.0)),
            memory_threshold=float(os.getenv('SCALE_MEMORY_THRESHOLD', 80.0))
        )
        
        self.docker_client = docker.from_env()
        self.scaling_history: Dict[str, datetime] = {}
        self.metrics_history: List[ServiceMetrics] = []
        
        # Services to monitor
        self.monitored_services = [
            'api-production',
            'frontend-production',
            'worker-production'
        ]
        
        logger.info(f"Auto-scaler initialized with config: {self.config}")
    
    def run(self):
        """Main run loop"""
        logger.info("Starting production auto-scaler...")
        
        try:
            while True:
                self.check_and_scale_services()
                time.sleep(self.config.check_interval)
        except KeyboardInterrupt:
            logger.info("Auto-scaler stopped by user")
        except Exception as e:
            logger.error(f"Auto-scaler error: {e}")
            raise
    
    def check_and_scale_services(self):
        """Check all services and scale if needed"""
        logger.debug("Checking services for scaling...")
        
        for service_name in self.monitored_services:
            try:
                metrics = self.get_service_metrics(service_name)
                if metrics:
                    self.metrics_history.append(metrics)
                    self.evaluate_scaling(metrics)
            except Exception as e:
                logger.error(f"Error checking service {service_name}: {e}")
        
        # Clean up old metrics (keep last 100)
        if len(self.metrics_history) > 100:
            self.metrics_history = self.metrics_history[-100:]
    
    def get_service_metrics(self, service_name: str) -> Optional[ServiceMetrics]:
        """Get current metrics for a service"""
        try:
            # Get service info
            service = self.docker_client.services.get(service_name)
            service_tasks = service.tasks()
            
            if not service_tasks:
                logger.warning(f"No tasks found for service {service_name}")
                return None
            
            # Calculate aggregate metrics
            total_cpu = 0.0
            total_memory = 0.0
            running_tasks = 0
            
            for task in service_tasks:
                if task['Status']['State'] == 'running':
                    running_tasks += 1
                    # Get container stats
                    try:
                        container = self.docker_client.containers.get(task['Status']['ContainerStatus']['ContainerID'])
                        stats = container.stats(stream=False)
                        
                        # Calculate CPU percentage
                        cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
                        system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
                        
                        if system_delta > 0:
                            cpu_percent = (cpu_delta / system_delta) * 100.0
                        else:
                            cpu_percent = 0.0
                        
                        # Calculate memory percentage
                        memory_usage = stats['memory_stats']['usage']
                        memory_limit = stats['memory_stats']['limit']
                        
                        if memory_limit > 0:
                            memory_percent = (memory_usage / memory_limit) * 100.0
                        else:
                            memory_percent = 0.0
                        
                        total_cpu += cpu_percent
                        total_memory += memory_percent
                        
                    except Exception as e:
                        logger.debug(f"Could not get stats for container {task['Status']['ContainerStatus']['ContainerID']}: {e}")
            
            if running_tasks == 0:
                return None
            
            avg_cpu = total_cpu / running_tasks
            avg_memory = total_memory / running_tasks
            
            # Get current replicas
            current_replicas = service.attrs['Spec']['Mode']['Replicated']['Replicas']
            
            # Get target replicas (same as current for now)
            target_replicas = current_replicas
            
            # Get last scale time
            last_scale_time = self.scaling_history.get(service_name)
            
            metrics = ServiceMetrics(
                service_name=service_name,
                cpu_percent=avg_cpu,
                memory_percent=avg_memory,
                current_replicas=current_replicas,
                target_replicas=target_replicas,
                last_scale_time=last_scale_time
            )
            
            logger.debug(f"Service {service_name} metrics: CPU={avg_cpu:.1f}%, Memory={avg_memory:.1f}%, Replicas={current_replicas}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting metrics for service {service_name}: {e}")
            return None
    
    def evaluate_scaling(self, metrics: ServiceMetrics):
        """Evaluate if scaling is needed for a service"""
        service_name = metrics.service_name
        
        # Check cooldown periods
        if not self.can_scale(service_name):
            return
        
        # Determine scaling action
        scaling_action = self.determine_scaling_action(metrics)
        
        if scaling_action:
            self.execute_scaling(service_name, scaling_action, metrics)
    
    def can_scale(self, service_name: str) -> bool:
        """Check if service can be scaled (cooldown period)"""
        last_scale = self.scaling_history.get(service_name)
        
        if not last_scale:
            return True
        
        cooldown = self.config.scale_up_cooldown if last_scale else self.config.scale_down_cooldown
        time_since_scale = datetime.now() - last_scale
        
        return time_since_scale.total_seconds() > cooldown
    
    def determine_scaling_action(self, metrics: ServiceMetrics) -> Optional[str]:
        """Determine if scaling up or down is needed"""
        # Check if scaling up is needed
        if (metrics.cpu_percent > self.config.cpu_threshold or 
            metrics.memory_percent > self.config.memory_threshold):
            
            if metrics.current_replicas < self.config.max_instances:
                return 'scale_up'
        
        # Check if scaling down is needed
        elif (metrics.cpu_percent < self.config.cpu_threshold * 0.5 and 
              metrics.memory_percent < self.config.memory_threshold * 0.5):
            
            if metrics.current_replicas > self.config.min_instances:
                return 'scale_down'
        
        return None
    
    def execute_scaling(self, service_name: str, action: str, metrics: ServiceMetrics):
        """Execute scaling action"""
        try:
            current_replicas = metrics.current_replicas
            
            if action == 'scale_up':
                new_replicas = min(current_replicas + 1, self.config.max_instances)
                logger.info(f"Scaling up {service_name} from {current_replicas} to {new_replicas} replicas")
            else:  # scale_down
                new_replicas = max(current_replicas - 1, self.config.min_instances)
                logger.info(f"Scaling down {service_name} from {current_replicas} to {new_replicas} replicas")
            
            # Execute scaling using Docker Swarm
            self.scale_service(service_name, new_replicas)
            
            # Update scaling history
            self.scaling_history[service_name] = datetime.now()
            
            # Log scaling action
            self.log_scaling_action(service_name, action, current_replicas, new_replicas, metrics)
            
        except Exception as e:
            logger.error(f"Error executing scaling for {service_name}: {e}")
    
    def scale_service(self, service_name: str, replicas: int):
        """Scale a service using Docker Swarm"""
        try:
            # Use docker service scale command
            cmd = ['docker', 'service', 'scale', f'{service_name}={replicas}']
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully scaled {service_name} to {replicas} replicas")
            else:
                logger.error(f"Failed to scale {service_name}: {result.stderr}")
                raise Exception(f"Scaling failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout scaling {service_name}")
            raise Exception("Scaling timeout")
        except Exception as e:
            logger.error(f"Error scaling {service_name}: {e}")
            raise
    
    def log_scaling_action(self, service_name: str, action: str, old_replicas: int, new_replicas: int, metrics: ServiceMetrics):
        """Log scaling action with metrics"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'service': service_name,
            'action': action,
            'old_replicas': old_replicas,
            'new_replicas': new_replicas,
            'cpu_percent': metrics.cpu_percent,
            'memory_percent': metrics.memory_percent,
            'reason': f"CPU: {metrics.cpu_percent:.1f}%, Memory: {metrics.memory_percent:.1f}%"
        }
        
        logger.info(f"Scaling action logged: {json.dumps(log_entry)}")
        
        # Save to file for monitoring
        log_file = f"/var/log/autoscaler-{service_name}.log"
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.warning(f"Could not write to log file {log_file}: {e}")
    
    def get_scaling_summary(self) -> Dict:
        """Get summary of current scaling state"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'config': {
                'min_instances': self.config.min_instances,
                'max_instances': self.config.max_instances,
                'cpu_threshold': self.config.cpu_threshold,
                'memory_threshold': self.config.memory_threshold
            },
            'services': {},
            'scaling_history': {}
        }
        
        # Get current service states
        for service_name in self.monitored_services:
            try:
                service = self.docker_client.services.get(service_name)
                current_replicas = service.attrs['Spec']['Mode']['Replicated']['Replicas']
                
                summary['services'][service_name] = {
                    'current_replicas': current_replicas,
                    'last_scale': self.scaling_history.get(service_name, {}).isoformat() if self.scaling_history.get(service_name) else None
                }
            except Exception as e:
                summary['services'][service_name] = {
                    'error': str(e)
                }
        
        # Add scaling history
        for service_name, last_scale in self.scaling_history.items():
            summary['scaling_history'][service_name] = last_scale.isoformat()
        
        return summary
    
    def health_check(self) -> bool:
        """Health check for the auto-scaler"""
        try:
            # Check if Docker client is working
            self.docker_client.ping()
            
            # Check if we can access services
            for service_name in self.monitored_services:
                try:
                    self.docker_client.services.get(service_name)
                except Exception:
                    logger.warning(f"Could not access service {service_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

def main():
    """Main function"""
    try:
        # Initialize auto-scaler
        autoscaler = ProductionAutoScaler()
        
        # Run health check
        if not autoscaler.health_check():
            logger.error("Auto-scaler health check failed")
            exit(1)
        
        # Start auto-scaler
        autoscaler.run()
        
    except Exception as e:
        logger.error(f"Auto-scaler failed to start: {e}")
        exit(1)

if __name__ == "__main__":
    main()