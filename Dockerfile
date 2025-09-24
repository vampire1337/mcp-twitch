# Use Python 3.12 slim image for better performance
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies with uv (much faster than pip)
RUN uv sync --frozen --no-dev

# Copy source code
COPY mcp_twitch_server.py openapi.json ./

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Health check - basic port check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8080}/mcp || exit 1

# Expose port (Railway will set PORT env var)
EXPOSE 8080

# Default command - can be overridden by Railway
CMD ["uv", "run", "python", "mcp_twitch_server.py", "--transport", "http", "--host", "0.0.0.0", "--port", "8080"]