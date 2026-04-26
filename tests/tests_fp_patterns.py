"""
Unit tests for False Positive Pattern Database

Tests cover:
- Pattern matching logic
- Confidence adjustment calculations
- Custom pattern creation and management
- Edge cases and regex validation
"""

import pytest
import json
from scanner.web.fp_pattern_database import (
    FalsePositivePatternDB,
    FPPattern,
    FPPatternType
)


@pytest.fixture
def fp_db():
    """Create a fresh FP database instance for each test"""
    return FalsePositivePatternDB()


class TestPatternMatching:
    """Test pattern matching functionality"""

    def test_builtin_patterns_loaded(self, fp_db):
        """Verify built-in patterns are loaded"""
        assert len(fp_db.patterns) > 20
        assert len(fp_db.compiled_patterns) > 20

    def test_vue_xss_pattern_match(self, fp_db):
        """Test Vue.js auto-escape pattern matching"""
        finding = {
            "title": "XSS Vulnerability",
            "response_body": "Vue.js framework detected",
            "description": "Reflected input in Vue template"
        }
        is_fp, reason, patterns = fp_db.check_finding_against_patterns(finding)
        assert "xss_vue_auto_escape" in patterns
        assert len(patterns) > 0

    def test_react_xss_pattern_match(self, fp_db):
        """Test React JSX pattern matching"""
        finding = {
            "title": "XSS Vulnerability",
            "response_body": "import React from 'react';",
            "description": "Potential XSS in JSX"
        }
        is_fp, reason, patterns = fp_db.check_finding_against_patterns(finding)
        assert "xss_react_jsx_escape" in patterns

    def test_django_csrf_pattern_match(self, fp_db):
        """Test Django CSRF pattern matching"""
        finding = {
            "title": "Missing CSRF Token",
            "response_body": "{% csrf_token %}",
            "description": "Form submission without token"
        }
        is_fp, reason, patterns = fp_db.check_finding_against_patterns(finding)
        assert "csrf_django_token" in patterns

    def test_sql_parameterized_pattern_match(self, fp_db):
        """Test SQL parameterization pattern matching"""
        finding = {
            "title": "SQL Injection",
            "description": "Prepared statement with parameterized query",
            "response_body": "user_id = ?"
        }
        is_fp, reason, patterns = fp_db.check_finding_against_patterns(finding)
        assert "sql_parameterized_query" in patterns

    def test_orm_sql_pattern_match(self, fp_db):
        """Test ORM framework pattern matching"""
        finding = {
            "title": "SQL Injection",
            "response_body": "SQLAlchemy ORM",
            "description": "Database query using ORM"
        }
        is_fp, reason, patterns = fp_db.check_finding_against_patterns(finding)
        assert "sql_orm_safe" in patterns

    def test_jwt_auth_pattern_match(self, fp_db):
        """Test JWT authentication pattern matching"""
        finding = {
            "title": "Authentication Weakness",
            "response_body": "Bearer eyJhbGc... RS256",
            "description": "JWT with RS256 algorithm"
        }
        is_fp, reason, patterns = fp_db.check_finding_against_patterns(finding)
        assert "auth_jwt_valid" in patterns

    def test_rate_limit_pattern_match(self, fp_db):
        """Test rate limit pattern matching"""
        finding = {
            "title": "No Rate Limiting",
            "response_body": "429 Too Many Requests",
            "description": "Rate limit test triggered"
        }
        is_fp, reason, patterns = fp_db.check_finding_against_patterns(finding)
        assert "rate_limit_implemented" in patterns

    def test_csp_xss_pattern_match(self, fp_db):
        """Test CSP policy pattern matching"""
        finding = {
            "title": "XSS Vulnerability",
            "response_headers": "Content-Security-Policy: default-src 'self'",
            "description": "Inline script execution"
        }
        is_fp, reason, patterns = fp_db.check_finding_against_patterns(finding)
        assert "xss_csp_strict" in patterns

    def test_cors_localhost_pattern_match(self, fp_db):
        """Test localhost CORS pattern matching"""
        finding = {
            "title": "CORS Allow Origin *",
            "response_headers": {"Access-Control-Allow-Origin": "*"},
            "response_body": "localhost:3000",
            "description": "CORS misconfiguration"
        }
        is_fp, reason, patterns = fp_db.check_finding_against_patterns(finding)
        assert "cors_localhost_dev" in patterns

    def test_test_credentials_pattern_match(self, fp_db):
        """Test demo credentials pattern matching"""
        finding = {
            "title": "Hardcoded Credentials",
            "response_body": "username: test, password: test123",
            "description": "Sensitive data in response"
        }
        is_fp, reason, patterns = fp_db.check_finding_against_patterns(finding)
        assert "sensitive_data_test_cred" in patterns

    def test_no_pattern_match(self, fp_db):
        """Test finding with no matching patterns"""
        finding = {
            "title": "Some Vulnerability",
            "description": "Unique finding without framework indicators"
        }
        is_fp, reason, patterns = fp_db.check_finding_against_patterns(finding)
        assert len(patterns) == 0
        assert not is_fp


class TestConfidenceAdjustment:
    """Test confidence score adjustment logic"""

    def test_no_match_adjustment(self, fp_db):
        """No patterns matched = no adjustment"""
        finding = {
            "title": "Vulnerability",
            "description": "Some finding"
        }
        adjustment = fp_db.get_confidence_adjustment(finding)
        assert adjustment == 1.0

    def test_single_pattern_adjustment(self, fp_db):
        """Single pattern match applies its severity impact"""
        finding = {
            "title": "XSS",
            "response_body": "Vue.js framework"
        }
        adjustment = fp_db.get_confidence_adjustment(finding)
        assert 0.3 <= adjustment < 1.0

    def test_multiple_pattern_adjustment(self, fp_db):
        """Multiple pattern matches compound the adjustment"""
        finding = {
            "title": "XSS",
            "response_body": "Vue.js CSP policy default-src 'self'",
            "response_headers": "Content-Security-Policy: default-src 'self'"
        }
        adjustment = fp_db.get_confidence_adjustment(finding)
        # Should be compounded lower
        assert adjustment < 0.8

    def test_adjustment_bounds(self, fp_db):
        """Adjustment always stays in valid range"""
        for i in range(100):
            finding = {
                "title": f"Test {i}",
                "description": "Vue React Angular Django Rails Spring"
            }
            adjustment = fp_db.get_confidence_adjustment(finding)
            assert 0.3 <= adjustment <= 1.0


class TestCustomPatterns:
    """Test custom pattern creation and management"""

    def test_add_custom_pattern(self, fp_db):
        """Add a new custom pattern"""
        pattern_dict = {
            "pattern_type": "CUSTOM",
            "description": "Test custom pattern",
            "regex_pattern": r"test_pattern_\d+",
            "severity_impact": 0.5,
            "keywords": ["test"]
        }
        pattern_id = fp_db.add_custom_pattern(pattern_dict)
        assert pattern_id.startswith("custom_")
        assert pattern_id in fp_db.patterns

    def test_custom_pattern_matching(self, fp_db):
        """Custom pattern can match findings"""
        pattern_dict = {
            "pattern_type": "CUSTOM",
            "description": "Custom XSS pattern",
            "regex_pattern": r"echo_user_input|unsafe_print",
            "severity_impact": 0.65
        }
        pattern_id = fp_db.add_custom_pattern(pattern_dict)

        finding = {
            "title": "XSS",
            "description": "Found echo_user_input in code"
        }
        is_fp, reason, patterns = fp_db.check_finding_against_patterns(finding)
        assert pattern_id in patterns

    def test_invalid_regex_pattern(self, fp_db):
        """Invalid regex raises error"""
        pattern_dict = {
            "pattern_type": "CUSTOM",
            "description": "Invalid regex",
            "regex_pattern": r"[invalid(regex",
            "severity_impact": 0.5
        }
        with pytest.raises(Exception):
            fp_db.add_custom_pattern(pattern_dict)

    def test_remove_pattern(self, fp_db):
        """Disable a pattern"""
        pattern_id = "xss_vue_auto_escape"
        assert fp_db.patterns[pattern_id].enabled
        fp_db.remove_pattern(pattern_id)
        assert not fp_db.patterns[pattern_id].enabled

    def test_enable_pattern(self, fp_db):
        """Re-enable a disabled pattern"""
        pattern_id = "xss_vue_auto_escape"
        fp_db.remove_pattern(pattern_id)
        assert not fp_db.patterns[pattern_id].enabled
        fp_db.enable_pattern(pattern_id)
        assert fp_db.patterns[pattern_id].enabled

    def test_list_patterns(self, fp_db):
        """List patterns with filtering"""
        all_patterns = fp_db.list_patterns(enabled_only=False)
        assert len(all_patterns) > 20

        xss_patterns = fp_db.list_patterns(pattern_type="xss_framework")
        assert len(xss_patterns) >= 6
        assert all(p["pattern_type"] == "xss_framework" for p in xss_patterns)

    def test_pattern_stats(self, fp_db):
        """Get pattern statistics"""
        stats = fp_db.get_pattern_stats()
        assert stats["total_patterns"] > 20
        assert stats["enabled_patterns"] > 0
        assert "by_type" in stats
        assert stats["by_type"]["xss_framework"] > 0


class TestFrameworkDetection:
    """Test framework-specific false positive detection"""

    def test_angular_sanitizer_detected(self, fp_db):
        """Angular DomSanitizer pattern"""
        finding = {
            "title": "XSS",
            "response_body": "Angular framework using DomSanitizer",
            "description": "Sanitized HTML output"
        }
        is_fp, reason, patterns = fp_db.check_finding_against_patterns(finding)
        assert "xss_angular_sanitizer" in patterns

    def test_jinja2_autoescape_detected(self, fp_db):
        """Jinja2 autoescape pattern"""
        finding = {
            "title": "XSS",
            "response_body": "Jinja2 templates with autoescape on",
            "description": "Template injection"
        }
        is_fp, reason, patterns = fp_db.check_finding_against_patterns(finding)
        assert "xss_jinja2_autoescape" in patterns

    def test_rails_erb_detected(self, fp_db):
        """Rails ERB template pattern"""
        finding = {
            "title": "XSS",
            "response_body": "<%= escaped_content %>",
            "description": "Rails template injection"
        }
        is_fp, reason, patterns = fp_db.check_finding_against_patterns(finding)
        assert "xss_rails_html_escape" in patterns

    def test_laravel_blade_detected(self, fp_db):
        """Laravel Blade template pattern"""
        finding = {
            "title": "XSS",
            "response_body": "{{ user_input }} in Blade template",
            "description": "Laravel template injection"
        }
        is_fp, reason, patterns = fp_db.check_finding_against_patterns(finding)
        assert "xss_laravel_blade_escape" in patterns

    def test_spring_security_csrf_detected(self, fp_db):
        """Spring Security CSRF pattern"""
        finding = {
            "title": "CSRF",
            "response_body": "X-CSRF-TOKEN: abc123",
            "description": "CSRF token missing"
        }
        is_fp, reason, patterns = fp_db.check_finding_against_patterns(finding)
        assert "csrf_spring_security" in patterns


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_empty_finding(self, fp_db):
        """Empty finding dict"""
        finding = {}
        is_fp, reason, patterns = fp_db.check_finding_against_patterns(finding)
        assert patterns == []

    def test_null_values_in_finding(self, fp_db):
        """Findings with None values"""
        finding = {
            "title": None,
            "description": None,
            "response_body": None
        }
        is_fp, reason, patterns = fp_db.check_finding_against_patterns(finding)
        # Should handle gracefully without crashing

    def test_large_response_body(self, fp_db):
        """Findings with very large response bodies"""
        large_body = "x" * 100000 + "Vue.js framework"
        finding = {
            "title": "XSS",
            "response_body": large_body
        }
        adjustment = fp_db.get_confidence_adjustment(finding)
        assert 0.3 <= adjustment <= 1.0

    def test_case_insensitive_matching(self, fp_db):
        """Pattern matching should be case-insensitive"""
        finding1 = {
            "title": "XSS",
            "response_body": "vue.js"
        }
        finding2 = {
            "title": "XSS",
            "response_body": "Vue.js"
        }
        finding3 = {
            "title": "XSS",
            "response_body": "VUE.JS"
        }
        _, _, patterns1 = fp_db.check_finding_against_patterns(finding1)
        _, _, patterns2 = fp_db.check_finding_against_patterns(finding2)
        _, _, patterns3 = fp_db.check_finding_against_patterns(finding3)
        assert patterns1 == patterns2 == patterns3

    def test_regex_special_chars_in_finding(self, fp_db):
        """Findings with regex special characters"""
        finding = {
            "title": "SQL Injection",
            "response_body": "user_input [*+?{}|()^$\\]"
        }
        # Should not crash
        is_fp, reason, patterns = fp_db.check_finding_against_patterns(finding)

    def test_multiple_framework_indicators(self, fp_db):
        """Finding with multiple framework indicators"""
        finding = {
            "title": "XSS",
            "response_body": "Vue.js React Angular Django"
        }
        is_fp, reason, patterns = fp_db.check_finding_against_patterns(finding)
        # Should match multiple patterns
        assert len(patterns) >= 2


class TestIntegration:
    """Integration tests combining multiple features"""

    def test_full_scan_with_adjustments(self, fp_db):
        """Simulate scanning with confidence adjustments"""
        findings = [
            {
                "id": "1",
                "title": "XSS Vulnerability",
                "description": "Reflected XSS in search",
                "response_body": "Vue.js framework detected",
                "confidence": 75
            },
            {
                "id": "2",
                "title": "SQL Injection",
                "description": "SQL Injection in user ID",
                "response_body": "Parameterized query using ?",
                "confidence": 85
            },
            {
                "id": "3",
                "title": "Missing CSRF Token",
                "description": "Form POST without token",
                "response_body": "Django CSRF middleware",
                "confidence": 70
            },
        ]

        results = []
        for finding in findings:
            adjustment = fp_db.get_confidence_adjustment(finding)
            is_fp, reason, patterns = fp_db.check_finding_against_patterns(finding)
            adjusted_confidence = finding["confidence"] * adjustment
            results.append({
                "id": finding["id"],
                "original_confidence": finding["confidence"],
                "adjusted_confidence": adjusted_confidence,
                "is_likely_fp": is_fp,
                "reason": reason,
                "patterns": patterns
            })

        # Should reduce confidence for framework-specific FPs
        assert results[0]["adjusted_confidence"] < results[0]["original_confidence"]
        assert results[1]["adjusted_confidence"] < results[1]["original_confidence"]
        assert results[2]["adjusted_confidence"] < results[2]["original_confidence"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
