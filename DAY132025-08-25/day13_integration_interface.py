"""
Day 13 - Enterprise Integration Dashboard Interface
Smart SQL Pipeline Generator - Enterprise Integration UI
Simplified version with better error handling
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime, timedelta
import secrets

# Page configuration
st.set_page_config(
    page_title="Smart SQL - Enterprise Integration",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    
    .integration-status {
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
        text-align: center;
        margin: 0.25rem;
    }
    
    .status-healthy {
        background-color: #d4edda;
        color: #155724;
    }
    
    .status-unhealthy {
        background-color: #f8d7da;
        color: #721c24;
    }
    
    .api-key-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #007bff;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class EnterpriseIntegrationDashboard:
    """Dashboard controller for enterprise integration management"""
    
    def __init__(self):
        self.setup_session_state()
    
    def setup_session_state(self):
        """Initialize session state variables"""
        if 'current_tab' not in st.session_state:
            st.session_state.current_tab = "Overview"

    def render_dashboard(self):
        """Render main dashboard"""
        
        st.title("🔗 Enterprise Integration Platform")
        st.markdown("**Smart SQL Pipeline Generator - Enterprise Integration Dashboard**")
        
        # Sidebar navigation
        self.render_sidebar()
        
        # Main content based on selected tab
        if st.session_state.current_tab == "Overview":
            self.render_overview_tab()
        elif st.session_state.current_tab == "API Keys":
            self.render_api_keys_tab()
        elif st.session_state.current_tab == "Webhooks":
            self.render_webhooks_tab()
        elif st.session_state.current_tab == "Integrations":
            self.render_integrations_tab()
        elif st.session_state.current_tab == "Monitoring":
            self.render_monitoring_tab()

    def render_sidebar(self):
        """Render sidebar navigation"""
        with st.sidebar:
            st.markdown("# 🔗 Smart SQL")
            st.markdown("### Enterprise Integration")
            
            # Tab selection
            tab_options = ["Overview", "API Keys", "Webhooks", "Integrations", "Monitoring"]
            selected_tab = st.selectbox("Navigate to:", tab_options, 
                                      index=tab_options.index(st.session_state.current_tab))
            st.session_state.current_tab = selected_tab
            
            st.divider()
            
            # Quick stats
            st.subheader("📊 Quick Stats")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Active APIs", "12", "↑ 2")
            with col2:
                st.metric("Webhooks", "8", "↑ 1")
            
            col3, col4 = st.columns(2)
            with col3:
                st.metric("Integrations", "5", "→ 0")
            with col4:
                st.metric("Uptime", "99.9%", "↑ 0.1%")

    def render_overview_tab(self):
        """Render overview dashboard"""
        
        # Header metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h3>24</h3>
                <p>Active API Keys</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <h3>15</h3>
                <p>Webhook Endpoints</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <h3>8</h3>
                <p>External Integrations</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div class="metric-card">
                <h3>1.2K</h3>
                <p>API Calls Today</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # Activity overview
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📈 Integration Activity (Last 7 Days)")
            
            # Generate sample data for activity chart
            dates = pd.date_range(start=datetime.now() - timedelta(days=6), end=datetime.now(), freq='D')
            activity_data = {
                'Date': dates,
                'API Calls': [850, 920, 1100, 980, 1200, 1350, 1180],
                'Webhook Triggers': [45, 52, 67, 43, 78, 89, 72]
            }
            
            activity_df = pd.DataFrame(activity_data)
            
            fig = make_subplots(rows=2, cols=1, subplot_titles=('API Usage', 'Webhook Events'))
            
            fig.add_trace(
                go.Scatter(x=activity_df['Date'], y=activity_df['API Calls'], 
                          name='API Calls', line=dict(color='#2E86AB')),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(x=activity_df['Date'], y=activity_df['Webhook Triggers'], 
                          name='Webhook Triggers', line=dict(color='#A23B72')),
                row=2, col=1
            )
            
            fig.update_layout(height=400, showlegend=True)
            fig.update_xaxes(title_text="Date")
            fig.update_yaxes(title_text="Count")
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🔗 Recent Integrations")
            
            recent_integrations = [
                {"name": "Snowflake Prod", "type": "Database", "status": "healthy", "time": "2 hours ago"},
                {"name": "Slack Alerts", "type": "Webhook", "status": "healthy", "time": "5 hours ago"},
                {"name": "Tableau API", "type": "API", "status": "healthy", "time": "1 day ago"},
                {"name": "Apache Kafka", "type": "Streaming", "status": "unknown", "time": "2 days ago"},
            ]
            
            for integration in recent_integrations:
                status_class = f"status-{integration['status']}"
                st.markdown(f"""
                <div style="padding: 0.5rem; border-bottom: 1px solid #eee;">
                    <strong>{integration['name']}</strong><br>
                    <small>{integration['type']}</small>
                    <span class="integration-status {status_class}">{integration['status'].upper()}</span><br>
                    <small style="color: #666;">{integration['time']}</small>
                </div>
                """, unsafe_allow_html=True)

    def render_api_keys_tab(self):
        """Render API Keys management tab"""
        
        st.subheader("🔑 API Key Management")
        
        # Create new API key section
        with st.expander("➕ Create New API Key", expanded=False):
            with st.form("create_api_key_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    key_name = st.text_input("API Key Name", placeholder="e.g., Production Analytics")
                    expires_days = st.selectbox("Expires In", [30, 90, 180, 365, None], 
                                               format_func=lambda x: f"{x} days" if x else "Never")
                
                with col2:
                    rate_limit = st.number_input("Rate Limit (requests/hour)", min_value=100, max_value=10000, value=1000)
                    permissions = st.multiselect("Permissions", 
                                               ["pipeline:read", "pipeline:execute", "webhook:create", 
                                                "webhook:manage", "integration:read", "admin"],
                                               default=["pipeline:read"])
                
                submitted = st.form_submit_button("🚀 Generate API Key", type="primary")
                
                if submitted and key_name:
                    # Generate API key
                    new_api_key = f"sql_{secrets.token_urlsafe(32)}"
                    
                    st.success("✅ API Key Generated Successfully!")
                    
                    st.markdown(f"""
                    <div class="api-key-box">
                        <strong>🔑 Your API Key (Save this securely!):</strong><br>
                        <code>{new_api_key}</code><br><br>
                        <strong>📋 Details:</strong><br>
                        • Name: {key_name}<br>
                        • Rate Limit: {rate_limit:,} requests/hour<br>
                        • Permissions: {', '.join(permissions)}<br>
                        • Expires: {f"{expires_days} days" if expires_days else "Never"}
                    </div>
                    """, unsafe_allow_html=True)
        
        # Existing API keys table
        st.subheader("📋 Active API Keys")
        
        # Mock data for existing API keys
        api_keys_data = {
            "Name": ["Production Analytics", "Dev Environment", "Monitoring Service", "External Partner"],
            "Key ID": ["sql_ak_abc123", "sql_ak_def456", "sql_ak_ghi789", "sql_ak_jkl012"],
            "Created": ["2024-01-15", "2024-01-20", "2024-01-22", "2024-01-25"],
            "Last Used": ["2 hours ago", "5 minutes ago", "1 day ago", "3 days ago"],
            "Rate Limit": ["5,000/hr", "1,000/hr", "2,000/hr", "500/hr"],
            "Usage (24h)": [450, 23, 156, 12],
            "Status": ["Active", "Active", "Active", "Expired"]
        }
        
        df = pd.DataFrame(api_keys_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # API usage analytics
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 API Usage by Key")
            
            usage_data = pd.DataFrame({
                'API Key': ['Production Analytics', 'Dev Environment', 'Monitoring Service', 'External Partner'],
                'Requests': [4500, 230, 1560, 120]
            })
            
            fig = px.bar(usage_data, x='API Key', y='Requests', 
                        title="24 Hour Request Volume",
                        color='Requests',
                        color_continuous_scale='Blues')
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("⏱️ Rate Limit Utilization")
            
            rate_data = pd.DataFrame({
                'API Key': ['Production Analytics', 'Dev Environment', 'Monitoring Service', 'External Partner'],
                'Utilization': [90, 2.3, 7.8, 2.4]
            })
            
            fig = go.Figure(go.Bar(
                x=rate_data['API Key'],
                y=rate_data['Utilization'],
                marker_color=['red' if x > 80 else 'orange' if x > 50 else 'green' for x in rate_data['Utilization']]
            ))
            fig.update_layout(title="Rate Limit Usage (%)", yaxis_title="Utilization %")
            st.plotly_chart(fig, use_container_width=True)

    def render_webhooks_tab(self):
        """Render webhook management tab"""
        
        st.subheader("🔗 Webhook Management")
        
        # Create new webhook section
        with st.expander("➕ Create New Webhook", expanded=False):
            with st.form("create_webhook_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    webhook_url = st.text_input("Webhook URL", placeholder="https://api.example.com/webhooks")
                    webhook_secret = st.text_input("Secret (optional)", type="password", 
                                                 placeholder="Leave empty to auto-generate")
                
                with col2:
                    events = st.multiselect("Events to Subscribe", [
                        "pipeline.started", "pipeline.completed", "pipeline.failed",
                        "integration.connected", "integration.disconnected",
                        "system.alert", "data.quality.warning"
                    ], default=["pipeline.completed"])
                
                submitted = st.form_submit_button("🎯 Create Webhook", type="primary")
                
                if submitted and webhook_url:
                    webhook_id = f"wh_{secrets.token_urlsafe(12)}"
                    generated_secret = webhook_secret or secrets.token_urlsafe(32)
                    
                    st.success("✅ Webhook Created Successfully!")
                    
                    st.markdown(f"""
                    <div class="api-key-box">
                        <strong>🔗 Webhook Details:</strong><br>
                        • ID: <code>{webhook_id}</code><br>
                        • URL: <code>{webhook_url}</code><br>
                        • Secret: <code>{generated_secret}</code><br>
                        • Events: {', '.join(events)}
                    </div>
                    """, unsafe_allow_html=True)
        
        # Active webhooks
        st.subheader("📡 Active Webhooks")
        
        webhooks_data = [
            {
                "id": "wh_analytics_001",
                "url": "https://analytics.company.com/sql-events",
                "events": ["pipeline.completed", "pipeline.failed"],
                "status": "Active",
                "success_rate": 98.5,
                "last_triggered": "5 minutes ago"
            },
            {
                "id": "wh_slack_alerts",
                "url": "https://hooks.slack.com/services/T123/B456/xyz",
                "events": ["system.alert", "pipeline.failed"],
                "status": "Active",
                "success_rate": 100.0,
                "last_triggered": "2 hours ago"
            }
        ]
        
        for webhook in webhooks_data:
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    status_color = "🟢" if webhook["status"] == "Active" else "🔴"
                    st.markdown(f"**{status_color} {webhook['id']}**")
                    st.caption(f"URL: {webhook['url']}")
                    st.caption(f"Events: {', '.join(webhook['events'])}")
                
                with col2:
                    st.metric("Success Rate", f"{webhook['success_rate']:.1f}%")
                    st.caption(f"Last: {webhook['last_triggered']}")
                
                with col3:
                    if st.button("🧪 Test", key=f"test_{webhook['id']}"):
                        st.success("Test webhook sent!")
                
                st.divider()

    def render_integrations_tab(self):
        """Render integrations management tab"""
        
        st.subheader("🔧 System Integrations")
        
        # Mock integration data
        integrations = [
            {
                "name": "PostgreSQL Production",
                "type": "Database",
                "status": "Healthy",
                "response_time": "12ms",
                "uptime": "99.9%"
            },
            {
                "name": "Snowflake Analytics",
                "type": "Database",
                "status": "Healthy",
                "response_time": "45ms",
                "uptime": "99.7%"
            },
            {
                "name": "Tableau Server API",
                "type": "API",
                "status": "Warning",
                "response_time": "250ms",
                "uptime": "98.2%"
            }
        ]
        
        for integration in integrations:
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    status_emoji = {"Healthy": "🟢", "Warning": "🟡", "Down": "🔴"}
                    st.markdown(f"**{status_emoji[integration['status']]} {integration['name']}**")
                    st.caption(f"Type: {integration['type']}")
                
                with col2:
                    st.metric("Response Time", integration['response_time'])
                    st.caption(f"Uptime: {integration['uptime']}")
                
                with col3:
                    if st.button("🔧 Test", key=f"test_int_{integration['name']}"):
                        st.success("Connection test successful!")
                
                st.divider()

    def render_monitoring_tab(self):
        """Render monitoring and analytics tab"""
        
        st.subheader("📊 Integration Monitoring & Analytics")
        
        # Real-time metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Requests", "45.2K", "↑ 12%")
        with col2:
            st.metric("Success Rate", "98.7%", "↑ 0.3%")
        with col3:
            st.metric("Avg Response", "89ms", "↓ 15ms")
        with col4:
            st.metric("Active Connections", "47", "↑ 3")
        
        st.divider()
        
        # Time series monitoring
        st.subheader("📈 System Performance")
        
        # Generate time series data
        times = pd.date_range(start=datetime.now() - timedelta(hours=24), 
                             end=datetime.now(), freq='H')
        
        metrics_data = pd.DataFrame({
            'Time': times,
            'API Requests': [100 + i*5 + (i%4)*20 for i in range(len(times))],
            'Response Time (ms)': [80 + (i%8)*15 for i in range(len(times))],
        })
        
        fig = make_subplots(rows=2, cols=1, subplot_titles=('API Requests per Hour', 'Response Time'))
        
        fig.add_trace(go.Scatter(x=metrics_data['Time'], y=metrics_data['API Requests'],
                               name='API Requests', line=dict(color='#2E86AB')), row=1, col=1)
        fig.add_trace(go.Scatter(x=metrics_data['Time'], y=metrics_data['Response Time (ms)'],
                               name='Response Time', line=dict(color='#A23B72')), row=2, col=1)
        
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # Recent alerts
        st.subheader("🚨 Recent System Events")
        
        alerts = [
            {"type": "Success", "message": "New API key generated successfully", "time": "5 min ago"},
            {"type": "Info", "message": "System health check completed", "time": "1 hour ago"},
            {"type": "Warning", "message": "High API usage detected", "time": "2 hours ago"},
            {"type": "Success", "message": "Webhook delivery successful", "time": "4 hours ago"},
        ]
        
        for alert in alerts:
            emoji = {"Warning": "⚠️", "Info": "ℹ️", "Error": "❌", "Success": "✅"}
            color = {"Warning": "#fff3cd", "Info": "#d1ecf1", "Error": "#f8d7da", "Success": "#d4edda"}
            
            st.markdown(f"""
            <div style="background-color: {color[alert['type']]}; padding: 0.5rem; 
                       border-radius: 5px; margin: 0.5rem 0;">
                {emoji[alert['type']]} <strong>{alert['type']}</strong><br>
                {alert['message']}<br>
                <small>{alert['time']}</small>
            </div>
            """, unsafe_allow_html=True)


# Main application
def main():
    """Main application entry point"""
    
    try:
        dashboard = EnterpriseIntegrationDashboard()
        dashboard.render_dashboard()
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #666; padding: 1rem;'>
            <p><strong>Smart SQL Enterprise Integration Platform</strong> | Day 13 MVP</p>
            <p>🔗 Connect • 🚀 Scale • 📊 Monitor</p>
            <p><em>Demo Mode - All data is simulated for demonstration</em></p>
        </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Dashboard Error: {str(e)}")
        st.info("If you see import errors, try: pip install streamlit plotly pandas")


if __name__ == "__main__":
    main()