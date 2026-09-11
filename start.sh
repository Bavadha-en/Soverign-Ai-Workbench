#!/usr/bin/env bash
# ===============================================================================
#         CONFIGIQ - SOVEREIGN ON-PREMISE AGENTIC AI WORKBENCH
#                  Air-Gapped Industrial AI Deployment (PS 26117)
# ===============================================================================

set -e

COLOR_CYAN='\033[0;36m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_RED='\033[0;31m'
COLOR_NC='\033[0m' # No Color

echo -e "${COLOR_CYAN}"
echo "==============================================================================="
echo "        CONFIGIQ - SOVEREIGN ON-PREMISE AGENTIC AI WORKBENCH"
echo "                 Air-Gapped Industrial AI Deployment (PS 26117)"
echo "==============================================================================="
echo -e "${COLOR_NC}"

MODE="native"
if [ "$1" == "--docker" ] || [ "$1" == "-d" ]; then
    MODE="docker"
fi

if [ "$MODE" == "docker" ]; then
    echo -e "${COLOR_YELLOW}[INFO] Launching ConfigIQ in Isolated Docker Containers...${COLOR_NC}"
    docker-compose up -d --build
    echo -e "${COLOR_GREEN}[SUCCESS] ConfigIQ is active in Docker containers:${COLOR_NC}"
    echo "  - Operations Console: http://localhost:5173"
    echo "  - Backend API:        http://localhost:8000"
    echo "  - API Documentation:  http://localhost:8000/docs"
    exit 0
fi

echo -e "${COLOR_YELLOW}[INFO] Launching ConfigIQ in Native Local Mode...${COLOR_NC}"

# 1. Start backend in background
echo -e "${COLOR_CYAN}[1/2] Starting Sovereign Backend (Port 8000)...${COLOR_NC}"
python3 -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

trap "echo -e '${COLOR_RED}Stopping ConfigIQ...${COLOR_NC}'; kill $BACKEND_PID 2>/dev/null || true; exit 0" SIGINT SIGTERM EXIT

# 2. Wait briefly for backend
sleep 2

# 3. Start frontend
echo -e "${COLOR_CYAN}[2/2] Starting Sovereign Operations Console (Port 5173)...${COLOR_NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!

echo -e "${COLOR_GREEN}"
echo "==============================================================================="
echo " ConfigIQ Workbench successfully initialized in 100% Local / Air-Gapped Mode!"
echo " Operations Console: http://localhost:5173"
echo " API Docs (Swagger): http://localhost:8000/docs"
echo "==============================================================================="
echo -e "${COLOR_NC}"

wait $FRONTEND_PID $BACKEND_PID
