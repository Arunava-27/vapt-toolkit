import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# Import dependencies from middleware and services
from ..middleware.auth import validate_api_key
from database import (
    get_project, list_projects, get_schedule, list_schedules,
    get_fp_patterns, update_fp_pattern_status, save_fp_pattern,
    create_schedule, update_schedule, delete_schedule
)
from scanner.api_auth import check_rate_limit
from scanner.web.fp_pattern_database import FalsePositivePatternDB
from scanner.scope_manager import get_scope_manager

fp_pattern_db = FalsePositivePatternDB()
from pathlib import Path

# Wordlist configuration
_WORDLISTS_DIR = Path(__file__).parent.parent.parent / "wordlists"

_DOWNLOADABLE = [
    {
        "name": "subdomains-top5000.txt",
        "description": "SecLists — Top 5 000 subdomains",
        "url": (
            "https://raw.githubusercontent.com/danielmiessler/SecLists"
            "/master/Discovery/DNS/subdomains-top1million-5000.txt"
        ),
    },
    {
        "name": "subdomains-top20000.txt",
        "description": "SecLists — Top 20 000 subdomains",
        "url": (
            "https://raw.githubusercontent.com/danielmiessler/SecLists"
            "/master/Discovery/DNS/subdomains-top1million-20000.txt"
        ),
    },
    {
        "name": "subdomains-top110000.txt",
        "description": "SecLists — Top 110 000 subdomains (very large)",
        "url": (
            "https://raw.githubusercontent.com/danielmiessler/SecLists"
            "/master/Discovery/DNS/subdomains-top1million-110000.txt"
        ),
    },
    {
        "name": "dns-jhaddix.txt",
        "description": "jhaddix all.txt — ~2 million (huge, bug bounty)",
        "url": (
            "https://raw.githubusercontent.com/danielmiessler/SecLists"
            "/master/Discovery/DNS/dns-Jhaddix.txt"
        ),
    },
]


def _wordlist_info(path: Path) -> dict:
    """Get wordlist information from a file."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = [l for l in text.splitlines() if l.strip() and not l.startswith("#")]
    return {
        "name":    path.name,
        "lines":   len(lines),
        "size_kb": round(path.stat().st_size / 1024, 1),
    }

_BIG_TARGETS = [
    "facebook.com", "google.com", "amazon.com", "microsoft.com", "cloudflare.com",
    "twitter.com", "x.com", "instagram.com", "youtube.com", "netflix.com",
    "apple.com", "github.com", "linkedin.com", "tiktok.com", "reddit.com",
    "whatsapp.com", "wikipedia.org", "yahoo.com",
]

# --- Health Check Endpoints ---

@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/system/tools")
async def system_tools():
    """Get status of external tools (Nmap, SearchSploit)."""
    from wsl_config import wsl
    return wsl.get_status()


# --- Scan Validation ---

@router.post("/scan/validate")
async def validate_scan(req):
    """Validate scan request against constraints."""
    from server_original import ScanRequest
    
    warnings = []
    target = req.target.lower().strip()

    if any(t in target for t in _BIG_TARGETS):
        warnings.append({
            "level": "warning", "code": "big_target",
            "message": f"'{req.target}' is a major public service. Scans will likely be rate-limited, "
                       "blocked, or very slow. Only scan systems you own or have explicit permission to test."
        })

    if target.startswith(("http://", "https://")):
        warnings.append({
            "level": "info", "code": "protocol_in_target",
            "message": "Target includes http:// or https://. Port and recon scans expect a bare domain or IP — "
                       "the protocol prefix will be stripped for those modules."
        })

    if req.scan_type in ("syn", "syn_udp", "udp"):
        warnings.append({
            "level": "warning", "code": "needs_root",
            "message": f"Scan type '{req.scan_type}' requires root/Administrator privileges "
                       "and Npcap on Windows. The scan will fail without these."
        })

    if req.port_range == "full":
        warnings.append({
            "level": "warning", "code": "full_ports",
            "message": "Full port scan (all 65 535 ports) can take 10–30+ minutes for remote targets."
        })

    if req.port_timing == 5:
        warnings.append({
            "level": "info", "code": "t5_timing",
            "message": "T5 (Insane) timing floods the target with packets — may trigger IDS/IPS or "
                       "produce inaccurate results on slow links."
        })

    is_passive = req.scan_classification == "passive"
    if req.cve and not is_passive and not req.ports and not req.full_scan and not req.existing_ports:
        warnings.append({
            "level": "error", "code": "cve_no_ports",
            "message": "CVE lookup needs port scan results. Enable the 'Port Scan' module, "
                       "or run a port scan first and resume with CVE."
        })

    if req.scan_type == "aggressive" and (req.version_detect or req.os_detect):
        warnings.append({
            "level": "info", "code": "aggressive_redundant",
            "message": "Aggressive mode (-A) already includes version detection (-sV) and OS detection (-O). "
                       "Those toggles are redundant."
        })

    if req.full_scan:
        warnings.append({
            "level": "info", "code": "full_scan_time",
            "message": "Full scan runs all 4 modules sequentially. Expect 5–30+ minutes depending on target."
        })

    if req.port_script == "vuln":
        warnings.append({
            "level": "warning", "code": "vuln_scripts",
            "message": "NSE 'vuln' scripts actively probe for vulnerabilities and can be intrusive. "
                       "Only use on systems you own or have explicit permission to test."
        })

    return {"warnings": warnings}


# --- Schedule Management ---

class ScheduleRequest(BaseModel):
    project_id: str
    frequency: str
    time: str
    day_of_week: Optional[int] = None
    enabled: bool = True


@router.post("/schedule/create")
async def create_schedule_endpoint(req: ScheduleRequest):
    """Create a new scan schedule."""
    if req.frequency not in ("daily", "weekly", "monthly"):
        raise HTTPException(status_code=400, detail="Invalid frequency")
    
    if req.frequency == "weekly" and (req.day_of_week is None or not 0 <= req.day_of_week <= 6):
        raise HTTPException(status_code=400, detail="day_of_week (0-6) required for weekly schedules")
    
    project = get_project(req.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        schedule_data = {
            "project_id": req.project_id, 
            "frequency": req.frequency, 
            "time": req.time, 
            "day_of_week": req.day_of_week, 
            "enabled": req.enabled
        }
        schedule_id = create_schedule(schedule_data)
        return get_schedule(schedule_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/schedules")
async def list_schedules_endpoint():
    """List all schedules."""
    return list_schedules()


@router.get("/schedule/{schedule_id}")
async def get_schedule_endpoint(schedule_id: str):
    """Get schedule details."""
    schedule = get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule


@router.put("/schedule/{schedule_id}")
async def update_schedule_endpoint(schedule_id: str, req: ScheduleRequest):
    """Update a schedule."""
    schedule = get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    if req.frequency not in ("daily", "weekly", "monthly"):
        raise HTTPException(status_code=400, detail="Invalid frequency")
    
    try:
        update_data = {
            "frequency": req.frequency,
            "time": req.time,
            "day_of_week": req.day_of_week,
            "enabled": req.enabled,
        }
        update_schedule(schedule_id, update_data)
        return get_schedule(schedule_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/schedule/{schedule_id}")
async def delete_schedule_endpoint(schedule_id: str):
    """Delete a schedule."""
    schedule = get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    delete_schedule(schedule_id)
    return {"ok": True}


@router.post("/schedule/{schedule_id}/run-now")
async def run_schedule_now(schedule_id: str):
    """Trigger a scheduled scan immediately."""
    schedule = get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    try:
        # TODO: Implement scheduled scan execution
        # For now, just return success message
        return {"ok": True, "message": "Scan queued"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- False Positive Patterns ---

class FPPatternRequest(BaseModel):
    pattern_type: str
    description: str
    regex_pattern: str
    severity_impact: float = 0.6
    keywords: list = []
    safe_framework: Optional[str] = None


@router.get("/patterns/fp")
async def list_fp_patterns(
    pattern_type: Optional[str] = None,
    enabled_only: bool = True,
    _: str = Depends(validate_api_key)
):
    """List all false positive patterns."""
    try:
        db_patterns = get_fp_patterns(enabled_only=enabled_only)
        builtin_patterns = fp_pattern_db.list_patterns(pattern_type=pattern_type, enabled_only=enabled_only)
        
        all_patterns = {p["id"]: p for p in builtin_patterns}
        for p in db_patterns:
            if p["id"] not in all_patterns:
                all_patterns[p["id"]] = p
        
        return {
            "total": len(all_patterns),
            "patterns": sorted(all_patterns.values(), key=lambda x: x["pattern_type"]),
            "stats": fp_pattern_db.get_pattern_stats()
        }
    except Exception as e:
        logger.error(f"Error listing FP patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/patterns/fp")
async def create_fp_pattern(
    request: FPPatternRequest,
    _: str = Depends(validate_api_key)
):
    """Create a new custom false positive pattern."""
    try:
        pattern_dict = request.dict()
        pattern_id = fp_pattern_db.add_custom_pattern(pattern_dict)
        save_fp_pattern(pattern_dict)
        
        return {
            "status": "created",
            "pattern_id": pattern_id,
            "message": "Custom FP pattern created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating FP pattern: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/patterns/fp/{pattern_id}")
async def delete_fp_pattern_endpoint(
    pattern_id: str,
    _: str = Depends(validate_api_key)
):
    """Disable or delete a false positive pattern."""
    try:
        fp_pattern_db.remove_pattern(pattern_id)
        update_fp_pattern_status(pattern_id, False)
        
        return {
            "status": "disabled",
            "pattern_id": pattern_id,
            "message": "Pattern disabled successfully"
        }
    except Exception as e:
        logger.error(f"Error disabling FP pattern: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/patterns/fp/{pattern_id}/enable")
async def enable_fp_pattern_endpoint(
    pattern_id: str,
    _: str = Depends(validate_api_key)
):
    """Re-enable a disabled false positive pattern."""
    try:
        fp_pattern_db.enable_pattern(pattern_id)
        update_fp_pattern_status(pattern_id, True)
        
        return {
            "status": "enabled",
            "pattern_id": pattern_id,
            "message": "Pattern enabled successfully"
        }
    except Exception as e:
        logger.error(f"Error enabling FP pattern: {e}")
        raise HTTPException(status_code=400, detail=str(e))


class CheckFindingRequest(BaseModel):
    title: str
    description: Optional[str] = None
    response_body: Optional[str] = None
    response_headers: Optional[dict] = None
    evidence: Optional[str] = None
    category: Optional[str] = None


@router.post("/findings/check-fp")
async def check_finding_for_fp(
    request: CheckFindingRequest,
    _: str = Depends(validate_api_key)
):
    """Check if a finding is likely a false positive."""
    try:
        finding = request.dict()
        
        is_likely_fp, reason, matched_patterns = fp_pattern_db.check_finding_against_patterns(finding)
        confidence_adjustment = fp_pattern_db.get_confidence_adjustment(finding)
        
        return {
            "is_likely_false_positive": is_likely_fp,
            "confidence_adjustment": confidence_adjustment,
            "reason": reason,
            "matched_patterns": matched_patterns,
            "pattern_details": [
                fp_pattern_db.patterns[pid].description
                for pid in matched_patterns
                if pid in fp_pattern_db.patterns
            ]
        }
    except Exception as e:
        logger.error(f"Error checking finding for FP: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/patterns/fp/stats")
async def get_fp_pattern_stats(
    _: str = Depends(validate_api_key)
):
    """Get statistics about false positive patterns."""
    try:
        return {
            "stats": fp_pattern_db.get_pattern_stats(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting FP stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Scope Management ---

class ScopeValidationRequest(BaseModel):
    targets: list


class ScopePresetRequest(BaseModel):
    name: str
    targets: list


class ScopeExportRequest(BaseModel):
    targets: list
    format: str


@router.post("/scans/scope/validate")
async def validate_scope_endpoint(request: ScopeValidationRequest):
    """Validate scope targets."""
    try:
        scope_manager = get_scope_manager()
        parsed = scope_manager.parse_scope(request.targets)
        
        valid = len(parsed.errors) == 0
        return {
            "valid": valid,
            "errors": parsed.errors,
            "valid_count": len(parsed),
            "total_count": len(request.targets),
            "targets": [t.to_dict() for t in parsed.targets],
        }
    except Exception as e:
        logger.error(f"Error validating scope: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/scans/scope/presets")
async def get_scope_presets():
    """Get all saved scope presets."""
    try:
        scope_manager = get_scope_manager()
        presets = scope_manager.load_presets()
        return {
            "presets": [
                {
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "targets": p.get("targets", []),
                    "created_at": p.get("created_at"),
                }
                for p in presets
            ]
        }
    except Exception as e:
        logger.error(f"Error loading presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scans/scope/presets")
async def save_scope_preset(request: ScopePresetRequest):
    """Save a new scope preset."""
    try:
        if not request.name.strip():
            raise HTTPException(status_code=400, detail="Preset name cannot be empty")
        
        if not request.targets:
            raise HTTPException(status_code=400, detail="Preset must have at least one target")
        
        scope_manager = get_scope_manager()
        preset_id = scope_manager.save_preset(request.name, request.targets)
        
        return {
            "id": preset_id,
            "name": request.name,
            "targets": request.targets,
            "created_at": datetime.now().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/scans/scope/presets/{preset_id}")
async def delete_scope_preset(preset_id: str):
    """Delete a scope preset."""
    try:
        scope_manager = get_scope_manager()
        deleted = scope_manager.delete_preset(preset_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Preset not found")
        
        return {"message": "Preset deleted successfully", "preset_id": preset_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scans/scope/expand")
async def expand_scope(request: ScopeValidationRequest):
    """Expand scope targets (handle wildcards and CIDR notation)."""
    try:
        scope_manager = get_scope_manager()
        expanded = scope_manager.expand_scope(request.targets)
        
        return {
            "original": request.targets,
            "expanded": expanded,
            "count_original": len(request.targets),
            "count_expanded": len(expanded),
        }
    except Exception as e:
        logger.error(f"Error expanding scope: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/scans/scope/export")
async def export_scope(request: ScopeExportRequest):
    """Export scope in specified format (json, yaml, txt)."""
    try:
        if request.format not in ("json", "yaml", "txt"):
            raise HTTPException(status_code=400, detail=f"Invalid format: {request.format}")
        
        scope_manager = get_scope_manager()
        content = scope_manager.export_scope(request.targets, request.format)
        
        return {
            "format": request.format,
            "content": content,
            "target_count": len(request.targets),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting scope: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# --- Wordlist Management ---

class DownloadRequest(BaseModel):
    name: str


@router.get("/wordlists")
async def api_list_wordlists():
    """List available and downloadable wordlists."""
    available = []
    if _WORDLISTS_DIR.exists():
        for f in sorted(_WORDLISTS_DIR.glob("*.txt")):
            available.append(_wordlist_info(f))

    available_names = {a["name"] for a in available}
    downloadable = [d for d in _DOWNLOADABLE if d["name"] not in available_names]

    return {"available": available, "downloadable": downloadable}


@router.post("/wordlists/download")
async def api_download_wordlist(body: DownloadRequest):
    """SSE stream: download wordlist with progress."""
    entry = next((d for d in _DOWNLOADABLE if d["name"] == body.name), None)
    if not entry:
        raise HTTPException(status_code=400, detail="Unknown wordlist name")

    _WORDLISTS_DIR.mkdir(parents=True, exist_ok=True)
    dest = _WORDLISTS_DIR / body.name

    async def _stream():
        try:
            import aiohttp as _aiohttp

            async with _aiohttp.ClientSession() as session:
                async with session.get(
                    entry["url"],
                    timeout=_aiohttp.ClientTimeout(total=300),
                ) as r:
                    if r.status != 200:
                        yield f"data: {json.dumps({'error': f'HTTP {r.status}'})}\n\n"
                        return

                    total = int(r.headers.get("Content-Length", 0))
                    chunks = []
                    received = 0

                    async for chunk in r.content.iter_chunked(32768):
                        chunks.append(chunk)
                        received += len(chunk)
                        pct = int(received * 100 / total) if total else -1
                        yield (
                            f"data: {json.dumps({'progress': pct, 'bytes': received})}\n\n"
                        )

            content = b"".join(chunks)
            dest.write_bytes(content)
            lines = sum(
                1 for l in content.decode(errors="ignore").splitlines()
                if l.strip() and not l.startswith("#")
            )
            yield (
                f"data: {json.dumps({'done': True, 'name': body.name, 'lines': lines, 'size_kb': round(len(content)/1024,1)})}\n\n"
            )
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(_stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.post("/wordlists/upload")
async def api_upload_wordlist(file: UploadFile = File(...)):
    """Upload a custom wordlist."""
    import re as _re
    
    raw_name = file.filename or "custom.txt"
    safe_name = _re.sub(r"[^a-zA-Z0-9_\-.]", "_", raw_name)
    if not safe_name.lower().endswith(".txt"):
        safe_name += ".txt"

    _WORDLISTS_DIR.mkdir(parents=True, exist_ok=True)
    dest = _WORDLISTS_DIR / safe_name
    content = await file.read()
    dest.write_bytes(content)

    lines = sum(1 for l in content.decode(errors="ignore").splitlines()
                if l.strip() and not l.startswith("#"))
    return {"name": safe_name, "lines": lines, "size_kb": round(len(content) / 1024, 1)}


@router.delete("/wordlists/{name}")
async def api_delete_wordlist(name: str):
    """Delete a wordlist."""
    if name == "subdomains-ctf.txt":
        raise HTTPException(status_code=403, detail="Built-in wordlist cannot be deleted")
    dest = _WORDLISTS_DIR / name
    if not dest.exists() or not dest.is_file():
        raise HTTPException(status_code=404, detail="Wordlist not found")
    dest.unlink()
    return {"ok": True}
