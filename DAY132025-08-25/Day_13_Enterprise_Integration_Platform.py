@echo off
echo 🚀 Starting Smart SQL Day 13 - Enterprise Integration Platform
echo ================================================================

echo.
echo 📋 Activating virtual environment...
call venv\Scripts\activate

echo.
echo 📦 Installing additional dependencies...
pip install fastapi uvicorn redis httpx PyJWT sqlalchemy python-multipart

echo.
echo 🧪 Running tests...
cd src
python ..\test_day13.py

echo.
echo ⏳ Starting Redis (Docker) - if Docker is available...
docker run -d -p 6379:6379 --name smart-sql-redis redis:latest 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✅ Redis started successfully!
) else (
    echo ⚠️  Redis not started - Dashboard will work with mock data
)

echo.
echo 🔥 Starting API Server...
start cmd /k "title Smart SQL API Server && python day13_integration_engine.py"

echo.
echo ⏳ Waiting 3 seconds for API server to start...
timeout /t 3 /nobreak > nul

echo.
echo 🎨 Starting Dashboard...
start cmd /k "title Smart SQL Dashboard && streamlit run day13_integration_interface.py"

echo.
echo 🌐 Opening browser windows...
timeout /t 2 /nobreak > nul
start http://localhost:8501
start http://localhost:8000/docs

echo.
echo ================================================================
echo 🎉 Day 13 Enterprise Integration Platform Started!
echo ================================================================
echo 📊 Dashboard: http://localhost:8501
echo 🔗 API Docs: http://localhost:8000/docs
echo 📋 API Base: http://localhost:8000/api/v1
echo ================================================================
echo.
echo Press any key to close this window...
pause > nul