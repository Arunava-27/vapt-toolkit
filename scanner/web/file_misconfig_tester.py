"""
File Handling & Security Misconfiguration Module

Tests for file upload vulnerabilities, path traversal, and security misconfigurations.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import requests
import logging
from urllib.parse import urljoin, urlparse
import mimetypes
from .confidence_scorer import ConfidenceScorer, ConfidenceLevel

logger = logging.getLogger(__name__)


class FileUploadVulnerability(Enum):
    """Types of file upload vulnerabilities"""
    EXEC_RISK = "execution_risk"
    MIME_BYPASS = "mime_type_bypass"
    PATH_TRAVERSAL = "path_traversal"
    LFI = "local_file_inclusion"
    OVERWRITE = "file_overwrite"


@dataclass
class FileUploadPayload:
    """Represents a file upload test payload"""
    filename: str
    content: bytes
    content_type: str
    description: str
    bypass_type: str


class FileUploadDetector:
    """Detects file upload endpoints"""

    @staticmethod
    def find_upload_endpoints(html_content: str, base_url: str) -> List[Dict[str, Any]]:
        """
        Find file upload endpoints in HTML.
        Looks for forms with file inputs and enctype="multipart/form-data".
        
        Returns list of {url, fields, method}
        """
        endpoints = []

        # Find all forms with file inputs
        form_pattern = r'<form[^>]*enctype=["\']?multipart/form-data["\']?[^>]*>(.*?)</form>'
        for form_match in re.finditer(form_pattern, html_content, re.IGNORECASE | re.DOTALL):
            form_html = form_match.group(0)
            form_content = form_match.group(1)

            # Extract action and method
            action_match = re.search(r'action=["\']?([^"\'\s>]+)', form_html, re.IGNORECASE)
            method_match = re.search(r'method=["\']?(\w+)["\']?', form_html, re.IGNORECASE)

            action = action_match.group(1) if action_match else ""
            method = method_match.group(1).upper() if method_match else "POST"

            # Extract file input fields
            file_fields = []
            input_pattern = r'<input[^>]*type=["\']?file["\']?[^>]*name=["\']?([^"\'\s>]+)'
            for inp_match in re.finditer(input_pattern, form_content, re.IGNORECASE):
                file_fields.append(inp_match.group(1))

            if file_fields:
                endpoints.append({
                    "url": urljoin(base_url, action) if action else base_url,
                    "method": method,
                    "file_fields": file_fields,
                    "raw_html": form_html[:300],
                })

        return endpoints

    @staticmethod
    def extract_upload_restrictions(html_content: str) -> Dict[str, Any]:
        """
        Extract client-side upload restrictions.
        Looks for accept attributes and JavaScript validation.
        """
        restrictions = {
            "accepted_types": [],
            "max_size": None,
            "client_validation": False,
        }

        # Look for accept attributes
        accept_pattern = r'accept=["\']?([^"\'\s>]+)'
        for match in re.finditer(accept_pattern, html_content):
            types = match.group(1).split(',')
            restrictions["accepted_types"].extend([t.strip() for t in types])

        # Look for file size limits
        size_pattern = r'maxsize|max[_-]?size|size[_-]?limit\s*[:=]\s*(\d+)'
        if re.search(size_pattern, html_content, re.IGNORECASE):
            restrictions["max_size"] = 1000000  # Placeholder

        # Check for JavaScript validation
        if "validate" in html_content.lower() and "file" in html_content.lower():
            restrictions["client_validation"] = True

        return restrictions


class FileHandlingTester:
    """Tests file upload and handling vulnerabilities"""

    def __init__(self, timeout: float = 10.0, verify_ssl: bool = True):
        self.timeout = timeout
        self.verify_ssl = verify_ssl

    def test_file_upload(self, endpoint_url: str, file_field_name: str,
                        cookies: Dict[str, str] = None,
                        headers: Dict[str, str] = None) -> List[Dict[str, Any]]:
        """
        Test file upload endpoint for vulnerabilities.
        
        Tests:
        - Executable file upload (.php, .jsp, .asp)
        - MIME type bypass
        - Path traversal in filename
        - Double extension bypass
        """
        findings = []

        payloads = self._generate_upload_payloads()

        for payload in payloads:
            try:
                # Prepare file for upload
                files = {file_field_name: (payload.filename, payload.content, payload.content_type)}
                req_headers = {"User-Agent": "VAPT-Scanner/1.0"} | (headers or {})

                # Bypass MIME type check with double content-type
                response = requests.post(
                    endpoint_url,
                    files=files,
                    cookies=cookies,
                    headers=req_headers,
                    timeout=self.timeout,
                    verify=self.verify_ssl
                )

                # Analyze response
                if response.status_code == 200:
                    # Upload succeeded
                    finding = self._analyze_upload_response(response, payload, endpoint_url, file_field_name)
                    if finding:
                        conf_score, conf_level = ConfidenceScorer.calculate_confidence(
                            "File Upload",
                            ["file_upload"],
                            {"upload_success": True},
                            {"response_status": "unexpected", "reproducible": True}
                        )
                        finding.update({
                            "confidence_score": conf_score,
                            "confidence_level": conf_level,
                            "detection_methods": ["file_upload"],
                            "verification_steps": ConfidenceScorer.get_verification_hints(
                                "File Upload", endpoint_url, file_field_name, "file_upload"
                            ),
                            "false_positive_risk": ConfidenceScorer.get_false_positive_risk(
                                "File Upload", ["file_upload"], conf_score
                            ),
                        })
                        findings.append(finding)
                        logger.warning(f"File upload vulnerability detected: {payload.description}")

                # Check if file was stored
                stored_path = self._detect_file_storage(response, payload.filename)
                if stored_path:
                    finding = {
                        "type": "File Upload Risk",
                        "severity": "High" if any(x in payload.filename for x in [".php", ".jsp", ".asp"]) else "Medium",
                        "url": endpoint_url,
                        "file_field": file_field_name,
                        "filename": payload.filename,
                        "bypass_type": payload.bypass_type,
                        "evidence": f"File uploaded successfully: {stored_path}",
                        "status_code": response.status_code,
                    }
                    conf_score, conf_level = ConfidenceScorer.calculate_confidence(
                        "File Upload",
                        ["file_upload"],
                        {"file_detected": True},
                        {"response_status": "unexpected", "reproducible": True}
                    )
                    finding.update({
                        "confidence_score": conf_score,
                        "confidence_level": conf_level,
                        "detection_methods": ["file_upload"],
                        "verification_steps": ConfidenceScorer.get_verification_hints(
                            "File Upload", endpoint_url, file_field_name, "file_upload"
                        ),
                        "false_positive_risk": ConfidenceScorer.get_false_positive_risk(
                            "File Upload", ["file_upload"], conf_score
                        ),
                    })
                    findings.append(finding)

            except requests.RequestException as e:
                logger.debug(f"Upload test failed: {e}")
                continue

        return findings

    def test_path_traversal(self, endpoint_url: str, parameter_name: str = "file",
                           cookies: Dict[str, str] = None,
                           headers: Dict[str, str] = None) -> List[Dict[str, Any]]:
        """
        Test file handling endpoints for path traversal vulnerabilities.
        
        Attempts to access files outside intended directory.
        """
        findings = []

        payloads = [
            ("../../../etc/passwd", "Unix password file"),
            ("..\\..\\..\\windows\\win.ini", "Windows config"),
            ("....//....//....//etc/passwd", "Double encoding bypass"),
            ("%2e%2e%2f%2e%2e%2fetc%2fpasswd", "URL encoding bypass"),
            ("..;/..;/..;/etc/passwd", "Semicolon bypass"),
            ("....%5c....%5c....%5cwindows%5cwin.ini", "Backslash encoding"),
        ]

        for path, description in payloads:
            try:
                params = {parameter_name: path}
                response = requests.get(
                    endpoint_url,
                    params=params,
                    cookies=cookies,
                    headers=headers,
                    timeout=self.timeout,
                    verify=self.verify_ssl
                )

                # Check for file content indicators
                if self._contains_file_content(response.text, path):
                    finding = {
                        "type": "Path Traversal / Local File Inclusion",
                        "severity": "Critical",
                        "url": endpoint_url,
                        "parameter": parameter_name,
                        "payload": path,
                        "description": description,
                        "evidence": f"File content retrieved: {response.text[:100]}...",
                    }
                    conf_score, conf_level = ConfidenceScorer.calculate_confidence(
                        "Path Traversal",
                        ["file_upload"],
                        {"file_content_detected": True},
                        {"response_status": "unexpected", "reproducible": True}
                    )
                    finding.update({
                        "confidence_score": conf_score,
                        "confidence_level": conf_level,
                        "detection_methods": ["file_upload"],
                        "verification_steps": ConfidenceScorer.get_verification_hints(
                            "Path Traversal", endpoint_url, parameter_name, "file_upload"
                        ),
                        "false_positive_risk": ConfidenceScorer.get_false_positive_risk(
                            "Path Traversal", ["file_upload"], conf_score
                        ),
                    })
                    findings.append(finding)
                    logger.warning(f"Path traversal found: {path}")

            except requests.RequestException as e:
                logger.debug(f"Path traversal test failed: {e}")
                continue

        return findings

    @staticmethod
    def _generate_upload_payloads() -> List[FileUploadPayload]:
        """Generate file upload test payloads"""
        payloads = [
            FileUploadPayload(
                filename="test.php",
                content=b"<?php echo 'XSSVULN'; ?>",
                content_type="image/jpeg",  # MIME type bypass
                description="PHP shell with JPEG MIME type",
                bypass_type="mime_bypass"
            ),
            FileUploadPayload(
                filename="test.php.jpg",
                content=b"<?php echo 'XSSVULN'; ?>",
                content_type="image/jpeg",
                description="PHP shell with double extension",
                bypass_type="double_extension"
            ),
            FileUploadPayload(
                filename="test.jpg.php",
                content=b"<?php echo 'XSSVULN'; ?>",
                content_type="image/jpeg",
                description="PHP shell with reverse double extension",
                bypass_type="reverse_extension"
            ),
            FileUploadPayload(
                filename="test.phtml",
                content=b"<?php echo 'XSSVULN'; ?>",
                content_type="image/jpeg",
                description="PHTML shell (executable by many servers)",
                bypass_type="alternative_ext"
            ),
            FileUploadPayload(
                filename="test.jsp",
                content=b"<%= \"XSSVULN\" %>",
                content_type="image/jpeg",
                description="JSP shell",
                bypass_type="jsp_upload"
            ),
            FileUploadPayload(
                filename="..\\..\\shell.php",
                content=b"<?php echo 'XSSVULN'; ?>",
                content_type="image/jpeg",
                description="Path traversal in filename (Windows)",
                bypass_type="path_traversal"
            ),
            FileUploadPayload(
                filename="../../../../tmp/shell.php",
                content=b"<?php echo 'XSSVULN'; ?>",
                content_type="image/jpeg",
                description="Path traversal in filename (Unix)",
                bypass_type="path_traversal"
            ),
        ]
        return payloads

    @staticmethod
    def _analyze_upload_response(response: requests.Response, payload: FileUploadPayload,
                                endpoint_url: str, file_field: str) -> Optional[Dict[str, Any]]:
        """Analyze response to determine if upload poses execution risk"""
        
        # Check for file path in response
        if payload.filename in response.text:
            return {
                "type": "File Upload - Execution Risk",
                "severity": "Critical",
                "url": endpoint_url,
                "file_field": file_field,
                "filename": payload.filename,
                "bypass_type": payload.bypass_type,
                "evidence": f"Uploaded file path exposed in response",
            }

        # Check for success messages
        if "success" in response.text.lower() or "uploaded" in response.text.lower():
            return {
                "type": "File Upload - Possible Execution",
                "severity": "High",
                "url": endpoint_url,
                "file_field": file_field,
                "filename": payload.filename,
                "bypass_type": payload.bypass_type,
                "evidence": "Upload succeeded with executable file type",
            }

        return None

    @staticmethod
    def _detect_file_storage(response: requests.Response, filename: str) -> Optional[str]:
        """Detect where file was stored"""
        # Look for common storage patterns
        patterns = [
            rf'(/uploads/.*{re.escape(filename)})',
            rf'(/files/.*{re.escape(filename)})',
            rf'(uploads["\']?\s*:\s*["\'].*{re.escape(filename)})',
            rf'([^"\s]+{re.escape(filename)})',
        ]

        for pattern in patterns:
            match = re.search(pattern, response.text)
            if match:
                return match.group(1)

        return None

    @staticmethod
    def _contains_file_content(response_text: str, path: str) -> bool:
        """Check if response contains expected file content"""
        # Check for Unix password file content
        if "passwd" in path and ("root:" in response_text or "/bin/" in response_text):
            return True

        # Check for Windows config
        if "win.ini" in path and ("[" in response_text or "=" in response_text):
            return True

        # Generic file content indicators
        if "ERROR" not in response_text and "404" not in response_text and len(response_text) > 50:
            return True

        return False


class SecurityMisconfigurationTester:
    """Tests for security misconfiguration vulnerabilities"""

    def __init__(self, timeout: float = 10.0, verify_ssl: bool = True):
        self.timeout = timeout
        self.verify_ssl = verify_ssl

    def test_security_headers(self, url: str) -> List[Dict[str, Any]]:
        """
        Test for missing security headers.
        Checks for: HSTS, CSP, X-Frame-Options, X-Content-Type-Options, etc.
        """
        findings = []

        try:
            response = requests.get(url, timeout=self.timeout, verify=self.verify_ssl)
            headers = dict(response.headers)

            # Critical security headers
            security_headers = {
                "Strict-Transport-Security": "HSTS - Forces HTTPS",
                "Content-Security-Policy": "CSP - Prevents XSS/injection",
                "X-Frame-Options": "Clickjacking protection",
                "X-Content-Type-Options": "MIME-type sniffing protection",
                "Referrer-Policy": "Referrer information control",
                "Permissions-Policy": "Feature policy for browser features",
            }

            for header_name, description in security_headers.items():
                if header_name not in headers:
                    finding = {
                        "type": "Missing Security Header",
                        "severity": "Medium",
                        "url": url,
                        "header": header_name,
                        "description": description,
                        "evidence": f"Header '{header_name}' not present",
                    }
                    conf_score, conf_level = ConfidenceScorer.calculate_confidence(
                        "Security Misconfiguration",
                        ["default_value"],
                        {"header_missing": True},
                        {"reproducible": True}
                    )
                    finding.update({
                        "confidence_score": conf_score,
                        "confidence_level": conf_level,
                        "detection_methods": ["default_value"],
                        "verification_steps": ConfidenceScorer.get_verification_hints(
                            "Security Misconfiguration", url, header_name, "default_value"
                        ),
                        "false_positive_risk": ConfidenceScorer.get_false_positive_risk(
                            "Security Misconfiguration", ["default_value"], conf_score
                        ),
                    })
                    findings.append(finding)

        except requests.RequestException as e:
            logger.debug(f"Security header check failed: {e}")

        return findings

    def test_directory_listing(self, url: str) -> List[Dict[str, Any]]:
        """Test for directory listing enabled"""
        findings = []

        # Common web directories
        directories = ["/", "/uploads", "/files", "/images", "/assets", "/api", "/admin"]

        for directory in directories:
            test_url = urljoin(url, directory)

            try:
                response = requests.get(test_url, timeout=self.timeout, verify=self.verify_ssl)

                # Check for directory listing patterns
                if self._is_directory_listing(response.text):
                    finding = {
                        "type": "Directory Listing Enabled",
                        "severity": "Medium",
                        "url": test_url,
                        "evidence": "Server exposes directory contents",
                    }
                    conf_score, conf_level = ConfidenceScorer.calculate_confidence(
                        "Security Misconfiguration",
                        ["default_value"],
                        {"directory_listing_detected": True},
                        {"reproducible": True}
                    )
                    finding.update({
                        "confidence_score": conf_score,
                        "confidence_level": conf_level,
                        "detection_methods": ["default_value"],
                        "verification_steps": ConfidenceScorer.get_verification_hints(
                            "Security Misconfiguration", test_url, "directory", "default_value"
                        ),
                        "false_positive_risk": ConfidenceScorer.get_false_positive_risk(
                            "Security Misconfiguration", ["default_value"], conf_score
                        ),
                    })
                    findings.append(finding)
                    logger.warning(f"Directory listing found: {test_url}")

            except requests.RequestException:
                pass

        return findings

    def test_debug_endpoints(self, url: str) -> List[Dict[str, Any]]:
        """Test for exposed debug endpoints"""
        findings = []

        # Common debug paths
        debug_paths = [
            "/debug", "/admin", "/actuator", "/status", "/.git",
            "/.env", "/config", "/api/debug", "/console",
            "/swagger-ui", "/graphql", "/graphiql",
        ]

        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

        for path in debug_paths:
            test_url = urljoin(base_url, path)

            try:
                response = requests.get(test_url, timeout=self.timeout, verify=self.verify_ssl)

                if response.status_code < 400:
                    finding = {
                        "type": "Debug Endpoint Exposed",
                        "severity": "High",
                        "url": test_url,
                        "status_code": response.status_code,
                        "evidence": f"Debug endpoint accessible at {path}",
                    }
                    conf_score, conf_level = ConfidenceScorer.calculate_confidence(
                        "Security Misconfiguration",
                        ["debug_enabled"],
                        {"endpoint_accessible": True},
                        {"response_status": "unexpected", "reproducible": True}
                    )
                    finding.update({
                        "confidence_score": conf_score,
                        "confidence_level": conf_level,
                        "detection_methods": ["debug_enabled"],
                        "verification_steps": ConfidenceScorer.get_verification_hints(
                            "Security Misconfiguration", test_url, "debug_endpoint", "debug_enabled"
                        ),
                        "false_positive_risk": ConfidenceScorer.get_false_positive_risk(
                            "Security Misconfiguration", ["debug_enabled"], conf_score
                        ),
                    })
                    findings.append(finding)
                    logger.warning(f"Debug endpoint found: {test_url}")

            except requests.RequestException:
                pass

        return findings

    def test_default_credentials(self, base_url: str) -> List[Dict[str, Any]]:
        """Test for common default credentials"""
        findings = []

        # Common admin paths and default credentials
        admin_endpoints = [
            ("/admin", [("admin", "admin"), ("admin", "password")]),
            ("/administrator", [("admin", "admin")]),
            ("/wp-admin", [("admin", "admin")]),
        ]

        for path, credentials in admin_endpoints:
            test_url = urljoin(base_url, path)

            for username, password in credentials:
                try:
                    response = requests.post(
                        test_url,
                        data={"username": username, "password": password},
                        timeout=self.timeout,
                        verify=self.verify_ssl
                    )

                    if response.status_code == 200 or "success" in response.text.lower():
                        finding = {
                            "type": "Default Credentials",
                            "severity": "Critical",
                            "url": test_url,
                            "username": username,
                            "password": password,
                            "evidence": f"Login successful with {username}:{password}",
                        }
                        conf_score, conf_level = ConfidenceScorer.calculate_confidence(
                            "Authentication",
                            ["default_value"],
                            {"credentials_accepted": True},
                            {"response_status": "unexpected", "reproducible": True}
                        )
                        finding.update({
                            "confidence_score": conf_score,
                            "confidence_level": conf_level,
                            "detection_methods": ["default_value"],
                            "verification_steps": ConfidenceScorer.get_verification_hints(
                                "Authentication", test_url, "credentials", "default_value"
                            ),
                            "false_positive_risk": ConfidenceScorer.get_false_positive_risk(
                                "Authentication", ["default_value"], conf_score
                            ),
                        })
                        findings.append(finding)
                        logger.warning(f"Default credentials found: {username}:{password}")

                except requests.RequestException:
                    pass

        return findings

    @staticmethod
    def _is_directory_listing(html_content: str) -> bool:
        """Check if response is a directory listing"""
        patterns = [
            r"<pre>",
            r"Index of",
            r"\[Dir\]",
            r"Parent Directory",
            r"<a href=",
        ]

        return any(re.search(pattern, html_content, re.IGNORECASE) for pattern in patterns)
