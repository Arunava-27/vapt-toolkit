"""
Tests for the Verification Hints module.
"""

import pytest
from scanner.web.verification_hints import VerificationHints, VerificationHint


class TestVerificationHints:
    """Test suite for VerificationHints class."""

    def test_sql_injection_hints(self):
        """Test SQL injection hints generation."""
        hints = VerificationHints.get_sql_injection_hints()
        assert isinstance(hints, VerificationHint)
        assert hints.title == "SQL Injection Verification"
        assert len(hints.steps) > 0
        assert len(hints.tools) > 0
        assert len(hints.expected_signs) > 0
        assert len(hints.false_positive_indicators) > 0

    def test_xss_hints(self):
        """Test XSS hints generation."""
        hints = VerificationHints.get_xss_hints()
        assert isinstance(hints, VerificationHint)
        assert hints.title == "Cross-Site Scripting (XSS) Verification"
        assert "script" in hints.description.lower()
        assert len(hints.steps) > 0

    def test_csrf_hints(self):
        """Test CSRF hints generation."""
        hints = VerificationHints.get_csrf_hints()
        assert isinstance(hints, VerificationHint)
        assert "CSRF" in hints.title
        assert "token" in [s.lower() for s in hints.steps] or any("token" in s.lower() for s in hints.steps)

    def test_idor_hints(self):
        """Test IDOR hints generation."""
        hints = VerificationHints.get_idor_hints()
        assert isinstance(hints, VerificationHint)
        assert "IDOR" in hints.title
        assert len(hints.steps) >= 7

    def test_authentication_hints(self):
        """Test authentication hints generation."""
        hints = VerificationHints.get_authentication_hints()
        assert isinstance(hints, VerificationHint)
        assert "Authentication" in hints.title
        assert len(hints.tools) > 0

    def test_authorization_hints(self):
        """Test authorization hints generation."""
        hints = VerificationHints.get_authorization_hints()
        assert isinstance(hints, VerificationHint)
        assert "Authorization" in hints.title

    def test_ssrf_hints(self):
        """Test SSRF hints generation."""
        hints = VerificationHints.get_ssrf_hints()
        assert isinstance(hints, VerificationHint)
        assert "SSRF" in hints.title

    def test_file_upload_hints(self):
        """Test file upload hints generation."""
        hints = VerificationHints.get_file_upload_hints()
        assert isinstance(hints, VerificationHint)
        assert "File Upload" in hints.title

    def test_path_traversal_hints(self):
        """Test path traversal hints generation."""
        hints = VerificationHints.get_path_traversal_hints()
        assert isinstance(hints, VerificationHint)
        assert "Path Traversal" in hints.title

    def test_misconfiguration_hints(self):
        """Test misconfiguration hints generation."""
        hints = VerificationHints.get_misconfiguration_hints()
        assert isinstance(hints, VerificationHint)
        assert "Misconfiguration" in hints.title

    def test_business_logic_hints(self):
        """Test business logic hints generation."""
        hints = VerificationHints.get_business_logic_hints()
        assert isinstance(hints, VerificationHint)
        assert "Business Logic" in hints.title

    def test_rate_limiting_hints(self):
        """Test rate limiting hints generation."""
        hints = VerificationHints.get_rate_limiting_hints()
        assert isinstance(hints, VerificationHint)
        assert "Rate Limiting" in hints.title

    def test_get_hints_for_type_sql_injection(self):
        """Test getting hints by type for SQL injection."""
        hints = VerificationHints.get_hints_for_type("SQL_INJECTION")
        assert hints is not None
        assert hints.title == "SQL Injection Verification"

    def test_get_hints_for_type_xss(self):
        """Test getting hints by type for XSS."""
        hints = VerificationHints.get_hints_for_type("XSS")
        assert hints is not None
        assert "XSS" in hints.title

    def test_get_hints_for_type_csrf(self):
        """Test getting hints by type for CSRF."""
        hints = VerificationHints.get_hints_for_type("CSRF")
        assert hints is not None

    def test_get_hints_for_type_idor(self):
        """Test getting hints by type for IDOR."""
        hints = VerificationHints.get_hints_for_type("IDOR")
        assert hints is not None

    def test_get_hints_for_type_authentication(self):
        """Test getting hints by type for authentication."""
        hints = VerificationHints.get_hints_for_type("AUTHENTICATION")
        assert hints is not None

    def test_get_hints_for_type_authorization(self):
        """Test getting hints by type for authorization."""
        hints = VerificationHints.get_hints_for_type("AUTHORIZATION")
        assert hints is not None

    def test_get_hints_for_type_ssrf(self):
        """Test getting hints by type for SSRF."""
        hints = VerificationHints.get_hints_for_type("SSRF")
        assert hints is not None

    def test_get_hints_for_type_file_upload(self):
        """Test getting hints by type for file upload."""
        hints = VerificationHints.get_hints_for_type("FILE_UPLOAD")
        assert hints is not None

    def test_get_hints_for_type_path_traversal(self):
        """Test getting hints by type for path traversal."""
        hints = VerificationHints.get_hints_for_type("PATH_TRAVERSAL")
        assert hints is not None

    def test_get_hints_for_type_misconfiguration(self):
        """Test getting hints by type for misconfiguration."""
        hints = VerificationHints.get_hints_for_type("MISCONFIGURATION")
        assert hints is not None

    def test_get_hints_for_type_business_logic(self):
        """Test getting hints by type for business logic."""
        hints = VerificationHints.get_hints_for_type("BUSINESS_LOGIC")
        assert hints is not None

    def test_get_hints_for_type_rate_limiting(self):
        """Test getting hints by type for rate limiting."""
        hints = VerificationHints.get_hints_for_type("RATE_LIMITING")
        assert hints is not None

    def test_get_hints_for_type_invalid(self):
        """Test getting hints for invalid type."""
        hints = VerificationHints.get_hints_for_type("INVALID_TYPE")
        assert hints is None

    def test_get_all_hints(self):
        """Test getting all hints."""
        all_hints = VerificationHints.get_all_hints()
        assert isinstance(all_hints, dict)
        assert len(all_hints) == 12
        assert "SQL_INJECTION" in all_hints
        assert "XSS" in all_hints
        assert "CSRF" in all_hints
        assert "IDOR" in all_hints
        assert "AUTHENTICATION" in all_hints
        assert "AUTHORIZATION" in all_hints
        assert "SSRF" in all_hints
        assert "FILE_UPLOAD" in all_hints
        assert "PATH_TRAVERSAL" in all_hints
        assert "MISCONFIGURATION" in all_hints
        assert "BUSINESS_LOGIC" in all_hints
        assert "RATE_LIMITING" in all_hints

    def test_verification_hint_structure(self):
        """Test that hints have all required fields."""
        hints = VerificationHints.get_sql_injection_hints()
        assert hasattr(hints, 'title')
        assert hasattr(hints, 'description')
        assert hasattr(hints, 'steps')
        assert hasattr(hints, 'tools')
        assert hasattr(hints, 'expected_signs')
        assert hasattr(hints, 'false_positive_indicators')

    def test_hints_have_content(self):
        """Test that all hints contain meaningful content."""
        all_hints = VerificationHints.get_all_hints()
        for hint_type, hint in all_hints.items():
            assert hint.title, f"Hint {hint_type} missing title"
            assert hint.description, f"Hint {hint_type} missing description"
            assert hint.steps, f"Hint {hint_type} missing steps"
            assert len(hint.steps) >= 5, f"Hint {hint_type} has fewer than 5 steps"
            assert hint.tools, f"Hint {hint_type} missing tools"
            assert hint.expected_signs, f"Hint {hint_type} missing expected signs"
            assert hint.false_positive_indicators, f"Hint {hint_type} missing false positive indicators"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
