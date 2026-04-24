"""Request/response logging for vulnerability evidence and reproducibility."""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any
import json


@dataclass
class HTTPRequest:
    """Captured HTTP request."""
    method: str
    url: str
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class HTTPResponse:
    """Captured HTTP response."""
    status_code: int
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[str] = None
    response_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class VulnerabilityFinding:
    """Web vulnerability finding with full evidence."""
    type: str  # SQLi, XSS, CSRF, IDOR, etc.
    severity: str  # Critical, High, Medium, Low
    endpoint: str
    method: str
    parameter: Optional[str] = None
    payload: Optional[str] = None
    evidence: Optional[str] = None
    request: Optional[HTTPRequest] = None
    response: Optional[HTTPResponse] = None
    reproducible: bool = True
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        if self.request:
            data["request"] = asdict(self.request)
        if self.response:
            data["response"] = asdict(self.response)
        return data


class WebVulnerabilityLogger:
    """Capture and manage vulnerability evidence."""
    
    def __init__(self, max_response_size: int = 10000):
        """
        Initialize logger.
        
        Args:
            max_response_size: Maximum response body size to capture (bytes)
        """
        self.max_response_size = max_response_size
        self.findings: list[VulnerabilityFinding] = []
    
    def log_finding(
        self,
        vuln_type: str,
        severity: str,
        endpoint: str,
        method: str = "GET",
        parameter: Optional[str] = None,
        payload: Optional[str] = None,
        evidence: Optional[str] = None,
        request: Optional[HTTPRequest] = None,
        response: Optional[HTTPResponse] = None,
        reproducible: bool = True,
    ) -> VulnerabilityFinding:
        """
        Log a vulnerability finding.
        
        Returns: VulnerabilityFinding object
        """
        finding = VulnerabilityFinding(
            type=vuln_type,
            severity=severity,
            endpoint=endpoint,
            method=method,
            parameter=parameter,
            payload=payload,
            evidence=evidence,
            request=request,
            response=response,
            reproducible=reproducible,
        )
        self.findings.append(finding)
        return finding
    
    def capture_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[str] = None,
    ) -> HTTPRequest:
        """Capture HTTP request."""
        # Sanitize sensitive headers
        safe_headers = self._sanitize_headers(headers or {})
        
        return HTTPRequest(
            method=method,
            url=url,
            headers=safe_headers,
            body=body[:500] if body else None,  # Limit request body size
        )
    
    def capture_response(
        self,
        status_code: int,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[str] = None,
        response_time: float = 0.0,
    ) -> HTTPResponse:
        """Capture HTTP response."""
        # Sanitize sensitive headers
        safe_headers = self._sanitize_headers(headers or {})
        
        # Truncate large response bodies
        safe_body = body
        if body and len(body) > self.max_response_size:
            safe_body = body[:self.max_response_size]
        
        return HTTPResponse(
            status_code=status_code,
            headers=safe_headers,
            body=safe_body,
            response_time=response_time,
        )
    
    @staticmethod
    def _sanitize_headers(headers: Dict[str, str]) -> Dict[str, str]:
        """Remove sensitive headers from logging."""
        sensitive_headers = {
            "authorization",
            "cookie",
            "x-api-key",
            "api-key",
            "token",
            "x-token",
            "password",
            "secret",
        }
        
        return {
            k: v if k.lower() not in sensitive_headers else "[REDACTED]"
            for k, v in headers.items()
        }
    
    def get_findings(self) -> list[VulnerabilityFinding]:
        """Get all findings."""
        return self.findings
    
    def get_findings_by_type(self, vuln_type: str) -> list[VulnerabilityFinding]:
        """Get findings by vulnerability type."""
        return [f for f in self.findings if f.type == vuln_type]
    
    def get_findings_by_severity(self, severity: str) -> list[VulnerabilityFinding]:
        """Get findings by severity level."""
        return [f for f in self.findings if f.severity == severity]
    
    def deduplicate(self) -> list[VulnerabilityFinding]:
        """
        Deduplicate findings (same endpoint + parameter + type).
        
        Returns: Deduplicated findings list
        """
        seen = set()
        deduplicated = []
        
        for finding in self.findings:
            # Create key from endpoint, method, parameter, and type
            key = (finding.endpoint, finding.method, finding.parameter, finding.type)
            if key not in seen:
                seen.add(key)
                deduplicated.append(finding)
        
        return deduplicated
    
    def to_json(self, deduplicate: bool = True) -> str:
        """Convert findings to JSON."""
        findings = self.deduplicate() if deduplicate else self.findings
        data = {
            "total_findings": len(findings),
            "findings": [f.to_dict() for f in findings],
        }
        return json.dumps(data, indent=2, default=str)
    
    def to_dict(self, deduplicate: bool = True) -> dict:
        """Convert findings to dictionary."""
        findings = self.deduplicate() if deduplicate else self.findings
        
        # Group by type and severity
        by_type = {}
        by_severity = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        
        for finding in findings:
            # Group by type
            if finding.type not in by_type:
                by_type[finding.type] = []
            by_type[finding.type].append(finding.to_dict())
            
            # Count by severity
            if finding.severity in by_severity:
                by_severity[finding.severity] += 1
        
        return {
            "total_findings": len(findings),
            "by_severity": by_severity,
            "by_type": by_type,
            "findings": [f.to_dict() for f in findings],
        }
    
    def clear(self):
        """Clear all findings."""
        self.findings.clear()
    
    def summary(self) -> str:
        """Get summary of findings."""
        by_type = {}
        by_severity = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        
        for finding in self.findings:
            by_type[finding.type] = by_type.get(finding.type, 0) + 1
            if finding.severity in by_severity:
                by_severity[finding.severity] += 1
        
        summary_lines = [
            f"Total findings: {len(self.findings)}",
            "By severity:",
        ]
        for severity, count in by_severity.items():
            summary_lines.append(f"  {severity}: {count}")
        
        summary_lines.append("By type:")
        for vuln_type, count in sorted(by_type.items()):
            summary_lines.append(f"  {vuln_type}: {count}")
        
        return "\n".join(summary_lines)
