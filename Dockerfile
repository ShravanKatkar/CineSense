# Multi-stage Dockerfile for CineSense — AI-Powered Movie Discovery Platform

# ── Stage 1: Build React 19 + Vite Frontend SPA ──
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ── Stage 2: Python 3.12 Backend Runtime ──
FROM python:3.12-slim AS backend-runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system dependencies & PostgreSQL client for migration health check
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Install Python dependencies
COPY backend/pyproject.toml backend/uv.lock* ./backend/
WORKDIR /app/backend
RUN uv sync --frozen --no-dev || uv sync --no-dev

# Copy backend application and database migrations
COPY backend/ ./

# Copy processed movie dataset and precomputed embeddings matching paths.py hierarchy
COPY data/processed /app/data/processed

# Copy built React frontend assets into static directory for unified serving
COPY --from=frontend-builder /app/frontend/dist /app/backend/static

# Make entrypoint script executable
RUN chmod +x /app/backend/docker-entrypoint.sh

EXPOSE 8000

# Container health monitoring
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Entrypoint automatically checks database readiness, runs migrations, and launches FastAPI
ENTRYPOINT ["/app/backend/docker-entrypoint.sh"]
CMD ["uv", "run", "fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]

