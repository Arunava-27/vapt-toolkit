#!/usr/bin/env python3
"""VAPT Toolkit — FastAPI backend with SSE streaming + project persistence."""

import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

import os
import re as _re
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel

from scanner.recon import ReconScanner
from scanner.port_scanner import PortScanner
from scanner.web_scanner import WebScanner
from scanner.cve_scanner import CVEScanner
from scanner.scope import validate_scope, normalize_target, get_scope_summary
from scanner.scan_logger import ScanLogger
from scanner.web.web_scanner_orchestrator import WebVulnerabilityScanner, WebScanConfiguration
from scanner.web.scan_comparison import ScanComparator
from scanner.api_auth import validate_api_key, check_rate_limit, generate_api_key, list_api_keys, revoke_api_key, get_rate_limit_info
from scanner.notifications import get_notification_manager
from scanner.reporters.executive_reporter import ExecutiveReporter
from scanner.reporters.pdf_executive import ExecutivePDFGenerator
from database import init_db, save_project, list_projects, get_project, rename_project, delete_project, dashboard_stats
from reporter.pdf_reporter import generate_pdf
from wsl_config import wsl


# ── Notification Manager ─────────────────────────────────────────────────────

notification_manager = get_notification_manager()

# ── Background scan registry ──────────────────────────────────────────────────

@dataclass
class ScanState:
    scan_id: str
    target: str
    config: dict
    events: list = field(default_factory=list)
    status: str = "running"   # running | done | error | stopped
    task: Optional[asyncio.Task] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    port_scanner: Optional[object] = None   # held so stop() can kill nmap
    notification_config: dict = field(default_factory=lambda: {
        'severity_filter': 'high',  # critical, high, medium, low, all
        'channels': ['desktop'],  # desktop, email, slack, teams
        'email': None,
        'finding_types': 'all'  # all, cve, vulnerability, misconfiguration, etc.
    })

ACTIVE_SCANS: dict[str, ScanState] = {}

def _gc_scans():
    """Remove finished scans older than 2 hours."""
    cutoff = datetime.now().timestamp() - 7200
    stale = [k for k, v in ACTIVE_SCANS.items()
             if v.status != "running"
             and datetime.fromisoformat(v.created_at).timestamp() < cutoff]
    for k in stale:
        del ACTIVE_SCANS[k]


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    
    # Register notification callback to push notifications into scan events
    async def notification_callback(notification):
        # Push to all active scans that have notification channels enabled
        for state in ACTIVE_SCANS.values():
            if state.status == "running" and state.notification_config.get('channels'):
                state.events.append({
                    "event": "notification",
                    **notification
                })
    
    notification_manager.register_callback(notification_callback)
    
    yield


app = FastAPI(title="VAPT Toolkit API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Models ────────────────────────────────────────────────────────────────────

class ScanRequest(BaseModel):
    target: str
    recon: bool = False
    ports: bool = False
    web: bool = False
    cve: bool = False
    full_scan: bool = False
    scan_classification: str = "active"  # active | passive | hybrid
    port_range: str = "top-1000"
    version_detect: bool = False
    scan_type: str = "connect"       # connect | syn | udp | syn_udp | aggressive
    os_detect: bool = False
    port_script: str = ""            # "" | "default" | "banner" | "vuln" | "safe" | "http" | "ssl" | "smb" | "ftp" | "ssh" | "dns" | "smtp"
    port_timing: int = 4             # T0-T5
    skip_ping: bool = False          # -Pn
    port_extra_flags: str = ""       # raw additional nmap flags
    web_depth: int = 1
    web_vulnerability_scan: bool = False  # Enable comprehensive web vulnerability scanning
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
    scope: Optional[list[str]] = None  # Authorized targets for active scans
    override_robots_txt: bool = False  # Override robots.txt (false = respect it)
    schedule_id: Optional[str] = None  # For scans triggered by scheduler
    notification_config: Optional[dict] = None  # Notification settings


class RenameBody(BaseModel):
    name: str


class NotificationConfig(BaseModel):
    severity_filter: str = "high"  # critical, high, medium, low, all
    channels: list[str] = ["desktop"]  # desktop, email, slack, teams
    email: Optional[str] = None
    finding_types: str = "all"  # all, cve, vulnerability, misconfiguration, etc.


class SendNotificationRequest(BaseModel):
    title: str
    message: str
    severity: str = "info"
    finding_type: Optional[str] = None


class ComparisonRequest(BaseModel):
    """Request to compare two scans."""
    scan_id_1: str
    scan_id_2: str
    severity_filter: Optional[list[str]] = None  # List of severities to include
    finding_types: Optional[list[str]] = None  # List of finding types to include
    confidence_min: Optional[int] = None  # Minimum confidence score (0-100)


# ── API Key Authentication ────────────────────────────────────────────────────

class ScheduleRequest(BaseModel):
    project_id: str
    frequency: str  # daily, weekly, monthly
    time: str  # HH:MM format


class CreateApiKeyResponse(BaseModel):
    api_key: str
    key_id: str
    project_id: str
    created_at: str
    warning: str = "Store this key securely. You won't be able to see it again!"


async def get_api_key(authorization: str = Header(None)) -> str:
    """Extract and validate API key from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    try:
        scheme, credentials = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            raise ValueError("Invalid auth scheme")
        return credentials
    except (ValueError, IndexError):
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")


async def require_api_key(api_key: str = Depends(get_api_key)) -> str:
    """Dependency: validate API key and check rate limit."""
    project_id = validate_api_key(api_key)
    if not project_id:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    if not check_rate_limit(api_key):
        raise HTTPException(status_code=429, detail="Rate limit exceeded (100 requests/min)")
    
    return project_id


# ── SSE helper ────────────────────────────────────────────────────────────────

def sse(event: str, **kwargs) -> str:
    return f"data: {json.dumps({'event': event, **kwargs}, default=str)}\n\n"

def sse_dict(d: dict) -> str:
    return f"data: {json.dumps(d, default=str)}\n\n"


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/system/tools")
async def system_tools():
    """Get status of external tools (Nmap, SearchSploit)."""
    return wsl.get_status()


# ── Scan validation ───────────────────────────────────────────────────────────

_BIG_TARGETS = [
    "facebook.com", "google.com", "amazon.com", "microsoft.com", "cloudflare.com",
    "twitter.com", "x.com", "instagram.com", "youtube.com", "netflix.com",
    "apple.com", "github.com", "linkedin.com", "tiktok.com", "reddit.com",
    "whatsapp.com", "wikipedia.org", "yahoo.com",
]

@app.post("/api/scan/validate")
async def validate_scan(req: ScanRequest):
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

    # For active/hybrid scans, CVE needs port data. For passive scans, CVE uses OSINT data only.
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


# ── Background scan task ──────────────────────────────────────────────────────

def _should_send_notification(
    severity: str,
    finding_type: str,
    config: dict
) -> bool:
    """Check if a finding should trigger a notification based on config."""
    severity_levels = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
    
    # Check severity filter
    if config['severity_filter'] != 'all':
        min_severity = severity_levels.get(config['severity_filter'], 0)
        finding_severity = severity_levels.get(severity.lower(), 0)
        if finding_severity < min_severity:
            return False
    
    # Check finding type filter
    if config['finding_types'] != 'all':
        if finding_type not in config['finding_types']:
            return False
    
    return True


async def _send_notification_for_finding(
    state: ScanState,
    finding_title: str,
    finding_details: dict,
    severity: str = "high",
    finding_type: str = "finding"
):
    """Send notification for a finding if it matches the config."""
    if not _should_send_notification(severity, finding_type, state.notification_config):
        return
    
    channels = state.notification_config.get('channels', ['desktop'])
    email = state.notification_config.get('email')
    
    await notification_manager.send_finding_notification(
        finding_title=finding_title,
        finding_details=finding_details,
        severity=severity,
        finding_type=finding_type,
        recipient_email=email,
        channels=channels
    )


async def _execute_scan(state: ScanState):
    req = ScanRequest(**state.config)
    results: dict = {}

    def push(event: str, **kwargs):
        state.events.append({"event": event, **kwargs})

    async def push_progress(msg: str):
        push("progress", message=msg)

    try:
        push("start", target=req.target, scan_type=req.scan_classification)
        
        # Validate target for active scans
        is_active = req.scan_classification == "active"
        if is_active or req.ports or req.web:
            try:
                if not validate_scope(req.target, req.scope):
                    error_msg = f"Target '{req.target}' is NOT in authorized scope. {get_scope_summary(req.scope or [])}"
                    push("module_error", module="scope", message=error_msg)
                    state.status = "error"
                    raise ValueError(error_msg)
                if req.scope:
                    push("progress", message=f"✓ Target verified in scope. {get_scope_summary(req.scope)}")
            except ValueError as e:
                push("module_error", module="scope", message=str(e))
                state.status = "error"
                raise
        
        # Determine which modules to run based on scan classification
        # Passive: recon + cve (non-intrusive)
        # Active: ports + web + cve (intrusive probing)
        # Hybrid: all modules
        is_passive = req.scan_classification == "passive"
        is_hybrid = req.scan_classification == "hybrid" or req.full_scan

        if (req.recon or req.full_scan or is_passive or is_hybrid) and state.status != "stopped":
            push("module_start", module="recon")
            try:
                scanner = ReconScanner(req.target, wordlist=req.recon_wordlist)
                results["recon"] = await scanner.run(progress_cb=push_progress)
                push("recon", data=results["recon"])
            except Exception as e:
                push("module_error", module="recon", message=str(e))

        # CONSTRAINT: Passive scans NEVER run port or web scanning
        if is_passive:
            push("progress", message="[PASSIVE SCAN] Skipping port scanning (intrusive). Only OSINT and CVE lookups.")
        
        if (req.ports or req.full_scan or is_active or is_hybrid) and not is_passive and state.status != "stopped":
            push("module_start", module="ports")
            try:
                loop = asyncio.get_event_loop()
                # Auto-enable version detection if CVE scanning is requested
                version_detect = req.version_detect or (req.cve or req.full_scan)
                port_scanner = PortScanner(
                    target=req.target,
                    port_range=req.port_range,
                    version_detect=version_detect,
                    scan_type=req.scan_type,
                    os_detect=req.os_detect,
                    script=req.port_script,
                    timing=req.port_timing,
                    skip_ping=req.skip_ping,
                    extra_flags=req.port_extra_flags,
                )
                state.port_scanner = port_scanner          # expose for stop()
                push("progress", message=f"Launching nmap on {req.target} (range: {req.port_range}, type: {req.scan_type})…")
                results["ports"] = await loop.run_in_executor(None, port_scanner.run)
                state.port_scanner = None
                if state.status == "stopped":
                    push("module_error", module="ports", message="Stopped by user.")
                else:
                    push("ports", data=results["ports"])
                    
                    # Send notifications for critical open ports
                    open_ports = results["ports"].get("open_ports", [])
                    for port in open_ports:
                        port_num = port.get("port")
                        service = port.get("service", "unknown")
                        severity = "high" if service in ["ssh", "rdp", "telnet", "ftp"] else "medium"
                        
                        await _send_notification_for_finding(
                            state,
                            finding_title=f"Open Port Detected: {port_num}",
                            finding_details={
                                "port": port_num,
                                "protocol": port.get("protocol", "tcp"),
                                "service": service,
                                "version": port.get("version", "unknown"),
                                "target": req.target,
                            },
                            severity=severity,
                            finding_type="open_port"
                        )
            except Exception as e:
                push("module_error", module="ports", message=str(e))

        open_ports = (
            results.get("ports", {}).get("open_ports")
            or req.existing_ports
            or []
        )

        # CVE scanning works with both port data AND OSINT recon data
        if (req.cve or req.full_scan or is_passive or is_hybrid) and state.status != "stopped":
            push("module_start", module="cve")
            try:
                # For passive scans: use recon data; for active: use port data
                recon_data = results.get("recon") if is_passive else None
                cve_scanner = CVEScanner(open_ports=open_ports or [], recon_data=recon_data)
                results["cve"] = await cve_scanner.run(progress_cb=push_progress)
                push("cve", data=results["cve"])
                
                # Send notifications for critical CVEs
                cves = results["cve"].get("vulnerabilities", [])
                for cve in cves:
                    severity = cve.get("severity", "medium").lower()
                    if severity in ["critical", "high"]:
                        await _send_notification_for_finding(
                            state,
                            finding_title=f"CVE Found: {cve.get('id', 'Unknown')}",
                            finding_details={
                                "cve_id": cve.get("id", "Unknown"),
                                "severity": severity,
                                "description": cve.get("description", "")[:500],
                                "target": req.target,
                                "cvss_score": cve.get("cvss_score", "N/A"),
                            },
                            severity=severity,
                            finding_type="cve"
                        )
            except Exception as e:
                push("module_error", module="cve", message=str(e))
        elif is_passive and not open_ports:
            push("progress", message="[PASSIVE SCAN] CVE lookup uses public OSINT data only. No direct port scanning.")

        # CONSTRAINT: Passive scans NEVER run web scanning (active probing)
        if (req.web or req.full_scan or is_active or is_hybrid) and not is_passive and state.status != "stopped":
            push("module_start", module="web")
            try:
                url = req.target if req.target.startswith("http") else f"https://{req.target}"
                web_scanner = WebScanner(url, depth=req.web_depth)
                results["web"] = await web_scanner.run(progress_cb=push_progress)
                push("web", data=results["web"])
            except Exception as e:
                push("module_error", module="web", message=str(e))
        
        # Comprehensive Web Vulnerability Scanner (NEW)
        if (req.web_vulnerability_scan or req.full_scan or is_active or is_hybrid) and not is_passive and state.status != "stopped":
            push("module_start", module="web_vulnerabilities")
            try:
                url = req.target if req.target.startswith("http") else f"https://{req.target}"
                
                # Build web scan configuration from request
                web_config = WebScanConfiguration(
                    target_url=url,
                    scope=req.scope,
                    scope_strict=True,
                    override_robots_txt=req.override_robots_txt,
                    verify_ssl=True,
                    request_timeout=10.0,
                    depth=req.web_depth,
                    test_injection=req.web_test_injection,
                    test_xss=req.web_test_xss,
                    test_auth=req.web_test_auth,
                    test_idor=req.web_test_idor,
                    test_csrf_ssrf=req.web_test_csrf_ssrf,
                    test_file_upload=req.web_test_file_upload,
                    test_misconfiguration=req.web_test_misconfiguration,
                    test_sensitive_data=req.web_test_sensitive_data,
                    test_business_logic=req.web_test_business_logic,
                    test_rate_limiting=req.web_test_rate_limiting,
                    max_pages_to_crawl=50,
                    max_payloads_per_param=30,
                    rate_limit_delay=0.1,
                )
                
                push("progress", message="Starting comprehensive web vulnerability scanning (13 modules)...")
                
                loop = asyncio.get_event_loop()
                web_vuln_scanner = WebVulnerabilityScanner(web_config)
                
                # Run scanner in executor to avoid blocking
                async def run_web_scan():
                    return await loop.run_in_executor(None, web_vuln_scanner.run_scan)
                
                web_vuln_results = await run_web_scan()
                results["web_vulnerabilities"] = web_vuln_results
                
                # Push findings with counts
                total_findings = web_vuln_results.get("total_findings", 0)
                high_severity = web_vuln_results.get("high_severity_count", 0)
                push("progress", message=f"Web vulnerability scan complete: {total_findings} total findings ({high_severity} high severity)")
                push("web_vulnerabilities", data=web_vuln_results)
                
                # Send notifications for critical web vulnerabilities
                vulnerabilities = web_vuln_results.get("vulnerabilities", [])
                for vuln in vulnerabilities:
                    severity = vuln.get("severity", "medium").lower()
                    if severity in ["critical", "high"]:
                        await _send_notification_for_finding(
                            state,
                            finding_title=f"Web Vulnerability: {vuln.get('type', 'Unknown')}",
                            finding_details={
                                "type": vuln.get("type", "Unknown"),
                                "severity": severity,
                                "description": vuln.get("description", "")[:500],
                                "url": vuln.get("url", ""),
                                "target": req.target,
                            },
                            severity=severity,
                            finding_type="web_vulnerability"
                        )
                
            except Exception as e:
                push("module_error", module="web_vulnerabilities", message=str(e))

        if state.status != "stopped":
            name = (req.project_name or "").strip() or \
                   f"{req.target} — {req.scan_classification.title()} — {datetime.now().strftime('%b %d %H:%M')}"
            pid = save_project(name, req.target, state.config, results)
            state.project_id = pid
            state.project_name = name
            push("done", project_id=pid, project_name=name, scan_type=req.scan_classification)
            state.status = "done"

    except asyncio.CancelledError:
        state.status = "stopped"
        push("stopped", message="Scan was cancelled.")
    except Exception as e:
        state.status = "error"
        push("error", message=str(e))


# ── Scan endpoints ────────────────────────────────────────────────────────────

@app.post("/api/scan")
async def start_scan(req: ScanRequest):
    _gc_scans()
    scan_id = str(uuid.uuid4())
    state = ScanState(scan_id=scan_id, target=req.target, config=req.dict())
    ACTIVE_SCANS[scan_id] = state
    state.task = asyncio.create_task(_execute_scan(state))
    return {"scan_id": scan_id}


@app.get("/api/scan/{scan_id}/stream")
async def scan_stream(scan_id: str, request: Request):
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


@app.get("/api/scan/{scan_id}/status")
async def scan_status(scan_id: str):
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


@app.delete("/api/scan/{scan_id}")
async def stop_scan_endpoint(scan_id: str):
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


@app.get("/api/scans")
async def list_active_scans():
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


# ── Projects CRUD ─────────────────────────────────────────────────────────────

@app.get("/api/projects")
async def api_list_projects():
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, list_projects)


@app.get("/api/dashboard")
async def api_dashboard():
    loop = asyncio.get_event_loop()
    stats = await loop.run_in_executor(None, dashboard_stats)
    active = sum(1 for s in ACTIVE_SCANS.values() if s.status == "running")
    recent = await loop.run_in_executor(None, list_projects)
    return {**stats, "active_scans": active, "recent_projects": recent[:5]}


@app.get("/api/projects/{pid}")
async def api_get_project(pid: str):
    p = get_project(pid)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return p


@app.put("/api/projects/{pid}")
async def api_rename_project(pid: str, body: RenameBody):
    if not get_project(pid):
        raise HTTPException(status_code=404, detail="Project not found")
    rename_project(pid, body.name.strip())
    return {"ok": True}


@app.delete("/api/projects/{pid}")
async def api_delete_project(pid: str):
    if not get_project(pid):
        raise HTTPException(status_code=404, detail="Project not found")
    delete_project(pid)
    return {"ok": True}


@app.get("/api/projects/{pid}/pdf")
async def api_export_pdf(pid: str):
    p = get_project(pid)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    loop = asyncio.get_event_loop()
    pdf_bytes = await loop.run_in_executor(None, generate_pdf, p)
    slug = "".join(c if c.isalnum() or c in "-_." else "-" for c in p["target"])
    filename = f"vapt-{slug}-{pid[:8]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/compare/scans")
async def api_compare_scans(body: ComparisonRequest):
    """
    Compare two scans and return detailed comparison results.
    
    Response includes:
    - new_findings: Vulnerabilities found in scan 2 but not scan 1
    - fixed_findings: Vulnerabilities found in scan 1 but not scan 2
    - unchanged_findings: Vulnerabilities present in both scans
    - regressions: Vulnerabilities previously fixed but reappeared
    - risk_delta: Change in overall risk score (negative=improving, positive=degrading)
    - risk_trend: "improving", "degrading", or "stable"
    - severity_distribution: Breakdown by severity level
    """
    # Get both projects by scan ID
    project_1 = None
    project_2 = None
    scan_1 = None
    scan_2 = None
    
    # Search through all projects to find scans
    all_projects = list_projects()
    for project in all_projects:
        pid = project["id"]
        p = get_project(pid)
        if p and p.get("scans"):
            for scan in p["scans"]:
                if scan.get("scan_id") == body.scan_id_1:
                    project_1 = p
                    scan_1 = scan
                if scan.get("scan_id") == body.scan_id_2:
                    project_2 = p
                    scan_2 = scan
    
    if not scan_1 or not scan_2:
        raise HTTPException(
            status_code=404,
            detail="One or both scans not found"
        )
    
    # Build filters
    filters = {}
    if body.severity_filter:
        filters["severity"] = body.severity_filter
    if body.finding_types:
        filters["finding_types"] = body.finding_types
    if body.confidence_min is not None:
        filters["confidence_min"] = body.confidence_min
    
    # Compare scans
    comparator = ScanComparator()
    comparison_result = comparator.compare_scans(scan_1, scan_2, filters if filters else None)
    
    return comparison_result.to_dict()


# ── Executive Report Endpoints ────────────────────────────────────────────────

@app.get("/api/reports/executive/{pid}")
async def get_executive_report(pid: str):
    """Get executive summary report data for a project."""
    project = get_project(pid)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    scans = project.get("scans", [])
    if not scans:
        raise HTTPException(status_code=404, detail="No scans available for this project")
    
    latest_scan = scans[-1]
    scan_result = latest_scan.get("results", {})
    
    def generate_report():
        reporter = ExecutiveReporter(scan_result, historical_scans=scans[:-1] if len(scans) > 1 else [])
        return reporter.get_summary_data()
    
    loop = asyncio.get_event_loop()
    report_data = await loop.run_in_executor(None, generate_report)
    
    return {
        "project_id": pid,
        "target": project.get("target"),
        "scan_count": len(scans),
        **report_data,
    }


@app.get("/api/reports/executive/{pid}/html")
async def get_executive_report_html(pid: str):
    """Get executive summary report as HTML."""
    project = get_project(pid)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    scans = project.get("scans", [])
    if not scans:
        raise HTTPException(status_code=404, detail="No scans available for this project")
    
    latest_scan = scans[-1]
    scan_result = latest_scan.get("results", {})
    
    def generate_html():
        reporter = ExecutiveReporter(scan_result, historical_scans=scans[:-1] if len(scans) > 1 else [])
        return reporter.generate_html()
    
    loop = asyncio.get_event_loop()
    html_content = await loop.run_in_executor(None, generate_html)
    
    slug = "".join(c if c.isalnum() or c in "-_." else "-" for c in project.get("target", "report"))
    
    return Response(
        content=html_content,
        media_type="text/html",
        headers={"Content-Disposition": f'inline; filename="executive-{slug}.html"'},
    )


@app.get("/api/reports/executive/{pid}/pdf")
async def get_executive_report_pdf(pid: str):
    """Get executive summary report as PDF."""
    project = get_project(pid)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    scans = project.get("scans", [])
    if not scans:
        raise HTTPException(status_code=404, detail="No scans available for this project")
    
    latest_scan = scans[-1]
    scan_result = latest_scan.get("results", {})
    
    def generate_pdf():
        reporter = ExecutiveReporter(scan_result, historical_scans=scans[:-1] if len(scans) > 1 else [])
        report_data = reporter.get_summary_data()
        pdf_generator = ExecutivePDFGenerator(report_data)
        return pdf_generator.generate()
    
    loop = asyncio.get_event_loop()
    pdf_buffer = await loop.run_in_executor(None, generate_pdf)
    
    slug = "".join(c if c.isalnum() or c in "-_." else "-" for c in project.get("target", "report"))
    filename = f"executive-{slug}-{pid[:8]}.pdf"
    
    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── API Automation Endpoints ──────────────────────────────────────────────────

@app.get("/api/scan/{scan_id}/status")
async def api_get_scan_status(scan_id: str, project_id: str = Depends(require_api_key)):
    """Get real-time scan status with progress and findings."""
    state = ACTIVE_SCANS.get(scan_id)
    if not state:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Check if project owns this scan
    if state.project_id and state.project_id != project_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Calculate progress and find phases
    progress = 0
    current_phase = "pending"
    findings_count = 0
    estimated_remaining = 0
    
    events = state.events
    if events:
        # Parse phase from events
        for event in reversed(events):
            if event.get("event") == "module_start":
                current_phase = event.get("module", "processing")
                break
        
        # Count findings
        for event in events:
            if event.get("event") in ("recon", "ports", "web", "cve"):
                data = event.get("data", {})
                findings_count += len(data.get("vulnerabilities", []))
                findings_count += len(data.get("open_ports", []))
        
        # Estimate progress (4 main modules)
        modules_started = sum(1 for e in events if e.get("event") == "module_start")
        progress = min((modules_started / 4) * 100, 95) if state.status == "running" else 100
    
    elapsed = (datetime.now() - datetime.fromisoformat(state.created_at)).total_seconds()
    estimated_remaining = max(0, (elapsed / (progress / 100)) - elapsed) if progress > 0 else 0
    
    return {
        "scan_id": scan_id,
        "status": state.status,
        "progress": int(progress),
        "elapsed_time": int(elapsed),
        "estimated_remaining": int(estimated_remaining),
        "current_phase": current_phase,
        "findings_count": findings_count,
        "message": events[-1].get("message", "") if events else "Starting scan..."
    }


@app.post("/api/scan/{scan_id}/stop")
async def api_stop_scan(scan_id: str, project_id: str = Depends(require_api_key)):
    """Stop a running scan and return current findings."""
    state = ACTIVE_SCANS.get(scan_id)
    if not state:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Check if project owns this scan
    if state.project_id and state.project_id != project_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    state.status = "stopped"
    if state.port_scanner:
        try:
            state.port_scanner.stop()
        except Exception:
            pass
    if state.task and not state.task.done():
        state.task.cancel()
    
    # Collect current findings from events
    findings = []
    for event in state.events:
        if event.get("event") in ("recon", "ports", "web", "cve"):
            data = event.get("data", {})
            if event.get("event") == "ports" and "open_ports" in data:
                for port in data["open_ports"][:10]:  # Limit to 10
                    findings.append({
                        "type": "open_port",
                        "severity": "INFO",
                        "endpoint": f"{port.get('port')}/{port.get('protocol', 'tcp')}",
                        "confidence_score": 100
                    })
    
    return {
        "status": "stopped",
        "findings": findings
    }


@app.get("/api/findings/latest")
async def api_get_latest_findings(
    severity: Optional[str] = None,
    limit: int = 10,
    project_id: str = Depends(require_api_key)
):
    """Get latest findings from recent scans with optional filtering."""
    if limit > 100:
        limit = 100
    if limit < 1:
        limit = 1
    
    # Collect findings from all projects or specific project
    findings = []
    projects = list_projects()
    
    for project in projects:
        if severity and severity not in findings:
            continue
        
        for scan in project.get("scans", [])[:1]:  # Get latest scan only
            results = scan.get("results", {})
            
            # Extract findings from different modules
            ports = results.get("ports", {}).get("open_ports", [])
            for port in ports:
                findings.append({
                    "type": "open_port",
                    "severity": "INFO",
                    "endpoint": f"{port.get('port')}/{port.get('protocol', 'tcp')}",
                    "confidence_score": 100,
                    "project_id": project["id"],
                    "timestamp": scan.get("timestamp", "")
                })
            
            # CVE findings
            cves = results.get("cve", {}).get("correlations", [])
            for corr in cves:
                for cve in corr.get("cves", []):
                    cve_severity = (cve.get("severity") or "NONE").upper()
                    if severity and severity != cve_severity:
                        continue
                    findings.append({
                        "type": "cve",
                        "severity": cve_severity,
                        "endpoint": cve.get("cve_id", ""),
                        "confidence_score": 95,
                        "project_id": project["id"],
                        "timestamp": scan.get("timestamp", "")
                    })
            
            # Web vulnerabilities
            web_vulns = results.get("web_vulnerabilities", {}).get("findings", [])
            for vuln in web_vulns:
                vuln_severity = (vuln.get("severity") or "MEDIUM").upper()
                if severity and severity != vuln_severity:
                    continue
                findings.append({
                    "type": vuln.get("type", "web_issue"),
                    "severity": vuln_severity,
                    "endpoint": vuln.get("endpoint", ""),
                    "confidence_score": 85,
                    "project_id": project["id"],
                    "timestamp": scan.get("timestamp", "")
                })
    
    # Sort by timestamp (newest first) and limit
    findings.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return findings[:limit]


@app.post("/api/schedule/create")
async def api_create_schedule(body: ScheduleRequest, project_id: str = Depends(require_api_key)):
    """Create a scheduled scan (returns confirmation, actual scheduling handled separately)."""
    if body.project_id != project_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    p = get_project(body.project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Validate schedule parameters
    if body.frequency not in ("daily", "weekly", "monthly"):
        raise HTTPException(status_code=400, detail="Invalid frequency")
    
    try:
        h, m = body.time.split(":")
        h, m = int(h), int(m)
        if not (0 <= h < 24 and 0 <= m < 60):
            raise ValueError()
    except (ValueError, IndexError):
        raise HTTPException(status_code=400, detail="Invalid time format (use HH:MM)")
    
    return {
        "status": "scheduled",
        "project_id": body.project_id,
        "frequency": body.frequency,
        "time": body.time,
        "message": f"Scan scheduled {body.frequency} at {body.time}",
        "note": "Implement actual scheduling in production environment"
    }


@app.get("/api/scan/{scan_id}/results")
async def api_get_scan_results(scan_id: str, project_id: str = Depends(require_api_key)):
    """Get complete scan results in JSON format."""
    state = ACTIVE_SCANS.get(scan_id)
    if not state:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Check if project owns this scan
    if state.project_id and state.project_id != project_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Compile results from state events
    results = {
        "scan_id": scan_id,
        "status": state.status,
        "target": state.target,
        "project_id": state.project_id,
        "created_at": state.created_at,
        "events": state.events,
    }
    
    return results


# ── API Key Management ────────────────────────────────────────────────────────

@app.post("/api/keys/create")
async def api_create_key(project_id: str = Depends(require_api_key)) -> CreateApiKeyResponse:
    """Generate a new API key for the authenticated project."""
    p = get_project(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    
    plain_key, key_hash = generate_api_key(project_id)
    
    return CreateApiKeyResponse(
        api_key=plain_key,
        key_id=key_hash[:16],
        project_id=project_id,
        created_at=datetime.now().isoformat(),
    )


@app.get("/api/keys/list")
async def api_list_keys(project_id: str = Depends(require_api_key)):
    """List all API keys for the authenticated project (masked)."""
    p = get_project(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {"keys": list_api_keys(project_id)}


@app.delete("/api/keys/{key_id}")
async def api_revoke_key(key_id: str, project_id: str = Depends(require_api_key)):
    """Revoke an API key."""
    p = get_project(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    
    revoke_api_key(key_id)
    return {"ok": True}


@app.get("/api/keys/info")
async def api_get_key_info(authorization: str = Header(None)):
    """Get rate limit info for the current API key (no auth check)."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    try:
        scheme, credentials = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            raise ValueError()
    except (ValueError, IndexError):
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")
    
    return get_rate_limit_info(credentials)


# ── Wordlist management ───────────────────────────────────────────────────────

_WORDLISTS_DIR = Path(__file__).parent / "wordlists"

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
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = [l for l in text.splitlines() if l.strip() and not l.startswith("#")]
    return {
        "name":    path.name,
        "lines":   len(lines),
        "size_kb": round(path.stat().st_size / 1024, 1),
    }


@app.get("/api/wordlists")
async def api_list_wordlists():
    available = []
    if _WORDLISTS_DIR.exists():
        for f in sorted(_WORDLISTS_DIR.glob("*.txt")):
            available.append(_wordlist_info(f))

    available_names = {a["name"] for a in available}
    downloadable = [d for d in _DOWNLOADABLE if d["name"] not in available_names]

    return {"available": available, "downloadable": downloadable}


class DownloadRequest(BaseModel):
    name: str


@app.post("/api/wordlists/download")
async def api_download_wordlist(body: DownloadRequest):
    """SSE stream: data: {"progress": 0-100, "bytes": N} … data: {"done": true, "lines": N}"""
    entry = next((d for d in _DOWNLOADABLE if d["name"] == body.name), None)
    if not entry:
        raise HTTPException(status_code=400, detail="Unknown wordlist name")

    _WORDLISTS_DIR.mkdir(parents=True, exist_ok=True)
    dest = _WORDLISTS_DIR / body.name

    import aiohttp as _aiohttp

    async def _stream():
        try:
            async with _aiohttp.ClientSession() as session:
                async with session.get(
                    entry["url"],
                    timeout=_aiohttp.ClientTimeout(total=300),
                ) as r:
                    if r.status != 200:
                        yield f"data: {json.dumps({'error': f'HTTP {r.status}'})}\n\n"
                        return

                    total = int(r.headers.get("Content-Length", 0))
                    chunks: list[bytes] = []
                    received = 0

                    async for chunk in r.content.iter_chunked(32768):  # 32 KB chunks
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


@app.post("/api/wordlists/upload")
async def api_upload_wordlist(file: UploadFile = File(...)):
    raw_name = file.filename or "custom.txt"
    # Sanitise filename — keep only safe chars
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


@app.delete("/api/wordlists/{name}")
async def api_delete_wordlist(name: str):
    # Never allow deleting the built-in CTF list
    if name == "subdomains-ctf.txt":
        raise HTTPException(status_code=403, detail="Built-in wordlist cannot be deleted")
    dest = _WORDLISTS_DIR / name
    if not dest.exists() or not dest.is_file():
        raise HTTPException(status_code=404, detail="Wordlist not found")
    dest.unlink()
    return {"ok": True}


# ── Notification Management ───────────────────────────────────────────────────

@app.post("/api/scan/{scan_id}/notification/config")
async def set_scan_notification_config(scan_id: str, config: NotificationConfig):
    """Set notification configuration for a scan."""
    state = ACTIVE_SCANS.get(scan_id)
    if not state:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    state.notification_config = {
        'severity_filter': config.severity_filter,
        'channels': config.channels,
        'email': config.email,
        'finding_types': config.finding_types,
    }
    
    return {"ok": True, "notification_config": state.notification_config}


@app.get("/api/scan/{scan_id}/notification/config")
async def get_scan_notification_config(scan_id: str):
    """Get notification configuration for a scan."""
    state = ACTIVE_SCANS.get(scan_id)
    if not state:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    return state.notification_config


@app.post("/api/notification/send")
async def send_test_notification(req: SendNotificationRequest):
    """Send a test notification (for UI testing)."""
    result = await notification_manager.send_desktop_notification(
        title=req.title,
        message=req.message,
        severity=req.severity,
        finding_type=req.finding_type
    )
    return {"ok": result, "message": "Notification sent"}


@app.post("/api/notification/test-email")
async def test_email_notification(email: str):
    """Send a test email notification."""
    test_finding = {
        'type': 'test',
        'description': 'This is a test notification',
        'timestamp': datetime.now().isoformat(),
    }
    
    result = notification_manager.send_email_notification(
        recipient=email,
        finding_title="Test Finding",
        finding_details=test_finding,
        severity="high"
    )
    
    return {"ok": result, "message": "Test email sent" if result else "Failed to send email"}


@app.post("/api/notification/test-slack")
async def test_slack_notification():
    """Send a test Slack notification."""
    test_finding = {
        'type': 'test',
        'description': 'This is a test notification from VAPT Toolkit',
        'timestamp': datetime.now().isoformat(),
    }
    
    result = await notification_manager.send_slack_webhook(
        finding_title="Test Finding",
        finding_details=test_finding,
        severity="high"
    )
    
    return {"ok": result, "message": "Test Slack notification sent" if result else "Failed to send Slack notification"}


@app.post("/api/notification/test-teams")
async def test_teams_notification():
    """Send a test Teams notification."""
    test_finding = {
        'type': 'test',
        'description': 'This is a test notification from VAPT Toolkit',
        'timestamp': datetime.now().isoformat(),
    }
    
    result = await notification_manager.send_teams_webhook(
        finding_title="Test Finding",
        finding_details=test_finding,
        severity="high"
    )
    
    return {"ok": result, "message": "Test Teams notification sent" if result else "Failed to send Teams notification"}


@app.get("/api/notification/config")
async def get_notification_config():
    """Get global notification configuration status."""
    return {
        'smtp_configured': bool(notification_manager.smtp_config.get('host')),
        'slack_configured': bool(notification_manager.slack_webhook),
        'teams_configured': bool(notification_manager.teams_webhook),
        'smtp_host': notification_manager.smtp_config.get('host', ''),
    }


# ── Schedule Management ───────────────────────────────────────────────────────

class ScheduleRequest(BaseModel):
    project_id: str
    frequency: str  # 'daily', 'weekly', 'monthly'
    time: str       # 'HH:MM' format
    day_of_week: Optional[int] = None  # 0-6 for weekly (Monday=0)
    enabled: bool = True


@app.post("/api/schedule/create")
async def create_schedule_endpoint(req: ScheduleRequest):
    """Create a new scan schedule."""
    if req.frequency not in ("daily", "weekly", "monthly"):
        raise HTTPException(status_code=400, detail="Invalid frequency")
    
    if req.frequency == "weekly" and (req.day_of_week is None or not 0 <= req.day_of_week <= 6):
        raise HTTPException(status_code=400, detail="day_of_week (0-6) required for weekly schedules")
    
    # Validate project exists
    project = get_project(req.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        schedule = scheduler.create_schedule(
            project_id=req.project_id, 
            frequency=req.frequency, 
            time_str=req.time, 
            day_of_week=req.day_of_week, 
            enabled=req.enabled
        )
        return schedule
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/schedules")
async def list_schedules_endpoint():
    """List all schedules."""
    return list_schedules()


@app.get("/api/schedule/{schedule_id}")
async def get_schedule_endpoint(schedule_id: str):
    """Get schedule details."""
    schedule = get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule


@app.put("/api/schedule/{schedule_id}")
async def update_schedule_endpoint(schedule_id: str, req: ScheduleRequest):
    """Update a schedule."""
    schedule = get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    if req.frequency not in ("daily", "weekly", "monthly"):
        raise HTTPException(status_code=400, detail="Invalid frequency")
    
    try:
        updated = scheduler.update_schedule(schedule_id, {
            "frequency": req.frequency,
            "time": req.time,
            "day_of_week": req.day_of_week,
            "enabled": req.enabled,
        })
        return updated
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/schedule/{schedule_id}")
async def delete_schedule_endpoint(schedule_id: str):
    """Delete a schedule."""
    schedule = get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    scheduler.delete_schedule(schedule_id)
    return {"ok": True}


@app.post("/api/schedule/{schedule_id}/run-now")
async def run_schedule_now(schedule_id: str):
    """Trigger a scheduled scan immediately."""
    schedule = get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    try:
        # Queue the scan to run immediately
        scheduler.run_scheduled_scan(schedule_id)
        return {"ok": True, "message": "Scan queued"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── OpenAPI / Swagger Documentation ───────────────────────────────────────────

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="VAPT Toolkit REST API",
        version="1.0.0",
        description="REST API for bulk scanning, status tracking, and automation.",
        routes=app.routes,
    )
    
    # Add API key security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "custom",
            "description": "API key authentication. Use format: Bearer <api_key>"
        }
    }
    
    # Add global security requirement
    openapi_schema["security"] = [{"BearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
