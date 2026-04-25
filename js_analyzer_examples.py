"""
JavaScript Analyzer - Usage Guide and Integration Examples

This module provides comprehensive JavaScript file analysis for:
- Hidden API endpoints
- Hardcoded secrets
- Debug code in production
- Exposed source maps
"""

import asyncio
from scanner.web.js_analyzer import JavaScriptAnalyzer
from scanner.web.evidence_collector import WebVulnerabilityFinding


def example_basic_usage():
    """Basic usage example - analyzing JavaScript content"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic JavaScript Analysis")
    print("="*60)
    
    analyzer = JavaScriptAnalyzer()
    
    js_code = """
    // API Configuration
    const CONFIG = {
      apiKey: 'sk_live_1234567890abcdef',  // Stripe key
      baseUrl: '/api/v1',
      authToken: 'ghp_FakeGitHubToken123456789'
    };
    
    async function fetchUserData(userId) {
      console.log('Fetching user:', userId);
      
      try {
        const response = await fetch(`/api/users/${userId}`, {
          headers: {
            'Authorization': 'Bearer ' + CONFIG.authToken
          }
        });
        
        const data = await response.json();
        console.log('User data:', data);
        debugger;
        return data;
      } catch (error) {
        console.error('Failed to fetch user:', error);
      }
    }
    """
    
    # Analyze the code
    endpoints = analyzer.extract_endpoints(js_code)
    secrets = analyzer.detect_secrets(js_code)
    debug_code = analyzer.find_debug_code(js_code)
    
    print(f"\nFound {len(endpoints)} endpoints:")
    for ep in endpoints:
        print(f"  - {ep['method']:6} {ep['url']}")
    
    print(f"\nFound {len(secrets)} hardcoded secrets:")
    for secret in secrets:
        print(f"  - {secret['type']:30} (line {secret['line_number']})")
    
    print(f"\nFound {len(debug_code)} debug code instances:")
    for debug in debug_code:
        print(f"  - {debug['type']:30} (line {debug['line_number']})")


def example_evidence_conversion():
    """Example - converting findings to evidence format"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Converting Findings to Evidence")
    print("="*60)
    
    analyzer = JavaScriptAnalyzer()
    
    js_code = """
    const apiKey = 'AKIAIOSFODNN7EXAMPLE';
    fetch('/admin/users').then(r => r.json());
    """
    
    # Analyze
    secrets = analyzer.detect_secrets(js_code)
    endpoints = analyzer.extract_endpoints(js_code)
    
    print(f"\nConverting {len(secrets)} secrets to evidence findings...")
    
    for secret in secrets:
        # Create evidence finding
        finding = WebVulnerabilityFinding(
            type="Hardcoded Secrets - " + secret['type'],
            severity=secret['severity'],
            url="app.js",
            evidence=f"Found {secret['type']} at line {secret['line_number']}",
            module="JavaScript Analyzer",
            confidence_score=85 if secret['severity'] == 'Critical' else 70,
        )
        
        print(f"\n  Finding ID: {finding.finding_id}")
        print(f"  Type: {finding.type}")
        print(f"  Severity: {finding.severity}")
        print(f"  Confidence: {finding.confidence_score}%")
    
    print(f"\nConverting {len(endpoints)} endpoints to evidence findings...")
    
    for endpoint in endpoints:
        if 'admin' in endpoint['url'].lower():
            finding = WebVulnerabilityFinding(
                type="Exposed Sensitive Endpoint",
                severity="High",
                url=endpoint['url'],
                method=endpoint['method'],
                evidence="Potentially sensitive administrative endpoint discovered in JavaScript",
                module="JavaScript Analyzer",
                confidence_score=60,
            )
            
            print(f"\n  Finding ID: {finding.finding_id}")
            print(f"  Endpoint: {finding.method} {finding.url}")
            print(f"  Severity: {finding.severity}")


def example_batch_analysis():
    """Example - analyzing multiple JavaScript URLs (would require async)"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Pattern Summary")
    print("="*60)
    
    analyzer = JavaScriptAnalyzer()
    
    # Show what patterns are detected
    print("\n✓ Endpoint Patterns Detected:")
    patterns = [
        ("fetch('/api/users')", "fetch()"),
        ("axios.post('/api/data')", "axios"),
        ("$.ajax({url: '/api/config'})", "jQuery.ajax()"),
        ("xhr.open('POST', '/api/submit')", "XMLHttpRequest"),
    ]
    
    for code, desc in patterns:
        print(f"  - {desc:20} - {code}")
    
    print("\n✓ Secret Patterns Detected:")
    secret_patterns = [
        ("AKIA...", "AWS Access Keys"),
        ("ghp_...", "GitHub Tokens"),
        ("sk_live_...", "Stripe API Keys"),
        ("xox[baprs]-...", "Slack Tokens"),
        ("AIza...", "Firebase Keys"),
        ("api_key: '...'", "Generic API Keys"),
        ("Bearer eyJ...", "Bearer Tokens"),
    ]
    
    for pattern, desc in secret_patterns:
        print(f"  - {desc:25} - {pattern}")
    
    print("\n✓ Debug Code Patterns Detected:")
    debug_patterns = [
        ("console.log()", "console methods"),
        ("debugger;", "debugger statements"),
        ("alert()", "alert calls"),
        ("// auth_token = '...'", "commented authentication"),
    ]
    
    for code, desc in debug_patterns:
        print(f"  - {desc:25} - {code}")


def example_severity_levels():
    """Example - understanding severity levels"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Severity Levels")
    print("="*60)
    
    analyzer = JavaScriptAnalyzer()
    
    print("\nSecurity Findings Severity Mapping:")
    print("\n  CRITICAL:")
    print("    - AWS Access Keys (can access entire AWS account)")
    print("    - Hardcoded passwords")
    print("    - Stripe live keys (can process real payments)")
    
    print("\n  HIGH:")
    print("    - GitHub tokens (can access private repositories)")
    print("    - JWT tokens (can bypass authentication)")
    print("    - AWS Secret Keys")
    print("    - Source maps (expose original source code)")
    
    print("\n  MEDIUM:")
    print("    - Generic API keys")
    print("    - Slack tokens")
    print("    - Firebase keys")
    
    print("\n  LOW:")
    print("    - console.log statements with potential data exposure")
    print("    - debugger statements")
    print("    - alert() calls")


def example_integration_workflow():
    """Example - how this integrates into the scanning workflow"""
    print("\n" + "="*60)
    print("EXAMPLE 5: Integration Workflow")
    print("="*60)
    
    print("""
    Typical Integration Workflow:
    
    1. SURFACE MAPPING PHASE (surface_mapper.py):
       ├─ Crawl website and find HTML pages
       ├─ Extract JavaScript file URLs (<script src="...">)
       └─ Store JS URLs for analysis
    
    2. JAVASCRIPT ANALYSIS PHASE (js_analyzer.py):
       ├─ Download all discovered JavaScript files
       ├─ Extract API endpoints
       │  └─ Convert to WebVulnerabilityFinding with "discovered_via: javascript"
       ├─ Detect hardcoded secrets
       │  └─ Convert to WebVulnerabilityFinding with "Sensitive Data Exposure"
       ├─ Find debug code
       │  └─ Convert to WebVulnerabilityFinding with "Debug Code in Production"
       └─ Check for source maps
          └─ Convert to WebVulnerabilityFinding with "Information Disclosure"
    
    3. EVIDENCE COLLECTION PHASE (evidence_collector.py):
       ├─ Deduplicate findings across all modules
       ├─ Calculate confidence scores
       ├─ Classify vulnerabilities (OWASP, CWE)
       └─ Export comprehensive report
    
    4. OUTPUT:
       ├─ JSON report with all findings
       ├─ Excel spreadsheet with evidence
       ├─ Compliance impact assessment
       └─ Remediation recommendations
    """)


def example_output_format():
    """Example - understanding output format"""
    print("\n" + "="*60)
    print("EXAMPLE 6: Output Format")
    print("="*60)
    
    analyzer = JavaScriptAnalyzer()
    
    js_code = "const key = 'sk_live_123'; fetch('/api/data');"
    
    analysis = {
        "file_url": "https://example.com/app.js",
        "endpoints": analyzer.extract_endpoints(js_code),
        "secrets": analyzer.detect_secrets(js_code),
        "debug_code": analyzer.find_debug_code(js_code),
        "source_maps": analyzer.check_source_maps("https://example.com/app.js"),
    }
    
    print("\nAnalysis Output Structure:")
    print(f"""
    {{
      "file_url": "{analysis['file_url']}",
      "endpoints": [
        {{
          "url": "/api/data",
          "method": "GET",
          "line_number": 1,
          "source_pattern": "fetch",
          "context": "const key = 'sk_live_123'; fetch('/api/data');"
        }}
      ],
      "secrets": [
        {{
          "type": "Stripe API Key",
          "match": "sk_live_123...",
          "line_number": 1,
          "severity": "Critical"
        }}
      ],
      "debug_code": [],
      "source_maps": [
        {{
          "potential_map": "https://example.com/app.js.map",
          "severity": "High",
          "issue": "Source map file might expose original source code"
        }}
      ]
    }}
    """)


if __name__ == '__main__':
    print("\n" + "="*60)
    print("JavaScript Analyzer - Usage Examples and Documentation")
    print("="*60)
    
    try:
        example_basic_usage()
        example_evidence_conversion()
        example_batch_analysis()
        example_severity_levels()
        example_integration_workflow()
        example_output_format()
        
        print("\n" + "="*60)
        print("For more information, see:")
        print("  - scanner/web/js_analyzer.py (implementation)")
        print("  - tests_js_analyzer.py (unit tests)")
        print("  - tests_js_analyzer_integration.py (integration tests)")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback
        traceback.print_exc()
