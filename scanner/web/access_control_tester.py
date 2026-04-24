"""
Access Control Testing Module (IDOR & Privilege Escalation)

Tests for insecure direct object references (IDOR), horizontal privilege escalation,
and vertical privilege escalation vulnerabilities.
"""

import re
import time
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import requests
import logging
from urllib.parse import urlencode, parse_qs, urlparse, quote
import uuid
import difflib

logger = logging.getLogger(__name__)


class EscalationType(Enum):
    """Types of privilege escalation"""
    HORIZONTAL = "horizontal"  # Access other user's resources
    VERTICAL = "vertical"  # Access admin/higher-privilege resources
    IDOR = "idor"  # Direct object reference without authorization


@dataclass
class IDORPayload:
    """Represents an IDOR test payload"""
    original_id: str
    test_id: str
    id_type: str  # numeric, uuid, alphanumeric, hash
    endpoint: str
    method: str


class IDORDetector:
    """Detects identifiers and generates IDOR payloads"""

    # Patterns for common identifier names
    IDENTIFIER_PATTERNS = [
        r"(?:id|user_?id|post_?id|article_?id|order_?id|product_?id|report_?id|item_?id)=(\w+)",
        r"\/([0-9]+)(?:\/|$|\?)",  # Numeric in path: /api/users/123
        r"\/([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})",  # UUID
        r"\/([a-f0-9]{24})",  # MongoDB ObjectId
    ]

    @staticmethod
    def extract_identifiers(url: str, response_body: str = None) -> List[Dict[str, Any]]:
        """
        Extract identifiers from URL and response body.
        Returns list of {value, type, location, name}
        """
        identifiers = []
        found_ids = set()

        # Extract from URL
        parsed = urlparse(url)
        
        # Check query parameters
        params = parse_qs(parsed.query)
        for param_name, param_values in params.items():
            if any(x in param_name.lower() for x in ["id", "user", "account", "order", "product"]):
                for val in param_values:
                    if val not in found_ids:
                        id_type = IDORDetector.classify_identifier(val)
                        identifiers.append({
                            "value": val,
                            "type": id_type,
                            "location": "query_parameter",
                            "name": param_name,
                        })
                        found_ids.add(val)

        # Check path segments
        path_segments = parsed.path.split('/')
        for segment in path_segments:
            if segment and IDORDetector.is_likely_identifier(segment):
                if segment not in found_ids:
                    id_type = IDORDetector.classify_identifier(segment)
                    identifiers.append({
                        "value": segment,
                        "type": id_type,
                        "location": "path",
                        "name": "path_segment",
                    })
                    found_ids.add(segment)

        # Extract from response body (if provided)
        if response_body:
            for pattern in IDORDetector.IDENTIFIER_PATTERNS:
                for match in re.finditer(pattern, response_body):
                    val = match.group(1)
                    if val not in found_ids and len(val) >= 2:
                        id_type = IDORDetector.classify_identifier(val)
                        identifiers.append({
                            "value": val,
                            "type": id_type,
                            "location": "response_body",
                            "name": "extracted_id",
                        })
                        found_ids.add(val)

        return identifiers

    @staticmethod
    def is_likely_identifier(value: str) -> bool:
        """Check if value looks like an identifier"""
        # Numeric
        if re.match(r'^\d+$', value) and 2 <= len(value) <= 10:
            return True
        # UUID
        if re.match(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', value, re.IGNORECASE):
            return True
        # MongoDB ObjectId
        if re.match(r'^[a-f0-9]{24}$', value, re.IGNORECASE):
            return True
        # Hex string
        if re.match(r'^[a-f0-9]{32,}$', value, re.IGNORECASE) and len(value) >= 16:
            return True
        # Base64-ish (alphanumeric + _ - /)
        if re.match(r'^[a-zA-Z0-9_\-/]{8,}$', value) and not any(c.isspace() for c in value):
            return True

        return False

    @staticmethod
    def classify_identifier(value: str) -> str:
        """Classify the type of identifier"""
        if re.match(r'^\d+$', value):
            return "numeric"
        if re.match(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', value, re.IGNORECASE):
            return "uuid"
        if re.match(r'^[a-f0-9]{24}$', value, re.IGNORECASE):
            return "mongo_objectid"
        if re.match(r'^[a-f0-9]{32,}$', value, re.IGNORECASE):
            return "hex"
        return "alphanumeric"

    @staticmethod
    def generate_idor_payloads(identifier: Dict[str, Any], count: int = 5) -> List[str]:
        """
        Generate alternative identifier values to test IDOR.
        
        Args:
            identifier: Identifier dict with value and type
            count: Number of variants to generate
            
        Returns list of test values
        """
        payloads = []
        original = identifier["value"]
        id_type = identifier["type"]

        if id_type == "numeric":
            # Try adjacent numbers
            try:
                num = int(original)
                for offset in [1, 2, 3, -1, -2, 100, 999]:
                    payloads.append(str(num + offset))
                # Try common IDs
                payloads.extend(["1", "2", "10", "100", "admin", "0"])
            except ValueError:
                pass

        elif id_type == "uuid":
            # Generate random UUIDs (limited set to avoid noise)
            for _ in range(count):
                payloads.append(str(uuid.uuid4()))

        elif id_type == "mongo_objectid":
            # MongoDB ObjectIds are timestamp-based, generate nearby ones
            try:
                # Change last characters
                for i in range(count):
                    modified = original[:-8] + format(i, '08x')
                    payloads.append(modified)
            except:
                pass

        elif id_type == "hex":
            # Change bits in hex string
            try:
                for i in range(count):
                    modified = original
                    if i < len(original):
                        char = original[i]
                        # Flip bit
                        new_char = format(int(char, 16) ^ 1, 'x')
                        modified = original[:i] + new_char + original[i+1:]
                    payloads.append(modified)
            except:
                pass

        else:  # alphanumeric
            # Try simple increments or common values
            payloads.extend(["admin", "root", "test", "1", "2", "admin2", "user1", "user2"])

        return payloads[:count]


class ResponseAnalyzer:
    """Analyzes responses for IDOR vulnerabilities"""

    @staticmethod
    def calculate_similarity(response1_text: str, response2_text: str) -> float:
        """
        Calculate similarity between two responses (0.0 to 1.0).
        Uses sequence matching ratio.
        """
        matcher = difflib.SequenceMatcher(None, response1_text[:1000], response2_text[:1000])
        return matcher.ratio()

    @staticmethod
    def detect_access_change(baseline_response: requests.Response,
                            test_response: requests.Response,
                            min_similarity: float = 0.7) -> Tuple[bool, str]:
        """
        Detect if responses differ significantly (indicating potential IDOR).
        
        Returns (is_different, evidence)
        """
        baseline_text = baseline_response.text
        test_text = test_response.text

        # Check status codes
        if baseline_response.status_code != test_response.status_code:
            return True, f"Status code changed: {baseline_response.status_code} → {test_response.status_code}"

        # Check content length
        diff = abs(len(baseline_text) - len(test_text))
        if diff > 100:  # More than 100 bytes difference
            return True, f"Content length differs by {diff} bytes"

        # Calculate similarity
        similarity = ResponseAnalyzer.calculate_similarity(baseline_text, test_text)

        if similarity < min_similarity:
            return True, f"Response similarity only {similarity:.1%} (threshold: {min_similarity:.0%})"

        # Check for authorization errors in test response
        auth_errors = ["unauthorized", "forbidden", "permission denied", "not authorized", "access denied"]
        if any(error in test_text.lower() for error in auth_errors):
            return True, "Authorization error in test response"

        # Check for sensitive data differences
        if ResponseAnalyzer.contains_user_data(baseline_text) and ResponseAnalyzer.contains_user_data(test_text):
            if not ResponseAnalyzer.same_user_data(baseline_text, test_text):
                return True, "User data differs between responses"

        return False, "Responses are similar (no IDOR detected)"

    @staticmethod
    def contains_user_data(response_text: str) -> bool:
        """Check if response likely contains user data"""
        user_data_patterns = [
            r"email", r"user", r"name", r"profile", r"account",
            r"username", r"user_?name", r"first_?name", r"last_?name",
        ]
        return any(re.search(pattern, response_text, re.IGNORECASE) for pattern in user_data_patterns)

    @staticmethod
    def same_user_data(response1: str, response2: str) -> bool:
        """Check if both responses reference the same user"""
        emails1 = re.findall(r'[\w.-]+@[\w.-]+', response1)
        emails2 = re.findall(r'[\w.-]+@[\w.-]+', response2)
        return bool(set(emails1) & set(emails2))

    @staticmethod
    def extract_sensitive_fields(response_text: str) -> Dict[str, List[str]]:
        """
        Extract potentially sensitive fields from response.
        
        Returns dict of {field_type: [values]}
        """
        fields = {
            "emails": re.findall(r'[\w.-]+@[\w.-]+', response_text),
            "phone_numbers": re.findall(r'\+?[\d\s\-()]{10,}', response_text),
            "credit_cards": re.findall(r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b', response_text),
            "social_security": re.findall(r'\b\d{3}-\d{2}-\d{4}\b', response_text),
            "api_keys": re.findall(r'(api_?key|token|secret|password)[\s:="\']+([a-zA-Z0-9_-]{20,})', response_text),
        }
        return {k: v for k, v in fields.items() if v}


class IDORTester:
    """Main IDOR and privilege escalation tester"""

    def __init__(self, timeout: float = 10.0, verify_ssl: bool = True):
        self.timeout = timeout
        self.verify_ssl = verify_ssl

    def test_endpoint_idor(self, url: str, method: str = "GET",
                          cookies: Dict[str, str] = None,
                          headers: Dict[str, str] = None,
                          baseline_params: Dict[str, str] = None) -> List[Dict[str, Any]]:
        """
        Test endpoint for IDOR vulnerabilities.
        
        Args:
            url: Target endpoint URL
            method: HTTP method
            cookies: Session cookies
            headers: Custom headers
            baseline_params: Initial parameters for baseline request
            
        Returns list of IDOR findings
        """
        findings = []

        try:
            # Get baseline response
            baseline_resp = self._make_request(url, method, baseline_params, cookies, headers)
            if baseline_resp is None or baseline_resp.status_code >= 400:
                logger.debug(f"Baseline request failed: {baseline_resp.status_code if baseline_resp else 'None'}")
                return findings

            # Extract identifiers from URL and response
            identifiers = IDORDetector.extract_identifiers(url, baseline_resp.text)

            for identifier in identifiers:
                logger.debug(f"Testing IDOR for identifier: {identifier['value']} ({identifier['type']})")

                # Generate test payloads
                test_payloads = IDORDetector.generate_idor_payloads(identifier, count=5)

                for test_id in test_payloads:
                    # Create test request with modified identifier
                    test_params = self._modify_identifier_in_params(baseline_params or {}, identifier, test_id, url)
                    test_url = self._modify_identifier_in_url(url, identifier, test_id)

                    try:
                        test_resp = self._make_request(test_url, method, test_params, cookies, headers)

                        if test_resp is None:
                            continue

                        # Analyze response
                        is_vulnerable, evidence = ResponseAnalyzer.detect_access_change(baseline_resp, test_resp)

                        if is_vulnerable:
                            sensitive_fields = ResponseAnalyzer.extract_sensitive_fields(test_resp.text)

                            finding = {
                                "type": "Insecure Direct Object Reference (IDOR)",
                                "severity": "Critical" if sensitive_fields else "High",
                                "escalation_type": EscalationType.IDOR.value,
                                "url": test_url,
                                "method": method,
                                "original_id": identifier["value"],
                                "test_id": test_id,
                                "id_type": identifier["type"],
                                "evidence": evidence,
                                "sensitive_data": sensitive_fields,
                                "status_code": test_resp.status_code,
                            }
                            findings.append(finding)
                            logger.warning(f"IDOR vulnerability found: {identifier['value']} → {test_id}")
                            break  # Found vulnerability for this identifier, move to next

                    except requests.RequestException as e:
                        logger.debug(f"Test request failed: {e}")
                        continue

        except requests.RequestException as e:
            logger.warning(f"IDOR test failed: {e}")

        return findings

    def test_privilege_escalation(self, admin_url: str, user_url: str,
                                 user_cookies: Dict[str, str] = None,
                                 admin_cookies: Dict[str, str] = None,
                                 method: str = "GET") -> List[Dict[str, Any]]:
        """
        Test for vertical privilege escalation (user accessing admin endpoints).
        
        Args:
            admin_url: Admin endpoint URL
            user_url: User endpoint URL (for comparison)
            user_cookies: Regular user session cookies
            admin_cookies: Admin session cookies (for baseline)
            method: HTTP method
            
        Returns list of privilege escalation findings
        """
        findings = []

        try:
            # Get baseline (admin accessing admin endpoint)
            admin_resp = self._make_request(admin_url, method, None, admin_cookies)
            if admin_resp is None or admin_resp.status_code >= 400:
                logger.debug("Admin baseline access failed")
                return findings

            # Try user accessing admin endpoint
            user_accessing_admin = self._make_request(admin_url, method, None, user_cookies)
            if user_accessing_admin is None:
                return findings

            # Check if user got similar content as admin
            if user_accessing_admin.status_code == 200:
                similarity = ResponseAnalyzer.calculate_similarity(admin_resp.text, user_accessing_admin.text)

                if similarity > 0.7:  # More than 70% similar
                    finding = {
                        "type": "Vertical Privilege Escalation",
                        "severity": "Critical",
                        "escalation_type": EscalationType.VERTICAL.value,
                        "url": admin_url,
                        "method": method,
                        "evidence": f"User accessed admin endpoint with {similarity:.0%} similarity to admin response",
                        "status_code": user_accessing_admin.status_code,
                    }
                    findings.append(finding)
                    logger.warning("Vertical privilege escalation detected")

        except requests.RequestException as e:
            logger.debug(f"Privilege escalation test failed: {e}")

        return findings

    def _make_request(self, url: str, method: str = "GET",
                     params: Dict[str, str] = None,
                     cookies: Dict[str, str] = None,
                     headers: Dict[str, str] = None) -> Optional[requests.Response]:
        """Make HTTP request"""
        try:
            req_headers = {"User-Agent": "VAPT-Scanner/1.0"} | (headers or {})

            if method.upper() == "GET":
                response = requests.get(url, params=params, cookies=cookies,
                                      headers=req_headers, timeout=self.timeout,
                                      verify=self.verify_ssl, allow_redirects=True)
            else:
                response = requests.post(url, data=params, cookies=cookies,
                                       headers=req_headers, timeout=self.timeout,
                                       verify=self.verify_ssl, allow_redirects=True)

            return response

        except requests.RequestException as e:
            logger.debug(f"Request failed: {e}")
            return None

    @staticmethod
    def _modify_identifier_in_params(params: Dict[str, str], identifier: Dict[str, Any],
                                     test_id: str, url: str) -> Dict[str, str]:
        """Modify identifier in request parameters"""
        result = params.copy()

        if identifier["location"] == "query_parameter":
            result[identifier["name"]] = test_id

        return result

    @staticmethod
    def _modify_identifier_in_url(url: str, identifier: Dict[str, Any], test_id: str) -> str:
        """Modify identifier in URL path"""
        if identifier["location"] == "path":
            # Replace path segment
            return url.replace(f"/{identifier['value']}", f"/{test_id}", 1)

        return url
