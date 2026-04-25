#!/usr/bin/env python3
"""
Validation script for GitHub Actions CI/CD integration
Tests SARIF reporter and PR comment generator
"""

import json
import sys

def test_sarif_reporter():
    """Test SARIF reporter functionality."""
    from scanner.reporters.sarif_reporter import VAPTSarifReporter, create_sarif_report

    print("=" * 60)
    print("Testing SARIF Reporter")
    print("=" * 60)

    # Test 1: Initialize reporter
    reporter = VAPTSarifReporter(tool_version="1.0.0", scan_target="http://localhost:3000")
    print(f"✓ Reporter initialized: {reporter.tool_version}")
    print(f"✓ Scan target: {reporter.scan_target}")
    print(f"✓ Run ID: {reporter.run_id[:8]}...")

    # Test 2: Generate SARIF with sample findings
    sample_findings = [
        {
            'type': 'SQL Injection',
            'severity': 'critical',
            'message': 'SQL Injection in user ID parameter',
            'location': '/api/users',
            'parameter': 'id',
            'evidence': 'SQL error detected in response',
            'confidence': 0.98,
            'cwe_id': 'CWE-89',
            'owasp_category': 'A03:2021 - Injection'
        },
        {
            'type': 'XSS',
            'severity': 'high',
            'message': 'Reflected XSS in search parameter',
            'location': '/api/search',
            'parameter': 'q',
            'evidence': 'Payload reflected in HTML response',
            'confidence': 0.95,
            'cwe_id': 'CWE-79',
            'owasp_category': 'A03:2021 - Injection'
        }
    ]

    sarif_report = reporter.generate(sample_findings)

    # Validate SARIF structure
    assert sarif_report["$schema"].endswith("sarif-schema-2.1.0.json"), "Invalid schema"
    assert sarif_report["version"] == "2.1.0", "Invalid version"
    assert len(sarif_report["runs"]) == 1, "Invalid runs count"
    print(f"✓ SARIF schema valid (v{sarif_report['version']})")

    # Validate results
    results = sarif_report["runs"][0]["results"]
    assert len(results) == 2, f"Expected 2 results, got {len(results)}"
    print(f"✓ Results count: {len(results)}")

    # Validate first result
    assert results[0]["ruleId"] == "VAPT-SQL-INJECTION", "Invalid rule ID"
    assert results[0]["level"] == "error", "Invalid severity level"
    print(f"✓ Result 1: {results[0]['ruleId']} ({results[0]['level']})")

    # Validate second result
    assert results[1]["ruleId"] == "VAPT-XSS", "Invalid rule ID"
    assert results[1]["level"] == "error", "Invalid severity level"
    print(f"✓ Result 2: {results[1]['ruleId']} ({results[1]['level']})")

    # Validate JSON serialization
    json_str = json.dumps(sarif_report, indent=2)
    assert len(json_str) > 0, "JSON serialization failed"
    print(f"✓ JSON serialization successful ({len(json_str)} bytes)")

    # Test SARIF rule definitions
    rules = sarif_report["runs"][0]["tool"]["driver"]["rules"]
    assert len(rules) > 0, "No rules found"
    print(f"✓ SARIF includes {len(rules)} rule definitions")

    # Validate rule structure
    for rule in rules:
        assert "id" in rule, "Rule missing ID"
        assert "name" in rule, "Rule missing name"
        assert "properties" in rule, "Rule missing properties"
        assert "cwe" in rule["properties"], "Rule missing CWE"
        assert "owasp" in rule["properties"], "Rule missing OWASP"

    print("✓ All rules have required properties")

    # Test convenience function
    sarif_func = create_sarif_report(sample_findings, "1.0.0", "http://test.com")
    assert sarif_func["version"] == "2.1.0", "Convenience function failed"
    print(f"✓ create_sarif_report() convenience function works")

    print("✅ SARIF Reporter tests PASSED\n")
    return True


def test_pr_comment_generator():
    """Test PR comment generator functionality."""
    from tools.pr_comment_generator import PRCommentGenerator, generate_pr_comment

    print("=" * 60)
    print("Testing PR Comment Generator")
    print("=" * 60)

    # Test 1: Initialize generator
    gen = PRCommentGenerator(scan_target="https://api.example.com", duration_seconds=45.5)
    print(f"✓ Generator initialized")
    print(f"✓ Scan target: {gen.scan_target}")
    print(f"✓ Duration: {gen.duration_seconds}s")

    # Sample findings
    sample_findings = [
        {
            'type': 'SQL Injection',
            'severity': 'critical',
            'message': 'SQL Injection in user ID parameter',
            'location': '/api/users',
            'parameter': 'id',
            'evidence': 'SQL error detected in response',
            'confidence': 0.98,
            'cwe_id': 'CWE-89',
            'owasp_category': 'A03:2021 - Injection'
        },
        {
            'type': 'XSS',
            'severity': 'high',
            'message': 'Reflected XSS in search parameter',
            'location': '/api/search',
            'parameter': 'q',
            'evidence': 'Payload reflected in HTML response',
            'confidence': 0.95,
            'cwe_id': 'CWE-79',
            'owasp_category': 'A03:2021 - Injection'
        }
    ]

    # Test 2: Generate full PR comment
    comment = gen.generate(sample_findings)
    assert isinstance(comment, str), "Comment is not a string"
    assert len(comment) > 100, "Comment is too short"
    assert "VAPT Security Scan Results" in comment, "Missing title"
    assert "SQL Injection" in comment, "Missing finding"
    assert "XSS" in comment, "Missing finding"
    print(f"✓ Full comment generated ({len(comment)} chars)")

    # Test 3: Verify comment sections
    assert "Summary" in comment, "Missing summary section"
    assert "Critical" in comment, "Missing severity"
    assert "High" in comment, "Missing severity"
    assert "Scan Details" in comment, "Missing details section"
    assert "https://api.example.com" in comment, "Missing target"
    print(f"✓ All required sections present")

    # Test 4: Generate summary-only comment
    summary_comment = gen.generate_summary_only(sample_findings)
    assert isinstance(summary_comment, str), "Summary comment is not a string"
    assert len(summary_comment) > 0, "Summary comment is empty"
    assert len(summary_comment) < len(comment), "Summary should be shorter than full"
    print(f"✓ Summary-only comment generated ({len(summary_comment)} chars)")

    # Test 5: Test convenience function
    pr_func = generate_pr_comment(sample_findings, "http://test.com", 30.0)
    assert "VAPT" in pr_func, "Convenience function failed"
    print(f"✓ generate_pr_comment() convenience function works")

    # Test 6: Test with empty findings
    empty_comment = gen.generate([])
    assert isinstance(empty_comment, str), "Empty findings comment failed"
    print(f"✓ Comment generated with empty findings ({len(empty_comment)} chars)")

    # Test 7: Check severity icons
    assert "🔴" in comment or "Critical" in comment
    assert "🟠" in comment or "High" in comment
    print(f"✓ Severity indicators present")

    print("✅ PR Comment Generator tests PASSED\n")
    return True


if __name__ == "__main__":
    try:
        test_sarif_reporter()
        test_pr_comment_generator()

        print("=" * 60)
        print("🎉 ALL VALIDATION TESTS PASSED!")
        print("=" * 60)
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
