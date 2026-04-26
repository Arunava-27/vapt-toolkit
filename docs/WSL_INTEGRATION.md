# WSL Integration Guide

## Overview
The VAPT Toolkit now supports running on Windows with external Linux-only tools (Nmap, SearchSploit) via WSL (Windows Subsystem for Linux). This allows developers on Windows to run comprehensive penetration testing scans without needing virtual machines.

## Architecture

```
Windows (React Frontend) → FastAPI Backend (Windows or WSL) → Tools (WSL)
        localhost:5173              localhost:8000        /usr/bin/nmap, etc.
```

- **Frontend**: React app runs on Windows (localhost:5173)
- **Backend**: Python FastAPI can run on Windows or WSL (localhost:8000)
- **Tools**: Nmap, SearchSploit run via WSL when needed

## Installation

### Prerequisites
- Windows 10/11 with WSL 2 enabled
- Ubuntu distribution installed in WSL (default)

### Step 1: Install WSL 2
```powershell
# In PowerShell (as Administrator):
wsl --install --distribution Ubuntu
```

### Step 2: Install Tools in WSL
```bash
# In WSL Ubuntu terminal:
sudo apt update
sudo apt install -y nmap exploitdb
```

### Step 3: Configure Backend
The backend automatically detects:
- ✅ Whether running on Windows or Linux
- ✅ Tool availability in Windows PATH
- ✅ Tool availability in WSL via `wsl.exe which <tool>`

**No manual configuration needed!** The `wsl_config.py` module handles detection and execution.

## How It Works

### Tool Detection (`wsl_config.py`)
1. **On Windows**: Prioritizes WSL tools, then falls back to Windows PATH
2. **On Linux**: Uses system PATH directly
3. Returns tool paths and availability status

### Command Execution
- **If running on Windows with WSL**: Uses WSL tools via `wsl.exe nmap ...`
- **If tool found on Windows PATH**: Direct execution (used as fallback)
- **If tool found on Linux**: Direct execution

### API Endpoint
Check tool status at any time:
```bash
curl http://localhost:8000/api/system/tools
```

**Response (Windows with WSL):**
```json
{
  "running_on_wsl": false,
  "wsl_distro": "Ubuntu",
  "nmap": {
    "available": true,
    "path": "/usr/bin/nmap"
  },
  "searchsploit": {
    "available": true,
    "path": "/usr/bin/searchsploit"
  }
}
```

## Running the App

### Option 1: Backend on Windows, Frontend on Windows (Easiest)
```bash
# Terminal 1: Start backend
cd E:\personal\vapt-toolkit
.\.venv\Scripts\python.exe server.py
# → Listens on http://localhost:8000
# → Nmap/SearchSploit discovered from WSL automatically

# Terminal 2: Start frontend
cd E:\personal\vapt-toolkit\frontend
npm run dev
# → Opens http://localhost:5173
```

### Option 2: Backend in WSL, Frontend on Windows (Alternative)
```bash
# WSL Terminal: Start backend
cd /mnt/e/personal/vapt-toolkit
python server.py
# → Listens on http://localhost:8000
# → Nmap/SearchSploit available natively in WSL

# Windows Terminal: Start frontend
cd E:\personal\vapt-toolkit\frontend
npm run dev
# → Opens http://localhost:5173
```

## Troubleshooting

### "Nmap not found" error
```bash
# Install in WSL:
sudo apt install nmap

# Or on Windows native:
choco install nmap
```

### "SearchSploit not found" error
```bash
# Install in WSL:
sudo apt install exploitdb
```

### Check tool availability
```bash
curl http://localhost:8000/api/system/tools | jq .
```

### Port scan fails with WSL nmap
Ensure WSL Ubuntu is running:
```powershell
wsl --list --verbose
# Should show Ubuntu with STATE: Running
```

## Technical Details

### Files Modified
- **`wsl_config.py`** - Core WSL detection and execution module (NEW)
- **`server.py`** - Added `/api/system/tools` health check endpoint
- **`scanner/port_scanner.py`** - Integrated WSL nmap discovery
- **`scanner/cve_scanner.py`** - Integrated WSL searchsploit execution

### Key Features
- ✅ Auto-detection of Windows vs WSL environment
- ✅ Fallback logic: Windows → WSL → fail gracefully
- ✅ Works with python-nmap library (no subprocess wrapping needed for nmap.PortScanner)
- ✅ Direct subprocess wrapping for searchsploit
- ✅ Health check API endpoint for debugging

### Limitations
- File paths in WSL scans may need adjustment for complex cases
- Currently tested with basic Nmap scans (SYN, Connect, Aggressive)
- SearchSploit requires exploitdb database in WSL

## Future Improvements
- [ ] Add Windows native Nmap support (choco install nmap)
- [ ] Container-based tool execution (Docker)
- [ ] Remote execution support (SSH to Linux server)
- [ ] Tool version reporting in health endpoint
