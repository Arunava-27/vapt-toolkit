#!/usr/bin/env python3
"""Quick validation script for bulk scanning implementation."""

import sys
from database import init_db, create_bulk_job, get_bulk_job
from scanner.web.bulk_scanner import BulkScanner

def test_database():
    """Test database functions."""
    print("Testing database functions...")
    
    try:
        # Initialize database
        init_db()
        print("  ✅ Database initialization")
        
        # Create a bulk job
        job_id = create_bulk_job(
            project_id="test-project",
            targets=["example.com", "test.org"],
            config={"recon": True, "ports": True}
        )
        print(f"  ✅ Created bulk job: {job_id[:8]}...")
        
        # Retrieve the job
        job = get_bulk_job(job_id)
        assert job is not None, "Job not found"
        assert job["status"] == "pending", f"Expected pending, got {job['status']}"
        assert job["total_targets"] == 2, f"Expected 2 targets, got {job['total_targets']}"
        print(f"  ✅ Retrieved bulk job with correct schema")
        
        return True
    except Exception as e:
        print(f"  ❌ Database test failed: {e}")
        return False


def test_bulk_scanner():
    """Test BulkScanner class."""
    print("Testing BulkScanner class...")
    
    try:
        # Create scanner
        scanner = BulkScanner(max_parallel=5)
        print("  ✅ BulkScanner initialized")
        
        # Create job
        job_id = "test-job-123"
        targets = ["example.com", "test.org", "sample.com"]
        modules = {"recon": True, "ports": True}
        
        result = scanner.create_job(job_id, targets, modules)
        assert result == job_id, "Job ID mismatch"
        print(f"  ✅ Created job with {len(targets)} targets")
        
        # Get status
        status = scanner.get_job_status(job_id)
        assert status["total"] == 3, f"Expected 3 total, got {status['total']}"
        assert status["progress"] == 0, f"Expected 0% progress, got {status['progress']}"
        print(f"  ✅ Job status correct: {status['progress']}% complete")
        
        # Cancel job
        cancel_result = scanner.cancel_job(job_id)
        assert cancel_result["status"] == "cancellation_requested"
        print(f"  ✅ Job cancellation works")
        
        return True
    except Exception as e:
        print(f"  ❌ BulkScanner test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validation tests."""
    print("\n" + "="*60)
    print("  BULK SCANNING IMPLEMENTATION VALIDATION")
    print("="*60 + "\n")
    
    results = []
    
    # Test database
    results.append(("Database", test_database()))
    
    # Test BulkScanner
    results.append(("BulkScanner", test_bulk_scanner()))
    
    # Summary
    print("\n" + "="*60)
    print("  VALIDATION SUMMARY")
    print("="*60)
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {name:.<40} {status}")
    
    all_passed = all(p for _, p in results)
    
    print("\n" + "="*60)
    if all_passed:
        print("  ✅ ALL VALIDATIONS PASSED - IMPLEMENTATION READY")
        print("="*60 + "\n")
        return 0
    else:
        print("  ❌ SOME VALIDATIONS FAILED - FIX ISSUES ABOVE")
        print("="*60 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
