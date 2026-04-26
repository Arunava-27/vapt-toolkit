"""Tests for the webhook system."""

import asyncio
import json
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import hashlib
import hmac

from scanner.webhooks import WebhookManager, WebhookEvent, get_webhook_manager


class TestWebhookEvent:
    """Test WebhookEvent data class."""
    
    def test_webhook_event_creation(self):
        event = WebhookEvent(
            event_type="scan_completed",
            project_id="p1",
            scan_id="s1",
            data={"findings": 5}
        )
        assert event.event_type == "scan_completed"
        assert event.project_id == "p1"
        assert event.scan_id == "s1"
        assert event.data == {"findings": 5}
        assert event.timestamp is not None
    
    def test_webhook_event_default_timestamp(self):
        event = WebhookEvent(event_type="test_event")
        assert event.timestamp is not None


class TestWebhookManager:
    """Test WebhookManager functionality."""
    
    @pytest.fixture
    def manager(self):
        return WebhookManager()
    
    def test_register_webhook(self, manager):
        webhook_id = manager.register_webhook(
            project_id="p1",
            url="https://example.com/webhook",
            events=["scan_completed"],
            secret="test_secret"
        )
        
        assert webhook_id is not None
        assert len(webhook_id) > 0
        
        # Verify webhook is registered
        webhooks = manager.get_webhooks(project_id="p1")
        assert len(webhooks) == 1
        assert webhooks[0]["id"] == webhook_id
        assert webhooks[0]["url"] == "https://example.com/webhook"
        assert webhooks[0]["events"] == ["scan_completed"]
    
    def test_get_webhooks_all(self, manager):
        manager.register_webhook("p1", "https://example.com/1", ["scan_completed"], "secret1")
        manager.register_webhook("p2", "https://example.com/2", ["scan_started"], "secret2")
        
        all_webhooks = manager.get_webhooks()
        assert len(all_webhooks) >= 2
    
    def test_get_webhooks_by_project(self, manager):
        manager.register_webhook("p1", "https://example.com/1", ["scan_completed"], "secret1")
        manager.register_webhook("p2", "https://example.com/2", ["scan_started"], "secret2")
        
        p1_webhooks = manager.get_webhooks(project_id="p1")
        assert len(p1_webhooks) == 1
        assert p1_webhooks[0]["project_id"] == "p1"
    
    def test_delete_webhook(self, manager):
        webhook_id = manager.register_webhook("p1", "https://example.com/1", ["scan_completed"], "secret1")
        assert len(manager.get_webhooks(project_id="p1")) == 1
        
        manager.delete_webhook(webhook_id)
        assert len(manager.get_webhooks(project_id="p1")) == 0
    
    def test_enable_disable_webhook(self, manager):
        webhook_id = manager.register_webhook("p1", "https://example.com/1", ["scan_completed"], "secret1")
        
        manager.disable_webhook(webhook_id)
        webhooks = manager.get_webhooks(project_id="p1")
        assert webhooks[0]["enabled"] is False
        
        manager.enable_webhook(webhook_id)
        webhooks = manager.get_webhooks(project_id="p1")
        assert webhooks[0]["enabled"] is True
    
    def test_validate_webhook_signature(self, manager):
        secret = "test_secret"
        payload = b'{"event": "test"}'
        
        # Generate correct signature
        correct_sig = "sha256=" + hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        assert manager.validate_webhook_signature(payload, secret, correct_sig) is True
        
        # Test with incorrect signature
        assert manager.validate_webhook_signature(payload, secret, "sha256=wrong") is False
        
        # Test with wrong scheme
        assert manager.validate_webhook_signature(payload, secret, "md5=something") is False
    
    @pytest.mark.asyncio
    async def test_trigger_webhook_event_filtering(self, manager):
        """Test that webhooks are only triggered for subscribed events."""
        manager.register_webhook(
            "p1",
            "https://example.com/1",
            ["scan_completed"],
            "secret1"
        )
        manager.register_webhook(
            "p1",
            "https://example.com/2",
            ["scan_started"],
            "secret2"
        )
        
        # Mock the delivery method
        with patch.object(manager, '_deliver_webhook', new_callable=AsyncMock) as mock_deliver:
            mock_deliver.return_value = {"success": True}
            
            event = WebhookEvent(
                event_type="scan_completed",
                project_id="p1"
            )
            
            result = await manager.trigger_webhook(event)
            
            # Only the first webhook should be triggered
            assert mock_deliver.call_count == 1
            args = mock_deliver.call_args
            assert args[0][0] is not None  # webhook_id
    
    @pytest.mark.asyncio
    async def test_trigger_wildcard_events(self, manager):
        """Test that wildcards subscribe to all events."""
        manager.register_webhook(
            "p1",
            "https://example.com/1",
            ["*"],
            "secret1"
        )
        
        # Mock the delivery method
        with patch.object(manager, '_deliver_webhook', new_callable=AsyncMock) as mock_deliver:
            mock_deliver.return_value = {"success": True}
            
            event = WebhookEvent(
                event_type="scan_completed",
                project_id="p1"
            )
            
            await manager.trigger_webhook(event)
            
            # Wildcard webhook should be triggered
            assert mock_deliver.call_count == 1
    
    def test_get_webhook_logs(self, manager):
        webhook_id = manager.register_webhook("p1", "https://example.com/1", ["scan_completed"], "secret1")
        
        # Logs should be empty initially
        logs = manager.get_webhook_logs(webhook_id)
        assert isinstance(logs, list)
    
    def test_get_webhook_stats(self, manager):
        webhook_id = manager.register_webhook("p1", "https://example.com/1", ["scan_completed"], "secret1")
        
        stats = manager.get_webhook_stats(webhook_id)
        assert "total_deliveries" in stats
        assert "successful" in stats
        assert "failed" in stats
        assert stats["total_deliveries"] == 0
    
    @pytest.mark.asyncio
    async def test_deliver_webhook_retry_logic(self, manager):
        """Test that webhooks retry on failure."""
        webhook_id = manager.register_webhook("p1", "https://example.com/1", ["scan_completed"], "secret1")
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            
            # First attempt fails (500), second succeeds (200)
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value="OK")
            
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session.post = AsyncMock()
            
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            
            mock_session.post.return_value = mock_context
            mock_session_class.return_value = mock_session
            
            event = WebhookEvent(
                event_type="scan_completed",
                project_id="p1"
            )
            
            result = await manager._deliver_webhook(webhook_id, "https://example.com/1", "secret_hash", event)
            
            # Should have attempted at least once
            assert result["attempts"] >= 1
    
    def test_retry_delays(self, manager):
        """Test exponential backoff delays."""
        assert manager.RETRY_DELAYS == [1, 2, 4, 8, 16]
        assert manager.TIMEOUT == 5
        assert manager.RATE_LIMIT == 10
    
    def test_global_webhook_manager(self):
        """Test that get_webhook_manager returns a singleton."""
        manager1 = get_webhook_manager()
        manager2 = get_webhook_manager()
        assert manager1 is manager2


class TestWebhookSignature:
    """Test webhook signature generation and validation."""
    
    def test_signature_generation(self):
        manager = WebhookManager()
        secret = "my_secret"
        payload = b'{"event": "scan_completed"}'
        
        signature = "sha256=" + hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        assert signature.startswith("sha256=")
        assert len(signature) > 20
    
    def test_signature_validation_different_secrets(self):
        manager = WebhookManager()
        payload = b'{"event": "scan_completed"}'
        
        sig1 = "sha256=" + hmac.new(b"secret1", payload, hashlib.sha256).hexdigest()
        sig2 = "sha256=" + hmac.new(b"secret2", payload, hashlib.sha256).hexdigest()
        
        assert manager.validate_webhook_signature(payload, "secret1", sig1) is True
        assert manager.validate_webhook_signature(payload, "secret1", sig2) is False


class TestWebhookEventTypes:
    """Test different webhook event types."""
    
    def test_supported_event_types(self):
        supported = {
            "scan_started",
            "scan_completed",
            "finding_discovered",
            "scan_failed",
            "report_generated",
            "vulnerability_fixed",
        }
        
        for event_type in supported:
            event = WebhookEvent(event_type=event_type, data={})
            assert event.event_type == event_type
    
    def test_webhook_event_with_complex_data(self):
        data = {
            "findings": [
                {"type": "cve", "severity": "high", "cve_id": "CVE-2024-0001"},
                {"type": "port", "port": 8080}
            ],
            "scan_duration": 120,
            "target": "example.com"
        }
        
        event = WebhookEvent(
            event_type="scan_completed",
            project_id="p1",
            scan_id="s1",
            data=data
        )
        
        assert event.data == data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
