#!/usr/bin/env python3
"""
Web Scanner Module Validation Script

Tests that all 15+ web scanner modules load without errors
and validates basic functionality.
"""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# List of all web scanner modules to validate
WEB_MODULES = [
    'access_control_tester',
    'auth_tester',
    'business_logic_tester',
    'bulk_scanner',
    'cloud_scanner',
    'confidence_scorer',
    'csrf_ssrf_tester',
    'detectors',
    'evidence_collector',
    'file_misconfig_tester',
    'fp_pattern_database',
    'injection_tester',
    'js_analyzer',
    'payloads',
    'ratelimit_tester',
    'scan_comparison',
    'scope_enforcer',
    'sensitive_data_tester',
    'surface_mapper',
    'verification_hints',
    'web_logger',
    'vulnerability_classifier',
    'xss_tester',
    'web_scanner_orchestrator',
]

def test_module_imports():
    """Test that all web scanner modules can be imported."""
    logger.info("=" * 70)
    logger.info("VALIDATION: Web Scanner Module Imports")
    logger.info("=" * 70)
    
    failed = []
    passed = []
    
    for module_name in WEB_MODULES:
        try:
            exec(f"from scanner.web.{module_name} import *")
            passed.append(module_name)
            logger.info(f"✓ {module_name}")
        except Exception as e:
            failed.append((module_name, str(e)))
            logger.error(f"✗ {module_name}: {e}")
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info(f"SUMMARY: {len(passed)}/{len(WEB_MODULES)} modules loaded successfully")
    logger.info("=" * 70)
    
    if failed:
        logger.error(f"\n{len(failed)} modules FAILED to load:")
        for module, error in failed:
            logger.error(f"  - {module}: {error}")
        return False
    else:
        logger.info(f"\n✓ All {len(passed)} modules loaded successfully!")
        return True

def test_confidence_scorer():
    """Test ConfidenceScorer basic functionality."""
    logger.info("\n" + "=" * 70)
    logger.info("VALIDATION: ConfidenceScorer Functionality")
    logger.info("=" * 70)
    
    try:
        from scanner.web.confidence_scorer import ConfidenceScorer, ConfidenceLevel
        
        scorer = ConfidenceScorer()
        logger.info("✓ ConfidenceScorer instantiated")
        
        # Verify key attributes exist
        assert hasattr(scorer, 'calculate_confidence'), "Missing calculate_confidence method"
        logger.info("✓ ConfidenceScorer has calculate_confidence method")
        
        # Verify ConfidenceLevel enum
        levels = [e.value for e in ConfidenceLevel]
        logger.info(f"✓ ConfidenceLevel enum available: {levels}")
        
        return True
    except Exception as e:
        logger.error(f"✗ ConfidenceScorer test failed: {e}")
        return False

def test_xss_tester_import():
    """Test XSSTester can be imported and instantiated."""
    logger.info("\n" + "=" * 70)
    logger.info("VALIDATION: XSSTester Module")
    logger.info("=" * 70)
    
    try:
        from scanner.web.xss_tester import XSSTester, XSSContext
        
        tester = XSSTester()
        logger.info("✓ XSSTester instantiated")
        
        # Verify key attributes exist
        assert hasattr(tester, 'test_endpoint_xss'), "Missing test_endpoint_xss method"
        assert hasattr(tester, 'test_parameter_xss'), "Missing test_parameter_xss method"
        assert hasattr(tester, 'test_dom_based_xss'), "Missing test_dom_based_xss method"
        logger.info("✓ XSSTester has all test methods")
        
        # Verify XSSContext enum
        contexts = [c.value for c in XSSContext]
        logger.info(f"✓ XSSContext types available: {contexts}")
        
        return True
    except Exception as e:
        logger.error(f"✗ XSSTester test failed: {e}")
        return False

def test_injection_tester_import():
    """Test InjectionTester can be imported."""
    logger.info("\n" + "=" * 70)
    logger.info("VALIDATION: InjectionTester Module")
    logger.info("=" * 70)
    
    try:
        from scanner.web.injection_tester import InjectionTester
        
        tester = InjectionTester(depth=1, timeout=5)
        logger.info("✓ InjectionTester instantiated with depth=1")
        
        assert hasattr(tester, 'test_sqli_url_parameter'), "Missing test_sqli_url_parameter method"
        assert hasattr(tester, 'test_command_injection'), "Missing test_command_injection method"
        assert hasattr(tester, 'test_nosql_injection'), "Missing test_nosql_injection method"
        logger.info("✓ InjectionTester has all test methods")
        
        return True
    except Exception as e:
        logger.error(f"✗ InjectionTester test failed: {e}")
        return False

def test_surface_mapper_import():
    """Test SurfaceMapper can be imported."""
    logger.info("\n" + "=" * 70)
    logger.info("VALIDATION: SurfaceMapper Module")
    logger.info("=" * 70)
    
    try:
        from scanner.web.surface_mapper import SurfaceMapper, Endpoint, Parameter
        
        mapper = SurfaceMapper(base_url="http://localhost:8000")
        logger.info("✓ SurfaceMapper instantiated")
        
        assert hasattr(mapper, 'run'), "Missing run method"
        logger.info("✓ SurfaceMapper has run method")
        
        # Test data classes
        param = Parameter(name="test", param_type="string")
        logger.info(f"✓ Parameter dataclass works: {param.name}")
        
        return True
    except Exception as e:
        logger.error(f"✗ SurfaceMapper test failed: {e}")
        return False

def test_scope_enforcer_import():
    """Test ScopeEnforcer can be imported."""
    logger.info("\n" + "=" * 70)
    logger.info("VALIDATION: ScopeEnforcer Module")
    logger.info("=" * 70)
    
    try:
        from scanner.web.scope_enforcer import ScopeEnforcer
        
        enforcer = ScopeEnforcer(
            base_url="http://example.com",
            authorized_targets=["example.com"]
        )
        logger.info("✓ ScopeEnforcer instantiated")
        
        # Test same origin check
        is_same = enforcer.is_same_origin("http://example.com/path")
        logger.info(f"✓ Same origin check works: is_same={is_same}")
        
        return True
    except Exception as e:
        logger.error(f"✗ ScopeEnforcer test failed: {e}")
        return False

def test_evidence_collector_import():
    """Test EvidenceCollector can be imported."""
    logger.info("\n" + "=" * 70)
    logger.info("VALIDATION: EvidenceCollector Module")
    logger.info("=" * 70)
    
    try:
        from scanner.web.evidence_collector import VulnerabilityAggregator, FindingType
        
        aggregator = VulnerabilityAggregator()
        logger.info("✓ VulnerabilityAggregator instantiated")
        
        # Test finding types
        types = [t.value for t in FindingType]
        logger.info(f"✓ FindingType enum has {len(types)} types")
        
        return True
    except Exception as e:
        logger.error(f"✗ EvidenceCollector test failed: {e}")
        return False

def test_bulk_scanner_import():
    """Test BulkScanner can be imported."""
    logger.info("\n" + "=" * 70)
    logger.info("VALIDATION: BulkScanner Module")
    logger.info("=" * 70)
    
    try:
        from scanner.web.bulk_scanner import BulkScanner, ScanTask
        
        scanner = BulkScanner(max_parallel=5)
        logger.info("✓ BulkScanner instantiated with max_parallel=5")
        
        # Test task creation
        task = ScanTask(
            target_id="test",
            target_url="http://test.local",
            modules={},
            job_id="job1"
        )
        logger.info(f"✓ ScanTask created: {task.target_id}")
        
        return True
    except Exception as e:
        logger.error(f"✗ BulkScanner test failed: {e}")
        return False

def test_cloud_scanner_import():
    """Test CloudScanner can be imported."""
    logger.info("\n" + "=" * 70)
    logger.info("VALIDATION: CloudScanner Module")
    logger.info("=" * 70)
    
    try:
        from scanner.web.cloud_scanner import CloudConfigScanner
        
        scanner = CloudConfigScanner(timeout=5)
        logger.info("✓ CloudConfigScanner instantiated")
        
        assert hasattr(scanner, 'check_aws_metadata'), "Missing check_aws_metadata method"
        logger.info("✓ CloudConfigScanner has check_aws_metadata method")
        
        return True
    except Exception as e:
        logger.error(f"✗ CloudScanner test failed: {e}")
        return False

def run_all_validations():
    """Run all validation tests."""
    logger.info("\n")
    logger.info("╔" + "=" * 68 + "╗")
    logger.info("║" + " " * 68 + "║")
    logger.info("║" + "Web Scanner Module Validation Suite".center(68) + "║")
    logger.info("║" + " " * 68 + "║")
    logger.info("╚" + "=" * 68 + "╝")
    
    tests = [
        ("Module Imports", test_module_imports),
        ("ConfidenceScorer", test_confidence_scorer),
        ("XSSTester", test_xss_tester_import),
        ("InjectionTester", test_injection_tester_import),
        ("SurfaceMapper", test_surface_mapper_import),
        ("ScopeEnforcer", test_scope_enforcer_import),
        ("EvidenceCollector", test_evidence_collector_import),
        ("BulkScanner", test_bulk_scanner_import),
        ("CloudScanner", test_cloud_scanner_import),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Final summary
    logger.info("\n" + "=" * 70)
    logger.info("FINAL VALIDATION SUMMARY")
    logger.info("=" * 70)
    
    passed_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info("\n" + "=" * 70)
    logger.info(f"OVERALL: {passed_count}/{total_count} validation tests passed")
    logger.info("=" * 70)
    
    return passed_count == total_count

if __name__ == "__main__":
    success = run_all_validations()
    sys.exit(0 if success else 1)
