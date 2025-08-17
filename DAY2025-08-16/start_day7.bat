@echo off
echo Starting Smart SQL Agent Pro - Day 7 Multi-User System
echo.

echo Starting API Server...
start "API Server" cmd /k "cd /d %~dp0 && python -m uvicorn enhanced_api_server:app --reload --port 8000"

timeout /t 3

echo Starting Streamlit Interface...
start "Streamlit App" cmd /k "cd /d %~dp0 && streamlit run day7_complete_interface.py --server.port 8501"

echo.
echo Both services are starting...
echo API Server: http://localhost:8000
echo Web Interface: http://localhost:8501
echo API Documentation: http://localhost:8000/docs
pause
