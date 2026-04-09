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

from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel

from scanner.recon import ReconScanner
from scanner.port_scanner import PortScanner
from scanner.web_scanner import WebScanner
from scanner.cve_scanner import CVEScanner
from database import init_db, save_project, list_projects, get_project, rename_project, delete_project, dashboard_stats
from reporter.pdf_reporter import generate_pdf


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
    port_range: str = "top-1000"
    version_detect: bool = False
    scan_type: str = "connect"       # connect | syn | udp | syn_udp | aggressive
    os_detect: bool = False
    port_script: str = ""            # "" | "default" | "banner" | "vuln" | "safe" | "http" | "ssl" | "smb" | "ftp" | "ssh" | "dns" | "smtp"
    port_timing: int = 4             # T0-T5
    skip_ping: bool = False          # -Pn
    port_extra_flags: str = ""       # raw additional nmap flags
    web_depth: int = 1
    recon_wordlist: str = "subdomains-top5000.txt"
    existing_ports: Optional[list] = None
    project_name: Optional[str] = None


class RenameBody(BaseModel):
    name: str


# ── SSE helper ────────────────────────────────────────────────────────────────

def sse(event: str, **kwargs) -> str:
    return f"data: {json.dumps({'event': event, **kwargs}, default=str)}\n\n"

def sse_dict(d: dict) -> str:
    return f"data: {json.dumps(d, default=str)}\n\n"


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok"}


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

    if req.cve and not req.ports and not req.full_scan and not req.existing_ports:
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

async def _execute_scan(state: ScanState):
    req = ScanRequest(**state.config)
    results: dict = {}

    def push(event: str, **kwargs):
        state.events.append({"event": event, **kwargs})

    async def push_progress(msg: str):
        push("progress", message=msg)

    try:
        push("start", target=req.target)

        if (req.recon or req.full_scan) and state.status != "stopped":
            push("module_start", module="recon")
            try:
                scanner = ReconScanner(req.target, wordlist=req.recon_wordlist)
                results["recon"] = await scanner.run(progress_cb=push_progress)
                push("recon", data=results["recon"])
            except Exception as e:
                push("module_error", module="recon", message=str(e))

        if (req.ports or req.full_scan) and state.status != "stopped":
            push("module_start", module="ports")
            try:
                loop = asyncio.get_event_loop()
                port_scanner = PortScanner(
                    target=req.target,
                    port_range=req.port_range,
                    version_detect=req.version_detect,
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
            except Exception as e:
                push("module_error", module="ports", message=str(e))

        open_ports = (
            results.get("ports", {}).get("open_ports")
            or req.existing_ports
            or []
        )

        if (req.cve or req.full_scan) and open_ports and state.status != "stopped":
            push("module_start", module="cve")
            try:
                cve_scanner = CVEScanner(open_ports)
                results["cve"] = await cve_scanner.run(progress_cb=push_progress)
                push("cve", data=results["cve"])
            except Exception as e:
                push("module_error", module="cve", message=str(e))

        if (req.web or req.full_scan) and state.status != "stopped":
            push("module_start", module="web")
            try:
                url = req.target if req.target.startswith("http") else f"https://{req.target}"
                web_scanner = WebScanner(url, depth=req.web_depth)
                results["web"] = await web_scanner.run(progress_cb=push_progress)
                push("web", data=results["web"])
            except Exception as e:
                push("module_error", module="web", message=str(e))

        if state.status != "stopped":
            name = (req.project_name or "").strip() or \
                   f"{req.target} — {datetime.now().strftime('%b %d %H:%M')}"
            pid = save_project(name, req.target, state.config, results)
            state.project_id = pid
            state.project_name = name
            push("done", project_id=pid, project_name=name)
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
