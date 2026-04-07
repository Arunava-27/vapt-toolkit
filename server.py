#!/usr/bin/env python3
"""VAPT Toolkit — FastAPI backend with SSE streaming + project persistence."""

import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

import os
import re as _re
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
from typing import Optional

from scanner.recon import ReconScanner
from scanner.port_scanner import PortScanner
from scanner.web_scanner import WebScanner
from scanner.cve_scanner import CVEScanner
from database import init_db, save_project, list_projects, get_project, rename_project, delete_project
from reporter.pdf_reporter import generate_pdf


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
    web_depth: int = 1
    recon_wordlist: str = "subdomains-top5000.txt"  # filename or preset alias ("ctf"|"medium"|"large")
    existing_ports: Optional[list] = None
    project_name: Optional[str] = None  # auto-generated if omitted


class RenameBody(BaseModel):
    name: str


# ── SSE helper ────────────────────────────────────────────────────────────────

def sse(event: str, **kwargs) -> str:
    return f"data: {json.dumps({'event': event, **kwargs}, default=str)}\n\n"


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok"}


# ── Scan (SSE streaming) ──────────────────────────────────────────────────────

@app.post("/api/scan")
async def run_scan(req: ScanRequest, request: Request):
    async def stream():
        results = {}
        try:
            yield sse("start", target=req.target)

            if req.recon or req.full_scan:
                if await request.is_disconnected():
                    return
                yield sse("module_start", module="recon")
                scanner = ReconScanner(req.target, wordlist=req.recon_wordlist)
                results["recon"] = await scanner.run()
                yield sse("recon", data=results["recon"])

            if req.ports or req.full_scan:
                if await request.is_disconnected():
                    return
                yield sse("module_start", module="ports")
                loop = asyncio.get_event_loop()
                port_scanner = PortScanner(req.target, req.port_range, req.version_detect)
                results["ports"] = await loop.run_in_executor(None, port_scanner.run)
                yield sse("ports", data=results["ports"])

            open_ports = (
                results.get("ports", {}).get("open_ports")
                or req.existing_ports
                or []
            )
            if (req.cve or req.full_scan) and open_ports:
                if await request.is_disconnected():
                    return
                yield sse("module_start", module="cve")
                cve_scanner = CVEScanner(open_ports)
                results["cve"] = await cve_scanner.run()
                yield sse("cve", data=results["cve"])

            if req.web or req.full_scan:
                if await request.is_disconnected():
                    return
                yield sse("module_start", module="web")
                url = req.target if req.target.startswith("http") else f"https://{req.target}"
                web_scanner = WebScanner(url, depth=req.web_depth)
                results["web"] = await web_scanner.run()
                yield sse("web", data=results["web"])

            # Auto-save to DB
            name = (req.project_name or "").strip() or \
                   f"{req.target} — {datetime.now().strftime('%b %d %H:%M')}"
            pid = save_project(name, req.target, req.dict(), results)
            yield sse("done", results=results, project_id=pid, project_name=name)

        except Exception as e:
            yield sse("error", message=str(e))

    return StreamingResponse(stream(), media_type="text/event-stream")


# ── Projects CRUD ─────────────────────────────────────────────────────────────

@app.get("/api/projects")
async def api_list_projects():
    return list_projects()


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
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
