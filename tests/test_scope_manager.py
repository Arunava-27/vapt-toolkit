"""
Comprehensive unit tests for scanner/scope_manager.py - Scope validation and management.
"""
import pytest
import json
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path
import tempfile
import os

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from scanner.scope_manager import ScopeManager, ScopeTarget, ParsedScope
except ImportError:
    pytest.skip("scope_manager module not available", allow_module_level=True)


class TestScopeTargetClass:
    """Test ScopeTarget data class."""
    
    def test_scope_target_url(self):
        """Test creating a URL scope target."""
        target = ScopeTarget(
            value="https://example.com",
            target_type="url"
        )
        
        assert target.value == "https://example.com"
        assert target.target_type == "url"
        assert target.error is None
    
    def test_scope_target_with_error(self):
        """Test creating a scope target with error."""
        target = ScopeTarget(
            value="invalid",
            target_type="url",
            error="Invalid URL format"
        )
        
        assert target.error == "Invalid URL format"


class TestParsedScope:
    """Test ParsedScope data class."""
    
    def test_parsed_scope_creation(self):
        """Test creating a ParsedScope."""
        targets = [
            ScopeTarget("https://example.com", "url"),
            ScopeTarget("example.com", "domain")
        ]
        
        scope = ParsedScope(targets=targets, errors=[])
        
        assert len(scope.targets) == 2
        assert len(scope.errors) == 0
    
    def test_parsed_scope_length(self):
        """Test ParsedScope __len__ method."""
        targets = [
            ScopeTarget("https://example.com", "url"),
            ScopeTarget("example.com", "domain")
        ]
        
        scope = ParsedScope(targets=targets, errors=[])
        
        assert len(scope) == 2
    
    def test_parsed_scope_iteration(self):
        """Test iterating over ParsedScope."""
        targets = [
            ScopeTarget("https://example.com", "url"),
            ScopeTarget("example.com", "domain")
        ]
        
        scope = ParsedScope(targets=targets, errors=[])
        
        for i, target in enumerate(scope):
            assert target == targets[i]


@pytest.fixture
def scope_manager():
    """Create a ScopeManager instance for testing."""
    return ScopeManager()


class TestTargetTypeInference:
    """Test inferring target type."""
    
    def test_infer_url_type(self, scope_manager):
        """Test inferring URL target type."""
        target_type = scope_manager.infer_target_type("https://example.com")
        assert target_type == "url"
        
        target_type = scope_manager.infer_target_type("http://example.com:8080")
        assert target_type == "url"
    
    def test_infer_domain_type(self, scope_manager):
        """Test inferring domain target type."""
        target_type = scope_manager.infer_target_type("example.com")
        assert target_type == "domain"
    
    def test_infer_ip_type(self, scope_manager):
        """Test inferring IP address target type."""
        target_type = scope_manager.infer_target_type("192.168.1.1")
        assert target_type == "ip"
        
        target_type = scope_manager.infer_target_type("2001:db8::1")
        assert target_type == "ip"
    
    def test_infer_cidr_type(self, scope_manager):
        """Test inferring CIDR range target type."""
        target_type = scope_manager.infer_target_type("10.0.0.0/8")
        assert target_type == "cidr"
    
    def test_infer_wildcard_type(self, scope_manager):
        """Test inferring wildcard target type."""
        target_type = scope_manager.infer_target_type("*.example.com")
        assert target_type == "wildcard"


class TestURLValidation:
    """Test URL validation."""
    
    def test_validate_https_url(self, scope_manager):
        """Test validating HTTPS URL."""
        result = scope_manager.validate_url("https://example.com")
        assert result["valid"] is True
    
    def test_validate_http_url(self, scope_manager):
        """Test validating HTTP URL."""
        result = scope_manager.validate_url("http://example.com")
        assert result["valid"] is True
    
    def test_validate_url_with_port(self, scope_manager):
        """Test validating URL with port."""
        result = scope_manager.validate_url("https://example.com:8443")
        assert result["valid"] is True
    
    def test_validate_url_with_path(self, scope_manager):
        """Test validating URL with path."""
        result = scope_manager.validate_url("https://example.com/api/v1")
        assert result["valid"] is True
    
    def test_validate_invalid_url(self, scope_manager):
        """Test validating invalid URL."""
        result = scope_manager.validate_url("not a url")
        assert result["valid"] is False


class TestDomainValidation:
    """Test domain validation."""
    
    def test_validate_domain(self, scope_manager):
        """Test validating domain."""
        result = scope_manager.validate_domain("example.com")
        assert result["valid"] is True
    
    def test_validate_subdomain(self, scope_manager):
        """Test validating subdomain."""
        result = scope_manager.validate_domain("api.example.com")
        assert result["valid"] is True
    
    def test_validate_domain_with_port(self, scope_manager):
        """Test validating domain with port."""
        result = scope_manager.validate_domain("example.com:8443")
        assert result["valid"] is True
    
    def test_validate_invalid_domain(self, scope_manager):
        """Test validating invalid domain."""
        result = scope_manager.validate_domain("not valid domain!")
        assert result["valid"] is False


class TestIPValidation:
    """Test IP address validation."""
    
    def test_validate_ipv4(self, scope_manager):
        """Test validating IPv4 address."""
        result = scope_manager.validate_ip("192.168.1.1")
        assert result["valid"] is True
    
    def test_validate_ipv6(self, scope_manager):
        """Test validating IPv6 address."""
        result = scope_manager.validate_ip("2001:db8::1")
        assert result["valid"] is True
    
    def test_validate_invalid_ip(self, scope_manager):
        """Test validating invalid IP."""
        result = scope_manager.validate_ip("256.256.256.256")
        assert result["valid"] is False


class TestCIDRValidation:
    """Test CIDR range validation and expansion."""
    
    def test_validate_cidr(self, scope_manager):
        """Test validating CIDR range."""
        result = scope_manager.validate_cidr("10.0.0.0/24")
        assert result["valid"] is True
    
    def test_expand_cidr_small(self, scope_manager):
        """Test expanding small CIDR range."""
        ips = scope_manager.expand_cidr("192.168.1.0/30")
        
        # /30 gives 4 IPs (2 usable)
        assert len(ips) == 4
        assert "192.168.1.0" in ips
        assert "192.168.1.3" in ips
    
    def test_expand_cidr_large_limited(self, scope_manager):
        """Test expanding large CIDR range (should be limited)."""
        ips = scope_manager.expand_cidr("10.0.0.0/8")
        
        # Should be limited to prevent explosion
        assert len(ips) <= 1000


class TestWildcardExpansion:
    """Test wildcard target handling."""
    
    def test_validate_wildcard(self, scope_manager):
        """Test validating wildcard."""
        result = scope_manager.validate_wildcard("*.example.com")
        assert result["valid"] is True
    
    def test_expand_wildcard_simple(self, scope_manager):
        """Test expanding simple wildcard."""
        subdomains = scope_manager.expand_wildcard("*.example.com")
        
        # Should return common subdomains
        assert len(subdomains) > 0
        assert any("example.com" in s for s in subdomains)


class TestScopeTargetValidation:
    """Test generic target validation."""
    
    def test_validate_target_url(self, scope_manager):
        """Test validating URL target."""
        result = scope_manager.validate_target("https://example.com")
        assert result["valid"] is True
    
    def test_validate_target_domain(self, scope_manager):
        """Test validating domain target."""
        result = scope_manager.validate_target("example.com")
        assert result["valid"] is True
    
    def test_validate_target_ip(self, scope_manager):
        """Test validating IP target."""
        result = scope_manager.validate_target("192.168.1.1")
        assert result["valid"] is True
    
    def test_validate_target_cidr(self, scope_manager):
        """Test validating CIDR target."""
        result = scope_manager.validate_target("10.0.0.0/24")
        assert result["valid"] is True


class TestScopeParsingAndValidation:
    """Test parsing multi-target scope."""
    
    def test_parse_mixed_scope(self, scope_manager, sample_scope_targets):
        """Test parsing mixed scope targets."""
        mixed_targets = sample_scope_targets["mixed"]
        
        parsed = scope_manager.parse_scope(mixed_targets)
        
        assert len(parsed.targets) > 0
        assert len(parsed.errors) == 0 or all(e for e in parsed.errors)
    
    def test_parse_scope_with_invalid_targets(self, scope_manager):
        """Test parsing scope with invalid targets."""
        targets = [
            "https://example.com",
            "not a valid target!!!",
            "192.168.1.1"
        ]
        
        parsed = scope_manager.parse_scope(targets)
        
        assert len(parsed.targets) >= 2
        assert len(parsed.errors) > 0


class TestScopePresets:
    """Test scope preset save/load functionality."""
    
    def test_save_preset(self, scope_manager):
        """Test saving a scope preset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(scope_manager, 'preset_dir', tmpdir):
                preset = {
                    "name": "test_preset",
                    "targets": ["https://example.com", "example.com"]
                }
                
                scope_manager.save_preset("test_preset", preset["targets"])
                
                # Verify file was created
                preset_file = Path(tmpdir) / "test_preset.json"
                assert preset_file.exists()
    
    def test_load_preset(self, scope_manager):
        """Test loading a scope preset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            preset_file = Path(tmpdir) / "test_preset.json"
            preset_data = {
                "name": "test_preset",
                "targets": ["https://example.com"]
            }
            preset_file.write_text(json.dumps(preset_data))
            
            with patch.object(scope_manager, 'preset_dir', tmpdir):
                loaded = scope_manager.load_preset("test_preset")
                
                assert loaded["targets"] == preset_data["targets"]
    
    def test_list_presets(self, scope_manager):
        """Test listing available presets."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir).joinpath("preset1.json").write_text("{}")
            Path(tmpdir).joinpath("preset2.json").write_text("{}")
            
            with patch.object(scope_manager, 'preset_dir', tmpdir):
                presets = scope_manager.list_presets()
                
                assert len(presets) == 2


class TestScopeExport:
    """Test exporting scope."""
    
    def test_export_scope_json(self, scope_manager):
        """Test exporting scope as JSON."""
        targets = ["https://example.com", "example.com"]
        
        json_output = scope_manager.export_scope(targets, format="json")
        
        assert json_output is not None
        parsed = json.loads(json_output)
        assert len(parsed["targets"]) > 0
    
    def test_export_scope_yaml(self, scope_manager):
        """Test exporting scope as YAML."""
        targets = ["https://example.com"]
        
        yaml_output = scope_manager.export_scope(targets, format="yaml")
        
        assert yaml_output is not None
        assert "targets" in yaml_output
    
    def test_export_scope_txt(self, scope_manager):
        """Test exporting scope as TXT."""
        targets = ["https://example.com", "example.com"]
        
        txt_output = scope_manager.export_scope(targets, format="txt")
        
        assert txt_output is not None
        assert "example.com" in txt_output
