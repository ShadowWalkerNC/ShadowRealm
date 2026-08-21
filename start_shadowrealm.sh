#!/usr/bin/env bash
echo "======================================================="
echo "🚀 ShadowRealm / Odysseus One-Click Auto-Launcher"
echo "======================================================="

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

if command -v docker &> /dev/null && docker info &> /dev/null; then
    echo "🐳 Docker detected! Launching containerized ShadowRealm stack..."
    docker-compose up -d
else
    echo "⚠️  Docker is not running or not installed."
    echo "🟢 Starting ShadowRealm FastAPI Uvicorn Server (Port 7000)..."
    python3 -m uvicorn app:app --host 0.0.0.0 --port 7000 --log-level warning &
fi

echo "⏳ Waiting for server to initialize on http://localhost:7000 ..."
until curl -s http://localhost:7000/api/health > /dev/null 2>&1; do
    sleep 2
done

echo "✅ ShadowRealm server is live!"
echo "🌐 Opening Web UI at http://localhost:7000 ..."

if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:7000
elif command -v open &> /dev/null; then
    open http://localhost:7000
fi

echo "======================================================="
echo "✨ ShadowRealm is running!"
echo "======================================================="
