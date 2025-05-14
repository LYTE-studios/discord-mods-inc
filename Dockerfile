FROM python:3.11-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# System dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        netcat \
        libpq-dev \
        gosu \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Create a non-root user
RUN addgroup --system web \
    && adduser --system --ingroup web web

# Copy entrypoint script and set permissions
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install pytest pytest-django pytest-cov pytest-asyncio

# Create necessary directories
RUN mkdir -p /app/static /app/web/media

# Copy project files
COPY . /app/

# Set permissions
RUN chown -R web:web /app \
    && chmod -R 777 /app \
    && chmod g+s /app/static /app/web/media

# Make entrypoint script run as root for directory creation
RUN chown root:root /usr/local/bin/docker-entrypoint.sh \
    && chmod 755 /usr/local/bin/docker-entrypoint.sh

# Switch to non-root user
USER web

# Expose the port the app runs on
EXPOSE 8000

# Set the entrypoint script
ENTRYPOINT ["docker-entrypoint.sh"]

# Default command
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "web.config.wsgi:application"]