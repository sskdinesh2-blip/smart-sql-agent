#!/bin/bash
echo "Starting Smart SQL Agent Pro - Day 7 Multi-User System"
echo

# Start API server in background
echo "Starting API Server..."
python -m uvicorn enhanced_api_server:app --reload --port 8000 &
API_PID=$!

# Wait a moment for API to start
sleep 3

# Start Streamlit interface
echo "Starting Streamlit Interface..."
streamlit run day7_complete_interface.py --server.port 8501 &
STREAMLIT_PID=$!

echo
echo "Both services are running:"
echo "API Server: http://localhost:8000"
echo "Web Interface: http://localhost:8501"
echo "API Documentation: http://localhost:8000/docs"
echo
echo "Press Ctrl+C to stop both services"

# Wait for interrupt
trap 'kill $API_PID $STREAMLIT_PID; exit' INT
wait
