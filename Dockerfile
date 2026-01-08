FROM ghcr.io/astral-sh/uv:alpine3.21 AS builder

LABEL authors="aleks"
LABEL description="Robot Server Application with Hardware Control"

# Set working directory
WORKDIR /app

# Install system dependencies first (combine for efficiency)
RUN apk update && \
    apk add --no-cache \
        python3-dev \
        build-base \
        linux-headers \
        freetype-dev \
        jpeg-dev \
        git \
        i2c-tools \
        gstreamer \
        gstreamer-dev \
        hdf5-dev \
        curl \
        bash \
        procps \
        util-linux \
    && rm -rf /var/cache/apk/*

# Copy dependency files first for better caching
#TODO - use pyproject and uv.lock here!
COPY requirements.txt ./

# Create virtual environment and install Python dependencies
RUN uv venv /app/.venv
# Use the virtual environment automatically
ENV VIRTUAL_ENV=/app/.venv
# Place entry points in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"
RUN uv pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN addgroup -g 1000 robotuser && \
    adduser -D -s /bin/bash -u 1000 -G robotuser robotuser && \
    chown -R robotuser:robotuser /app

# Switch to non-root user
USER robotuser

# Set environment variables
ENV PYTHONPATH="/app" \
    PYTHONUNBUFFERED=1

# Create startup script with proper error handling
RUN cat > /app/entrypoint.sh << 'EOF'
#!/bin/bash
set -e

# Function for logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function for error handling
handle_error() {
    log "ERROR: $1"
    exit 1
}

# Activate virtual environment
source /app/.venv/bin/activate || handle_error "Failed to activate virtual environment"

# Create necessary directories
mkdir -p /app/logs /app/config

# Start the web server
log "Starting Robot Web Server..."
cd /app/server
exec python3 webServer.py
EOF

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Health check to ensure the service is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Expose ports
EXPOSE 5000 8888

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
