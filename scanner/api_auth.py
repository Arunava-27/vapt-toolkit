"""API key authentication and rate limiting for VAPT Toolkit."""

import hashlib
import secrets
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple

DB_PATH = Path(__file__).parent.parent / "vapt.db"

# Rate limiting: requests per minute per API key
RATE_LIMIT_PER_MINUTE = 100
CLEANUP_INTERVAL = 300  # Cleanup old rate limit records every 5 minutes

# In-memory rate limit tracking (cleared on startup)
_request_tracking = {}


def _get_db():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _hash_api_key(api_key: str) -> str:
    """Hash API key using SHA256."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def generate_api_key(project_id: str) -> Tuple[str, str]:
    """
    Generate a new API key for a project.
    Returns: (plain_key, key_hash)
    """
    plain_key = f"vapt_{secrets.token_urlsafe(32)}"
    key_hash = _hash_api_key(plain_key)
    
    conn = _get_db()
    try:
        conn.execute(
            """
            INSERT INTO api_keys (id, project_id, key_hash, created_at, last_used)
            VALUES (?, ?, ?, ?, NULL)
            """,
            (secrets.token_hex(16), project_id, key_hash, datetime.now().isoformat())
        )
        conn.commit()
    finally:
        conn.close()
    
    return plain_key, key_hash


def validate_api_key(api_key: str) -> Optional[str]:
    """
    Validate API key and return project_id if valid.
    Updates last_used timestamp on successful validation.
    Returns: project_id or None if invalid
    """
    key_hash = _hash_api_key(api_key)
    
    conn = _get_db()
    try:
        row = conn.execute(
            "SELECT project_id FROM api_keys WHERE key_hash = ?",
            (key_hash,)
        ).fetchone()
        
        if row:
            # Update last_used timestamp
            conn.execute(
                "UPDATE api_keys SET last_used = ? WHERE key_hash = ?",
                (datetime.now().isoformat(), key_hash)
            )
            conn.commit()
            return row["project_id"]
        return None
    finally:
        conn.close()


def check_rate_limit(api_key: str) -> bool:
    """
    Check if API key has exceeded rate limit.
    Returns: True if within limit, False if exceeded
    """
    now = time.time()
    minute_ago = now - 60
    
    key_hash = _hash_api_key(api_key)
    
    # Cleanup old tracking entries periodically
    if now % CLEANUP_INTERVAL < 1:  # Run cleanup every ~5 minutes
        _request_tracking.clear()
    
    if key_hash not in _request_tracking:
        _request_tracking[key_hash] = []
    
    # Remove requests older than 1 minute
    _request_tracking[key_hash] = [
        req_time for req_time in _request_tracking[key_hash]
        if req_time > minute_ago
    ]
    
    # Check if limit exceeded
    if len(_request_tracking[key_hash]) >= RATE_LIMIT_PER_MINUTE:
        return False
    
    # Record this request
    _request_tracking[key_hash].append(now)
    return True


def get_rate_limit_info(api_key: str) -> dict:
    """Get current rate limit info for API key."""
    now = time.time()
    minute_ago = now - 60
    
    key_hash = _hash_api_key(api_key)
    
    if key_hash in _request_tracking:
        recent_requests = [
            req_time for req_time in _request_tracking[key_hash]
            if req_time > minute_ago
        ]
    else:
        recent_requests = []
    
    return {
        "requests_used": len(recent_requests),
        "requests_limit": RATE_LIMIT_PER_MINUTE,
        "requests_remaining": RATE_LIMIT_PER_MINUTE - len(recent_requests),
        "reset_at": datetime.fromtimestamp(minute_ago + 60).isoformat(),
    }


def list_api_keys(project_id: str) -> list[dict]:
    """List all API keys for a project (masked)."""
    conn = _get_db()
    try:
        rows = conn.execute(
            """
            SELECT id, created_at, last_used
            FROM api_keys
            WHERE project_id = ?
            ORDER BY created_at DESC
            """,
            (project_id,)
        ).fetchall()
        
        return [
            {
                "id": r["id"],
                "created_at": r["created_at"],
                "last_used": r["last_used"],
            }
            for r in rows
        ]
    finally:
        conn.close()


def revoke_api_key(key_id: str) -> bool:
    """Revoke an API key by ID."""
    conn = _get_db()
    try:
        conn.execute("DELETE FROM api_keys WHERE id = ?", (key_id,))
        conn.commit()
        return True
    finally:
        conn.close()
