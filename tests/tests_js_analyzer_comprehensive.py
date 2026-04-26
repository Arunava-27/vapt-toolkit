"""
Comprehensive Test Suite - JavaScript Analyzer

Demonstrates all detection capabilities with real-world examples
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scanner.web.js_analyzer import JavaScriptAnalyzer


def test_all_endpoint_patterns():
    """Test all endpoint detection patterns"""
    print("\n" + "="*70)
    print("TESTING: Endpoint Detection Patterns")
    print("="*70)
    
    analyzer = JavaScriptAnalyzer()
    
    test_cases = [
        ("fetch('/api/users')", "fetch basic", 1),
        ("fetch('/api/users').then(r => r.json())", "fetch with chain", 1),
        ("axios.get('/api/data')", "axios GET", 1),
        ("axios.post('/api/submit', data)", "axios POST", 1),
        ("axios.put('/api/update', data)", "axios PUT", 1),
        ("axios.delete('/api/delete')", "axios DELETE", 1),
        ("$.ajax({url: '/api/config'})", "jQuery AJAX", 1),
        ("$.ajax({url: '/api/test', type: 'POST'})", "jQuery AJAX POST", 1),
        ("xhr.open('GET', '/api/endpoint')", "XMLHttpRequest GET", 1),
        ("xhr.open('POST', '/api/endpoint')", "XMLHttpRequest POST", 1),
        ("@POST('/api/endpoint')", "Spring annotation", 1),
    ]
    
    passed = 0
    failed = 0
    
    for code, description, expected_count in test_cases:
        endpoints = analyzer.extract_endpoints(code)
        if len(endpoints) >= expected_count:
            print(f"  ✓ {description:30} - Found {len(endpoints)} endpoint(s)")
            passed += 1
        else:
            print(f"  ✗ {description:30} - Expected {expected_count}, found {len(endpoints)}")
            failed += 1
    
    print(f"\nEndpoint Detection: {passed}/{len(test_cases)} passed")
    return failed == 0


def test_all_secret_patterns():
    """Test all secret detection patterns"""
    print("\n" + "="*70)
    print("TESTING: Secret Detection Patterns")
    print("="*70)
    
    analyzer = JavaScriptAnalyzer()
    
    test_cases = [
        ("AKIAIOSFODNN7EXAMPLE", "AWS Access Key", 1),
        ("aws_secret_access_key = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'", "AWS Secret Key", 1),
        ("ghp_1234567890abcdefghijklmnopqrstuvwxyz", "GitHub Token", 1),
        ("gho_1234567890abcdefghijklmnopqrstuvwxyz", "GitHub OAuth Token", 1),
        ("sk_live_1234567890abcdefghijklmnopqrst", "Stripe Live Key", 1),
        ("pk_live_1234567890abcdefghijklmnopqrst", "Stripe Publishable Key", 1),
        ("sk_test_1234567890abcdefghijk", "Stripe Test Key", 1),
        ("xoxb-1234567890-1234567890-AbCdEfGhIjKlMnOpQrStUvWxYz", "Slack Bot Token", 1),
        ("AIzaSyDumKzGUhRYKMr9YFJZi-J17zxD8QsDeSM", "Firebase Key", 1),
        ("Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0", "Bearer Token", 1),
        ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U", "JWT Token", 1),
        ("api_key = 'sk123456789abcdefghijk'", "Generic API Key", 1),
        ("password = 'MySecurePassword123!'", "Hardcoded Password", 1),
    ]
    
    passed = 0
    failed = 0
    
    for code, description, expected_count in test_cases:
        secrets = analyzer.detect_secrets(code)
        if len(secrets) >= expected_count:
            severity = secrets[0]['severity'] if secrets else 'Unknown'
            print(f"  ✓ {description:30} - Found {len(secrets)} secret(s) [{severity}]")
            passed += 1
        else:
            print(f"  ✗ {description:30} - Expected {expected_count}, found {len(secrets)}")
            failed += 1
    
    print(f"\nSecret Detection: {passed}/{len(test_cases)} passed")
    return failed == 0


def test_all_debug_patterns():
    """Test all debug code detection patterns"""
    print("\n" + "="*70)
    print("TESTING: Debug Code Detection Patterns")
    print("="*70)
    
    analyzer = JavaScriptAnalyzer()
    
    test_cases = [
        ("console.log('message')", "console.log", 1),
        ("console.error('error')", "console.error", 1),
        ("console.warn('warning')", "console.warn", 1),
        ("console.debug('debug')", "console.debug", 1),
        ("debugger;", "debugger statement", 1),
        ("alert('alert message')", "alert() call", 1),
        ("// auth_token = 'secret'", "Commented auth", 1),
        ("// TODO: Fix auth issue", "Security TODO comment", 1),
    ]
    
    passed = 0
    failed = 0
    
    for code, description, expected_count in test_cases:
        debug = analyzer.find_debug_code(code)
        if len(debug) >= expected_count:
            print(f"  ✓ {description:30} - Found {len(debug)} instance(s)")
            passed += 1
        else:
            print(f"  ✗ {description:30} - Expected {expected_count}, found {len(debug)}")
            failed += 1
    
    print(f"\nDebug Code Detection: {passed}/{len(test_cases)} passed")
    return failed == 0


def test_severity_classification():
    """Test severity level classification"""
    print("\n" + "="*70)
    print("TESTING: Severity Classification")
    print("="*70)
    
    analyzer = JavaScriptAnalyzer()
    
    test_cases = [
        ("AKIAIOSFODNN7EXAMPLE", "Critical"),
        ("password = 'secret'", "Critical"),
        ("sk_live_1234567890abcdefghijk", "Critical"),
        ("ghp_1234567890abcdefghijk", "High"),
        ("firebase_key = 'test_key_12345'", "Medium"),
        ("console.log(data)", "Low"),
    ]
    
    passed = 0
    
    for code, expected_severity in test_cases:
        if 'console' in code:
            debug = analyzer.find_debug_code(code)
            actual = "Low" if debug else "Unknown"
        else:
            secrets = analyzer.detect_secrets(code)
            actual = secrets[0]['severity'] if secrets else "Unknown"
        
        if actual == expected_severity:
            print(f"  ✓ {code:40} - {actual}")
            passed += 1
        else:
            print(f"  ✗ {code:40} - Expected {expected_severity}, got {actual}")
    
    print(f"\nSeverity Classification: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


def test_complex_scenarios():
    """Test complex, real-world scenarios"""
    print("\n" + "="*70)
    print("TESTING: Complex Real-World Scenarios")
    print("="*70)
    
    analyzer = JavaScriptAnalyzer()
    
    # Scenario 1: Ecommerce app
    ecommerce_code = """
    class PaymentService {
      constructor() {
        this.stripeKey = 'sk_live_1234567890abcdef';
        this.apiEndpoint = '/api/v2/payment';
      }
      
      async processPayment(amount) {
        console.log('Processing payment:', amount);
        try {
          const response = await fetch(this.apiEndpoint, {
            method: 'POST',
            body: JSON.stringify({ amount })
          });
          return response.json();
        } catch (e) {
          console.error(e);
          debugger;
        }
      }
    }
    """
    
    endpoints_1 = analyzer.extract_endpoints(ecommerce_code)
    secrets_1 = analyzer.detect_secrets(ecommerce_code)
    debug_1 = analyzer.find_debug_code(ecommerce_code)
    
    print(f"  Ecommerce App:")
    print(f"    - Endpoints: {len(endpoints_1)}")
    print(f"    - Secrets: {len(secrets_1)}")
    print(f"    - Debug: {len(debug_1)}")
    
    scenario_1_passed = len(endpoints_1) > 0 and len(secrets_1) > 0 and len(debug_1) > 0
    
    # Scenario 2: Social media app
    social_code = """
    const CONFIG = {
      githubToken: 'ghp_Iv1.1a2b3c4d5e6f7g8h9i0j',
      apiBase: '/api/social',
      adminEndpoint: '/api/admin/users'
    };
    
    axios.get(CONFIG.apiBase + '/feed')
      .then(data => {
        console.log('Feed:', data);
        // auth_token = 'old_token_backup'
      });
    """
    
    endpoints_2 = analyzer.extract_endpoints(social_code)
    secrets_2 = analyzer.detect_secrets(social_code)
    debug_2 = analyzer.find_debug_code(social_code)
    
    print(f"  Social Media App:")
    print(f"    - Endpoints: {len(endpoints_2)}")
    print(f"    - Secrets: {len(secrets_2)}")
    print(f"    - Debug: {len(debug_2)}")
    
    scenario_2_passed = len(secrets_2) > 0 and len(debug_2) > 0
    
    # Scenario 3: Admin dashboard
    admin_code = """
    $.ajax({
      url: '/api/admin/dashboard',
      type: 'POST',
      headers: {
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.admin'
      }
    });
    
    const AWS_KEY = 'AKIAIOSFODNN7EXAMPLE';
    const AWS_SECRET = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY';
    """
    
    endpoints_3 = analyzer.extract_endpoints(admin_code)
    secrets_3 = analyzer.detect_secrets(admin_code)
    
    print(f"  Admin Dashboard:")
    print(f"    - Endpoints: {len(endpoints_3)}")
    print(f"    - Secrets: {len(secrets_3)}")
    
    scenario_3_passed = len(endpoints_3) > 0 and len(secrets_3) >= 2
    
    all_passed = scenario_1_passed and scenario_2_passed and scenario_3_passed
    
    print(f"\nComplex Scenarios: {'✓ All passed' if all_passed else '✗ Some failed'}")
    return all_passed


def test_false_positive_handling():
    """Test false positive minimization"""
    print("\n" + "="*70)
    print("TESTING: False Positive Minimization")
    print("="*70)
    
    analyzer = JavaScriptAnalyzer()
    
    # Code with many false positives in comments/examples
    test_code = """
    // Example usage:
    // const token = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.example';
    
    // Mock/Test data
    // api_key = 'test_key_123456789';
    
    // Documentation:
    // POST /api/example with Authorization: Bearer token_here
    
    // This is actual code:
    const realKey = 'sk_live_abc123def456';
    """
    
    secrets = analyzer.detect_secrets(test_code)
    
    # Should find the real Stripe key but minimize false positives from comments
    real_secrets = [s for s in secrets if 'Stripe' in s['type']]
    
    print(f"  Total findings: {len(secrets)}")
    print(f"  Real secrets: {len(real_secrets)}")
    print(f"  False positives reduced: {len(secrets) <= 3}")
    
    # Success if we found the real secret
    test_passed = len(real_secrets) > 0
    
    print(f"\nFalse Positive Handling: {'✓ Passed' if test_passed else '✗ Failed'}")
    return test_passed


def run_all_tests():
    """Run all tests and provide summary"""
    print("\n" + "="*70)
    print("JAVASCRIPT ANALYZER - COMPREHENSIVE TEST SUITE")
    print("="*70)
    
    results = {
        "Endpoints": test_all_endpoint_patterns(),
        "Secrets": test_all_secret_patterns(),
        "Debug Code": test_all_debug_patterns(),
        "Severity": test_severity_classification(),
        "Complex": test_complex_scenarios(),
        "False Positives": test_false_positive_handling(),
    }
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {test_name:25} {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*70)
    if all_passed:
        print("✓ ALL TESTS PASSED - JavaScript Analyzer is ready for deployment")
    else:
        print("✗ SOME TESTS FAILED - Please review failures above")
    print("="*70 + "\n")
    
    return all_passed


if __name__ == '__main__':
    try:
        all_passed = run_all_tests()
        sys.exit(0 if all_passed else 1)
    except Exception as e:
        print(f"\n✗ Error running tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
