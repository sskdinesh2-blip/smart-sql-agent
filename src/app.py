"""
Smart SQL Pipeline Generator - Streamlit Web Interface
"""
import streamlit as st
import sys
import os

# Add src directory to path
sys.path.append(os.path.dirname(__file__))

from sql_agent import SQLPipelineAgent
import time

# Page config
st.set_page_config(
    page_title="Smart SQL Agent",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
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

if 'pipelines' not in st.session_state:
    st.session_state.pipelines = []

# Header
st.markdown('<h1 class="main-header">🤖 ADK Smart SQL Pipeline Generator</h1>', unsafe_allow_html=True)
st.markdown("### Convert business requirements into production-ready SQL pipelines using AI")

# Check if agent is ready
if not st.session_state.agent_ready:
    st.error(f"❌ Failed to initialize AI agent: {st.session_state.get('agent_error', 'Unknown error')}")
    st.markdown("""
    **Fix this by:**
    1. Check your `.env` file contains: `OPENAI_API_KEY=sk-your-key-here`
    2. Make sure your OpenAI API key is valid
    3. Restart the application
    """)
    st.stop()

# Main interface
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📝 Input Requirements")
    
    # Sample requirements
    samples = [
        "Create a daily sales report by region and product category",
        "Build customer segmentation with RFM analysis", 
        "Generate monthly inventory turnover report",
        "Create fraud detection pipeline",
        "Build customer lifetime value analysis"
    ]
    
    selected = st.selectbox("Sample Requirements:", ["Custom"] + samples)
    
    if selected != "Custom":
        requirement = st.text_area("Business Requirement:", value=selected, height=100)
    else:
        requirement = st.text_area(
            "Business Requirement:", 
            placeholder="e.g., Create a daily customer report with purchase behavior analysis",
            height=100
        )
    
    schema_info = st.text_area(
        "Database Schema (Optional):",
        placeholder="customers(id, name, email)\norders(id, customer_id, amount, date)",
        height=60
    )
    
    complexity = st.selectbox("Complexity:", ["simple", "medium", "complex"], index=1)
    
    # Generate button
    if st.button("🚀 Generate SQL Pipeline", type="primary", use_container_width=True):
        if requirement.strip():
            with st.spinner("🧠 AI is generating your SQL pipeline..."):
                progress = st.progress(0)
                for i in range(100):
                    time.sleep(0.01)
                    progress.progress(i + 1)
                
                result = st.session_state.agent.generate_pipeline(requirement, schema_info, complexity)
                
                pipeline_data = {
                    "requirement": requirement,
                    "result": result,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                st.session_state.pipelines.append(pipeline_data)
                st.session_state.current = pipeline_data
                
                progress.empty()
                st.success("✅ SQL Pipeline Generated!")
                st.rerun()
        else:
            st.error("❌ Please enter a requirement!")

with col2:
    st.header("⚡ Generated SQL Pipeline")
    
    if 'current' in st.session_state:
        pipeline = st.session_state.current
        result = pipeline['result']
        
        if result.get("error"):
            st.error(f"❌ {result['error']}")
        else:
            # Tabs for different sections
            tab1, tab2, tab3 = st.tabs(["📜 SQL Query", "📊 Info", "💾 Download"])
            
            with tab1:
                st.subheader("Generated SQL")
                sql_content = result.get("main_query", result.get("full_response", "No SQL generated"))
                st.code(sql_content, language="sql")
            
            with tab2:
                st.subheader("Pipeline Info")
                st.write(f"**Requirement:** {pipeline['requirement']}")
                st.write(f"**Generated:** {pipeline['timestamp']}")
                st.write(f"**Status:** ✅ Ready for use")
                
                if result.get("optimization"):
                    st.write("**Optimization Tips:**")
                    st.write(result["optimization"])
            
            with tab3:
                st.subheader("Download SQL")
                sql_content = result.get("main_query", result.get("full_response", ""))
                if sql_content:
                    st.download_button(
                        "📥 Download SQL File",
                        sql_content,
                        file_name=f"pipeline_{int(time.time())}.sql",
                        mime="text/sql"
                    )
                else:
                    st.info("No SQL available for download")
    else:
        st.info("👆 Generate a SQL pipeline to see results here")
        
        st.subheader("🌟 What You'll Get:")
        st.markdown("""
        - **Production-ready SQL** with proper formatting
        - **Data validation** and quality checks
        - **Performance optimization** suggestions
        - **Download capability** for your files
        """)

# Footer
st.markdown("---")
if st.session_state.pipelines:
    st.write(f"**Total Pipelines Generated:** {len(st.session_state.pipelines)}")

st.markdown("### 🎯 Built for Data Engineers | Powered by OpenAI GPT-4")