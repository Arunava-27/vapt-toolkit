"""
Web Vulnerability Scanner Integration & Orchestration

Main orchestrator that ties together all vulnerability testing modules
and integrates with the VAPT toolkit's scanning infrastructure.
"""

import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import requests

from scanner.web.scope_enforcer import ScopeEnforcer
from scanner.web.surface_mapper import SurfaceMapper
from scanner.web.injection_tester import InjectionTester
from scanner.web.xss_tester import XSSTester
from scanner.web.auth_tester import AuthenticationTester
from scanner.web.access_control_tester import IDORTester
from scanner.web.csrf_ssrf_tester import CSRFTester, SSRFTester
from scanner.web.file_misconfig_tester import FileHandlingTester, SecurityMisconfigurationTester
from scanner.web.sensitive_data_tester import SensitiveDataTester
from scanner.web.business_logic_tester import BusinessLogicTester
from scanner.web.ratelimit_tester import RateLimitTester
from scanner.web.evidence_collector import VulnerabilityAggregator

logger = logging.getLogger(__name__)


class ScanPhase(Enum):
    """Phases of the web vulnerability scan"""
    RECONNAISSANCE = "reconnaissance"
    SURFACE_MAPPING = "surface_mapping"
    INJECTION = "injection"
    XSS = "xss"
    AUTHENTICATION = "authentication"
    ACCESS_CONTROL = "access_control"
    CSRF_SSRF = "csrf_ssrf"
    FILE_UPLOAD = "file_upload"
    MISCONFIGURATION = "misconfiguration"
    SENSITIVE_DATA = "sensitive_data"
    BUSINESS_LOGIC = "business_logic"
    RATE_LIMITING = "rate_limiting"
    REPORTING = "reporting"


@dataclass
class WebScanConfiguration:
    """Configuration for web vulnerability scan"""
    target_url: str
    scope: List[str] = None  # URLs to scan (default: same domain)
    scope_strict: bool = False  # If True, only scan exact scope URLs
    override_robots_txt: bool = False
    verify_ssl: bool = True
    request_timeout: float = 10.0
    depth: int = 1  # Testing depth (1=basic, 2=extended, 3=advanced)
    
    # Module toggles
    test_injection: bool = True
    test_xss: bool = True
    test_auth: bool = True
    test_idor: bool = True
    test_csrf_ssrf: bool = True
    test_file_upload: bool = True
    test_misconfiguration: bool = True
    test_sensitive_data: bool = True
    test_business_logic: bool = True
    test_rate_limiting: bool = True
    
    # Performance tuning
    max_pages_to_crawl: int = 100
    max_payloads_per_param: int = 50
    rate_limit_delay: float = 0.1  # Seconds between requests


class WebVulnerabilityScanner:
    """Main orchestrator for web vulnerability scanning"""
    
    def __init__(self, config: WebScanConfiguration):
        """
        Initialize scanner with configuration.
        
        Args:
            config: WebScanConfiguration object
        """
        self.config = config
        self.scope_enforcer = ScopeEnforcer(
            override_robots_txt=config.override_robots_txt
        )
        self.aggregator = VulnerabilityAggregator()
        self.scan_stats = {
            "start_time": None,
            "end_time": None,
            "phases_completed": [],
            "endpoints_tested": 0,
            "payloads_sent": 0,
            "findings": 0,
        }
        self.session_cookies = {}
        self.discovered_endpoints = []
    
    def run_scan(self) -> Dict[str, Any]:
        """
        Run comprehensive web vulnerability scan.
        
        Returns final aggregated report with all findings
        """
        logger.info(f"Starting web vulnerability scan on {self.config.target_url}")
        self.scan_stats["start_time"] = time.time()
        self.aggregator.scan_metadata["target_url"] = self.config.target_url
        self.aggregator.scan_metadata["start_time"] = time.time()
        
        try:
            # Phase 1: Reconnaissance & Surface Mapping
            self._run_surface_mapping()
            
            # Phase 2: Injection Testing
            if self.config.test_injection:
                self._run_injection_tests()
            
            # Phase 3: XSS Testing
            if self.config.test_xss:
                self._run_xss_tests()
            
            # Phase 4: Authentication Testing
            if self.config.test_auth:
                self._run_authentication_tests()
            
            # Phase 5: Access Control Testing
            if self.config.test_idor:
                self._run_access_control_tests()
            
            # Phase 6: CSRF/SSRF Testing
            if self.config.test_csrf_ssrf:
                self._run_csrf_ssrf_tests()
            
            # Phase 7: File Upload Testing
            if self.config.test_file_upload:
                self._run_file_upload_tests()
            
            # Phase 8: Misconfiguration Testing
            if self.config.test_misconfiguration:
                self._run_misconfiguration_tests()
            
            # Phase 9: Sensitive Data Testing
            if self.config.test_sensitive_data:
                self._run_sensitive_data_tests()
            
            # Phase 10: Business Logic Testing
            if self.config.test_business_logic:
                self._run_business_logic_tests()
            
            # Phase 11: Rate Limiting Testing
            if self.config.test_rate_limiting:
                self._run_rate_limiting_tests()
            
            # Phase 12: Final aggregation & reporting
            self._generate_final_report()
        
        except Exception as e:
            logger.error(f"Scan failed: {e}", exc_info=True)
        
        finally:
            self.scan_stats["end_time"] = time.time()
            self.aggregator.scan_metadata["end_time"] = time.time()
            self.aggregator.scan_metadata["duration"] = (
                self.scan_stats["end_time"] - self.scan_stats["start_time"]
            )
            logger.info(f"Scan completed in {self.aggregator.scan_metadata['duration']:.1f}s")
        
        return self.aggregator.aggregate_results()
    
    def _run_surface_mapping(self):
        """Phase 1: Discover endpoints, parameters, and application structure"""
        logger.info("Phase 1: Surface Mapping & Endpoint Discovery")
        
        try:
            mapper = SurfaceMapper(timeout=self.config.request_timeout, 
                                  verify_ssl=self.config.verify_ssl)
            
            results = mapper.crawl_and_map(
                base_url=self.config.target_url,
                scope_enforcer=self.scope_enforcer,
                max_pages=self.config.max_pages_to_crawl
            )
            
            self.discovered_endpoints = results.get("endpoints", [])
            self.scan_stats["endpoints_tested"] = len(self.discovered_endpoints)
            
            logger.info(f"Discovered {self.scan_stats['endpoints_tested']} endpoints")
            self.scan_stats["phases_completed"].append("surface_mapping")
        
        except Exception as e:
            logger.warning(f"Surface mapping failed: {e}")
    
    def _run_injection_tests(self):
        """Phase 2: SQL Injection, Command Injection, NoSQL, LDAP"""
        logger.info("Phase 2: Injection Testing")
        
        try:
            tester = InjectionTester(timeout=self.config.request_timeout,
                                    verify_ssl=self.config.verify_ssl)
            
            findings = []
            
            for endpoint in self.discovered_endpoints[:10]:  # Test first 10
                # Check scope
                if not self.scope_enforcer.is_url_in_scope(endpoint.get("url", "")):
                    continue
                
                endpoint_findings = tester.test_endpoint_injection(
                    url=endpoint.get("url", ""),
                    parameters=endpoint.get("parameters", {}),
                    depth=self.config.depth
                )
                findings.extend(endpoint_findings)
                self.scan_stats["payloads_sent"] += len(endpoint_findings) * 3
            
            if findings:
                self.aggregator.collector.add_findings_batch(findings, "Injection Testing")
                logger.info(f"Found {len(findings)} injection vulnerabilities")
            
            self.scan_stats["phases_completed"].append("injection")
        
        except Exception as e:
            logger.warning(f"Injection testing failed: {e}")
    
    def _run_xss_tests(self):
        """Phase 3: Reflected, Stored, and DOM-based XSS"""
        logger.info("Phase 3: XSS Testing")
        
        try:
            tester = XSSTester(timeout=self.config.request_timeout,
                              verify_ssl=self.config.verify_ssl)
            
            findings = []
            
            for endpoint in self.discovered_endpoints[:10]:
                if not self.scope_enforcer.is_url_in_scope(endpoint.get("url", "")):
                    continue
                
                endpoint_findings = tester.test_endpoint_xss(
                    url=endpoint.get("url", ""),
                    method=endpoint.get("method", "GET"),
                    parameters=endpoint.get("parameters", {}),
                    depth=self.config.depth
                )
                findings.extend(endpoint_findings)
            
            if findings:
                self.aggregator.collector.add_findings_batch(findings, "XSS Testing")
                logger.info(f"Found {len(findings)} XSS vulnerabilities")
            
            self.scan_stats["phases_completed"].append("xss")
        
        except Exception as e:
            logger.warning(f"XSS testing failed: {e}")
    
    def _run_authentication_tests(self):
        """Phase 4: Authentication & Session Analysis"""
        logger.info("Phase 4: Authentication Testing")
        
        try:
            tester = AuthenticationTester(timeout=self.config.request_timeout,
                                         verify_ssl=self.config.verify_ssl)
            
            results = tester.test_target_authentication(self.config.target_url)
            
            # Flatten results for aggregation
            findings = []
            
            if results.get("weak_credentials"):
                findings.extend(results["weak_credentials"])
            if results.get("session_issues"):
                findings.extend(results["session_issues"])
            if results.get("jwt_issues"):
                findings.extend(results["jwt_issues"])
            
            if findings:
                self.aggregator.collector.add_findings_batch(findings, "Authentication Testing")
                logger.info(f"Found {len(findings)} authentication issues")
            
            self.scan_stats["phases_completed"].append("authentication")
        
        except Exception as e:
            logger.warning(f"Authentication testing failed: {e}")
    
    def _run_access_control_tests(self):
        """Phase 5: IDOR & Privilege Escalation"""
        logger.info("Phase 5: Access Control Testing")
        
        try:
            tester = IDORTester(timeout=self.config.request_timeout,
                               verify_ssl=self.config.verify_ssl)
            
            findings = []
            
            for endpoint in self.discovered_endpoints[:5]:
                if not self.scope_enforcer.is_url_in_scope(endpoint.get("url", "")):
                    continue
                
                endpoint_findings = tester.test_endpoint_idor(
                    url=endpoint.get("url", ""),
                    method=endpoint.get("method", "GET"),
                    baseline_params=endpoint.get("parameters", {})
                )
                findings.extend(endpoint_findings)
            
            if findings:
                self.aggregator.collector.add_findings_batch(findings, "Access Control Testing")
                logger.info(f"Found {len(findings)} access control issues")
            
            self.scan_stats["phases_completed"].append("access_control")
        
        except Exception as e:
            logger.warning(f"Access control testing failed: {e}")
    
    def _run_csrf_ssrf_tests(self):
        """Phase 6: CSRF & SSRF Testing"""
        logger.info("Phase 6: CSRF & SSRF Testing")
        
        try:
            csrf_tester = CSRFTester(timeout=self.config.request_timeout,
                                    verify_ssl=self.config.verify_ssl)
            ssrf_tester = SSRFTester(timeout=self.config.request_timeout,
                                    verify_ssl=self.config.verify_ssl)
            
            findings = []
            
            # CSRF testing
            csrf_results = csrf_tester.test_csrf_protection(self.config.target_url)
            if csrf_results.get("csrf_token_missing"):
                findings.extend(csrf_results["csrf_token_missing"])
            if csrf_results.get("weak_token_protection"):
                findings.extend(csrf_results["weak_token_protection"])
            
            # SSRF testing
            for endpoint in self.discovered_endpoints[:3]:
                ssrf_findings = ssrf_tester.test_ssrf(endpoint.get("url", ""))
                findings.extend(ssrf_findings)
            
            if findings:
                self.aggregator.collector.add_findings_batch(findings, "CSRF & SSRF Testing")
                logger.info(f"Found {len(findings)} CSRF/SSRF issues")
            
            self.scan_stats["phases_completed"].append("csrf_ssrf")
        
        except Exception as e:
            logger.warning(f"CSRF/SSRF testing failed: {e}")
    
    def _run_file_upload_tests(self):
        """Phase 7: File Upload & Path Traversal"""
        logger.info("Phase 7: File Upload Testing")
        
        try:
            handler = FileHandlingTester(timeout=self.config.request_timeout,
                                        verify_ssl=self.config.verify_ssl)
            
            findings = []
            
            # Test file upload endpoints (from surface mapping)
            for endpoint in self.discovered_endpoints[:5]:
                if "/upload" in endpoint.get("url", ""):
                    file_findings = handler.test_file_upload(
                        endpoint.get("url", ""),
                        "file"  # Default file field name
                    )
                    findings.extend(file_findings)
                    
                    # Also test path traversal
                    pt_findings = handler.test_path_traversal(endpoint.get("url", ""))
                    findings.extend(pt_findings)
            
            if findings:
                self.aggregator.collector.add_findings_batch(findings, "File Handling Testing")
                logger.info(f"Found {len(findings)} file handling issues")
            
            self.scan_stats["phases_completed"].append("file_upload")
        
        except Exception as e:
            logger.warning(f"File upload testing failed: {e}")
    
    def _run_misconfiguration_tests(self):
        """Phase 8: Security Misconfiguration"""
        logger.info("Phase 8: Misconfiguration Testing")
        
        try:
            tester = SecurityMisconfigurationTester(timeout=self.config.request_timeout,
                                                   verify_ssl=self.config.verify_ssl)
            
            findings = []
            
            # Test security headers
            header_findings = tester.test_security_headers(self.config.target_url)
            findings.extend(header_findings)
            
            # Test directory listing
            dir_findings = tester.test_directory_listing(self.config.target_url)
            findings.extend(dir_findings)
            
            # Test debug endpoints
            debug_findings = tester.test_debug_endpoints(self.config.target_url)
            findings.extend(debug_findings)
            
            if findings:
                self.aggregator.collector.add_findings_batch(findings, "Misconfiguration Testing")
                logger.info(f"Found {len(findings)} misconfiguration issues")
            
            self.scan_stats["phases_completed"].append("misconfiguration")
        
        except Exception as e:
            logger.warning(f"Misconfiguration testing failed: {e}")
    
    def _run_sensitive_data_tests(self):
        """Phase 9: Sensitive Data Exposure"""
        logger.info("Phase 9: Sensitive Data Testing")
        
        try:
            tester = SensitiveDataTester(timeout=self.config.request_timeout,
                                        verify_ssl=self.config.verify_ssl)
            
            findings = []
            
            for endpoint in self.discovered_endpoints[:15]:
                if not self.scope_enforcer.is_url_in_scope(endpoint.get("url", "")):
                    continue
                
                endpoint_findings_dict = tester.test_sensitive_exposure(
                    endpoint.get("url", "")
                )
                
                # Flatten the results
                for key, value in endpoint_findings_dict.items():
                    if isinstance(value, list):
                        findings.extend(value)
            
            if findings:
                self.aggregator.collector.add_findings_batch(findings, "Sensitive Data Testing")
                logger.info(f"Found {len(findings)} sensitive data issues")
            
            self.scan_stats["phases_completed"].append("sensitive_data")
        
        except Exception as e:
            logger.warning(f"Sensitive data testing failed: {e}")
    
    def _run_business_logic_tests(self):
        """Phase 10: Business Logic Vulnerabilities"""
        logger.info("Phase 10: Business Logic Testing")
        
        try:
            tester = BusinessLogicTester(timeout=self.config.request_timeout,
                                        verify_ssl=self.config.verify_ssl)
            
            results = tester.test_application_logic(self.config.target_url)
            
            findings = []
            
            # Extract findings from results
            for key, value in results.items():
                if isinstance(value, list):
                    findings.extend(value)
            
            if findings:
                self.aggregator.collector.add_findings_batch(findings, "Business Logic Testing")
                logger.info(f"Found {len(findings)} business logic issues")
            
            self.scan_stats["phases_completed"].append("business_logic")
        
        except Exception as e:
            logger.warning(f"Business logic testing failed: {e}")
    
    def _run_rate_limiting_tests(self):
        """Phase 11: Rate Limiting & Abuse Testing"""
        logger.info("Phase 11: Rate Limiting Testing")
        
        try:
            tester = RateLimitTester(timeout=self.config.request_timeout,
                                    verify_ssl=self.config.verify_ssl)
            
            findings = []
            
            # Test main endpoint for rate limiting
            api_results = tester.comprehensive_abuse_test(
                login_endpoint=self.config.target_url + "/login",
                api_endpoint=self.config.target_url,
                otp_endpoint=None
            )
            
            # Extract findings
            if api_results.get("login_brute_force"):
                findings.extend(api_results["login_brute_force"])
            if api_results.get("otp_brute_force"):
                findings.extend(api_results["otp_brute_force"])
            
            if findings:
                self.aggregator.collector.add_findings_batch(findings, "Rate Limiting Testing")
                logger.info(f"Found {len(findings)} rate limiting issues")
            
            self.scan_stats["phases_completed"].append("rate_limiting")
        
        except Exception as e:
            logger.warning(f"Rate limiting testing failed: {e}")
    
    def _generate_final_report(self):
        """Phase 12: Final aggregation & reporting"""
        logger.info("Phase 12: Generating Final Report")
        
        self.scan_stats["finding"] = len(self.aggregator.collector.findings)
        stats = self.aggregator.collector.get_statistics()
        
        logger.info(f"Scan Summary:")
        logger.info(f"  Total Findings: {stats['total_findings']}")
        logger.info(f"  High Confidence: {stats['high_confidence_count']}")
        logger.info(f"  Phases Completed: {len(self.scan_stats['phases_completed'])}/11")
        
        logger.info(f"Findings by Severity:")
        for severity, count in stats['by_severity'].items():
            logger.info(f"  {severity}: {count}")
        
        logger.info(f"Findings by Module:")
        for module, count in stats['by_module'].items():
            logger.info(f"  {module}: {count}")
