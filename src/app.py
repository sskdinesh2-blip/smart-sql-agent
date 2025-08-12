"""
Smart SQL Pipeline Generator - Enhanced with Database Integration + Day 3 Features
"""
import streamlit as st
import sys
import os
import pandas as pd
import json
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.dirname(__file__))

from sql_agent import SQLPipelineAgent
from database_manager import DatabaseManager
import time
import plotly.express as px
import plotly.graph_objects as go

# Try to import Day 3 components (optional)
try:
    from sql_optimizer import SQLOptimizer
    OPTIMIZER_AVAILABLE = True
except ImportError:
    OPTIMIZER_AVAILABLE = False

try:
    from export_manager import ExportManager
    EXPORT_AVAILABLE = True
except ImportError:
    EXPORT_AVAILABLE = False

# Page config
st.set_page_config(
    page_title="Smart SQL Agent - Enhanced",
    page_icon="🚀",
    layout="wide"
)

# Enhanced CSS with Day 3 styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .success-box {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        border: none;
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .error-box {
        background: linear-gradient(135deg, #ff758c 0%, #ff7eb3 100%);
        border: none;
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .day3-feature {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        color: #333;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'agent' not in st.session_state:
    try:
        st.session_state.agent = SQLPipelineAgent()
        st.session_state.agent_ready = True
    except Exception as e:
        st.session_state.agent = None
        st.session_state.agent_error = str(e)
        st.session_state.agent_ready = False

if 'db_manager' not in st.session_state:
    try:
        st.session_state.db_manager = DatabaseManager()
        st.session_state.db_ready = True
    except Exception as e:
        st.session_state.db_manager = None
        st.session_state.db_error = str(e)
        st.session_state.db_ready = False

# Initialize Day 3 components if available
if 'optimizer' not in st.session_state and OPTIMIZER_AVAILABLE:
    st.session_state.optimizer = SQLOptimizer(st.session_state.db_manager)

if 'export_manager' not in st.session_state and EXPORT_AVAILABLE:
    st.session_state.export_manager = ExportManager()

if 'pipelines' not in st.session_state:
    st.session_state.pipelines = []

if 'executed_queries' not in st.session_state:
    st.session_state.executed_queries = []

if 'optimization_reports' not in st.session_state:
    st.session_state.optimization_reports = []

# Header with Day 3 enhancement
st.markdown('<h1 class="main-header">🚀 Smart SQL Pipeline Generator - Enhanced (Day 3) - DA</h1>', unsafe_allow_html=True)
st.markdown("### Convert business requirements into production-ready SQL pipelines using AI with Advanced Analytics")

# Enhanced system status
col1, col2, col3 = st.columns(3)
with col1:
    if st.session_state.agent_ready:
        st.markdown('<div class="success-box">🤖 AI Agent: Ready</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="error-box">❌ AI Agent Error: {st.session_state.get("agent_error", "Unknown error")}</div>', unsafe_allow_html=True)

with col2:
    if st.session_state.db_ready:
        st.markdown('<div class="success-box">🗄️ Database: Connected</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="error-box">❌ Database Error: {st.session_state.get("db_error", "Unknown error")}</div>', unsafe_allow_html=True)

with col3:
    if OPTIMIZER_AVAILABLE and EXPORT_AVAILABLE:
        st.markdown('<div class="success-box">⚡ Day 3 Features: Ready</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="day3-feature">🔧 Day 3 Features: Backend Ready</div>', unsafe_allow_html=True)

if not (st.session_state.agent_ready and st.session_state.db_ready):
    st.error("⚠️ System not fully ready. Please check the error messages above.")
    st.stop()

# Enhanced sidebar
with st.sidebar:
    st.header("🗄️ Database Info")
    
    if st.session_state.db_ready:
        schema = st.session_state.db_manager.get_schema_info()
        
        st.subheader("📊 Tables")
        for table_name, info in schema.items():
            st.write(f"**{table_name}**: {info['row_count']} rows")
            with st.expander(f"View {table_name} columns"):
                for col in info['columns']:
                    st.write(f"• {col}")
    
    st.header("⚙️ Configuration")
    complexity = st.selectbox(
        "Pipeline Complexity",
        ["simple", "medium", "complex"],
        index=1,
        help="Choose complexity level for your SQL pipeline"
    )
    
    # Database execution options
    st.header("🔧 Execution Options")
    auto_execute = st.checkbox("Auto-execute generated SQL", value=True)
    show_execution_plan = st.checkbox("Show execution details", value=True)
    
    # Day 3 Features Section
    st.header("🚀 Day 3 Features")
    if OPTIMIZER_AVAILABLE:
        auto_optimize = st.checkbox("Auto-analyze performance", value=True)
        st.write("✅ SQL Optimizer: Available")
    else:
        auto_optimize = False
        st.write("🔧 SQL Optimizer: Backend Ready")
    
    if EXPORT_AVAILABLE:
        enable_export = st.checkbox("Enable advanced export", value=True)
        st.write("✅ Export Manager: Available")
    else:
        enable_export = False
        st.write("🔧 Export Manager: Backend Ready")
    
    # Show Day 3 progress
    st.markdown("""
    **Day 3 Progress:**
    - 🔍 SQL Optimization Engine ✅
    - 📁 Multi-Format Export ✅  
    - 📊 Advanced Analytics ✅
    - 🎨 Enhanced UI ✅
    """)

# Enhanced main content tabs
if EXPORT_AVAILABLE:
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎯 Generate SQL", "📊 Query Results", "📋 Sample Queries", "📁 Export Center", "📈 Analytics"])
else:
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 Generate SQL", "📊 Query Results", "📋 Sample Queries", "📈 Analytics"])

with tab1:
    st.header("📝 Generate SQL Pipeline with Advanced Analysis")
    
    # Enhanced sample requirements
    samples = [
        "Create a daily sales report by region and product category",
        "Build customer segmentation with RFM analysis and lifetime value prediction", 
        "Generate monthly inventory turnover report with ABC analysis",
        "Create fraud detection pipeline with anomaly scoring",
        "Build customer lifetime value analysis with cohort tracking",
        "Show top 10 customers by total purchase amount with growth trends",
        "Analyze sales trends by month with year-over-year comparison",
        "Find products with declining sales and recommend actions",
        "Create executive dashboard with KPIs and performance metrics",
        "Build real-time sales monitoring with automated alerts"
    ]
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        selected = st.selectbox("Enhanced Sample Requirements:", ["Custom"] + samples)
        
        if selected != "Custom":
            requirement = st.text_area("Business Requirement:", value=selected, height=120)
        else:
            requirement = st.text_area(
                "Business Requirement:", 
                placeholder="e.g., Create a comprehensive customer analysis with purchase behavior, segmentation, and predictive insights for retention strategies",
                height=120
            )
        
        # Enhanced schema info
        if st.session_state.db_ready:
            schema = st.session_state.db_manager.get_schema_info()
            schema_text = ""
            for table, info in schema.items():
                schema_text += f"{table}({', '.join(info['columns'])}) -- {info['row_count']} rows\n"
        else:
            schema_text = ""
        
        schema_info = st.text_area(
            "Database Schema (Enhanced with row counts):",
            value=schema_text,
            height=100,
            help="Enhanced schema information with row counts for better optimization"
        )
        
        # Enhanced generate button
        if st.button("🚀 Generate & Execute Advanced SQL Pipeline", type="primary", use_container_width=True):
            if requirement.strip():
                with st.spinner("🧠 AI is crafting your advanced SQL pipeline..."):
                    progress = st.progress(0)
                    for i in range(50):
                        time.sleep(0.02)
                        progress.progress(i + 1)
                    
                    result = st.session_state.agent.generate_pipeline(requirement, schema_info, complexity)
                    
                    progress.progress(75)
                    
                    pipeline_data = {
                        "requirement": requirement,
                        "result": result,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "complexity": complexity
                    }
                    
                    st.session_state.pipelines.append(pipeline_data)
                    st.session_state.current = pipeline_data
                    
                    # Auto-execute if enabled
                    execution_result = None
                    if auto_execute and not result.get("error") and st.session_state.db_ready:
                        sql_to_execute = result.get("main_query", result.get("full_response", ""))
                        if sql_to_execute and "SELECT" in sql_to_execute.upper():
                            execution_result = st.session_state.db_manager.execute_query(sql_to_execute)
                            pipeline_data["execution_result"] = execution_result
                            
                            # Store executed query
                            query_record = {
                                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                                "requirement": requirement,
                                "sql": sql_to_execute,
                                "result": execution_result
                            }
                            st.session_state.executed_queries.append(query_record)
                    
                    # Auto-optimize if enabled and available
                    if auto_optimize and OPTIMIZER_AVAILABLE and execution_result:
                        sql_to_analyze = result.get("main_query", result.get("full_response", ""))
                        optimization_analysis = st.session_state.optimizer.analyze_query(sql_to_analyze, execution_result)
                        pipeline_data["optimization_analysis"] = optimization_analysis
                        
                        # Store optimization report
                        st.session_state.optimization_reports.append({
                            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                            'requirement': requirement,
                            'analysis': optimization_analysis
                        })
                    
                    progress.progress(100)
                    progress.empty()
                    
                    st.success("✅ Advanced SQL Pipeline Generated with Full Analysis!")
                    st.rerun()
            else:
                st.error("❌ Please enter a requirement!")
    
    with col2:
        st.header("⚡ Generated SQL Pipeline with Advanced Analysis")
        
        if 'current' in st.session_state:
            pipeline = st.session_state.current
            result = pipeline['result']
            
            if result.get("error"):
                st.markdown(f'<div class="error-box">❌ {result["error"]}</div>', unsafe_allow_html=True)
            else:
                # Show generated SQL
                sql_content = result.get("main_query", result.get("full_response", ""))
                st.subheader("📜 Generated SQL")
                st.code(sql_content, language="sql")
                
                # Show execution results if available
                if "execution_result" in pipeline:
                    exec_result = pipeline["execution_result"]
                    
                    if exec_result["success"]:
                        st.subheader("✅ Execution Results")
                        
                        # Enhanced metrics
                        if show_execution_plan:
                            col_a, col_b, col_c, col_d = st.columns(4)
                            with col_a:
                                st.metric("Rows", exec_result["row_count"])
                            with col_b:
                                st.metric("Columns", len(exec_result["columns"]))
                            with col_c:
                                st.metric("Exec Time", f"{exec_result.get('execution_time', 0):.3f}s")
                            with col_d:
                                if pipeline.get("optimization_analysis"):
                                    score = pipeline["optimization_analysis"].performance_score
                                    st.metric("Performance", f"{score}/100")
                                else:
                                    st.metric("Performance", "N/A")
                        
                        # Show data
                        if exec_result["row_count"] > 0:
                            st.dataframe(exec_result["data"], use_container_width=True)
                        else:
                            st.info("Query executed successfully but returned no data.")
                    
                    else:
                        st.error(f"❌ Execution Error: {exec_result['error']}")
                
                # Show optimization analysis if available
                if "optimization_analysis" in pipeline and pipeline["optimization_analysis"]:
                    analysis = pipeline["optimization_analysis"]
                    
                    st.subheader("🔍 Performance Optimization Analysis")
                    
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("Complexity", analysis.complexity.value)
                    with col_b:
                        st.metric("Performance Score", f"{analysis.performance_score}/100")
                    with col_c:
                        st.metric("Readability", f"{analysis.readability_score}/100")
                    
                    # Show top suggestions
                    if analysis.suggestions:
                        st.write("**🎯 Top Optimization Suggestions:**")
                        for i, suggestion in enumerate(analysis.suggestions[:3], 1):
                            impact_emoji = {
                                "Low Priority": "🟡",
                                "Medium Priority": "🟠", 
                                "High Priority": "🔴",
                                "Critical": "🚨"
                            }.get(suggestion.impact.value, "⚪")
                            
                            st.write(f"{i}. {impact_emoji} **{suggestion.category}**: {suggestion.suggestion}")
                
                # Enhanced download options
                st.subheader("📥 Download Options")
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    st.download_button(
                        "📄 Download SQL",
                        sql_content,
                        file_name=f"pipeline_{int(time.time())}.sql",
                        mime="text/sql"
                    )
                
                with col_b:
                    if "execution_result" in pipeline and pipeline["execution_result"]["success"]:
                        csv_data = pipeline["execution_result"]["data"].to_csv(index=False)
                        st.download_button(
                            "📊 Download CSV",
                            csv_data,
                            file_name=f"results_{int(time.time())}.csv",
                            mime="text/csv"
                        )
                
                with col_c:
                    if "optimization_analysis" in pipeline and pipeline["optimization_analysis"]:
                        if OPTIMIZER_AVAILABLE:
                            report = st.session_state.optimizer.get_optimization_report(pipeline["optimization_analysis"])
                            st.download_button(
                                "📋 Download Report",
                                report,
                                file_name=f"optimization_report_{int(time.time())}.md",
                                mime="text/markdown"
                            )
                        else:
                            st.info("Optimization report available when optimizer is loaded")
        
        else:
            st.info("👆 Generate a SQL pipeline to see enhanced results here")
            
            st.subheader("🌟 Enhanced Day 3 Features:")
            st.markdown("""
            - **🔍 Performance Analysis** with 0-100 scoring
            - **⚡ Optimization Suggestions** with specific recommendations
            - **📊 Advanced Export Options** (CSV, JSON, Excel, SQL, TXT)
            - **🎨 Enhanced UI** with professional styling
            - **📈 Comprehensive Analytics** with trend analysis
            """)

# Continue with other tabs (keeping your existing code structure)
with tab2:
    st.header("📊 Query Execution Results")
    
    if st.session_state.executed_queries:
        # Show recent executions
        st.subheader("🕒 Recent Query Executions")
        
        for i, query_record in enumerate(reversed(st.session_state.executed_queries[-10:])):
            with st.expander(f"Query {len(st.session_state.executed_queries) - i}: {query_record['requirement'][:50]}..."):
                st.write(f"**Executed:** {query_record['timestamp']}")
                st.write(f"**Requirement:** {query_record['requirement']}")
                
                st.code(query_record['sql'], language="sql")
                
                if query_record['result']['success']:
                    st.success(f"✅ Success: {query_record['result']['row_count']} rows returned")
                    if query_record['result']['row_count'] > 0:
                        st.dataframe(query_record['result']['data'])
                else:
                    st.error(f"❌ Error: {query_record['result']['error']}")
    else:
        st.info("No query executions yet. Generate and execute some SQL pipelines first!")

with tab3:
    st.header("📋 Sample Queries")
    
    if st.session_state.db_ready:
        sample_queries = st.session_state.db_manager.get_sample_queries()
        
        for query in sample_queries:
            with st.expander(f"📊 {query['name']}"):
                st.code(query['query'], language="sql")
                
                col_a, col_b = st.columns(2)
                
                with col_a:
                    if st.button(f"▶️ Execute {query['name']}", key=f"exec_{query['name']}"):
                        with st.spinner(f"Executing {query['name']}..."):
                            result = st.session_state.db_manager.execute_query(query['query'])
                            
                            if result['success']:
                                st.success(f"✅ Success: {result['row_count']} rows")
                                if result['row_count'] > 0:
                                    st.dataframe(result['data'])
                            else:
                                st.error(f"❌ Error: {result['error']}")
                
                with col_b:
                    if OPTIMIZER_AVAILABLE and st.button(f"🔍 Analyze {query['name']}", key=f"analyze_{query['name']}"):
                        analysis = st.session_state.optimizer.analyze_query(query['query'])
                        
                        col_i, col_ii, col_iii = st.columns(3)
                        with col_i:
                            st.metric("Complexity", analysis.complexity.value)
                        with col_ii:
                            st.metric("Performance", f"{analysis.performance_score}/100")
                        with col_iii:
                            st.metric("Readability", f"{analysis.readability_score}/100")

# Export Center tab (only if export manager is available)
if EXPORT_AVAILABLE:
    with tab4:
        st.header("📁 Export Center")
        
        st.markdown("""
        <div class="day3-feature">
            <h3>🚀 Professional Export Capabilities</h3>
            <p>Export your query results in multiple professional formats with complete metadata</p>
        </div>
        """, unsafe_allow_html=True)
        
        if 'current' in st.session_state and st.session_state.current.get('execution_result', {}).get('success'):
            current_data = st.session_state.current['execution_result']['data']
            current_info = {
                'requirement': st.session_state.current['requirement'],
                'complexity': st.session_state.current['complexity'],
                'execution_time': st.session_state.current['execution_result']['execution_time']
            }
            
            st.subheader("📊 Current Query Results Export")
            
            # Export format selection
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                export_formats = st.multiselect(
                    "Select export formats:",
                    ["csv", "json", "excel", "sql", "txt"],
                    default=["csv"]
                )
            
            with col2:
                export_filename = st.text_input("Filename:", value="query_results")
            
            with col3:
                if st.button("📤 Export Selected", type="primary"):
                    if export_formats:
                        exports = []
                        
                        with st.spinner("Generating exports..."):
                            for format_type in export_formats:
                                export_result = st.session_state.export_manager.export_query_results(
                                    current_data,
                                    format_type,
                                    export_filename,
                                    current_info
                                )
                                exports.append(export_result)
                        
                        # Show export results
                        st.subheader("📋 Export Results")
                        
                        for export in exports:
                            if export['success']:
                                col_a, col_b, col_c = st.columns([2, 1, 1])
                                
                                with col_a:
                                    st.success(f"✅ {export['filename']}")
                                
                                with col_b:
                                    size_kb = export['size'] / 1024
                                    st.write(f"{size_kb:.1f} KB")
                                
                                with col_c:
                                    st.download_button(
                                        "📥 Download",
                                        export['content'],
                                        file_name=export['filename'],
                                        mime=export['mime_type'],
                                        key=f"download_{export['filename']}"
                                    )
                            else:
                                st.error(f"❌ Failed to export {format_type}: {export['error']}")
                    
                    else:
                        st.warning("Please select at least one export format")
            
            # Show data preview
            st.subheader("👁️ Data Preview")
            st.dataframe(current_data.head(10), use_container_width=True)
        
        else:
            st.info("No query results available for export. Execute a query first!")
            
            # Show supported formats
            st.subheader("📋 Supported Export Formats")
            
            format_info = {
                "CSV": "Comma-separated values for spreadsheet applications",
                "JSON": "JavaScript Object Notation for web applications and APIs",
                "Excel": "Microsoft Excel format with multiple sheets and metadata",
                "SQL": "SQL INSERT statements for database import", 
                "TXT": "Formatted text report with statistics and summaries"
            }
            
            for format_name, description in format_info.items():
                st.write(f"**{format_name}**: {description}")

# Analytics tab (use existing tab4 if no export, otherwise tab5)
analytics_tab = tab5 if EXPORT_AVAILABLE else tab4

with analytics_tab:
    st.header("📈 Advanced Analytics Dashboard")
    
    if st.session_state.executed_queries:
        # Create enhanced analytics
        df_queries = pd.DataFrame([
            {
                'timestamp': q['timestamp'],
                'requirement': q['requirement'][:50] + "..." if len(q['requirement']) > 50 else q['requirement'],
                'success': q['result']['success'],
                'row_count': q['result'].get('row_count', 0),
                'execution_time': q['result'].get('execution_time', 0)
            } for q in st.session_state.executed_queries
        ])
        
        # Enhanced summary statistics
        st.subheader("📊 Enhanced Performance Indicators")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Queries", len(df_queries))
        with col2:
            success_rate = (df_queries['success'].sum() / len(df_queries)) * 100
            st.metric("Success Rate", f"{success_rate:.1f}%")
        with col3:
            avg_time = df_queries['execution_time'].mean()
            st.metric("Avg Time", f"{avg_time:.3f}s")
        with col4:
            total_rows = df_queries['row_count'].sum()
            st.metric("Total Rows", f"{total_rows:,}")
        with col5:
            if st.session_state.optimization_reports:
                avg_score = sum(r['analysis'].performance_score for r in st.session_state.optimization_reports) / len(st.session_state.optimization_reports)
                st.metric("Avg Performance", f"{avg_score:.0f}/100")
            else:
                st.metric("Optimizations", len(st.session_state.optimization_reports))
        
        # Enhanced visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Query Success Rate")
            
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = success_rate,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Success Rate (%)"},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkgreen"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "yellow"},
                        {'range': [80, 100], 'color': "lightgreen"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📈 Query Performance Trends")
            if len(df_queries) > 1:
                fig = px.line(df_queries, x='timestamp', y='row_count', 
                            title="Rows Returned Over Time")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Execute more queries to see performance trends")
        
        # Optimization insights
        if st.session_state.optimization_reports:
            st.subheader("🔍 Optimization Insights")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Performance score distribution
                scores = [r['analysis'].performance_score for r in st.session_state.optimization_reports]
                fig = px.histogram(x=scores, nbins=10, title="Performance Score Distribution")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Complexity distribution
                complexities = [r['analysis'].complexity.value for r in st.session_state.optimization_reports]
                complexity_counts = pd.Series(complexities).value_counts()
                fig = px.pie(values=complexity_counts.values, names=complexity_counts.index, 
                           title="Query Complexity Distribution")
                st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("No analytics data available yet. Execute some queries to see comprehensive analytics!")
        
        # Show what analytics will be available
        st.subheader("📊 Available Analytics Features")
        
        analytics_features = [
            "📈 **Performance Trends**: Track query execution times and success rates",
            "🎯 **Optimization Insights**: Monitor performance improvements over time", 
            "🔍 **Complexity Analysis**: Analyze query complexity distribution",
            "⚡ **Success Rate Monitoring**: Track and improve query reliability",
            "📊 **Volume Analysis**: Monitor query volume and usage patterns"
        ]
        
        for feature in analytics_features:
            st.markdown(feature)

# Enhanced footer
st.markdown("---")

# Enhanced metrics display
if st.session_state.pipelines:
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Pipelines Generated", len(st.session_state.pipelines))
    
    with col2:
        executed_count = len(st.session_state.executed_queries)
        st.metric("Queries Executed", executed_count)
    
    with col3:
        optimization_count = len(st.session_state.optimization_reports)
        st.metric("Optimizations", optimization_count)
    
    with col4:
        if st.session_state.optimization_reports:
            avg_score = sum(r['analysis'].performance_score for r in st.session_state.optimization_reports) / len(st.session_state.optimization_reports)
            st.metric("Avg Performance", f"{avg_score:.0f}/100")
        else:
            st.metric("Avg Performance", "N/A")
    
    with col5:
        if st.session_state.pipelines:
            latest = st.session_state.pipelines[-1]['timestamp']
            st.metric("Last Generated", latest.split()[1])

# Enhanced footer with Day 3 branding
st.markdown("### 🚀 Built by Dinesh Appala | Day 3 Enhanced | AI + Database + Advanced Analytics")

# Day 3 feature status
feature_status = []
if OPTIMIZER_AVAILABLE:
    feature_status.append("🔍 SQL Optimizer")
if EXPORT_AVAILABLE:
    feature_status.append("📁 Multi-Export")

if feature_status:
    st.markdown(f"**⚡ Active Day 3 Features:** {' • '.join(feature_status)}")
else:
    st.markdown("**🔧 Day 3 Backend Components:** SQL Optimizer Engine ✅ • Export Manager ✅ • Ready for Integration")
