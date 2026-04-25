# Docker Production Deployment Guide

Production-ready deployment configuration for VAPT Toolkit.

## Table of Contents

- [Pre-Deployment Checklist](#pre-deployment-checklist)
- [Security Hardening](#security-hardening)
- [Performance Optimization](#performance-optimization)
- [Monitoring & Logging](#monitoring--logging)
- [Backup & Recovery](#backup--recovery)
- [Scaling Strategies](#scaling-strategies)
- [Cloud Deployment](#cloud-deployment)

## Pre-Deployment Checklist

### Security

- [ ] Generate strong API key: `openssl rand -hex 32`
- [ ] Update `API_KEY_SECRET` in `.env`
- [ ] Configure HTTPS/TLS for production
- [ ] Set up firewall rules (only allow 80, 443)
- [ ] Enable Docker content trust: `export DOCKER_CONTENT_TRUST=1`
- [ ] Audit container images: `docker scan <image>`
- [ ] Review volume permissions: All owned by `vapt:vapt` user
- [ ] Disable debug mode: `LOG_LEVEL=WARNING`

### Performance

- [ ] Allocate sufficient resources (4GB+ RAM, 2+ CPU cores)
- [ ] Configure resource limits in docker-compose
- [ ] Set up log rotation to prevent disk fill
- [ ] Enable SQLite WAL (Write-Ahead Logging)
- [ ] Monitor memory usage

### Operations

- [ ] Set up automated backups (daily)
- [ ] Configure monitoring/alerting
- [ ] Test disaster recovery procedures
- [ ] Document custom configurations
- [ ] Set up CI/CD deployment pipeline

## Security Hardening

### 1. Environment Variables

Never commit secrets to version control:

```bash
# Generate secrets
API_SECRET=$(openssl rand -hex 32)
DB_PASSWORD=$(openssl rand -hex 16)

# Use environment file (not in git)
cat > .env.production << EOF
API_KEY_SECRET=$API_SECRET
DATABASE_PASSWORD=$DB_PASSWORD
SMTP_PASSWORD=<from-vault>
EOF

# Secure permissions
chmod 600 .env.production
```

### 2. Docker Security

```yaml
# docker-compose.yml
services:
  vapt-web:
    build: .
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
      - /run
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    user: "vapt:vapt"
```

### 3. Image Scanning

```bash
# Scan for vulnerabilities
docker scan vapt-toolkit:latest

# Use official scanners
trivy image vapt-toolkit:latest
grype vapt-toolkit:latest
```

### 4. Network Security

```yaml
# docker-compose.yml
networks:
  vapt-network:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.name: br_vapt
      com.docker.network.bridge.enable_ip_masquerade: "true"
      com.docker.network.driver.mtu: "1500"
```

### 5. Registry Authentication

For private registries:

```bash
# Login to registry
docker login myregistry.azurecr.io -u username

# Pull authenticated images
docker compose pull
```

## Performance Optimization

### 1. Resource Limits

```yaml
# docker-compose.yml
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

### 2. Database Optimization

Add to Dockerfile for production:

```dockerfile
# Optimize SQLite for production
RUN sqlite3 /app/vapt.db << 'EOF'
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=-64000;
PRAGMA temp_store=MEMORY;
PRAGMA query_only=OFF;
EOF
```

### 3. Log Rotation

```yaml
# docker-compose.yml
services:
  vapt-web:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 4. Volume Performance

```yaml
# Use local driver for best performance
volumes:
  vapt-db-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /var/lib/vapt/db
```

## Monitoring & Logging

### 1. Container Monitoring

```bash
# Real-time stats
watch -n 1 'docker stats --no-stream'

# Health checks
docker compose ps
curl http://localhost:8000/api/health
```

### 2. Centralized Logging

Add ELK stack (Elasticsearch, Logstash, Kibana):

```yaml
# docker-compose.yml
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
    environment:
      - discovery.type=single-node
    ports:
      - "9200:9200"
    
  kibana:
    image: docker.elastic.co/kibana/kibana:8.0.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
```

### 3. Prometheus Metrics

Add to docker-compose.yml:

```yaml
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
```

### 4. Alert Configuration

Example alerts for Alertmanager:

```yaml
groups:
  - name: vapt
    rules:
      - alert: VAPTAPIDown
        expr: up{job="vapt-web"} == 0
        for: 1m
        annotations:
          summary: "VAPT API is down"
```

## Backup & Recovery

### 1. Automated Daily Backups

Create `backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backups/vapt"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
docker run --rm \
  -v vapt-db-data:/data \
  -v $BACKUP_DIR:/backup \
  alpine cp /data/vapt.db /backup/vapt_$TIMESTAMP.db

# Backup scan results
docker run --rm \
  -v vapt-scans:/data \
  -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/scans_$TIMESTAMP.tar.gz /data

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "vapt_*.db" -mtime +30 -delete
find $BACKUP_DIR -name "scans_*.tar.gz" -mtime +30 -delete
```

### 2. Recovery Procedure

```bash
# Stop containers
docker compose down

# Restore database
docker run --rm \
  -v vapt-db-data:/data \
  -v /backups/vapt:/backup \
  alpine cp /backup/vapt_20240101_000000.db /data/vapt.db

# Restore volumes
docker run --rm \
  -v vapt-scans:/data \
  -v /backups/vapt:/backup \
  alpine tar xzf /backup/scans_20240101_000000.tar.gz -C /data

# Start containers
docker compose up -d
```

### 3. Backup Schedule (Crontab)

```cron
# Daily backup at 2 AM
0 2 * * * /opt/vapt/backup.sh >> /var/log/vapt-backup.log 2>&1

# Weekly verification at 3 AM Sunday
0 3 * * 0 /opt/vapt/verify-backup.sh >> /var/log/vapt-verify.log 2>&1
```

## Scaling Strategies

### 1. Horizontal Scaling (Multiple API instances)

```yaml
# docker-compose.yml (for stateless API)
services:
  vapt-web:
    build: .
    deploy:
      replicas: 3
    ports:
      - "8000-8002:8000"
```

With load balancer (Nginx):

```nginx
upstream vapt_api {
    server vapt-web-1:8000;
    server vapt-web-2:8000;
    server vapt-web-3:8000;
}

server {
    listen 80;
    location / {
        proxy_pass http://vapt_api;
    }
}
```

### 2. Vertical Scaling (More resources)

```yaml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 4G
    reservations:
      cpus: '2'
      memory: 2G
```

### 3. Database Scaling

For high-load scenarios, migrate to PostgreSQL:

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: vapt
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - vapt-postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  vapt-postgres-data:
```

Update `DATABASE_URL`:
```
DATABASE_URL=postgresql://user:pass@postgres:5432/vapt
```

## Cloud Deployment

### AWS ECS

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name vapt-prod

# Push image to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker tag vapt-web:latest <account>.dkr.ecr.us-east-1.amazonaws.com/vapt-web:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/vapt-web:latest
```

### Azure Container Instances

```bash
# Create resource group
az group create --name vapt-rg --location eastus

# Create container
az container create \
  --resource-group vapt-rg \
  --name vapt-web \
  --image myregistry.azurecr.io/vapt-web:latest \
  --ports 8000 \
  --environment-variables VAPT_PORT=8000
```

### Google Cloud Run

```bash
# Push to Google Container Registry
gcloud builds submit --tag gcr.io/my-project/vapt-web

# Deploy
gcloud run deploy vapt-web \
  --image gcr.io/my-project/vapt-web:latest \
  --platform managed \
  --memory 2Gi
```

### Kubernetes (GKE/EKS)

```yaml
# vapt-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vapt-web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: vapt-web
  template:
    metadata:
      labels:
        app: vapt-web
    spec:
      containers:
      - name: vapt-web
        image: vapt-web:latest
        ports:
        - containerPort: 8000
        resources:
          limits:
            memory: "2Gi"
            cpu: "1000m"
          requests:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

Deploy to Kubernetes:
```bash
kubectl apply -f vapt-deployment.yaml
kubectl expose deployment vapt-web --type=LoadBalancer --port=80 --target-port=8000
```

## Production Deployment Template

Complete production docker-compose.yml:

```yaml
version: '3.9'

services:
  vapt-web:
    build:
      context: .
      dockerfile: Dockerfile
    restart: always
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=WARNING
      - DATABASE_URL=sqlite:///vapt.db
      - API_KEY_SECRET=${API_KEY_SECRET}
    volumes:
      - vapt-db-data:/app
      - vapt-logs:/app/logs
    networks:
      - vapt-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    security_opt:
      - no-new-privileges:true
    user: "vapt:vapt"

volumes:
  vapt-db-data:
  vapt-logs:

networks:
  vapt-network:
    driver: bridge
```

---

**Version**: 1.0.0 | **Status**: Production-Ready
