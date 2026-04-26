"""Queries for scheduled jobs."""
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any

from ..connection import get_conn


def save_scheduled_job(name: str, target: str, config: Dict[str, Any], schedule: str) -> str:
    """Create scheduled job."""
    job_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    with get_conn() as c:
        c.execute(
            """INSERT INTO scheduled_jobs 
               (id, name, target, config, schedule, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (job_id, name, target, json.dumps(config, default=str), schedule, "active", now, now)
        )
    return job_id


def get_scheduled_jobs() -> List[Dict[str, Any]]:
    """Get all scheduled jobs."""
    with get_conn() as c:
        rows = c.execute("SELECT * FROM scheduled_jobs WHERE status = 'active' ORDER BY created_at DESC").fetchall()
        return [dict(row) for row in rows]


def delete_scheduled_job(job_id: str) -> bool:
    """Delete scheduled job."""
    with get_conn() as c:
        c.execute("DELETE FROM scheduled_jobs WHERE id = ?", (job_id,))
    return True
