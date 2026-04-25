@echo off
REM Docker Build and Validation Script for VAPT Toolkit (Windows)

setlocal enabledelayedexpansion

echo.
echo ================================================
echo   VAPT Toolkit - Docker Build and Validation
echo ================================================
echo.

REM Check prerequisites
echo [1/6] Checking prerequisites...

docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed
    exit /b 1
)

docker ps >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker daemon is not running
    exit /b 1
)

echo [OK] Docker installed and running

REM Validate files exist
echo.
echo [2/6] Validating configuration files...

setlocal enabledelayedexpansion
set FILES=Dockerfile docker-compose.yml .dockerignore requirements.txt
for %%F in (!FILES!) do (
    if exist %%F (
        echo [OK] %%F exists
    ) else (
        echo [ERROR] %%F not found
        exit /b 1
    )
)

if not exist ".env" (
    echo [INFO] Creating .env from .env.example...
    copy .env.example .env >nul
)
echo [OK] .env configured

REM Build images
echo.
echo [3/6] Building Docker images...
echo [INFO] This may take a few minutes...

docker compose build --no-cache
if errorlevel 1 (
    echo [ERROR] Build failed
    exit /b 1
)
echo [OK] Docker images built

REM Start services
echo.
echo [4/6] Starting services...

docker compose up -d
if errorlevel 1 (
    echo [ERROR] Failed to start services
    exit /b 1
)

echo [INFO] Waiting for services to start (30 seconds)...
timeout /t 10 /nobreak >nul

echo.
echo [5/6] Verifying service health...

docker compose ps | find "vapt-web" >nul
if errorlevel 1 (
    echo [ERROR] vapt-web container not running
    docker compose logs vapt-web
    exit /b 1
)
echo [OK] vapt-web container running

docker compose ps | find "vapt-frontend" >nul
if errorlevel 1 (
    echo [WARNING] vapt-frontend may still be building
) else (
    echo [OK] vapt-frontend container running
)

REM Test API connectivity
echo.
echo [INFO] Testing API connectivity...

set API_AVAILABLE=0
for /l %%i in (1,1,5) do (
    curl -s http://localhost:8000/api/health >nul 2>&1
    if errorlevel 0 (
        set API_AVAILABLE=1
        goto :api_ready
    )
    echo [INFO] Attempt %%i/5...
    timeout /t 5 /nobreak >nul
)

:api_ready
if !API_AVAILABLE! equ 1 (
    echo [OK] API responding at http://localhost:8000
) else (
    echo [ERROR] API not responding
    echo [INFO] Container logs:
    docker compose logs vapt-web
    exit /b 1
)

REM Test health endpoint
echo [INFO] Testing health endpoint...
for /f "delims=" %%i in ('curl -s http://localhost:8000/api/health') do set HEALTH_RESPONSE=%%i
echo [INFO] Health check response: !HEALTH_RESPONSE!

REM Check volumes
echo.
echo [6/6] Verifying volume mounts...

docker volume ls | find "vapt-db-data" >nul
if errorlevel 1 (
    echo [ERROR] Database volume not found
    exit /b 1
)
echo [OK] Database volume exists

docker volume ls | find "vapt-scans" >nul
if errorlevel 1 (
    echo [ERROR] Scans volume not found
    exit /b 1
)
echo [OK] Scans volume exists

docker volume ls | find "vapt-logs" >nul
if errorlevel 1 (
    echo [ERROR] Logs volume not found
    exit /b 1
)
echo [OK] Logs volume exists

REM Summary
echo.
echo ================================================
echo   VALIDATION SUCCESSFUL!
echo ================================================
echo.
echo VAPT Toolkit is running:
echo   API Server:      http://localhost:8000
echo   API Docs:        http://localhost:8000/docs
echo   API Health:      http://localhost:8000/api/health
echo   Frontend:        http://localhost:3000
echo.
echo Useful commands:
echo   View logs:       docker compose logs -f
echo   Stop services:   docker compose down
echo   View containers: docker compose ps
echo.
echo Next steps:
echo   1. Open http://localhost:8000/docs to explore API endpoints
echo   2. Open http://localhost:3000 to access the frontend
echo   3. See docs/DOCKER_DEPLOYMENT.md for configuration options
echo.

exit /b 0
