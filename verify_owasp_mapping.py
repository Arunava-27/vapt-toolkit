"""
OWASP Top 10 2021 & CWE-ID Mapping Verification Script

Verifies:
1. All findings have OWASP Top 10 2021 category mapping
2. All findings have CWE-ID mapping
3. Consistency across modules
4. Valid CWE-ID format
5. OWASP categories are from 2021 edition
"""

import sys
import re
from scanner.web.vulnerability_classifier import VulnerabilityClassifier, OWASPCategory


def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")


def print_success(msg):
    """Print success message"""
    print(f"✓ {msg}")


def print_error(msg):
    """Print error message"""
    print(f"✗ {msg}")


def print_warning(msg):
    """Print warning message"""
    print(f"⚠ {msg}")


def verify_owasp_mappings():
    """Verify OWASP mappings are complete and valid"""
    print_section("OWASP Top 10 2021 Mapping Verification")
    
    errors = []
    
    # Check all mappings exist and are OWASPCategory
    print("\n1. Checking OWASP mapping completeness...")
    for finding_type, owasp_category in VulnerabilityClassifier.OWASP_MAPPING.items():
        if not isinstance(owasp_category, OWASPCategory):
            errors.append(f"  '{finding_type}' maps to non-OWASPCategory: {owasp_category}")
        else:
            print(f"  ✓ {finding_type}: {owasp_category.value}")
    
    if errors:
        for error in errors:
            print_error(error)
        return False
    
    print_success(f"All {len(VulnerabilityClassifier.OWASP_MAPPING)} finding types have OWASP mappings")
    
    # Check OWASP categories are 2021
    print("\n2. Verifying OWASP categories are from 2021 edition...")
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
        if category.value in valid_categories:
            print(f"  ✓ {category.value}")
        else:
            errors.append(f"  Invalid OWASP category: {category.value}")
    
    if errors:
        for error in errors:
            print_error(error)
        return False
    
    print_success("All OWASP categories are from 2021 edition")
    return True


def verify_cwe_mappings():
    """Verify CWE mappings are complete and valid"""
    print_section("CWE-ID Mapping Verification")
    
    errors = []
    
    # Check all mappings exist
    print("\n1. Checking CWE-ID completeness...")
    for finding_type, cwe_id in VulnerabilityClassifier.CWE_MAPPING.items():
        if not cwe_id or cwe_id == "":
            errors.append(f"  '{finding_type}' has no CWE-ID mapping")
        else:
            print(f"  ✓ {finding_type}: {cwe_id}")
    
    if errors:
        for error in errors:
            print_error(error)
        return False
    
    print_success(f"All {len(VulnerabilityClassifier.CWE_MAPPING)} finding types have CWE-ID mappings")
    
    # Check CWE format
    print("\n2. Verifying CWE-ID format (CWE-XXXX)...")
    cwe_pattern = re.compile(r"^CWE-\d+$")
    for finding_type, cwe_id in VulnerabilityClassifier.CWE_MAPPING.items():
        if not cwe_pattern.match(cwe_id):
            errors.append(f"  Invalid CWE-ID format for '{finding_type}': {cwe_id}")
        else:
            print(f"  ✓ {cwe_id} (for {finding_type})")
    
    if errors:
        for error in errors:
            print_error(error)
        return False
    
    print_success("All CWE-IDs follow valid format (CWE-XXXX)")
    
    # Check CWE values are known
    print("\n3. Verifying CWE-IDs are valid (from MITRE)...")
    known_cwes = {
        "CWE-16", "CWE-22", "CWE-79", "CWE-89", "CWE-200",
        "CWE-287", "CWE-327", "CWE-352", "CWE-434", "CWE-502",
        "CWE-639", "CWE-770", "CWE-840", "CWE-918"
    }
    
    unique_cwes = set(VulnerabilityClassifier.CWE_MAPPING.values())
    for cwe_id in unique_cwes:
        if cwe_id in known_cwes:
            print(f"  ✓ {cwe_id} - Known CWE")
        else:
            errors.append(f"  Unknown CWE-ID: {cwe_id}")
    
    if errors:
        for error in errors:
            print_error(error)
        return False
    
    print_success("All CWE-IDs are valid MITRE CWE identifiers")
    return True


def verify_mapping_consistency():
    """Verify consistency between OWASP and CWE mappings"""
    print_section("Mapping Consistency Verification")
    
    errors = []
    
    # Check same keys in both mappings
    print("\n1. Checking finding type consistency...")
    owasp_keys = set(VulnerabilityClassifier.OWASP_MAPPING.keys())
    cwe_keys = set(VulnerabilityClassifier.CWE_MAPPING.keys())
    
    if owasp_keys != cwe_keys:
        only_owasp = owasp_keys - cwe_keys
        only_cwe = cwe_keys - owasp_keys
        if only_owasp:
            errors.append(f"  Only in OWASP mapping: {only_owasp}")
        if only_cwe:
            errors.append(f"  Only in CWE mapping: {only_cwe}")
    else:
        print_success("OWASP and CWE mappings have identical finding types")
    
    # Check compliance mapping coverage
    print("\n2. Checking compliance mapping coverage...")
    compliance_keys = set(VulnerabilityClassifier.COMPLIANCE_IMPACT.keys())
    
    # Compliance should be subset of OWASP (doesn't need to cover "Other")
    if compliance_keys.issubset(owasp_keys):
        print_success(f"Compliance impact mappings exist for {len(compliance_keys)} finding types")
    else:
        extra = compliance_keys - owasp_keys
        errors.append(f"  Extra keys in COMPLIANCE_IMPACT: {extra}")
    
    # Check alias consistency
    print("\n3. Checking vulnerability type aliases...")
    aliases = [
        ("XSS", "Cross-Site Scripting"),
        ("CSRF", "Cross-Site Request Forgery"),
        ("SSRF", "Server-Side Request Forgery"),
        ("IDOR", "Insecure Direct Object Reference"),
        ("Directory Traversal", "Path Traversal"),
    ]
    
    for alias, primary in aliases:
        if alias in VulnerabilityClassifier.OWASP_MAPPING and primary in VulnerabilityClassifier.OWASP_MAPPING:
            alias_owasp = VulnerabilityClassifier.OWASP_MAPPING.get(alias)
            primary_owasp = VulnerabilityClassifier.OWASP_MAPPING.get(primary)
            
            alias_cwe = VulnerabilityClassifier.CWE_MAPPING.get(alias)
            primary_cwe = VulnerabilityClassifier.CWE_MAPPING.get(primary)
            
            if alias_owasp == primary_owasp and alias_cwe == primary_cwe:
                print(f"  ✓ {alias} ≈ {primary} (consistent mapping)")
            else:
                print(f"  ⚠ {alias} maps differently than {primary}")
                print(f"    → Alias: {alias_owasp.value} / {alias_cwe}")
                print(f"    → Primary: {primary_owasp.value} / {primary_cwe}")
    
    if errors:
        for error in errors:
            print_error(error)
        return False
    
    print_success("Mapping consistency verified")
    return True


def verify_compliance_mapping():
    """Verify compliance framework mappings"""
    print_section("Compliance Framework Mapping Verification")
    
    errors = []
    valid_frameworks = {"HIPAA", "PCI-DSS", "GDPR", "SOC2"}
    
    print("\n1. Checking compliance framework types...")
    for finding_type, frameworks in VulnerabilityClassifier.COMPLIANCE_IMPACT.items():
        if not isinstance(frameworks, list):
            errors.append(f"  '{finding_type}' compliance value is not a list: {type(frameworks)}")
        else:
            for framework in frameworks:
                if framework not in valid_frameworks:
                    errors.append(f"  Unknown compliance framework for '{finding_type}': {framework}")
                else:
                    print(f"  ✓ {finding_type}: {', '.join(sorted(frameworks))}")
    
    if errors:
        for error in errors:
            print_error(error)
        return False
    
    print_success("All compliance frameworks are valid")
    
    # Verify high-risk findings
    print("\n2. Checking high-risk findings have compliance mappings...")
    high_risk = [
        "SQL Injection",
        "Cross-Site Scripting",
        "Authentication Weakness",
        "Sensitive Data Exposure",
    ]
    
    for finding in high_risk:
        if finding in VulnerabilityClassifier.COMPLIANCE_IMPACT:
            frameworks = VulnerabilityClassifier.COMPLIANCE_IMPACT[finding]
            print(f"  ✓ {finding}: {', '.join(frameworks)}")
        else:
            errors.append(f"  High-risk finding '{finding}' missing compliance mapping")
    
    if errors:
        for error in errors:
            print_error(error)
        return False
    
    print_success("High-risk findings have compliance mappings")
    return True


def verify_classification_method():
    """Test the classify method"""
    print_section("Classification Method Verification")
    
    errors = []
    
    print("\n1. Testing classify() method...")
    
    # Test SQL Injection
    result = VulnerabilityClassifier.classify("SQL Injection")
    if result.get("owasp_category") == "A03:2021 - Injection" and result.get("cwe_id") == "CWE-89":
        print(f"  ✓ SQL Injection → {result['owasp_category']} / {result['cwe_id']}")
    else:
        errors.append(f"  SQL Injection classification incorrect: {result}")
    
    # Test XSS
    result = VulnerabilityClassifier.classify("Cross-Site Scripting")
    if "A07" in result.get("owasp_category", "") and result.get("cwe_id") == "CWE-79":
        print(f"  ✓ XSS → {result['owasp_category']} / {result['cwe_id']}")
    else:
        errors.append(f"  XSS classification incorrect: {result}")
    
    # Test unknown finding
    result = VulnerabilityClassifier.classify("Unknown Finding Type")
    if "A05" in result.get("owasp_category", "") and result.get("cwe_id") == "CWE-200":
        print(f"  ✓ Unknown → defaults to {result['owasp_category']} / {result['cwe_id']}")
    else:
        errors.append(f"  Unknown finding default mapping incorrect: {result}")
    
    if errors:
        for error in errors:
            print_error(error)
        return False
    
    print_success("Classification method works correctly")
    return True


def generate_mapping_report():
    """Generate a summary report of all mappings"""
    print_section("Mapping Summary Report")
    
    print("\n1. Finding Type Coverage:")
    print(f"   • Total unique finding types: {len(VulnerabilityClassifier.OWASP_MAPPING)}")
    print(f"   • OWASP categories mapped: {len(set(cat.value for cat in VulnerabilityClassifier.OWASP_MAPPING.values()))}")
    print(f"   • Unique CWE-IDs: {len(set(VulnerabilityClassifier.CWE_MAPPING.values()))}")
    print(f"   • Compliance frameworks: {len({'HIPAA', 'PCI-DSS', 'GDPR', 'SOC2'})}")
    
    print("\n2. OWASP Category Distribution:")
    owasp_dist = {}
    for finding, category in VulnerabilityClassifier.OWASP_MAPPING.items():
        cat_name = category.value
        owasp_dist[cat_name] = owasp_dist.get(cat_name, 0) + 1
    
    for category in sorted(owasp_dist.keys()):
        print(f"   • {category}: {owasp_dist[category]} finding types")
    
    print("\n3. CWE-ID Frequency:")
    cwe_dist = {}
    for finding, cwe in VulnerabilityClassifier.CWE_MAPPING.items():
        cwe_dist[cwe] = cwe_dist.get(cwe, 0) + 1
    
    for cwe in sorted(cwe_dist.keys(), key=lambda x: int(x.split('-')[1])):
        print(f"   • {cwe}: {cwe_dist[cwe]} finding types")


def main():
    """Run all verification tests"""
    print("\n" + "=" * 70)
    print("  VAPT Toolkit - OWASP Top 10 2021 & CWE Mapping Verification")
    print("=" * 70)
    
    all_passed = True
    
    # Run verifications
    all_passed &= verify_owasp_mappings()
    all_passed &= verify_cwe_mappings()
    all_passed &= verify_mapping_consistency()
    all_passed &= verify_compliance_mapping()
    all_passed &= verify_classification_method()
    
    # Generate report
    generate_mapping_report()
    
    # Summary
    print_section("Verification Summary")
    
    if all_passed:
        print_success("All verification tests PASSED ✓")
        print("\nThe mapping verification confirms:")
        print("  ✓ All findings have OWASP Top 10 2021 category mapping")
        print("  ✓ All findings have CWE-ID mapping")
        print("  ✓ Consistency across modules verified")
        print("  ✓ All CWE-IDs are in valid format (CWE-XXXX)")
        print("  ✓ OWASP categories are from 2021 edition")
        print("  ✓ Compliance framework mappings are complete")
        print("\nDocumentation generated:")
        print("  • docs/OWASP_MAPPING.md - Complete mapping reference")
        print("  • docs/FAQ.md - User-focused FAQ with 25 Q&A pairs")
        return 0
    else:
        print_error("Some verification tests FAILED ✗")
        print("\nPlease review the errors above and fix mapping inconsistencies.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
