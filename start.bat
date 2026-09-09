@echo off
setlocal enabledelayedexpansion

echo ===============================================================================
echo         CONFIGIQ - SOVEREIGN ON-PREMISE AGENTIC AI WORKBENCH
echo                  Air-Gapped Industrial AI Deployment (PS 26117)
echo ===============================================================================
echo.

set MODE=native
if "%1"=="--docker" set MODE=docker
if "%1"=="-d" set MODE=docker

if "%MODE%"=="docker" (
    echo [INFO] Launching ConfigIQ in Isolated Docker Containers...
    docker-compose up -d --build
    if %errorlevel% neq 0 (
        echo [ERROR] Docker Compose failed to start.
        exit /b %errorlevel%
    )
    echo [SUCCESS] ConfigIQ Services are running in Docker:
    echo   - Web Console: http://localhost:5173
    echo   - Backend API: http://localhost:8000
    echo   - API Docs:    http://localhost:8000/docs
    echo   - Ollama:      http://localhost:11434
    echo.
    start http://localhost:5173
    goto :end
)

echo [INFO] Launching ConfigIQ in Native Local Mode...
echo.

:: 1. Verify / Start Backend
echo [1/3] Starting Sovereign Backend on port 8000...
start "ConfigIQ Backend (Port 8000)" cmd /k "uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

:: 2. Wait for Backend initialization
echo [2/3] Waiting for Backend to be healthy...
timeout /t 3 /nobreak >nul

:: 3. Start Frontend Dashboard
echo [3/3] Starting Sovereign Operations Console on port 5173...
cd frontend
start "ConfigIQ Web Console (Port 5173)" cmd /k "npm run dev"
cd ..

echo.
echo ===============================================================================
echo  ConfigIQ Workbench successfully initialized in 100%% Local / Air-Gapped Mode!
echo  Access Web Dashboard at: http://localhost:5173
echo  Access Swagger API at:   http://localhost:8000/docs
echo ===============================================================================
echo.

:: Open browser
start http://localhost:5173

:end
endlocal
