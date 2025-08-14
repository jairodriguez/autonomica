#!/usr/bin/env python3
"""
Notification Service Component for Rollback Service
Handles notifications for rollback events
"""

import time
import logging
import requests
import smtplib
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

class NotificationService:
    """Handles notifications for rollback events"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.notification_config = config['rollback']['notifications']
        self.slack_webhook_url = self.notification_config['slack']['webhook_url']
        self.email_config = self.notification_config['email']
        self.webhook_config = self.notification_config['webhook']
        
        logger.info("Notification service initialized")
    
    def notify_team(self, rollback_event: 'RollbackEvent', action: Dict[str, Any]) -> bool:
        """Notify team about rollback initiation"""
        try:
            logger.info(f"Notifying team about rollback {rollback_event.id}")
            
            # Prepare notification message
            message = self._prepare_rollback_notification_message(rollback_event, action)
            
            # Send notifications to all configured channels
            success = True
            
            # Send Slack notification
            if 'slack' in action.get('channels', []):
                if not self._send_slack_notification(message, action):
                    success = False
            
            # Send email notification
            if 'email' in action.get('channels', []):
                if not self._send_email_notification(message, action):
                    success = False
            
            # Send webhook notification
            if 'webhook' in action.get('channels', []):
                if not self._send_webhook_notification(message, action):
                    success = False
            
            if success:
                logger.info(f"Team notification sent successfully for rollback {rollback_event.id}")
            else:
                logger.warning(f"Some team notifications failed for rollback {rollback_event.id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error notifying team about rollback: {e}")
            return False
    
    def notify_completion(self, rollback_event: 'RollbackEvent', action: Dict[str, Any]) -> bool:
        """Notify team about rollback completion"""
        try:
            logger.info(f"Notifying team about rollback completion {rollback_event.id}")
            
            # Prepare completion message
            message = self._prepare_completion_notification_message(rollback_event, action)
            
            # Send notifications to all configured channels
            success = True
            
            # Send Slack notification
            if 'slack' in action.get('channels', []):
                if not self._send_slack_notification(message, action):
                    success = False
            
            # Send email notification
            if 'email' in action.get('channels', []):
                if not self._send_email_notification(message, action):
                    success = False
            
            # Send webhook notification
            if 'webhook' in action.get('channels', []):
                if not self._send_webhook_notification(message, action):
                    success = False
            
            if success:
                logger.info(f"Completion notification sent successfully for rollback {rollback_event.id}")
            else:
                logger.warning(f"Some completion notifications failed for rollback {rollback_event.id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error notifying team about rollback completion: {e}")
            return False
    
    def _prepare_rollback_notification_message(self, rollback_event: 'RollbackEvent', action: Dict[str, Any]) -> str:
        """Prepare notification message for rollback initiation"""
        try:
            # Get the message template from action
            message_template = action.get('message', 'Rollback initiated for deployment {deployment_id}')
            
            # Replace placeholders with actual values
            message = message_template.format(
                deployment_id=rollback_event.deployment_id,
                rollback_id=rollback_event.id,
                trigger=rollback_event.trigger.value,
                severity=rollback_event.severity,
                timestamp=rollback_event.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')
            )
            
            # Add additional context
            context = f"""
Rollback Details:
- Rollback ID: {rollback_event.id}
- Deployment ID: {rollback_event.deployment_id}
- Trigger: {rollback_event.trigger.value}
- Severity: {rollback_event.severity}
- Timestamp: {rollback_event.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}
- Status: {rollback_event.status.value}

Metrics at time of rollback:
- Error Rate: {rollback_event.metrics.get('error_rate', 'N/A'):.2%}
- Response Time (P95): {rollback_event.metrics.get('response_time_p95', 'N/A'):.0f}ms
- CPU Usage: {rollback_event.metrics.get('cpu_usage', 'N/A'):.1%}
- Memory Usage: {rollback_event.metrics.get('memory_usage', 'N/A'):.1%}
- Service Status: {rollback_event.metrics.get('service_status', 'N/A')}

The rollback system is now processing this request. You will receive another notification when the rollback is complete.
"""
            
            return message + context
            
        except Exception as e:
            logger.error(f"Error preparing rollback notification message: {e}")
            return f"Rollback initiated for deployment {rollback_event.deployment_id}"
    
    def _prepare_completion_notification_message(self, rollback_event: 'RollbackEvent', action: Dict[str, Any]) -> str:
        """Prepare notification message for rollback completion"""
        try:
            # Get the message template from action
            message_template = action.get('message', 'Rollback completed for deployment {deployment_id}')
            
            # Replace placeholders with actual values
            message = message_template.format(
                deployment_id=rollback_event.deployment_id,
                rollback_id=rollback_event.id,
                trigger=rollback_event.trigger.value,
                severity=rollback_event.severity,
                timestamp=rollback_event.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')
            )
            
            # Add completion context
            status_text = "SUCCESSFULLY" if rollback_event.status.value == 'completed' else "FAILED"
            duration_text = f" in {rollback_event.duration:.2f} seconds" if rollback_event.duration else ""
            
            context = f"""
Rollback {status_text} COMPLETED{duration_text}

Final Details:
- Rollback ID: {rollback_event.id}
- Deployment ID: {rollback_event.deployment_id}
- Final Status: {rollback_event.status.value}
- Duration: {rollback_event.duration:.2f}s if rollback_event.duration else 'N/A'
- Actions Taken: {', '.join(rollback_event.actions_taken) if rollback_event.actions_taken else 'None'}

"""
            
            if rollback_event.error_message:
                context += f"Error: {rollback_event.error_message}\n"
            
            if rollback_event.status.value == 'completed':
                context += "\nThe system has been successfully rolled back to the previous stable version. All services should now be operating normally."
            else:
                context += "\nThe rollback failed. Manual intervention may be required. Please check the logs for more details."
            
            return message + context
            
        except Exception as e:
            logger.error(f"Error preparing completion notification message: {e}")
            return f"Rollback completed for deployment {rollback_event.deployment_id}"
    
    def _send_slack_notification(self, message: str, action: Dict[str, Any]) -> bool:
        """Send notification to Slack"""
        try:
            if not self.slack_webhook_url:
                logger.warning("Slack webhook URL not configured")
                return False
            
            # Prepare Slack message
            slack_message = {
                "text": message,
                "channel": action.get('channel', '#deployments'),
                "username": "Autonomica Rollback Bot",
                "icon_emoji": ":warning:" if "critical" in message.lower() else ":information_source:"
            }
            
            # Send to Slack
            response = requests.post(
                self.slack_webhook_url,
                json=slack_message,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Slack notification sent successfully")
                return True
            else:
                logger.error(f"Failed to send Slack notification: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
            return False
    
    def _send_email_notification(self, message: str, action: Dict[str, Any]) -> bool:
        """Send notification via email"""
        try:
            # Get email configuration
            smtp_host = self.email_config['smtp_config']['host']
            smtp_port = self.email_config['smtp_config']['port']
            smtp_username = self.email_config['smtp_config']['username']
            smtp_password = self.email_config['smtp_config']['password']
            
            # Prepare email
            msg = MIMEMultipart()
            msg['From'] = smtp_username
            msg['To'] = ', '.join(self.email_config['recipients'])
            msg['Subject'] = f"Rollback Notification - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Add message body
            msg.attach(MIMEText(message, 'plain'))
            
            # Send email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            logger.info("Email notification sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            return False
    
    def _send_webhook_notification(self, message: str, action: Dict[str, Any]) -> bool:
        """Send notification via webhook"""
        try:
            # Get webhook configuration
            webhook_url = self.webhook_config['endpoints'][0]['url']
            headers = self.webhook_config['endpoints'][0].get('headers', {})
            
            # Prepare webhook payload
            payload = {
                'message': message,
                'timestamp': datetime.now().isoformat(),
                'type': 'rollback_notification',
                'action': action.get('name', 'unknown')
            }
            
            # Send webhook
            response = requests.post(
                webhook_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201, 202]:
                logger.info("Webhook notification sent successfully")
                return True
            else:
                logger.error(f"Failed to send webhook notification: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending webhook notification: {e}")
            return False
    
    def send_urgent_notification(self, rollback_event: 'RollbackEvent', urgency: str = 'high') -> bool:
        """Send urgent notification for critical rollbacks"""
        try:
            logger.info(f"Sending urgent notification for rollback {rollback_event.id}")
            
            # Prepare urgent message
            urgent_message = f"""
🚨 URGENT ROLLBACK ALERT 🚨

A critical rollback has been triggered and requires immediate attention.

Rollback ID: {rollback_event.id}
Deployment ID: {rollback_event.deployment_id}
Trigger: {rollback_event.trigger.value}
Severity: {rollback_event.severity}
Timestamp: {rollback_event.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

This is an automated notification. The rollback system is handling the situation, but human oversight may be required.

Please check the monitoring dashboards and logs for more details.
"""
            
            # Send to urgent channels
            success = True
            
            # Send to urgent Slack channel
            if self.slack_webhook_url:
                urgent_slack_message = {
                    "text": urgent_message,
                    "channel": "#alerts-urgent",
                    "username": "Autonomica Rollback Bot",
                    "icon_emoji": ":rotating_light:"
                }
                
                try:
                    response = requests.post(
                        self.slack_webhook_url,
                        json=urgent_slack_message,
                        timeout=10
                    )
                    
                    if response.status_code != 200:
                        success = False
                        logger.error(f"Failed to send urgent Slack notification: {response.status_code}")
                        
                except Exception as e:
                    success = False
                    logger.error(f"Error sending urgent Slack notification: {e}")
            
            # Send urgent email
            try:
                if not self._send_urgent_email(urgent_message):
                    success = False
            except Exception as e:
                success = False
                logger.error(f"Error sending urgent email: {e}")
            
            if success:
                logger.info(f"Urgent notification sent successfully for rollback {rollback_event.id}")
            else:
                logger.warning(f"Some urgent notifications failed for rollback {rollback_event.id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending urgent notification: {e}")
            return False
    
    def _send_urgent_email(self, message: str) -> bool:
        """Send urgent email notification"""
        try:
            # Get email configuration
            smtp_host = self.email_config['smtp_config']['host']
            smtp_port = self.email_config['smtp_config']['port']
            smtp_username = self.email_config['smtp_config']['username']
            smtp_password = self.email_config['smtp_config']['password']
            
            # Prepare urgent email
            msg = MIMEMultipart()
            msg['From'] = smtp_username
            msg['To'] = ', '.join(self.email_config['recipients'])
            msg['Subject'] = f"🚨 URGENT: Critical Rollback Alert - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Add message body
            msg.attach(MIMEText(message, 'plain'))
            
            # Send email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            logger.info("Urgent email notification sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error sending urgent email notification: {e}")
            return False
    
    def send_rollback_summary(self, rollback_events: List['RollbackEvent']) -> bool:
        """Send summary of recent rollback events"""
        try:
            if not rollback_events:
                logger.info("No rollback events to summarize")
                return True
            
            # Prepare summary message
            summary_message = self._prepare_rollback_summary_message(rollback_events)
            
            # Send summary to all channels
            success = True
            
            # Send to Slack
            if self.slack_webhook_url:
                slack_summary = {
                    "text": summary_message,
                    "channel": "#deployments",
                    "username": "Autonomica Rollback Bot",
                    "icon_emoji": ":chart_with_upwards_trend:"
                }
                
                try:
                    response = requests.post(
                        self.slack_webhook_url,
                        json=slack_summary,
                        timeout=10
                    )
                    
                    if response.status_code != 200:
                        success = False
                        
                except Exception as e:
                    success = False
                    logger.error(f"Error sending rollback summary to Slack: {e}")
            
            # Send to email
            try:
                if not self._send_summary_email(summary_message):
                    success = False
            except Exception as e:
                success = False
                logger.error(f"Error sending rollback summary email: {e}")
            
            if success:
                logger.info("Rollback summary sent successfully")
            else:
                logger.warning("Some rollback summary notifications failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending rollback summary: {e}")
            return False
    
    def _prepare_rollback_summary_message(self, rollback_events: List['RollbackEvent']) -> str:
        """Prepare rollback summary message"""
        try:
            total_rollbacks = len(rollback_events)
            successful_rollbacks = sum(1 for event in rollback_events if event.status.value == 'completed')
            failed_rollbacks = sum(1 for event in rollback_events if event.status.value == 'failed')
            
            summary = f"""
📊 Rollback Summary Report

Period: Last 24 hours
Total Rollbacks: {total_rollbacks}
Successful: {successful_rollbacks}
Failed: {failed_rollbacks}
Success Rate: {(successful_rollbacks/total_rollbacks*100):.1f}% if total_rollbacks > 0 else 0}%

Recent Rollback Events:
"""
            
            for event in rollback_events[-5:]:  # Last 5 events
                status_emoji = "✅" if event.status.value == 'completed' else "❌"
                summary += f"{status_emoji} {event.deployment_id} - {event.trigger.value} ({event.status.value})\n"
            
            if total_rollbacks > 5:
                summary += f"\n... and {total_rollbacks - 5} more rollback events"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error preparing rollback summary message: {e}")
            return "Rollback summary report generated"
    
    def _send_summary_email(self, message: str) -> bool:
        """Send rollback summary email"""
        try:
            # Get email configuration
            smtp_host = self.email_config['smtp_config']['host']
            smtp_port = self.email_config['smtp_config']['port']
            smtp_username = self.email_config['smtp_config']['username']
            smtp_password = self.email_config['smtp_config']['password']
            
            # Prepare summary email
            msg = MIMEMultipart()
            msg['From'] = smtp_username
            msg['To'] = ', '.join(self.email_config['recipients'])
            msg['Subject'] = f"Rollback Summary Report - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Add message body
            msg.attach(MIMEText(message, 'plain'))
            
            # Send email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            logger.info("Rollback summary email sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error sending rollback summary email: {e}")
            return False