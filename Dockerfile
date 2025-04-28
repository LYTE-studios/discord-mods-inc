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
RUN mkdir -p /app/static /app/media \
    && chown -R web:web /app

# Copy Django project files
COPY web/ /app/web/
COPY manage.py /app/
COPY config.py /app/

# Ensure web directory is a Python package
RUN touch /app/web/__init__.py

# Set proper ownership
RUN chown -R web:web /app

# Switch to non-root user
USER web

# Expose the port the app runs on
EXPOSE 8000

# Set the entrypoint script
ENTRYPOINT ["docker-entrypoint.sh"]

# Default command
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "web.config.wsgi:application"]