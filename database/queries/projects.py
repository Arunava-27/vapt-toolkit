"""Queries for projects table."""
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any

from ..connection import get_conn


def save_project(target: str, name: str, scans: Optional[List[Dict]] = None) -> str:
    """Save or update project."""
    project_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    with get_conn() as c:
        c.execute(
            """INSERT INTO projects (id, target, name, status, scans, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                project_id,
                target,
                name,
                "completed",
                json.dumps(scans or [], default=str),
                now,
                now
            )
        )
    return project_id


def get_projects() -> List[Dict[str, Any]]:
    """Get all projects."""
    with get_conn() as c:
        rows = c.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()
        return [dict(row) for row in rows]


def get_project(project_id: str) -> Optional[Dict[str, Any]]:
    """Get project by ID."""
    with get_conn() as c:
        row = c.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        return dict(row) if row else None


def delete_project(project_id: str) -> bool:
    """Delete project."""
    with get_conn() as c:
        c.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    return True


def update_project(project_id: str, **kwargs) -> bool:
    """Update project fields."""
    now = datetime.utcnow().isoformat()
    
    with get_conn() as c:
        # Build update statement dynamically
        allowed_fields = {"name", "status"}
        fields_to_update = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not fields_to_update:
            return False
        
        fields_to_update["updated_at"] = now
        
        set_clause = ", ".join([f"{k} = ?" for k in fields_to_update.keys()])
        values = list(fields_to_update.values()) + [project_id]
        
        c.execute(
            f"UPDATE projects SET {set_clause} WHERE id = ?",
            values
        )
    return True


def add_scan_to_project(project_id: str, scan_data: Dict[str, Any]) -> bool:
    """Add scan result to project."""
    project = get_project(project_id)
    if not project:
        return False
    
    scans = json.loads(project.get("scans") or "[]")
    scans.append(scan_data)
    
    now = datetime.utcnow().isoformat()
    
    with get_conn() as c:
        c.execute(
            "UPDATE projects SET scans = ?, updated_at = ? WHERE id = ?",
            (json.dumps(scans, default=str), now, project_id)
        )
    return True


def get_project_scans(project_id: str) -> List[Dict[str, Any]]:
    """Get all scans for a project."""
    project = get_project(project_id)
    if not project:
        return []
    
    return json.loads(project.get("scans") or "[]")
