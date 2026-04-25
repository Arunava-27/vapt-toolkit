# VAPT Toolkit - Deployment Guide

A comprehensive guide for deploying the VAPT Toolkit (Vulnerability Assessment & Penetration Testing) in development, staging, and production environments.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Development Setup](#development-setup)
3. [Production Deployment Options](#production-deployment-options)
4. [Configuration](#configuration)
5. [Database Setup](#database-setup)
6. [Starting Services](#starting-services)
7. [Health Checks](#health-checks)
8. [Troubleshooting](#troubleshooting)
9. [Monitoring](#monitoring)

---

## Prerequisites

### System Requirements

| Component | Requirement |
|-----------|-------------|
| **OS** | Linux, macOS, Windows (WSL2), or Docker-capable host |
| **CPU** | 2+ cores (4+ recommended for production) |
| **RAM** | 2GB minimum (4GB+ recommended) |
| **Storage** | 10GB+ (depends on scan/report history) |
| **Network** | Outbound access for NVD API, DNS, port scanning |

### Python

- **Version**: Python 3.10 or higher
- **Download**: https://www.python.org/downloads/
- **Windows**: Enable "Add Python to PATH" during installation

**Verify installation:**
```bash
python --version
pip --version
```

### Node.js

- **Version**: Node.js 16+ or higher
- **Download**: https://nodejs.org/
- **Includes npm** for package management

**Verify installation:**
```bash
node --version
npm --version
```

### Docker & Docker Compose

- **Docker**: Latest stable version (v20.10+)
- **Docker Compose**: v2.0+ (included with Docker Desktop)
- **Download**: https://www.docker.com/products/docker-desktop

**Verify installation:**
```bash
docker --version
docker compose version
```

### Additional Tools

| Tool | Purpose | Optional? |
|------|---------|-----------|
| **Git** | Version control | Required |
| **nmap** | Port scanning (Linux/macOS) | Required (WSL on Windows) |
| **curl** | Health checks, API testing | Recommended |
| **openssl** | Generating secrets | Recommended |

---

## Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/Arunava-27/vapt-toolkit.git
cd vapt-toolkit
```

### 2. Backend Setup (FastAPI)

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup (React + Vite)

```bash
cd frontend
npm install
cd ..
```

### 4. Environment Configuration

```bash
# Copy example configuration
cp .env.example .env

# Edit .env with your settings (see Configuration section below)
# Key variables to set:
# - API_KEY_SECRET (generate: openssl rand -hex 32)
# - LOG_LEVEL=DEBUG (for development)
```

### 5. Initialize Database

```bash
# Database auto-initializes on first API call
# Or manually initialize:
python -c "from database import init_db; init_db()"
```

### 6. Start Development Services

#### Backend (Terminal 1)
```bash
source .venv/bin/activate  # Ensure venv is active
python server.py
# API available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

#### Frontend (Terminal 2)
```bash
cd frontend
npm run dev
# Frontend available at http://localhost:5173
```

**Expected output:**
- Backend: `Uvicorn running on http://0.0.0.0:8000`
- Frontend: `Local: http://localhost:5173`

### 7. Verify Development Setup

```bash
# Test API health
curl http://localhost:8000/api/health

# Test frontend
curl http://localhost:5173 | head -20
```

---

## Production Deployment Options

### Option 1: Docker Compose (Recommended for Most)

**Best for**: Small to medium deployments, single-server setups, quick provisioning.

#### Setup Steps

1. **Prepare production .env file**

```bash
cp .env.example .env.prod
# Edit with production values (see Configuration section)
```

2. **Update docker-compose.yml for production**

```bash
# Ensure volumes are persistent
# Set restart policy: restart: always
# Configure resource limits (optional)
```

3. **Deploy services**

```bash
# Build images (first time)
docker compose -f docker-compose.yml build

# Start services
docker compose -f docker-compose.yml up -d

# Verify services running
docker compose ps
```

4. **Monitor deployment**

```bash
# View logs
docker compose logs -f vapt-web

# Check container health
docker compose logs vapt-web | tail -20
```

5. **Stop/Restart services**

```bash
# Restart
docker compose restart

# Stop
docker compose down

# Remove volumes (WARNING: deletes data)
docker compose down -v
```

---

### Option 2: Cloud Deployment (AWS/GCP/Azure)

#### AWS - Elastic Container Service (ECS)

**Architecture**: ECS Fargate + RDS (PostgreSQL) + ALB

**Steps:**

1. **Create RDS database** (PostgreSQL)
   - Instance class: db.t3.micro (dev) or db.t3.small (prod)
   - Storage: 20GB+ with auto-scaling
   - Backup: 7-day retention minimum

2. **Update database URL** in ECS task definition
   ```
   DATABASE_URL=postgresql://user:pass@rds-endpoint:5432/vaptdb
   ```

3. **Create ECR repositories** for vapt-web and vapt-frontend
   ```bash
   aws ecr create-repository --repository-name vapt-web
   aws ecr create-repository --repository-name vapt-frontend
   ```

4. **Build and push images**
   ```bash
   aws ecr get-login-password | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
   
   docker build -t vapt-web:latest .
   docker tag vapt-web:latest <account>.dkr.ecr.us-east-1.amazonaws.com/vapt-web:latest
   docker push <account>.dkr.ecr.us-east-1.amazonaws.com/vapt-web:latest
   ```

5. **Create ECS task definition** with resource limits
   - CPU: 512m, Memory: 1024m (minimum)
   - Environment variables: API_KEY_SECRET, DATABASE_URL, etc.

6. **Create ECS service** with ALB
   - Health check path: `/api/health`
   - Port: 8000 (backend), 3000 (frontend)
   - Auto-scaling: Min 2, Max 4 tasks

#### GCP - Cloud Run

**Architecture**: Cloud Run + Cloud SQL + Cloud Load Balancing

**Steps:**

1. **Create Cloud SQL instance** (PostgreSQL)
   ```bash
   gcloud sql instances create vapt-db --database-version POSTGRES_14 --tier db-f1-micro
   ```

2. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy vapt-web \
     --source . \
     --platform managed \
     --memory 1Gi \
     --set-env-vars DATABASE_URL=postgresql://... \
     --allow-unauthenticated
   ```

3. **Configure Cloud SQL proxy** for Cloud Run access
   - Use built-in Cloud SQL connector

#### Azure - App Service + Database

**Architecture**: App Service + Azure Database (PostgreSQL) + Application Gateway

**Steps:**

1. **Create resource group**
   ```bash
   az group create --name vapt-rg --location eastus
   ```

2. **Create Azure Database for PostgreSQL**
   ```bash
   az postgres server create --resource-group vapt-rg --name vapt-db --admin-user dbadmin
   ```

3. **Create App Service Plan**
   ```bash
   az appservice plan create --resource-group vapt-rg --name vapt-plan --sku B2
   ```

4. **Deploy container**
   ```bash
   az webapp create --resource-group vapt-rg --plan vapt-plan --name vapt-web \
     --deployment-container-image-name myregistry.azurecr.io/vapt-web:latest
   ```

---

### Option 3: On-Premises Deployment

**Best for**: Air-gapped networks, compliance requirements, full control.

#### Hardware Requirements

- **Dedicated Server** or **Virtual Machine**
  - CPU: 4+ cores
  - RAM: 8GB+
  - Storage: 50GB+ SSD
  - Bandwidth: Sufficient for scan traffic

#### Setup Steps

1. **Install OS**
   - Recommended: Ubuntu 22.04 LTS Server
   - Configure static IP address
   - Enable SSH access

2. **Install dependencies**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Install docker-compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install other tools
sudo apt install -y git curl nmap
```

3. **Clone and configure application**

```bash
git clone https://github.com/Arunava-27/vapt-toolkit.git
cd vapt-toolkit

cp .env.example .env
# Edit .env with production values
```

4. **Setup systemd service** (auto-start on reboot)

Create `/etc/systemd/system/vapt-toolkit.service`:

```ini
[Unit]
Description=VAPT Toolkit
After=docker.service
Requires=docker.service

[Service]
Type=simple
WorkingDirectory=/opt/vapt-toolkit
ExecStart=/usr/local/bin/docker-compose up
ExecStop=/usr/local/bin/docker-compose down
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable vapt-toolkit
sudo systemctl start vapt-toolkit
sudo systemctl status vapt-toolkit
```

5. **Configure reverse proxy** (nginx)

```nginx
server {
    listen 80;
    server_name vapt.example.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name vapt.example.com;

    ssl_certificate /etc/letsencrypt/live/vapt.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/vapt.example.com/privkey.pem;

    # API proxy
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## Configuration

### Environment Variables

Create `.env` file from `.env.example` and configure:

#### API Server Configuration

```env
# Server Port (internal: 8000, external: 80/443)
VAPT_PORT=8000

# Database URL
# SQLite (development): sqlite:///vapt.db
# PostgreSQL (production): postgresql://user:password@host:5432/vaptdb
DATABASE_URL=sqlite:///vapt.db

# API Key Secret (CRITICAL: Change in production!)
# Generate: openssl rand -hex 32
API_KEY_SECRET=your-super-secret-key-change-this-in-production

# API Key Expiry (days)
API_KEY_EXPIRY_DAYS=90

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

#### Frontend Configuration

```env
# Frontend Port
FRONTEND_PORT=3000

# API URL (public endpoint)
VITE_API_URL=http://localhost:8000

# Environment
NODE_ENV=production  # development, production
```

#### Scan Configuration

```env
# Target URL for default scans
TARGET_URL=http://localhost:3000

# Scan timeout (seconds)
SCAN_TIMEOUT=300

# Concurrent scans limit
MAX_CONCURRENT_SCANS=5
```

#### Notification Configuration

```env
# ──── SMTP (Email) ────
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com

# ──── Slack ────
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# ──── Microsoft Teams ────
TEAMS_WEBHOOK_URL=https://outlook.webhook.office.com/webhookb2/YOUR/WEBHOOK/URL
```

#### SMTP Provider Examples

**Gmail (App Password):**
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
```

**AWS SES (us-east-1):**
```env
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USERNAME=your-smtp-username
SMTP_PASSWORD=your-smtp-password
```

**SendGrid:**
```env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=SG.your_sendgrid_api_key
```

### Generating Secrets

```bash
# Generate API_KEY_SECRET
openssl rand -hex 32

# Generate strong password for database user
openssl rand -base64 32
```

---

## Database Setup

### SQLite (Development/Small Deployments)

**Default**: Automatic initialization on first API call.

**Manual initialization:**
```bash
python -c "from database import init_db; init_db()"
```

**Backup:**
```bash
cp vapt.db vapt.db.backup.$(date +%s)
```

**Restore:**
```bash
cp vapt.db.backup.1234567890 vapt.db
```

### PostgreSQL (Production)

**Docker setup:**
```bash
docker run -d \
  --name vapt-postgres \
  -e POSTGRES_DB=vaptdb \
  -e POSTGRES_USER=vaptuser \
  -e POSTGRES_PASSWORD=strong_password \
  -v vapt-postgres-data:/var/lib/postgresql/data \
  postgres:14
```

**Manual setup (Linux):**

```bash
# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql <<EOF
CREATE DATABASE vaptdb;
CREATE USER vaptuser WITH PASSWORD 'strong_password';
ALTER ROLE vaptuser SET client_encoding TO 'utf8';
ALTER ROLE vaptuser SET default_transaction_isolation TO 'read committed';
ALTER ROLE vaptuser SET default_transaction_deferrable TO ON;
ALTER ROLE vaptuser SET default_transaction_level TO 'read committed';
GRANT ALL PRIVILEGES ON DATABASE vaptdb TO vaptuser;
\q
EOF
```

**Update .env:**
```env
DATABASE_URL=postgresql://vaptuser:strong_password@localhost:5432/vaptdb
```

**Initialize schema:**
```bash
# Application will auto-initialize tables on first run
# Or manually run migration scripts if provided
python -c "from database import init_db; init_db()"
```

**Backup PostgreSQL database:**
```bash
pg_dump -U vaptuser -h localhost vaptdb > vapt_backup.sql
```

**Restore PostgreSQL database:**
```bash
psql -U vaptuser -h localhost vaptdb < vapt_backup.sql
```

---

## Starting Services

### Docker Compose (Production)

```bash
# Start all services (background)
docker compose up -d

# View logs (follow)
docker compose logs -f

# View specific service logs
docker compose logs -f vapt-web

# Stop all services
docker compose down

# Stop and remove volumes (WARNING: deletes data!)
docker compose down -v

# Restart services
docker compose restart

# Rebuild images
docker compose build --no-cache
docker compose up -d
```

### Manual (Development)

**Backend (Terminal 1):**
```bash
# Activate venv
source .venv/bin/activate

# Start API server
python server.py
# Available at http://localhost:8000
```

**Frontend (Terminal 2):**
```bash
cd frontend
npm run dev
# Available at http://localhost:5173
```

### Systemd Service (On-Premises)

```bash
# Check status
sudo systemctl status vapt-toolkit

# View logs
sudo journalctl -u vapt-toolkit -f

# Restart
sudo systemctl restart vapt-toolkit

# Stop
sudo systemctl stop vapt-toolkit

# Start
sudo systemctl start vapt-toolkit
```

---

## Health Checks

### API Health Endpoint

```bash
# Check API health
curl -v http://localhost:8000/api/health

# Expected response:
# HTTP/1.1 200 OK
# {"status":"healthy","version":"1.0"}
```

### Docker Health Status

```bash
# Check container health
docker compose ps

# Should show: "healthy" status

# View health check logs
docker inspect --format='{{json .State.Health}}' vapt-web | jq
```

### Frontend Health Check

```bash
# Check if frontend is responding
curl -I http://localhost:3000

# Expected: HTTP/1.1 200 OK
```

### Database Connectivity

```bash
# Test SQLite
sqlite3 vapt.db ".tables"

# Test PostgreSQL
psql -U vaptuser -h localhost -d vaptdb -c "SELECT 1"
```

### Comprehensive Health Check Script

Create `health-check.sh`:

```bash
#!/bin/bash

echo "=== VAPT Toolkit Health Check ==="
echo

echo "[1/4] Checking API health..."
if curl -sf http://localhost:8000/api/health > /dev/null; then
    echo "✓ API is healthy"
else
    echo "✗ API is DOWN"
    exit 1
fi

echo "[2/4] Checking frontend..."
if curl -sf http://localhost:3000 > /dev/null; then
    echo "✓ Frontend is responding"
else
    echo "✗ Frontend is DOWN"
fi

echo "[3/4] Checking Docker services..."
docker compose ps | grep -E "(vapt-web|vapt-frontend)" && echo "✓ Containers running" || echo "✗ Containers not running"

echo "[4/4] Checking database..."
if [ -f "vapt.db" ]; then
    echo "✓ Database file exists"
else
    echo "✗ Database file missing"
fi

echo
echo "=== Health Check Complete ==="
```

Run:
```bash
chmod +x health-check.sh
./health-check.sh
```

---

## Troubleshooting

### API Server Won't Start

**Problem**: `Connection refused` or port already in use

```bash
# Check if port 8000 is in use
lsof -i :8000  # Linux/macOS
netstat -ano | findstr :8000  # Windows

# Kill process using port
kill -9 <PID>  # Linux/macOS
taskkill /PID <PID> /F  # Windows

# Change port in .env
VAPT_PORT=8001
```

**Problem**: Module import errors

```bash
# Ensure venv is activated
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate  # Windows

# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Docker Issues

**Problem**: `docker compose not found`

```bash
# Verify installation
docker compose version

# If not found, install:
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

**Problem**: Container exits immediately

```bash
# View logs
docker compose logs vapt-web

# Common causes:
# - Env vars not set: docker compose config
# - Port conflict: docker ps
# - Missing dependencies: docker compose build --no-cache
```

**Problem**: Permission denied errors

```bash
# Ensure user is in docker group
sudo usermod -aG docker $USER
newgrp docker
docker ps  # Test
```

### Database Issues

**Problem**: `Database is locked` (SQLite)

```bash
# Remove database file if corrupted
rm vapt.db
# Restart application (will recreate)
```

**Problem**: PostgreSQL connection failed

```bash
# Verify PostgreSQL is running
sudo systemctl status postgresql

# Check connection string in .env
# Format: postgresql://user:password@host:port/database

# Test connection
psql -U vaptuser -h localhost -d vaptdb
```

### Frontend Not Loading

**Problem**: Blank page or 404

```bash
# Check browser console for errors
# Press F12, go to Console tab

# Verify frontend is running
curl http://localhost:3000

# Check if API URL is correct
# VITE_API_URL should point to API server
# For production: https://api.example.com
# For development: http://localhost:8000
```

**Problem**: CORS errors

```bash
# Check API CORS headers
curl -i -H "Origin: http://localhost:5173" http://localhost:8000/api/

# If needed, update CORS in server.py
# Add: allow_origins=["http://localhost:5173", "https://yourdomain.com"]
```

### Scanning Issues

**Problem**: Scans not starting

```bash
# Check API logs
docker compose logs vapt-web | grep -i error

# Verify nmap is installed
which nmap  # Linux/macOS
```

**Problem**: Scans timing out

```bash
# Increase timeout in .env
SCAN_TIMEOUT=600  # 10 minutes

# Check system resources
free -h  # Linux/macOS
Get-ComputerInfo | grep -i memory  # Windows
```

### Memory/CPU Issues

**Problem**: High memory usage

```bash
# Check container resource usage
docker stats

# Limit container resources in docker-compose.yml:
# deploy:
#   resources:
#     limits:
#       cpus: '1'
#       memory: 2G
```

---

## Monitoring

### Logs

#### View Logs (Docker)

```bash
# All services
docker compose logs

# Specific service
docker compose logs vapt-web
docker compose logs vapt-frontend

# Follow logs (tail -f)
docker compose logs -f vapt-web

# Last 50 lines
docker compose logs --tail 50 vapt-web

# Since specific time
docker compose logs --since 2024-01-01 vapt-web
```

#### Log Files (On-Premises)

Logs stored in:
- `/app/logs/` (inside container)
- Mounted to host via volume

```bash
# View logs
tail -f logs/vapt-web.log

# Search for errors
grep ERROR logs/vapt-web.log

# Rotate logs (weekly)
# Use logrotate: /etc/logrotate.d/vapt-toolkit
```

### Key Metrics to Monitor

#### API Performance
```bash
# Response time
curl -w "Time: %{time_total}s\n" http://localhost:8000/api/health

# Request count (from logs)
grep "POST /api/scan" logs/vapt-web.log | wc -l
```

#### System Resources
```bash
# CPU and memory (Docker)
docker stats vapt-web

# Disk usage
du -sh /app
df -h /

# Database size
ls -lh vapt.db
```

#### Error Rate
```bash
# Count HTTP 5xx errors (last hour)
grep "$(date -d '1 hour ago' '+%Y-%m-%d %H')" logs/vapt-web.log | grep "5[0-9][0-9]" | wc -l
```

### Monitoring Tools Setup

#### Option 1: Prometheus + Grafana (Advanced)

```yaml
# docker-compose.yml additions
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    volumes:
      - grafana-data:/var/lib/grafana
```

#### Option 2: ELK Stack (Elasticsearch, Logstash, Kibana)

```yaml
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
    environment:
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
  
  kibana:
    image: docker.elastic.co/kibana/kibana:8.0.0
    ports:
      - "5601:5601"
```

#### Option 3: Simple Monitoring Script

Create `monitor.sh`:

```bash
#!/bin/bash

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

{
  echo "[$TIMESTAMP] --- System Status ---"
  echo "CPU: $(top -bn1 | grep 'Cpu(s)' | awk '{print $2}')"
  echo "Memory: $(free -h | awk '/^Mem:/ {print $3"/"$2}')"
  echo "Disk: $(df -h / | awk 'NR==2 {print $3"/"$2}')"
  echo ""
  echo "--- Docker Status ---"
  docker compose ps
  echo ""
  echo "--- API Health ---"
  curl -s http://localhost:8000/api/health | jq .
  echo ""
} >> monitor.log

# Run every 5 minutes
# crontab: */5 * * * * /opt/vapt-toolkit/monitor.sh
```

### Alerting

#### Email Alerts (On Failure)

```bash
#!/bin/bash

if ! curl -sf http://localhost:8000/api/health > /dev/null; then
    echo "VAPT API is DOWN" | mail -s "Alert: VAPT Toolkit" admin@example.com
fi

# Add to crontab (every 5 minutes)
# */5 * * * * /opt/vapt-toolkit/alert.sh
```

#### Docker Health Check Notifications

```bash
# Monitor Docker health status
watch -n 5 'docker compose ps | grep -E "(vapt-web|vapt-frontend)"'
```

---

## Quick Reference

### Common Commands

```bash
# Development
python server.py                    # Start backend
npm run dev -C frontend             # Start frontend

# Docker
docker compose up -d                # Start (background)
docker compose down                 # Stop
docker compose logs -f vapt-web     # View logs
docker compose ps                   # Status

# Database
sqlite3 vapt.db ".dump"             # Backup SQLite
pg_dump vaptdb > backup.sql         # Backup PostgreSQL

# Testing
curl http://localhost:8000/api/health
curl http://localhost:3000
```

---

## Production Checklist

- [ ] Change `API_KEY_SECRET` in .env
- [ ] Set `LOG_LEVEL=INFO` (not DEBUG)
- [ ] Configure database (PostgreSQL recommended)
- [ ] Setup backup strategy
- [ ] Configure HTTPS/SSL certificate
- [ ] Setup reverse proxy (nginx)
- [ ] Configure monitoring/alerting
- [ ] Test health checks
- [ ] Document custom configurations
- [ ] Plan disaster recovery
- [ ] Setup log rotation
- [ ] Configure auto-restart (systemd/Docker)

---

## Support

- **Issues**: https://github.com/Arunava-27/vapt-toolkit/issues
- **Docs**: See `docs/` directory for detailed guides
- **Docker Guide**: See `docs/DOCKER_DEPLOYMENT.md`

---

**Last Updated**: January 2024
**Maintained By**: VAPT Toolkit Team
