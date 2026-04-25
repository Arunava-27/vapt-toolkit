"""
CSRF & SSRF Testing Module

Tests for Cross-Site Request Forgery (CSRF) vulnerabilities and 
Server-Side Request Forgery (SSRF) vulnerabilities.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import requests
import logging
from urllib.parse import urljoin, urlparse, parse_qs
import time
from .confidence_scorer import ConfidenceScorer, ConfidenceLevel

logger = logging.getLogger(__name__)


class RequestType(Enum):
    """Types of HTTP requests"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class CSRFTokenType(Enum):
    """Types of CSRF protection mechanisms"""
    TOKEN = "token"  # Anti-CSRF token
    HEADER = "header"  # X-CSRF-Token, X-Requested-With
    ORIGIN = "origin"  # Origin/Referer validation
    SAMESITE = "samesite"  # SameSite cookie attribute
    NONE = "none"  # No protection


@dataclass
class CSRFToken:
    """Represents a CSRF token"""
    name: str  # Parameter or header name
    value: str
    token_type: CSRFTokenType
    expires: int = 0  # 0 = session-wide


class CSRFAnalyzer:
    """Analyzes requests for CSRF vulnerabilities"""

    STATE_CHANGING_METHODS = ["POST", "PUT", "DELETE", "PATCH"]

    @staticmethod
    def extract_csrf_token(response_text: str, form_html: str = None) -> Optional[CSRFToken]:
        """
        Extract CSRF token from response.
        Looks for common patterns: _token, csrf_token, token, __RequestVerificationToken
        """
        token_patterns = [
            (r'<input[^>]*name=["\']?(_token|csrf_token|csrfToken|__RequestVerificationToken)["\']?[^>]*value=["\']?([^"\'>\s]+)', "token"),
            (r'<input[^>]*value=["\']?([^"\'>\s]+)["\']?[^>]*name=["\']?(_token|csrf_token|csrfToken)["\']?', "token"),
            (r'token\s*[:=]\s*["\']?([a-f0-9]{32,})["\']?', "token"),
            (r'X-CSRF-Token\s*[:=]\s*["\']?([a-f0-9]{32,}|[\w\-]+)["\']?', "header"),
        ]

        search_text = form_html or response_text

        for pattern, token_type in token_patterns:
            match = re.search(pattern, search_text, re.IGNORECASE)
            if match:
                if len(match.groups()) >= 2:
                    name = match.group(1) or match.group(2)
                    value = match.group(2) or match.group(1)
                else:
                    value = match.group(1)
                    name = "token"

                token = CSRFToken(
                    name=name,
                    value=value,
                    token_type=CSRFTokenType.TOKEN if token_type == "token" else CSRFTokenType.HEADER
                )
                return token

        return None

    @staticmethod
    def find_state_changing_forms(html_content: str, base_url: str) -> List[Dict[str, Any]]:
        """
        Find forms that perform state changes (POST, PUT, DELETE).
        
        Returns list of form metadata: {method, action, fields, csrf_protection}
        """
        forms = []

        # Find all forms
        form_pattern = r'<form[^>]*>(.*?)</form>'
        for form_match in re.finditer(form_pattern, html_content, re.IGNORECASE | re.DOTALL):
            form_html = form_match.group(0)
            form_content = form_match.group(1)

            # Extract method
            method_match = re.search(r'method=["\']?(\w+)["\']?', form_html, re.IGNORECASE)
            method = method_match.group(1).upper() if method_match else "POST"

            # Only care about state-changing methods
            if method not in CSRFAnalyzer.STATE_CHANGING_METHODS:
                continue

            # Extract action
            action_match = re.search(r'action=["\']?([^"\'\s>]+)', form_html, re.IGNORECASE)
            action = action_match.group(1) if action_match else ""

            # Extract fields
            fields = {}
            input_pattern = r'<input[^>]*name=["\']?([^"\'\s>]+)["\']?'
            for inp_match in re.finditer(input_pattern, form_content, re.IGNORECASE):
                fields[inp_match.group(1)] = "text"

            # Check for CSRF token
            csrf_token = CSRFAnalyzer.extract_csrf_token(html_content, form_html)

            forms.append({
                "method": method,
                "action": urljoin(base_url, action) if action else base_url,
                "fields": fields,
                "csrf_token": csrf_token,
                "has_csrf_protection": csrf_token is not None,
                "raw_html": form_html[:200],  # Truncate for storage
            })

        return forms

    @staticmethod
    def check_csrf_token_freshness(response_before: requests.Response,
                                   response_after: requests.Response) -> Tuple[bool, str]:
        """
        Check if CSRF tokens are per-request or session-wide.
        
        Returns (tokens_differ, evidence)
        """
        token_before = CSRFAnalyzer.extract_csrf_token(response_before.text)
        token_after = CSRFAnalyzer.extract_csrf_token(response_after.text)

        if token_before and token_after:
            if token_before.value != token_after.value:
                return True, "Tokens differ between requests (per-request protection)"
            else:
                return False, "Tokens are identical (session-wide protection)"

        return False, "Could not extract tokens for comparison"

    @staticmethod
    def check_origin_validation(url: str, cookies: Dict[str, str] = None,
                               timeout: float = 10.0, verify_ssl: bool = True) -> Tuple[bool, str]:
        """
        Check if server validates Origin/Referer headers.
        
        Returns (validates_origin, evidence)
        """
        try:
            # First request with valid origin
            valid_headers = {
                "Origin": urlparse(url).netloc,
                "User-Agent": "VAPT-Scanner/1.0",
            }

            resp_valid = requests.get(url, headers=valid_headers, cookies=cookies,
                                     timeout=timeout, verify=verify_ssl)

            # Second request with spoofed origin
            spoofed_headers = {
                "Origin": "https://malicious.com",
                "User-Agent": "VAPT-Scanner/1.0",
            }

            resp_spoofed = requests.get(url, headers=spoofed_headers, cookies=cookies,
                                       timeout=timeout, verify=verify_ssl)

            # Compare responses
            if resp_valid.status_code == 200 and resp_spoofed.status_code >= 400:
                return True, "Server rejects requests with spoofed Origin header"

            if resp_valid.status_code == resp_spoofed.status_code:
                return False, "Server doesn't validate Origin header (vulnerable)"

            return False, "Origin validation unclear"

        except requests.RequestException as e:
            logger.debug(f"Origin validation check failed: {e}")
            return False, f"Request failed: {e}"

    @staticmethod
    def check_samesite_cookie(cookies: Dict[str, str], response_headers: Dict[str, str]) -> Tuple[bool, str]:
        """
        Check if cookies have SameSite protection.
        
        Returns (has_samesite, evidence)
        """
        set_cookie = response_headers.get("Set-Cookie", "")

        if "SameSite" in set_cookie:
            if "SameSite=None" in set_cookie:
                return False, "SameSite=None allows cross-site requests"
            return True, f"SameSite protection found: {set_cookie}"

        return False, "No SameSite protection on session cookies"


class SSRFDetector:
    """Detects potential SSRF vulnerabilities"""

    # Common SSRF endpoints
    SSRF_PATHS = [
        "/image", "/proxy", "/fetch", "/download", "/export",
        "/load", "/url", "/read", "/get", "/data",
        "/api/image", "/api/proxy", "/api/fetch", "/api/download",
    ]

    # Internal addresses to test
    INTERNAL_URLS = [
        "http://localhost/",
        "http://127.0.0.1/",
        "http://169.254.169.254/",  # AWS metadata
        "http://10.0.0.1/",
        "http://192.168.1.1/",
        "file:///etc/passwd",  # Local file access
    ]

    @staticmethod
    def find_ssrf_endpoints(base_url: str, html_content: str = None,
                           timeout: float = 5.0, verify_ssl: bool = True) -> List[str]:
        """
        Find endpoints that might be vulnerable to SSRF.
        Looks for URL parameters and common patterns.
        """
        endpoints = []

        # Strategy 1: Check common SSRF paths
        parsed_base = urlparse(base_url)
        base_domain = f"{parsed_base.scheme}://{parsed_base.netloc}"

        for path in SSRFDetector.SSRF_PATHS:
            test_url = urljoin(base_domain, path)
            try:
                resp = requests.head(test_url, timeout=timeout, verify=verify_ssl)
                if resp.status_code < 400:
                    endpoints.append(test_url)
            except requests.RequestException:
                pass

        # Strategy 2: Parse HTML for URL parameters
        if html_content:
            # Look for forms with "url" or "image" parameters
            form_pattern = r'<form[^>]*>(.*?)</form>'
            for form_match in re.finditer(form_pattern, html_content, re.IGNORECASE | re.DOTALL):
                form_html = form_match.group(0)

                # Check for URL/image inputs
                if any(kw in form_html.lower() for kw in ["url", "image", "proxy", "fetch", "download"]):
                    action_match = re.search(r'action=["\']?([^"\'\s>]+)', form_html, re.IGNORECASE)
                    if action_match:
                        form_url = urljoin(base_domain, action_match.group(1))
                        if form_url not in endpoints:
                            endpoints.append(form_url)

        return endpoints

    @staticmethod
    def generate_ssrf_payloads() -> List[Dict[str, Any]]:
        """Generate SSRF test payloads"""
        return [
            {
                "url": "http://localhost/admin",
                "type": "localhost",
                "description": "Local admin panel"
            },
            {
                "url": "http://127.0.0.1:8080/",
                "type": "localhost_alt_port",
                "description": "Alternative port on localhost"
            },
            {
                "url": "http://169.254.169.254/latest/meta-data/",
                "type": "aws_metadata",
                "description": "AWS metadata service"
            },
            {
                "url": "http://10.0.0.1/admin",
                "type": "internal_network",
                "description": "Internal network address"
            },
            {
                "url": "file:///etc/passwd",
                "type": "local_file",
                "description": "Local file access attempt"
            },
            {
                "url": "http://localhost/../../admin",
                "type": "path_traversal",
                "description": "Path traversal attack"
            },
        ]

    @staticmethod
    def detect_ssrf_response(response: requests.Response, payload: str) -> Tuple[bool, str]:
        """
        Detect if SSRF payload was processed.
        
        Returns (is_vulnerable, evidence)
        """
        # Check for success indicators
        if response.status_code == 200:
            # Look for local file content
            if "root:" in response.text or "/bin/" in response.text:
                return True, "Local file content detected in response (/etc/passwd)"

            # Check for AWS metadata
            if "ami-" in response.text or "instance-type" in response.text:
                return True, "AWS metadata detected in response"

            # Check for application error revealing internal address
            if "localhost" in response.text.lower() or "127.0.0.1" in response.text:
                return True, "Internal address referenced in response"

        # Check for different response than direct access
        if response.status_code < 400 and "<!DOCTYPE" in response.text:
            return True, "HTML content retrieved (possible internal page)"

        # Connection timeout on internal address could indicate port open
        if response.status_code == 504 or response.status_code == 500:
            return True, "Server error - may indicate internal service interaction"

        return False, "No SSRF indicators found"


class CSRFTester:
    """Main CSRF vulnerability tester"""

    def __init__(self, timeout: float = 10.0, verify_ssl: bool = True):
        self.timeout = timeout
        self.verify_ssl = verify_ssl

    def test_csrf_protection(self, url: str, cookies: Dict[str, str] = None,
                            headers: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Comprehensive CSRF protection analysis.
        
        Returns findings organized by protection mechanism
        """
        findings = {
            "state_changing_forms": [],
            "csrf_token_missing": [],
            "weak_token_protection": [],
            "origin_validation": [],
            "samesite_protection": [],
        }

        try:
            # Get page and extract forms
            resp = requests.get(url, cookies=cookies, headers=headers,
                              timeout=self.timeout, verify=self.verify_ssl)

            forms = CSRFAnalyzer.find_state_changing_forms(resp.text, url)

            for form in forms:
                findings["state_changing_forms"].append({
                    "method": form["method"],
                    "action": form["action"],
                    "fields": form["fields"],
                })

                # Check CSRF protection
                if not form["has_csrf_protection"]:
                    conf_score, conf_level = ConfidenceScorer.calculate_confidence(
                        "CSRF",
                        ["token_missing"],
                        {"token_missing": True},
                        {"response_status": "unexpected", "reproducible": True}
                    )
                    
                    finding = {
                        "type": "Missing CSRF Protection",
                        "severity": "High",
                        "url": form["action"],
                        "method": form["method"],
                        "evidence": "Form performs state change but has no CSRF token",
                        "confidence_score": conf_score,
                        "confidence_level": conf_level,
                        "detection_methods": ["token_missing"],
                        "verification_steps": ConfidenceScorer.get_verification_hints(
                            "CSRF", form["action"], "csrf_token", "token_missing"
                        ),
                        "false_positive_risk": ConfidenceScorer.get_false_positive_risk(
                            "CSRF", ["token_missing"], conf_score
                        ),
                    }
                    findings["csrf_token_missing"].append(finding)
                    logger.warning(f"CSRF protection missing on {form['action']}")

                else:
                    # Check token freshness
                    resp2 = requests.get(url, cookies=cookies, headers=headers,
                                       timeout=self.timeout, verify=self.verify_ssl)

                    tokens_differ, token_evidence = CSRFAnalyzer.check_csrf_token_freshness(resp, resp2)

                    if not tokens_differ:
                        conf_score, conf_level = ConfidenceScorer.calculate_confidence(
                            "CSRF",
                            ["token_static"],
                            {"token_static": True},
                            {"response_status": "unexpected", "reproducible": True}
                        )
                        
                        finding = {
                            "type": "Weak CSRF Token Protection",
                            "severity": "Medium",
                            "url": form["action"],
                            "method": form["method"],
                            "evidence": token_evidence,
                            "confidence_score": conf_score,
                            "confidence_level": conf_level,
                            "detection_methods": ["token_static"],
                            "verification_steps": ConfidenceScorer.get_verification_hints(
                                "CSRF", form["action"], "csrf_token", "token_static"
                            ),
                            "false_positive_risk": ConfidenceScorer.get_false_positive_risk(
                                "CSRF", ["token_static"], conf_score
                            ),
                        }
                        findings["weak_token_protection"].append(finding)

            # Check origin validation
            origin_validates, origin_evidence = CSRFAnalyzer.check_origin_validation(
                url, cookies, self.timeout, self.verify_ssl
            )
            
            if not origin_validates:
                conf_score, conf_level = ConfidenceScorer.calculate_confidence(
                    "CSRF",
                    ["state_change_success"],
                    {"state_change_success": True},
                    {"response_status": "unexpected", "reproducible": True}
                )
                
                origin_finding = {
                    "validates": origin_validates,
                    "evidence": origin_evidence,
                    "confidence_score": conf_score,
                    "confidence_level": conf_level,
                    "detection_methods": ["state_change_success"],
                    "verification_steps": ConfidenceScorer.get_verification_hints(
                        "CSRF", url, "Origin", "state_change_success"
                    ),
                    "false_positive_risk": ConfidenceScorer.get_false_positive_risk(
                        "CSRF", ["state_change_success"], conf_score
                    ),
                }
            else:
                origin_finding = {
                    "validates": origin_validates,
                    "evidence": origin_evidence,
                }
            
            findings["origin_validation"].append(origin_finding)

            # Check SameSite protection
            samesite_present, samesite_evidence = CSRFAnalyzer.check_samesite_cookie(
                cookies or {}, dict(resp.headers)
            )
            
            if not samesite_present:
                conf_score, conf_level = ConfidenceScorer.calculate_confidence(
                    "CSRF",
                    ["combined"],
                    {"samesite_missing": True},
                    {"response_status": "unexpected"}
                )
                
                samesite_finding = {
                    "present": samesite_present,
                    "evidence": samesite_evidence,
                    "confidence_score": conf_score,
                    "confidence_level": conf_level,
                    "detection_methods": ["combined"],
                    "verification_steps": ConfidenceScorer.get_verification_hints(
                        "CSRF", url, "Set-Cookie", "combined"
                    ),
                    "false_positive_risk": ConfidenceScorer.get_false_positive_risk(
                        "CSRF", ["combined"], conf_score
                    ),
                }
            else:
                samesite_finding = {
                    "present": samesite_present,
                    "evidence": samesite_evidence,
                }
            
            findings["samesite_protection"].append(samesite_finding)

        except requests.RequestException as e:
            logger.warning(f"CSRF test failed: {e}")

        return findings


class SSRFTester:
    """Main SSRF vulnerability tester"""

    def __init__(self, timeout: float = 5.0, verify_ssl: bool = True):
        self.timeout = timeout
        self.verify_ssl = verify_ssl

    def test_ssrf(self, url: str, parameter_name: str = "url",
                 cookies: Dict[str, str] = None,
                 headers: Dict[str, str] = None) -> List[Dict[str, Any]]:
        """
        Test endpoint for SSRF vulnerabilities by injecting internal URLs.
        
        Args:
            url: Target endpoint
            parameter_name: Parameter name that accepts URLs (default: "url")
            cookies: Session cookies
            headers: Custom headers
            
        Returns list of SSRF findings
        """
        findings = []

        payloads = SSRFDetector.generate_ssrf_payloads()

        for payload in payloads:
            test_params = {parameter_name: payload["url"]}

            try:
                response = requests.get(url, params=test_params, cookies=cookies,
                                      headers=headers, timeout=self.timeout,
                                      verify=self.verify_ssl)

                is_vulnerable, evidence = SSRFDetector.detect_ssrf_response(response, payload["url"])

                if is_vulnerable:
                    detection_method = "response_contains_internal"
                    
                    conf_score, conf_level = ConfidenceScorer.calculate_confidence(
                        "SSRF",
                        [detection_method],
                        {detection_method: True},
                        {"response_status": "unexpected", "reproducible": True}
                    )
                    
                    finding = {
                        "type": "Server-Side Request Forgery (SSRF)",
                        "severity": "Critical",
                        "url": url,
                        "parameter": parameter_name,
                        "payload": payload["url"],
                        "payload_type": payload["type"],
                        "evidence": evidence,
                        "status_code": response.status_code,
                        "confidence_score": conf_score,
                        "confidence_level": conf_level,
                        "detection_methods": [detection_method],
                        "verification_steps": ConfidenceScorer.get_verification_hints(
                            "SSRF", url, parameter_name, detection_method
                        ),
                        "false_positive_risk": ConfidenceScorer.get_false_positive_risk(
                            "SSRF", [detection_method], conf_score
                        ),
                    }
                    findings.append(finding)
                    logger.warning(f"SSRF vulnerability found: {parameter_name}")

            except requests.Timeout:
                # Timeout might indicate connection to internal service
                detection_method = "timing_detected"
                
                conf_score, conf_level = ConfidenceScorer.calculate_confidence(
                    "SSRF",
                    [detection_method],
                    {detection_method: True},
                    {"response_status": "timeout"}
                )
                
                finding = {
                    "type": "Server-Side Request Forgery (SSRF) - Potential",
                    "severity": "High",
                    "url": url,
                    "parameter": parameter_name,
                    "payload": payload["url"],
                    "payload_type": payload["type"],
                    "evidence": "Request timeout - may indicate SSRF to unreachable internal service",
                    "confidence_score": conf_score,
                    "confidence_level": conf_level,
                    "detection_methods": [detection_method],
                    "verification_steps": ConfidenceScorer.get_verification_hints(
                        "SSRF", url, parameter_name, detection_method
                    ),
                    "false_positive_risk": ConfidenceScorer.get_false_positive_risk(
                        "SSRF", [detection_method], conf_score
                    ),
                }
                findings.append(finding)

            except requests.RequestException as e:
                logger.debug(f"SSRF test failed: {e}")
                continue

        return findings
