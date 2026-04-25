#!/usr/bin/env python3
"""Benchmarking suite for VAPT toolkit.

Measures:
- Scan execution time (by module)
- API response times (all endpoints)
- Database query performance
- Memory consumption
"""

import time
import psutil
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Callable, Coroutine
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import statistics


@dataclass
class BenchmarkResult:
    """Result of a benchmark operation."""
    name: str
    duration_ms: float
    memory_mb: float
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class BenchmarkSuite:
    """Benchmarking suite for performance testing."""

    def __init__(self, output_dir: str = "data/benchmarks"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[BenchmarkResult] = []
        self.baseline: Dict[str, float] = {}

    def benchmark_function(
        self,
        func: Callable,
        *args,
        name: str = None,
        iterations: int = 1,
        **kwargs
    ) -> BenchmarkResult:
        """Benchmark a synchronous function."""
        name = name or func.__name__

        times = []
        for _ in range(iterations):
            process = psutil.Process()
            mem_before = process.memory_info().rss / 1024 / 1024

            start = time.perf_counter()
            func(*args, **kwargs)
            duration = (time.perf_counter() - start) * 1000

            mem_after = process.memory_info().rss / 1024 / 1024
            times.append(duration)

        avg_duration = statistics.mean(times)
        memory_mb = mem_after

        result = BenchmarkResult(
            name=name,
            duration_ms=avg_duration,
            memory_mb=memory_mb,
        )
        self.results.append(result)
        return result

    async def benchmark_async_function(
        self,
        func: Callable,
        *args,
        name: str = None,
        iterations: int = 1,
        **kwargs
    ) -> BenchmarkResult:
        """Benchmark an async function."""
        name = name or func.__name__

        times = []
        for _ in range(iterations):
            process = psutil.Process()
            mem_before = process.memory_info().rss / 1024 / 1024

            start = time.perf_counter()
            await func(*args, **kwargs)
            duration = (time.perf_counter() - start) * 1000

            mem_after = process.memory_info().rss / 1024 / 1024
            times.append(duration)

        avg_duration = statistics.mean(times)
        memory_mb = mem_after

        result = BenchmarkResult(
            name=name,
            duration_ms=avg_duration,
            memory_mb=memory_mb,
        )
        self.results.append(result)
        return result

    def benchmark_concurrent(
        self,
        func: Callable,
        tasks: List[tuple],
        name: str = None,
        max_workers: int = 4,
    ) -> BenchmarkResult:
        """Benchmark concurrent execution of tasks.

        Args:
            func: Function to execute
            tasks: List of (args, kwargs) tuples
            name: Benchmark name
            max_workers: Max concurrent workers
        """
        name = name or func.__name__

        process = psutil.Process()
        mem_before = process.memory_info().rss / 1024 / 1024

        start = time.perf_counter()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for args, kwargs in tasks:
                future = executor.submit(func, *args, **kwargs)
                futures.append(future)

            # Wait for all to complete
            for future in futures:
                future.result()

        duration = (time.perf_counter() - start) * 1000
        mem_after = process.memory_info().rss / 1024 / 1024

        result = BenchmarkResult(
            name=name,
            duration_ms=duration,
            memory_mb=mem_after,
        )
        self.results.append(result)
        return result

    def set_baseline(self, name: str, target_ms: float) -> None:
        """Set baseline/target for a benchmark."""
        self.baseline[name] = target_ms

    def check_target(self, name: str, duration_ms: float) -> bool:
        """Check if benchmark meets target."""
        if name not in self.baseline:
            return True
        return duration_ms <= self.baseline[name]

    def get_summary(self) -> Dict[str, Any]:
        """Get benchmark summary."""
        if not self.results:
            return {}

        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_benchmarks": len(self.results),
            "benchmarks": [],
        }

        for result in self.results:
            benchmark = asdict(result)
            if result.name in self.baseline:
                target = self.baseline[result.name]
                benchmark["target_ms"] = target
                benchmark["meets_target"] = result.duration_ms <= target
                benchmark["overhead_ms"] = result.duration_ms - target
            summary["benchmarks"].append(benchmark)

        return summary

    def save_report(self, filename: str = "benchmark_report.json"):
        """Save benchmark report to file."""
        filepath = self.output_dir / filename
        report = self.get_summary()

        with open(filepath, "w") as f:
            json.dump(report, f, indent=2)

        return filepath

    def print_report(self):
        """Print benchmark report."""
        summary = self.get_summary()

        if not summary:
            print("No benchmark data available")
            return

        print("\n" + "=" * 80)
        print("BENCHMARK REPORT")
        print("=" * 80)
        print(f"\nTimestamp: {summary['timestamp']}")
        print(f"Total Benchmarks: {summary['total_benchmarks']}")
        print("\n" + "-" * 80)

        for benchmark in summary["benchmarks"]:
            print(f"\n{benchmark['name']}:")
            print(f"  Duration: {benchmark['duration_ms']:.2f}ms")
            print(f"  Memory: {benchmark['memory_mb']:.2f}MB")

            if "target_ms" in benchmark:
                status = "[PASS]" if benchmark["meets_target"] else "[FAIL]"
                print(f"  Target: {benchmark['target_ms']:.2f}ms {status}")
                if benchmark["overhead_ms"] > 0:
                    print(f"  Overhead: {benchmark['overhead_ms']:.2f}ms")

        print("\n" + "=" * 80)


class PerformanceBenchmarks:
    """Pre-defined benchmark suite for VAPT toolkit."""

    def __init__(self):
        self.suite = BenchmarkSuite()
        self._setup_targets()

    def _setup_targets(self):
        """Set up performance targets."""
        # Scan execution targets
        self.suite.set_baseline("scan_sql_injection", 5000)  # 5 seconds
        self.suite.set_baseline("scan_xss", 5000)
        self.suite.set_baseline("scan_directory_traversal", 3000)

        # API response targets
        self.suite.set_baseline("api_create_scan", 1000)  # 1 second
        self.suite.set_baseline("api_get_findings", 500)  # 500ms
        self.suite.set_baseline("api_list_scans", 300)  # 300ms

        # Database query targets
        self.suite.set_baseline("db_query_findings", 100)  # 100ms
        self.suite.set_baseline("db_query_scans", 50)  # 50ms

        # Reporting targets
        self.suite.set_baseline("generate_pdf_report", 5000)  # 5 seconds
        self.suite.set_baseline("generate_xlsx_report", 3000)  # 3 seconds

    def add_scan_benchmark(
        self,
        name: str,
        scan_func: Callable,
        *args,
        **kwargs
    ) -> BenchmarkResult:
        """Add scan execution benchmark."""
        return self.suite.benchmark_function(
            scan_func,
            *args,
            name=name,
            **kwargs
        )

    def add_api_benchmark(
        self,
        name: str,
        api_func: Callable,
        *args,
        **kwargs
    ) -> BenchmarkResult:
        """Add API endpoint benchmark."""
        return self.suite.benchmark_function(
            api_func,
            *args,
            name=name,
            **kwargs
        )

    def add_db_benchmark(
        self,
        name: str,
        query_func: Callable,
        *args,
        **kwargs
    ) -> BenchmarkResult:
        """Add database query benchmark."""
        return self.suite.benchmark_function(
            query_func,
            *args,
            name=name,
            **kwargs
        )

    def run_concurrent_api_tests(
        self,
        endpoint_func: Callable,
        num_requests: int = 10,
        name: str = "concurrent_api_calls"
    ) -> BenchmarkResult:
        """Benchmark concurrent API requests."""
        tasks = [
            ((f"request_{i}",), {})
            for i in range(num_requests)
        ]
        return self.suite.benchmark_concurrent(
            endpoint_func,
            tasks,
            name=name,
            max_workers=4
        )

    def compare_before_after(self, before_file: str, after_file: str):
        """Compare before/after benchmark results."""
        before_path = self.suite.output_dir / before_file
        after_path = self.suite.output_dir / after_file

        if not before_path.exists() or not after_path.exists():
            print("Benchmark files not found")
            return

        with open(before_path) as f:
            before = json.load(f)

        with open(after_path) as f:
            after = json.load(f)

        print("\n" + "=" * 80)
        print("PERFORMANCE COMPARISON: BEFORE vs AFTER")
        print("=" * 80)

        before_map = {b["name"]: b for b in before["benchmarks"]}
        after_map = {b["name"]: b for b in after["benchmarks"]}

        improvements = []
        regressions = []

        for name, after_bench in after_map.items():
            if name in before_map:
                before_bench = before_map[name]
                improvement = before_bench["duration_ms"] - after_bench["duration_ms"]
                percent = (improvement / before_bench["duration_ms"]) * 100

                print(f"\n{name}:")
                print(f"  Before: {before_bench['duration_ms']:.2f}ms")
                print(f"  After: {after_bench['duration_ms']:.2f}ms")
                print(f"  Change: {improvement:+.2f}ms ({percent:+.1f}%)")

                if improvement > 0:
                    improvements.append((name, improvement, percent))
                else:
                    regressions.append((name, improvement, percent))

        print("\n" + "-" * 80)
        print(f"\nImproved: {len(improvements)}")
        for name, imp, pct in sorted(improvements, key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {name}: {imp:.2f}ms ({pct:.1f}%)")

        if regressions:
            print(f"\nRegressions: {len(regressions)}")
            for name, imp, pct in sorted(regressions, key=lambda x: x[1]):
                print(f"  {name}: {imp:.2f}ms ({pct:.1f}%)")

        print("\n" + "=" * 80)

    def get_report(self) -> Dict[str, Any]:
        """Get full benchmark report."""
        return self.suite.get_summary()

    def save_report(self, filename: str = "benchmark_report.json"):
        """Save report to file."""
        return self.suite.save_report(filename)

    def print_report(self):
        """Print report to console."""
        return self.suite.print_report()


if __name__ == "__main__":
    # Example usage
    benchmarks = PerformanceBenchmarks()

    # Simulate some benchmarks
    def dummy_scan():
        time.sleep(0.1)

    def dummy_api():
        time.sleep(0.05)

    benchmarks.add_scan_benchmark("scan_sql_injection", dummy_scan)
    benchmarks.add_api_benchmark("api_get_findings", dummy_api)

    benchmarks.print_report()
    benchmarks.save_report()
