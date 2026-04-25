"""
Unit tests for Scan Comparison module.

Tests cover:
- Comparison logic (new/fixed/unchanged/regression detection)
- Risk delta calculation
- Filtering
- Edge cases
"""

import unittest
from datetime import datetime
from scanner.web.scan_comparison import (
    ScanComparator, ScanComparisonResult, ComparisonFinding, ComparisonStatus
)


class TestScanComparator(unittest.TestCase):
    """Test suite for ScanComparator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.comparator = ScanComparator()
        
        # Create baseline scan
        self.scan_1 = {
            "scan_id": "scan_001",
            "timestamp": "2024-01-01T10:00:00",
            "results": {
                "web_vulnerabilities": {
                    "findings": [
                        {
                            "type": "SQL Injection",
                            "severity": "Critical",
                            "url": "http://example.com/login",
                            "endpoint": "/login",
                            "parameter": "username",
                            "confidence_score": 90,
                            "evidence": "Time-based SQLi detected",
                        },
                        {
                            "type": "Cross-Site Scripting",
                            "severity": "High",
                            "url": "http://example.com/search",
                            "endpoint": "/search",
                            "parameter": "q",
                            "confidence_score": 85,
                            "evidence": "Marker reflected in response",
                        },
                    ]
                },
                "cve": {"correlations": []}
            }
        }
        
        # Create second scan: has one new issue, one fixed, one unchanged
        self.scan_2 = {
            "scan_id": "scan_002",
            "timestamp": "2024-01-02T10:00:00",
            "results": {
                "web_vulnerabilities": {
                    "findings": [
                        {
                            "type": "SQL Injection",
                            "severity": "Critical",
                            "url": "http://example.com/login",
                            "endpoint": "/login",
                            "parameter": "username",
                            "confidence_score": 90,
                            "evidence": "Time-based SQLi still present",
                        },
                        {
                            "type": "Weak Cryptography",
                            "severity": "High",
                            "url": "http://example.com/api",
                            "endpoint": "/api",
                            "parameter": "token",
                            "confidence_score": 75,
                            "evidence": "MD5 detected in authentication",
                        },
                    ]
                },
                "cve": {"correlations": []}
            }
        }
    
    def test_compare_scans_basic(self):
        """Test basic comparison functionality."""
        result = self.comparator.compare_scans(self.scan_1, self.scan_2)
        
        self.assertIsInstance(result, ScanComparisonResult)
        self.assertEqual(result.scan_1_id, "scan_001")
        self.assertEqual(result.scan_2_id, "scan_002")
        
        # Verify we have results in all categories
        self.assertGreater(len(result.new_findings) + len(result.fixed_findings) + 
                          len(result.unchanged_findings), 0)
    
    def test_detect_new_findings(self):
        """Test detection of new findings."""
        result = self.comparator.compare_scans(self.scan_1, self.scan_2)
        
        # Weak Cryptography is new
        new_types = {f.finding_type for f in result.new_findings}
        self.assertIn("Weak Cryptography", new_types)
    
    def test_detect_fixed_findings(self):
        """Test detection of fixed findings."""
        result = self.comparator.compare_scans(self.scan_1, self.scan_2)
        
        # XSS was fixed
        fixed_types = {f.finding_type for f in result.fixed_findings}
        self.assertIn("Cross-Site Scripting", fixed_types)
    
    def test_detect_unchanged_findings(self):
        """Test detection of unchanged findings."""
        result = self.comparator.compare_scans(self.scan_1, self.scan_2)
        
        # SQL Injection persists
        unchanged_types = {f.finding_type for f in result.unchanged_findings}
        self.assertIn("SQL Injection", unchanged_types)
    
    def test_risk_score_calculation(self):
        """Test risk score calculation."""
        result = self.comparator.compare_scans(self.scan_1, self.scan_2)
        
        # Risk scores should be positive
        self.assertGreater(result.scan_1_risk_score, 0)
        self.assertGreater(result.scan_2_risk_score, 0)
        
        # Risk delta should be calculated
        self.assertEqual(
            result.risk_delta,
            result.scan_2_risk_score - result.scan_1_risk_score
        )
    
    def test_risk_delta_degrading(self):
        """Test risk delta when security degrades."""
        # Create a scan with more critical issues
        scan_worse = {
            "scan_id": "scan_worse",
            "results": {
                "web_vulnerabilities": {
                    "findings": [
                        {
                            "type": "SQL Injection",
                            "severity": "Critical",
                            "url": "http://example.com/login",
                            "endpoint": "/login",
                            "parameter": "username",
                            "confidence_score": 95,
                            "evidence": "Multiple injection points",
                        },
                        {
                            "type": "SQL Injection",
                            "severity": "Critical",
                            "url": "http://example.com/register",
                            "endpoint": "/register",
                            "parameter": "email",
                            "confidence_score": 90,
                            "evidence": "Union-based SQLi",
                        },
                    ]
                },
                "cve": {"correlations": []}
            }
        }
        
        result = self.comparator.compare_scans(self.scan_1, scan_worse)
        
        self.assertGreater(result.risk_delta, 0)
        self.assertEqual(result.risk_trend, "degrading")
    
    def test_risk_delta_improving(self):
        """Test risk delta when security improves."""
        scan_better = {
            "scan_id": "scan_better",
            "results": {
                "web_vulnerabilities": {
                    "findings": [
                        {
                            "type": "SQL Injection",
                            "severity": "Low",
                            "url": "http://example.com/login",
                            "endpoint": "/login",
                            "parameter": "username",
                            "confidence_score": 40,
                            "evidence": "Very limited impact",
                        },
                    ]
                },
                "cve": {"correlations": []}
            }
        }
        
        result = self.comparator.compare_scans(self.scan_1, scan_better)
        
        self.assertLess(result.risk_delta, 0)
        self.assertEqual(result.risk_trend, "improving")
    
    def test_severity_distribution(self):
        """Test severity distribution calculation."""
        result = self.comparator.compare_scans(self.scan_1, self.scan_2)
        
        # Check distributions have all severity levels
        for severity in ["Critical", "High", "Medium", "Low", "Info"]:
            self.assertIn(severity, result.severity_distribution_1)
            self.assertIn(severity, result.severity_distribution_2)
        
        # Check some values
        self.assertEqual(result.severity_distribution_1.get("Critical"), 1)
        self.assertEqual(result.severity_distribution_1.get("High"), 1)
    
    def test_filtering_by_severity(self):
        """Test filtering findings by severity."""
        filters = {"severity": ["Critical"]}
        result = self.comparator.compare_scans(self.scan_1, self.scan_2, filters)
        
        # Should only have Critical severity findings
        all_findings = (
            result.new_findings + result.fixed_findings +
            result.unchanged_findings + result.regressions
        )
        
        for finding in all_findings:
            self.assertEqual(finding.severity, "Critical")
    
    def test_filtering_by_confidence(self):
        """Test filtering findings by confidence score."""
        filters = {"confidence_min": 85}
        result = self.comparator.compare_scans(self.scan_1, self.scan_2, filters)
        
        # All findings should have confidence >= 85
        all_findings = (
            result.new_findings + result.fixed_findings +
            result.unchanged_findings + result.regressions
        )
        
        for finding in all_findings:
            self.assertGreaterEqual(finding.confidence_score, 85)
    
    def test_filtering_by_type(self):
        """Test filtering findings by type."""
        filters = {"finding_types": ["SQL Injection"]}
        result = self.comparator.compare_scans(self.scan_1, self.scan_2, filters)
        
        # All findings should be SQL Injection
        all_findings = (
            result.new_findings + result.fixed_findings +
            result.unchanged_findings + result.regressions
        )
        
        for finding in all_findings:
            self.assertEqual(finding.finding_type, "SQL Injection")
    
    def test_get_differences(self):
        """Test get_differences convenience method."""
        differences = self.comparator.get_differences(self.scan_1, self.scan_2)
        
        self.assertIn("new", differences)
        self.assertIn("fixed", differences)
        self.assertIn("unchanged", differences)
        self.assertIn("modified", differences)
        
        # Verify types are correct
        for finding in differences["new"]:
            self.assertEqual(finding.status, ComparisonStatus.NEW)
    
    def test_regression_detection_with_history(self):
        """Test regression detection with scan history."""
        # Create a scan history: initial -> fixed -> regressed
        scan_initial = {
            "scan_id": "initial",
            "results": {
                "web_vulnerabilities": {
                    "findings": [
                        {
                            "type": "SQL Injection",
                            "severity": "Critical",
                            "url": "http://example.com/login",
                            "endpoint": "/login",
                            "parameter": "username",
                            "confidence_score": 90,
                            "evidence": "SQLi present",
                        }
                    ]
                },
                "cve": {"correlations": []}
            }
        }
        
        scan_fixed = {
            "scan_id": "fixed",
            "results": {
                "web_vulnerabilities": {"findings": []},
                "cve": {"correlations": []}
            }
        }
        
        scan_regressed = {
            "scan_id": "regressed",
            "results": {
                "web_vulnerabilities": {
                    "findings": [
                        {
                            "type": "SQL Injection",
                            "severity": "Critical",
                            "url": "http://example.com/login",
                            "endpoint": "/login",
                            "parameter": "username",
                            "confidence_score": 90,
                            "evidence": "SQLi reappeared",
                        }
                    ]
                },
                "cve": {"correlations": []}
            }
        }
        
        history = [scan_initial, scan_fixed, scan_regressed]
        regressions = self.comparator.detect_regressions(history)
        
        # Should detect the regression
        self.assertGreater(len(regressions), 0)
        self.assertEqual(regressions[0]["finding_type"], "SQL Injection")
    
    def test_empty_scans(self):
        """Test comparison with empty scans."""
        empty_scan = {
            "scan_id": "empty",
            "results": {
                "web_vulnerabilities": {"findings": []},
                "cve": {"correlations": []}
            }
        }
        
        result = self.comparator.compare_scans(empty_scan, empty_scan)
        
        self.assertEqual(len(result.new_findings), 0)
        self.assertEqual(len(result.fixed_findings), 0)
        self.assertEqual(result.scan_1_risk_score, 0)
        self.assertEqual(result.scan_2_risk_score, 0)
    
    def test_same_scan_comparison(self):
        """Test comparing a scan with itself."""
        result = self.comparator.compare_scans(self.scan_1, self.scan_1)
        
        # All findings should be unchanged
        self.assertEqual(len(result.new_findings), 0)
        self.assertEqual(len(result.fixed_findings), 0)
        self.assertEqual(len(result.unchanged_findings), 2)
        
        # Risk delta should be zero
        self.assertEqual(result.risk_delta, 0)
        self.assertEqual(result.risk_trend, "stable")
    
    def test_comparison_result_to_dict(self):
        """Test conversion of comparison result to dictionary."""
        result = self.comparator.compare_scans(self.scan_1, self.scan_2)
        result_dict = result.to_dict()
        
        self.assertIsInstance(result_dict, dict)
        self.assertIn("scan_1_id", result_dict)
        self.assertIn("new_findings", result_dict)
        self.assertIn("risk_delta", result_dict)
    
    def test_finding_with_cve_results(self):
        """Test comparison with CVE findings."""
        scan_with_cve = {
            "scan_id": "cve_scan",
            "results": {
                "web_vulnerabilities": {"findings": []},
                "cve": {
                    "correlations": [
                        {
                            "port": "443",
                            "cves": [
                                {
                                    "cve_id": "CVE-2021-12345",
                                    "severity": "Critical",
                                    "description": "Test CVE"
                                }
                            ]
                        }
                    ]
                }
            }
        }
        
        empty_scan = {
            "scan_id": "empty",
            "results": {
                "web_vulnerabilities": {"findings": []},
                "cve": {"correlations": []}
            }
        }
        
        result = self.comparator.compare_scans(empty_scan, scan_with_cve)
        
        # Should detect CVE as new finding
        self.assertGreater(len(result.new_findings), 0)
        cve_findings = [f for f in result.new_findings if f.finding_type == "CVE"]
        self.assertGreater(len(cve_findings), 0)
    
    def test_calculate_risk_delta_method(self):
        """Test the calculate_risk_delta convenience method."""
        delta_info = self.comparator.calculate_risk_delta(self.scan_1, self.scan_2)
        
        self.assertIn("risk_score_1", delta_info)
        self.assertIn("risk_score_2", delta_info)
        self.assertIn("risk_delta", delta_info)
        self.assertIn("trend", delta_info)
        self.assertIn("severity_distribution_1", delta_info)
        self.assertIn("severity_distribution_2", delta_info)
    
    def test_vulnerability_count_delta(self):
        """Test vulnerability count delta calculation."""
        result = self.comparator.compare_scans(self.scan_1, self.scan_2)
        
        # Scan 1 has 2 findings, Scan 2 has 2 findings
        self.assertEqual(result.total_vulnerabilities_1, 2)
        self.assertEqual(result.total_vulnerabilities_2, 2)
        
        # Delta should be 0
        self.assertEqual(result.vulnerability_delta, 0)


class TestComparisonFinding(unittest.TestCase):
    """Test ComparisonFinding data class."""
    
    def test_finding_creation(self):
        """Test creating a comparison finding."""
        finding = ComparisonFinding(
            finding_id="test_001",
            finding_type="SQL Injection",
            severity="Critical",
            status=ComparisonStatus.NEW,
            url="http://example.com/login",
            endpoint="/login",
            confidence_score=95,
        )
        
        self.assertEqual(finding.finding_type, "SQL Injection")
        self.assertEqual(finding.status, ComparisonStatus.NEW)
    
    def test_finding_to_dict(self):
        """Test converting finding to dictionary."""
        finding = ComparisonFinding(
            finding_id="test_001",
            finding_type="XSS",
            severity="High",
            status=ComparisonStatus.FIXED,
            url="http://example.com/page",
        )
        
        finding_dict = finding.to_dict()
        
        self.assertEqual(finding_dict["finding_type"], "XSS")
        self.assertEqual(finding_dict["status"], "fixed")  # Should be string value


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def setUp(self):
        self.comparator = ScanComparator()
    
    def test_scan_with_missing_results_field(self):
        """Test handling scan without results field."""
        incomplete_scan = {"scan_id": "incomplete"}
        empty_scan = {
            "scan_id": "empty",
            "results": {
                "web_vulnerabilities": {"findings": []},
                "cve": {"correlations": []}
            }
        }
        
        # Should not crash
        result = self.comparator.compare_scans(incomplete_scan, empty_scan)
        self.assertIsInstance(result, ScanComparisonResult)


if __name__ == "__main__":
    unittest.main()
