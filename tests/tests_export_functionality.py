"""
Tests for Enhanced Data Export Functionality.
Tests all export formats, filtering, and data integrity.
"""

import json
import csv
import io
from datetime import datetime
import pytest
from scanner.reporters.export_generator import ExportGenerator, ExportFormat


# Sample scan data for testing
SAMPLE_SCAN_DATA = {
    "config": {
        "target": "https://example.com",
        "recon": True,
        "ports": True,
        "web": True,
        "cve": True,
        "scan_classification": "active",
        "duration": "5m 42s",
    },
    "results": {
        "web_vulnerabilities": {
            "findings": [
                {
                    "finding_id": "1",
                    "title": "SQL Injection in Login Form",
                    "type": "sqli",
                    "severity": "critical",
                    "confidence": "high",
                    "description": "SQL injection vulnerability found in login endpoint",
                    "url": "/admin/login",
                    "evidence": "payload: ' OR '1'='1",
                    "remediation": "Use parameterized queries",
                },
                {
                    "finding_id": "2",
                    "title": "Cross-Site Scripting (XSS)",
                    "type": "xss",
                    "severity": "high",
                    "confidence": "high",
                    "description": "Stored XSS in comment section",
                    "url": "/comments",
                    "evidence": "<script>alert('XSS')</script>",
                    "remediation": "Input validation and output encoding",
                },
                {
                    "finding_id": "3",
                    "title": "Missing Security Headers",
                    "type": "headers",
                    "severity": "medium",
                    "confidence": "high",
                    "description": "Missing Content-Security-Policy header",
                    "url": "/",
                    "evidence": "Response headers missing CSP",
                    "remediation": "Add security headers",
                },
            ],
            "total_findings": 3,
        },
        "cve": {
            "correlations": [
                {
                    "service": "Apache/2.4.1",
                    "cves": [
                        {
                            "id": "CVE-2023-44487",
                            "severity": "high",
                            "cvss_score": 7.5,
                            "description": "HTTP/2 Rapid Reset vulnerability",
                        }
                    ],
                }
            ],
            "total_cves": 1,
        },
        "ports": {
            "open_ports": [
                {
                    "port": 80,
                    "protocol": "tcp",
                    "service": "http",
                    "version": "Apache/2.4.1",
                },
                {
                    "port": 443,
                    "protocol": "tcp",
                    "service": "https",
                    "version": "Apache/2.4.1",
                },
            ],
        },
    },
    "timestamp": datetime.now().isoformat(),
}


class TestExportGenerator:
    """Test suite for ExportGenerator."""

    def test_generator_initialization(self):
        """Test ExportGenerator initialization."""
        gen = ExportGenerator(SAMPLE_SCAN_DATA)
        assert gen.target == "https://example.com"
        assert gen.config["scan_classification"] == "active"
        assert len(gen.findings) > 0

    def test_findings_extraction(self):
        """Test that findings are extracted correctly."""
        gen = ExportGenerator(SAMPLE_SCAN_DATA)
        assert len(gen.findings) >= 5  # 3 web + 1 CVE + 2 open ports
        
        # Check finding types
        types = {f["type"] for f in gen.findings}
        assert "web_vulnerability" in types or "cve" in types or "open_port" in types

    def test_json_export(self):
        """Test JSON export format."""
        gen = ExportGenerator(SAMPLE_SCAN_DATA)
        json_output = gen.export_json(include_metadata=True, include_evidence=True)
        
        # Verify JSON is valid
        data = json.loads(json_output)
        assert "findings" in data
        assert "summary" in data
        assert "metadata" in data
        assert data["format"] == "json"

    def test_json_export_without_metadata(self):
        """Test JSON export without metadata."""
        gen = ExportGenerator(SAMPLE_SCAN_DATA)
        json_output = gen.export_json(include_metadata=False)
        
        data = json.loads(json_output)
        assert "metadata" not in data
        assert "findings" in data

    def test_json_export_without_evidence(self):
        """Test JSON export without evidence."""
        gen = ExportGenerator(SAMPLE_SCAN_DATA)
        json_output = gen.export_json(include_evidence=False)
        
        data = json.loads(json_output)
        # Check that evidence field is removed
        for finding in data["findings"]:
            assert "evidence" not in finding or finding.get("evidence") is None

    def test_json_export_with_severity_filter(self):
        """Test JSON export with severity filtering."""
        gen = ExportGenerator(SAMPLE_SCAN_DATA)
        json_output = gen.export_json(severity="critical")
        
        data = json.loads(json_output)
        # All findings should be critical
        for finding in data["findings"]:
            assert finding["severity"] == "critical"

    def test_csv_export(self):
        """Test CSV export format."""
        gen = ExportGenerator(SAMPLE_SCAN_DATA)
        csv_output = gen.export_csv()
        
        # Parse CSV
        reader = csv.DictReader(io.StringIO(csv_output))
        rows = list(reader)
        assert len(rows) > 0
        
        # Check headers
        assert "Title" in reader.fieldnames
        assert "Severity" in reader.fieldnames
        assert "Location" in reader.fieldnames

    def test_csv_export_content(self):
        """Test CSV export contains correct data."""
        gen = ExportGenerator(SAMPLE_SCAN_DATA)
        csv_output = gen.export_csv(include_metadata=False)
        
        reader = csv.DictReader(io.StringIO(csv_output))
        rows = list(reader)
        
        # Verify at least one finding exists
        assert len(rows) > 0
        first_row = rows[0]
        assert "Title" in first_row
        assert first_row["Title"] != ""

    def test_html_export(self):
        """Test HTML export format."""
        gen = ExportGenerator(SAMPLE_SCAN_DATA)
        html_output = gen.export_html()
        
        # Check for HTML structure
        assert "<!DOCTYPE html>" in html_output
        assert "<head>" in html_output
        assert "<body>" in html_output
        assert "VAPT Scan Report" in html_output

    def test_html_export_styling(self):
        """Test HTML export has proper styling."""
        gen = ExportGenerator(SAMPLE_SCAN_DATA)
        html_output = gen.export_html()
        
        assert "<style>" in html_output
        assert "critical" in html_output.lower()
        assert ".header" in html_output or "header" in html_output.lower()

    def test_html_export_findings(self):
        """Test HTML export includes findings."""
        gen = ExportGenerator(SAMPLE_SCAN_DATA)
        html_output = gen.export_html()
        
        # Check for findings
        assert "SQL Injection" in html_output or "findings" in html_output.lower()

    def test_markdown_export(self):
        """Test Markdown export format."""
        gen = ExportGenerator(SAMPLE_SCAN_DATA)
        md_output = gen.export_markdown()
        
        # Check for markdown elements
        assert "# VAPT Scan Report" in md_output
        assert "##" in md_output  # Headers
        assert "|" in md_output  # Tables

    def test_markdown_export_metadata(self):
        """Test Markdown export includes metadata."""
        gen = ExportGenerator(SAMPLE_SCAN_DATA)
        md_output = gen.export_markdown(include_metadata=True)
        
        assert "Target" in md_output
        assert "example.com" in md_output
        assert "Severity Summary" in md_output

    def test_markdown_export_references(self):
        """Test Markdown export includes OWASP/CWE references."""
        gen = ExportGenerator(SAMPLE_SCAN_DATA)
        md_output = gen.export_markdown()
        
        # Check for reference sections
        assert "OWASP" in md_output or "owasp" in md_output.lower()

    def test_sarif_export(self):
        """Test SARIF export format."""
        gen = ExportGenerator(SAMPLE_SCAN_DATA)
        sarif_output = gen.export_sarif()
        
        # Verify SARIF JSON is valid
        data = json.loads(sarif_output)
        assert "$schema" in data
        assert data["version"] == "2.1.0"
        assert "runs" in data

    def test_xlsx_export(self):
        """Test Excel export format."""
        gen = ExportGenerator(SAMPLE_SCAN_DATA)
        xlsx_bytes = gen.export_xlsx()
        
        # Verify it's bytes
        assert isinstance(xlsx_bytes, bytes)
        assert len(xlsx_bytes) > 0
        
        # Check for Excel file signature
        assert xlsx_bytes[:2] == b'PK'  # ZIP file signature

    def test_xlsx_export_with_evidence(self):
        """Test Excel export includes evidence."""
        gen = ExportGenerator(SAMPLE_SCAN_DATA)
        xlsx_with_evidence = gen.export_xlsx(include_evidence=True)
        xlsx_without_evidence = gen.export_xlsx(include_evidence=False)
        
        # Both should be bytes
        assert isinstance(xlsx_with_evidence, bytes)
        assert isinstance(xlsx_without_evidence, bytes)
        
        # With evidence should typically be larger or same size
        assert len(xlsx_with_evidence) >= len(xlsx_without_evidence)

    def test_export_all_formats(self):
        """Test all export formats can be generated."""
        gen = ExportGenerator(SAMPLE_SCAN_DATA)
        
        formats = [
            ExportFormat.JSON,
            ExportFormat.CSV,
            ExportFormat.HTML,
            ExportFormat.MARKDOWN,
            ExportFormat.SARIF,
            ExportFormat.XLSX,
        ]
        
        for fmt in formats:
            result = gen.export(fmt)
            assert result is not None
            if fmt != ExportFormat.XLSX:
                assert len(result) > 0

    def test_severity_filtering(self):
        """Test filtering by severity."""
        gen = ExportGenerator(SAMPLE_SCAN_DATA)
        
        # Test each severity level
        for severity in ["critical", "high", "medium", "low"]:
            filtered = gen._filter_findings(severity=severity)
            for finding in filtered:
                assert finding["severity"].lower() == severity

    def test_confidence_filtering(self):
        """Test filtering by confidence."""
        gen = ExportGenerator(SAMPLE_SCAN_DATA)
        
        for confidence in ["high", "medium", "low"]:
            filtered = gen._filter_findings(confidence=confidence)
            for finding in filtered:
                assert finding["confidence"].lower() == confidence

    def test_type_filtering(self):
        """Test filtering by type."""
        gen = ExportGenerator(SAMPLE_SCAN_DATA)
        
        filtered = gen._filter_findings(finding_type="web_vulnerability")
        for finding in filtered:
            assert finding["type"] == "web_vulnerability"

    def test_combined_filtering(self):
        """Test combined filtering."""
        gen = ExportGenerator(SAMPLE_SCAN_DATA)
        
        filtered = gen._filter_findings(
            severity="high",
            confidence="high",
            finding_type="web_vulnerability"
        )
        
        for finding in filtered:
            assert finding["severity"].lower() == "high"
            assert finding["confidence"].lower() == "high"
            assert finding["type"] == "web_vulnerability"

    def test_metadata_extraction(self):
        """Test metadata extraction."""
        gen = ExportGenerator(SAMPLE_SCAN_DATA)
        metadata = gen._get_metadata()
        
        assert metadata["target"] == "https://example.com"
        assert metadata["scan_type"] == "active"
        assert "total_findings" in metadata
        assert "findings_by_severity" in metadata

    def test_severity_summary(self):
        """Test severity summary."""
        gen = ExportGenerator(SAMPLE_SCAN_DATA)
        summary = gen._severity_summary()
        
        assert isinstance(summary, dict)
        assert all(key in summary for key in ["critical", "high", "medium", "low", "info"])

    def test_owasp_mapping(self):
        """Test OWASP mapping."""
        gen = ExportGenerator(SAMPLE_SCAN_DATA)
        
        owasp_sql = gen._get_owasp("SQL Injection test")
        assert owasp_sql is not None
        
        owasp_xss = gen._get_owasp("Cross-Site Scripting")
        assert owasp_xss is not None

    def test_cwe_mapping(self):
        """Test CWE mapping."""
        gen = ExportGenerator(SAMPLE_SCAN_DATA)
        
        cwe_sql = gen._get_cwe("SQL Injection test")
        assert cwe_sql == 89
        
        cwe_xss = gen._get_cwe("Cross-Site Scripting")
        assert cwe_xss == 79

    def test_empty_findings_export(self):
        """Test export with empty findings."""
        empty_data = {
            "config": {"target": "https://test.com"},
            "results": {
                "web_vulnerabilities": {"findings": []},
                "cve": {"correlations": []},
                "ports": {"open_ports": []},
            },
            "timestamp": datetime.now().isoformat(),
        }
        
        gen = ExportGenerator(empty_data)
        json_output = gen.export_json()
        data = json.loads(json_output)
        
        assert data["summary"]["total"] == 0

    def test_large_findings_export(self):
        """Test export with many findings."""
        large_data = SAMPLE_SCAN_DATA.copy()
        large_data["results"]["web_vulnerabilities"]["findings"] = [
            {
                "finding_id": str(i),
                "title": f"Vulnerability {i}",
                "type": "test",
                "severity": ["critical", "high", "medium", "low"][i % 4],
                "confidence": "high",
                "description": f"Test vulnerability {i}",
                "url": f"/page/{i}",
                "evidence": f"Evidence for vuln {i}",
                "remediation": "Fix it",
            }
            for i in range(100)
        ]
        
        gen = ExportGenerator(large_data)
        json_output = gen.export_json()
        data = json.loads(json_output)
        
        assert len(data["findings"]) == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
