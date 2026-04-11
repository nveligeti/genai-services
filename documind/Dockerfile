# Dockerfile
# Chapter 12: multi-stage build
# Stage 1: base → Stage 2: production → Stage 3: development

ARG PYTHON_VERSION=3.11.9

# =============================================================
# Stage 1: base — shared foundation for all stages
# =============================================================
FROM python:${PYTHON_VERSION}-slim AS base

# Prevents Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
# Prevents Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1
# Virtual environment path
ENV VENV_PATH=/opt/venv
ENV PATH="$VENV_PATH/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    curl \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv $VENV_PATH

# Set working directory
WORKDIR /app

# ── Layer ordering: deps before code ─────────────────────────
# Copy requirements FIRST — cached unless deps change
COPY requirements.txt .

# Install production dependencies
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt


# =============================================================
# Stage 2: production
# =============================================================
FROM base AS production

WORKDIR /app

# Copy application code AFTER deps (cache benefit)
COPY alembic/ alembic/
COPY alembic.ini .
COPY app/ app/

# Create uploads directory
RUN mkdir -p /app/uploads

# ── Non-root user — Chapter 12 security ──────────────────────
ARG USERNAME=fastapi
ARG USER_UID=1001
ARG USER_GID=1001

RUN groupadd --gid $USER_GID $USERNAME \
    && adduser \
       --disabled-password \
       --gecos "" \
       --uid $USER_UID \
       --gid $USER_GID \
       --no-create-home \
       $USERNAME

# Give non-root user ownership of app directory
RUN chown -R $USERNAME:$USERNAME /app

# Switch to non-root user
USER $USERNAME

# Expose port
EXPOSE 8000

# Health check — used by Docker and docker-compose
HEALTHCHECK --interval=30s --timeout=10s \
    --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start server using factory pattern
CMD ["uvicorn", "app.main:create_app", \
     "--factory", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1"]


# =============================================================
# Stage 3: development — adds hot reload + dev tools
# =============================================================
FROM base AS development

WORKDIR /app

COPY requirements.txt .
COPY requirements-dev.txt .

RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy everything including tests
COPY . .

RUN mkdir -p /app/uploads

EXPOSE 8000

# Development: hot reload enabled
CMD ["uvicorn", "app.main:create_app", \
     "--factory", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--reload"]