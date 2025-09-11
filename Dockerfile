# Dockerfile for Railway deployment
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FASTMCP_LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import mcp_twitch_server; print('healthy')" || exit 1

# Expose port for HTTP transport
EXPOSE 8080

# Default command - Railway entry point
CMD ["python", "app.py"]
