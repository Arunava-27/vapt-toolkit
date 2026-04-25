# Docker Quick Reference

## Installation & Setup

```bash
# Copy environment configuration
cp .env.example .env

# Build and start all services
docker compose up -d

# Verify services running
docker compose ps
```

## Access Points

```
API Server:     http://localhost:8000
API Docs:       http://localhost:8000/docs
Health Check:   http://localhost:8000/api/health
Frontend:       http://localhost:3000
```

## Common Commands

| Command | Purpose |
|---------|---------|
| `docker compose up -d` | Start services in background |
| `docker compose down` | Stop and remove containers |
| `docker compose logs -f` | View live logs |
| `docker compose ps` | Show container status |
| `docker compose exec vapt-web bash` | Shell into API container |
| `docker compose build --no-cache` | Rebuild images |
| `docker compose restart` | Restart all services |
| `docker volume ls` | List volumes |
| `docker stats` | Monitor resource usage |

## Startup Scripts

### Linux/macOS
```bash
chmod +x docker-start.sh test-docker.sh
./docker-start.sh up        # Start services
./test-docker.sh            # Validate setup
```

### Windows
```batch
docker-start.bat up         # Start services
test-docker.bat             # Validate setup
```

## Configuration

Edit `.env` file:
```bash
VAPT_PORT=8000              # API port
FRONTEND_PORT=3000          # Frontend port
LOG_LEVEL=INFO              # Log verbosity
API_KEY_SECRET=...          # Security key
```

## Troubleshooting

**Services won't start:**
```bash
docker compose logs vapt-web    # Check error logs
docker compose build --no-cache # Rebuild
docker compose restart          # Restart
```

**Database errors:**
```bash
docker compose exec vapt-web python -c "from database import init_db; init_db()"
```

**Port already in use:**
```bash
# Change port in .env and restart
VAPT_PORT=9000
docker compose up -d
```

## Persistence

| Volume | Data Persisted |
|--------|---|
| `vapt-db-data` | Database (vapt.db) |
| `vapt-scans` | Scan results |
| `vapt-reports` | Generated reports |
| `vapt-logs` | Application logs |

## Docker Stats

```bash
# Monitor in real-time
watch -n 1 'docker stats'

# Check specific container
docker stats vapt-web
```

## Backup Database

```bash
# Backup
docker run --rm -v vapt-db-data:/data -v $(pwd):/backup \
  alpine cp /data/vapt.db /backup/vapt.db.backup

# Restore
docker run --rm -v vapt-db-data:/data -v $(pwd):/backup \
  alpine cp /backup/vapt.db.backup /data/vapt.db
```

## Advanced

**Custom docker-compose file:**
```bash
docker compose -f docker-compose.prod.yml up -d
```

**Scale services:**
```bash
docker compose up -d --scale vapt-web=3
```

**View detailed logs:**
```bash
docker compose logs -f --tail 100 vapt-web
```

**Remove everything (destructive):**
```bash
docker compose down -v
```

---

For detailed documentation, see:
- `docs/DOCKER_DEPLOYMENT.md` - Complete guide
- `docs/DOCKER_PRODUCTION.md` - Production deployment
