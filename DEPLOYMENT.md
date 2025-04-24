# Deployment Guide

This guide covers the deployment process for the AI Team Platform on Ubuntu servers.

## Prerequisites

- Ubuntu 20.04 LTS or newer
- Domain name pointed to your server (A record for `gideon.lytestudios.be`)
- Root access to the server
- Minimum requirements:
  - 2 CPU cores
  - 4GB RAM
  - 20GB storage

## Required Environment Variables

Create a `.env` file with the following variables:

```env
DJANGO_SECRET_KEY=your_secret_key
DJANGO_DEBUG=False
ALLOWED_HOSTS=gideon.lytestudios.be
DOMAIN=gideon.lytestudios.be

# Database settings
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres
SUPABASE_DB_PASSWORD=your_db_password

# Redis settings
REDIS_HOST=redis
REDIS_PORT=6379

# SSL settings
SSL_EMAIL=your_email@example.com

# API Keys
OPENAI_API_KEY=your_openai_key
GITHUB_TOKEN=your_github_token
JWT_SECRET_KEY=your_jwt_secret
ENCRYPTION_KEY=your_encryption_key
```

## Domain Setup

1. Point your domain to your server's IP address using an A record:
   ```
   Type: A
   Name: gideon
   Value: your_server_ip
   TTL: 3600
   ```

2. Wait for DNS propagation (can take up to 48 hours, but usually much faster)

## Deployment Steps

1. Clone the repository:
   ```bash
   git clone [repository_url]
   cd [repository_name]
   ```

2. Create and edit the `.env` file with your credentials:
   ```bash
   cp .env.example .env
   nano .env
   ```

3. Run the setup script:
   ```bash
   chmod +x setup.sh
   sudo ./setup.sh
   ```

4. The setup script will:
   - Install required packages
   - Configure Nginx
   - Set up SSL certificates
   - Start Docker containers
   - Configure automatic SSL renewal

## Post-Deployment Verification

1. Check if services are running:
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   ```

2. View logs:
   ```bash
   # All logs
   docker-compose -f docker-compose.prod.yml logs

   # Specific service logs
   docker-compose -f docker-compose.prod.yml logs web
   docker-compose -f docker-compose.prod.yml logs nginx
   ```

3. Test SSL:
   ```bash
   curl https://gideon.lytestudios.be
   ```

## Maintenance Procedures

### Updating the Application

1. Pull latest changes:
   ```bash
   git pull origin main
   ```

2. Rebuild and restart containers:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d --build
   ```

### Backup Procedures

1. Backup environment variables:
   ```bash
   cp .env .env.backup
   ```

2. Backup volumes:
   ```bash
   docker run --rm -v ai_team_static_volume:/source:ro -v /backup:/backup ubuntu tar czf /backup/static-backup.tar.gz -C /source ./
   docker run --rm -v ai_team_media_volume:/source:ro -v /backup:/backup ubuntu tar czf /backup/media-backup.tar.gz -C /source ./
   ```

### SSL Certificate Renewal

Certificates auto-renew via Certbot's cron job. To manually renew:
```bash
sudo certbot renew
```

## Troubleshooting Guide

### Common Issues

1. **502 Bad Gateway**
   - Check if Django service is running:
     ```bash
     docker-compose -f docker-compose.prod.yml logs web
     ```
   - Verify Nginx configuration:
     ```bash
     sudo nginx -t
     ```

2. **SSL Certificate Issues**
   - Check certificate status:
     ```bash
     sudo certbot certificates
     ```
   - Renew certificates:
     ```bash
     sudo certbot renew --dry-run
     ```

3. **Static Files Not Loading**
   - Verify static files collection:
     ```bash
     docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic
     ```
   - Check Nginx static files configuration
   - Verify volume mounts

4. **WebSocket Connection Failed**
   - Check Nginx WebSocket configuration
   - Verify Django Channels setup
   - Check Redis connection

### Checking Logs

1. **Nginx Logs**
   ```bash
   sudo tail -f /var/www/gideon.lytestudios.be/logs/nginx-*.log
   ```

2. **Docker Logs**
   ```bash
   docker-compose -f docker-compose.prod.yml logs -f
   ```

3. **Application Logs**
   ```bash
   docker-compose -f docker-compose.prod.yml logs -f web
   ```

### Security Checks

1. **SSL Configuration**
   - Test SSL setup:
     ```bash
     curl https://www.ssllabs.com/ssltest/analyze.html?d=gideon.lytestudios.be
     ```

2. **Firewall Status**
   ```bash
   sudo ufw status
   ```

3. **Docker Security**
   ```bash
   docker info --format '{{.SecurityOptions}}'
   ```

## Performance Optimization

1. **Nginx Tuning**
   - Edit `/etc/nginx/nginx.conf`
   - Adjust worker processes and connections
   - Configure caching parameters

2. **Redis Performance**
   - Monitor Redis usage:
     ```bash
     docker-compose -f docker-compose.prod.yml exec redis redis-cli info
     ```

3. **Application Performance**
   - Monitor Django debug toolbar in development
   - Use Django Silk for production profiling
   - Monitor Celery tasks and queues

## Support

For additional support:
1. Check the project's GitHub issues
2. Review application logs
3. Contact the development team

Remember to always backup data before making significant changes to the production environment.