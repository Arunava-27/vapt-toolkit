# JSON Scan Feature - Quick Start Guide

## 🚀 Getting Started

The JSON Scan feature lets you define security scans using JSON configuration. Perfect for:
- Automation & CI/CD integration
- Repeatable scan profiles
- Programmatic API access
- Custom workflow integration

## 📋 Quick Examples

### Example 1: Quick Scan (5 minutes)
```json
{
  "name": "Quick Security Check",
  "target": "192.168.29.48",
  "modules": ["xss", "sqli", "csrf"],
  "depth": "quick"
}
```

### Example 2: Full Scan (30+ minutes)
```json
{
  "name": "Comprehensive Assessment",
  "target": "example.com",
  "modules": ["all"],
  "depth": "full"
}
```

### Example 3: Web-Only Focus (20 minutes)
```json
{
  "name": "Web Testing",
  "target": "https://target.com",
  "modules": ["xss", "sqli", "idor", "auth", "csrf"],
  "depth": "medium"
}
```

### Example 4: Infrastructure & CVE (20 minutes)
```json
{
  "name": "Infrastructure Assessment",
  "target": "192.168.1.0/24",
  "modules": ["recon", "ports", "cve"],
  "depth": "full"
}
```

## 🎯 How to Use

### Via Web UI
1. Go to **Scan** page
2. Click **"Scan Instructions"** tab
3. Choose a template OR paste JSON
4. Click **"Execute Scan"**
5. Monitor progress in dashboard

### Via curl
```bash
curl -X POST http://localhost:8000/api/scans/json/from-json \
  -H "Content-Type: application/json" \
  -d '{
    "json_instruction": "{\"name\":\"Test\",\"target\":\"192.168.29.48\",\"depth\":\"quick\"}"
  }'
```

### Via Python
```python
import requests
import json

config = {
    "name": "My Scan",
    "target": "192.168.29.48",
    "modules": ["all"],
    "depth": "quick"
}

response = requests.post(
    "http://localhost:8000/api/scans/json/from-json",
    json={"json_instruction": json.dumps(config)}
)

scan = response.json()
print(f"Scan {scan['scan_id']} started: {scan['message']}")
```

## 📚 Available Modules

Choose which tests to run:

| Module | What It Tests | Time |
|--------|---------------|------|
| `xss` | Cross-Site Scripting | 2-5m |
| `sqli` | SQL Injection | 3-5m |
| `csrf` | CSRF/SSRF attacks | 1-3m |
| `idor` | Broken access control | 3-5m |
| `auth` | Authentication issues | 2-5m |
| `headers` | Security headers | 1-2m |
| `file_upload` | File upload vulns | 2-3m |
| `recon` | OSINT/Reconnaissance | 5-10m |
| `ports` | Port scanning | 5-15m |
| `cve` | CVE lookups | 2-5m |
| `all` | Everything | 20-60m |

## 🎨 Scan Depths

| Depth | Coverage | Time | Best For |
|-------|----------|------|----------|
| `quick` | Lightweight testing | 5m | Quick checks |
| `medium` | Standard testing | 15m | Regular scans |
| `full` | Exhaustive testing | 30m+ | Thorough assessments |

## 🛠️ Advanced Options

### Export Results
```json
{
  "name": "Full Scan with Export",
  "target": "target.com",
  "modules": ["all"],
  "depth": "full",
  "export": {
    "formats": ["json", "html", "pdf"],
    "send_email": true,
    "email": "admin@example.com"
  }
}
```

### Notifications
```json
{
  "name": "Scan with Alerts",
  "target": "target.com",
  "modules": ["all"],
  "notifications": {
    "severity_filter": "high",
    "channels": ["desktop", "email"],
    "email": "security@example.com"
  }
}
```

### Custom Scope
```json
{
  "name": "Scoped Scan",
  "target": "192.168.1.1",
  "modules": ["all"],
  "scope": [
    "192.168.1.0/24",
    "10.0.0.0/8"
  ]
}
```

### Authentication
```json
{
  "name": "Authenticated Scan",
  "target": "app.example.com",
  "modules": ["all"],
  "advanced": {
    "auth_type": "bearer",
    "auth_credentials": {
      "token": "your-jwt-token-here"
    }
  }
}
```

## ✅ Validation

### Check if JSON is Valid
```bash
curl -X POST http://localhost:8000/api/scans/json/validate \
  -H "Content-Type: application/json" \
  -d '{
    "json_instruction": "{\"name\":\"Test\",\"target\":\"192.168.29.48\"}"
  }'
```

### Get Schema
```bash
curl http://localhost:8000/api/scans/json/schema | jq
```

### Get Templates
```bash
curl http://localhost:8000/api/scans/json/templates | jq
```

## 🎁 Pre-built Templates

Five templates available in the UI:

1. **Quick Scan** - 5 min, web basics
2. **Standard Scan** - 15 min, ports + web
3. **Full Scan** - 30+ min, everything
4. **Web Focus** - 20 min, intensive web testing
5. **Ports+CVE** - 20 min, infrastructure

## 🔍 Real-World Examples

### Testing Metasploitable2
```json
{
  "name": "Metasploitable2 Full Test",
  "target": "192.168.29.48",
  "modules": ["all"],
  "depth": "full",
  "scope": ["192.168.29.0/24"]
}
```

### CI/CD Integration (Quick Check)
```json
{
  "name": "PR Security Check",
  "target": "https://staging.example.com",
  "modules": ["xss", "sqli", "csrf"],
  "depth": "quick",
  "notifications": {
    "severity_filter": "critical",
    "channels": ["email"],
    "email": "team@example.com"
  }
}
```

### Production Assessment (Thorough)
```json
{
  "name": "Production Security Assessment",
  "target": "https://api.example.com",
  "modules": ["all"],
  "depth": "full",
  "scope": ["api.example.com", "app.example.com"],
  "export": {
    "formats": ["html", "pdf"],
    "send_email": true,
    "email": "ciso@example.com"
  }
}
```

## 🚨 Common Mistakes

❌ **Wrong**: Forgetting target
```json
{ "name": "Scan" }  // Missing target!
```

✅ **Right**: Including both name and target
```json
{ "name": "Scan", "target": "192.168.29.48" }
```

---

❌ **Wrong**: Invalid target format
```json
{ "name": "Test", "target": "example" }  // Invalid!
```

✅ **Right**: Valid target formats
```json
{ "name": "Test", "target": "example.com" }
{ "name": "Test", "target": "192.168.1.1" }
{ "name": "Test", "target": "http://example.com" }
```

---

❌ **Wrong**: Invalid module names
```json
{ "name": "Test", "target": "host", "modules": ["foo", "bar"] }
```

✅ **Right**: Valid module names
```json
{ "name": "Test", "target": "host", "modules": ["xss", "sqli", "csrf"] }
```

## 📊 Response Format

When you submit a JSON scan:

```json
{
  "scan_id": "3f5bd219-ceda-47b1-b600-93bfeba8da10",
  "status": "running",
  "message": "Scan 'Test' started. Target: 192.168.29.48",
  "estimated_time_seconds": 300
}
```

Use `scan_id` to track progress:
```bash
curl http://localhost:8000/api/scans/3f5bd219-ceda-47b1-b600-93bfeba8da10/progress
```

## 🔗 Related Links

- [Full Documentation](./JSON_SCAN_FEATURE_COMPLETE.md)
- [API Reference](./docs/API_REFERENCE.md)
- [Troubleshooting](./JSON_SCAN_FEATURE_COMPLETE.md#troubleshooting)

---

**Status**: ✅ Ready to use  
**Support**: Check logs or open an issue
