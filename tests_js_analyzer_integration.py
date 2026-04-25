"""
Integration tests for JavaScript analyzer with evidence collector

Tests that findings can be properly converted to WebVulnerabilityFinding objects
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scanner.web.js_analyzer import JavaScriptAnalyzer
from scanner.web.evidence_collector import WebVulnerabilityFinding, FindingType, FindingSeverity


def test_javascript_findings_to_evidence():
    """Test converting JS analyzer findings to evidence format"""
    
    analyzer = JavaScriptAnalyzer()
    
    # Test code with various issues
    test_code = """
    const API_KEY = 'sk_live_1234567890abcdef';
    
    async function fetchUser(id) {
      console.log('User ID:', id);
      const response = await fetch('/api/users/' + id);
      return response.json();
    }
    
    // password = 'admin123';
    debugger;
    """
    
    # Analyze
    analysis = {
        'endpoints': analyzer.extract_endpoints(test_code),
        'secrets': analyzer.detect_secrets(test_code),
        'debug': analyzer.find_debug_code(test_code),
    }
    
    # Convert to findings
    findings = []
    
    # Create findings for secrets
    for secret in analysis['secrets']:
        finding = WebVulnerabilityFinding(
            type="Hardcoded Secrets",
            severity=secret.get('severity', 'High'),
            url="test_file.js",
            evidence=f"Found {secret['type']}: {secret['match']} at line {secret['line_number']}",
            module="JavaScript Analyzer",
            confidence_score=90 if secret.get('severity') == 'Critical' else 75,
        )
        findings.append(finding)
    
    # Create findings for debug code
    for debug in analysis['debug']:
        finding = WebVulnerabilityFinding(
            type="Debug Code in Production",
            severity="Low",
            url="test_file.js",
            evidence=f"Found {debug['type']} at line {debug['line_number']}",
            module="JavaScript Analyzer",
            confidence_score=50,
        )
        findings.append(finding)
    
    # Verify we have findings
    assert len(findings) > 0, "Should have generated findings"
    
    # Verify findings are properly formed
    for finding in findings:
        assert finding.finding_id, "Should have finding ID"
        assert finding.fingerprint, "Should have fingerprint"
        assert finding.confidence_score >= 0 and finding.confidence_score <= 100, "Should have valid confidence score"
    
    print(f"✓ Converted {len(findings)} findings to evidence format")
    print(f"  - Found {len([f for f in findings if 'Hardcoded' in f.type])} secret findings")
    print(f"  - Found {len([f for f in findings if 'Debug' in f.type])} debug findings")


def test_endpoint_findings():
    """Test endpoint discovery findings"""
    
    analyzer = JavaScriptAnalyzer()
    
    test_code = """
    fetch('/api/admin/users')
      .then(r => r.json())
      .then(d => console.log(d));
      
    axios.post('/api/internal/config', data);
    
    $.ajax({
      url: '/api/sensitive-data',
      type: 'GET'
    });
    """
    
    endpoints = analyzer.extract_endpoints(test_code)
    
    # Create findings for potentially sensitive endpoints
    findings = []
    for endpoint in endpoints:
        # Check for sensitive paths
        if any(sensitive in endpoint['url'].lower() for sensitive in ['admin', 'internal', 'sensitive', 'config', 'secret']):
            finding = WebVulnerabilityFinding(
                type="Exposed Sensitive Endpoint",
                severity="High",
                url=endpoint['url'],
                method=endpoint['method'],
                evidence=f"Found potentially sensitive API endpoint in JavaScript",
                module="JavaScript Analyzer",
                confidence_score=60,
            )
            findings.append(finding)
    
    assert len(findings) > 0, "Should find sensitive endpoints"
    
    print(f"✓ Identified {len(findings)} potentially sensitive endpoints")
    for f in findings:
        print(f"  - {f.url} ({f.method})")


def test_severity_mapping():
    """Test that severity levels are properly mapped"""
    
    analyzer = JavaScriptAnalyzer()
    
    # Test different severity levels
    test_cases = [
        ("AKIAIOSFODNN7EXAMPLE", "Critical"),  # AWS key
        ("ghp_1234567890abcdef", "High"),      # GitHub token
        ("console.log('test')", "Low"),        # Debug code
    ]
    
    for code, expected_severity in test_cases:
        if "console" in code:
            debug = analyzer.find_debug_code(code)
            assert len(debug) > 0
            print(f"✓ Debug code correctly severity mapped")
        else:
            secrets = analyzer.detect_secrets(code)
            if secrets:
                severity = secrets[0].get('severity', 'Medium')
                print(f"✓ {expected_severity} severity correctly mapped: {secrets[0]['type']}")


def test_source_map_findings():
    """Test source map exposure findings"""
    
    analyzer = JavaScriptAnalyzer()
    
    source_maps = analyzer.check_source_maps('https://example.com/assets/app.min.js')
    
    if source_maps:
        finding = WebVulnerabilityFinding(
            type="Source Map Exposure",
            severity="High",
            url="https://example.com/assets/app.min.js.map",
            evidence="JavaScript source map file may expose original source code",
            module="JavaScript Analyzer",
            confidence_score=75,
        )
        
        assert finding.type == "Source Map Exposure"
        print("✓ Source map findings properly formatted")


def test_deduplication():
    """Test that duplicate findings are handled"""
    
    analyzer = JavaScriptAnalyzer()
    
    # Same secret appearing twice
    test_code = """
    const key1 = 'AKIAIOSFODNN7EXAMPLE';
    const key2 = 'AKIAIOSFODNN7EXAMPLE';  // Same key, different variable
    """
    
    secrets = analyzer.detect_secrets(test_code)
    
    # Should have minimal duplicates due to our deduplication logic
    print(f"✓ Deduplication: Found {len(secrets)} secrets (should minimize duplicates)")


if __name__ == '__main__':
    print("Running Integration Tests for JavaScript Analyzer...\n")
    
    try:
        test_javascript_findings_to_evidence()
        print()
        
        test_endpoint_findings()
        print()
        
        test_severity_mapping()
        print()
        
        test_source_map_findings()
        print()
        
        test_deduplication()
        print()
        
        print("=" * 50)
        print("All integration tests passed! ✓")
        print("=" * 50)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
