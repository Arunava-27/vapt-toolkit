# JSON Scan Instructions - Complete Guide

## Overview

The JSON Scan Instructions system allows you to define and execute security scans programmatically using JSON-based configurations. This enables seamless integration with CI/CD pipelines, automation frameworks, and batch scanning operations.

## Table of Contents

1. [Quick Start](#quick-start)
2. [JSON Schema Reference](#json-schema-reference)
3. [Field Descriptions](#field-descriptions)
4. [Templates](#templates)
5. [Examples](#examples)
6. [Use Cases](#use-cases)
7. [Validation & Errors](#validation--errors)
8. [API Integration](#api-integration)

---

## Quick Start

### 1. Basic Scan

```json
{
  "name": "Basic Website Scan",
  "target": "https://example.com",
  "modules": ["xss", "sqli"],
  "depth": "medium"
}
```

### 2. Comprehensive Scan

```json
{
  "name": "Full Security Audit",
  "target": "https://example.com",
  "scope": ["https://example.com/*", "https://api.example.com/*"],
  "modules": ["all"],
  "depth": "full",
  "notifications": {
    "email": "security@example.com",
    "slack_webhook": "https://hooks.slack.com/..."
  },
  "export": {
    "formats": ["pdf", "json"],
    "send_email": true
  }
}
```

### 3. CI/CD Pipeline Scan

```json
{
  "name": "CI/CD Automated Scan",
  "target": "https://staging.example.com",
  "modules": ["xss", "sqli", "csrf"],
  "depth": "medium",
  "concurrency": 10,
  "timeout": 600,
  "notifications": {
    "severity_filter": "high",
    "channels": ["slack"]
  }
}
```

---

## JSON Schema Reference

### Root Object

```typescript
{
  name: string (required)              // Scan name (1-200 chars)
  target: string (required)            // Target URL or domain
  description?: string                 // Scan description (max 1000 chars)
  scope?: string[]                     // Authorized scope patterns
  modules?: string[]                   // Vulnerability modules to run
  depth?: string                       // Scan depth (quick|medium|full)
  concurrency?: integer                // Concurrent requests (1-50)
  timeout?: integer                    // Request timeout in seconds (5-3600)
  notifications?: NotificationConfig   // Notification settings
  export?: ExportConfig               // Export settings
  schedule?: ScheduleConfig           // Scheduling settings
  advanced?: AdvancedConfig           // Advanced options
}
```

---

## Field Descriptions

### Required Fields

#### `name` (string)
- **Description**: Descriptive name for your scan
- **Constraints**: 1-200 characters
- **Example**: `"Full Site Scan - Production"`

#### `target` (string)
- **Description**: Target URL or domain to scan
- **Format**: URL (e.g., `https://example.com`) or domain (e.g., `example.com`)
- **Example**: `"https://example.com"`

### Optional Core Fields

#### `description` (string)
- **Description**: Detailed scan description
- **Constraints**: Maximum 1000 characters
- **Example**: `"Comprehensive security audit of production environment"`

#### `scope` (string[])
- **Description**: Authorized target patterns for active scans
- **Usage**: Restricts scan to specified URLs/patterns (wildcards supported)
- **Example**:
  ```json
  [
    "https://example.com/*",
    "https://api.example.com/*",
    "https://cdn.example.com/*"
  ]
  ```

#### `modules` (string[])
- **Description**: Vulnerability modules to run
- **Options**:
  - `"all"` - Run all available modules
  - `"xss"` - Cross-site scripting detection
  - `"sqli"` - SQL injection detection
  - `"csrf"` - Cross-site request forgery detection
  - `"redirect"` - Open redirect detection
  - `"header_injection"` - HTTP header injection
  - `"path_traversal"` - Path traversal/directory traversal
  - `"idor"` - Insecure direct object reference
  - `"file_upload"` - Unsafe file upload handling
  - `"auth"` - Authentication flaws
  - `"headers"` - Security header analysis
  - `"recon"` - Reconnaissance/enumeration
  - `"ports"` - Port scanning
  - `"cve"` - CVE vulnerability checks
- **Default**: `["all"]`
- **Example**: `["xss", "sqli", "csrf", "auth"]`

#### `depth` (string)
- **Description**: Scan depth/coverage level
- **Options**:
  - `"quick"` - Fast surface-level scan (~5 min)
  - `"medium"` - Balanced scan (~15 min)
  - `"full"` - Comprehensive deep scan (~30+ min)
- **Default**: `"medium"`
- **Mapping**:
  - Quick → Limited crawl depth, basic payloads
  - Medium → Moderate crawl, standard payloads
  - Full → Deep crawl, advanced payloads, header injection, path traversal

#### `concurrency` (integer)
- **Description**: Number of concurrent requests during scan
- **Range**: 1-50
- **Default**: 5
- **Recommendation**: 5-10 for remote targets, 10-20 for local
- **Example**: `8`

#### `timeout` (integer)
- **Description**: Request timeout in seconds
- **Range**: 5-3600
- **Default**: 600 (10 minutes)
- **Note**: Longer timeouts for slower targets
- **Example**: `900` (15 minutes)

### Notification Configuration

```json
"notifications": {
  "email": "admin@example.com",
  "slack_webhook": "https://hooks.slack.com/services/...",
  "teams_webhook": "https://outlook.webhook.office.com/...",
  "severity_filter": "high",
  "channels": ["desktop", "email", "slack"]
}
```

#### Fields
- **email** (string): Email address for notifications
- **slack_webhook** (string): Slack webhook URL for notifications
- **teams_webhook** (string): Microsoft Teams webhook URL
- **severity_filter** (string): Notification threshold
  - `"critical"` - Critical findings only
  - `"high"` - High and critical
  - `"medium"` - Medium, high, critical
  - `"low"` - All severities
  - `"all"` - All findings
- **channels** (string[]): Notification delivery methods
  - `"desktop"` - Browser notifications
  - `"email"` - Email notifications
  - `"slack"` - Slack messages
  - `"teams"` - Teams notifications

### Export Configuration

```json
"export": {
  "formats": ["pdf", "json", "csv", "html"],
  "send_email": true,
  "email": "reports@example.com"
}
```

#### Fields
- **formats** (string[]): Export formats
  - `"pdf"` - PDF report
  - `"json"` - JSON data
  - `"csv"` - CSV spreadsheet
  - `"html"` - HTML report
- **send_email** (boolean): Send report via email
- **email** (string): Email for report delivery

### Schedule Configuration

```json
"schedule": {
  "recurring": "weekly",
  "day": "Monday",
  "time": "02:00"
}
```

#### Fields
- **recurring** (string): Schedule frequency
  - `"one-time"` - Run once immediately
  - `"daily"` - Run every day
  - `"weekly"` - Run on specific day
  - `"monthly"` - Run on specific date
- **day** (string): Day for weekly schedule
  - `"Monday"`, `"Tuesday"`, ..., `"Sunday"`
- **date** (integer): Date for monthly (1-31)
- **time** (string): Execution time (HH:MM, 24-hour format)

### Advanced Configuration

```json
"advanced": {
  "skip_robots_txt": false,
  "user_agent": "Mozilla/5.0 ...",
  "proxy_url": "http://proxy.example.com:8080",
  "auth_type": "bearer",
  "auth_credentials": {
    "token": "eyJhbGciOiJIUzI1NiIs..."
  }
}
```

#### Fields
- **skip_robots_txt** (boolean): Ignore robots.txt
- **user_agent** (string): Custom User-Agent header
- **proxy_url** (string): HTTP proxy URL
- **auth_type** (string): Authentication method
  - `"none"` - No authentication
  - `"basic"` - HTTP Basic Auth
  - `"bearer"` - Bearer token
  - `"api_key"` - API key
  - `"oauth2"` - OAuth 2.0
- **auth_credentials** (object): Auth details
  - For Basic: `{"username": "...", "password": "..."}`
  - For Bearer: `{"token": "..."}`
  - For API Key: `{"api_key": "..."}`

---

## Templates

### Pre-built Templates

The UI provides ready-to-use templates:

#### ⚡ Quick Scan
- **Duration**: 5-10 minutes
- **Modules**: XSS, SQL Injection, Security Headers
- **Depth**: Quick
- **Use Case**: Fast surface-level assessment

#### 🔍 Full Audit
- **Duration**: 30-60 minutes
- **Modules**: All modules
- **Depth**: Full
- **Use Case**: Comprehensive security assessment
- **Includes**: PDF export, email notifications

#### 🔗 API Security Test
- **Duration**: 15-20 minutes
- **Modules**: SQLi, XSS, CSRF, Auth
- **Depth**: Full
- **Use Case**: REST/GraphQL API testing
- **Special**: Bearer token support

#### ⚖️ Compliance Scan
- **Duration**: 20-30 minutes
- **Modules**: OWASP Top 10, CWE-related checks
- **Depth**: Full
- **Use Case**: Compliance and standards verification
- **Includes**: PDF export, email delivery

#### 🔄 CI/CD Pipeline Scan
- **Duration**: 10-15 minutes
- **Modules**: Core vulnerabilities
- **Depth**: Medium
- **Use Case**: Automated CI/CD integration
- **Includes**: Slack notifications, JSON export

---

## Examples

### Example 1: Simple Website Scan

```json
{
  "name": "Company Website Security Check",
  "target": "https://company.example.com",
  "modules": ["xss", "sqli", "csrf"],
  "depth": "medium",
  "concurrency": 5,
  "timeout": 600
}
```

### Example 2: API Endpoint Testing

```json
{
  "name": "API v2 Security Assessment",
  "target": "https://api.example.com",
  "scope": ["https://api.example.com/v2/*"],
  "modules": ["all"],
  "depth": "full",
  "concurrency": 10,
  "timeout": 1800,
  "advanced": {
    "auth_type": "bearer",
    "auth_credentials": {
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    },
    "skip_robots_txt": true
  },
  "notifications": {
    "email": "api-security@example.com",
    "severity_filter": "high"
  },
  "export": {
    "formats": ["json", "csv"],
    "send_email": true
  }
}
```

### Example 3: CI/CD Automated Scan

```json
{
  "name": "Staging Environment - ${BUILD_NUMBER}",
  "target": "https://staging.example.com",
  "scope": ["https://staging.example.com/*"],
  "modules": ["xss", "sqli", "csrf", "idor"],
  "depth": "medium",
  "concurrency": 15,
  "timeout": 900,
  "notifications": {
    "slack_webhook": "${SLACK_WEBHOOK_URL}",
    "severity_filter": "high",
    "channels": ["slack"]
  },
  "export": {
    "formats": ["json"],
    "send_email": false
  }
}
```

### Example 4: Compliance Audit

```json
{
  "name": "PCI-DSS Compliance Audit",
  "target": "https://payment.example.com",
  "scope": [
    "https://payment.example.com/checkout/*",
    "https://payment.example.com/account/*"
  ],
  "modules": [
    "sqli",
    "xss",
    "csrf",
    "idor",
    "auth",
    "headers",
    "path_traversal"
  ],
  "depth": "full",
  "concurrency": 5,
  "timeout": 3600,
  "notifications": {
    "email": "compliance@example.com",
    "severity_filter": "medium",
    "channels": ["email"]
  },
  "export": {
    "formats": ["pdf", "json", "csv"],
    "send_email": true,
    "email": "reports@example.com"
  },
  "schedule": {
    "recurring": "monthly",
    "date": 1,
    "time": "03:00"
  }
}
```

### Example 5: Scheduled Weekly Scan

```json
{
  "name": "Weekly Production Scan",
  "target": "https://example.com",
  "modules": ["all"],
  "depth": "full",
  "schedule": {
    "recurring": "weekly",
    "day": "Monday",
    "time": "02:00"
  },
  "notifications": {
    "email": "security-team@example.com",
    "slack_webhook": "https://hooks.slack.com/services/...",
    "severity_filter": "high",
    "channels": ["email", "slack"]
  },
  "export": {
    "formats": ["pdf", "json"],
    "send_email": true
  }
}
```

---

## Use Cases

### 1. CI/CD Pipeline Integration

Automatically run security scans on every deployment:

```bash
#!/bin/bash
curl -X POST http://localhost:8000/api/scans/json/from-json \
  -H "Content-Type: application/json" \
  -d '{
    "name": "CI/CD Scan - '$BUILD_NUMBER'",
    "target": "'$STAGING_URL'",
    "modules": ["xss", "sqli", "csrf"],
    "depth": "medium",
    "notifications": {
      "slack_webhook": "'$SLACK_WEBHOOK'",
      "severity_filter": "high"
    }
  }'
```

### 2. Batch Scanning

Scan multiple targets sequentially:

```python
import json
import requests

targets = [
  "https://app1.example.com",
  "https://app2.example.com",
  "https://app3.example.com"
]

for target in targets:
    instruction = {
        "name": f"Batch Scan - {target}",
        "target": target,
        "modules": ["all"],
        "depth": "medium"
    }
    
    response = requests.post(
        "http://localhost:8000/api/scans/json/from-json",
        json={"json_instruction": instruction}
    )
    print(f"{target}: {response.json()['scan_id']}")
```

### 3. Scheduled Compliance Audits

Set up recurring scans for compliance:

```json
{
  "name": "Monthly Security Audit",
  "target": "https://example.com",
  "modules": ["all"],
  "depth": "full",
  "schedule": {
    "recurring": "monthly",
    "date": 15,
    "time": "03:00"
  },
  "export": {
    "formats": ["pdf"],
    "send_email": true,
    "email": "compliance@example.com"
  }
}
```

### 4. Multi-Environment Testing

Different scan configs for different environments:

```python
environments = {
  "dev": {"depth": "quick", "concurrency": 10},
  "staging": {"depth": "medium", "concurrency": 5},
  "prod": {"depth": "full", "concurrency": 3}
}

for env, config in environments.items():
    instruction = {
        "name": f"Security Scan - {env}",
        "target": f"https://{env}.example.com",
        "modules": ["all"],
        **config
    }
    # Execute scan...
```

### 5. Custom Vulnerability Testing

Target specific vulnerabilities:

```json
{
  "name": "OWASP Top 10 - 2021 Assessment",
  "target": "https://example.com",
  "modules": [
    "idor",
    "auth",
    "sqli",
    "xss",
    "csrf",
    "path_traversal",
    "file_upload",
    "header_injection"
  ],
  "depth": "full",
  "concurrency": 8,
  "export": {
    "formats": ["pdf", "json"]
  }
}
```

---

## Validation & Errors

### Common Validation Errors

#### Missing Required Fields
```
Error: Missing required field: 'name'
Solution: Add "name" field with a descriptive string
```

#### Invalid Target
```
Error: Field 'target' cannot be empty
Solution: Provide a valid URL or domain
```

#### Invalid Module
```
Error: Invalid module: 'xsss'. Valid: {...}
Solution: Check spelling. Use 'xss' instead of 'xsss'
```

#### Invalid Depth
```
Error: Field 'depth' must be one of: {'quick', 'medium', 'full'}
Solution: Use one of: quick, medium, or full
```

#### Invalid Time Format
```
Error: Field 'schedule.time' must be in HH:MM format
Solution: Use 24-hour format. Example: "14:30"
```

### Real-Time Validation

The UI provides live validation as you type:
- ✅ Green checkmark = Valid
- ❌ Red error = Invalid
- 💡 Suggestions = Common fixes

### Validate via API

```bash
curl -X POST http://localhost:8000/api/scans/json/validate \
  -H "Content-Type: application/json" \
  -d '{"json_instruction": "{...}"}'
```

Response:
```json
{
  "is_valid": false,
  "errors": [
    "Field 'depth' must be one of: {'quick', 'medium', 'full'}"
  ],
  "suggestions": [
    "💡 Use 'depth': 'quick' | 'medium' | 'full'"
  ]
}
```

---

## API Integration

### REST Endpoints

#### 1. Validate JSON Instruction
```
POST /api/scans/json/validate
Content-Type: application/json

{
  "json_instruction": "{...}"  // string or object
}
```

**Response:**
```json
{
  "is_valid": true,
  "errors": [],
  "suggestions": []
}
```

#### 2. Start Scan from JSON
```
POST /api/scans/json/from-json
Content-Type: application/json

{
  "json_instruction": "{...}",
  "project_name": "optional-name",
  "project_id": "optional-id"
}
```

**Response:**
```json
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "estimated_time_seconds": 900,
  "message": "Scan 'Full Audit' started. Target: https://example.com"
}
```

#### 3. Get Templates
```
GET /api/scans/json/templates
```

**Response:**
```json
{
  "templates": [
    {
      "id": "quick-scan",
      "name": "Quick Scan",
      "description": "Fast surface-level scan",
      "icon": "⚡",
      "estimated_time_seconds": 300,
      "json_instruction": {...}
    },
    ...
  ]
}
```

#### 4. Get JSON Schema
```
GET /api/scans/json/schema
```

**Response:**
```json
{
  "type": "object",
  "required": ["name", "target"],
  "properties": {...}
}
```

### Example: Python Integration

```python
import json
import requests

class JSONScanClient:
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
    
    def validate(self, instruction):
        """Validate JSON instruction."""
        response = requests.post(
            f"{self.api_url}/api/scans/json/validate",
            json={"json_instruction": instruction}
        )
        return response.json()
    
    def start_scan(self, instruction, project_name=None):
        """Start a scan."""
        response = requests.post(
            f"{self.api_url}/api/scans/json/from-json",
            json={
                "json_instruction": instruction,
                "project_name": project_name
            }
        )
        return response.json()
    
    def get_templates(self):
        """Get available templates."""
        response = requests.get(
            f"{self.api_url}/api/scans/json/templates"
        )
        return response.json()["templates"]

# Usage
client = JSONScanClient()

# Validate
result = client.validate({
    "name": "Test",
    "target": "https://example.com",
    "modules": ["xss", "sqli"]
})

if result["is_valid"]:
    # Start scan
    scan = client.start_scan({
        "name": "My Scan",
        "target": "https://example.com",
        "modules": ["all"],
        "depth": "medium"
    })
    print(f"Scan ID: {scan['scan_id']}")
```

### Example: JavaScript Integration

```javascript
class JSONScanClient {
  constructor(apiUrl = 'http://localhost:8000') {
    this.apiUrl = apiUrl;
  }

  async validate(instruction) {
    const response = await fetch(
      `${this.apiUrl}/api/scans/json/validate`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ json_instruction: instruction })
      }
    );
    return response.json();
  }

  async startScan(instruction, projectName = null) {
    const response = await fetch(
      `${this.apiUrl}/api/scans/json/from-json`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          json_instruction: instruction,
          project_name: projectName
        })
      }
    );
    return response.json();
  }

  async getTemplates() {
    const response = await fetch(
      `${this.apiUrl}/api/scans/json/templates`
    );
    const data = await response.json();
    return data.templates;
  }
}

// Usage
const client = new JSONScanClient();

const instruction = {
  name: 'My Scan',
  target: 'https://example.com',
  modules: ['all'],
  depth: 'medium'
};

const result = await client.validate(instruction);
if (result.is_valid) {
  const scan = await client.startScan(instruction);
  console.log(`Scan ID: ${scan.scan_id}`);
}
```

---

## Security Considerations

1. **API Keys**: Use API keys for programmatic access
2. **Scope Validation**: Always define authorized scope to prevent scanning unintended targets
3. **Credentials**: Never hardcode sensitive credentials; use environment variables
4. **Webhooks**: Use HTTPS for webhook URLs and verify signatures
5. **Rate Limiting**: Respect API rate limits (100 req/min default)
6. **Timeout**: Set appropriate timeouts for your network conditions

---

## Troubleshooting

### Scan Timeout
- Increase `timeout` value
- Reduce `concurrency`
- Use `depth: "quick"` for faster scans

### Target Not Reachable
- Verify target URL is correct
- Check network connectivity
- Verify firewall rules

### Auth Failures
- Confirm credentials are correct
- Verify auth type matches target
- Check token expiration

### Missing Notifications
- Verify webhook URLs
- Check channel configuration
- Confirm notification settings

---

## Support

For issues or questions:
1. Check the documentation above
2. Review example configurations
3. Validate JSON with live validation tool
4. Check API response messages for guidance
