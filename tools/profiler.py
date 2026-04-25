#!/usr/bin/env python3
"""Performance profiling module for VAPT toolkit.

Profiles:
- Web scanner modules (SQL injection, XSS, etc.)
- Reporting generators (PDF, XLSX, etc.)
- API endpoints (scan creation, findings retrieval)
- Database queries
"""

import time
import psutil
import os
import json
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass, asdict
import tracemalloc


@dataclass
class ProfileResult:
    """Result of a profiled operation."""
    name: str
    duration_ms: float
    memory_start_mb: float
    memory_end_mb: float
    memory_peak_mb: float
    memory_delta_mb: float
    call_count: int = 1
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class PerformanceProfiler:
    """Main profiling class."""

    def __init__(self, output_dir: str = "data/profiling"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[ProfileResult] = []
        self.process = psutil.Process(os.getpid())

    @contextmanager
    def profile(self, operation_name: str, enable_tracemalloc: bool = False):
        """Context manager for profiling an operation.

        Usage:
            with profiler.profile("scan_sql_injection"):
                # run operation
        """
        if enable_tracemalloc:
            tracemalloc.start()

        # Get initial state
        initial_memory = self.process.memory_info().rss / 1024 / 1024
        start_time = time.perf_counter()

        if enable_tracemalloc:
            tracemalloc.reset_peak()

        try:
            yield
        finally:
            # Get final state
            end_time = time.perf_counter()
            final_memory = self.process.memory_info().rss / 1024 / 1024

            duration_ms = (end_time - start_time) * 1000
            memory_delta = final_memory - initial_memory

            if enable_tracemalloc:
                current, peak = tracemalloc.get_traced_memory()
                peak_memory = peak / 1024 / 1024
                tracemalloc.stop()
            else:
                peak_memory = final_memory

            result = ProfileResult(
                name=operation_name,
                duration_ms=duration_ms,
                memory_start_mb=initial_memory,
                memory_end_mb=final_memory,
                memory_peak_mb=peak_memory,
                memory_delta_mb=memory_delta,
            )
            self.results.append(result)

    def profile_function(
        self,
        func: Callable,
        *args,
        operation_name: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Profile a function call."""
        name = operation_name or func.__name__
        with self.profile(name):
            return func(*args, **kwargs)

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics of profiling results."""
        if not self.results:
            return {}

        total_duration = sum(r.duration_ms for r in self.results)
        total_memory_delta = sum(r.memory_delta_mb for r in self.results)
        peak_memory = max(r.memory_peak_mb for r in self.results)

        by_operation = {}
        for result in self.results:
            if result.name not in by_operation:
                by_operation[result.name] = {
                    "count": 0,
                    "total_ms": 0,
                    "min_ms": float('inf'),
                    "max_ms": 0,
                    "avg_ms": 0,
                    "memory_delta_mb": 0,
                }

            op_stats = by_operation[result.name]
            op_stats["count"] += 1
            op_stats["total_ms"] += result.duration_ms
            op_stats["min_ms"] = min(op_stats["min_ms"], result.duration_ms)
            op_stats["max_ms"] = max(op_stats["max_ms"], result.duration_ms)
            op_stats["memory_delta_mb"] += result.memory_delta_mb

        for op_stats in by_operation.values():
            op_stats["avg_ms"] = op_stats["total_ms"] / op_stats["count"]

        return {
            "total_operations": len(self.results),
            "total_duration_ms": total_duration,
            "total_memory_delta_mb": total_memory_delta,
            "peak_memory_mb": peak_memory,
            "by_operation": by_operation,
            "timestamp": datetime.now().isoformat(),
        }

    def save_report(self, filename: str = "profile_report.json"):
        """Save profiling report to file."""
        report = {
            "summary": self.get_summary(),
            "results": [asdict(r) for r in self.results],
        }

        filepath = self.output_dir / filename
        with open(filepath, "w") as f:
            json.dump(report, f, indent=2)

        return filepath

    def print_report(self):
        """Print profiling report to console."""
        summary = self.get_summary()

        if not summary:
            print("No profiling data available")
            return

        print("\n" + "=" * 80)
        print("PERFORMANCE PROFILING REPORT")
        print("=" * 80)

        print(f"\nTimestamp: {summary['timestamp']}")
        print(f"Total Operations: {summary['total_operations']}")
        print(f"Total Duration: {summary['total_duration_ms']:.2f}ms")
        print(f"Total Memory Delta: {summary['total_memory_delta_mb']:.2f}MB")
        print(f"Peak Memory: {summary['peak_memory_mb']:.2f}MB")

        print("\n" + "-" * 80)
        print("BY OPERATION:")
        print("-" * 80)

        for op_name, stats in sorted(summary["by_operation"].items()):
            print(f"\n{op_name}:")
            print(f"  Count:        {stats['count']}")
            print(f"  Total:        {stats['total_ms']:.2f}ms")
            print(f"  Average:      {stats['avg_ms']:.2f}ms")
            print(f"  Min:          {stats['min_ms']:.2f}ms")
            print(f"  Max:          {stats['max_ms']:.2f}ms")
            print(f"  Memory Delta: {stats['memory_delta_mb']:.2f}MB")

        print("\n" + "=" * 80)


class DatabaseProfiler:
    """Profile database queries."""

    def __init__(self, db_conn):
        self.db_conn = db_conn
        self.queries: List[Dict[str, Any]] = []

    def profile_query(self, query: str, params: tuple = ()):
        """Profile a single database query."""
        start = time.perf_counter()
        try:
            cursor = self.db_conn.execute(query, params)
            result = cursor.fetchall()
            duration_ms = (time.perf_counter() - start) * 1000

            self.queries.append({
                "query": query,
                "params": params,
                "duration_ms": duration_ms,
                "row_count": len(result) if result else 0,
                "timestamp": datetime.now().isoformat(),
            })
            return result
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            self.queries.append({
                "query": query,
                "params": params,
                "duration_ms": duration_ms,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            })
            raise

    def get_slow_queries(self, threshold_ms: float = 100) -> List[Dict[str, Any]]:
        """Get queries slower than threshold."""
        return [q for q in self.queries if q.get("duration_ms", 0) > threshold_ms]

    def get_summary(self) -> Dict[str, Any]:
        """Get query profiling summary."""
        if not self.queries:
            return {}

        total_time = sum(q.get("duration_ms", 0) for q in self.queries)
        avg_time = total_time / len(self.queries) if self.queries else 0

        return {
            "total_queries": len(self.queries),
            "total_time_ms": total_time,
            "average_time_ms": avg_time,
            "min_time_ms": min(q.get("duration_ms", 0) for q in self.queries),
            "max_time_ms": max(q.get("duration_ms", 0) for q in self.queries),
            "slow_queries": self.get_slow_queries(),
        }

    def print_report(self):
        """Print database profiling report."""
        summary = self.get_summary()

        if not summary:
            print("No database profiling data")
            return

        print("\n" + "=" * 80)
        print("DATABASE PROFILING REPORT")
        print("=" * 80)
        print(f"\nTotal Queries: {summary['total_queries']}")
        print(f"Total Time: {summary['total_time_ms']:.2f}ms")
        print(f"Average Time: {summary['average_time_ms']:.2f}ms")
        print(f"Min Time: {summary['min_time_ms']:.2f}ms")
        print(f"Max Time: {summary['max_time_ms']:.2f}ms")

        slow = summary.get("slow_queries", [])
        if slow:
            print(f"\nSlow Queries (>100ms): {len(slow)}")
            for i, q in enumerate(slow[:10], 1):
                print(f"\n  {i}. {q['query'][:60]}...")
                print(f"     Duration: {q['duration_ms']:.2f}ms")
                if q.get("row_count"):
                    print(f"     Rows: {q['row_count']}")

        print("\n" + "=" * 80)


def get_profiler(output_dir: str = "data/profiling") -> PerformanceProfiler:
    """Factory function for getting a profiler instance."""
    return PerformanceProfiler(output_dir)


def get_db_profiler(db_conn):
    """Factory function for getting a database profiler instance."""
    return DatabaseProfiler(db_conn)


if __name__ == "__main__":
    # Example usage
    profiler = get_profiler()

    # Simulate some operations
    with profiler.profile("sample_operation_1"):
        time.sleep(0.1)

    with profiler.profile("sample_operation_2", enable_tracemalloc=True):
        data = [i for i in range(1000000)]
        time.sleep(0.05)

    with profiler.profile("sample_operation_1"):
        time.sleep(0.08)

    profiler.print_report()
    profiler.save_report()
