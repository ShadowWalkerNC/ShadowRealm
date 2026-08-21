@echo off
setlocal enabledelayedexpansion
echo =======================================================
echo 🚀 ShadowRealm / Odysseus One-Click Auto-Launcher
echo =======================================================

cd /d "%~dp0"

echo 🔍 Checking Docker environment...
docker info >nul 2>&1
if %errorlevel% equ 0 (
    echo 🐳 Docker detected! Launching containerized ShadowRealm stack...
    docker-compose up -d
) else (
    echo ⚠️  Docker daemon is not running. Launching via Python server...
    start "ShadowRealm Server" /B python -m uvicorn app:app --host 0.0.0.0 --port 7000 --log-level warning
)

echo ⏳ Waiting for server on http://localhost:7000 ...
:wait_loop
timeout /t 2 /nobreak >nul
curl -s http://localhost:7000/api/health >nul 2>&1
if %errorlevel% neq 0 goto wait_loop

echo ✅ ShadowRealm server is live!
echo 🌐 Opening Web UI at http://localhost:7000 in your browser...
start http://localhost:7000

echo =======================================================
echo ✨ ShadowRealm auto-launcher complete!
echo =======================================================
