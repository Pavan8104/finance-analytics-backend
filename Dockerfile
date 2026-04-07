# =============================================================================
# Finance Analytics API — Multistage Dockerfile
# =============================================================================
# Stage 1: builder  — installs dependencies
# Stage 2: runtime  — lean production image, non-root user
# =============================================================================

# ---- Stage 1: Builder -------------------------------------------------------
FROM python:3.12-slim AS builder

# Don't write .pyc files, don't buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install build dependencies in one layer, clean up in same layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python deps into a prefix directory (not site-packages directly)
# This allows clean copying into the final stage
COPY requirements.txt .
RUN pip install --prefix=/install --no-warn-script-location -r requirements.txt


# ---- Stage 2: Runtime -------------------------------------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/install/bin:$PATH" \
    PYTHONPATH="/install/lib/python3.12/site-packages"

WORKDIR /app

# Install only runtime system dependencies (no build tools)
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 curl && \
    rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /install

# Create non-root user for security
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --shell /bin/bash --create-home appuser

# Copy application source
COPY --chown=appuser:appgroup . .

# Create logs directory with correct ownership
RUN mkdir -p logs && chown appuser:appgroup logs

# Switch to non-root user
USER appuser

# Expose application port
EXPOSE 8000

# Health check — Docker will mark the container unhealthy if this fails
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
