# Web Scanner Modules Documentation

Complete reference for all 15 web vulnerability scanning modules in the VAPT Toolkit.

## Module Overview

| # | Module | Purpose | Detection Type | Confidence |
|---|--------|---------|-----------------|------------|
| 1 | **access_control_tester** | IDOR & Privilege Escalation | Behavioral | High-Medium |
| 2 | **auth_tester** | Authentication & Session Management | State Analysis | High-Medium |
| 3 | **business_logic_tester** | Workflow & Business Logic Flaws | Behavioral | Medium |
| 4 | **bulk_scanner** | Multi-target Parallel Scanning | Orchestration | N/A |
| 5 | **cloud_scanner** | Cloud Metadata & Misconfigurations | Endpoint Detection | High-Medium |
| 6 | **confidence_scorer** | Vulnerability Confidence Scoring | Analysis Engine | N/A |
| 7 | **csrf_ssrf_tester** | CSRF & SSRF Vulnerabilities | Token/Endpoint Analysis | High-Medium |
| 8 | **evidence_collector** | Findings Aggregation & Deduplication | Data Processing | N/A |
| 9 | **file_misconfig_tester** | File Upload & Path Traversal | Payload Injection | High-Medium |
| 10 | **fp_pattern_database** | False Positive Pattern Filtering | Pattern Matching | N/A |
| 11 | **injection_tester** | SQLi, Command, NoSQL, LDAP Injection | Payload Testing | High-Medium-Low |
| 12 | **js_analyzer** | JavaScript Secret & API Discovery | Static Analysis | Medium-High |
| 13 | **payloads** | Centralized Payload Library | Data Library | N/A |
| 14 | **ratelimit_tester** | Rate Limiting & Brute Force | Behavioral | Medium |
| 15 | **scope_enforcer** | Scope Validation & robots.txt | Enforcement | N/A |
| 16 | **sensitive_data_tester** | Sensitive Data Exposure Detection | Pattern Matching | High-Medium |
| 17 | **surface_mapper** | Endpoint & Parameter Discovery | Reconnaissance | N/A |
| 18 | **web_logger** | HTTP Request/Response Logging | Data Recording | N/A |
| 19 | **vulnerability_classifier** | Finding Classification & Categorization | Analysis | N/A |
| 20 | **xss_tester** | Cross-Site Scripting Detection | Payload Testing | High-Medium-Low |

---

## Detailed Module Documentation

### 1. **access_control_tester.py**
**Purpose:** Tests for Insecure Direct Object References (IDOR), horizontal privilege escalation, and vertical privilege escalation.

**Key Classes:**
- `IDORDetector` - Automatically discovers identifiers in URLs and parameters
- `IDORTester` - Tests identifier manipulation for access control bypasses
- `PrivilegeEscalationTester` - Tests horizontal/vertical escalation vectors

**Detection Capabilities:**
- Identifier pattern recognition (numeric, UUID, MongoDB ObjectId, alphanumeric)
- IDOR payload generation and testing
- Response comparison for unauthorized access
- Access level differentiation (user vs. admin)

**Confidence Levels:**
- HIGH: Successful unauthorized resource access with different user contexts
- MEDIUM: Partial unauthorized access, error-based IDOR
- LOW: Suspicious patterns requiring manual verification

**Usage Example:**
```python
from scanner.web.access_control_tester import IDORTester

tester = IDORTester()
findings = await tester.test_idor(
    base_url="https://api.example.com",
    endpoints=["/api/users/123", "/api/orders/456"]
)
```

---

### 2. **auth_tester.py**
**Purpose:** Detects authentication and session management vulnerabilities including weak auth, credential reuse, JWT flaws, and session fixation.

**Key Classes:**
- `LoginEndpointDetector` - Finds login/authentication endpoints
- `CredentialTester` - Tests password policies and credential validation
- `SessionAnalyzer` - Analyzes session token security properties
- `JWTAnalyzer` - Detects JWT vulnerabilities (weak signatures, algorithm confusion)

**Detection Capabilities:**
- Login endpoint discovery
- Brute force resistance testing
- Weak credential patterns
- JWT signature algorithm analysis
- Session token property validation (secure, httponly, samesite)
- Account enumeration detection

**Confidence Levels:**
- HIGH: Confirmed weak algorithms, missing security attributes
- MEDIUM: Suspicious patterns, potential enumeration vectors
- LOW: Edge cases requiring validation

**Usage Example:**
```python
from scanner.web.auth_tester import AuthenticationTester

tester = AuthenticationTester()
findings = tester.test_weak_credentials(
    login_url="https://example.com/login",
    test_users=["admin", "user@example.com"]
)
```

---

### 3. **business_logic_tester.py**
**Purpose:** Identifies business logic flaws including workflow bypass, price manipulation, replay attacks, race conditions, and account takeover scenarios.

**Key Classes:**
- `WorkflowAnalyzer` - Detects multi-step workflows and state progression
- `RaceConditionTester` - Tests for concurrent request race conditions
- `ReplayAttackTester` - Tests request replay vulnerability
- `WorkflowBypassTester` - Attempts to skip workflow steps

**Detection Capabilities:**
- Multi-step workflow detection (signup, checkout, password reset)
- Workflow step bypassing
- State manipulation attacks
- Race condition detection through threading
- Price/quantity manipulation testing
- Token/nonce reuse detection

**Confidence Levels:**
- MEDIUM: Successful workflow bypass or state inconsistency
- LOW: Suspicious timing or response variations

**Usage Example:**
```python
from scanner.web.business_logic_tester import BusinessLogicTester

tester = BusinessLogicTester()
findings = tester.test_workflow_bypass(
    base_url="https://shop.example.com",
    workflow_steps=["add_to_cart", "checkout", "payment", "confirm"]
)
```

---

### 4. **bulk_scanner.py**
**Purpose:** Orchestrates parallel scanning of multiple targets with queue management, retry logic, and progress tracking.

**Key Classes:**
- `ScanTask` - Represents individual target scan job
- `BulkScanner` - Manages parallel scan execution and job queue

**Features:**
- Configurable parallelism (default: 10 concurrent scans)
- Priority queue-based scheduling
- Automatic retry with exponential backoff
- Job progress tracking and reporting
- Async callback integration for custom scan logic

**Usage Example:**
```python
from scanner.web.bulk_scanner import BulkScanner, ScanTask

scanner = BulkScanner(max_parallel=10)
tasks = [
    ScanTask(target_id="site1", target_url="https://site1.com", modules=modules_config),
    ScanTask(target_id="site2", target_url="https://site2.com", modules=modules_config),
]
results = await scanner.run_bulk_scan(tasks)
```

---

### 5. **cloud_scanner.py**
**Purpose:** Detects and analyzes cloud provider misconfigurations including AWS metadata endpoints, S3 bucket enumeration, GCP/Azure resource discovery.

**Key Classes:**
- `CloudConfigScanner` - Main cloud detection engine

**Detection Capabilities:**
- AWS metadata endpoint detection (169.254.169.254)
- AWS S3 bucket enumeration and misconfiguration
- GCP bucket discovery and public access validation
- Azure blob storage detection
- Cloud-specific secrets and credentials exposure
- IAM role and instance profile detection

**Confidence Levels:**
- HIGH: Successfully accessed metadata endpoints or public cloud resources
- MEDIUM: Identified cloud endpoints with restricted access
- LOW: Suspicious cloud infrastructure indicators

**Usage Example:**
```python
from scanner.web.cloud_scanner import CloudConfigScanner

scanner = CloudConfigScanner(timeout=5)
findings = scanner.check_aws_metadata(target="http://vulnerable-app.com")
```

---

### 6. **confidence_scorer.py**
**Purpose:** Calculates and manages confidence scores for vulnerability findings based on detection method consistency, vulnerability type, and evidence quality.

**Key Classes:**
- `ConfidenceScorer` - Central scoring engine
- `ConfidenceLevel` - Enum (HIGH, MEDIUM, LOW, SUSPICIOUS)

**Scoring Factors:**
- Detection method (error_based, time_based, union_based, etc.)
- Detection consistency (multiple methods = higher confidence)
- Vulnerability type baseline scores
- Evidence quality and repeatability

**Usage Example:**
```python
from scanner.web.confidence_scorer import ConfidenceScorer, ConfidenceLevel

scorer = ConfidenceScorer()
confidence = scorer.calculate_confidence(
    vuln_type="SQL Injection",
    detection_methods=["error_based", "time_based"],
    evidence_count=3
)
```

---

### 7. **csrf_ssrf_tester.py**
**Purpose:** Detects Cross-Site Request Forgery (CSRF) and Server-Side Request Forgery (SSRF) vulnerabilities.

**Key Classes:**
- `CSRFAnalyzer` - Analyzes CSRF token implementation
- `CSRFTester` - Tests CSRF protection bypass
- `SSRFTester` - Tests SSRF vulnerability vectors

**Detection Capabilities:**
- CSRF token presence and validation checking
- Token static/predictable patterns
- State-change requests without token verification
- SSRF via parameter injection (URLs, IP addresses)
- SSRF to internal services and metadata endpoints
- SSRF via DNS rebinding and timing analysis
- Protocol-specific SSRF (file://, gopher://, etc.)

**Confidence Levels:**
- HIGH: Successful CSRF state change or SSRF to internal resource
- MEDIUM: Missing token or weak token implementation
- LOW: Suspicious patterns requiring verification

**Usage Example:**
```python
from scanner.web.csrf_ssrf_tester import CSRFTester, SSRFTester

csrf_tester = CSRFTester()
csrf_findings = csrf_tester.test_csrf_protection(
    form_url="https://example.com/transfer",
    target_url="https://attacker.com"
)

ssrf_tester = SSRFTester()
ssrf_findings = ssrf_tester.test_ssrf(base_url="https://example.com")
```

---

### 8. **evidence_collector.py**
**Purpose:** Aggregates findings from all testing modules, deduplicates results, manages finding state, and exports evidence.

**Key Classes:**
- `VulnerabilityAggregator` - Collects and deduplicates findings
- `FindingType` - Enum of all vulnerability types
- `FindingSeverity` - Enum (CRITICAL, HIGH, MEDIUM, LOW, INFO)

**Features:**
- Automatic finding deduplication using hash-based comparison
- Severity classification
- Evidence attachment and chain-of-evidence tracking
- Export to JSON, CSV, and other formats
- Bulk finding management and filtering

**Usage Example:**
```python
from scanner.web.evidence_collector import VulnerabilityAggregator

aggregator = VulnerabilityAggregator()
aggregator.add_finding(
    vuln_type="SQL Injection",
    url="https://example.com/search?q=test",
    severity="HIGH",
    evidence=[evidence_obj]
)
deduplicated = aggregator.get_deduplicated_findings()
```

---

### 9. **file_misconfig_tester.py**
**Purpose:** Tests for file upload vulnerabilities, path traversal, local file inclusion (LFI), and security misconfigurations.

**Key Classes:**
- `FileUploadDetector` - Discovers file upload endpoints
- `FileUploadTester` - Tests upload vulnerability vectors
- `SecurityMisconfigurationTester` - Tests security misconfigurations
- `PathTraversalTester` - Tests directory traversal

**Detection Capabilities:**
- File upload endpoint discovery in HTML forms
- Executable file upload (PHP, JSP, ASPX, etc.)
- MIME type bypass techniques
- Path traversal in file parameters (../, ..\\)
- Local File Inclusion (LFI) detection
- File overwrite and race conditions
- Directory listing bypass

**Confidence Levels:**
- HIGH: Successful executable file upload or file system access
- MEDIUM: Partial bypass or suspicious file handling
- LOW: MIME type mismatch or edge cases

**Usage Example:**
```python
from scanner.web.file_misconfig_tester import FileHandlingTester

tester = FileHandlingTester()
findings = tester.test_file_upload(
    upload_url="https://example.com/upload",
    form_field="document"
)
```

---

### 10. **fp_pattern_database.py**
**Purpose:** Manages a database of known false positive patterns to automatically filter out low-confidence findings and improve scan accuracy.

**Key Classes:**
- `FPPatternDatabase` - Pattern storage and matching engine
- `FPPattern` - Individual false positive pattern definition
- `FPPatternType` - Enum of pattern categories

**Pattern Types:**
- Security headers (false XSS positives)
- Framework-specific XSS protection
- CSRF token in framework (false CSRF positives)
- Parameterized SQL (false SQLi positives)
- Rate limit headers (false rate limit detection)
- Sensitive data in design/documentation

**Usage Example:**
```python
from scanner.web.fp_pattern_database import FPPatternDatabase

db = FPPatternDatabase()
adjusted_confidence = db.adjust_finding_confidence(
    finding_type="XSS",
    response_body=response_html,
    detection_method="marker_reflected"
)
```

---

### 11. **injection_tester.py**
**Purpose:** Comprehensive injection testing across multiple vectors: SQL Injection, Command Injection, NoSQL Injection, and LDAP Injection.

**Key Classes:**
- `InjectionTester` - Main async injection testing engine
- `ResponseAnalyzer` - Analyzes injection responses

**Detection Capabilities:**
- SQLi: Error-based, time-based, union-based, boolean-based
- Command Injection: OS command execution detection
- NoSQL Injection: MongoDB, CouchDB specific payloads
- LDAP Injection: LDAP query bypass patterns
- Context-aware payload generation by depth (1-3)
- Response analysis for error messages and time-delays
- Database fingerprinting

**Confidence Levels:**
- HIGH: Union-based or confirmed command execution
- MEDIUM: Time-based or error-based detection
- LOW: Boolean-based or inconsistent results

**Usage Example:**
```python
from scanner.web.injection_tester import InjectionTester

tester = InjectionTester(depth=2, timeout=10)
findings = await tester.test_injection(
    url="https://example.com/search",
    params=["q", "filter"],
    injectable_methods=["GET", "POST"]
)
```

---

### 12. **js_analyzer.py**
**Purpose:** Analyzes JavaScript files for hidden API endpoints, hardcoded secrets, debug code, and security vulnerabilities.

**Key Classes:**
- `JSAnalyzer` - Main JavaScript analysis engine
- `APIEndpoint` - Discovered endpoint from JS
- `SecretType` - Enum of secret types
- `DebugCodeType` - Enum of debug code patterns

**Detection Capabilities:**
- Hidden API endpoint discovery (fetch, axios, XMLHttpRequest calls)
- Hardcoded secrets detection:
  - AWS access keys and secrets
  - GitHub tokens
  - Stripe/payment API keys
  - JWT tokens and Bearer tokens
  - Passwords and authentication strings
- Debug code detection (console.log, debugger statements)
- Source map discovery and analysis
- Security-related TODO/FIXME comments
- Third-party library identification

**Confidence Levels:**
- HIGH: Confirmed API endpoints with known functionality
- MEDIUM: Potential endpoints or high-entropy strings
- LOW: Debug code or informational findings

**Usage Example:**
```python
from scanner.web.js_analyzer import JSAnalyzer

analyzer = JSAnalyzer()
findings = await analyzer.analyze_javascript(
    base_url="https://example.com",
    js_files=["https://example.com/app.js"]
)
```

---

### 13. **payloads.py**
**Purpose:** Centralized payload library with context-aware variants for all vulnerability types. Organized by depth level (1-3) for adaptive testing.

**Payload Categories:**
- SQL Injection (error-based, time-based, union-based, boolean)
- Command Injection (OS-specific payloads)
- NoSQL Injection (MongoDB, CouchDB variants)
- LDAP Injection patterns
- XSS Payloads (HTML, JavaScript, attribute, CSS contexts)
- XXE and XML injection payloads
- PII patterns for data detection
- API key pattern signatures
- Command execution signatures

**Depth Levels:**
- Depth 1: Fast basic detection
- Depth 2: Extended payload variants
- Depth 3: Advanced database fingerprinting

**Usage Example:**
```python
from scanner.web.payloads import SQLI_PAYLOADS, COMMAND_PAYLOADS

# Access depth 2 SQL injection payloads
time_based_sqli = SQLI_PAYLOADS[2]["time_based"]
```

---

### 14. **ratelimit_tester.py**
**Purpose:** Tests for rate limiting and abuse resilience including brute force resistance, API rate limiting, and OTP throttling.

**Key Classes:**
- `RateLimitDetector` - Analyzes rate limit headers and behavior
- `BruteForceResistanceTester` - Tests brute force protection
- `RateLimitingVulnerability` - Enum of vulnerability types

**Detection Capabilities:**
- HTTP rate limit header analysis (X-RateLimit-*, RateLimit-*)
- Brute force resistance testing (login attempts, OTP)
- Rate limit bypass techniques (IP rotation, header manipulation)
- Weak rate limiting (too high thresholds)
- Missing rate limiting on critical endpoints
- Account lockout threshold detection
- Token/OTP throttling analysis

**Confidence Levels:**
- MEDIUM: No rate limiting detected or weak limits (1000+/min)
- LOW: Suspicious rate limit bypass attempt

**Usage Example:**
```python
from scanner.web.ratelimit_tester import RateLimitTester

tester = RateLimitTester()
findings = await tester.test_rate_limiting(
    target_url="https://example.com/api/login",
    request_count=100,
    interval_seconds=60
)
```

---

### 15. **scope_enforcer.py**
**Purpose:** Enforces scanning scope boundaries and respects robots.txt restrictions to ensure authorized testing.

**Key Classes:**
- `ScopeEnforcer` - Validates URLs against authorized scope

**Features:**
- Domain and CIDR range scope validation
- robots.txt parsing and enforcement
- Same-origin verification
- Authorized targets whitelist management
- Scope bypass prevention

**Usage Example:**
```python
from scanner.web.scope_enforcer import ScopeEnforcer

enforcer = ScopeEnforcer(
    base_url="https://example.com",
    authorized_targets=["example.com", "api.example.com"],
    respect_robots_txt=True
)

is_in_scope = await enforcer.is_in_scope("https://api.example.com/users")
```

---

### 16. **sensitive_data_tester.py**
**Purpose:** Detects sensitive data leakage in HTTP responses including PII, credentials, API keys, internal information, and financial data.

**Key Classes:**
- `SensitiveDataDetector` - Pattern-based sensitive data detection
- `DataType` - Enum of data categories
- `SensitiveDataPattern` - Individual pattern definition

**Detection Capabilities:**
- PII: Email, SSN, phone numbers, names
- Credentials: Passwords, authentication tokens
- API Keys: AWS, Stripe, GitHub, Firebase tokens
- Internal Information: IPs, file paths, version numbers
- Financial: Credit card numbers, bank accounts
- Health Information: Medical record numbers
- Government IDs: Passport, license numbers

**Confidence Levels:**
- HIGH: Confirmed sensitive data in response (credit cards, SSN)
- MEDIUM: Partial matches or patterns (email addresses)
- LOW: Version numbers or general internal info

**Usage Example:**
```python
from scanner.web.sensitive_data_tester import SensitiveDataTester

tester = SensitiveDataTester()
findings = tester.test_sensitive_data_exposure(
    base_url="https://example.com",
    endpoints=["/api/profile", "/api/orders"]
)
```

---

### 17. **surface_mapper.py**
**Purpose:** Discovers application surface including endpoints, parameters, forms, and builds attack surface inventory.

**Key Classes:**
- `SurfaceMapper` - Main discovery engine
- `Endpoint` - Discovered endpoint definition
- `Parameter` - URL/form parameter
- `Form` - HTML form definition
- `FormField` - Individual form field

**Features:**
- HTML endpoint discovery (links, form actions)
- JavaScript API endpoint extraction
- JSON parameter parsing
- Form field enumeration (text, file, hidden, etc.)
- Parameter type inference (email, number, file, etc.)
- Relative URL resolution
- Crawling with scope enforcement

**Usage Example:**
```python
from scanner.web.surface_mapper import SurfaceMapper

mapper = SurfaceMapper(base_url="https://example.com")
endpoints = await mapper.discover_endpoints(
    crawl_depth=2,
    respect_scope=True
)
```

---

### 18. **web_logger.py**
**Purpose:** Logs HTTP requests and responses for audit trail and evidence collection.

**Key Classes:**
- `WebVulnerabilityLogger` - Central logging engine
- `HTTPRequest` - Request record
- `HTTPResponse` - Response record

**Features:**
- Request/response capture and formatting
- Sensitive data masking
- Timestamp and correlation ID tracking
- Findings attachment to requests
- Export and reporting integration

**Usage Example:**
```python
from scanner.web.web_logger import WebVulnerabilityLogger

logger = WebVulnerabilityLogger()
logger.log_finding(
    request=http_request,
    response=http_response,
    finding_type="SQL Injection"
)
```

---

### 19. **vulnerability_classifier.py**
**Purpose:** Classifies findings into standardized vulnerability categories and maps to security frameworks (OWASP Top 10, CWE).

**Key Classes:**
- `VulnerabilityClassifier` - Classification engine
- `VulnerabilityCategory` - Enum of categories

**Features:**
- OWASP Top 10 mapping
- CWE/CVSS scoring
- Risk level determination
- Finding grouping and correlation
- Framework-specific categorization

**Usage Example:**
```python
from scanner.web.vulnerability_classifier import VulnerabilityClassifier

classifier = VulnerabilityClassifier()
classification = classifier.classify(finding_type="SQL Injection")
```

---

### 20. **xss_tester.py**
**Purpose:** Comprehensive XSS testing for reflected, stored, and DOM-based vulnerabilities with context-aware payloads.

**Key Classes:**
- `XSSTester` - Main XSS testing engine
- `XSSContext` - Enum (HTML, JavaScript, Attribute, CSS, URL)
- `XSSPayload` - Payload variant with context

**Detection Capabilities:**
- Reflected XSS in URL parameters and forms
- Stored XSS testing (if data storage accessible)
- DOM-based XSS via JavaScript analysis
- Context-aware payload generation (HTML, JS, attribute, CSS, URL)
- Bypass techniques: encoding, null bytes, case manipulation
- Protocol handlers (javascript:, data:, vbscript:)
- Event handler injection (onclick, onerror, onload, etc.)

**Confidence Levels:**
- HIGH: Marker/payload reflected in response
- MEDIUM: Suspicious XSS patterns or weak filters
- LOW: Encoding inconsistencies or false positives

**Usage Example:**
```python
from scanner.web.xss_tester import XSSTester

tester = XSSTester()
findings = await tester.test_xss(
    base_url="https://example.com",
    parameters=["search", "filter", "id"],
    contexts=["HTML", "JAVASCRIPT", "ATTRIBUTE"]
)
```

---

## Dependency Analysis

### External Package Dependencies

| Package | Version | Used By | Purpose |
|---------|---------|---------|---------|
| requests | 2.32.3 | Most testers | HTTP requests |
| aiohttp | 3.10.5 | async modules | Async HTTP |
| beautifulsoup4 | 4.13.0 | surface_mapper | HTML parsing |
| asyncio | builtin | Most testers | Async orchestration |

### Internal Module Dependencies

```
web_scanner_orchestrator.py (main entry point)
├── scope_enforcer.py
├── surface_mapper.py
├── injection_tester.py
├── xss_tester.py
├── auth_tester.py
├── access_control_tester.py (IDOR)
├── csrf_ssrf_tester.py
├── file_misconfig_tester.py
├── sensitive_data_tester.py
├── business_logic_tester.py
├── ratelimit_tester.py
├── js_analyzer.py
├── cloud_scanner.py
├── evidence_collector.py
├── bulk_scanner.py
└── confidence_scorer.py (used by all)
    └── fp_pattern_database.py (optional enhancement)
```

---

## Installation & Setup

### Prerequisites
- Python 3.9+
- All packages in requirements.txt installed

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run web scanner orchestrator
python -c "from scanner.web.web_scanner_orchestrator import WebScannerOrchestrator; print('Imported successfully')"

# Test individual module
python -c "from scanner.web.xss_tester import XSSTester; print('XSSTester loaded')"
```

### Common Issues & Solutions

**Issue: aiohttp import error**
- Solution: Ensure aiohttp 3.10.5+ is installed: `pip install aiohttp==3.10.5`

**Issue: BeautifulSoup4 not found**
- Solution: Install beautifulsoup4: `pip install beautifulsoup4==4.13.0`

**Issue: Circular import in evidence_collector**
- Solution: Module uses lazy loading. If issues occur, ensure vulnerability_classifier.py is present.

---

## Performance Considerations

- **Injection Tester**: Use depth=1 for fast scanning, depth=3 for thorough analysis
- **JS Analyzer**: Can be CPU-intensive for large JS files; consider enabling caching
- **Bulk Scanner**: Adjust max_parallel based on target server rate limits (default: 10)
- **Surface Mapper**: Set crawl_depth=1 for speed, 2-3 for comprehensive mapping

---

## Testing & Validation

All modules are tested via pytest. See test files in `/tests/` directory:

- `tests_js_analyzer.py`
- `tests_injection_tester.py`
- `tests_xss_tester.py`
- `tests_auth_tester.py`
- `tests_scope_manager.py`
- And others...

---

## See Also

- `DELIVERY_SUMMARY.md` - Overall scanner architecture
- `FP_PATTERNS_GUIDE.md` - False positive management
- `CONFIDENCE_SCORING_IMPLEMENTATION.md` - Confidence scoring details
- `BULK_SCANNING_API.md` - Bulk scanning API reference
