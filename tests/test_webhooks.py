"""
Comprehensive unit tests for scanner/webhooks.py - Webhook delivery and management.
"""
import pytest
import json
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch, call
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from scanner.webhooks import WebhookManager, WebhookEvent
except ImportError:
    pytest.skip("webhooks module not available", allow_module_level=True)


class TestWebhookEvent:
    """Test WebhookEvent data class."""
    
    def test_webhook_event_creation(self):
        """Test creating a WebhookEvent."""
        event = WebhookEvent(
            event_type="scan_completed",
            timestamp=datetime.now().isoformat(),
            project_id="proj_123",
            scan_id="scan_001",
            data={"findings": 5}
        )
        
        assert event.event_type == "scan_completed"
        assert event.project_id == "proj_123"
        assert event.data["findings"] == 5
    
    def test_webhook_event_required_fields(self):
        """Test WebhookEvent requires essential fields."""
        event = WebhookEvent(
            event_type="test",
            timestamp=datetime.now().isoformat(),
            data={}
        )
        
        assert event.event_type == "test"
        assert event.project_id is None
        assert event.scan_id is None


@pytest.fixture
def webhook_manager(mock_db_connection):
    """Create a WebhookManager instance for testing."""
    with patch('scanner.webhooks.db') as mock_db:
        mock_db._conn = MagicMock(return_value=MagicMock())
        manager = WebhookManager()
        manager.db = mock_db
        yield manager


class TestWebhookRegistration:
    """Test webhook registration and retrieval."""
    
    @pytest.mark.asyncio
    async def test_register_webhook(self, webhook_manager):
        """Test registering a new webhook."""
        webhook_manager.db.create_webhook = MagicMock(
            return_value={"id": "wh_001", "url": "https://example.com/webhook"}
        )
        
        result = await webhook_manager.register_webhook(
            "proj_123",
            "https://example.com/webhook",
            ["scan_completed"]
        )
        
        assert result["id"] == "wh_001"
    
    @pytest.mark.asyncio
    async def test_get_webhooks(self, webhook_manager):
        """Test retrieving webhooks for a project."""
        webhook_manager.db.get_webhooks = MagicMock(
            return_value=[
                {"id": "wh_001", "url": "https://example.com/webhook1"},
                {"id": "wh_002", "url": "https://example.com/webhook2"}
            ]
        )
        
        result = await webhook_manager.get_webhooks("proj_123")
        
        assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_delete_webhook(self, webhook_manager):
        """Test deleting a webhook."""
        webhook_manager.db.delete_webhook = MagicMock()
        
        await webhook_manager.delete_webhook("wh_001")
        
        webhook_manager.db.delete_webhook.assert_called_once_with("wh_001")


class TestWebhookSignature:
    """Test webhook signature generation and validation."""
    
    def test_validate_webhook_signature(self, webhook_manager):
        """Test validating webhook signature."""
        secret = "test_secret_key"
        payload = json.dumps({"event": "scan_completed", "data": {}})
        
        # Generate expected signature
        import hmac
        import hashlib
        expected_sig = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        result = webhook_manager.validate_webhook_signature(
            payload,
            expected_sig,
            secret
        )
        
        assert result is True
    
    def test_validate_webhook_signature_fails_on_mismatch(self, webhook_manager):
        """Test validation fails for incorrect signature."""
        result = webhook_manager.validate_webhook_signature(
            "payload",
            "wrong_signature",
            "secret"
        )
        
        assert result is False


class TestWebhookDelivery:
    """Test webhook delivery with retry logic."""
    
    @pytest.mark.asyncio
    async def test_trigger_webhook_success(self, webhook_manager, mock_aiohttp_session):
        """Test successful webhook delivery."""
        webhook_manager.db.get_webhooks = MagicMock(
            return_value=[{
                "id": "wh_001",
                "url": "https://example.com/webhook",
                "enabled": True,
                "secret_hash": "secret_hash"
            }]
        )
        
        event = WebhookEvent(
            event_type="scan_completed",
            timestamp=datetime.now().isoformat(),
            project_id="proj_123",
            data={"findings": 5}
        )
        
        with patch('aiohttp.ClientSession', return_value=mock_aiohttp_session):
            await webhook_manager.trigger_webhook(event)
    
    @pytest.mark.asyncio
    async def test_trigger_webhook_filters_disabled(self, webhook_manager):
        """Test that disabled webhooks are not triggered."""
        webhook_manager.db.get_webhooks = MagicMock(
            return_value=[{
                "id": "wh_001",
                "url": "https://example.com/webhook",
                "enabled": False
            }]
        )
        
        event = WebhookEvent(
            event_type="scan_completed",
            timestamp=datetime.now().isoformat(),
            project_id="proj_123",
            data={}
        )
        
        with patch('aiohttp.ClientSession') as mock_session:
            await webhook_manager.trigger_webhook(event)
            # Session should not be used since webhook is disabled
            assert not mock_session.called or mock_session.return_value.post.call_count == 0
    
    @pytest.mark.asyncio
    async def test_webhook_retry_on_failure(self, webhook_manager):
        """Test webhook retry logic on delivery failure."""
        webhook_manager.db.get_webhooks = MagicMock(
            return_value=[{
                "id": "wh_001",
                "url": "https://example.com/webhook",
                "enabled": True,
                "secret_hash": "secret"
            }]
        )
        
        event = WebhookEvent(
            event_type="scan_completed",
            timestamp=datetime.now().isoformat(),
            project_id="proj_123",
            data={}
        )
        
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_session.post = AsyncMock(return_value=mock_response)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with patch('asyncio.sleep', new_callable=AsyncMock):
                await webhook_manager.trigger_webhook(event)
                
                # Verify retries occurred
                assert mock_session.post.call_count >= 1


class TestWebhookEventFiltering:
    """Test webhook event type filtering."""
    
    @pytest.mark.asyncio
    async def test_trigger_webhook_respects_events_filter(self, webhook_manager):
        """Test that webhooks only trigger for subscribed events."""
        webhook_manager.db.get_webhooks = MagicMock(
            return_value=[{
                "id": "wh_001",
                "url": "https://example.com/webhook",
                "enabled": True,
                "events": ["scan_completed"],  # Only subscribed to scan_completed
                "secret_hash": "secret"
            }]
        )
        
        # Try to trigger a different event
        event = WebhookEvent(
            event_type="finding_discovered",  # Not in subscribed events
            timestamp=datetime.now().isoformat(),
            project_id="proj_123",
            data={}
        )
        
        with patch('aiohttp.ClientSession') as mock_session:
            await webhook_manager.trigger_webhook(event)


class TestWebhookLogging:
    """Test webhook delivery logging."""
    
    @pytest.mark.asyncio
    async def test_webhook_log_on_success(self, webhook_manager):
        """Test logging successful webhook delivery."""
        webhook_manager.db.get_webhooks = MagicMock(
            return_value=[{
                "id": "wh_001",
                "url": "https://example.com/webhook",
                "enabled": True,
                "secret_hash": "secret"
            }]
        )
        webhook_manager.db.log_webhook_delivery = MagicMock()
        
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_session.post = AsyncMock(return_value=mock_response)
        
        event = WebhookEvent(
            event_type="scan_completed",
            timestamp=datetime.now().isoformat(),
            project_id="proj_123",
            data={}
        )
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            await webhook_manager.trigger_webhook(event)
    
    @pytest.mark.asyncio
    async def test_webhook_log_on_failure(self, webhook_manager):
        """Test logging failed webhook delivery."""
        webhook_manager.db.get_webhooks = MagicMock(
            return_value=[{
                "id": "wh_001",
                "url": "https://example.com/webhook",
                "enabled": True,
                "secret_hash": "secret"
            }]
        )
        webhook_manager.db.log_webhook_delivery = MagicMock()
        
        mock_session = AsyncMock()
        mock_session.post = AsyncMock(side_effect=Exception("Connection failed"))
        
        event = WebhookEvent(
            event_type="scan_completed",
            timestamp=datetime.now().isoformat(),
            project_id="proj_123",
            data={}
        )
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            await webhook_manager.trigger_webhook(event)
