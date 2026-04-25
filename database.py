"""SQLite persistence for VAPT scan projects."""
import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
from typing import Optional

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

        # Create fp_patterns table for false positive pattern database
        c.execute("""
            CREATE TABLE IF NOT EXISTS fp_patterns (
                id              TEXT PRIMARY KEY,
                project_id      TEXT,
                pattern_type    TEXT NOT NULL,
                description     TEXT NOT NULL,
                regex_pattern   TEXT NOT NULL,
                severity_impact REAL NOT NULL DEFAULT 0.6,
                enabled         BOOLEAN DEFAULT 1,
                keywords        TEXT,
                safe_framework  TEXT,
                created_at      TEXT NOT NULL,
                updated_at      TEXT,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            )
        """)
        
        # Create webhooks table if not exists
        c.execute("""
            CREATE TABLE IF NOT EXISTS webhooks (
                id              TEXT PRIMARY KEY,
                project_id      TEXT NOT NULL,
                url             TEXT NOT NULL,
                events          TEXT NOT NULL,
                secret_hash     TEXT NOT NULL,
                enabled         BOOLEAN DEFAULT 1,
                created_at      TEXT NOT NULL,
                last_triggered  TEXT,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            )
        """)
        
        # Create webhook_logs table if not exists
        c.execute("""
            CREATE TABLE IF NOT EXISTS webhook_logs (
                id          TEXT PRIMARY KEY,
                webhook_id  TEXT NOT NULL,
                event       TEXT NOT NULL,
                payload     TEXT NOT NULL,
                status      TEXT,
                response    TEXT,
                attempts    INTEGER DEFAULT 1,
                created_at  TEXT NOT NULL,
                FOREIGN KEY(webhook_id) REFERENCES webhooks(id)
            )
        """)
        
        # Create bulk_jobs table for parallel scanning
        c.execute("""
            CREATE TABLE IF NOT EXISTS bulk_jobs (
                id              TEXT PRIMARY KEY,
                project_id      TEXT NOT NULL,
                status          TEXT DEFAULT 'pending',
                progress        INTEGER DEFAULT 0,
                total_targets   INTEGER NOT NULL,
                completed_count INTEGER DEFAULT 0,
                failed_count    INTEGER DEFAULT 0,
                created_at      TEXT NOT NULL,
                started_at      TEXT,
                completed_at    TEXT,
                config          TEXT,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            )
        """)
        
        # Create bulk_job_targets table for individual target status
        c.execute("""
            CREATE TABLE IF NOT EXISTS bulk_job_targets (
                id          TEXT PRIMARY KEY,
                job_id      TEXT NOT NULL,
                target_url  TEXT NOT NULL,
                status      TEXT DEFAULT 'pending',
                result      TEXT,
                error       TEXT,
                started_at  TEXT,
                completed_at TEXT,
                FOREIGN KEY(job_id) REFERENCES bulk_jobs(id)
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


# ── Bulk Job Management ───────────────────────────────────────────────────

def create_bulk_job(project_id: str, targets: list, config: dict) -> str:
    """Create a new bulk scanning job."""
    job_id = str(uuid.uuid4())
    with _conn() as c:
        c.execute(
            """INSERT INTO bulk_jobs (id, project_id, status, total_targets, config, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (job_id, project_id, "pending", len(targets), json.dumps(config, default=str),
             datetime.now().isoformat())
        )
        
        # Add individual targets
        for target in targets:
            target_id = str(uuid.uuid4())
            c.execute(
                """INSERT INTO bulk_job_targets (id, job_id, target_url, status)
                   VALUES (?, ?, ?, ?)""",
                (target_id, job_id, target, "pending")
            )
    
    return job_id


def get_bulk_job(job_id: str) -> dict | None:
    """Get bulk job details."""
    with _conn() as c:
        row = c.execute(
            """SELECT id, project_id, status, progress, total_targets, completed_count, failed_count,
                      created_at, started_at, completed_at, config
               FROM bulk_jobs WHERE id=?""",
            (job_id,)
        ).fetchone()
    
    if not row:
        return None
    
    return dict(row)


def get_bulk_job_targets(job_id: str, limit: int = 100, offset: int = 0) -> list[dict]:
    """Get targets for a bulk job."""
    with _conn() as c:
        rows = c.execute(
            """SELECT id, job_id, target_url, status, result, error, started_at, completed_at
               FROM bulk_job_targets WHERE job_id=?
               ORDER BY created_at LIMIT ? OFFSET ?""",
            (job_id, limit, offset)
        ).fetchall()
    
    return [dict(row) for row in rows]


def update_bulk_job_status(job_id: str, status: str, progress: int = None):
    """Update bulk job status."""
    with _conn() as c:
        if progress is not None:
            c.execute(
                "UPDATE bulk_jobs SET status=?, progress=? WHERE id=?",
                (status, progress, job_id)
            )
        else:
            c.execute(
                "UPDATE bulk_jobs SET status=? WHERE id=?",
                (status, job_id)
            )


def update_bulk_job_timing(job_id: str, started_at: str = None, completed_at: str = None):
    """Update job timing fields."""
    with _conn() as c:
        if started_at:
            c.execute("UPDATE bulk_jobs SET started_at=? WHERE id=?", (started_at, job_id))
        if completed_at:
            c.execute("UPDATE bulk_jobs SET completed_at=? WHERE id=?", (completed_at, job_id))


def update_bulk_job_counters(job_id: str, completed: int = 0, failed: int = 0):
    """Increment bulk job counters."""
    with _conn() as c:
        current = c.execute(
            "SELECT completed_count, failed_count FROM bulk_jobs WHERE id=?",
            (job_id,)
        ).fetchone()
        
        if current:
            new_completed = current[0] + completed
            new_failed = current[1] + failed
            total = c.execute(
                "SELECT total_targets FROM bulk_jobs WHERE id=?",
                (job_id,)
            ).fetchone()[0]
            
            progress = int((new_completed / total) * 100) if total > 0 else 0
            
            c.execute(
                "UPDATE bulk_jobs SET completed_count=?, failed_count=?, progress=? WHERE id=?",
                (new_completed, new_failed, progress, job_id)
            )


def update_target_status(target_id: str, status: str, result: str = None, error: str = None,
                        started_at: str = None, completed_at: str = None):
    """Update individual target status in a bulk job."""
    with _conn() as c:
        c.execute(
            """UPDATE bulk_job_targets 
               SET status=?, result=?, error=?, started_at=?, completed_at=?
               WHERE id=?""",
            (status, result, error, started_at, completed_at, target_id)
        )


def list_bulk_jobs(project_id: str = None, limit: int = 50) -> list[dict]:
    """List bulk jobs, optionally filtered by project."""
    with _conn() as c:
        if project_id:
            rows = c.execute(
                """SELECT id, project_id, status, progress, total_targets, completed_count, failed_count,
                          created_at, started_at, completed_at
                   FROM bulk_jobs WHERE project_id=?
                   ORDER BY created_at DESC LIMIT ?""",
                (project_id, limit)
            ).fetchall()
        else:
            rows = c.execute(
                """SELECT id, project_id, status, progress, total_targets, completed_count, failed_count,
                          created_at, started_at, completed_at
                   FROM bulk_jobs
                   ORDER BY created_at DESC LIMIT ?""",
                (limit,)
            ).fetchall()
    
    return [dict(row) for row in rows]


def cancel_bulk_job(job_id: str):
    """Cancel a bulk job."""
    with _conn() as c:
        c.execute(
            "UPDATE bulk_jobs SET status=? WHERE id=?",
            ("cancelled", job_id)
        )


# ── False Positive Pattern Management ──────────────────────────────────────

def save_fp_pattern(pattern_dict: dict, project_id: Optional[str] = None) -> str:
    """Save a custom false positive pattern"""
    import uuid
    pattern_id = pattern_dict.get("id", f"fp_{uuid.uuid4().hex[:8]}")
    
    with _conn() as c:
        c.execute(
            """INSERT OR REPLACE INTO fp_patterns 
               (id, project_id, pattern_type, description, regex_pattern, severity_impact, enabled, keywords, safe_framework, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                pattern_id,
                project_id,
                pattern_dict["pattern_type"],
                pattern_dict["description"],
                pattern_dict["regex_pattern"],
                float(pattern_dict.get("severity_impact", 0.6)),
                pattern_dict.get("enabled", True),
                json.dumps(pattern_dict.get("keywords", [])),
                pattern_dict.get("safe_framework"),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            )
        )
    return pattern_id


def get_fp_patterns(project_id: Optional[str] = None, enabled_only: bool = True) -> list[dict]:
    """Get false positive patterns, optionally for specific project"""
    with _conn() as c:
        query = "SELECT * FROM fp_patterns WHERE (project_id IS NULL OR project_id = ?)"
        params = [project_id]
        
        if enabled_only:
            query += " AND enabled = 1"
        
        query += " ORDER BY pattern_type, created_at DESC"
        
        rows = c.execute(query, params).fetchall()
    
    result = []
    for r in rows:
        result.append({
            "id": r["id"],
            "project_id": r["project_id"],
            "pattern_type": r["pattern_type"],
            "description": r["description"],
            "regex_pattern": r["regex_pattern"],
            "severity_impact": r["severity_impact"],
            "enabled": bool(r["enabled"]),
            "keywords": json.loads(r["keywords"] or "[]"),
            "safe_framework": r["safe_framework"],
            "created_at": r["created_at"],
        })
    return result


def update_fp_pattern_status(pattern_id: str, enabled: bool) -> bool:
    """Enable or disable a pattern"""
    with _conn() as c:
        c.execute(
            "UPDATE fp_patterns SET enabled = ?, updated_at = ? WHERE id = ?",
            (enabled, datetime.now().isoformat(), pattern_id)
        )
        return c.total_changes > 0


def delete_fp_pattern(pattern_id: str) -> bool:
    """Delete a custom false positive pattern"""
    with _conn() as c:
        c.execute("DELETE FROM fp_patterns WHERE id = ?", (pattern_id,))
        return c.total_changes > 0
