"""Queries for bulk jobs."""
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any

from ..connection import get_conn


def save_bulk_job(name: str, targets: List[str], config: Dict[str, Any]) -> str:
    """Create new bulk job."""
    job_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    with get_conn() as c:
        c.execute(
            """INSERT INTO bulk_jobs 
               (id, name, targets, config, status, total_targets, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                job_id,
                name,
                json.dumps(targets),
                json.dumps(config, default=str),
                "pending",
                len(targets),
                now,
                now
            )
        )
    return job_id


def get_bulk_jobs() -> List[Dict[str, Any]]:
    """Get all bulk jobs."""
    with get_conn() as c:
        rows = c.execute("SELECT * FROM bulk_jobs ORDER BY created_at DESC").fetchall()
        return [dict(row) for row in rows]


def get_bulk_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Get bulk job by ID."""
    with get_conn() as c:
        row = c.execute("SELECT * FROM bulk_jobs WHERE id = ?", (job_id,)).fetchone()
        return dict(row) if row else None


def get_bulk_job_scans(job_id: str) -> List[Dict[str, Any]]:
    """Get scan results from bulk job."""
    job = get_bulk_job(job_id)
    if not job:
        return []
    
    return json.loads(job.get("results") or "[]")


def update_bulk_job_status(job_id: str, status: str) -> bool:
    """Update bulk job status."""
    now = datetime.utcnow().isoformat()
    
    with get_conn() as c:
        c.execute(
            "UPDATE bulk_jobs SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, job_id)
        )
    return True


def update_bulk_job_results(job_id: str, results: List[Dict[str, Any]], completed_count: int) -> bool:
    """Update bulk job results."""
    now = datetime.utcnow().isoformat()
    
    with get_conn() as c:
        c.execute(
            "UPDATE bulk_jobs SET results = ?, completed_targets = ?, updated_at = ? WHERE id = ?",
            (json.dumps(results, default=str), completed_count, now, job_id)
        )
    return True
