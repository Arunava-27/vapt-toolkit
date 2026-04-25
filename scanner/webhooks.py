"""Webhook system for notifying external systems of scan events."""

import asyncio
import hashlib
import hmac
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Optional
import aiohttp
import logging

logger = logging.getLogger(__name__)


@dataclass
class WebhookEvent:
    """Represents a webhook event to be triggered."""
    event_type: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    project_id: Optional[str] = None
    scan_id: Optional[str] = None
    data: dict = field(default_factory=dict)


class WebhookManager:
    """Manages webhook registration, triggering, and delivery."""
    
    # Exponential backoff retry delays (in seconds)
    RETRY_DELAYS = [1, 2, 4, 8, 16]
    TIMEOUT = 5  # seconds
    RATE_LIMIT = 10  # webhooks per second
    
    def __init__(self):
        self.db_connection = None  # Set by server
        self._semaphore = asyncio.Semaphore(self.RATE_LIMIT)
        self._pending_deliveries = []
    
    def register_webhook(self, project_id: str, url: str, events: list, secret: str) -> str:
        """
        Register a webhook for a project.
        
        Args:
            project_id: The project ID
            url: Webhook URL to POST to
            events: List of event types to subscribe to
            secret: Secret for signing payloads
            
        Returns:
            webhook_id: The registered webhook ID
        """
        from database import _conn
        
        webhook_id = str(uuid.uuid4())
        secret_hash = hashlib.sha256(secret.encode()).hexdigest()
        
        with _conn() as c:
            c.execute(
                """
                INSERT INTO webhooks 
                (id, project_id, url, events, secret_hash, enabled, created_at)
                VALUES (?, ?, ?, ?, ?, 1, ?)
                """,
                (
                    webhook_id,
                    project_id,
                    url,
                    json.dumps(events),
                    secret_hash,
                    datetime.now().isoformat()
                )
            )
        
        logger.info(f"Registered webhook {webhook_id} for project {project_id} with events: {events}")
        return webhook_id
    
    def get_webhooks(self, project_id: Optional[str] = None) -> list:
        """
        Get registered webhooks.
        
        Args:
            project_id: Optional filter by project
            
        Returns:
            List of webhook configurations (without secrets)
        """
        from database import _conn
        
        with _conn() as c:
            if project_id:
                rows = c.execute(
                    "SELECT id, project_id, url, events, enabled, created_at, last_triggered FROM webhooks WHERE project_id = ?",
                    (project_id,)
                ).fetchall()
            else:
                rows = c.execute(
                    "SELECT id, project_id, url, events, enabled, created_at, last_triggered FROM webhooks"
                ).fetchall()
        
        return [
            {
                "id": row["id"],
                "project_id": row["project_id"],
                "url": row["url"],
                "events": json.loads(row["events"]),
                "enabled": bool(row["enabled"]),
                "created_at": row["created_at"],
                "last_triggered": row["last_triggered"],
            }
            for row in rows
        ]
    
    def delete_webhook(self, webhook_id: str) -> bool:
        """
        Delete a webhook.
        
        Args:
            webhook_id: The webhook ID to delete
            
        Returns:
            True if successful
        """
        from database import _conn
        
        with _conn() as c:
            c.execute("DELETE FROM webhooks WHERE id = ?", (webhook_id,))
        
        logger.info(f"Deleted webhook {webhook_id}")
        return True
    
    def enable_webhook(self, webhook_id: str) -> bool:
        """Enable a webhook."""
        from database import _conn
        
        with _conn() as c:
            c.execute("UPDATE webhooks SET enabled = 1 WHERE id = ?", (webhook_id,))
        return True
    
    def disable_webhook(self, webhook_id: str) -> bool:
        """Disable a webhook."""
        from database import _conn
        
        with _conn() as c:
            c.execute("UPDATE webhooks SET enabled = 0 WHERE id = ?", (webhook_id,))
        return True
    
    def _get_webhook_secret(self, webhook_id: str) -> Optional[str]:
        """Get the secret for a webhook (for validation)."""
        from database import _conn
        
        with _conn() as c:
            row = c.execute(
                "SELECT secret_hash FROM webhooks WHERE id = ?",
                (webhook_id,)
            ).fetchone()
        return row["secret_hash"] if row else None
    
    def validate_webhook_signature(self, payload: bytes, secret: str, signature: str) -> bool:
        """
        Validate webhook signature.
        
        Args:
            payload: The raw request body
            secret: The webhook secret
            signature: The signature from the header (format: "sha256=...")
            
        Returns:
            True if signature is valid
        """
        if not signature.startswith("sha256="):
            return False
        
        expected_sig = "sha256=" + hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_sig)
    
    async def trigger_webhook(self, event: WebhookEvent) -> dict:
        """
        Trigger webhooks for an event.
        
        Args:
            event: The webhook event
            
        Returns:
            Dictionary with delivery results
        """
        from database import _conn
        
        # Get matching webhooks
        with _conn() as c:
            rows = c.execute(
                "SELECT id, project_id, url, events, secret_hash, enabled FROM webhooks WHERE enabled = 1"
            ).fetchall()
        
        results = {
            "triggered": 0,
            "failed": 0,
            "deliveries": []
        }
        
        for row in rows:
            events = json.loads(row["events"])
            
            # Check if this webhook is subscribed to this event type
            if "*" not in events and event.event_type not in events:
                continue
            
            # Skip if project_id filter doesn't match
            if event.project_id and row["project_id"] != event.project_id:
                continue
            
            # Schedule delivery
            task = asyncio.create_task(
                self._deliver_webhook(
                    row["id"],
                    row["url"],
                    row["secret_hash"],
                    event
                )
            )
            
            results["triggered"] += 1
            self._pending_deliveries.append(task)
        
        # Wait for all deliveries to complete
        if self._pending_deliveries:
            completed = await asyncio.gather(*self._pending_deliveries, return_exceptions=True)
            self._pending_deliveries = []
            
            for result in completed:
                if isinstance(result, dict):
                    results["deliveries"].append(result)
                    if not result.get("success"):
                        results["failed"] += 1
        
        return results
    
    async def _deliver_webhook(self, webhook_id: str, url: str, secret_hash: str, event: WebhookEvent) -> dict:
        """
        Deliver a webhook with retry logic.
        
        Args:
            webhook_id: Webhook ID
            url: Webhook URL
            secret_hash: Secret hash for signing
            event: The event to deliver
            
        Returns:
            Delivery result dictionary
        """
        from database import _conn
        
        # Build payload
        payload = {
            "event": event.event_type,
            "timestamp": event.timestamp,
            "project_id": event.project_id,
            "scan_id": event.scan_id,
            "data": event.data,
        }
        
        payload_json = json.dumps(payload)
        payload_bytes = payload_json.encode()
        
        # Sign payload
        signature = "sha256=" + hmac.new(
            secret_hash.encode(),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            "Content-Type": "application/json",
            "X-VAPT-Signature": signature,
            "X-VAPT-Event": event.event_type,
            "X-VAPT-Delivery": webhook_id,
        }
        
        result = {
            "webhook_id": webhook_id,
            "event": event.event_type,
            "url": url,
            "success": False,
            "status_code": None,
            "response": None,
            "attempts": 0,
        }
        
        async with aiohttp.ClientSession() as session:
            for attempt in range(len(self.RETRY_DELAYS)):
                result["attempts"] = attempt + 1
                
                try:
                    async with self._semaphore:
                        async with session.post(
                            url,
                            data=payload_bytes,
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=self.TIMEOUT)
                        ) as resp:
                            result["status_code"] = resp.status
                            
                            if 200 <= resp.status < 300:
                                result["success"] = True
                                result["response"] = "OK"
                                logger.info(
                                    f"Webhook {webhook_id} delivered successfully to {url} "
                                    f"(attempt {attempt + 1})"
                                )
                                break
                            else:
                                response_text = await resp.text()
                                result["response"] = response_text[:500]  # Truncate long responses
                                
                                if attempt < len(self.RETRY_DELAYS) - 1:
                                    delay = self.RETRY_DELAYS[attempt]
                                    logger.warning(
                                        f"Webhook {webhook_id} delivery failed with status {resp.status}. "
                                        f"Retrying in {delay}s..."
                                    )
                                    await asyncio.sleep(delay)
                                else:
                                    logger.error(
                                        f"Webhook {webhook_id} delivery failed after {attempt + 1} attempts"
                                    )
                
                except asyncio.TimeoutError:
                    result["response"] = "Timeout"
                    if attempt < len(self.RETRY_DELAYS) - 1:
                        delay = self.RETRY_DELAYS[attempt]
                        logger.warning(
                            f"Webhook {webhook_id} timeout. Retrying in {delay}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"Webhook {webhook_id} delivery failed after {attempt + 1} attempts (timeout)"
                        )
                
                except Exception as e:
                    result["response"] = str(e)[:500]
                    if attempt < len(self.RETRY_DELAYS) - 1:
                        delay = self.RETRY_DELAYS[attempt]
                        logger.warning(
                            f"Webhook {webhook_id} error: {e}. Retrying in {delay}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"Webhook {webhook_id} delivery failed after {attempt + 1} attempts: {e}"
                        )
        
        # Log delivery attempt
        with _conn() as c:
            c.execute(
                """
                INSERT INTO webhook_logs
                (id, webhook_id, event, payload, status, response, attempts, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    webhook_id,
                    event.event_type,
                    payload_json,
                    result["status_code"] or "error",
                    result["response"],
                    result["attempts"],
                    datetime.now().isoformat()
                )
            )
            
            # Update last_triggered
            c.execute(
                "UPDATE webhooks SET last_triggered = ? WHERE id = ?",
                (datetime.now().isoformat(), webhook_id)
            )
        
        return result
    
    def get_webhook_logs(self, webhook_id: str, limit: int = 50) -> list:
        """
        Get webhook delivery logs.
        
        Args:
            webhook_id: The webhook ID
            limit: Maximum number of logs to return
            
        Returns:
            List of log entries
        """
        from database import _conn
        
        with _conn() as c:
            rows = c.execute(
                """
                SELECT id, webhook_id, event, payload, status, response, attempts, created_at
                FROM webhook_logs
                WHERE webhook_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (webhook_id, limit)
            ).fetchall()
        
        return [
            {
                "id": row["id"],
                "webhook_id": row["webhook_id"],
                "event": row["event"],
                "payload": json.loads(row["payload"]),
                "status": row["status"],
                "response": row["response"],
                "attempts": row["attempts"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]
    
    def get_webhook_stats(self, webhook_id: str) -> dict:
        """Get statistics for a webhook."""
        from database import _conn
        
        with _conn() as c:
            logs = c.execute(
                """
                SELECT status, COUNT(*) as count
                FROM webhook_logs
                WHERE webhook_id = ?
                GROUP BY status
                """,
                (webhook_id,)
            ).fetchall()
        
        stats = {
            "total_deliveries": sum(row["count"] for row in logs),
            "successful": 0,
            "failed": 0,
            "error": 0,
            "by_status": {}
        }
        
        for row in logs:
            status = row["status"]
            count = row["count"]
            stats["by_status"][status] = count
            
            if 200 <= int(status) < 300:
                stats["successful"] += count
            else:
                stats["failed"] += count
        
        return stats


# Global instance
_webhook_manager = None


def get_webhook_manager() -> WebhookManager:
    """Get or create the global webhook manager instance."""
    global _webhook_manager
    if _webhook_manager is None:
        _webhook_manager = WebhookManager()
    return _webhook_manager
