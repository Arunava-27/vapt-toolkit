# Phase 6 Manual Testing Checklist

## Pre-Testing Phase

### Environment Setup
- [ ] DVWA environment running and accessible
- [ ] WebGoat environment running and accessible
- [ ] Juice Shop environment running and accessible
- [ ] VAPT toolkit API running on port 8000
- [ ] VAPT frontend running on port 5173
- [ ] Network connectivity verified between all services
- [ ] Database initialized and ready
- [ ] API keys generated for testing
- [ ] Test user accounts created
- [ ] Test data loaded

### Tools & Resources
- [ ] Manual testing guide reviewed
- [ ] Test template prepared
- [ ] Screenshot tool available
- [ ] Test tracking spreadsheet created
- [ ] Defect logging template prepared
- [ ] Test environment documentation available
- [ ] Known vulnerabilities documented
- [ ] Payload database prepared

### Team Preparation
- [ ] QA team trained on toolkit features
- [ ] Test scenarios reviewed with team
- [ ] Roles and responsibilities assigned
- [ ] Communication channels established
- [ ] Escalation process defined
- [ ] Test schedule agreed upon

---

## Web Scanning Tests (15)

### Injection Vulnerabilities

#### WS-001: SQL Injection Detection
- [ ] Test execution started
  - [ ] Accessed DVWA SQL injection page
  - [ ] Executed sql_i payload: `' OR '1'='1`
  - [ ] Ran VAPT web scanner
- [ ] Results validation
  - [ ] SQL injection detected: ✓ / ✗
  - [ ] Severity correct (HIGH/CRITICAL): ✓ / ✗
  - [ ] Payload samples provided: ✓ / ✗
- [ ] Evidence
  - [ ] Screenshot captured: [filename]
  - [ ] Notes recorded: [summary]
- [ ] Status: [ ] PASS [ ] FAIL [ ] BLOCKED

#### WS-002: Reflected XSS Detection
- [ ] Test execution started
  - [ ] Found reflected XSS endpoint
  - [ ] Injected XSS payload: `<script>alert('XSS')</script>`
  - [ ] Ran VAPT web scanner
- [ ] Results validation
  - [ ] Reflected XSS detected: ✓ / ✗
  - [ ] Input vector identified: ✓ / ✗
  - [ ] Severity correct (MEDIUM/HIGH): ✓ / ✗
- [ ] Evidence
  - [ ] Screenshot captured: [filename]
  - [ ] Notes recorded: [summary]
- [ ] Status: [ ] PASS [ ] FAIL [ ] BLOCKED

#### WS-003: Stored XSS Detection
- [ ] Test execution started
  - [ ] Found comment/review form
  - [ ] Submitted XSS payload in form
  - [ ] Verified payload stored
  - [ ] Ran VAPT web scanner
- [ ] Results validation
  - [ ] Stored XSS detected: ✓ / ✗
  - [ ] Flagged as persistent: ✓ / ✗
  - [ ] Entry point documented: ✓ / ✗
- [ ] Evidence
  - [ ] Screenshot captured: [filename]
  - [ ] Notes recorded: [summary]
- [ ] Status: [ ] PASS [ ] FAIL [ ] BLOCKED

#### WS-011: Command Injection
- [ ] Test execution started
  - [ ] Found command execution endpoint
  - [ ] Injected command: `; ls -la /`
  - [ ] Ran VAPT web scanner
- [ ] Results validation
  - [ ] Command injection detected: ✓ / ✗
  - [ ] Payload demonstrated: ✓ / ✗
  - [ ] Severity correct (CRITICAL): ✓ / ✗
- [ ] Evidence
  - [ ] Screenshot captured: [filename]
  - [ ] Notes recorded: [summary]
- [ ] Status: [ ] PASS [ ] FAIL [ ] BLOCKED

#### WS-012: XXE Injection (if applicable)
- [ ] Test execution started
  - [ ] Found XML endpoint
  - [ ] Injected XXE payload
  - [ ] Ran VAPT web scanner
- [ ] Results validation
  - [ ] XXE detected: ✓ / ✗
  - [ ] Entity resolution shown: ✓ / ✗
  - [ ] Severity assessed: ✓ / ✗
- [ ] Evidence
  - [ ] Screenshot captured: [filename]
  - [ ] Notes recorded: [summary]
- [ ] Status: [ ] PASS [ ] FAIL [ ] SKIPPED

### Access Control Vulnerabilities

#### WS-004: CSRF Detection
- [ ] Test execution started
  - [ ] Found state-changing endpoint
  - [ ] Verified no CSRF token
  - [ ] Ran VAPT web scanner
- [ ] Results validation
  - [ ] Missing token detected: ✓ / ✗
  - [ ] Endpoint documented: ✓ / ✗
  - [ ] Attack flow described: ✓ / ✗
- [ ] Evidence
  - [ ] Screenshot captured: [filename]
  - [ ] Notes recorded: [summary]
- [ ] Status: [ ] PASS [ ] FAIL [ ] BLOCKED

#### WS-005: IDOR Detection
- [ ] Test execution started
  - [ ] Logged in as user A
  - [ ] Attempted to access user B's resources
  - [ ] Manipulated object IDs
  - [ ] Ran VAPT web scanner
- [ ] Results validation
  - [ ] IDOR vulnerability detected: ✓ / ✗
  - [ ] Resource type documented: ✓ / ✗
  - [ ] ID manipulation shown: ✓ / ✗
- [ ] Evidence
  - [ ] Screenshot captured: [filename]
  - [ ] Notes recorded: [summary]
- [ ] Status: [ ] PASS [ ] FAIL [ ] BLOCKED

#### WS-006: Authentication Bypass
- [ ] Test execution started
  - [ ] Attempted SQL injection bypass: `admin' --`
  - [ ] Tested cookie tampering
  - [ ] Tried session fixation
  - [ ] Ran VAPT web scanner
- [ ] Results validation
  - [ ] Auth bypass vector documented: ✓ / ✗
  - [ ] Weak session management flagged: ✓ / ✗
  - [ ] Severity correct (CRITICAL): ✓ / ✗
- [ ] Evidence
  - [ ] Screenshot captured: [filename]
  - [ ] Notes recorded: [summary]
- [ ] Status: [ ] PASS [ ] FAIL [ ] BLOCKED

### Security Configuration

#### WS-007: Insecure Cookies
- [ ] Test execution started
  - [ ] Captured session cookies
  - [ ] Checked HttpOnly flag
  - [ ] Checked Secure flag
  - [ ] Checked SameSite attribute
- [ ] Results validation
  - [ ] Missing flags identified: ✓ / ✗
  - [ ] Severity assessed: ✓ / ✗
  - [ ] Recommendations provided: ✓ / ✗
- [ ] Evidence
  - [ ] Screenshot captured: [filename]
  - [ ] Notes recorded: [summary]
- [ ] Status: [ ] PASS [ ] FAIL [ ] BLOCKED

#### WS-008: Missing Security Headers
- [ ] Test execution started
  - [ ] Scanned all endpoints
  - [ ] Checked CSP, X-Frame-Options, HSTS
  - [ ] Verified header presence
- [ ] Results validation
  - [ ] Missing headers documented: ✓ / ✗
  - [ ] Severity correct: ✓ / ✗
  - [ ] Impact described: ✓ / ✗
- [ ] Evidence
  - [ ] Screenshot captured: [filename]
  - [ ] Notes recorded: [summary]
- [ ] Status: [ ] PASS [ ] FAIL [ ] BLOCKED

### Input Validation & Encoding

#### WS-009: File Upload Vulnerabilities
- [ ] Test execution started
  - [ ] Uploaded executable file
  - [ ] Tested file size limits
  - [ ] Tried double extensions
  - [ ] Ran VAPT web scanner
- [ ] Results validation
  - [ ] Unrestricted upload detected: ✓ / ✗
  - [ ] Execution vulnerability flagged: ✓ / ✗
  - [ ] Severity correct (CRITICAL): ✓ / ✗
- [ ] Evidence
  - [ ] Screenshot captured: [filename]
  - [ ] Notes recorded: [summary]
- [ ] Status: [ ] PASS [ ] FAIL [ ] BLOCKED

#### WS-010: Path Traversal
- [ ] Test execution started
  - [ ] Attempted: `../../../etc/passwd`
  - [ ] Tried URL encoding variants
  - [ ] Tested double encoding
  - [ ] Ran VAPT web scanner
- [ ] Results validation
  - [ ] Path traversal detected: ✓ / ✗
  - [ ] Access scope shown: ✓ / ✗
  - [ ] Severity correct (HIGH): ✓ / ✗
- [ ] Evidence
  - [ ] Screenshot captured: [filename]
  - [ ] Notes recorded: [summary]
- [ ] Status: [ ] PASS [ ] FAIL [ ] BLOCKED

### Other Vulnerabilities

#### WS-013: SSRF Detection
- [ ] Test execution started
  - [ ] Found URL fetching endpoint
  - [ ] Attempted localhost access
  - [ ] Tried internal services
  - [ ] Ran VAPT web scanner
- [ ] Results validation
  - [ ] SSRF documented: ✓ / ✗
  - [ ] Internal endpoint exposure shown: ✓ / ✗
  - [ ] Severity assessed: ✓ / ✗
- [ ] Evidence
  - [ ] Screenshot captured: [filename]
  - [ ] Notes recorded: [summary]
- [ ] Status: [ ] PASS [ ] FAIL [ ] BLOCKED

#### WS-014: Open Redirect
- [ ] Test execution started
  - [ ] Found redirect parameter
  - [ ] Tested: `?redirect=http://evil.com`
  - [ ] Tried: `?redirect=//attacker.com`
  - [ ] Ran VAPT web scanner
- [ ] Results validation
  - [ ] Open redirect detected: ✓ / ✗
  - [ ] Attack flow documented: ✓ / ✗
  - [ ] Severity correct (MEDIUM): ✓ / ✗
- [ ] Evidence
  - [ ] Screenshot captured: [filename]
  - [ ] Notes recorded: [summary]
- [ ] Status: [ ] PASS [ ] FAIL [ ] BLOCKED

#### WS-015: Information Disclosure
- [ ] Test execution started
  - [ ] Triggered errors
  - [ ] Reviewed HTML comments
  - [ ] Checked response bodies
  - [ ] Ran VAPT web scanner
- [ ] Results validation
  - [ ] Sensitive data items found: ✓ / ✗
  - [ ] Framework info flagged: ✓ / ✗
  - [ ] Severity assessed: ✓ / ✗
- [ ] Evidence
  - [ ] Screenshot captured: [filename]
  - [ ] Notes recorded: [summary]
- [ ] Status: [ ] PASS [ ] FAIL [ ] BLOCKED

---

## API Tests (5)

### API-001: API Key Authentication
- [ ] Generated API key
- [ ] Tested valid key
- [ ] Tested missing key (401 response)
- [ ] Tested invalid key (401 response)
- [ ] Status: [ ] PASS [ ] FAIL

### API-002: Rate Limiting
- [ ] Sent rapid requests
- [ ] Monitored rate limit headers
- [ ] Verified 429 response
- [ ] Checked reset time
- [ ] Status: [ ] PASS [ ] FAIL

### API-003: Bulk Scanning
- [ ] Created bulk job with 5 targets
- [ ] Monitored job status
- [ ] Verified sequential scanning
- [ ] Checked result aggregation
- [ ] Status: [ ] PASS [ ] FAIL

### API-004: Export Functionality
- [ ] Executed scan
- [ ] Exported PDF
- [ ] Exported Excel
- [ ] Exported JSON
- [ ] Verified file integrity
- [ ] Status: [ ] PASS [ ] FAIL

### API-005: Webhook Delivery
- [ ] Registered webhook endpoint
- [ ] Executed scan
- [ ] Verified events received
- [ ] Checked payload content
- [ ] Tested retry logic
- [ ] Status: [ ] PASS [ ] FAIL

---

## Reporting Tests (5)

- [ ] REP-001: PDF generation - [ ] PASS [ ] FAIL
- [ ] REP-002: Excel export - [ ] PASS [ ] FAIL
- [ ] REP-003: Scan comparison - [ ] PASS [ ] FAIL
- [ ] REP-004: Heat map rendering - [ ] PASS [ ] FAIL
- [ ] REP-005: Executive report - [ ] PASS [ ] FAIL

---

## UX Tests (5)

- [ ] UX-001: Scope editor - [ ] PASS [ ] FAIL
- [ ] UX-002: Theme switching - [ ] PASS [ ] FAIL
- [ ] UX-003: Notifications - [ ] PASS [ ] FAIL
- [ ] UX-004: Scheduling - [ ] PASS [ ] FAIL
- [ ] UX-005: Search/Filter - [ ] PASS [ ] FAIL

---

## Post-Testing Phase

### Results Compilation
- [ ] All test cases executed
- [ ] Results documented
- [ ] Screenshots organized
- [ ] Pass/fail rates calculated
- [ ] Test report generated

### Defect Management
- [ ] All defects logged
- [ ] Severity assigned
- [ ] Priority assigned
- [ ] Assigned to developers
- [ ] Tracking established

### Quality Gates
- [ ] Pass rate ≥ 95%: [ ] YES [ ] NO
- [ ] Critical defects resolved: [ ] YES [ ] NO
- [ ] High defects assigned: [ ] YES [ ] NO
- [ ] Medium defects documented: [ ] YES [ ] NO
- [ ] Low defects triaged: [ ] YES [ ] NO

### Sign-Off
- [ ] QA Lead reviewed results
- [ ] Dev Lead reviewed defects
- [ ] PM approved release status
- [ ] Final report approved

---

## Test Summary Statistics

| Metric | Value |
|--------|-------|
| Total Tests Planned | 35 |
| Total Tests Executed | 0 |
| Tests Passed | 0 |
| Tests Failed | 0 |
| Tests Blocked | 0 |
| Pass Rate | 0% |
| Critical Defects | 0 |
| High Defects | 0 |
| Medium Defects | 0 |
| Low Defects | 0 |

---

## Notes & Issues

(To be filled during testing)

---

## Sign-Off

**QA Lead**: _________________ **Date**: ________

**Dev Lead**: _________________ **Date**: ________

**Project Manager**: _________________ **Date**: ________

---

**Checklist Version**: 1.0
**Status**: Ready for Execution
**Last Updated**: 2024-01-15
