# Autonomica Worker Pod Dockerfile
# Handles background tasks, web scraping, and long-running processes

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Build tools
    build-essential \
    python3-dev \
    libffi-dev \
    # For Playwright and web scraping
    wget \
    gnupg \
    unzip \
    xvfb \
    # Browser dependencies
    libgconf-2-4 \
    libxss1 \
    libxtst6 \
    libxrandr2 \
    libasound2 \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libcairo-gobject2 \
    libgtk-3-0 \
    libgdk-pixbuf2.0-0 \
    # Additional utilities
    curl \
    git \
    # Clean up
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN groupadd -r worker && useradd -r -g worker worker

# Copy requirements first (for better layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright and browsers
RUN pip install playwright && \
    playwright install chromium && \
    playwright install-deps chromium

# Copy application code
COPY . .

# Change ownership to worker user
RUN chown -R worker:worker /app

# Switch to non-root user
USER worker

# Create necessary directories
RUN mkdir -p /app/logs /app/data

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import redis; import requests; print('Health check passed')" || exit 1

# Expose port for health checks and monitoring
EXPOSE 8080

# Default command (can be overridden)
CMD ["python", "worker.py"] 