# syntax=docker/dockerfile:1
# ==============================================================================
# Aegis AI Security Guardrail Proxy - Production Multi-Stage Dockerfile
# Security Hardened | Non-Root User (UID 10001) | Minimal Distroless/Slim Base
# Zero Telemetry | dumb-init Signal Handling | Built-in Healthcheck
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build & Dependencies Compiler
# ------------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS builder

# Prevent python from writing pyc files and buffering stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /build

# Install build dependencies required for native C extensions (cryptography, pymupdf)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment for clean packaging
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy package definitions first for optimal layer caching
COPY pyproject.toml .

# Install dependencies into virtual environment
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir .

# ------------------------------------------------------------------------------
# Stage 2: Hardened Runtime Container
# ------------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS runner

# Metadata labels
LABEL org.opencontainers.image.title="Aegis AI Security Guardrail Proxy" \
      org.opencontainers.image.description="High-Performance Self-Hosted AI Security Guardrail Proxy with Multi-Layer Document Forensics" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.vendor="Aegis Security Engineering" \
      org.opencontainers.image.licenses="Proprietary / Enterprise"

# Security & runtime environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DO_NOT_TRACK=1 \
    PATH="/opt/venv/bin:$PATH" \
    ENVIRONMENT=production \
    DEBUG=false \
    HOST=0.0.0.0 \
    PORT=8000 \
    DB_PATH=/app/data/aegis_saas.db \
    DATABASE_URL=sqlite+aiosqlite:////app/data/aegis_saas.db


WORKDIR /app

# Install dumb-init for proper PID 1 signal forwarding and zombie process reaping
RUN apt-get update && apt-get install -y --no-install-recommends \
    dumb-init \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-privileged system user and group (UID/GID 10001)
RUN groupadd -g 10001 aegis && \
    useradd -u 10001 -g aegis -m -d /home/aegis -s /usr/sbin/nologin aegis

# Copy virtual environment from builder stage
COPY --from=builder --chown=aegis:aegis /opt/venv /opt/venv

# Copy application source code
COPY --chown=aegis:aegis app/ /app/app/
COPY --chown=aegis:aegis src/ /app/src/
COPY --chown=aegis:aegis pyproject.toml /app/pyproject.toml

# Create persistent data directory with strict ownership
RUN mkdir -p /app/data && \
    chown -R aegis:aegis /app/data && \
    chmod 750 /app/data

# Switch to non-root user
USER 10001:10001

# Expose proxy port
EXPOSE 8000

# Container Healthcheck (Zero external network dependencies, verifies local endpoint)
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health', timeout=2).getcode() == 200 else 1)"

# Start application under dumb-init supervisor
ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--no-access-log", "--proxy-headers"]
