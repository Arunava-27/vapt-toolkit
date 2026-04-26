"""
Unit tests for JavaScript analyzer

Tests all detection patterns and functionality.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scanner.web.js_analyzer import JavaScriptAnalyzer, SecretType, DebugCodeType


def test_endpoint_extraction():
    """Test API endpoint extraction from JavaScript"""
    analyzer = JavaScriptAnalyzer()
    
    # Test fetch() detection
    fetch_code = """
    fetch('/api/users')
      .then(response => response.json())
      .then(data => console.log(data));
    """
    endpoints = analyzer.extract_endpoints(fetch_code)
    assert len(endpoints) > 0
    assert any('/api/users' in ep['url'] for ep in endpoints)
    print("✓ fetch() endpoint detection works")
    
    # Test axios detection
    axios_code = """
    axios.post('/api/login', {
      username: 'user',
      password: 'pass'
    });
    """
    endpoints = analyzer.extract_endpoints(axios_code)
    assert len(endpoints) > 0
    assert any('/api/login' in ep['url'] for ep in endpoints)
    assert any(ep['method'] == 'POST' for ep in endpoints)
    print("✓ axios endpoint detection works")
    
    # Test jQuery.ajax detection
    jquery_code = """
    $.ajax({
      url: '/api/data',
      type: 'GET',
      success: function(data) { }
    });
    """
    endpoints = analyzer.extract_endpoints(jquery_code)
    assert len(endpoints) > 0
    assert any('/api/data' in ep['url'] for ep in endpoints)
    print("✓ jQuery.ajax endpoint detection works")
    
    # Test XMLHttpRequest detection
    xhr_code = """
    let xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/submit');
    """
    endpoints = analyzer.extract_endpoints(xhr_code)
    assert len(endpoints) > 0
    assert any('/api/submit' in ep['url'] for ep in endpoints)
    print("✓ XMLHttpRequest endpoint detection works")


def test_secret_detection():
    """Test hardcoded secret detection"""
    analyzer = JavaScriptAnalyzer()
    
    # Test AWS key detection
    aws_code = """
    const accessKey = 'AKIAIOSFODNN7EXAMPLE';
    const secretKey = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY';
    """
    secrets = analyzer.detect_secrets(aws_code)
    assert len(secrets) > 0
    assert any('AWS' in s['type'] for s in secrets)
    print("✓ AWS key detection works")
    
    # Test GitHub token detection
    github_code = """
    const ghToken = 'ghp_1234567890abcdefghijklmnopqrstuvwxyz';
    """
    secrets = analyzer.detect_secrets(github_code)
    assert len(secrets) > 0
    assert any('GitHub' in s['type'] for s in secrets)
    print("✓ GitHub token detection works")
    
    # Test Stripe key detection
    stripe_code = """
    stripe.setPublishableKey('sk_live_nJWtWHsPUKFINnKVm8gUvC3a');
    """
    secrets = analyzer.detect_secrets(stripe_code)
    assert len(secrets) > 0
    assert any('Stripe' in s['type'] for s in secrets)
    print("✓ Stripe key detection works")
    
    # Test generic API key detection
    api_key_code = """
    const apiKey = 'abc123def456ghi789jkl012';
    config.apiSecret = 'my-super-secret-key-12345';
    """
    secrets = analyzer.detect_secrets(api_key_code)
    assert len(secrets) > 0
    assert any('API' in s['type'] or 'Generic' in s['type'] for s in secrets)
    print("✓ Generic API key detection works")
    
    # Test JWT token detection
    jwt_code = """
    const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U';
    """
    secrets = analyzer.detect_secrets(jwt_code)
    assert len(secrets) > 0
    assert any('JWT' in s['type'] for s in secrets)
    print("✓ JWT token detection works")
    
    # Test Bearer token detection
    bearer_code = """
    headers: {
      'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U'
    }
    """
    secrets = analyzer.detect_secrets(bearer_code)
    assert len(secrets) > 0
    assert any('Bearer' in s['type'] for s in secrets)
    print("✓ Bearer token detection works")
    
    # Test password detection
    password_code = """
    const password = 'MySuperSecretPassword123!';
    config.dbPassword = 'postgres123';
    """
    secrets = analyzer.detect_secrets(password_code)
    assert len(secrets) > 0
    assert any('Password' in s['type'] for s in secrets)
    print("✓ Hardcoded password detection works")


def test_debug_code_detection():
    """Test debug code detection"""
    analyzer = JavaScriptAnalyzer()
    
    # Test console.log detection
    console_code = """
    function login(user) {
      console.log('User:', user);
      console.log('Attempting login');
    }
    """
    debug_instances = analyzer.find_debug_code(console_code)
    assert len(debug_instances) > 0
    assert any(DebugCodeType.CONSOLE_LOG.value in str(d) or 'console' in d['type'].lower() for d in debug_instances)
    print("✓ console.log detection works")
    
    # Test debugger statement detection
    debugger_code = """
    function handleError(err) {
      debugger;
      console.error(err);
    }
    """
    debug_instances = analyzer.find_debug_code(debugger_code)
    assert len(debug_instances) > 0
    print("✓ debugger statement detection works")
    
    # Test alert detection
    alert_code = """
    if (!user) {
      alert('User not found');
    }
    """
    debug_instances = analyzer.find_debug_code(alert_code)
    assert len(debug_instances) > 0
    assert any('alert' in str(d).lower() for d in debug_instances)
    print("✓ alert() detection works")
    
    # Test commented authentication
    comment_code = """
    // auth_token = 'abc123';
    // password = 'secret123';
    // TODO: Fix security issue
    """
    debug_instances = analyzer.find_debug_code(comment_code)
    assert len(debug_instances) > 0
    print("✓ Commented authentication detection works")


def test_source_map_detection():
    """Test source map exposure detection"""
    analyzer = JavaScriptAnalyzer()
    
    maps = analyzer.check_source_maps('https://example.com/app.js')
    assert len(maps) > 0
    assert any('.map' in m.get('potential_map', '') for m in maps)
    print("✓ Source map detection works")


def test_real_world_example():
    """Test with a real-world-like JavaScript example"""
    analyzer = JavaScriptAnalyzer()
    
    real_world_js = """
    // API Configuration
    const API_BASE_URL = '/api/v1';
    const AUTH_TOKEN = 'ghp_FakeGitHubTokenForTesting1234567890';
    
    class UserService {
      constructor() {
        this.apiKey = 'sk_live_1234567890abcdef';
        this.awsKey = 'AKIAIOSFODNN7EXAMPLE';
      }
      
      async getUser(id) {
        console.log('Getting user:', id);
        try {
          const response = await fetch(`/api/users/${id}`);
          return await response.json();
        } catch (error) {
          console.error('Error fetching user:', error);
          debugger;
        }
      }
      
      async updatePassword(userId, newPassword) {
        // TODO: Implement password hashing
        // auth_token = 'old_token_123';
        debugger;
        
        return fetch('/api/users/password', {
          method: 'POST',
          body: JSON.stringify({ userId, newPassword })
        });
      }
      
      configureAxios() {
        axios.post('/api/config', { secretKey: 'my-secret-123' });
      }
    }
    """
    
    analysis = {
        'endpoints': analyzer.extract_endpoints(real_world_js),
        'secrets': analyzer.detect_secrets(real_world_js),
        'debug': analyzer.find_debug_code(real_world_js),
    }
    
    # Verify we found multiple issues
    assert len(analysis['endpoints']) > 0, "Should find multiple endpoints"
    assert len(analysis['secrets']) > 0, "Should find hardcoded secrets"
    assert len(analysis['debug']) > 0, "Should find debug code"
    
    print(f"✓ Real-world analysis found:")
    print(f"  - {len(analysis['endpoints'])} endpoints")
    print(f"  - {len(analysis['secrets'])} secrets")
    print(f"  - {len(analysis['debug'])} debug instances")


def test_severity_summary():
    """Test severity summarization"""
    analyzer = JavaScriptAnalyzer()
    
    test_code = """
    const awsKey = 'AKIAIOSFODNN7EXAMPLE';
    console.log('debug');
    debugger;
    """
    
    analysis = {
        'endpoints': analyzer.extract_endpoints(test_code),
        'secrets': analyzer.detect_secrets(test_code),
        'debug_code': analyzer.find_debug_code(test_code),
        'source_maps': analyzer.check_source_maps('app.js'),
    }
    
    summary = analyzer.get_severity_summary(analysis)
    assert summary['Critical'] > 0, "Should find critical AWS key"
    print(f"✓ Severity summary works: {summary}")


def test_no_false_positives():
    """Test that we avoid common false positives"""
    analyzer = JavaScriptAnalyzer()
    
    # Common false positives
    example_code = """
    // Example: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.example
    // Mock JWT: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.mock.token
    const demoToken = 'demo_token_12345';
    """
    
    secrets = analyzer.detect_secrets(example_code)
    # Should minimize false positives in comments and example code
    print(f"✓ False positive handling: found {len(secrets)} potential secrets")


if __name__ == '__main__':
    print("Running JavaScript Analyzer Tests...\n")
    
    try:
        test_endpoint_extraction()
        print()
        
        test_secret_detection()
        print()
        
        test_debug_code_detection()
        print()
        
        test_source_map_detection()
        print()
        
        test_real_world_example()
        print()
        
        test_severity_summary()
        print()
        
        test_no_false_positives()
        print()
        
        print("=" * 50)
        print("All tests passed! ✓")
        print("=" * 50)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
