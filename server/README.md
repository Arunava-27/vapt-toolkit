# VAPT Toolkit Server - Modular Architecture

The server has been refactored from a single monolithic `server.py` (2,993 lines) into a modular structure with clear separation of concerns.

## Structure

```
server/
├── main.py                 # FastAPI app initialization & route registration
├── middleware/
│   ├── __init__.py
│   └── auth.py            # API key validation, rate limiting
├── routes/                # Endpoint modules, organized by domain
│   ├── __init__.py
│   ├── scan.py           # Scan management (GET, POST, pause, resume, cancel)
│   ├── projects.py       # Project CRUD operations
│   ├── reports.py        # Report generation & exports
│   ├── bulk.py           # Bulk scanning operations
│   ├── webhooks.py       # Webhook management
│   ├── notifications.py  # Notification settings
│   └── admin.py          # Health, stats, scheduling
└── services/             # Business logic & orchestration
    ├── __init__.py
    └── scan_service.py   # Scan orchestration logic
```

## Running the Server

### Development
```bash
python server.py
```

### Production with Uvicorn
```bash
uvicorn server.main:app --host 0.0.0.0 --port 8000
```

### Production with Gunicorn
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker server.main:app
```

## Route Organization

| Module | Routes | Purpose |
|--------|--------|---------|
| `scan.py` | POST /api/scan, GET /api/scan/status, ... | Scan execution and management |
| `projects.py` | GET/POST/PUT/DELETE /api/projects | Project persistence |
| `reports.py` | GET/POST /api/reports/*, /api/export/* | Report generation & exports |
| `bulk.py` | POST /api/bulk/scan, GET /api/bulk/jobs | Bulk scanning orchestration |
| `webhooks.py` | GET/POST/DELETE /api/webhooks | Webhook management |
| `notifications.py` | GET/PUT /api/notifications/settings | Notification preferences |
| `admin.py` | GET /api/health, /api/stats, /api/dashboard | Health & metrics |

## Adding New Routes

1. Create a new file in `server/routes/`
2. Import FastAPI router and define endpoints:
   ```python
   from fastapi import APIRouter
   
   router = APIRouter()
   
   @router.get("/api/myfeature")
   async def get_myfeature():
       return {"feature": "data"}
   ```
3. Import and register in `server/main.py`:
   ```python
   from server.routes import myfeature
   app.include_router(myfeature.router, prefix="/api", tags=["myfeature"])
   ```

## Benefits of Modular Architecture

✅ **Maintainability** - Each route module is ~150-300 lines vs 2,993 lines total  
✅ **Testability** - Easy to unit test individual route handlers  
✅ **Scalability** - Add new routes without touching existing code  
✅ **Readability** - Clear organization by domain/feature  
✅ **Collaboration** - Multiple developers can work on different routes in parallel  

## Legacy Support

The old monolithic server is backed up as `server_old_monolithic.py` for reference.

For database operations, see `database/` module documentation.
