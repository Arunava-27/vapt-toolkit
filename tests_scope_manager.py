"""
Tests for scope management functionality.

Tests cover:
- Target type inference
- Target validation
- Scope parsing
- Wildcard expansion
- CIDR expansion
- Preset management
- Export/import
"""

import pytest
import json
import tempfile
from pathlib import Path
from scanner.scope_manager import ScopeManager, ScopeTarget, ParsedScope


class TestTargetTypeInference:
    """Test target type inference."""
    
    def test_infer_url_types(self):
        """Test URL type inference."""
        assert ScopeManager.infer_target_type("https://example.com") == "url"
        assert ScopeManager.infer_target_type("http://example.com:8080/path") == "url"
        assert ScopeManager.infer_target_type("http://192.168.1.1") == "url"
    
    def test_infer_ip_types(self):
        """Test IP type inference."""
        assert ScopeManager.infer_target_type("192.168.1.1") == "ip"
        assert ScopeManager.infer_target_type("10.0.0.0/8") == "ip"
        assert ScopeManager.infer_target_type("172.16.0.1") == "ip"
    
    def test_infer_domain_types(self):
        """Test domain type inference."""
        assert ScopeManager.infer_target_type("example.com") == "domain"
        assert ScopeManager.infer_target_type("sub.example.com") == "domain"
        assert ScopeManager.infer_target_type("example.co.uk") == "domain"
        assert ScopeManager.infer_target_type("example.com:8080") == "domain"
    
    def test_infer_wildcard_types(self):
        """Test wildcard type inference."""
        assert ScopeManager.infer_target_type("*.example.com") == "wildcard"
        assert ScopeManager.infer_target_type("sub.*.example.com") == "wildcard"
    
    def test_infer_endpoint_types(self):
        """Test endpoint type inference."""
        assert ScopeManager.infer_target_type("/admin/login") == "endpoint"
        assert ScopeManager.infer_target_type("/api/v1/users") == "endpoint"


class TestTargetValidation:
    """Test target validation."""
    
    def test_validate_valid_urls(self):
        """Test validation of valid URLs."""
        assert ScopeManager.validate_url("https://example.com") is None
        assert ScopeManager.validate_url("http://example.com:8080") is None
        assert ScopeManager.validate_url("https://192.168.1.1") is None
    
    def test_validate_invalid_urls(self):
        """Test validation of invalid URLs."""
        assert ScopeManager.validate_url("ftp://example.com") is not None
        assert ScopeManager.validate_url("https://") is not None
    
    def test_validate_valid_ips(self):
        """Test validation of valid IPs."""
        assert ScopeManager.validate_ip("192.168.1.1") is None
        assert ScopeManager.validate_ip("10.0.0.0/8") is None
        assert ScopeManager.validate_ip("::1") is None  # IPv6
    
    def test_validate_invalid_ips(self):
        """Test validation of invalid IPs."""
        assert ScopeManager.validate_ip("999.999.999.999") is not None
        assert ScopeManager.validate_ip("192.168.1.0/33") is not None
    
    def test_validate_valid_domains(self):
        """Test validation of valid domains."""
        assert ScopeManager.validate_domain("example.com") is None
        assert ScopeManager.validate_domain("sub.example.com") is None
        assert ScopeManager.validate_domain("example.co.uk") is None
    
    def test_validate_invalid_domains(self):
        """Test validation of invalid domains."""
        assert ScopeManager.validate_domain("example-.com") is not None
        assert ScopeManager.validate_domain("-example.com") is not None
    
    def test_validate_wildcards(self):
        """Test wildcard validation."""
        assert ScopeManager.validate_wildcard("*.example.com") is None
        assert ScopeManager.validate_wildcard("*.*.example.com") is None
        assert ScopeManager.validate_wildcard("*.*.*.*") is None
    
    def test_validate_target_generic(self):
        """Test generic target validation."""
        # Valid targets
        assert ScopeManager.validate_target("https://example.com") is None
        assert ScopeManager.validate_target("192.168.1.1") is None
        assert ScopeManager.validate_target("example.com") is None
        assert ScopeManager.validate_target("*.example.com") is None
        
        # Invalid targets
        assert ScopeManager.validate_target("") is not None
        assert ScopeManager.validate_target("invalid") is not None


class TestScopeParsing:
    """Test scope parsing and validation."""
    
    def test_parse_valid_scope(self):
        """Test parsing valid scope."""
        targets = [
            "https://example.com",
            "192.168.1.0/24",
            "sub.example.com",
            "*.api.example.com",
        ]
        parsed = ScopeManager.parse_scope(targets)
        
        assert len(parsed) == 4
        assert len(parsed.errors) == 0
        assert parsed.targets[0].type == "url"
        assert parsed.targets[1].target_type == "ip"
        assert parsed.targets[2].target_type == "domain"
        assert parsed.targets[3].target_type == "wildcard"
    
    def test_parse_scope_with_errors(self):
        """Test parsing scope with errors."""
        targets = [
            "https://example.com",
            "invalid",
            "192.168.1.1",
            "999.999.999.999",  # Invalid IP
        ]
        parsed = ScopeManager.parse_scope(targets)
        
        assert len(parsed) == 2  # Only 2 valid targets
        assert len(parsed.errors) == 2  # 2 errors
    
    def test_parse_scope_no_duplicates(self):
        """Test parsing scope removes duplicates."""
        targets = [
            "example.com",
            "example.com",  # Duplicate
            "EXAMPLE.COM",  # Case-insensitive duplicate
        ]
        parsed = ScopeManager.parse_scope(targets, allow_duplicates=False)
        
        assert len(parsed) == 1
        assert len(parsed.errors) == 2
    
    def test_parse_scope_with_duplicates(self):
        """Test parsing scope allows duplicates."""
        targets = [
            "example.com",
            "example.com",
        ]
        parsed = ScopeManager.parse_scope(targets, allow_duplicates=True)
        
        assert len(parsed) == 2
        assert len(parsed.errors) == 0


class TestScopeExpansion:
    """Test scope expansion."""
    
    def test_expand_cidr_notation(self):
        """Test CIDR notation expansion."""
        targets = ["192.168.1.0/30"]
        expanded = ScopeManager.expand_scope(targets)
        
        assert len(expanded) == 1
        assert "192.168.1.0" in expanded[0]
        assert "192.168.1.3" in expanded[0]
    
    def test_expand_mixed_targets(self):
        """Test expansion of mixed target types."""
        targets = [
            "example.com",
            "10.0.0.0/24",
            "*.api.example.com",
        ]
        expanded = ScopeManager.expand_scope(targets)
        
        assert len(expanded) == 3
        assert expanded[0] == "example.com"
        assert "10.0.0" in expanded[1]


class TestScopeExport:
    """Test scope export functionality."""
    
    def test_export_json(self):
        """Test JSON export."""
        targets = ["example.com", "192.168.1.1"]
        exported = ScopeManager.export_scope(targets, format="json")
        
        data = json.loads(exported)
        assert data["targets"] == targets
    
    def test_export_yaml(self):
        """Test YAML export."""
        targets = ["example.com", "192.168.1.1"]
        exported = ScopeManager.export_scope(targets, format="yaml")
        
        assert "targets:" in exported
        assert "- example.com" in exported
        assert "- 192.168.1.1" in exported
    
    def test_export_txt(self):
        """Test TXT export."""
        targets = ["example.com", "192.168.1.1"]
        exported = ScopeManager.export_scope(targets, format="txt")
        
        lines = exported.strip().split("\n")
        assert len(lines) == 2
        assert "example.com" in lines
        assert "192.168.1.1" in lines
    
    def test_export_invalid_format(self):
        """Test export with invalid format."""
        targets = ["example.com"]
        
        with pytest.raises(ValueError):
            ScopeManager.export_scope(targets, format="invalid")


class TestScopeImport:
    """Test scope import functionality."""
    
    def test_import_json(self):
        """Test JSON import."""
        content = json.dumps({"targets": ["example.com", "192.168.1.1"]})
        targets = ScopeManager.import_scope(content, format="json")
        
        assert targets == ["example.com", "192.168.1.1"]
    
    def test_import_json_list(self):
        """Test JSON import with direct list."""
        content = json.dumps(["example.com", "192.168.1.1"])
        targets = ScopeManager.import_scope(content, format="json")
        
        assert targets == ["example.com", "192.168.1.1"]
    
    def test_import_yaml(self):
        """Test YAML import."""
        content = """targets:
  - example.com
  - 192.168.1.1"""
        targets = ScopeManager.import_scope(content, format="yaml")
        
        assert targets == ["example.com", "192.168.1.1"]
    
    def test_import_txt(self):
        """Test TXT import."""
        content = """example.com
192.168.1.1
# This is a comment
10.0.0.0/8"""
        targets = ScopeManager.import_scope(content, format="txt")
        
        assert len(targets) == 3
        assert "example.com" in targets
        assert "# This is a comment" not in targets
    
    def test_import_invalid_json(self):
        """Test import with invalid JSON."""
        content = "{ invalid json }"
        
        with pytest.raises(ValueError):
            ScopeManager.import_scope(content, format="json")


class TestScopeValidationForScanning:
    """Test scope validation for scanning."""
    
    def test_validate_scope_empty(self):
        """Test validation of empty scope."""
        valid, errors = ScopeManager.validate_scope_for_scanning([])
        
        assert not valid
        assert len(errors) > 0
    
    def test_validate_scope_valid(self):
        """Test validation of valid scope."""
        targets = ["example.com", "192.168.1.1"]
        valid, errors = ScopeManager.validate_scope_for_scanning(targets)
        
        assert valid
        assert len(errors) == 0
    
    def test_validate_scope_invalid_targets(self):
        """Test validation with invalid targets."""
        targets = ["example.com", "invalid", "999.999.999.999"]
        valid, errors = ScopeManager.validate_scope_for_scanning(targets)
        
        assert not valid
        assert len(errors) > 0


class TestScopeSummary:
    """Test scope summary generation."""
    
    def test_empty_scope_summary(self):
        """Test summary for empty scope."""
        summary = ScopeManager.get_scope_summary([])
        
        assert "No scope" in summary
    
    def test_single_target_summary(self):
        """Test summary for single target."""
        summary = ScopeManager.get_scope_summary(["example.com"])
        
        assert "example.com" in summary
    
    def test_multiple_targets_summary(self):
        """Test summary for multiple targets."""
        targets = ["example.com", "192.168.1.1", "api.example.com", "10.0.0.0/8"]
        summary = ScopeManager.get_scope_summary(targets, max_items=3)
        
        assert "example.com" in summary
        assert "..." in summary


class TestScopeTargetDataclass:
    """Test ScopeTarget dataclass."""
    
    def test_scope_target_creation(self):
        """Test creating a scope target."""
        target = ScopeTarget(
            value="example.com",
            target_type="domain",
            error=None,
            group="production"
        )
        
        assert target.value == "example.com"
        assert target.target_type == "domain"
        assert target.error is None
        assert target.group == "production"
    
    def test_scope_target_to_dict(self):
        """Test converting scope target to dict."""
        target = ScopeTarget(
            value="example.com",
            target_type="domain",
        )
        
        data = target.to_dict()
        assert data["value"] == "example.com"
        assert data["target_type"] == "domain"


class TestParsedScope:
    """Test ParsedScope dataclass."""
    
    def test_parsed_scope_len(self):
        """Test getting length of parsed scope."""
        targets = [
            ScopeTarget("example.com", "domain"),
            ScopeTarget("192.168.1.1", "ip", error="Invalid"),
            ScopeTarget("*.api.example.com", "wildcard"),
        ]
        parsed = ParsedScope(targets=targets)
        
        assert len(parsed) == 2  # Only valid targets
    
    def test_parsed_scope_iter(self):
        """Test iterating over parsed scope."""
        targets = [
            ScopeTarget("example.com", "domain"),
            ScopeTarget("192.168.1.1", "ip", error="Invalid"),
            ScopeTarget("*.api.example.com", "wildcard"),
        ]
        parsed = ParsedScope(targets=targets)
        
        values = list(parsed)
        assert len(values) == 2
        assert "example.com" in values


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
