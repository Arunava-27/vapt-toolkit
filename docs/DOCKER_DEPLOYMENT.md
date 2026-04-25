# VAPT Toolkit Docker Deployment Guide

Complete guide to deploying VAPT Toolkit using Docker and Docker Compose.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Services Overview](#services-overview)
- [Volume Management](#volume-management)
- [Port Mapping](#port-mapping)
- [Logs & Monitoring](#logs--monitoring)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- **Docker**: v20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose**: v2.0+ (included with Docker Desktop on Windows/Mac)
- **4GB+ RAM** recommended for smooth operation
- **10GB+ disk space** for scans and logs

### Verify Installation

```bash
# Check Docker version
docker --version

# Check Docker Compose version
docker compose version

# Verify Docker daemon is running
docker ps
```

## Quick Start

Get VAPT Toolkit running in 3 commands:

```bash
# 1. Clone environment configuration
cp .env.example .env

# 2. Build and start all services
docker compose up -d

# 3. Verify services are running
docker compose ps
```

Services will be available at:
- **API Server**: http://localhost:8000
- **Frontend**: http://localhost:3000
- **Health Check**: http://localhost:8000/health

## Configuration

### Environment Variables

Create a `.env` file in the project root (or copy from `.env.example`):

```bash
# API Configuration
VAPT_PORT=8000
FRONTEND_PORT=3000
LOG_LEVEL=INFO

# Database
DATABASE_URL=sqlite:///vapt.db

# Security
API_KEY_SECRET=your-secret-key-here

# Frontend
VITE_API_URL=http://localhost:8000
NODE_ENV=production

# Email Notifications (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com

# Slack Integration (Optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Microsoft Teams Integration (Optional)
TEAMS_WEBHOOK_URL=https://outlook.webhook.office.com/webhookb2/YOUR/WEBHOOK/URL
```

### Security Best Practices

1. **Change API Key Secret**: Generate a secure key for production:
   ```bash
   openssl rand -hex 32
   ```
   Update `API_KEY_SECRET` in `.env` with the generated key.

2. **Use Strong Credentials**: For email/Slack notifications, use secure credentials or app-specific passwords.

3. **Network Isolation**: Services communicate over an isolated Docker network by default.

4. **Non-Root User**: The API container runs as non-root user `vapt` for security.

## Services Overview

### 1. vapt-web (FastAPI Backend)

Main API server running FastAPI with Uvicorn.

```yaml
Container: vapt-web
Port: 8000
Image: Built from Dockerfile
Dependencies: vapt-db
Health Check: http://localhost:8000/health
```

**Key Features**:
- Automatic restart on failure
- Health check every 30 seconds
- Mounts for persistence
- Non-root execution

**View Logs**:
```bash
docker compose logs -f vapt-web
```

### 2. vapt-db (Database Volume Manager)

SQLite database persistence layer using BusyBox placeholder service.

```yaml
Container: vapt-db
Type: Volume Manager (BusyBox)
Mounted Volume: /app (contains vapt.db)
```

**Database File**: `vapt.db` persists in the `vapt-db-data` volume

### 3. vapt-frontend (React App)

React frontend served with Node and `serve` package.

```yaml
Container: vapt-frontend
Port: 3000
Image: Built from frontend/Dockerfile
Dependencies: vapt-web
Node Version: 20-alpine
```

**Build Optimization**:
- Multi-stage build reduces image size
- Production dependencies only
- Serve optimized for SPA delivery

**View Logs**:
```bash
docker compose logs -f vapt-frontend
```

## Volume Management

Volumes ensure data persistence across container restarts.

### Volume Types

| Volume | Purpose | Mount Path | Persistence |
|--------|---------|-----------|-------------|
| `vapt-db-data` | SQLite database | `/app` | Across restarts |
| `vapt-scans` | Scan results | `/app/scans` | Across restarts |
| `vapt-reports` | Generated reports | `/app/reports` | Across restarts |
| `vapt-logs` | Application logs | `/app/logs` | Across restarts |

### Inspect Volumes

```bash
# List all VAPT volumes
docker volume ls | grep vapt

# Inspect a specific volume
docker volume inspect vapt-db-data

# View volume contents
docker run --rm -v vapt-db-data:/data alpine ls -la /data
```

### Backup Database

```bash
# Backup the database
docker run --rm -v vapt-db-data:/data -v $(pwd):/backup \
  alpine cp /data/vapt.db /backup/vapt.db.backup

# Restore from backup
docker run --rm -v vapt-db-data:/data -v $(pwd):/backup \
  alpine cp /backup/vapt.db.backup /data/vapt.db
```

### Remove Volumes (Destructive)

```bash
# Remove all VAPT volumes (data will be lost!)
docker compose down -v
```

## Port Mapping

Default port mapping:

```
Host          Container    Service
8000    <-->  8000         API Server (vapt-web)
3000    <-->  3000         Frontend (vapt-frontend)
```

### Custom Ports

Modify in `.env`:

```bash
VAPT_PORT=9000        # API on port 9000
FRONTEND_PORT=3001    # Frontend on port 3001
```

Then rebuild:

```bash
docker compose up -d --force-recreate
```

## Logs & Monitoring

### View Live Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f vapt-web
docker compose logs -f vapt-frontend

# Last 50 lines
docker compose logs --tail 50 vapt-web
```

### Log Levels

Control log verbosity via `LOG_LEVEL` in `.env`:

```
LOG_LEVEL=DEBUG    # Verbose debugging
LOG_LEVEL=INFO     # General information (default)
LOG_LEVEL=WARNING  # Warnings only
LOG_LEVEL=ERROR    # Errors only
```

### Monitor Container Stats

```bash
# Real-time stats for all containers
docker stats

# Stats for specific container
docker stats vapt-web vapt-frontend
```

### Health Status

```bash
# Check service health
docker compose ps

# Manual health check
curl http://localhost:8000/health
```

## Production Deployment

### Pre-Production Checklist

- [ ] Change `API_KEY_SECRET` to a strong, random value
- [ ] Set `NODE_ENV=production` in `.env`
- [ ] Configure email/Slack notifications if needed
- [ ] Review firewall rules for ports 8000 and 3000
- [ ] Set up log rotation and monitoring
- [ ] Test database backups
- [ ] Plan scaling strategy

### Docker Image Optimization

The multi-stage Dockerfile optimizes for:
- **Size**: Slim base images reduce download time
- **Security**: Non-root user, minimal attack surface
- **Performance**: Only runtime dependencies included

### Deploy with Custom Registry

```bash
# Build for custom registry
docker compose build --no-cache

# Tag images
docker tag vapt-toolkit-vapt-web myregistry.azurecr.io/vapt-web:latest
docker tag vapt-toolkit-vapt-frontend myregistry.azurecr.io/vapt-frontend:latest

# Push to registry
docker push myregistry.azurecr.io/vapt-web:latest
docker push myregistry.azurecr.io/vapt-frontend:latest
```

### SSL/TLS with Reverse Proxy

For production HTTPS, use Nginx reverse proxy:

```yaml
# Add to docker-compose.yml
nginx:
  image: nginx:alpine
  ports:
    - "443:443"
    - "80:80"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf:ro
    - ./certs:/etc/nginx/certs:ro
  networks:
    - vapt-network
  depends_on:
    - vapt-web
    - vapt-frontend
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker compose logs vapt-web

# Rebuild without cache
docker compose build --no-cache vapt-web

# Restart services
docker compose restart
```

### API not responding

```bash
# Check if port 8000 is in use
netstat -an | grep 8000

# Test connectivity
curl -v http://localhost:8000/health

# Check container logs
docker compose logs vapt-web
```

### Database connection error

```bash
# Verify volume is mounted
docker inspect vapt-web | grep -A 10 Mounts

# Check database file exists
docker run --rm -v vapt-db-data:/data alpine ls -la /data

# Reinitialize database
docker compose exec vapt-web python -c "from database import init_db; init_db()"
```

### Frontend not loading

```bash
# Check frontend logs
docker compose logs vapt-frontend

# Verify API URL in frontend
curl http://localhost:3000/

# Check API connectivity from frontend container
docker compose exec vapt-frontend curl http://vapt-web:8000/health
```

### High memory usage

```bash
# Check container memory
docker stats

# Limit memory in docker-compose.yml
services:
  vapt-web:
    mem_limit: 2g
```

### Permission denied errors

```bash
# Fix volume permissions
docker compose exec vapt-web chmod -R 755 /app
```

### Docker daemon not running

```bash
# On Linux
sudo systemctl start docker

# On Windows/Mac
# Start Docker Desktop application
```

## Common Commands

```bash
# Start services (detached)
docker compose up -d

# Stop services (keep data)
docker compose stop

# Start stopped services
docker compose start

# Remove containers (keep volumes)
docker compose down

# Remove everything including volumes (destructive!)
docker compose down -v

# View service status
docker compose ps

# Execute command in container
docker compose exec vapt-web python -c "print('test')"

# View logs
docker compose logs -f

# Rebuild image
docker compose build --no-cache

# Rebuild and restart
docker compose up -d --force-recreate

# Scale services (if stateless)
docker compose up -d --scale vapt-web=2
```

## Network Diagnostics

```bash
# Inspect the VAPT network
docker network inspect vapt-toolkit_vapt-network

# Test connectivity between services
docker compose exec vapt-web ping vapt-frontend

# Check DNS resolution
docker compose exec vapt-web getent hosts vapt-frontend
```

## Performance Tuning

### Resource Limits

Add to `docker-compose.yml`:

```yaml
services:
  vapt-web:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### Database Optimization

For production SQLite, optimize in Dockerfile:

```dockerfile
RUN sqlite3 /app/vapt.db "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;"
```

## Support & Documentation

- **FastAPI Docs**: http://localhost:8000/docs
- **Docker Documentation**: https://docs.docker.com
- **VAPT README**: See project README.md
- **Issue Reporting**: See GitHub Issues

---

**Version**: 1.0.0 | **Last Updated**: 2024 | **Maintenance**: Production-ready
