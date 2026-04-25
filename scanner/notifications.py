"""Notification system for critical findings."""
import asyncio
import json
import os
import smtplib
import logging
from typing import Optional, Dict, List, Callable
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiohttp

logger = logging.getLogger(__name__)


class NotificationManager:
    """Manages notifications across multiple channels."""
    
    def __init__(self):
        self.smtp_config = {
            'host': os.getenv('SMTP_HOST', ''),
            'port': int(os.getenv('SMTP_PORT', 587)),
            'username': os.getenv('SMTP_USERNAME', ''),
            'password': os.getenv('SMTP_PASSWORD', ''),
            'from_email': os.getenv('SMTP_FROM_EMAIL', ''),
        }
        self.slack_webhook = os.getenv('SLACK_WEBHOOK_URL', '')
        self.teams_webhook = os.getenv('TEAMS_WEBHOOK_URL', '')
        self.notification_callbacks: List[Callable] = []
        
    def register_callback(self, callback: Callable) -> None:
        """Register a callback for real-time notifications (SSE, WebSocket)."""
        self.notification_callbacks.append(callback)
    
    async def _trigger_callbacks(self, notification: Dict) -> None:
        """Trigger all registered callbacks."""
        for callback in self.notification_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(notification)
                else:
                    callback(notification)
            except Exception as e:
                logger.error(f"Error in notification callback: {e}")
    
    # ── Desktop Notification (WebSocket/SSE) ──────────────────────────────────
    
    async def send_desktop_notification(
        self,
        title: str,
        message: str,
        severity: str = "info",
        finding_type: Optional[str] = None
    ) -> bool:
        """Send desktop notification via WebSocket/SSE."""
        try:
            notification = {
                'type': 'notification',
                'title': title,
                'message': message,
                'severity': severity,
                'finding_type': finding_type,
                'timestamp': datetime.now().isoformat(),
            }
            await self._trigger_callbacks(notification)
            return True
        except Exception as e:
            logger.error(f"Desktop notification error: {e}")
            return False
    
    # ── Email Notification ────────────────────────────────────────────────────
    
    def send_email_notification(
        self,
        recipient: str,
        finding_title: str,
        finding_details: Dict,
        severity: str = "critical"
    ) -> bool:
        """Send email alert with finding details."""
        if not all([self.smtp_config['host'], self.smtp_config['from_email']]):
            logger.warning("SMTP not configured. Email notification skipped.")
            return False
        
        try:
            subject = f"[{severity.upper()}] VAPT Finding: {finding_title}"
            
            html_body = self._build_email_html(
                finding_title,
                finding_details,
                severity
            )
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_config['from_email']
            msg['To'] = recipient
            
            msg.attach(MIMEText(html_body, 'html'))
            
            with smtplib.SMTP(
                self.smtp_config['host'],
                self.smtp_config['port']
            ) as server:
                if self.smtp_config['port'] == 587:
                    server.starttls()
                
                if self.smtp_config['username']:
                    server.login(
                        self.smtp_config['username'],
                        self.smtp_config['password']
                    )
                
                server.send_message(msg)
            
            logger.info(f"Email notification sent to {recipient}")
            return True
        except Exception as e:
            logger.error(f"Email notification error: {e}")
            return False
    
    def _build_email_html(
        self,
        title: str,
        details: Dict,
        severity: str
    ) -> str:
        """Build HTML email body."""
        severity_color = {
            'critical': '#d32f2f',
            'high': '#f57c00',
            'medium': '#fbc02d',
            'low': '#388e3c',
        }.get(severity.lower(), '#666666')
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; }}
                .header {{ 
                    background-color: {severity_color}; 
                    color: white; 
                    padding: 20px; 
                    border-radius: 5px;
                }}
                .content {{ padding: 20px; background-color: #f5f5f5; }}
                .detail {{ margin: 10px 0; }}
                .label {{ font-weight: bold; color: #333; }}
                .value {{ color: #666; margin-left: 10px; }}
                .footer {{ text-align: center; padding: 20px; color: #999; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>{title}</h2>
                    <p>Severity: <strong>{severity.upper()}</strong></p>
                </div>
                <div class="content">
                    {self._format_details_html(details)}
                </div>
                <div class="footer">
                    <p>VAPT Toolkit - Automated Notification</p>
                    <p>{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    def _format_details_html(self, details: Dict) -> str:
        """Format details as HTML."""
        html = ""
        for key, value in details.items():
            if isinstance(value, (dict, list)):
                value = json.dumps(value, indent=2)
            
            key_display = key.replace('_', ' ').title()
            html += f'<div class="detail"><span class="label">{key_display}:</span><span class="value">{value}</span></div>'
        
        return html
    
    # ── Slack Webhook ────────────────────────────────────────────────────────
    
    async def send_slack_webhook(
        self,
        finding_title: str,
        finding_details: Dict,
        severity: str = "critical"
    ) -> bool:
        """Post finding to Slack channel."""
        if not self.slack_webhook:
            logger.warning("Slack webhook not configured. Skipping Slack notification.")
            return False
        
        try:
            severity_color = {
                'critical': '#d32f2f',
                'high': '#f57c00',
                'medium': '#fbc02d',
                'low': '#388e3c',
            }.get(severity.lower(), '#666666')
            
            fields = []
            for key, value in finding_details.items():
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, indent=2)
                
                fields.append({
                    "title": key.replace('_', ' ').title(),
                    "value": str(value)[:500],
                    "short": len(str(value)) < 50
                })
            
            payload = {
                "attachments": [
                    {
                        "color": severity_color,
                        "title": finding_title,
                        "text": f"Severity: {severity.upper()}",
                        "fields": fields[:10],
                        "footer": "VAPT Toolkit",
                        "ts": int(datetime.now().timestamp())
                    }
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.slack_webhook, json=payload) as resp:
                    if resp.status != 200:
                        logger.error(f"Slack webhook returned {resp.status}")
                        return False
            
            logger.info("Slack notification sent")
            return True
        except Exception as e:
            logger.error(f"Slack notification error: {e}")
            return False
    
    # ── Microsoft Teams Webhook ───────────────────────────────────────────────
    
    async def send_teams_webhook(
        self,
        finding_title: str,
        finding_details: Dict,
        severity: str = "critical"
    ) -> bool:
        """Post finding to Microsoft Teams channel."""
        if not self.teams_webhook:
            logger.warning("Teams webhook not configured. Skipping Teams notification.")
            return False
        
        try:
            severity_color = {
                'critical': 'E81828',
                'high': 'FF8C00',
                'medium': 'FFB900',
                'low': '107C10',
            }.get(severity.lower(), '606E7D')
            
            facts = []
            for key, value in finding_details.items():
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, indent=2)
                
                facts.append({
                    "name": key.replace('_', ' ').title(),
                    "value": str(value)[:500]
                })
            
            payload = {
                "@type": "MessageCard",
                "@context": "https://schema.org/extensions",
                "summary": finding_title,
                "themeColor": severity_color,
                "title": finding_title,
                "sections": [
                    {
                        "activityTitle": f"Severity: {severity.upper()}",
                        "facts": facts[:10],
                        "markdown": True
                    }
                ],
                "footer": {
                    "image": "",
                    "text": f"VAPT Toolkit | {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.teams_webhook, json=payload) as resp:
                    if resp.status not in (200, 201):
                        logger.error(f"Teams webhook returned {resp.status}")
                        return False
            
            logger.info("Teams notification sent")
            return True
        except Exception as e:
            logger.error(f"Teams notification error: {e}")
            return False
    
    # ── Generic notification dispatcher ───────────────────────────────────────
    
    async def send_finding_notification(
        self,
        finding_title: str,
        finding_details: Dict,
        severity: str = "critical",
        finding_type: Optional[str] = None,
        recipient_email: Optional[str] = None,
        channels: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        Send finding notifications across multiple channels.
        
        Args:
            finding_title: Title/name of the finding
            finding_details: Dictionary of finding details
            severity: Severity level (critical, high, medium, low)
            finding_type: Type of finding (cve, vulnerability, misconfiguration, etc.)
            recipient_email: Email to send to (if email channel enabled)
            channels: List of channels to notify (desktop, email, slack, teams)
        
        Returns:
            Dictionary with channel results: {'desktop': True, 'email': False, ...}
        """
        if not channels:
            channels = ['desktop']
        
        results = {}
        
        for channel in channels:
            if channel == 'desktop':
                results['desktop'] = await self.send_desktop_notification(
                    title=finding_title,
                    message=finding_details.get('description', ''),
                    severity=severity,
                    finding_type=finding_type
                )
            elif channel == 'email' and recipient_email:
                results['email'] = self.send_email_notification(
                    recipient=recipient_email,
                    finding_title=finding_title,
                    finding_details=finding_details,
                    severity=severity
                )
            elif channel == 'slack':
                results['slack'] = await self.send_slack_webhook(
                    finding_title=finding_title,
                    finding_details=finding_details,
                    severity=severity
                )
            elif channel == 'teams':
                results['teams'] = await self.send_teams_webhook(
                    finding_title=finding_title,
                    finding_details=finding_details,
                    severity=severity
                )
        
        return results


# ── Global notification manager instance ──────────────────────────────────────
_notification_manager = None

def get_notification_manager() -> NotificationManager:
    """Get or create the global notification manager instance."""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager
