# Multi-stage build for production
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy application metadata and source before editable install
COPY . .
RUN pip install --no-cache-dir -e .[dev]

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    docker.io \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy Python environment and application from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

# Create non-root user
RUN useradd -m -u 1000 hiveuser && \
    chown -R hiveuser:hiveuser /app
USER hiveuser

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "infra.fastapi_gateway.app:app", "--host", "0.0.0.0", "--port", "8000"]
