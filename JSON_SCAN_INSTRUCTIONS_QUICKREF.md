# JSON Scan Instructions - Quick Reference Guide

## 🚀 Quick Start

### 1. Using the UI Component
```jsx
import ScanInstructionBuilder from './components/ScanInstructionBuilder';

<ScanInstructionBuilder onScanStart={(scanId) => {
  console.log('Scan started:', scanId);
}} />
```

### 2. Basic JSON Scan
```json
{
  "name": "My First Scan",
  "target": "https://example.com",
  "modules": ["xss", "sqli"]
}
```

### 3. Using Templates
- Open ScanInstructionBuilder
- Click "Templates" tab
- Click "Use Template" on any template
- Customize if needed
- Click "Execute Scan"

### 4. Via API
```bash
curl -X POST http://localhost:8000/api/scans/json/from-json \
  -H "Content-Type: application/json" \
  -d '{"json_instruction": {"name": "Test", "target": "https://example.com"}}'
```

---

## 📋 Essential Fields

| Field | Type | Required | Values |
|-------|------|----------|--------|
| name | string | ✓ | Any (1-200 chars) |
| target | string | ✓ | URL/domain |
| modules | array | | "all" or ["xss", "sqli", "csrf", ...] |
| depth | string | | "quick", "medium", "full" |
| concurrency | number | | 1-50 (default: 5) |
| timeout | number | | 5-3600 (default: 600) |
| description | string | | Any (max 1000 chars) |
| scope | array | | URL patterns |

---

## 🎯 Common Patterns

### Quick Scan (5 min)
```json
{
  "name": "Quick Check",
  "target": "https://example.com",
  "depth": "quick",
  "modules": ["xss", "sqli"]
}
```

### Full Audit (30 min)
```json
{
  "name": "Full Audit",
  "target": "https://example.com",
  "depth": "full",
  "modules": ["all"]
}
```

### API Testing
```json
{
  "name": "API Test",
  "target": "https://api.example.com",
  "modules": ["sqli", "xss", "csrf", "auth"],
  "advanced": {
    "auth_type": "bearer",
    "auth_credentials": {"token": "..."}
  }
}
```

### With Notifications
```json
{
  "name": "Notified Scan",
  "target": "https://example.com",
  "modules": ["all"],
  "notifications": {
    "email": "admin@example.com",
    "severity_filter": "high"
  }
}
```

### With Export
```json
{
  "name": "Export Scan",
  "target": "https://example.com",
  "modules": ["all"],
  "export": {
    "formats": ["pdf", "json"],
    "send_email": true,
    "email": "reports@example.com"
  }
}
```

### Scheduled (Weekly Monday 2 AM)
```json
{
  "name": "Weekly Scan",
  "target": "https://example.com",
  "modules": ["all"],
  "schedule": {
    "recurring": "weekly",
    "day": "Monday",
    "time": "02:00"
  }
}
```

---

## ✅ Validation

### API Validation
```bash
curl -X POST http://localhost:8000/api/scans/json/validate \
  -H "Content-Type: application/json" \
  -d '{"json_instruction": {"name": "Test", "target": "https://example.com"}}'
```

### Response (Valid)
```json
{
  "is_valid": true,
  "errors": [],
  "suggestions": []
}
```

### Response (Invalid)
```json
{
  "is_valid": false,
  "errors": ["Field 'depth' must be one of: {'quick', 'medium', 'full'}"],
  "suggestions": ["Use 'depth': 'quick' | 'medium' | 'full'"]
}
```

---

## 🔧 Advanced Options

### Authentication
```json
{
  "advanced": {
    "auth_type": "bearer",
    "auth_credentials": {
      "token": "eyJhbGci..."
    }
  }
}
```

### Proxy
```json
{
  "advanced": {
    "proxy_url": "http://proxy.example.com:8080"
  }
}
```

### Custom User-Agent
```json
{
  "advanced": {
    "user_agent": "Mozilla/5.0..."
  }
}
```

### Skip Robots.txt
```json
{
  "advanced": {
    "skip_robots_txt": true
  }
}
```

---

## 📦 Available Modules

**Web Vulnerabilities**
- `xss` - Cross-site scripting
- `sqli` - SQL injection
- `csrf` - Cross-site request forgery
- `redirect` - Open redirects
- `idor` - Insecure direct object references
- `file_upload` - Unsafe file uploads
- `path_traversal` - Path traversal

**Security Configuration**
- `header_injection` - HTTP header injection
- `auth` - Authentication flaws
- `headers` - Security headers analysis

**Infrastructure**
- `recon` - Reconnaissance/enumeration
- `ports` - Port scanning
- `cve` - CVE vulnerability lookup

**Special**
- `all` - Run all modules

---

## 🎨 Depth Levels

| Depth | Duration | Coverage | Use Case |
|-------|----------|----------|----------|
| quick | 5-10 min | Surface-level | Fast checks |
| medium | 15-20 min | Balanced | Standard audits |
| full | 30+ min | Deep | Comprehensive |

---

## 🔔 Notification Channels

- `desktop` - Browser notifications
- `email` - Email messages
- `slack` - Slack messages
- `teams` - Microsoft Teams

### Severity Filters
- `critical` - Critical only
- `high` - High and above
- `medium` - Medium and above
- `low` - Low and above
- `all` - All findings

---

## 📊 Export Formats

- `pdf` - PDF report
- `json` - JSON data
- `csv` - Spreadsheet
- `html` - Web page

---

## 📅 Schedule Types

### One-Time
```json
{
  "schedule": {
    "recurring": "one-time"
  }
}
```

### Daily
```json
{
  "schedule": {
    "recurring": "daily",
    "time": "03:00"
  }
}
```

### Weekly
```json
{
  "schedule": {
    "recurring": "weekly",
    "day": "Monday",
    "time": "02:00"
  }
}
```

### Monthly
```json
{
  "schedule": {
    "recurring": "monthly",
    "date": 15,
    "time": "03:00"
  }
}
```

---

## 🐍 Python Integration

### Minimal Example
```python
import requests

instruction = {
    "name": "Quick Scan",
    "target": "https://example.com",
    "modules": ["xss", "sqli"]
}

response = requests.post(
    "http://localhost:8000/api/scans/json/from-json",
    json={"json_instruction": instruction}
)

print(response.json()["scan_id"])
```

### With Validation
```python
import requests

instruction = {
    "name": "Quick Scan",
    "target": "https://example.com"
}

# Validate first
validation = requests.post(
    "http://localhost:8000/api/scans/json/validate",
    json={"json_instruction": instruction}
).json()

if validation["is_valid"]:
    # Start scan
    scan = requests.post(
        "http://localhost:8000/api/scans/json/from-json",
        json={"json_instruction": instruction}
    ).json()
    print(f"Scan ID: {scan['scan_id']}")
else:
    print(f"Errors: {validation['errors']}")
    print(f"Suggestions: {validation['suggestions']}")
```

### Batch Scanning
```python
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

---

## 🧪 Common Errors & Fixes

| Error | Fix |
|-------|-----|
| Missing required field: 'name' | Add `"name": "Your scan name"` |
| Missing required field: 'target' | Add `"target": "https://example.com"` |
| Invalid module: 'xyz' | Use valid module names |
| Field 'depth' must be one of: {'quick', 'medium', 'full'} | Use one of: quick, medium, full |
| Field 'concurrency' must be between 1 and 50 | Use value between 1-50 |
| Field 'timeout' must be between 5 and 3600 | Use value between 5-3600 |
| Invalid 'schedule.time' format | Use HH:MM format (e.g., "14:30") |
| Invalid notification channel | Use: desktop, email, slack, teams |
| Invalid export format | Use: pdf, json, csv, html |

---

## 📚 Resources

- **Full Documentation**: JSON_SCAN_INSTRUCTIONS.md
- **Implementation Details**: JSON_SCAN_INSTRUCTIONS_IMPLEMENTATION.md
- **API Schema**: GET /api/scans/json/schema
- **Templates**: GET /api/scans/json/templates

---

## 🎯 Pre-built Templates

1. **Quick Scan** (⚡) - 5 min, basic modules
2. **Full Audit** (🔍) - 30 min, all modules
3. **API Test** (🔗) - API testing preset
4. **Compliance** (⚖️) - OWASP focus
5. **CI/CD** (🔄) - Pipeline integration

---

## 🚀 Getting Started (Step by Step)

1. **Open UI Component**
   - Import `ScanInstructionBuilder`
   - Place in your page

2. **Select Template** (or write custom JSON)
   - Click Templates tab
   - Choose a template
   - Click "Use Template"

3. **Customize** (optional)
   - Edit JSON as needed
   - Click "Validate" to check

4. **Execute**
   - Click "Execute Scan"
   - Get back scan ID

5. **Monitor**
   - Use scan ID to get results
   - Subscribe to notifications

---

## 🔗 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | /api/scans/json/validate | Validate JSON |
| POST | /api/scans/json/from-json | Start scan |
| GET | /api/scans/json/templates | Get templates |
| GET | /api/scans/json/schema | Get schema |

---

**Last Updated**: 2024
**Status**: Production Ready ✅
