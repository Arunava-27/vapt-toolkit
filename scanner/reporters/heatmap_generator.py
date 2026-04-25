"""Heat Map Generator for Risk Visualization across targets, time, and severity."""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict
from enum import Enum


class SeverityLevel(Enum):
    """Severity levels for vulnerabilities."""
    CRITICAL = 4
    HIGH = 3
    MEDIUM = 2
    LOW = 1
    INFO = 0


class HeatMapGenerator:
    """Generates heat map data for risk visualization."""

    # Risk color mapping
    RISK_COLORS = {
        "critical": "#cf222e",  # Red
        "high": "#f0883e",      # Orange
        "medium": "#d29922",    # Yellow
        "low": "#3fb950",       # Green
        "info": "#0969da",      # Blue
        "none": "#eaeaea",      # Light gray
    }

    # Severity order
    SEVERITY_ORDER = {
        "Critical": 4,
        "High": 3,
        "Medium": 2,
        "Low": 1,
        "Info": 0,
    }

    def __init__(self):
        """Initialize heat map generator."""
        pass

    def generate_by_target(
        self,
        scans: List[Dict[str, Any]],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate heat map data by target and severity.

        Args:
            scans: List of scan result dictionaries
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)

        Returns:
            Heat map matrix: {
                "matrix": [[risk_value, ...], ...],
                "targets": ["target1", "target2", ...],
                "severities": ["Critical", "High", "Medium", "Low"],
                "data": [[{"target": ..., "severity": ..., "count": ..., "color": ...}, ...], ...]
            }
        """
        # Filter scans by date
        filtered_scans = self._filter_scans_by_date(scans, start_date, end_date)

        # Aggregate vulnerabilities by target and severity
        target_severity_map = defaultdict(lambda: defaultdict(int))

        for scan in filtered_scans:
            target = scan.get("target", "Unknown")
            findings = self._extract_findings(scan)

            for finding in findings:
                severity = finding.get("severity", "Info")
                target_severity_map[target][severity] += 1

        # Get unique targets and severities
        targets = sorted(target_severity_map.keys())
        severities = ["Critical", "High", "Medium", "Low", "Info"]

        # Build matrix and data structures
        matrix = []
        data = []

        for target in targets:
            row = []
            row_data = []

            for severity in severities:
                count = target_severity_map[target][severity]
                risk_value = self._calculate_risk_value(count, severity)
                color = self.RISK_COLORS.get(severity.lower(), self.RISK_COLORS["none"])

                row.append(risk_value)
                row_data.append({
                    "target": target,
                    "severity": severity,
                    "count": count,
                    "color": color,
                    "value": risk_value,
                })

            matrix.append(row)
            data.append(row_data)

        return {
            "type": "by_target",
            "matrix": matrix,
            "targets": targets,
            "severities": severities,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }

    def generate_by_time(
        self,
        scans: List[Dict[str, Any]],
        target: Optional[str] = None,
        period: str = "week",
    ) -> Dict[str, Any]:
        """
        Generate time-series heat map data.

        Args:
            scans: List of scan result dictionaries
            target: Optional target filter
            period: "day", "week", "month", "quarter", "year"

        Returns:
            Time-series heat map: {
                "matrix": [[risk_value, ...], ...],
                "time_periods": ["2024-01-01", ...],
                "severities": ["Critical", "High", "Medium", "Low"],
                "data": [[{...}, ...], ...]
            }
        """
        # Filter by target if provided
        filtered_scans = scans
        if target:
            filtered_scans = [s for s in scans if s.get("target") == target]

        # Group by time period
        period_data = self._group_by_period(filtered_scans, period)

        # Get time periods and severities
        time_periods = sorted(period_data.keys())
        severities = ["Critical", "High", "Medium", "Low", "Info"]

        # Build matrix and data structures
        matrix = []
        data = []

        for severity in severities:
            row = []
            row_data = []

            for period_key in time_periods:
                severity_map = period_data[period_key]
                count = severity_map.get(severity, 0)
                risk_value = self._calculate_risk_value(count, severity)
                color = self.RISK_COLORS.get(severity.lower(), self.RISK_COLORS["none"])

                row.append(risk_value)
                row_data.append({
                    "period": period_key,
                    "severity": severity,
                    "count": count,
                    "color": color,
                    "value": risk_value,
                })

            matrix.append(row)
            data.append(row_data)

        return {
            "type": "by_time",
            "matrix": matrix,
            "time_periods": time_periods,
            "severities": severities,
            "data": data,
            "period": period,
            "target": target,
            "timestamp": datetime.now().isoformat(),
        }

    def generate_by_severity(
        self,
        findings: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Generate severity distribution heat map.

        Args:
            findings: List of vulnerability findings

        Returns:
            Severity distribution: {
                "distribution": {"Critical": 5, "High": 12, ...},
                "percentages": {"Critical": 10.4, "High": 25.0, ...},
                "total": 48,
                "risk_score": 75
            }
        """
        distribution = defaultdict(int)
        total = len(findings)

        for finding in findings:
            severity = finding.get("severity", "Info")
            distribution[severity] += 1

        # Calculate percentages
        percentages = {}
        for severity, count in distribution.items():
            percentages[severity] = (count / total * 100) if total > 0 else 0

        # Calculate overall risk score
        risk_score = self._calculate_overall_risk_score(findings)

        return {
            "type": "by_severity",
            "distribution": dict(distribution),
            "percentages": percentages,
            "total": total,
            "risk_score": risk_score,
            "colors": {
                severity: self.RISK_COLORS.get(severity.lower(), self.RISK_COLORS["none"])
                for severity in distribution.keys()
            },
            "timestamp": datetime.now().isoformat(),
        }

    def generate_by_vulnerability_type(
        self,
        scans: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Generate heat map by vulnerability type and severity.

        Args:
            scans: List of scan result dictionaries

        Returns:
            Vulnerability type heat map
        """
        type_severity_map = defaultdict(lambda: defaultdict(int))

        for scan in scans:
            findings = self._extract_findings(scan)

            for finding in findings:
                vuln_type = finding.get("type", "Unknown")
                severity = finding.get("severity", "Info")
                type_severity_map[vuln_type][severity] += 1

        # Get types and severities
        vuln_types = sorted(type_severity_map.keys())
        severities = ["Critical", "High", "Medium", "Low", "Info"]

        # Build matrix and data
        matrix = []
        data = []

        for vuln_type in vuln_types:
            row = []
            row_data = []

            for severity in severities:
                count = type_severity_map[vuln_type][severity]
                risk_value = self._calculate_risk_value(count, severity)
                color = self.RISK_COLORS.get(severity.lower(), self.RISK_COLORS["none"])

                row.append(risk_value)
                row_data.append({
                    "type": vuln_type,
                    "severity": severity,
                    "count": count,
                    "color": color,
                    "value": risk_value,
                })

            matrix.append(row)
            data.append(row_data)

        return {
            "type": "by_vulnerability_type",
            "matrix": matrix,
            "vulnerability_types": vuln_types,
            "severities": severities,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }

    # ─── Private Helper Methods ────────────────────────────────────────────

    def _extract_findings(self, scan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract all findings from a scan result."""
        findings = []

        # Web vulnerabilities
        web_vulns = scan.get("web_vulnerabilities", {})
        if isinstance(web_vulns, dict):
            findings.extend(web_vulns.get("findings", []))

        # CVE findings
        cve_data = scan.get("cve", {})
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

    def _filter_scans_by_date(
        self,
        scans: List[Dict[str, Any]],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Filter scans by date range."""
        filtered = scans

        if start_date:
            start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            filtered = [
                s for s in filtered
                if self._parse_timestamp(s.get("timestamp") or s.get("created_at")) >= start
            ]

        if end_date:
            end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            filtered = [
                s for s in filtered
                if self._parse_timestamp(s.get("timestamp") or s.get("created_at")) <= end
            ]

        return filtered

    def _group_by_period(
        self,
        scans: List[Dict[str, Any]],
        period: str = "week",
    ) -> Dict[str, Dict[str, int]]:
        """Group findings by time period."""
        period_map = defaultdict(lambda: defaultdict(int))

        for scan in scans:
            timestamp = self._parse_timestamp(scan.get("timestamp") or scan.get("created_at"))
            period_key = self._get_period_key(timestamp, period)

            findings = self._extract_findings(scan)
            for finding in findings:
                severity = finding.get("severity", "Info")
                period_map[period_key][severity] += 1

        return period_map

    def _get_period_key(self, timestamp: datetime, period: str) -> str:
        """Get period key for a timestamp."""
        if period == "day":
            return timestamp.strftime("%Y-%m-%d")
        elif period == "week":
            year, week, _ = timestamp.isocalendar()
            return f"{year}-W{week:02d}"
        elif period == "month":
            return timestamp.strftime("%Y-%m")
        elif period == "quarter":
            quarter = (timestamp.month - 1) // 3 + 1
            return f"{timestamp.year}-Q{quarter}"
        elif period == "year":
            return str(timestamp.year)
        else:
            return timestamp.strftime("%Y-%m-%d")

    def _parse_timestamp(self, timestamp_str: Optional[str]) -> datetime:
        """Parse timestamp string to datetime."""
        if not timestamp_str:
            return datetime.now()

        try:
            # Try ISO format
            if timestamp_str.endswith("Z"):
                return datetime.fromisoformat(timestamp_str[:-1] + "+00:00")
            else:
                return datetime.fromisoformat(timestamp_str)
        except (ValueError, AttributeError):
            # Fallback to current time
            return datetime.now()

    def _calculate_risk_value(self, count: int, severity: str) -> float:
        """Calculate risk value for a cell (0-100)."""
        severity_weight = self.SEVERITY_ORDER.get(severity, 0)

        # Base calculation: min severity is 0, max is 100
        # Formula: (count * severity_weight) with logarithmic scaling
        if count == 0:
            return 0.0

        # Logarithmic scaling to prevent overflow
        risk = min(100, (count * severity_weight * 10) / 100)
        return round(risk, 2)

    def _calculate_overall_risk_score(self, findings: List[Dict[str, Any]]) -> int:
        """Calculate overall risk score from findings (0-100)."""
        if not findings:
            return 0

        total_score = 0
        weights = {
            "Critical": 100,
            "High": 75,
            "Medium": 50,
            "Low": 25,
            "Info": 10,
        }

        for finding in findings:
            severity = finding.get("severity", "Info")
            weight = weights.get(severity, 10)
            total_score += weight

        # Normalize to 0-100
        avg_score = total_score / len(findings)
        return min(100, int(avg_score))
