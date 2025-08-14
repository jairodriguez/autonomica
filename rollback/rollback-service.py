#!/usr/bin/env python3
"""
Automated Rollback Service for Production Deployments
This service monitors deployments and automatically rolls back failed deployments
"""

import os
import sys
import time
import json
import logging
import yaml
import requests
import docker
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import queue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/rollback/rollback-service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RollbackStatus(Enum):
    """Rollback status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class RollbackTrigger(Enum):
    """Rollback trigger types"""
    HIGH_ERROR_RATE = "high_error_rate"
    SERVICE_UNAVAILABLE = "service_unavailable"
    HIGH_RESPONSE_TIME = "high_response_time"
    HIGH_CPU_USAGE = "high_cpu_usage"
    HIGH_MEMORY_USAGE = "high_memory_usage"
    DATABASE_ISSUES = "database_connection_issues"
    BUSINESS_METRICS = "business_metrics"

@dataclass
class RollbackEvent:
    """Rollback event data structure"""
    id: str
    deployment_id: str
    trigger: RollbackTrigger
    severity: str
    timestamp: datetime
    status: RollbackStatus
    metrics: Dict[str, Any]
    actions_taken: List[str]
    duration: Optional[float] = None
    error_message: Optional[str] = None

@dataclass
class HealthMetrics:
    """Health metrics data structure"""
    error_rate: float
    response_time_p95: float
    cpu_usage: float
    memory_usage: float
    database_connections: int
    service_status: str
    timestamp: datetime

class RollbackService:
    """Main rollback service class"""
    
    def __init__(self, config_path: str = "rollback-config.yml"):
        self.config_path = config_path
        self.config = self.load_config()
        self.docker_client = docker.from_env()
        self.rollback_queue = queue.Queue()
        self.active_rollbacks = {}
        self.rollback_history = []
        self.monitoring_thread = None
        self.running = False
        
        # Initialize components
        self.health_checker = HealthChecker(self.config)
        self.rollback_executor = RollbackExecutor(self.config, self.docker_client)
        self.notification_service = NotificationService(self.config)
        self.metrics_collector = MetricsCollector(self.config)
        
        logger.info("Rollback service initialized successfully")
    
    def load_config(self) -> Dict[str, Any]:
        """Load rollback configuration from file"""
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
            logger.info(f"Configuration loaded from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            sys.exit(1)
    
    def start(self):
        """Start the rollback service"""
        if self.running:
            logger.warning("Service is already running")
            return
        
        self.running = True
        logger.info("Starting rollback service...")
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        # Start rollback processing thread
        self.rollback_thread = threading.Thread(target=self._rollback_processing_loop)
        self.rollback_thread.daemon = True
        self.rollback_thread.start()
        
        logger.info("Rollback service started successfully")
    
    def stop(self):
        """Stop the rollback service"""
        self.running = False
        logger.info("Stopping rollback service...")
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)
        
        if self.rollback_thread:
            self.rollback_thread.join(timeout=10)
        
        logger.info("Rollback service stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Check health of all services
                self._check_services_health()
                
                # Check for rollback triggers
                self._check_rollback_triggers()
                
                # Sleep for configured interval
                time.sleep(self.config['rollback']['health_check']['health_check_interval'])
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(30)  # Wait before retrying
    
    def _check_services_health(self):
        """Check health of all monitored services"""
        try:
            # Get health metrics from all services
            health_metrics = self.health_checker.get_all_health_metrics()
            
            # Store metrics for analysis
            self.metrics_collector.store_metrics(health_metrics)
            
            # Check for any immediate issues
            for service, metrics in health_metrics.items():
                if self._should_trigger_rollback(service, metrics):
                    self._queue_rollback(service, metrics)
                    
        except Exception as e:
            logger.error(f"Error checking services health: {e}")
    
    def _should_trigger_rollback(self, service: str, metrics: HealthMetrics) -> bool:
        """Determine if rollback should be triggered"""
        try:
            triggers = self.config['rollback']['triggers']
            
            # Check application triggers
            for trigger in triggers['application']:
                if self._evaluate_trigger_condition(trigger, metrics):
                    logger.warning(f"Rollback trigger '{trigger['name']}' activated for {service}")
                    return True
            
            # Check infrastructure triggers
            for trigger in triggers['infrastructure']:
                if self._evaluate_trigger_condition(trigger, metrics):
                    logger.warning(f"Rollback trigger '{trigger['name']}' activated for {service}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating rollback triggers: {e}")
            return False
    
    def _evaluate_trigger_condition(self, trigger: Dict[str, Any], metrics: HealthMetrics) -> bool:
        """Evaluate a single trigger condition"""
        try:
            condition = trigger['condition']
            
            # Simple condition evaluation (can be extended with more complex logic)
            if 'error_rate' in condition:
                threshold = float(condition.split('>')[1].strip())
                return metrics.error_rate > threshold
            
            elif 'response_time' in condition:
                threshold = float(condition.split('>')[1].strip())
                return metrics.response_time_p95 > threshold
            
            elif 'cpu_usage' in condition:
                threshold = float(condition.split('>')[1].strip())
                return metrics.cpu_usage > threshold
            
            elif 'memory_usage' in condition:
                threshold = float(condition.split('>')[1].strip())
                return metrics.memory_usage > threshold
            
            elif 'service_status' in condition:
                expected_status = condition.split('==')[1].strip().strip("'")
                return metrics.service_status == expected_status
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating trigger condition '{trigger['name']}': {e}")
            return False
    
    def _queue_rollback(self, service: str, metrics: HealthMetrics):
        """Queue a rollback for processing"""
        try:
            # Create rollback event
            rollback_event = RollbackEvent(
                id=f"rollback_{int(time.time())}",
                deployment_id=self._get_current_deployment_id(service),
                trigger=self._determine_trigger(metrics),
                severity=self._determine_severity(metrics),
                timestamp=datetime.now(),
                status=RollbackStatus.PENDING,
                metrics=asdict(metrics),
                actions_taken=[]
            )
            
            # Add to queue
            self.rollback_queue.put(rollback_event)
            logger.info(f"Rollback queued for {service}: {rollback_event.id}")
            
        except Exception as e:
            logger.error(f"Error queuing rollback: {e}")
    
    def _get_current_deployment_id(self, service: str) -> str:
        """Get current deployment ID for a service"""
        try:
            # This would typically query your deployment tracking system
            # For now, we'll use a timestamp-based ID
            return f"{service}_deployment_{int(time.time())}"
        except Exception as e:
            logger.error(f"Error getting deployment ID: {e}")
            return "unknown"
    
    def _determine_trigger(self, metrics: HealthMetrics) -> RollbackTrigger:
        """Determine which trigger caused the rollback"""
        if metrics.error_rate > 0.05:
            return RollbackTrigger.HIGH_ERROR_RATE
        elif metrics.service_status == 'down':
            return RollbackTrigger.SERVICE_UNAVAILABLE
        elif metrics.response_time_p95 > 2000:
            return RollbackTrigger.HIGH_RESPONSE_TIME
        elif metrics.cpu_usage > 0.9:
            return RollbackTrigger.HIGH_CPU_USAGE
        elif metrics.memory_usage > 0.95:
            return RollbackTrigger.HIGH_MEMORY_USAGE
        else:
            return RollbackTrigger.BUSINESS_METRICS
    
    def _determine_severity(self, metrics: HealthMetrics) -> str:
        """Determine severity level based on metrics"""
        if metrics.error_rate > 0.1 or metrics.service_status == 'down':
            return 'critical'
        elif metrics.error_rate > 0.05 or metrics.response_time_p95 > 5000:
            return 'warning'
        else:
            return 'info'
    
    def _rollback_processing_loop(self):
        """Process rollback queue"""
        while self.running:
            try:
                # Get rollback event from queue
                try:
                    rollback_event = self.rollback_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                # Process rollback
                self._process_rollback(rollback_event)
                
            except Exception as e:
                logger.error(f"Error in rollback processing loop: {e}")
                time.sleep(5)
    
    def _process_rollback(self, rollback_event: RollbackEvent):
        """Process a single rollback event"""
        try:
            logger.info(f"Processing rollback {rollback_event.id}")
            
            # Update status
            rollback_event.status = RollbackStatus.IN_PROGRESS
            self.active_rollbacks[rollback_event.id] = rollback_event
            
            # Execute pre-rollback actions
            self._execute_pre_rollback_actions(rollback_event)
            
            # Execute rollback
            start_time = time.time()
            success = self.rollback_executor.execute_rollback(rollback_event)
            rollback_event.duration = time.time() - start_time
            
            # Update status
            if success:
                rollback_event.status = RollbackStatus.COMPLETED
                logger.info(f"Rollback {rollback_event.id} completed successfully")
            else:
                rollback_event.status = RollbackStatus.FAILED
                logger.error(f"Rollback {rollback_event.id} failed")
            
            # Execute post-rollback actions
            self._execute_post_rollback_actions(rollback_event)
            
            # Move to history
            self.rollback_history.append(rollback_event)
            if rollback_event.id in self.active_rollbacks:
                del self.active_rollbacks[rollback_event.id]
            
        except Exception as e:
            logger.error(f"Error processing rollback {rollback_event.id}: {e}")
            rollback_event.status = RollbackStatus.FAILED
            rollback_event.error_message = str(e)
    
    def _execute_pre_rollback_actions(self, rollback_event: RollbackEvent):
        """Execute pre-rollback actions"""
        try:
            actions = self.config['rollback']['actions']['pre_rollback']
            
            for action in actions:
                if action['name'] == 'notify_team':
                    self.notification_service.notify_team(rollback_event, action)
                elif action['name'] == 'capture_metrics':
                    self.metrics_collector.capture_metrics(rollback_event, action)
                elif action['name'] == 'create_incident':
                    self._create_incident(rollback_event, action)
                    
        except Exception as e:
            logger.error(f"Error executing pre-rollback actions: {e}")
    
    def _execute_post_rollback_actions(self, rollback_event: RollbackEvent):
        """Execute post-rollback actions"""
        try:
            actions = self.config['rollback']['actions']['post_rollback']
            
            for action in actions:
                if action['name'] == 'notify_completion':
                    self.notification_service.notify_completion(rollback_event, action)
                elif action['name'] == 'update_deployment_status':
                    self._update_deployment_status(rollback_event, action)
                elif action['name'] == 'create_post_mortem':
                    self._create_post_mortem(rollback_event, action)
                    
        except Exception as e:
            logger.error(f"Error executing post-rollback actions: {e}")
    
    def _create_incident(self, rollback_event: RollbackEvent, action: Dict[str, Any]):
        """Create incident for rollback"""
        try:
            # This would integrate with your incident management system
            incident_data = {
                'title': f'Rollback Incident: {rollback_event.trigger.value}',
                'description': f'Automated rollback triggered for deployment {rollback_event.deployment_id}',
                'priority': action.get('priority', 'high'),
                'rollback_id': rollback_event.id,
                'deployment_id': rollback_event.deployment_id,
                'trigger': rollback_event.trigger.value,
                'severity': rollback_event.severity
            }
            
            logger.info(f"Incident created: {incident_data['title']}")
            
        except Exception as e:
            logger.error(f"Error creating incident: {e}")
    
    def _update_deployment_status(self, rollback_event: RollbackEvent, action: Dict[str, Any]):
        """Update deployment status"""
        try:
            # This would update your deployment tracking system
            status = action.get('status', 'rolled_back')
            logger.info(f"Deployment {rollback_event.deployment_id} status updated to: {status}")
            
        except Exception as e:
            logger.error(f"Error updating deployment status: {e}")
    
    def _create_post_mortem(self, rollback_event: RollbackEvent, action: Dict[str, Any]):
        """Create post-mortem document"""
        try:
            template = action.get('template', 'rollback_post_mortem.md')
            
            post_mortem_data = {
                'rollback_id': rollback_event.id,
                'deployment_id': rollback_event.deployment_id,
                'trigger': rollback_event.trigger.value,
                'severity': rollback_event.severity,
                'timestamp': rollback_event.timestamp.isoformat(),
                'duration': rollback_event.duration,
                'metrics': rollback_event.metrics,
                'actions_taken': rollback_event.actions_taken,
                'error_message': rollback_event.error_message
            }
            
            # This would create a post-mortem document using the template
            logger.info(f"Post-mortem created for rollback {rollback_event.id}")
            
        except Exception as e:
            logger.error(f"Error creating post-mortem: {e}")
    
    def get_rollback_status(self, rollback_id: str) -> Optional[RollbackEvent]:
        """Get status of a specific rollback"""
        # Check active rollbacks
        if rollback_id in self.active_rollbacks:
            return self.active_rollbacks[rollback_id]
        
        # Check history
        for rollback in self.rollback_history:
            if rollback.id == rollback_id:
                return rollback
        
        return None
    
    def get_rollback_history(self, limit: int = 100) -> List[RollbackEvent]:
        """Get rollback history"""
        return self.rollback_history[-limit:]
    
    def cancel_rollback(self, rollback_id: str) -> bool:
        """Cancel an active rollback"""
        if rollback_id in self.active_rollbacks:
            rollback_event = self.active_rollbacks[rollback_id]
            rollback_event.status = RollbackStatus.CANCELLED
            logger.info(f"Rollback {rollback_id} cancelled")
            return True
        return False

def main():
    """Main function to run the rollback service"""
    try:
        # Create rollback service
        service = RollbackService()
        
        # Start service
        service.start()
        
        # Keep main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        
        # Stop service
        service.stop()
        
    except Exception as e:
        logger.error(f"Fatal error in rollback service: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()