# ==============================================================================
# MAADT Unified Container Dockerfile
# Combines Next.js 16 WebGL Operator HUD + FastAPI Core + Nginx Ingress Reverse Proxy
# Standard Cloud Container (Google Cloud Run / AWS / Local Single-Port Deployments)
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build Next.js standalone frontend
# ------------------------------------------------------------------------------
FROM node:20-alpine AS frontend-builder
RUN apk add --no-cache libc6-compat
WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend ./
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 2: Unified Production Cloud Container
# ------------------------------------------------------------------------------
FROM python:3.12-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend \
    MAADT_CONFIG_DIR=/app/configs \
    MAADT_DB_PATH=/app/data/maadt_data.db \
    NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=8080

WORKDIR /app

# Install runtime packages: Nginx, gettext (for envsubst), curl, and Node.js 20 runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    nginx \
    gettext-base \
    nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Python backend dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy configs, backend source, and data directory
COPY configs /app/configs
COPY backend /app/backend
RUN mkdir -p /app/data

# Copy Next.js standalone frontend from frontend-builder
WORKDIR /app/frontend
COPY --from=frontend-builder /app/frontend/public ./public
COPY --from=frontend-builder /app/frontend/.next/standalone ./
COPY --from=frontend-builder /app/frontend/.next/static ./.next/static

# Copy Cloud Nginx configuration and entrypoint coordinator
COPY cloud/nginx.conf.template /etc/nginx/nginx.conf.template
COPY cloud/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

WORKDIR /app

# Cloud Run expects listening on $PORT (default 8080)
EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://127.0.0.1:8080/api/v1/system/status || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
