# Webhook System Guide — VAPT Toolkit

## Overview

The VAPT Toolkit webhook system enables real-time notifications to external systems when important events occur during vulnerability scanning. This guide explains how to use webhooks, validate signatures, and integrate with popular services.

---

## Quick Start

### 1. Register a Webhook

Use the API to register a webhook for your project:

```bash
curl -X POST https://your-vapt-server/api/webhooks \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-webhook-endpoint.com/events",
    "events": ["scan_completed", "scan_failed"],
    "secret": "your-webhook-secret-key"
  }'
```

**Response:**
```json
{
  "id": "wh_abc123",
  "project_id": "p_xyz789",
  "url": "https://your-webhook-endpoint.com/events",
  "events": ["scan_completed", "scan_failed"],
  "enabled": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### 2. Receive Webhook Events

Your endpoint will receive POST requests with the following structure:

```json
{
  "event": "scan_completed",
  "timestamp": "2024-01-15T10:35:45Z",
  "project_id": "p_xyz789",
  "scan_id": "s_scan123",
  "data": {
    "target": "example.com",
    "scan_type": "active",
    "results_summary": {
      "cves": 5,
      "ports": 3,
      "subdomains": 12,
      "web_vulns": 2
    }
  },
  "signature": "sha256=abc123def456..."
}
```

### 3. Validate Signatures

Verify the webhook signature to ensure the request came from VAPT:

```python
import hmac
import hashlib

def validate_webhook_signature(request_body, secret, signature_header):
    """Validate VAPT webhook signature."""
    expected_sig = "sha256=" + hmac.new(
        secret.encode(),
        request_body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature_header, expected_sig)

# In your webhook handler:
signature = request.headers.get("X-VAPT-Signature")
if not validate_webhook_signature(request.body, secret, signature):
    return {"error": "Invalid signature"}, 401
```

---

## Event Types

### `scan_started`
Triggered when a scan begins.

**Data:**
```json
{
  "event": "scan_started",
  "project_id": "p_xyz789",
  "scan_id": "s_scan123",
  "data": {
    "target": "example.com",
    "scan_type": "active"
  }
}
```

### `scan_completed`
Triggered when a scan finishes successfully.

**Data:**
```json
{
  "event": "scan_completed",
  "project_id": "p_xyz789",
  "scan_id": "s_scan123",
  "data": {
    "target": "example.com",
    "scan_type": "active",
    "results_summary": {
      "cves": 5,
      "ports": 3,
      "subdomains": 12,
      "web_vulns": 2
    }
  }
}
```

### `scan_failed`
Triggered when a scan encounters an error.

**Data:**
```json
{
  "event": "scan_failed",
  "project_id": "p_xyz789",
  "scan_id": "s_scan123",
  "data": {
    "target": "example.com",
    "error": "Timeout during port scan",
    "scan_type": "active"
  }
}
```

### `finding_discovered`
Triggered when a high-severity finding is discovered (planned).

**Data:**
```json
{
  "event": "finding_discovered",
  "project_id": "p_xyz789",
  "scan_id": "s_scan123",
  "data": {
    "type": "cve",
    "severity": "critical",
    "cve_id": "CVE-2024-0001",
    "description": "...",
    "target": "example.com"
  }
}
```

### `report_generated`
Triggered when a report is generated (planned).

### `vulnerability_fixed`
Triggered in comparison mode when a vulnerability is fixed (planned).

---

## API Endpoints

### List Webhooks

```bash
GET /api/webhooks
Authorization: Bearer YOUR_API_KEY
```

**Response:**
```json
[
  {
    "id": "wh_abc123",
    "url": "https://example.com/webhook",
    "events": ["scan_completed"],
    "enabled": true,
    "created_at": "2024-01-15T10:30:00Z",
    "last_triggered": "2024-01-15T10:35:00Z"
  }
]
```

### Get Webhook Logs

```bash
GET /api/webhooks/{webhook_id}/logs?limit=50
Authorization: Bearer YOUR_API_KEY
```

**Response:**
```json
{
  "logs": [
    {
      "id": "log_123",
      "webhook_id": "wh_abc123",
      "event": "scan_completed",
      "payload": { ... },
      "status": 200,
      "response": "OK",
      "attempts": 1,
      "created_at": "2024-01-15T10:35:00Z"
    }
  ],
  "stats": {
    "total_deliveries": 45,
    "successful": 43,
    "failed": 2,
    "by_status": {
      "200": 43,
      "500": 2
    }
  }
}
```

### Enable Webhook

```bash
POST /api/webhooks/{webhook_id}/enable
Authorization: Bearer YOUR_API_KEY
```

### Disable Webhook

```bash
POST /api/webhooks/{webhook_id}/disable
Authorization: Bearer YOUR_API_KEY
```

### Delete Webhook

```bash
DELETE /api/webhooks/{webhook_id}
Authorization: Bearer YOUR_API_KEY
```

### Test Webhook

```bash
POST /api/webhooks/test
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json

{
  "webhook_id": "wh_abc123",
  "event_type": "test_event"
}
```

---

## Integration Examples

### Slack

```python
import hmac
import hashlib
import json
from flask import Flask, request

app = Flask(__name__)
WEBHOOK_SECRET = "your-secret-key"
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

def validate_vapt_signature(req):
    """Validate VAPT webhook signature."""
    sig = req.headers.get("X-VAPT-Signature")
    expected = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode(),
        req.data,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(sig, expected)

@app.route("/vapt-webhook", methods=["POST"])
def handle_vapt_webhook():
    if not validate_vapt_signature(request):
        return {"error": "Invalid signature"}, 401
    
    data = request.json
    event = data["event"]
    
    if event == "scan_completed":
        summary = data["data"]["results_summary"]
        message = f"""
        🎯 VAPT Scan Completed
        Target: {data["data"]["target"]}
        CVEs Found: {summary["cves"]}
        Open Ports: {summary["ports"]}
        Subdomains: {summary["subdomains"]}
        Web Vulns: {summary["web_vulns"]}
        """
    elif event == "scan_failed":
        message = f"""
        ❌ VAPT Scan Failed
        Target: {data["data"]["target"]}
        Error: {data["data"]["error"]}
        """
    else:
        message = f"🔔 VAPT Event: {event}"
    
    # Send to Slack
    requests.post(SLACK_WEBHOOK_URL, json={
        "text": message
    })
    
    return {"ok": True}

if __name__ == "__main__":
    app.run(port=5000)
```

### GitHub

Automatically create issues when high-severity findings are discovered:

```python
import hmac
import hashlib
import requests
from flask import Flask, request

app = Flask(__name__)
WEBHOOK_SECRET = "your-secret-key"
GITHUB_TOKEN = "your-github-token"
GITHUB_REPO = "owner/repo"

@app.route("/vapt-github-webhook", methods=["POST"])
def handle_github_webhook():
    sig = request.headers.get("X-VAPT-Signature")
    expected = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode(),
        request.data,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(sig, expected):
        return {"error": "Invalid signature"}, 401
    
    data = request.json
    
    if data["event"] == "scan_completed":
        summary = data["data"]["results_summary"]
        
        if summary["cves"] > 0 or summary["web_vulns"] > 0:
            issue_title = f"Security Scan: {summary['cves']} CVEs found on {data['data']['target']}"
            issue_body = f"""
## Security Scan Results

**Target:** {data['data']['target']}
**Scan Type:** {data['data']['scan_type']}

### Findings
- CVEs: {summary['cves']}
- Open Ports: {summary['ports']}
- Subdomains: {summary['subdomains']}
- Web Vulnerabilities: {summary['web_vulns']}

[View scan in VAPT](/projects/{data['project_id']})
            """
            
            response = requests.post(
                f"https://api.github.com/repos/{GITHUB_REPO}/issues",
                headers={
                    "Authorization": f"token {GITHUB_TOKEN}",
                    "Accept": "application/vnd.github.v3+json"
                },
                json={
                    "title": issue_title,
                    "body": issue_body,
                    "labels": ["security", "vapt-scan"]
                }
            )
            
            return {"ok": True, "issue": response.json()["html_url"]}
    
    return {"ok": True}
```

### Email Notifications

Send email alerts for critical findings:

```python
import hmac
import hashlib
import smtplib
from email.mime.text import MIMEText
from flask import Flask, request

app = Flask(__name__)
WEBHOOK_SECRET = "your-secret-key"
SMTP_CONFIG = {
    "server": "smtp.gmail.com",
    "port": 587,
    "username": "your-email@gmail.com",
    "password": "your-app-password"
}

@app.route("/vapt-email-webhook", methods=["POST"])
def handle_email_webhook():
    sig = request.headers.get("X-VAPT-Signature")
    expected = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode(),
        request.data,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(sig, expected):
        return {"error": "Invalid signature"}, 401
    
    data = request.json
    
    if data["event"] in ["scan_completed", "scan_failed"]:
        summary = data["data"].get("results_summary", {})
        
        subject = f"VAPT Scan Alert: {data['data']['target']}"
        body = f"""
VAPT Scan Report

Target: {data['data']['target']}
Status: {'✓ Completed' if data['event'] == 'scan_completed' else '✗ Failed'}
Scan Type: {data['data']['scan_type']}

{'Findings:' if data['event'] == 'scan_completed' else 'Error:'}
{json.dumps(summary or data['data'].get('error'), indent=2)}

Review this scan in VAPT Dashboard
        """
        
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = SMTP_CONFIG["username"]
        msg["To"] = "security-team@example.com"
        
        with smtplib.SMTP(SMTP_CONFIG["server"], SMTP_CONFIG["port"]) as server:
            server.starttls()
            server.login(SMTP_CONFIG["username"], SMTP_CONFIG["password"])
            server.send_message(msg)
        
        return {"ok": True}
    
    return {"ok": True}
```

---

## Retry Logic

If webhook delivery fails, VAPT automatically retries with exponential backoff:

- **Attempt 1:** Immediate
- **Attempt 2:** 1 second delay
- **Attempt 3:** 2 seconds delay
- **Attempt 4:** 4 seconds delay
- **Attempt 5:** 8 seconds delay
- **Attempt 6:** 16 seconds delay

Total retry window: ~30 seconds

**Retryable failures:**
- Timeout (5 second limit)
- 5xx server errors
- Network errors

**Non-retryable failures:**
- 4xx client errors (400, 401, 403, 404, etc.)
- Request cancellation

---

## Security Best Practices

### 1. Always Validate Signatures

Never trust webhooks without validating the signature header:

```python
def validate_signature(payload, secret, signature):
    """Validate webhook signature."""
    expected = "sha256=" + hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)
```

### 2. Keep Secrets Secure

- Store webhook secrets in environment variables, not in code
- Rotate secrets regularly
- Never commit secrets to version control

### 3. Use HTTPS Only

Always register webhooks with HTTPS endpoints. Avoid HTTP.

### 4. Verify Timestamps

Check the `timestamp` field in webhook payloads to prevent replay attacks:

```python
from datetime import datetime, timedelta

def check_timestamp(webhook_timestamp):
    """Ensure webhook is recent (within 5 minutes)."""
    webhook_time = datetime.fromisoformat(webhook_timestamp)
    now = datetime.utcnow()
    
    if abs((now - webhook_time).total_seconds()) > 300:
        raise ValueError("Webhook timestamp too old")
```

### 5. Implement Idempotency

Use the webhook ID to detect and prevent duplicate processing:

```python
# Store processed webhook IDs in a database
processed_ids = set()

@app.route("/webhook", methods=["POST"])
def handle_webhook():
    data = request.json
    
    if data["id"] in processed_ids:
        return {"ok": True}  # Already processed
    
    # Process the webhook
    process_event(data)
    
    # Mark as processed
    processed_ids.add(data["id"])
    
    return {"ok": True}
```

---

## Troubleshooting

### Webhook Not Being Triggered

1. **Check webhook is enabled:**
   ```bash
   curl https://your-vapt-server/api/webhooks \
     -H "Authorization: Bearer YOUR_API_KEY"
   ```

2. **Verify event subscription:**
   - Make sure webhook is subscribed to the correct event
   - Use `"*"` to subscribe to all events

3. **Check webhook logs:**
   ```bash
   curl https://your-vapt-server/api/webhooks/{webhook_id}/logs \
     -H "Authorization: Bearer YOUR_API_KEY"
   ```

### Signature Validation Failing

1. **Use raw request body:**
   - Validate against the raw HTTP body, not the parsed JSON
   - Some frameworks parse the body, making validation fail

2. **Check secret is correct:**
   - Verify the secret used matches the one registered
   - Secrets are case-sensitive

3. **Sample Python validation:**
   ```python
   # Get raw body BEFORE Flask parses it
   raw_body = request.get_data()
   signature = request.headers.get("X-VAPT-Signature")
   expected = "sha256=" + hmac.new(
       SECRET.encode(),
       raw_body,
       hashlib.sha256
   ).hexdigest()
   ```

### High Failure Rate

1. **Check endpoint availability:**
   - Webhook must respond with 2xx status within 5 seconds
   - Ensure endpoint is publicly accessible

2. **Monitor logs:**
   - Review webhook delivery logs for specific errors
   - Check application logs for any issues

3. **Increase endpoint timeout:**
   - VAPT has a 5 second timeout
   - Ensure your endpoint responds quickly

---

## Rate Limiting

- **Webhook Registration:** 10 webhooks per second per project
- **Webhook Triggers:** Unlimited (depends on scan activity)
- **Log Retention:** Latest 500 deliveries per webhook

---

## Example: Complete Flask App

```python
import hmac
import hashlib
import json
from flask import Flask, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

# Configuration
VAPT_WEBHOOK_SECRET = "your-webhook-secret"
PROCESSED_WEBHOOKS = {}  # In production, use a database

def validate_webhook_signature(payload, secret, signature):
    """Validate VAPT webhook signature."""
    expected = "sha256=" + hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)

def is_webhook_recent(timestamp_str):
    """Check if webhook is within acceptable time window."""
    webhook_time = datetime.fromisoformat(timestamp_str)
    now = datetime.utcnow()
    return abs((now - webhook_time).total_seconds()) <= 300

@app.route("/vapt-webhook", methods=["POST"])
def handle_vapt_webhook():
    """Handle VAPT webhook events."""
    
    # Validate signature
    signature = request.headers.get("X-VAPT-Signature")
    if not signature or not validate_webhook_signature(request.data, VAPT_WEBHOOK_SECRET, signature):
        return jsonify({"error": "Invalid signature"}), 401
    
    data = request.json
    
    # Validate timestamp
    if not is_webhook_recent(data["timestamp"]):
        return jsonify({"error": "Webhook too old"}), 400
    
    # Check for duplicates (idempotency)
    webhook_id = f"{data.get('scan_id')}_{data.get('event')}_{data['timestamp']}"
    if webhook_id in PROCESSED_WEBHOOKS:
        return jsonify({"ok": True, "cached": True}), 200
    
    # Process based on event type
    try:
        if data["event"] == "scan_completed":
            handle_scan_completed(data)
        elif data["event"] == "scan_failed":
            handle_scan_failed(data)
        elif data["event"] == "finding_discovered":
            handle_finding_discovered(data)
        
        # Mark as processed
        PROCESSED_WEBHOOKS[webhook_id] = datetime.utcnow()
        
        return jsonify({"ok": True}), 200
        
    except Exception as e:
        app.logger.error(f"Error processing webhook: {e}")
        return jsonify({"error": "Processing failed"}), 500

def handle_scan_completed(data):
    """Handle scan completion."""
    print(f"Scan completed for {data['data']['target']}")
    summary = data["data"]["results_summary"]
    print(f"  CVEs: {summary['cves']}")
    print(f"  Ports: {summary['ports']}")
    print(f"  Web Vulns: {summary['web_vulns']}")

def handle_scan_failed(data):
    """Handle scan failure."""
    print(f"Scan failed for {data['data']['target']}")
    print(f"  Error: {data['data']['error']}")

def handle_finding_discovered(data):
    """Handle finding discovery."""
    print(f"Finding discovered: {data['data']['type']}")
    print(f"  Severity: {data['data']['severity']}")

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8080)
```

---

## Monitoring

Monitor webhook health using the logs endpoint:

```bash
# Get webhook statistics
curl https://your-vapt-server/api/webhooks/{webhook_id}/logs \
  -H "Authorization: Bearer YOUR_API_KEY" | jq '.stats'

# Output:
# {
#   "total_deliveries": 45,
#   "successful": 43,
#   "failed": 2,
#   "by_status": {
#     "200": 43,
#     "500": 2
#   }
# }
```

---

## Support

For issues or questions:
1. Check webhook logs: `/api/webhooks/{webhook_id}/logs`
2. Review this guide's troubleshooting section
3. Enable debug logging on your webhook endpoint
4. Test with `/api/webhooks/test` endpoint
