"""Database connection management."""
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator, Any

DB_PATH = Path(__file__).parent.parent / "vapt.db"


@contextmanager
def get_conn() -> Generator[sqlite3.Connection, None, None]:
    """Get database connection context manager."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Initialize database with schema."""
    with get_conn() as c:
        # Check if old schema exists
        cursor = c.execute("PRAGMA table_info(projects)")
        columns = {row[1] for row in cursor.fetchall()}
        
        if "config" in columns:  # Old schema detected
            # Old schema migration code - for backward compatibility
            print("Migrating database to new schema...")
            old_rows = c.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()
            c.execute("DROP TABLE projects")
            
            # Create new schema
            _create_schema(c)
            
            # Import json for migration
            import json
            
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
            _create_schema(c)


def _create_schema(conn: sqlite3.Connection):
    """Create database schema."""
    conn.executescript("""
        -- Projects table
        CREATE TABLE IF NOT EXISTS projects (
            id          TEXT PRIMARY KEY,
            target      TEXT NOT NULL UNIQUE,
            name        TEXT NOT NULL,
            status      TEXT DEFAULT 'completed',
            scans       TEXT,
            created_at  TEXT,
            updated_at  TEXT
        );
        
        -- Bulk scan jobs
        CREATE TABLE IF NOT EXISTS bulk_jobs (
            id              TEXT PRIMARY KEY,
            name            TEXT NOT NULL,
            targets         TEXT NOT NULL,
            config          TEXT NOT NULL,
            status          TEXT DEFAULT 'pending',
            total_targets   INTEGER,
            completed_targets INTEGER DEFAULT 0,
            results         TEXT,
            created_at      TEXT,
            updated_at      TEXT
        );
        
        -- Scheduled jobs
        CREATE TABLE IF NOT EXISTS scheduled_jobs (
            id              TEXT PRIMARY KEY,
            name            TEXT NOT NULL,
            target          TEXT NOT NULL,
            config          TEXT NOT NULL,
            schedule        TEXT NOT NULL,
            last_run        TEXT,
            next_run        TEXT,
            status          TEXT DEFAULT 'active',
            created_at      TEXT,
            updated_at      TEXT
        );
        
        -- False positive patterns
        CREATE TABLE IF NOT EXISTS fp_patterns (
            id              TEXT PRIMARY KEY,
            pattern         TEXT NOT NULL,
            description     TEXT,
            severity        TEXT,
            category        TEXT,
            enabled         INTEGER DEFAULT 1,
            created_at      TEXT
        );
        
        -- Indices for performance
        CREATE INDEX IF NOT EXISTS idx_projects_target ON projects(target);
        CREATE INDEX IF NOT EXISTS idx_bulk_jobs_status ON bulk_jobs(status);
        CREATE INDEX IF NOT EXISTS idx_scheduled_jobs_status ON scheduled_jobs(status);
        CREATE INDEX IF NOT EXISTS idx_fp_patterns_enabled ON fp_patterns(enabled);
    """)
