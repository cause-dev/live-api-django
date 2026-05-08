# -- STAGE 1: Builder --
# Using a specific version for reproducibility
ARG PYTHON_VERSION=3.14
FROM ghcr.io/astral-sh/uv:python${PYTHON_VERSION}-alpine AS builder


# Optimized UV settings for container builds
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

# Install system build dependencies (only what's needed for 'uv sync')
RUN --mount=type=cache,target=/var/cache/apk \
    apk add --no-cache git gcc musl-dev python3-dev libffi-dev


# Install dependencies first to leverage Docker layer caching
# This layer only rebuilds if pyproject.toml or uv.lock changes
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --group prod --frozen --no-install-project --no-dev

# Copy application code and install the project
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --group prod --frozen --no-dev

# -- STAGE 2: Runner --
FROM python:${PYTHON_VERSION}-alpine AS runner

# Production-standard environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    PORT=8000

WORKDIR /app

# Create a non-root user for security (Crucial for production)
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Copy only the virtual environment and app from the builder
# This keeps the image size minimal (no uv, no compilers, no git)
COPY --from=builder --chown=appuser:appgroup /app /app

# Switch to the unprivileged user
USER appuser

# Healthcheck to allow orchestrators (K8s/Docker Swarm) to monitor app health
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

EXPOSE ${PORT}

ENTRYPOINT ["/sbin/tini", "--"]

# Production server: Never use 'runserver' in production.
# Use Gunicorn (WSGI) or Uvicorn/Granian (ASGI).
CMD ["gunicorn", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--worker-tmp-dir", "/dev/shm", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "config.wsgi:application"]
