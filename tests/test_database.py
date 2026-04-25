"""
Comprehensive unit tests for database.py - Data persistence and CRUD operations.
"""
import pytest
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, call
import sys
import tempfile
import os

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import database as db
except ImportError:
    pytest.skip("database module not available", allow_module_level=True)


@pytest.fixture
def test_db():
    """Create a test database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    # Initialize the database
    old_db_path = getattr(db, 'DB_PATH', None)
    db.DB_PATH = db_path
    
    try:
        db.init_db()
        yield db_path
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)
        if old_db_path:
            db.DB_PATH = old_db_path


class TestDatabaseInitialization:
    """Test database initialization and schema creation."""
    
    def test_init_db_creates_tables(self, test_db):
        """Test that init_db creates all required tables."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        
        required_tables = {
            'projects', 'api_keys', 'schedules', 'fp_patterns',
            'webhooks', 'webhook_logs', 'bulk_jobs', 'bulk_job_targets'
        }
        
        assert required_tables.issubset(tables), f"Missing tables: {required_tables - tables}"
        conn.close()
    
    def test_init_db_schema_columns(self, test_db):
        """Test that tables have correct columns."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        # Check projects table columns
        cursor.execute("PRAGMA table_info(projects)")
        columns = {row[1] for row in cursor.fetchall()}
        
        expected = {'id', 'target', 'name', 'status', 'scans', 'created_at', 'updated_at'}
        assert expected.issubset(columns), f"Missing columns in projects: {expected - columns}"
        
        conn.close()


class TestProjectOperations:
    """Test CRUD operations for projects."""
    
    def test_save_project_creates_new(self, test_db, sample_project):
        """Test creating a new project."""
        result = db.save_project(sample_project)
        assert result is not None
        
        # Verify project can be retrieved
        retrieved = db.get_project(sample_project["id"])
        assert retrieved is not None
        assert retrieved["target"] == sample_project["target"]
    
    def test_save_project_updates_existing(self, test_db, sample_project):
        """Test updating an existing project."""
        db.save_project(sample_project)
        
        sample_project["name"] = "Updated Name"
        db.save_project(sample_project)
        
        retrieved = db.get_project(sample_project["id"])
        assert retrieved["name"] == "Updated Name"
    
    def test_get_project_returns_none_for_missing(self, test_db):
        """Test that get_project returns None for non-existent project."""
        result = db.get_project("nonexistent_id")
        assert result is None
    
    def test_list_projects_returns_all(self, test_db, sample_project):
        """Test listing all projects."""
        db.save_project(sample_project)
        
        projects = db.list_projects()
        assert len(projects) > 0
        assert any(p["id"] == sample_project["id"] for p in projects)
    
    def test_rename_project(self, test_db, sample_project):
        """Test renaming a project."""
        db.save_project(sample_project)
        new_name = "Renamed Project"
        
        db.rename_project(sample_project["id"], new_name)
        
        retrieved = db.get_project(sample_project["id"])
        assert retrieved["name"] == new_name
    
    def test_delete_project(self, test_db, sample_project):
        """Test deleting a project."""
        db.save_project(sample_project)
        db.delete_project(sample_project["id"])
        
        result = db.get_project(sample_project["id"])
        assert result is None


class TestAPIKeyOperations:
    """Test CRUD operations for API keys."""
    
    def test_create_api_key(self, test_db, sample_project, sample_api_key):
        """Test creating an API key."""
        db.save_project(sample_project)
        
        result = db.create_api_key(
            sample_project["id"],
            sample_api_key["key_hash"]
        )
        
        assert result is not None
        assert "id" in result
    
    def test_list_api_keys(self, test_db, sample_project, sample_api_key):
        """Test listing API keys for a project."""
        db.save_project(sample_project)
        db.create_api_key(sample_project["id"], sample_api_key["key_hash"])
        
        keys = db.list_api_keys(sample_project["id"])
        assert len(keys) > 0
    
    def test_update_key_last_used(self, test_db, sample_project, sample_api_key):
        """Test updating last_used timestamp for API key."""
        db.save_project(sample_project)
        key = db.create_api_key(sample_project["id"], sample_api_key["key_hash"])
        
        new_time = datetime.now()
        db.update_key_last_used(key["id"], new_time)
        
        # Verify update was recorded
        keys = db.list_api_keys(sample_project["id"])
        assert len(keys) > 0


class TestScheduleOperations:
    """Test CRUD operations for schedules."""
    
    def test_create_schedule(self, test_db, sample_project, sample_schedule):
        """Test creating a schedule."""
        db.save_project(sample_project)
        
        result = db.create_schedule(
            sample_project["id"],
            sample_schedule["frequency"],
            sample_schedule["time"]
        )
        
        assert result is not None
        assert result["frequency"] == sample_schedule["frequency"]
    
    def test_get_schedule(self, test_db, sample_project, sample_schedule):
        """Test retrieving a schedule."""
        db.save_project(sample_project)
        created = db.create_schedule(
            sample_project["id"],
            sample_schedule["frequency"],
            sample_schedule["time"]
        )
        
        retrieved = db.get_schedule(created["id"])
        assert retrieved is not None
        assert retrieved["frequency"] == sample_schedule["frequency"]
    
    def test_update_schedule(self, test_db, sample_project, sample_schedule):
        """Test updating a schedule."""
        db.save_project(sample_project)
        schedule = db.create_schedule(
            sample_project["id"],
            sample_schedule["frequency"],
            sample_schedule["time"]
        )
        
        db.update_schedule(schedule["id"], "weekly", "03:00")
        
        updated = db.get_schedule(schedule["id"])
        assert updated["frequency"] == "weekly"
        assert updated["time"] == "03:00"
    
    def test_delete_schedule(self, test_db, sample_project, sample_schedule):
        """Test deleting a schedule."""
        db.save_project(sample_project)
        schedule = db.create_schedule(
            sample_project["id"],
            sample_schedule["frequency"],
            sample_schedule["time"]
        )
        
        db.delete_schedule(schedule["id"])
        
        result = db.get_schedule(schedule["id"])
        assert result is None


class TestWebhookOperations:
    """Test CRUD operations for webhooks."""
    
    def test_create_webhook(self, test_db, sample_project, sample_webhook):
        """Test creating a webhook."""
        db.save_project(sample_project)
        
        result = db.create_webhook(
            sample_project["id"],
            sample_webhook["url"],
            sample_webhook["events"],
            sample_webhook["secret_hash"]
        )
        
        assert result is not None
        assert result["url"] == sample_webhook["url"]
    
    def test_get_webhooks_by_project(self, test_db, sample_project, sample_webhook):
        """Test retrieving webhooks for a project."""
        db.save_project(sample_project)
        db.create_webhook(
            sample_project["id"],
            sample_webhook["url"],
            sample_webhook["events"],
            sample_webhook["secret_hash"]
        )
        
        webhooks = db.get_webhooks(sample_project["id"])
        assert len(webhooks) > 0
        assert webhooks[0]["url"] == sample_webhook["url"]
    
    def test_enable_disable_webhook(self, test_db, sample_project, sample_webhook):
        """Test enabling/disabling webhooks."""
        db.save_project(sample_project)
        webhook = db.create_webhook(
            sample_project["id"],
            sample_webhook["url"],
            sample_webhook["events"],
            sample_webhook["secret_hash"]
        )
        
        # Disable
        db.disable_webhook(webhook["id"])
        disabled = db.get_webhooks(sample_project["id"])[0]
        assert not disabled["enabled"]
        
        # Enable
        db.enable_webhook(webhook["id"])
        enabled = db.get_webhooks(sample_project["id"])[0]
        assert enabled["enabled"]
    
    def test_delete_webhook(self, test_db, sample_project, sample_webhook):
        """Test deleting a webhook."""
        db.save_project(sample_project)
        webhook = db.create_webhook(
            sample_project["id"],
            sample_webhook["url"],
            sample_webhook["events"],
            sample_webhook["secret_hash"]
        )
        
        db.delete_webhook(webhook["id"])
        
        webhooks = db.get_webhooks(sample_project["id"])
        assert len(webhooks) == 0


class TestFalsePositivePatterns:
    """Test false positive pattern operations."""
    
    def test_save_fp_pattern(self, test_db, sample_project, sample_fp_pattern):
        """Test saving a false positive pattern."""
        db.save_project(sample_project)
        
        result = db.save_fp_pattern(
            sample_project["id"],
            sample_fp_pattern["pattern_type"],
            sample_fp_pattern["description"],
            sample_fp_pattern["regex_pattern"]
        )
        
        assert result is not None
    
    def test_get_fp_patterns(self, test_db, sample_project, sample_fp_pattern):
        """Test retrieving false positive patterns."""
        db.save_project(sample_project)
        db.save_fp_pattern(
            sample_project["id"],
            sample_fp_pattern["pattern_type"],
            sample_fp_pattern["description"],
            sample_fp_pattern["regex_pattern"]
        )
        
        patterns = db.get_fp_patterns(sample_project["id"])
        assert len(patterns) > 0
    
    def test_update_fp_pattern_status(self, test_db, sample_project, sample_fp_pattern):
        """Test updating FP pattern enabled status."""
        db.save_project(sample_project)
        pattern = db.save_fp_pattern(
            sample_project["id"],
            sample_fp_pattern["pattern_type"],
            sample_fp_pattern["description"],
            sample_fp_pattern["regex_pattern"]
        )
        
        db.update_fp_pattern_status(pattern["id"], False)
        
        updated = db.get_fp_patterns(sample_project["id"])[0]
        assert not updated["enabled"]


class TestBulkJobOperations:
    """Test bulk job CRUD operations."""
    
    def test_create_bulk_job(self, test_db, sample_project, sample_bulk_job):
        """Test creating a bulk job."""
        db.save_project(sample_project)
        
        result = db.create_bulk_job(
            sample_project["id"],
            sample_bulk_job["config"]
        )
        
        assert result is not None
        assert result["status"] == "pending"
    
    def test_get_bulk_job(self, test_db, sample_project, sample_bulk_job):
        """Test retrieving a bulk job."""
        db.save_project(sample_project)
        job = db.create_bulk_job(sample_project["id"], sample_bulk_job["config"])
        
        retrieved = db.get_bulk_job(job["id"])
        assert retrieved is not None
        assert retrieved["id"] == job["id"]
    
    def test_update_bulk_job_status(self, test_db, sample_project, sample_bulk_job):
        """Test updating bulk job status."""
        db.save_project(sample_project)
        job = db.create_bulk_job(sample_project["id"], sample_bulk_job["config"])
        
        db.update_bulk_job_status(job["id"], "in_progress")
        
        updated = db.get_bulk_job(job["id"])
        assert updated["status"] == "in_progress"
    
    def test_add_bulk_job_target(self, test_db, sample_project, sample_bulk_job):
        """Test adding a target to a bulk job."""
        db.save_project(sample_project)
        job = db.create_bulk_job(sample_project["id"], sample_bulk_job["config"])
        
        result = db.add_bulk_job_target(job["id"], "https://example.com")
        
        assert result is not None


class TestDashboardStats:
    """Test dashboard statistics aggregation."""
    
    def test_dashboard_stats_empty_db(self, test_db):
        """Test dashboard stats with empty database."""
        stats = db.dashboard_stats()
        
        assert stats["total_projects"] == 0
        assert stats["total_scans"] == 0
    
    def test_dashboard_stats_with_projects(self, test_db, sample_project):
        """Test dashboard stats with projects."""
        db.save_project(sample_project)
        
        stats = db.dashboard_stats()
        
        assert stats["total_projects"] >= 1


class TestDatabaseConnectionHandling:
    """Test database connection and error handling."""
    
    def test_db_connection_context_manager(self, test_db):
        """Test that _conn() properly manages database connections."""
        with db._conn(test_db) as conn:
            assert conn is not None
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            assert cursor.fetchone() is not None
    
    def test_db_connection_closes_on_error(self, test_db):
        """Test that connections close properly even on error."""
        try:
            with db._conn(test_db) as conn:
                raise Exception("Test error")
        except Exception:
            pass
        
        # Connection should be closed, verify we can open a new one
        with db._conn(test_db) as conn:
            assert conn is not None
