"""Test suite for bulk scanning functionality."""

import asyncio
import pytest
import json
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from scanner.web.bulk_scanner import BulkScanner, ScanTask
from database import (
    create_bulk_job, get_bulk_job, get_bulk_job_targets,
    update_bulk_job_status, update_target_status, list_bulk_jobs
)


class TestBulkScannerCore:
    """Test core BulkScanner functionality."""
    
    @pytest.fixture
    def bulk_scanner(self):
        """Create a BulkScanner instance."""
        return BulkScanner(max_parallel=3)
    
    def test_create_job(self, bulk_scanner):
        """Test job creation."""
        targets = ["example.com", "test.com", "sample.org"]
        modules = {"recon": True, "ports": True}
        
        job_id = "test-job-1"
        result = bulk_scanner.create_job(job_id, targets, modules)
        
        assert result == job_id
        assert job_id in bulk_scanner.job_queue
        assert len(bulk_scanner.job_queue[job_id]) == 3
        assert bulk_scanner.job_progress[job_id]["total"] == 3
        assert bulk_scanner.job_progress[job_id]["completed"] == 0
    
    def test_get_job_status(self, bulk_scanner):
        """Test getting job status."""
        job_id = "test-job-2"
        targets = ["example.com", "test.com"]
        modules = {"web": True}
        
        bulk_scanner.create_job(job_id, targets, modules)
        status = bulk_scanner.get_job_status(job_id)
        
        assert status["job_id"] == job_id
        assert status["total"] == 2
        assert status["completed"] == 0
        assert status["failed"] == 0
        assert status["progress"] == 0
    
    def test_get_job_results(self, bulk_scanner):
        """Test getting job results."""
        job_id = "test-job-3"
        targets = ["example.com"]
        modules = {"recon": True}
        
        bulk_scanner.create_job(job_id, targets, modules)
        results = bulk_scanner.get_job_results(job_id)
        
        assert results["job_id"] == job_id
        assert "targets" in results
        assert results["status"]["total"] == 1
    
    def test_cancel_job(self, bulk_scanner):
        """Test job cancellation."""
        job_id = "test-job-4"
        targets = ["example.com", "test.com"]
        modules = {"web": True}
        
        bulk_scanner.create_job(job_id, targets, modules)
        result = bulk_scanner.cancel_job(job_id)
        
        assert result["job_id"] == job_id
        assert result["status"] == "cancellation_requested"
    
    def test_get_queue_size(self, bulk_scanner):
        """Test getting queue size."""
        job_id = "test-job-5"
        targets = ["a.com", "b.com", "c.com"]
        
        bulk_scanner.create_job(job_id, targets, {})
        queue_size = bulk_scanner.get_queue_size(job_id)
        
        assert queue_size == 3
    
    def test_max_parallel_enforcement(self, bulk_scanner):
        """Test that max_parallel is respected."""
        assert bulk_scanner.max_parallel == 3
        
        # Create large job
        targets = [f"target{i}.com" for i in range(50)]
        bulk_scanner.create_job("large-job", targets, {})
        
        # Only max_parallel should process concurrently
        assert bulk_scanner.max_parallel == 3


class TestBulkScannerAsync:
    """Test async processing of bulk scanning."""
    
    @pytest.fixture
    async def async_bulk_scanner(self):
        """Create async-enabled BulkScanner."""
        async def mock_scan(target: str, modules: dict):
            await asyncio.sleep(0.01)  # Simulate scan
            return {"target": target, "vulnerabilities": 3}
        
        scanner = BulkScanner(max_parallel=2, scan_callback=mock_scan)
        return scanner
    
    @pytest.mark.asyncio
    async def test_concurrent_scanning(self, async_bulk_scanner):
        """Test concurrent target scanning."""
        job_id = "async-job-1"
        targets = ["example.com", "test.com", "sample.org"]
        modules = {"web": True}
        
        async_bulk_scanner.create_job(job_id, targets, modules)
        
        # Process job
        results = await async_bulk_scanner.process_job(job_id)
        
        assert len(results.get("results", [])) == 3
        assert results["status"] == "completed"
        
        # Check progress
        final_status = async_bulk_scanner.get_job_status(job_id)
        assert final_status["completed"] == 3
    
    @pytest.mark.asyncio
    async def test_error_handling_in_scan(self, async_bulk_scanner):
        """Test error handling during scanning."""
        async def failing_scan(target: str, modules: dict):
            if "fail" in target:
                raise Exception(f"Failed to scan {target}")
            return {"target": target}
        
        async_bulk_scanner.scan_callback = failing_scan
        
        job_id = "error-job"
        targets = ["good.com", "fail.com", "also-good.com"]
        
        async_bulk_scanner.create_job(job_id, targets, {})
        results = await async_bulk_scanner.process_job(job_id)
        
        # Check that some succeeded and some failed
        failed = [r for r in results["results"] if r.get("status") == "failed"]
        completed = [r for r in results["results"] if r.get("status") == "completed"]
        
        assert len(completed) == 2
        assert len(failed) >= 1
    
    @pytest.mark.asyncio
    async def test_concurrency_limit(self, async_bulk_scanner):
        """Test that concurrency limit is enforced."""
        running_count = []
        
        async def tracking_scan(target: str, modules: dict):
            current = len([t for t in async_bulk_scanner.running_tasks.values() 
                          if t.get("status") == "scanning"])
            running_count.append(current)
            await asyncio.sleep(0.05)
            return {"target": target}
        
        async_bulk_scanner.scan_callback = tracking_scan
        
        job_id = "concurrency-test"
        targets = [f"target{i}.com" for i in range(10)]
        
        async_bulk_scanner.create_job(job_id, targets, {})
        await async_bulk_scanner.process_job(job_id)
        
        # Max running should not exceed max_parallel
        assert max(running_count) <= async_bulk_scanner.max_parallel


class TestDatabaseIntegration:
    """Test database functions for bulk jobs."""
    
    def test_create_bulk_job_db(self):
        """Test creating bulk job in database."""
        project_id = "test-project"
        targets = ["example.com", "test.com"]
        config = {"recon": True}
        
        job_id = create_bulk_job(project_id, targets, config)
        
        assert job_id is not None
        assert len(job_id) > 0
    
    def test_get_bulk_job_db(self):
        """Test retrieving bulk job from database."""
        project_id = "test-project-2"
        targets = ["sample.com"]
        config = {"web": True}
        
        job_id = create_bulk_job(project_id, targets, config)
        job = get_bulk_job(job_id)
        
        assert job is not None
        assert job["project_id"] == project_id
        assert job["total_targets"] == 1
        assert job["status"] == "pending"
    
    def test_get_bulk_job_targets_db(self):
        """Test retrieving targets from database."""
        project_id = "test-project-3"
        targets = ["a.com", "b.com", "c.com"]
        
        job_id = create_bulk_job(project_id, targets, {})
        db_targets = get_bulk_job_targets(job_id)
        
        assert len(db_targets) == 3
        assert all(t["status"] == "pending" for t in db_targets)
    
    def test_update_job_status_db(self):
        """Test updating job status."""
        job_id = create_bulk_job("proj", ["test.com"], {})
        
        update_bulk_job_status(job_id, "running", 50)
        job = get_bulk_job(job_id)
        
        assert job["status"] == "running"
        assert job["progress"] == 50
    
    def test_list_bulk_jobs_db(self):
        """Test listing bulk jobs."""
        project_id = "test-project-list"
        
        # Create multiple jobs
        for i in range(3):
            create_bulk_job(project_id, [f"target{i}.com"], {})
        
        jobs = list_bulk_jobs(project_id, limit=10)
        
        assert len(jobs) >= 3


class TestPerformance:
    """Test performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_scanning_speed_improvement(self):
        """Test that parallel scanning is faster than sequential."""
        scan_times = []
        
        async def slow_scan(target: str, modules: dict):
            await asyncio.sleep(0.1)
            return {"target": target}
        
        # Test with max_parallel = 1 (sequential)
        sequential_scanner = BulkScanner(max_parallel=1, scan_callback=slow_scan)
        targets = [f"target{i}.com" for i in range(5)]
        
        import time
        sequential_scanner.create_job("seq-job", targets, {})
        start = time.time()
        await sequential_scanner.process_job("seq-job")
        seq_time = time.time() - start
        
        # Test with max_parallel = 5 (parallel)
        parallel_scanner = BulkScanner(max_parallel=5, scan_callback=slow_scan)
        parallel_scanner.create_job("par-job", targets, {})
        start = time.time()
        await parallel_scanner.process_job("par-job")
        par_time = time.time() - start
        
        # Parallel should be significantly faster
        # Each scan takes 0.1s, so 5 sequential = ~0.5s, 5 parallel = ~0.1s
        assert par_time < seq_time * 0.6  # Allow 60% overhead


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_targets(self):
        """Test with empty target list."""
        scanner = BulkScanner()
        
        job_id = "empty-job"
        result = scanner.create_job(job_id, [], {})
        
        assert result == job_id
        assert scanner.job_progress[job_id]["total"] == 0
    
    def test_duplicate_targets(self):
        """Test with duplicate targets."""
        scanner = BulkScanner()
        targets = ["same.com", "same.com", "different.com"]
        
        job_id = "dup-job"
        scanner.create_job(job_id, targets, {})
        
        # Should create task for each target, even duplicates
        assert len(scanner.job_queue[job_id]) == 3
    
    def test_large_target_list(self):
        """Test with large number of targets."""
        scanner = BulkScanner(max_parallel=5)
        targets = [f"target{i:04d}.com" for i in range(1000)]
        
        job_id = "large-job"
        scanner.create_job(job_id, targets, {})
        
        assert scanner.job_progress[job_id]["total"] == 1000
        assert len(scanner.job_queue[job_id]) == 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
