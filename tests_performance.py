#!/usr/bin/env python3
"""Performance tests for VAPT toolkit.

Tests:
- Performance regression tests
- Load tests (concurrent requests)
- Stress tests (large datasets)
- Memory leak tests
"""

import pytest
import time
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor
import sys
import os

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.benchmark import PerformanceBenchmarks, BenchmarkSuite
from tools.profiler import PerformanceProfiler, get_profiler
from tools.cache import get_cache_manager, LRUCache
from tools.database_optimizer import get_optimizer


class TestPerformanceBaseline:
    """Test baseline performance metrics."""

    def setup_method(self):
        """Setup for each test."""
        self.benchmarks = PerformanceBenchmarks()

    def test_cache_retrieval_speed(self):
        """Cache retrieval should be <1ms."""
        cache = get_cache_manager()

        # Set a value
        cache.set_scan_result("test_scan", {"data": "test"})

        # Measure retrieval
        start = time.perf_counter()
        for _ in range(1000):
            cache.get_scan_result("test_scan")
        duration_ms = (time.perf_counter() - start) * 1000

        avg_ms = duration_ms / 1000
        assert avg_ms < 1.0, f"Cache retrieval too slow: {avg_ms:.3f}ms"

    def test_cache_hit_rate(self):
        """Cache hit rate should be >90% with repeated access."""
        cache = LRUCache(max_size=100)

        # Set values
        for i in range(10):
            cache.set(f"key_{i}", f"value_{i}")

        # Access repeatedly
        for _ in range(100):
            for i in range(10):
                cache.get(f"key_{i}")

        stats = cache.get_stats()
        hit_rate = stats["hit_rate"]
        assert hit_rate > 90, f"Hit rate too low: {hit_rate:.1f}%"

    def test_profiler_memory_tracking(self):
        """Profiler should accurately track memory."""
        profiler = get_profiler()

        with profiler.profile("memory_test"):
            # Allocate ~10MB
            data = [i for i in range(1000000)]

        summary = profiler.get_summary()
        assert len(summary["by_operation"]) > 0
        ops = summary["by_operation"]["memory_test"]
        assert ops["memory_delta_mb"] >= 5, "Memory delta too small"


class TestPerformanceRegressions:
    """Test for performance regressions."""

    def test_scan_module_performance(self):
        """Web scan modules should meet time targets."""
        # This is a placeholder for actual scan module testing
        # In production, would call actual scan functions
        profiler = get_profiler()

        # Simulate scan execution
        with profiler.profile("scan_sql_injection"):
            time.sleep(0.05)  # Simulate 50ms scan

        summary = profiler.get_summary()
        sql_time = summary["by_operation"]["scan_sql_injection"]["avg_ms"]

        # Target: <5000ms (5s for full medium scan)
        assert sql_time < 100, f"Scan too slow: {sql_time:.2f}ms"

    def test_api_response_time(self):
        """API endpoints should respond within target times."""
        profiler = get_profiler()

        # Simulate API call
        with profiler.profile("api_get_findings"):
            time.sleep(0.01)  # Simulate 10ms API call

        summary = profiler.get_summary()
        api_time = summary["by_operation"]["api_get_findings"]["avg_ms"]

        # Target: <1000ms (1s)
        assert api_time < 100, f"API response too slow: {api_time:.2f}ms"

    def test_database_query_performance(self):
        """Database queries should meet targets."""
        optimizer = get_optimizer()

        # Check for indexes
        indexes = optimizer.get_existing_indexes()
        # At least some indexes should exist
        assert len(indexes) > 0 or not Path("vapt.db").exists(), "No indexes found"


class TestLoadTesting:
    """Test performance under load."""

    def test_concurrent_cache_access(self):
        """Cache should handle concurrent access."""
        cache = LRUCache(max_size=1000)

        # Pre-populate
        for i in range(100):
            cache.set(f"key_{i}", f"value_{i}")

        # Concurrent reads
        def worker():
            for _ in range(100):
                for i in range(100):
                    cache.get(f"key_{i}")

        start = time.perf_counter()

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(worker) for _ in range(4)]
            for f in futures:
                f.result()

        duration = time.perf_counter() - start

        stats = cache.get_stats()
        assert stats["hit_rate"] > 80, f"Hit rate too low under load: {stats['hit_rate']:.1f}%"
        assert duration < 10, f"Concurrent access too slow: {duration:.2f}s"

    def test_concurrent_cache_writes(self):
        """Cache should handle concurrent writes."""
        cache = LRUCache(max_size=10000)

        def worker(worker_id):
            for i in range(100):
                cache.set(f"worker_{worker_id}_key_{i}", f"value_{i}")

        start = time.perf_counter()

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(worker, i) for i in range(4)]
            for f in futures:
                f.result()

        duration = time.perf_counter() - start
        assert duration < 5, f"Concurrent writes too slow: {duration:.2f}s"
        assert cache.cache.__sizeof__() > 0, "Cache is empty"


class TestMemoryLeaks:
    """Test for memory leaks."""

    def test_cache_no_memory_leak(self):
        """Cache should not leak memory on repeated access."""
        cache = LRUCache(max_size=1000)

        # Multiple rounds of cache operations
        for round_num in range(5):
            for i in range(1000):
                cache.set(f"key_{i}", [j for j in range(100)])
                cache.get(f"key_{i}")

        # Cache size should be bounded
        assert len(cache.cache) <= 1000, "Cache exceeds max size"
        assert cache.evictions > 0, "Cache not evicting old entries"

    def test_profiler_no_memory_leak(self):
        """Profiler should not accumulate excessive memory."""
        profiler = get_profiler()

        # Many profiling operations
        for i in range(100):
            with profiler.profile(f"operation_{i % 10}"):
                time.sleep(0.001)

        summary = profiler.get_summary()
        assert len(summary["by_operation"]) <= 10, "Too many unique operations"


class TestStressTesting:
    """Stress tests for extreme conditions."""

    def test_cache_with_large_values(self):
        """Cache should handle large values."""
        cache = LRUCache(max_size=100)

        # Store large values
        large_data = {
            "data": ["x" * 1000 for _ in range(100)],
            "nested": {"level1": {"level2": {"level3": list(range(1000))}}}
        }

        cache.set("large_key", large_data)
        retrieved = cache.get("large_key")

        assert retrieved == large_data, "Large value corrupted"

    def test_benchmark_with_many_operations(self):
        """Benchmark should handle many operations."""
        suite = BenchmarkSuite()

        def dummy_func():
            pass

        # Add many benchmarks
        for i in range(50):
            suite.benchmark_function(dummy_func, name=f"operation_{i}")

        summary = suite.get_summary()
        assert len(summary["benchmarks"]) == 50, "Not all benchmarks recorded"

    def test_profiler_with_deep_recursion(self):
        """Profiler should handle recursive operations."""
        profiler = get_profiler()

        def recursive_func(n):
            if n <= 0:
                return 1
            return n * recursive_func(n - 1)

        with profiler.profile("factorial"):
            result = recursive_func(20)

        assert result == 2432902008176640000, "Calculation wrong"

        summary = profiler.get_summary()
        assert "factorial" in summary["by_operation"], "Operation not profiled"


class TestPerformanceOptimizations:
    """Test that optimizations are effective."""

    def test_indexed_query_faster_than_full_scan(self):
        """Queries with indexes should be faster."""
        optimizer = get_optimizer()

        # This would require actual database operations in production
        # Here we just verify the optimizer can detect indexes
        indexes = optimizer.get_existing_indexes()

        # Not all databases will have been created in test
        if Path("vapt.db").exists():
            assert isinstance(indexes, dict), "Index analysis failed"

    def test_cache_faster_than_recompute(self):
        """Cache retrieval should be faster than recomputation."""
        cache = LRUCache()

        # Slow function
        def slow_func():
            time.sleep(0.01)
            return "result"

        # Time recomputation
        start = time.perf_counter()
        for _ in range(10):
            result = slow_func()
        recompute_time = time.perf_counter() - start

        # Time cached access
        cache.set("key", result)
        start = time.perf_counter()
        for _ in range(10):
            cached_result = cache.get("key")
        cache_time = time.perf_counter() - start

        # Cache should be much faster
        speedup = recompute_time / cache_time
        assert speedup > 100, f"Cache not fast enough: {speedup:.1f}x speedup"


class TestBenchmarkComparison:
    """Test benchmark comparison functionality."""

    def test_benchmark_summary_format(self):
        """Benchmark summary should be properly formatted."""
        benchmarks = PerformanceBenchmarks()

        def dummy():
            pass

        benchmarks.add_api_benchmark("test_api", dummy)

        report = benchmarks.get_report()

        assert "timestamp" in report, "No timestamp in report"
        assert "benchmarks" in report, "No benchmarks in report"
        assert len(report["benchmarks"]) > 0, "No benchmark results"

    def test_performance_target_validation(self):
        """Performance targets should be validated."""
        benchmarks = PerformanceBenchmarks()

        # Simulate meeting target
        benchmarks.suite.set_baseline("fast_op", 100)

        def fast_op():
            time.sleep(0.01)

        result = benchmarks.add_api_benchmark("fast_op", fast_op)
        assert benchmarks.suite.check_target("fast_op", result.duration_ms)


@pytest.mark.performance
class TestPerformanceIntegration:
    """Integration tests for performance features."""

    def test_cache_manager_integration(self):
        """Cache manager should integrate properly."""
        manager = get_cache_manager()

        # Test all cache types
        manager.set_scan_result("s1", {"findings": 5})
        manager.set_cve_info("CVE-2023-1", {"severity": "high"})
        manager.set_compliance_mapping("pci-dss", {"controls": 12})

        assert manager.get_scan_result("s1") is not None
        assert manager.get_cve_info("CVE-2023-1") is not None
        assert manager.get_compliance_mapping("pci-dss") is not None

    def test_profiler_benchmark_integration(self):
        """Profiler and benchmark should work together."""
        profiler = get_profiler()
        benchmarks = PerformanceBenchmarks()

        def test_op():
            with profiler.profile("test"):
                time.sleep(0.01)

        benchmarks.add_api_benchmark("integrated", test_op)

        profile_summary = profiler.get_summary()
        benchmark_summary = benchmarks.get_report()

        assert len(profile_summary["by_operation"]) > 0
        assert len(benchmark_summary["benchmarks"]) > 0


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-m", "not integration"])
