# Cloud Run Dockerfile
# Build from backend directory: gcloud run deploy --source ./backend

FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

# Install dependencies
RUN pip install --no-cache /wheels/*

# Copy application code
COPY app/ ./app/

# Copy Firebase credentials
COPY serviceAccountKey.json ./serviceAccountKey.json

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Cloud Run uses PORT environment variable
ENV PORT=8000

# Expose port
EXPOSE 8000

# Run the application
CMD exec gunicorn app.main:app -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT --timeout 120
