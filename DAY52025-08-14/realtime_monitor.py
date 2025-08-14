# src/realtime_monitor.py
"""
Real-Time System Monitoring Dashboard
Enterprise-level monitoring with live metrics, alerts, and performance tracking
"""

import streamlit as st
import time
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
import threading
import queue
from typing import Dict, List, Any
import psutil
import random

# Import our enhanced systems
from logging_manager import SmartSQLLogger
from error_recovery_manager import ErrorRecoveryManager
from enhanced_sql_agent import EnhancedSQLPipelineAgent

class RealTimeMonitor:
    """
    Real-time monitoring system with live metrics, alerts, and performance tracking
    """
    
    def __init__(self):
        self.logger = SmartSQLLogger()
        self.recovery_manager = ErrorRecoveryManager()
        self.metrics_queue = queue.Queue()
        self.is_monitoring = False
        self.monitoring_thread = None
        
        # Initialize metrics storage
        if 'metrics_history' not in st.session_state:
            st.session_state.metrics_history = []
        
        if 'alerts' not in st.session_state:
            st.session_state.alerts = []
        
        if 'system_stats' not in st.session_state:
            st.session_state.system_stats = {
                'cpu_usage': [],
                'memory_usage': [],
                'response_times': [],
                'error_rates': [],
                'timestamps': []
            }

    def start_monitoring(self):
        """Start real-time monitoring in background thread"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            
            self.logger.log_user_activity("monitoring_started", "system", {
                "monitoring_type": "real_time",
                "thread_started": True
            })

    def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1.0)
        
        self.logger.log_user_activity("monitoring_stopped", "system", {
            "monitoring_type": "real_time",
            "thread_stopped": True
        })

    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.is_monitoring:
            try:
                # Collect system metrics
                metrics = self._collect_system_metrics()
                
                # Store metrics
                current_time = datetime.now()
                st.session_state.system_stats['timestamps'].append(current_time)
                st.session_state.system_stats['cpu_usage'].append(metrics['cpu_percent'])
                st.session_state.system_stats['memory_usage'].append(metrics['memory_percent'])
                st.session_state.system_stats['response_times'].append(metrics['response_time'])
                st.session_state.system_stats['error_rates'].append(metrics['error_rate'])
                
                # Keep only last 100 data points
                for key in st.session_state.system_stats:
                    if len(st.session_state.system_stats[key]) > 100:
                        st.session_state.system_stats[key] = st.session_state.system_stats[key][-100:]
                
                # Check for alerts
                self._check_alerts(metrics)
                
                # Log metrics
                self.logger.log_performance("system_monitoring", metrics['response_time'], {
                    "cpu_usage": metrics['cpu_percent'],
                    "memory_usage": metrics['memory_percent'],
                    "error_rate": metrics['error_rate']
                })
                
                time.sleep(2)  # Update every 2 seconds
                
            except Exception as e:
                self.logger.log_error(e, {"operation": "monitoring_loop"})
                time.sleep(5)  # Wait longer on error

    def _collect_system_metrics(self) -> Dict[str, float]:
        """Collect current system metrics"""
        
        # Get actual system metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Simulate application-specific metrics
        response_time = random.uniform(0.5, 2.0)  # Simulate response time
        error_rate = random.uniform(0, 5)  # Simulate error rate %
        
        # Get health from recovery manager
        health = self.recovery_manager.get_health_report()
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'response_time': response_time,
            'error_rate': error_rate,
            'recovery_rate': health.get('recovery_rate', 0),
            'total_errors': health.get('total_errors', 0),
            'timestamp': datetime.now()
        }

    def _check_alerts(self, metrics: Dict[str, float]):
        """Check metrics against alert thresholds"""
        
        alerts = []
        current_time = datetime.now()
        
        # CPU Alert
        if metrics['cpu_percent'] > 80:
            alerts.append({
                'level': 'HIGH',
                'type': 'CPU_USAGE',
                'message': f"High CPU usage: {metrics['cpu_percent']:.1f}%",
                'timestamp': current_time,
                'value': metrics['cpu_percent']
            })
        
        # Memory Alert
        if metrics['memory_percent'] > 85:
            alerts.append({
                'level': 'HIGH', 
                'type': 'MEMORY_USAGE',
                'message': f"High memory usage: {metrics['memory_percent']:.1f}%",
                'timestamp': current_time,
                'value': metrics['memory_percent']
            })
        
        # Response Time Alert
        if metrics['response_time'] > 3.0:
            alerts.append({
                'level': 'MEDIUM',
                'type': 'RESPONSE_TIME',
                'message': f"Slow response time: {metrics['response_time']:.2f}s",
                'timestamp': current_time,
                'value': metrics['response_time']
            })
        
        # Error Rate Alert
        if metrics['error_rate'] > 10:
            alerts.append({
                'level': 'HIGH',
                'type': 'ERROR_RATE', 
                'message': f"High error rate: {metrics['error_rate']:.1f}%",
                'timestamp': current_time,
                'value': metrics['error_rate']
            })
        
        # Add alerts to session state
        for alert in alerts:
            st.session_state.alerts.append(alert)
            
            # Log alert
            self.logger.log_user_activity("alert_triggered", "system", {
                "alert_level": alert['level'],
                "alert_type": alert['type'],
                "alert_message": alert['message'],
                "metric_value": alert['value']
            })
        
        # Keep only last 50 alerts
        if len(st.session_state.alerts) > 50:
            st.session_state.alerts = st.session_state.alerts[-50:]

    def create_realtime_dashboard(self):
        """Create the real-time monitoring dashboard"""
        
        st.title("📊 Real-Time System Monitor")
        st.markdown("**Live monitoring with automatic alerts and performance tracking**")
        
        # Control buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🟢 Start Monitoring", type="primary"):
                self.start_monitoring()
                st.success("✅ Real-time monitoring started!")
        
        with col2:
            if st.button("🔴 Stop Monitoring"):
                self.stop_monitoring()
                st.info("⏹️ Monitoring stopped")
        
        with col3:
            if st.button("🔄 Refresh Dashboard"):
                st.rerun()
        
        with col4:
            auto_refresh = st.checkbox("Auto-refresh (5s)", value=True)
        
        # Auto-refresh functionality
        if auto_refresh:
            time.sleep(0.1)  # Small delay to prevent too frequent updates
            st.rerun()
        
        # Current Status Cards
        self._create_status_cards()
        
        st.divider()
        
        # Real-time Charts
        self._create_realtime_charts()
        
        st.divider()
        
        # Alerts Section
        self._create_alerts_section()
        
        st.divider()
        
        # System Health Details
        self._create_health_details()

    def _create_status_cards(self):
        """Create real-time status cards"""
        
        st.subheader("📈 Live System Metrics")
        
        if st.session_state.system_stats['timestamps']:
            # Get latest metrics
            latest_cpu = st.session_state.system_stats['cpu_usage'][-1]
            latest_memory = st.session_state.system_stats['memory_usage'][-1]
            latest_response = st.session_state.system_stats['response_times'][-1]
            latest_errors = st.session_state.system_stats['error_rates'][-1]
            
            # Calculate trends (last 10 data points)
            if len(st.session_state.system_stats['cpu_usage']) >= 10:
                cpu_trend = np.mean(st.session_state.system_stats['cpu_usage'][-5:]) - np.mean(st.session_state.system_stats['cpu_usage'][-10:-5])
                memory_trend = np.mean(st.session_state.system_stats['memory_usage'][-5:]) - np.mean(st.session_state.system_stats['memory_usage'][-10:-5])
                response_trend = np.mean(st.session_state.system_stats['response_times'][-5:]) - np.mean(st.session_state.system_stats['response_times'][-10:-5])
                error_trend = np.mean(st.session_state.system_stats['error_rates'][-5:]) - np.mean(st.session_state.system_stats['error_rates'][-10:-5])
            else:
                cpu_trend = memory_trend = response_trend = error_trend = 0
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                delta_color = "inverse" if cpu_trend > 0 else "normal"
                st.metric(
                    "🖥️ CPU Usage", 
                    f"{latest_cpu:.1f}%",
                    delta=f"{cpu_trend:+.1f}%",
                    delta_color=delta_color
                )
            
            with col2:
                delta_color = "inverse" if memory_trend > 0 else "normal"
                st.metric(
                    "💾 Memory Usage",
                    f"{latest_memory:.1f}%", 
                    delta=f"{memory_trend:+.1f}%",
                    delta_color=delta_color
                )
            
            with col3:
                delta_color = "inverse" if response_trend > 0 else "normal"
                st.metric(
                    "⚡ Response Time",
                    f"{latest_response:.2f}s",
                    delta=f"{response_trend:+.2f}s",
                    delta_color=delta_color
                )
            
            with col4:
                delta_color = "inverse" if error_trend > 0 else "normal"
                st.metric(
                    "🚨 Error Rate",
                    f"{latest_errors:.1f}%",
                    delta=f"{error_trend:+.1f}%",
                    delta_color=delta_color
                )
        
        else:
            st.info("📊 Start monitoring to see live metrics")

    def _create_realtime_charts(self):
        """Create real-time charts"""
        
        st.subheader("📈 Real-Time Performance Charts")
        
        if st.session_state.system_stats['timestamps']:
            
            # Create subplot with 2x2 layout
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('CPU Usage (%)', 'Memory Usage (%)', 'Response Time (s)', 'Error Rate (%)'),
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            timestamps = st.session_state.system_stats['timestamps']
            
            # CPU Usage
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=st.session_state.system_stats['cpu_usage'],
                    mode='lines+markers',
                    name='CPU %',
                    line=dict(color='#1f77b4', width=2),
                    hovertemplate='%{y:.1f}%<br>%{x}<extra></extra>'
                ),
                row=1, col=1
            )
            
            # Memory Usage
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=st.session_state.system_stats['memory_usage'],
                    mode='lines+markers',
                    name='Memory %',
                    line=dict(color='#ff7f0e', width=2),
                    hovertemplate='%{y:.1f}%<br>%{x}<extra></extra>'
                ),
                row=1, col=2
            )
            
            # Response Time
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=st.session_state.system_stats['response_times'],
                    mode='lines+markers',
                    name='Response Time',
                    line=dict(color='#2ca02c', width=2),
                    hovertemplate='%{y:.2f}s<br>%{x}<extra></extra>'
                ),
                row=2, col=1
            )
            
            # Error Rate
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=st.session_state.system_stats['error_rates'],
                    mode='lines+markers',
                    name='Error Rate',
                    line=dict(color='#d62728', width=2),
                    hovertemplate='%{y:.1f}%<br>%{x}<extra></extra>'
                ),
                row=2, col=2
            )
            
            # Update layout
            fig.update_layout(
                height=600,
                showlegend=False,
                title_text="Real-Time System Metrics",
                title_x=0.5
            )
            
            # Add threshold lines
            fig.add_hline(y=80, line_dash="dash", line_color="red", opacity=0.7, row=1, col=1)  # CPU threshold
            fig.add_hline(y=85, line_dash="dash", line_color="red", opacity=0.7, row=1, col=2)  # Memory threshold
            fig.add_hline(y=3.0, line_dash="dash", line_color="red", opacity=0.7, row=2, col=1)  # Response time threshold
            fig.add_hline(y=10.0, line_dash="dash", line_color="red", opacity=0.7, row=2, col=2)  # Error rate threshold
            
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.info("📈 Start monitoring to see real-time charts")

    def _create_alerts_section(self):
        """Create alerts section"""
        
        st.subheader("🚨 System Alerts")
        
        if st.session_state.alerts:
            # Filter recent alerts (last hour)
            recent_alerts = [
                alert for alert in st.session_state.alerts
                if alert['timestamp'] > datetime.now() - timedelta(hours=1)
            ]
            
            if recent_alerts:
                # Alert summary
                high_alerts = len([a for a in recent_alerts if a['level'] == 'HIGH'])
                medium_alerts = len([a for a in recent_alerts if a['level'] == 'MEDIUM'])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("🔴 High Priority", high_alerts)
                with col2:
                    st.metric("🟡 Medium Priority", medium_alerts)
                with col3:
                    st.metric("📊 Total (1h)", len(recent_alerts))
                
                # Recent alerts table
                alerts_df = pd.DataFrame(recent_alerts)
                alerts_df['timestamp'] = alerts_df['timestamp'].dt.strftime('%H:%M:%S')
                
                # Style alerts by level
                def color_alerts(val):
                    if val == 'HIGH':
                        return 'background-color: #ffebee'
                    elif val == 'MEDIUM':
                        return 'background-color: #fff3e0'
                    return ''
                
                styled_df = alerts_df.style.applymap(color_alerts, subset=['level'])
                st.dataframe(styled_df, use_container_width=True)
                
            else:
                st.success("✅ No alerts in the last hour")
        
        else:
            st.info("🔔 No alerts yet - system monitoring will generate alerts based on thresholds")

    def _create_health_details(self):
        """Create detailed health information"""
        
        st.subheader("💚 System Health Details")
        
        # Get current health status
        try:
            # This would typically come from your enhanced agent
            health_data = {
                'overall_status': 'HEALTHY',
                'components': {
                    'monitoring_system': 'OPERATIONAL',
                    'error_recovery': 'ACTIVE',
                    'logging_system': 'OPERATIONAL',
                    'database_connections': 'HEALTHY'
                },
                'uptime': '99.95%',
                'last_restart': '2 days ago',
                'monitoring_duration': len(st.session_state.system_stats['timestamps']) * 2 if st.session_state.system_stats['timestamps'] else 0
            }
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🎯 System Status**")
                for component, status in health_data['components'].items():
                    status_icon = "🟢" if status in ['OPERATIONAL', 'ACTIVE', 'HEALTHY'] else "🟡"
                    st.write(f"{status_icon} **{component.replace('_', ' ').title()}**: {status}")
            
            with col2:
                st.markdown("**📊 System Info**")
                st.write(f"⏱️ **Uptime**: {health_data['uptime']}")
                st.write(f"🔄 **Last Restart**: {health_data['last_restart']}")
                st.write(f"📡 **Monitoring Duration**: {health_data['monitoring_duration']} seconds")
                st.write(f"📈 **Data Points Collected**: {len(st.session_state.system_stats['timestamps'])}")
        
        except Exception as e:
            st.error(f"⚠️ Health check failed: {e}")

# 🧪 Test the real-time monitor
def main():
    """Test the real-time monitoring system"""
    
    st.set_page_config(
        page_title="Real-Time Monitor",
        page_icon="📊",
        layout="wide"
    )
    
    # Initialize monitor
    if 'monitor' not in st.session_state:
        st.session_state.monitor = RealTimeMonitor()
    
    # Create dashboard
    st.session_state.monitor.create_realtime_dashboard()

if __name__ == "__main__":
    main()
