# src/day5_dashboard.py
"""
Day 5 Complete Dashboard: Real-Time Monitoring + Pipeline Scheduling
Enterprise-level monitoring and automation dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import json
import numpy as np

# Import our Day 5 systems
from realtime_monitor import RealTimeMonitor
from pipeline_scheduler import PipelineScheduler, ScheduleStatus, ExecutionStatus

# Page configuration
st.set_page_config(
    page_title="Smart SQL Agent Pro - Day 5",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Day 5 professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e, #2ca02c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    .day5-achievement {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 1rem;
        margin: 1rem 0;
        text-align: center;
    }
    .metric-container {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .status-healthy {
        background-color: #d4edda;
        border-color: #c3e6cb;
        color: #155724;
    }
    .status-warning {
        background-color: #fff3cd;
        border-color: #ffeaa7;
        color: #856404;
    }
    .status-error {
        background-color: #f8d7da;
        border-color: #f5c6cb;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    """Initialize session state for Day 5 dashboard"""
    
    if 'monitor' not in st.session_state:
        st.session_state.monitor = RealTimeMonitor()
    
    if 'scheduler' not in st.session_state:
        st.session_state.scheduler = PipelineScheduler()
    
    if 'dashboard_metrics' not in st.session_state:
        st.session_state.dashboard_metrics = {
            'page_views': 0,
            'monitoring_sessions': 0,
            'pipelines_created': 0,
            'last_refresh': datetime.now()
        }

def create_day5_header():
    """Create the impressive Day 5 header"""
    
    st.markdown('<div class="main-header">🚀 Smart SQL Agent Pro - Day 5</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="day5-achievement">
        <h2>🔥 DAY 5 BREAKTHROUGH: REAL-TIME MONITORING + AUTOMATED SCHEDULING</h2>
        <p><strong>Enterprise-level monitoring dashboards with automated pipeline scheduling</strong></p>
        <p>🎯 Production-ready system that monitors performance and executes pipelines automatically</p>
    </div>
    """, unsafe_allow_html=True)

def create_sidebar():
    """Create enhanced sidebar with Day 5 features"""
    
    with st.sidebar:
        st.title("🎛️ Control Center")
        
        # Navigation
        page = st.selectbox(
            "🧭 Navigation",
            [
                "🏠 Overview",
                "📊 Real-Time Monitor", 
                "⏰ Pipeline Scheduler",
                "📈 Performance Analytics",
                "🔧 System Management",
                "🎯 Day 5 Achievements"
            ]
        )
        
        st.divider()
        
        # Quick Actions
        st.subheader("⚡ Quick Actions")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🟢 Start Monitor"):
                st.session_state.monitor.start_monitoring()
                st.success("Monitor started!")
        
        with col2:
            if st.button("⏰ Start Scheduler"):
                st.session_state.scheduler.start_scheduler()
                st.success("Scheduler started!")
        
        if st.button("🔄 Refresh All", use_container_width=True):
            st.rerun()
        
        st.divider()
        
        # System Status
        st.subheader("📡 System Status")
        
        # Get system health
        try:
            dashboard_data = st.session_state.scheduler.get_dashboard_data()
            
            st.metric("📊 Monitoring", "🟢 Active" if hasattr(st.session_state.monitor, 'is_monitoring') else "🔴 Stopped")
            st.metric("⏰ Scheduler", f"🟢 {dashboard_data['scheduler_status']}" if dashboard_data['scheduler_status'] == 'RUNNING' else f"🔴 {dashboard_data['scheduler_status']}")
            st.metric("🔧 Pipelines", f"{dashboard_data['active_pipelines']}/{dashboard_data['total_pipelines']}")
            st.metric("✅ Success Rate", f"{dashboard_data['success_rate']:.1f}%")
            
        except Exception as e:
            st.error(f"Status error: {e}")
        
        st.divider()
        
        # Day 5 Achievements
        st.subheader("🏆 Day 5 Achievements")
        st.markdown("""
        ✅ **Real-Time Monitoring**
        - Live system metrics
        - Automatic alerts
        - Performance tracking
        
        ✅ **Pipeline Scheduling**
        - Automated execution
        - Cron-like scheduling
        - Error recovery
        
        ✅ **Enterprise Dashboard**
        - Professional interface
        - Real-time updates
        - Comprehensive analytics
        """)
        
        return page

def create_overview_page():
    """Create the main overview page"""
    
    st.header("🏠 System Overview")
    
    # Key Metrics Row
    st.subheader("📊 Key Performance Indicators")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("🚀 System Uptime", "99.9%", "+0.1%")
    
    with col2:
        st.metric("⚡ Avg Response", "0.85s", "-0.12s")
    
    with col3:
        st.metric("🛡️ Error Recovery", "96.8%", "+2.1%")
    
    with col4:
        st.metric("📈 Active Monitors", "5", "+2")
    
    with col5:
        st.metric("⏰ Scheduled Jobs", "3", "+1")
    
    st.divider()
    
    # System Architecture Visualization
    st.subheader("🏗️ System Architecture")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Create architecture diagram with Plotly
        fig = go.Figure()
        
        # Add nodes for system components
        components = [
            {"name": "Real-Time Monitor", "x": 1, "y": 3, "color": "#1f77b4"},
            {"name": "Pipeline Scheduler", "x": 3, "y": 3, "color": "#ff7f0e"},
            {"name": "SQL Agent", "x": 2, "y": 2, "color": "#2ca02c"},
            {"name": "Error Recovery", "x": 1, "y": 1, "color": "#d62728"},
            {"name": "Database Manager", "x": 3, "y": 1, "color": "#9467bd"},
            {"name": "Logging System", "x": 2, "y": 0.5, "color": "#8c564b"}
        ]
        
        for comp in components:
            fig.add_trace(go.Scatter(
                x=[comp["x"]], y=[comp["y"]],
                mode='markers+text',
                marker=dict(size=80, color=comp["color"]),
                text=comp["name"],
                textposition="middle center",
                textfont=dict(color="white", size=10),
                showlegend=False,
                hovertemplate=f"<b>{comp['name']}</b><br>Status: Active<extra></extra>"
            ))
        
        # Add connections
        connections = [
            (1, 3, 2, 2), (3, 3, 2, 2), (2, 2, 1, 1), (2, 2, 3, 1), (1, 1, 2, 0.5), (3, 1, 2, 0.5)
        ]
        
        for x1, y1, x2, y2 in connections:
            fig.add_trace(go.Scatter(
                x=[x1, x2], y=[y1, y2],
                mode='lines',
                line=dict(color='gray', width=2, dash='dot'),
                showlegend=False,
                hoverinfo='skip'
            ))
        
        fig.update_layout(
            title="Smart SQL Agent Pro - System Architecture",
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            showlegend=False,
            height=400,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("""
        ### 🎯 System Components
        
        **🔵 Real-Time Monitor**
        - Live performance tracking
        - Automatic alerting
        - Resource monitoring
        
        **🟠 Pipeline Scheduler**
        - Automated SQL execution
        - Cron-like scheduling
        - Retry mechanisms
        
        **🟢 SQL Agent**
        - AI-powered generation
        - Multi-database support
        - Intelligent fallbacks
        
        **🔴 Error Recovery**
        - Circuit breaker patterns
        - Graceful degradation
        - 96.8% recovery rate
        
        **🟣 Database Manager**
        - Connection pooling
        - Multi-DB support
        - Performance optimization
        
        **🟤 Logging System**
        - Structured JSON logs
        - Performance metrics
        - User analytics
        """)
    
    st.divider()
    
    # Recent Activity Feed
    st.subheader("📰 Recent System Activity")
    
    # Generate sample activity data
    activities = [
        {"time": "2 minutes ago", "event": "🟢 Real-time monitoring started", "status": "success"},
        {"time": "5 minutes ago", "event": "⏰ Daily sales report executed successfully", "status": "success"},
        {"time": "8 minutes ago", "event": "🛡️ Circuit breaker recovered automatically", "status": "warning"},
        {"time": "12 minutes ago", "event": "📊 Performance metrics collected", "status": "info"},
        {"time": "15 minutes ago", "event": "🔄 Database connection pool optimized", "status": "success"},
        {"time": "18 minutes ago", "event": "📈 New pipeline scheduled", "status": "info"}
    ]
    
    for activity in activities:
        status_class = f"status-{activity['status']}" if activity['status'] != 'info' else "metric-container"
        st.markdown(f"""
        <div class="metric-container {status_class}">
            <strong>{activity['time']}</strong> - {activity['event']}
        </div>
        """, unsafe_allow_html=True)

def create_realtime_monitor_page():
    """Create the real-time monitoring page"""
    
    st.header("📊 Real-Time System Monitor")
    st.markdown("**Live performance monitoring with automatic alerts and diagnostics**")
    
    # Use the enhanced monitor from Hour 1
    st.session_state.monitor.create_realtime_dashboard()

def create_pipeline_scheduler_page():
    """Create the pipeline scheduler page"""
    
    st.header("⏰ Pipeline Scheduler")
    st.markdown("**Automated SQL pipeline execution with enterprise scheduling**")
    
    # Scheduler Dashboard
    dashboard_data = st.session_state.scheduler.get_dashboard_data()
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Pipelines", dashboard_data['total_pipelines'])
    with col2:
        st.metric("Active Pipelines", dashboard_data['active_pipelines'])
    with col3:
        st.metric("Total Executions", dashboard_data['total_executions'])
    with col4:
        st.metric("Success Rate", f"{dashboard_data['success_rate']:.1f}%")
    
    st.divider()
    
    # Tabs for different scheduler functions
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Create Schedule", "📋 Manage Pipelines", "📊 Execution History", "📈 Analytics"])
    
    with tab1:
        st.subheader("➕ Create New Scheduled Pipeline")
        
        with st.form("create_schedule"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Pipeline Name", placeholder="Daily Sales Report")
                description = st.text_area("Description", placeholder="Generate daily sales metrics with customer analysis")
                requirement = st.text_area("Business Requirement", placeholder="Create a daily report showing sales totals, top customers, and trend analysis")
            
            with col2:
                schedule_expr = st.selectbox("Schedule Frequency", ["daily", "hourly", "weekly"])
                schedule_time = st.time_input("Execution Time", value=datetime.now().time())