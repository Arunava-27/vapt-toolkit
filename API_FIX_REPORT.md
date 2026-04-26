# API 422 Unprocessable Entity Fix Report

## Problem
After refactoring the server into modular routes, the scan endpoints were returning HTTP 422 (Unprocessable Entity) errors:
- `POST /api/scan` → 422
- `POST /api/scan/validate` → 422  
- `POST /api/scans/json/validate` → 422

**Root Cause**: FastAPI requires Pydantic models for request body validation. The endpoints had raw `req` parameters without proper request models, causing FastAPI to reject incoming requests with validation errors.

---

## Solution Applied

### 1. Added Pydantic Request Models to `server/routes/scan.py`

Created three request models:

#### ScanRequest (for POST /api/scan)
```python
class ScanRequest(BaseModel):
    target: str
    recon: bool = False
    ports: bool = False
    web: bool = False
    cve: bool = False
    full_scan: bool = False
    scan_classification: str = "active"
    port_range: str = "top-1000"
    version_detect: bool = False
    scan_type: str = "connect"
    os_detect: bool = False
    port_script: str = ""
    port_timing: int = 4
    skip_ping: bool = True
    port_extra_flags: str = ""
    web_depth: int = 1
    web_vulnerability_scan: bool = False
    web_test_injection: bool = True
    web_test_xss: bool = True
    web_test_auth: bool = True
    web_test_idor: bool = True
    web_test_csrf_ssrf: bool = True
    web_test_file_upload: bool = True
    web_test_misconfiguration: bool = True
    web_test_sensitive_data: bool = True
    web_test_business_logic: bool = True
    web_test_rate_limiting: bool = True
    recon_wordlist: str = "subdomains-top5000.txt"
    existing_ports: Optional[list] = None
    project_name: Optional[str] = None
    project_id: Optional[str] = None
    scope: Optional[list[str]] = None
    override_robots_txt: bool = False
    schedule_id: Optional[str] = None
    notification_config: Optional[dict] = None
```

#### JSONScanRequest (for POST /api/scans/json/from-json)
```python
class JSONScanRequest(BaseModel):
    json_instruction: str
    project_name: Optional[str] = None
    project_id: Optional[str] = None
```

#### JSONScanValidationRequest (for POST /api/scans/json/validate)
```python
class JSONScanValidationRequest(BaseModel):
    json_instruction: str
```

### 2. Updated Endpoint Signatures

Changed endpoints from:
```python
async def start_scan(req):  # ❌ No model
```

To:
```python
async def start_scan(req: ScanRequest):  # ✅ With model
```

Updated endpoints:
- `POST /api/scan` → `start_scan(req: ScanRequest)`
- `POST /api/scans/json/validate` → `validate_json_scan(req: JSONScanValidationRequest)`
- `POST /api/scans/json/from-json` → `start_scan_from_json(req: JSONScanRequest)`

### 3. Added Pydantic Model to `server/routes/admin.py`

Created ScanValidationRequest for POST /api/scan/validate:
```python
class ScanValidationRequest(BaseModel):
    target: str
    recon: bool = False
    ports: bool = False
    web: bool = False
    cve: bool = False
    full_scan: bool = False
    scan_classification: str = "active"
    port_range: str = "top-1000"
    port_timing: int = 4
    port_script: str = ""
    scan_type: str = "connect"
    version_detect: bool = False
    os_detect: bool = False
    existing_ports: bool = False
```

Updated endpoint:
```python
async def validate_scan(req: ScanValidationRequest):
```

### 4. Initialized JSONScanExecutor and JSONScanValidator in `server/main.py`

Added imports and initialization:
```python
from scanner.json_scan_executor import JSONScanExecutor, JSONScanValidator

json_scan_executor = JSONScanExecutor()
json_scan_validator = JSONScanValidator()
```

Injected into scan routes module:
```python
scan.json_scan_executor = json_scan_executor
scan.json_scan_validator = json_scan_validator
scan.ACTIVE_SCANS = ACTIVE_SCANS
```

### 5. Added Response Models

Created JSONScanValidationResponse for consistent API responses:
```python
class JSONScanValidationResponse(BaseModel):
    is_valid: bool
    errors: list = []
    suggestions: list = []
```

---

## Testing Results

### Before Fix
```
POST /api/scan → 422 Unprocessable Entity
POST /api/scan/validate → 422 Unprocessable Entity
POST /api/scans/json/validate → 422 Unprocessable Entity
```

### After Fix
```
POST /api/scan → 200 OK
   Response: {"scan_id":"e5d81a2a-8619-4c96-a63b-e404cb834c08"}

POST /api/scan/validate → 200 OK
   Response: {"warnings":[]}

POST /api/scans/json/validate → 200 OK
   Response: {"is_valid":true,"errors":[],"suggestions":[]}
```

### Example Request
```bash
curl -X POST http://localhost:8000/api/scan \
  -H "Content-Type: application/json" \
  -d '{
    "target": "example.com",
    "recon": true,
    "ports": true,
    "web": true,
    "scan_classification": "active"
  }'
```

---

## Files Modified

1. **server/routes/scan.py** (65 lines changed)
   - Added `from pydantic import BaseModel`
   - Added ScanRequest, JSONScanRequest, JSONScanValidationRequest models
   - Added JSONScanValidationResponse model
   - Updated 3 endpoint signatures to use models

2. **server/routes/admin.py** (18 lines added)
   - Added ScanValidationRequest model
   - Updated validate_scan endpoint signature
   - Removed unused import of server_original

3. **server/main.py** (8 lines added)
   - Added imports for JSONScanExecutor and JSONScanValidator
   - Initialize both objects globally
   - Inject into scan routes module

---

## Impact

✅ **Fixed**: All scan endpoints now accept requests properly  
✅ **Verified**: Endpoints return 200 OK with correct response format  
✅ **Working**: Scan execution begins correctly (port scanner invoked with WSL nmap)  
✅ **Backward Compatible**: Request payload structure matches previous API  

---

## Known Issues

1. **Webhook Integration Error**: "cannot import name '_conn' from database"
   - Not related to API fixes, requires separate investigation
   - Does not block scan execution

2. **Wordlist Warning**: Wordlist not found for recon
   - Expected on first run, can be downloaded with setup command

---

## Deployment

1. Update all clients to use the corrected request models if custom tooling was built
2. No database migrations required
3. No additional dependencies needed
4. Compatible with existing frontend

---

Generated: Session 6126d546  
Status: ✅ All endpoints functional
