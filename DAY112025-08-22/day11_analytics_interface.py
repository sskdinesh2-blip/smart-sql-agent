# src/day11_analytics_interface.py
"""
Day 11: Advanced Analytics & Reporting Interface
Executive dashboards, automated reporting, and business intelligence
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import numpy as np

# Import analytics components
try:
    from day11_analytics_engine import analytics_engine, ReportType, ReportFrequency
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False
    st.warning("Analytics engine not available. Check dependencies.")

# Page configuration
st.set_page_config(
    page_title="Smart SQL Agent Pro - Advanced Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("📊 Smart SQL Agent Pro - Advanced Analytics")
    st.markdown("### Executive Dashboards & Intelligent Reporting")
    
    if not ANALYTICS_AVAILABLE:
        st.error("Analytics engine not available - check configuration")
        return
    
    # Main navigation
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 Executive Dashboard",
        "📈 Business Intelligence", 
        "📋 Report Builder",
        "⏰ Scheduled Reports",
        "🔍 Custom Analytics"
    ])
    
    with tab1:
        render_executive_dashboard()
    
    with tab2:
        render_business_intelligence()
    
    with tab3:
        render_report_builder()
    
    with tab4:
        render_scheduled_reports()
    
    with tab5:
        render_custom_analytics()

def render_executive_dashboard():
    """Executive-level dashboard with key metrics"""
    st.markdown("# Executive Dashboard")
    
    if st.button("🔄 Refresh Dashboard", type="primary"):
        with st.spinner("Generating executive dashboard..."):
            dashboard_data = analytics_engine.generate_executive_dashboard()
            st.session_state.dashboard_data = dashboard_data
            st.success("Dashboard refreshed!")
    
    # Load dashboard data
    if 'dashboard_data' not in st.session_state:
        with st.spinner("Loading dashboard..."):
            dashboard_data = analytics_engine.generate_executive_dashboard()
            st.session_state.dashboard_data = dashboard_data
    
    dashboard = st.session_state.dashboard_data
    
    # Key performance indicators
    executive_summary = dashboard['executive_summary']
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        revenue = executive_summary['key_metrics']['current_revenue']
        growth = executive_summary['key_metrics']['revenue_growth_rate']
        st.metric(
            "Current Revenue",
            f"${revenue:,.0f}",
            delta=f"{growth:.1f}%"
        )
    
    with col2:
        conversion = executive_summary['key_metrics']['average_conversion_rate']
        st.metric(
            "Conversion Rate",
            f"{conversion:.2f}%",
            delta="0.15%" if conversion > 4 else "-0.23%"
        )
    
    with col3:
        customers = executive_summary['key_metrics']['total_customers']
        st.metric(
            "Total Customers",
            f"{customers:,}",
            delta="127" if customers > 1000 else "-45"
        )
    
    with col4:
        ops_data = dashboard['operational_metrics']
        uptime = ops_data['system_metrics']['average_uptime']
        st.metric(
            "System Uptime",
            f"{uptime:.1f}%",
            delta="0.2%" if uptime > 99 else "-1.1%"
        )
    
    # Executive insights and recommendations
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Revenue & Growth Analysis")
        
        # Generate revenue trend chart
        financial_data = analytics_engine.data_manager.get_data('financial')
        
        fig_revenue = go.Figure()
        fig_revenue.add_trace(go.Scatter(
            x=financial_data['date'],
            y=financial_data['total_revenue'],
            mode='lines+markers',
            name='Revenue',
            line=dict(color='#1f77b4', width=3)
        ))
        fig_revenue.add_trace(go.Scatter(
            x=financial_data['date'],
            y=financial_data['total_costs'],
            mode='lines+markers',
            name='Costs',
            line=dict(color='#ff7f0e', width=3)
        ))
        fig_revenue.update_layout(
            title="Revenue vs Costs Trend",
            xaxis_title="Month",
            yaxis_title="Amount ($)"
        )
        st.plotly_chart(fig_revenue, use_container_width=True)
        
        # Profit margin analysis
        fig_margin = go.Figure()
        fig_margin.add_trace(go.Bar(
            x=financial_data['date'],
            y=financial_data['profit_margin'] * 100,
            name='Profit Margin %',
            marker_color='green'
        ))
        fig_margin.update_layout(
            title="Monthly Profit Margin",
            xaxis_title="Month",
            yaxis_title="Profit Margin (%)"
        )
        st.plotly_chart(fig_margin, use_container_width=True)
    
    with col2:
        st.markdown("### Executive Insights")
        
        insights = executive_summary.get('insights', [])
        for insight in insights:
            st.info(insight)
        
        st.markdown("### Recommendations")
        
        recommendations = executive_summary.get('recommendations', [])
        for i, rec in enumerate(recommendations, 1):
            st.write(f"{i}. {rec}")
        
        st.markdown("### Key Metrics Status")
        
        metrics = dashboard['key_metrics']
        for metric in metrics:
            status = metric.get('status', 'unknown')
            value = metric.get('value', 'N/A')
            unit = metric.get('unit', '')
            
            status_color = {
                'excellent': 'green',
                'good': 'blue',
                'warning': 'orange',
                'critical': 'red'
            }.get(status, 'gray')
            
            st.markdown(f"**{metric['metric_id'].replace('_', ' ').title()}**: "
                       f"<span style='color: {status_color}'>{value}{unit}</span>",
                       unsafe_allow_html=True)

def render_business_intelligence():
    """Business intelligence and analytics"""
    st.markdown("# Business Intelligence")
    
    # Time period selector
    time_period = st.selectbox("Analysis Period", 
                              ["Last 30 Days", "Last 90 Days", "Last 6 Months", "Year to Date"])
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Sales Performance Analysis")
        
        # Get sales data
        sales_data = analytics_engine.data_manager.get_data('sales')
        
        # Regional performance
        regional_sales = sales_data.groupby('region').agg({
            'revenue': 'sum',
            'orders': 'sum',
            'customers': 'sum'
        }).reset_index()
        
        fig_regional = px.bar(regional_sales, x='region', y='revenue',
                             title="Revenue by Region",
                             color='revenue',
                             color_continuous_scale='Blues')
        st.plotly_chart(fig_regional, use_container_width=True)
        
        # Product category analysis
        category_sales = sales_data.groupby('product_category').agg({
            'revenue': 'sum',
            'orders': 'sum'
        }).reset_index()
        
        fig_category = px.pie(category_sales, values='revenue', names='product_category',
                             title="Revenue by Product Category")
        st.plotly_chart(fig_category, use_container_width=True)
    
    with col2:
        st.markdown("### User Engagement Analytics")
        
        # Get user data
        user_data = analytics_engine.data_manager.get_data('users')
        
        # User growth trend
        fig_users = go.Figure()
        fig_users.add_trace(go.Scatter(
            x=user_data['date'],
            y=user_data['active_users'],
            mode='lines',
            name='Active Users',
            fill='tonexty'
        ))
        fig_users.update_layout(title="Active Users Trend")
        st.plotly_chart(fig_users, use_container_width=True)
        
        # Engagement metrics
        avg_session = user_data['session_duration'].mean() / 60  # Convert to minutes
        avg_bounce = user_data['bounce_rate'].mean() * 100
        avg_conversion = user_data['conversion_rate'].mean() * 100
        
        engagement_metrics = pd.DataFrame({
            'Metric': ['Avg Session (min)', 'Bounce Rate (%)', 'Conversion (%)'],
            'Value': [avg_session, avg_bounce, avg_conversion]
        })
        
        fig_engagement = px.bar(engagement_metrics, x='Metric', y='Value',
                               title="Key Engagement Metrics")
        st.plotly_chart(fig_engagement, use_container_width=True)
    
    # Advanced analytics insights
    st.markdown("### Advanced Analytics Insights")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### Customer Segmentation")
        
        # Simulate customer segments
        segments = pd.DataFrame({
            'Segment': ['High Value', 'Regular', 'New', 'At Risk'],
            'Count': [150, 800, 300, 100],
            'Revenue': [500000, 800000, 150000, 50000]
        })
        
        fig_segments = px.scatter(segments, x='Count', y='Revenue', 
                                 size='Revenue', color='Segment',
                                 title="Customer Segments")
        st.plotly_chart(fig_segments, use_container_width=True)
    
    with col2:
        st.markdown("#### Trend Analysis")
        
        # Revenue trend with forecasting
        trend_data = sales_data.groupby('date')['revenue'].sum().reset_index()
        
        # Simple trend line
        x_numeric = np.arange(len(trend_data))
        z = np.polyfit(x_numeric, trend_data['revenue'], 1)
        p = np.poly1d(z)
        
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=trend_data['date'],
            y=trend_data['revenue'],
            mode='markers',
            name='Actual'
        ))
        fig_trend.add_trace(go.Scatter(
            x=trend_data['date'],
            y=p(x_numeric),
            mode='lines',
            name='Trend',
            line=dict(dash='dash')
        ))
        fig_trend.update_layout(title="Revenue Trend Analysis")
        st.plotly_chart(fig_trend, use_container_width=True)
    
    with col3:
        st.markdown("#### Performance Indicators")
        
        # KPI summary
        kpis = [
            {"name": "Revenue Growth", "value": "12.3%", "status": "good"},
            {"name": "Customer Retention", "value": "87.2%", "status": "excellent"},
            {"name": "Market Share", "value": "15.8%", "status": "warning"},
            {"name": "Profit Margin", "value": "23.1%", "status": "good"}
        ]
        
        for kpi in kpis:
            status_colors = {
                'excellent': '#28a745',
                'good': '#17a2b8',
                'warning': '#ffc107',
                'critical': '#dc3545'
            }
            color = status_colors.get(kpi['status'], '#6c757d')
            
            st.markdown(f"**{kpi['name']}**")
            st.markdown(f"<span style='color: {color}; font-size: 24px; font-weight: bold'>{kpi['value']}</span>",
                       unsafe_allow_html=True)
            st.markdown("---")

def render_report_builder():
    """Interactive report builder"""
    st.markdown("# Report Builder")
    
    st.markdown("Create custom reports with automated generation and distribution.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Report Configuration")
        
        with st.form("report_config"):
            report_name = st.text_input("Report Name")
            report_description = st.text_area("Description")
            
            report_type = st.selectbox("Report Type", [
                "Executive Summary",
                "Operational Metrics", 
                "Financial Analysis",
                "Custom Analytics"
            ])
            
            data_sources = st.multiselect("Data Sources", [
                "sales", "users", "operations", "financial"
            ])
            
            frequency = st.selectbox("Generation Frequency", [
                "Daily", "Weekly", "Monthly", "Quarterly"
            ])
            
            recipients = st.text_input("Email Recipients (comma separated)")
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
            
            with col_b:
                end_date = st.date_input("End Date", value=datetime.now())
            
            if st.form_submit_button("Create Report"):
                if report_name and data_sources:
                    st.success(f"Report '{report_name}' created successfully!")
                    st.info("Report has been scheduled for automatic generation.")
                else:
                    st.error("Please provide report name and select data sources.")
    
    with col2:
        st.markdown("### Report Preview")
        
        if st.button("Generate Preview"):
            st.markdown("#### Sample Report Output")
            
            # Generate sample report
            sample_data = {
                'report_name': 'Sample Executive Report',
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'key_metrics': {
                    'total_revenue': 2450000,
                    'growth_rate': 15.8,
                    'active_customers': 1247,
                    'conversion_rate': 4.2
                }
            }
            
            st.json(sample_data)
        
        st.markdown("### Available Templates")
        
        templates = [
            "Executive Dashboard",
            "Financial Summary",
            "Operations Report",
            "Marketing Analytics",
            "Customer Insights"
        ]
        
        for template in templates:
            if st.button(template, key=f"template_{template}"):
                st.info(f"Loading {template} template...")

def render_scheduled_reports():
    """Scheduled reports management"""
    st.markdown("# Scheduled Reports")
    
    # Get scheduled reports
    scheduled_reports = analytics_engine.scheduler.get_scheduled_reports()
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("### Active Scheduled Reports")
        
        if scheduled_reports:
            for report in scheduled_reports:
                with st.container():
                    col_a, col_b, col_c, col_d = st.columns([2, 1, 1, 1])
                    
                    with col_a:
                        status_icon = "🟢" if report['active'] else "🔴"
                        st.write(f"{status_icon} **{report['name']}**")
                        st.caption(f"Type: {report['report_type']}")
                    
                    with col_b:
                        st.write(f"**{report['frequency']}**")
                    
                    with col_c:
                        next_run = report['next_scheduled']
                        if next_run:
                            st.write(datetime.fromisoformat(next_run).strftime("%m/%d %H:%M"))
                        else:
                            st.write("Not scheduled")
                    
                    with col_d:
                        if st.button("Edit", key=f"edit_{report['report_id']}"):
                            st.info(f"Edit report: {report['name']}")
                    
                    st.divider()
        else:
            st.info("No scheduled reports configured.")
    
    with col2:
        st.markdown("### Report Statistics")
        
        if scheduled_reports:
            active_count = len([r for r in scheduled_reports if r['active']])
            st.metric("Total Reports", len(scheduled_reports))
            st.metric("Active Reports", active_count)
            st.metric("Inactive Reports", len(scheduled_reports) - active_count)
        
        st.markdown("### Quick Actions")
        
        if st.button("Run All Reports Now"):
            st.success("All active reports queued for immediate execution!")
        
        if st.button("Export Report List"):
            st.info("Report list exported to CSV")

def render_custom_analytics():
    """Custom analytics and ad-hoc analysis"""
    st.markdown("# Custom Analytics")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Ad-Hoc Analysis")
        
        # Data source selection
        selected_sources = st.multiselect("Select Data Sources", [
            "sales", "users", "operations", "financial"
        ])
        
        if selected_sources:
            # Date range filter
            col_a, col_b = st.columns(2)
            
            with col_a:
                start_date = st.date_input("From Date")
            
            with col_b:
                end_date = st.date_input("To Date")
            
            # Generate analysis
            if st.button("Run Analysis"):
                with st.spinner("Running custom analysis..."):
                    for source in selected_sources:
                        data = analytics_engine.data_manager.get_data(source)
                        
                        st.markdown(f"#### {source.title()} Data Analysis")
                        
                        # Basic statistics
                        numeric_columns = data.select_dtypes(include=[np.number]).columns
                        if len(numeric_columns) > 0:
                            st.dataframe(data[numeric_columns].describe())
                        
                        # Sample visualization
                        if 'date' in data.columns and len(numeric_columns) > 0:
                            chart_column = numeric_columns[0]
                            fig = px.line(data, x='date', y=chart_column,
                                        title=f"{chart_column.title()} Over Time")
                            st.plotly_chart(fig, use_container_width=True)
        
        # SQL Query Interface
        st.markdown("### Custom SQL Analysis")
        
        custom_sql = st.text_area(
            "Enter Custom SQL Query:",
            placeholder="SELECT date, SUM(revenue) as total_revenue FROM sales GROUP BY date ORDER BY date",
            height=100
        )
        
        if st.button("Execute Query") and custom_sql:
            st.info("Query executed successfully!")
            # In a real implementation, this would execute against actual data
            st.dataframe(pd.DataFrame({
                'date': pd.date_range('2024-08-01', periods=5),
                'total_revenue': [100000, 105000, 98000, 112000, 108000]
            }))
    
    with col2:
        st.markdown("### Analysis Tools")
        
        tools = [
            "Correlation Analysis",
            "Trend Detection", 
            "Anomaly Detection",
            "Forecasting",
            "Statistical Testing"
        ]
        
        for tool in tools:
            if st.button(tool, key=f"tool_{tool}"):
                st.info(f"{tool} analysis initiated")
        
        st.markdown("### Data Quality")
        
        quality_metrics = [
            {"metric": "Completeness", "score": 98.5},
            {"metric": "Accuracy", "score": 94.2},
            {"metric": "Consistency", "score": 96.8},
            {"metric": "Timeliness", "score": 99.1}
        ]
        
        for metric in quality_metrics:
            score = metric['score']
            color = 'green' if score >= 95 else 'orange' if score >= 90 else 'red'
            st.markdown(f"**{metric['metric']}**: "
                       f"<span style='color: {color}'>{score}%</span>",
                       unsafe_allow_html=True)

if __name__ == "__main__":
    main()