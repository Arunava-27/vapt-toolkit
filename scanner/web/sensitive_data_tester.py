"""
Sensitive Data Exposure Module

Detects sensitive data leakage in HTTP responses including PII,
credentials, API keys, internal information, and more.
"""

import re
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import requests
import logging
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class DataType(Enum):
    """Types of sensitive data"""
    PII = "pii"  # Personally Identifiable Information
    CREDENTIALS = "credentials"  # Passwords, tokens, keys
    API_KEYS = "api_keys"  # API keys and secrets
    INTERNAL_INFO = "internal_info"  # IPs, paths, versions
    FINANCIAL = "financial"  # Credit cards, bank accounts
    HEALTH = "health"  # Health information
    GOVERNMENT = "government"  # SSN, passport, etc.


@dataclass
class SensitiveDataPattern:
    """Represents a sensitive data pattern"""
    name: str
    pattern: str
    data_type: DataType
    severity: str  # Critical, High, Medium, Low
    description: str
    regex_flags: int = re.IGNORECASE


class SensitiveDataDetector:
    """Detects sensitive data in responses"""

    # Comprehensive pattern library for sensitive data detection
    PATTERNS = [
        # PII - Email addresses
        SensitiveDataPattern(
            name="Email Address",
            pattern=r'[\w\.-]+@[\w\.-]+\.\w+',
            data_type=DataType.PII,
            severity="Medium",
            description="Email address exposed"
        ),
        # PII - Phone numbers (multiple formats)
        SensitiveDataPattern(
            name="Phone Number (US)",
            pattern=r'(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',
            data_type=DataType.PII,
            severity="Medium",
            description="US phone number exposed"
        ),
        # PII - Full name pattern
        SensitiveDataPattern(
            name="Full Name",
            pattern=r'(?:first_?name|last_?name|full_?name|name)\s*[\'"]?:?\s*[\'"]?([A-Z][a-z]+ [A-Z][a-z]+)',
            data_type=DataType.PII,
            severity="Low",
            description="Full name exposed in response"
        ),
        # GOVERNMENT - Social Security Number
        SensitiveDataPattern(
            name="US Social Security Number (SSN)",
            pattern=r'\b(?!000|666)[0-9]{3}-(?!00)[0-9]{2}-(?!0000)[0-9]{4}\b',
            data_type=DataType.GOVERNMENT,
            severity="Critical",
            description="US SSN exposed"
        ),
        # GOVERNMENT - Passport numbers
        SensitiveDataPattern(
            name="Passport Number",
            pattern=r'(?:passport|pasport|passport_?number)\s*[\'"]?:?\s*[\'"]?([A-Z0-9]{6,10})[\'"]?',
            data_type=DataType.GOVERNMENT,
            severity="Critical",
            description="Passport number exposed"
        ),
        # FINANCIAL - Credit card numbers
        SensitiveDataPattern(
            name="Credit Card Number (Visa/Mastercard/AmEx)",
            pattern=r'\b(?:\d{4}[\s\-]?){3}\d{4}\b',
            data_type=DataType.FINANCIAL,
            severity="Critical",
            description="Credit card number exposed"
        ),
        # FINANCIAL - Bank account numbers
        SensitiveDataPattern(
            name="Bank Account Number",
            pattern=r'(?:account|account_?number|account_?id)\s*[\'"]?:?\s*[\'"]?(\d{8,17})[\'"]?',
            data_type=DataType.FINANCIAL,
            severity="Critical",
            description="Bank account number exposed"
        ),
        # CREDENTIALS - API Keys (AWS)
        SensitiveDataPattern(
            name="AWS Access Key",
            pattern=r'AKIA[0-9A-Z]{16}',
            data_type=DataType.API_KEYS,
            severity="Critical",
            description="AWS access key exposed"
        ),
        # CREDENTIALS - API Keys (generic format)
        SensitiveDataPattern(
            name="API Key (Generic)",
            pattern=r'(?:api_?key|apikey|api_?secret|secret_?key)\s*[\'"]?:?\s*[\'"]?([a-zA-Z0-9_\-]{20,})[\'"]?',
            data_type=DataType.API_KEYS,
            severity="Critical",
            description="Generic API key exposed"
        ),
        # CREDENTIALS - GitHub Personal Access Tokens
        SensitiveDataPattern(
            name="GitHub Personal Access Token",
            pattern=r'ghp_[a-zA-Z0-9]{36}',
            data_type=DataType.API_KEYS,
            severity="Critical",
            description="GitHub PAT exposed"
        ),
        # CREDENTIALS - GitHub OAuth Tokens
        SensitiveDataPattern(
            name="GitHub OAuth Token",
            pattern=r'gho_[a-zA-Z0-9]{36}',
            data_type=DataType.API_KEYS,
            severity="Critical",
            description="GitHub OAuth token exposed"
        ),
        # CREDENTIALS - Stripe API Key
        SensitiveDataPattern(
            name="Stripe API Key",
            pattern=r'(?:sk_live|pk_live|sk_test|pk_test)_[a-zA-Z0-9]{24,}',
            data_type=DataType.API_KEYS,
            severity="Critical",
            description="Stripe API key exposed"
        ),
        # CREDENTIALS - Private SSH Key
        SensitiveDataPattern(
            name="Private SSH Key",
            pattern=r'-----BEGIN (?:RSA|DSA|EC|ED25519|OPENSSH) PRIVATE KEY',
            data_type=DataType.CREDENTIALS,
            severity="Critical",
            description="Private SSH key exposed"
        ),
        # CREDENTIALS - Password in URL
        SensitiveDataPattern(
            name="Password in URL",
            pattern=r'(?:password|passwd|pwd)=([^\s&\'\"]+)',
            data_type=DataType.CREDENTIALS,
            severity="High",
            description="Password parameter in URL"
        ),
        # CREDENTIALS - Database connection strings
        SensitiveDataPattern(
            name="Database Connection String",
            pattern=r'(?:mysql|mongodb|postgresql|oracle|mssql)://\w+:[\w\-]+@',
            data_type=DataType.CREDENTIALS,
            severity="Critical",
            description="Database connection string exposed"
        ),
        # INTERNAL_INFO - Internal IP addresses
        SensitiveDataPattern(
            name="Private IP Address",
            pattern=r'(?:(?:10|172\.(?:1[6-9]|2\d|3[01])|192\.168)\.\d{1,3}\.\d{1,3})',
            data_type=DataType.INTERNAL_INFO,
            severity="High",
            description="Private IP address exposed"
        ),
        # INTERNAL_INFO - AWS ARNs
        SensitiveDataPattern(
            name="AWS ARN",
            pattern=r'arn:aws:[a-z\-]+:[a-z\-]*:\d{12}:[a-z\-/]*',
            data_type=DataType.INTERNAL_INFO,
            severity="High",
            description="AWS ARN exposed"
        ),
        # INTERNAL_INFO - File paths
        SensitiveDataPattern(
            name="Server File Path",
            pattern=r'(?:/home/\w+/|/var/www/|/opt/|/usr/local/|C:\\Users\\)',
            data_type=DataType.INTERNAL_INFO,
            severity="Medium",
            description="Server file path exposed"
        ),
        # INTERNAL_INFO - Software versions
        SensitiveDataPattern(
            name="Software Version",
            pattern=r'(?:Apache|nginx|PHP|Python|Node|Java|IIS)\s*/?\s*(?:v)?(\d+\.\d+\.\d+)',
            data_type=DataType.INTERNAL_INFO,
            severity="Medium",
            description="Software version information exposed"
        ),
        # INTERNAL_INFO - Error stack traces
        SensitiveDataPattern(
            name="Stack Trace",
            pattern=r'(?:Error|Exception|Traceback|File).*?(?:line \d+|at \w+)',
            data_type=DataType.INTERNAL_INFO,
            severity="Medium",
            description="Stack trace or debug information exposed"
        ),
        # JWT Token
        SensitiveDataPattern(
            name="JWT Token",
            pattern=r'(?:eyJ[A-Za-z0-9_-]+){3}',
            data_type=DataType.CREDENTIALS,
            severity="High",
            description="JWT token exposed"
        ),
        # OAuth tokens
        SensitiveDataPattern(
            name="OAuth Bearer Token",
            pattern=r'Bearer\s+([a-zA-Z0-9\._\-]+)',
            data_type=DataType.CREDENTIALS,
            severity="High",
            description="OAuth bearer token exposed"
        ),
    ]

    @staticmethod
    def scan_response(response_text: str, response_url: str = None,
                      response_headers: Dict[str, str] = None) -> List[Dict[str, Any]]:
        """
        Scan response for sensitive data.
        
        Returns list of findings: {type, severity, data_type, value, location}
        """
        findings = []
        found_data: Set[Tuple[str, str]] = set()  # (pattern_name, matched_value)

        search_text = response_text

        for pattern in SensitiveDataDetector.PATTERNS:
            try:
                matches = re.finditer(pattern.pattern, search_text, pattern.regex_flags)

                for match in matches:
                    matched_value = match.group(0)

                    # Deduplicate same type of sensitive data
                    key = (pattern.name, matched_value)
                    if key in found_data:
                        continue
                    found_data.add(key)

                    # Extract context around match
                    start = max(0, match.start() - 50)
                    end = min(len(search_text), match.end() + 50)
                    context = search_text[start:end]

                    finding = {
                        "type": "Sensitive Data Exposure",
                        "severity": pattern.severity,
                        "data_type": pattern.data_type.value,
                        "pattern_name": pattern.name,
                        "description": pattern.description,
                        "matched_value": SensitiveDataDetector._mask_sensitive(matched_value),
                        "context": context[:100],
                        "url": response_url,
                    }
                    findings.append(finding)
                    logger.warning(f"Sensitive data found: {pattern.name}")

            except re.error as e:
                logger.debug(f"Regex error for pattern {pattern.name}: {e}")
                continue

        return findings

    @staticmethod
    def _mask_sensitive(value: str) -> str:
        """Mask sensitive value for logging"""
        if len(value) <= 4:
            return value

        # Show first 2 and last 2 characters
        return f"{value[:2]}{'*' * (len(value) - 4)}{value[-2:]}"

    @staticmethod
    def detect_excessive_data(response_text: str) -> Dict[str, Any]:
        """
        Detect if response contains excessive data that shouldn't be there.
        
        Returns analysis of data types found
        """
        analysis = {
            "total_size": len(response_text),
            "has_debug_info": False,
            "has_source_code": False,
            "has_comments": False,
            "has_error_details": False,
            "has_internal_paths": False,
        }

        # Debug info indicators
        debug_patterns = [
            r'__FILE__', r'__LINE__', r'debug\s*=\s*true',
            r'console\.log', r'print_r\(', r'var_dump\(',
        ]
        analysis["has_debug_info"] = any(re.search(p, response_text, re.IGNORECASE) for p in debug_patterns)

        # Source code indicators
        code_patterns = [
            r'<script>.*?function\s+\w+', r'function\s+\w+\s*\{',
            r'var\s+\w+\s*=', r'const\s+\w+\s*=',
        ]
        analysis["has_source_code"] = any(re.search(p, response_text) for p in code_patterns)

        # Comments
        comment_patterns = [
            r'<!--.*?-->', r'//\s+TODO', r'//\s+HACK', r'#\s+TODO',
        ]
        analysis["has_comments"] = any(re.search(p, response_text) for p in comment_patterns)

        # Error details
        error_patterns = [
            r'Exception', r'Traceback', r'Stack trace', r'Error:',
        ]
        analysis["has_error_details"] = any(re.search(p, response_text, re.IGNORECASE) for p in error_patterns)

        # Internal paths
        path_patterns = [
            r'/home/\w+', r'/var/www', r'/opt/', r'C:\\Users\\',
        ]
        analysis["has_internal_paths"] = any(re.search(p, response_text) for p in path_patterns)

        return analysis


class CookieAnalyzer:
    """Analyzes cookies for sensitive data exposure"""

    @staticmethod
    def analyze_cookies(response: requests.Response) -> List[Dict[str, Any]]:
        """
        Analyze cookies for security issues.
        
        Returns findings for overly sensitive cookies
        """
        findings = []

        for cookie_name, cookie_value in response.cookies.items():
            # Check if cookie value contains sensitive patterns
            sensitive_patterns = [
                (r'[a-f0-9]{32,}', "High-entropy value (possible secret)"),
                (r'admin|root|privilege', "Privilege indicator in cookie"),
                (r'user_?id|account_?id', "User ID in cookie (IDOR risk)"),
            ]

            for pattern, description in sensitive_patterns:
                if re.search(pattern, cookie_value, re.IGNORECASE):
                    finding = {
                        "type": "Sensitive Cookie",
                        "severity": "Medium",
                        "cookie_name": cookie_name,
                        "issue": description,
                        "evidence": f"Cookie '{cookie_name}' may contain sensitive data",
                    }
                    findings.append(finding)
                    break

        return findings

    @staticmethod
    def check_cookie_flags(response_headers: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Check Set-Cookie headers for security flags.
        
        Returns findings for missing security flags
        """
        findings = []
        set_cookie = response_headers.get("Set-Cookie", "")

        if not set_cookie:
            return findings

        # Check for security flags
        if "Secure" not in set_cookie:
            findings.append({
                "type": "Insecure Cookie Flag",
                "severity": "High",
                "issue": "Secure flag missing",
                "evidence": "Cookie can be transmitted over HTTP",
            })

        if "HttpOnly" not in set_cookie:
            findings.append({
                "type": "HttpOnly Cookie Flag Missing",
                "severity": "High",
                "issue": "HttpOnly flag missing",
                "evidence": "Cookie accessible via JavaScript (XSS risk)",
            })

        return findings


class HeaderAnalyzer:
    """Analyzes response headers for information leakage"""

    @staticmethod
    def analyze_headers(response_headers: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Analyze response headers for information leakage.
        
        Returns findings for headers revealing sensitive info
        """
        findings = []

        # Headers that may reveal sensitive information
        sensitive_headers = {
            "Server": "Software and version information",
            "X-AspNet-Version": "ASP.NET version exposed",
            "X-Powered-By": "Framework/language information",
            "X-Debug": "Debug mode enabled",
            "X-Original-URL": "Original URL exposure",
            "X-Rewrite-URL": "Rewrite URL exposure",
        }

        for header_name, description in sensitive_headers.items():
            if header_name in response_headers:
                value = response_headers[header_name]
                finding = {
                    "type": "Header Information Leakage",
                    "severity": "Low",
                    "header": header_name,
                    "value": value,
                    "issue": description,
                }
                findings.append(finding)

        return findings


class SensitiveDataTester:
    """Main orchestrator for sensitive data exposure testing"""

    def __init__(self, timeout: float = 10.0, verify_ssl: bool = True):
        self.timeout = timeout
        self.verify_ssl = verify_ssl

    def test_sensitive_exposure(self, url: str, cookies: Dict[str, str] = None,
                               headers: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Comprehensive sensitive data exposure test.
        
        Tests:
        - Response body for PII, credentials, API keys, internal info
        - Cookies for sensitive values
        - Headers for information leakage
        - Excessive data in responses
        """
        findings = {
            "response_data": [],
            "cookie_issues": [],
            "header_leakage": [],
            "excessive_data": [],
        }

        try:
            response = requests.get(
                url,
                cookies=cookies,
                headers=headers,
                timeout=self.timeout,
                verify=self.verify_ssl
            )

            # Scan response body
            body_findings = SensitiveDataDetector.scan_response(response.text, url)
            findings["response_data"].extend(body_findings)

            # Analyze cookies
            cookie_findings = CookieAnalyzer.analyze_cookies(response)
            findings["cookie_issues"].extend(cookie_findings)

            # Check cookie flags
            flag_findings = CookieAnalyzer.check_cookie_flags(dict(response.headers))
            findings["cookie_issues"].extend(flag_findings)

            # Analyze headers
            header_findings = HeaderAnalyzer.analyze_headers(dict(response.headers))
            findings["header_leakage"].extend(header_findings)

            # Detect excessive data
            data_analysis = SensitiveDataDetector.detect_excessive_data(response.text)
            if any(data_analysis.values()):
                findings["excessive_data"].append({
                    "type": "Excessive Data Exposure",
                    "severity": "Medium",
                    "analysis": data_analysis,
                })

        except requests.RequestException as e:
            logger.warning(f"Sensitive data test failed: {e}")

        return findings

    def test_multiple_endpoints(self, base_url: str, endpoints: List[str] = None,
                               cookies: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Test multiple endpoints for sensitive data exposure.
        
        Returns aggregated findings organized by endpoint
        """
        aggregated_findings = {}

        test_endpoints = endpoints or [base_url]

        for endpoint in test_endpoints:
            findings = self.test_sensitive_exposure(endpoint, cookies)
            if any(findings.values()):
                aggregated_findings[endpoint] = findings

        return aggregated_findings
