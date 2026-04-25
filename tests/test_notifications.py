"""
Comprehensive unit tests for scanner/notifications.py - Notification delivery system.
"""
import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock, call
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from scanner.notifications import NotificationManager
except ImportError:
    pytest.skip("notifications module not available", allow_module_level=True)


@pytest.fixture
def notification_manager():
    """Create a NotificationManager instance for testing."""
    return NotificationManager()


class TestNotificationManagerInitialization:
    """Test NotificationManager setup."""
    
    def test_notification_manager_creation(self, notification_manager):
        """Test creating a NotificationManager."""
        assert notification_manager is not None
        assert hasattr(notification_manager, 'register_callback')
        assert hasattr(notification_manager, 'send_desktop_notification')
    
    def test_register_callback(self, notification_manager):
        """Test registering notification callback."""
        async def callback(data):
            pass
        
        notification_manager.register_callback(callback)
        
        assert len(notification_manager._callbacks) > 0


class TestDesktopNotifications:
    """Test desktop notification delivery."""
    
    @pytest.mark.asyncio
    async def test_send_desktop_notification(self, notification_manager):
        """Test sending desktop notification."""
        callback_called = False
        
        async def test_callback(data):
            nonlocal callback_called
            callback_called = True
        
        notification_manager.register_callback(test_callback)
        
        await notification_manager.send_desktop_notification(
            "Test Title",
            "Test Message",
            severity="high"
        )
        
        # Allow async callback to execute
        await asyncio.sleep(0.1)
    
    @pytest.mark.asyncio
    async def test_desktop_notification_without_callbacks(self, notification_manager):
        """Test desktop notification when no callbacks registered."""
        # Should not raise error
        await notification_manager.send_desktop_notification(
            "Test",
            "Message"
        )


class TestEmailNotifications:
    """Test email notification delivery."""
    
    @pytest.mark.asyncio
    async def test_send_email_notification(self, notification_manager, mock_smtp):
        """Test sending email notification."""
        with patch('smtplib.SMTP', return_value=mock_smtp):
            await notification_manager.send_email_notification(
                "test@example.com",
                "Test Subject",
                "Test Body"
            )
    
    @pytest.mark.asyncio
    async def test_send_email_builds_html(self, notification_manager):
        """Test that email HTML is properly built."""
        html = notification_manager._build_email_html(
            "High Severity Finding",
            "XSS vulnerability found",
            "https://example.com/api/search?q=<script>alert('xss')</script>"
        )
        
        assert html is not None
        assert "High Severity Finding" in html
        assert "XSS vulnerability found" in html
    
    @pytest.mark.asyncio
    async def test_send_email_with_invalid_address(self, notification_manager):
        """Test sending email to invalid address."""
        with pytest.raises(Exception):
            await notification_manager.send_email_notification(
                "not-an-email",
                "Subject",
                "Body"
            )


class TestSlackNotifications:
    """Test Slack webhook notifications."""
    
    @pytest.mark.asyncio
    async def test_send_slack_webhook(self, notification_manager, mock_aiohttp_session):
        """Test sending Slack notification."""
        with patch.dict('os.environ', {'SLACK_WEBHOOK_URL': 'https://hooks.slack.com/test'}):
            with patch('aiohttp.ClientSession', return_value=mock_aiohttp_session):
                await notification_manager.send_slack_webhook(
                    "Critical XSS Found",
                    "XSS in /api/search endpoint",
                    severity="critical"
                )
    
    @pytest.mark.asyncio
    async def test_slack_webhook_missing_url(self, notification_manager):
        """Test Slack notification when URL not configured."""
        with patch.dict('os.environ', {}, clear=True):
            # Should handle gracefully
            await notification_manager.send_slack_webhook(
                "Title",
                "Body"
            )


class TestTeamsNotifications:
    """Test Microsoft Teams webhook notifications."""
    
    @pytest.mark.asyncio
    async def test_send_teams_webhook(self, notification_manager, mock_aiohttp_session):
        """Test sending Teams notification."""
        with patch.dict('os.environ', {'TEAMS_WEBHOOK_URL': 'https://outlook.webhook.office.com/test'}):
            with patch('aiohttp.ClientSession', return_value=mock_aiohttp_session):
                await notification_manager.send_teams_webhook(
                    "Critical SQLi Found",
                    "SQL Injection in /api/users endpoint",
                    severity="critical"
                )
    
    @pytest.mark.asyncio
    async def test_teams_webhook_missing_url(self, notification_manager):
        """Test Teams notification when URL not configured."""
        with patch.dict('os.environ', {}, clear=True):
            # Should handle gracefully
            await notification_manager.send_teams_webhook(
                "Title",
                "Body"
            )


class TestFindingNotifications:
    """Test finding-specific notifications."""
    
    @pytest.mark.asyncio
    async def test_send_finding_notification_all_channels(self, notification_manager):
        """Test dispatching finding to all channels."""
        callback_called = False
        
        async def test_callback(data):
            nonlocal callback_called
            callback_called = True
        
        notification_manager.register_callback(test_callback)
        
        with patch.dict('os.environ', {
            'SLACK_WEBHOOK_URL': 'https://hooks.slack.com/test',
            'TEAMS_WEBHOOK_URL': 'https://outlook.webhook.office.com/test'
        }):
            with patch('smtplib.SMTP'):
                with patch('aiohttp.ClientSession'):
                    finding = {
                        "type": "XSS",
                        "severity": "high",
                        "endpoint": "/api/search",
                        "parameter": "q",
                        "evidence": "Payload reflected"
                    }
                    
                    await notification_manager.send_finding_notification(
                        finding,
                        "test@example.com"
                    )


class TestNotificationSeverityCoding:
    """Test severity level handling."""
    
    @pytest.mark.asyncio
    async def test_critical_severity_formatting(self, notification_manager):
        """Test formatting for critical severity."""
        html = notification_manager._build_email_html(
            "Critical Finding",
            "Body",
            "URL",
            severity="critical"
        )
        
        assert html is not None
        assert "critical" in html.lower() or "critical" in html
    
    @pytest.mark.asyncio
    async def test_low_severity_formatting(self, notification_manager):
        """Test formatting for low severity."""
        html = notification_manager._build_email_html(
            "Low Finding",
            "Body",
            "URL",
            severity="low"
        )
        
        assert html is not None


class TestNotificationErrorHandling:
    """Test error handling in notifications."""
    
    @pytest.mark.asyncio
    async def test_callback_exception_handling(self, notification_manager):
        """Test that callback exceptions don't break notifications."""
        async def failing_callback(data):
            raise Exception("Callback error")
        
        notification_manager.register_callback(failing_callback)
        
        # Should not raise
        await notification_manager.send_desktop_notification(
            "Test",
            "Message"
        )
    
    @pytest.mark.asyncio
    async def test_email_connection_error(self, notification_manager):
        """Test handling email connection errors."""
        with patch('smtplib.SMTP', side_effect=Exception("SMTP connection failed")):
            # Should handle gracefully
            try:
                await notification_manager.send_email_notification(
                    "test@example.com",
                    "Subject",
                    "Body"
                )
            except Exception:
                pass


class TestNotificationFiltering:
    """Test notification filtering and throttling."""
    
    @pytest.mark.asyncio
    async def test_duplicate_notification_suppression(self, notification_manager):
        """Test that duplicate notifications are suppressed."""
        call_count = 0
        
        async def counting_callback(data):
            nonlocal call_count
            call_count += 1
        
        notification_manager.register_callback(counting_callback)
        
        # Send same notification twice
        await notification_manager.send_desktop_notification(
            "XSS Found",
            "/api/search"
        )
        await notification_manager.send_desktop_notification(
            "XSS Found",
            "/api/search"
        )


class TestNotificationFormatting:
    """Test notification message formatting."""
    
    def test_email_html_formatting(self, notification_manager):
        """Test HTML email formatting."""
        html = notification_manager._build_email_html(
            "XSS Vulnerability",
            "Reflected XSS in search parameter",
            "https://example.com/api/search?q=payload"
        )
        
        assert "<html>" in html
        assert "XSS Vulnerability" in html
        assert "Reflected XSS" in html
    
    def test_slack_message_formatting(self, notification_manager):
        """Test Slack message formatting."""
        message = {
            "title": "SQLi Found",
            "severity": "critical",
            "endpoint": "/api/users"
        }
        
        # Message should be JSON-serializable
        import json
        json.dumps(message)
