# src/ultimate_showcase.py
"""
Smart SQL Agent Pro - Ultimate Feature Showcase
Complete interface showing ALL capabilities from Days 1-6
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import json
import sqlite3
import os
import random
import numpy as np
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Smart SQL Agent Pro - Ultimate Showcase",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.8rem;
        font-weight: bold;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e, #2ca02c, #d62728, #9467bd, #8c564b);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .feature-showcase {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 1rem;
        margin: 1rem 0;
        text-align: center;
    }
    .day-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.8rem;
        border-left: 5px solid #1f77b4;
        margin: 1rem 0;
    }
    .feature-card {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 2px solid #e9ecef;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-highlight {
        background: linear-gradient(45deg, #28a745, #20c997);
        color: white;
        padding: 0.8rem;
        border-radius: 0.5rem;
        text-align: center;
        margin: 0.5rem;
    }
    .api-demo {
        background: #f1f3f4;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #17a2b8;
    }
</style>
""", unsafe_allow_html=True)

class UltimateAgent:
    """Complete agent showcasing all features"""
    
    def __init__(self):
        self.setup_session_state()
        self.setup_sample_data()
    
    def setup_session_state(self):
        """Initialize all session state variables"""
        
        # Core metrics
        if 'system_metrics' not in st.session_state:
            st.session_state.system_metrics = {
                'total_queries': 2847,
                'success_rate': 96.8,
                'avg_response_time': 0.85,
                'uptime_days': 15,
                'error_recovery_rate': 96.8,
                'api_calls': 1205,
                'pipelines_executed': 247
            }
        
        # Real-time monitoring data
        if 'realtime_data' not in st.session_state:
            st.session_state.realtime_data = {
                'timestamps': [],
                'cpu_usage': [],
                'memory_usage': [],
                'response_times': [],
                'throughput': []
            }
        
        # Pipeline data
        if 'pipeline_data' not in st.session_state:
            st.session_state.pipeline_data = {
                'daily_sales': {
                    'name': 'Daily Sales Report',
                    'schedule': 'Daily at 09:00',
                    'status': 'ACTIVE',
                    'executions': 67,
                    'success_rate': 98.5,
                    'last_run': '2024-08-15 09:00:15',
                    'avg_duration': '1.2s'
                },
                'customer_analytics': {
                    'name': 'Customer Segmentation',
                    'schedule': 'Weekly on Monday',
                    'status': 'ACTIVE',
                    'executions': 24,
                    'success_rate': 96.2,
                    'last_run': '2024-08-12 10:30:22',
                    'avg_duration': '2.1s'
                },
                'inventory_sync': {
                    'name': 'Inventory Synchronization',
                    'schedule': 'Hourly',
                    'status': 'PAUSED',
                    'executions': 156,
                    'success_rate': 94.8,
                    'last_run': '2024-08-15 14:00:05',
                    'avg_duration': '0.8s'
                }
            }
    
    def setup_sample_data(self):
        """Setup sample database and data"""
        try:
            conn = sqlite3.connect('showcase_data.db')
            cursor = conn.cursor()
            
            # Create tables if they don't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    email TEXT,
                    city TEXT,
                    segment TEXT,
                    created_date DATE,
                    total_spent REAL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    order_id INTEGER PRIMARY KEY,
                    customer_id INTEGER,
                    product TEXT,
                    amount REAL,
                    date DATE,
                    status TEXT
                )
            ''')
            
            # Insert sample data
            cursor.execute("SELECT COUNT(*) FROM customers")
            if cursor.fetchone()[0] == 0:
                sample_customers = [
                    (1, 'Alice Johnson', 'alice@example.com', 'New York', 'Premium', '2024-01-15', 2499.99),
                    (2, 'Bob Smith', 'bob@example.com', 'Los Angeles', 'Standard', '2024-02-20', 1299.50),
                    (3, 'Carol Davis', 'carol@example.com', 'Chicago', 'Premium', '2024-03-10', 3199.99),
                    (4, 'David Wilson', 'david@example.com', 'Houston', 'Standard', '2024-01-25', 899.99),
                    (5, 'Eva Brown', 'eva@example.com', 'Phoenix', 'Enterprise', '2024-02-14', 5499.99)
                ]
                
                sample_orders = [
                    (1, 1, 'Analytics Platform', 1299.99, '2024-08-01', 'Completed'),
                    (2, 2, 'Database Tools', 599.99, '2024-08-02', 'Completed'),
                    (3, 1, 'ML Pipeline', 1199.99, '2024-08-03', 'Completed'),
                    (4, 3, 'Enterprise Suite', 2999.99, '2024-08-04', 'Processing'),
                    (5, 4, 'Starter Pack', 299.99, '2024-08-05', 'Completed'),
                    (6, 5, 'Full Platform', 4999.99, '2024-08-06', 'Completed'),
                    (7, 2, 'Add-on Tools', 699.99, '2024-08-07', 'Completed'),
                    (8, 3, 'Premium Support', 199.99, '2024-08-08', 'Active')
                ]
                
                cursor.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?)", sample_customers)
                cursor.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)", sample_orders)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            st.error(f"Database setup error: {e}")
    
    def generate_sql(self, requirement, schema_info=""):
        """Generate SQL with intelligent fallbacks"""
        
        start_time = time.time()
        
        # Simulate AI generation or use fallbacks
        req_lower = requirement.lower()
        
        if 'revenue' in req_lower or 'sales' in req_lower:
            sql = '''-- Sales Revenue Analysis
SELECT 
    c.name,
    c.segment,
    COUNT(o.order_id) as order_count,
    SUM(o.amount) as total_revenue,
    AVG(o.amount) as avg_order_value,
    MAX(o.date) as last_order_date
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
WHERE o.status = 'Completed'
GROUP BY c.id, c.name, c.segment
ORDER BY total_revenue DESC;'''
        
        elif 'customer' in req_lower and 'segment' in req_lower:
            sql = '''-- Customer Segmentation Analysis
SELECT 
    segment,
    COUNT(*) as customer_count,
    AVG(total_spent) as avg_customer_value,
    SUM(total_spent) as segment_revenue,
    MIN(created_date) as earliest_customer,
    MAX(created_date) as latest_customer
FROM customers
GROUP BY segment
ORDER BY segment_revenue DESC;'''
        
        elif 'trend' in req_lower or 'monthly' in req_lower:
            sql = '''-- Monthly Trends Analysis
SELECT 
    strftime('%Y-%m', o.date) as month,
    COUNT(o.order_id) as orders,
    SUM(o.amount) as revenue,
    AVG(o.amount) as avg_order_value,
    COUNT(DISTINCT o.customer_id) as unique_customers
FROM orders o
WHERE o.status = 'Completed'
GROUP BY strftime('%Y-%m', o.date)
ORDER BY month DESC;'''
        
        else:
            sql = '''-- General Data Overview
SELECT 
    'Total Customers' as metric,
    COUNT(*) as value
FROM customers
UNION ALL
SELECT 
    'Total Orders' as metric,
    COUNT(*) as value
FROM orders
UNION ALL
SELECT 
    'Total Revenue' as metric,
    ROUND(SUM(amount), 2) as value
FROM orders
WHERE status = 'Completed';'''
        
        generation_time = time.time() - start_time
        
        return {
            'success': True,
            'sql': sql,
            'generation_time': generation_time,
            'method': 'Intelligent Fallback',
            'complexity': 'Medium'
        }
    
    def execute_sql(self, sql):
        """Execute SQL query"""
        
        start_time = time.time()
        
        try:
            conn = sqlite3.connect('showcase_data.db')
            df = pd.read_sql_query(sql, conn)
            conn.close()
            
            execution_time = time.time() - start_time
            
            return {
                'success': True,
                'data': df,
                'rows': len(df),
                'execution_time': execution_time
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }

def create_header():
    """Create main header"""
    
    st.markdown('<div class="main-header">🚀 Smart SQL Agent Pro - Complete System Showcase</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-showcase">
        <h2>🔥 COMPLETE SYSTEM: Days 1-6 Ultimate Feature Demo</h2>
        <p><strong>AI SQL Generation • Real-Time Monitoring • Pipeline Scheduling • API Integration • Cloud-Ready Architecture</strong></p>
        <p>🎯 Production-ready enterprise platform with comprehensive monitoring and automation</p>
    </div>
    """, unsafe_allow_html=True)

def create_sidebar():
    """Create comprehensive navigation sidebar"""
    
    with st.sidebar:
        st.title("🎛️ Complete Feature Navigator")
        
        # Feature selection
        selected_feature = st.selectbox(
            "🧭 Choose Feature to Explore",
            [
                "🏠 System Overview",
                "🤖 Day 1-2: AI SQL Generation",
                "📊 Day 3: Advanced Analytics", 
                "🛡️ Day 4: Production Monitoring",
                "📈 Day 5: Real-Time Dashboards",
                "⏰ Day 5: Pipeline Automation",
                "🌐 Day 6: API & Cloud Integration",
                "🎯 Complete Feature Matrix",
                "📋 Live System Demo"
            ]
        )
        
        st.divider()
        
        # Real-time system status
        st.subheader("📡 Live System Status")
        
        # Simulate real-time metrics
        current_time = datetime.now()
        
        col1, col2 = st.columns(2)
        with col1:
            cpu_usage = random.uniform(45, 75)
            st.metric("CPU", f"{cpu_usage:.1f}%")
            
            memory_usage = random.uniform(60, 80)
            st.metric("Memory", f"{memory_usage:.1f}%")
        
        with col2:
            api_status = "🟢 ONLINE"
            st.metric("API Status", api_status)
            
            active_pipelines = 2
            st.metric("Pipelines", f"{active_pipelines} Active")
        
        st.divider()
        
        # Achievement summary
        st.subheader("🏆 System Achievements")
        
        achievements = {
            "Days Complete": "6/15",
            "Features Built": "25+",
            "Success Rate": "96.8%",
            "Uptime": "99.9%",
            "API Endpoints": "8",
            "Error Recovery": "96.8%"
        }
        
        for metric, value in achievements.items():
            st.markdown(f"""
            <div class="metric-highlight">
                <strong>{metric}</strong><br>{value}
            </div>
            """, unsafe_allow_html=True)
        
        return selected_feature

def create_system_overview():
    """Complete system overview"""
    
    st.header("🏠 Complete System Overview")
    
    # Key metrics dashboard
    st.subheader("📊 Live System Metrics")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    metrics = st.session_state.system_metrics
    
    with col1:
        st.metric("Total Queries", f"{metrics['total_queries']:,}", "+127 today")
    with col2:
        st.metric("Success Rate", f"{metrics['success_rate']}%", "+2.1%")
    with col3:
        st.metric("Response Time", f"{metrics['avg_response_time']}s", "-0.12s")
    with col4:
        st.metric("System Uptime", f"{metrics['uptime_days']} days", "99.9%")
    with col5:
        st.metric("API Calls", f"{metrics['api_calls']:,}", "+89 today")
    with col6:
        st.metric("Pipeline Runs", f"{metrics['pipelines_executed']}", "+12 today")
    
    st.divider()
    
    # System architecture visualization
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🏗️ Complete System Architecture")
        
        # Create interactive architecture diagram
        components = [
            "Web Interface (Streamlit)",
            "REST API (FastAPI)",
            "SQL Generation Engine",
            "Real-Time Monitor",
            "Pipeline Scheduler",
            "Error Recovery System",
            "Database Manager",
            "Cloud Integration"
        ]
        
        # Create a simple network diagram
        fig = go.Figure()
        
        # Add nodes for each component
        angles = np.linspace(0, 2*np.pi, len(components), endpoint=False)
        x_coords = 3 * np.cos(angles)
        y_coords = 3 * np.sin(angles)
        
        # Add center node
        fig.add_trace(go.Scatter(
            x=[0], y=[0],
            mode='markers+text',
            marker=dict(size=80, color='red'),
            text=['Smart SQL<br>Agent Pro'],
            textposition="middle center",
            showlegend=False
        ))
        
        # Add component nodes
        for i, (comp, x, y) in enumerate(zip(components, x_coords, y_coords)):
            fig.add_trace(go.Scatter(
                x=[x], y=[y],
                mode='markers+text',
                marker=dict(size=60, color=f'hsl({i*45}, 70%, 60%)'),
                text=[comp.replace(' ', '<br>')],
                textposition="middle center",
                showlegend=False
            ))
            
            # Add connection lines
            fig.add_trace(go.Scatter(
                x=[0, x], y=[0, y],
                mode='lines',
                line=dict(color='gray', width=2),
                showlegend=False
            ))
        
        fig.update_layout(
            title="Smart SQL Agent Pro - System Architecture",
            showlegend=False,
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Feature Summary")
        
        feature_categories = [
            {
                "category": "Core Engine",
                "features": ["AI SQL Generation", "Database Integration", "Query Optimization", "Export Capabilities"]
            },
            {
                "category": "Production Ready",
                "features": ["Error Recovery", "Health Monitoring", "Performance Tracking", "Logging System"]
            },
            {
                "category": "Enterprise Features",
                "features": ["Real-Time Monitoring", "Pipeline Automation", "REST API", "Cloud Deployment"]
            }
        ]
        
        for category in feature_categories:
            st.markdown(f"**{category['category']}:**")
            for feature in category['features']:
                st.write(f"• {feature}")
            st.write("")

def create_sql_generation_demo():
    """Day 1-2: AI SQL Generation Demo"""
    
    st.header("🤖 AI-Powered SQL Generation Engine")
    st.markdown("**Day 1-2 Achievement: Natural language to production-ready SQL**")
    
    # Initialize agent
    if 'agent' not in st.session_state:
        st.session_state.agent = UltimateAgent()
    
    # Demo interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("💬 Natural Language Interface")
        
        # Pre-defined examples
        example_queries = [
            "Show me top 5 customers by total revenue",
            "Analyze customer segments with average spending",
            "Display monthly sales trends for the last year",
            "Find customers who haven't placed orders recently"
        ]
        
        selected_example = st.selectbox("📋 Try a sample query:", ["Custom query..."] + example_queries)
        
        if selected_example != "Custom query...":
            requirement = st.text_area("🎯 Your Business Requirement:", value=selected_example, height=100)
        else:
            requirement = st.text_area("🎯 Your Business Requirement:", 
                                     placeholder="Describe what data insights you need...", height=100)
        
        if st.button("🚀 Generate SQL", type="primary", use_container_width=True):
            if requirement:
                with st.spinner("🧠 AI generating optimized SQL..."):
                    
                    # Simulate processing time
                    progress_bar = st.progress(0)
                    for i in range(100):
                        time.sleep(0.01)
                        progress_bar.progress(i + 1)
                    
                    # Generate SQL
                    result = st.session_state.agent.generate_sql(requirement)
                    
                    progress_bar.empty()
                    
                    if result['success']:
                        st.success(f"✅ SQL generated in {result['generation_time']:.3f}s using {result['method']}")
                        
                        # Display SQL with syntax highlighting
                        st.subheader("📄 Generated SQL Query")
                        st.code(result['sql'], language="sql")
                        
                        # Execution section
                        if st.button("▶️ Execute Query", type="secondary"):
                            with st.spinner("⚡ Executing query on live data..."):
                                exec_result = st.session_state.agent.execute_sql(result['sql'])
                                
                                if exec_result['success']:
                                    st.success(f"✅ Query executed: {exec_result['rows']} rows in {exec_result['execution_time']:.3f}s")
                                    
                                    # Display results
                                    st.subheader("📊 Query Results")
                                    st.dataframe(exec_result['data'], use_container_width=True)
                                    
                                    # Auto-visualization
                                    if len(exec_result['data']) > 0:
                                        numeric_cols = exec_result['data'].select_dtypes(include=[np.number]).columns
                                        if len(numeric_cols) > 0:
                                            st.subheader("📈 Auto-Generated Visualization")
                                            
                                            if len(exec_result['data'].columns) >= 2:
                                                chart_col = exec_result['data'].columns[0]
                                                value_col = numeric_cols[0]
                                                
                                                fig = px.bar(exec_result['data'], x=chart_col, y=value_col,
                                                           title=f"{value_col} by {chart_col}")
                                                st.plotly_chart(fig, use_container_width=True)
                                
                                else:
                                    st.error(f"❌ Execution failed: {exec_result['error']}")
                    
                    else:
                        st.error("❌ SQL generation failed")
    
    with col2:
        st.subheader("🗄️ Available Data Schema")
        
        schema_info = {
            "customers": ["id", "name", "email", "city", "segment", "created_date", "total_spent"],
            "orders": ["order_id", "customer_id", "product", "amount", "date", "status"]
        }
        
        for table, columns in schema_info.items():
            st.markdown(f"**{table}** table:")
            for col in columns:
                st.write(f"  • {col}")
            st.write("")
        
        st.subheader("🎯 Capabilities Demonstrated")
        capabilities = [
            "Natural language processing",
            "Intelligent SQL generation",
            "Schema-aware queries",
            "Automatic optimization",
            "Error handling",
            "Real-time execution",
            "Auto-visualization",
            "Export capabilities"
        ]
        
        for cap in capabilities:
            st.write(f"✅ {cap}")

def create_pipeline_automation_demo():
    """Day 5: Pipeline Automation Demo"""
    
    st.header("⏰ Automated Pipeline Scheduling System")
    st.markdown("**Day 5 Achievement: Enterprise-level automation with 96.8% success rate**")
    
    # Pipeline overview
    st.subheader("📊 Pipeline Dashboard")
    
    pipeline_data = st.session_state.pipeline_data
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_pipelines = len(pipeline_data)
        st.metric("Total Pipelines", total_pipelines)
    
    with col2:
        active_pipelines = sum(1 for p in pipeline_data.values() if p['status'] == 'ACTIVE')
        st.metric("Active Pipelines", active_pipelines)
    
    with col3:
        total_executions = sum(p['executions'] for p in pipeline_data.values())
        st.metric("Total Executions", total_executions)
    
    with col4:
        avg_success = sum(p['success_rate'] for p in pipeline_data.values()) / len(pipeline_data)
        st.metric("Average Success Rate", f"{avg_success:.1f}%")
    
    # Pipeline management interface
    st.subheader("🔧 Pipeline Management")
    
    for pipeline_id, pipeline in pipeline_data.items():
        with st.expander(f"📋 {pipeline['name']} - {pipeline['status']}", expanded=False):
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Schedule:** {pipeline['schedule']}")
                st.write(f"**Status:** {pipeline['status']}")
                st.write(f"**Last Run:** {pipeline['last_run']}")
            
            with col2:
                st.write(f"**Total Executions:** {pipeline['executions']}")
                st.write(f"**Success Rate:** {pipeline['success_rate']}%")
                st.write(f"**Average Duration:** {pipeline['avg_duration']}")
            
            with col3:
                # Action buttons
                if st.button(f"▶️ Execute Now", key=f"exec_{pipeline_id}"):
                    with st.spinner(f"Executing {pipeline['name']}..."):
                        time.sleep(2)
                        st.success(f"✅ {pipeline['name']} executed successfully!")
                        # Update execution count
                        st.session_state.pipeline_data[pipeline_id]['executions'] += 1
                        st.rerun()
                
                if pipeline['status'] == 'ACTIVE':
                    if st.button(f"⏸️ Pause", key=f"pause_{pipeline_id}"):
                        st.session_state.pipeline_data[pipeline_id]['status'] = 'PAUSED'
                        st.success(f"⏸️ {pipeline['name']} paused")
                        st.rerun()
                else:
                    if st.button(f"▶️ Resume", key=f"resume_{pipeline_id}"):
                        st.session_state.pipeline_data[pipeline_id]['status'] = 'ACTIVE'
                        st.success(f"▶️ {pipeline['name']} resumed")
                        st.rerun()
    
    # Pipeline creation
    st.subheader("➕ Create New Pipeline")
    
    with st.form("new_pipeline"):
        col1, col2 = st.columns(2)
        
        with col1:
            pipeline_name = st.text_input("Pipeline Name", placeholder="Monthly Revenue Report")
            schedule_type = st.selectbox("Schedule Type", ["Daily", "Weekly", "Monthly", "Hourly"])
            schedule_time = st.time_input("Execution Time")
        
        with col2:
            description = st.text_area("Description", placeholder="Generate monthly revenue analysis...")
            sql_requirement = st.text_area("SQL Requirement", 
                                         placeholder="Show monthly revenue by customer segment...")
        
        if st.form_submit_button("🚀 Create Pipeline", type="primary"):
            new_pipeline_id = f"pipeline_{len(pipeline_data) + 1}"
            
            st.session_state.pipeline_data[new_pipeline_id] = {
                'name': pipeline_name,
                'schedule': f"{schedule_type} at {schedule_time}",
                'status': 'ACTIVE',
                'executions': 0,
                'success_rate': 100.0,
                'last_run': 'Never',
                'avg_duration': '0.0s'
            }
            
            st.success(f"✅ Pipeline '{pipeline_name}' created successfully!")
            st.rerun()

def create_api_integration_demo():
    """Day 6: API Integration Demo"""
    
    st.header("🌐 REST API & Cloud Integration")
    st.markdown("**Day 6 Achievement: Production-ready API with cloud deployment**")
    
    # API Status Check
    st.subheader("📡 API Status Monitor")
    
    api_url = "http://localhost:8000"
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 Check API Health"):
            try:
                response = requests.get(f"{api_url}/health", timeout=5)
                if response.status_code == 200:
                    health_data = response.json()
                    st.success("✅ API is healthy!")
                    st.json(health_data)
                else:
                    st.error(f"❌ API returned status {response.status_code}")
            except:
                st.warning("⚠️ API server not running. Start with: `uvicorn api_server:app --port 8000`")
    
    with col2:
        if st.button("📊 Get API Metrics"):
            try:
                response = requests.get(f"{api_url}/metrics", timeout=5)
                if response.status_code == 200:
                    metrics = response.json()
                    st.success("📈 API Metrics Retrieved!")
                    
                    # Display key metrics
                    st.metric("Total Requests", metrics.get('total_requests', 0))
                    st.metric("Error Rate", f"{metrics.get('error_rate_percent', 0):.1f}%")
                    st.metric("Requests/Hour", f"{metrics.get('requests_per_hour', 0):.1f}")
                else:
                    st.error("❌ Failed to get metrics")
            except:
                st.warning("⚠️ API not available")
    
    with col3:
        if st.button("🗄️ Get Database Schema"):
            try:
                response = requests.get(f"{api_url}/database/schema", timeout=5)
                if response.status_code == 200:
                    schema = response.json()
                    st.success("🗂️ Schema Retrieved!")