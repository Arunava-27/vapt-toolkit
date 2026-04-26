#!/usr/bin/env python3
"""VAPT Toolkit — FastAPI backend with SSE streaming + project persistence."""

import asyncio
import json
import uuid
import logging
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
from scanner.scope_manager import ScopeManager, get_scope_manager
from scanner.scan_logger import ScanLogger
from scanner.web.web_scanner_orchestrator import WebVulnerabilityScanner, WebScanConfiguration
from scanner.web.scan_comparison import ScanComparator
from scanner.web.bulk_scanner import BulkScanner
from scanner.api_auth import validate_api_key, check_rate_limit, generate_api_key, list_api_keys, revoke_api_key, get_rate_limit_info
from scanner.notifications import get_notification_manager
from scanner.webhooks import get_webhook_manager, WebhookEvent
from scanner.reporters.executive_reporter import ExecutiveReporter
from scanner.reporters.pdf_executive import ExecutivePDFGenerator
from scanner.reporters.heatmap_generator import HeatMapGenerator
from scanner.reporters.export_generator import ExportGenerator, ExportFormat
from scanner.reporters.template_engine import TemplateEngine
from scanner.reporters.templates import (EXECUTIVE_SUMMARY_TEMPLATE, TECHNICAL_REPORT_TEMPLATE,
                                        COMPLIANCE_REPORT_TEMPLATE, RISK_ASSESSMENT_TEMPLATE,
                                        REMEDIATION_ROADMAP_TEMPLATE)
from database import (init_db, save_project, list_projects, get_project, rename_project, delete_project, dashboard_stats,
                     create_bulk_job, get_bulk_job, get_bulk_job_targets, update_bulk_job_status, update_bulk_job_timing,
                     update_bulk_job_counters, update_target_status, list_bulk_jobs, cancel_bulk_job,
                     get_schedule, update_schedule, delete_schedule, create_schedule, list_schedules,
                     save_fp_pattern, get_fp_patterns, update_fp_pattern_status, delete_fp_pattern)
from scanner.reporters.template_engine import TemplateEngine
from scanner.reporters.templates import (EXECUTIVE_SUMMARY_TEMPLATE, TECHNICAL_REPORT_TEMPLATE,
                                        COMPLIANCE_REPORT_TEMPLATE, RISK_ASSESSMENT_TEMPLATE,
                                        REMEDIATION_ROADMAP_TEMPLATE)
from scanner.web.fp_pattern_database import FalsePositivePatternDB
from scanner.json_scan_executor import JSONScanExecutor, JSONScanValidator
from reporter.pdf_reporter import generate_pdf
from wsl_config import wsl


# ── Template Engine ───────────────────────────────────────────────────────────

template_engine = TemplateEngine(db_conn_factory=True)



# ── False Positive Pattern Database ──────────────────────────────────────────

fp_pattern_db = FalsePositivePatternDB()


# ── Logger ────────────────────────────────────────────────────────────────────

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# ── Notification Manager ─────────────────────────────────────────────────────

notification_manager = get_notification_manager()

# ── Webhook Manager ───────────────────────────────────────────────────────────

webhook_manager = get_webhook_manager()

# ── Bulk Scanner ──────────────────────────────────────────────────────────────

async def _execute_scan_for_bulk(target: str, modules: dict, job_id: str = None):
    """Execute a scan for a bulk job."""
    config = {
        "target": target,
        "recon": modules.get("recon", False),
        "ports": modules.get("ports", False),
        "web": modules.get("web", False),
        "cve": modules.get("cve", False),
        "full_scan": modules.get("full_scan", False),
        "scan_classification": modules.get("scan_classification", "active"),
        "port_range": modules.get("port_range", "top-1000"),
    }
    
    # Create a scan state for this target
    scan_id = str(uuid.uuid4())
    state = ScanState(
        scan_id=scan_id,
        target=target,
        config=config,
        project_id=modules.get("project_id"),
        project_name=modules.get("project_name")
    )
    
    ACTIVE_SCANS[scan_id] = state
    
    try:
        await _execute_scan(state)
        result = {
            "scan_id": scan_id,
            "status": state.status,
            "events": state.events,
            "results": {}
        }
        return result
    finally:
        # Clean up old scan
        _gc_scans()


bulk_scanner = BulkScanner(
    max_parallel=10,
    scan_callback=_execute_scan_for_bulk
)

# ── JSON Scan Executor ────────────────────────────────────────────────────────

json_scan_executor = JSONScanExecutor()
json_scan_validator = JSONScanValidator()

# Placeholder for templates - will be initialized after models are defined
SCAN_TEMPLATES = []

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
    skip_ping: bool = True          # -Pn (default True for better host detection)
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


# ── Scope Management Models ───────────────────────────────────────────────

class ScopeValidationRequest(BaseModel):
    """Request to validate scope targets."""
    targets: list[str]


class ScopeExportRequest(BaseModel):
    """Request to export scope."""
    targets: list[str]
    format: str = "json"  # json, yaml, txt


class ScopePresetRequest(BaseModel):
    """Request to save or load scope preset."""
    name: str
    targets: list[str]


class ScopePresetResponse(BaseModel):
    """Response with preset information."""
    id: str
    name: str
    targets: list[str]
    created_at: str


# ── API Key Authentication ────────────────────────────────────────────────────

class ScheduleRequest(BaseModel):
    project_id: str
    frequency: str  # daily, weekly, monthly
    time: str  # HH:MM format


class BulkScanRequest(BaseModel):
    targets: list[str]
    modules: dict
    max_parallel: int = 5
    project_id: Optional[str] = None


class CreateApiKeyResponse(BaseModel):
    api_key: str
    key_id: str
    project_id: str
    created_at: str
    warning: str = "Store this key securely. You won't be able to see it again!"


# ── JSON Scan Instruction Models ──────────────────────────────────────────

class JSONScanRequest(BaseModel):
    """Request to start a scan from JSON instruction."""
    json_instruction: str  # Raw JSON string or dict
    project_name: Optional[str] = None
    project_id: Optional[str] = None


class JSONScanValidationRequest(BaseModel):
    """Request to validate JSON scan instruction."""
    json_instruction: str


class JSONScanResponse(BaseModel):
    """Response for JSON scan execution."""
    scan_id: str
    status: str
    estimated_time_seconds: int
    message: str


class JSONScanValidationResponse(BaseModel):
    """Response for JSON validation."""
    is_valid: bool
    errors: list[str] = []
    suggestions: list[str] = []


class ScanTemplate(BaseModel):
    """Pre-built scan template."""
    id: str
    name: str
    description: str
    icon: str  # emoji or icon name
    json_instruction: dict
    estimated_time_seconds: int


# ── Initialize Scan Templates (now that ScanTemplate model is defined) ────────

SCAN_TEMPLATES = [
    ScanTemplate(
        id="quick-scan",
        name="Quick Scan",
        description="Fast surface-level scan (5-10 min)",
        icon="⚡",
        json_instruction={
            "name": "Quick Scan - {target}",
            "description": "Fast surface-level vulnerability scan",
            "target": "",
            "scope": [],
            "modules": ["xss", "sqli", "headers"],
            "depth": "quick",
            "concurrency": 8,
            "timeout": 300,
            "notifications": {
                "severity_filter": "high",
                "channels": ["desktop"]
            }
        },
        estimated_time_seconds=300
    ),
    ScanTemplate(
        id="full-audit",
        name="Full Audit",
        description="Comprehensive security audit (30-60 min)",
        icon="🔍",
        json_instruction={
            "name": "Full Audit - {target}",
            "description": "Comprehensive security assessment",
            "target": "",
            "scope": [],
            "modules": ["all"],
            "depth": "full",
            "concurrency": 5,
            "timeout": 3600,
            "notifications": {
                "severity_filter": "medium",
                "channels": ["desktop", "email"]
            },
            "export": {
                "formats": ["pdf", "json", "csv"],
                "send_email": True
            }
        },
        estimated_time_seconds=1800
    ),
    ScanTemplate(
        id="api-test",
        name="API Security Test",
        description="REST/GraphQL API security assessment",
        icon="🔗",
        json_instruction={
            "name": "API Test - {target}",
            "description": "API endpoint security assessment",
            "target": "",
            "scope": [],
            "modules": ["sqli", "xss", "csrf", "auth"],
            "depth": "full",
            "concurrency": 10,
            "timeout": 900,
            "advanced": {
                "auth_type": "bearer",
                "skip_robots_txt": True
            }
        },
        estimated_time_seconds=900
    ),
    ScanTemplate(
        id="compliance-scan",
        name="Compliance Scan",
        description="OWASP Top 10, CWE focus (20-30 min)",
        icon="⚖️",
        json_instruction={
            "name": "Compliance Scan - {target}",
            "description": "OWASP Top 10 and CWE compliance check",
            "target": "",
            "scope": [],
            "modules": ["sqli", "xss", "csrf", "idor", "auth", "headers"],
            "depth": "full",
            "concurrency": 5,
            "timeout": 1200,
            "export": {
                "formats": ["pdf", "json"],
                "send_email": True
            }
        },
        estimated_time_seconds=1200
    ),
    ScanTemplate(
        id="ci-cd-scan",
        name="CI/CD Pipeline Scan",
        description="Automated scan for CI/CD integration",
        icon="🔄",
        json_instruction={
            "name": "CI/CD Scan - {target}",
            "description": "Automated security scan for CI/CD pipeline",
            "target": "",
            "scope": [],
            "modules": ["xss", "sqli", "csrf"],
            "depth": "medium",
            "concurrency": 10,
            "timeout": 600,
            "notifications": {
                "severity_filter": "high",
                "channels": ["slack"]
            },
            "export": {
                "formats": ["json", "csv"]
            }
        },
        estimated_time_seconds=600
    )
]


# ── Webhook Models ────────────────────────────────────────────────────────────

class WebhookRegisterRequest(BaseModel):
    url: str
    events: list[str]  # e.g., ["scan_completed", "finding_discovered"]
    secret: str  # Secret for signing webhooks


class WebhookResponse(BaseModel):
    id: str
    project_id: str
    url: str
    events: list[str]
    enabled: bool
    created_at: str
    last_triggered: Optional[str] = None


class WebhookTestRequest(BaseModel):
    webhook_id: str
    event_type: str = "test_event"


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


# ── JSON Scan Instructions ────────────────────────────────────────────────────

@app.post("/api/scans/json/validate")
async def validate_json_scan(req: JSONScanValidationRequest) -> JSONScanValidationResponse:
    """Validate a JSON scan instruction."""
    is_valid, errors = json_scan_validator.validate_json(req.json_instruction)
    suggestions = json_scan_executor.suggest_corrections(req.json_instruction) if not is_valid else []
    
    return JSONScanValidationResponse(
        is_valid=is_valid,
        errors=errors,
        suggestions=suggestions
    )


@app.post("/api/scans/json/from-json")
async def start_scan_from_json(req: JSONScanRequest) -> JSONScanResponse:
    """Start a scan from JSON instruction."""
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
    
    return JSONScanResponse(
        scan_id=scan_id,
        status="running",
        estimated_time_seconds=estimated_time,
        message=f"Scan '{instruction.name}' started. Target: {instruction.target}"
    )


@app.get("/api/scans/json/templates")
async def get_scan_templates() -> dict:
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


@app.get("/api/scans/json/schema")
async def get_json_schema() -> dict:
    """Get JSON schema for validation."""
    return json_scan_executor.get_schema()



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
        
        # Trigger webhook for scan start (non-blocking)
        try:
            await asyncio.wait_for(
                webhook_manager.trigger_webhook(
                    WebhookEvent(
                        event_type="scan_started",
                        scan_id=state.scan_id,
                        data={
                            "target": req.target,
                            "scan_type": req.scan_classification,
                        }
                    )
                ),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            logger.warning(f"Webhook trigger timeout for scan {state.scan_id}")
        except Exception as webhook_err:
            logger.warning(f"Webhook trigger failed: {webhook_err}")
        
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
        is_active = req.scan_classification == "active"
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
                logger.info(f"[SERVER] Port scan completed for {req.target}, found {len(results['ports'].get('open_ports', []))} ports")
                if state.status == "stopped":
                    push("module_error", module="ports", message="Stopped by user.")
                else:
                    logger.info(f"[SERVER] Pushing 'ports' event with {len(results['ports'].get('open_ports', []))} ports to frontend")
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
        # Web scanner runs only when explicitly requested via req.web or req.full_scan
        if (req.web or req.full_scan) and not is_passive and state.status != "stopped":
            push("module_start", module="web")
            try:
                # If ports were found, prefer HTTP over HTTPS
                web_url = req.target
                if not web_url.startswith("http"):
                    # Check if HTTP ports are open (80, 8080, 8000, etc.)
                    http_ports = [p.get("port") for p in open_ports if p.get("proto") == "TCP" and p.get("port") in [80, 8000, 8080, 8009, 8180, 8888, 3000]]
                    if http_ports:
                        web_url = f"http://{req.target}:{http_ports[0]}"
                    else:
                        web_url = f"https://{req.target}"
                
                web_scanner = WebScanner(web_url, depth=req.web_depth)
                results["web"] = await web_scanner.run(progress_cb=push_progress)
                push("web", data=results["web"])
            except Exception as e:
                push("module_error", module="web", message=str(e))
        
        # Comprehensive Web Vulnerability Scanner (NEW)
        if (req.web_vulnerability_scan or req.full_scan or is_active or is_hybrid) and not is_passive and state.status != "stopped":
            push("module_start", module="web_vulnerabilities")
            try:
                # If ports were found, prefer HTTP over HTTPS
                web_url = req.target
                if not web_url.startswith("http"):
                    # Check if HTTP ports are open (80, 8080, 8000, etc.)
                    http_ports = [p.get("port") for p in open_ports if p.get("proto") == "TCP" and p.get("port") in [80, 8000, 8080, 8009, 8180, 8888, 3000]]
                    if http_ports:
                        web_url = f"http://{req.target}:{http_ports[0]}"
                    else:
                        web_url = f"https://{req.target}"
                
                # Build web scan configuration from request
                web_config = WebScanConfiguration(
                    target_url=web_url,
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
            
            # Trigger webhook events
            try:
                await asyncio.wait_for(
                    webhook_manager.trigger_webhook(
                        WebhookEvent(
                            event_type="scan_completed",
                            project_id=pid,
                            scan_id=state.scan_id,
                            data={
                                "target": req.target,
                                "scan_type": req.scan_classification,
                                "results_summary": {
                                    "cves": results.get("cve", {}).get("total_cves", 0),
                                    "ports": len(results.get("ports", {}).get("open_ports", [])),
                                    "subdomains": len(results.get("recon", {}).get("subdomains", [])),
                                    "web_vulns": results.get("web_vulnerabilities", {}).get("total_findings", 0),
                                }
                            }
                        )
                    ),
                    timeout=5.0
                )
            except (asyncio.TimeoutError, Exception) as webhook_err:
                logger.warning(f"Failed to trigger completion webhook: {webhook_err}")

    except asyncio.CancelledError:
        state.status = "stopped"
        push("stopped", message="Scan was cancelled.")
    except Exception as e:
        logger.exception(f"Scan execution error for {req.target}: {e}")
        state.status = "error"
        push("error", message=str(e))
        
        # Trigger webhook for scan failure
        try:
            await webhook_manager.trigger_webhook(
                WebhookEvent(
                    event_type="scan_failed",
                    scan_id=state.scan_id,
                    project_id=state.project_id,
                    data={
                        "target": req.target,
                        "error": str(e),
                        "scan_type": req.scan_classification,
                    }
                )
            )
        except Exception as webhook_err:
            logger.warning(f"Failed to trigger webhook: {webhook_err}")


# ── Scan endpoints ────────────────────────────────────────────────────────────

@app.post("/api/scan")
async def start_scan(req: ScanRequest):
    try:
        _gc_scans()
        scan_id = str(uuid.uuid4())
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
    try:
        loop = asyncio.get_event_loop()
        logger.info("Projects: Starting to fetch list...")
        projects = await asyncio.wait_for(
            loop.run_in_executor(None, list_projects),
            timeout=5.0
        )
        logger.info(f"Projects: Returning {len(projects)} projects")
        return projects
    except asyncio.TimeoutError:
        logger.warning("Projects: list_projects() timed out after 5s")
        raise HTTPException(status_code=503, detail="Database query timeout. Please try again.")
    except Exception as e:
        logger.exception(f"Projects endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard")
async def api_dashboard():
    try:
        loop = asyncio.get_event_loop()
        logger.info("Dashboard: Starting to fetch stats...")
        
        # Fetch dashboard stats with timeout
        try:
            stats = await asyncio.wait_for(
                loop.run_in_executor(None, dashboard_stats),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            logger.warning("Dashboard: dashboard_stats() timed out after 5s")
            stats = {"projects": 0, "ports": 0, "cves": 0, "subdomains": 0, "web": 0}
        
        # Get active scans count
        active = sum(1 for s in ACTIVE_SCANS.values() if s.status == "running")
        
        # Fetch recent projects with timeout
        try:
            recent = await asyncio.wait_for(
                loop.run_in_executor(None, list_projects),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            logger.warning("Dashboard: list_projects() timed out after 5s")
            recent = []
        
        logger.info(f"Dashboard: Returning stats with {len(recent)} recent projects")
        return {**stats, "active_scans": active, "recent_projects": recent[:5]}
    except Exception as e:
        logger.exception(f"Dashboard endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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


@app.get("/api/exports/scan/{pid}")
async def api_export_scan(
    pid: str,
    format: str = "json",
    include_metadata: bool = True,
    include_evidence: bool = True,
    severity: str = None,
    confidence: str = None,
):
    """Export scan results in various formats."""
    try:
        p = get_project(pid)
        if not p:
            raise HTTPException(status_code=404, detail="Project not found")

        # Build scan data from latest scan
        scans = p.get("scans", [])
        if not scans:
            raise HTTPException(status_code=404, detail="No scans found for this project")

        latest_scan = scans[-1]
        scan_data = {
            "config": latest_scan.get("config", {}),
            "results": latest_scan.get("results", {}),
            "timestamp": latest_scan.get("timestamp", datetime.now().isoformat()),
        }

        # Create exporter
        exporter = ExportGenerator(scan_data)

        # Validate format
        try:
            export_format = ExportFormat(format.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

        # Generate export
        loop = asyncio.get_event_loop()
        exported_data = await loop.run_in_executor(
            None,
            exporter.export,
            export_format,
            include_metadata,
            include_evidence,
            severity,
            confidence,
        )

        # Determine response based on format
        if export_format == ExportFormat.JSON:
            return Response(
                content=exported_data,
                media_type="application/json",
                headers={"Content-Disposition": f'attachment; filename="scan-export.json"'},
            )
        elif export_format == ExportFormat.CSV:
            return Response(
                content=exported_data,
                media_type="text/csv",
                headers={"Content-Disposition": f'attachment; filename="scan-export.csv"'},
            )
        elif export_format == ExportFormat.HTML:
            return Response(
                content=exported_data,
                media_type="text/html",
                headers={"Content-Disposition": f'attachment; filename="scan-export.html"'},
            )
        elif export_format == ExportFormat.MARKDOWN:
            return Response(
                content=exported_data,
                media_type="text/markdown",
                headers={"Content-Disposition": f'attachment; filename="scan-export.md"'},
            )
        elif export_format == ExportFormat.SARIF:
            return Response(
                content=exported_data,
                media_type="application/json",
                headers={"Content-Disposition": f'attachment; filename="scan-export.sarif.json"'},
            )
        elif export_format == ExportFormat.XLSX:
            return Response(
                content=exported_data,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f'attachment; filename="scan-export.xlsx"'},
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/exports/bulk")
async def api_export_bulk(
    project_ids: list = None,
    format: str = "json",
    include_metadata: bool = True,
):
    """Export multiple scans in specified format."""
    try:
        if not project_ids:
            all_projects = list_projects()
            project_ids = [p["id"] for p in all_projects]

        exports = []
        for pid in project_ids[:50]:  # Limit to 50 projects
            p = get_project(pid)
            if not p:
                continue

            scans = p.get("scans", [])
            if not scans:
                continue

            latest_scan = scans[-1]
            scan_data = {
                "config": latest_scan.get("config", {}),
                "results": latest_scan.get("results", {}),
                "timestamp": latest_scan.get("timestamp", datetime.now().isoformat()),
            }

            exporter = ExportGenerator(scan_data)
            loop = asyncio.get_event_loop()
            exported = await loop.run_in_executor(
                None,
                exporter.export,
                ExportFormat(format.lower()),
                include_metadata,
                False,  # No evidence for bulk exports
                None,
                None,
            )

            exports.append({
                "project_id": pid,
                "target": p.get("target"),
                "data": exported if format.lower() != "json" else json.loads(exported),
            })

        response_data = {
            "format": format,
            "count": len(exports),
            "exports": exports,
        }

        return Response(
            content=json.dumps(response_data),
            media_type="application/json",
        )

    except Exception as e:
        logger.error(f"Bulk export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/exports/templates")
async def api_get_export_templates():
    """Get list of available export templates."""
    return {
        "templates": [
            {
                "format": "json",
                "name": "JSON",
                "description": "Pretty JSON with full details and metadata",
                "use_case": "Data analysis, integration, archival",
            },
            {
                "format": "csv",
                "name": "CSV",
                "description": "Spreadsheet-compatible findings grid",
                "use_case": "Excel, import to other tools",
            },
            {
                "format": "html",
                "name": "HTML",
                "description": "Standalone interactive report",
                "use_case": "Sharing via email, web view",
            },
            {
                "format": "xlsx",
                "name": "Excel",
                "description": "Professional multi-sheet workbook with formatting",
                "use_case": "Professional reports, executive summaries",
            },
            {
                "format": "markdown",
                "name": "Markdown",
                "description": "GitHub and documentation compatible",
                "use_case": "GitHub repositories, wikis, documentation",
            },
            {
                "format": "sarif",
                "name": "SARIF",
                "description": "GitHub Security Alerts format",
                "use_case": "GitHub integration, CI/CD workflows",
            },
        ]
    }


@app.get("/api/findings/{finding_id}/hints")
async def api_get_finding_hints(finding_id: str):
    """Get manual verification hints for a specific finding."""
    try:
        from scanner.web.verification_hints import VerificationHints
        
        # Search through all projects to find the finding
        all_projects = list_projects()
        for project in all_projects:
            pid = project["id"]
            p = get_project(pid)
            if not p or not p.get("scans"):
                continue
            
            for scan in p["scans"]:
                results = scan.get("results", {})
                web_vulns = results.get("web_vulnerabilities", {}).get("findings", [])
                
                for finding in web_vulns:
                    if finding.get("finding_id") == finding_id:
                        finding_type = finding.get("type")
                        hints = VerificationHints.get_hints_for_type(finding_type)
                        
                        if hints:
                            return {
                                "finding_id": finding_id,
                                "finding_type": finding_type,
                                "hints": {
                                    "title": hints.title,
                                    "description": hints.description,
                                    "steps": hints.steps,
                                    "tools": hints.tools,
                                    "expected_signs": hints.expected_signs,
                                    "false_positive_indicators": hints.false_positive_indicators
                                }
                            }
        
        raise HTTPException(status_code=404, detail="Finding not found")
    except Exception as e:
        logger.error(f"Error retrieving hints for finding {finding_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve hints")


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


# ── Bulk Scanning API ─────────────────────────────────────────────────────────

@app.post("/api/bulk/scan")
async def create_bulk_scan(req: BulkScanRequest):
    """
    Create and start a bulk scanning job.
    
    Request body:
    {
        "targets": ["example.com", "test.com"],
        "modules": {"recon": true, "ports": true, "web": true},
        "max_parallel": 5,
        "project_id": "optional-project-id"
    }
    
    Returns:
    {
        "job_id": "uuid",
        "status": "running",
        "estimated_time_seconds": 300,
        "targets_count": 2,
        "max_parallel": 5
    }
    """
    if not req.targets:
        raise HTTPException(status_code=400, detail="No targets provided")
    
    if len(req.targets) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 targets per job")
    
    if req.max_parallel < 1 or req.max_parallel > 20:
        raise HTTPException(status_code=400, detail="max_parallel must be between 1-20")
    
    try:
        # Create job in database
        job_id = create_bulk_job(
            project_id=req.project_id or str(uuid.uuid4()),
            targets=req.targets,
            config=req.modules.copy()
        )
        
        # Register with bulk scanner
        bulk_scanner.create_job(job_id, req.targets, req.modules)
        bulk_scanner.max_parallel = req.max_parallel
        
        # Start scanning asynchronously
        asyncio.create_task(_run_bulk_job(job_id))
        
        # Get initial status
        status = await bulk_scanner.start_scanning(job_id)
        
        return {
            "job_id": job_id,
            **status,
            "targets_count": len(req.targets)
        }
    
    except Exception as e:
        logger.error(f"Error creating bulk scan: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bulk/jobs")
async def list_bulk_jobs_endpoint(project_id: str = None, limit: int = 50):
    """List all bulk scanning jobs."""
    jobs = list_bulk_jobs(project_id, limit)
    return {"jobs": jobs, "count": len(jobs)}


@app.get("/api/bulk/jobs/{job_id}")
async def get_bulk_job_status(job_id: str):
    """Get status of a bulk scanning job."""
    job = get_bulk_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    status = bulk_scanner.get_job_status(job_id)
    
    return {
        "job_id": job_id,
        "status": job.get("status"),
        "progress": job.get("progress"),
        "completed": job.get("completed_count"),
        "failed": job.get("failed_count"),
        "total": job.get("total_targets"),
        "created_at": job.get("created_at"),
        "started_at": job.get("started_at"),
        "completed_at": job.get("completed_at"),
        "queue_size": bulk_scanner.get_queue_size(job_id),
        "running_count": bulk_scanner.get_running_count(job_id)
    }


@app.get("/api/bulk/jobs/{job_id}/targets")
async def get_bulk_job_targets_endpoint(job_id: str, limit: int = 50, offset: int = 0):
    """Get targets and their status for a bulk job."""
    job = get_bulk_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    targets = get_bulk_job_targets(job_id, limit, offset)
    
    return {
        "job_id": job_id,
        "targets": targets,
        "total": job.get("total_targets"),
        "limit": limit,
        "offset": offset
    }


@app.get("/api/bulk/jobs/{job_id}/results")
async def get_bulk_job_results(job_id: str):
    """Get aggregated results from a bulk scanning job."""
    job = get_bulk_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.get("status") not in ("completed", "cancelled"):
        raise HTTPException(status_code=400, detail="Job is still running or failed")
    
    results = bulk_scanner.get_job_results(job_id)
    
    return {
        "job_id": job_id,
        "status": job.get("status"),
        "created_at": job.get("created_at"),
        "completed_at": job.get("completed_at"),
        "summary": {
            "total": results.get("status", {}).get("total"),
            "completed": results.get("status", {}).get("completed"),
            "failed": results.get("status", {}).get("failed")
        },
        "results": results.get("targets", [])
    }


@app.post("/api/bulk/jobs/{job_id}/cancel")
async def cancel_bulk_job_endpoint(job_id: str):
    """Cancel a running bulk scanning job."""
    job = get_bulk_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.get("status") == "completed":
        raise HTTPException(status_code=400, detail="Job already completed")
    
    if job.get("status") == "cancelled":
        raise HTTPException(status_code=400, detail="Job already cancelled")
    
    result = bulk_scanner.cancel_job(job_id)
    update_bulk_job_status(job_id, "cancelled")
    
    return result


@app.get("/api/bulk/stats")
async def get_bulk_stats():
    """Get statistics about bulk scanning jobs."""
    jobs = list_bulk_jobs(limit=1000)
    
    total_jobs = len(jobs)
    completed = sum(1 for j in jobs if j.get("status") == "completed")
    running = sum(1 for j in jobs if j.get("status") == "running")
    failed = sum(1 for j in jobs if j.get("status") == "failed")
    cancelled = sum(1 for j in jobs if j.get("status") == "cancelled")
    
    total_targets = sum(j.get("total_targets", 0) for j in jobs)
    completed_targets = sum(j.get("completed_count", 0) for j in jobs)
    failed_targets = sum(j.get("failed_count", 0) for j in jobs)
    
    return {
        "total_jobs": total_jobs,
        "status_breakdown": {
            "completed": completed,
            "running": running,
            "failed": failed,
            "cancelled": cancelled,
            "pending": total_jobs - completed - running - failed - cancelled
        },
        "targets": {
            "total": total_targets,
            "completed": completed_targets,
            "failed": failed_targets,
            "success_rate": (completed_targets / total_targets * 100) if total_targets > 0 else 0
        }
    }


# ── Background bulk job processing ────────────────────────────────────────────

async def _run_bulk_job(job_id: str):
    """Background task to process a bulk scanning job."""
    try:
        update_bulk_job_status(job_id, "running")
        update_bulk_job_timing(job_id, started_at=datetime.now().isoformat())
        
        logger.info(f"Starting bulk job {job_id}")
        
        results = await bulk_scanner.process_job(job_id)
        
        # Update database with results
        update_bulk_job_status(job_id, "completed", 100)
        update_bulk_job_timing(job_id, completed_at=datetime.now().isoformat())
        
        # Update target statuses
        for target_result in results.get("results", []):
            target_id = target_result.get("target_id")
            status = target_result.get("status", "unknown")
            result = target_result.get("result")
            error = target_result.get("error")
            
            update_target_status(
                target_id,
                status,
                result=str(result) if result else None,
                error=error,
                completed_at=datetime.now().isoformat()
            )
        
        logger.info(f"Completed bulk job {job_id}")
    
    except Exception as e:
        logger.error(f"Error in bulk job {job_id}: {str(e)}")
        update_bulk_job_status(job_id, "failed")
        update_bulk_job_timing(job_id, completed_at=datetime.now().isoformat())


# ── Webhook Management ────────────────────────────────────────────────────────

@app.post("/api/webhooks")
async def register_webhook(
    body: WebhookRegisterRequest,
    project_id: str = Depends(require_api_key)
) -> WebhookResponse:
    """Register a webhook for a project."""
    project = get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Validate URL
    if not body.url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid webhook URL")
    
    # Validate events
    valid_events = {
        "scan_started", "scan_completed", "finding_discovered",
        "scan_failed", "report_generated", "vulnerability_fixed", "*"
    }
    for event in body.events:
        if event not in valid_events:
            raise HTTPException(status_code=400, detail=f"Invalid event type: {event}")
    
    # Register webhook
    webhook_id = webhook_manager.register_webhook(
        project_id=project_id,
        url=body.url,
        events=body.events,
        secret=body.secret
    )
    
    return WebhookResponse(
        id=webhook_id,
        project_id=project_id,
        url=body.url,
        events=body.events,
        enabled=True,
        created_at=datetime.now().isoformat()
    )


@app.get("/api/webhooks")
async def list_webhooks(project_id: str = Depends(require_api_key)) -> list[WebhookResponse]:
    """List webhooks for a project."""
    project = get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    webhooks = webhook_manager.get_webhooks(project_id=project_id)
    return [WebhookResponse(**w) for w in webhooks]


@app.delete("/api/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    project_id: str = Depends(require_api_key)
) -> dict:
    """Delete a webhook."""
    webhooks = webhook_manager.get_webhooks(project_id=project_id)
    webhook = next((w for w in webhooks if w["id"] == webhook_id), None)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    webhook_manager.delete_webhook(webhook_id)
    return {"ok": True}


@app.post("/api/webhooks/{webhook_id}/enable")
async def enable_webhook(
    webhook_id: str,
    project_id: str = Depends(require_api_key)
) -> dict:
    """Enable a webhook."""
    webhooks = webhook_manager.get_webhooks(project_id=project_id)
    webhook = next((w for w in webhooks if w["id"] == webhook_id), None)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    webhook_manager.enable_webhook(webhook_id)
    return {"ok": True}


@app.post("/api/webhooks/{webhook_id}/disable")
async def disable_webhook(
    webhook_id: str,
    project_id: str = Depends(require_api_key)
) -> dict:
    """Disable a webhook."""
    webhooks = webhook_manager.get_webhooks(project_id=project_id)
    webhook = next((w for w in webhooks if w["id"] == webhook_id), None)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    webhook_manager.disable_webhook(webhook_id)
    return {"ok": True}


@app.get("/api/webhooks/{webhook_id}/logs")
async def get_webhook_logs(
    webhook_id: str,
    limit: int = 50,
    project_id: str = Depends(require_api_key)
) -> dict:
    """Get webhook delivery logs."""
    webhooks = webhook_manager.get_webhooks(project_id=project_id)
    webhook = next((w for w in webhooks if w["id"] == webhook_id), None)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    logs = webhook_manager.get_webhook_logs(webhook_id, limit=limit)
    stats = webhook_manager.get_webhook_stats(webhook_id)
    
    return {
        "logs": logs,
        "stats": stats
    }


@app.post("/api/webhooks/test")
async def test_webhook(
    body: WebhookTestRequest,
    project_id: str = Depends(require_api_key)
) -> dict:
    """Test a webhook by sending a test event."""
    webhooks = webhook_manager.get_webhooks(project_id=project_id)
    webhook = next((w for w in webhooks if w["id"] == body.webhook_id), None)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    # Send test event
    event = WebhookEvent(
        event_type=body.event_type,
        project_id=project_id,
        data={
            "test": True,
            "message": "This is a test event"
        }
    )
    
    result = await webhook_manager.trigger_webhook(event)
    return result


# ── False Positive Patterns API ────────────────────────────────────────────

class FPPatternRequest(BaseModel):
    pattern_type: str
    description: str
    regex_pattern: str
    severity_impact: float = 0.6
    keywords: list = []
    safe_framework: Optional[str] = None


@app.get("/api/patterns/fp")
async def list_fp_patterns(
    pattern_type: Optional[str] = None,
    enabled_only: bool = True,
    _: str = Depends(validate_api_key)
):
    """List all false positive patterns"""
    try:
        # Get patterns from both database and built-in
        db_patterns = get_fp_patterns(enabled_only=enabled_only)
        builtin_patterns = fp_pattern_db.list_patterns(pattern_type=pattern_type, enabled_only=enabled_only)
        
        # Combine and deduplicate by ID
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


@app.post("/api/patterns/fp")
async def create_fp_pattern(
    request: FPPatternRequest,
    _: str = Depends(validate_api_key)
):
    """Create a new custom false positive pattern"""
    try:
        # Validate regex
        pattern_dict = request.dict()
        pattern_id = fp_pattern_db.add_custom_pattern(pattern_dict)
        
        # Also save to database for persistence
        save_fp_pattern(pattern_dict)
        
        return {
            "status": "created",
            "pattern_id": pattern_id,
            "message": "Custom FP pattern created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating FP pattern: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/patterns/fp/{pattern_id}")
async def delete_fp_pattern_endpoint(
    pattern_id: str,
    _: str = Depends(validate_api_key)
):
    """Disable or delete a false positive pattern"""
    try:
        # Disable in memory
        fp_pattern_db.remove_pattern(pattern_id)
        
        # Also update in database
        update_fp_pattern_status(pattern_id, False)
        
        return {
            "status": "disabled",
            "pattern_id": pattern_id,
            "message": "Pattern disabled successfully"
        }
    except Exception as e:
        logger.error(f"Error disabling FP pattern: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/patterns/fp/{pattern_id}/enable")
async def enable_fp_pattern_endpoint(
    pattern_id: str,
    _: str = Depends(validate_api_key)
):
    """Re-enable a disabled false positive pattern"""
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


@app.post("/api/findings/check-fp")
async def check_finding_for_fp(
    request: CheckFindingRequest,
    _: str = Depends(validate_api_key)
):
    """Check if a finding is likely a false positive"""
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


@app.get("/api/patterns/fp/stats")
async def get_fp_pattern_stats(
    _: str = Depends(validate_api_key)
):
    """Get statistics about false positive patterns"""
    try:
        return {
            "stats": fp_pattern_db.get_pattern_stats(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting FP stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Heat Map Report Endpoints ────────────────────────────────────────────────

@app.get("/api/reports/heatmap/by-target")
async def get_heatmap_by_target(
    projectId: str,
    start_date: str = None,
    end_date: str = None
):
    """Get heat map data organized by target and severity."""
    project = get_project(projectId)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    scans = project.get("scans", [])
    if not scans:
        raise HTTPException(status_code=404, detail="No scans available for this project")
    
    # Extract scan results
    scan_results = [scan.get("results", {}) for scan in scans]
    
    def generate_heatmap():
        generator = HeatMapGenerator()
        return generator.generate_by_target(scan_results, start_date, end_date)
    
    loop = asyncio.get_event_loop()
    heatmap_data = await loop.run_in_executor(None, generate_heatmap)
    
    return heatmap_data


@app.get("/api/reports/heatmap/by-time")
async def get_heatmap_by_time(
    projectId: str,
    target: str = None,
    period: str = "week"
):
    """Get time-series heat map data."""
    project = get_project(projectId)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    scans = project.get("scans", [])
    if not scans:
        raise HTTPException(status_code=404, detail="No scans available for this project")
    
    # Extract scan results
    scan_results = [scan.get("results", {}) for scan in scans]
    
    def generate_heatmap():
        generator = HeatMapGenerator()
        return generator.generate_by_time(scan_results, target, period)
    
    loop = asyncio.get_event_loop()
    heatmap_data = await loop.run_in_executor(None, generate_heatmap)
    
    return heatmap_data


@app.get("/api/reports/heatmap/by-severity")
async def get_heatmap_by_severity(projectId: str):
    """Get severity distribution heat map."""
    project = get_project(projectId)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    scans = project.get("scans", [])
    if not scans:
        raise HTTPException(status_code=404, detail="No scans available for this project")
    
    # Extract all findings
    findings = []
    for scan in scans:
        results = scan.get("results", {})
        
        # Web vulnerabilities
        web_vulns = results.get("web_vulnerabilities", {})
        if isinstance(web_vulns, dict):
            findings.extend(web_vulns.get("findings", []))
        
        # CVE findings
        cve_data = results.get("cve", {})
        for corr in cve_data.get("correlations", []):
            for cve in corr.get("cves", []):
                findings.append({
                    "type": "CVE",
                    "title": cve.get("id", "Unknown"),
                    "severity": cve.get("severity", "Medium"),
                    "description": cve.get("description", ""),
                    "cvss_score": cve.get("cvss_score", 0),
                })
    
    def generate_heatmap():
        generator = HeatMapGenerator()
        return generator.generate_by_severity(findings)
    
    loop = asyncio.get_event_loop()
    heatmap_data = await loop.run_in_executor(None, generate_heatmap)
    
    return heatmap_data


@app.get("/api/reports/heatmap/by-type")
async def get_heatmap_by_type(projectId: str):
    """Get heat map data organized by vulnerability type and severity."""
    project = get_project(projectId)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    scans = project.get("scans", [])
    if not scans:
        raise HTTPException(status_code=404, detail="No scans available for this project")
    
    # Extract scan results
    scan_results = [scan.get("results", {}) for scan in scans]
    
    def generate_heatmap():
        generator = HeatMapGenerator()
        return generator.generate_by_vulnerability_type(scan_results)
    
    loop = asyncio.get_event_loop()
    heatmap_data = await loop.run_in_executor(None, generate_heatmap)
    
    return heatmap_data


# ── Scope Management Endpoints ────────────────────────────────────────────

@app.post("/api/scans/scope/validate")
async def validate_scope_endpoint(request: ScopeValidationRequest):
    """
    Validate scope targets.
    
    Returns validation status and any errors found.
    """
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


@app.get("/api/scans/scope/presets")
async def get_scope_presets():
    """
    Get all saved scope presets.
    """
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


@app.post("/api/scans/scope/presets")
async def save_scope_preset(request: ScopePresetRequest):
    """
    Save a new scope preset.
    """
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


@app.delete("/api/scans/scope/presets/{preset_id}")
async def delete_scope_preset(preset_id: str):
    """
    Delete a scope preset.
    """
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


@app.post("/api/scans/scope/expand")
async def expand_scope(request: ScopeValidationRequest):
    """
    Expand scope targets (handle wildcards and CIDR notation).
    
    Returns expanded list of targets.
    """
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


@app.post("/api/scans/scope/export")
async def export_scope(request: ScopeExportRequest):
    """
    Export scope in specified format (json, yaml, txt).
    """
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




# ── Report Template Endpoints ─────────────────────────────────────────────────

@app.get("/api/templates/report")
async def list_report_templates(projectId: str = None):
    """List available report templates."""
    try:
        templates = template_engine.list_templates(projectId)
        return {
            "templates": templates,
            "total": len(templates),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/templates/report")
async def create_report_template(request: dict):
    """Create a new custom report template."""
    try:
        name = request.get("name")
        content = request.get("content")
        project_id = request.get("project_id")
        
        if not name or not content:
            raise HTTPException(status_code=400, detail="Name and content required")
        
        template_id = template_engine.create_template(name, content, project_id)
        return {
            "id": template_id,
            "name": name,
            "created_at": datetime.now().isoformat(),
            "message": "Template created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/templates/report/{template_id}/preview")
async def get_template_preview(template_id: str, projectId: str = None):
    """Get preview of a template with sample data."""
    try:
        project = None
        sample_data = None
        
        if projectId:
            project = get_project(projectId)
            if project and project.get("scans"):
                latest_scan = project["scans"][-1]
                sample_data = {
                    "project_name": project.get("name", "Sample Project"),
                    "target": project.get("target"),
                    "timestamp": latest_scan.get("timestamp"),
                    **latest_scan.get("results", {})
                }
        
        preview_html = template_engine.get_template_preview(template_id, sample_data)
        return {"preview": preview_html}
    except Exception as e:
        logger.error(f"Error generating preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/templates/report/{template_id}/apply")
async def apply_report_template(template_id: str, request: dict):
    """Apply template to scan results and generate report."""
    try:
        project_id = request.get("project_id")
        scan_index = request.get("scan_index", -1)
        
        project = get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        scans = project.get("scans", [])
        if not scans:
            raise HTTPException(status_code=404, detail="No scans available")
        
        scan = scans[scan_index]
        scan_data = {
            "project_name": project.get("name"),
            "target": project.get("target"),
            "timestamp": scan.get("timestamp"),
            **scan.get("results", {})
        }
        
        rendered_html = template_engine.apply_template(template_id, scan_data)
        return {
            "report": rendered_html,
            "project_id": project_id,
            "template_id": template_id,
            "generated_at": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/templates/report/{template_id}")
async def delete_report_template(template_id: str):
    """Delete a report template."""
    try:
        success = template_engine.delete_template(template_id)
        if success:
            return {"message": "Template deleted successfully", "template_id": template_id}
        else:
            raise HTTPException(status_code=404, detail="Template not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/templates/report/preset")
async def save_template_preset(request: dict):
    """Save a template preset configuration."""
    try:
        name = request.get("name")
        config = request.get("config")
        
        if not name or not config:
            raise HTTPException(status_code=400, detail="Name and config required")
        
        preset_id = template_engine.save_template_preset(name, config)
        return {
            "id": preset_id,
            "name": name,
            "created_at": datetime.now().isoformat(),
            "message": "Preset saved successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/templates/report/prebuilt")
async def get_prebuilt_templates():
    """Get list of prebuilt templates."""
    try:
        prebuilt = [
            {
                "id": "executive_summary",
                "name": "Executive Summary",
                "description": "High-level overview for executives and stakeholders",
                "use_case": "Executive management, board reviews"
            },
            {
                "id": "technical_report",
                "name": "Detailed Technical Report",
                "description": "Comprehensive technical findings for security teams",
                "use_case": "Security teams, detailed analysis"
            },
            {
                "id": "compliance_report",
                "name": "Compliance Report",
                "description": "OWASP Top 10, CWE, and CVSS mapped findings",
                "use_case": "Compliance audits, regulatory reporting"
            },
            {
                "id": "risk_assessment",
                "name": "Risk Assessment",
                "description": "Risk-based prioritization and impact analysis",
                "use_case": "Risk management, prioritization"
            },
            {
                "id": "remediation_roadmap",
                "name": "Remediation Roadmap",
                "description": "Actionable remediation timeline and steps",
                "use_case": "Remediation planning, timeline management"
            }
        ]
        return {"templates": prebuilt}
    except Exception as e:
        logger.error(f"Error fetching prebuilt templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
