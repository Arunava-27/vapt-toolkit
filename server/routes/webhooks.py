"""Webhook management endpoints."""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from database import get_project
from scanner.webhooks import get_webhook_manager, WebhookEvent
from ..middleware.auth import require_api_key

logger = logging.getLogger(__name__)

router = APIRouter()

webhook_manager = get_webhook_manager()


class WebhookRegisterRequest(BaseModel):
    url: str
    events: list[str]
    secret: str


class WebhookResponse(BaseModel):
    id: str
    project_id: str
    url: str
    events: list[str]
    enabled: bool
    created_at: str
    last_triggered: Optional[str] = None


class WebhookTestRequest(BaseModel):
    webhook_id: str
    event_type: str = "test_event"


# Webhook Endpoints

@router.post("/webhooks")
async def register_webhook(
    body: WebhookRegisterRequest,
    project_id: str = Depends(require_api_key)
) -> WebhookResponse:
    """Register a webhook for a project."""
    project = get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Validate URL
    if not body.url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid webhook URL")
    
    # Validate events
    valid_events = {
        "scan_started", "scan_completed", "finding_discovered",
        "scan_failed", "report_generated", "vulnerability_fixed", "*"
    }
    for event in body.events:
        if event not in valid_events:
            raise HTTPException(status_code=400, detail=f"Invalid event type: {event}")
    
    # Register webhook
    webhook_id = webhook_manager.register_webhook(
        project_id=project_id,
        url=body.url,
        events=body.events,
        secret=body.secret
    )
    
    return WebhookResponse(
        id=webhook_id,
        project_id=project_id,
        url=body.url,
        events=body.events,
        enabled=True,
        created_at=datetime.now().isoformat()
    )


@router.get("/webhooks")
async def list_webhooks(project_id: str = Depends(require_api_key)) -> list[WebhookResponse]:
    """List webhooks for a project."""
    project = get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    webhooks = webhook_manager.get_webhooks(project_id=project_id)
    return [WebhookResponse(**w) for w in webhooks]


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    project_id: str = Depends(require_api_key)
) -> dict:
    """Delete a webhook."""
    webhooks = webhook_manager.get_webhooks(project_id=project_id)
    webhook = next((w for w in webhooks if w["id"] == webhook_id), None)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    webhook_manager.delete_webhook(webhook_id)
    return {"ok": True}


@router.post("/webhooks/{webhook_id}/enable")
async def enable_webhook(
    webhook_id: str,
    project_id: str = Depends(require_api_key)
) -> dict:
    """Enable a webhook."""
    webhooks = webhook_manager.get_webhooks(project_id=project_id)
    webhook = next((w for w in webhooks if w["id"] == webhook_id), None)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    webhook_manager.enable_webhook(webhook_id)
    return {"ok": True}


@router.post("/webhooks/{webhook_id}/disable")
async def disable_webhook(
    webhook_id: str,
    project_id: str = Depends(require_api_key)
) -> dict:
    """Disable a webhook."""
    webhooks = webhook_manager.get_webhooks(project_id=project_id)
    webhook = next((w for w in webhooks if w["id"] == webhook_id), None)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    webhook_manager.disable_webhook(webhook_id)
    return {"ok": True}


@router.get("/webhooks/{webhook_id}/logs")
async def get_webhook_logs(
    webhook_id: str,
    limit: int = 50,
    project_id: str = Depends(require_api_key)
) -> dict:
    """Get webhook delivery logs."""
    webhooks = webhook_manager.get_webhooks(project_id=project_id)
    webhook = next((w for w in webhooks if w["id"] == webhook_id), None)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    logs = webhook_manager.get_webhook_logs(webhook_id, limit=limit)
    stats = webhook_manager.get_webhook_stats(webhook_id)
    
    return {
        "logs": logs,
        "stats": stats
    }


@router.post("/webhooks/test")
async def test_webhook(
    body: WebhookTestRequest,
    project_id: str = Depends(require_api_key)
) -> dict:
    """Test a webhook by sending a test event."""
    webhooks = webhook_manager.get_webhooks(project_id=project_id)
    webhook = next((w for w in webhooks if w["id"] == body.webhook_id), None)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    # Send test event
    event = WebhookEvent(
        event_type=body.event_type,
        project_id=project_id,
        data={
            "test": True,
            "message": "This is a test event"
        }
    )
    
    result = await webhook_manager.trigger_webhook(event)
    return result
