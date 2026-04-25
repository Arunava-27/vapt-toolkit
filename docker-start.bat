@echo off
REM Docker startup script for VAPT Toolkit (Windows)
REM Usage: docker-start.bat [up|down|restart|logs]

setlocal enabledelayedexpansion

set COMMAND=%1
if "!COMMAND!"=="" set COMMAND=up

echo.
echo ============================================================
echo   VAPT Toolkit Docker Manager
echo ============================================================
echo   Command: !COMMAND!
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed or not in PATH
    exit /b 1
)

REM Check if Docker daemon is running
docker ps >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker daemon is not running. Start Docker Desktop.
    exit /b 1
)

REM Ensure .env exists
if not exist ".env" (
    echo [INFO] Creating .env from .env.example...
    copy .env.example .env >nul
    echo [INFO] .env created. Please edit it with your configuration.
)

goto %COMMAND%

:up
echo [INFO] Starting VAPT Toolkit services...
docker compose up -d --build
if errorlevel 1 goto error

echo.
echo [INFO] Services status:
docker compose ps

echo.
echo ============================================================
echo   VAPT Toolkit is running!
echo ============================================================
echo.
echo   Access VAPT Toolkit:
echo   - API:      http://localhost:8000
echo   - Docs:     http://localhost:8000/docs
echo   - Frontend: http://localhost:3000
echo   - Health:   http://localhost:8000/health
echo.
goto end

:down
echo [INFO] Stopping VAPT Toolkit services...
docker compose down
if errorlevel 1 goto error
echo [INFO] Services stopped.
goto end

:restart
echo [INFO] Restarting VAPT Toolkit services...
docker compose restart
if errorlevel 1 goto error
timeout /t 2 /nobreak >nul
docker compose ps
goto end

:logs
echo [INFO] Showing logs (press Ctrl+C to exit)...
docker compose logs -f
goto end

:clean
echo [WARNING] This will remove all containers and volumes!
set /p response="Continue? (y/N): "
if /i "!response!"=="y" (
    docker compose down -v
    echo [INFO] Cleaned up.
) else (
    echo [INFO] Cancelled.
)
goto end

:ps
echo [INFO] Container status:
docker compose ps
goto end

:build
echo [INFO] Building images...
docker compose build --no-cache
if errorlevel 1 goto error
echo [INFO] Build complete.
goto end

:shell-web
echo [INFO] Opening shell in vapt-web container...
docker compose exec vapt-web cmd /c "cd /app && cmd"
goto end

:shell-frontend
echo [INFO] Opening shell in vapt-frontend container...
docker compose exec vapt-frontend sh
goto end

:error
echo.
echo [ERROR] Command failed!
exit /b 1

:usage
echo.
echo Usage: %0 {up^|down^|restart^|logs^|clean^|ps^|build^|shell-web^|shell-frontend}
echo.
echo Commands:
echo   up              Start all services
echo   down            Stop all services
echo   restart         Restart all services
echo   logs            Show live logs (Ctrl+C to exit)
echo   clean           Remove containers and volumes (destructive!)
echo   ps              Show container status
echo   build           Rebuild images
echo   shell-web       Open shell in API container
echo   shell-frontend  Open shell in frontend container
echo.
exit /b 1

:end
exit /b 0
