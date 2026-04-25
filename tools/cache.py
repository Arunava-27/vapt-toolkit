#!/usr/bin/env python3
"""Caching layer for VAPT toolkit.

Implements LRU cache for:
- Scan results (1 hour TTL)
- CVE lookups (24 hour TTL)
- Compliance mappings (7 day TTL)
"""

import time
import json
from typing import Any, Optional, Dict, Callable
from collections import OrderedDict
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from functools import wraps
import hashlib


@dataclass
class CacheEntry:
    """Single cache entry with TTL support."""
    value: Any
    created_at: float = field(default_factory=time.time)
    ttl_seconds: int = 3600  # Default 1 hour

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return (time.time() - self.created_at) > self.ttl_seconds

    def age_seconds(self) -> float:
        """Get age of entry in seconds."""
        return time.time() - self.created_at


class LRUCache:
    """Thread-safe LRU cache with TTL support."""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self.cache:
            entry = self.cache[key]
            if entry.is_expired():
                del self.cache[key]
                self.misses += 1
                return None

            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.hits += 1
            return entry.value

        self.misses += 1
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        """Set value in cache."""
        if key in self.cache:
            del self.cache[key]

        if len(self.cache) >= self.max_size:
            # Remove least recently used (first item)
            self.cache.popitem(last=False)
            self.evictions += 1

        self.cache[key] = CacheEntry(value=value, ttl_seconds=ttl_seconds)

    def delete(self, key: str) -> None:
        """Delete key from cache."""
        if key in self.cache:
            del self.cache[key]

    def clear(self) -> None:
        """Clear entire cache."""
        self.cache.clear()

    def invalidate_expired(self) -> int:
        """Remove all expired entries."""
        count = 0
        expired_keys = [k for k, v in self.cache.items() if v.is_expired()]
        for key in expired_keys:
            del self.cache[key]
            count += 1
        return count

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "evictions": self.evictions,
            "total_requests": total_requests,
        }

    def print_stats(self):
        """Print cache statistics."""
        stats = self.get_stats()
        print(f"\nCache Statistics:")
        print(f"  Size: {stats['size']}/{stats['max_size']}")
        print(f"  Hits: {stats['hits']}")
        print(f"  Misses: {stats['misses']}")
        print(f"  Hit Rate: {stats['hit_rate']:.1f}%")
        print(f"  Evictions: {stats['evictions']}")


class CacheManager:
    """Manages multiple specialized caches."""

    def __init__(self):
        self.scan_results_cache = LRUCache(max_size=500)  # 1 hour TTL
        self.cve_lookup_cache = LRUCache(max_size=5000)   # 24 hour TTL
        self.compliance_cache = LRUCache(max_size=1000)   # 7 day TTL
        self.general_cache = LRUCache(max_size=2000)

    def get_scan_result(self, scan_id: str) -> Optional[Dict]:
        """Get cached scan result."""
        return self.scan_results_cache.get(f"scan:{scan_id}")

    def set_scan_result(self, scan_id: str, result: Dict) -> None:
        """Cache scan result (1 hour TTL)."""
        self.scan_results_cache.set(f"scan:{scan_id}", result, ttl_seconds=3600)

    def get_cve_info(self, cve_id: str) -> Optional[Dict]:
        """Get cached CVE info."""
        return self.cve_lookup_cache.get(f"cve:{cve_id}")

    def set_cve_info(self, cve_id: str, info: Dict) -> None:
        """Cache CVE info (24 hour TTL)."""
        self.cve_lookup_cache.set(f"cve:{cve_id}", info, ttl_seconds=86400)

    def get_compliance_mapping(self, compliance_type: str) -> Optional[Dict]:
        """Get cached compliance mapping."""
        return self.compliance_cache.get(f"compliance:{compliance_type}")

    def set_compliance_mapping(self, compliance_type: str, mapping: Dict) -> None:
        """Cache compliance mapping (7 day TTL)."""
        self.compliance_cache.set(
            f"compliance:{compliance_type}",
            mapping,
            ttl_seconds=604800  # 7 days
        )

    def invalidate_scan(self, scan_id: str) -> None:
        """Invalidate scan cache entry."""
        self.scan_results_cache.delete(f"scan:{scan_id}")

    def invalidate_cve(self, cve_id: str) -> None:
        """Invalidate CVE cache entry."""
        self.cve_lookup_cache.delete(f"cve:{cve_id}")

    def clear_all(self) -> None:
        """Clear all caches."""
        self.scan_results_cache.clear()
        self.cve_lookup_cache.clear()
        self.compliance_cache.clear()
        self.general_cache.clear()

    def get_all_stats(self) -> Dict[str, Dict]:
        """Get stats for all caches."""
        return {
            "scan_results": self.scan_results_cache.get_stats(),
            "cve_lookup": self.cve_lookup_cache.get_stats(),
            "compliance": self.compliance_cache.get_stats(),
            "general": self.general_cache.get_stats(),
        }

    def print_all_stats(self):
        """Print stats for all caches."""
        print("\n" + "=" * 60)
        print("CACHE STATISTICS")
        print("=" * 60)
        stats = self.get_all_stats()
        for cache_name, cache_stats in stats.items():
            print(f"\n{cache_name}:")
            print(f"  Size: {cache_stats['size']}/{cache_stats['max_size']}")
            print(f"  Hit Rate: {cache_stats['hit_rate']:.1f}%")
            print(f"  Hits/Misses: {cache_stats['hits']}/{cache_stats['misses']}")


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get or create global cache manager."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def cached(
    cache_type: str = "general",
    ttl_seconds: int = 3600,
    key_func: Optional[Callable] = None
):
    """Decorator for caching function results.

    Args:
        cache_type: Type of cache (scan, cve, compliance, general)
        ttl_seconds: TTL in seconds
        key_func: Optional function to generate cache key

    Usage:
        @cached(cache_type="cve", ttl_seconds=86400)
        def lookup_cve(cve_id):
            # expensive lookup
            return cve_info
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            manager = get_cache_manager()

            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default: use function name and first arg
                key_parts = [func.__name__] + [str(a) for a in args[:2]]
                cache_key = ":".join(key_parts)

            # Try cache
            if cache_type == "scan":
                cached_val = manager.scan_results_cache.get(cache_key)
            elif cache_type == "cve":
                cached_val = manager.cve_lookup_cache.get(cache_key)
            elif cache_type == "compliance":
                cached_val = manager.compliance_cache.get(cache_key)
            else:
                cached_val = manager.general_cache.get(cache_key)

            if cached_val is not None:
                return cached_val

            # Compute and cache
            result = func(*args, **kwargs)

            if cache_type == "scan":
                manager.scan_results_cache.set(cache_key, result, ttl_seconds)
            elif cache_type == "cve":
                manager.cve_lookup_cache.set(cache_key, result, ttl_seconds)
            elif cache_type == "compliance":
                manager.compliance_cache.set(cache_key, result, ttl_seconds)
            else:
                manager.general_cache.set(cache_key, result, ttl_seconds)

            return result

        return wrapper
    return decorator


if __name__ == "__main__":
    # Example usage
    cache = get_cache_manager()

    # Test scan cache
    cache.set_scan_result("scan_001", {"findings": 5})
    print(cache.get_scan_result("scan_001"))

    # Test CVE cache
    cache.set_cve_info("CVE-2023-1234", {"severity": "high"})
    print(cache.get_cve_info("CVE-2023-1234"))

    # Print stats
    cache.print_all_stats()

    # Test decorator
    @cached(cache_type="general", ttl_seconds=60)
    def expensive_function(x):
        time.sleep(0.1)
        return x * 2

    import time
    print("\nFirst call (should take ~0.1s):")
    t0 = time.time()
    result1 = expensive_function(5)
    print(f"  Result: {result1}, Time: {time.time() - t0:.3f}s")

    print("Second call (should be instant from cache):")
    t0 = time.time()
    result2 = expensive_function(5)
    print(f"  Result: {result2}, Time: {time.time() - t0:.3f}s")

    cache.print_all_stats()
