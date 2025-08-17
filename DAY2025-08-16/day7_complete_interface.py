# src/day7_complete_interface.py
"""
Day 7 Complete Interface: Multi-User System with Team Collaboration
Combines authentication, team features, and enhanced cloud deployment
"""

import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import time
from datetime import datetime
import sqlite3

# Page configuration
st.set_page_config(
    page_title="Smart SQL Agent Pro - Team Edition",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session state initialization
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_token' not in st.session_state:
    st.session_state.user_token = None
if 'current_user' not in st.session_state:
    st.session_state.current_user = None

API_BASE_URL = "http://localhost:8000"

def make_authenticated_request(endpoint, method="GET", data=None):
    """Make authenticated API request"""
    headers = {}
    if st.session_state.user_token:
        headers["Authorization"] = f"Bearer {st.session_state.user_token}"
    
    try:
        if method == "GET":
            response = requests.get(f"{API_BASE_URL}{endpoint}", headers=headers, timeout=5)
        elif method == "POST":
            response = requests.post(f"{API_BASE_URL}{endpoint}", 
                                   headers={**headers, "Content-Type": "application/json"}, 
                                   json=data, timeout=5)
        return response
    except requests.exceptions.RequestException:
        return None

def login_page():
    """User login interface"""
    st.title("🔐 Smart SQL Agent Pro - Login")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login to Your Account")
        
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Login", type="primary"):
                if username and password:
                    response = make_authenticated_request("/auth/login", "POST", {
                        "username": username,
                        "password": password
                    })
                    
                    if response and response.status_code == 200:
                        token_data = response.json()
                        st.session_state.user_token = token_data["access_token"]
                        st.session_state.current_user = token_data["user"]
                        st.session_state.authenticated = True
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
                else:
                    st.error("Please enter both username and password")
        
        with col2:
            if st.button("Demo Login"):
                # Use demo credentials
                response = make_authenticated_request("/auth/login", "POST", {
                    "username": "admin",
                    "password": "admin123"
                })
                
                if response and response.status_code == 200:
                    token_data = response.json()
                    st.session_state.user_token = token_data["access_token"]
                    st.session_state.current_user = token_data["user"]
                    st.session_state.authenticated = True
                    st.success("Demo login successful!")
                    st.rerun()
    
    with tab2:
        st.subheader("Create New Account")
        
        new_username = st.text_input("Username", key="reg_username")
        new_email = st.text_input("Email", key="reg_email")
        new_password = st.text_input("Password", type="password", key="reg_password")
        role = st.selectbox("Role", ["user", "admin"], key="reg_role")
        
        if st.button("Register"):
            if new_username and new_email and new_password:
                response = make_authenticated_request("/auth/register", "POST", {
                    "username": new_username,
                    "email": new_email,
                    "password": new_password,
                    "role": role
                })
                
                if response and response.status_code == 200:
                    st.success("Registration successful! Please login.")
                else:
                    st.error("Registration failed. Username or email may already exist.")
            else:
                st.error("Please fill all fields")

def dashboard_page():
    """Main dashboard with team collaboration features"""
    st.title("🏠 Smart SQL Agent Pro - Team Dashboard")
    
    # User info sidebar
    with st.sidebar:
        st.subheader(f"Welcome, {st.session_state.current_user['username']}")
        st.write(f"Role: {st.session_state.current_user['role']}")
        st.write(f"Email: {st.session_state.current_user['email']}")
        
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.user_token = None
            st.session_state.current_user = None
            st.rerun()
    
    # Main dashboard tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🤖 SQL Generation", 
        "👥 Team Projects", 
        "📊 Shared Queries", 
        "📈 Analytics", 
        "⚙️ System Admin"
    ])
    
    with tab1:
        render_sql_generation()
    
    with tab2:
        render_team_projects()
    
    with tab3:
        render_shared_queries()
    
    with tab4:
        render_analytics()
    
    with tab5:
        if st.session_state.current_user['role'] == 'admin':
            render_admin_panel()
        else:
            st.info("Admin access required for this section.")

def render_sql_generation():
    """Enhanced SQL generation with team features"""
    st.subheader("AI SQL Generation")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Get user's projects for context
        projects_response = make_authenticated_request("/projects")
        projects = []
        if projects_response and projects_response.status_code == 200:
            projects = projects_response.json()
        
        # Project selection
        project_options = ["None"] + [f"{p['name']} (ID: {p['id']})" for p in projects]
        selected_project = st.selectbox("Project Context", project_options)
        
        # SQL generation form
        requirement = st.text_area(
            "Describe your SQL requirement:",
            placeholder="e.g., Show top 10 customers by revenue for Q4 2024",
            height=100
        )
        
        schema_info = st.text_area(
            "Database schema (optional):",
            placeholder="Table structures, relationships, etc.",
            height=80
        )
        
        if st.button("Generate SQL", type="primary"):
            if requirement:
                project_id = None
                if selected_project != "None":
                    project_id = int(selected_project.split("ID: ")[1].split(")")[0])
                
                with st.spinner("Generating SQL..."):
                    response = make_authenticated_request("/sql/generate", "POST", {
                        "requirement": requirement,
                        "schema_info": schema_info,
                        "project_id": project_id
                    })
                    
                    if response and response.status_code == 200:
                        result = response.json()
                        
                        st.success(f"Generated in {result['generation_time']}s")
                        st.code(result['sql'], language="sql")
                        
                        # Option to share the query
                        with st.expander("Share this query with team"):
                            query_title = st.text_input("Query Title")
                            query_description = st.text_area("Description")
                            tags = st.text_input("Tags (comma separated)")
                            is_public = st.checkbox("Make public")
                            
                            if st.button("Share Query"):
                                if query_title:
                                    share_response = make_authenticated_request("/queries/share", "POST", {
                                        "title": query_title,
                                        "sql_query": result['sql'],
                                        "description": query_description,
                                        "project_id": project_id,
                                        "tags": tags.split(',') if tags else [],
                                        "is_public": is_public
                                    })
                                    
                                    if share_response and share_response.status_code == 200:
                                        st.success("Query shared successfully!")
                                    else:
                                        st.error("Failed to share query")
                    else:
                        st.error("Failed to generate SQL. Make sure API server is running.")
            else:
                st.error("Please enter a requirement")
    
    with col2:
        st.subheader("Quick Stats")
        
        # Get user analytics
        analytics_response = make_authenticated_request("/analytics/user")
        if analytics_response and analytics_response.status_code == 200:
            analytics = analytics_response.json()
            
            st.metric("Queries Shared", analytics.get('queries_shared', 0))
            st.metric("Total Executions", analytics.get('total_executions', 0))
            st.metric("Public Queries", analytics.get('public_queries', 0))
        
        st.subheader("Recent Activity")
        if 'recent_activity' in locals() and analytics.get('recent_activity'):
            for activity in analytics['recent_activity'][:3]:
                st.write(f"**{activity['title']}**")
                st.caption(f"Executions: {activity['executions']}")

def render_team_projects():
    """Team project management"""
    st.subheader("Team Projects")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Create new project
        with st.expander("Create New Project"):
            project_name = st.text_input("Project Name")
            project_description = st.text_area("Description")
            
            if st.button("Create Project"):
                if project_name:
                    response = make_authenticated_request("/projects", "POST", {
                        "name": project_name,
                        "description": project_description,
                        "team_members": []
                    })
                    
                    if response and response.status_code == 200:
                        st.success("Project created successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to create project")
        
        # Display projects
        projects_response = make_authenticated_request("/projects")
        if projects_response and projects_response.status_code == 200:
            projects = projects_response.json()
            
            for project in projects:
                with st.container():
                    st.markdown(f"### {project['name']}")
                    st.write(project['description'])
                    
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.write(f"Owner ID: {project['owner_id']}")
                    with col_b:
                        st.write(f"Members: {len(project.get('team_members', []))}")
                    with col_c:
                        st.write(f"Status: {project['status']}")
                    
                    st.divider()
    
    with col2:
        st.subheader("Project Summary")
        if 'projects' in locals():
            st.metric("Total Projects", len(projects))
            st.metric("Your Projects", len([p for p in projects if p['owner_id'] == st.session_state.current_user['id']]))

def render_shared_queries():
    """Shared queries management"""
    st.subheader("Shared SQL Queries")
    
    # Get shared queries
    queries_response = make_authenticated_request("/queries/shared")
    if queries_response and queries_response.status_code == 200:
        queries = queries_response.json()
        
        for query in queries:
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**{query['title']}**")
                    st.write(query['description'])
                    
                    # Show SQL preview
                    preview = query['sql_query'][:200] + "..." if len(query['sql_query']) > 200 else query['sql_query']
                    st.code(preview, language="sql")
                    
                    # Tags
                    if query.get('tags'):
                        st.write("Tags: " + ", ".join(query['tags']))
                
                with col2:
                    st.metric("Executions", query['execution_count'])
                    st.write(f"Public: {'Yes' if query['is_public'] else 'No'}")
                    
                    if st.button(f"View Comments", key=f"comments_{query['id']}"):
                        st.session_state[f'show_comments_{query["id"]}'] = True
                
                # Comments section
                if st.session_state.get(f'show_comments_{query["id"]}', False):
                    comments_response = make_authenticated_request(f"/queries/{query['id']}/comments")
                    if comments_response and comments_response.status_code == 200:
                        comments = comments_response.json()
                        
                        st.markdown("**Comments:**")
                        for comment in comments:
                            st.write(f"**{comment['username']}**: {comment['content']}")
                            st.caption(comment['created_at'])
                        
                        # Add new comment
                        new_comment = st.text_input(f"Add comment", key=f"comment_{query['id']}")
                        if st.button(f"Post Comment", key=f"post_{query['id']}") and new_comment:
                            comment_response = make_authenticated_request(
                                f"/queries/{query['id']}/comments", 
                                "POST", 
                                {"content": new_comment, "query_id": query['id']}
                            )
                            if comment_response and comment_response.status_code == 200:
                                st.success("Comment added!")
                                st.rerun()
                
                st.divider()

def render_analytics():
    """Team analytics dashboard"""
    st.subheader("Team Analytics")
    
    # Get team analytics
    analytics_response = make_authenticated_request("/analytics/team")
    if analytics_response and analytics_response.status_code == 200:
        analytics = analytics_response.json()
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Queries", analytics.get('total_queries', 0))
        with col2:
            st.metric("Total Executions", analytics.get('total_executions', 0))
        with col3:
            st.metric("Avg Executions", analytics.get('avg_executions', 0))
        with col4:
            st.metric("Contributors", len(analytics.get('top_contributors', [])))
        
        # Top contributors
        if analytics.get('top_contributors'):
            st.subheader("Top Contributors")
            contrib_df = pd.DataFrame(analytics['top_contributors'])
            fig = px.bar(contrib_df, x='username', y='queries', 
                        title="Queries Created by User")
            st.plotly_chart(fig, use_container_width=True)
        
        # Recent activity
        if analytics.get('recent_activity'):
            st.subheader("Recent Activity")
            activity_df = pd.DataFrame(analytics['recent_activity'])
            st.dataframe(activity_df, use_container_width=True)

def render_admin_panel():
    """System administration panel"""
    st.subheader("System Administration")
    
    # System health
    health_response = make_authenticated_request("/health")
    if health_response and health_response.status_code == 200:
        health = health_response.json()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("System Status", health['status'].title())
        with col2:
            st.metric("Uptime", health['metrics']['uptime_formatted'])
        with col3:
            st.metric("Success Rate", f"{health['metrics']['success_rate']}%")
    
    # Detailed metrics
    metrics_response = make_authenticated_request("/metrics")
    if metrics_response and metrics_response.status_code == 200:
        metrics = metrics_response.json()
        
        st.subheader("System Metrics")
        
        # System metrics
        system_metrics = metrics.get('system', {})
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Request Statistics:**")
            st.write(f"Total Requests: {system_metrics.get('total_requests', 0)}")
            st.write(f"Successful: {system_metrics.get('successful_requests', 0)}")
            st.write(f"Failed: {system_metrics.get('failed_requests', 0)}")
        
        with col2:
            st.write("**User Statistics:**")
            user_metrics = metrics.get('users', {})
            st.write(f"Total Users: {user_metrics.get('total_users', 0)}")
            st.write(f"Admin Users: {user_metrics.get('admin_users', 0)}")
            st.write(f"Active Users: {user_metrics.get('active_users', 0)}")
    
    # User management
    st.subheader("User Management")
    users_response = make_authenticated_request("/auth/users")
    if users_response and users_response.status_code == 200:
        users = users_response.json()
        
        # Display users in a table
        user_data = []
        for user in users:
            user_data.append({
                "ID": user['id'],
                "Username": user['username'],
                "Email": user['email'],
                "Role": user['role'],
                "Active": user['is_active'],
                "Created": user.get('created_at', 'N/A')
            })
        
        if user_data:
            st.dataframe(pd.DataFrame(user_data), use_container_width=True)

def main():
    """Main application entry point"""
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
    }
    
    .success-msg {
        background: #d4edda;
        color: #155724;
        padding: 0.75rem;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Check API server availability
    health_response = make_authenticated_request("/health")
    api_available = health_response is not None and health_response.status_code == 200
    
    if not api_available:
        st.error("""
        **API Server Not Available**
        
        Please start the API server first:
        ```
        cd src
        python -m uvicorn enhanced_api_server:app --reload --port 8000
        ```
        """)
        return
    
    # Authentication check
    if not st.session_state.authenticated:
        login_page()
    else:
        dashboard_page()

if __name__ == "__main__":
    main()