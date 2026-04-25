"""Tests for heat map generator."""

import unittest
from datetime import datetime, timedelta
from scanner.reporters.heatmap_generator import HeatMapGenerator, SeverityLevel


class TestHeatMapGenerator(unittest.TestCase):
    """Test suite for HeatMapGenerator."""

    def setUp(self):
        """Set up test fixtures."""
        self.generator = HeatMapGenerator()
        
        # Sample scan data
        self.sample_scan_1 = {
            "target": "example.com",
            "timestamp": datetime.now().isoformat(),
            "web_vulnerabilities": {
                "findings": [
                    {"type": "XSS", "severity": "High", "endpoint": "/login"},
                    {"type": "CSRF", "severity": "Medium", "endpoint": "/form"},
                    {"type": "SQLi", "severity": "Critical", "endpoint": "/search"},
                ]
            },
            "cve": {
                "correlations": [
                    {
                        "cves": [
                            {"id": "CVE-2024-0001", "severity": "High", "cvss_score": 8.5},
                        ]
                    }
                ]
            }
        }
        
        self.sample_scan_2 = {
            "target": "test.org",
            "timestamp": (datetime.now() - timedelta(days=7)).isoformat(),
            "web_vulnerabilities": {
                "findings": [
                    {"type": "XSS", "severity": "Medium", "endpoint": "/api"},
                    {"type": "Information Disclosure", "severity": "Low", "endpoint": "/"},
                ]
            },
            "cve": {
                "correlations": [
                    {
                        "cves": [
                            {"id": "CVE-2024-0002", "severity": "Medium", "cvss_score": 6.5},
                            {"id": "CVE-2024-0003", "severity": "Low", "cvss_score": 3.5},
                        ]
                    }
                ]
            }
        }

    def test_generate_by_target_basic(self):
        """Test basic by-target heat map generation."""
        scans = [self.sample_scan_1, self.sample_scan_2]
        result = self.generator.generate_by_target(scans)
        
        assert result["type"] == "by_target"
        assert "matrix" in result
        assert "targets" in result
        assert "severities" in result
        assert "data" in result
        
        assert len(result["targets"]) == 2
        assert set(result["targets"]) == {"example.com", "test.org"}
        assert result["severities"] == ["Critical", "High", "Medium", "Low", "Info"]

    def test_generate_by_target_matrix_structure(self):
        """Test matrix structure for by-target heat map."""
        scans = [self.sample_scan_1, self.sample_scan_2]
        result = self.generator.generate_by_target(scans)
        
        # Matrix should be 2 targets x 5 severities
        assert len(result["matrix"]) == 2
        assert len(result["matrix"][0]) == 5
        assert len(result["matrix"][1]) == 5
        
        # All values should be non-negative
        for row in result["matrix"]:
            for value in row:
                assert value >= 0

    def test_generate_by_target_data_structure(self):
        """Test data structure for by-target heat map."""
        scans = [self.sample_scan_1]
        result = self.generator.generate_by_target(scans)
        
        # Should have data for each target
        assert len(result["data"]) == 1
        
        # Each row should have 5 severity columns
        assert len(result["data"][0]) == 5
        
        # Each cell should have required fields
        for cell in result["data"][0]:
            assert "target" in cell
            assert "severity" in cell
            assert "count" in cell
            assert "color" in cell
            assert "value" in cell

    def test_generate_by_target_counts(self):
        """Test that finding counts are correct."""
        scans = [self.sample_scan_1]
        result = self.generator.generate_by_target(scans)
        
        data_row = result["data"][0]
        
        # Check counts by severity
        critical_count = next(c for c in data_row if c["severity"] == "Critical")["count"]
        high_count = next(c for c in data_row if c["severity"] == "High")["count"]
        medium_count = next(c for c in data_row if c["severity"] == "Medium")["count"]
        
        assert critical_count == 1  # 1 Critical
        assert high_count == 2  # 2 High (1 XSS + 1 CVE)
        assert medium_count == 1  # 1 Medium

    def test_generate_by_target_date_filtering(self):
        """Test date filtering in by-target heat map."""
        scans = [self.sample_scan_1, self.sample_scan_2]
        
        # Filter to only recent scans
        result = self.generator.generate_by_target(
            scans,
            start_date=(datetime.now() - timedelta(days=1)).isoformat(),
            end_date=datetime.now().isoformat()
        )
        
        # Should only include example.com (recent scan)
        assert len(result["targets"]) == 1
        assert result["targets"][0] == "example.com"

    def test_generate_by_time_basic(self):
        """Test basic by-time heat map generation."""
        scans = [self.sample_scan_1, self.sample_scan_2]
        result = self.generator.generate_by_time(scans, period="week")
        
        assert result["type"] == "by_time"
        assert "matrix" in result
        assert "time_periods" in result
        assert "severities" in result
        assert "data" in result
        assert result["period"] == "week"

    def test_generate_by_time_matrix_structure(self):
        """Test matrix structure for by-time heat map."""
        scans = [self.sample_scan_1, self.sample_scan_2]
        result = self.generator.generate_by_time(scans, period="week")
        
        # Matrix should be 5 severities x number of weeks
        assert len(result["matrix"]) == 5
        assert len(result["matrix"][0]) >= 1
        
        # All values should be non-negative
        for row in result["matrix"]:
            for value in row:
                assert value >= 0

    def test_generate_by_time_periods(self):
        """Test time period generation."""
        scans = [self.sample_scan_1, self.sample_scan_2]
        
        result_daily = self.generator.generate_by_time(scans, period="day")
        result_weekly = self.generator.generate_by_time(scans, period="week")
        result_monthly = self.generator.generate_by_time(scans, period="month")
        
        assert len(result_daily["time_periods"]) >= 1
        assert len(result_weekly["time_periods"]) >= 1
        assert len(result_monthly["time_periods"]) >= 1

    def test_generate_by_time_target_filter(self):
        """Test target filtering in by-time heat map."""
        scans = [self.sample_scan_1, self.sample_scan_2]
        result = self.generator.generate_by_time(scans, target="example.com", period="week")
        
        assert result["target"] == "example.com"

    def test_generate_by_severity_basic(self):
        """Test basic by-severity heat map generation."""
        findings = self.sample_scan_1["web_vulnerabilities"]["findings"]
        result = self.generator.generate_by_severity(findings)
        
        assert result["type"] == "by_severity"
        assert "distribution" in result
        assert "percentages" in result
        assert "total" in result
        assert "risk_score" in result
        assert "colors" in result

    def test_generate_by_severity_distribution(self):
        """Test severity distribution calculation."""
        findings = self.sample_scan_1["web_vulnerabilities"]["findings"]
        result = self.generator.generate_by_severity(findings)
        
        # Should have counts for each severity
        assert result["distribution"]["Critical"] == 1
        assert result["distribution"]["High"] == 1
        assert result["distribution"]["Medium"] == 1
        assert result["total"] == 3

    def test_generate_by_severity_percentages(self):
        """Test percentage calculation."""
        findings = self.sample_scan_1["web_vulnerabilities"]["findings"]
        result = self.generator.generate_by_severity(findings)
        
        # Check percentages sum to 100
        total_percentage = sum(result["percentages"].values())
        assert abs(total_percentage - 100.0) < 0.01

    def test_generate_by_severity_risk_score(self):
        """Test risk score calculation."""
        findings = self.sample_scan_1["web_vulnerabilities"]["findings"]
        result = self.generator.generate_by_severity(findings)
        
        # Risk score should be between 0 and 100
        assert 0 <= result["risk_score"] <= 100

    def test_generate_by_severity_empty(self):
        """Test by-severity with empty findings."""
        result = self.generator.generate_by_severity([])
        
        assert result["total"] == 0
        assert result["risk_score"] == 0
        assert result["distribution"] == {}

    def test_generate_by_vulnerability_type_basic(self):
        """Test basic by-type heat map generation."""
        scans = [self.sample_scan_1]
        result = self.generator.generate_by_vulnerability_type(scans)
        
        assert result["type"] == "by_vulnerability_type"
        assert "matrix" in result
        assert "vulnerability_types" in result
        assert "severities" in result
        assert "data" in result

    def test_generate_by_vulnerability_type_data(self):
        """Test vulnerability type data structure."""
        scans = [self.sample_scan_1]
        result = self.generator.generate_by_vulnerability_type(scans)
        
        # Should include web vulnerabilities
        vuln_types = result["vulnerability_types"]
        assert len(vuln_types) > 0
        assert "CVE" in vuln_types

    def test_risk_value_calculation(self):
        """Test risk value calculation."""
        # Test various counts and severities
        risk_1 = self.generator._calculate_risk_value(0, "Critical")
        assert risk_1 == 0.0
        
        risk_2 = self.generator._calculate_risk_value(1, "Critical")
        assert risk_2 > 0
        
        risk_3 = self.generator._calculate_risk_value(5, "Critical")
        assert risk_3 > risk_2
        
        risk_4 = self.generator._calculate_risk_value(5, "Low")
        assert risk_4 < risk_3

    def test_overall_risk_score_calculation(self):
        """Test overall risk score calculation."""
        findings = [
            {"severity": "Critical"},
            {"severity": "Critical"},
            {"severity": "High"},
            {"severity": "Medium"},
            {"severity": "Low"},
        ]
        
        score = self.generator._calculate_overall_risk_score(findings)
        
        assert isinstance(score, int)
        assert 0 <= score <= 100

    def test_color_mapping(self):
        """Test color mapping for severities."""
        assert self.generator.RISK_COLORS["critical"] == "#cf222e"
        assert self.generator.RISK_COLORS["high"] == "#f0883e"
        assert self.generator.RISK_COLORS["medium"] == "#d29922"
        assert self.generator.RISK_COLORS["low"] == "#3fb950"
        assert self.generator.RISK_COLORS["info"] == "#0969da"

    def test_timestamp_parsing(self):
        """Test timestamp parsing."""
        # Test ISO format
        iso_time = "2024-01-15T10:30:00+00:00"
        parsed = self.generator._parse_timestamp(iso_time)
        assert isinstance(parsed, datetime)
        
        # Test with Z suffix
        z_time = "2024-01-15T10:30:00Z"
        parsed_z = self.generator._parse_timestamp(z_time)
        assert isinstance(parsed_z, datetime)
        
        # Test None returns current time
        current = self.generator._parse_timestamp(None)
        assert isinstance(current, datetime)

    def test_period_key_generation(self):
        """Test period key generation."""
        test_time = datetime(2024, 1, 15, 10, 30, 0)
        
        daily_key = self.generator._get_period_key(test_time, "day")
        assert daily_key == "2024-01-15"
        
        monthly_key = self.generator._get_period_key(test_time, "month")
        assert monthly_key == "2024-01"
        
        yearly_key = self.generator._get_period_key(test_time, "year")
        assert yearly_key == "2024"

    def test_multiple_scans_aggregation(self):
        """Test aggregation across multiple scans."""
        scans = [self.sample_scan_1, self.sample_scan_2]
        result = self.generator.generate_by_target(scans)
        
        # Should have findings aggregated from both scans
        data = result["data"]
        
        # Check that counts are aggregated
        for row in data:
            for cell in row:
                assert cell["count"] >= 0

    def test_severity_order(self):
        """Test severity ordering."""
        assert self.generator.SEVERITY_ORDER["Critical"] == 4
        assert self.generator.SEVERITY_ORDER["High"] == 3
        assert self.generator.SEVERITY_ORDER["Medium"] == 2
        assert self.generator.SEVERITY_ORDER["Low"] == 1
        assert self.generator.SEVERITY_ORDER["Info"] == 0

    def test_result_contains_timestamp(self):
        """Test that results contain timestamps."""
        scans = [self.sample_scan_1]
        
        result_target = self.generator.generate_by_target(scans)
        assert "timestamp" in result_target
        
        result_time = self.generator.generate_by_time(scans)
        assert "timestamp" in result_time
        
        result_severity = self.generator.generate_by_severity([])
        assert "timestamp" in result_severity


class TestHeatMapIntegration(unittest.TestCase):
    """Integration tests for heat map generation."""

    def setUp(self):
        """Set up test fixtures."""
        self.generator = HeatMapGenerator()

    def test_complete_workflow(self):
        """Test complete heat map generation workflow."""
        # Create realistic scan data
        scans = [
            {
                "target": "api.example.com",
                "timestamp": datetime.now().isoformat(),
                "web_vulnerabilities": {
                    "findings": [
                        {"type": "Insecure Deserialization", "severity": "Critical"},
                        {"type": "SQL Injection", "severity": "Critical"},
                        {"type": "Cross-Site Scripting", "severity": "High"},
                        {"type": "Cross-Site Request Forgery", "severity": "Medium"},
                    ]
                },
                "cve": {
                    "correlations": [
                        {
                            "cves": [
                                {"id": "CVE-2024-1000", "severity": "Critical", "cvss_score": 9.8},
                                {"id": "CVE-2024-1001", "severity": "High", "cvss_score": 7.5},
                            ]
                        }
                    ]
                }
            },
            {
                "target": "web.example.com",
                "timestamp": (datetime.now() - timedelta(days=7)).isoformat(),
                "web_vulnerabilities": {
                    "findings": [
                        {"type": "Cross-Site Scripting", "severity": "High"},
                        {"type": "Broken Authentication", "severity": "High"},
                    ]
                },
                "cve": {
                    "correlations": [
                        {
                            "cves": [
                                {"id": "CVE-2024-2000", "severity": "Medium", "cvss_score": 5.5},
                            ]
                        }
                    ]
                }
            }
        ]
        
        # Generate all types of heat maps
        by_target = self.generator.generate_by_target(scans)
        by_time = self.generator.generate_by_time(scans)
        
        # Collect all findings for severity analysis
        all_findings = []
        for scan in scans:
            all_findings.extend(scan["web_vulnerabilities"]["findings"])
            for corr in scan["cve"]["correlations"]:
                for cve in corr["cves"]:
                    all_findings.append({"severity": cve["severity"], "type": "CVE"})
        
        by_severity = self.generator.generate_by_severity(all_findings)
        by_type = self.generator.generate_by_vulnerability_type(scans)
        
        # Verify all results are valid
        assert by_target["type"] == "by_target"
        assert by_time["type"] == "by_time"
        assert by_severity["type"] == "by_severity"
        assert by_type["type"] == "by_vulnerability_type"
        
        # Verify structure
        assert len(by_target["targets"]) == 2
        assert len(by_time["time_periods"]) >= 1
        assert by_severity["total"] > 0
        assert len(by_type["vulnerability_types"]) > 0


if __name__ == "__main__":
    unittest.main(verbosity=2)
