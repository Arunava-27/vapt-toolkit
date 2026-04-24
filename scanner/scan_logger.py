"""
Request/response logging for active scans.

Maintains audit trail of all probes, payloads, and responses
for traceability and evidence collection.
"""
import json
from datetime import datetime
from typing import Any, Optional


class ScanLogger:
    """Log all scan activity for active scans."""
    
    def __init__(self):
        self.logs: list[dict] = []
    
    def log_request(
        self,
        module: str,
        method: str,
        url: str,
        headers: dict = None,
        data: str = None,
        payload: str = None,
        tags: list[str] = None,
    ) -> None:
        """Log an outgoing request."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "request",
            "module": module,
            "method": method,
            "url": url,
            "headers": headers or {},
            "data": data,
            "payload": payload,
            "tags": tags or [],
        }
        self.logs.append(entry)
    
    def log_response(
        self,
        status: Optional[int],
        headers: dict = None,
        body: str = None,
        response_time_ms: float = None,
        finding: Optional[str] = None,
        tags: list[str] = None,
    ) -> None:
        """Log an incoming response."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "response",
            "status": status,
            "headers": headers or {},
            "body_preview": (body[:500] if body else None),
            "body_size": len(body) if body else 0,
            "response_time_ms": response_time_ms,
            "finding": finding,
            "tags": tags or [],
        }
        self.logs.append(entry)
    
    def log_finding(
        self,
        module: str,
        severity: str,
        title: str,
        description: str,
        evidence: dict = None,
        tags: list[str] = None,
    ) -> None:
        """Log a vulnerability finding."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "finding",
            "module": module,
            "severity": severity,
            "title": title,
            "description": description,
            "evidence": evidence or {},
            "tags": tags or [],
        }
        self.logs.append(entry)
    
    def log_event(
        self,
        message: str,
        event_type: str = "info",
        details: dict = None,
        tags: list[str] = None,
    ) -> None:
        """Log a general event."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": event_type,
            "message": message,
            "details": details or {},
            "tags": tags or [],
        }
        self.logs.append(entry)
    
    def get_logs(self) -> list[dict]:
        """Get all logs."""
        return self.logs
    
    def get_summary(self) -> dict:
        """Get summary statistics."""
        requests = sum(1 for l in self.logs if l.get("type") == "request")
        responses = sum(1 for l in self.logs if l.get("type") == "response")
        findings = sum(1 for l in self.logs if l.get("type") == "finding")
        
        severities = {}
        for l in self.logs:
            if l.get("type") == "finding":
                sev = l.get("severity", "unknown")
                severities[sev] = severities.get(sev, 0) + 1
        
        return {
            "total_requests": requests,
            "total_responses": responses,
            "total_findings": findings,
            "findings_by_severity": severities,
            "total_log_entries": len(self.logs),
        }
    
    def to_json(self) -> str:
        """Export logs as JSON."""
        return json.dumps(self.logs, indent=2)
