"""Scan endpoints for starting, monitoring, and managing scans."""

import asyncio
import json
import uuid
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse

from database import get_project
from scanner.json_scan_executor import JSONScanExecutor, JSONScanValidator
from ..services.scan_service import _execute_scan

logger = logging.getLogger(__name__)

router = APIRouter()

# These would be initialized in main.py
json_scan_executor = None
json_scan_validator = None
ACTIVE_SCANS = {}
SCAN_TEMPLATES = []


def sse_dict(d: dict) -> str:
    """Format data for SSE streaming."""
    return f"data: {json.dumps(d, default=str)}\n\n"


def _gc_scans():
    """Remove finished scans older than 2 hours."""
    from datetime import datetime
    cutoff = datetime.now().timestamp() - 7200
    stale = [k for k, v in ACTIVE_SCANS.items()
             if v.status != "running"
             and datetime.fromisoformat(v.created_at).timestamp() < cutoff]
    for k in stale:
        del ACTIVE_SCANS[k]


# JSON Scan Endpoints

@router.post("/scans/json/validate")
async def validate_json_scan(req):
    """Validate a JSON scan instruction."""
    is_valid, errors = json_scan_validator.validate_json(req.json_instruction)
    suggestions = json_scan_executor.suggest_corrections(req.json_instruction) if not is_valid else []
    
    from pydantic import BaseModel
    
    class JSONScanValidationResponse(BaseModel):
        is_valid: bool
        errors: list = []
        suggestions: list = []
    
    return JSONScanValidationResponse(
        is_valid=is_valid,
        errors=errors,
        suggestions=suggestions
    )


@router.post("/scans/json/from-json")
async def start_scan_from_json(req, app=None):
    """Start a scan from JSON instruction."""
    from datetime import datetime
    from dataclasses import dataclass, field
    
    # Parse and validate JSON instruction
    json_data = req.json_instruction
    
    if isinstance(json_data, str):
        try:
            json_data = json.loads(json_data)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    
    # Validate before parsing
    instruction = json_scan_executor.parse_json_instruction(json_data)
    if not instruction:
        is_valid, errors = json_scan_validator.validate(json_data)
        logger.error(f"Failed to parse instruction. Validation errors: {errors}")
        raise HTTPException(status_code=400, detail=f"Invalid scan instruction: {errors}")
    
    # Estimate time based on depth
    depth_times = {"quick": 300, "medium": 900, "full": 1800}
    estimated_time = depth_times.get(instruction.depth, 900)
    
    # Create scan config from instruction
    config = {
        "target": instruction.target,
        "recon": "recon" in instruction.modules or "all" in instruction.modules,
        "ports": "ports" in instruction.modules or "all" in instruction.modules,
        "web": any(m in instruction.modules for m in ["xss", "sqli", "csrf", "idor", "headers", "auth"]) or "all" in instruction.modules,
        "cve": "cve" in instruction.modules or "all" in instruction.modules,
        "full_scan": False,
        "scan_classification": "active",
        "port_range": "top-1000",
        "web_depth": {"quick": 1, "medium": 2, "full": 3}.get(instruction.depth, 2),
        "web_vulnerability_scan": True,
        "web_test_xss": "xss" in instruction.modules or "all" in instruction.modules,
        "web_test_injection": "sqli" in instruction.modules or "all" in instruction.modules,
        "web_test_auth": "auth" in instruction.modules or "all" in instruction.modules,
        "web_test_idor": "idor" in instruction.modules or "all" in instruction.modules,
        "web_test_csrf_ssrf": "csrf" in instruction.modules or "all" in instruction.modules,
        "web_test_file_upload": "file_upload" in instruction.modules or "all" in instruction.modules,
        "web_test_misconfiguration": "headers" in instruction.modules or "all" in instruction.modules,
        "web_test_sensitive_data": "all" in instruction.modules,
        "web_test_business_logic": "all" in instruction.modules,
        "web_test_rate_limiting": "all" in instruction.modules,
        "scope": instruction.scope,
        "override_robots_txt": instruction.advanced_config.skip_robots_txt,
        "skip_ping": True,
        "project_name": req.project_name or instruction.name,
        "notification_config": {
            "severity_filter": instruction.notifications.severity_filter,
            "channels": instruction.notifications.channels,
            "email": instruction.notifications.email,
            "finding_types": "all"
        }
    }
    
    # Create scan state
    from dataclasses import dataclass, field
    
    @dataclass
    class ScanState:
        scan_id: str
        target: str
        config: dict
        events: list = field(default_factory=list)
        status: str = "running"
        task: Optional[asyncio.Task] = None
        created_at: str = field(default_factory=lambda: datetime.now().isoformat())
        project_id: Optional[str] = None
        project_name: Optional[str] = None
        port_scanner: Optional[object] = None
        notification_config: dict = field(default_factory=lambda: {
            'severity_filter': 'high',
            'channels': ['desktop'],
            'email': None,
            'finding_types': 'all'
        })
    
    scan_id = str(uuid.uuid4())
    state = ScanState(
        scan_id=scan_id,
        target=instruction.target,
        config=config,
        project_id=req.project_id,
        project_name=req.project_name or instruction.name,
        notification_config=config["notification_config"]
    )
    
    ACTIVE_SCANS[scan_id] = state
    
    # Start scan in background
    async def run_scan():
        await _execute_scan(state)
    
    state.task = asyncio.create_task(run_scan())
    
    from pydantic import BaseModel
    
    class JSONScanResponse(BaseModel):
        scan_id: str
        status: str
        estimated_time_seconds: int
        message: str
    
    return JSONScanResponse(
        scan_id=scan_id,
        status="running",
        estimated_time_seconds=estimated_time,
        message=f"Scan '{instruction.name}' started. Target: {instruction.target}"
    )


@router.get("/scans/json/templates")
async def get_scan_templates():
    """Get pre-built scan templates."""
    return {
        "templates": [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "icon": t.icon,
                "estimated_time_seconds": t.estimated_time_seconds,
                "json_instruction": t.json_instruction
            }
            for t in SCAN_TEMPLATES
        ]
    }


@router.get("/scans/json/schema")
async def get_json_schema():
    """Get JSON schema for validation."""
    return json_scan_executor.get_schema()


# Main Scan Endpoints

@router.post("/scan")
async def start_scan(req):
    """Start a new vulnerability scan."""
    try:
        _gc_scans()
        scan_id = str(uuid.uuid4())
        
        from dataclasses import dataclass, field
        from datetime import datetime
        
        @dataclass
        class ScanState:
            scan_id: str
            target: str
            config: dict
            events: list = field(default_factory=list)
            status: str = "running"
            task: Optional[asyncio.Task] = None
            created_at: str = field(default_factory=lambda: datetime.now().isoformat())
            project_id: Optional[str] = None
            project_name: Optional[str] = None
            port_scanner: Optional[object] = None
            notification_config: dict = field(default_factory=lambda: {
                'severity_filter': 'high',
                'channels': ['desktop'],
                'email': None,
                'finding_types': 'all'
            })
        
        state = ScanState(scan_id=scan_id, target=req.target, config=req.dict())
        ACTIVE_SCANS[scan_id] = state
        try:
            state.task = asyncio.create_task(_execute_scan(state))
        except Exception as e:
            logger.exception(f"Failed to create scan task: {e}")
            state.status = "error"
            state.events.append({"event": "error", "message": str(e)})
            raise HTTPException(status_code=500, detail=str(e))
        return {"scan_id": scan_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Scan endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scan/{scan_id}/stream")
async def scan_stream(scan_id: str, request: Request):
    """Stream scan events using Server-Sent Events."""
    state = ACTIVE_SCANS.get(scan_id)
    if not state:
        raise HTTPException(status_code=404, detail="Scan not found")

    async def stream():
        sent = 0
        while True:
            if await request.is_disconnected():
                break
            while sent < len(state.events):
                yield sse_dict(state.events[sent])
                sent += 1
            if state.status != "running":
                break
            await asyncio.sleep(0.3)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )


@router.get("/scan/{scan_id}/status")
async def scan_status(scan_id: str):
    """Get status of a running or completed scan."""
    state = ACTIVE_SCANS.get(scan_id)
    if not state:
        raise HTTPException(status_code=404, detail="Scan not found")
    return {
        "scan_id":      scan_id,
        "status":       state.status,
        "target":       state.target,
        "events_count": len(state.events),
        "project_id":   state.project_id,
        "project_name": state.project_name,
        "created_at":   state.created_at,
    }


@router.delete("/scan/{scan_id}")
async def stop_scan_endpoint(scan_id: str):
    """Stop a running scan."""
    state = ACTIVE_SCANS.get(scan_id)
    if not state:
        raise HTTPException(status_code=404, detail="Scan not found")
    state.status = "stopped"
    # Kill the nmap subprocess if a port scan is in progress
    if state.port_scanner:
        try:
            state.port_scanner.stop()
        except Exception:
            pass
    if state.task and not state.task.done():
        state.task.cancel()
    return {"ok": True}


@router.get("/scans")
async def list_active_scans():
    """List all active scans."""
    return [
        {
            "scan_id":      s.scan_id,
            "status":       s.status,
            "target":       s.target,
            "created_at":   s.created_at,
            "events_count": len(s.events),
            "project_id":   s.project_id,
        }
        for s in ACTIVE_SCANS.values()
    ]
