# ==============================================================================
# MAADT Backend Service Dockerfile
# Python FastAPI Core Intelligence Gateway & Digital Twin Engine
# ==============================================================================

FROM python:3.12-slim AS runner

# Prevent Python from writing .pyc files and enable unbuffered output for live logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend \
    MAADT_CONFIG_DIR=/app/configs \
    MAADT_DB_PATH=/app/data/maadt_data.db \
    OLLAMA_BASE_URL=http://host.docker.internal:11434 \
    PORT=8000

WORKDIR /app

# Install runtime dependencies (curl for container healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first for optimal Docker layer caching
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy configuration definitions and backend application source code
COPY configs /app/configs
COPY backend /app/backend

# Create persistent state directory and configure non-root system user for security
RUN mkdir -p /app/data && \
    groupadd -r maadt && useradd -r -g maadt -d /app maadt && \
    chown -R maadt:maadt /app

USER maadt
WORKDIR /app/backend

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/api/v1/system/status || exit 1

CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
