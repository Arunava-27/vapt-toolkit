# Multi-stage build for production-ready VAPT Toolkit
# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /tmp/build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    make \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Create non-root user for security
RUN groupadd -r vapt && useradd -r -g vapt vapt

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    nmap \
    dnsutils \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/vapt/.local

# Set environment variables
ENV PATH=/home/vapt/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VAPT_PORT=8000

# Copy application code
COPY --chown=vapt:vapt . .

# Create necessary directories
RUN mkdir -p /app/logs /app/scans /app/reports && \
    chown -R vapt:vapt /app

# Switch to non-root user
USER vapt

# Expose FastAPI port
EXPOSE 8000

# Health check with retry logic
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Default entrypoint: start FastAPI server with uvicorn
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
