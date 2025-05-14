#!/bin/bash

# Exit on error
set -e

# Handle signals
trap 'kill -TERM $PID' TERM INT

# Function to wait for Redis
wait_for_redis() {
    echo "Waiting for Redis..."
    until timeout 1 bash -c "cat < /dev/null > /dev/tcp/${REDIS_HOST}/${REDIS_PORT}" 2>/dev/null
    do
        echo "Redis is unavailable - sleeping"
        sleep 1
    done
    echo "Redis is up"
}

# Function to create health check endpoint
setup_health_check() {
    mkdir -p /app/web/health
    cat > /app/web/health/views.py << 'EOF'
from django.http import HttpResponse

def health_check(request):
    return HttpResponse("OK")
EOF

    cat > /app/web/health/urls.py << 'EOF'
from django.urls import path
from . import views

urlpatterns = [
    path('', views.health_check, name='health_check'),
]
EOF

    # Add health URLs to main URLs
    if ! grep -q "health/" /app/web/config/urls.py; then
        sed -i '/urlpatterns = \[/a \    path("health/", include("web.health.urls")),' /app/web/config/urls.py
        sed -i '1i from django.urls import include' /app/web/config/urls.py
    fi
}

# Wait for Redis to be ready
wait_for_redis

# Setup health check endpoint
setup_health_check

# Run migrations and collect static files
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py createcachetable

# Start the main process
echo "Starting process: $@"
exec "$@" &
PID=$!
wait $PID

# Note: Don't need the final exec "$@" as it's already handled by the previous exec