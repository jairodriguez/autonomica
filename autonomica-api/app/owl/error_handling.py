"""
Comprehensive Error Handling and Recovery System for OWL Orchestration

This module provides robust error handling, recovery mechanisms, and resilience 
features for the multi-agent system, ensuring stable operation even when individual
components fail.
"""

from __future__ import annotations

import asyncio
import logging
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import traceback
import uuid

logger = logging.getLogger(__name__)


class ErrorSeverity(str, Enum):
    """Classification of error severity levels."""
    LOW = "low"           # Minor issues that don't affect core functionality
    MEDIUM = "medium"     # Issues that may affect some functionality
    HIGH = "high"         # Critical issues that affect major functionality
    CRITICAL = "critical" # System-threatening issues requiring immediate action


class ErrorCategory(str, Enum):
    """Categories of errors that can occur in the system."""
    AGENT_FAILURE = "agent_failure"
    TASK_EXECUTION = "task_execution"
    COMMUNICATION = "communication"
    RESOURCE_ALLOCATION = "resource_allocation"
    WORKFLOW_ORCHESTRATION = "workflow_orchestration"
    EXTERNAL_SERVICE = "external_service"
    SYSTEM_RESOURCE = "system_resource"
    AUTHENTICATION = "authentication"
    DATA_CORRUPTION = "data_corruption"


class RecoveryStrategy(str, Enum):
    """Available recovery strategies for different error types."""
    RETRY = "retry"                    # Retry the failed operation
    FAILOVER = "failover"             # Switch to backup/alternative
    GRACEFUL_DEGRADATION = "degradation"  # Reduce functionality
    ROLLBACK = "rollback"             # Revert to previous state
    RESTART_COMPONENT = "restart"      # Restart the failing component
    ESCALATE = "escalate"             # Escalate to human intervention
    IGNORE = "ignore"                 # Continue despite the error


@dataclass
class ErrorEvent:
    """Represents a single error event in the system."""
    id: str = field(default_factory=lambda: f"err_{uuid.uuid4()}")
    category: ErrorCategory = ErrorCategory.SYSTEM_RESOURCE
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    message: str = ""
    component: str = ""  # Which component generated the error
    context: Dict[str, Any] = field(default_factory=dict)
    traceback: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    resolved: bool = False
    resolution_attempts: int = 0
    max_resolution_attempts: int = 3


@dataclass
class RecoveryAction:
    """Represents a recovery action that can be taken for an error."""
    strategy: RecoveryStrategy
    action: Callable
    description: str
    max_attempts: int = 3
    backoff_factor: float = 1.5  # Exponential backoff multiplier
    timeout: float = 30.0  # Timeout in seconds


class CircuitBreaker:
    """
    Circuit breaker pattern implementation to prevent cascading failures.
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "closed"  # closed, open, half-open
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute a function through the circuit breaker."""
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is open - service unavailable")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt a reset."""
        if self.last_failure_time is None:
            return True
        return (datetime.utcnow() - self.last_failure_time).total_seconds() > self.recovery_timeout
    
    def _on_success(self):
        """Handle successful operation."""
        self.failure_count = 0
        self.state = "closed"
    
    def _on_failure(self):
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


class ErrorRecoverySystem:
    """
    Advanced error handling and recovery system for the OWL orchestration platform.
    
    Features:
    - Automatic error detection and classification
    - Intelligent recovery strategy selection
    - Circuit breaker pattern for service protection
    - Error analytics and reporting
    - Graceful degradation capabilities
    """
    
    def __init__(self):
        self.error_history: List[ErrorEvent] = []
        self.recovery_strategies: Dict[ErrorCategory, List[RecoveryAction]] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.system_health_score: float = 1.0
        self.error_thresholds = {
            ErrorSeverity.LOW: 10,      # 10 low errors per hour trigger alert
            ErrorSeverity.MEDIUM: 5,    # 5 medium errors per hour
            ErrorSeverity.HIGH: 2,      # 2 high errors per hour
            ErrorSeverity.CRITICAL: 1   # 1 critical error triggers immediate response
        }
        
        # Initialize default recovery strategies
        self._setup_default_recovery_strategies()
        
        logger.info("Error Recovery System initialized")
    
    def _setup_default_recovery_strategies(self):
        """Set up default recovery strategies for different error categories."""
        
        # Agent failure recovery strategies
        self.recovery_strategies[ErrorCategory.AGENT_FAILURE] = [
            RecoveryAction(
                strategy=RecoveryStrategy.RESTART_COMPONENT,
                action=self._restart_agent,
                description="Restart the failed agent",
                max_attempts=2
            ),
            RecoveryAction(
                strategy=RecoveryStrategy.FAILOVER,
                action=self._failover_to_backup_agent,
                description="Switch to backup agent",
                max_attempts=1
            )
        ]
        
        # Task execution recovery strategies
        self.recovery_strategies[ErrorCategory.TASK_EXECUTION] = [
            RecoveryAction(
                strategy=RecoveryStrategy.RETRY,
                action=self._retry_task,
                description="Retry task with different parameters",
                max_attempts=3
            ),
            RecoveryAction(
                strategy=RecoveryStrategy.FAILOVER,
                action=self._assign_task_to_different_agent,
                description="Assign task to a different agent",
                max_attempts=2
            )
        ]
        
        # Communication error recovery
        self.recovery_strategies[ErrorCategory.COMMUNICATION] = [
            RecoveryAction(
                strategy=RecoveryStrategy.RETRY,
                action=self._retry_communication,
                description="Retry message delivery",
                max_attempts=3,
                backoff_factor=2.0
            )
        ]
        
        # Resource allocation recovery
        self.recovery_strategies[ErrorCategory.RESOURCE_ALLOCATION] = [
            RecoveryAction(
                strategy=RecoveryStrategy.GRACEFUL_DEGRADATION,
                action=self._reduce_resource_requirements,
                description="Reduce resource requirements",
                max_attempts=1
            ),
            RecoveryAction(
                strategy=RecoveryStrategy.FAILOVER,
                action=self._use_alternative_resources,
                description="Use alternative resource pool",
                max_attempts=1
            )
        ]
    
    async def handle_error(self, error: Exception, category: ErrorCategory, 
                          component: str, context: Dict[str, Any] = None) -> bool:
        """
        Handle an error with appropriate recovery strategy.
        
        Returns True if error was successfully recovered, False otherwise.
        """
        # Create error event
        error_event = ErrorEvent(
            category=category,
            severity=self._determine_severity(error, category),
            message=str(error),
            component=component,
            context=context or {},
            traceback=traceback.format_exc()
        )
        
        # Log the error
        self._log_error(error_event)
        
        # Add to error history
        self.error_history.append(error_event)
        
        # Update system health score
        self._update_system_health_score(error_event)
        
        # Check if we should trigger circuit breaker
        circuit_breaker = self._get_circuit_breaker(component)
        
        try:
            # Attempt recovery
            recovery_successful = await self._attempt_recovery(error_event)
            
            if recovery_successful:
                error_event.resolved = True
                logger.info(f"Successfully recovered from error {error_event.id}")
                return True
            else:
                logger.error(f"Failed to recover from error {error_event.id}")
                return False
                
        except Exception as recovery_error:
            logger.error(f"Recovery attempt failed: {str(recovery_error)}")
            return False
    
    def _determine_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Determine the severity of an error based on its type and category."""
        
        # Critical errors
        if isinstance(error, (SystemExit, KeyboardInterrupt)):
            return ErrorSeverity.CRITICAL
        
        if category == ErrorCategory.DATA_CORRUPTION:
            return ErrorSeverity.CRITICAL
        
        # High severity errors
        if category in [ErrorCategory.AGENT_FAILURE, ErrorCategory.WORKFLOW_ORCHESTRATION]:
            return ErrorSeverity.HIGH
        
        if isinstance(error, (ConnectionError, TimeoutError)):
            return ErrorSeverity.HIGH
        
        # Medium severity errors
        if category in [ErrorCategory.TASK_EXECUTION, ErrorCategory.RESOURCE_ALLOCATION]:
            return ErrorSeverity.MEDIUM
        
        # Default to low severity
        return ErrorSeverity.LOW
    
    def _log_error(self, error_event: ErrorEvent):
        """Log error event with appropriate level."""
        log_message = f"[{error_event.category.value}] {error_event.message} in {error_event.component}"
        
        if error_event.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif error_event.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif error_event.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def _update_system_health_score(self, error_event: ErrorEvent):
        """Update the overall system health score based on error severity."""
        severity_impact = {
            ErrorSeverity.LOW: 0.01,
            ErrorSeverity.MEDIUM: 0.05,
            ErrorSeverity.HIGH: 0.15,
            ErrorSeverity.CRITICAL: 0.5
        }
        
        impact = severity_impact.get(error_event.severity, 0.01)
        self.system_health_score = max(0.0, self.system_health_score - impact)
        
        # Slowly recover health score over time
        recovery_rate = 0.001  # 0.1% per error handled
        self.system_health_score = min(1.0, self.system_health_score + recovery_rate)
    
    def _get_circuit_breaker(self, component: str) -> CircuitBreaker:
        """Get or create a circuit breaker for a component."""
        if component not in self.circuit_breakers:
            self.circuit_breakers[component] = CircuitBreaker()
        return self.circuit_breakers[component]
    
    async def _attempt_recovery(self, error_event: ErrorEvent) -> bool:
        """Attempt to recover from an error using available strategies."""
        strategies = self.recovery_strategies.get(error_event.category, [])
        
        for strategy in strategies:
            if error_event.resolution_attempts >= strategy.max_attempts:
                continue
            
            try:
                logger.info(f"Attempting recovery: {strategy.description}")
                
                # Calculate backoff delay
                delay = strategy.backoff_factor ** error_event.resolution_attempts
                if delay > 1:
                    await asyncio.sleep(min(delay, 60))  # Cap at 60 seconds
                
                # Execute recovery action
                success = await self._execute_recovery_action(strategy, error_event)
                
                error_event.resolution_attempts += 1
                
                if success:
                    return True
                    
            except Exception as e:
                logger.error(f"Recovery strategy failed: {str(e)}")
                continue
        
        return False
    
    async def _execute_recovery_action(self, action: RecoveryAction, error_event: ErrorEvent) -> bool:
        """Execute a specific recovery action."""
        try:
            # Set timeout for recovery action
            result = await asyncio.wait_for(
                action.action(error_event),
                timeout=action.timeout
            )
            return bool(result)
        except asyncio.TimeoutError:
            logger.error(f"Recovery action timed out: {action.description}")
            return False
        except Exception as e:
            logger.error(f"Recovery action failed: {action.description} - {str(e)}")
            return False
    
    # Recovery action implementations
    async def _restart_agent(self, error_event: ErrorEvent) -> bool:
        """Restart a failed agent."""
        component = error_event.component
        logger.info(f"Restarting agent: {component}")
        
        # Implementation would restart the specific agent
        # This is a placeholder for the actual restart logic
        return True
    
    async def _failover_to_backup_agent(self, error_event: ErrorEvent) -> bool:
        """Failover to a backup agent."""
        logger.info("Failing over to backup agent")
        
        # Implementation would switch to backup agent
        return True
    
    async def _retry_task(self, error_event: ErrorEvent) -> bool:
        """Retry a failed task."""
        logger.info("Retrying failed task")
        
        # Implementation would retry the task
        return True
    
    async def _assign_task_to_different_agent(self, error_event: ErrorEvent) -> bool:
        """Assign task to a different agent."""
        logger.info("Reassigning task to different agent")
        
        # Implementation would reassign the task
        return True
    
    async def _retry_communication(self, error_event: ErrorEvent) -> bool:
        """Retry failed communication."""
        logger.info("Retrying communication")
        
        # Implementation would retry message delivery
        return True
    
    async def _reduce_resource_requirements(self, error_event: ErrorEvent) -> bool:
        """Reduce resource requirements for graceful degradation."""
        logger.info("Reducing resource requirements")
        
        # Implementation would reduce resource usage
        return True
    
    async def _use_alternative_resources(self, error_event: ErrorEvent) -> bool:
        """Use alternative resource pools."""
        logger.info("Switching to alternative resources")
        
        # Implementation would switch resource pools
        return True
    
    def get_system_health_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system health and error metrics."""
        recent_errors = [
            e for e in self.error_history
            if (datetime.utcnow() - e.timestamp).total_seconds() < 3600  # Last hour
        ]
        
        error_count_by_severity = {}
        error_count_by_category = {}
        
        for error in recent_errors:
            severity = error.severity.value
            category = error.category.value
            
            error_count_by_severity[severity] = error_count_by_severity.get(severity, 0) + 1
            error_count_by_category[category] = error_count_by_category.get(category, 0) + 1
        
        resolved_errors = len([e for e in recent_errors if e.resolved])
        total_recent_errors = len(recent_errors)
        
        return {
            "system_health_score": round(self.system_health_score, 3),
            "total_errors_last_hour": total_recent_errors,
            "resolved_errors_last_hour": resolved_errors,
            "resolution_rate": resolved_errors / total_recent_errors if total_recent_errors > 0 else 1.0,
            "errors_by_severity": error_count_by_severity,
            "errors_by_category": error_count_by_category,
            "active_circuit_breakers": len([cb for cb in self.circuit_breakers.values() if cb.state == "open"]),
            "system_status": self._get_system_status()
        }
    
    def _get_system_status(self) -> str:
        """Determine overall system status based on health score."""
        if self.system_health_score >= 0.9:
            return "healthy"
        elif self.system_health_score >= 0.7:
            return "degraded"
        elif self.system_health_score >= 0.5:
            return "warning"
        else:
            return "critical"
    
    def check_error_thresholds(self) -> List[str]:
        """Check if error thresholds have been exceeded."""
        alerts = []
        recent_errors = [
            e for e in self.error_history
            if (datetime.utcnow() - e.timestamp).total_seconds() < 3600
        ]
        
        severity_counts = {}
        for error in recent_errors:
            severity = error.severity
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        for severity, threshold in self.error_thresholds.items():
            count = severity_counts.get(severity, 0)
            if count > threshold:
                alerts.append(f"Threshold exceeded: {count} {severity.value} errors (threshold: {threshold})")
        
        return alerts
    
    def clear_old_errors(self, hours: int = 24):
        """Clear error history older than specified hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        self.error_history = [
            e for e in self.error_history
            if e.timestamp > cutoff_time
        ]
        logger.info(f"Cleared error history older than {hours} hours")