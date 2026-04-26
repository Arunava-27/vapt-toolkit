"""Database module - SQLite persistence for VAPT scans."""
import sys
import importlib.util
from pathlib import Path

# Import from the database package
from .connection import init_db, get_conn
from .queries import (
    save_project,
    get_projects,
    get_project,
    delete_project,
    update_project,
    add_scan_to_project,
    get_project_scans,
    save_bulk_job,
    get_bulk_jobs,
    get_bulk_job,
    get_bulk_job_scans,
    update_bulk_job_status,
    update_bulk_job_results,
    save_scheduled_job,
    get_scheduled_jobs,
    delete_scheduled_job,
    save_fp_pattern,
    get_fp_patterns,
    delete_fp_pattern,
)

# Also import functions from the root database.py file if available
# This provides backward compatibility
try:
    root_db_path = Path(__file__).parent.parent / "database.py"
    if root_db_path.exists():
        spec = importlib.util.spec_from_file_location("_root_database", root_db_path)
        root_db = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(root_db)
        
        # Import all the functions that are only available in root database.py
        list_projects = getattr(root_db, 'list_projects', None)
        rename_project = getattr(root_db, 'rename_project', None)
        dashboard_stats = getattr(root_db, 'dashboard_stats', None)
        list_schedules = getattr(root_db, 'list_schedules', None)
        get_schedule = getattr(root_db, 'get_schedule', None)
        create_schedule = getattr(root_db, 'create_schedule', None)
        update_schedule = getattr(root_db, 'update_schedule', None)
        delete_schedule = getattr(root_db, 'delete_schedule', None)
        create_bulk_job = getattr(root_db, 'create_bulk_job', None)
        get_bulk_job_targets = getattr(root_db, 'get_bulk_job_targets', None)
        update_bulk_job_timing = getattr(root_db, 'update_bulk_job_timing', None)
        update_target_status = getattr(root_db, 'update_target_status', None)
        list_bulk_jobs = getattr(root_db, 'list_bulk_jobs', None)
        cancel_bulk_job = getattr(root_db, 'cancel_bulk_job', None)
        update_fp_pattern_status = getattr(root_db, 'update_fp_pattern_status', None)
except Exception:
    # If we can't import from root database.py, that's OK
    # These functions might not be needed
    pass

__all__ = [
    "init_db",
    "get_conn",
    "save_project",
    "get_projects",
    "get_project",
    "delete_project",
    "update_project",
    "add_scan_to_project",
    "get_project_scans",
    "save_bulk_job",
    "get_bulk_jobs",
    "get_bulk_job",
    "get_bulk_job_scans",
    "update_bulk_job_status",
    "update_bulk_job_results",
    "save_scheduled_job",
    "get_scheduled_jobs",
    "delete_scheduled_job",
    "save_fp_pattern",
    "get_fp_patterns",
    "delete_fp_pattern",
    "list_projects",
    "rename_project",
    "dashboard_stats",
    "list_schedules",
    "get_schedule",
    "create_schedule",
    "update_schedule",
    "delete_schedule",
    "create_bulk_job",
    "get_bulk_job_targets",
    "update_bulk_job_timing",
    "update_target_status",
    "list_bulk_jobs",
    "cancel_bulk_job",
    "update_fp_pattern_status",
]
