# Optimized Deployment Guide

## Overview
This guide describes the optimized deployment setup for the Discord Mods Inc project. The setup has been optimized for resource efficiency and performance.

## System Requirements

Minimum requirements:
- 1GB RAM
- 1 CPU core
- 20GB disk space

Recommended:
- 2GB RAM
- 2 CPU cores
- 40GB disk space

## Resource Allocation

Services are configured with the following resource limits:

- Web: 512MB RAM, 0.5 CPU
- Nginx: 128MB RAM, 0.2 CPU
- Redis: 256MB RAM, 0.2 CPU
- Celery: 384MB RAM, 0.3 CPU

Total: ~1.3GB RAM, 1.2 CPU cores

## Deployment Steps

1. Clone the repository:
```bash
git clone <repository-url>
cd discord-mods-inc
```

2. Create and configure .env file:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. Run the setup script:
```bash
sudo bash setup.sh
```

4. Verify the deployment:
```bash
# Check service status
docker compose ps

# Check logs
docker compose logs -f

# Test health endpoints
curl http://localhost/health/
```

## Monitoring

Health check endpoints are available at:
- `/health/` - Application health
- Each service has built-in health checks configured in docker-compose.yml

## Security Features

1. Rate Limiting:
   - General endpoints: 10 req/sec with burst of 20
   - API endpoints: 5 req/sec with burst of 10

2. Security Headers:
   - X-Frame-Options
   - X-XSS-Protection
   - X-Content-Type-Options
   - Content-Security-Policy
   - Referrer-Policy

3. File Access:
   - Restricted media file types
   - Hidden files blocked
   - Proper file permissions

## Performance Optimizations

1. Nginx:
   - Gzip compression
   - Static file caching
   - Keepalive connections
   - Optimized logging
   - WebSocket support

2. Docker:
   - Multi-stage builds
   - Alpine-based images
   - Resource limits
   - Health checks
   - Volume optimizations

## Maintenance

1. Logs:
   - Located in /var/log/nginx/
   - Configured with rate limiting and buffering

2. Backups:
   - Media files in /app/web/media
   - Static files in /app/web/staticfiles
   - Redis data persisted in named volume

3. Scaling:
   - Adjust resource limits in docker-compose.yml
   - Modify worker counts in Gunicorn/Celery settings

## Troubleshooting

1. Check service health:
```bash
docker compose ps
```

2. View logs:
```bash
docker compose logs -f [service_name]
```

3. Restart services:
```bash
docker compose restart [service_name]
```

4. Common issues:
   - Permission errors: Check volume permissions
   - Memory issues: Adjust resource limits
   - Connection errors: Check health checks and logs

## Updates

To update the deployment:

1. Pull latest changes:
```bash
git pull origin main
```

2. Rebuild and restart:
```bash
docker compose down
docker compose up -d --build
```

## Notes

- The setup uses Docker's built-in orchestration
- Services are configured to restart automatically
- Resource limits can be adjusted based on needs
- Health checks ensure service availability
- Security measures are in place for production use