"""
Business Logic Testing Module

Tests for business logic vulnerabilities including workflow bypass,
price manipulation, replay attacks, race conditions, and account takeover.
"""

import re
import time
import threading
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import requests
import logging
from urllib.parse import urljoin, parse_qs, urlparse
from collections import defaultdict

logger = logging.getLogger(__name__)


class BusinessLogicVulnerability(Enum):
    """Types of business logic vulnerabilities"""
    WORKFLOW_BYPASS = "workflow_bypass"
    PRICE_MANIPULATION = "price_manipulation"
    REPLAY_ATTACK = "replay_attack"
    RACE_CONDITION = "race_condition"
    ACCOUNT_TAKEOVER = "account_takeover"
    STEP_SEQUENCING = "step_sequencing"


@dataclass
class WorkflowStep:
    """Represents a workflow step"""
    step_name: str
    endpoint: str
    method: str
    required_params: Dict[str, str]
    response_indicator: str  # Pattern to detect successful step


class WorkflowAnalyzer:
    """Analyzes application workflows"""

    @staticmethod
    def detect_multi_step_workflow(html_content: str, base_url: str) -> List[WorkflowStep]:
        """
        Detect multi-step workflows (e.g., signup, checkout, password reset).
        Looks for sequential forms or state progression.
        
        Returns list of workflow steps
        """
        steps = []

        # Common workflow indicators
        workflow_patterns = [
            (r'step[_\s]*(\d+)', "Step-based form"),
            (r'(confirm|verify|validate|proceed)', "Confirmation step"),
            (r'(review|summary|preview)', "Review step"),
            (r'(complete|finish|submit)', "Final step"),
        ]

        # Find forms in order of appearance
        form_pattern = r'<form[^>]*action=["\']?([^"\'\s>]+)["\']?[^>]*>(.*?)</form>'
        form_order = 0

        for form_match in re.finditer(form_pattern, html_content, re.IGNORECASE | re.DOTALL):
            form_html = form_match.group(0)
            form_content = form_match.group(2)

            # Extract form details
            action_match = re.search(r'action=["\']?([^"\'\s>]+)', form_html, re.IGNORECASE)
            method_match = re.search(r'method=["\']?(\w+)["\']?', form_html, re.IGNORECASE)

            action = action_match.group(1) if action_match else ""
            method = method_match.group(1).upper() if method_match else "POST"

            # Extract form fields
            fields = {}
            input_pattern = r'<input[^>]*name=["\']?([^"\'\s>]+)'
            for inp_match in re.finditer(input_pattern, form_content, re.IGNORECASE):
                fields[inp_match.group(1)] = ""

            if fields:
                step_name = f"Step_{form_order}"

                # Try to identify step purpose
                form_text = form_html.lower()
                for pattern, step_desc in workflow_patterns:
                    if re.search(pattern, form_text):
                        step_name = step_desc
                        break

                step = WorkflowStep(
                    step_name=step_name,
                    endpoint=urljoin(base_url, action) if action else base_url,
                    method=method,
                    required_params=fields,
                    response_indicator=step_name
                )
                steps.append(step)
                form_order += 1

        return steps

    @staticmethod
    def test_step_sequencing(steps: List[WorkflowStep], cookies: Dict[str, str] = None,
                            timeout: float = 10.0, verify_ssl: bool = True) -> List[Dict[str, Any]]:
        """
        Test if workflow steps can be skipped or reordered.
        
        Returns findings for step sequencing vulnerabilities
        """
        findings = []

        if len(steps) < 2:
            return findings

        # Test 1: Skip steps
        # Try to go directly to final step
        for skip_index in range(len(steps) - 1):
            final_step = steps[-1]
            test_params = final_step.required_params.copy()

            try:
                resp = requests.request(
                    final_step.method,
                    final_step.endpoint,
                    data=test_params if final_step.method == "POST" else None,
                    params=test_params if final_step.method == "GET" else None,
                    cookies=cookies,
                    timeout=timeout,
                    verify=verify_ssl
                )

                # If success without completing earlier steps
                if resp.status_code == 200 and "error" not in resp.text.lower():
                    finding = {
                        "type": "Workflow Bypass - Step Skipping",
                        "severity": "High",
                        "vulnerability": BusinessLogicVulnerability.WORKFLOW_BYPASS.value,
                        "endpoint": final_step.endpoint,
                        "skipped_steps": steps[:skip_index+1],
                        "evidence": f"Final step {final_step.step_name} accessible without completing earlier steps",
                    }
                    findings.append(finding)
                    logger.warning("Workflow bypass detected - step skipping")
                    break

            except requests.RequestException:
                pass

        # Test 2: Reverse step order
        if len(steps) >= 3:
            reverse_step = steps[0]
            final_step = steps[-1]

            try:
                # Try final step before initial step
                resp = requests.request(
                    reverse_step.method,
                    final_step.endpoint,
                    data=reverse_step.required_params if reverse_step.method == "POST" else None,
                    params=reverse_step.required_params if reverse_step.method == "GET" else None,
                    cookies=cookies,
                    timeout=timeout,
                    verify=verify_ssl
                )

                if resp.status_code == 200:
                    finding = {
                        "type": "Workflow Bypass - Step Reordering",
                        "severity": "High",
                        "vulnerability": BusinessLogicVulnerability.STEP_SEQUENCING.value,
                        "evidence": "Workflow steps can be executed in arbitrary order",
                    }
                    findings.append(finding)

            except requests.RequestException:
                pass

        return findings


class PricingLogicTester:
    """Tests for price manipulation vulnerabilities"""

    PRICE_PATTERNS = [
        r'price[\'"]?\s*[:=]\s*([0-9.]+)',
        r'amount[\'"]?\s*[:=]\s*([0-9.]+)',
        r'total[\'"]?\s*[:=]\s*([0-9.]+)',
        r'\$\s*([0-9.]+)',
        r'cost[\'"]?\s*[:=]\s*([0-9.]+)',
    ]

    @staticmethod
    def extract_prices(response_text: str) -> List[Tuple[str, str]]:
        """
        Extract prices from response.
        Returns list of (value, context)
        """
        prices = []

        for pattern in PricingLogicTester.PRICE_PATTERNS:
            for match in re.finditer(pattern, response_text):
                price_value = match.group(1)
                context = response_text[max(0, match.start()-50):min(len(response_text), match.end()+50)]
                prices.append((price_value, context))

        return prices

    @staticmethod
    def test_price_manipulation(endpoint_url: str, price_param: str = "price",
                               cookies: Dict[str, str] = None,
                               timeout: float = 10.0,
                               verify_ssl: bool = True) -> List[Dict[str, Any]]:
        """
        Test for price manipulation vulnerabilities.
        Attempts to modify price parameters.
        """
        findings = []

        test_values = [
            ("0", "Zero price"),
            ("0.01", "Minimal price"),
            ("-100", "Negative price"),
            ("9999999", "Extremely high price"),
        ]

        for test_value, description in test_values:
            params = {price_param: test_value}

            try:
                response = requests.post(
                    endpoint_url,
                    data=params,
                    cookies=cookies,
                    timeout=timeout,
                    verify=verify_ssl
                )

                # Check if the modified price was accepted
                if test_value in response.text or "success" in response.text.lower():
                    finding = {
                        "type": "Price Manipulation",
                        "severity": "Critical",
                        "vulnerability": BusinessLogicVulnerability.PRICE_MANIPULATION.value,
                        "endpoint": endpoint_url,
                        "parameter": price_param,
                        "test_value": test_value,
                        "description": description,
                        "evidence": f"System accepted {description}: {test_value}",
                    }
                    findings.append(finding)
                    logger.warning(f"Price manipulation found: {description}")

            except requests.RequestException:
                pass

        return findings


class ReplayAttackTester:
    """Tests for replay attack vulnerabilities"""

    @staticmethod
    def test_state_change_replay(endpoint_url: str, method: str = "POST",
                                params: Dict[str, str] = None,
                                cookies: Dict[str, str] = None,
                                timeout: float = 10.0,
                                verify_ssl: bool = True) -> List[Dict[str, Any]]:
        """
        Test if state-changing requests can be replayed.
        
        Returns findings for replay vulnerabilities
        """
        findings = []

        if params is None:
            params = {}

        try:
            # First request
            resp1 = requests.request(
                method,
                endpoint_url,
                data=params if method in ["POST", "PUT", "DELETE"] else None,
                params=params if method == "GET" else None,
                cookies=cookies,
                timeout=timeout,
                verify=verify_ssl
            )

            if resp1.status_code >= 400:
                return findings

            time.sleep(0.5)  # Small delay

            # Identical replay
            resp2 = requests.request(
                method,
                endpoint_url,
                data=params if method in ["POST", "PUT", "DELETE"] else None,
                params=params if method == "GET" else None,
                cookies=cookies,
                timeout=timeout,
                verify=verify_ssl
            )

            # If both succeed identically, it's a replay vulnerability
            if resp1.status_code == resp2.status_code == 200:
                finding = {
                    "type": "Replay Attack",
                    "severity": "High",
                    "vulnerability": BusinessLogicVulnerability.REPLAY_ATTACK.value,
                    "endpoint": endpoint_url,
                    "method": method,
                    "evidence": "Identical state-changing requests were both accepted",
                }
                findings.append(finding)
                logger.warning("Replay vulnerability detected")

        except requests.RequestException as e:
            logger.debug(f"Replay test failed: {e}")

        return findings

    @staticmethod
    def test_token_reuse(endpoint_url: str, token_param: str = "token",
                        cookies: Dict[str, str] = None,
                        timeout: float = 10.0,
                        verify_ssl: bool = True) -> Tuple[bool, str]:
        """
        Test if tokens/nonces can be reused across requests.
        
        Returns (is_vulnerable, evidence)
        """
        try:
            # Extract token from first request
            resp1 = requests.get(endpoint_url, cookies=cookies, timeout=timeout, verify=verify_ssl)

            token_match = re.search(rf'{token_param}\s*=\s*[\'"]?([a-f0-9\-]+)[\'"]?', resp1.text)
            if not token_match:
                return False, "Could not extract token"

            token_value = token_match.group(1)

            # Try to use same token multiple times
            for attempt in range(2):
                params = {token_param: token_value}
                resp = requests.post(endpoint_url, data=params, cookies=cookies,
                                    timeout=timeout, verify=verify_ssl)

                if resp.status_code >= 400:
                    return False, "Token invalidated after first use (not vulnerable)"

            return True, f"Token was reused successfully ({token_value[:10]}...)"

        except requests.RequestException as e:
            logger.debug(f"Token reuse test failed: {e}")
            return False, f"Test failed: {e}"


class RaceConditionTester:
    """Tests for race condition vulnerabilities"""

    @staticmethod
    def test_concurrent_requests(endpoint_url: str, params: Dict[str, str] = None,
                                cookies: Dict[str, str] = None,
                                method: str = "POST",
                                concurrent_count: int = 10,
                                timeout: float = 10.0,
                                verify_ssl: bool = True) -> List[Dict[str, Any]]:
        """
        Test for race condition vulnerabilities by sending concurrent requests.
        
        Useful for testing:
        - Double spending (e.g., using same voucher twice)
        - Double withdrawal from account
        - Stock manipulation
        """
        findings = []

        if params is None:
            params = {}

        results = []
        errors = []
        lock = threading.Lock()

        def send_request():
            try:
                response = requests.request(
                    method,
                    endpoint_url,
                    data=params if method in ["POST", "PUT"] else None,
                    params=params if method == "GET" else None,
                    cookies=cookies,
                    timeout=timeout,
                    verify=verify_ssl
                )
                with lock:
                    results.append(response.status_code)
            except requests.RequestException as e:
                with lock:
                    errors.append(str(e))

        # Send requests concurrently
        threads = []
        for _ in range(concurrent_count):
            thread = threading.Thread(target=send_request)
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Analyze results
        success_count = sum(1 for code in results if code == 200)

        # If most requests succeeded, it might indicate race condition
        if success_count >= concurrent_count * 0.8:
            finding = {
                "type": "Race Condition - Concurrent Request Processing",
                "severity": "High",
                "vulnerability": BusinessLogicVulnerability.RACE_CONDITION.value,
                "endpoint": endpoint_url,
                "concurrent_requests": concurrent_count,
                "successful_requests": success_count,
                "evidence": f"{success_count}/{concurrent_count} concurrent requests succeeded (possible race condition)",
            }
            findings.append(finding)
            logger.warning("Race condition vulnerability detected")

        return findings


class AccountTakeoverTester:
    """Tests for account takeover vulnerabilities"""

    @staticmethod
    def test_password_reset_bypass(reset_endpoint: str,
                                  user_identifier: str = "email",
                                  user_value: str = None,
                                  timeout: float = 10.0,
                                  verify_ssl: bool = True) -> List[Dict[str, Any]]:
        """
        Test password reset functionality for vulnerabilities.
        Checks for:
        - No rate limiting
        - Predictable reset tokens
        - Missing user validation
        """
        findings = []

        if user_value is None:
            return findings

        # Test 1: Multiple reset requests (no rate limiting)
        reset_attempts = 0
        for attempt in range(5):
            try:
                params = {user_identifier: user_value}
                resp = requests.post(reset_endpoint, data=params, timeout=timeout, verify=verify_ssl)

                if resp.status_code == 200:
                    reset_attempts += 1

            except requests.RequestException:
                pass

        if reset_attempts >= 5:
            finding = {
                "type": "Password Reset - No Rate Limiting",
                "severity": "High",
                "vulnerability": BusinessLogicVulnerability.ACCOUNT_TAKEOVER.value,
                "endpoint": reset_endpoint,
                "evidence": "Password reset endpoint allows multiple requests without rate limiting",
            }
            findings.append(finding)

        # Test 2: Extract reset token from response
        try:
            resp = requests.post(reset_endpoint, data={user_identifier: user_value},
                               timeout=timeout, verify=verify_ssl)

            token_match = re.search(r'(?:token|code|reset_?token)\s*=\s*[\'"]?([a-f0-9\-]{20,})[\'"]?', resp.text)

            if token_match:
                token = token_match.group(1)

                # Try to predict token format
                if AccountTakeoverTester._is_predictable_token(token):
                    finding = {
                        "type": "Account Takeover - Predictable Reset Token",
                        "severity": "Critical",
                        "vulnerability": BusinessLogicVulnerability.ACCOUNT_TAKEOVER.value,
                        "endpoint": reset_endpoint,
                        "token_sample": token[:20] + "...",
                        "evidence": "Reset token appears to follow predictable pattern",
                    }
                    findings.append(finding)

        except requests.RequestException:
            pass

        return findings

    @staticmethod
    def _is_predictable_token(token: str) -> bool:
        """Check if token looks predictable"""
        # Sequential numbers
        if re.match(r'^\d+$', token):
            return True

        # Simple patterns
        if len(set(token)) < 5:  # Low entropy
            return True

        # Timestamp-based
        if re.match(r'^[0-9]{10,}$', token):  # Unix timestamp
            return True

        return False


class BusinessLogicTester:
    """Main orchestrator for business logic testing"""

    def __init__(self, timeout: float = 10.0, verify_ssl: bool = True):
        self.timeout = timeout
        self.verify_ssl = verify_ssl

    def test_application_logic(self, base_url: str, cookies: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Comprehensive business logic testing.
        
        Returns findings organized by vulnerability type
        """
        findings = {
            "workflow": [],
            "pricing": [],
            "replay": [],
            "race_condition": [],
            "account_takeover": [],
        }

        try:
            # Get base page to analyze workflows
            resp = requests.get(base_url, timeout=self.timeout, verify=self.verify_ssl)

            # Analyze workflows
            workflows = WorkflowAnalyzer.detect_multi_step_workflow(resp.text, base_url)
            if workflows:
                workflow_findings = WorkflowAnalyzer.test_step_sequencing(
                    workflows, cookies, self.timeout, self.verify_ssl
                )
                findings["workflow"].extend(workflow_findings)

            # Test for pricing vulnerabilities
            prices = PricingLogicTester.extract_prices(resp.text)
            if prices:
                # Test first price found (simplified)
                for endpoint in self._find_transaction_endpoints(resp.text, base_url):
                    price_findings = PricingLogicTester.test_price_manipulation(
                        endpoint, cookies=cookies, timeout=self.timeout, verify_ssl=self.verify_ssl
                    )
                    findings["pricing"].extend(price_findings)
                    break

        except requests.RequestException as e:
            logger.warning(f"Business logic test failed: {e}")

        return findings

    @staticmethod
    def _find_transaction_endpoints(html_content: str, base_url: str) -> List[str]:
        """Find transaction endpoints (checkout, payment, etc.)"""
        patterns = [
            r'action=["\']?([^"\'\s>]*(?:checkout|payment|transaction|purchase|order)[^"\'\s>]*)["\']?',
            r'href=["\']?([^"\'\s>]*(?:checkout|payment|transaction|purchase|order)[^"\'\s>]*)["\']?',
        ]

        endpoints = []
        for pattern in patterns:
            for match in re.finditer(pattern, html_content, re.IGNORECASE):
                endpoint = match.group(1)
                full_endpoint = urljoin(base_url, endpoint)
                endpoints.append(full_endpoint)

        return list(set(endpoints))  # Deduplicate
