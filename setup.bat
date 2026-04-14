@echo off
setlocal enabledelayedexpansion

:: RAGMU Docker Setup Script for Windows
:: Usage: setup.bat [init|start|stop|logs|status|clean]

set "PROJECT_NAME=ragmu"
set "COMPOSE_FILE=docker-compose.yml"

:: ─── Helpers ─────────────────────────────────────────────────────────────────
:print_header
echo.
echo ==========================================
echo   RAGMU Docker Setup
echo ==========================================
echo.
goto :eof

:check_docker
where docker >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed or not in PATH.
    echo Download from: https://www.docker.com/products/docker-desktop
    exit /b 1
)
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker daemon is not running. Please start Docker Desktop.
    exit /b 1
)
goto :eof

:: ─── Commands ────────────────────────────────────────────────────────────────
:cmd_init
call :print_header
call :check_docker || exit /b 1

echo [1/4] Checking .env file...
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo       Created .env from .env.example
        echo       ^ Edit .env to change passwords before proceeding.
    ) else (
        echo [WARN] .env.example not found. Creating minimal .env...
        echo DB_URL=postgresql://ragmu_user:ragmu_password@postgres:5432/ragmu_db > .env
        echo OLLAMA_BASE_URL=http://ollama:11434 >> .env
    )
) else (
    echo       .env already exists, skipping.
)

echo [2/4] Building Docker images...
docker-compose -f %COMPOSE_FILE% build --no-cache
if errorlevel 1 ( echo [ERROR] Build failed. & exit /b 1 )

echo [3/4] Starting services...
docker-compose -f %COMPOSE_FILE% up -d
if errorlevel 1 ( echo [ERROR] Failed to start services. & exit /b 1 )

echo [4/4] Waiting for app to become healthy...
timeout /t 10 /nobreak >nul
docker-compose -f %COMPOSE_FILE% ps

echo.
echo [OK] RAGMU is running!
echo      Web UI   : http://localhost:8000
echo      API Docs : http://localhost:8000/docs
echo      pgAdmin  : http://localhost:5050
goto :eof

:cmd_start
call :check_docker || exit /b 1
echo Starting RAGMU services...
docker-compose -f %COMPOSE_FILE% up -d
echo Done. Access at http://localhost:8000
goto :eof

:cmd_stop
call :check_docker || exit /b 1
echo Stopping RAGMU services...
docker-compose -f %COMPOSE_FILE% down
echo Services stopped.
goto :eof

:cmd_logs
call :check_docker || exit /b 1
docker-compose -f %COMPOSE_FILE% logs -f --tail=100 %2
goto :eof

:cmd_status
call :check_docker || exit /b 1
docker-compose -f %COMPOSE_FILE% ps
goto :eof

:cmd_clean
call :check_docker || exit /b 1
echo [WARN] This will remove all containers AND volumes (database data will be lost).
set /p "CONFIRM=Type 'yes' to confirm: "
if /i "!CONFIRM!"=="yes" (
    docker-compose -f %COMPOSE_FILE% down -v
    echo Cleaned up all containers and volumes.
) else (
    echo Cancelled.
)
goto :eof

:cmd_pull_model
call :check_docker || exit /b 1
if "%2"=="" (
    echo Usage: setup.bat pull-model ^<model-name^>
    echo Example: setup.bat pull-model llama3.1:8b
    exit /b 1
)
echo Pulling Ollama model: %2
docker-compose -f %COMPOSE_FILE% exec ollama ollama pull %2
goto :eof

:usage
echo Usage: setup.bat [command]
echo.
echo Commands:
echo   init          Full setup: build images and start services
echo   start         Start existing services
echo   stop          Stop all services
echo   logs [svc]    Stream logs (optional: app / postgres / ollama / pgadmin)
echo   status        Show service status
echo   clean         Remove all containers and volumes (destructive!)
echo   pull-model    Pull an Ollama model (e.g. setup.bat pull-model llama3.1:8b)
goto :eof

:: ─── Entry Point ─────────────────────────────────────────────────────────────
set "CMD=%1"
if "%CMD%"==""           goto usage
if "%CMD%"=="init"       goto cmd_init
if "%CMD%"=="start"      goto cmd_start
if "%CMD%"=="stop"       goto cmd_stop
if "%CMD%"=="logs"       goto cmd_logs
if "%CMD%"=="status"     goto cmd_status
if "%CMD%"=="clean"      goto cmd_clean
if "%CMD%"=="pull-model" goto cmd_pull_model

echo [ERROR] Unknown command: %CMD%
echo.
goto usage
