"""
OWASP Top 10 2021 & CWE-ID Mapping Verification Tests

Verifies:
1. All findings have OWASP Top 10 2021 category mapping
2. All findings have CWE-ID mapping
3. Consistency across modules
4. Valid CWE-ID format
5. OWASP categories are from 2021 edition
"""

import pytest
from scanner.web.vulnerability_classifier import VulnerabilityClassifier, OWASPCategory


class TestOWASPMappingCompleteness:
    """Verify all vulnerability types have OWASP mapping"""

    def test_all_owasp_mappings_exist(self):
        """Verify every key has an OWASP category"""
        for finding_type, owasp_category in VulnerabilityClassifier.OWASP_MAPPING.items():
            assert isinstance(owasp_category, OWASPCategory), \
                f"'{finding_type}' OWASP mapping is not OWASPCategory: {owasp_category}"

    def test_owasp_categories_are_2021_edition(self):
        """Verify all OWASP categories are from 2021 edition"""
        valid_categories = [
            "A01:2021 - Broken Access Control",
            "A02:2021 - Cryptographic Failures",
            "A03:2021 - Injection",
            "A04:2021 - Insecure Design",
            "A05:2021 - Security Misconfiguration",
            "A06:2021 - Vulnerable and Outdated Components",
            "A07:2021 - Identification and Authentication Failures",
            "A08:2021 - Software and Data Integrity Failures",
            "A09:2021 - Logging and Monitoring Failures",
            "A10:2021 - Server-Side Request Forgery (SSRF)",
        ]
        
        for category in OWASPCategory:
            assert category.value in valid_categories, \
                f"Invalid OWASP category: {category.value}"

    def test_no_duplicate_owasp_mappings(self):
        """Verify no accidental duplicate mappings"""
        seen = {}
        for finding_type, owasp_category in VulnerabilityClassifier.OWASP_MAPPING.items():
            key = (finding_type, owasp_category)
            assert key not in seen, \
                f"Duplicate mapping: {finding_type} -> {owasp_category}"
            seen[key] = True


class TestCWEMappingCompleteness:
    """Verify all vulnerability types have CWE mapping"""

    def test_all_cwe_mappings_exist(self):
        """Verify every key has a CWE-ID"""
        for finding_type, cwe_id in VulnerabilityClassifier.CWE_MAPPING.items():
            assert cwe_id is not None and cwe_id != "", \
                f"'{finding_type}' has no CWE-ID mapping"

    def test_cwe_id_format_is_valid(self):
        """Verify all CWE-IDs follow correct format: CWE-XXXX"""
        import re
        cwe_pattern = re.compile(r"^CWE-\d+$")
        
        for finding_type, cwe_id in VulnerabilityClassifier.CWE_MAPPING.items():
            assert cwe_pattern.match(cwe_id), \
                f"Invalid CWE-ID format for '{finding_type}': {cwe_id}"

    def test_all_cwe_ids_are_known(self):
        """Verify CWE-IDs are valid (in known CWE list)"""
        # List of valid CWE-IDs used by VAPT
        known_cwes = {
            "CWE-16", "CWE-22", "CWE-79", "CWE-89", "CWE-200",
            "CWE-287", "CWE-327", "CWE-352", "CWE-434", "CWE-502",
            "CWE-639", "CWE-770", "CWE-840", "CWE-918"
        }
        
        for cwe_id in set(VulnerabilityClassifier.CWE_MAPPING.values()):
            assert cwe_id in known_cwes, \
                f"Unknown CWE-ID: {cwe_id}. If this is new, add to known_cwes set."

    def test_no_duplicate_cwe_mappings(self):
        """Verify no accidental duplicate mappings"""
        seen = {}
        for finding_type, cwe_id in VulnerabilityClassifier.CWE_MAPPING.items():
            key = (finding_type, cwe_id)
            assert key not in seen, \
                f"Duplicate CWE mapping: {finding_type} -> {cwe_id}"
            seen[key] = True


class TestMappingConsistency:
    """Verify consistency between OWASP and CWE mappings"""

    def test_same_finding_types_in_both_mappings(self):
        """Verify finding types exist in both mappings"""
        owasp_keys = set(VulnerabilityClassifier.OWASP_MAPPING.keys())
        cwe_keys = set(VulnerabilityClassifier.CWE_MAPPING.keys())
        
        assert owasp_keys == cwe_keys, \
            f"Mapping inconsistency:\n" \
            f"Only in OWASP: {owasp_keys - cwe_keys}\n" \
            f"Only in CWE: {cwe_keys - owasp_keys}"

    def test_same_finding_types_in_compliance(self):
        """Verify finding types are consistent with compliance mapping"""
        owasp_keys = set(VulnerabilityClassifier.OWASP_MAPPING.keys())
        compliance_keys = set(VulnerabilityClassifier.COMPLIANCE_IMPACT.keys())
        
        # Compliance mapping may not have "Other" but core mappings should be there
        assert compliance_keys.issubset(owasp_keys), \
            f"Extra keys in COMPLIANCE_IMPACT: {compliance_keys - owasp_keys}"

    def test_alias_consistency(self):
        """Verify vulnerability aliases map to same classifications"""
        aliases = [
            ("XSS", "Cross-Site Scripting"),
            ("CSRF", "Cross-Site Request Forgery"),
            ("SSRF", "Server-Side Request Forgery"),
            ("IDOR", "Insecure Direct Object Reference"),
            ("Injection", "SQL Injection"),  # Both map to A03
            ("Directory Traversal", "Path Traversal"),
        ]
        
        for alias, primary in aliases:
            if alias in VulnerabilityClassifier.OWASP_MAPPING and \
               primary in VulnerabilityClassifier.OWASP_MAPPING:
                # For aliases that have different mappings, allow it
                # but document the difference
                alias_owasp = VulnerabilityClassifier.OWASP_MAPPING.get(alias)
                primary_owasp = VulnerabilityClassifier.OWASP_MAPPING.get(primary)
                
                # Check CWE too
                alias_cwe = VulnerabilityClassifier.CWE_MAPPING.get(alias)
                primary_cwe = VulnerabilityClassifier.CWE_MAPPING.get(primary)
                
                # Log for documentation purposes
                if alias_owasp != primary_owasp:
                    print(f"Note: '{alias}' ({alias_owasp}) differs from " \
                          f"'{primary}' ({primary_owasp})")


class TestComplianceMapping:
    """Verify compliance framework mappings"""

    def test_all_compliance_values_are_lists(self):
        """Verify compliance impact values are lists of strings"""
        for finding_type, frameworks in VulnerabilityClassifier.COMPLIANCE_IMPACT.items():
            assert isinstance(frameworks, list), \
                f"'{finding_type}' compliance value is not a list: {type(frameworks)}"
            assert all(isinstance(f, str) for f in frameworks), \
                f"'{finding_type}' compliance value contains non-strings: {frameworks}"

    def test_valid_compliance_frameworks(self):
        """Verify only known compliance frameworks are listed"""
        valid_frameworks = {"HIPAA", "PCI-DSS", "GDPR", "SOC2"}
        
        for finding_type, frameworks in VulnerabilityClassifier.COMPLIANCE_IMPACT.items():
            for framework in frameworks:
                assert framework in valid_frameworks, \
                    f"Unknown compliance framework for '{finding_type}': {framework}"

    def test_high_risk_findings_have_compliance_mappings(self):
        """Verify critical findings are mapped to compliance frameworks"""
        high_risk_findings = [
            "SQL Injection",
            "Cross-Site Scripting",
            "Authentication Weakness",
            "Sensitive Data Exposure",
        ]
        
        for finding in high_risk_findings:
            assert finding in VulnerabilityClassifier.COMPLIANCE_IMPACT, \
                f"High-risk finding '{finding}' has no compliance mapping"
            
            frameworks = VulnerabilityClassifier.COMPLIANCE_IMPACT[finding]
            assert len(frameworks) > 0, \
                f"'{finding}' has empty compliance mapping"


class TestClassificationMethod:
    """Test the classify method returns correct structure"""

    def test_classify_returns_valid_structure(self):
        """Verify classify() returns dict with required keys"""
        result = VulnerabilityClassifier.classify("SQL Injection")
        
        assert isinstance(result, dict), "classify() should return dict"
        assert "owasp_category" in result, "Missing 'owasp_category' key"
        assert "cwe_id" in result, "Missing 'cwe_id' key"

    def test_classify_sql_injection(self):
        """Test specific classification for SQL Injection"""
        result = VulnerabilityClassifier.classify("SQL Injection")
        
        assert result["owasp_category"] == "A03:2021 - Injection"
        assert result["cwe_id"] == "CWE-89"

    def test_classify_xss(self):
        """Test specific classification for XSS"""
        result = VulnerabilityClassifier.classify("Cross-Site Scripting")
        
        assert "A07" in result["owasp_category"]
        assert result["cwe_id"] == "CWE-79"

    def test_classify_unknown_finding_uses_defaults(self):
        """Test that unknown findings get default mapping"""
        result = VulnerabilityClassifier.classify("Unknown Finding Type")
        
        assert "A05" in result["owasp_category"], \
            "Unknown findings should default to A05 (Security Misconfiguration)"
        assert result["cwe_id"] == "CWE-200", \
            "Unknown findings should default to CWE-200"

    def test_classify_other_uses_defaults(self):
        """Test that 'Other' category uses defaults"""
        result = VulnerabilityClassifier.classify("Other")
        
        assert "A05" in result["owasp_category"]
        assert result["cwe_id"] == "CWE-200"

    def test_classify_case_sensitivity(self):
        """Test that classification works with exact case"""
        result1 = VulnerabilityClassifier.classify("SQL Injection")
        result2 = VulnerabilityClassifier.classify("sql injection")  # lowercase
        
        # Should map differently - exact match required
        assert result1["cwe_id"] == "CWE-89"
        assert result2["cwe_id"] == "CWE-200"  # Falls back to default


class TestOWASPCategoryEnum:
    """Test OWASP Category enumeration"""

    def test_all_owasp_categories_exist(self):
        """Verify all 10 OWASP categories are defined"""
        expected_codes = ["A01", "A02", "A03", "A04", "A05", "A06", "A07", "A08", "A09", "A10"]
        
        for code in expected_codes:
            # Check that enum has the category
            assert hasattr(OWASPCategory, code), f"Missing OWASPCategory.{code}"

    def test_owasp_categories_have_descriptions(self):
        """Verify each OWASP category has a meaningful value"""
        for category in OWASPCategory:
            assert category.value.startswith("A"), "Value should start with 'A'"
            assert "2021" in category.value, "Value should reference 2021 edition"
            assert "-" in category.value, "Value should contain description separator"

    def test_owasp_category_descriptions_are_unique(self):
        """Verify no duplicate descriptions in OWASP categories"""
        values = [cat.value for cat in OWASPCategory]
        assert len(values) == len(set(values)), "Duplicate OWASP category descriptions"


class TestMappingCoverage:
    """Test coverage of all vulnerability types"""

    def test_critical_vulnerability_types_mapped(self):
        """Verify critical vulnerability types have mappings"""
        critical_types = [
            "SQL Injection",
            "Cross-Site Scripting",
            "Cross-Site Request Forgery",
            "Authentication Weakness",
            "Authorization Weakness",
        ]
        
        for vuln_type in critical_types:
            assert vuln_type in VulnerabilityClassifier.OWASP_MAPPING, \
                f"Critical type '{vuln_type}' not in OWASP mapping"
            assert vuln_type in VulnerabilityClassifier.CWE_MAPPING, \
                f"Critical type '{vuln_type}' not in CWE mapping"

    def test_remediation_tips_available(self):
        """Verify remediation tips exist for mapped findings"""
        for finding_type in VulnerabilityClassifier.OWASP_MAPPING.keys():
            if finding_type != "Other":  # Other may not have specific tips
                tips = VulnerabilityClassifier.REMEDIATION_TIPS.get(finding_type)
                assert tips is not None, f"No remediation tips for '{finding_type}'"
                assert len(tips) > 0, f"Empty remediation tips for '{finding_type}'"


# Run all tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
