"""
Tests for SARIF reporter and PR comment generator
Validates GitHub Actions CI/CD integration
"""

import json
import pytest
from datetime import datetime
from scanner.reporters.sarif_reporter import VAPTSarifReporter, create_sarif_report
from tools.pr_comment_generator import PRCommentGenerator, generate_pr_comment


class TestSARIFReporter:
    """Tests for SARIF v2.1.0 report generation."""

    @pytest.fixture
    def reporter(self):
        """Create reporter instance."""
        return VAPTSarifReporter(
            tool_version="1.0.0",
            scan_target="http://localhost:3000"
        )

    @pytest.fixture
    def sample_findings(self):
        """Sample vulnerabilities for testing."""
        return [
            {
                'type': 'SQL Injection',
                'severity': 'critical',
                'message': 'SQL Injection in user ID parameter',
                'location': '/api/users',
                'parameter': 'id',
                'evidence': 'SQL error detected in response',
                'confidence': 0.98,
                'cwe_id': 'CWE-89',
                'owasp_category': 'A03:2021 - Injection'
            },
            {
                'type': 'XSS',
                'severity': 'high',
                'message': 'Reflected XSS in search parameter',
                'location': '/api/search',
                'parameter': 'q',
                'evidence': 'Payload reflected in HTML response',
                'confidence': 0.95,
                'cwe_id': 'CWE-79',
                'owasp_category': 'A03:2021 - Injection'
            },
            {
                'type': 'Weak Security Headers',
                'severity': 'medium',
                'message': 'Missing Content-Security-Policy header',
                'location': 'HTTP Response Headers',
                'parameter': 'Content-Security-Policy',
                'evidence': 'Security header not found',
                'confidence': 1.0,
                'cwe_id': 'CWE-693',
                'owasp_category': 'A05:2021 - Security Misconfiguration'
            }
        ]

    def test_reporter_initialization(self, reporter):
        """Test reporter initializes correctly."""
        assert reporter.tool_version == "1.0.0"
        assert reporter.scan_target == "http://localhost:3000"
        assert reporter.organization == "VAPT Toolkit"
        assert reporter.run_id  # Should have UUID

    def test_sarif_schema_compliance(self, reporter, sample_findings):
        """Test SARIF output complies with v2.1.0 spec."""
        report = reporter.generate(sample_findings)

        # Check root properties
        assert report["$schema"].endswith("sarif-schema-2.1.0.json")
        assert report["version"] == "2.1.0"
        assert "runs" in report
        assert len(report["runs"]) == 1

    def test_sarif_run_structure(self, reporter, sample_findings):
        """Test SARIF run object structure."""
        report = reporter.generate(sample_findings)
        run = report["runs"][0]

        assert "tool" in run
        assert "invocation" in run
        assert "results" in run
        assert "properties" in run

    def test_tool_driver_info(self, reporter, sample_findings):
        """Test tool driver information."""
        report = reporter.generate(sample_findings)
        driver = report["runs"][0]["tool"]["driver"]

        assert driver["name"] == "VAPT Toolkit"
        assert driver["version"] == "1.0.0"
        assert driver["organization"] == "VAPT Toolkit"
        assert "rules" in driver
        assert len(driver["rules"]) > 0

    def test_rules_include_all_vulnerability_types(self, reporter):
        """Test all vulnerability types have rules."""
        report = reporter.generate([])
        rules = report["runs"][0]["tool"]["driver"]["rules"]
        rule_ids = [r["id"] for r in rules]

        expected_rule_ids = [
            "VAPT-SQL-INJECTION",
            "VAPT-XSS",
            "VAPT-CSRF",
            "VAPT-IDOR",
            "VAPT-SSRF",
            "VAPT-AUTH-WEAKNESS",
            "VAPT-WEAK-CRYPTO",
            "VAPT-SECURITY-MISCONFIGURATION",
            "VAPT-SENSITIVE-DATA",
            "VAPT-FILE-UPLOAD",
            "VAPT-BUSINESS-LOGIC",
        ]

        for rule_id in expected_rule_ids:
            assert rule_id in rule_ids, f"Missing rule: {rule_id}"

    def test_rule_structure(self, reporter):
        """Test rule has required SARIF properties."""
        report = reporter.generate([])
        rules = report["runs"][0]["tool"]["driver"]["rules"]

        for rule in rules:
            assert "id" in rule
            assert "name" in rule
            assert "shortDescription" in rule
            assert "fullDescription" in rule
            assert "defaultConfiguration" in rule
            assert "properties" in rule
            assert "cwe" in rule["properties"]
            assert "owasp" in rule["properties"]
            assert "tags" in rule["properties"]

    def test_finding_conversion_to_result(self, reporter, sample_findings):
        """Test finding is correctly converted to SARIF result."""
        report = reporter.generate(sample_findings)
        results = report["runs"][0]["results"]

        assert len(results) == 3

        # Check first result (SQL Injection - critical)
        sqli_result = results[0]
        assert sqli_result["ruleId"] == "VAPT-SQL-INJECTION"
        assert sqli_result["level"] == "error"
        assert sqli_result["kind"] == "fail"
        assert "message" in sqli_result
        assert "locations" in sqli_result
        assert "properties" in sqli_result

    def test_severity_mapping(self, reporter):
        """Test severity levels are correctly mapped to SARIF levels."""
        findings = [
            {'type': 'Test', 'severity': 'critical', 'location': '/test'},
            {'type': 'Test', 'severity': 'high', 'location': '/test'},
            {'type': 'Test', 'severity': 'medium', 'location': '/test'},
            {'type': 'Test', 'severity': 'low', 'location': '/test'},
        ]

        report = reporter.generate(findings)
        results = report["runs"][0]["results"]

        assert results[0]["level"] == "error"  # critical
        assert results[1]["level"] == "error"  # high
        assert results[2]["level"] == "warning"  # medium
        assert results[3]["level"] == "note"  # low

    def test_message_formatting(self, reporter, sample_findings):
        """Test message is correctly formatted."""
        report = reporter.generate([sample_findings[0]])
        result = report["runs"][0]["results"][0]

        assert "message" in result
        assert "text" in result["message"]
        assert result["message"]["text"] == sample_findings[0]["message"]
        assert "id" in result["message"]

    def test_location_structure(self, reporter, sample_findings):
        """Test location object structure."""
        report = reporter.generate([sample_findings[0]])
        location = report["runs"][0]["results"][0]["locations"][0]

        assert "physicalLocation" in location
        assert "address" in location["physicalLocation"]
        assert "region" in location["physicalLocation"]
        assert "logicalLocations" in location

    def test_properties_include_metadata(self, reporter, sample_findings):
        """Test result properties include all metadata."""
        report = reporter.generate([sample_findings[0]])
        props = report["runs"][0]["results"][0]["properties"]

        assert "severity" in props
        assert "confidence" in props
        assert "vulnerabilityType" in props
        assert "cweId" in props
        assert "owaspCategory" in props
        assert "evidence" in props
        assert "tags" in props

    def test_confidence_score_preservation(self, reporter, sample_findings):
        """Test confidence scores are preserved."""
        report = reporter.generate(sample_findings)
        results = report["runs"][0]["results"]

        assert results[0]["properties"]["confidence"] == 0.98
        assert results[1]["properties"]["confidence"] == 0.95
        assert results[2]["properties"]["confidence"] == 1.0

    def test_empty_findings_list(self, reporter):
        """Test report generation with no findings."""
        report = reporter.generate([])

        assert report["runs"][0]["results"] == []

    def test_invocation_info(self, reporter, sample_findings):
        """Test invocation information."""
        report = reporter.generate(sample_findings)
        invocation = report["runs"][0]["invocation"]

        assert invocation["toolExecutionSuccessful"] is True
        assert "startTimeUtc" in invocation
        assert "endTimeUtc" in invocation
        assert "properties" in invocation

    def test_run_properties(self, reporter, sample_findings):
        """Test run-level properties."""
        report = reporter.generate(sample_findings)
        props = report["runs"][0]["properties"]

        assert props["scanTarget"] == "http://localhost:3000"
        assert "generatedAt" in props

    def test_cwe_rule_id_mapping(self, reporter):
        """Test CWE IDs are correctly mapped."""
        findings = [
            {'type': 'SQL Injection', 'severity': 'high', 'location': '/test'},
            {'type': 'XSS', 'severity': 'high', 'location': '/test'},
            {'type': 'CSRF', 'severity': 'high', 'location': '/test'},
        ]

        report = reporter.generate(findings)
        results = report["runs"][0]["results"]

        assert results[0]["ruleId"] == "VAPT-SQL-INJECTION"
        assert results[1]["ruleId"] == "VAPT-XSS"
        assert results[2]["ruleId"] == "VAPT-CSRF"

    def test_fixes_included_for_known_types(self, reporter):
        """Test fixes are included for known vulnerability types."""
        findings = [
            {'type': 'SQL Injection', 'severity': 'critical', 'location': '/test'},
            {'type': 'Unknown Type', 'severity': 'high', 'location': '/test'},
        ]

        report = reporter.generate(findings)
        results = report["runs"][0]["results"]

        # Known type should have multiple fixes
        assert "fixes" in results[0]
        assert len(results[0]["fixes"]) > 0

        # Unknown type should have generic fix
        assert "fixes" in results[1]

    def test_json_serializable(self, reporter, sample_findings):
        """Test report is JSON serializable."""
        report = reporter.generate(sample_findings)

        # Should not raise exception
        json_str = json.dumps(report, indent=2)
        assert len(json_str) > 0

        # Should be parseable back
        parsed = json.loads(json_str)
        assert parsed["version"] == "2.1.0"

    def test_create_sarif_report_convenience_function(self, sample_findings):
        """Test convenience function."""
        report = create_sarif_report(sample_findings, "1.0.0", "http://test.com")

        assert report["version"] == "2.1.0"
        assert len(report["runs"][0]["results"]) == 3


class TestPRCommentGenerator:
    """Tests for GitHub PR comment generation."""

    @pytest.fixture
    def generator(self):
        """Create generator instance."""
        return PRCommentGenerator(
            scan_target="https://api.example.com",
            duration_seconds=45.5
        )

    @pytest.fixture
    def sample_findings(self):
        """Sample findings for PR comment."""
        return [
            {
                'type': 'SQL Injection',
                'severity': 'critical',
                'message': 'SQL Injection vulnerability',
                'location': '/api/users',
                'parameter': 'id',
                'evidence': 'SQL error detected',
                'confidence': 0.98,
                'cwe_id': 'CWE-89',
                'owasp_category': 'A03:2021 - Injection'
            },
            {
                'type': 'XSS',
                'severity': 'high',
                'message': 'Reflected XSS',
                'location': '/api/search',
                'parameter': 'q',
                'evidence': 'Payload reflected',
                'confidence': 0.95,
                'cwe_id': 'CWE-79',
                'owasp_category': 'A03:2021 - Injection'
            },
            {
                'type': 'Missing Headers',
                'severity': 'medium',
                'message': 'Missing CSP',
                'location': '/api',
                'parameter': 'headers',
                'evidence': 'CSP missing',
                'confidence': 1.0,
                'cwe_id': 'CWE-693',
                'owasp_category': 'A05:2021'
            },
        ]

    def test_generator_initialization(self, generator):
        """Test generator initializes correctly."""
        assert generator.scan_target == "https://api.example.com"
        assert generator.duration_seconds == 45.5

    def test_full_comment_generation(self, generator, sample_findings):
        """Test full PR comment generation."""
        comment = generator.generate(sample_findings)

        assert isinstance(comment, str)
        assert len(comment) > 0

        # Check for main sections
        assert "VAPT Security Scan Results" in comment
        assert "Summary" in comment
        assert "Critical" in comment
        assert "High" in comment
        assert "Medium" in comment

    def test_comment_includes_severity_icons(self, generator, sample_findings):
        """Test comment includes severity icons."""
        comment = generator.generate(sample_findings)

        assert "🔴" in comment  # Critical
        assert "🟠" in comment  # High
        assert "🟡" in comment  # Medium

    def test_comment_includes_finding_details(self, generator, sample_findings):
        """Test comment includes detailed finding information."""
        comment = generator.generate(sample_findings)

        # Should include vulnerability types
        assert "SQL Injection" in comment
        assert "XSS" in comment

        # Should include locations
        assert "/api/users" in comment
        assert "/api/search" in comment

        # Should include confidence
        assert "98%" in comment
        assert "95%" in comment

    def test_comment_includes_scan_details(self, generator, sample_findings):
        """Test comment includes scan metadata."""
        comment = generator.generate(sample_findings)

        assert "Scan Details" in comment
        assert "https://api.example.com" in comment
        assert "45.50s" in comment
        assert "VAPT Toolkit" in comment

    def test_summary_only_mode(self, generator, sample_findings):
        """Test summary-only comment mode."""
        comment = generator.generate_summary_only(sample_findings)

        assert isinstance(comment, str)
        assert len(comment) > 0

        # Should have counts
        assert "1" in comment and "Critical" in comment
        assert "1" in comment and "High" in comment
        assert "1" in comment and "Medium" in comment

    def test_summary_only_no_findings(self, generator):
        """Test summary-only with no findings."""
        comment = generator.generate_summary_only([])

        assert "No Vulnerabilities Detected" in comment or "Passed" in comment

    def test_finding_formatting_with_parameter(self, generator):
        """Test finding is formatted with parameter."""
        findings = [
            {
                'type': 'XSS',
                'severity': 'high',
                'message': 'Test',
                'location': '/api/test',
                'parameter': 'q',
                'evidence': 'Evidence',
                'confidence': 0.9,
                'cwe_id': 'CWE-79',
                'owasp_category': 'A03:2021'
            }
        ]

        comment = generator.generate(findings)

        # Should show parameter in location
        assert "/api/test?q" in comment or "q=" in comment

    def test_finding_formatting_without_parameter(self, generator):
        """Test finding is formatted without parameter."""
        findings = [
            {
                'type': 'Missing Headers',
                'severity': 'medium',
                'message': 'Test',
                'location': '/api',
                'parameter': '',
                'evidence': 'Evidence',
                'confidence': 0.9,
                'cwe_id': 'CWE-693',
                'owasp_category': 'A05:2021'
            }
        ]

        comment = generator.generate(findings)

        # Should show just location
        assert "/api" in comment

    def test_cwe_and_owasp_references(self, generator, sample_findings):
        """Test CWE and OWASP references are included."""
        comment = generator.generate(sample_findings)

        assert "CWE-89" in comment
        assert "CWE-79" in comment
        assert "A03:2021" in comment

    def test_evidence_display(self, generator, sample_findings):
        """Test evidence is displayed."""
        comment = generator.generate(sample_findings)

        assert "SQL error detected" in comment
        assert "Payload reflected" in comment
        assert "CSP missing" in comment

    def test_confidence_bar_visualization(self, generator):
        """Test confidence bar visualization."""
        comment = generator.generate_summary_only([])
        # Summary only doesn't show bars, test with full comment

        findings = [
            {
                'type': 'Test',
                'severity': 'high',
                'message': 'Test',
                'location': '/test',
                'parameter': '',
                'evidence': 'Test',
                'confidence': 0.95,
                'cwe_id': 'CWE-79',
                'owasp_category': 'A03:2021'
            }
        ]

        comment = generator.generate(findings)
        assert "%" in comment  # Should include percentage

    def test_severity_summary_table(self, generator, sample_findings):
        """Test severity summary table."""
        comment = generator.generate(sample_findings)

        # Should include table headers
        assert "Severity" in comment
        assert "Count" in comment
        assert "Status" in comment

        # Should include severity rows
        assert "Critical" in comment
        assert "High" in comment
        assert "Medium" in comment

    def test_multiple_findings_same_severity(self, generator):
        """Test multiple findings with same severity."""
        findings = [
            {
                'type': 'SQL Injection',
                'severity': 'critical',
                'message': 'Finding 1',
                'location': '/api/users',
                'parameter': 'id',
                'evidence': 'Evidence 1',
                'confidence': 0.98,
                'cwe_id': 'CWE-89',
                'owasp_category': 'A03:2021'
            },
            {
                'type': 'SQL Injection',
                'severity': 'critical',
                'message': 'Finding 2',
                'location': '/api/posts',
                'parameter': 'id',
                'evidence': 'Evidence 2',
                'confidence': 0.96,
                'cwe_id': 'CWE-89',
                'owasp_category': 'A03:2021'
            },
        ]

        comment = generator.generate(findings)

        # Should include both findings
        assert "/api/users" in comment
        assert "/api/posts" in comment
        assert comment.count("1. 🔴") > 0  # At least one finding numbered

    def test_generate_pr_comment_convenience_function(self, sample_findings):
        """Test convenience function."""
        comment = generate_pr_comment(
            sample_findings,
            "https://test.com",
            45.5,
            summary_only=False
        )

        assert isinstance(comment, str)
        assert "VAPT Security Scan Results" in comment

    def test_convenience_function_summary_only(self, sample_findings):
        """Test convenience function with summary_only."""
        comment = generate_pr_comment(
            sample_findings,
            "https://test.com",
            45.5,
            summary_only=True
        )

        assert isinstance(comment, str)
        # Summary is more concise
        assert len(comment) < len(generate_pr_comment(
            sample_findings,
            "https://test.com",
            45.5,
            summary_only=False
        ))

    def test_footer_includes_automation_notice(self, generator):
        """Test footer includes automation notice."""
        comment = generator.generate([])

        assert "Automated" in comment
        assert "VAPT Toolkit" in comment


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
