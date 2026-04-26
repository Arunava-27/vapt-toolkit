"""Notification management endpoints."""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from scanner.notifications import get_notification_manager

logger = logging.getLogger(__name__)

router = APIRouter()

notification_manager = get_notification_manager()

# Reference to ACTIVE_SCANS from main app
ACTIVE_SCANS = {}


class NotificationConfig(BaseModel):
    severity_filter: str = "high"
    channels: list[str] = ["desktop"]
    email: Optional[str] = None
    finding_types: str = "all"


class SendNotificationRequest(BaseModel):
    title: str
    message: str
    severity: str = "info"
    finding_type: Optional[str] = None


# Notification Endpoints

async def set_scan_notification_config(scan_id: str, config: NotificationConfig):
    """Set notification configuration for a scan."""
    state = ACTIVE_SCANS.get(scan_id)
    if not state:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    state.notification_config = {
        'severity_filter': config.severity_filter,
        'channels': config.channels,
        'email': config.email,
        'finding_types': config.finding_types,
    }
    
    return {"ok": True, "notification_config": state.notification_config}


async def get_scan_notification_config(scan_id: str):
    """Get notification configuration for a scan."""
    state = ACTIVE_SCANS.get(scan_id)
    if not state:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    return state.notification_config


async def send_test_notification(req: SendNotificationRequest):
    """Send a test notification (for UI testing)."""
    result = await notification_manager.send_desktop_notification(
        title=req.title,
        message=req.message,
        severity=req.severity,
        finding_type=req.finding_type
    )
    return {"ok": result, "message": "Notification sent"}


async def test_email_notification(email: str):
    """Send a test email notification."""
    test_finding = {
        'type': 'test',
        'description': 'This is a test notification',
        'timestamp': datetime.now().isoformat(),
    }
    
    result = notification_manager.send_email_notification(
        recipient=email,
        finding_title="Test Finding",
        finding_details=test_finding,
        severity="high"
    )
    
    return {"ok": result, "message": "Test email sent" if result else "Failed to send email"}


async def test_slack_notification():
    """Send a test Slack notification."""
    test_finding = {
        'type': 'test',
        'description': 'This is a test notification from VAPT Toolkit',
        'timestamp': datetime.now().isoformat(),
    }
    
    result = await notification_manager.send_slack_webhook(
        finding_title="Test Finding",
        finding_details=test_finding,
        severity="high"
    )
    
    return {"ok": result, "message": "Test Slack notification sent" if result else "Failed to send Slack notification"}


async def test_teams_notification():
    """Send a test Teams notification."""
    test_finding = {
        'type': 'test',
        'description': 'This is a test notification from VAPT Toolkit',
        'timestamp': datetime.now().isoformat(),
    }
    
    result = await notification_manager.send_teams_webhook(
        finding_title="Test Finding",
        finding_details=test_finding,
        severity="high"
    )
    
    return {"ok": result, "message": "Test Teams notification sent" if result else "Failed to send Teams notification"}


async def get_notification_config():
    """Get global notification configuration status."""
    return {
        'smtp_configured': bool(notification_manager.smtp_config.get('host')),
        'slack_configured': bool(notification_manager.slack_webhook),
        'teams_configured': bool(notification_manager.teams_webhook),
        'smtp_host': notification_manager.smtp_config.get('host', ''),
    }
