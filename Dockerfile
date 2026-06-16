FROM python:3.11-slim

WORKDIR /app

# Minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only essential requirements
COPY requirements-barebone.txt .

# Install minimal packages - no cache to save image size
RUN pip install --no-cache-dir --no-compile -r requirements-barebone.txt

# Copy application
COPY app/ ./app/

# Create directories
RUN mkdir -p /app/data /app/uploads

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with minimal worker
CMD ["gunicorn", \
     "-w", "1", \
     "-b", "0.0.0.0:8000", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--max-requests", "50", \
     "--timeout", "30", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "app.main:app"]
