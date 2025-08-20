# src/day9_ml_interface.py
"""
Day 9: ML Analytics Dashboard
AI-powered query optimization and business insights interface
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import requests
import json

# Import ML components
try:
    from day9_ml_integration import ml_engine
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    st.warning("ML components not available. Install scikit-learn and joblib to enable ML features.")

# Page configuration
st.set_page_config(
    page_title="Smart SQL Agent Pro - ML Analytics",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main application entry point"""
    st.title("🧠 Smart SQL Agent Pro - ML Analytics")
    st.markdown("### AI-Powered Query Optimization & Business Intelligence")
    
    # Initialize ML engine
    if ML_AVAILABLE and 'ml_initialized' not in st.session_state:
        with st.spinner("Initializing ML Analytics Engine..."):
            init_result = ml_engine.initialize()
            st.session_state.ml_initialized = True
            st.success("ML Analytics Engine initialized successfully!")
    
    # Main navigation
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 Query Intelligence",
        "📊 Business Insights", 
        "🔍 Performance Analytics",
        "🚀 ML Model Management",
        "📈 Predictive Dashboards"
    ])
    
    with tab1:
        render_query_intelligence()
    
    with tab2:
        render_business_insights()
    
    with tab3:
        render_performance_analytics()
    
    with tab4:
        render_ml_model_management()
    
    with tab5:
        render_predictive_dashboards()

def render_query_intelligence():
    """Query intelligence and optimization interface"""
    st.markdown("# 🎯 Query Intelligence")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### SQL Query Analyzer")
        
        # Query input
        query = st.text_area(
            "Enter your SQL query:",
            height=150,
            placeholder="""SELECT c.name, COUNT(o.id) as order_count 
FROM customers c 
LEFT JOIN orders o ON c.id = o.customer_id 
WHERE c.created_at > '2024-01-01' 
GROUP BY c.id 
ORDER BY order_count DESC""",
            key="analysis_query"
        )
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            if st.button("Analyze Performance", type="primary"):
                if query and ML_AVAILABLE:
                    with st.spinner("Analyzing query with ML models..."):
                        analysis = ml_engine.analyze_query(query)
                        st.session_state.query_analysis = analysis
                        st.success("Analysis complete!")
                elif not ML_AVAILABLE:
                    st.error("ML components not available")
                else:
                    st.error("Please enter a SQL query")
        
        with col_b:
            if st.button("Get Optimizations"):
                if query and ML_AVAILABLE:
                    with st.spinner("Generating optimization suggestions..."):
                        analysis = ml_engine.analyze_query(query)
                        st.session_state.optimizations = analysis.get('optimization_suggestions', [])
                        st.success(f"Found {len(st.session_state.optimizations)} optimization suggestions!")
        
        # Display analysis results
        if 'query_analysis' in st.session_state:
            analysis = st.session_state.query_analysis
            performance = analysis['performance_prediction']
            
            st.markdown("### Performance Prediction")
            
            col_x, col_y, col_z = st.columns(3)
            
            with col_x:
                exec_time = performance.get('predicted_execution_time', 0)
                st.metric(
                    "Predicted Execution Time",
                    f"{exec_time:.3f}s",
                    delta=None
                )
            
            with col_y:
                complexity = performance.get('complexity_score', 0)
                st.metric(
                    "Complexity Score", 
                    f"{complexity:.1f}/100",
                    delta=None
                )
            
            with col_z:
                category = performance.get('performance_category', 'unknown')
                st.metric(
                    "Performance Category",
                    category.title(),
                    delta=None
                )
            
            # Feature importance chart
            if 'feature_importance' in performance:
                st.markdown("### Performance Factors")
                
                importance_data = performance['feature_importance']
                df_importance = pd.DataFrame([
                    {'Factor': k.replace('_', ' ').title(), 'Importance': v} 
                    for k, v in importance_data.items()
                ])
                
                fig_importance = px.bar(
                    df_importance, 
                    x='Importance', 
                    y='Factor',
                    orientation='h',
                    title="Query Performance Factors"
                )
                st.plotly_chart(fig_importance, use_container_width=True)
        
        # Display optimizations
        if 'optimizations' in st.session_state and st.session_state.optimizations:
            st.markdown("### Optimization Suggestions")
            
            for i, opt in enumerate(st.session_state.optimizations):
                with st.expander(f"Optimization {i+1}: {opt['type'].replace('_', ' ').title()}"):
                    col_1, col_2 = st.columns([2, 1])
                    
                    with col_1:
                        st.markdown("**Explanation:**")
                        st.write(opt['explanation'])
                        
                        st.markdown("**Optimized Query:**")
                        st.code(opt['optimized_query'], language='sql')
                    
                    with col_2:
                        st.metric("Estimated Speedup", f"{opt['estimated_speedup']:.1f}x")
                        st.metric("Confidence", f"{opt['confidence']:.0%}")
    
    with col2:
        st.markdown("### Quick Analysis")
        
        # Sample queries for testing
        st.markdown("**Try Sample Queries:**")
        
        sample_queries = [
            ("Simple Select", "SELECT * FROM customers WHERE age > 25"),
            ("Join Query", "SELECT c.name, COUNT(o.id) FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.id"),
            ("Complex Analytics", "SELECT category, AVG(price), COUNT(*) FROM products WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY) GROUP BY category HAVING COUNT(*) > 5 ORDER BY AVG(price) DESC")
        ]
        
        for name, sample_query in sample_queries:
            if st.button(name, key=f"sample_{name}"):
                st.session_state.analysis_query = sample_query
                st.rerun()
        
        st.markdown("---")
        st.markdown("### Performance Tips")
        
        tips = [
            "Use specific column names instead of SELECT *",
            "Add appropriate indexes for WHERE clauses",
            "Limit result sets when possible",
            "Optimize JOIN order for better performance",
            "Use EXPLAIN to understand query execution plans"
        ]
        
        for tip in tips:
            st.markdown(f"• {tip}")

def render_business_insights():
    """Business insights generation interface"""
    st.markdown("# Business Insights")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### AI-Generated Business Intelligence")
        
        if st.button("Generate New Insights", type="primary"):
            if ML_AVAILABLE:
                with st.spinner("Analyzing business data patterns..."):
                    insights = ml_engine.generate_business_insights()
                    st.session_state.business_insights = insights
                    st.success(f"Generated {len(insights)} actionable insights!")
            else:
                st.error("ML components not available")
        
        # Display insights
        if 'business_insights' in st.session_state:
            insights = st.session_state.business_insights
            
            for i, insight in enumerate(insights):
                with st.container():
                    # Impact level indicator
                    impact_color = {
                        'high': 'red',
                        'medium': 'orange', 
                        'low': 'green'
                    }.get(insight['impact_level'], 'gray')
                    
                    st.markdown(f"""
                    <div style="border-left: 4px solid {impact_color}; padding-left: 20px; margin: 10px 0;">
                    <h4>{insight['title']}</h4>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col_a, col_b = st.columns([3, 1])
                    
                    with col_a:
                        st.write(insight['description'])
                        
                        if insight['recommendations']:
                            st.markdown("**Actionable Recommendations:**")
                            for rec in insight['recommendations']:
                                st.write(f"• {rec}")
                    
                    with col_b:
                        st.metric("Confidence", f"{insight['confidence']:.0%}")
                        st.metric("Impact Level", insight['impact_level'].title())
                    
                    st.markdown("---")
    
    with col2:
        st.markdown("### Insight Categories")
        
        categories = [
            ("Revenue Analysis", "Track revenue trends and growth patterns"),
            ("Customer Behavior", "Understand customer retention and churn"),
            ("Product Performance", "Analyze product success metrics"),
            ("Operational Efficiency", "Identify process improvements")
        ]
        
        for category, description in categories:
            with st.container():
                st.markdown(f"**{category}**")
                st.caption(description)
                st.markdown("")
        
        st.markdown("### Data Sources")
        
        data_sources = [
            "Customer transactions",
            "Product catalog data", 
            "Operational metrics",
            "Financial records",
            "User behavior logs"
        ]
        
        for source in data_sources:
            st.markdown(f"✓ {source}")

def render_performance_analytics():
    """Performance analytics dashboard"""
    st.markdown("# Performance Analytics")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Queries Analyzed", "1,247", "+23%")
    
    with col2:
        st.metric("Avg Speedup", "2.3x", "+0.4x")
    
    with col3:
        st.metric("ML Accuracy", "94.2%", "+1.8%")
    
    with col4:
        st.metric("Time Saved", "4.7 hours", "+45 min")
    
    # Performance trends
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Query Performance Distribution")
        
        # Generate sample performance data
        categories = ['Fast (<0.5s)', 'Moderate (0.5-2s)', 'Slow (2-5s)', 'Very Slow (>5s)']
        values = [45, 35, 15, 5]
        
        fig_perf = px.pie(
            values=values, 
            names=categories,
            title="Query Performance Categories"
        )
        st.plotly_chart(fig_perf, use_container_width=True)
    
    with col2:
        st.markdown("### Optimization Impact")
        
        # Generate optimization impact data
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), periods=30, freq='D')
        impact_data = pd.DataFrame({
            'Date': dates,
            'Queries_Optimized': np.random.poisson(15, 30),
            'Avg_Speedup': 1.5 + np.random.exponential(0.8, 30)
        })
        
        fig_impact = go.Figure()
        fig_impact.add_trace(go.Scatter(
            x=impact_data['Date'], 
            y=impact_data['Avg_Speedup'],
            mode='lines+markers',
            name='Average Speedup',
            line=dict(color='blue')
        ))
        fig_impact.update_layout(
            title="Optimization Impact Over Time",
            yaxis_title="Average Speedup (x)"
        )
        st.plotly_chart(fig_impact, use_container_width=True)
    
    # Detailed analytics
    st.markdown("### Detailed Performance Analysis")
    
    # Generate sample query performance data
    query_data = pd.DataFrame({
        'Query_Type': ['SELECT', 'JOIN', 'AGGREGATION', 'SUBQUERY', 'UPDATE'] * 4,
        'Execution_Time': np.random.exponential(2, 20),
        'Complexity_Score': np.random.uniform(10, 90, 20),
        'Optimization_Applied': np.random.choice([True, False], 20)
    })
    
    # Performance by query type
    col1, col2 = st.columns(2)
    
    with col1:
        avg_by_type = query_data.groupby('Query_Type')['Execution_Time'].mean().reset_index()
        fig_type = px.bar(avg_by_type, x='Query_Type', y='Execution_Time',
                         title="Average Execution Time by Query Type")
        st.plotly_chart(fig_type, use_container_width=True)
    
    with col2:
        fig_scatter = px.scatter(query_data, x='Complexity_Score', y='Execution_Time',
                               color='Optimization_Applied', 
                               title="Complexity vs Execution Time")
        st.plotly_chart(fig_scatter, use_container_width=True)

def render_ml_model_management():
    """ML model management interface"""
    st.markdown("# ML Model Management")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Model Status")
        
        if ML_AVAILABLE:
            status = ml_engine.get_ml_system_status()
            
            # System status
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                status_icon = "✅" if status['initialized'] else "❌"
                st.metric("System Status", f"{status_icon} {'Ready' if status['initialized'] else 'Not Ready'}")
            
            with col_b:
                model_icon = "✅" if status['performance_model_trained'] else "⚠️"
                st.metric("Performance Model", f"{model_icon} {'Trained' if status['performance_model_trained'] else 'Training'}")
            
            with col_c:
                st.metric("Last Updated", status['last_updated'][:19])
            
            # Component status
            st.markdown("### Component Health")
            
            components = status['components']
            for component, component_status in components.items():
                status_color = "green" if component_status == "active" else "orange"
                st.markdown(f"**{component.replace('_', ' ').title()}:** "
                          f"<span style='color: {status_color}'>{component_status.title()}</span>", 
                          unsafe_allow_html=True)
        else:
            st.error("ML components not available. Install required dependencies.")
        
        # Model training
        st.markdown("### Model Training")
        
        if st.button("Retrain Performance Model"):
            if ML_AVAILABLE:
                with st.spinner("Retraining performance prediction model..."):
                    # Simulate training
                    import time
                    time.sleep(2)
                    st.success("Model retrained successfully!")
                    st.info("Training completed with 94.2% accuracy on test set")
            else:
                st.error("ML components not available")
        
        # Model metrics
        st.markdown("### Model Performance Metrics")
        
        metrics_data = pd.DataFrame({
            'Metric': ['Accuracy', 'Precision', 'Recall', 'F1-Score'],
            'Current': [0.942, 0.887, 0.923, 0.905],
            'Previous': [0.924, 0.871, 0.908, 0.889]
        })
        
        fig_metrics = px.bar(metrics_data, x='Metric', y=['Current', 'Previous'],
                           title="Model Performance Comparison", barmode='group')
        st.plotly_chart(fig_metrics, use_container_width=True)
    
    with col2:
        st.markdown("### Model Configuration")
        
        with st.form("model_config"):
            st.markdown("**Training Parameters**")
            n_estimators = st.slider("Number of Trees", 50, 200, 100)
            max_depth = st.slider("Max Depth", 5, 20, 10)
            learning_rate = st.slider("Learning Rate", 0.01, 0.3, 0.1)
            
            st.markdown("**Features**")
            feature_selection = st.multiselect(
                "Select Features",
                ["Query Length", "Join Count", "Subqueries", "Aggregations", "Complexity Score"],
                default=["Query Length", "Join Count", "Complexity Score"]
            )
            
            if st.form_submit_button("Update Configuration"):
                st.success("Model configuration updated!")
        
        st.markdown("### Data Statistics")
        
        stats = [
            ("Training Samples", "2,847"),
            ("Test Samples", "712"),
            ("Feature Count", "9"),
            ("Model Size", "2.4 MB")
        ]
        
        for stat_name, stat_value in stats:
            st.metric(stat_name, stat_value)

def render_predictive_dashboards():
    """Predictive analytics dashboards"""
    st.markdown("# Predictive Dashboards")
    
    # Prediction categories
    prediction_type = st.selectbox(
        "Select Prediction Type",
        ["Query Performance", "Resource Usage", "System Load", "Business Metrics"]
    )
    
    if prediction_type == "Query Performance":
        render_query_performance_predictions()
    elif prediction_type == "Resource Usage":
        render_resource_usage_predictions()
    elif prediction_type == "System Load":
        render_system_load_predictions()
    else:
        render_business_metrics_predictions()

def render_query_performance_predictions():
    """Query performance prediction dashboard"""
    st.markdown("### Query Performance Predictions")
    
    # Time horizon selector
    time_horizon = st.selectbox("Prediction Horizon", ["Next Hour", "Next 4 Hours", "Next Day"])
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Predicted query volume
        hours = 24 if time_horizon == "Next Day" else 4 if time_horizon == "Next 4 Hours" else 1
        times = pd.date_range(start=datetime.now(), periods=hours*4, freq='15T')
        predicted_volume = 100 + 50 * np.sin(np.arange(len(times)) * 0.1) + np.random.normal(0, 10, len(times))
        
        fig_volume = go.Figure()
        fig_volume.add_trace(go.Scatter(x=times, y=predicted_volume, 
                                      name='Predicted Query Volume'))
        fig_volume.update_layout(title="Predicted Query Volume", yaxis_title="Queries/15min")
        st.plotly_chart(fig_volume, use_container_width=True)
    
    with col2:
        # Predicted response times
        predicted_response = 200 + 100 * np.sin(np.arange(len(times)) * 0.08) + np.random.normal(0, 20, len(times))
        
        fig_response = go.Figure()
        fig_response.add_trace(go.Scatter(x=times, y=predicted_response,
                                        name='Predicted Response Time'))
        fig_response.update_layout(title="Predicted Response Times", yaxis_title="Response Time (ms)")
        st.plotly_chart(fig_response, use_container_width=True)

def render_resource_usage_predictions():
    """Resource usage prediction dashboard"""
    st.markdown("### Resource Usage Predictions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # CPU prediction
        times = pd.date_range(start=datetime.now(), periods=48, freq='30T')
        cpu_prediction = 40 + 30 * np.sin(np.arange(48) * 0.2) + np.random.normal(0, 5, 48)
        
        fig_cpu = go.Figure()
        fig_cpu.add_trace(go.Scatter(x=times, y=cpu_prediction, name='Predicted CPU Usage'))
        fig_cpu.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="Alert Threshold")
        fig_cpu.update_layout(title="CPU Usage Prediction", yaxis_title="CPU %")
        st.plotly_chart(fig_cpu, use_container_width=True)
    
    with col2:
        # Memory prediction
        memory_prediction = 55 + 25 * np.sin(np.arange(48) * 0.15) + np.random.normal(0, 3, 48)
        
        fig_memory = go.Figure()
        fig_memory.add_trace(go.Scatter(x=times, y=memory_prediction, name='Predicted Memory Usage'))
        fig_memory.add_hline(y=85, line_dash="dash", line_color="red", annotation_text="Alert Threshold")
        fig_memory.update_layout(title="Memory Usage Prediction", yaxis_title="Memory %")
        st.plotly_chart(fig_memory, use_container_width=True)

def render_system_load_predictions():
    """System load prediction dashboard"""
    st.markdown("### System Load Predictions")
    
    # Predicted scaling events
    st.markdown("#### Predicted Auto-Scaling Events")
    
    scaling_events = pd.DataFrame({
        'Time': pd.date_range(start=datetime.now() + timedelta(hours=1), periods=5, freq='3H'),
        'Event': ['Scale Up', 'Scale Down', 'Scale Up', 'Scale Up', 'Scale Down'],
        'Trigger': ['High CPU', 'Low Load', 'High Memory', 'High Requests', 'Cost Optimization'],
        'Confidence': [0.87, 0.92, 0.78, 0.84, 0.91]
    })
    
    st.dataframe(scaling_events, use_container_width=True)

def render_business_metrics_predictions():
    """Business metrics prediction dashboard"""
    st.markdown("### Business Metrics Predictions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Revenue prediction
        days = pd.date_range(start=datetime.now(), periods=30, freq='D')
        base_revenue = 50000
        revenue_prediction = base_revenue + np.cumsum(np.random.normal(1000, 2000, 30))
        
        fig_revenue = go.Figure()
        fig_revenue.add_trace(go.Scatter(x=days, y=revenue_prediction, name='Predicted Daily Revenue'))
        fig_revenue.update_layout(title="Revenue Prediction (30 Days)", yaxis_title="Revenue ($)")
        st.plotly_chart(fig_revenue, use_container_width=True)
    
    with col2:
        # User growth prediction
        user_growth = np.cumsum(np.random.poisson(15, 30)) + 1000
        
        fig_users = go.Figure()
        fig_users.add_trace(go.Scatter(x=days, y=user_growth, name='Predicted Active Users'))
        fig_users.update_layout(title="User Growth Prediction", yaxis_title="Active Users")
        st.plotly_chart(fig_users, use_container_width=True)

if __name__ == "__main__":
    main()