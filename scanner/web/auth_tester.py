"""
Authentication & Session Analysis Module

Tests for weak authentication, session management vulnerabilities,
and credential handling issues. Includes rate-limited credential testing.
"""

import re
import json
import time
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import requests
import logging
from urllib.parse import urljoin, urlparse
import hashlib
import base64

logger = logging.getLogger(__name__)


class TokenType(Enum):
    """Types of session tokens"""
    COOKIE = "cookie"
    JWT = "jwt"
    CUSTOM_HEADER = "custom_header"
    BEARER_TOKEN = "bearer_token"
    OAUTH = "oauth"


@dataclass
class SessionToken:
    """Represents a session token"""
    token_type: TokenType
    name: str
    value: str
    domain: str = ""
    path: str = ""
    secure: bool = False
    httponly: bool = False
    samesite: str = ""
    expires: str = ""


class LoginEndpointDetector:
    """Detects and maps login/authentication endpoints"""

    # Common login endpoint patterns
    LOGIN_PATHS = [
        "/login", "/signin", "/auth/login", "/authenticate", "/auth",
        "/user/login", "/account/login", "/admin/login", "/api/login",
        "/api/auth/login", "/users/login", "/authentication",
        "/user/authenticate", "/login.php", "/login.html",
    ]

    LOGIN_KEYWORDS = ["login", "signin", "auth", "authenticate", "credential", "password"]

    @staticmethod
    def find_login_endpoints(base_url: str, html_content: str = None,
                            timeout: float = 10.0, verify_ssl: bool = True) -> List[str]:
        """
        Find login endpoints by:
        1. Common path patterns
        2. Form detection (looking for password fields)
        3. Crawling links
        
        Returns list of likely login URLs
        """
        endpoints = []
        tested_urls = set()

        # Strategy 1: Test common paths
        base_domain = urlparse(base_url).netloc
        for path in LoginEndpointDetector.LOGIN_PATHS:
            test_url = urljoin(base_url, path)
            if test_url in tested_urls:
                continue
            tested_urls.add(test_url)

            try:
                resp = requests.head(test_url, timeout=timeout, verify=verify_ssl, allow_redirects=True)
                if resp.status_code < 400:
                    endpoints.append(test_url)
            except requests.RequestException:
                pass

        # Strategy 2: Parse HTML for forms with password fields
        if html_content:
            # Find all forms with password fields
            password_form_pattern = r'<form[^>]*action=["\']?([^"\'\s>]+)["\']?[^>]*>(.*?)</form>'
            for match in re.finditer(password_form_pattern, html_content, re.IGNORECASE | re.DOTALL):
                action = match.group(1)
                form_content = match.group(2)

                if any(kw in form_content.lower() for kw in ["password", "passwd", "pwd"]):
                    form_url = urljoin(base_url, action)
                    if form_url not in endpoints and form_url not in tested_urls:
                        endpoints.append(form_url)

        return list(set(endpoints))

    @staticmethod
    def extract_login_form(url: str, timeout: float = 10.0, 
                          verify_ssl: bool = True) -> Optional[Dict[str, Any]]:
        """
        Extract login form details from URL.
        Returns form metadata: method, fields, action, etc.
        """
        try:
            resp = requests.get(url, timeout=timeout, verify=verify_ssl)
            if resp.status_code >= 400:
                return None

            # Find first form with password field
            form_pattern = r'<form[^>]*>(.*?)</form>'
            for match in re.finditer(form_pattern, resp.text, re.IGNORECASE | re.DOTALL):
                form_html = match.group(0)
                form_content = match.group(1)

                if any(kw in form_html.lower() for kw in ["password", "passwd", "pwd"]):
                    # Extract form action and method
                    action_match = re.search(r'action=["\']?([^"\'\s>]+)', form_html, re.IGNORECASE)
                    method_match = re.search(r'method=["\']?(\w+)["\']?', form_html, re.IGNORECASE)

                    action = action_match.group(1) if action_match else ""
                    method = method_match.group(1).upper() if method_match else "POST"

                    # Extract input fields
                    fields = {}
                    input_pattern = r'<input[^>]*(?:name|id)=["\']?([^"\'\s>]+)["\']?[^>]*(?:type=["\']?(\w+)["\']?)?'
                    for inp_match in re.finditer(input_pattern, form_content, re.IGNORECASE):
                        field_name = inp_match.group(1)
                        field_type = inp_match.group(2) or "text"
                        fields[field_name] = field_type

                    return {
                        "url": urljoin(url, action) if action else url,
                        "method": method,
                        "fields": fields,
                        "raw_html": form_html
                    }

            return None

        except requests.RequestException as e:
            logger.debug(f"Failed to extract login form: {e}")
            return None


class CredentialTester:
    """Rate-limited credential testing for weak password detection"""

    # Common weak credentials (intentionally limited to avoid too many tests)
    WEAK_CREDENTIALS = [
        ("admin", "admin"),
        ("admin", "password"),
        ("admin", "123456"),
        ("admin", "12345678"),
        ("root", "root"),
        ("root", "password"),
        ("user", "user"),
        ("user", "password"),
        ("test", "test"),
        ("guest", "guest"),
    ]

    def __init__(self, max_attempts_per_endpoint: int = 3, 
                 rate_limit_delay: float = 2.0):
        """
        Initialize credential tester with rate limiting.
        
        Args:
            max_attempts_per_endpoint: Max login attempts per endpoint (safety)
            rate_limit_delay: Delay between attempts in seconds
        """
        self.max_attempts = max_attempts_per_endpoint
        self.rate_limit_delay = rate_limit_delay
        self.attempts_made = 0

    def test_weak_credentials(self, login_url: str, form_metadata: Dict[str, Any],
                             timeout: float = 10.0,
                             verify_ssl: bool = True) -> List[Dict[str, Any]]:
        """
        Test weak credentials against login endpoint.
        Rate-limited to max_attempts_per_endpoint.
        
        Returns findings for successful login attempts
        """
        findings = []

        if not form_metadata:
            return findings

        fields = form_metadata.get("fields", {})
        method = form_metadata.get("method", "POST")
        url = form_metadata.get("url", login_url)

        # Identify username and password fields
        username_field = None
        password_field = None

        for field_name, field_type in fields.items():
            if any(x in field_name.lower() for x in ["user", "email", "login", "username"]):
                username_field = field_name
            if any(x in field_name.lower() for x in ["pass", "password", "pwd"]):
                password_field = field_name

        if not username_field or not password_field:
            return findings

        # Test credentials with rate limiting
        for username, password in self.WEAK_CREDENTIALS[:self.max_attempts]:
            if self.attempts_made >= self.max_attempts:
                break

            time.sleep(self.rate_limit_delay)  # Rate limit

            test_data = {
                username_field: username,
                password_field: password,
            }

            # Add other fields with placeholder values
            for field_name in fields:
                if field_name not in [username_field, password_field]:
                    test_data[field_name] = "test"

            try:
                if method.upper() == "POST":
                    response = requests.post(url, data=test_data, timeout=timeout, verify=verify_ssl)
                else:
                    response = requests.get(url, params=test_data, timeout=timeout, verify=verify_ssl)

                self.attempts_made += 1

                # Check for successful login indicators
                is_success = self._check_login_success(response, username)

                if is_success:
                    finding = {
                        "type": "Weak Credentials",
                        "severity": "Critical",
                        "url": login_url,
                        "username": username,
                        "password": password,
                        "evidence": f"Login succeeded with {username}:{password}",
                        "status_code": response.status_code,
                    }
                    findings.append(finding)
                    logger.warning(f"Weak credentials found: {username}:{password}")

            except requests.RequestException as e:
                logger.debug(f"Credential test failed: {e}")
                continue

        return findings

    @staticmethod
    def _check_login_success(response: requests.Response, username: str) -> bool:
        """
        Detect if login was successful.
        Looks for common success indicators.
        """
        text_lower = response.text.lower()

        # Success indicators
        success_patterns = [
            r"dashboard", r"welcome", r"logout", r"profile",
            r"successfully\s+logged", r"authentication\s+successful",
            r"welcome\s+" + username,
        ]

        for pattern in success_patterns:
            if re.search(pattern, text_lower):
                return True

        # Failure indicators (if present, likely not successful)
        failure_patterns = [r"invalid", r"failed", r"incorrect", r"unauthorized", r"forbidden"]
        has_failure = any(re.search(pattern, text_lower) for pattern in failure_patterns)

        if has_failure:
            return False

        # Check for redirects (common success indicator)
        if response.status_code in [301, 302, 303, 307, 308]:
            return True

        return False


class SessionAnalyzer:
    """Analyzes session tokens and cookie security"""

    @staticmethod
    def extract_tokens(response: requests.Response, 
                      response_headers: Dict[str, str] = None) -> List[SessionToken]:
        """
        Extract session tokens from response headers and cookies.
        
        Returns list of SessionToken objects
        """
        tokens = []

        if response_headers is None:
            response_headers = dict(response.headers)

        # Extract from Set-Cookie headers
        cookies = response.cookies
        for cookie_name, cookie_value in cookies.items():
            token = SessionToken(
                token_type=TokenType.COOKIE,
                name=cookie_name,
                value=cookie_value,
                secure=response_headers.get("Secure", "").lower() == "true",
                httponly=response_headers.get("HttpOnly", "").lower() == "true",
                samesite=response_headers.get("SameSite", ""),
                domain=cookies.get(cookie_name, {}).get("domain", ""),
                path=cookies.get(cookie_name, {}).get("path", "/"),
            )
            tokens.append(token)

        # Extract from Authorization headers
        auth_header = response_headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token_value = auth_header.replace("Bearer ", "")
            token = SessionToken(
                token_type=TokenType.BEARER_TOKEN,
                name="Authorization",
                value=token_value,
            )
            tokens.append(token)

        # Extract JWT if present
        for token in tokens:
            if SessionAnalyzer.is_jwt(token.value):
                token.token_type = TokenType.JWT

        return tokens

    @staticmethod
    def is_jwt(token_value: str) -> bool:
        """Check if token looks like a JWT"""
        if not isinstance(token_value, str):
            return False
        parts = token_value.split('.')
        return len(parts) == 3  # JWT has 3 parts: header.payload.signature

    @staticmethod
    def analyze_jwt(jwt_token: str) -> Optional[Dict[str, Any]]:
        """
        Decode and analyze JWT token (without signature verification).
        
        Returns decoded JWT payload
        """
        try:
            parts = jwt_token.split('.')
            if len(parts) != 3:
                return None

            # Decode payload (second part)
            payload_b64 = parts[1]
            # Add padding if needed
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += '=' * padding

            payload_json = base64.urlsafe_b64decode(payload_b64)
            return json.loads(payload_json)

        except Exception as e:
            logger.debug(f"Failed to decode JWT: {e}")
            return None

    @staticmethod
    def check_jwt_expiry(jwt_token: str) -> Tuple[bool, str]:
        """
        Check if JWT is expired.
        Returns (is_expired, message)
        """
        payload = SessionAnalyzer.analyze_jwt(jwt_token)
        if not payload:
            return False, "Could not decode JWT"

        if "exp" not in payload:
            return False, "No expiry time in JWT"

        exp_time = payload["exp"]
        current_time = time.time()

        if current_time > exp_time:
            return True, f"JWT expired at {time.ctime(exp_time)}"
        else:
            expires_in = exp_time - current_time
            return False, f"JWT expires in {expires_in:.0f} seconds"

    @staticmethod
    def check_session_security(token: SessionToken) -> List[str]:
        """
        Check session token for security issues.
        Returns list of findings/recommendations
        """
        findings = []

        if token.token_type == TokenType.COOKIE:
            if not token.secure:
                findings.append("Cookie missing 'Secure' flag - can be transmitted over HTTP")
            if not token.httponly:
                findings.append("Cookie missing 'HttpOnly' flag - vulnerable to XSS theft")
            if not token.samesite:
                findings.append("Cookie missing 'SameSite' attribute - vulnerable to CSRF")
            elif token.samesite.lower() == "none":
                findings.append("Cookie has SameSite=None - may allow cross-site requests")

        elif token.token_type == TokenType.JWT:
            # Check JWT for common issues
            payload = SessionAnalyzer.analyze_jwt(token.value)
            if payload:
                if "aud" not in payload:
                    findings.append("JWT missing 'aud' (audience) claim")
                if "iss" not in payload:
                    findings.append("JWT missing 'iss' (issuer) claim")

        return findings

    @staticmethod
    def test_token_tampering(token_value: str, endpoint_url: str,
                            cookies: Dict[str, str] = None,
                            timeout: float = 10.0,
                            verify_ssl: bool = True) -> Tuple[bool, str]:
        """
        Test if token value can be modified and still be accepted.
        
        Returns (is_vulnerable, evidence)
        """
        try:
            # Try flipping bits in token
            tampered_token = ""
            if len(token_value) > 10:
                # Flip first character's bit
                first_char = token_value[0]
                tampered_char = chr(ord(first_char) ^ 1)
                tampered_token = tampered_char + token_value[1:]

            if tampered_token:
                test_cookies = (cookies or {}).copy()
                if "session" in test_cookies:
                    test_cookies["session"] = tampered_token

                resp = requests.get(endpoint_url, cookies=test_cookies, 
                                   timeout=timeout, verify=verify_ssl)

                # If 200 OK with tampered token, it's not validated
                if resp.status_code == 200:
                    return True, "Tampered token accepted with status 200"

                # If not 401/403, token validation might be weak
                if resp.status_code not in [401, 403]:
                    return True, f"Unexpected response {resp.status_code} to tampered token"

        except requests.RequestException:
            pass

        return False, "Token validation appears to be working"


class AuthenticationTester:
    """Main orchestrator for authentication testing"""

    def __init__(self, timeout: float = 10.0, verify_ssl: bool = True):
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.credential_tester = CredentialTester()

    def test_target_authentication(self, base_url: str) -> Dict[str, Any]:
        """
        Comprehensive authentication security test.
        
        Returns findings organized by vulnerability type
        """
        findings = {
            "login_endpoints": [],
            "weak_credentials": [],
            "session_issues": [],
            "jwt_issues": [],
        }

        try:
            # Get base page
            resp = requests.get(base_url, timeout=self.timeout, verify=self.verify_ssl)

            # Find login endpoints
            login_endpoints = LoginEndpointDetector.find_login_endpoints(base_url, resp.text, self.timeout, self.verify_ssl)
            findings["login_endpoints"] = login_endpoints

            # Test each login endpoint
            for login_url in login_endpoints[:3]:  # Limit to first 3
                logger.info(f"Testing authentication at {login_url}")

                # Extract form
                form_meta = LoginEndpointDetector.extract_login_form(login_url, self.timeout, self.verify_ssl)

                if form_meta:
                    # Test weak credentials
                    weak_cred_findings = self.credential_tester.test_weak_credentials(
                        login_url, form_meta, self.timeout, self.verify_ssl
                    )
                    findings["weak_credentials"].extend(weak_cred_findings)

                    # Analyze session after login attempt
                    try:
                        login_resp = requests.post(form_meta["url"], data={}, 
                                                  timeout=self.timeout, verify=self.verify_ssl)
                        tokens = SessionAnalyzer.extract_tokens(login_resp)

                        for token in tokens:
                            security_issues = SessionAnalyzer.check_session_security(token)
                            if security_issues:
                                for issue in security_issues:
                                    findings["session_issues"].append({
                                        "type": "Session Security",
                                        "severity": "High",
                                        "token_name": token.name,
                                        "issue": issue,
                                    })

                            if token.token_type == TokenType.JWT:
                                is_expired, exp_msg = SessionAnalyzer.check_jwt_expiry(token.value)
                                findings["jwt_issues"].append({
                                    "type": "JWT Analysis",
                                    "token": token.name,
                                    "expired": is_expired,
                                    "expiry_info": exp_msg,
                                })

                    except requests.RequestException:
                        pass

        except requests.RequestException as e:
            logger.warning(f"Authentication test failed: {e}")

        return findings
