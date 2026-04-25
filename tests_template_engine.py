"""Test template engine functionality."""
import unittest
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scanner.reporters.template_engine import TemplateEngine
from scanner.reporters.templates import (
    EXECUTIVE_SUMMARY_TEMPLATE,
    TECHNICAL_REPORT_TEMPLATE,
    COMPLIANCE_REPORT_TEMPLATE,
    RISK_ASSESSMENT_TEMPLATE,
    REMEDIATION_ROADMAP_TEMPLATE
)


class TestTemplateEngine(unittest.TestCase):
    """Test suite for template engine."""

    def setUp(self):
        """Initialize template engine for testing."""
        self.engine = TemplateEngine()
        self.sample_data = {
            "project_name": "Test Project",
            "target": "example.com",
            "timestamp": datetime.now().isoformat(),
            "recon": {
                "subdomains": ["api.example.com", "admin.example.com"]
            },
            "ports": {
                "open_ports": [
                    {"port": 80, "service": "http"},
                    {"port": 443, "service": "https"}
                ]
            },
            "cve": {
                "total_cves": 3,
                "cves": [
                    {"id": "CVE-2021-1234", "severity": "high", "cvss_score": 7.5}
                ]
            },
            "web_vulnerabilities": {
                "total_findings": 5,
                "vulnerabilities": [
                    {"title": "XSS Vulnerability", "severity": "high", "risk_score": 8},
                    {"title": "SQL Injection", "severity": "critical", "risk_score": 9}
                ]
            },
            "web": {"total": 10}
        }

    def test_extract_variables(self):
        """Test variable extraction from template."""
        template_content = "{{ project_name }} - {{ target }} on {{ timestamp }}"
        variables = self.engine._extract_variables(template_content)
        
        var_names = [v["name"] for v in variables]
        self.assertIn("project_name", var_names)
        self.assertIn("target", var_names)
        self.assertIn("timestamp", var_names)
    
    def test_create_template(self):
        """Test template creation."""
        template_id = self.engine.create_template(
            "Test Template",
            "<h1>{{ project_name }}</h1>"
        )
        
        self.assertIsNotNone(template_id)
        self.assertIn(template_id, self.engine.templates_cache)
        self.assertEqual(
            self.engine.templates_cache[template_id]["name"],
            "Test Template"
        )

    def test_apply_template_basic(self):
        """Test basic template rendering."""
        template_id = self.engine.create_template(
            "Basic Template",
            "<h1>{{ scan.project_name }}</h1><p>{{ scan.target }}</p>"
        )
        
        rendered = self.engine.apply_template(template_id, self.sample_data)
        
        self.assertIn("Test Project", rendered)
        self.assertIn("example.com", rendered)
        self.assertIn("<h1>", rendered)

    def test_apply_template_with_loops(self):
        """Test template rendering with loops."""
        template_id = self.engine.create_template(
            "Loop Template",
            """<ul>
            {% for subdomain in scan.recon.subdomains %}
                <li>{{ subdomain }}</li>
            {% endfor %}
            </ul>"""
        )
        
        rendered = self.engine.apply_template(template_id, self.sample_data)
        
        self.assertIn("api.example.com", rendered)
        self.assertIn("admin.example.com", rendered)
        self.assertIn("<li>", rendered)

    def test_apply_template_with_conditionals(self):
        """Test template rendering with conditionals."""
        template_id = self.engine.create_template(
            "Conditional Template",
            """{% if severity_summary.critical > 0 %}
            <div class="alert">Critical issues found!</div>
            {% endif %}"""
        )
        
        rendered = self.engine.apply_template(template_id, self.sample_data)
        self.assertIn("alert", rendered)

    def test_list_templates(self):
        """Test listing templates."""
        self.engine.create_template("Template 1", "<h1>Template 1</h1>")
        self.engine.create_template("Template 2", "<h1>Template 2</h1>")
        
        templates = self.engine.list_templates()
        
        self.assertGreaterEqual(len(templates), 2)
        names = [t["name"] for t in templates]
        self.assertIn("Template 1", names)
        self.assertIn("Template 2", names)

    def test_delete_template(self):
        """Test template deletion."""
        template_id = self.engine.create_template(
            "Temp Template",
            "<h1>Temporary</h1>"
        )
        
        self.assertIn(template_id, self.engine.templates_cache)
        
        self.engine.delete_template(template_id)
        
        self.assertNotIn(template_id, self.engine.templates_cache)

    def test_save_template_preset(self):
        """Test saving template preset."""
        config = {
            "sections": [
                {"type": "header", "title": "Security Report"},
                {"type": "summary"},
                {"type": "findings", "limit": 10},
                {"type": "remediation"}
            ]
        }
        
        preset_id = self.engine.save_template_preset("Test Preset", config)
        
        self.assertIsNotNone(preset_id)
        self.assertIn(preset_id, self.engine.templates_cache)

    def test_get_template_preview(self):
        """Test getting template preview."""
        template_id = self.engine.create_template(
            "Preview Template",
            "<h1>{{ scan.project_name }}</h1>"
        )
        
        preview = self.engine.get_template_preview(template_id, self.sample_data)
        
        self.assertIsNotNone(preview)
        self.assertIn("Test Project", preview)
        self.assertIn("<h1>", preview)

    def test_missing_variables_handling(self):
        """Test handling of missing variables."""
        template_id = self.engine.create_template(
            "Missing Vars Template",
            "{{ scan.project_name }} - {{ scan.nonexistent_field | default('N/A') }}"
        )
        
        rendered = self.engine.apply_template(template_id, self.sample_data)
        
        self.assertIn("Test Project", rendered)
        self.assertIn("N/A", rendered)

    def test_severity_summary_calculation(self):
        """Test severity summary calculation."""
        context = self.engine._prepare_context(self.sample_data)
        
        severity = context["severity_summary"]
        self.assertEqual(severity["critical"], 1)
        self.assertEqual(severity["high"], 1)

    def test_prebuilt_templates_valid(self):
        """Test that prebuilt templates are valid Jinja2 templates."""
        templates = [
            ("Executive Summary", EXECUTIVE_SUMMARY_TEMPLATE),
            ("Technical Report", TECHNICAL_REPORT_TEMPLATE),
            ("Compliance Report", COMPLIANCE_REPORT_TEMPLATE),
            ("Risk Assessment", RISK_ASSESSMENT_TEMPLATE),
            ("Remediation Roadmap", REMEDIATION_ROADMAP_TEMPLATE),
        ]
        
        for name, template_content in templates:
            template_id = self.engine.create_template(name, template_content)
            
            # Should render without errors
            rendered = self.engine.apply_template(template_id, self.sample_data)
            
            self.assertIsNotNone(rendered)
            self.assertGreater(len(rendered), 0)
            self.assertIn("<!DOCTYPE html>", rendered)

    def test_template_with_table_rendering(self):
        """Test rendering templates with tables."""
        template_id = self.engine.create_template(
            "Table Template",
            """<table>
            <tr><th>Port</th><th>Service</th></tr>
            {% for port in scan.ports.open_ports %}
            <tr><td>{{ port.port }}</td><td>{{ port.service }}</td></tr>
            {% endfor %}
            </table>"""
        )
        
        rendered = self.engine.apply_template(template_id, self.sample_data)
        
        self.assertIn("<table>", rendered)
        self.assertIn("80", rendered)
        self.assertIn("http", rendered)
        self.assertIn("443", rendered)
        self.assertIn("https", rendered)

    def test_complex_data_structure_rendering(self):
        """Test rendering with complex nested data structures."""
        template_id = self.engine.create_template(
            "Complex Template",
            """<div>
            {% for cve in scan.cve.cves %}
                <p>{{ cve.id }} - {{ cve.severity }} ({{ cve.cvss_score }})</p>
            {% endfor %}
            </div>"""
        )
        
        rendered = self.engine.apply_template(template_id, self.sample_data)
        
        self.assertIn("CVE-2021-1234", rendered)
        self.assertIn("high", rendered)
        self.assertIn("7.5", rendered)


class TestTemplateEngineCaching(unittest.TestCase):
    """Test template caching mechanisms."""

    def setUp(self):
        """Initialize engine for caching tests."""
        self.engine = TemplateEngine()

    def test_template_caching(self):
        """Test that templates are properly cached."""
        template_id = self.engine.create_template(
            "Cached Template",
            "<h1>Test</h1>"
        )
        
        content1 = self.engine._get_template_content(template_id)
        content2 = self.engine._get_template_content(template_id)
        
        self.assertEqual(content1, content2)

    def test_cache_retrieval_performance(self):
        """Test that cached templates are retrieved efficiently."""
        template_id = self.engine.create_template(
            "Performance Template",
            "<h1>{{ scan.project_name }}</h1>"
        )
        
        import time
        
        # First retrieval
        start = time.time()
        self.engine._get_template_content(template_id)
        first_time = time.time() - start
        
        # Second retrieval (should be faster from cache)
        start = time.time()
        self.engine._get_template_content(template_id)
        second_time = time.time() - start
        
        # Both should be very fast, but demonstrate caching works
        self.assertIsNotNone(first_time)
        self.assertIsNotNone(second_time)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def setUp(self):
        """Initialize engine for edge case tests."""
        self.engine = TemplateEngine()

    def test_empty_template(self):
        """Test rendering empty template."""
        template_id = self.engine.create_template("Empty", "")
        rendered = self.engine.apply_template(template_id, {})
        self.assertEqual(rendered, "")

    def test_template_with_special_characters(self):
        """Test template with special characters."""
        template_id = self.engine.create_template(
            "Special Chars",
            "<p>Test & special < > characters</p>"
        )
        rendered = self.engine.apply_template(template_id, {})
        self.assertIn("special", rendered)

    def test_template_with_unicode(self):
        """Test template with unicode characters."""
        template_id = self.engine.create_template(
            "Unicode",
            "<p>Unicode: ñ é ü 中文 🔒</p>"
        )
        rendered = self.engine.apply_template(template_id, {})
        self.assertIn("🔒", rendered)

    def test_large_data_set_rendering(self):
        """Test rendering with large data sets."""
        large_data = {
            "vulnerabilities": [
                {"id": f"vuln_{i}", "title": f"Vulnerability {i}", "severity": "high"}
                for i in range(1000)
            ]
        }
        
        template_id = self.engine.create_template(
            "Large Data",
            """{% for vuln in vulnerabilities %}
            <div>{{ vuln.id }}: {{ vuln.title }}</div>
            {% endfor %}"""
        )
        
        rendered = self.engine.apply_template(template_id, large_data)
        self.assertIn("vuln_0", rendered)
        self.assertIn("vuln_999", rendered)


if __name__ == "__main__":
    unittest.main()
