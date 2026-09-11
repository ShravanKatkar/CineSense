#!/usr/bin/env bash
set -e

echo "======================================================================"
echo "          CineSense AI Movie Recommendation System (Docker)"
echo "======================================================================"
echo ""

# 1. Verify Docker CLI
if ! command -v docker >/dev/null 2>&1; then
    echo "[ERROR] Docker is not installed or not in PATH."
    exit 1
fi

# 2. Verify Docker Daemon
if ! docker info >/dev/null 2>&1; then
    echo "[ERROR] Docker daemon is not running. Please start Docker."
    exit 1
fi

echo "[SUCCESS] Docker daemon is active."

# 3. Check for .env file
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo "[INFO] Creating .env from .env.example..."
    cp .env.example .env
fi

# 4. Build and start containers
echo "Building and launching containers..."
docker compose up --build -d

echo ""
echo "======================================================================"
echo "[SUCCESS] CineSense production containers are running!"
echo "  - Web App:              http://localhost:8000"
echo "  - API Docs:             http://localhost:8000/docs"
echo "  - System Health:        http://localhost:8000/api/v1/health"
echo "  - System Diagnostics:   http://localhost:8000/api/v1/system/status"
echo "======================================================================"
