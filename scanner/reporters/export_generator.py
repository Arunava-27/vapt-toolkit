"""
Enhanced Export Generator for VAPT Scan Results.
Supports multiple export formats: JSON, CSV, HTML, SARIF, XLSX, Markdown.
Includes metadata, filtering, and evidence handling.
"""

import json
import csv
import io
import html
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
from scanner.reporters.sarif_reporter import VAPTSarifReporter


class ExportFormat(Enum):
    """Supported export formats."""
    JSON = "json"
    CSV = "csv"
    HTML = "html"
    SARIF = "sarif"
    XLSX = "xlsx"
    MARKDOWN = "markdown"


class ExportGenerator:
    """Generate exports for scan results in multiple formats."""

    # OWASP Top 10 Mapping
    OWASP_MAP = {
        "sqli": "A03:2021 - Injection",
        "xss": "A07:2021 - Cross-Site Scripting (XSS)",
        "csrf": "A01:2021 - Broken Access Control",
        "xxe": "A05:2021 - Security Misconfiguration",
        "auth": "A07:2021 - Identification and Authentication Failures",
        "broken_auth": "A07:2021 - Identification and Authentication Failures",
        "session": "A02:2021 - Cryptographic Failures",
        "crypto": "A02:2021 - Cryptographic Failures",
        "access": "A01:2021 - Broken Access Control",
        "insecure": "A05:2021 - Security Misconfiguration",
        "headers": "A05:2021 - Security Misconfiguration",
        "ssl": "A02:2021 - Cryptographic Failures",
        "tls": "A02:2021 - Cryptographic Failures",
    }

    # CWE Mapping
    CWE_MAP = {
        "sqli": 89,
        "xss": 79,
        "csrf": 352,
        "xxe": 611,
        "auth": 287,
        "broken_auth": 287,
        "session": 613,
        "crypto": 327,
        "access": 284,
        "insecure": 16,
    }

    def __init__(self, scan_data: Dict[str, Any]):
        """
        Initialize export generator.
        
        Args:
            scan_data: Dictionary containing scan results with config and results
        """
        self.scan_data = scan_data
        self.config = scan_data.get("config", {})
        self.results = scan_data.get("results", {})
        self.timestamp = scan_data.get("timestamp", datetime.now().isoformat())
        self.target = self.config.get("target", "Unknown")
        self.findings = self._extract_findings()

    def _extract_findings(self) -> List[Dict[str, Any]]:
        """Extract all findings from scan results."""
        findings = []

        # Web vulnerabilities
        web_findings = self.results.get("web_vulnerabilities", {}).get("findings", [])
        for finding in web_findings:
            findings.append({
                "type": "web_vulnerability",
                "title": finding.get("title", "Unknown"),
                "severity": finding.get("severity", "Unknown").lower(),
                "confidence": finding.get("confidence", "Unknown").lower(),
                "description": finding.get("description", ""),
                "location": finding.get("url", ""),
                "evidence": finding.get("evidence", ""),
                "remediation": finding.get("remediation", ""),
                "cwe_id": self._get_cwe(finding.get("title", "")),
                "owasp": self._get_owasp(finding.get("title", "")),
            })

        # CVEs
        cve_correlations = self.results.get("cve", {}).get("correlations", [])
        for correlation in cve_correlations:
            for cve in correlation.get("cves", []):
                findings.append({
                    "type": "cve",
                    "title": cve.get("id", "Unknown CVE"),
                    "severity": (cve.get("severity") or "unknown").lower(),
                    "confidence": "high",
                    "description": cve.get("description", ""),
                    "location": correlation.get("service", "Unknown service"),
                    "evidence": f"CVSS Score: {cve.get('cvss_score', 'N/A')}",
                    "remediation": "Update to patched version",
                    "cwe_id": None,
                    "owasp": "A06:2021 - Vulnerable and Outdated Components",
                })

        # Open Ports
        open_ports = self.results.get("ports", {}).get("open_ports", [])
        for port in open_ports:
            findings.append({
                "type": "open_port",
                "title": f"Open Port {port.get('port', 'Unknown')}",
                "severity": "low",
                "confidence": "high",
                "description": f"Port {port.get('port')} is open with service {port.get('service', 'Unknown')}",
                "location": f"Port {port.get('port')}",
                "evidence": f"Service: {port.get('service', 'Unknown')}",
                "remediation": "Review exposed services and restrict access if not needed",
                "cwe_id": None,
                "owasp": "A01:2021 - Broken Access Control",
            })

        return findings

    def _get_owasp(self, title: str) -> Optional[str]:
        """Get OWASP category for a finding."""
        title_lower = title.lower()
        for keyword, owasp in self.OWASP_MAP.items():
            if keyword in title_lower:
                return owasp
        return "A01:2021 - Broken Access Control"

    def _get_cwe(self, title: str) -> Optional[int]:
        """Get CWE ID for a finding."""
        title_lower = title.lower()
        for keyword, cwe_id in self.CWE_MAP.items():
            if keyword in title_lower:
                return cwe_id
        return None

    def _filter_findings(
        self,
        severity: Optional[str] = None,
        confidence: Optional[str] = None,
        finding_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Filter findings by criteria."""
        filtered = self.findings

        if severity:
            severity = severity.lower()
            filtered = [f for f in filtered if f.get("severity", "").lower() == severity]

        if confidence:
            confidence = confidence.lower()
            filtered = [f for f in filtered if f.get("confidence", "").lower() == confidence]

        if finding_type:
            filtered = [f for f in filtered if f.get("type") == finding_type]

        return filtered

    def _get_metadata(self) -> Dict[str, Any]:
        """Get scan metadata."""
        return {
            "scan_date": self.timestamp,
            "target": self.target,
            "duration": self.config.get("duration", "Unknown"),
            "scan_type": self.config.get("scan_classification", "active"),
            "modules": {
                "recon": self.config.get("recon", False),
                "ports": self.config.get("ports", False),
                "web": self.config.get("web", False),
                "cve": self.config.get("cve", False),
            },
            "total_findings": len(self.findings),
            "findings_by_severity": self._severity_summary(),
        }

    def _severity_summary(self) -> Dict[str, int]:
        """Get count of findings by severity."""
        summary = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0,
        }
        for finding in self.findings:
            severity = finding.get("severity", "info").lower()
            if severity in summary:
                summary[severity] += 1
        return summary

    def export_json(
        self,
        include_metadata: bool = True,
        include_evidence: bool = True,
        severity: Optional[str] = None,
        confidence: Optional[str] = None,
    ) -> str:
        """
        Export scan results as JSON.
        
        Args:
            include_metadata: Include scan metadata
            include_evidence: Include evidence data
            severity: Filter by severity level
            confidence: Filter by confidence level
            
        Returns:
            JSON string
        """
        findings = self._filter_findings(severity=severity, confidence=confidence)

        if not include_evidence:
            for finding in findings:
                finding.pop("evidence", None)

        export_data = {
            "format": "json",
            "export_date": datetime.now().isoformat(),
        }

        if include_metadata:
            export_data["metadata"] = self._get_metadata()

        export_data["findings"] = findings
        export_data["summary"] = {
            "total": len(findings),
            "by_type": self._count_by_type(findings),
            "by_severity": self._count_by_severity(findings),
        }

        return json.dumps(export_data, indent=2, default=str)

    def export_csv(
        self,
        include_metadata: bool = True,
        severity: Optional[str] = None,
        confidence: Optional[str] = None,
    ) -> str:
        """
        Export scan results as CSV.
        
        Args:
            include_metadata: Include metadata as header comments
            severity: Filter by severity level
            confidence: Filter by confidence level
            
        Returns:
            CSV string
        """
        findings = self._filter_findings(severity=severity, confidence=confidence)

        output = io.StringIO()

        if include_metadata:
            metadata = self._get_metadata()
            output.write(f"# VAPT Scan Export - {metadata['scan_date']}\n")
            output.write(f"# Target: {metadata['target']}\n")
            output.write(f"# Total Findings: {metadata['total_findings']}\n")
            output.write("#\n")

        fieldnames = [
            "Type",
            "Title",
            "Severity",
            "Confidence",
            "Location",
            "Description",
            "Remediation",
            "CWE ID",
            "OWASP",
        ]

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for finding in findings:
            writer.writerow({
                "Type": finding.get("type", ""),
                "Title": finding.get("title", ""),
                "Severity": finding.get("severity", ""),
                "Confidence": finding.get("confidence", ""),
                "Location": finding.get("location", ""),
                "Description": finding.get("description", ""),
                "Remediation": finding.get("remediation", ""),
                "CWE ID": finding.get("cwe_id", ""),
                "OWASP": finding.get("owasp", ""),
            })

        return output.getvalue()

    def export_html(
        self,
        include_metadata: bool = True,
        include_evidence: bool = True,
        severity: Optional[str] = None,
        confidence: Optional[str] = None,
    ) -> str:
        """
        Export scan results as standalone HTML report.
        
        Args:
            include_metadata: Include scan metadata
            include_evidence: Include evidence data
            severity: Filter by severity level
            confidence: Filter by confidence level
            
        Returns:
            HTML string
        """
        findings = self._filter_findings(severity=severity, confidence=confidence)
        metadata = self._get_metadata() if include_metadata else None

        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VAPT Scan Report</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; background: #f5f5f5; color: #333; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; border-radius: 8px; margin-bottom: 30px; }
        .header h1 { font-size: 32px; margin-bottom: 10px; }
        .metadata { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px; }
        .metadata-item { background: rgba(255,255,255,0.1); padding: 10px; border-radius: 4px; }
        .metadata-item label { display: block; font-size: 12px; opacity: 0.8; }
        .metadata-item value { display: block; font-size: 16px; font-weight: bold; }
        .summary { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 30px 0; }
        .summary-card { background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .summary-card .number { font-size: 28px; font-weight: bold; margin-bottom: 5px; }
        .summary-card .label { color: #666; font-size: 14px; }
        .critical { color: #dc3545; }
        .high { color: #fd7e14; }
        .medium { color: #ffc107; }
        .low { color: #28a745; }
        .info { color: #17a2b8; }
        .findings { margin-top: 30px; }
        .finding { background: white; border-left: 4px solid #ddd; padding: 20px; margin-bottom: 15px; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
        .finding.critical { border-left-color: #dc3545; }
        .finding.high { border-left-color: #fd7e14; }
        .finding.medium { border-left-color: #ffc107; }
        .finding.low { border-left-color: #28a745; }
        .finding-title { font-size: 18px; font-weight: bold; margin-bottom: 10px; }
        .finding-badges { margin-bottom: 10px; }
        .badge { display: inline-block; padding: 4px 8px; border-radius: 3px; font-size: 12px; font-weight: bold; margin-right: 5px; color: white; }
        .badge-severity { background: #dc3545; }
        .badge-confidence { background: #6c757d; }
        .badge-type { background: #007bff; }
        .finding-detail { margin-top: 10px; line-height: 1.6; }
        .finding-detail label { display: block; font-weight: bold; color: #666; margin-top: 8px; }
        .finding-detail p { margin-top: 4px; }
        .code-block { background: #f5f5f5; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 12px; overflow-x: auto; margin-top: 5px; }
        footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>VAPT Scan Report</h1>
            <p>Vulnerability Assessment and Penetration Test Results</p>"""

        if metadata:
            html_content += f"""
            <div class="metadata">
                <div class="metadata-item">
                    <label>Target</label>
                    <value>{html.escape(metadata['target'])}</value>
                </div>
                <div class="metadata-item">
                    <label>Scan Date</label>
                    <value>{metadata['scan_date']}</value>
                </div>
                <div class="metadata-item">
                    <label>Scan Type</label>
                    <value>{metadata['scan_type']}</value>
                </div>
                <div class="metadata-item">
                    <label>Total Findings</label>
                    <value>{metadata['total_findings']}</value>
                </div>
            </div>"""

        html_content += """
        </div>"""

        if metadata:
            severity_summary = metadata.get("findings_by_severity", {})
            html_content += """
        <div class="summary">"""
            for severity_level in ["critical", "high", "medium", "low"]:
                count = severity_summary.get(severity_level, 0)
                html_content += f"""
            <div class="summary-card">
                <div class="number {severity_level}">{count}</div>
                <div class="label">{severity_level.capitalize()} Severity</div>
            </div>"""
            html_content += """
        </div>"""

        html_content += """
        <div class="findings">
            <h2>Findings</h2>"""

        for finding in findings:
            severity = finding.get("severity", "info")
            html_content += f"""
            <div class="finding {severity}">
                <div class="finding-title">{html.escape(finding.get('title', 'Unknown'))}</div>
                <div class="finding-badges">
                    <span class="badge badge-type">{finding.get('type', 'Unknown')}</span>
                    <span class="badge badge-severity">{finding.get('severity', 'Unknown').upper()}</span>
                    <span class="badge badge-confidence">{finding.get('confidence', 'Unknown').capitalize()}</span>
                </div>"""

            if finding.get("location"):
                html_content += f"""
                <div class="finding-detail">
                    <label>Location:</label>
                    <p>{html.escape(finding.get('location', ''))}</p>
                </div>"""

            if finding.get("description"):
                html_content += f"""
                <div class="finding-detail">
                    <label>Description:</label>
                    <p>{html.escape(finding.get('description', ''))}</p>
                </div>"""

            if include_evidence and finding.get("evidence"):
                html_content += f"""
                <div class="finding-detail">
                    <label>Evidence:</label>
                    <div class="code-block">{html.escape(finding.get('evidence', ''))}</div>
                </div>"""

            if finding.get("remediation"):
                html_content += f"""
                <div class="finding-detail">
                    <label>Remediation:</label>
                    <p>{html.escape(finding.get('remediation', ''))}</p>
                </div>"""

            if finding.get("owasp"):
                html_content += f"""
                <div class="finding-detail">
                    <label>OWASP:</label>
                    <p>{html.escape(finding.get('owasp', ''))}</p>
                </div>"""

            if finding.get("cwe_id"):
                html_content += f"""
                <div class="finding-detail">
                    <label>CWE ID:</label>
                    <p><a href="https://cwe.mitre.org/data/definitions/{finding.get('cwe_id')}.html" target="_blank">CWE-{finding.get('cwe_id')}</a></p>
                </div>"""

            html_content += """
            </div>"""

        html_content += """
        </div>
        <footer>
            <p>Generated on """ + datetime.now().isoformat() + """</p>
            <p>VAPT Toolkit - Enhanced Vulnerability Assessment Tool</p>
        </footer>
    </div>
</body>
</html>"""

        return html_content

    def export_sarif(
        self,
        include_metadata: bool = True,
        severity: Optional[str] = None,
        confidence: Optional[str] = None,
    ) -> str:
        """
        Export scan results as SARIF v2.1.0.
        
        Args:
            include_metadata: Include scan metadata
            severity: Filter by severity level
            confidence: Filter by confidence level
            
        Returns:
            SARIF JSON string
        """
        findings = self._filter_findings(severity=severity, confidence=confidence)

        reporter = VAPTSarifReporter(
            tool_version="1.0.0",
            scan_target=self.target,
        )

        # Convert findings to SARIF format
        sarif_findings = []
        for finding in findings:
            sarif_findings.append({
                "title": finding.get("title", "Unknown"),
                "severity": finding.get("severity", "low"),
                "description": finding.get("description", ""),
                "location": finding.get("location", ""),
                "evidence": finding.get("evidence", ""),
                "remediation": finding.get("remediation", ""),
            })

        sarif_output = reporter.generate(sarif_findings)

        if include_metadata:
            metadata = self._get_metadata()
            # Add metadata to the runs array properties
            if "runs" in sarif_output and len(sarif_output["runs"]) > 0:
                if "properties" not in sarif_output["runs"][0]:
                    sarif_output["runs"][0]["properties"] = {}
                sarif_output["runs"][0]["properties"]["metadata"] = metadata

        return json.dumps(sarif_output, indent=2, default=str)

    def export_markdown(
        self,
        include_metadata: bool = True,
        include_evidence: bool = True,
        severity: Optional[str] = None,
        confidence: Optional[str] = None,
    ) -> str:
        """
        Export scan results as Markdown.
        
        Args:
            include_metadata: Include scan metadata
            include_evidence: Include evidence data
            severity: Filter by severity level
            confidence: Filter by confidence level
            
        Returns:
            Markdown string
        """
        findings = self._filter_findings(severity=severity, confidence=confidence)
        metadata = self._get_metadata() if include_metadata else None

        md_content = "# VAPT Scan Report\n\n"
        md_content += "> Vulnerability Assessment and Penetration Test Results\n\n"

        if metadata:
            md_content += "## Scan Information\n\n"
            md_content += f"- **Target**: {metadata['target']}\n"
            md_content += f"- **Scan Date**: {metadata['scan_date']}\n"
            md_content += f"- **Scan Type**: {metadata['scan_type']}\n"
            md_content += f"- **Total Findings**: {metadata['total_findings']}\n\n"

            md_content += "## Severity Summary\n\n"
            md_content += "| Severity | Count |\n"
            md_content += "|----------|-------|\n"
            for severity_level in ["critical", "high", "medium", "low", "info"]:
                count = metadata.get("findings_by_severity", {}).get(severity_level, 0)
                md_content += f"| {severity_level.capitalize()} | {count} |\n"
            md_content += "\n"

        md_content += "## Findings\n\n"

        for idx, finding in enumerate(findings, 1):
            severity_badge = f":warning: **{finding.get('severity', 'Unknown').upper()}**"
            md_content += f"### {idx}. {finding.get('title', 'Unknown')} {severity_badge}\n\n"

            md_content += f"**Type**: `{finding.get('type', 'Unknown')}`  \n"
            md_content += f"**Confidence**: {finding.get('confidence', 'Unknown')}  \n"
            md_content += f"**Severity**: {finding.get('severity', 'Unknown')}  \n"

            if finding.get("location"):
                md_content += f"**Location**: `{finding.get('location', '')}`  \n"

            md_content += "\n"

            if finding.get("description"):
                md_content += "**Description**\n\n"
                md_content += f"{finding.get('description', '')}\n\n"

            if include_evidence and finding.get("evidence"):
                md_content += "**Evidence**\n\n"
                md_content += f"```\n{finding.get('evidence', '')}\n```\n\n"

            if finding.get("remediation"):
                md_content += "**Remediation**\n\n"
                md_content += f"{finding.get('remediation', '')}\n\n"

            if finding.get("owasp") or finding.get("cwe_id"):
                md_content += "**References**\n\n"
                if finding.get("owasp"):
                    md_content += f"- OWASP: {finding.get('owasp', '')}\n"
                if finding.get("cwe_id"):
                    md_content += f"- CWE: [CWE-{finding.get('cwe_id')}](https://cwe.mitre.org/data/definitions/{finding.get('cwe_id')}.html)\n"
                md_content += "\n"

            md_content += "---\n\n"

        md_content += f"_Report generated on {datetime.now().isoformat()}_\n"
        md_content += "_VAPT Toolkit - Enhanced Vulnerability Assessment Tool_\n"

        return md_content

    def export_xlsx(
        self,
        include_metadata: bool = True,
        include_evidence: bool = True,
        severity: Optional[str] = None,
        confidence: Optional[str] = None,
    ) -> bytes:
        """
        Export scan results as Excel workbook.
        Requires: from scanner.reporters.excel_exporter import ExcelExporter
        
        Args:
            include_metadata: Include scan metadata
            include_evidence: Include evidence data
            severity: Filter by severity level
            confidence: Filter by confidence level
            
        Returns:
            Excel bytes
        """
        from scanner.reporters.excel_exporter import ExcelExporter

        findings = self._filter_findings(severity=severity, confidence=confidence)
        metadata = self._get_metadata() if include_metadata else None

        exporter = ExcelExporter(self.target)
        return exporter.generate(
            findings=findings,
            metadata=metadata,
            include_evidence=include_evidence,
        )

    def _count_by_type(self, findings: List[Dict]) -> Dict[str, int]:
        """Count findings by type."""
        counts = {}
        for finding in findings:
            ftype = finding.get("type", "unknown")
            counts[ftype] = counts.get(ftype, 0) + 1
        return counts

    def _count_by_severity(self, findings: List[Dict]) -> Dict[str, int]:
        """Count findings by severity."""
        counts = {}
        for finding in findings:
            severity = finding.get("severity", "unknown")
            counts[severity] = counts.get(severity, 0) + 1
        return counts

    def export(
        self,
        format: ExportFormat,
        include_metadata: bool = True,
        include_evidence: bool = True,
        severity: Optional[str] = None,
        confidence: Optional[str] = None,
    ) -> Any:
        """
        Export scan results in specified format.
        
        Args:
            format: Export format
            include_metadata: Include scan metadata
            include_evidence: Include evidence data
            severity: Filter by severity level
            confidence: Filter by confidence level
            
        Returns:
            Exported data (str or bytes depending on format)
        """
        if format == ExportFormat.JSON:
            return self.export_json(include_metadata, include_evidence, severity, confidence)
        elif format == ExportFormat.CSV:
            return self.export_csv(include_metadata, severity, confidence)
        elif format == ExportFormat.HTML:
            return self.export_html(include_metadata, include_evidence, severity, confidence)
        elif format == ExportFormat.SARIF:
            return self.export_sarif(include_metadata, severity, confidence)
        elif format == ExportFormat.MARKDOWN:
            return self.export_markdown(include_metadata, include_evidence, severity, confidence)
        elif format == ExportFormat.XLSX:
            return self.export_xlsx(include_metadata, include_evidence, severity, confidence)
        else:
            raise ValueError(f"Unsupported format: {format}")
