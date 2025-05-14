# Build stage
FROM python:3.11-slim-bullseye as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install build dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /build

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install runtime dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
        gosu \
        netcat-openbsd \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir gunicorn

# Create app user
RUN addgroup --system web \
    && adduser --system --ingroup web web

# Create app directories
WORKDIR /app
RUN mkdir -p /app/web/{staticfiles,media,static} \
    && chown -R web:web /app \
    && chmod -R 755 /app \
    && chmod -R 777 /app/web/{staticfiles,media,static}

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/

# Copy project files
COPY --chown=web:web . /app/

# Copy and set up entrypoint
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Switch to non-root user
USER web

# Expose the port
EXPOSE 8000

# Set the entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]

# Default command with optimized settings
CMD ["gunicorn", \
     "--bind=0.0.0.0:8000", \
     "--workers=2", \
     "--threads=4", \
     "--worker-class=gthread", \
     "--worker-tmp-dir=/dev/shm", \
     "--timeout=120", \
     "--keep-alive=32", \
     "--max-requests=1000", \
     "--max-requests-jitter=50", \
     "--chdir=/app", \
     "web.config.wsgi:application"]