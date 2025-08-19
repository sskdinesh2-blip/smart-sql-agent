# src/day8_monitoring.py
"""
Day 8: Production Monitoring & Alerting System
Real-time metrics, health checks, and automated alerts
"""

import psutil
import time
import json
import requests
import smtplib
import sqlite3
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import asyncio
from fastapi import FastAPI, BackgroundTasks
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import logging

# Metrics collectors
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_USERS = Gauge('active_users_total', 'Number of active users')
DATABASE_CONNECTIONS = Gauge('database_connections_active', 'Active database connections')
SYSTEM_CPU = Gauge('system_cpu_percent', 'System CPU usage percentage')
SYSTEM_MEMORY = Gauge('system_memory_percent', 'System memory usage percentage')
ERROR_RATE = Gauge('error_rate_percent', 'Error rate percentage')

@dataclass
class AlertConfig:
    """Alert configuration settings"""
    cpu_threshold: float = 80.0
    memory_threshold: float = 85.0
    error_rate_threshold: float = 5.0
    response_time_threshold: float = 2.0
    disk_threshold: float = 90.0
    database_connection_threshold: int = 80

@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict[str, int]
    database_connections: int
    active_users: int
    request_count: int
    error_count: int
    average_response_time: float

class ProductionMonitor:
    """Production monitoring and alerting system"""
    
    def __init__(self, alert_config: AlertConfig = None):
        self.alert_config = alert_config or AlertConfig()
        self.metrics_history = []
        self.alert_history = []
        self.setup_logging()
        
    def setup_logging(self):
        """Setup production logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/production.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system performance metrics"""
        try:
            # CPU and Memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
            
            # Database connections (mock - replace with actual DB query)
            database_connections = self.get_database_connection_count()
            
            # Active users (from your auth system)
            active_users = self.get_active_user_count()
            
            # Request metrics (from your API)
            request_count, error_count, avg_response_time = self.get_request_metrics()
            
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_percent=disk_percent,
                network_io=network_io,
                database_connections=database_connections,
                active_users=active_users,
                request_count=request_count,
                error_count=error_count,
                average_response_time=avg_response_time
            )
            
            # Update Prometheus metrics
            SYSTEM_CPU.set(cpu_percent)
            SYSTEM_MEMORY.set(memory_percent)
            ACTIVE_USERS.set(active_users)
            DATABASE_CONNECTIONS.set(database_connections)
            
            self.metrics_history.append(metrics)
            
            # Keep only last 1000 metrics
            if len(self.metrics_history) > 1000:
                self.metrics_history = self.metrics_history[-1000:]
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")
            return None
    
    def get_database_connection_count(self) -> int:
        """Get current database connection count"""
        try:
            # Mock implementation - replace with actual database query
            return 15  # Placeholder
        except Exception as e:
            self.logger.error(f"Error getting DB connection count: {e}")
            return 0
    
    def get_active_user_count(self) -> int:
        """Get count of active users in last 5 minutes"""
        try:
            # Mock implementation - replace with actual user session query
            return 8  # Placeholder
        except Exception as e:
            self.logger.error(f"Error getting active user count: {e}")
            return 0
    
    def get_request_metrics(self) -> tuple:
        """Get request count, error count, and average response time"""
        try:
            # Mock implementation - replace with actual metrics collection
            return 150, 3, 0.45  # request_count, error_count, avg_response_time
        except Exception as e:
            self.logger.error(f"Error getting request metrics: {e}")
            return 0, 0, 0.0
    
    def check_alerts(self, metrics: SystemMetrics) -> List[Dict]:
        """Check if any alert conditions are met"""
        alerts = []
        
        # CPU alert
        if metrics.cpu_percent > self.alert_config.cpu_threshold:
            alerts.append({
                'type': 'cpu_high',
                'severity': 'warning',
                'message': f'High CPU usage: {metrics.cpu_percent:.1f}%',
                'value': metrics.cpu_percent,
                'threshold': self.alert_config.cpu_threshold,
                'timestamp': metrics.timestamp
            })
        
        # Memory alert
        if metrics.memory_percent > self.alert_config.memory_threshold:
            alerts.append({
                'type': 'memory_high',
                'severity': 'warning',
                'message': f'High memory usage: {metrics.memory_percent:.1f}%',
                'value': metrics.memory_percent,
                'threshold': self.alert_config.memory_threshold,
                'timestamp': metrics.timestamp
            })
        
        # Disk alert
        if metrics.disk_percent > self.alert_config.disk_threshold:
            alerts.append({
                'type': 'disk_high',
                'severity': 'critical',
                'message': f'High disk usage: {metrics.disk_percent:.1f}%',
                'value': metrics.disk_percent,
                'threshold': self.alert_config.disk_threshold,
                'timestamp': metrics.timestamp
            })
        
        # Response time alert
        if metrics.average_response_time > self.alert_config.response_time_threshold:
            alerts.append({
                'type': 'response_time_high',
                'severity': 'warning',
                'message': f'High response time: {metrics.average_response_time:.2f}s',
                'value': metrics.average_response_time,
                'threshold': self.alert_config.response_time_threshold,
                'timestamp': metrics.timestamp
            })
        
        # Error rate alert
        if metrics.request_count > 0:
            error_rate = (metrics.error_count / metrics.request_count) * 100
            if error_rate > self.alert_config.error_rate_threshold:
                alerts.append({
                    'type': 'error_rate_high',
                    'severity': 'critical',
                    'message': f'High error rate: {error_rate:.1f}%',
                    'value': error_rate,
                    'threshold': self.alert_config.error_rate_threshold,
                    'timestamp': metrics.timestamp
                })
        
        # Database connections alert
        if metrics.database_connections > self.alert_config.database_connection_threshold:
            alerts.append({
                'type': 'db_connections_high',
                'severity': 'warning',
                'message': f'High DB connections: {metrics.database_connections}',
                'value': metrics.database_connections,
                'threshold': self.alert_config.database_connection_threshold,
                'timestamp': metrics.timestamp
            })
        
        return alerts
    
    def send_slack_alert(self, alert: Dict, webhook_url: str):
        """Send alert to Slack"""
        try:
            severity_colors = {
                'info': '#36a64f',
                'warning': '#ffb366',
                'critical': '#ff4444'
            }
            
            payload = {
                "attachments": [{
                    "color": severity_colors.get(alert['severity'], '#808080'),
                    "title": f"Smart SQL Agent Alert - {alert['severity'].upper()}",
                    "text": alert['message'],
                    "fields": [
                        {
                            "title": "Current Value",
                            "value": str(alert['value']),
                            "short": True
                        },
                        {
                            "title": "Threshold",
                            "value": str(alert['threshold']),
                            "short": True
                        },
                        {
                            "title": "Time",
                            "value": alert['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
                            "short": True
                        }
                    ]
                }]
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            if response.status_code == 200:
                self.logger.info(f"Slack alert sent successfully: {alert['type']}")
            else:
                self.logger.error(f"Failed to send Slack alert: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Error sending Slack alert: {e}")
    
    def send_email_alert(self, alert: Dict, smtp_config: Dict):
        """Send alert via email"""
        try:
            msg = MimeMultipart()
            msg['From'] = smtp_config['from_email']
            msg['To'] = smtp_config['to_email']
            msg['Subject'] = f"Smart SQL Agent Alert - {alert['severity'].upper()}: {alert['type']}"
            
            body = f"""
Smart SQL Agent Production Alert

Severity: {alert['severity'].upper()}
Type: {alert['type']}
Message: {alert['message']}

Details:
- Current Value: {alert['value']}
- Threshold: {alert['threshold']}
- Timestamp: {alert['timestamp']}

Please investigate immediately.

Best regards,
Smart SQL Agent Monitoring System
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(smtp_config['smtp_server'], smtp_config['smtp_port'])
            server.starttls()
            server.login(smtp_config['username'], smtp_config['password'])
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"Email alert sent successfully: {alert['type']}")
            
        except Exception as e:
            self.logger.error(f"Error sending email alert: {e}")
    
    def process_alerts(self, alerts: List[Dict]):
        """Process and send alerts"""
        for alert in alerts:
            # Add to alert history
            self.alert_history.append(alert)
            
            # Log alert
            self.logger.warning(f"ALERT: {alert['message']}")
            
            # Send notifications (implement based on configuration)
            # slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
            # if slack_webhook:
            #     self.send_slack_alert(alert, slack_webhook)
    
    def get_health_status(self) -> Dict:
        """Get overall system health status"""
        if not self.metrics_history:
            return {'status': 'unknown', 'message': 'No metrics available'}
        
        latest_metrics = self.metrics_history[-1]
        alerts = self.check_alerts(latest_metrics)
        
        # Determine overall health
        critical_alerts = [a for a in alerts if a['severity'] == 'critical']
        warning_alerts = [a for a in alerts if a['severity'] == 'warning']
        
        if critical_alerts:
            status = 'critical'
            message = f"{len(critical_alerts)} critical alerts"
        elif warning_alerts:
            status = 'warning'
            message = f"{len(warning_alerts)} warnings"
        else:
            status = 'healthy'
            message = 'All systems operational'
        
        return {
            'status': status,
            'message': message,
            'timestamp': latest_metrics.timestamp.isoformat(),
            'metrics': {
                'cpu_percent': latest_metrics.cpu_percent,
                'memory_percent': latest_metrics.memory_percent,
                'disk_percent': latest_metrics.disk_percent,
                'active_users': latest_metrics.active_users,
                'database_connections': latest_metrics.database_connections,
                'average_response_time': latest_metrics.average_response_time
            },
            'alerts': alerts
        }
    
    def get_performance_report(self, hours: int = 24) -> Dict:
        """Generate performance report for specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return {'error': 'No metrics available for specified period'}
        
        # Calculate averages
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        avg_response_time = sum(m.average_response_time for m in recent_metrics) / len(recent_metrics)
        max_users = max(m.active_users for m in recent_metrics)
        total_requests = sum(m.request_count for m in recent_metrics)
        total_errors = sum(m.error_count for m in recent_metrics)
        
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'period_hours': hours,
            'metrics_count': len(recent_metrics),
            'averages': {
                'cpu_percent': round(avg_cpu, 2),
                'memory_percent': round(avg_memory, 2),
                'response_time_seconds': round(avg_response_time, 3)
            },
            'peaks': {
                'max_concurrent_users': max_users,
                'max_cpu': max(m.cpu_percent for m in recent_metrics),
                'max_memory': max(m.memory_percent for m in recent_metrics)
            },
            'totals': {
                'requests': total_requests,
                'errors': total_errors,
                'error_rate_percent': round(error_rate, 2)
            }
        }
    
    async def monitoring_loop(self):
        """Main monitoring loop that runs continuously"""
        self.logger.info("Starting production monitoring loop")
        
        while True:
            try:
                # Collect metrics
                metrics = self.collect_system_metrics()
                if metrics:
                    # Check for alerts
                    alerts = self.check_alerts(metrics)
                    if alerts:
                        self.process_alerts(alerts)
                
                # Wait for next collection cycle
                await asyncio.sleep(30)  # Collect metrics every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error

class LoadBalancerHealthCheck:
    """Health check for load balancer integration"""
    
    def __init__(self, monitor: ProductionMonitor):
        self.monitor = monitor
    
    def is_healthy(self) -> bool:
        """Determine if this instance should receive traffic"""
        try:
            health = self.monitor.get_health_status()
            return health['status'] in ['healthy', 'warning']
        except:
            return False
    
    def get_load_balancer_response(self) -> Dict:
        """Return health check response for load balancer"""
        if self.is_healthy():
            return {
                'status': 'UP',
                'timestamp': datetime.now().isoformat(),
                'checks': {
                    'database': 'UP',
                    'memory': 'UP',
                    'cpu': 'UP'
                }
            }
        else:
            return {
                'status': 'DOWN',
                'timestamp': datetime.now().isoformat(),
                'checks': {
                    'database': 'DOWN',
                    'memory': 'DOWN',
                    'cpu': 'DOWN'
                }
            }

# Global monitor instance
production_monitor = ProductionMonitor()

# FastAPI endpoints for monitoring
monitoring_app = FastAPI()

@monitoring_app.get("/health")
async def health_check():
    """Health check endpoint for load balancers"""
    return production_monitor.get_health_status()

@monitoring_app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()

@monitoring_app.get("/status")
async def detailed_status():
    """Detailed system status"""
    return {
        'health': production_monitor.get_health_status(),
        'performance_24h': production_monitor.get_performance_report(24),
        'alert_history': production_monitor.alert_history[-10:],  # Last 10 alerts
        'uptime': time.time() - production_monitor.metrics_history[0].timestamp.timestamp() if production_monitor.metrics_history else 0
    }

@monitoring_app.post("/test-alert")
async def test_alert():
    """Test alert system"""
    test_alert = {
        'type': 'test_alert',
        'severity': 'info',
        'message': 'Test alert from monitoring system',
        'value': 100,
        'threshold': 90,
        'timestamp': datetime.now()
    }
    
    production_monitor.process_alerts([test_alert])
    return {'message': 'Test alert sent'}

if __name__ == "__main__":
    # Start monitoring
    import uvicorn
    
    # Start monitoring loop in background
    import threading
    
    def start_monitoring():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(production_monitor.monitoring_loop())
    
    monitor_thread = threading.Thread(target=start_monitoring, daemon=True)
    monitor_thread.start()
    
    # Start monitoring API
    uvicorn.run(monitoring_app, host="0.0.0.0", port=8080)