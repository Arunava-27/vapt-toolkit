"""APScheduler-based scan scheduling system for VAPT."""

import uuid
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger


class ScanScheduler:
    def __init__(self, db_module):
        """Initialize scheduler with database module for persistence."""
        self.scheduler = BackgroundScheduler()
        self.db = db_module
        self._active_jobs = {}  # Track scheduled job IDs for deletion
        
    def start(self):
        """Start the background scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            self._restore_schedules()
    
    def stop(self):
        """Stop the background scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
    
    def _parse_time(self, time_str: str) -> tuple:
        """Parse time string (HH:MM) into hour, minute tuple."""
        parts = time_str.split(':')
        return int(parts[0]), int(parts[1])
    
    def _calculate_next_run(self, frequency: str, time_str: str, day_of_week: int = None) -> datetime:
        """Calculate next run time based on frequency."""
        hour, minute = self._parse_time(time_str)
        now = datetime.now()
        
        if frequency == "daily":
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        elif frequency == "weekly":
            days_ahead = (day_of_week - now.weekday()) % 7
            next_run = now + timedelta(days=days_ahead)
            next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(weeks=1)
        elif frequency == "monthly":
            # Next run on same day of next month
            if now.month == 12:
                next_run = now.replace(year=now.year + 1, month=1, day=1, 
                                       hour=hour, minute=minute, second=0, microsecond=0)
            else:
                next_run = now.replace(month=now.month + 1, day=1,
                                       hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                # If we've already passed the date in this month, go to next month
                if now.month == 12:
                    next_run = now.replace(year=now.year + 1, month=1, 
                                           hour=hour, minute=minute, second=0, microsecond=0)
                else:
                    next_run = now.replace(month=now.month + 1,
                                           hour=hour, minute=minute, second=0, microsecond=0)
        else:
            next_run = now + timedelta(hours=1)
        
        return next_run
    
    def create_schedule(self, project_id: str, frequency: str, time_str: str, 
                       day_of_week: int = None, enabled: bool = True) -> dict:
        """
        Create a new schedule.
        
        Args:
            project_id: Project to schedule scans for
            frequency: 'daily', 'weekly', or 'monthly'
            time_str: Time in 'HH:MM' format (UTC)
            day_of_week: 0-6 (Monday-Sunday) for weekly schedules
            enabled: Whether schedule is active
            
        Returns:
            Schedule record dict
        """
        schedule_id = str(uuid.uuid4())
        next_run = self._calculate_next_run(frequency, time_str, day_of_week)
        
        schedule_data = {
            "id": schedule_id,
            "project_id": project_id,
            "frequency": frequency,
            "time": time_str,
            "day_of_week": day_of_week,
            "enabled": enabled,
            "last_run": None,
            "next_run": next_run.isoformat(),
            "created_at": datetime.now().isoformat(),
        }
        
        # Save to database
        self.db.create_schedule(schedule_data)
        
        # Register with APScheduler if enabled
        if enabled:
            self._register_job(schedule_data)
        
        return schedule_data
    
    def _register_job(self, schedule_data: dict):
        """Register a schedule with APScheduler."""
        schedule_id = schedule_data["id"]
        frequency = schedule_data["frequency"]
        time_str = schedule_data["time"]
        day_of_week = schedule_data.get("day_of_week")
        
        hour, minute = self._parse_time(time_str)
        
        try:
            if frequency == "daily":
                trigger = CronTrigger(hour=hour, minute=minute)
            elif frequency == "weekly":
                trigger = CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute)
            elif frequency == "monthly":
                trigger = CronTrigger(day=1, hour=hour, minute=minute)
            else:
                return
            
            job = self.scheduler.add_job(
                self.run_scheduled_scan,
                trigger=trigger,
                args=[schedule_id],
                id=schedule_id,
                replace_existing=True
            )
            self._active_jobs[schedule_id] = job.id
        except Exception as e:
            print(f"Failed to register job for schedule {schedule_id}: {e}")
    
    def run_scheduled_scan(self, schedule_id: str):
        """Execute scan for a schedule. Called by APScheduler."""
        # This imports here to avoid circular imports
        from database import get_project, update_schedule_run
        
        try:
            schedule = self.db.get_schedule(schedule_id)
            if not schedule:
                return
            
            project_id = schedule["project_id"]
            project = get_project(project_id)
            if not project:
                return
            
            # Update last_run timestamp
            self.db.update_schedule_run(schedule_id, datetime.now().isoformat())
            
            # The actual scan execution will be triggered via API
            # This is just marking that the schedule was executed
            print(f"[SCHEDULER] Running scheduled scan for project {project_id} (schedule {schedule_id})")
            
        except Exception as e:
            print(f"Error running scheduled scan {schedule_id}: {e}")
    
    def list_schedules(self) -> list:
        """Get all schedules."""
        return self.db.list_schedules()
    
    def get_schedule(self, schedule_id: str) -> dict:
        """Get schedule by ID."""
        return self.db.get_schedule(schedule_id)
    
    def update_schedule(self, schedule_id: str, updates: dict) -> dict:
        """Update an existing schedule."""
        schedule = self.db.get_schedule(schedule_id)
        if not schedule:
            raise ValueError(f"Schedule {schedule_id} not found")
        
        # Merge updates
        updated = {**schedule, **updates}
        updated["updated_at"] = datetime.now().isoformat()
        
        # Recalculate next_run if frequency/time changed
        if "frequency" in updates or "time" in updates:
            freq = updated["frequency"]
            time_str = updated["time"]
            dow = updated.get("day_of_week")
            updated["next_run"] = self._calculate_next_run(freq, time_str, dow).isoformat()
        
        # Save to database
        self.db.update_schedule(schedule_id, updated)
        
        # Re-register with scheduler if enabled
        if updated["enabled"]:
            if schedule_id in self._active_jobs:
                try:
                    self.scheduler.remove_job(schedule_id)
                except:
                    pass
            self._register_job(updated)
        else:
            # Disable the job
            if schedule_id in self._active_jobs:
                try:
                    self.scheduler.remove_job(schedule_id)
                    del self._active_jobs[schedule_id]
                except:
                    pass
        
        return updated
    
    def delete_schedule(self, schedule_id: str):
        """Delete a schedule."""
        # Remove from scheduler
        if schedule_id in self._active_jobs:
            try:
                self.scheduler.remove_job(schedule_id)
                del self._active_jobs[schedule_id]
            except:
                pass
        
        # Remove from database
        self.db.delete_schedule(schedule_id)
    
    def _restore_schedules(self):
        """Restore all enabled schedules from database on startup."""
        schedules = self.db.list_schedules()
        for schedule in schedules:
            if schedule.get("enabled"):
                self._register_job(schedule)
