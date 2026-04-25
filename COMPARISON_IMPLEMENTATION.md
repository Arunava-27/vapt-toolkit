# UX-Comparison Module Implementation Guide

## Overview

The UX-Comparison module enables side-by-side comparison of vulnerability scans to identify changes between scan iterations. It automatically detects new vulnerabilities, fixed issues, unchanged findings, and regressions (vulnerabilities that reappeared).

**Key Features:**
- Compare any two scans from a project
- Identify new, fixed, unchanged, and regressed vulnerabilities
- Calculate risk delta and trend analysis
- Visual indicators (green=new, red=fixed, yellow=regressions, gray=unchanged)
- Filter by severity, finding type, and confidence score
- Download comparison reports as CSV
- Regression alerts for critical regressions

## Architecture

### Backend Components

#### `scanner/web/scan_comparison.py`

Core comparison logic with three main classes:

**ScanComparator**
- `compare_scans(scan_1, scan_2, filters)` - Main comparison method
  - Extracts findings from both scans
  - Categorizes findings by status
  - Calculates risk scores and deltas
  - Applies optional filtering
  - Returns: `ScanComparisonResult`

- `get_differences(scan_1, scan_2, filters)` - Convenience method
  - Returns: Dict with "new", "fixed", "unchanged", "modified" keys

- `detect_regressions(scan_history)` - Regression detection
  - Analyzes scan history to find vulnerabilities that were fixed but reappeared
  - Requires minimum 2 scans in history
  - Returns: List of regression findings

- `calculate_risk_delta(scan_1, scan_2)` - Risk analysis
  - Compares risk scores between scans
  - Calculates severity distribution deltas
  - Determines trend: "improving", "degrading", "stable"
  - Returns: Dict with detailed risk metrics

- `filter_findings(findings, filters)` - Flexible filtering
  - Supported filters:
    - `severity`: List of severity levels
    - `finding_types`: List of finding type names
    - `confidence_min`: Minimum confidence score (0-100)

**ComparisonFinding**
- Represents a single finding with comparison status
- Fields:
  - `finding_id`: Unique identifier
  - `finding_type`: Type of vulnerability
  - `severity`: Critical/High/Medium/Low/Info
  - `status`: NEW, FIXED, UNCHANGED, REGRESSION, MODIFIED
  - `confidence_score`: 0-100 score
  - `evidence`: Detection evidence/details
  - `appeared_in_scan`: Which scan this finding appears in

**ScanComparisonResult**
- Contains complete comparison between two scans
- Categorized findings by status
- Risk metrics and trend analysis
- Severity distributions for both scans
- Methods:
  - `to_dict()` - Convert to API response format

#### Risk Scoring

Risk scores are calculated as:
```
risk_score = Σ(severity_weight × confidence_coefficient)
```

Severity weights:
- Critical: 100
- High: 50
- Medium: 25
- Low: 5
- Info: 1

Confidence coefficient: confidence_score / 100

### API Endpoint

**POST /api/compare/scans**

Request body:
```json
{
  "scan_id_1": "string (scan ID to use as baseline)",
  "scan_id_2": "string (scan ID to compare against)",
  "severity_filter": ["Critical", "High"] (optional),
  "finding_types": ["SQL Injection", "XSS"] (optional),
  "confidence_min": 75 (optional, 0-100)
}
```

Response:
```json
{
  "scan_1_id": "string",
  "scan_2_id": "string",
  "comparison_timestamp": "ISO-8601 timestamp",
  "new_findings": [
    {
      "finding_id": "string",
      "finding_type": "SQL Injection",
      "severity": "Critical",
      "status": "new",
      "url": "http://example.com/login",
      "endpoint": "/login",
      "parameter": "username",
      "method": "POST",
      "payload": "admin' OR '1'='1",
      "confidence_score": 95,
      "evidence": "Time-based SQLi detected"
    }
  ],
  "fixed_findings": [...],
  "unchanged_findings": [...],
  "regressions": [...],
  "modified_findings": [...],
  "scan_1_risk_score": 150.5,
  "scan_2_risk_score": 165.0,
  "risk_delta": 14.5,
  "risk_trend": "degrading",
  "total_vulnerabilities_1": 5,
  "total_vulnerabilities_2": 6,
  "vulnerability_delta": 1,
  "severity_distribution_1": {
    "Critical": 1,
    "High": 2,
    "Medium": 1,
    "Low": 1,
    "Info": 0
  },
  "severity_distribution_2": {
    "Critical": 1,
    "High": 2,
    "Medium": 2,
    "Low": 1,
    "Info": 0
  }
}
```

Error responses:
- `404`: One or both scans not found
- `400`: Invalid request parameters

### Frontend Component

**ScanComparison.jsx**

Props:
- `scan1Id` (string): First scan ID
- `scan2Id` (string): Second scan ID
- `onClose` (function): Callback when closing comparison

Features:
- **Summary Cards**: Risk scores and delta
- **Vulnerability Summary**: Counts by status
- **Regression Alert**: Critical alert if regressions detected
- **Severity Distribution**: Side-by-side comparison
- **Tab Navigation**: Switch between finding categories
- **Filtering**: By severity level
- **Expandable Rows**: Click row to see details
- **Color Coding**:
  - Green (#dcfce7): New findings
  - Red (#fee2e2): Fixed findings
  - Yellow (#fef3c7): Regressions
  - Gray (#f3f4f6): Unchanged findings
- **CSV Export**: Download comparison report

## Usage Examples

### Python API

```python
from scanner.web.scan_comparison import ScanComparator
from database import get_project

# Get project with scan history
project = get_project(project_id)
scans = project["scans"]

# Compare last two scans
comparator = ScanComparator()
result = comparator.compare_scans(
    scans[-2],
    scans[-1],
    filters={
        "severity": ["Critical", "High"],
        "confidence_min": 80
    }
)

# Print summary
print(f"New findings: {len(result.new_findings)}")
print(f"Fixed findings: {len(result.fixed_findings)}")
print(f"Risk delta: {result.risk_delta:+.1f}")
print(f"Trend: {result.risk_trend}")

# Check for regressions
if result.regressions:
    print(f"WARNING: {len(result.regressions)} regressions detected!")
    for reg in result.regressions:
        print(f"  - {reg.finding_type} at {reg.url}")

# Get comparison data for API response
response_data = result.to_dict()
```

### REST API Usage

```bash
# Compare two scans
curl -X POST http://localhost:8000/api/compare/scans \
  -H "Content-Type: application/json" \
  -d '{
    "scan_id_1": "abc123def456",
    "scan_id_2": "xyz789uvw012",
    "severity_filter": ["Critical", "High"],
    "confidence_min": 80
  }'

# Response includes categorized findings and risk metrics
```

### Frontend Usage

```jsx
import ScanComparison from "./components/ScanComparison";

function ProjectDetail() {
  const [showComparison, setShowComparison] = useState(false);
  const [comparisonScans, setComparisonScans] = useState({});

  const handleCompare = (scan1Id, scan2Id) => {
    setComparisonScans({ scan1: scan1Id, scan2: scan2Id });
    setShowComparison(true);
  };

  return (
    <div>
      {showComparison && (
        <ScanComparison
          scan1Id={comparisonScans.scan1}
          scan2Id={comparisonScans.scan2}
          onClose={() => setShowComparison(false)}
        />
      )}
    </div>
  );
}
```

## Use Cases

### 1. Vulnerability Tracking

Track vulnerability fixes across scan iterations:
```python
project = get_project(project_id)
latest = project["scans"][-1]
previous = project["scans"][-2]

result = comparator.compare_scans(previous, latest)
print(f"Fixed: {len(result.fixed_findings)} vulnerabilities")
print(f"New: {len(result.new_findings)} vulnerabilities")
```

### 2. Regression Testing

Detect regressions in scan history:
```python
regressions = comparator.detect_regressions(project["scans"])
if regressions:
    alert_team(f"Found {len(regressions)} regressions!")
```

### 3. Baseline Comparison

Compare against initial baseline:
```python
baseline = project["scans"][0]
current = project["scans"][-1]

result = comparator.compare_scans(baseline, current)
print(f"Overall improvement: {-result.risk_delta:+.1f}")
```

### 4. Severity Filtering

Focus on critical issues only:
```python
result = comparator.compare_scans(
    scan_1,
    scan_2,
    filters={"severity": ["Critical"]}
)
```

### 5. Confidence-Based Analysis

High-confidence findings only:
```python
result = comparator.compare_scans(
    scan_1,
    scan_2,
    filters={"confidence_min": 85}
)
```

## Testing

Comprehensive test suite in `test_scan_comparison.py`:

```bash
python -m unittest test_scan_comparison -v
```

Test coverage includes:
- Basic comparison functionality
- New/fixed/unchanged finding detection
- Regression detection with scan history
- Risk score calculation
- Risk delta and trend analysis
- Severity distribution
- Filtering (severity, type, confidence)
- Edge cases (empty scans, same scan comparison)
- CVE finding integration
- Data serialization

**22 tests, all passing**

## Integration Points

### Database
- Scans stored as JSON in `projects.scans` array
- Each scan has `scan_id`, `config`, `results`, `timestamp`
- Comparison uses existing scan structure

### Confidence Scoring
- Integrates with `scanner.web.confidence_scorer`
- Uses confidence scores from findings
- Confidence influences risk calculations

### Evidence Collection
- Uses findings extracted by `scanner.web.evidence_collector`
- Standardized `WebVulnerabilityFinding` format
- Evidence used in comparison details

### Notifications (Optional)
- Can trigger alerts for regressions
- Can notify on risk degradation
- Severity thresholds configurable

## Performance Considerations

- **Finding Hashing**: Uses SHA256 hashing for finding comparison (16-char hash)
- **Memory**: Minimal overhead - findings stored as dictionaries
- **Time Complexity**: O(n) where n = total findings across both scans
- **Large Scans**: Tested with 100+ findings per scan

## Error Handling

The module gracefully handles:
- Missing fields in findings
- Empty scan results
- Incomplete scan data
- Non-existent scans (API returns 404)
- Null/None values

## Future Enhancements

1. **Temporal Analysis**: Track trends over multiple scans
2. **Automated Remediation Tracking**: Link to fix implementations
3. **False Positive Learning**: Reduce false positives in subsequent scans
4. **SLA Tracking**: Monitor time to fix by severity
5. **Export Formats**: JSON, PDF, HTML reports
6. **Webhook Integration**: Trigger actions on regression detection
7. **Machine Learning**: Predict future vulnerabilities based on patterns

## Troubleshooting

### Issue: Comparison shows 0 findings
**Solution**: Verify both scan IDs are valid and scans contain findings

### Issue: Risk delta not changing
**Solution**: Check confidence scores - delta may be within "stable" threshold (±5)

### Issue: Regression not detected
**Solution**: Ensure scan history has at least 3 scans (initial, fixed, regressed)

### Issue: Filtering returns no results
**Solution**: Verify filter values match actual finding data (severity levels, types)

## Code Quality

- **Type Hints**: Full type annotations throughout
- **Docstrings**: Comprehensive documentation
- **Error Handling**: Graceful degradation
- **Testing**: 22 unit tests with 100% pass rate
- **Code Style**: PEP 8 compliant
- **Performance**: O(n) complexity for large datasets
