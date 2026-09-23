#!/bin/sh
set -e

# Google Cloud Run provides dynamic PORT (defaults to 8080)
export PORT="${PORT:-8080}"
echo "[MAADT Cloud Runner] Initializing on Cloud Run Port: $PORT"

# Render nginx configuration from template
envsubst '${PORT}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

# Start FastAPI backend in background
echo "[MAADT Cloud Runner] Starting FastAPI backend core..."
cd /app/backend
python -u -m uvicorn api.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# Start Next.js standalone frontend in background
echo "[MAADT Cloud Runner] Starting Next.js standalone frontend..."
cd /app/frontend
PORT=3000 HOSTNAME=127.0.0.1 node server.js &
FRONTEND_PID=$!

# Handle graceful shutdown on Cloud Run container termination
cleanup() {
    echo "[MAADT Cloud Runner] Terminating background processes..."
    kill -TERM "$BACKEND_PID" 2>/dev/null || true
    kill -TERM "$FRONTEND_PID" 2>/dev/null || true
    exit 0
}

trap cleanup INT TERM EXIT

# Wait for FastAPI backend to bind and pass self-check
echo "[MAADT Cloud Runner] Waiting for FastAPI to initialize..."
i=0
while ! curl -s http://127.0.0.1:8000/api/v1/system/status >/dev/null 2>&1; do
    sleep 0.5
    i=$((i + 1))
    if [ "$i" -gt 60 ]; then
        echo "[MAADT Cloud Runner] ERROR: FastAPI backend failed to initialize within 30s!"
        exit 1
    fi
done
echo "[MAADT Cloud Runner] FastAPI backend is ready!"

# Wait for Next.js frontend to bind
echo "[MAADT Cloud Runner] Waiting for Next.js frontend to initialize..."
j=0
while ! curl -s http://127.0.0.1:3000/ >/dev/null 2>&1; do
    sleep 0.5
    j=$((j + 1))
    if [ "$j" -gt 60 ]; then
        echo "[MAADT Cloud Runner] ERROR: Next.js frontend failed to initialize within 30s!"
        exit 1
    fi
done
echo "[MAADT Cloud Runner] Next.js frontend is ready!"

# Start Nginx in foreground as the main ingress proxy
echo "[MAADT Cloud Runner] Starting Nginx reverse proxy on port $PORT..."
nginx -g "daemon off;"
