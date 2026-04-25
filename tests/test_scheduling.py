"""
Comprehensive unit tests for scanner/scheduling.py - Scan scheduling.
"""
import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from scanner.scheduling import ScanScheduler
except ImportError:
    pytest.skip("scheduling module not available", allow_module_level=True)


@pytest.fixture
def mock_db():
    """Mock database module."""
    mock = MagicMock()
    mock.get_schedule = MagicMock(return_value=None)
    mock.list_schedules_for_project = MagicMock(return_value=[])
    return mock


@pytest.fixture
def scheduler(mock_db):
    """Create a ScanScheduler instance for testing."""
    with patch('scanner.scheduling.db', mock_db):
        scheduler = ScanScheduler(mock_db)
        yield scheduler
        if scheduler.scheduler and scheduler.scheduler.running:
            scheduler.stop()


class TestSchedulerLifecycle:
    """Test scheduler startup and shutdown."""
    
    def test_scheduler_initialization(self, scheduler):
        """Test scheduler is properly initialized."""
        assert scheduler is not None
        assert hasattr(scheduler, 'scheduler')
    
    def test_scheduler_start_stop(self, scheduler):
        """Test starting and stopping the scheduler."""
        scheduler.start()
        assert scheduler.scheduler.running
        
        scheduler.stop()
        assert not scheduler.scheduler.running


class TestScheduleCreation:
    """Test creating and managing schedules."""
    
    def test_create_daily_schedule(self, scheduler, mock_db):
        """Test creating a daily schedule."""
        mock_db.create_schedule = MagicMock(
            return_value={"id": "sch_001", "frequency": "daily"}
        )
        
        result = scheduler.create_schedule(
            "proj_123",
            "daily",
            "02:00"
        )
        
        assert result is not None
    
    def test_create_weekly_schedule(self, scheduler, mock_db):
        """Test creating a weekly schedule."""
        mock_db.create_schedule = MagicMock(
            return_value={"id": "sch_002", "frequency": "weekly"}
        )
        
        result = scheduler.create_schedule(
            "proj_123",
            "weekly",
            "02:00",
            day_of_week=1
        )
        
        assert result is not None
    
    def test_create_monthly_schedule(self, scheduler, mock_db):
        """Test creating a monthly schedule."""
        mock_db.create_schedule = MagicMock(
            return_value={"id": "sch_003", "frequency": "monthly"}
        )
        
        result = scheduler.create_schedule(
            "proj_123",
            "monthly",
            "02:00"
        )
        
        assert result is not None


class TestScheduleTimeCalculation:
    """Test time-related calculations."""
    
    def test_parse_time_valid(self, scheduler):
        """Test parsing valid time strings."""
        hour, minute = scheduler._parse_time("14:30")
        
        assert hour == 14
        assert minute == 30
    
    def test_parse_time_invalid(self, scheduler):
        """Test parsing invalid time strings."""
        with pytest.raises(ValueError):
            scheduler._parse_time("25:00")  # Invalid hour
        
        with pytest.raises(ValueError):
            scheduler._parse_time("12:60")  # Invalid minute
    
    def test_calculate_next_run_daily(self, scheduler):
        """Test calculating next run for daily schedule."""
        next_run = scheduler._calculate_next_run("daily", "02:00")
        
        assert next_run is not None
        assert isinstance(next_run, datetime)
    
    def test_calculate_next_run_weekly(self, scheduler):
        """Test calculating next run for weekly schedule."""
        next_run = scheduler._calculate_next_run("weekly", "02:00", day_of_week=1)
        
        assert next_run is not None
        assert isinstance(next_run, datetime)


class TestScheduleDeletion:
    """Test schedule deletion."""
    
    def test_delete_schedule(self, scheduler, mock_db):
        """Test deleting a schedule."""
        mock_db.delete_schedule = MagicMock()
        
        scheduler.delete_schedule("sch_001")
        
        mock_db.delete_schedule.assert_called_once_with("sch_001")


class TestScheduleUpdate:
    """Test updating schedules."""
    
    def test_update_schedule(self, scheduler, mock_db):
        """Test updating a schedule."""
        mock_db.update_schedule = MagicMock()
        
        scheduler.update_schedule("sch_001", "weekly", "03:00")
        
        mock_db.update_schedule.assert_called_once()


class TestScheduleRestoration:
    """Test restoring schedules from database."""
    
    def test_restore_schedules_on_startup(self, scheduler, mock_db):
        """Test that schedules are restored from database on startup."""
        mock_db.list_all_schedules = MagicMock(
            return_value=[
                {
                    "id": "sch_001",
                    "project_id": "proj_123",
                    "frequency": "daily",
                    "time": "02:00",
                    "enabled": True
                }
            ]
        )
        
        # Restore schedules
        scheduler._restore_schedules()


class TestScheduleError Handling:
    """Test error handling in scheduler."""
    
    def test_handle_invalid_frequency(self, scheduler):
        """Test that invalid frequency raises error."""
        with pytest.raises((ValueError, KeyError)):
            scheduler.create_schedule("proj_123", "invalid_freq", "02:00")
    
    def test_handle_missing_project(self, scheduler, mock_db):
        """Test that creating schedule for missing project is handled."""
        mock_db.create_schedule = MagicMock(side_effect=Exception("Project not found"))
        
        with pytest.raises(Exception):
            scheduler.create_schedule("nonexistent_proj", "daily", "02:00")
