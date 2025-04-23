# Deployment Documentation

This directory contains all deployment, monitoring, and backup configurations for the Discord AI Bot.

## Prerequisites

- Docker and Docker Compose
- Ansible 2.9+
- AWS CLI configured with appropriate permissions
- Python 3.11+
- Prometheus and Grafana
- PostgreSQL (for Supabase)

## Environment Setup

1. Create environment file:
```bash
cp deploy/templates/env.j2 .env
```

2. Configure required environment variables:
```bash
# Required API Keys
DISCORD_TOKEN=your_discord_bot_token
OPENAI_API_KEY=your_openai_api_key
GITHUB_TOKEN=your_github_token

# Database Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Security Keys
JWT_SECRET_KEY=your_jwt_secret
ENCRYPTION_KEY=your_encryption_key
```

## Deployment Process

### 1. Initial Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Setup infrastructure
ansible-playbook deploy/setup.yml

# Initialize database
python scripts/init_db.py
```

### 2. Deployment

```bash
# Deploy application
ansible-playbook deploy/deploy.yml

# Verify deployment
ansible-playbook deploy/verify.yml
```

### 3. Monitoring Setup

```bash
# Setup monitoring stack
ansible-playbook deploy/monitoring.yml
```

Access monitoring dashboards:
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090

## Backup System

### Automatic Backups

Backups are automatically performed:
- Database: Daily full backup
- Application data: Daily incremental backup
- Logs: Weekly rotation

### Manual Backup

```bash
# Perform manual backup
ansible-playbook deploy/backup.yml
```

### Restore from Backup

```bash
# List available backups
aws s3 ls s3://${BACKUP_BUCKET}/

# Restore specific backup
ansible-playbook deploy/restore.yml -e "backup_date=YYYY-MM-DD"
```

## Security Measures

1. **Authentication**:
   - JWT-based authentication
   - Token rotation
   - Rate limiting

2. **Data Protection**:
   - Encryption at rest
   - Secure key management
   - Regular security audits

3. **Access Control**:
   - Role-based access
   - Least privilege principle
   - Activity logging

## Monitoring and Alerts

### Metrics Collected

1. **System Metrics**:
   - CPU usage
   - Memory usage
   - Disk space
   - Network I/O

2. **Application Metrics**:
   - Request latency
   - Error rates
   - API usage
   - Bot commands

3. **Security Metrics**:
   - Authentication attempts
   - Rate limit hits
   - Security events

### Alert Thresholds

- CPU Usage: > 80%
- Memory Usage: > 80%
- Disk Usage: > 90%
- Error Rate: > 5%
- API Latency: > 2000ms

## Troubleshooting

### Common Issues

1. **Container Won't Start**:
```bash
# Check container logs
docker logs discord-ai-bot

# Verify environment variables
docker exec discord-ai-bot env
```

2. **Database Connection Issues**:
```bash
# Check database connectivity
python scripts/check_db.py

# Verify Supabase status
curl -I ${SUPABASE_URL}
```

3. **High Resource Usage**:
```bash
# Check resource usage
docker stats discord-ai-bot

# Analyze logs
tail -f /var/log/discord-ai-bot/application.log
```

### Recovery Procedures

1. **Service Recovery**:
```bash
# Restart service
ansible-playbook deploy/restart.yml

# Verify health
ansible-playbook deploy/verify.yml
```

2. **Data Recovery**:
```bash
# List available backups
ansible-playbook deploy/list_backups.yml

# Restore from backup
ansible-playbook deploy/restore.yml -e "backup_id=<id>"
```

## Maintenance

### Regular Tasks

1. **Daily**:
   - Monitor system health
   - Check error logs
   - Verify backup completion

2. **Weekly**:
   - Review security logs
   - Check resource usage trends
   - Update monitoring dashboards

3. **Monthly**:
   - Security patches
   - Performance optimization
   - Backup testing

### Version Updates

1. Create new release:
```bash
git tag -a v1.x.x -m "Release description"
git push origin v1.x.x
```

2. Monitor deployment:
```bash
# Watch deployment progress
ansible-playbook deploy/status.yml

# Verify new version
curl http://localhost:8080/version
```

## Support

For deployment issues:
1. Check logs: `/var/log/discord-ai-bot/`
2. Review monitoring dashboards
3. Contact DevOps team

## Contributing

1. Follow deployment guidelines
2. Test changes in staging
3. Update documentation
4. Create pull request

## License

See main project LICENSE file.