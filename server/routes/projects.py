"""Project management endpoints."""

import asyncio
import logging
from fastapi import APIRouter, HTTPException

from database import (list_projects, get_project, rename_project, delete_project, 
                      dashboard_stats, save_project)
from reporter.pdf_reporter import generate_pdf
from fastapi.responses import Response
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# Get reference to ACTIVE_SCANS from main app
ACTIVE_SCANS = {}


class RenameBody(BaseModel):
    name: str


@router.get("/projects")
async def api_list_projects():
    """List all projects."""
    try:
        loop = asyncio.get_event_loop()
        logger.info("Projects: Starting to fetch list...")
        projects = await asyncio.wait_for(
            loop.run_in_executor(None, list_projects),
            timeout=5.0
        )
        logger.info(f"Projects: Returning {len(projects)} projects")
        return projects
    except asyncio.TimeoutError:
        logger.warning("Projects: list_projects() timed out after 5s")
        raise HTTPException(status_code=503, detail="Database query timeout. Please try again.")
    except Exception as e:
        logger.exception(f"Projects endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def api_dashboard():
    """Get dashboard statistics."""
    try:
        loop = asyncio.get_event_loop()
        logger.info("Dashboard: Starting to fetch stats...")
        
        # Fetch dashboard stats with timeout
        try:
            stats = await asyncio.wait_for(
                loop.run_in_executor(None, dashboard_stats),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            logger.warning("Dashboard: dashboard_stats() timed out after 5s")
            stats = {"projects": 0, "ports": 0, "cves": 0, "subdomains": 0, "web": 0}
        
        # Get active scans count
        active = sum(1 for s in ACTIVE_SCANS.values() if s.status == "running")
        
        # Fetch recent projects with timeout
        try:
            recent = await asyncio.wait_for(
                loop.run_in_executor(None, list_projects),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            logger.warning("Dashboard: list_projects() timed out after 5s")
            recent = []
        
        logger.info(f"Dashboard: Returning stats with {len(recent)} recent projects")
        return {**stats, "active_scans": active, "recent_projects": recent[:5]}
    except Exception as e:
        logger.exception(f"Dashboard endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{pid}")
async def api_get_project(pid: str):
    """Get a specific project."""
    p = get_project(pid)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return p


@router.put("/projects/{pid}")
async def api_rename_project(pid: str, body: RenameBody):
    """Rename a project."""
    if not get_project(pid):
        raise HTTPException(status_code=404, detail="Project not found")
    rename_project(pid, body.name.strip())
    return {"ok": True}


@router.delete("/projects/{pid}")
async def api_delete_project(pid: str):
    """Delete a project."""
    if not get_project(pid):
        raise HTTPException(status_code=404, detail="Project not found")
    delete_project(pid)
    return {"ok": True}


@router.get("/projects/{pid}/pdf")
async def api_export_pdf(pid: str):
    """Export project as PDF."""
    p = get_project(pid)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    loop = asyncio.get_event_loop()
    pdf_bytes = await loop.run_in_executor(None, generate_pdf, p)
    slug = "".join(c if c.isalnum() or c in "-_." else "-" for c in p["target"])
    filename = f"vapt-{slug}-{pid[:8]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
