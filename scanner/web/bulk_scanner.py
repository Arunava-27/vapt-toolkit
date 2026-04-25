"""Bulk target scanning with parallel queue management."""

import asyncio
import uuid
import json
import logging
from datetime import datetime
from typing import Optional, Callable
from dataclasses import dataclass, field
from queue import Queue, PriorityQueue
from threading import Thread, Lock, Event
import time


logger = logging.getLogger(__name__)


@dataclass
class ScanTask:
    """Represents a target to scan."""
    target_id: str
    target_url: str
    modules: dict
    job_id: str
    retry_count: int = 0
    max_retries: int = 3
    
    def __lt__(self, other):
        """For priority queue ordering."""
        return self.retry_count < other.retry_count


class BulkScanner:
    """Manages parallel scanning of multiple targets with queue management."""
    
    def __init__(self, max_parallel: int = 10, scan_callback: Optional[Callable] = None):
        """
        Initialize BulkScanner.
        
        Args:
            max_parallel: Maximum number of concurrent scans (default: 10)
            scan_callback: Async callback function for executing individual scans
                          Signature: async def scan_callback(target, modules) -> results
        """
        self.max_parallel = max_parallel
        self.scan_callback = scan_callback
        self.job_queue: dict[str, list[ScanTask]] = {}  # job_id -> [tasks]
        self.running_tasks: dict[str, dict] = {}  # target_id -> task info
        self.job_progress: dict[str, dict] = {}  # job_id -> {completed, failed, total}
        self.lock = Lock()
        self.workers_running = False
        self.worker_thread: Optional[Thread] = None
        self.stop_event = Event()
    
    def create_job(self, job_id: str, targets: list[str], modules: dict) -> str:
        """
        Create a new scanning job.
        
        Args:
            job_id: Unique job identifier
            targets: List of target URLs to scan
            modules: Modules configuration (e.g., {"recon": True, "ports": True})
        
        Returns:
            job_id
        """
        with self.lock:
            tasks = [
                ScanTask(
                    target_id=str(uuid.uuid4()),
                    target_url=target,
                    modules=modules,
                    job_id=job_id
                )
                for target in targets
            ]
            self.job_queue[job_id] = tasks
            self.job_progress[job_id] = {
                "total": len(targets),
                "completed": 0,
                "failed": 0,
                "progress": 0
            }
        
        logger.info(f"Created bulk job {job_id} with {len(targets)} targets")
        return job_id
    
    def get_job_status(self, job_id: str) -> dict:
        """Get current status of a job."""
        with self.lock:
            if job_id not in self.job_progress:
                return None
            
            return {
                "job_id": job_id,
                "progress": self.job_progress[job_id]["progress"],
                "completed": self.job_progress[job_id]["completed"],
                "failed": self.job_progress[job_id]["failed"],
                "total": self.job_progress[job_id]["total"],
                "pending": self.job_progress[job_id]["total"] - 
                          self.job_progress[job_id]["completed"] - 
                          self.job_progress[job_id]["failed"]
            }
    
    def get_job_results(self, job_id: str) -> dict:
        """Get aggregated results from a completed job."""
        with self.lock:
            if job_id not in self.job_queue:
                return None
            
            tasks = self.job_queue[job_id]
            results = {
                "job_id": job_id,
                "status": self.job_progress[job_id],
                "targets": []
            }
            
            for task in tasks:
                target_info = self.running_tasks.get(task.target_id, {})
                results["targets"].append({
                    "target": task.target_url,
                    "status": target_info.get("status", "pending"),
                    "result": target_info.get("result"),
                    "error": target_info.get("error")
                })
            
            return results
    
    async def start_scanning(self, job_id: str) -> dict:
        """
        Start scanning job with parallel workers.
        
        Args:
            job_id: Job to start scanning
        
        Returns:
            Status dict with estimated time
        """
        with self.lock:
            if job_id not in self.job_queue:
                return {"error": "Job not found"}
            
            # Estimate time: assume 2 minutes per target, then divide by parallel count
            total_targets = self.job_progress[job_id]["total"]
            est_time_seconds = (total_targets * 120) / self.max_parallel
        
        logger.info(f"Starting job {job_id} with {total_targets} targets, "
                   f"est. time: {int(est_time_seconds/60)}m")
        
        return {
            "job_id": job_id,
            "status": "running",
            "estimated_time_seconds": est_time_seconds,
            "max_parallel": self.max_parallel
        }
    
    def cancel_job(self, job_id: str) -> dict:
        """Cancel a job."""
        with self.lock:
            if job_id not in self.job_queue:
                return {"error": "Job not found"}
            
            # Mark remaining tasks as cancelled
            for task in self.job_queue[job_id]:
                if task.target_id in self.running_tasks:
                    status = self.running_tasks[task.target_id].get("status", "pending")
                    if status == "pending":
                        self.running_tasks[task.target_id]["status"] = "cancelled"
            
            logger.info(f"Cancelled job {job_id}")
        
        return {"job_id": job_id, "status": "cancellation_requested"}
    
    async def process_job(self, job_id: str) -> dict:
        """
        Process all targets in a job with parallel scanning.
        
        Yields/returns progress updates and results.
        """
        if not self.scan_callback:
            raise ValueError("No scan_callback provided to BulkScanner")
        
        with self.lock:
            tasks = self.job_queue.get(job_id, [])
        
        if not tasks:
            return {"error": "Job not found"}
        
        # Process tasks with concurrency limit
        results = []
        semaphore = asyncio.Semaphore(self.max_parallel)
        
        async def scan_with_semaphore(task: ScanTask):
            async with semaphore:
                return await self._scan_target(task, job_id)
        
        # Run all scans concurrently
        scan_results = await asyncio.gather(
            *[scan_with_semaphore(task) for task in tasks],
            return_exceptions=True
        )
        
        results = [r for r in scan_results if not isinstance(r, Exception)]
        
        return {
            "job_id": job_id,
            "status": "completed",
            "results": results,
            "summary": self.get_job_status(job_id)
        }
    
    async def _scan_target(self, task: ScanTask, job_id: str) -> dict:
        """Scan a single target with retry logic."""
        target_id = task.target_id
        
        with self.lock:
            self.running_tasks[target_id] = {
                "status": "scanning",
                "started_at": datetime.now().isoformat(),
                "target": task.target_url
            }
        
        try:
            logger.info(f"Starting scan of {task.target_url} (attempt {task.retry_count + 1})")
            
            # Call the actual scanner
            result = await self.scan_callback(task.target_url, task.modules)
            
            with self.lock:
                self.running_tasks[target_id]["status"] = "completed"
                self.running_tasks[target_id]["result"] = result
                self.running_tasks[target_id]["completed_at"] = datetime.now().isoformat()
                
                # Update job progress
                self.job_progress[job_id]["completed"] += 1
                self.job_progress[job_id]["progress"] = int(
                    (self.job_progress[job_id]["completed"] / self.job_progress[job_id]["total"]) * 100
                )
            
            logger.info(f"Completed scan of {task.target_url}")
            
            return {
                "target": task.target_url,
                "target_id": target_id,
                "status": "completed",
                "result": result
            }
        
        except Exception as e:
            logger.error(f"Error scanning {task.target_url}: {str(e)}")
            
            with self.lock:
                self.running_tasks[target_id]["status"] = "error"
                self.running_tasks[target_id]["error"] = str(e)
                self.running_tasks[target_id]["completed_at"] = datetime.now().isoformat()
                
                # Retry logic
                if task.retry_count < task.max_retries:
                    task.retry_count += 1
                    self.running_tasks[target_id]["status"] = "pending"
                    logger.info(f"Will retry {task.target_url} (attempt {task.retry_count + 1})")
                else:
                    self.job_progress[job_id]["failed"] += 1
                    self.job_progress[job_id]["progress"] = int(
                        ((self.job_progress[job_id]["completed"] + self.job_progress[job_id]["failed"]) 
                         / self.job_progress[job_id]["total"]) * 100
                    )
            
            return {
                "target": task.target_url,
                "target_id": target_id,
                "status": "failed",
                "error": str(e)
            }
    
    def get_running_count(self, job_id: str = None) -> int:
        """Get count of currently running scans."""
        with self.lock:
            if job_id:
                return sum(1 for t in self.running_tasks.values() 
                          if t.get("status") == "scanning")
            return len([t for t in self.running_tasks.values() 
                       if t.get("status") == "scanning"])
    
    def get_queue_size(self, job_id: str = None) -> int:
        """Get count of pending scans."""
        with self.lock:
            if job_id:
                return sum(1 for t in self.job_queue.get(job_id, []) 
                          if t.target_id not in self.running_tasks or 
                          self.running_tasks[t.target_id].get("status") == "pending")
            return sum(sum(1 for t in tasks if t.target_id not in self.running_tasks or 
                          self.running_tasks[t.target_id].get("status") == "pending")
                      for tasks in self.job_queue.values())
    
    def cleanup_job(self, job_id: str):
        """Clean up resources for a completed job."""
        with self.lock:
            if job_id in self.job_queue:
                del self.job_queue[job_id]
            if job_id in self.job_progress:
                del self.job_progress[job_id]
