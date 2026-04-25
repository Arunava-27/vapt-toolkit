"""
Evidence Collection & Deduplication Module

Aggregates findings from all vulnerability testing modules,
deduplicates results, and exports evidence in multiple formats.
"""

import json
import hashlib
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
from datetime import datetime
import logging

from .confidence_scorer import ConfidenceScorer, ConfidenceLevel

logger = logging.getLogger(__name__)

# Lazy-load classifier to avoid circular imports
_classifier = None

def get_classifier():
    """Lazy-load classifier to avoid circular imports."""
    global _classifier
    if _classifier is None:
        try:
            from scanner.web.vulnerability_classifier import VulnerabilityClassifier
            _classifier = VulnerabilityClassifier
        except ImportError:
            _classifier = None
    return _classifier


class FindingSeverity(Enum):
    """Severity levels for findings"""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFO = "Info"


class FindingType(Enum):
    """Types of vulnerabilities"""
    SQL_INJECTION = "SQL Injection"
    XSS = "Cross-Site Scripting"
    CSRF = "Cross-Site Request Forgery"
    SSRF = "Server-Side Request Forgery"
    AUTHENTICATION = "Authentication Weakness"
    AUTHORIZATION = "Authorization Weakness"
    IDOR = "Insecure Direct Object Reference"
    SENSITIVE_DATA = "Sensitive Data Exposure"
    WEAK_CRYPTO = "Weak Cryptography"
    INJECTION = "Injection"
    FILE_UPLOAD = "File Upload"
    PATH_TRAVERSAL = "Path Traversal"
    MISCONFIGURATION = "Security Misconfiguration"
    BUSINESS_LOGIC = "Business Logic"
    RATE_LIMITING = "Rate Limiting"
    OTHER = "Other"


@dataclass
class WebVulnerabilityFinding:
    """Standardized vulnerability finding"""
    
    # Core identification
    type: str  # Vulnerability type
    severity: str  # Critical, High, Medium, Low
    finding_id: str = field(default="")  # Unique ID (generated)
    
    # Technical details
    url: str = ""
    method: str = "GET"
    parameter: str = ""
    endpoint: str = ""
    
    # Evidence
    payload: str = ""
    response_snippet: str = ""
    request_headers: Dict[str, str] = field(default_factory=dict)
    response_headers: Dict[str, str] = field(default_factory=dict)
    evidence: str = ""  # Description of how vulnerability was found
    
    # Confidence scoring
    confidence_score: int = 50  # 0-100
    confidence_level: str = "Low"  # High, Medium, Low, Suspicious
    detection_methods: List[str] = field(default_factory=list)  # Methods used
    verification_steps: List[str] = field(default_factory=list)  # Manual verification steps
    false_positive_risk: float = 0.5  # 0-1, where 1 = likely FP
    
    # Metadata
    module: str = ""  # Which module detected this
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    reproducible: bool = True
    
    # Fingerprinting
    fingerprint: str = field(default="")  # Hash for deduplication
    related_findings: List[str] = field(default_factory=list)
    
    # Compliance & Standards
    owasp_category: str = ""  # OWASP Top 10 2021 category
    cwe_id: str = ""  # CWE (Common Weakness Enumeration) ID
    cvss_score: float = 0.0  # CVSS v3.1 score (0-10)
    remediation_tips: List[str] = field(default_factory=list)  # How to fix this vulnerability
    compliance_impact: List[str] = field(default_factory=list)  # Affected standards (HIPAA, PCI-DSS, etc)
    
    def __post_init__(self):
        """Generate ID and fingerprint after initialization"""
        if not self.finding_id:
            self.finding_id = self._generate_id()
        if not self.fingerprint:
            self.fingerprint = self._generate_fingerprint()
        
        # Auto-populate compliance fields if classifier is available
        if not self.owasp_category or not self.cwe_id:
            classifier = get_classifier()
            if classifier:
                try:
                    classification = classifier.classify(self.type)
                    if not self.owasp_category:
                        self.owasp_category = classification.get("owasp_category", "")
                    if not self.cwe_id:
                        self.cwe_id = classification.get("cwe_id", "")
                    if not self.remediation_tips:
                        self.remediation_tips = classifier.get_remediation_tips(self.type)
                    if not self.compliance_impact:
                        self.compliance_impact = classifier.get_compliance_impact(self.type)
                    if self.cvss_score == 0.0:
                        self.cvss_score = classifier._estimate_score_from_severity(self.severity)
                except Exception as e:
                    logger.debug(f"Failed to auto-populate compliance fields: {e}")
    
    def _generate_id(self) -> str:
        """Generate unique finding ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        hash_input = f"{self.type}_{self.url}_{self.parameter}_{timestamp}"
        short_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8]
        return f"VUL-{timestamp}-{short_hash}"
    
    def _generate_fingerprint(self) -> str:
        """Generate fingerprint for deduplication"""
        # Fingerprint based on: type + url + method + parameter + endpoint
        fp_input = f"{self.type}_{self.endpoint or self.url}_{self.method}_{self.parameter}".lower()
        return hashlib.sha256(fp_input.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class EvidenceCollector:
    """Collects and manages evidence from vulnerability tests"""
    
    def __init__(self):
        self.findings: List[WebVulnerabilityFinding] = []
        self.finding_index: Dict[str, WebVulnerabilityFinding] = {}
        self.module_stats: Dict[str, int] = {}
    
    def add_finding(self, finding_data: Dict[str, Any]) -> Optional[WebVulnerabilityFinding]:
        """
        Add a finding from any module.
        
        Args:
            finding_data: Dictionary containing finding information
            
        Returns:
            WebVulnerabilityFinding object or None if filtered
        """
        # Convert module output to standardized format
        finding = self._normalize_finding(finding_data)
        
        if finding is None:
            return None
        
        # Check for duplicates
        if self._is_duplicate(finding):
            logger.debug(f"Duplicate finding filtered: {finding.type}")
            return None
        
        # Add to collections
        self.findings.append(finding)
        self.finding_index[finding.fingerprint] = finding
        
        # Update module stats
        self.module_stats[finding.module] = self.module_stats.get(finding.module, 0) + 1
        
        logger.info(f"Finding collected: {finding.type} @ {finding.url}")
        return finding
    
    def add_findings_batch(self, findings_list: List[Dict[str, Any]], module: str) -> int:
        """
        Add multiple findings from a module at once.
        
        Args:
            findings_list: List of finding dictionaries
            module: Module name
            
        Returns:
            Number of findings actually added
        """
        added = 0
        
        for finding_data in findings_list:
            finding_data["module"] = module
            finding = self.add_finding(finding_data)
            if finding:
                added += 1
        
        return added
    
    def _normalize_finding(self, finding_data: Dict[str, Any]) -> Optional[WebVulnerabilityFinding]:
        """
        Convert module-specific finding format to standardized format.
        
        Each module may format findings differently.
        """
        try:
            # Extract common fields
            finding_type = finding_data.get("type", "Other")
            severity = finding_data.get("severity", "Medium")
            
            # Module-specific mapping
            module = finding_data.get("module", "unknown")
            
            # Create standardized finding
            finding = WebVulnerabilityFinding(
                type=finding_type,
                severity=severity,
                url=finding_data.get("url", ""),
                method=finding_data.get("method", "GET"),
                parameter=finding_data.get("parameter", ""),
                endpoint=finding_data.get("endpoint", ""),
                payload=finding_data.get("payload", ""),
                response_snippet=finding_data.get("response_snippet", "")[:200],
                evidence=finding_data.get("evidence", ""),
                module=module,
                reproducible=finding_data.get("reproducible", True),
                confidence_score=finding_data.get("confidence_score", 50),
                confidence_level=finding_data.get("confidence_level", "Low"),
                detection_methods=finding_data.get("detection_methods", []),
                verification_steps=finding_data.get("verification_steps", []),
                false_positive_risk=finding_data.get("false_positive_risk", 0.5),
            )
            
            return finding
        
        except Exception as e:
            logger.warning(f"Failed to normalize finding: {e}")
            return None
    
    def _is_duplicate(self, finding: WebVulnerabilityFinding) -> bool:
        """Check if finding is a duplicate based on fingerprint"""
        return finding.fingerprint in self.finding_index
    
    def get_by_severity(self, severity: str) -> List[WebVulnerabilityFinding]:
        """Get findings by severity level"""
        return [f for f in self.findings if f.severity == severity]
    
    def get_by_type(self, finding_type: str) -> List[WebVulnerabilityFinding]:
        """Get findings by type"""
        return [f for f in self.findings if f.type == finding_type]
    
    def get_by_module(self, module: str) -> List[WebVulnerabilityFinding]:
        """Get findings by module"""
        return [f for f in self.findings if f.module == module]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Generate statistics about collected findings"""
        stats = {
            "total_findings": len(self.findings),
            "by_severity": {},
            "by_type": {},
            "by_module": self.module_stats,
            "by_confidence_level": {
                "High": len(self.get_by_confidence_level("High")),
                "Medium": len(self.get_by_confidence_level("Medium")),
                "Low": len(self.get_by_confidence_level("Low")),
                "Suspicious": len(self.get_by_confidence_level("Suspicious")),
            },
            "reproducible_count": sum(1 for f in self.findings if f.reproducible),
            "high_confidence_count": sum(1 for f in self.findings if f.severity in ["Critical", "High"]),
            "average_confidence_score": (
                int(sum(f.confidence_score for f in self.findings) / len(self.findings))
                if self.findings else 0
            ),
        }
        
        # Count by severity
        for severity in ["Critical", "High", "Medium", "Low", "Info"]:
            count = len(self.get_by_severity(severity))
            if count > 0:
                stats["by_severity"][severity] = count
        
        # Count by type
        for finding in self.findings:
            stats["by_type"][finding.type] = stats["by_type"].get(finding.type, 0) + 1
        
        return stats
    
    def deduplicate(self) -> int:
        """
        Remove duplicate findings and return count of removed duplicates.
        This is automatically done on add_finding, but can be called to deduplicate
        manually added findings that weren't processed through add_finding.
        """
        original_count = len(self.findings)
        unique_fingerprints = set()
        unique_findings = []
        
        for finding in self.findings:
            if finding.fingerprint not in unique_fingerprints:
                unique_findings.append(finding)
                unique_fingerprints.add(finding.fingerprint)
            else:
                # Link to original finding
                for existing_finding in unique_findings:
                    if existing_finding.fingerprint == finding.fingerprint:
                        existing_finding.related_findings.append(finding.finding_id)
                        break
        
        self.findings = unique_findings
        self.finding_index = {f.fingerprint: f for f in unique_findings}
        
        removed = original_count - len(self.findings)
        if removed > 0:
            logger.info(f"Deduplicated {removed} duplicate findings")
        
        return removed
    
    def filter_by_confidence(self, min_confidence: int = 50) -> List[WebVulnerabilityFinding]:
        """
        Filter findings by minimum confidence threshold.
        
        Args:
            min_confidence: Minimum confidence score (0-100, default 50)
            
        Returns:
            List of findings meeting confidence threshold
        """
        return [f for f in self.findings if f.confidence_score >= min_confidence]
    
    def get_by_confidence_level(self, level: str) -> List[WebVulnerabilityFinding]:
        """
        Get findings by confidence level (High, Medium, Low, Suspicious).
        
        Args:
            level: Confidence level string
            
        Returns:
            List of findings with specified confidence level
        """
        return [f for f in self.findings if f.confidence_level == level]
    
    def get_suspicious_findings(self) -> List[WebVulnerabilityFinding]:
        """Get findings marked as Suspicious (confidence < 70%)."""
        return self.get_by_confidence_level("Suspicious")
    
    def sort_by_confidence(self, descending: bool = True) -> List[WebVulnerabilityFinding]:
        """
        Sort findings by confidence score.
        
        Args:
            descending: If True, sort high to low; if False, low to high
            
        Returns:
            Sorted list of findings
        """
        return sorted(self.findings, key=lambda f: f.confidence_score, reverse=descending)
    
    def sort_by_severity_and_confidence(self) -> List[WebVulnerabilityFinding]:
        """
        Sort findings by severity first, then by confidence score.
        
        Returns:
            Sorted list of findings
        """
        severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Info": 4}
        return sorted(
            self.findings,
            key=lambda f: (
                severity_order.get(f.severity, 5),
                -f.confidence_score  # Higher confidence first
            )
        )
    
    def export_json(self) -> str:
        """Export findings as JSON"""
        export_data = {
            "metadata": {
                "export_time": datetime.utcnow().isoformat(),
                "total_findings": len(self.findings),
                "statistics": self.get_statistics(),
            },
            "findings": [f.to_dict() for f in self.findings],
        }
        
        return json.dumps(export_data, indent=2, default=str)
    
    def export_csv(self) -> str:
        """Export findings as CSV"""
        if not self.findings:
            return ""
        
        import csv
        import io
        
        output = io.StringIO()
        
        # Get all field names from first finding
        fieldnames = list(self.findings[0].to_dict().keys())
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for finding in self.findings:
            writer.writerow(finding.to_dict())
        
        return output.getvalue()
    
    def export_report(self) -> str:
        """Export findings as human-readable report"""
        report = []
        report.append("=" * 80)
        report.append("WEB VULNERABILITY SCAN REPORT")
        report.append("=" * 80)
        report.append(f"\nGenerated: {datetime.utcnow().isoformat()}")
        
        stats = self.get_statistics()
        report.append(f"\nTotal Findings: {stats['total_findings']}")
        report.append(f"High Confidence: {stats['high_confidence_count']}")
        report.append(f"Reproducible: {stats['reproducible_count']}")
        
        # By severity
        report.append("\n" + "-" * 80)
        report.append("FINDINGS BY SEVERITY")
        report.append("-" * 80)
        
        for severity in ["Critical", "High", "Medium", "Low"]:
            findings = self.get_by_severity(severity)
            if findings:
                report.append(f"\n{severity.upper()} ({len(findings)})")
                for finding in findings:
                    report.append(f"  [{finding.type}] {finding.url}")
                    if finding.parameter:
                        report.append(f"    Parameter: {finding.parameter}")
                    report.append(f"    Evidence: {finding.evidence[:100]}")
        
        # By module
        report.append("\n" + "-" * 80)
        report.append("FINDINGS BY MODULE")
        report.append("-" * 80)
        
        for module, count in sorted(stats['by_module'].items()):
            report.append(f"\n{module}: {count} findings")
        
        # Top vulnerabilities
        report.append("\n" + "-" * 80)
        report.append("TOP VULNERABILITY TYPES")
        report.append("-" * 80)
        
        sorted_types = sorted(stats['by_type'].items(), key=lambda x: x[1], reverse=True)
        for vuln_type, count in sorted_types[:10]:
            report.append(f"  {vuln_type}: {count}")
        
        report.append("\n" + "=" * 80)
        
        return "\n".join(report)


class FindingCorrelation:
    """Correlates related findings across modules"""
    
    @staticmethod
    def find_related_findings(finding: WebVulnerabilityFinding,
                            all_findings: List[WebVulnerabilityFinding]) -> List[str]:
        """
        Find other findings that are related to this one.
        
        Criteria:
        - Same endpoint
        - Same parameter
        - Same type
        - Similar evidence
        """
        related = []
        
        for other in all_findings:
            if other.finding_id == finding.finding_id:
                continue
            
            # Same endpoint + same parameter
            if (finding.endpoint == other.endpoint and 
                finding.parameter == other.parameter):
                related.append(other.finding_id)
                continue
            
            # Same type at same URL (different params)
            if (finding.type == other.type and 
                finding.url == other.url):
                related.append(other.finding_id)
                continue
        
        return related
    
    @staticmethod
    def rank_findings(findings: List[WebVulnerabilityFinding]) -> List[Tuple[WebVulnerabilityFinding, float]]:
        """
        Rank findings by risk score and actionability.
        
        Scoring factors:
        - Severity (Critical=4, High=3, Medium=2, Low=1)
        - Reproducibility (2x if reproducible)
        - False positive risk (divide by 2 if high risk)
        - Number of related findings (multiply by 1.2x per related)
        """
        severity_scores = {
            "Critical": 4.0,
            "High": 3.0,
            "Medium": 2.0,
            "Low": 1.0,
            "Info": 0.5,
        }
        
        ranked = []
        
        for finding in findings:
            # Base score from severity
            score = severity_scores.get(finding.severity, 1.0)
            
            # Reproducibility bonus
            if finding.reproducible:
                score *= 2.0
            
            # False positive risk penalty
            if finding.false_positive_risk == "High":
                score *= 0.5
            elif finding.false_positive_risk == "Medium":
                score *= 0.8
            
            # Related findings bonus (indicates pattern)
            if finding.related_findings:
                score *= (1.0 + len(finding.related_findings) * 0.1)
            
            ranked.append((finding, score))
        
        # Sort by score descending
        ranked.sort(key=lambda x: x[1], reverse=True)
        
        return ranked


class VulnerabilityAggregator:
    """Aggregates results from all modules into a cohesive report"""
    
    def __init__(self):
        self.collector = EvidenceCollector()
        self.scan_metadata = {
            "start_time": None,
            "end_time": None,
            "duration": None,
            "target_url": None,
            "scan_type": None,
        }
    
    def aggregate_results(self, 
                         surface_map_results: Dict[str, Any] = None,
                         injection_results: List[Dict[str, Any]] = None,
                         xss_results: List[Dict[str, Any]] = None,
                         auth_results: Dict[str, Any] = None,
                         idor_results: List[Dict[str, Any]] = None,
                         csrf_results: Dict[str, Any] = None,
                         ssrf_results: List[Dict[str, Any]] = None,
                         file_results: List[Dict[str, Any]] = None,
                         misconfig_results: List[Dict[str, Any]] = None,
                         sensitive_results: Dict[str, Any] = None,
                         business_logic_results: Dict[str, Any] = None,
                         ratelimit_results: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Aggregate results from all modules.
        
        Returns consolidated report
        """
        results_by_module = {
            "surface_mapping": (surface_map_results, "Surface Mapping"),
            "injection": (injection_results, "Injection Testing"),
            "xss": (xss_results, "XSS Testing"),
            "authentication": (auth_results, "Authentication"),
            "access_control": (idor_results, "Access Control"),
            "csrf": (csrf_results, "CSRF Testing"),
            "ssrf": (ssrf_results, "SSRF Testing"),
            "file_handling": (file_results, "File Handling"),
            "misconfiguration": (misconfig_results, "Misconfiguration"),
            "sensitive_data": (sensitive_results, "Sensitive Data"),
            "business_logic": (business_logic_results, "Business Logic"),
            "rate_limiting": (ratelimit_results, "Rate Limiting"),
        }
        
        # Process each module's results
        for module_key, (results, module_name) in results_by_module.items():
            if results is None:
                continue
            
            # Handle different result formats
            findings_list = []
            
            if isinstance(results, dict):
                # Extract findings from nested structure
                for key, value in results.items():
                    if isinstance(value, list):
                        findings_list.extend(value)
                    elif isinstance(value, dict) and "type" in value:
                        findings_list.append(value)
            elif isinstance(results, list):
                findings_list = results
            
            # Add findings from this module
            added_count = self.collector.add_findings_batch(findings_list, module_name)
            logger.info(f"Added {added_count} findings from {module_name}")
        
        # Deduplicate and correlate
        self.collector.deduplicate()
        
        # Rank findings
        ranked_findings = FindingCorrelation.rank_findings(self.collector.findings)
        
        return {
            "metadata": self.scan_metadata,
            "statistics": self.collector.get_statistics(),
            "findings": [f.to_dict() for f, score in ranked_findings],
            "findings_ranked": [(f.to_dict(), score) for f, score in ranked_findings],
            "total_findings": len(self.collector.findings),
            "high_severity_count": len(self.collector.get_by_severity("Critical")) + 
                                  len(self.collector.get_by_severity("High")),
        }
    
    def export_all_formats(self, base_path: str) -> Dict[str, str]:
        """
        Export findings in multiple formats.
        
        Returns dict mapping format name to file path
        """
        exports = {}
        
        try:
            # JSON export
            json_path = f"{base_path}_findings.json"
            with open(json_path, 'w') as f:
                f.write(self.collector.export_json())
            exports["json"] = json_path
            
            # CSV export
            csv_path = f"{base_path}_findings.csv"
            with open(csv_path, 'w') as f:
                f.write(self.collector.export_csv())
            exports["csv"] = csv_path
            
            # Report export
            report_path = f"{base_path}_report.txt"
            with open(report_path, 'w') as f:
                f.write(self.collector.export_report())
            exports["report"] = report_path
            
            logger.info(f"Exported findings to: {', '.join(exports.values())}")
        
        except Exception as e:
            logger.error(f"Export failed: {e}")
        
        return exports
