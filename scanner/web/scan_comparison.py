"""
Scan Comparison Module

Compares two vulnerability scans to identify:
- New findings (vulnerabilities introduced between scans)
- Fixed findings (vulnerabilities that were patched)
- Unchanged findings (persistent vulnerabilities)
- Regressions (vulnerabilities that reappeared)
- Risk delta (change in overall risk score)

Integrates with confidence scoring and evidence collection for detailed comparison.
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
import hashlib
import logging

logger = logging.getLogger(__name__)


class ComparisonStatus(Enum):
    """Status of a finding in comparison."""
    NEW = "new"
    FIXED = "fixed"
    UNCHANGED = "unchanged"
    REGRESSION = "regression"
    MODIFIED = "modified"


@dataclass
class ComparisonFinding:
    """A single finding with its comparison status and details."""
    
    # Finding identifiers
    finding_id: str
    finding_type: str
    severity: str
    status: ComparisonStatus
    
    # Location
    url: str = ""
    endpoint: str = ""
    parameter: str = ""
    method: str = "GET"
    
    # Evidence and scoring
    payload: str = ""
    confidence_score: float = 0.0
    evidence: str = ""
    
    # Comparison metadata
    appeared_in_scan: Optional[str] = None  # Which scan(s)
    last_seen_scan: Optional[str] = None
    detection_count: int = 1
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        d = asdict(self)
        d["status"] = self.status.value if isinstance(self.status, ComparisonStatus) else self.status
        return d


@dataclass
class ScanComparisonResult:
    """Result of comparing two scans."""
    
    scan_1_id: str
    scan_2_id: str
    comparison_timestamp: str
    
    # Finding counts by status
    new_findings: List[ComparisonFinding] = field(default_factory=list)
    fixed_findings: List[ComparisonFinding] = field(default_factory=list)
    unchanged_findings: List[ComparisonFinding] = field(default_factory=list)
    regressions: List[ComparisonFinding] = field(default_factory=list)
    modified_findings: List[ComparisonFinding] = field(default_factory=list)
    
    # Risk metrics
    scan_1_risk_score: float = 0.0
    scan_2_risk_score: float = 0.0
    risk_delta: float = 0.0
    risk_trend: str = "stable"  # improving, degrading, stable
    
    # Summary
    total_vulnerabilities_1: int = 0
    total_vulnerabilities_2: int = 0
    vulnerability_delta: int = 0
    
    # Severity distribution
    severity_distribution_1: Dict[str, int] = field(default_factory=dict)
    severity_distribution_2: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "scan_1_id": self.scan_1_id,
            "scan_2_id": self.scan_2_id,
            "comparison_timestamp": self.comparison_timestamp,
            "new_findings": [f.to_dict() for f in self.new_findings],
            "fixed_findings": [f.to_dict() for f in self.fixed_findings],
            "unchanged_findings": [f.to_dict() for f in self.unchanged_findings],
            "regressions": [f.to_dict() for f in self.regressions],
            "modified_findings": [f.to_dict() for f in self.modified_findings],
            "scan_1_risk_score": self.scan_1_risk_score,
            "scan_2_risk_score": self.scan_2_risk_score,
            "risk_delta": self.risk_delta,
            "risk_trend": self.risk_trend,
            "total_vulnerabilities_1": self.total_vulnerabilities_1,
            "total_vulnerabilities_2": self.total_vulnerabilities_2,
            "vulnerability_delta": self.vulnerability_delta,
            "severity_distribution_1": self.severity_distribution_1,
            "severity_distribution_2": self.severity_distribution_2,
        }


class ScanComparator:
    """Compares two vulnerability scans and generates detailed comparison results."""
    
    SEVERITY_WEIGHTS = {
        "Critical": 100,
        "High": 50,
        "Medium": 25,
        "Low": 5,
        "Info": 1,
    }
    
    def __init__(self):
        """Initialize the comparator."""
        self.severity_levels = ["Critical", "High", "Medium", "Low", "Info"]
    
    def compare_scans(
        self,
        scan_1: Dict[str, Any],
        scan_2: Dict[str, Any],
        filters: Optional[Dict[str, Any]] = None
    ) -> ScanComparisonResult:
        """
        Compare two scans and return detailed comparison results.
        
        Args:
            scan_1: First scan results (baseline)
            scan_2: Second scan results (current)
            filters: Optional filtering criteria:
                - severity: List of severities to include
                - finding_types: List of finding types to include
                - confidence_min: Minimum confidence score (0-100)
        
        Returns:
            ScanComparisonResult with detailed findings breakdown
        """
        # Extract findings from scans
        findings_1 = self._extract_findings(scan_1, filters)
        findings_2 = self._extract_findings(scan_2, filters)
        
        # Create normalized lookup
        lookup_1 = self._create_finding_lookup(findings_1)
        lookup_2 = self._create_finding_lookup(findings_2)
        
        # Compare and categorize
        result = ScanComparisonResult(
            scan_1_id=scan_1.get("scan_id", "scan_1"),
            scan_2_id=scan_2.get("scan_id", "scan_2"),
            comparison_timestamp=datetime.now().isoformat(),
        )
        
        # Detect regressions (check scan history if available)
        regression_keys = self._detect_regressions(scan_1, scan_2)
        
        # Categorize findings
        all_keys = set(lookup_1.keys()) | set(lookup_2.keys())
        
        for key in all_keys:
            finding_1 = lookup_1.get(key)
            finding_2 = lookup_2.get(key)
            
            if finding_1 and finding_2:
                # Finding exists in both scans
                if self._findings_modified(finding_1, finding_2):
                    comparison = self._create_comparison_finding(
                        finding_2, ComparisonStatus.MODIFIED, scan_2
                    )
                    result.modified_findings.append(comparison)
                else:
                    comparison = self._create_comparison_finding(
                        finding_2, ComparisonStatus.UNCHANGED, scan_2
                    )
                    result.unchanged_findings.append(comparison)
            
            elif finding_1 and not finding_2:
                # Finding was fixed
                comparison = self._create_comparison_finding(
                    finding_1, ComparisonStatus.FIXED, scan_1
                )
                result.fixed_findings.append(comparison)
            
            elif finding_2 and not finding_1:
                # New finding
                is_regression = key in regression_keys
                status = ComparisonStatus.REGRESSION if is_regression else ComparisonStatus.NEW
                comparison = self._create_comparison_finding(finding_2, status, scan_2)
                
                if is_regression:
                    result.regressions.append(comparison)
                else:
                    result.new_findings.append(comparison)
        
        # Calculate risk scores and delta
        result.scan_1_risk_score = self._calculate_risk_score(findings_1)
        result.scan_2_risk_score = self._calculate_risk_score(findings_2)
        result.risk_delta = result.scan_2_risk_score - result.scan_1_risk_score
        
        # Determine trend
        if result.risk_delta < -5:
            result.risk_trend = "improving"
        elif result.risk_delta > 5:
            result.risk_trend = "degrading"
        else:
            result.risk_trend = "stable"
        
        # Calculate vulnerability counts
        result.total_vulnerabilities_1 = len(findings_1)
        result.total_vulnerabilities_2 = len(findings_2)
        result.vulnerability_delta = result.total_vulnerabilities_2 - result.total_vulnerabilities_1
        
        # Build severity distributions
        result.severity_distribution_1 = self._build_severity_distribution(findings_1)
        result.severity_distribution_2 = self._build_severity_distribution(findings_2)
        
        return result
    
    def get_differences(
        self,
        scan_1: Dict[str, Any],
        scan_2: Dict[str, Any],
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[ComparisonFinding]]:
        """
        Get categorized differences between two scans.
        
        Returns dict with keys: new, fixed, unchanged, modified
        """
        result = self.compare_scans(scan_1, scan_2, filters)
        return {
            "new": result.new_findings,
            "fixed": result.fixed_findings,
            "unchanged": result.unchanged_findings,
            "modified": result.modified_findings,
        }
    
    def detect_regressions(self, scan_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect regressions: vulnerabilities that were fixed but reappeared.
        
        Args:
            scan_history: List of scans in chronological order
        
        Returns:
            List of regression findings with evidence
        """
        if len(scan_history) < 2:
            return []
        
        regressions = []
        
        # For each pair of consecutive scans
        for i in range(len(scan_history) - 1):
            scan_a = scan_history[i]
            scan_b = scan_history[i + 1]
            
            findings_a = self._extract_findings(scan_a)
            findings_b = self._extract_findings(scan_b)
            
            lookup_a = self._create_finding_lookup(findings_a)
            lookup_b = self._create_finding_lookup(findings_b)
            
            # Find fixed in A->B but reappeared later
            fixed_in_ab = set(lookup_a.keys()) - set(lookup_b.keys())
            
            # Check if any of these reappear in later scans
            if i + 2 < len(scan_history):
                scan_c = scan_history[i + 2]
                findings_c = self._extract_findings(scan_c)
                lookup_c = self._create_finding_lookup(findings_c)
                
                for key in fixed_in_ab:
                    if key in lookup_c:
                        regression_finding = self._create_comparison_finding(
                            lookup_c[key],
                            ComparisonStatus.REGRESSION,
                            scan_c
                        )
                        regression_finding.last_seen_scan = scan_a.get("scan_id")
                        regressions.append(asdict(regression_finding))
        
        return regressions
    
    def calculate_risk_delta(
        self,
        scan_1: Dict[str, Any],
        scan_2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate the change in risk between two scans.
        
        Returns dict with:
            - risk_score_1, risk_score_2
            - delta (positive=worse, negative=better)
            - trend (improving|degrading|stable)
            - critical_count_delta, high_count_delta, etc.
        """
        findings_1 = self._extract_findings(scan_1)
        findings_2 = self._extract_findings(scan_2)
        
        score_1 = self._calculate_risk_score(findings_1)
        score_2 = self._calculate_risk_score(findings_2)
        delta = score_2 - score_1
        
        # Determine trend
        if delta < -5:
            trend = "improving"
        elif delta > 5:
            trend = "degrading"
        else:
            trend = "stable"
        
        # Severity deltas
        severity_dist_1 = self._build_severity_distribution(findings_1)
        severity_dist_2 = self._build_severity_distribution(findings_2)
        
        severity_deltas = {}
        for severity in self.severity_levels:
            severity_deltas[f"{severity.lower()}_delta"] = (
                severity_dist_2.get(severity, 0) - severity_dist_1.get(severity, 0)
            )
        
        return {
            "risk_score_1": score_1,
            "risk_score_2": score_2,
            "risk_delta": delta,
            "trend": trend,
            "severity_distribution_1": severity_dist_1,
            "severity_distribution_2": severity_dist_2,
            **severity_deltas,
        }
    
    def filter_findings(
        self,
        findings: List[Dict[str, Any]],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Filter findings by severity, type, and confidence.
        
        Args:
            findings: List of findings
            filters: Dict with optional keys:
                - severity: List of severity levels to include
                - finding_types: List of finding types to include
                - confidence_min: Minimum confidence score (0-100)
        
        Returns:
            Filtered findings list
        """
        if not filters:
            return findings
        
        filtered = findings
        
        if "severity" in filters and filters["severity"]:
            severity_list = filters["severity"]
            filtered = [f for f in filtered if f.get("severity") in severity_list]
        
        if "finding_types" in filters and filters["finding_types"]:
            types_list = filters["finding_types"]
            filtered = [f for f in filtered if f.get("type") in types_list]
        
        if "confidence_min" in filters:
            min_conf = filters["confidence_min"]
            filtered = [
                f for f in filtered
                if f.get("confidence_score", 0) >= min_conf
            ]
        
        return filtered
    
    # ── Private helpers ───────────────────────────────────────────────────────
    
    def _extract_findings(
        self,
        scan: Dict[str, Any],
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Extract findings from a scan result."""
        findings = []
        
        # Extract from web vulnerabilities
        web_results = scan.get("results", {}).get("web_vulnerabilities", {})
        if web_results:
            web_findings = web_results.get("findings", [])
            findings.extend(web_findings)
        
        # Extract from CVE results
        cve_results = scan.get("results", {}).get("cve", {})
        if cve_results:
            correlations = cve_results.get("correlations", [])
            for corr in correlations:
                cves = corr.get("cves", [])
                for cve in cves:
                    findings.append({
                        "type": "CVE",
                        "cve_id": cve.get("cve_id"),
                        "severity": cve.get("severity", "Unknown"),
                        "url": corr.get("port", ""),
                        "evidence": f"CVE {cve.get('cve_id')}",
                        "confidence_score": 85,  # CVEs from databases are high confidence
                    })
        
        # Apply filters
        if filters:
            findings = self.filter_findings(findings, filters)
        
        return findings
    
    def _create_finding_lookup(
        self,
        findings: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Create a normalized lookup of findings by hash for comparison."""
        lookup = {}
        for finding in findings:
            key = self._hash_finding(finding)
            lookup[key] = finding
        return lookup
    
    def _hash_finding(self, finding: Dict[str, Any]) -> str:
        """
        Create a normalized hash of a finding for comparison.
        
        Hashes: type + url + endpoint + parameter (ignores evidence/timestamp)
        """
        components = [
            finding.get("type", ""),
            finding.get("url", ""),
            finding.get("endpoint", ""),
            finding.get("parameter", ""),
        ]
        content = "|".join(str(c) for c in components)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _findings_modified(
        self,
        finding_1: Dict[str, Any],
        finding_2: Dict[str, Any]
    ) -> bool:
        """Check if a finding has been modified (e.g., confidence score changed)."""
        # Consider modified if confidence or severity changed
        conf_1 = finding_1.get("confidence_score", 0)
        conf_2 = finding_2.get("confidence_score", 0)
        
        if abs(conf_1 - conf_2) > 10:  # Threshold for significant confidence change
            return True
        
        severity_1 = finding_1.get("severity", "")
        severity_2 = finding_2.get("severity", "")
        
        return severity_1 != severity_2
    
    def _create_comparison_finding(
        self,
        finding: Dict[str, Any],
        status: ComparisonStatus,
        scan: Dict[str, Any]
    ) -> ComparisonFinding:
        """Convert a finding into a comparison finding."""
        return ComparisonFinding(
            finding_id=finding.get("finding_id", self._hash_finding(finding)),
            finding_type=finding.get("type", "Unknown"),
            severity=finding.get("severity", "Unknown"),
            status=status,
            url=finding.get("url", ""),
            endpoint=finding.get("endpoint", ""),
            parameter=finding.get("parameter", ""),
            method=finding.get("method", "GET"),
            payload=finding.get("payload", ""),
            confidence_score=finding.get("confidence_score", 0),
            evidence=finding.get("evidence", ""),
            appeared_in_scan=scan.get("scan_id"),
        )
    
    def _calculate_risk_score(self, findings: List[Dict[str, Any]]) -> float:
        """
        Calculate overall risk score from findings.
        
        Score = sum of (severity_weight * confidence_coefficient)
        """
        score = 0.0
        for finding in findings:
            severity = finding.get("severity", "Low")
            confidence = finding.get("confidence_score", 50) / 100.0
            weight = self.SEVERITY_WEIGHTS.get(severity, 1)
            score += weight * confidence
        return score
    
    def _build_severity_distribution(
        self,
        findings: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Count findings by severity level."""
        distribution = {s: 0 for s in self.severity_levels}
        for finding in findings:
            severity = finding.get("severity", "Info")
            if severity in distribution:
                distribution[severity] += 1
        return distribution
    
    def _detect_regressions(
        self,
        scan_1: Dict[str, Any],
        scan_2: Dict[str, Any]
    ) -> Set[str]:
        """
        Detect regression keys by checking if they appear in prior scan history.
        
        A regression is when a vulnerability was previously fixed but reappeared.
        We check the scan history for evidence of this pattern.
        """
        regression_keys = set()
        
        # Get full scan history if available
        history = scan_1.get("history", [])
        if len(history) < 2:
            return regression_keys
        
        # Find findings in scan_2 that were absent in scan_1 but present earlier
        findings_1 = self._extract_findings(scan_1)
        findings_2 = self._extract_findings(scan_2)
        
        lookup_1 = self._create_finding_lookup(findings_1)
        lookup_2 = self._create_finding_lookup(findings_2)
        
        # For each new finding in scan_2
        for key in set(lookup_2.keys()) - set(lookup_1.keys()):
            # Check if it exists in earlier scans
            for prior_scan in history[:-2]:  # Exclude last two scans
                prior_findings = self._extract_findings(prior_scan)
                prior_lookup = self._create_finding_lookup(prior_findings)
                
                if key in prior_lookup:
                    # Found it in older scan, so it's a regression
                    regression_keys.add(key)
                    break
        
        return regression_keys
