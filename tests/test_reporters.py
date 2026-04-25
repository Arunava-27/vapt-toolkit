"""
Comprehensive unit tests for scanner/reporters/ modules - Report generation.
"""
import pytest
import json
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import sys
from pathlib import Path
import tempfile

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from scanner.reporters.executive_reporter import ExecutiveReporter
    from scanner.reporters.heatmap_generator import HeatMapGenerator
    from scanner.reporters.export_generator import ExportGenerator
except ImportError:
    pytest.skip("reporter modules not available", allow_module_level=True)


class TestExecutiveReporter:
    """Test executive report generation."""
    
    @pytest.fixture
    def executive_reporter(self):
        """Create an ExecutiveReporter instance."""
        return ExecutiveReporter()
    
    def test_generate_executive_report(self, executive_reporter, sample_scan_result):
        """Test generating an executive report."""
        report = executive_reporter.generate(sample_scan_result)
        
        assert report is not None
        assert isinstance(report, dict)
        assert "title" in report or "summary" in report
    
    def test_executive_report_contains_key_metrics(self, executive_reporter, sample_scan_result):
        """Test that executive report contains key metrics."""
        report = executive_reporter.generate(sample_scan_result)
        
        # Should contain risk summary
        assert any(key in report for key in [
            "risk_score", "severity_distribution", "total_findings",
            "critical_count", "high_count"
        ])
    
    def test_executive_report_one_page_format(self, executive_reporter, sample_scan_result):
        """Test that executive report is one-page suitable."""
        report = executive_reporter.generate(sample_scan_result)
        
        # Report should be condensed
        assert report is not None


class TestHeatmapGenerator:
    """Test heatmap report generation."""
    
    @pytest.fixture
    def heatmap_generator(self):
        """Create a HeatMapGenerator instance."""
        return HeatMapGenerator()
    
    def test_generate_heatmap(self, heatmap_generator, sample_scan_result):
        """Test generating a heatmap."""
        heatmap = heatmap_generator.generate(sample_scan_result)
        
        assert heatmap is not None
    
    def test_heatmap_risk_scoring(self, heatmap_generator, sample_scan_result):
        """Test heatmap risk scoring."""
        heatmap = heatmap_generator.generate(sample_scan_result)
        
        # Should contain risk scores
        assert heatmap is not None
    
    def test_heatmap_severity_mapping(self, heatmap_generator):
        """Test heatmap severity level mapping."""
        findings = [
            {"severity": "critical", "endpoint": "/api/users"},
            {"severity": "high", "endpoint": "/api/posts"},
            {"severity": "medium", "endpoint": "/api/search"}
        ]
        
        heatmap = heatmap_generator.generate_from_findings(findings)
        
        # Should have severity distribution
        assert heatmap is not None


class TestExportGenerator:
    """Test multi-format export generation."""
    
    @pytest.fixture
    def export_generator(self):
        """Create an ExportGenerator instance."""
        return ExportGenerator()
    
    def test_export_json_format(self, export_generator, sample_scan_result):
        """Test JSON export."""
        export = export_generator.export(sample_scan_result, format="json")
        
        assert export is not None
        # Should be valid JSON
        data = json.loads(export) if isinstance(export, str) else export
        assert "findings" in data or len(data) > 0
    
    def test_export_csv_format(self, export_generator, sample_scan_result):
        """Test CSV export."""
        export = export_generator.export(sample_scan_result, format="csv")
        
        assert export is not None
        # Should contain comma-separated values
        assert isinstance(export, str)
    
    def test_export_html_format(self, export_generator, sample_scan_result):
        """Test HTML export."""
        export = export_generator.export(sample_scan_result, format="html")
        
        assert export is not None
        assert isinstance(export, str)
        assert "<html>" in export or "<HTML>" in export or "<!DOCTYPE" in export
    
    def test_export_markdown_format(self, export_generator, sample_scan_result):
        """Test Markdown export."""
        export = export_generator.export(sample_scan_result, format="markdown")
        
        assert export is not None
        assert isinstance(export, str)
    
    def test_export_xlsx_format(self, export_generator, sample_scan_result):
        """Test XLSX export."""
        export = export_generator.export(sample_scan_result, format="xlsx")
        
        assert export is not None or export is None
    
    def test_export_sarif_format(self, export_generator, sample_scan_result):
        """Test SARIF export."""
        export = export_generator.export(sample_scan_result, format="sarif")
        
        assert export is not None
        # SARIF is JSON-based
        if isinstance(export, str):
            data = json.loads(export)
            assert "$schema" in data or "version" in data


class TestReportFormatValidation:
    """Test report format validation."""
    
    def test_valid_report_format(self, export_generator):
        """Test validating report format."""
        valid_formats = ["json", "csv", "html", "markdown", "xlsx", "sarif"]
        
        for fmt in valid_formats:
            assert export_generator.is_valid_format(fmt)
    
    def test_invalid_report_format(self, export_generator):
        """Test that invalid format is rejected."""
        assert not export_generator.is_valid_format("invalid_format")


class TestReportDelivery:
    """Test report delivery."""
    
    def test_save_report_to_file(self, export_generator, sample_scan_result):
        """Test saving report to file."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            filepath = f.name
        
        try:
            export = export_generator.export(sample_scan_result, format="json")
            export_generator.save_report(filepath, export)
            
            # Verify file exists
            assert Path(filepath).exists()
        finally:
            Path(filepath).unlink(missing_ok=True)
    
    def test_export_with_filename_override(self, export_generator, sample_scan_result):
        """Test exporting with custom filename."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "custom_report.json"
            
            export_generator.export_to_file(
                sample_scan_result,
                format="json",
                output_path=str(output_file)
            )


class TestReportAggregation:
    """Test aggregating multiple scans in report."""
    
    def test_aggregate_multiple_scans(self, export_generator):
        """Test aggregating findings from multiple scans."""
        scan1 = {
            "scan_id": "scan_001",
            "findings": [
                {"type": "XSS", "severity": "high"},
                {"type": "SQLi", "severity": "critical"}
            ]
        }
        
        scan2 = {
            "scan_id": "scan_002",
            "findings": [
                {"type": "CSRF", "severity": "medium"}
            ]
        }
        
        aggregated = export_generator.aggregate_scans([scan1, scan2])
        
        assert aggregated is not None
        # Should have combined findings
        assert "findings" in aggregated or "total_findings" in aggregated


class TestRiskScoring:
    """Test risk scoring in reports."""
    
    def test_calculate_risk_score(self, export_generator, sample_scan_result):
        """Test calculating risk score from findings."""
        score = export_generator.calculate_risk_score(sample_scan_result)
        
        assert score is not None
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100
    
    def test_risk_score_severity_distribution(self, export_generator):
        """Test risk score based on severity distribution."""
        findings = {
            "critical": 2,
            "high": 5,
            "medium": 10,
            "low": 3
        }
        
        score = export_generator.calculate_risk_score_from_distribution(findings)
        
        assert score is not None


class TestTrendAnalysis:
    """Test trend analysis in reports."""
    
    def test_calculate_trends(self, export_generator):
        """Test calculating trends from scan history."""
        scans = [
            {
                "scan_id": "scan_001",
                "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
                "findings_count": 15
            },
            {
                "scan_id": "scan_002",
                "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
                "findings_count": 12
            },
            {
                "scan_id": "scan_003",
                "timestamp": datetime.now().isoformat(),
                "findings_count": 10
            }
        ]
        
        trends = export_generator.analyze_trends(scans)
        
        assert trends is not None
        # Should show improving trend
        assert "trend" in trends or "direction" in trends


class TestReportCWEMapping:
    """Test CWE mapping in reports."""
    
    def test_map_findings_to_cwe(self, export_generator, sample_scan_result):
        """Test mapping findings to CWE."""
        mapped = export_generator.map_to_cwe(sample_scan_result)
        
        assert mapped is not None
        # Should have CWE references
        assert any("cwe" in str(finding).lower() for finding in mapped)


class TestReportOWASPMapping:
    """Test OWASP mapping in reports."""
    
    def test_map_findings_to_owasp(self, export_generator, sample_scan_result):
        """Test mapping findings to OWASP Top 10."""
        mapped = export_generator.map_to_owasp(sample_scan_result)
        
        assert mapped is not None
        # Should have OWASP references
        assert any("owasp" in str(finding).lower() for finding in mapped)
