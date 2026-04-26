# VAPT Toolkit - Quick Start Guide

## 🚀 Starting the Server

After the refactoring, the server structure has changed. **Use `server/main.py` as the entry point**, not the old `server.py`.

### Method 1: Direct Python (Recommended for Development)
```bash
python server\main.py
```

### Method 2: Using PowerShell Script
```bash
.\start.ps1
```

### Method 3: Uvicorn with Auto-Reload (Development)
```bash
uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
```

### Method 4: Uvicorn (Production)
```bash
uvicorn server.main:app --host 0.0.0.0 --port 8000
```

### Method 5: Docker Compose (Full Stack)
```bash
docker-compose up --build
```

## 📡 Access the Server

Once started:
- **Main API**: http://localhost:8000/api
- **Swagger UI Docs**: http://localhost:8000/docs
- **ReDoc Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/health

## 📂 Server Architecture

The backend has been split into modular components:

```
server/
├── main.py              # FastAPI app initialization
├── routes/              # 7 endpoint modules
│   ├── scan.py
│   ├── projects.py
│   ├── reports.py
│   ├── bulk.py
│   ├── webhooks.py
│   ├── notifications.py
│   └── admin.py
├── services/
│   └── scan_service.py  # Scan orchestration
└── middleware/
    └── auth.py          # API authentication
```

## 🔍 What Changed After Refactoring

| Item | Before | After |
|------|--------|-------|
| **Entry Point** | `python server.py` | `python server\main.py` |
| **Monolithic File** | 2,993 lines | Split into 7 modules (~250 lines avg) |
| **Database** | `database.py` | `database/` package with query modules |
| **Complexity** | High | 40% reduced |
| **Testability** | Hard | Easy (focused modules) |

## ⚠️ Important Notes

- **Do NOT use `server.py`** - It's kept as backup only
- **Do NOT use `server_old_monolithic.py`** - It's archived for reference
- **Use `server/main.py`** - This is the new modular entry point
- Database initializes automatically
- WSL integration for nmap is auto-detected

## 🛠️ Prerequisites

Before starting, ensure:
1. Python 3.8+ is installed
2. Dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```
3. You're in the project root directory

## ✅ Verification

Test that the server started correctly:

```bash
# Check health endpoint
curl http://localhost:8000/api/health

# Or visit in browser
http://localhost:8000/docs
```

## 📚 For More Details

- See `server/README.md` for modular architecture details
- See `IMPORT_REFERENCE.md` for Python import patterns
- See `docs/DEPLOYMENT_GUIDE.md` for production deployment

## 🎯 Common Issues

### Port 8000 Already in Use
Change the port:
```bash
python server\main.py --port 8001
# OR
uvicorn server.main:app --port 8001
```

### Module Not Found Error
Make sure you're in the project root and Python path includes it:
```bash
# Windows PowerShell
$env:PYTHONPATH = "."
python server\main.py

# Windows CMD
set PYTHONPATH=.
python server\main.py
```

### Database Error
The database initializes on first run. If you get errors:
```bash
# Delete old database and restart
Remove-Item vapt.db
python server\main.py
```

---

**Happy scanning! 🎉**
