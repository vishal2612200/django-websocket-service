# syntax=docker/dockerfile:1

# --- UI build stage ---
FROM node:20-alpine AS ui-builder
WORKDIR /ui
COPY ui/package*.json ./
RUN npm ci || npm install
COPY ui/ .
RUN npm run build

# --- Python build stage with optimized package installation ---
FROM python:3.11-slim AS python-base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/home/appuser/.local/bin:${PATH}" \
    DJANGO_SETTINGS_MODULE=app.settings

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates build-essential && rm -rf /var/lib/apt/lists/*

# Install Python packages with optimized flags
COPY requirements.txt ./
RUN pip install --user --upgrade pip && \
    pip install --user --no-cache-dir --compile --prefer-binary -r requirements.txt

# --- Final runtime image with startup optimizations ---
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/home/appuser/.local/bin:${PATH}" \
    DJANGO_SETTINGS_MODULE=app.settings \
    PORT=8000 \
    STATIC_ROOT=/app/static \
    # Python optimizations for faster startup
    PYTHONOPTIMIZE=2 \
    PYTHONHASHSEED=0 \
    PYTHONFAULTHANDLER=0 \
    PYTHONUNBUFFERED=1 \
    # Uvicorn optimizations
    UVICORN_THREAD_POOL_SIZE=8 \
    UVICORN_ACCESS_LOG=0 \
    UVICORN_LOG_LEVEL=warning

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 10001 appuser
WORKDIR /app

# Copy installed site-packages and scripts
COPY --from=python-base /root/.local /home/appuser/.local

# Copy application code so that package `app` is at /app/app and manage.py at /app
COPY app/ ./
# Move asgi.py to the correct location for imports
RUN mv /app/asgi.py /app/app/asgi.py
# Ensure chat directory is in the right place
RUN mkdir -p /app/app/chat && cp -r /app/chat/* /app/app/chat/ 2>/dev/null || true

# Copy startup optimizer and smoke test
COPY scripts/startup_optimizer.py /app/scripts/startup_optimizer.py
COPY scripts/smoke_ws.py /app/scripts/smoke_ws.py

# Optimize file system for faster startup
RUN find /app -name "*.pyc" -delete && \
    find /app -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Pre-compile Python bytecode for faster startup with parallel compilation
RUN python -m compileall /app/app/ -q -f -j 0

# System optimizations for high concurrency and faster startup
RUN echo "* soft nofile 65536" >> /etc/security/limits.conf && \
    echo "* hard nofile 65536" >> /etc/security/limits.conf

# Create optimized bytecode cache with parallel compilation
RUN python -m compileall /app/app/ -q -f -j 0

# Copy built UI into static directory
RUN mkdir -p ${STATIC_ROOT}
COPY --from=ui-builder /ui/dist/ ${STATIC_ROOT}/

# Pre-warm Python modules for faster startup
RUN python -c "import django; import channels; import redis; import uvicorn; import asgiref" 2>/dev/null || true

USER appuser
EXPOSE 8000

# Worker Configuration:
# - UVICORN_WORKERS: Number of ASGI worker processes (default: 1, overridden in docker-compose.yml)
# - uvicorn[standard] provides thread pool for blocking operations
# - Each worker runs in separate process for fault tolerance
# - Thread pool size: min(32, cpu_count + 4) per worker
# - Total concurrency: workers × thread_pool_size
ENV UVICORN_WORKERS=1
CMD ["sh", "-lc", "uvicorn app.asgi:application --host 0.0.0.0 --port 8000 --lifespan on --workers ${UVICORN_WORKERS:-1} --log-level warning"]
