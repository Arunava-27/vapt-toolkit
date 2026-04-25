"""Comprehensive injection testing: SQLi, Command, NoSQL, LDAP."""
import asyncio
import time
from typing import Optional, List, Tuple
from urllib.parse import urljoin, parse_qs, urlencode, urlparse, urlunparse
import aiohttp

from .payloads import (
    SQLI_PAYLOADS, COMMAND_PAYLOADS, NOSQL_PAYLOADS, LDAP_PAYLOADS,
    SQLI_ERROR_SIGNATURES, COMMAND_EXEC_SIGNATURES
)
from .detectors import ResponseAnalyzer
from .web_logger import WebVulnerabilityLogger, HTTPRequest, HTTPResponse
from .surface_mapper import Endpoint, Parameter
from .confidence_scorer import ConfidenceScorer, ConfidenceLevel


class InjectionTester:
    """Comprehensive injection testing across all vector types."""
    
    def __init__(self, depth: int = 1, timeout: int = 10, rate_limit: float = 0.1):
        """
        Initialize injection tester.
        
        Args:
            depth: Payload depth (1-3)
            timeout: Request timeout (seconds)
            rate_limit: Minimum delay between requests (seconds)
        """
        self.depth = max(1, min(3, depth))
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.rate_limit = rate_limit
        self.analyzer = ResponseAnalyzer()
        self.logger = WebVulnerabilityLogger()
        self._last_request_time = 0
    
    async def _rate_limited_request(self, session: aiohttp.ClientSession, method: str, url: str, **kwargs):
        """Make rate-limited HTTP request."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit:
            await asyncio.sleep(self.rate_limit - elapsed)
        
        self._last_request_time = time.time()
        
        try:
            if method.upper() == "GET":
                async with session.get(url, allow_redirects=False, timeout=self.timeout, **kwargs) as resp:
                    status = resp.status
                    headers = dict(resp.headers)
                    body = await resp.text(errors="ignore")
                    response_time = time.time() - self._last_request_time
                    return status, headers, body, response_time
            elif method.upper() == "POST":
                async with session.post(url, allow_redirects=False, timeout=self.timeout, **kwargs) as resp:
                    status = resp.status
                    headers = dict(resp.headers)
                    body = await resp.text(errors="ignore")
                    response_time = time.time() - self._last_request_time
                    return status, headers, body, response_time
        except asyncio.TimeoutError:
            return None, {}, "", self.rate_limit
        except Exception:
            return None, {}, "", 0
        
        return None, {}, "", 0
    
    # ── SQL Injection ────────────────────────────────────────────────────────
    
    async def test_sqli_url_parameter(
        self,
        session: aiohttp.ClientSession,
        endpoint: Endpoint,
        param_name: str,
        progress_cb=None,
    ) -> Optional[dict]:
        """Test SQL injection in URL parameter."""
        if endpoint.method != "GET":
            return None
        
        payloads = SQLI_PAYLOADS.get(self.depth, {})
        
        # Test error-based SQLi
        for payload in payloads.get("error_based", []):
            modified_url = self._inject_url_param(endpoint.url, param_name, payload)
            
            status, headers, body, resp_time = await self._rate_limited_request(session, "GET", modified_url)
            if status is None:
                continue
            
            # Check for SQL errors
            is_vuln, db_type, signature = self.analyzer.detect_sqli_error(body)
            
            if is_vuln:
                finding = self.logger.log_finding(
                    vuln_type="SQL Injection (Error-Based)",
                    severity="Critical",
                    endpoint=endpoint.url,
                    method=endpoint.method,
                    parameter=param_name,
                    payload=payload,
                    evidence=f"{db_type} detected: {signature}",
                    request=self.logger.capture_request("GET", modified_url, headers),
                    response=self.logger.capture_response(status, headers, body, resp_time),
                )
                
                # Calculate confidence
                conf_score, conf_level = ConfidenceScorer.calculate_confidence(
                    "SQL Injection",
                    ["error_based"],
                    {"error_detection": True},
                    {"response_status": "unexpected", "reproducible": True}
                )
                
                finding_dict = finding.to_dict()
                finding_dict.update({
                    "confidence_score": conf_score,
                    "confidence_level": conf_level,
                    "detection_methods": ["error_based"],
                    "verification_steps": ConfidenceScorer.get_verification_hints(
                        "SQL Injection", endpoint.url, param_name, "error_based"
                    ),
                    "false_positive_risk": ConfidenceScorer.get_false_positive_risk(
                        "SQL Injection", ["error_based"], conf_score
                    ),
                })
                return finding_dict
        
        # Test time-based blind SQLi
        baseline_url = self._inject_url_param(endpoint.url, param_name, "1")
        _, _, _, baseline_time = await self._rate_limited_request(session, "GET", baseline_url)
        
        for payload in payloads.get("time_based", []):
            modified_url = self._inject_url_param(endpoint.url, param_name, payload)
            _, _, body, resp_time = await self._rate_limited_request(session, "GET", modified_url)
            
            if self.analyzer.detect_sqli_time_based(resp_time, baseline_time):
                finding = self.logger.log_finding(
                    vuln_type="SQL Injection (Time-Based Blind)",
                    severity="Critical",
                    endpoint=endpoint.url,
                    method=endpoint.method,
                    parameter=param_name,
                    payload=payload,
                    evidence=f"Response delay: {resp_time:.2f}s vs baseline {baseline_time:.2f}s",
                )
                
                # Calculate confidence
                conf_score, conf_level = ConfidenceScorer.calculate_confidence(
                    "SQL Injection",
                    ["time_based"],
                    {"timing_detection": True},
                    {"response_status": "unexpected", "reproducible": True}
                )
                
                finding_dict = finding.to_dict()
                finding_dict.update({
                    "confidence_score": conf_score,
                    "confidence_level": conf_level,
                    "detection_methods": ["time_based"],
                    "verification_steps": ConfidenceScorer.get_verification_hints(
                        "SQL Injection", endpoint.url, param_name, "time_based"
                    ),
                    "false_positive_risk": ConfidenceScorer.get_false_positive_risk(
                        "SQL Injection", ["time_based"], conf_score
                    ),
                })
                return finding_dict
        
        return None
    
    async def test_sqli_form_field(
        self,
        session: aiohttp.ClientSession,
        endpoint: Endpoint,
        field_name: str,
        form_action: str,
        progress_cb=None,
    ) -> Optional[dict]:
        """Test SQL injection in form field."""
        if endpoint.method.upper() not in ("POST", "GET"):
            return None
        
        payloads = SQLI_PAYLOADS.get(self.depth, {})
        
        # Build form data with all required fields
        form_data = {}
        if endpoint.forms:
            for form in endpoint.forms:
                for field in form.fields:
                    form_data[field.name] = field.value
        
        # Test error-based SQLi
        for payload in payloads.get("error_based", []):
            test_data = form_data.copy()
            test_data[field_name] = payload
            
            status, headers, body, resp_time = await self._rate_limited_request(
                session,
                endpoint.method,
                form_action,
                data=test_data,
            )
            
            if status is None:
                continue
            
            is_vuln, db_type, signature = self.analyzer.detect_sqli_error(body)
            
            if is_vuln:
                finding = self.logger.log_finding(
                    vuln_type="SQL Injection (Form Field - Error-Based)",
                    severity="Critical",
                    endpoint=form_action,
                    method=endpoint.method,
                    parameter=field_name,
                    payload=payload,
                    evidence=f"{db_type} detected: {signature}",
                )
                
                # Calculate confidence
                conf_score, conf_level = ConfidenceScorer.calculate_confidence(
                    "SQL Injection",
                    ["error_based"],
                    {"error_detection": True},
                    {"response_status": "unexpected", "reproducible": True}
                )
                
                finding_dict = finding.to_dict()
                finding_dict.update({
                    "confidence_score": conf_score,
                    "confidence_level": conf_level,
                    "detection_methods": ["error_based"],
                    "verification_steps": ConfidenceScorer.get_verification_hints(
                        "SQL Injection", form_action, field_name, "error_based"
                    ),
                    "false_positive_risk": ConfidenceScorer.get_false_positive_risk(
                        "SQL Injection", ["error_based"], conf_score
                    ),
                })
                return finding_dict
        
        return None
    
    # ── Command Injection ────────────────────────────────────────────────────
    
    async def test_command_injection(
        self,
        session: aiohttp.ClientSession,
        endpoint: Endpoint,
        param_name: str,
        progress_cb=None,
    ) -> Optional[dict]:
        """Test command injection in URL parameter."""
        if endpoint.method != "GET":
            return None
        
        payloads = COMMAND_PAYLOADS.get(self.depth, [])
        
        for payload in payloads:
            modified_url = self._inject_url_param(endpoint.url, param_name, payload)
            
            status, headers, body, resp_time = await self._rate_limited_request(session, "GET", modified_url)
            if status is None:
                continue
            
            # Check for command execution indicators
            is_vuln, os_type = self.analyzer.detect_command_exec(body)
            
            if is_vuln:
                finding = self.logger.log_finding(
                    vuln_type="Command Injection",
                    severity="Critical",
                    endpoint=endpoint.url,
                    method=endpoint.method,
                    parameter=param_name,
                    payload=payload,
                    evidence=f"{os_type} command execution detected",
                )
                
                # Calculate confidence
                conf_score, conf_level = ConfidenceScorer.calculate_confidence(
                    "Injection",
                    ["command_execution"],
                    {"command_detection": True},
                    {"response_status": "unexpected", "payload_complexity": "complex"}
                )
                
                finding_dict = finding.to_dict()
                finding_dict.update({
                    "confidence_score": conf_score,
                    "confidence_level": conf_level,
                    "detection_methods": ["command_execution"],
                    "verification_steps": ConfidenceScorer.get_verification_hints(
                        "Injection", endpoint.url, param_name, "command_execution"
                    ),
                    "false_positive_risk": ConfidenceScorer.get_false_positive_risk(
                        "Injection", ["command_execution"], conf_score
                    ),
                })
                return finding_dict
        
        return None
    
    # ── NoSQL Injection ──────────────────────────────────────────────────────
    
    async def test_nosql_injection(
        self,
        session: aiohttp.ClientSession,
        endpoint: Endpoint,
        param_name: str,
        progress_cb=None,
    ) -> Optional[dict]:
        """Test NoSQL injection in URL parameter."""
        if endpoint.method != "GET":
            return None
        
        payloads = NOSQL_PAYLOADS.get(self.depth, [])
        
        for payload in payloads:
            modified_url = self._inject_url_param(endpoint.url, param_name, payload)
            
            status, headers, body, resp_time = await self._rate_limited_request(session, "GET", modified_url)
            if status is None:
                continue
            
            # Check for NoSQL error indicators
            is_vuln = self.analyzer.detect_nosql_injection(body)
            
            if is_vuln:
                finding = self.logger.log_finding(
                    vuln_type="NoSQL Injection",
                    severity="Critical",
                    endpoint=endpoint.url,
                    method=endpoint.method,
                    parameter=param_name,
                    payload=payload,
                    evidence="NoSQL error or type error detected in response",
                )
                
                # Calculate confidence
                conf_score, conf_level = ConfidenceScorer.calculate_confidence(
                    "Injection",
                    ["error_detection"],
                    {"error_detection": True},
                    {"response_status": "unexpected"}
                )
                
                finding_dict = finding.to_dict()
                finding_dict.update({
                    "confidence_score": conf_score,
                    "confidence_level": conf_level,
                    "detection_methods": ["error_detection"],
                    "verification_steps": ConfidenceScorer.get_verification_hints(
                        "Injection", endpoint.url, param_name, "error_detection"
                    ),
                    "false_positive_risk": ConfidenceScorer.get_false_positive_risk(
                        "Injection", ["error_detection"], conf_score
                    ),
                })
                return finding_dict
        
        return None
    
    # ── LDAP Injection ───────────────────────────────────────────────────────
    
    async def test_ldap_injection(
        self,
        session: aiohttp.ClientSession,
        endpoint: Endpoint,
        param_name: str,
        progress_cb=None,
    ) -> Optional[dict]:
        """Test LDAP injection in URL parameter."""
        if endpoint.method != "GET":
            return None
        
        payloads = LDAP_PAYLOADS.get(self.depth, [])
        
        for payload in payloads:
            modified_url = self._inject_url_param(endpoint.url, param_name, payload)
            
            status, headers, body, resp_time = await self._rate_limited_request(session, "GET", modified_url)
            if status is None:
                continue
            
            # Check for LDAP error indicators
            ldap_indicators = [
                "ldap:", "ldapError", "LDAP search error",
                "No such object", "Invalid DN", "undefined entry",
            ]
            
            if any(ind in body for ind in ldap_indicators):
                finding = self.logger.log_finding(
                    vuln_type="LDAP Injection",
                    severity="High",
                    endpoint=endpoint.url,
                    method=endpoint.method,
                    parameter=param_name,
                    payload=payload,
                    evidence="LDAP error detected in response",
                )
                
                # Calculate confidence
                conf_score, conf_level = ConfidenceScorer.calculate_confidence(
                    "Injection",
                    ["error_detection"],
                    {"error_detection": True},
                    {"response_status": "unexpected"}
                )
                
                finding_dict = finding.to_dict()
                finding_dict.update({
                    "confidence_score": conf_score,
                    "confidence_level": conf_level,
                    "detection_methods": ["error_detection"],
                    "verification_steps": ConfidenceScorer.get_verification_hints(
                        "Injection", endpoint.url, param_name, "error_detection"
                    ),
                    "false_positive_risk": ConfidenceScorer.get_false_positive_risk(
                        "Injection", ["error_detection"], conf_score
                    ),
                })
                return finding_dict
        
        return None
    
    # ── Helpers ──────────────────────────────────────────────────────────────
    
    @staticmethod
    def _inject_url_param(url: str, param: str, value: str) -> str:
        """Inject/modify URL parameter."""
        parsed = urlparse(url)
        params = parse_qs(parsed.query, keep_blank_values=True)
        params[param] = [value]
        
        query_string = urlencode(params, doseq=True)
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            query_string,
            parsed.fragment,
        ))
    
    async def test_endpoint(
        self,
        session: aiohttp.ClientSession,
        endpoint: Endpoint,
        progress_cb=None,
    ) -> List[dict]:
        """Test all injection vectors on an endpoint."""
        findings = []
        
        # Test each parameter
        for param in endpoint.parameters:
            if progress_cb:
                await progress_cb(f"Testing injection on {endpoint.method} {endpoint.url}?{param.name}")
            
            # SQLi
            result = await self.test_sqli_url_parameter(session, endpoint, param.name, progress_cb)
            if result:
                findings.append(result)
                continue  # Skip other tests if SQLi found
            
            # Command Injection
            result = await self.test_command_injection(session, endpoint, param.name, progress_cb)
            if result:
                findings.append(result)
                continue
            
            # NoSQL Injection
            result = await self.test_nosql_injection(session, endpoint, param.name, progress_cb)
            if result:
                findings.append(result)
                continue
            
            # LDAP Injection
            result = await self.test_ldap_injection(session, endpoint, param.name, progress_cb)
            if result:
                findings.append(result)
        
        return findings
    
    async def run(
        self,
        endpoints: List[Endpoint],
        progress_cb=None,
    ) -> dict:
        """
        Run injection tests on all endpoints.
        
        Returns: Results summary
        """
        all_findings = []
        
        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                if endpoint.method != "GET" and not endpoint.parameters:
                    continue
                
                findings = await self.test_endpoint(session, endpoint, progress_cb)
                all_findings.extend(findings)
        
        return {
            "total_endpoints_tested": len(endpoints),
            "total_findings": len(all_findings),
            "findings": all_findings,
        }
