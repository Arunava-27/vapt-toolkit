"""Queries for false positive patterns."""
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any

from ..connection import get_conn


def save_fp_pattern(pattern: str, description: str = "", severity: str = "medium", category: str = "") -> str:
    """Save false positive pattern."""
    pattern_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    with get_conn() as c:
        c.execute(
            """INSERT INTO fp_patterns 
               (id, pattern, description, severity, category, enabled, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (pattern_id, pattern, description, severity, category, 1, now)
        )
    return pattern_id


def get_fp_patterns(enabled_only: bool = True) -> List[Dict[str, Any]]:
    """Get false positive patterns."""
    with get_conn() as c:
        if enabled_only:
            rows = c.execute("SELECT * FROM fp_patterns WHERE enabled = 1 ORDER BY created_at DESC").fetchall()
        else:
            rows = c.execute("SELECT * FROM fp_patterns ORDER BY created_at DESC").fetchall()
        return [dict(row) for row in rows]


def delete_fp_pattern(pattern_id: str) -> bool:
    """Delete false positive pattern."""
    with get_conn() as c:
        c.execute("DELETE FROM fp_patterns WHERE id = ?", (pattern_id,))
    return True
