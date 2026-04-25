"""
VAPT Toolkit PR Comment Generator
Generates formatted PR comments with VAPT security scan results.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class SeverityLevel(Enum):
    """Severity levels for vulnerabilities."""
    CRITICAL = ("Critical", "🔴")
    HIGH = ("High", "🟠")
    MEDIUM = ("Medium", "🟡")
    LOW = ("Low", "🟢")
    INFO = ("Info", "🔵")


class PRCommentGenerator:
    """Generate formatted PR comments with scan results."""

    def __init__(self, scan_target: str = "Unknown", duration_seconds: float = 0):
        """
        Initialize PR comment generator.

        Args:
            scan_target: URL that was scanned
            duration_seconds: Time taken to complete scan
        """
        self.scan_target = scan_target
        self.duration_seconds = duration_seconds

    def generate(self, findings: List[Dict[str, Any]]) -> str:
        """
        Generate a formatted PR comment from scan findings.

        Args:
            findings: List of vulnerability findings

        Returns:
            Formatted markdown PR comment
        """
        # Count findings by severity
        severity_counts = self._count_by_severity(findings)

        # Group findings
        critical = [f for f in findings if f.get("severity", "").lower() == "critical"]
        high = [f for f in findings if f.get("severity", "").lower() == "high"]
        medium = [f for f in findings if f.get("severity", "").lower() == "medium"]
        low = [f for f in findings if f.get("severity", "").lower() == "low"]

        # Build comment
        parts = [
            self._header(),
            self._severity_summary(severity_counts),
            self._findings_section(critical, "Critical", SeverityLevel.CRITICAL),
            self._findings_section(high, "High", SeverityLevel.HIGH),
            self._findings_section(medium, "Medium", SeverityLevel.MEDIUM),
            self._findings_section(low, "Low", SeverityLevel.LOW),
            self._scan_details(),
            self._footer(),
        ]

        return "\n\n".join(filter(None, parts))

    def generate_summary_only(self, findings: List[Dict[str, Any]]) -> str:
        """
        Generate a brief summary-only comment (for quick feedback).

        Args:
            findings: List of vulnerability findings

        Returns:
            Brief markdown summary
        """
        severity_counts = self._count_by_severity(findings)
        total = sum(severity_counts.values())

        if total == 0:
            return (
                "## ✅ VAPT Security Scan Passed\n\n"
                f"No vulnerabilities detected in **{self.scan_target}**\n"
                f"Scan completed in {self.duration_seconds:.1f}s"
            )

        return (
            "## 🛡️ VAPT Security Scan Results\n\n"
            f"**{total}** vulnerabilities found:\n"
            f"- {SeverityLevel.CRITICAL.value[1]} **{severity_counts['critical']}** Critical\n"
            f"- {SeverityLevel.HIGH.value[1]} **{severity_counts['high']}** High\n"
            f"- {SeverityLevel.MEDIUM.value[1]} **{severity_counts['medium']}** Medium\n"
            f"- {SeverityLevel.LOW.value[1]} **{severity_counts['low']}** Low\n\n"
            f"[View detailed report →](#details)"
        )

    def _header(self) -> str:
        """Generate comment header."""
        total_findings = sum(self._count_by_severity([]).values())
        return "## 🛡️ VAPT Security Scan Results"

    def _severity_summary(self, severity_counts: Dict[str, int]) -> str:
        """Generate severity summary table."""
        total = sum(severity_counts.values())

        if total == 0:
            return "### ✅ No Vulnerabilities Detected"

        lines = [
            "### Summary",
            "",
            "| Severity | Count | Status |",
            "|----------|-------|--------|",
            f"| {SeverityLevel.CRITICAL.value[1]} Critical | **{severity_counts['critical']}** | {'❌' if severity_counts['critical'] > 0 else '✅'} |",
            f"| {SeverityLevel.HIGH.value[1]} High | **{severity_counts['high']}** | {'❌' if severity_counts['high'] > 0 else '✅'} |",
            f"| {SeverityLevel.MEDIUM.value[1]} Medium | **{severity_counts['medium']}** | {'⚠️' if severity_counts['medium'] > 0 else '✅'} |",
            f"| {SeverityLevel.LOW.value[1]} Low | **{severity_counts['low']}** | {'ℹ️' if severity_counts['low'] > 0 else '✅'} |",
            f"| **Total** | **{total}** | |",
        ]
        return "\n".join(lines)

    def _findings_section(
        self,
        findings: List[Dict[str, Any]],
        severity_name: str,
        severity_level: SeverityLevel
    ) -> str:
        """Generate section for findings of specific severity."""
        if not findings:
            return ""

        icon = severity_level.value[1]
        lines = [
            f"### {icon} {severity_name} Severity Findings",
            ""
        ]

        for idx, finding in enumerate(findings, 1):
            lines.extend(self._format_finding(finding, idx, icon))

        return "\n".join(lines)

    def _format_finding(
        self,
        finding: Dict[str, Any],
        index: int,
        icon: str
    ) -> List[str]:
        """Format a single finding for display."""
        vuln_type = finding.get("type", "Unknown")
        location = finding.get("location", "Unknown")
        parameter = finding.get("parameter", "")
        message = finding.get("message", "")
        evidence = finding.get("evidence", "")
        confidence = finding.get("confidence", 0)
        cwe_id = finding.get("cwe_id", "")
        owasp = finding.get("owasp_category", "")

        lines = [
            f"#### {index}. {icon} {vuln_type}",
            "",
        ]

        # Location
        if parameter:
            lines.append(f"**Location**: `{location}?{parameter}=...`")
        else:
            lines.append(f"**Location**: `{location}`")

        # Message
        if message:
            lines.append(f"**Issue**: {message}")

        # Confidence
        confidence_pct = int(confidence * 100)
        lines.append(f"**Confidence**: {confidence_pct}% " + self._get_confidence_bar(confidence))

        # Evidence
        if evidence:
            lines.append(f"**Evidence**: {evidence}")

        # CWE and OWASP
        refs = []
        if cwe_id:
            refs.append(f"[{cwe_id}](https://cwe.mitre.org/data/definitions/{cwe_id.split('-')[1]}.html)")
        if owasp:
            refs.append(f"*{owasp}*")

        if refs:
            lines.append(f"**References**: {' | '.join(refs)}")

        lines.append("")

        return lines

    def _scan_details(self) -> str:
        """Generate scan details section."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

        lines = [
            "<details>",
            "<summary><strong>📋 Scan Details</strong></summary>",
            "<br>",
            "",
            "| Property | Value |",
            "|----------|-------|",
            f"| **Target** | `{self.scan_target}` |",
            f"| **Timestamp** | {timestamp} |",
            f"| **Duration** | {self.duration_seconds:.2f}s |",
            f"| **Tool** | VAPT Toolkit v1.0.0 |",
            f"| **Tests Enabled** | XSS, SQLi, CSRF, IDOR, SSRF, Auth, File Upload, Logic |",
            "",
            "</details>",
        ]

        return "\n".join(lines)

    def _footer(self) -> str:
        """Generate comment footer."""
        lines = [
            "---",
            "🤖 *Automated security scan by VAPT Toolkit CI/CD Integration*",
            "[View GitHub Security Tab](https://github.com/) | "
            "[Configure Scan](https://github.com/) | "
            "[Report Issue](https://github.com/)",
        ]
        return "\n".join(lines)

    def _count_by_severity(self, findings: Optional[List[Dict[str, Any]]] = None) -> Dict[str, int]:
        """Count findings by severity level."""
        if findings is None:
            findings = []

        counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        }

        for finding in findings:
            severity = finding.get("severity", "low").lower()
            if severity in counts:
                counts[severity] += 1

        return counts

    @staticmethod
    def _get_confidence_bar(confidence: float) -> str:
        """Get visual confidence bar."""
        filled = int(confidence * 5)
        empty = 5 - filled
        return f"`[{'█' * filled}{'░' * empty}]`"


def generate_pr_comment(
    findings: List[Dict[str, Any]],
    scan_target: str = "Unknown",
    duration_seconds: float = 0,
    summary_only: bool = False,
) -> str:
    """
    Convenience function to generate a PR comment.

    Args:
        findings: List of vulnerability findings
        scan_target: Target URL that was scanned
        duration_seconds: Time taken to complete scan
        summary_only: If True, generate summary-only comment

    Returns:
        Formatted markdown PR comment
    """
    generator = PRCommentGenerator(scan_target, duration_seconds)
    if summary_only:
        return generator.generate_summary_only(findings)
    return generator.generate(findings)
