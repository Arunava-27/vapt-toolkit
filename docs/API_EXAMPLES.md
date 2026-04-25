# VAPT Toolkit REST API Examples

## Overview

The VAPT Toolkit REST API enables programmatic access to scanning, status tracking, and automation capabilities. All endpoints require API key authentication.

## Authentication

All API endpoints require an `Authorization: Bearer <api_key>` header.

### Generate API Key

First, create an API key for your project:

```bash
curl -X POST http://localhost:8000/api/keys/create \
  -H "Authorization: Bearer YOUR_EXISTING_API_KEY"
```

Response:
```json
{
  "api_key": "vapt_xxxxxxxxxxxx",
  "key_id": "xxxxxxxx",
  "project_id": "proj-123",
  "created_at": "2024-01-15T10:30:00",
  "warning": "Store this key securely. You won't be able to see it again!"
}
```

**⚠️ Important:** Store the `api_key` in a secure location. You won't be able to retrieve it again!

## Rate Limiting

- **Limit:** 100 requests per minute per API key
- **Headers:** Check `X-RateLimit-*` headers in responses
- **Rate Limit Exceeded:** Returns HTTP 429

Check current rate limit status:
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:8000/api/keys/info
```

Response:
```json
{
  "requests_used": 5,
  "requests_limit": 100,
  "requests_remaining": 95,
  "reset_at": "2024-01-15T10:31:00"
}
```

---

## API Endpoints

### 1. Get Scan Status

Get real-time status and progress of a running scan.

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:8000/api/scan/SCAN_ID/status
```

Response:
```json
{
  "scan_id": "scan-123",
  "status": "running",
  "progress": 45,
  "elapsed_time": 120,
  "estimated_remaining": 140,
  "current_phase": "ports",
  "findings_count": 5,
  "message": "Testing port 443 (https)..."
}
```

**Status values:** `running`, `completed`, `failed`, `stopped`

---

### 2. Stop a Running Scan

Gracefully stop a running scan and retrieve current findings.

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:8000/api/scan/SCAN_ID/stop
```

Response:
```json
{
  "status": "stopped",
  "findings": [
    {
      "type": "open_port",
      "severity": "INFO",
      "endpoint": "443/tcp",
      "confidence_score": 100
    }
  ]
}
```

---

### 3. Get Latest Findings

Retrieve latest findings from all scans, with optional filtering.

```bash
# Get all latest findings (limit 10)
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:8000/api/findings/latest

# Filter by severity
curl -H "Authorization: Bearer YOUR_API_KEY" \
  "http://localhost:8000/api/findings/latest?severity=CRITICAL&limit=20"
```

Query Parameters:
- `severity` (optional): `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO`
- `limit` (optional): Max 100, default 10

Response:
```json
[
  {
    "type": "open_port",
    "severity": "INFO",
    "endpoint": "443/tcp",
    "confidence_score": 100,
    "project_id": "proj-123",
    "timestamp": "2024-01-15T10:30:00"
  },
  {
    "type": "cve",
    "severity": "CRITICAL",
    "endpoint": "CVE-2024-1234",
    "confidence_score": 95,
    "project_id": "proj-123",
    "timestamp": "2024-01-15T10:30:00"
  }
]
```

---

### 4. Create Scheduled Scan

Schedule a recurring scan for a project.

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "proj-123",
    "frequency": "daily",
    "time": "09:00"
  }' \
  http://localhost:8000/api/schedule/create
```

Parameters:
- `project_id`: Project to scan
- `frequency`: `daily`, `weekly`, or `monthly`
- `time`: Time in HH:MM format (24-hour)

Response:
```json
{
  "status": "scheduled",
  "project_id": "proj-123",
  "frequency": "daily",
  "time": "09:00",
  "message": "Scan scheduled daily at 09:00"
}
```

---

### 5. Get Complete Scan Results

Retrieve full scan results including all events and findings.

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:8000/api/scan/SCAN_ID/results
```

Response:
```json
{
  "scan_id": "scan-123",
  "status": "completed",
  "target": "example.com",
  "project_id": "proj-123",
  "created_at": "2024-01-15T10:00:00",
  "events": [
    {
      "event": "start",
      "target": "example.com",
      "scan_type": "active"
    },
    {
      "event": "module_start",
      "module": "recon"
    },
    {
      "event": "recon",
      "data": {
        "subdomains": ["www.example.com", "api.example.com"],
        "emails": ["admin@example.com"]
      }
    }
  ]
}
```

---

## API Key Management

### List API Keys

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:8000/api/keys/list
```

Response:
```json
{
  "keys": [
    {
      "id": "xxxxxxxx",
      "created_at": "2024-01-15T10:30:00",
      "last_used": "2024-01-15T10:35:00"
    }
  ]
}
```

### Revoke API Key

```bash
curl -X DELETE \
  -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:8000/api/keys/KEY_ID
```

Response:
```json
{
  "ok": true
}
```

---

## Python SDK Example

```python
import requests
import time

class VAPTClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"}
    
    def get_scan_status(self, scan_id):
        """Get scan status."""
        resp = requests.get(
            f"{self.base_url}/api/scan/{scan_id}/status",
            headers=self.headers
        )
        resp.raise_for_status()
        return resp.json()
    
    def get_latest_findings(self, severity=None, limit=10):
        """Get latest findings."""
        params = {"limit": limit}
        if severity:
            params["severity"] = severity
        resp = requests.get(
            f"{self.base_url}/api/findings/latest",
            headers=self.headers,
            params=params
        )
        resp.raise_for_status()
        return resp.json()
    
    def stop_scan(self, scan_id):
        """Stop a running scan."""
        resp = requests.post(
            f"{self.base_url}/api/scan/{scan_id}/stop",
            headers=self.headers
        )
        resp.raise_for_status()
        return resp.json()
    
    def create_schedule(self, project_id, frequency, time):
        """Create a scheduled scan."""
        resp = requests.post(
            f"{self.base_url}/api/schedule/create",
            headers=self.headers,
            json={
                "project_id": project_id,
                "frequency": frequency,
                "time": time
            }
        )
        resp.raise_for_status()
        return resp.json()

# Usage
client = VAPTClient("http://localhost:8000", "vapt_xxxxxxxxxxxx")

# Poll scan status
while True:
    status = client.get_scan_status("scan-123")
    print(f"Progress: {status['progress']}% ({status['current_phase']})")
    
    if status['status'] != 'running':
        break
    
    time.sleep(5)

# Get findings
findings = client.get_latest_findings(severity="CRITICAL")
print(f"Found {len(findings)} critical findings")
```

---

## JavaScript/Node.js Example

```javascript
class VAPTClient {
  constructor(baseUrl, apiKey) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.apiKey = apiKey;
  }

  async _request(method, path, body = null) {
    const options = {
      method,
      headers: {
        "Authorization": `Bearer ${this.apiKey}`,
        "Content-Type": "application/json"
      }
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(
      `${this.baseUrl}${path}`,
      options
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return response.json();
  }

  getScanStatus(scanId) {
    return this._request("GET", `/api/scan/${scanId}/status`);
  }

  stopScan(scanId) {
    return this._request("POST", `/api/scan/${scanId}/stop`);
  }

  getLatestFindings(severity = null, limit = 10) {
    let path = `/api/findings/latest?limit=${limit}`;
    if (severity) {
      path += `&severity=${severity}`;
    }
    return this._request("GET", path);
  }

  createSchedule(projectId, frequency, time) {
    return this._request("POST", "/api/schedule/create", {
      project_id: projectId,
      frequency,
      time
    });
  }
}

// Usage
const client = new VAPTClient("http://localhost:8000", "vapt_xxxxxxxxxxxx");

// Poll scan status
const pollScan = async (scanId) => {
  while (true) {
    const status = await client.getScanStatus(scanId);
    console.log(`Progress: ${status.progress}% (${status.current_phase})`);

    if (status.status !== 'running') {
      break;
    }

    await new Promise(resolve => setTimeout(resolve, 5000));
  }
};

// Get critical findings
client.getLatestFindings("CRITICAL", 20).then(findings => {
  console.log(`Found ${findings.length} critical findings`);
});
```

---

## Error Handling

Common HTTP status codes:

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad request (invalid parameters) |
| 401 | Unauthorized (missing/invalid API key) |
| 403 | Forbidden (access denied) |
| 404 | Not found (scan/project doesn't exist) |
| 429 | Rate limit exceeded (100 requests/min) |
| 500 | Server error |

Error response format:
```json
{
  "detail": "Rate limit exceeded (100 requests/min)"
}
```

---

## Best Practices

1. **Secure API Keys**
   - Store keys in environment variables, not in code
   - Rotate keys regularly
   - Revoke unused keys

2. **Handle Rate Limits**
   - Implement exponential backoff for 429 responses
   - Monitor `requests_remaining` header
   - Batch requests when possible

3. **Polling**
   - Use exponential backoff (start with 1s, max 30s)
   - Respect rate limits when polling
   - Cache results to reduce API calls

4. **Error Handling**
   - Handle timeouts gracefully
   - Retry on 5xx errors
   - Log all API errors

---

## Swagger/OpenAPI Documentation

Interactive API documentation available at:
```
http://localhost:8000/docs
```

Full OpenAPI schema:
```
http://localhost:8000/openapi.json
```
