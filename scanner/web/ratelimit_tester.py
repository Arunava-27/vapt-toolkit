"""
Rate Limiting & Abuse Testing Module

Tests for rate limiting and abuse resilience including brute force resistance,
API rate limiting, OTP/token throttling, and bypass techniques.
"""

import re
import time
import threading
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import requests
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class RateLimitingVulnerability(Enum):
    """Types of rate limiting vulnerabilities"""
    NO_RATE_LIMIT = "no_rate_limit"
    WEAK_RATE_LIMIT = "weak_rate_limit"
    BYPASSABLE_RATE_LIMIT = "bypassable_rate_limit"
    INSUFFICIENT_THROTTLING = "insufficient_throttling"


@dataclass
class RateLimitResponse:
    """Represents a rate limiting response"""
    status_code: int
    headers: Dict[str, str]
    remaining: Optional[int] = None  # Requests remaining
    reset_time: Optional[int] = None  # Seconds until reset
    is_rate_limited: bool = False


class RateLimitDetector:
    """Detects rate limiting mechanisms"""

    # Common rate limit header patterns
    RATE_LIMIT_HEADERS = [
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
        "X-Rate-Limit-Limit",
        "X-Rate-Limit-Remaining",
        "X-Rate-Limit-Reset",
        "RateLimit-Limit",
        "RateLimit-Remaining",
        "RateLimit-Reset",
        "Retry-After",
    ]

    # Rate limit status codes
    RATE_LIMIT_CODES = [429, 403, 503]

    @staticmethod
    def detect_rate_limit_headers(response_headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Detect rate limiting headers in response.
        
        Returns info about rate limiting: {is_present, headers_found, details}
        """
        found_headers = {}

        for header_name in RateLimitDetector.RATE_LIMIT_HEADERS:
            # Case-insensitive search
            for actual_header, value in response_headers.items():
                if actual_header.lower() == header_name.lower():
                    found_headers[header_name] = value

        analysis = {
            "is_present": len(found_headers) > 0,
            "headers_found": found_headers,
        }

        # Parse rate limit info
        if "X-RateLimit-Remaining" in found_headers:
            try:
                analysis["remaining"] = int(found_headers["X-RateLimit-Remaining"])
            except ValueError:
                pass

        if "X-RateLimit-Reset" in found_headers:
            try:
                analysis["reset_time"] = int(found_headers["X-RateLimit-Reset"])
            except ValueError:
                pass

        return analysis

    @staticmethod
    def detect_rate_limiting_behavior(response: requests.Response) -> Tuple[bool, str]:
        """
        Detect if response indicates rate limiting.
        
        Returns (is_rate_limited, evidence)
        """
        # Check status code
        if response.status_code == 429:
            return True, "HTTP 429 Too Many Requests"

        if response.status_code in [403, 503]:
            # Check for rate limit indicators in body
            if any(x in response.text.lower() for x in ["rate", "limit", "quota", "throttle"]):
                return True, f"HTTP {response.status_code} with rate limit indicators in body"

        # Check for Retry-After header
        if "Retry-After" in response.headers:
            return True, f"Retry-After header present: {response.headers['Retry-After']}"

        return False, "No rate limiting indicators"


class BruteForceTester:
    """Tests resistance to brute force attacks"""

    @staticmethod
    def test_login_brute_force(endpoint_url: str, username: str,
                              timeout: float = 10.0, verify_ssl: bool = True,
                              max_attempts: int = 20) -> List[Dict[str, Any]]:
        """
        Test if login endpoint is protected against brute force.
        
        Args:
            endpoint_url: Login endpoint
            username: Username to attack
            max_attempts: Number of login attempts
            
        Returns findings for brute force vulnerabilities
        """
        findings = []
        successful_attempts = 0
        rate_limited = False

        passwords = [
            "password", "123456", "admin", "letmein", "welcome",
            "pass123", "qwerty", "12345", "password123", "111111",
            "1234567890", "abc123", "password1", "admin123", "root",
        ]

        start_time = time.time()
        response_times = []

        for attempt, password in enumerate(passwords[:max_attempts]):
            try:
                request_start = time.time()

                response = requests.post(
                    endpoint_url,
                    data={"username": username, "password": password},
                    timeout=timeout,
                    verify=verify_ssl
                )

                request_time = time.time() - request_start
                response_times.append(request_time)

                # Check for rate limiting
                is_rate_limited, _ = RateLimitDetector.detect_rate_limiting_behavior(response)
                if is_rate_limited:
                    rate_limited = True
                    break

                if response.status_code == 200 or "success" in response.text.lower():
                    successful_attempts += 1

            except requests.RequestException as e:
                logger.debug(f"Brute force attempt failed: {e}")
                continue

        # Analysis
        if not rate_limited and attempt >= 5:
            finding = {
                "type": "Brute Force - No Rate Limiting",
                "severity": "High",
                "vulnerability": RateLimitingVulnerability.NO_RATE_LIMIT.value,
                "endpoint": endpoint_url,
                "attempts_made": attempt + 1,
                "evidence": f"Sent {attempt + 1} login attempts without rate limiting",
            }
            findings.append(finding)

        if successful_attempts > 0:
            finding = {
                "type": "Brute Force - Credentials Found",
                "severity": "Critical",
                "vulnerable": True,
                "successful_attempts": successful_attempts,
                "evidence": f"Found {successful_attempts} working password(s) in brute force",
            }
            findings.append(finding)

        return findings

    @staticmethod
    def test_otp_brute_force(endpoint_url: str, otp_param: str = "otp",
                            timeout: float = 10.0, verify_ssl: bool = True,
                            max_attempts: int = 100) -> List[Dict[str, Any]]:
        """
        Test if OTP endpoint is protected against brute force.
        
        Attempts common OTP values: 000000, 111111, etc.
        """
        findings = []

        otp_values = [
            "000000", "111111", "123456", "999999",
            "1234", "0000", "1111",  # 4-digit OTPs
        ]

        attempts_before_limit = 0

        for otp in otp_values:
            try:
                params = {otp_param: otp}
                response = requests.post(
                    endpoint_url,
                    data=params,
                    timeout=timeout,
                    verify=verify_ssl
                )

                # Check for rate limiting
                is_rate_limited, evidence = RateLimitDetector.detect_rate_limiting_behavior(response)

                if is_rate_limited:
                    break

                attempts_before_limit += 1

                if response.status_code == 200 or "success" in response.text.lower():
                    finding = {
                        "type": "OTP Brute Force - Valid OTP Found",
                        "severity": "Critical",
                        "otp": otp,
                        "evidence": f"OTP {otp} was accepted",
                    }
                    findings.append(finding)
                    break

            except requests.RequestException:
                continue

        if attempts_before_limit >= 10:
            finding = {
                "type": "OTP Brute Force - No Rate Limiting",
                "severity": "High",
                "vulnerability": RateLimitingVulnerability.NO_RATE_LIMIT.value,
                "endpoint": endpoint_url,
                "attempts_before_limit": attempts_before_limit,
                "evidence": f"Attempted {attempts_before_limit} OTPs without rate limiting",
            }
            findings.append(finding)

        return findings


class APIRateLimitTester:
    """Tests API rate limiting"""

    @staticmethod
    def measure_rate_limit_threshold(endpoint_url: str,
                                     timeout: float = 10.0,
                                     verify_ssl: bool = True,
                                     max_requests: int = 100) -> Dict[str, Any]:
        """
        Measure rate limit threshold by sending requests until limit is hit.
        
        Returns: {threshold, rate_limit_per_second, reset_time, headers}
        """
        results = {
            "requests_before_limit": 0,
            "rate_limit_detected": False,
            "rate_limit_headers": {},
            "reset_time": None,
        }

        for attempt in range(max_requests):
            try:
                response = requests.get(endpoint_url, timeout=timeout, verify=verify_ssl)

                # Check for rate limiting
                is_limited, _ = RateLimitDetector.detect_rate_limiting_behavior(response)

                # Extract rate limit headers
                header_info = RateLimitDetector.detect_rate_limit_headers(dict(response.headers))
                if header_info["is_present"]:
                    results["rate_limit_headers"] = header_info

                if is_limited:
                    results["rate_limit_detected"] = True
                    results["requests_before_limit"] = attempt
                    break

                results["requests_before_limit"] = attempt + 1

            except requests.RequestException:
                break

        return results

    @staticmethod
    def test_rate_limit_bypass_techniques(endpoint_url: str,
                                         timeout: float = 10.0,
                                         verify_ssl: bool = True) -> List[Dict[str, Any]]:
        """
        Test common rate limit bypass techniques.
        
        Techniques tested:
        - X-Forwarded-For header spoofing
        - User-Agent rotation
        - Parameter manipulation
        - Double-encoded requests
        """
        findings = []

        bypass_headers = [
            {"X-Forwarded-For": "192.168.1.1"},
            {"X-Forwarded-For": "127.0.0.1"},
            {"X-Client-IP": "10.0.0.1"},
            {"CF-Connecting-IP": "1.1.1.1"},
            {"User-Agent": "Mozilla/5.0 (Custom)"},
        ]

        for headers in bypass_headers:
            try:
                # Send multiple requests with bypass header
                success_count = 0

                for _ in range(5):
                    response = requests.get(
                        endpoint_url,
                        headers=headers,
                        timeout=timeout,
                        verify=verify_ssl
                    )

                    if response.status_code == 200:
                        success_count += 1

                if success_count == 5:
                    finding = {
                        "type": "Rate Limit Bypass",
                        "severity": "High",
                        "vulnerability": RateLimitingVulnerability.BYPASSABLE_RATE_LIMIT.value,
                        "bypass_technique": str(headers),
                        "evidence": f"Rate limit bypassed using: {headers}",
                    }
                    findings.append(finding)
                    logger.warning(f"Rate limit bypass found: {headers}")

            except requests.RequestException:
                pass

        return findings


class ConcurrentAccessTester:
    """Tests concurrent access rate limiting"""

    @staticmethod
    def test_concurrent_request_limiting(endpoint_url: str,
                                        concurrent_count: int = 20,
                                        timeout: float = 10.0,
                                        verify_ssl: bool = True) -> Dict[str, Any]:
        """
        Test if endpoint limits concurrent requests.
        
        Returns analysis of concurrent handling
        """
        results = {
            "total_requests": concurrent_count,
            "successful_requests": 0,
            "failed_requests": 0,
            "rate_limited_count": 0,
            "is_limited": False,
        }

        responses = []
        lock = threading.Lock()

        def send_request():
            try:
                response = requests.get(endpoint_url, timeout=timeout, verify=verify_ssl)
                with lock:
                    responses.append(response)
                    if response.status_code == 200:
                        results["successful_requests"] += 1
                    else:
                        results["failed_requests"] += 1

                    # Check for rate limiting
                    is_limited, _ = RateLimitDetector.detect_rate_limiting_behavior(response)
                    if is_limited:
                        results["rate_limited_count"] += 1

            except requests.RequestException:
                with lock:
                    results["failed_requests"] += 1

        # Send concurrent requests
        threads = []
        for _ in range(concurrent_count):
            thread = threading.Thread(target=send_request)
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Analysis
        if results["rate_limited_count"] == 0 and results["successful_requests"] == concurrent_count:
            results["is_limited"] = False
        elif results["rate_limited_count"] > concurrent_count * 0.3:
            results["is_limited"] = True

        return results


class RateLimitTester:
    """Main orchestrator for rate limiting testing"""

    def __init__(self, timeout: float = 10.0, verify_ssl: bool = True):
        self.timeout = timeout
        self.verify_ssl = verify_ssl

    def test_endpoint_rate_limiting(self, endpoint_url: str) -> Dict[str, Any]:
        """
        Comprehensive rate limiting test on endpoint.
        
        Returns analysis of rate limit mechanisms
        """
        findings = {
            "rate_limit_headers": {},
            "threshold_analysis": {},
            "bypass_techniques": [],
            "concurrent_behavior": {},
        }

        try:
            # Check headers
            response = requests.get(endpoint_url, timeout=self.timeout, verify=self.verify_ssl)
            findings["rate_limit_headers"] = RateLimitDetector.detect_rate_limit_headers(dict(response.headers))

            # Measure threshold
            findings["threshold_analysis"] = APIRateLimitTester.measure_rate_limit_threshold(
                endpoint_url, self.timeout, self.verify_ssl
            )

            # Test bypass techniques
            findings["bypass_techniques"] = APIRateLimitTester.test_rate_limit_bypass_techniques(
                endpoint_url, self.timeout, self.verify_ssl
            )

            # Test concurrent access
            findings["concurrent_behavior"] = ConcurrentAccessTester.test_concurrent_request_limiting(
                endpoint_url, 20, self.timeout, self.verify_ssl
            )

        except requests.RequestException as e:
            logger.warning(f"Rate limiting test failed: {e}")

        return findings

    def comprehensive_abuse_test(self, login_endpoint: str = None,
                                api_endpoint: str = None,
                                otp_endpoint: str = None) -> Dict[str, Any]:
        """
        Comprehensive abuse testing across multiple endpoints.
        
        Tests:
        - Login brute force
        - API rate limiting
        - OTP brute force
        """
        findings = {
            "login_brute_force": [],
            "api_rate_limit": {},
            "otp_brute_force": [],
        }

        if login_endpoint:
            findings["login_brute_force"] = BruteForceTester.test_login_brute_force(
                login_endpoint, "admin", self.timeout, self.verify_ssl
            )

        if api_endpoint:
            findings["api_rate_limit"] = self.test_endpoint_rate_limiting(api_endpoint)

        if otp_endpoint:
            findings["otp_brute_force"] = BruteForceTester.test_otp_brute_force(
                otp_endpoint, timeout=self.timeout, verify_ssl=self.verify_ssl
            )

        return findings
