#!/usr/bin/env python3
"""Quick verification script for heat map generator."""

from scanner.reporters.heatmap_generator import HeatMapGenerator

# Instantiate generator
gen = HeatMapGenerator()
print("[OK] HeatMapGenerator successfully imported and instantiated")

# Test generate_by_severity
result = gen.generate_by_severity([
    {"severity": "High"},
    {"severity": "Medium"}
])
print(f"[OK] generate_by_severity works: Risk score={result['risk_score']}")

# Test generate_by_target
scans = [
    {
        "target": "example.com",
        "web_vulnerabilities": {"findings": [{"severity": "High"}]},
        "cve": {"correlations": []}
    }
]
result = gen.generate_by_target(scans)
print(f"[OK] generate_by_target works: Found {len(result['targets'])} target(s)")

# Test generate_by_time
result = gen.generate_by_time(scans, period="week")
print(f"[OK] generate_by_time works: Generated {len(result['time_periods'])} period(s)")

# Test generate_by_vulnerability_type
result = gen.generate_by_vulnerability_type(scans)
print(f"[OK] generate_by_vulnerability_type works: Found {len(result['vulnerability_types'])} type(s)")

print("\n[SUCCESS] All heat map generator tests passed!")

