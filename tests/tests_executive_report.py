"""Tests for Executive Report Generation."""

import json
import pytest
from datetime import datetime
from io import BytesIO
from scanner.reporters.executive_reporter import ExecutiveReporter
from scanner.reporters.pdf_executive import ExecutivePDFGenerator


# ── Test Fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def sample_scan_result():
    """Sample scan result with various findings."""
    return {
        "web_vulnerabilities": {
            "findings": [
                {
                    "type": "XSS",
                    "title": "Stored XSS in Comment Field",
                    "severity": "Critical",
                    "description": "User input is not properly sanitized",
                    "owasp_category": "A07:2021",
                    "cvss_score": 9.2,
                },
                {
                    "type": "SQL Injection",
                    "title": "SQL Injection in Login Form",
                    "severity": "Critical",
                    "description": "Parameterized queries not used",
                    "owasp_category": "A03:2021",
                    "cvss_score": 8.9,
                },
                {
                    "type": "CSRF",
                    "title": "Missing CSRF Token",
                    "severity": "High",
                    "description": "State-changing operations lack CSRF protection",
                    "owasp_category": "A01:2021",
                    "cvss_score": 7.5,
                },
                {
                    "type": "Authentication",
                    "title": "Weak Password Policy",
                    "severity": "Medium",
                    "description": "Passwords can be as short as 4 characters",
                    "owasp_category": "A07:2021",
                    "cvss_score": 5.3,
                },
                {
                    "type": "Information Disclosure",
                    "title": "Debug Mode Enabled",
                    "severity": "Low",
                    "description": "Application running in debug mode",
                    "owasp_category": "A05:2021",
                    "cvss_score": 2.1,
                },
            ],
            "total_findings": 5,
        },
        "cve": {
            "total_cves": 3,
            "correlations": [
                {
                    "service": "Apache",
                    "version": "2.4.49",
                    "cves": [
                        {
                            "id": "CVE-2021-41773",
                            "severity": "Critical",
                            "description": "Path traversal vulnerability",
                            "cvss_score": 9.8,
                        }
                    ],
                },
                {
                    "service": "OpenSSL",
                    "version": "1.1.1a",
                    "cves": [
                        {
                            "id": "CVE-2020-1971",
                            "severity": "High",
                            "description": "Certificate verification issue",
                            "cvss_score": 7.5,
                        }
                    ],
                },
            ],
        },
        "ports": {
            "open_ports": [
                {"port": 80, "service": "HTTP", "version": "Apache 2.4.49"},
                {"port": 443, "service": "HTTPS", "version": "Apache 2.4.49"},
                {"port": 22, "service": "SSH", "version": "OpenSSH 7.4p1"},
            ]
        },
    }


@pytest.fixture
def empty_scan_result():
    """Empty scan result with no findings."""
    return {
        "web_vulnerabilities": {"findings": [], "total_findings": 0},
        "cve": {"total_cves": 0, "correlations": []},
        "ports": {"open_ports": []},
    }


@pytest.fixture
def historical_scans():
    """Historical scan results for trend analysis."""
    return [
        {
            "timestamp": "2024-01-01T10:00:00",
            "results": {
                "web_vulnerabilities": {
                    "findings": [
                        {"severity": "High", "title": "Old XSS"},
                    ]
                },
                "cve": {"total_cves": 1, "correlations": []},
                "ports": {"open_ports": [{"port": 80}]},
            },
        },
        {
            "timestamp": "2024-01-08T10:00:00",
            "results": {
                "web_vulnerabilities": {
                    "findings": [
                        {"severity": "High", "title": "Old XSS"},
                        {"severity": "Medium", "title": "New CSRF"},
                    ]
                },
                "cve": {"total_cves": 1, "correlations": []},
                "ports": {"open_ports": [{"port": 80}]},
            },
        },
    ]


# ── Risk Score Tests ──────────────────────────────────────────────────────────

def test_calculate_risk_score_with_critical_findings(sample_scan_result):
    """Test risk score calculation with critical findings."""
    reporter = ExecutiveReporter(sample_scan_result)
    risk_score = reporter._calculate_risk_score()
    assert 50 <= risk_score <= 100, "Risk score with critical findings should be high"


def test_calculate_risk_score_no_findings(empty_scan_result):
    """Test risk score with no findings."""
    reporter = ExecutiveReporter(empty_scan_result)
    risk_score = reporter._calculate_risk_score()
    assert risk_score == 0, "Risk score with no findings should be 0"


def test_calculate_risk_score_range(sample_scan_result):
    """Test that risk score is always 0-100."""
    reporter = ExecutiveReporter(sample_scan_result)
    risk_score = reporter._calculate_risk_score()
    assert 0 <= risk_score <= 100, "Risk score must be between 0 and 100"


# ── Findings Tests ────────────────────────────────────────────────────────────

def test_get_all_findings(sample_scan_result):
    """Test extraction of all findings."""
    reporter = ExecutiveReporter(sample_scan_result)
    findings = reporter._get_all_findings()
    assert len(findings) >= 5, "Should extract all web findings"


def test_get_top_findings(sample_scan_result):
    """Test extraction of top critical findings."""
    reporter = ExecutiveReporter(sample_scan_result)
    top_findings = reporter._get_top_findings(limit=3)
    assert len(top_findings) == 3, "Should return exactly 3 findings"
    assert top_findings[0].get("severity") in ["Critical", "High"], "First finding should be critical/high"


def test_get_top_findings_sorted(sample_scan_result):
    """Test that top findings are sorted by severity."""
    reporter = ExecutiveReporter(sample_scan_result)
    top_findings = reporter._get_top_findings(limit=10)
    
    severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    for i in range(len(top_findings) - 1):
        current = severity_order.get(top_findings[i].get("severity", "Low"), 4)
        next_item = severity_order.get(top_findings[i + 1].get("severity", "Low"), 4)
        assert current <= next_item, "Findings should be sorted by severity (critical first)"


# ── Compliance Tests ──────────────────────────────────────────────────────────

def test_calculate_compliance_coverage(sample_scan_result):
    """Test OWASP Top 10 coverage calculation."""
    reporter = ExecutiveReporter(sample_scan_result)
    compliance = reporter._calculate_compliance_coverage()
    
    assert isinstance(compliance, dict), "Compliance should be a dict"
    assert len(compliance) > 0, "Should have at least one OWASP category"
    
    # Check that percentages sum to ~100%
    total_percent = sum(compliance.values())
    assert 90 <= total_percent <= 110, f"Compliance percentages should sum to ~100, got {total_percent}"


def test_compliance_coverage_no_findings(empty_scan_result):
    """Test compliance coverage with no findings."""
    reporter = ExecutiveReporter(empty_scan_result)
    compliance = reporter._calculate_compliance_coverage()
    assert compliance == {}, "Compliance with no findings should be empty"


# ── Remediation Roadmap Tests ─────────────────────────────────────────────────

def test_get_remediation_roadmap(sample_scan_result):
    """Test remediation roadmap generation."""
    reporter = ExecutiveReporter(sample_scan_result)
    roadmap = reporter._get_remediation_roadmap()
    
    assert isinstance(roadmap, list), "Roadmap should be a list"
    assert len(roadmap) > 0, "Should have at least one remediation item"
    assert all("title" in item for item in roadmap), "All items should have title"
    assert all("ratio" in item for item in roadmap), "All items should have impact/effort ratio"


def test_remediation_roadmap_sorted(sample_scan_result):
    """Test that remediation items are sorted by impact/effort ratio."""
    reporter = ExecutiveReporter(sample_scan_result)
    roadmap = reporter._get_remediation_roadmap()
    
    for i in range(len(roadmap) - 1):
        assert roadmap[i]["ratio"] >= roadmap[i + 1]["ratio"], "Roadmap should be sorted by ratio (quick wins first)"


# ── Metrics Tests ─────────────────────────────────────────────────────────────

def test_get_key_metrics(sample_scan_result):
    """Test key metrics calculation."""
    reporter = ExecutiveReporter(sample_scan_result)
    metrics = reporter._get_key_metrics()
    
    assert metrics["total_findings"] > 0, "Should have findings"
    assert metrics["critical_count"] > 0, "Should have critical findings"
    assert metrics["open_ports"] > 0, "Should have open ports"
    assert metrics["total_cves"] > 0, "Should have CVEs"


def test_key_metrics_structure(sample_scan_result):
    """Test that metrics have required fields."""
    reporter = ExecutiveReporter(sample_scan_result)
    metrics = reporter._get_key_metrics()
    
    required_fields = ["total_findings", "critical_count", "high_count", "medium_count", "low_count", "open_ports", "total_cves"]
    for field in required_fields:
        assert field in metrics, f"Metrics should have {field}"


# ── Risk Description Tests ────────────────────────────────────────────────────

def test_risk_description_critical(sample_scan_result):
    """Test risk description for critical risk."""
    reporter = ExecutiveReporter(sample_scan_result)
    desc = reporter._get_risk_description(80)
    assert "Critical" in desc or "critical" in desc.lower(), "Should mention critical risk"


def test_risk_description_ranges():
    """Test risk descriptions for different score ranges."""
    reporter = ExecutiveReporter({})
    
    critical_desc = reporter._get_risk_description(80)
    assert "immediate" in critical_desc.lower(), "Critical should mention immediate action"
    
    high_desc = reporter._get_risk_description(60)
    assert "high" in high_desc.lower() or "remediation" in high_desc.lower(), "High should mention high risk"
    
    low_desc = reporter._get_risk_description(10)
    assert "low" in low_desc.lower() or "minimal" in low_desc.lower(), "Low should mention low risk"


# ── HTML Report Tests ─────────────────────────────────────────────────────────

def test_generate_html_returns_string(sample_scan_result):
    """Test that HTML report is generated as string."""
    reporter = ExecutiveReporter(sample_scan_result)
    html = reporter.generate_html()
    
    assert isinstance(html, str), "HTML report should be a string"
    assert len(html) > 0, "HTML report should not be empty"


def test_html_contains_required_elements(sample_scan_result):
    """Test that HTML report contains required elements."""
    reporter = ExecutiveReporter(sample_scan_result)
    html = reporter.generate_html()
    
    required_elements = [
        "Executive Security Summary",
        "Risk Score",
        "Total Findings",
        "Critical",
        "OWASP",
        "Remediation",
    ]
    
    for element in required_elements:
        assert element in html, f"HTML should contain {element}"


def test_html_is_valid_markup(sample_scan_result):
    """Test that HTML is valid markup."""
    reporter = ExecutiveReporter(sample_scan_result)
    html = reporter.generate_html()
    
    assert html.startswith("<!DOCTYPE html>"), "HTML should start with DOCTYPE"
    assert html.count("<html") == html.count("</html>"), "HTML tags should be balanced"
    assert html.count("<body") == html.count("</body>"), "Body tags should be balanced"


def test_html_includes_risk_score(sample_scan_result):
    """Test that HTML includes risk score."""
    reporter = ExecutiveReporter(sample_scan_result)
    risk_score = reporter._calculate_risk_score()
    html = reporter.generate_html()
    
    assert str(risk_score) in html, f"HTML should include risk score {risk_score}"


# ── Summary Data Tests ────────────────────────────────────────────────────────

def test_get_summary_data(sample_scan_result):
    """Test summary data generation."""
    reporter = ExecutiveReporter(sample_scan_result)
    summary = reporter.get_summary_data()
    
    assert isinstance(summary, dict), "Summary should be a dict"
    assert "risk_score" in summary, "Summary should have risk_score"
    assert "risk_level" in summary, "Summary should have risk_level"
    assert "key_findings" in summary, "Summary should have key_findings"
    assert "compliance_status" in summary, "Summary should have compliance_status"
    assert "remediation_roadmap" in summary, "Summary should have remediation_roadmap"
    assert "metrics" in summary, "Summary should have metrics"
    assert "timestamp" in summary, "Summary should have timestamp"


def test_summary_data_risk_level(sample_scan_result):
    """Test that risk level matches risk score."""
    reporter = ExecutiveReporter(sample_scan_result)
    summary = reporter.get_summary_data()
    
    risk_score = summary["risk_score"]
    risk_level = summary["risk_level"]
    
    if risk_score >= 66:
        assert risk_level == "Critical", "Risk score >= 66 should be Critical"
    elif risk_score >= 33:
        assert risk_level == "High", "Risk score 33-65 should be High"
    else:
        assert risk_level == "Low", "Risk score < 33 should be Low"


# ── PDF Generation Tests ──────────────────────────────────────────────────────

def test_pdf_generation(sample_scan_result):
    """Test PDF generation produces BytesIO object."""
    reporter = ExecutiveReporter(sample_scan_result)
    summary = reporter.get_summary_data()
    
    pdf_gen = ExecutivePDFGenerator(summary)
    pdf_buffer = pdf_gen.generate()
    
    assert isinstance(pdf_buffer, BytesIO), "PDF should be BytesIO object"
    assert pdf_buffer.getvalue(), "PDF should have content"
    assert pdf_buffer.getvalue().startswith(b"%PDF"), "PDF should start with PDF magic bytes"


def test_pdf_buffer_seekable(sample_scan_result):
    """Test that PDF buffer is properly seekable."""
    reporter = ExecutiveReporter(sample_scan_result)
    summary = reporter.get_summary_data()
    
    pdf_gen = ExecutivePDFGenerator(summary)
    pdf_buffer = pdf_gen.generate()
    
    # Should be at end of buffer after generation
    assert pdf_buffer.tell() == 0, "PDF buffer should be seeked to start"
    
    # Should be readable
    content = pdf_buffer.read()
    assert len(content) > 0, "PDF buffer should be readable"


# ── Integration Tests ─────────────────────────────────────────────────────────

def test_full_report_generation_flow(sample_scan_result):
    """Test full report generation flow (HTML + PDF)."""
    reporter = ExecutiveReporter(sample_scan_result)
    
    # Generate HTML
    html = reporter.generate_html()
    assert html, "HTML should be generated"
    
    # Generate summary data
    summary = reporter.get_summary_data()
    assert summary, "Summary should be generated"
    
    # Generate PDF
    pdf_gen = ExecutivePDFGenerator(summary)
    pdf_buffer = pdf_gen.generate()
    assert pdf_buffer, "PDF should be generated"


def test_report_with_historical_data(sample_scan_result, historical_scans):
    """Test report generation with historical data for trends."""
    reporter = ExecutiveReporter(sample_scan_result, historical_scans=historical_scans)
    trend = reporter._calculate_risk_trend()
    
    assert isinstance(trend, list), "Trend should be a list"
    # Trend may be empty if historical scans don't have proper structure


# ── Edge Cases ────────────────────────────────────────────────────────────────

def test_report_with_missing_fields(empty_scan_result):
    """Test report generation with missing fields."""
    reporter = ExecutiveReporter(empty_scan_result)
    summary = reporter.get_summary_data()
    
    assert summary is not None, "Should handle missing fields gracefully"
    assert summary["risk_score"] == 0, "Risk score should be 0 for empty result"


def test_report_with_malformed_findings():
    """Test report generation with malformed findings."""
    result = {
        "web_vulnerabilities": {
            "findings": [
                {},  # Empty finding
                {"severity": "Critical"},  # Missing title
                {"title": "Test", "severity": "Invalid"},  # Invalid severity
            ],
            "total_findings": 3,
        },
        "cve": {"total_cves": 0, "correlations": []},
        "ports": {"open_ports": []},
    }
    
    reporter = ExecutiveReporter(result)
    findings = reporter._get_all_findings()
    assert isinstance(findings, list), "Should handle malformed findings"


def test_large_findings_list():
    """Test report generation with many findings."""
    result = {
        "web_vulnerabilities": {
            "findings": [
                {"severity": f"{'Critical' if i % 4 == 0 else 'High' if i % 4 == 1 else 'Medium' if i % 4 == 2 else 'Low'}",
                 "title": f"Vulnerability {i}",
                 "cvss_score": 7.5}
                for i in range(100)
            ],
            "total_findings": 100,
        },
        "cve": {"total_cves": 50, "correlations": []},
        "ports": {"open_ports": [{"port": i} for i in range(1000, 1010)]},
    }
    
    reporter = ExecutiveReporter(result)
    findings = reporter._get_all_findings()
    assert len(findings) == 100, "Should handle large findings lists"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
