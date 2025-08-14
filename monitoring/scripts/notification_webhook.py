#!/usr/bin/env python3
"""
Autonomica Notification Webhook Service
This service receives alerts from Alertmanager and processes them for testing and development.

Implements part of Subtask 8.3: Configure alert thresholds and notifications
"""

import json
import logging
import time
from datetime import datetime
from flask import Flask, request, jsonify
from typing import Dict, List, Any
import threading
import queue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class AlertProcessor:
    """Processes and stores incoming alerts."""
    
    def __init__(self):
        self.alerts = []
        self.alert_history = []
        self.max_history = 1000
        self.lock = threading.Lock()
        
    def add_alert(self, alert_data: Dict[str, Any]) -> None:
        """Add a new alert to the system."""
        with self.lock:
            # Add timestamp if not present
            if 'startsAt' not in alert_data:
                alert_data['startsAt'] = datetime.now().isoformat()
            
            # Add to current alerts
            self.alerts.append(alert_data)
            
            # Add to history
            self.alert_history.append({
                'timestamp': datetime.now().isoformat(),
                'alert': alert_data
            })
            
            # Trim history if too long
            if len(self.alert_history) > self.max_history:
                self.alert_history.pop(0)
            
            logger.info(f"Alert received: {alert_data.get('labels', {}).get('alertname', 'Unknown')}")
    
    def resolve_alert(self, alert_data: Dict[str, Any]) -> None:
        """Mark an alert as resolved."""
        with self.lock:
            # Find and remove from current alerts
            self.alerts = [
                alert for alert in self.alerts 
                if not self._alerts_match(alert, alert_data)
            ]
            
            logger.info(f"Alert resolved: {alert_data.get('labels', {}).get('alertname', 'Unknown')}")
    
    def _alerts_match(self, alert1: Dict[str, Any], alert2: Dict[str, Any]) -> bool:
        """Check if two alerts match (for resolution)."""
        labels1 = alert1.get('labels', {})
        labels2 = alert2.get('labels', {})
        
        # Match on key identifying fields
        key_fields = ['alertname', 'instance', 'service']
        for field in key_fields:
            if labels1.get(field) != labels2.get(field):
                return False
        return True
    
    def get_current_alerts(self) -> List[Dict[str, Any]]:
        """Get all currently firing alerts."""
        with self.lock:
            return self.alerts.copy()
    
    def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get alert history."""
        with self.lock:
            return self.alert_history[-limit:].copy()
    
    def get_alerts_by_severity(self, severity: str) -> List[Dict[str, Any]]:
        """Get alerts filtered by severity."""
        with self.lock:
            return [
                alert for alert in self.alerts
                if alert.get('labels', {}).get('severity') == severity
            ]
    
    def get_alerts_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get alerts filtered by category."""
        with self.lock:
            return [
                alert for alert in self.alerts
                if alert.get('labels', {}).get('category') == category
            ]
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get a summary of current alert status."""
        with self.lock:
            total_alerts = len(self.alerts)
            critical_count = len(self.get_alerts_by_severity('critical'))
            warning_count = len(self.get_alerts_by_severity('warning'))
            
            # Group by category
            category_counts = {}
            for alert in self.alerts:
                category = alert.get('labels', {}).get('category', 'unknown')
                category_counts[category] = category_counts.get(category, 0) + 1
            
            # Group by service
            service_counts = {}
            for alert in self.alerts:
                service = alert.get('labels', {}).get('service', 'unknown')
                service_counts[service] = service_counts.get(service, 0) + 1
            
            return {
                'total_alerts': total_alerts,
                'critical_count': critical_count,
                'warning_count': warning_count,
                'category_counts': category_counts,
                'service_counts': service_counts,
                'timestamp': datetime.now().isoformat()
            }

# Global alert processor
alert_processor = AlertProcessor()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'notification-webhook'
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """Main webhook endpoint for all alerts."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data received'}), 400
        
        # Process the alert data
        if 'alerts' in data:
            for alert in data['alerts']:
                if alert.get('status') == 'firing':
                    alert_processor.add_alert(alert)
                elif alert.get('status') == 'resolved':
                    alert_processor.resolve_alert(alert)
        
        logger.info(f"Webhook processed: {len(data.get('alerts', []))} alerts")
        return jsonify({'status': 'success', 'processed': len(data.get('alerts', []))})
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/critical', methods=['POST'])
def critical_webhook():
    """Webhook endpoint for critical alerts."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data received'}), 400
        
        # Process critical alerts
        if 'alerts' in data:
            for alert in data['alerts']:
                if alert.get('status') == 'firing':
                    alert_processor.add_alert(alert)
                elif alert.get('status') == 'resolved':
                    alert_processor.resolve_alert(alert)
        
        logger.warning(f"Critical webhook processed: {len(data.get('alerts', []))} alerts")
        return jsonify({'status': 'success', 'processed': len(data.get('alerts', []))})
        
    except Exception as e:
        logger.error(f"Error processing critical webhook: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/warning', methods=['POST'])
def warning_webhook():
    """Webhook endpoint for warning alerts."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data received'}), 400
        
        # Process warning alerts
        if 'alerts' in data:
            for alert in data['alerts']:
                if alert.get('status') == 'firing':
                    alert_processor.add_alert(alert)
                elif alert.get('status') == 'resolved':
                    alert_processor.resolve_alert(alert)
        
        logger.info(f"Warning webhook processed: {len(data.get('alerts', []))} alerts")
        return jsonify({'status': 'success', 'processed': len(data.get('alerts', []))})
        
    except Exception as e:
        logger.error(f"Error processing warning webhook: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/business', methods=['POST'])
def business_webhook():
    """Webhook endpoint for business-critical alerts."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data received'}), 400
        
        # Process business alerts
        if 'alerts' in data:
            for alert in data['alerts']:
                if alert.get('status') == 'firing':
                    alert_processor.add_alert(alert)
                elif alert.get('status') == 'resolved':
                    alert_processor.resolve_alert(alert)
        
        logger.warning(f"Business webhook processed: {len(data.get('alerts', []))} alerts")
        return jsonify({'status': 'success', 'processed': len(data.get('alerts', []))})
        
    except Exception as e:
        logger.error(f"Error processing business webhook: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/infrastructure', methods=['POST'])
def infrastructure_webhook():
    """Webhook endpoint for infrastructure alerts."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data received'}), 400
        
        # Process infrastructure alerts
        if 'alerts' in data:
            for alert in data['alerts']:
                if alert.get('status') == 'firing':
                    alert_processor.add_alert(alert)
                elif alert.get('status') == 'resolved':
                    alert_processor.resolve_alert(alert)
        
        logger.info(f"Infrastructure webhook processed: {len(data.get('alerts', []))} alerts")
        return jsonify({'status': 'success', 'processed': len(data.get('alerts', []))})
        
    except Exception as e:
        logger.error(f"Error processing infrastructure webhook: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/alerts', methods=['GET'])
def get_alerts():
    """Get all current alerts."""
    return jsonify({
        'alerts': alert_processor.get_current_alerts(),
        'summary': alert_processor.get_alert_summary()
    })

@app.route('/alerts/history', methods=['GET'])
def get_alert_history():
    """Get alert history."""
    limit = request.args.get('limit', 100, type=int)
    return jsonify({
        'history': alert_processor.get_alert_history(limit),
        'total': len(alert_processor.alert_history)
    })

@app.route('/alerts/severity/<severity>', methods=['GET'])
def get_alerts_by_severity(severity):
    """Get alerts filtered by severity."""
    return jsonify({
        'alerts': alert_processor.get_alerts_by_severity(severity),
        'severity': severity,
        'count': len(alert_processor.get_alerts_by_severity(severity))
    })

@app.route('/alerts/category/<category>', methods=['GET'])
def get_alerts_by_category(category):
    """Get alerts filtered by category."""
    return jsonify({
        'alerts': alert_processor.get_alerts_by_category(category),
        'category': category,
        'count': len(alert_processor.get_alerts_by_category(category))
    })

@app.route('/alerts/summary', methods=['GET'])
def get_alert_summary():
    """Get alert summary."""
    return jsonify(alert_processor.get_alert_summary())

@app.route('/alerts/clear', methods=['POST'])
def clear_alerts():
    """Clear all current alerts (for testing)."""
    with alert_processor.lock:
        alert_processor.alerts.clear()
    
    logger.info("All alerts cleared")
    return jsonify({'status': 'success', 'message': 'All alerts cleared'})

@app.route('/alerts/test', methods=['POST'])
def test_alert():
    """Send a test alert for testing purposes."""
    try:
        data = request.get_json()
        if not data:
            data = {
                'labels': {
                    'alertname': 'TestAlert',
                    'severity': 'warning',
                    'category': 'testing',
                    'service': 'webhook'
                },
                'annotations': {
                    'summary': 'This is a test alert',
                    'description': 'This alert was generated for testing purposes'
                },
                'status': 'firing',
                'startsAt': datetime.now().isoformat()
            }
        
        alert_processor.add_alert(data)
        logger.info("Test alert generated")
        return jsonify({'status': 'success', 'message': 'Test alert generated', 'alert': data})
        
    except Exception as e:
        logger.error(f"Error generating test alert: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Autonomica Notification Webhook Service')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5001, help='Port to bind to (default: 5001)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    logger.info("🚀 Starting Autonomica Notification Webhook Service...")
    logger.info(f"📊 Service will be available at http://{args.host}:{args.port}")
    logger.info("📋 Available endpoints:")
    logger.info("   - POST /webhook - Main webhook endpoint")
    logger.info("   - POST /critical - Critical alerts")
    logger.info("   - POST /warning - Warning alerts")
    logger.info("   - POST /business - Business alerts")
    logger.info("   - POST /infrastructure - Infrastructure alerts")
    logger.info("   - GET  /alerts - Current alerts")
    logger.info("   - GET  /alerts/summary - Alert summary")
    logger.info("   - POST /alerts/test - Generate test alert")
    
    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug,
        threaded=True
    )