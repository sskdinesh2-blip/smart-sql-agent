# src/day10_enterprise_interface.py
"""
Day 10: Enterprise Security Dashboard
Advanced security monitoring, compliance, and integration interface
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

# Import security components
try:
    from day10_security_framework import security_framework, ComplianceFramework, SecurityLevel
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False
    st.warning("Security framework not available. Install cryptography package to enable security features.")

# Page configuration
st.set_page_config(
    page_title="Smart SQL Agent Pro - Enterprise Security",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("🛡️ Smart SQL Agent Pro - Enterprise Security")
    st.markdown("### Advanced Security, Compliance & Enterprise Integration")
    
    # Security status check
    if SECURITY_AVAILABLE:
        st.success("Enterprise Security Framework Active")
    else:
        st.error("Security framework not available - install required dependencies")
        return
    
    # Main navigation
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔐 Security Dashboard",
        "📋 Compliance Center", 
        "🔍 Audit & Monitoring",
        "👥 Access Control",
        "⚠️ Threat Detection"
    ])
    
    with tab1:
        render_security_dashboard()
    
    with tab2:
        render_compliance_center()
    
    with tab3:
        render_audit_monitoring()
    
    with tab4:
        render_access_control()
    
    with tab5:
        render_threat_detection()

def render_security_dashboard():
    """Main security dashboard"""
    st.markdown("# Security Overview")
    
    if SECURITY_AVAILABLE:
        dashboard_data = security_framework.get_security_dashboard()
        
        # Key security metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Security Events (24h)",
                dashboard_data['security_events_24h'],
                delta=None
            )
        
        with col2:
            threat_level = dashboard_data['threat_level']
            threat_color = {
                'minimal': 'green',
                'low': 'blue', 
                'medium': 'orange',
                'high': 'red'
            }.get(threat_level, 'gray')
            
            st.markdown(f"**Threat Level**")
            st.markdown(f"<span style='color: {threat_color}; font-size: 24px; font-weight: bold'>{threat_level.upper()}</span>", 
                       unsafe_allow_html=True)
        
        with col3:
            avg_compliance = sum(dashboard_data['compliance_scores'].values()) / len(dashboard_data['compliance_scores'])
            st.metric(
                "Avg Compliance Score",
                f"{avg_compliance:.1f}%",
                delta=None
            )
        
        with col4:
            st.metric(
                "Critical Alerts",
                dashboard_data['severity_breakdown']['critical'],
                delta=None
            )
        
        # Security event breakdown
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Security Events by Severity")
            
            severity_data = dashboard_data['severity_breakdown']
            if sum(severity_data.values()) > 0:
                fig_severity = px.pie(
                    values=list(severity_data.values()),
                    names=list(severity_data.keys()),
                    title="Event Severity Distribution",
                    color_discrete_map={
                        'low': '#90EE90',
                        'medium': '#FFD700', 
                        'high': '#FFA500',
                        'critical': '#FF4500'
                    }
                )
                st.plotly_chart(fig_severity, use_container_width=True)
            else:
                st.info("No security events in the last 24 hours")
        
        with col2:
            st.markdown("### Compliance Framework Scores")
            
            compliance_df = pd.DataFrame([
                {'Framework': k.upper(), 'Score': v}
                for k, v in dashboard_data['compliance_scores'].items()
            ])
            
            fig_compliance = px.bar(
                compliance_df, 
                x='Framework', 
                y='Score',
                title="Compliance Scores by Framework",
                color='Score',
                color_continuous_scale='RdYlGn'
            )
            fig_compliance.update_layout(yaxis_range=[0, 100])
            st.plotly_chart(fig_compliance, use_container_width=True)
        
        # Recent security activity timeline
        st.markdown("### Recent Security Activity")
        
        # Generate sample security timeline data
        timeline_data = []
        for i in range(10):
            timeline_data.append({
                'Time': datetime.now() - timedelta(hours=i*2),
                'Event': ['Login Success', 'Failed Login', 'Admin Access', 'Query Executed', 'Policy Updated'][i % 5],
                'Severity': ['low', 'medium', 'high', 'low', 'medium'][i % 5],
                'User': f'User{i % 3 + 1}'
            })
        
        timeline_df = pd.DataFrame(timeline_data)
        
        for _, event in timeline_df.iterrows():
            severity_color = {
                'low': '🟢',
                'medium': '🟡', 
                'high': '🔴'
            }.get(event['Severity'], '⚪')
            
            col_a, col_b, col_c = st.columns([1, 3, 1])
            with col_a:
                st.write(event['Time'].strftime("%H:%M"))
            with col_b:
                st.write(f"{severity_color} {event['Event']} - {event['User']}")
            with col_c:
                st.write(event['Severity'].capitalize())

def render_compliance_center():
    """Compliance monitoring and reporting"""
    st.markdown("# Compliance Center")
    
    # Compliance framework selector
    framework_options = ['GDPR', 'SOX', 'HIPAA', 'PCI_DSS', 'ISO27001']
    selected_framework = st.selectbox("Select Compliance Framework", framework_options)
    
    if st.button("Generate Compliance Report", type="primary"):
        if SECURITY_AVAILABLE:
            framework_enum = getattr(ComplianceFramework, selected_framework)
            report = security_framework.generate_compliance_report(framework_enum)
            st.session_state.compliance_report = report
            st.success(f"Compliance report generated for {selected_framework}")
    
    # Display compliance report
    if 'compliance_report' in st.session_state:
        report = st.session_state.compliance_report
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"### {report['framework'].upper()} Compliance Report")
            
            # Overall score
            score = report['compliance_score']
            score_color = 'green' if score >= 90 else 'orange' if score >= 70 else 'red'
            st.markdown(f"**Overall Score:** <span style='color: {score_color}; font-size: 24px; font-weight: bold'>{score:.1f}%</span>", 
                       unsafe_allow_html=True)
            
            # Detailed findings
            st.markdown("### Compliance Findings")
            
            for finding in report['findings']:
                status_icon = "✅" if finding['compliant'] else "❌"
                severity = finding.get('severity', 'info')
                
                with st.expander(f"{status_icon} {finding['rule'].replace('_', ' ').title()}"):
                    st.write(f"**Required:** {finding['required']}")
                    st.write(f"**Status:** {'Compliant' if finding['compliant'] else 'Non-compliant'}")
                    st.write(f"**Details:** {finding['details']}")
                    if not finding['compliant']:
                        st.error(f"Severity: {severity}")
            
            # Recommendations
            st.markdown("### Recommendations")
            for i, rec in enumerate(report['recommendations'], 1):
                st.write(f"{i}. {rec}")
        
        with col2:
            st.markdown("### Compliance Summary")
            
            st.metric("Total Checks", report['total_checks'])
            st.metric("Passed", report['passed_checks'])
            st.metric("Failed", report['total_checks'] - report['passed_checks'])
            
            # Compliance trend (mock data)
            st.markdown("### Compliance Trend")
            
            dates = pd.date_range(start=datetime.now() - timedelta(days=30), periods=7, freq='5D')
            scores = [85, 87, 89, 92, 94, 93, score]
            
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(x=dates, y=scores, mode='lines+markers', name='Compliance Score'))
            fig_trend.update_layout(title="30-Day Compliance Trend", yaxis_range=[0, 100])
            st.plotly_chart(fig_trend, use_container_width=True)

def render_audit_monitoring():
    """Audit trail and monitoring interface"""
    st.markdown("# Audit & Monitoring")
    
    # Time range selector
    time_range = st.selectbox("Time Range", ["Last Hour", "Last 24 Hours", "Last 7 Days", "Last 30 Days"])
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Audit Trail")
        
        # Generate sample audit data
        audit_data = []
        hours = {'Last Hour': 1, 'Last 24 Hours': 24, 'Last 7 Days': 168, 'Last 30 Days': 720}[time_range]
        
        for i in range(min(50, hours)):
            audit_data.append({
                'Timestamp': datetime.now() - timedelta(hours=i),
                'User': f'user{i % 5 + 1}',
                'Action': ['Login', 'Query Execute', 'Data Export', 'Admin Access', 'Password Change'][i % 5],
                'Resource': ['/api/login', '/api/sql/generate', '/api/export', '/api/admin', '/api/profile'][i % 5],
                'IP Address': f'192.168.1.{100 + i % 50}',
                'Status': ['Success', 'Failed'][i % 10 == 0]  # 10% failure rate
            })
        
        audit_df = pd.DataFrame(audit_data)
        
        # Filter and display
        status_filter = st.selectbox("Filter by Status", ["All", "Success", "Failed"])
        if status_filter != "All":
            audit_df = audit_df[audit_df['Status'] == status_filter]
        
        st.dataframe(audit_df, use_container_width=True)
        
        # Export option
        if st.button("Export Audit Log"):
            csv = audit_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with col2:
        st.markdown("### Monitoring Alerts")
        
        # Active alerts
        alerts = [
            {"time": "2 min ago", "alert": "Multiple failed logins detected", "severity": "high"},
            {"time": "15 min ago", "alert": "Large data export by user3", "severity": "medium"},
            {"time": "1 hour ago", "alert": "Admin access from new IP", "severity": "medium"},
            {"time": "3 hours ago", "alert": "Unusual query pattern detected", "severity": "low"}
        ]
        
        for alert in alerts:
            severity_color = {
                'low': 'green',
                'medium': 'orange', 
                'high': 'red'
            }[alert['severity']]
            
            st.markdown(f"**{alert['time']}**")
            st.markdown(f"<span style='color: {severity_color}'>{alert['alert']}</span>", 
                       unsafe_allow_html=True)
            st.markdown("---")
        
        # Monitoring statistics
        st.markdown("### Statistics")
        
        stats_data = audit_df.groupby('Action').size().reset_index(name='Count')
        fig_stats = px.bar(stats_data, x='Action', y='Count', title="Actions by Type")
        st.plotly_chart(fig_stats, use_container_width=True)

def render_access_control():
    """Access control and policy management"""
    st.markdown("# Access Control")
    
    tab1, tab2, tab3 = st.tabs(["User Permissions", "Access Policies", "Role Management"])
    
    with tab1:
        st.markdown("### User Permissions")
        
        # Sample user data
        users_data = [
            {"User": "alice", "Role": "admin", "Last Login": "2024-08-20 14:30", "Status": "Active"},
            {"User": "bob", "Role": "user", "Last Login": "2024-08-20 12:15", "Status": "Active"},
            {"User": "charlie", "Role": "analyst", "Last Login": "2024-08-19 16:45", "Status": "Active"},
            {"User": "diana", "Role": "user", "Last Login": "2024-08-18 09:20", "Status": "Inactive"},
        ]
        
        users_df = pd.DataFrame(users_data)
        
        # Display users with edit capability
        for _, user in users_df.iterrows():
            col1, col2, col3, col4, col5 = st.columns([2, 1, 2, 1, 1])
            
            with col1:
                st.write(f"**{user['User']}**")
            with col2:
                st.write(user['Role'])
            with col3:
                st.write(user['Last Login'])
            with col4:
                status_color = 'green' if user['Status'] == 'Active' else 'red'
                st.markdown(f"<span style='color: {status_color}'>{user['Status']}</span>", 
                           unsafe_allow_html=True)
            with col5:
                if st.button("Edit", key=f"edit_{user['User']}"):
                    st.info(f"Edit user {user['User']}")
    
    with tab2:
        st.markdown("### Access Policies")
        
        # Display current policies
        policies_data = [
            {"Resource": "/api/admin/*", "Required Roles": "admin", "Operations": "GET,POST,PUT,DELETE", "MFA": "Required"},
            {"Resource": "/api/sql/generate", "Required Roles": "user,admin", "Operations": "POST", "MFA": "Optional"},
            {"Resource": "/api/reports/*", "Required Roles": "analyst,admin", "Operations": "GET", "MFA": "Required"},
        ]
        
        policies_df = pd.DataFrame(policies_data)
        st.dataframe(policies_df, use_container_width=True)
        
        # Add new policy
        with st.expander("Add New Policy"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_resource = st.text_input("Resource Pattern")
                new_roles = st.text_input("Required Roles (comma separated)")
            
            with col2:
                new_operations = st.multiselect("Allowed Operations", ["GET", "POST", "PUT", "DELETE"])
                mfa_required = st.checkbox("Require MFA")
            
            if st.button("Add Policy"):
                st.success("Policy added successfully!")
    
    with tab3:
        st.markdown("### Role Management")
        
        # Role definitions
        roles_data = [
            {"Role": "admin", "Description": "Full system access", "Users": 1, "Permissions": "All"},
            {"Role": "user", "Description": "Standard user access", "Users": 2, "Permissions": "SQL Generation, Reports"},
            {"Role": "analyst", "Description": "Data analysis access", "Users": 1, "Permissions": "Reports, Analytics"},
            {"Role": "viewer", "Description": "Read-only access", "Users": 0, "Permissions": "View Only"},
        ]
        
        for role in roles_data:
            with st.container():
                col1, col2, col3, col4 = st.columns([1, 2, 1, 2])
                
                with col1:
                    st.markdown(f"**{role['Role']}**")
                with col2:
                    st.write(role['Description'])
                with col3:
                    st.metric("Users", role['Users'])
                with col4:
                    st.write(role['Permissions'])
                
                st.markdown("---")

def render_threat_detection():
    """Threat detection and response"""
    st.markdown("# Threat Detection")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Active Threats")
        
        # Sample threat data
        threats = [
            {
                "time": "5 min ago",
                "type": "Brute Force Attack",
                "source": "192.168.1.150", 
                "target": "User: bob",
                "severity": "high",
                "status": "Active"
            },
            {
                "time": "2 hours ago",
                "type": "SQL Injection Attempt",
                "source": "10.0.0.45",
                "target": "/api/sql/generate",
                "severity": "critical", 
                "status": "Blocked"
            },
            {
                "time": "1 day ago",
                "type": "Privilege Escalation",
                "source": "192.168.1.200",
                "target": "User: charlie",
                "severity": "medium",
                "status": "Resolved"
            }
        ]
        
        for threat in threats:
            severity_colors = {
                'low': 'green',
                'medium': 'orange',
                'high': 'red', 
                'critical': 'darkred'
            }
            
            status_colors = {
                'Active': 'red',
                'Blocked': 'orange',
                'Resolved': 'green'
            }
            
            with st.container():
                col_a, col_b, col_c = st.columns([2, 1, 1])
                
                with col_a:
                    st.markdown(f"**{threat['type']}**")
                    st.write(f"Source: {threat['source']}")
                    st.write(f"Target: {threat['target']}")
                    st.caption(threat['time'])
                
                with col_b:
                    severity_color = severity_colors[threat['severity']]
                    st.markdown(f"<span style='color: {severity_color}; font-weight: bold'>{threat['severity'].upper()}</span>", 
                               unsafe_allow_html=True)
                
                with col_c:
                    status_color = status_colors[threat['status']]
                    st.markdown(f"<span style='color: {status_color}; font-weight: bold'>{threat['status']}</span>", 
                               unsafe_allow_html=True)
                
                # Action buttons
                if threat['status'] == 'Active':
                    col_x, col_y = st.columns(2)
                    with col_x:
                        if st.button("Block", key=f"block_{threat['time']}"):
                            st.success("Threat blocked!")
                    with col_y:
                        if st.button("Investigate", key=f"investigate_{threat['time']}"):
                            st.info("Investigation started")
                
                st.markdown("---")
    
    with col2:
        st.markdown("### Threat Intelligence")
        
        # Threat statistics
        threat_stats = {
            'Blocked Today': 15,
            'Active Threats': 2,
            'False Positives': 3,
            'Avg Response Time': '2.3 min'
        }
        
        for stat_name, stat_value in threat_stats.items():
            st.metric(stat_name, stat_value)
        
        st.markdown("### Detection Rules")
        
        rules = [
            "Brute Force Detection: 5 failed logins in 15 min",
            "SQL Injection: Pattern matching on suspicious keywords",
            "Data Exfiltration: Large volume downloads (>100MB)",
            "Privilege Escalation: Unusual role changes"
        ]
        
        for rule in rules:
            st.write(f"• {rule}")
        
        st.markdown("### Response Actions")
        
        actions = [
            "Automatic IP blocking",
            "User account lockout", 
            "Alert security team",
            "Log detailed forensics"
        ]
        
        for action in actions:
            st.write(f"✓ {action}")

if __name__ == "__main__":
    main()