# VAPT Toolkit API Reference

## Overview

The VAPT Toolkit exposes a comprehensive REST API for vulnerability assessment and penetration testing automation. All API endpoints require authentication via Bearer token with an API key and are subject to rate limiting.

**Base URL**: `http://localhost:8000`
**API Version**: 1.0
**Protocol**: HTTP/REST
**Authentication**: Bearer Token (API Key)

## Table of Contents

- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [Error Handling](#error-handling)
- [Scan Endpoints](#scan-endpoints)
- [Project Endpoints](#project-endpoints)
- [Report Endpoints](#report-endpoints)
- [API Key Management](#api-key-management)
- [Webhook Endpoints](#webhook-endpoints)
- [Bulk Operations](#bulk-operations)
- [Scheduling](#scheduling)
- [Notifications](#notifications)
- [Scope Management](#scope-management)
- [Patterns and Fingerprints](#patterns-and-fingerprints)
- [Code Examples](#code-examples)

## Authentication

### API Key Format

API keys follow a structured format with three components:

```
vapt_{32_character_base64_encoded_random}
```

**Example**: `vapt_aB3cD4eF5gH6iJ7kL8mN9oP0qR1sT2uV`

### Bearer Token Authentication

All API requests must include the `Authorization` header with a Bearer token containing your API key:

```
Authorization: Bearer vapt_aB3cD4eF5gH6iJ7kL8mN9oP0qR1sT2uV
```

### API Key Generation

Generate a new API key:

```http
POST /api/v1/keys/generate HTTP/1.1
Host: localhost:8000
Content-Type: application/json
Authorization: Bearer {existing_api_key}

{}
```

**Response** (201):
```json
{
  "id": "key_1234567890",
  "key": "vapt_aB3cD4eF5gH6iJ7kL8mN9oP0qR1sT2uV",
  "created_at": "2024-01-15T10:30:00Z",
  "name": "Production API Key"
}
```

### API Key Validation

The system validates API keys by:
1. Extracting the key from the Authorization header
2. Hashing it with SHA256
3. Comparing against stored hash in the database
4. Tracking last_used timestamp for audit purposes

## Rate Limiting

### Limits

- **Request Limit**: 100 requests per minute per API key
- **Concurrent Scans**: Unlimited (tracked separately)
- **Bulk Operations**: 50 items per request

### Headers

Rate limit information is returned in response headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 2024-01-15T10:31:00Z
```

### Exceeding Limits

When rate limit is exceeded, the API returns:

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json

{
  "detail": "Rate limit exceeded: 100 requests per minute",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 45
}
```

## Error Handling

### Error Response Format

All error responses follow this format:

```json
{
  "detail": "Human-readable error message",
  "error_code": "ERROR_CODE",
  "status_code": 400,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful request |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid parameters or malformed request |
| 401 | Unauthorized | Missing or invalid API key |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

### Common Error Codes

- `INVALID_API_KEY`: API key is invalid or expired
- `RATE_LIMIT_EXCEEDED`: Request limit exceeded
- `INVALID_SCAN_STATE`: Scan is not in a valid state for the operation
- `PROJECT_NOT_FOUND`: Project ID does not exist
- `SCAN_NOT_FOUND`: Scan ID does not exist
- `VALIDATION_ERROR`: Request validation failed
- `DUPLICATE_RESOURCE`: Resource already exists

## Scan Endpoints

### Start a Scan

Initiate a new vulnerability assessment scan on a target.

```http
POST /api/v1/scans/start HTTP/1.1
Host: localhost:8000
Content-Type: application/json
Authorization: Bearer {api_key}

{
  "project_id": "proj_abc123",
  "target_url": "https://target.com",
  "classification": "passive",
  "modules": ["osint", "web_scanner"],
  "custom_wordlist": null,
  "scope_includes": [
    "/api/v1/*",
    "/admin/*"
  ],
  "scope_excludes": [
    "*/logout",
    "*/login"
  ]
}
```

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| project_id | string | Yes | Project identifier |
| target_url | string | Yes | URL to scan |
| classification | string | Yes | `passive`, `active`, or `hybrid` |
| modules | array | No | Modules to enable (default: all enabled) |
| custom_wordlist | string | No | URL to custom wordlist file |
| scope_includes | array | No | URL patterns to include in scope |
| scope_excludes | array | No | URL patterns to exclude from scope |

**Response** (200):
```json
{
  "scan_id": "scan_abc123def456",
  "project_id": "proj_abc123",
  "target_url": "https://target.com",
  "status": "running",
  "classification": "passive",
  "started_at": "2024-01-15T10:30:00Z",
  "estimated_duration": "15m",
  "modules_enabled": ["osint", "web_scanner"]
}
```

### Get Scan Status

```http
GET /api/v1/scans/{scan_id} HTTP/1.1
Host: localhost:8000
Authorization: Bearer {api_key}
```

**Response** (200):
```json
{
  "scan_id": "scan_abc123def456",
  "project_id": "proj_abc123",
  "status": "running",
  "progress": 45,
  "findings_count": 12,
  "started_at": "2024-01-15T10:30:00Z",
  "elapsed_time": 300,
  "estimated_remaining": 600
}
```

### Stream Scan Events (SSE)

Connect to Server-Sent Events stream for real-time scan updates:

```http
GET /api/v1/scans/{scan_id}/stream HTTP/1.1
Host: localhost:8000
Authorization: Bearer {api_key}
```

**Events**:
```
data: {"type": "scan_started", "timestamp": "2024-01-15T10:30:00Z"}
data: {"type": "finding_discovered", "finding": {...}, "timestamp": "2024-01-15T10:30:15Z"}
data: {"type": "module_complete", "module": "web_scanner", "timestamp": "2024-01-15T10:35:00Z"}
data: {"type": "scan_completed", "status": "completed", "findings": 15, "timestamp": "2024-01-15T10:45:00Z"}
```

### Stop a Scan

```http
POST /api/v1/scans/{scan_id}/stop HTTP/1.1
Host: localhost:8000
Authorization: Bearer {api_key}

{}
```

**Response** (200):
```json
{
  "scan_id": "scan_abc123def456",
  "status": "stopped",
  "findings_count": 8,
  "stopped_at": "2024-01-15T10:40:00Z"
}
```

### List Scans

```http
GET /api/v1/scans?project_id=proj_abc123&status=completed&limit=10&offset=0 HTTP/1.1
Host: localhost:8000
Authorization: Bearer {api_key}
```

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| project_id | string | - | Filter by project ID |
| status | string | - | Filter by status (running, completed, stopped, failed) |
| limit | integer | 20 | Number of results (max 100) |
| offset | integer | 0 | Pagination offset |
| sort_by | string | created_at | Sort field |
| sort_dir | string | desc | Sort direction (asc, desc) |

**Response** (200):
```json
{
  "scans": [
    {
      "scan_id": "scan_abc123def456",
      "project_id": "proj_abc123",
      "target_url": "https://target.com",
      "status": "completed",
      "findings_count": 15,
      "started_at": "2024-01-15T10:30:00Z",
      "completed_at": "2024-01-15T10:45:00Z"
    }
  ],
  "total": 42,
  "limit": 10,
  "offset": 0
}
```

## Project Endpoints

### Create Project

```http
POST /api/v1/projects HTTP/1.1
Host: localhost:8000
Content-Type: application/json
Authorization: Bearer {api_key}

{
  "name": "Internal App Security",
  "description": "Security assessment of internal application",
  "owner": "security-team",
  "tags": ["internal", "web-app"]
}
```

**Response** (201):
```json
{
  "project_id": "proj_abc123",
  "name": "Internal App Security",
  "created_at": "2024-01-15T10:30:00Z",
  "owner": "security-team"
}
```

### Get Project

```http
GET /api/v1/projects/{project_id} HTTP/1.1
Host: localhost:8000
Authorization: Bearer {api_key}
```

**Response** (200):
```json
{
  "project_id": "proj_abc123",
  "name": "Internal App Security",
  "description": "Security assessment of internal application",
  "created_at": "2024-01-15T10:30:00Z",
  "scans_count": 5,
  "findings_count": 42,
  "owner": "security-team"
}
```

### List Projects

```http
GET /api/v1/projects?limit=10&offset=0 HTTP/1.1
Host: localhost:8000
Authorization: Bearer {api_key}
```

**Response** (200):
```json
{
  "projects": [
    {
      "project_id": "proj_abc123",
      "name": "Internal App Security",
      "scans_count": 5,
      "findings_count": 42
    }
  ],
  "total": 8,
  "limit": 10,
  "offset": 0
}
```

### Delete Project

```http
DELETE /api/v1/projects/{project_id} HTTP/1.1
Host: localhost:8000
Authorization: Bearer {api_key}
```

**Response** (204): No content

## Report Endpoints

### Generate Report

```http
POST /api/v1/reports/generate HTTP/1.1
Host: localhost:8000
Content-Type: application/json
Authorization: Bearer {api_key}

{
  "scan_id": "scan_abc123def456",
  "format": "pdf",
  "include_findings": true,
  "include_evidence": true,
  "remediation_advice": true
}
```

**Parameters**:

| Parameter | Type | Values | Description |
|-----------|------|--------|-------------|
| scan_id | string | - | Scan to report on |
| format | string | pdf, html, json, csv | Report format |
| include_findings | boolean | - | Include vulnerability findings |
| include_evidence | boolean | - | Include proof of concept evidence |
| remediation_advice | boolean | - | Include remediation recommendations |

**Response** (200):
```json
{
  "report_id": "report_xyz789",
  "scan_id": "scan_abc123def456",
  "format": "pdf",
  "status": "generating",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Download Report

```http
GET /api/v1/reports/{report_id}/download HTTP/1.1
Host: localhost:8000
Authorization: Bearer {api_key}
```

**Response** (200):
- Content-Type varies (application/pdf, text/html, etc.)
- File download binary content

## API Key Management

### List API Keys

```http
GET /api/v1/keys HTTP/1.1
Host: localhost:8000
Authorization: Bearer {api_key}
```

**Response** (200):
```json
{
  "keys": [
    {
      "id": "key_1234567890",
      "name": "Production Key",
      "created_at": "2024-01-01T00:00:00Z",
      "last_used": "2024-01-15T10:30:00Z",
      "masked_key": "vapt_****...T2uV"
    }
  ]
}
```

### Revoke API Key

```http
DELETE /api/v1/keys/{key_id} HTTP/1.1
Host: localhost:8000
Authorization: Bearer {api_key}
```

**Response** (204): No content

## Webhook Endpoints

### Register Webhook

```http
POST /api/v1/webhooks HTTP/1.1
Host: localhost:8000
Content-Type: application/json
Authorization: Bearer {api_key}

{
  "url": "https://your-service.com/webhook",
  "events": [
    "scan_started",
    "scan_completed",
    "finding_discovered"
  ],
  "secret": "your-webhook-secret"
}
```

**Response** (201):
```json
{
  "webhook_id": "webhook_abc123",
  "url": "https://your-service.com/webhook",
  "events": ["scan_started", "scan_completed", "finding_discovered"],
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Webhook Event Types

- `scan_started`: Fired when a scan begins
- `scan_completed`: Fired when a scan completes
- `finding_discovered`: Fired when a vulnerability is discovered
- `finding_verified`: Fired when a finding is verified by human review
- `module_complete`: Fired when a scan module completes
- `report_generated`: Fired when a report is generated

### Webhook Payload Example

All webhook payloads include:

```json
{
  "event": "scan_completed",
  "timestamp": "2024-01-15T10:45:00Z",
  "scan_id": "scan_abc123def456",
  "project_id": "proj_abc123",
  "data": {
    "status": "completed",
    "findings_count": 15,
    "completed_at": "2024-01-15T10:45:00Z"
  }
}
```

**Webhook Signing**:

Webhooks are signed using HMAC-SHA256. Verify the signature:

```
X-VAPT-Signature: sha256=abcd1234...
```

Verify with: `HMAC-SHA256(payload, secret_key) == signature`

### Webhook Retry Policy

Failed webhook deliveries are retried with exponential backoff:
- Attempt 1: Immediate
- Attempt 2: 1 second delay
- Attempt 3: 2 seconds delay
- Attempt 4: 4 seconds delay
- Attempt 5: 8 seconds delay
- Attempt 6: 16 seconds delay

Maximum timeout per request: 5 seconds

## Bulk Operations

### Bulk Scan Start

```http
POST /api/v1/scans/bulk HTTP/1.1
Host: localhost:8000
Content-Type: application/json
Authorization: Bearer {api_key}

{
  "project_id": "proj_abc123",
  "targets": [
    {
      "url": "https://target1.com",
      "classification": "passive"
    },
    {
      "url": "https://target2.com",
      "classification": "active"
    }
  ]
}
```

**Response** (200):
```json
{
  "bulk_operation_id": "bulk_op_123",
  "scans_created": 2,
  "scan_ids": ["scan_abc123", "scan_def456"]
}
```

## Scheduling

### Create Scheduled Scan

```http
POST /api/v1/schedules HTTP/1.1
Host: localhost:8000
Content-Type: application/json
Authorization: Bearer {api_key}

{
  "project_id": "proj_abc123",
  "target_url": "https://target.com",
  "classification": "passive",
  "cron_expression": "0 2 * * 0",
  "enabled": true
}
```

**Response** (201):
```json
{
  "schedule_id": "sched_123",
  "next_run": "2024-01-22T02:00:00Z",
  "enabled": true
}
```

## Notifications

### Get Notifications

```http
GET /api/v1/notifications?limit=10 HTTP/1.1
Host: localhost:8000
Authorization: Bearer {api_key}
```

**Response** (200):
```json
{
  "notifications": [
    {
      "id": "notif_123",
      "type": "finding_discovered",
      "title": "Critical SQL Injection Found",
      "message": "A critical SQL injection vulnerability was discovered in /api/v1/search",
      "created_at": "2024-01-15T10:30:00Z",
      "read": false
    }
  ]
}
```

## Scope Management

### Get Scope Configuration

```http
GET /api/v1/scope/{project_id} HTTP/1.1
Host: localhost:8000
Authorization: Bearer {api_key}
```

**Response** (200):
```json
{
  "project_id": "proj_abc123",
  "includes": ["/api/*", "/admin/*"],
  "excludes": ["/logout", "/login"],
  "active": true
}
```

### Update Scope

```http
PUT /api/v1/scope/{project_id} HTTP/1.1
Host: localhost:8000
Content-Type: application/json
Authorization: Bearer {api_key}

{
  "includes": ["/api/*", "/admin/*"],
  "excludes": ["/logout", "/login"]
}
```

## Patterns and Fingerprints

### Get False Positive Patterns

```http
GET /api/v1/patterns/false-positives HTTP/1.1
Host: localhost:8000
Authorization: Bearer {api_key}
```

**Response** (200):
```json
{
  "patterns": [
    {
      "id": "pattern_123",
      "name": "Known FP - jQuery XSS",
      "pattern": "jquery.*\\..*\\(.*\\)",
      "false_positive_rate": 0.95
    }
  ]
}
```

---

## Code Examples

### Python - Start a Scan

```python
import requests
import json

api_key = "vapt_aB3cD4eF5gH6iJ7kL8mN9oP0qR1sT2uV"
base_url = "http://localhost:8000"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "project_id": "proj_abc123",
    "target_url": "https://target.com",
    "classification": "passive",
    "modules": ["osint", "web_scanner"]
}

response = requests.post(
    f"{base_url}/api/v1/scans/start",
    headers=headers,
    json=payload
)

print(response.json())
```

### cURL - Start a Scan

```bash
#!/bin/bash

API_KEY="vapt_aB3cD4eF5gH6iJ7kL8mN9oP0qR1sT2uV"
BASE_URL="http://localhost:8000"

curl -X POST "${BASE_URL}/api/v1/scans/start" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "proj_abc123",
    "target_url": "https://target.com",
    "classification": "passive",
    "modules": ["osint", "web_scanner"]
  }'
```

### JavaScript - Stream Scan Events

```javascript
const apiKey = "vapt_aB3cD4eF5gH6iJ7kL8mN9oP0qR1sT2uV";
const scanId = "scan_abc123def456";

const eventSource = new EventSource(
  `http://localhost:8000/api/v1/scans/${scanId}/stream`,
  {
    headers: {
      "Authorization": `Bearer ${apiKey}`
    }
  }
);

eventSource.addEventListener("message", (event) => {
  const data = JSON.parse(event.data);
  console.log("Event:", data.type, data);

  if (data.type === "scan_completed") {
    eventSource.close();
  }
});

eventSource.addEventListener("error", (error) => {
  console.error("Stream error:", error);
  eventSource.close();
});
```

### Python - Monitor Scan with Polling

```python
import requests
import time
import json

api_key = "vapt_aB3cD4eF5gH6iJ7kL8mN9oP0qR1sT2uV"
base_url = "http://localhost:8000"
scan_id = "scan_abc123def456"

headers = {"Authorization": f"Bearer {api_key}"}

while True:
    response = requests.get(
        f"{base_url}/api/v1/scans/{scan_id}",
        headers=headers
    )
    
    data = response.json()
    print(f"Status: {data['status']}, Progress: {data['progress']}%, "
          f"Findings: {data['findings_count']}")
    
    if data['status'] in ['completed', 'stopped', 'failed']:
        break
    
    time.sleep(5)
```

### cURL - List All Findings

```bash
#!/bin/bash

API_KEY="vapt_aB3cD4eF5gH6iJ7kL8mN9oP0qR1sT2uV"
BASE_URL="http://localhost:8000"
SCAN_ID="scan_abc123def456"

curl -s "${BASE_URL}/api/v1/scans/${SCAN_ID}/findings" \
  -H "Authorization: Bearer ${API_KEY}" | jq '.findings[] | {
    id: .id,
    title: .title,
    severity: .severity,
    type: .type
  }'
```

### Python - Generate and Download Report

```python
import requests
import time

api_key = "vapt_aB3cD4eF5gH6iJ7kL8mN9oP0qR1sT2uV"
base_url = "http://localhost:8000"
scan_id = "scan_abc123def456"

headers = {"Authorization": f"Bearer {api_key}"}

# Request report generation
response = requests.post(
    f"{base_url}/api/v1/reports/generate",
    headers=headers,
    json={
        "scan_id": scan_id,
        "format": "pdf",
        "include_findings": True,
        "include_evidence": True
    }
)

report_data = response.json()
report_id = report_data["report_id"]

# Wait for report generation
time.sleep(5)

# Download report
response = requests.get(
    f"{base_url}/api/v1/reports/{report_id}/download",
    headers=headers
)

with open(f"report_{report_id}.pdf", "wb") as f:
    f.write(response.content)

print(f"Report saved to report_{report_id}.pdf")
```

---

## Best Practices

1. **Store API Keys Securely**: Never commit API keys to version control. Use environment variables.
2. **Rotate Keys Regularly**: Revoke and regenerate API keys periodically.
3. **Monitor Rate Limits**: Check X-RateLimit-* headers to avoid exceeding limits.
4. **Use Webhooks**: For long-running operations, use webhooks instead of polling.
5. **Handle Retries**: Implement exponential backoff for rate-limited requests.
6. **Verify Webhook Signatures**: Always verify HMAC-SHA256 signatures on webhook payloads.
7. **Use Scope Management**: Properly configure scope to avoid unnecessary requests.
8. **Test in Staging**: Test all integrations thoroughly before production use.

## Support

For issues or questions:
- Check the error code and error message in responses
- Review webhook delivery logs
- Consult rate limit headers for throttling issues
- Check API key validity and permissions
