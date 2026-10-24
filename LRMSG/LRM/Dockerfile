# =====================================================================
# BhuRakshak / PahaarPulse — Backend Dockerfile
# Production-hardened container packaging for FastAPI & Backboard RAG
# =====================================================================

FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies (curl for container healthcheck) and clean up apt cache
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies with resilient timeouts and retries
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --default-timeout=120 --retries 5 -r /app/backend/requirements.txt

# Create a dedicated non-root user and group
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/sh -m appuser

# Create required persistent storage and application directories
RUN mkdir -p /app/backend/uploads/field_reports /app/backend/data && \
    chown -R appuser:appgroup /app

# Copy backend source code and Alembic migrations
COPY backend /app/backend
RUN chown -R appuser:appgroup /app/backend

# Switch to non-root execution
USER appuser

# Expose backend API service port
EXPOSE 8000

# Health check probing the existing /health status endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start Uvicorn process (strictly constrained to 1 worker per in-memory rate limiting policy)
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
