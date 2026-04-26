# Server Startup Fix - Python Path Issue

## Problem
After refactoring, the server wouldn't start with error:
```
ModuleNotFoundError: No module named 'database'
```

This occurred when running `python server\main.py` because Python's module search path doesn't automatically include the project root directory when running from a subdirectory.

## Root Cause
When `server/main.py` executes, Python looks for imports in:
1. The directory containing the script (`server/`)
2. Installed packages
3. Python's sys.path

But NOT automatically in the project root, where `database/`, `scanner/`, and other modules are located.

## Solution
Added Python path configuration at the top of `server/main.py` (lines 13-15):

```python
# Ensure project root is in Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
```

This dynamically calculates the project root and adds it to `sys.path` before any imports occur.

## Files Modified
- **server/main.py** - Added path setup (lines 3-15)
  - Import `sys` and `Path`
  - Calculate `PROJECT_ROOT` from script location
  - Insert into `sys.path`

## How It Works
```
server/main.py location: E:\personal\vapt-toolkit\server\main.py
  ↓ parent.parent
Project root: E:\personal\vapt-toolkit\
  ↓ Added to sys.path
Now Python can import: database/, scanner/, wsl_config.py, etc.
```

## Verification
### Method 1: Direct Python
```bash
python server\main.py
# Expected: Server starts listening on port 8000
```

### Method 2: PowerShell Script
```bash
.\start.ps1
# Expected: Backend window opens and server runs
```

### Method 3: Via Uvicorn
```bash
uvicorn server.main:app --reload
# Expected: Server starts with auto-reload enabled
```

### Method 4: Test Endpoint
```bash
# In another terminal, while server is running:
curl http://localhost:8000/api/health
# Expected response: {"status":"ok"}
```

## Expected Console Output
```
INFO:__main__:Starting VAPT Toolkit server...
INFO:__main__:WSL Status: {'running_on_wsl': False, 'wsl_distro': None, ...}
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

## Testing Endpoints
Once the server is running:

1. **Health Check**
   ```bash
   curl http://localhost:8000/api/health
   ```

2. **WSL Status**
   ```bash
   curl http://localhost:8000/api/admin/wsl-status
   ```

3. **Swagger UI**
   Visit: http://localhost:8000/docs

4. **Alternative Docs**
   Visit: http://localhost:8000/redoc

## Why This Approach?
✅ **Dynamic** - Works regardless of where the project is installed  
✅ **Relative** - Uses Path() to calculate from script location  
✅ **Non-intrusive** - Only affects the server module startup  
✅ **Compatible** - Works with all Python versions  
✅ **Minimal** - Only 3 lines of code added  

## Alternative Approaches (Not Used)
- ❌ Using `PYTHONPATH` environment variable (system-wide, fragile)
- ❌ Changing working directory (side effects)
- ❌ Adding to `.pth` file (requires installation)
- ❌ Restructuring imports (requires many changes)

## Result
✅ Server starts without errors  
✅ All imports resolve correctly  
✅ WSL integration works  
✅ Modular refactoring preserved  
