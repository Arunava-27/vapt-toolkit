"""Response analysis and vulnerability fingerprinting."""
import re
from typing import Optional, Tuple, List
from .payloads import SQLI_ERROR_SIGNATURES, COMMAND_EXEC_SIGNATURES, PII_PATTERNS, API_KEY_PATTERNS


class ResponseAnalyzer:
    """Analyze HTTP responses for vulnerability indicators."""

    def __init__(self, timeout_threshold: float = 2.0):
        """
        Initialize analyzer.
        
        Args:
            timeout_threshold: Minimum response time (seconds) to indicate time-based blind injection
        """
        self.timeout_threshold = timeout_threshold

    # ── SQL Injection Detection ───────────────────────────────────────────────

    def detect_sqli_error(self, response_text: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Detect SQL error in response.
        
        Returns: (is_vulnerable, error_type, signature_matched)
        """
        response_lower = response_text.lower()
        for db_type, signatures in SQLI_ERROR_SIGNATURES.items():
            for sig in signatures:
                if sig in response_lower:
                    return True, db_type, sig
        return False, None, None

    def detect_sqli_time_based(self, response_time: float, baseline_time: float) -> bool:
        """Detect time-based blind SQL injection by comparing response times."""
        time_diff = response_time - baseline_time
        return time_diff >= self.timeout_threshold

    def detect_sqli_boolean(self, response_true: str, response_false: str, threshold: float = 0.7) -> bool:
        """Detect boolean-based blind SQL injection by comparing responses."""
        if not response_true or not response_false:
            return False
        true_len = len(response_true)
        false_len = len(response_false)
        if false_len == 0:
            return False
        ratio = true_len / false_len
        return abs(ratio - 1.0) > (1.0 - threshold)

    def detect_sqli_union(self, response_text: str) -> bool:
        """Detect UNION-based SQL injection by looking for injected data."""
        markers = ["NULL", "test", "admin"]
        return any(marker in response_text for marker in markers)

    # ── Command Injection Detection ───────────────────────────────────────────

    def detect_command_exec(self, response_text: str) -> Tuple[bool, Optional[str]]:
        """
        Detect command execution in response.
        
        Returns: (is_vulnerable, os_type)
        """
        for os_type, signatures in COMMAND_EXEC_SIGNATURES.items():
            for sig in signatures:
                if sig in response_text:
                    return True, os_type
        return False, None

    # ── XSS Detection ────────────────────────────────────────────────────────

    def detect_xss_reflected(self, response_text: str, payload: str) -> bool:
        """Detect reflected XSS by checking if payload appears in response."""
        return payload in response_text

    def detect_xss_context(self, response_text: str, payload: str) -> Optional[str]:
        """
        Detect XSS context type in HTML.
        
        Returns: "html", "attribute", "js", "css", or None
        """
        if f">{payload}<" in response_text or f" {payload}<" in response_text:
            return "html"
        if f'"{payload}' in response_text or f"'{payload}" in response_text:
            return "attribute"
        if f"({payload}" in response_text or f"={payload}" in response_text:
            return "js"
        if f":{payload}" in response_text or f"url({payload}" in response_text:
            return "css"
        return None

    # ── CSRF Detection ──────────────────────────────────────────────────────

    def detect_csrf_token(self, response_text: str) -> List[str]:
        """Detect CSRF tokens in response."""
        patterns = [
            r'<input[^>]*name=["\']?csrf["\']?[^>]*value=["\']?([^"\'> ]+)',
            r'<input[^>]*name=["\']?_token["\']?[^>]*value=["\']?([^"\'> ]+)',
            r'<input[^>]*name=["\']?authenticity_token["\']?[^>]*value=["\']?([^"\'> ]+)',
            r'<meta[^>]*name=["\']?csrf-token["\']?[^>]*content=["\']?([^"\'> ]+)',
        ]
        tokens = []
        for pattern in patterns:
            matches = re.findall(pattern, response_text, re.IGNORECASE)
            tokens.extend(matches)
        return tokens

    # ── Security Header Detection ────────────────────────────────────────────

    def check_security_headers(self, headers: dict) -> dict:
        """Check for presence of security headers."""
        header_lower = {k.lower(): v for k, v in headers.items()}
        return {
            "hsts": "strict-transport-security" in header_lower,
            "csp": "content-security-policy" in header_lower,
            "x_frame_options": "x-frame-options" in header_lower,
            "x_content_type": "x-content-type-options" in header_lower,
            "referrer_policy": "referrer-policy" in header_lower,
        }

    # ── Sensitive Data Detection ─────────────────────────────────────────────

    def detect_pii(self, response_text: str) -> dict:
        """Detect PII patterns in response."""
        findings = {}
        for pii_type, pattern in PII_PATTERNS.items():
            matches = re.findall(pattern, response_text)
            if matches:
                findings[pii_type] = len(matches)
        return findings

    def detect_api_keys(self, response_text: str) -> dict:
        """Detect API key patterns in response."""
        findings = {}
        for key_type, pattern in API_KEY_PATTERNS.items():
            matches = re.findall(pattern, response_text)
            if matches:
                findings[key_type] = len(matches)
        return findings

    # ── Open Redirect Detection ──────────────────────────────────────────────

    def detect_open_redirect(self, status_code: int, headers: dict, payload: str) -> bool:
        """Detect open redirect by checking Location header."""
        if status_code in (301, 302, 303, 307, 308):
            location = headers.get("Location", "")
            return payload in location
        return False

    # ── Path Traversal Detection ────────────────────────────────────────────

    def detect_path_traversal(self, response_text: str) -> bool:
        """Detect file system content in response (path traversal success)."""
        signatures = [
            "root:x:",
            "[fonts]",
            "[drivers]",
            "/bin/bash",
            "C:\\",
            "Windows\\System32",
        ]
        return any(sig in response_text for sig in signatures)

    # ── SSRF Detection ───────────────────────────────────────────────────────

    def detect_ssrf(self, response_time: float, status_code: int, response_text: str) -> dict:
        """
        Detect SSRF indicators.
        
        Returns: {is_vulnerable, evidence}
        """
        evidence = []
        
        # Quick response indicates internal service
        if response_time < 0.1 and status_code == 200:
            evidence.append("Quick response (possible internal service)")
        
        # 400/500 errors on SSRF attempts
        if status_code in (400, 401, 403, 404, 500):
            evidence.append(f"Status {status_code} on internal URL attempt")
        
        # Metadata service responses
        if "roles" in response_text and "Access key" in response_text:
            evidence.append("AWS metadata service response detected")
        
        return {
            "is_vulnerable": len(evidence) > 0,
            "evidence": evidence,
        }

    # ── IDOR Detection ───────────────────────────────────────────────────────

    def detect_idor(self, own_response: str, other_response: str, threshold: float = 0.5) -> Tuple[bool, float]:
        """
        Detect IDOR by comparing responses from different user IDs.
        
        Returns: (is_vulnerable, similarity_score)
        """
        own_len = len(own_response)
        other_len = len(other_response)
        
        if own_len == 0 or other_len == 0:
            return False, 0.0
        
        min_len = min(own_len, other_len)
        max_len = max(own_len, other_len)
        
        # Calculate similarity
        similarity = min_len / max_len
        
        # IDOR if responses are similar (accessing other user's data)
        return similarity > threshold, similarity

    # ── Brute Force Detection ────────────────────────────────────────────────

    def detect_rate_limiting(self, status_code: int, headers: dict) -> dict:
        """Detect rate limiting from response."""
        findings = {
            "is_rate_limited": status_code == 429,
            "headers": {},
        }
        
        rate_limit_headers = [
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
            "Retry-After",
        ]
        
        for header in rate_limit_headers:
            for h_name, h_value in headers.items():
                if h_name.lower() == header.lower():
                    findings["headers"][header] = h_value
        
        return findings

    # ── File Upload Detection ────────────────────────────────────────────────

    def detect_file_upload_form(self, response_text: str) -> List[str]:
        """Detect file upload forms in response."""
        # Find multipart/form-data forms
        pattern = r'<form[^>]*enctype=["\']?multipart/form-data["\']?[^>]*>'
        matches = re.findall(pattern, response_text, re.IGNORECASE)
        return [m for m in matches]

    def detect_file_execution_risk(self, filename: str) -> Tuple[bool, str]:
        """Detect if uploaded file could be executed."""
        risky_extensions = [
            ".php", ".phtml", ".php3", ".php4", ".php5", ".phar",
            ".jsp", ".jspx", ".jsw", ".jsv", ".jspf",
            ".asp", ".aspa", ".cer", ".asa",
            ".exe", ".dll", ".sh", ".bash", ".pl", ".py",
        ]
        
        filename_lower = filename.lower()
        for ext in risky_extensions:
            if filename_lower.endswith(ext):
                return True, ext
        
        return False, ""

    # ── Directory Listing Detection ──────────────────────────────────────────

    def detect_directory_listing(self, response_text: str) -> bool:
        """Detect if response is a directory listing."""
        patterns = [
            r'<title>.*?Index of',
            r'href=["\']?\?N=[A-Z]',  # Apache sorting links
            r'\[.+?\].*\d+',  # Directory listing format
        ]
        for pattern in patterns:
            if re.search(pattern, response_text, re.IGNORECASE):
                return True
        return False

    # ── NoSQL Injection Detection ────────────────────────────────────────────

    def detect_nosql_injection(self, response_text: str) -> bool:
        """Detect NoSQL injection indicators."""
        indicators = [
            "TypeError",
            "SyntaxError",
            "Unexpected token",
            "MongoError",
            "CouchDB",
            "ReferenceError",
        ]
        return any(ind in response_text for ind in indicators)
