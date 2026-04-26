"""Bulk scanning endpoints and background job management."""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database import (create_bulk_job, get_bulk_job, get_bulk_job_targets,
                      update_bulk_job_status, update_bulk_job_timing, update_target_status,
                      list_bulk_jobs, cancel_bulk_job)
from scanner.web.bulk_scanner import BulkScanner

logger = logging.getLogger(__name__)

router = APIRouter()

bulk_scanner = None


class BulkScanRequest(BaseModel):
    targets: list[str]
    modules: dict
    max_parallel: int = 5
    project_id: Optional[str] = None


# Bulk Scan Endpoints

@router.post("/bulk/scan")
async def create_bulk_scan(req: BulkScanRequest):
    """Create and start a bulk scanning job."""
    if not req.targets:
        raise HTTPException(status_code=400, detail="No targets provided")
    
    if len(req.targets) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 targets per job")
    
    if req.max_parallel < 1 or req.max_parallel > 20:
        raise HTTPException(status_code=400, detail="max_parallel must be between 1-20")
    
    try:
        import uuid
        job_id = create_bulk_job(
            project_id=req.project_id or str(uuid.uuid4()),
            targets=req.targets,
            config=req.modules.copy()
        )
        
        bulk_scanner.create_job(job_id, req.targets, req.modules)
        bulk_scanner.max_parallel = req.max_parallel
        
        asyncio.create_task(_run_bulk_job(job_id))
        
        status = await bulk_scanner.start_scanning(job_id)
        
        return {
            "job_id": job_id,
            **status,
            "targets_count": len(req.targets)
        }
    
    except Exception as e:
        logger.error(f"Error creating bulk scan: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bulk/jobs")
async def list_bulk_jobs_endpoint(project_id: str = None, limit: int = 50):
    """List all bulk scanning jobs."""
    jobs = list_bulk_jobs(project_id, limit)
    return {"jobs": jobs, "count": len(jobs)}


@router.get("/bulk/jobs/{job_id}")
async def get_bulk_job_status(job_id: str):
    """Get status of a bulk scanning job."""
    job = get_bulk_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    status = bulk_scanner.get_job_status(job_id)
    
    return {
        "job_id": job_id,
        "status": job.get("status"),
        "progress": job.get("progress"),
        "completed": job.get("completed_count"),
        "failed": job.get("failed_count"),
        "total": job.get("total_targets"),
        "created_at": job.get("created_at"),
        "started_at": job.get("started_at"),
        "completed_at": job.get("completed_at"),
        "queue_size": bulk_scanner.get_queue_size(job_id),
        "running_count": bulk_scanner.get_running_count(job_id)
    }


@router.get("/bulk/jobs/{job_id}/targets")
async def get_bulk_job_targets_endpoint(job_id: str, limit: int = 50, offset: int = 0):
    """Get targets and their status for a bulk job."""
    job = get_bulk_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    targets = get_bulk_job_targets(job_id, limit, offset)
    
    return {
        "job_id": job_id,
        "targets": targets,
        "total": job.get("total_targets"),
        "limit": limit,
        "offset": offset
    }


@router.get("/bulk/jobs/{job_id}/results")
async def get_bulk_job_results(job_id: str):
    """Get aggregated results from a bulk scanning job."""
    job = get_bulk_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.get("status") not in ("completed", "cancelled"):
        raise HTTPException(status_code=400, detail="Job is still running or failed")
    
    results = bulk_scanner.get_job_results(job_id)
    
    return {
        "job_id": job_id,
        "status": job.get("status"),
        "created_at": job.get("created_at"),
        "completed_at": job.get("completed_at"),
        "summary": {
            "total": results.get("status", {}).get("total"),
            "completed": results.get("status", {}).get("completed"),
            "failed": results.get("status", {}).get("failed")
        },
        "results": results.get("targets", [])
    }


@router.post("/bulk/jobs/{job_id}/cancel")
async def cancel_bulk_job_endpoint(job_id: str):
    """Cancel a running bulk scanning job."""
    job = get_bulk_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.get("status") == "completed":
        raise HTTPException(status_code=400, detail="Job already completed")
    
    if job.get("status") == "cancelled":
        raise HTTPException(status_code=400, detail="Job already cancelled")
    
    result = bulk_scanner.cancel_job(job_id)
    update_bulk_job_status(job_id, "cancelled")
    
    return result


@router.get("/bulk/stats")
async def get_bulk_stats():
    """Get statistics about bulk scanning jobs."""
    jobs = list_bulk_jobs(limit=1000)
    
    total_jobs = len(jobs)
    completed = sum(1 for j in jobs if j.get("status") == "completed")
    running = sum(1 for j in jobs if j.get("status") == "running")
    failed = sum(1 for j in jobs if j.get("status") == "failed")
    cancelled = sum(1 for j in jobs if j.get("status") == "cancelled")
    
    total_targets = sum(j.get("total_targets", 0) for j in jobs)
    completed_targets = sum(j.get("completed_count", 0) for j in jobs)
    failed_targets = sum(j.get("failed_count", 0) for j in jobs)
    
    return {
        "total_jobs": total_jobs,
        "status_breakdown": {
            "completed": completed,
            "running": running,
            "failed": failed,
            "cancelled": cancelled,
            "pending": total_jobs - completed - running - failed - cancelled
        },
        "targets": {
            "total": total_targets,
            "completed": completed_targets,
            "failed": failed_targets,
            "success_rate": (completed_targets / total_targets * 100) if total_targets > 0 else 0
        }
    }


# Background job processing

async def _run_bulk_job(job_id: str):
    """Background task to process a bulk scanning job."""
    try:
        update_bulk_job_status(job_id, "running")
        update_bulk_job_timing(job_id, started_at=datetime.now().isoformat())
        
        logger.info(f"Starting bulk job {job_id}")
        
        results = await bulk_scanner.process_job(job_id)
        
        # Update database with results
        update_bulk_job_status(job_id, "completed", 100)
        update_bulk_job_timing(job_id, completed_at=datetime.now().isoformat())
        
        # Update target statuses
        for target_result in results.get("results", []):
            target_id = target_result.get("target_id")
            status = target_result.get("status", "unknown")
            result = target_result.get("result")
            error = target_result.get("error")
            
            update_target_status(
                target_id,
                status,
                result=str(result) if result else None,
                error=error,
                completed_at=datetime.now().isoformat()
            )
        
        logger.info(f"Completed bulk job {job_id}")
    
    except Exception as e:
        logger.error(f"Error in bulk job {job_id}: {str(e)}")
        update_bulk_job_status(job_id, "failed")
        update_bulk_job_timing(job_id, completed_at=datetime.now().isoformat())
