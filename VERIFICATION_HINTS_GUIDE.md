# Manual Verification Hints Module

## Overview

The Manual Verification Hints module provides step-by-step guidance for manually verifying automated vulnerability findings. This reduces false positives by giving security analysts detailed verification procedures for each vulnerability type.

## Features

### Backend: VerificationHints Class

Located in \scanner/web/verification_hints.py\, the \VerificationHints\ class provides comprehensive verification guidance for 12 vulnerability types:

#### Supported Vulnerability Types

1. **SQL Injection** - Database query manipulation attacks
2. **Cross-Site Scripting (XSS)** - Client-side script injection
3. **Cross-Site Request Forgery (CSRF)** - Unauthorized state-changing requests
4. **Insecure Direct Object Reference (IDOR)** - Direct access to unauthorized resources
5. **Authentication Flaws** - Authentication bypass and weak mechanisms
6. **Authorization Flaws** - Access control weaknesses
7. **Server-Side Request Forgery (SSRF)** - Server-initiated unauthorized requests
8. **File Upload** - Malicious file upload exploitation
9. **Path Traversal** - Directory traversal and file access
10. **Security Misconfiguration** - Configuration-based vulnerabilities
11. **Business Logic** - Business workflow manipulation
12. **Rate Limiting** - Rate limit bypass

### Hint Structure

Each \VerificationHint\ contains:

- **title**: Name of the vulnerability type
- **description**: Overview of what to verify
- **steps**: Numbered verification steps (typically 7-10 steps)
- **tools**: Recommended tools for verification
- **expected_signs**: Indicators of actual vulnerability
- **false_positive_indicators**: Signs that it might not be a real issue

Example:

\\\python
hint = VerificationHints.get_sql_injection_hints()
# Returns:
# VerificationHint(
#     title="SQL Injection Verification",
#     description="Verify if the application is vulnerable to SQL injection attacks.",
#     steps=[
#         "1. Locate the vulnerable parameter identified in the scan",
#         "2. Try entering a single quote (') and observe the response",
#         ...
#     ],
#     tools=["sqlmap", "Burp Suite", "OWASP ZAP", "curl"],
#     expected_signs=[...],
#     false_positive_indicators=[...]
# )
\\\

## API Endpoints

### Get Verification Hints for a Finding

\\\
GET /api/findings/{finding_id}/hints
\\\

Returns verification hints for a specific finding.

**Response:**
\\\json
{
  "finding_id": "VUL-20240101000000-abc12345",
  "finding_type": "SQL_INJECTION",
  "hints": {
    "title": "SQL Injection Verification",
    "description": "Verify if the application is vulnerable to SQL injection attacks.",
    "steps": [
      "1. Locate the vulnerable parameter identified in the scan",
      "2. Try entering a single quote (') and observe the response",
      ...
    ],
    "tools": ["sqlmap", "Burp Suite", "OWASP ZAP", "curl"],
    "expected_signs": [...],
    "false_positive_indicators": [...]
  }
}
\\\

## Integration with Findings

### WebVulnerabilityFinding Enhancement

The \WebVulnerabilityFinding\ dataclass in \scanner/web/evidence_collector.py\ now includes:

\\\python
@dataclass
class WebVulnerabilityFinding:
    # ... existing fields ...
    verification_hints: Dict[str, Any] = field(default_factory=dict)
\\\

Hints are automatically populated when findings are created:

\\\python
from scanner.web.evidence_collector import WebVulnerabilityFinding

finding = WebVulnerabilityFinding(
    type="SQL_INJECTION",
    severity="High",
    url="https://example.com/search",
    # ... other fields ...
)

# verification_hints are automatically populated!
print(finding.verification_hints)
# {
#     "title": "SQL Injection Verification",
#     "description": "...",
#     "steps": [...],
#     "tools": [...],
#     ...
# }
\\\

## Frontend Integration

### VerificationHints React Component

Located in \rontend/src/components/VerificationHints.jsx\.

**Features:**
- Expandable/collapsible hint display
- Copy-to-clipboard for tools
- Clear separation of steps, tools, and indicators
- Warning styling for false positive indicators
- Responsive design

**Usage:**

\\\jsx
import VerificationHints from './components/VerificationHints';

function FindingDetail({ finding }) {
  return (
    <div>
      <h3>{finding.type}</h3>
      <p>Severity: {finding.severity}</p>
      <VerificationHints finding={finding} />
    </div>
  );
}
\\\

## Usage Examples

### Python Backend

`python
from scanner.web.verification_hints import VerificationHints

# Get hints for a specific type
hints = VerificationHints.get_hints_for_type("XSS")
print(f"Title: {hints.title}")
print(f"Steps: {hints.steps}")

# Get all hints
all_hints = VerificationHints.get_all_hints()
for vuln_type, hint in all_hints.items():
    print(f"{vuln_type}: {hint.title}")

# Access individual fields
sql_hints = VerificationHints.get_sql_injection_hints()
for i, step in enumerate(sql_hints.steps, 1):
    print(f"Step {i}: {step}")
`

### JavaScript/React Frontend

`jsx
import VerificationHints from './components/VerificationHints';

// In a finding details component
<VerificationHints finding={{
  finding_id: 'VUL-20240101000000-abc12345',
  type: 'SQL_INJECTION',
  severity: 'High',
  // ... other fields
}} />
`

### API Usage

`ash
# Get hints for a specific finding
curl -X GET "https://api.example.com/api/findings/VUL-20240101000000-abc12345/hints"

# Response
{
  "finding_id": "VUL-20240101000000-abc12345",
  "finding_type": "SQL_INJECTION",
  "hints": {
    "title": "SQL Injection Verification",
    ...
  }
}
`

## Testing

### Run Tests

\\\ash
pytest tests_verification_hints.py -v
\\\

### Test Coverage

The test suite (\	ests_verification_hints.py\) includes:

- Individual tests for each vulnerability type
- Tests for \get_hints_for_type()\ with valid and invalid types
- Tests for \get_all_hints()\
- Verification that all hints have required fields
- Validation that hints contain meaningful content

## Best Practices

### For Security Analysts

1. **Start with the steps**: Follow the numbered verification steps sequentially
2. **Use recommended tools**: The listed tools are proven for this vulnerability type
3. **Check expected signs**: Verify that you observe the expected indicators
4. **Validate false positives**: Review false positive indicators to confirm it's real
5. **Document findings**: Record the exact payload and response that confirmed the issue

### For Developers

1. **Leverage the API**: Call \/api/findings/{id}/hints\ to display hints in your UI
2. **Display prominently**: Make hints visible alongside finding details
3. **Provide easy copying**: Allow users to copy tools and payloads
4. **Link externally**: Consider linking to OWASP or CWE documentation
5. **Gather feedback**: Collect analyst feedback on hint accuracy and usefulness

## Architecture

`
scanner/web/verification_hints.py
├── VerificationHint (dataclass)
└── VerificationHints (class)
    ├── get_sql_injection_hints()
    ├── get_xss_hints()
    ├── get_csrf_hints()
    ├── get_idor_hints()
    ├── get_authentication_hints()
    ├── get_authorization_hints()
    ├── get_ssrf_hints()
    ├── get_file_upload_hints()
    ├── get_path_traversal_hints()
    ├── get_misconfiguration_hints()
    ├── get_business_logic_hints()
    ├── get_rate_limiting_hints()
    ├── get_hints_for_type(finding_type)
    └── get_all_hints()

scanner/web/evidence_collector.py
└── WebVulnerabilityFinding
    ├── verification_hints (new field)
    └── __post_init__() (enhanced)

server.py
└── @app.get("/api/findings/{finding_id}/hints")

frontend/src/components/VerificationHints.jsx
└── VerificationHints (React component)

tests_verification_hints.py
└── TestVerificationHints (test suite)
`

## Performance Considerations

- Hints are generated on-demand when findings are created (cached in finding object)
- API endpoint searches through projects/scans (consider indexing for large datasets)
- Frontend loads hints only when user expands the section (lazy loading)

## Future Enhancements

- [ ] Add custom hints per organization
- [ ] Machine learning to identify false positives
- [ ] Integration with OWASP/CWE external resources
- [ ] Multilingual hint support
- [ ] Video demonstrations for complex verification steps
- [ ] Historical tracking of hint effectiveness

## Troubleshooting

### Hints not appearing in findings

1. Verify \erification_hints.py\ is in \scanner/web/\
2. Check that \WebVulnerabilityFinding.__post_init__\ has the hint population code
3. Ensure the finding type matches a supported type

### API endpoint returns 404

1. Check that finding_id exists in the project
2. Verify the finding is in web vulnerabilities (not CVE/recon/port findings)
3. Confirm the endpoint path is correct: \/api/findings/{finding_id}/hints\

### React component not loading hints

1. Verify the API endpoint is accessible
2. Check browser console for CORS errors
3. Ensure finding object has \inding_id\ property

## Contributing

When adding new vulnerability types:

1. Create new method in \VerificationHints\ class
2. Add dataclass with all required fields (title, description, steps, tools, etc.)
3. Update \get_hints_for_type()\ mapping
4. Update \get_all_hints()\ method
5. Add unit tests
6. Update this documentation
