"""SQLite persistence for VAPT scan projects."""
import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(__file__).parent / "vapt.db"


@contextmanager
def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id         TEXT PRIMARY KEY,
                name       TEXT NOT NULL,
                target     TEXT NOT NULL,
                status     TEXT DEFAULT 'completed',
                config     TEXT,
                results    TEXT,
                created_at TEXT
            )
        """)


# ── Write ─────────────────────────────────────────────────────────────────────

def save_project(name: str, target: str, config: dict, results: dict,
                 status: str = "completed") -> str:
    pid = str(uuid.uuid4())
    with _conn() as c:
        c.execute(
            "INSERT INTO projects (id, name, target, status, config, results, created_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (pid, name, target, status,
             json.dumps(config, default=str),
             json.dumps(results, default=str),
             datetime.now().isoformat())
        )
    return pid


def rename_project(pid: str, name: str):
    with _conn() as c:
        c.execute("UPDATE projects SET name=? WHERE id=?", (name, pid))


def delete_project(pid: str):
    with _conn() as c:
        c.execute("DELETE FROM projects WHERE id=?", (pid,))


# ── Read ──────────────────────────────────────────────────────────────────────

def _summary(results: dict) -> dict:
    return {
        "subdomains": len(results.get("recon", {}).get("subdomains", [])),
        "ports":      len(results.get("ports", {}).get("open_ports", [])),
        "cves":       results.get("cve", {}).get("total_cves", 0),
        "web":        results.get("web", {}).get("total", 0),
    }


def list_projects() -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT id, name, target, status, config, results, created_at "
            "FROM projects ORDER BY created_at DESC"
        ).fetchall()
    out = []
    for r in rows:
        cfg = json.loads(r["config"] or "{}")
        res = json.loads(r["results"] or "{}")
        out.append({
            "id":         r["id"],
            "name":       r["name"],
            "target":     r["target"],
            "status":     r["status"],
            "created_at": r["created_at"],
            "modules":    {k: cfg.get(k, False) for k in ("recon", "ports", "cve", "web", "full_scan")},
            "summary":    _summary(res),
        })
    return out


def dashboard_stats() -> dict:
    """Aggregate stats across all projects for the dashboard."""
    with _conn() as c:
        rows = c.execute(
            "SELECT config, results, created_at FROM projects ORDER BY created_at DESC"
        ).fetchall()

    totals = {"projects": len(rows), "ports": 0, "cves": 0, "subdomains": 0, "web": 0}
    severity = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "NONE": 0}
    module_usage = {"recon": 0, "ports": 0, "cve": 0, "web": 0}

    for r in rows:
        cfg = json.loads(r["config"] or "{}")
        res = json.loads(r["results"] or "{}")
        sm  = _summary(res)

        totals["ports"]      += sm["ports"]
        totals["cves"]       += sm["cves"]
        totals["subdomains"] += sm["subdomains"]
        totals["web"]        += sm["web"]

        for mod in ("recon", "ports", "cve", "web"):
            if cfg.get("full_scan") or cfg.get(mod):
                module_usage[mod] += 1

        for corr in res.get("cve", {}).get("correlations", []):
            sev = (corr.get("severity") or "NONE").upper()
            severity[sev] = severity.get(sev, 0) + 1

    return {"totals": totals, "severity": severity, "module_usage": module_usage}


def get_project(pid: str) -> dict | None:
    with _conn() as c:
        row = c.execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone()
    if not row:
        return None
    return {
        "id":         row["id"],
        "name":       row["name"],
        "target":     row["target"],
        "status":     row["status"],
        "config":     json.loads(row["config"]  or "{}"),
        "results":    json.loads(row["results"] or "{}"),
        "created_at": row["created_at"],
    }
