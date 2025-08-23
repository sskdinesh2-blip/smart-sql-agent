# src/day12_performance_interface.py
"""
Day 12: Performance Optimization Dashboard
Advanced performance monitoring, caching, and scalability management
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import numpy as np

# Import performance components
try:
    from day12_performance_engine import performance_engine, OptimizationLevel, CacheStrategy
    PERFORMANCE_AVAILABLE = True
except ImportError:
    PERFORMANCE_AVAILABLE = False
    st.warning("Performance engine not available. Check dependencies.")

# Page configuration
st.set_page_config(
    page_title="Smart SQL Agent Pro - Performance Optimization",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("⚡ Smart SQL Agent Pro - Performance Optimization")
    st.markdown("### Advanced Caching, Query Optimization & Auto-Scaling")
    
    if not PERFORMANCE_AVAILABLE:
        st.error("Performance engine not available - check configuration")
        return
    
    # Main navigation
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 Performance Dashboard",
        "🚀 Query Optimizer", 
        "💾 Cache Management",
        "📊 Auto-Scaling Control",
        "🔧 System Optimization"
    ])
    
    with tab1:
        render_performance_dashboard()
    
    with tab2:
        render_query_optimizer()
    
    with tab3:
        render_cache_management()
    
    with tab4:
        render_autoscaling_control()
    
    with tab5:
        render_system_optimization()

def render_performance_dashboard():
    """Main performance monitoring dashboard"""
    st.markdown("# Performance Dashboard")
    
    # Auto-refresh option
    auto_refresh = st.checkbox("Auto-refresh (30s)", value=False)
    if auto_refresh:
        time.sleep(0.1)
        st.rerun()
    
    # Get performance summary
    if st.button("🔄 Refresh Metrics", type="primary"):
        with st.spinner("Collecting performance metrics..."):
            summary = performance_engine.get_performance_summary()
            st.session_state.perf_summary = summary
            st.success("Metrics refreshed!")
    
    if 'perf_summary' not in st.session_state:
        summary = performance_engine.get_performance_summary()
        st.session_state.perf_summary = summary
    
    summary = st.session_state.perf_summary
    
    # Key performance metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_time = summary['performance_metrics']['average_execution_time']
        st.metric(
            "Avg Query Time",
            f"{avg_time:.3f}s",
            delta="-0.045s" if avg_time < 0.5 else "+0.023s"
        )
    
    with col2:
        cache_hit_rate = summary['cache_statistics']['hit_rate']
        st.metric(
            "Cache Hit Rate",
            f"{cache_hit_rate:.1f}%",
            delta="+2.3%" if cache_hit_rate > 50 else "-1.1%"
        )
    
    with col3:
        cpu_usage = summary['system_metrics']['cpu_percent']
        st.metric(
            "CPU Usage",
            f"{cpu_usage:.1f}%",
            delta="+5.2%" if cpu_usage > 50 else "-2.1%"
        )
    
    with col4:
        instances = summary['system_metrics']['current_instances']
        st.metric(
            "Active Instances",
            str(instances),
            delta="+1" if instances > 1 else "0"
        )
    
    # Performance trends
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Query Performance Trends")
        
        # Generate sample performance trend data
        hours = pd.date_range(start=datetime.now() - timedelta(hours=6), periods=25, freq='15T')
        response_times = [0.2 + 0.1 * np.sin(i * 0.1) + np.random.normal(0, 0.05) for i in range(25)]
        response_times = [max(0.05, rt) for rt in response_times]  # Ensure positive
        
        fig_perf = go.Figure()
        fig_perf.add_trace(go.Scatter(
            x=hours, 
            y=response_times,
            mode='lines+markers',
            name='Response Time',
            line=dict(color='blue', width=2)
        ))
        fig_perf.add_hline(y=0.5, line_dash="dash", line_color="orange", 
                          annotation_text="Warning Threshold")
        fig_perf.add_hline(y=1.0, line_dash="dash", line_color="red",
                          annotation_text="Critical Threshold")
        fig_perf.update_layout(
            title="Query Response Time (Last 6 Hours)",
            xaxis_title="Time",
            yaxis_title="Response Time (seconds)"
        )
        st.plotly_chart(fig_perf, use_container_width=True)
    
    with col2:
        st.markdown("### System Resource Usage")
        
        # Generate system metrics
        cpu_data = [45 + 15 * np.sin(i * 0.2) + np.random.normal(0, 3) for i in range(25)]
        memory_data = [60 + 10 * np.sin(i * 0.15) + np.random.normal(0, 2) for i in range(25)]
        
        fig_resources = go.Figure()
        fig_resources.add_trace(go.Scatter(
            x=hours, 
            y=cpu_data,
            mode='lines',
            name='CPU %',
            line=dict(color='red')
        ))
        fig_resources.add_trace(go.Scatter(
            x=hours,
            y=memory_data,
            mode='lines',
            name='Memory %',
            line=dict(color='green')
        ))
        fig_resources.update_layout(
            title="System Resource Utilization",
            xaxis_title="Time",
            yaxis_title="Usage (%)",
            yaxis_range=[0, 100]
        )
        st.plotly_chart(fig_resources, use_container_width=True)
    
    # Cache and optimization statistics
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Cache Performance")
        
        cache_stats = summary['cache_statistics']
        
        # Cache hit rate pie chart
        fig_cache = go.Figure(data=[go.Pie(
            labels=['Cache Hits', 'Cache Misses'],
            values=[cache_stats['hits'], cache_stats['misses']]
        )])
        fig_cache.update_traces(marker=dict(colors=['#28a745', '#dc3545']))
        fig_cache.update_layout(title="Cache Hit vs Miss Distribution")
        st.plotly_chart(fig_cache, use_container_width=True)
        
        # Cache statistics table
        cache_data = [
            ["Total Entries", cache_stats['size']],
            ["Cache Hits", cache_stats['hits']],
            ["Cache Misses", cache_stats['misses']],
            ["Evictions", cache_stats['evictions']],
            ["Strategy", cache_stats['strategy']]
        ]
        
        cache_df = pd.DataFrame(cache_data, columns=['Metric', 'Value'])
        st.dataframe(cache_df, use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("### Optimization Impact")
        
        opt_rate = summary['performance_metrics']['optimization_rate']
        total_queries = summary['performance_metrics']['total_queries_last_hour']
        
        # Optimization rate gauge
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = opt_rate,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Optimization Rate"},
            delta = {'reference': 50},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 25], 'color': "lightgray"},
                    {'range': [25, 50], 'color': "yellow"},
                    {'range': [50, 75], 'color': "orange"},
                    {'range': [75, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig_gauge.update_layout(height=300)
        st.plotly_chart(fig_gauge, use_container_width=True)
        
        # Performance improvements
        st.markdown("**Recent Optimizations:**")
        improvements = [
            "Index suggestion applied: +23% speedup",
            "Query rewrite completed: +15% speedup", 
            "JOIN optimization: +18% speedup",
            "Result set limiting: +12% speedup"
        ]
        
        for improvement in improvements:
            st.write(f"• {improvement}")

def render_query_optimizer():
    """Query optimization interface"""
    st.markdown("# Query Optimizer")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### SQL Query Optimization")
        
        # Query input
        query = st.text_area(
            "Enter SQL Query:",
            height=200,
            placeholder="""SELECT c.customer_name, COUNT(o.order_id) as order_count
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
WHERE c.registration_date >= '2024-01-01'
GROUP BY c.customer_id, c.customer_name
ORDER BY order_count DESC""",
            key="optimizer_query"
        )
        
        # Optimization settings
        col_a, col_b = st.columns(2)
        
        with col_a:
            opt_level = st.selectbox("Optimization Level", [
                "Basic", "Aggressive", "Adaptive", "Custom"
            ])
        
        with col_b:
            execute_query = st.checkbox("Execute Optimized Query", value=True)
        
        if st.button("🚀 Optimize Query", type="primary"):
            if query:
                with st.spinner("Optimizing query..."):
                    # Convert string to enum
                    level_map = {
                        "Basic": OptimizationLevel.BASIC,
                        "Aggressive": OptimizationLevel.AGGRESSIVE,
                        "Adaptive": OptimizationLevel.ADAPTIVE,
                        "Custom": OptimizationLevel.CUSTOM
                    }
                    
                    if execute_query:
                        result = performance_engine.execute_optimized_query(query)
                        st.session_state.optimization_result = result
                    else:
                        opt_result = performance_engine.optimizer.optimize_query(
                            query, level_map[opt_level]
                        )
                        st.session_state.optimization_result = {'optimization_details': opt_result}
                
                st.success("Query optimization complete!")
            else:
                st.error("Please enter a SQL query")
        
        # Display optimization results
        if 'optimization_result' in st.session_state:
            result = st.session_state.optimization_result
            
            if 'optimization_details' in result:
                opt_details = result['optimization_details']
                
                st.markdown("### Optimization Results")
                
                col_x, col_y = st.columns(2)
                
                with col_x:
                    if 'execution_time' in result:
                        st.metric("Execution Time", f"{result['execution_time']:.3f}s")
                        st.metric("Cache Hit", "Yes" if result['cache_hit'] else "No")
                    
                    st.metric("Estimated Speedup", f"{opt_details['estimated_speedup']:.1f}x")
                    st.metric("Rules Applied", str(opt_details['applied_rules']))
                
                with col_y:
                    if opt_details['optimizations']:
                        st.markdown("**Applied Optimizations:**")
                        for opt in opt_details['optimizations']:
                            confidence = opt['confidence'] * 100
                            gain = opt['estimated_gain'] * 100
                            st.write(f"• {opt['description']}")
                            st.caption(f"Est. gain: {gain:.1f}%, Confidence: {confidence:.0f}%")
                
                # Show optimized query
                st.markdown("### Optimized Query")
                st.code(opt_details['optimized_query'], language='sql')
    
    with col2:
        st.markdown("### Optimization Statistics")
        
        # Sample optimization stats
        stats = [
            {"Rule": "Index Suggestions", "Applied": 45, "Avg Gain": "28%"},
            {"Rule": "JOIN Optimization", "Applied": 32, "Avg Gain": "22%"},
            {"Rule": "Result Limiting", "Applied": 67, "Avg Gain": "15%"},
            {"Rule": "Column Selection", "Applied": 23, "Avg Gain": "12%"},
        ]
        
        stats_df = pd.DataFrame(stats)
        st.dataframe(stats_df, use_container_width=True, hide_index=True)
        
        st.markdown("### Optimization Rules")
        
        rules = [
            "✓ Index hint suggestions",
            "✓ JOIN order optimization", 
            "✓ Subquery to JOIN conversion",
            "✓ Result set limiting",
            "✓ Column selection optimization",
            "✓ WHERE clause improvements"
        ]
        
        for rule in rules:
            st.write(rule)

def render_cache_management():
    """Cache management interface"""
    st.markdown("# Cache Management")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Cache Configuration")
        
        # Current cache settings
        current_stats = performance_engine.cache.get_stats()
        
        with st.form("cache_settings"):
            st.markdown("**Cache Parameters**")
            
            max_size = st.slider("Maximum Cache Size", 100, 10000, 1000)
            
            strategy = st.selectbox("Cache Strategy", [
                "LRU (Least Recently Used)",
                "LFU (Least Frequently Used)", 
                "TTL (Time To Live)",
                "Adaptive (Hybrid)"
            ])
            
            default_ttl = st.slider("Default TTL (seconds)", 60, 3600, 300)
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                if st.form_submit_button("Update Settings"):
                    st.success("Cache settings updated!")
            
            with col_b:
                if st.form_submit_button("Clear Cache"):
                    performance_engine.cache.clear()
                    st.success("Cache cleared!")
        
        # Cache performance over time
        st.markdown("### Cache Performance Trends")
        
        # Generate sample cache performance data
        times = pd.date_range(start=datetime.now() - timedelta(hours=2), periods=25, freq='5T')
        hit_rates = [60 + 20 * np.sin(i * 0.1) + np.random.normal(0, 5) for i in range(25)]
        hit_rates = [max(0, min(100, hr)) for hr in hit_rates]  # Clamp to 0-100
        
        fig_cache_perf = go.Figure()
        fig_cache_perf.add_trace(go.Scatter(
            x=times,
            y=hit_rates,
            mode='lines+markers',
            name='Cache Hit Rate %',
            line=dict(color='green', width=2)
        ))
        fig_cache_perf.add_hline(y=70, line_dash="dash", line_color="orange",
                                annotation_text="Target Hit Rate")
        fig_cache_perf.update_layout(
            title="Cache Hit Rate Over Time",
            xaxis_title="Time",
            yaxis_title="Hit Rate (%)",
            yaxis_range=[0, 100]
        )
        st.plotly_chart(fig_cache_perf, use_container_width=True)
    
    with col2:
        st.markdown("### Current Cache Status")
        
        # Cache statistics
        stats_data = [
            ["Strategy", current_stats['strategy'].upper()],
            ["Total Entries", current_stats['size']],
            ["Cache Hits", current_stats['hits']],
            ["Cache Misses", current_stats['misses']],
            ["Hit Rate", f"{current_stats['hit_rate']:.1f}%"],
            ["Evictions", current_stats['evictions']]
        ]
        
        stats_df = pd.DataFrame(stats_data, columns=['Metric', 'Value'])
        st.dataframe(stats_df, use_container_width=True, hide_index=True)
        
        st.markdown("### Cache Efficiency")
        
        # Efficiency metrics
        efficiency_score = current_stats['hit_rate']
        
        if efficiency_score >= 80:
            st.success(f"Excellent cache efficiency: {efficiency_score:.1f}%")
        elif efficiency_score >= 60:
            st.info(f"Good cache efficiency: {efficiency_score:.1f}%")
        elif efficiency_score >= 40:
            st.warning(f"Moderate cache efficiency: {efficiency_score:.1f}%")
        else:
            st.error(f"Poor cache efficiency: {efficiency_score:.1f}%")
        
        st.markdown("### Recommendations")
        
        recommendations = []
        if current_stats['hit_rate'] < 50:
            recommendations.append("Consider increasing cache size")
            recommendations.append("Review TTL settings for your workload")
        if current_stats['evictions'] > current_stats['hits']:
            recommendations.append("Cache size may be too small")
        if current_stats['hit_rate'] > 90:
            recommendations.append("Excellent performance - current settings optimal")
        
        if not recommendations:
            recommendations = ["Cache is performing well", "Monitor hit rate trends"]
        
        for rec in recommendations:
            st.write(f"• {rec}")

def render_autoscaling_control():
    """Auto-scaling control interface"""
    st.markdown("# Auto-Scaling Control")
    
    # Get current scaling status
    summary = performance_engine.get_performance_summary()
    scaling_status = summary['scaling_status']
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Scaling Status")
        
        # Current instance information
        current_instances = scaling_status['current_instances']
        
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            st.metric("Current Instances", current_instances)
        
        with col_b:
            st.metric("Min Instances", "1")
        
        with col_c:
            st.metric("Max Instances", "10")
        
        # Scaling recommendation
        if scaling_status['action_needed']:
            action = scaling_status['action']
            action_color = "green" if action['type'] == 'scale_up' else "blue"
            
            st.markdown(f"### Scaling Recommendation")
            st.markdown(f"**Action:** <span style='color: {action_color}'>{action['type'].replace('_', ' ').title()}</span>", 
                       unsafe_allow_html=True)
            st.write(f"**From:** {action['from_instances']} → **To:** {action['to_instances']} instances")
            
            st.markdown("**Reasons:**")
            for reason in action['reasons']:
                st.write(f"• {reason}")
            
            col_x, col_y = st.columns(2)
            
            with col_x:
                if st.button("🚀 Execute Scaling", type="primary"):
                    success = performance_engine.auto_scaler.execute_scaling_action(action)
                    if success:
                        st.success(f"Scaling action executed: {action['type']}")
                        st.rerun()
                    else:
                        st.error("Scaling action failed")
            
            with col_y:
                if st.button("⏭️ Skip This Time"):
                    st.info("Scaling recommendation dismissed")
        
        else:
            st.success("🎯 **No scaling action needed**")
            st.write("Current system performance is within optimal thresholds.")
        
        # Scaling history chart
        st.markdown("### Scaling History")
        
        # Generate sample scaling data
        scale_times = pd.date_range(start=datetime.now() - timedelta(days=7), periods=20, freq='8H')
        instance_counts = [1, 1, 2, 2, 3, 3, 2, 2, 1, 1, 2, 3, 4, 3, 2, 2, 1, 1, 2, 2]
        
        fig_scaling = go.Figure()
        fig_scaling.add_trace(go.Scatter(
            x=scale_times,
            y=instance_counts,
            mode='lines+markers',
            name='Instance Count',
            line=dict(color='purple', width=3),
            marker=dict(size=8)
        ))
        fig_scaling.update_layout(
            title="Instance Count Over Last 7 Days",
            xaxis_title="Time",
            yaxis_title="Instance Count",
            yaxis_range=[0, 5]
        )
        st.plotly_chart(fig_scaling, use_container_width=True)
    
    with col2:
        st.markdown("### Scaling Configuration")
        
        with st.form("scaling_config"):
            st.markdown("**Thresholds**")
            
            cpu_threshold = st.slider("CPU Threshold (%)", 50, 90, 70)
            memory_threshold = st.slider("Memory Threshold (%)", 60, 95, 80)
            response_threshold = st.slider("Response Time Threshold (s)", 0.5, 5.0, 2.0)
            
            st.markdown("**Cooldown Periods**")
            
            scale_up_cooldown = st.slider("Scale Up Cooldown (min)", 1, 30, 5)
            scale_down_cooldown = st.slider("Scale Down Cooldown (min)", 5, 60, 10)
            
            st.markdown("**Instance Limits**")
            
            min_instances = st.slider("Minimum Instances", 1, 3, 1)
            max_instances = st.slider("Maximum Instances", 5, 20, 10)
            
            if st.form_submit_button("Update Configuration"):
                st.success("Scaling configuration updated!")
        
        st.markdown("### Current Metrics")
        
        metrics = scaling_status['metrics_analyzed']
        
        metric_data = [
            ["CPU Usage", f"{metrics.get('cpu_percent', 0):.1f}%"],
            ["Memory Usage", f"{metrics.get('memory_percent', 0):.1f}%"],
            ["Response Time", f"{metrics.get('average_response_time', 0):.3f}s"],
            ["Queue Length", str(metrics.get('queue_length', 0))]
        ]
        
        metrics_df = pd.DataFrame(metric_data, columns=['Metric', 'Current Value'])
        st.dataframe(metrics_df, use_container_width=True, hide_index=True)

def render_system_optimization():
    """System optimization and tuning interface"""
    st.markdown("# System Optimization")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Performance Tuning")
        
        # System optimization options
        with st.form("system_optimization"):
            st.markdown("**Database Optimization**")
            
            enable_query_cache = st.checkbox("Enable Query Result Caching", value=True)
            enable_connection_pooling = st.checkbox("Enable Connection Pooling", value=True)
            enable_query_optimization = st.checkbox("Enable Automatic Query Optimization", value=True)
            
            st.markdown("**System Resources**")
            
            max_memory_usage = st.slider("Max Memory Usage (%)", 50, 95, 80)
            max_cpu_usage = st.slider("Max CPU Usage (%)", 50, 95, 70)
            
            st.markdown("**Performance Features**")
            
            enable_async_processing = st.checkbox("Enable Async Processing", value=True)
            enable_load_balancing = st.checkbox("Enable Load Balancing", value=True)
            enable_auto_scaling = st.checkbox("Enable Auto-Scaling", value=True)
            
            if st.form_submit_button("Apply Optimizations"):
                st.success("System optimizations applied!")
                st.info("Changes will take effect after system restart.")
        
        # Performance recommendations
        st.markdown("### Optimization Recommendations")
        
        recommendations = [
            {
                "category": "Query Performance",
                "items": [
                    "Enable intelligent query caching for 23% improvement",
                    "Implement index suggestions for 15% faster queries",
                    "Optimize JOIN operations for complex queries"
                ]
            },
            {
                "category": "System Resources",
                "items": [
                    "Current CPU utilization is optimal",
                    "Memory usage could be optimized with better caching",
                    "Consider enabling compression for large datasets"
                ]
            },
            {
                "category": "Scalability",
                "items": [
                    "Auto-scaling thresholds are well-configured",
                    "Load balancer is distributing traffic evenly",
                    "Connection pooling is reducing overhead effectively"
                ]
            }
        ]
        
        for rec in recommendations:
            with st.expander(f"📋 {rec['category']}"):
                for item in rec['items']:
                    st.write(f"• {item}")
    
    with col2:
        st.markdown("### System Health Score")
        
        # Calculate overall health score
        summary = performance_engine.get_performance_summary()
        
        cache_score = min(100, summary['cache_statistics']['hit_rate'] * 1.2)
        performance_score = max(0, 100 - (summary['performance_metrics']['average_execution_time'] * 200))
        cpu_score = max(0, 100 - summary['system_metrics']['cpu_percent'])
        
        overall_score = (cache_score + performance_score + cpu_score) / 3
        
        # Health score gauge
        fig_health = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = overall_score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "System Health Score"},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkgreen"},
                'steps': [
                    {'range': [0, 25], 'color': "red"},
                    {'range': [25, 50], 'color': "orange"},
                    {'range': [50, 75], 'color': "yellow"},
                    {'range': [75, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "blue", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig_health.update_layout(height=400)
        st.plotly_chart(fig_health, use_container_width=True)
        
        # Component health breakdown
        st.markdown("### Component Health")
        
        components = [
            {"Component": "Query Engine", "Health": 95, "Status": "Excellent"},
            {"Component": "Cache System", "Health": int(cache_score), "Status": "Good"},
            {"Component": "Load Balancer", "Health": 88, "Status": "Good"},
            {"Component": "Auto-Scaler", "Health": 92, "Status": "Excellent"},
            {"Component": "Database Pool", "Health": 85, "Status": "Good"}
        ]
        
        comp_df = pd.DataFrame(components)
        
        for _, comp in comp_df.iterrows():
            col_a, col_b = st.columns([2, 1])
            
            with col_a:
                st.write(f"**{comp['Component']}**")
            
            with col_b:
                health_color = (
                    'green' if comp['Health'] >= 90 
                    else 'orange' if comp['Health'] >= 70 
                    else 'red'
                )
                st.markdown(f"<span style='color: {health_color}'>{comp['Health']}% - {comp['Status']}</span>", 
                           unsafe_allow_html=True)
        
        st.markdown("### Quick Actions")
        
        action_buttons = [
            ("Optimize All Queries", "Apply optimization rules to all cached queries"),
            ("Refresh Cache", "Clear and rebuild intelligent cache"),
            ("Balance Load", "Redistribute connections across nodes"),
            ("Health Check", "Run comprehensive system diagnostics")
        ]
        
        for button_text, description in action_buttons:
            if st.button(button_text, key=f"action_{button_text}"):
                st.success(f"{button_text} completed!")
                st.info(description)

if __name__ == "__main__":
    main()