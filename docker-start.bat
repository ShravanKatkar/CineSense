@echo off
title CineSense Production Docker Launcher
cls

echo ======================================================================
echo          CineSense AI Movie Recommendation System (Docker)
echo ======================================================================
echo.

:: 1. Ensure Docker CLI is accessible
where docker >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    if exist "C:\Program Files\Docker\Docker\resources\bin\docker.exe" (
        set "PATH=C:\Program Files\Docker\Docker\resources\bin;%PATH%"
    ) else (
        echo [ERROR] Docker CLI not found! Please install Docker Desktop from:
        echo         https://www.docker.com/products/docker-desktop/
        echo.
        pause
        exit /b 1
    )
)

:: 2. Check if Docker Daemon Engine is running
docker info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Docker Desktop daemon is not currently active.
    if exist "C:\Program Files\Docker\Docker\Docker Desktop.exe" (
        echo [INFO] Launching Docker Desktop...
        start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
        echo [INFO] Waiting for Docker engine to initialize (this may take 20-30 seconds)...
        
        :wait_loop
        timeout /t 5 /nobreak >nul
        docker info >nul 2>&1
        if %ERRORLEVEL% EQU 0 goto docker_ready
        echo        Still waiting for Docker daemon...
        goto wait_loop
    ) else (
        echo [ERROR] Could not connect to Docker daemon. Please launch Docker Desktop manually.
        pause
        exit /b 1
    )
)

:docker_ready
echo [SUCCESS] Docker daemon is online and responsive!
echo.

:: 3. Check for .env file
if not exist ".env" (
    if exist ".env.example" (
        echo [INFO] Creating .env from .env.example...
        copy .env.example .env >nul
    )
)

:: 4. Build and start production containers
echo ======================================================================
echo  Building and starting CineSense production container stack:
echo    - PostgreSQL 16 + pgvector (Port 5432)
echo    - Redis 7 In-Memory Cache (Port 6379)
echo    - CineSense App: FastAPI + React 19 SPA (Port 8000)
echo ======================================================================
echo.

docker compose up --build -d

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Docker compose failed to start containers.
    pause
    exit /b 1
)

echo.
echo ======================================================================
echo [SUCCESS] All CineSense containers are running in production mode!
echo ======================================================================
echo.
echo  - Web Application:       http://localhost:8000
echo  - Interactive API Docs:  http://localhost:8000/docs
echo  - System Health:         http://localhost:8000/api/v1/health
echo  - Cache & Worker Status: http://localhost:8000/api/v1/system/status
echo.
echo To view container logs:   docker compose logs -f backend
echo To stop containers:       docker compose down
echo ======================================================================
echo.
pause
