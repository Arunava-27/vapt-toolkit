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
        # Check if old schema exists
        cursor = c.execute("PRAGMA table_info(projects)")
        columns = {row[1] for row in cursor.fetchall()}
        
        if "config" in columns:  # Old schema detected
            # Migrate old data to new format
            print("Migrating database to new schema...")
            old_rows = c.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()
            c.execute("DROP TABLE projects")
            
            # Create new schema
            c.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id          TEXT PRIMARY KEY,
                    target      TEXT NOT NULL UNIQUE,
                    name        TEXT NOT NULL,
                    status      TEXT DEFAULT 'completed',
                    scans       TEXT,
                    created_at  TEXT,
                    updated_at  TEXT
                )
            """)
            
            # Group scans by target (deduplicate, keep all scans for same target)
            target_scans = {}
            for row in old_rows:
                target = row["target"]
                if target not in target_scans:
                    target_scans[target] = {
                        "id": row["id"],
                        "name": row["name"],
                        "status": row["status"],
                        "created_at": row["created_at"],
                        "scans": []
                    }
                
                scan_record = {
                    "scan_id": row["id"],
                    "config": json.loads(row["config"] or "{}"),
                    "results": json.loads(row["results"] or "{}"),
                    "timestamp": row["created_at"],
                }
                target_scans[target]["scans"].append(scan_record)
            
            # Insert consolidated projects
            for target, data in target_scans.items():
                c.execute(
                    "INSERT INTO projects (id, target, name, status, scans, created_at, updated_at) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (data["id"], target, data["name"], data["status"],
                     json.dumps(data["scans"], default=str),
                     data["created_at"], data["created_at"])
                )
            print(f"Migration complete! Consolidated {len(old_rows)} scans into {len(target_scans)} projects")
        else:
            # New schema - just create if not exists
            c.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id          TEXT PRIMARY KEY,
                    target      TEXT NOT NULL UNIQUE,
                    name        TEXT NOT NULL,
                    status      TEXT DEFAULT 'completed',
                    scans       TEXT,
                    created_at  TEXT,
                    updated_at  TEXT
                )
            """)
        
        # Create api_keys table if not exists
        c.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id          TEXT PRIMARY KEY,
                project_id  TEXT NOT NULL,
                key_hash    TEXT NOT NULL UNIQUE,
                created_at  TEXT NOT NULL,
                last_used   TEXT,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            )
        """)
        
        # Create schedules table if not exists
        c.execute("""
            CREATE TABLE IF NOT EXISTS schedules (
                id          TEXT PRIMARY KEY,
                project_id  TEXT NOT NULL,
                frequency   TEXT NOT NULL,
                time        TEXT NOT NULL,
                day_of_week INTEGER,
                enabled     BOOLEAN DEFAULT 1,
                last_run    TEXT,
                next_run    TEXT,
                created_at  TEXT NOT NULL,
                updated_at  TEXT,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            )
        """)


# ── Write ─────────────────────────────────────────────────────────────────────

def save_project(name: str, target: str, config: dict, results: dict,
                 status: str = "completed") -> str:
    """Save or update a project. One project per target. Scans are stored as a list."""
    with _conn() as c:
        # Check if project already exists for this target
        existing = c.execute("SELECT id, scans FROM projects WHERE target=?", (target,)).fetchone()
        
        scan_record = {
            "scan_id": str(uuid.uuid4()),
            "scan_type": config.get("scan_classification", "active"),  # Track scan type
            "config": config,
            "results": results,
            "timestamp": datetime.now().isoformat(),
        }
        
        if existing:
            # Project exists - append new scan to history
            pid = existing["id"]
            scans = json.loads(existing["scans"] or "[]")
            scans.append(scan_record)
            c.execute(
                "UPDATE projects SET scans=?, status=?, updated_at=? WHERE id=?",
                (json.dumps(scans, default=str), status, datetime.now().isoformat(), pid)
            )
        else:
            # New project - create with first scan
            pid = str(uuid.uuid4())
            scans = [scan_record]
            c.execute(
                "INSERT INTO projects (id, target, name, status, scans, created_at, updated_at) "
                "VALUES (?,?,?,?,?,?,?)",
                (pid, target, name, status, json.dumps(scans, default=str),
                 datetime.now().isoformat(), datetime.now().isoformat())
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
    """Get summary from a single scan result."""
    return {
        "subdomains": len(results.get("recon", {}).get("subdomains", [])),
        "ports":      len(results.get("ports", {}).get("open_ports", [])),
        "cves":       results.get("cve", {}).get("total_cves", 0),
        "web":        results.get("web", {}).get("total", 0),
        "web_vulns":  results.get("web_vulnerabilities", {}).get("total_findings", 0),
    }


def list_projects() -> list[dict]:
    """List all projects with summary of latest scan."""
    with _conn() as c:
        rows = c.execute(
            "SELECT id, name, target, status, scans, created_at, updated_at "
            "FROM projects ORDER BY updated_at DESC"
        ).fetchall()
    out = []
    for r in rows:
        scans = json.loads(r["scans"] or "[]")
        latest_scan = scans[-1] if scans else {}
        res = latest_scan.get("results", {})
        out.append({
            "id":         r["id"],
            "name":       r["name"],
            "target":     r["target"],
            "status":     r["status"],
            "scan_count": len(scans),
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
            "modules":    {k: latest_scan.get("config", {}).get(k, False) for k in ("recon", "ports", "cve", "web", "web_vulnerability_scan", "full_scan")},
            "summary":    _summary(res),
        })
    return out


def dashboard_stats() -> dict:
    """Aggregate stats across all projects for the dashboard."""
    with _conn() as c:
        rows = c.execute(
            "SELECT scans FROM projects ORDER BY updated_at DESC"
        ).fetchall()

    totals = {"projects": len(rows), "ports": 0, "cves": 0, "subdomains": 0, "web": 0}
    severity = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "NONE": 0}
    module_usage = {"recon": 0, "ports": 0, "cve": 0, "web": 0}

    for r in rows:
        scans = json.loads(r["scans"] or "[]")
        latest_scan = scans[-1] if scans else {}
        cfg = latest_scan.get("config", {})
        res = latest_scan.get("results", {})
        sm = _summary(res)

        totals["ports"]      += sm["ports"]
        totals["cves"]       += sm["cves"]
        totals["subdomains"] += sm["subdomains"]
        totals["web"]        += sm["web"]

        for mod in ("recon", "ports", "cve", "web"):
            if cfg.get("full_scan") or cfg.get(mod):
                module_usage[mod] += 1

        # CVE severity distribution: iterate through each CVE within each correlation
        for corr in res.get("cve", {}).get("correlations", []):
            for cve in corr.get("cves", []):
                sev = (cve.get("severity") or "NONE").upper()
                # Normalize non-standard severity values to NONE
                if sev not in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "NONE"):
                    sev = "NONE"
                severity[sev] = severity.get(sev, 0) + 1

    return {"totals": totals, "severity": severity, "module_usage": module_usage}


def get_project(pid: str) -> dict | None:
    """Get project with scan history. Returns latest scan results by default."""
    with _conn() as c:
        row = c.execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone()
    if not row:
        return None
    
    scans = json.loads(row["scans"] or "[]")
    latest_scan = scans[-1] if scans else {}
    
    return {
        "id":         row["id"],
        "name":       row["name"],
        "target":     row["target"],
        "status":     row["status"],
        "config":     latest_scan.get("config", {}),
        "results":    latest_scan.get("results", {}),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "scan_count": len(scans),
        "scans":      scans,  # Full scan history available
    }

# ── Schedule Management ───────────────────────────────────────────────────────

def create_schedule(schedule_data: dict) -> str:
    """Create a new schedule."""
    with _conn() as c:
        c.execute(
            """INSERT INTO schedules (id, project_id, frequency, time, day_of_week, enabled, last_run, next_run, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (schedule_data["id"], schedule_data["project_id"], schedule_data["frequency"],
             schedule_data["time"], schedule_data.get("day_of_week"), schedule_data.get("enabled", True),
             schedule_data.get("last_run"), schedule_data["next_run"],
             schedule_data["created_at"], schedule_data.get("updated_at"))
        )
    return schedule_data["id"]


def list_schedules() -> list:
    """List all schedules."""
    with _conn() as c:
        rows = c.execute(
            "SELECT id, project_id, frequency, time, day_of_week, enabled, last_run, next_run, created_at, updated_at "
            "FROM schedules ORDER BY created_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def get_schedule(schedule_id: str) -> dict | None:
    """Get schedule by ID."""
    with _conn() as c:
        row = c.execute(
            "SELECT id, project_id, frequency, time, day_of_week, enabled, last_run, next_run, created_at, updated_at "
            "FROM schedules WHERE id=?", (schedule_id,)
        ).fetchone()
    return dict(row) if row else None


def update_schedule(schedule_id: str, updates: dict):
    """Update a schedule."""
    # Filter to only valid columns
    valid_columns = {"frequency", "time", "day_of_week", "enabled", "last_run", "next_run", "updated_at"}
    filtered = {k: v for k, v in updates.items() if k in valid_columns}
    
    if not filtered:
        return
    
    with _conn() as c:
        fields = ", ".join(f"{k}=?" for k in filtered.keys())
        values = list(filtered.values()) + [schedule_id]
        c.execute(f"UPDATE schedules SET {fields} WHERE id=?", values)


def update_schedule_run(schedule_id: str, last_run: str):
    """Update last_run for a schedule."""
    with _conn() as c:
        c.execute(
            "UPDATE schedules SET last_run=? WHERE id=?",
            (last_run, schedule_id)
        )


def delete_schedule(schedule_id: str):
    """Delete a schedule."""
    with _conn() as c:
        c.execute("DELETE FROM schedules WHERE id=?", (schedule_id,))
