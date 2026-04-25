# Docker Setup Validation Checklist

Complete checklist for validating your Docker containerization setup locally.

## Pre-Validation

- [ ] Docker Desktop is installed and running
- [ ] Docker daemon is active (`docker ps` should show no errors)
- [ ] Docker Compose v2.0+ is available (`docker compose version`)
- [ ] 4GB+ RAM allocated to Docker
- [ ] 10GB+ free disk space

## File Validation

All required Docker files have been created:

- [x] **Dockerfile** - Multi-stage Python build, production-optimized
- [x] **docker-compose.yml** - Services definition with volumes and networks
- [x] **frontend/Dockerfile** - React multi-stage build
- [x] **.dockerignore** - Excludes unnecessary files from build context
- [x] **.env.example** - Environment template for configuration
- [x] **docs/DOCKER_DEPLOYMENT.md** - Complete deployment guide
- [x] **docs/DOCKER_PRODUCTION.md** - Production deployment guide
- [x] **DOCKER_QUICKREF.md** - Quick reference for common commands
- [x] **docker-start.sh** - Linux/macOS startup script
- [x] **docker-start.bat** - Windows startup script
- [x] **test-docker.sh** - Linux/macOS validation script
- [x] **test-docker.bat** - Windows validation script

## Local Testing Steps

### Step 1: Prepare Environment

```bash
# Navigate to project root
cd /path/to/vapt-toolkit

# Copy environment configuration
cp .env.example .env

# Edit .env if needed (optional)
# vi .env
```

**Expected result**: `.env` file exists in project root

### Step 2: Build Docker Images

```bash
# Build all images (this will take 5-10 minutes)
docker compose build --no-cache

# Or with startup script:
./docker-start.sh build  # Linux/macOS
docker-start.bat build   # Windows
```

**Expected results**:
- No build errors
- Console shows "Successfully tagged"
- Images appear in `docker images | grep vapt`

### Step 3: Start Services

```bash
# Start all services
docker compose up -d

# Or with startup script:
./docker-start.sh up     # Linux/macOS
docker-start.bat up      # Windows
```

**Expected results**:
- Container names: `vapt-web`, `vapt-frontend`, `vapt-db`
- Services in "Up" state after 30 seconds

### Step 4: Verify Container Status

```bash
# Check all containers running
docker compose ps

# Should see:
# NAME          IMAGE                  STATUS
# vapt-web      vapt-toolkit:web       Up (healthy)
# vapt-frontend vapt-toolkit:frontend  Up
# vapt-db       busybox:latest         Up
```

**Expected results**:
- All containers show "Up"
- `vapt-web` shows as "healthy"

### Step 5: Test API Endpoints

```bash
# Test health endpoint
curl http://localhost:8000/api/health

# Should return JSON response like:
# {"status":"healthy",...}

# Open in browser
# http://localhost:8000/docs  # Interactive API documentation
```

**Expected results**:
- Health endpoint returns 200 status
- Swagger UI loads at /docs
- No CORS errors in browser console

### Step 6: Test Frontend

```bash
# Open in browser
# http://localhost:3000

# Frontend should load without console errors
```

**Expected results**:
- React app loads
- Can see VAPT interface
- No 404 errors for API calls

### Step 7: Verify Volumes

```bash
# List volumes
docker volume ls | grep vapt

# Should see:
# vapt-db-data
# vapt-scans
# vapt-reports
# vapt-logs

# Check volume contents
docker volume inspect vapt-db-data
# Should show Mountpoint with vapt.db database
```

**Expected results**:
- 4 volumes listed
- `vapt-db-data` contains `/app` mount point
- Database file exists: `ls /var/lib/docker/volumes/vapt-db-data/_data/`

### Step 8: Test Logs

```bash
# View logs
docker compose logs -f

# Press Ctrl+C to stop

# Logs should show:
# - FastAPI startup messages
# - React build/serve messages
# - No error stack traces
```

**Expected results**:
- Clear startup messages
- No ERROR level logs
- Can stop with Ctrl+C

### Step 9: Database Persistence

```bash
# Verify database exists
docker compose exec vapt-web ls -lh /app/vapt.db

# Should show: vapt.db file exists

# Test persistence by stopping/starting
docker compose stop
docker compose start

# Database should still exist with same content
docker compose exec vapt-web ls -lh /app/vapt.db
```

**Expected results**:
- Database file persists after restart
- File size doesn't change
- No data loss on container restart

### Step 10: Health Check

```bash
# Check Docker health status
docker compose ps | grep vapt-web

# Should show healthy status

# Test manual health check
curl -v http://localhost:8000/api/health
# Response code should be 200
```

**Expected results**:
- `vapt-web` shows as healthy
- Health endpoint returns HTTP 200
- Response indicates service is operational

## Performance Metrics

After validation, check performance:

```bash
# Monitor resource usage
docker stats

# Should see:
# - CPU: 5-15% (at idle)
# - Memory: 300-500 MB (vapt-web)
# - Memory: 200-300 MB (vapt-frontend)
```

**Expected results**:
- CPU usage below 20% at idle
- Memory usage under 1GB total
- No container restarts

## Cleanup

When testing is complete:

```bash
# Stop services (keep data)
docker compose stop

# Or remove containers (keep volumes)
docker compose down

# Or full cleanup (removes everything)
docker compose down -v
```

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| "Docker daemon not running" | Start Docker Desktop |
| "Port 8000 already in use" | Change VAPT_PORT in .env, or `lsof -i :8000` |
| "Build fails with permission denied" | Run with `sudo` on Linux |
| "Frontend loads but API errors" | Check VITE_API_URL in .env |
| "Database errors on startup" | Run `docker compose exec vapt-web python -c "from database import init_db; init_db()"` |
| "Out of disk space" | Run `docker compose down -v` and `docker image prune` |

## Integration Testing

Once basic validation passes:

### API Testing

```bash
# List available endpoints
curl http://localhost:8000/docs

# Test sample endpoints
curl http://localhost:8000/api/projects
curl http://localhost:8000/api/scan/status
```

### Frontend Testing

```bash
# Check UI interactions
# 1. Navigate to http://localhost:3000
# 2. Click on menu items
# 3. Verify API calls in browser DevTools Network tab
# 4. No 404 errors for API endpoints
```

### Database Testing

```bash
# Check database tables
docker compose exec vapt-web sqlite3 /app/vapt.db ".tables"

# Verify data persistence
docker compose exec vapt-web sqlite3 /app/vapt.db "SELECT COUNT(*) FROM projects;"
```

## Validation Success Criteria

✅ All tests pass if:

- [ ] Docker images build without errors
- [ ] All 3 services start and stay running
- [ ] API responds at http://localhost:8000/api/health
- [ ] Frontend loads at http://localhost:3000
- [ ] Database volume persists across restarts
- [ ] Health check shows "healthy"
- [ ] Logs show no errors
- [ ] Resource usage is reasonable
- [ ] Data persists after container restart

## Next Steps

Once validation passes:

1. **Configure for Production**
   - Read `docs/DOCKER_PRODUCTION.md`
   - Update security settings in `.env`
   - Set up monitoring

2. **Deploy**
   - Choose deployment platform (AWS, Azure, GCP, K8s)
   - Follow platform-specific guides

3. **Monitor**
   - Set up log aggregation
   - Configure alerts
   - Monitor performance metrics

## Documentation Links

- **Quick Reference**: See `DOCKER_QUICKREF.md`
- **Deployment Guide**: See `docs/DOCKER_DEPLOYMENT.md`
- **Production Setup**: See `docs/DOCKER_PRODUCTION.md`
- **Docker Docs**: https://docs.docker.com
- **Docker Compose Docs**: https://docs.docker.com/compose

## Support

If validation fails:

1. Check Docker daemon is running: `docker ps`
2. Review logs: `docker compose logs -f`
3. Check filesystem: `docker volume ls`
4. Verify network: `docker network ls`
5. Try rebuild: `docker compose build --no-cache`

---

**Status**: Ready for Validation  
**Created**: 2024  
**Last Updated**: 2024  
**Version**: 1.0.0
