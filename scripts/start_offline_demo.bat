@echo off
setlocal enabledelayedexpansion

echo ===============================================================================
echo         CONFIGIQ - SOVEREIGN ON-PREMISE AGENTIC AI WORKBENCH
echo                   OFFLINE DEMO LAUNCHER (AIR-GAPPED)
echo ===============================================================================
echo.
echo Internet connection is NOT required.
echo.

:: Step 1: Run comprehensive pre-demo offline check
echo [1/4] Running Pre-Flight Offline Dependency Check...
python scripts\run_offline_demo_check.py
if %errorlevel% neq 0 (
    echo [ERROR] Offline readiness check failed. Please resolve above issues before proceeding.
    pause
    exit /b 1
)

:: Step 2: Set Offline Environment variables
set LLM_PROVIDER=ollama
set OLLAMA_BASE_URL=http://localhost:11434
set GENERAL_MODEL=llama3:latest
set CODING_MODEL=qwen2.5-coder:7b
set CODING_HEAVY_MODEL=qwen2.5-coder:14b
set VISION_MODEL=moondream:latest
set EMBEDDING_MODEL=nomic-embed-text:latest
set ENVIRONMENT=on-premise / air-gapped

:: Step 3: Start Backend API (Port 8000)
echo [2/4] Starting Sovereign FastAPI Backend on port 8000...
start "ConfigIQ Sovereign Backend" cmd /k "python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000"

:: Wait for backend to bind
timeout /t 3 /nobreak >nul

:: Step 4: Start Frontend Console (Port 5173)
echo [3/4] Starting ConfigIQ Web Console on port 5173...
cd frontend
start "ConfigIQ Web Console" cmd /k "npm run dev"
cd ..

:: Wait for frontend to start
timeout /t 2 /nobreak >nul

:: Step 5: Final summary and open browser
echo.
echo ====================================
echo CONFIGIQ SOVEREIGN AI WORKBENCH
echo OFFLINE DEMO
echo ====================================
echo.
echo Internet connection is NOT required.
echo.
echo Ollama:
echo http://localhost:11434
echo.
echo Backend:
echo http://localhost:8000
echo.
echo Frontend:
echo http://localhost:5173
echo.
echo Models:
echo [x] llama3
echo [x] qwen2.5-coder:7b
echo [x] qwen2.5-coder:14b
echo [x] moondream
echo [x] nomic-embed-text
echo.
echo STATUS: READY FOR OFFLINE DEMO
echo ====================================
echo.

start http://localhost:5173

endlocal
