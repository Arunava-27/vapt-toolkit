# JavaScript Analyzer - Comprehensive Documentation

## Overview

The JavaScript Analyzer (`scanner/web/js_analyzer.py`) is a powerful module for analyzing JavaScript files in web applications to discover security issues before they become vulnerabilities.

## Features

### 1. **API Endpoint Discovery**
Automatically extracts hidden API endpoints from JavaScript code by detecting:
- `fetch()` calls
- `axios` HTTP requests
- `jQuery.ajax()` calls
- `XMLHttpRequest.open()` methods
- Spring/Java annotations

**Example:**
```javascript
fetch('/api/users')                    // ✓ Detected
axios.post('/api/admin/config')       // ✓ Detected
$.ajax({url: '/api/sensitive'})       // ✓ Detected
```

### 2. **Hardcoded Secret Detection**
Identifies hardcoded credentials and sensitive tokens:

| Secret Type | Pattern | Severity |
|---|---|---|
| AWS Access Keys | `AKIA[0-9A-Z]{16}` | Critical |
| AWS Secret Keys | `aws_secret_access_key` | Critical |
| GitHub Tokens | `ghp_[A-Za-z0-9_]{36,255}` | High |
| Stripe Keys | `sk_live_[A-Za-z0-9]{20,}` | Critical |
| Slack Tokens | `xox[baprs]-[0-9A-Za-z]{10,48}` | High |
| Firebase Keys | `AIza[0-9A-Za-z\-_]{35}` | Medium |
| JWT Tokens | `eyJ[A-Za-z0-9_-]...` | High |
| Bearer Tokens | `Bearer [token]` | High |
| Generic API Keys | `api_key: '[key]'` | Medium |
| Passwords | `password: '[pwd]'` | Critical |

### 3. **Debug Code Detection**
Finds production code that should be removed:
- `console.log()` / `console.error()` / `console.warn()` / `console.debug()`
- `debugger;` statements
- `alert()` calls
- Commented-out authentication code

### 4. **Source Map Exposure**
Detects potential source map files that expose original source code:
- Checks for `.js.map` files
- Can reveal original variable names, comments, and logic

## Installation & Setup

The analyzer is already integrated into the toolkit:

```python
from scanner.web.js_analyzer import JavaScriptAnalyzer

# Initialize
analyzer = JavaScriptAnalyzer(base_url="https://example.com")
```

## Usage Examples

### Basic Analysis

```python
from scanner.web.js_analyzer import JavaScriptAnalyzer

analyzer = JavaScriptAnalyzer()

# Analyze JavaScript code
js_code = """
const apiKey = 'sk_live_1234567890abcdef';
fetch('/api/users').then(r => r.json());
console.log('debug');
"""

# Extract findings
endpoints = analyzer.extract_endpoints(js_code)
secrets = analyzer.detect_secrets(js_code)
debug = analyzer.find_debug_code(js_code)

print(f"Endpoints: {len(endpoints)}")
print(f"Secrets: {len(secrets)}")
print(f"Debug instances: {len(debug)}")
```

### Converting to Evidence Format

```python
from scanner.web.evidence_collector import WebVulnerabilityFinding

for secret in secrets:
    finding = WebVulnerabilityFinding(
        type="Hardcoded Secrets",
        severity=secret['severity'],
        url="app.js",
        evidence=f"Found {secret['type']} at line {secret['line_number']}",
        module="JavaScript Analyzer",
        confidence_score=85,
    )
    # Finding is now ready for evidence collection
```

### Batch Analysis (Async)

```python
import asyncio
import aiohttp

async def analyze_multiple_files():
    analyzer = JavaScriptAnalyzer()
    js_urls = [
        "https://example.com/app.js",
        "https://example.com/vendor.js",
    ]
    
    async with aiohttp.ClientSession() as session:
        results = await analyzer.analyze_js_urls(
            js_urls,
            session=session,
            progress_cb=lambda msg: print(f"Progress: {msg}")
        )
    
    print(f"Analyzed {results['analyzed_files']} files")
    print(f"Found {results['total_endpoints']} endpoints")
    print(f"Found {results['total_secrets']} secrets")

asyncio.run(analyze_multiple_files())
```

## Severity Levels

### CRITICAL (Action Required Immediately)
- **AWS Access Keys** - Can provide full AWS account access
- **Hardcoded Passwords** - Direct authentication bypass
- **Stripe Live Keys** - Can process real payments

### HIGH (Urgent)
- **GitHub Tokens** - Can access private repositories
- **JWT Tokens** - Can bypass authentication systems
- **AWS Secret Keys** - AWS account compromise
- **Source Maps** - Exposes original source code and logic

### MEDIUM (Important)
- **Generic API Keys** - Depends on API scope
- **Slack Tokens** - Can access Slack workspace
- **Firebase Keys** - Can access Firebase services

### LOW (Informational)
- **Console Logs** - Potential data exposure
- **Debugger Statements** - Should be removed in production
- **Alert Calls** - Poor UX, should be replaced

## Detection Patterns

### Endpoint Patterns
```
fetch('/api/...')
axios.get|post|put|delete('/api/...')
$.ajax({url: '/api/...'})
XMLHttpRequest.open('METHOD', '/api/...')
```

### Secret Patterns
```
AKIA[0-9A-Z]{16}                           # AWS key
ghp_[A-Za-z0-9_]{36,}                      # GitHub token
sk_live_[A-Za-z0-9]{20,}                   # Stripe key
xox[baprs]-[0-9A-Za-z]{10,48}             # Slack token
AIza[0-9A-Za-z\-_]{35}                     # Firebase key
Bearer [A-Za-z0-9\-._~+/]+=*              # Bearer token
eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}  # JWT token
```

### Debug Patterns
```
console.log|error|warn|debug(
debugger;
alert(
// auth|token|password|apiKey
```

## Output Structure

### Analysis Result Format
```json
{
  "file_url": "https://example.com/app.js",
  "endpoints": [
    {
      "url": "/api/users",
      "method": "GET",
      "line_number": 15,
      "source_pattern": "fetch",
      "context": "const users = await fetch('/api/users')"
    }
  ],
  "secrets": [
    {
      "type": "AWS Access Key",
      "match": "AKIA...",
      "line_number": 3,
      "context": "const key = 'AKIAIOSFODNN7EXAMPLE';",
      "severity": "Critical"
    }
  ],
  "debug_code": [
    {
      "type": "console.log",
      "line_number": 20,
      "code": "console.log('debug info');"
    }
  ],
  "source_maps": [
    {
      "potential_map": "https://example.com/app.js.map",
      "severity": "High"
    }
  ]
}
```

## Integration Points

### With Surface Mapper
The surface mapper discovers JavaScript file URLs, which can be passed to the analyzer:
```python
# From surface_mapper
js_urls = surface_mapper._javascript_urls

# To js_analyzer
analyzer = JavaScriptAnalyzer()
results = await analyzer.analyze_js_urls(js_urls)
```

### With Evidence Collector
Findings are converted to standardized findings for reporting:
```python
# Create evidence findings
for endpoint in results['endpoints']:
    finding = WebVulnerabilityFinding(...)
    evidence_collector.add_finding(finding)
```

## Performance Considerations

- **File Size**: Efficiently handles files up to several MB
- **Concurrency**: Use async functions for multiple files
- **Timeout**: Default 10 seconds per file (configurable)
- **Memory**: Minimal memory footprint, suitable for large-scale scanning

## Limitations & Future Improvements

### Current Limitations
1. Doesn't execute JavaScript (no `eval` or dynamic code analysis)
2. Minified/obfuscated code is harder to analyze
3. Webpack/bundler-generated code may have false patterns
4. Template literals with computed values may be missed

### Potential Improvements
- AST parsing for more accurate detection
- Machine learning-based secret detection
- Dynamic code execution sandbox
- WebAssembly module analysis
- CSS/HTML embedded in JavaScript

## Testing

Run the test suites to verify functionality:

```bash
# Unit tests (all detection patterns)
python tests_js_analyzer.py

# Integration tests (with evidence collector)
python tests_js_analyzer_integration.py

# Usage examples
python js_analyzer_examples.py
```

## Class Reference

### JavaScriptAnalyzer

#### Methods

**`__init__(base_url: str = "", timeout: int = 10)`**
- Initialize analyzer
- Args: base_url (for relative URL resolution), timeout (seconds)

**`analyze_js_file(js_content: str, file_url: str = "") -> Dict`**
- Analyze single JavaScript file
- Returns: Dictionary with endpoints, secrets, debug_code, source_maps

**`extract_endpoints(js_content: str) -> List[Dict]`**
- Extract API endpoints
- Returns: List of endpoint dictionaries

**`detect_secrets(js_content: str) -> List[Dict]`**
- Detect hardcoded secrets
- Returns: List of secret dictionaries with type, match, severity

**`find_debug_code(js_content: str) -> List[Dict]`**
- Find debug code instances
- Returns: List of debug code dictionaries

**`check_source_maps(file_url: str) -> List[Dict]`**
- Check for potential source map exposure
- Returns: List of potential source maps

**`async analyze_js_urls(js_urls: List[str], session, progress_cb) -> Dict`**
- Analyze multiple JavaScript files from URLs
- Returns: Combined analysis results

**`get_severity_summary(analysis: Dict) -> Dict`**
- Get summary of findings by severity
- Returns: Dictionary with counts by severity level

## Security Implications

### Why This Matters
1. **Endpoint Discovery**: Reveals hidden APIs not documented in public APIs
2. **Credential Exposure**: Hardcoded secrets can lead to account compromise
3. **Debug Information**: Can leak sensitive data or aid attackers
4. **Source Maps**: Allow attackers to understand original code logic

### Remediation
- Remove all hardcoded secrets (use environment variables)
- Use API documentation, don't expose endpoints in frontend code
- Remove all `console.log` and `debugger` statements before production
- Never ship source maps to production

## Contributing

To add new detection patterns:

1. Add pattern to `_endpoint_patterns`, `_secret_patterns`, or `_debug_patterns`
2. Add test case in `tests_js_analyzer.py`
3. Document in this README
4. Test with real-world JavaScript samples

## License

Part of VAPT Toolkit
