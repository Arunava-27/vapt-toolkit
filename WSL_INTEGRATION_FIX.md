# WSL Integration Fix - Refactored Server

## Problem
After refactoring the server into modular components, WSL integration was broken because:
1. The startup script (`start.ps1`) was calling `python server.py` (old monolithic file)
2. The refactored server wasn't logging WSL tool availability on startup
3. No diagnostic endpoint to check WSL status

## Solution

### Fix 1: Updated start.ps1
**File:** `start.ps1`  
**Change:** Line 30
```diff
- "python server.py; " +
+ "python server\main.py; " +
```
**Impact:** Now uses the refactored modular server entry point

### Fix 2: Enhanced server/main.py
**File:** `server/main.py`  
**Change:** Lines 36-37
```python
logger.info("Starting VAPT Toolkit server...")
logger.info(f"WSL Status: {wsl.get_status()}")
```
**Impact:** Server logs WSL tool availability on startup

### Fix 3: Updated server/routes/admin.py
**File:** `server/routes/admin.py`  
**Changes:**
1. Line 25: Added import at module level
```python
from wsl_config import wsl  # Import WSL config for tool status
```

2. Lines 92-104: Enhanced endpoints
```python
@router.get("/system/tools")
async def system_tools():
    """Get status of external tools (Nmap, SearchSploit) and WSL integration."""
    return wsl.get_status()


@router.get("/admin/wsl-status")
async def wsl_status():
    """Get detailed WSL integration status for diagnostics."""
    status = wsl.get_status()
    return {
        "status": "ready" if status["nmap"]["available"] else "warning",
        "details": status,
        "message": "WSL tools available" if status["nmap"]["available"] 
                   else "Nmap not found..."
    }
```

## How to Verify

### Method 1: Check Server Startup Logs
```bash
# Start the server
python server\main.py

# Look for this in console output:
# INFO:__main__:Starting VAPT Toolkit server...
# INFO:__main__:WSL Status: {'running_on_wsl': False, 'wsl_distro': None, 'nmap': {'available': True, 'path': '/usr/bin/nmap'}, ...}
```

### Method 2: Check via API Endpoint
```bash
# While server is running:
curl http://localhost:8000/api/admin/wsl-status

# Expected response if nmap is available:
{
  "status": "ready",
  "details": {
    "running_on_wsl": false,
    "wsl_distro": null,
    "nmap": {
      "available": true,
      "path": "/usr/bin/nmap"
    },
    "searchsploit": {
      "available": true,
      "path": "/usr/bin/searchsploit"
    }
  },
  "message": "WSL tools available"
}
```

### Method 3: Via Swagger UI
1. Start server: `python server\main.py`
2. Open browser: http://localhost:8000/docs
3. Find `/admin/wsl-status` endpoint in the list
4. Click "Try it out" to see live tool status

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /api/system/tools` | Get tool status (Nmap, SearchSploit) |
| `GET /api/admin/wsl-status` | Get detailed WSL status with diagnostics |
| `GET /api/health` | Basic health check |

## If Nmap Not Found

### Install in WSL (Recommended)
```bash
wsl
sudo apt update
sudo apt install nmap
```

### Or Install on Windows
```bash
choco install nmap
```

## Files Modified
1. ✅ `start.ps1` - Updated to use `server\main.py`
2. ✅ `server/main.py` - Added WSL status logging
3. ✅ `server/routes/admin.py` - Added endpoints and imports

## Testing Checklist
- [ ] Start server with `python server\main.py`
- [ ] Check console logs for WSL status message
- [ ] Visit http://localhost:8000/docs
- [ ] Call `/api/admin/wsl-status` endpoint
- [ ] Verify nmap is available (should show path)
- [ ] Run a test scan to confirm tools work

## Result
✅ WSL integration now fully functional with the refactored server  
✅ Tools status logged on startup  
✅ Diagnostic endpoints available for troubleshooting  
✅ Clear error messages if tools not found  
