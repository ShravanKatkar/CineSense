@echo off
title CineSense AI Movie Recommendation Engine Launcher
cls

echo ======================================================================
echo             CineSense AI Movie Recommendation System
echo ======================================================================
echo.

set UV_PATH=C:\Users\shara\.local\bin\uv.exe

if not exist "%UV_PATH%" (
    echo [ERROR] uv package manager not found at %UV_PATH%
    pause
    exit /b 1
)

echo Cleaning up any lingering processes on ports 8000 and 5173...
powershell -Command "$p = Get-NetTCPConnection -LocalPort 8000,5173 -ErrorAction SilentlyContinue; foreach ($i in $p) { if ($i.OwningProcess -gt 0) { Stop-Process -Id $i.OwningProcess -Force -ErrorAction SilentlyContinue } }"

timeout /t 1 /nobreak >nul

echo.
echo [1/2] Launching FastAPI Backend Server on http://localhost:8000...
start "CineSense FastAPI Backend (Port 8000)" cmd /k "cd backend && "%UV_PATH%" run python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo [2/2] Launching Vite React Frontend Server on http://localhost:5173...
start "CineSense React Frontend (Port 5173)" cmd /k "cd frontend && npm run dev"

echo.
echo ======================================================================
echo  Both backend and frontend servers are launching in separate windows!
echo  Access the CineSense Web App at: http://localhost:5173
echo  Access the FastAPI API Docs at:   http://localhost:8000/docs
echo ======================================================================
echo.
pause
