# UX Scope Editor Guide

## Overview

The Drag-Drop Scope Editor is an intuitive interface for managing scan scope in the VAPT toolkit. It allows you to define, validate, and organize targets for vulnerability scanning with support for multiple target types, grouping, drag-drop reordering, and preset management.

## Features

### 1. **Target Types**

The editor automatically detects and categorizes targets:

#### **URLs**
- Full HTTP/HTTPS URLs with optional ports and paths
- Examples:
  - `https://example.com`
  - `http://api.example.com:8080/v1`
  - `https://192.168.1.1`

#### **Domains**
- Domain names and subdomains
- Optional port numbers
- Examples:
  - `example.com`
  - `sub.example.com`
  - `api.example.com:3000`
  - `example.co.uk`

#### **IP Addresses**
- IPv4 addresses and CIDR notation
- Examples:
  - `192.168.1.1`
  - `10.0.0.0/8` (CIDR network)
  - `172.16.0.0/12` (Private network)

#### **Wildcards**
- Domain wildcards for matching multiple subdomains
- Examples:
  - `*.example.com` (matches api.example.com, app.example.com, etc.)
  - `*.*.example.com` (matches api.staging.example.com, etc.)

#### **Endpoints**
- API endpoints or paths
- Examples:
  - `/admin/login`
  - `/api/v1/users`

### 2. **Drag-Drop Reordering**

- **Reorder targets** by dragging the drag handle (⋮⋮)
- Useful for setting scan priority or organizing logically
- Visual feedback during drag:
  - Highlight on hover
  - Opacity change while dragging
  - Smooth drop animation

### 3. **Validation**

Real-time validation with clear error messages:

- **URL validation**: Checks scheme (http/https) and hostname
- **IP validation**: Verifies IP format and CIDR notation
- **Domain validation**: Ensures proper domain structure
- **Wildcard validation**: Validates pattern syntax

**Validation is triggered:**
- As you type (real-time)
- When pasting bulk targets
- When importing from file
- When clicking "Validate" button

### 4. **Bulk Operations**

#### **Paste Bulk**
1. Click **"Paste Bulk"** button
2. Paste targets (one per line or comma-separated)
3. Supports comments starting with `#`
4. Click **"Add Targets"** to add all valid targets

Example:
```
# Production environment
https://api.example.com
example.com
*.api.example.com
192.168.1.0/24

# Staging
staging.example.com
10.0.0.0/8
```

#### **Import**
1. Click **"Import"** button
2. Select file (JSON, YAML, TXT, or CSV)
3. Targets are automatically parsed and validated

**Supported formats:**

**JSON:**
```json
{
  "targets": [
    "https://example.com",
    "192.168.1.1"
  ]
}
```

**YAML:**
```yaml
targets:
  - https://example.com
  - 192.168.1.1
  - *.example.com
```

**TXT (or any text file):**
```
https://example.com
192.168.1.1
*.example.com
# Comments are supported
```

### 5. **Presets**

Save and load scope configurations for reuse:

#### **Save Preset**
1. Configure your scope with targets
2. Click **"Presets"** button
3. Enter preset name (e.g., "Production Scope")
4. Click **"Save Current"**
5. Preset is saved and available for future scans

#### **Load Preset**
1. Click **"Presets"** button
2. Select from saved presets
3. Click **"Load"** to apply preset
4. All targets from preset are loaded into editor

**Use cases:**
- Production environment scan scope
- Testing environment targets
- Third-party audit targets
- Regular security assessment targets

### 6. **Export**

Export current scope in multiple formats:

- **JSON**: Machine-readable format for APIs
- **YAML**: Human-readable, supports comments
- **TXT**: Plain text, one target per line

All export formats preserve all target information.

### 7. **Statistics**

Real-time statistics:

- **✓ Valid**: Number of valid targets
- **✕ Errors**: Number of targets with validation errors
- **Target count**: Displayed per group

## Best Practices

### Scope Definition

1. **Be specific**: Define targets explicitly rather than overly broad scopes
   ```
   ✓ Good: api.example.com, app.example.com
   ✗ Bad: *.example.com (too broad)
   ```

2. **Include only authorized targets**: Never add targets you don't have permission to scan
   ```
   ✓ Good: targets you own or have explicit authorization
   ✗ Bad: competitor sites, government systems
   ```

3. **Separate concerns**: Group by environment
   ```
   # Production
   https://api.example.com
   https://app.example.com
   
   # Staging
   https://staging-api.example.com
   ```

4. **Use CIDR for IP ranges**: More efficient than individual IPs
   ```
   ✓ Good: 10.0.0.0/24 (256 addresses)
   ✗ Bad: 10.0.0.1, 10.0.0.2, 10.0.0.3, ... (tedious)
   ```

5. **Document your scope**: Use presets with descriptive names
   ```
   - "Q1 2024 Audit Scope"
   - "Production Critical Assets"
   - "Third-party Integration Test"
   ```

### Performance

1. **Limit scope size**: Smaller scopes scan faster
   - Keep active scans < 50 targets
   - Use passive scan for large scopes

2. **Use port ranges**: Reduce scanning time
   - `top-1000`: Fastest (default)
   - `top-10000`: Moderate
   - `all`: Comprehensive but slow

3. **Optimize wildcard use**: More specific is faster
   ```
   ✓ Fast: *.api.example.com (specific subdomain)
   ✗ Slow: *.example.com (all subdomains)
   ```

### Security

1. **Validate before scanning**: Always click "Validate" before running scan
2. **Review scope carefully**: Ensure all targets are authorized
3. **Save presets securely**: Don't share presets with sensitive targets
4. **Export carefully**: JSON/YAML exports contain full target information

## Scope Syntax Reference

### Valid Target Formats

| Format | Example | Type |
|--------|---------|------|
| HTTPS URL | `https://example.com` | URL |
| HTTP URL | `http://example.com:8080` | URL |
| URL with path | `https://api.example.com/v1` | URL |
| Domain | `example.com` | Domain |
| Subdomain | `api.example.com` | Domain |
| Domain with port | `example.com:3000` | Domain |
| IPv4 address | `192.168.1.1` | IP |
| CIDR notation | `10.0.0.0/8` | IP |
| IPv6 address | `::1` | IP |
| Wildcard domain | `*.example.com` | Wildcard |
| Nested wildcard | `*.api.example.com` | Wildcard |
| Endpoint | `/admin/login` | Endpoint |

### Invalid Targets

| Example | Reason |
|---------|--------|
| `example` | Missing TLD |
| `ftp://example.com` | Unsupported scheme (only http/https) |
| `999.999.999.999` | Invalid IP octets |
| `*.*.*.example.com` | Too many wildcards |
| `-example.com` | Invalid domain syntax |
| `example-.com` | Invalid domain syntax |

## Common Workflows

### 1. Single Target Scan

```
1. Click "Add Target"
2. Enter target (e.g., "https://example.com")
3. Click "Validate"
4. Start scan
```

### 2. Multiple Targets (Bulk Add)

```
1. Click "Paste Bulk"
2. Paste targets (CSV or newline-separated)
3. Verify no errors in validation
4. Click "Add Targets"
5. Click "Validate" for final check
6. Start scan
```

### 3. Import Existing Scope

```
1. Click "Import"
2. Select scope.json or scope.yaml file
3. Review targets in editor
4. Click "Validate"
5. Optionally save as preset for reuse
6. Start scan
```

### 4. Reuse Saved Scope (Preset)

```
1. Click "Presets"
2. Click "Load" on desired preset
3. Targets are automatically populated
4. Optionally modify targets
5. Click "Validate"
6. Start scan
```

### 5. Export Scope for Documentation

```
1. Configure your scope with targets
2. Click "Validate" to ensure all valid
3. Click "JSON" (or YAML/TXT) to export
4. File is downloaded automatically
5. Share or archive for audit trail
```

## Troubleshooting

### "Invalid URL format" Error

**Cause**: URL doesn't start with http:// or https://

**Solution**: Add protocol prefix
```
✗ example.com
✓ https://example.com
```

### "Invalid IP address" Error

**Cause**: IP octets out of range or invalid CIDR

**Solution**: Use valid IP format
```
✗ 999.999.999.999
✓ 192.168.1.1

✗ 192.168.0.0/33
✓ 192.168.0.0/24
```

### "Invalid domain format" Error

**Cause**: Domain contains invalid characters or syntax

**Solution**: Use valid domain syntax
```
✗ -example.com
✓ example.com

✗ example-.com
✓ example.com
```

### "Invalid wildcard pattern" Error

**Cause**: Wildcard syntax is incorrect

**Solution**: Use valid wildcard patterns
```
✗ *.*.*.example.com
✓ *.example.com

✗ *example.com
✓ *.example.com
```

### Targets Not Saving to Preset

**Cause**: Some targets have validation errors

**Solution**: Fix validation errors first
```
1. Check for targets with red background
2. Fix invalid targets
3. Ensure no errors in status
4. Try saving preset again
```

### Import Not Working

**Cause**: File format not supported or invalid JSON/YAML

**Solution**: Ensure file format is correct
```
✓ Supported: .json, .yaml, .yml, .txt, .csv
✗ Not supported: .xlsx, .xml, .pdf

✓ Valid JSON: {"targets": ["example.com"]}
✗ Invalid JSON: {targets: [example.com]}
```

## API Reference

### Scope Validation Endpoint

```
POST /api/scans/scope/validate

Request:
{
  "targets": ["https://example.com", "192.168.1.1"]
}

Response:
{
  "valid": true,
  "errors": [],
  "valid_count": 2,
  "total_count": 2,
  "targets": [...]
}
```

### Scope Presets Endpoint

```
GET /api/scans/scope/presets
Returns list of saved presets

POST /api/scans/scope/presets
Save new preset

DELETE /api/scans/scope/presets/{preset_id}
Delete preset
```

### Scope Export Endpoint

```
POST /api/scans/scope/export

Request:
{
  "targets": ["example.com"],
  "format": "json|yaml|txt"
}

Response:
{
  "format": "json",
  "content": "...",
  "target_count": 1
}
```

## Tips & Tricks

### Speed Tips

- Use keyboard shortcuts to speed up workflow
- Drag-drop is faster than edit for reordering
- Presets avoid re-entering common scopes

### Organization Tips

- Use descriptive preset names with dates
- Group related targets together
- Comment on scope purpose in presets

### Validation Tips

- Always validate before scanning
- Fix errors immediately (easier than debugging later)
- Use validation to catch typos and syntax errors

### Export Tips

- Export scopes for documentation
- Save export in audit trail
- Share scopes with team via exports

## Integration with Scanner

The Scope Editor integrates seamlessly with the VAPT scanner:

1. **Define scope** in editor
2. **Validate targets** before scanning
3. **Start scan** with configured scope
4. **Scanner respects scope** boundaries
5. **Only authorized targets** are scanned

This ensures safe, authorized, and documented scanning operations.
