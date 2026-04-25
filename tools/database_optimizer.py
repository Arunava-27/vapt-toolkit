#!/usr/bin/env python3
"""Database optimization module for VAPT toolkit.

Features:
- Index management
- Query optimization
- Connection pooling
- Query monitoring
"""

import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from contextlib import contextmanager
from dataclasses import dataclass
import json


@dataclass
class IndexInfo:
    """Information about a database index."""
    name: str
    table: str
    columns: List[str]
    unique: bool = False
    created_at: str = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


class DatabaseOptimizer:
    """Database optimization utilities."""

    # Recommended indexes for VAPT schema
    RECOMMENDED_INDEXES = [
        # Findings table
        IndexInfo("idx_findings_severity", "findings", ["severity"]),
        IndexInfo("idx_findings_scan_id", "findings", ["scan_id"]),
        IndexInfo("idx_findings_type", "findings", ["type"]),
        IndexInfo("idx_findings_status", "findings", ["status"]),

        # Scans table
        IndexInfo("idx_scans_created_at", "scans", ["created_at"]),
        IndexInfo("idx_scans_target", "scans", ["target"]),
        IndexInfo("idx_scans_status", "scans", ["status"]),

        # Bulk jobs
        IndexInfo("idx_bulk_jobs_status", "bulk_jobs", ["status"]),
        IndexInfo("idx_bulk_jobs_created_at", "bulk_jobs", ["created_at"]),

        # Schedules
        IndexInfo("idx_schedules_enabled", "schedules", ["enabled"]),
    ]

    def __init__(self, db_path: str = "vapt.db"):
        self.db_path = Path(db_path)
        self.query_log: List[Dict[str, Any]] = []

    @contextmanager
    def get_connection(self):
        """Get database connection with optimizations."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row

        # Enable optimization settings
        conn.execute("PRAGMA journal_mode=WAL")  # Write-ahead logging
        conn.execute("PRAGMA synchronous=NORMAL")  # Balance safety/performance
        conn.execute("PRAGMA cache_size=10000")  # Increase cache
        conn.execute("PRAGMA temp_store=MEMORY")  # Use memory for temp
        conn.execute("PRAGMA query_only=FALSE")  # Allow writes

        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def create_indexes(self) -> List[str]:
        """Create all recommended indexes."""
        created = []

        with self.get_connection() as conn:
            cursor = conn.cursor()

            for idx in self.RECOMMENDED_INDEXES:
                # Check if index exists
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
                    (idx.name,)
                )
                if cursor.fetchone():
                    continue

                # Check if table exists
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (idx.table,)
                )
                if not cursor.fetchone():
                    continue

                # Create index
                columns_str = ", ".join(idx.columns)
                unique_str = "UNIQUE" if idx.unique else ""
                sql = f"CREATE {unique_str} INDEX IF NOT EXISTS {idx.name} ON {idx.table} ({columns_str})"

                try:
                    cursor.execute(sql)
                    created.append(idx.name)
                    print(f"[OK] Created index: {idx.name} on {idx.table}")
                except Exception as e:
                    print(f"[FAIL] Failed to create index {idx.name}: {e}")

        return created

    def get_existing_indexes(self) -> Dict[str, List[str]]:
        """Get all existing indexes."""
        indexes = {}

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
            )

            for name, table in cursor.fetchall():
                if table not in indexes:
                    indexes[table] = []
                indexes[table].append(name)

        return indexes

    def analyze_database(self) -> Dict[str, Any]:
        """Analyze database for optimization opportunities."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get table stats
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            table_stats = {}
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]

                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()

                table_stats[table] = {
                    "row_count": count,
                    "column_count": len(columns),
                    "columns": [col[1] for col in columns],
                }

            return {
                "timestamp": datetime.now().isoformat(),
                "tables": table_stats,
                "indexes": self.get_existing_indexes(),
            }

    def optimize_query(self, query: str) -> str:
        """Suggest query optimizations."""
        suggestions = []

        # Check for SELECT *
        if "SELECT *" in query.upper():
            suggestions.append("✗ Use specific columns instead of SELECT *")

        # Check for LIKE at start
        if "LIKE '%'" in query.upper():
            suggestions.append("✗ Leading wildcards prevent index usage")

        # Check for OR conditions
        if " OR " in query.upper():
            suggestions.append("⚠ OR conditions may not use indexes efficiently")

        # Check for DISTINCT
        if "DISTINCT" in query.upper():
            suggestions.append("⚠ DISTINCT is expensive, consider GROUP BY")

        return "\n  ".join(suggestions) if suggestions else "✓ Query looks optimized"

    def log_query(self, query: str, duration_ms: float, row_count: int = 0):
        """Log executed query for analysis."""
        self.query_log.append({
            "query": query[:100],
            "duration_ms": duration_ms,
            "row_count": row_count,
            "timestamp": datetime.now().isoformat(),
        })

    def get_slow_queries(self, threshold_ms: float = 100) -> List[Dict[str, Any]]:
        """Get queries slower than threshold."""
        return [q for q in self.query_log if q["duration_ms"] > threshold_ms]

    def get_database_size(self) -> Dict[str, float]:
        """Get database file sizes."""
        main_file = self.db_path
        wal_file = self.db_path.with_suffix(".db-wal")
        shm_file = self.db_path.with_suffix(".db-shm")

        return {
            "main_db_mb": main_file.stat().st_size / 1024 / 1024 if main_file.exists() else 0,
            "wal_mb": wal_file.stat().st_size / 1024 / 1024 if wal_file.exists() else 0,
            "shm_mb": shm_file.stat().st_size / 1024 / 1024 if shm_file.exists() else 0,
        }

    def vacuum(self) -> None:
        """Optimize database by vacuuming."""
        with self.get_connection() as conn:
            conn.execute("VACUUM")
        print("✓ Database vacuumed")

    def print_analysis(self):
        """Print database analysis."""
        analysis = self.analyze_database()

        print("\n" + "=" * 80)
        print("DATABASE ANALYSIS")
        print("=" * 80)
        print(f"\nTimestamp: {analysis['timestamp']}")

        print("\nTABLES:")
        for table, stats in analysis["tables"].items():
            print(f"\n  {table}:")
            print(f"    Rows: {stats['row_count']:,}")
            print(f"    Columns: {stats['column_count']}")

        print("\n\nINDEXES:")
        if analysis["indexes"]:
            for table, indexes in analysis["indexes"].items():
                print(f"\n  {table}:")
                for idx in indexes:
                    print(f"    - {idx}")
        else:
            print("\n  No indexes found!")

        print("\n\nTOTAL DATABASE SIZE:")
        sizes = self.get_database_size()
        for name, size in sizes.items():
            if size > 0:
                print(f"  {name}: {size:.2f}MB")

        print("\n" + "=" * 80)

    def print_recommendations(self):
        """Print optimization recommendations."""
        print("\n" + "=" * 80)
        print("DATABASE OPTIMIZATION RECOMMENDATIONS")
        print("=" * 80)

        existing = self.get_existing_indexes()
        print("\nMISSING RECOMMENDED INDEXES:")

        missing = []
        for idx in self.RECOMMENDED_INDEXES:
            if idx.table not in existing or idx.name not in existing.get(idx.table, []):
                missing.append(idx)
                print(f"  [MISSING] {idx.name} on {idx.table}({', '.join(idx.columns)})")

        if not missing:
            print("  [OK] All recommended indexes exist")

        print("\nOTHER RECOMMENDATIONS:")
        print("  1. Use parameterized queries to prevent SQL injection")
        print("  2. Batch multiple operations in transactions")
        print("  3. Use connection pooling for concurrent access")
        print("  4. Monitor slow queries (>100ms)")
        print("  5. Regularly vacuum database to reclaim space")
        print("  6. Use EXPLAIN QUERY PLAN to analyze queries")
        print("  7. Consider archiving old scan results")

        print("\n" + "=" * 80)


class QueryMonitor:
    """Monitor and optimize database queries."""

    def __init__(self, db_optimizer: DatabaseOptimizer):
        self.optimizer = db_optimizer
        self.query_stats: Dict[str, Dict[str, Any]] = {}

    def execute_monitored(self, connection, query: str, params: tuple = ()) -> Any:
        """Execute query with monitoring."""
        start = time.perf_counter()
        cursor = connection.execute(query, params)
        result = cursor.fetchall()
        duration_ms = (time.perf_counter() - start) * 1000

        # Normalize query for stats
        normalized = query.upper().split()[0:5]  # First few words
        query_key = " ".join(normalized)

        if query_key not in self.query_stats:
            self.query_stats[query_key] = {
                "count": 0,
                "total_ms": 0,
                "min_ms": float('inf'),
                "max_ms": 0,
                "examples": [],
            }

        stats = self.query_stats[query_key]
        stats["count"] += 1
        stats["total_ms"] += duration_ms
        stats["min_ms"] = min(stats["min_ms"], duration_ms)
        stats["max_ms"] = max(stats["max_ms"], duration_ms)

        if len(stats["examples"]) < 3:
            stats["examples"].append(query[:80])

        # Log if slow
        if duration_ms > 100:
            self.optimizer.log_query(query, duration_ms, len(result))

        return result

    def get_stats(self) -> Dict[str, Any]:
        """Get query statistics."""
        total_queries = sum(s["count"] for s in self.query_stats.values())
        total_time = sum(s["total_ms"] for s in self.query_stats.values())

        return {
            "total_queries": total_queries,
            "total_time_ms": total_time,
            "avg_query_ms": total_time / total_queries if total_queries > 0 else 0,
            "query_breakdown": self.query_stats,
        }

    def print_stats(self):
        """Print query statistics."""
        stats = self.get_stats()

        print("\n" + "=" * 80)
        print("QUERY STATISTICS")
        print("=" * 80)
        print(f"\nTotal Queries: {stats['total_queries']}")
        print(f"Total Time: {stats['total_time_ms']:.2f}ms")
        print(f"Average Query: {stats['avg_query_ms']:.2f}ms")

        print("\nTOP QUERIES:")
        sorted_queries = sorted(
            stats["query_breakdown"].items(),
            key=lambda x: x[1]["total_ms"],
            reverse=True
        )

        for query, query_stats in sorted_queries[:10]:
            print(f"\n  {query}:")
            print(f"    Count: {query_stats['count']}")
            print(f"    Total: {query_stats['total_ms']:.2f}ms")
            print(f"    Avg: {query_stats['total_ms']/query_stats['count']:.2f}ms")
            print(f"    Min/Max: {query_stats['min_ms']:.2f}ms / {query_stats['max_ms']:.2f}ms")

        print("\n" + "=" * 80)


def get_optimizer(db_path: str = "vapt.db") -> DatabaseOptimizer:
    """Factory function for database optimizer."""
    return DatabaseOptimizer(db_path)


if __name__ == "__main__":
    # Example usage
    optimizer = get_optimizer()

    print("Analyzing database...")
    optimizer.print_analysis()

    print("\n\nCreating recommended indexes...")
    created = optimizer.create_indexes()
    print(f"Created {len(created)} indexes")

    print("\n\nOptimization recommendations...")
    optimizer.print_recommendations()

    print("\n\nOptimizing database...")
    optimizer.vacuum()
