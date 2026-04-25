# VAPT Toolkit — Phase 6: Manual Testing Guide

## Executive Summary

This guide defines the comprehensive manual testing strategy for the VAPT (Vulnerability Assessment & Penetration Testing) Toolkit. It covers 30+ test scenarios across web scanning, API functionality, reporting, and user experience.

---

## Table of Contents

1. [Test Strategy Overview](#test-strategy-overview)
2. [Test Environments Setup](#test-environments-setup)
3. [Web Scanning Tests (15 scenarios)](#web-scanning-tests)
4. [API Tests (5 scenarios)](#api-tests)
5. [Reporting Tests (5 scenarios)](#reporting-tests)
6. [UX Tests (5 scenarios)](#ux-tests)
7. [Test Execution Protocol](#test-execution-protocol)
8. [Results Tracking](#results-tracking)
9. [Defect Tracking Template](#defect-tracking-template)

---

## Test Strategy Overview

### Scope
- **Total Test Cases**: 35 scenarios
- **Target Applications**: DVWA, WebGoat, OWASP Juice Shop
- **Testing Focus**: Vulnerability detection, API functionality, reporting accuracy
- **Pass Criteria**: 95%+ pass rate with documented defects

### Testing Phases
1. **Phase 1**: Environment Setup (Days 1-2)
2. **Phase 2**: Web Scanning Tests (Days 3-5)
3. **Phase 3**: API & Backend Tests (Days 6-7)
4. **Phase 4**: Reporting & Analytics Tests (Day 8)
5. **Phase 5**: UX/Integration Tests (Day 9)
6. **Phase 6**: Report & Closure (Day 10)

### Success Metrics
- ✅ 30+ test scenarios executed
- ✅ 95%+ pass rate
- ✅ Critical defects resolved
- ✅ Medium defects documented
- ✅ Test report delivered

---

## Test Environments Setup

### Environment 1: DVWA (Damn Vulnerable Web Application)

#### Purpose
- Classic web vulnerabilities testing platform
- Known vulnerabilities for comparison

#### Installation (Docker)
```bash
# Pull DVWA image
docker pull vulnerables/web-dvwa

# Run DVWA
docker run --rm -it -p 80:80 -p 3306:3306 \
  -e MYSQL_PASS="password" \
  vulnerables/web-dvwa

# Access at http://localhost/DVWA/
# Default: admin / password
```

#### Key Endpoints
- SQL Injection: `/vulnerabilities/sqli/`
- Reflected XSS: `/vulnerabilities/xss_r/`
- Stored XSS: `/vulnerabilities/xss_s/`
- CSRF: `/vulnerabilities/csrf/`
- Command Injection: `/vulnerabilities/exec/`
- File Upload: `/vulnerabilities/upload/`

---

### Environment 2: OWASP WebGoat

#### Purpose
- Security training application with guided lessons
- Tests against multiple vulnerability categories

#### Installation (Docker)
```bash
# Pull WebGoat image
docker pull webgoat/goatandwolf

# Run WebGoat
docker run --rm -it -p 8080:8080 \
  webgoat/goatandwolf

# Access at http://localhost:8080/WebGoat
```

#### Key Lesson Modules
- A1: Broken Access Control
- A2: Cryptographic Failures
- A3: Injection
- A4: Insecure Design
- A5: Security Misconfiguration

---

### Environment 3: OWASP Juice Shop

#### Purpose
- Modern vulnerable web application
- Realistic attack scenarios
- Comprehensive vulnerability coverage

#### Installation (Docker)
```bash
# Pull Juice Shop image
docker pull bkimminich/juice-shop

# Run Juice Shop
docker run --rm -it -p 3000:3000 \
  bkimminich/juice-shop

# Access at http://localhost:3000
```

#### Key Vulnerabilities
- SQL Injection (login, search)
- XSS (product reviews, admin section)
- CSRF (user updates, admin actions)
- IDOR (product reviews, user data)
- Security misconfiguration (open endpoints)

---

## Web Scanning Tests

### Test Case WS-001: SQL Injection Detection

**Environment**: DVWA + Juice Shop
**Target**: Login forms, search parameters

**Procedure**:
1. Start VAPT toolkit and Nmap scanner
2. Target: `http://localhost/DVWA` (DVWA) or `http://localhost:3000` (Juice Shop)
3. Configure web scanner with SQL injection detection enabled
4. Scan login form: `POST /vulnerabilities/sqli/` or `/api/login`
5. Inject: `' OR '1'='1`, `'; DROP TABLE users--`, `1' UNION SELECT--`

**Expected Results**:
- ✓ SQL injection vulnerabilities detected
- ✓ Severity marked as HIGH or CRITICAL
- ✓ Payload examples shown in report
- ✓ Risk assessment provided

**Pass Criteria**: Vulnerability detected with accurate payload samples

---

### Test Case WS-002: Reflected XSS Detection

**Environment**: DVWA, Juice Shop
**Target**: Search forms, user input fields

**Procedure**:
1. Open DVWA `/vulnerabilities/xss_r/` or Juice Shop product search
2. Inject: `<script>alert('XSS')</script>`, `<img src=x onerror=alert('XSS')>`
3. Run VAPT web scanner
4. Scan reflected XSS endpoint

**Expected Results**:
- ✓ Reflected XSS detected
- ✓ Input vectors identified
- ✓ Severity marked as MEDIUM or HIGH
- ✓ Mitigation steps provided

**Pass Criteria**: Vulnerability detected; payload vectors identified

---

### Test Case WS-003: Stored XSS Detection

**Environment**: Juice Shop, WebGoat
**Target**: Comment/review submission forms

**Procedure**:
1. Juice Shop: Add product review with XSS payload
2. WebGoat: Submit story with XSS payload
3. Run VAPT web scanner
4. Verify stored payload executes on retrieval

**Expected Results**:
- ✓ Stored XSS identified as persistent
- ✓ Entry point documented
- ✓ Display point documented
- ✓ Severity: HIGH

**Pass Criteria**: Stored XSS flagged; persistence confirmed

---

### Test Case WS-004: CSRF Detection

**Environment**: Juice Shop, WebGoat
**Target**: State-changing endpoints

**Procedure**:
1. Identify CSRF-vulnerable endpoints (password change, profile update)
2. Verify absence of CSRF tokens
3. Run VAPT web scanner on these endpoints
4. Check for token validation

**Expected Results**:
- ✓ Missing CSRF token detected
- ✓ Endpoint documented
- ✓ Attack flow described
- ✓ Severity: MEDIUM

**Pass Criteria**: CSRF vulnerability documented

---

### Test Case WS-005: IDOR Detection

**Environment**: Juice Shop
**Target**: User data, orders, reviews

**Procedure**:
1. Login as user A
2. Attempt to access other users' resources by manipulating IDs
3. Example: `/api/user/1`, `/api/user/2`, `/api/orders/1`
4. Run VAPT scanner with IDOR detection

**Expected Results**:
- ✓ IDOR vulnerability identified
- ✓ Resource type documented
- ✓ ID manipulation shown
- ✓ Severity: MEDIUM-HIGH

**Pass Criteria**: IDOR vulnerability and attack vector documented

---

### Test Case WS-006: Authentication Bypass

**Environment**: DVWA, WebGoat
**Target**: Login mechanisms

**Procedure**:
1. Attempt SQL injection in login: `admin' --`, `' OR '1'='1`
2. Test cookie tampering
3. Verify session fixation attempts
4. Check password reset flows

**Expected Results**:
- ✓ Auth bypass vectors documented
- ✓ Weak session management flagged
- ✓ Severity: CRITICAL
- ✓ Mitigation recommended

**Pass Criteria**: Authentication issues identified

---

### Test Case WS-007: Insecure Cookies

**Environment**: All three platforms
**Target**: Session cookies

**Procedure**:
1. Capture authentication cookies
2. Check for HttpOnly flag
3. Check for Secure flag
4. Check for SameSite attribute
5. Verify cookie expiration

**Expected Results**:
- ✓ Missing HttpOnly flagged
- ✓ Missing Secure flagged
- ✓ Missing SameSite flagged
- ✓ Long expiration warnings

**Pass Criteria**: Cookie security issues documented

---

### Test Case WS-008: Missing Security Headers

**Environment**: All three platforms
**Target**: HTTP responses

**Procedure**:
1. Scan all endpoints
2. Check for CSP header
3. Check for X-Frame-Options
4. Check for X-Content-Type-Options
5. Check for HSTS
6. Check for Referrer-Policy

**Expected Results**:
- ✓ Each missing header documented
- ✓ Severity assessed
- ✓ Impact described
- ✓ Fix recommended

**Pass Criteria**: Missing headers identified; severity appropriate

---

### Test Case WS-009: File Upload Vulnerabilities

**Environment**: Juice Shop, DVWA
**Target**: File upload forms

**Procedure**:
1. Upload executable file (php, exe, sh)
2. Upload oversized file
3. Upload file with double extension
4. Verify upload restrictions

**Expected Results**:
- ✓ Unrestricted upload detected
- ✓ Execution vulnerability flagged
- ✓ Severity: CRITICAL
- ✓ Mitigation provided

**Pass Criteria**: Upload vulnerability identified

---

### Test Case WS-010: Path Traversal

**Environment**: DVWA, WebGoat
**Target**: File serving endpoints

**Procedure**:
1. Attempt traversal: `../../../etc/passwd`
2. Try: `....//....//....//etc/passwd`
3. Test URL encoding: `..%2F..%2F..%2Fetc%2Fpasswd`
4. Check for directory listing

**Expected Results**:
- ✓ Path traversal vulnerability detected
- ✓ Access scope shown
- ✓ Severity: HIGH
- ✓ Remediation suggested

**Pass Criteria**: Path traversal flagged; scope identified

---

### Test Case WS-011: Command Injection

**Environment**: DVWA
**Target**: Command execution endpoints

**Procedure**:
1. Inject: `; ls`, `| cat /etc/passwd`
2. Try: `&& whoami`, `backtick` execution
3. Attempt command chaining
4. Verify output capture

**Expected Results**:
- ✓ Command injection detected
- ✓ Payload demonstrated
- ✓ Severity: CRITICAL
- ✓ Mitigation recommended

**Pass Criteria**: Command injection vulnerability detected

---

### Test Case WS-012: XXE Injection

**Environment**: WebGoat (if XML endpoints available)
**Target**: XML parsing endpoints

**Procedure**:
1. Submit XXE payload:
   ```xml
   <?xml version="1.0"?>
   <!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
   <root>&xxe;</root>
   ```
2. Attempt external entity resolution
3. Test SSRF via XXE
4. Verify entity expansion limits

**Expected Results**:
- ✓ XXE vulnerability detected
- ✓ Entity resolution shown
- ✓ Severity: HIGH
- ✓ Mitigation provided

**Pass Criteria**: XXE vulnerability flagged (if applicable)

---

### Test Case WS-013: SSRF Detection

**Environment**: Juice Shop (if available), custom endpoints
**Target**: URL fetching endpoints

**Procedure**:
1. Attempt: `http://localhost:8080`
2. Try: `http://127.0.0.1:6379` (internal services)
3. Test with file:// protocol
4. Verify access filtering

**Expected Results**:
- ✓ SSRF vulnerability documented
- ✓ Internal endpoint exposure shown
- ✓ Severity: MEDIUM-HIGH
- ✓ Mitigation recommended

**Pass Criteria**: SSRF vulnerability identified (if applicable)

---

### Test Case WS-014: Open Redirect

**Environment**: Juice Shop
**Target**: Redirect parameters

**Procedure**:
1. Find redirect parameter: `?redirect=`, `?return=`, `?url=`
2. Test: `?redirect=http://evil.com`
3. Try: `?redirect=//attacker.com`
4. Verify domain validation

**Expected Results**:
- ✓ Open redirect detected
- ✓ Attack flow documented
- ✓ Severity: MEDIUM
- ✓ Whitelist recommendation

**Pass Criteria**: Open redirect vulnerability identified

---

### Test Case WS-015: Information Disclosure

**Environment**: All platforms
**Target**: Error messages, comments, debug info

**Procedure**:
1. Trigger errors: Invalid input, database errors
2. Check response bodies for sensitive info
3. Review HTML comments and metadata
4. Examine stack traces

**Expected Results**:
- ✓ Sensitive data in errors documented
- ✓ Framework/version info flagged
- ✓ Comments with secrets highlighted
- ✓ Severity: LOW-MEDIUM

**Pass Criteria**: Information disclosure items identified

---

## API Tests

### Test Case API-001: API Key Authentication

**Environment**: VAPT Toolkit API
**Target**: `POST /api/auth/generate-key`

**Procedure**:
1. Generate API key via dashboard
2. Test with valid key: Include `X-API-Key` header
3. Test without key
4. Test with invalid key
5. Verify rate limiting per key

**Expected Results**:
- ✓ Valid key accepted
- ✓ Missing key rejected (401)
- ✓ Invalid key rejected (401)
- ✓ Rate limit enforced

**Pass Criteria**: API authentication working correctly

---

### Test Case API-002: Rate Limiting

**Environment**: VAPT Toolkit API
**Target**: Any API endpoint

**Procedure**:
1. Send 100 requests in rapid succession
2. Monitor rate limit headers
3. Verify 429 response after limit exceeded
4. Check rate limit reset time

**Expected Results**:
- ✓ Rate limit headers present
- ✓ 429 returned when exceeded
- ✓ Reset time accurate
- ✓ Per-key limits enforced

**Pass Criteria**: Rate limiting functioning

---

### Test Case API-003: Bulk Scanning

**Environment**: VAPT Toolkit API
**Target**: `POST /api/bulk/create`

**Procedure**:
1. Create bulk job with 5 targets
2. Monitor job status: `GET /api/bulk/{job_id}`
3. Verify targets scanned sequentially
4. Check result aggregation

**Expected Results**:
- ✓ Bulk job created successfully
- ✓ Status tracking accurate
- ✓ Results aggregated correctly
- ✓ Job completion reported

**Pass Criteria**: Bulk scanning functioning

---

### Test Case API-004: Export Functionality

**Environment**: VAPT Toolkit API
**Target**: `GET /api/exports/{scan_id}`

**Procedure**:
1. Execute scan
2. Request PDF export: `format=pdf`
3. Request Excel export: `format=xlsx`
4. Request JSON export: `format=json`
5. Verify file integrity

**Expected Results**:
- ✓ PDF generated without errors
- ✓ Excel with proper formatting
- ✓ JSON valid and complete
- ✓ File sizes reasonable

**Pass Criteria**: All export formats working

---

### Test Case API-005: Webhook Delivery

**Environment**: VAPT Toolkit API
**Target**: Webhook endpoints

**Procedure**:
1. Register webhook: `POST /api/webhooks`
2. Execute scan
3. Verify webhook receives events
4. Check event payload
5. Verify retry logic

**Expected Results**:
- ✓ Webhook registered successfully
- ✓ Events delivered on scan events
- ✓ Payload contains required data
- ✓ Retries on failure

**Pass Criteria**: Webhook delivery functioning

---

## Reporting Tests

### Test Case REP-001: PDF Report Generation

**Environment**: VAPT Toolkit Reporter
**Target**: PDF generation pipeline

**Procedure**:
1. Execute full scan
2. Request PDF report generation
3. Download and verify file
4. Check content completeness
5. Verify charts/graphs render

**Expected Results**:
- ✓ PDF generates without errors
- ✓ All sections present
- ✓ Charts display correctly
- ✓ File is valid PDF

**Pass Criteria**: PDF report complete and valid

---

### Test Case REP-002: Excel Export

**Environment**: VAPT Toolkit Reporter
**Target**: Excel generation

**Procedure**:
1. Execute scan
2. Export to Excel
3. Open file in Excel
4. Verify all sheets present
5. Check data integrity

**Expected Results**:
- ✓ Excel file valid
- ✓ All data sheets present
- ✓ Formatting correct
- ✓ No corruption

**Pass Criteria**: Excel export functioning

---

### Test Case REP-003: Scan Comparison

**Environment**: VAPT Toolkit Comparison Module
**Target**: Comparison engine

**Procedure**:
1. Execute scan A on target
2. Execute scan B on same target (later)
3. Request comparison report
4. Verify delta detection
5. Check severity changes

**Expected Results**:
- ✓ New vulnerabilities identified
- ✓ Fixed vulnerabilities marked
- ✓ Severity changes shown
- ✓ Trends analyzed

**Pass Criteria**: Scan comparison accurate

---

### Test Case REP-004: Heat Map Rendering

**Environment**: VAPT Toolkit UI
**Target**: Heat map visualization

**Procedure**:
1. Execute scans across multiple targets
2. View heat map dashboard
3. Check color gradients
4. Verify interactive elements
5. Test filtering options

**Expected Results**:
- ✓ Heat map renders without errors
- ✓ Colors represent severity accurately
- ✓ Interactive features work
- ✓ Data filtered correctly

**Pass Criteria**: Heat map functional

---

### Test Case REP-005: Executive Report

**Environment**: VAPT Toolkit Reporter
**Target**: Executive report generation

**Procedure**:
1. Execute comprehensive scan
2. Generate executive report
3. Verify summary statistics
4. Check risk metrics
5. Verify recommendations

**Expected Results**:
- ✓ Report generates successfully
- ✓ Statistics accurate
- ✓ Risk scoring correct
- ✓ Recommendations provided

**Pass Criteria**: Executive report complete

---

## UX Tests

### Test Case UX-001: Scope Editor Workflow

**Environment**: VAPT Toolkit UI
**Target**: Scope editor interface

**Procedure**:
1. Create new project
2. Add multiple targets
3. Configure include/exclude patterns
4. Save scope configuration
5. Reload and verify persistence

**Expected Results**:
- ✓ Targets added successfully
- ✓ Patterns saved correctly
- ✓ Configuration persists
- ✓ UI responsive

**Pass Criteria**: Scope editor fully functional

---

### Test Case UX-002: Theme Switching

**Environment**: VAPT Toolkit UI
**Target**: Theme selector

**Procedure**:
1. Switch to dark theme
2. Verify all elements visible
3. Switch to light theme
4. Check contrast ratios
5. Reload page and verify persistence

**Expected Results**:
- ✓ Themes switch instantly
- ✓ All text readable
- ✓ Charts display correctly
- ✓ Theme persists

**Pass Criteria**: Theme switching functional

---

### Test Case UX-003: Notification Delivery

**Environment**: VAPT Toolkit
**Target**: Notification system

**Procedure**:
1. Start long-running scan
2. Verify progress notifications
3. Wait for completion notification
4. Check notification content
5. Test notification dismissal

**Expected Results**:
- ✓ Notifications appear timely
- ✓ Content accurate
- ✓ Dismissible properly
- ✓ No missing updates

**Pass Criteria**: Notifications functioning

---

### Test Case UX-004: Schedule Creation/Execution

**Environment**: VAPT Toolkit UI
**Target**: Scheduling interface

**Procedure**:
1. Create recurring scan schedule
2. Set frequency (daily/weekly)
3. Configure targets and modules
4. Verify schedule display
5. Check execution logs

**Expected Results**:
- ✓ Schedule created successfully
- ✓ Executes on time
- ✓ Results logged properly
- ✓ Notifications sent

**Pass Criteria**: Scheduling fully functional

---

### Test Case UX-005: Search/Filter Functionality

**Environment**: VAPT Toolkit UI
**Target**: Search and filter controls

**Procedure**:
1. Execute multiple scans
2. Search by vulnerability type
3. Filter by severity
4. Filter by date range
5. Combine multiple filters

**Expected Results**:
- ✓ Search returns correct results
- ✓ Filters apply instantly
- ✓ Multiple filters combine properly
- ✓ Results update correctly

**Pass Criteria**: Search/filter fully functional

---

## Test Execution Protocol

### Pre-Test Checklist
- [ ] All environments up and running
- [ ] VAPT toolkit started and accessible
- [ ] Test database initialized
- [ ] API keys generated
- [ ] Network connectivity verified
- [ ] Screenshot tool ready

### During Each Test
1. **Record test start time**
2. **Document environment state** (versions, configurations)
3. **Execute test steps exactly as written**
4. **Capture screenshots of results**
5. **Document actual vs expected results**
6. **Note any deviations or issues**
7. **Record test completion time**

### Test Documentation
- Use consistent timestamp format: `YYYY-MM-DD HH:MM:SS UTC`
- Include step-by-step screenshots
- Document payload/request bodies for reproducibility
- Note response codes and headers
- Record any error messages verbatim

---

## Results Tracking

### Test Results Entry Format

```
Test ID: WS-001
Test Name: SQL Injection Detection
Test Date: 2024-01-15
Tester: [Name]
Environment: DVWA

Steps Executed:
1. Navigated to http://localhost/DVWA
2. Opened SQL injection vulnerable page
3. Entered payload: ' OR '1'='1
4. Ran VAPT web scanner

Expected Result:
- SQL injection vulnerability detected
- Severity marked as HIGH
- Payload examples shown

Actual Result:
- SQL injection vulnerability detected ✓
- Severity marked as CRITICAL (higher than expected)
- Payload examples provided ✓

Status: PASS with note
Issues: Severity slightly higher than documented

Screenshots:
- [screenshot1.png]
- [screenshot2.png]
```

### Defect Entry Format

```
Defect ID: DEF-001
Title: SQL Injection severity overestimated
Severity: MEDIUM
Status: NEW

Description:
SQL injection vulnerabilities are being marked as CRITICAL
even when limited to basic injection detection.

Environment: DVWA SQLi page
Reproducible: Yes

Steps to Reproduce:
1. Navigate to SQL injection page
2. Run web scanner
3. Review results

Expected: Severity MEDIUM-HIGH
Actual: Severity CRITICAL

Suggested Fix:
Adjust severity scoring algorithm to account for
exploitation difficulty and data sensitivity.
```

---

## Defect Tracking Template

### Severity Levels
- **CRITICAL**: System crash, authentication bypass, data breach
- **HIGH**: Significant vulnerability, easy exploitation
- **MEDIUM**: Moderate vulnerability, requires specific conditions
- **LOW**: Minor issue, difficult to exploit

### Priority Levels
- **P1**: Block release, fix immediately
- **P2**: Should fix before release
- **P3**: Fix in next iteration
- **P4**: Nice to have, low priority

### Defect Workflow
```
NEW → ASSIGNED → IN PROGRESS → RESOLVED → VERIFIED → CLOSED
```

---

## Test Completion Checklist

- [ ] All 35 test cases executed
- [ ] Results documented for each test
- [ ] Screenshots captured and organized
- [ ] Defects logged and prioritized
- [ ] Pass rate calculated (target: 95%+)
- [ ] Test report generated
- [ ] Critical issues resolved
- [ ] Medium issues documented
- [ ] Team review completed
- [ ] Sign-off obtained

---

## Next Steps After Testing

1. **Analyze Results**: Review pass/fail rates
2. **Prioritize Defects**: Critical → High → Medium
3. **Fix Critical Issues**: Resolve before release
4. **Document Medium Issues**: For next iteration
5. **Generate Report**: Executive summary for stakeholders
6. **Plan Regression Testing**: For fixed issues
7. **Schedule Release**: Upon completion

---

**Document Version**: 1.0
**Last Updated**: 2024-01-15
**Status**: Ready for Execution
