"""Executive Summary Report Generator - One-page professional reports for C-level executives."""

import json
from datetime import datetime
from typing import Optional, Dict, List, Tuple, Any
from io import BytesIO
from pathlib import Path


class ExecutiveReporter:
    """Generates one-page executive summary reports with risk gauge, key findings, and compliance status."""

    # Risk score color thresholds
    RISK_COLORS = {
        "critical": "#cf222e",  # Red
        "high": "#f0883e",      # Orange
        "medium": "#d29922",    # Yellow
        "low": "#3fb950",       # Green
    }

    def __init__(self, scan_result: Dict[str, Any], historical_scans: Optional[List[Dict]] = None):
        """
        Initialize executive reporter.

        Args:
            scan_result: Complete scan result dictionary
            historical_scans: List of previous scan results for trend analysis
        """
        self.scan_result = scan_result
        self.historical_scans = historical_scans or []
        self.timestamp = datetime.now().isoformat()

    def _calculate_risk_score(self) -> int:
        """Calculate overall risk score (0-100) based on findings."""
        findings = self._get_all_findings()
        if not findings:
            return 0

        severity_weights = {"Critical": 100, "High": 75, "Medium": 50, "Low": 25}
        total_score = sum(severity_weights.get(f.get("severity", "Low"), 25) for f in findings)
        avg_score = total_score / len(findings)

        # Normalize to 0-100
        risk_score = min(100, int(avg_score))
        return risk_score

    def _get_all_findings(self) -> List[Dict[str, Any]]:
        """Extract all findings from scan result (web vulnerabilities, CVEs, etc)."""
        findings = []

        # Web vulnerabilities
        web_vulns = self.scan_result.get("web_vulnerabilities", {})
        if isinstance(web_vulns, dict):
            findings.extend(web_vulns.get("findings", []))

        # CVE findings
        cve_data = self.scan_result.get("cve", {})
        for corr in cve_data.get("correlations", []):
            for cve in corr.get("cves", []):
                findings.append({
                    "type": "CVE",
                    "title": cve.get("id", "Unknown"),
                    "severity": cve.get("severity", "Medium"),
                    "description": cve.get("description", ""),
                    "cvss_score": cve.get("cvss_score", 0),
                })

        return findings

    def _get_top_findings(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top N critical/high findings."""
        findings = self._get_all_findings()

        # Sort by severity
        severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        sorted_findings = sorted(
            findings,
            key=lambda f: (severity_order.get(f.get("severity", "Low"), 4), -f.get("cvss_score", 0)),
        )

        return sorted_findings[:limit]

    def _calculate_compliance_coverage(self) -> Dict[str, float]:
        """Calculate OWASP Top 10 coverage (% of findings per category)."""
        findings = self._get_all_findings()
        if not findings:
            return {}

        owasp_categories = {}
        for finding in findings:
            category = finding.get("owasp_category", "A05")
            owasp_categories[category] = owasp_categories.get(category, 0) + 1

        total = len(findings)
        coverage = {cat: round((count / total) * 100, 1) for cat, count in owasp_categories.items()}
        return coverage

    def _calculate_risk_trend(self) -> List[Tuple[str, int]]:
        """Calculate historical risk trend if available."""
        if not self.historical_scans:
            return []

        trend = []
        for scan in self.historical_scans[-10:]:  # Last 10 scans
            scan_result = scan.get("results", {})
            risk_score = self._calculate_risk_score_for_result(scan_result)
            timestamp = scan.get("timestamp", "")
            trend.append((timestamp, risk_score))

        return trend

    def _calculate_risk_score_for_result(self, result: Dict[str, Any]) -> int:
        """Calculate risk score for a specific result."""
        findings = self._extract_findings_from_result(result)
        if not findings:
            return 0

        severity_weights = {"Critical": 100, "High": 75, "Medium": 50, "Low": 25}
        total_score = sum(severity_weights.get(f.get("severity", "Low"), 25) for f in findings)
        avg_score = total_score / len(findings)
        return min(100, int(avg_score))

    def _extract_findings_from_result(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract findings from a specific result."""
        findings = []
        web_vulns = result.get("web_vulnerabilities", {})
        if isinstance(web_vulns, dict):
            findings.extend(web_vulns.get("findings", []))
        return findings

    def _get_remediation_roadmap(self) -> List[Dict[str, Any]]:
        """Generate remediation roadmap prioritized by impact/effort ratio."""
        findings = self._get_top_findings(limit=10)
        roadmap = []

        for finding in findings:
            effort_map = {"Critical": 3, "High": 2, "Medium": 2, "Low": 1}
            impact = {"Critical": 3, "High": 2, "Medium": 1, "Low": 1}
            severity = finding.get("severity", "Low")

            ratio = impact.get(severity, 1) / effort_map.get(severity, 1)

            roadmap.append(
                {
                    "title": finding.get("title", "Unknown Vulnerability"),
                    "severity": severity,
                    "type": finding.get("type", "Web Vulnerability"),
                    "impact": impact.get(severity, 1),
                    "effort": effort_map.get(severity, 1),
                    "ratio": round(ratio, 2),
                    "description": finding.get("description", "")[:100],
                }
            )

        # Sort by impact/effort ratio (quick wins first)
        return sorted(roadmap, key=lambda x: x["ratio"], reverse=True)[:5]

    def _get_key_metrics(self) -> Dict[str, Any]:
        """Generate key security metrics."""
        findings = self._get_all_findings()
        severity_count = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}

        for finding in findings:
            severity = finding.get("severity", "Low")
            if severity in severity_count:
                severity_count[severity] += 1

        ports_data = self.scan_result.get("ports", {})
        cve_data = self.scan_result.get("cve", {})

        return {
            "total_findings": len(findings),
            "critical_count": severity_count["Critical"],
            "high_count": severity_count["High"],
            "medium_count": severity_count["Medium"],
            "low_count": severity_count["Low"],
            "open_ports": len(ports_data.get("open_ports", [])),
            "total_cves": cve_data.get("total_cves", 0),
        }

    def generate_html(self) -> str:
        """Generate one-page executive summary HTML report."""
        risk_score = self._calculate_risk_score()
        top_findings = self._get_top_findings()
        compliance = self._calculate_compliance_coverage()
        roadmap = self._get_remediation_roadmap()
        metrics = self._get_key_metrics()

        # Determine risk level and color
        if risk_score >= 66:
            risk_level = "Critical"
            risk_color = self.RISK_COLORS["critical"]
        elif risk_score >= 33:
            risk_level = "High"
            risk_color = self.RISK_COLORS["high"]
        else:
            risk_level = "Low"
            risk_color = self.RISK_COLORS["low"]

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Executive Security Summary</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        @media print {{
            body {{ margin: 0; padding: 10mm; }}
            .page {{ page-break-after: avoid; }}
        }}
        
        body {{
            font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
            line-height: 1.4;
            color: #24292f;
            background: white;
            padding: 20px;
        }}
        
        .page {{
            max-width: 8.5in;
            height: 11in;
            margin: 0 auto;
            padding: 30px;
            background: white;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}
        
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            border-bottom: 2px solid #1f6feb;
            padding-bottom: 12px;
            margin-bottom: 12px;
        }}
        
        .header h1 {{
            font-size: 24px;
            color: #1f6feb;
            margin: 0;
        }}
        
        .header-meta {{
            text-align: right;
            font-size: 12px;
            color: #57606a;
        }}
        
        .risk-gauge-section {{
            display: flex;
            align-items: center;
            gap: 20px;
            background: #f6f8fa;
            padding: 16px;
            border-radius: 6px;
            margin-bottom: 12px;
        }}
        
        .gauge {{
            width: 120px;
            height: 120px;
            border-radius: 50%;
            background: conic-gradient(
                {risk_color} 0deg,
                {risk_color} {risk_score * 3.6}deg,
                #e5e7eb {risk_score * 3.6}deg,
                #e5e7eb 360deg
            );
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }}
        
        .gauge-inner {{
            width: 110px;
            height: 110px;
            border-radius: 50%;
            background: white;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            font-size: 32px;
            font-weight: bold;
            color: {risk_color};
        }}
        
        .gauge-label {{
            font-size: 11px;
            color: #57606a;
        }}
        
        .risk-info {{
            flex: 1;
        }}
        
        .risk-info h3 {{
            font-size: 16px;
            color: {risk_color};
            margin: 0 0 4px 0;
        }}
        
        .risk-level {{
            font-size: 14px;
            font-weight: 600;
            color: #24292f;
            margin-bottom: 8px;
        }}
        
        .risk-description {{
            font-size: 13px;
            color: #57606a;
            line-height: 1.3;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr 1fr;
            gap: 12px;
            margin-bottom: 12px;
        }}
        
        .metric-card {{
            background: #f6f8fa;
            padding: 12px;
            border-radius: 6px;
            border: 1px solid #d0d7de;
            text-align: center;
        }}
        
        .metric-value {{
            font-size: 20px;
            font-weight: bold;
            color: #1f6feb;
            line-height: 1.2;
        }}
        
        .metric-label {{
            font-size: 11px;
            color: #57606a;
            margin-top: 4px;
        }}
        
        .section {{
            margin-bottom: 12px;
        }}
        
        .section-title {{
            font-size: 14px;
            font-weight: 600;
            color: #24292f;
            border-bottom: 1px solid #d0d7de;
            padding-bottom: 6px;
            margin-bottom: 8px;
        }}
        
        .findings-list {{
            display: flex;
            flex-direction: column;
            gap: 6px;
            font-size: 12px;
        }}
        
        .finding-item {{
            display: flex;
            justify-content: space-between;
            padding: 6px;
            background: #f6f8fa;
            border-left: 3px solid {risk_color};
            border-radius: 2px;
        }}
        
        .finding-title {{
            flex: 1;
            font-weight: 500;
            color: #24292f;
        }}
        
        .finding-severity {{
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 10px;
            font-weight: 600;
            white-space: nowrap;
            margin-left: 8px;
        }}
        
        .sev-critical {{ background: #cf222e; color: white; }}
        .sev-high {{ background: #f0883e; color: white; }}
        .sev-medium {{ background: #d29922; color: white; }}
        .sev-low {{ background: #3fb950; color: white; }}
        
        .compliance-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            font-size: 12px;
        }}
        
        .compliance-item {{
            display: flex;
            justify-content: space-between;
            padding: 6px;
            background: #f6f8fa;
            border-radius: 4px;
        }}
        
        .compliance-category {{
            font-weight: 500;
            color: #24292f;
        }}
        
        .compliance-percent {{
            color: #1f6feb;
            font-weight: 600;
        }}
        
        .footer {{
            font-size: 10px;
            color: #57606a;
            border-top: 1px solid #d0d7de;
            padding-top: 8px;
            margin-top: auto;
            text-align: right;
        }}
        
        .empty-state {{
            text-align: center;
            color: #57606a;
            font-size: 12px;
            padding: 8px;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="page">
        <div class="header">
            <div>
                <h1>🛡️ Executive Security Summary</h1>
            </div>
            <div class="header-meta">
                <div><strong>Report Date:</strong> {datetime.fromisoformat(self.timestamp).strftime('%Y-%m-%d %H:%M:%S')}</div>
                <div style="margin-top: 4px;"><strong>Risk Level:</strong> <span style="color: {risk_color}; font-weight: 600;">{risk_level}</span></div>
            </div>
        </div>
        
        <!-- Risk Gauge Section -->
        <div class="risk-gauge-section">
            <div class="gauge">
                <div class="gauge-inner">
                    <div>{risk_score}</div>
                    <div class="gauge-label">/ 100</div>
                </div>
            </div>
            <div class="risk-info">
                <h3>Overall Risk Score: {risk_score}</h3>
                <div class="risk-level">{risk_level} Risk</div>
                <div class="risk-description">
                    {self._get_risk_description(risk_score)}
                </div>
            </div>
        </div>
        
        <!-- Key Metrics -->
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">{metrics['total_findings']}</div>
                <div class="metric-label">Total Findings</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" style="color: #cf222e;">{metrics['critical_count']}</div>
                <div class="metric-label">Critical</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" style="color: #f0883e;">{metrics['high_count']}</div>
                <div class="metric-label">High</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" style="color: #3fb950;">{metrics['open_ports']}</div>
                <div class="metric-label">Open Ports</div>
            </div>
        </div>
        
        <!-- Top Findings -->
        <div class="section">
            <div class="section-title">🔴 Top Critical Findings</div>
            <div class="findings-list">
                {self._render_findings_html(top_findings)}
            </div>
        </div>
        
        <!-- Compliance Status -->
        <div class="section">
            <div class="section-title">📋 OWASP Top 10 Coverage</div>
            <div class="compliance-grid">
                {self._render_compliance_html(compliance)}
            </div>
        </div>
        
        <!-- Remediation Roadmap -->
        <div class="section">
            <div class="section-title">🔧 Quick Win Remediation Items</div>
            <div class="findings-list">
                {self._render_roadmap_html(roadmap)}
            </div>
        </div>
        
        <div class="footer">
            Generated: {self.timestamp} | VAPT Toolkit Executive Report
        </div>
    </div>
</body>
</html>"""
        return html

    def _get_risk_description(self, risk_score: int) -> str:
        """Get risk description based on score."""
        if risk_score >= 80:
            return "Critical risk - immediate action required. Prioritize remediation of critical vulnerabilities."
        elif risk_score >= 60:
            return "High risk - strong recommendation for immediate remediation planning and execution."
        elif risk_score >= 40:
            return "Medium risk - develop remediation plan with clear timelines and resource allocation."
        elif risk_score >= 20:
            return "Low risk - monitor and maintain current security posture with regular assessments."
        else:
            return "Minimal risk - continue current security practices with periodic reviews."

    def _render_findings_html(self, findings: List[Dict[str, Any]]) -> str:
        """Render top findings as HTML."""
        if not findings:
            return '<div class="empty-state">No critical findings detected</div>'

        html = ""
        for idx, finding in enumerate(findings[:5], 1):
            severity = finding.get("severity", "Low")
            severity_class = f"sev-{severity.lower()}"
            title = finding.get("title", "Unknown")[:45]
            html += f"""
            <div class="finding-item">
                <span class="finding-title">{idx}. {title}</span>
                <span class="finding-severity {severity_class}">{severity}</span>
            </div>
            """
        return html

    def _render_compliance_html(self, compliance: Dict[str, float]) -> str:
        """Render compliance status as HTML."""
        if not compliance:
            return '<div class="empty-state" style="grid-column: 1/-1;">No OWASP categories detected</div>'

        html = ""
        for category, percent in sorted(compliance.items())[:8]:
            cat_short = category.split(":")[0].strip()
            html += f"""
            <div class="compliance-item">
                <span class="compliance-category">{cat_short}</span>
                <span class="compliance-percent">{percent:.0f}%</span>
            </div>
            """
        return html

    def _render_roadmap_html(self, roadmap: List[Dict[str, Any]]) -> str:
        """Render remediation roadmap as HTML."""
        if not roadmap:
            return '<div class="empty-state">No remediation items available</div>'

        html = ""
        for item in roadmap[:3]:
            severity = item.get("severity", "Low")
            severity_class = f"sev-{severity.lower()}"
            title = item.get("title", "Unknown")[:40]
            html += f"""
            <div class="finding-item">
                <span class="finding-title">• {title}</span>
                <span class="finding-severity {severity_class}">{severity}</span>
            </div>
            """
        return html

    def get_summary_data(self) -> Dict[str, Any]:
        """Get structured summary data for API responses."""
        risk_score = self._calculate_risk_score()
        return {
            "risk_score": risk_score,
            "risk_level": self._get_risk_level(risk_score),
            "key_findings": self._get_top_findings(limit=5),
            "compliance_status": self._calculate_compliance_coverage(),
            "remediation_roadmap": self._get_remediation_roadmap(),
            "metrics": self._get_key_metrics(),
            "timestamp": self.timestamp,
        }

    def _get_risk_level(self, score: int) -> str:
        """Get risk level string."""
        if score >= 66:
            return "Critical"
        elif score >= 33:
            return "High"
        else:
            return "Low"
