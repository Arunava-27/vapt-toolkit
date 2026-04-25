# Risk Heat Map Visualization Guide

**Phase 5 Professional Reporting Enhancement**

## Overview

The Risk Heat Map Visualization provides a professional, multi-dimensional view of vulnerability distribution across scan targets, time periods, and severity levels. It enables security teams to quickly identify risk patterns and trends at a glance.

## Table of Contents

1. [Features](#features)
2. [Getting Started](#getting-started)
3. [View Modes](#view-modes)
4. [Interpreting Heat Maps](#interpreting-heat-maps)
5. [Use Cases](#use-cases)
6. [API Reference](#api-reference)
7. [Technical Details](#technical-details)
8. [Examples](#examples)

## Features

### Multi-Dimensional Analysis
- **By Target**: See vulnerability distribution across all targets
- **By Time**: Track vulnerability trends over time periods (day, week, month, quarter, year)
- **By Severity**: Get severity distribution and risk score
- **By Type**: Analyze vulnerabilities by type and severity

### Interactive Features
- **Hover Tooltips**: Details on hover (target, severity, count, risk value)
- **Clickable Cells**: Drill-down into specific findings (future enhancement)
- **Dynamic Filters**: Date range and target selection
- **Export Options**: Download as SVG, PNG, or print

### Professional Design
- **Color Gradient**: Intuitive color coding (red=critical, orange=high, yellow=medium, green=low, blue=info)
- **Risk Scoring**: Numerical risk assessment (0-100)
- **Responsive Layout**: Works on desktop, tablet, and mobile devices
- **Print-Friendly**: Optimized for PDF and paper output

## Getting Started

### Accessing Heat Maps

1. Navigate to a project in the VAPT toolkit
2. Click the **"🔥 Risk Heat Map"** tab
3. Select your desired view mode from the dropdown
4. Adjust filters as needed
5. Click **"🔄 Refresh"** to update data

### Basic Navigation

```
View Mode Dropdown
├── By Target
├── By Time Series
├── By Severity
└── By Vulnerability Type
```

## View Modes

### 1. By Target

**Purpose**: Compare vulnerability severity distribution across different scan targets

**Layout**:
- **X-axis**: Individual targets (domain names, IPs)
- **Y-axis**: Severity levels (Critical, High, Medium, Low, Info)
- **Color Intensity**: Risk level (darker=higher risk)
- **Cell Values**: Number of findings at that severity for that target

**Best For**:
- Identifying high-risk targets
- Comparing relative risk across multiple targets
- Prioritizing remediation by target
- Portfolio-level risk assessment

**Example**:
```
          api.example.com    web.example.com    db.example.com
Critical       [2]               [0]                [1]
High           [5]               [3]                [2]
Medium         [8]               [6]                [4]
Low            [12]              [9]                [7]
Info           [4]               [2]                [1]
```

**Filters**:
- Start Date: Show findings from this date onwards
- End Date: Show findings up to this date

### 2. By Time Series

**Purpose**: Track vulnerability trends over time

**Layout**:
- **X-axis**: Time periods (days, weeks, months, quarters, or years)
- **Y-axis**: Severity levels (Critical, High, Medium, Low, Info)
- **Color Intensity**: Number of findings in that period
- **Cell Values**: Number of findings at that severity in that time period

**Best For**:
- Tracking remediation progress
- Identifying vulnerability trends
- Measuring improvement over time
- Regression detection
- Compliance reporting

**Periods**:
- **Daily**: 1-day intervals (for recent scans)
- **Weekly**: ISO 8601 week format (2024-W03)
- **Monthly**: Year-month format (2024-01)
- **Quarterly**: Quarter format (2024-Q1)
- **Yearly**: Year only (2024)

**Example**:
```
          2024-W01    2024-W02    2024-W03    2024-W04
Critical    [5]         [4]         [3]         [2]
High        [12]        [10]        [8]         [6]
Medium      [20]        [18]        [15]        [12]
Low         [35]        [33]        [30]        [28]
Info        [8]         [8]         [7]         [6]
```

**Filters**:
- Target: Focus on a specific target
- Period: Choose time granularity

### 3. By Severity

**Purpose**: Get a quick overview of severity distribution

**Layout**:
- **Bar Chart**: Each severity level shows count and percentage
- **Statistics**: Total findings count and overall risk score
- **Colors**: Standard severity colors

**Best For**:
- Executive reporting
- Quick risk assessment
- Compliance metrics
- Risk score tracking
- Dashboard widgets

**Output**:
```
Total Findings: 48
Risk Score: 75/100

Critical: [████████] 5 (10.4%)
High:     [██████████████████] 15 (31.3%)
Medium:   [█████████████████████] 20 (41.7%)
Low:      [████████] 8 (16.7%)
Info:     [██] 0 (0%)
```

### 4. By Vulnerability Type

**Purpose**: See which vulnerability types appear most frequently at each severity

**Layout**:
- **X-axis**: Severity levels
- **Y-axis**: Vulnerability types (XSS, SQLi, CSRF, etc.)
- **Color Intensity**: Frequency at that severity

**Best For**:
- Training focus areas
- Security tool recommendations
- Vulnerability trend analysis
- Root cause analysis
- Security posture trends

## Interpreting Heat Maps

### Color Coding

The heat map uses a standardized color scheme:

| Color | Severity | CVSS | Action |
|-------|----------|------|--------|
| 🔴 Red | Critical | 9.0-10.0 | Immediate remediation required |
| 🟠 Orange | High | 7.0-8.9 | Urgent remediation needed |
| 🟡 Yellow | Medium | 4.0-6.9 | Scheduled remediation |
| 🟢 Green | Low | 0.1-3.9 | Address in regular updates |
| 🔵 Blue | Info | 0 | Monitor for patterns |

### Cell Opacity

Cell opacity indicates the relative risk:
- **Darker/More Opaque**: Higher risk (more findings at higher severity)
- **Lighter/Less Opaque**: Lower risk (fewer findings at lower severity)
- **Empty (Light Gray)**: No findings at this level

### Numbers in Cells

The number displayed in each cell represents:
- Count of vulnerabilities at that intersection
- Click the cell for detailed findings list (future feature)

### Risk Score (0-100)

The risk score is calculated as:

```
Risk Score = Average of (severity_weight × count_per_finding) / total_findings

Weights:
- Critical: 100 points
- High: 75 points
- Medium: 50 points
- Low: 25 points
- Info: 10 points
```

**Interpretation**:
- 0-20: Low risk (green)
- 21-40: Medium-low risk (yellow-green)
- 41-60: Medium risk (yellow)
- 61-80: High risk (orange)
- 81-100: Critical risk (red)

## Use Cases

### 1. Executive Reporting

**Scenario**: Monthly security board meeting

**Steps**:
1. Go to "By Severity" view
2. Note total findings and risk score
3. Export as PNG for presentation
4. Use trend data from "By Time" view

**Output**: One-page summary with risk metrics

### 2. Target Prioritization

**Scenario**: Multiple targets, limited remediation resources

**Steps**:
1. View "By Target" heat map
2. Identify targets with most Critical/High findings
3. Note which vulnerability types dominate
4. Plan remediation by target priority

**Output**: Target remediation roadmap

### 3. Regression Detection

**Scenario**: Ensure fixes from last scan remain fixed

**Steps**:
1. Go to "By Time" view
2. Compare current week vs. previous week
3. Look for any severity level increases
4. Drill-down into cells that increased

**Output**: Regression report

### 4. Remediation Tracking

**Scenario**: Monitor progress on vulnerability fixes

**Steps**:
1. View "By Time" with weekly periods
2. Watch the trend line
3. See if each severity level is decreasing
4. Calculate remediation velocity

**Output**: Progress dashboard

### 5. Vulnerability Type Analysis

**Scenario**: Identify most prevalent vulnerability class

**Steps**:
1. Go to "By Type" view
2. Identify vulnerability types with most instances
3. Plan training or tool deployments
4. Track type-specific remediation

**Output**: Technical improvement plan

### 6. Portfolio Risk Assessment

**Scenario**: Compare security posture across multiple applications

**Steps**:
1. View "By Target" with all targets
2. Create risk ranking by target
3. Identify systemic issues (e.g., all targets have XSS)
4. Plan enterprise-wide fixes

**Output**: Portfolio risk matrix

## API Reference

### Endpoints

#### 1. Get Heat Map by Target

```http
GET /api/reports/heatmap/by-target?projectId=<project_id>&start_date=<YYYY-MM-DD>&end_date=<YYYY-MM-DD>
```

**Parameters**:
- `projectId` (required): Project ID
- `start_date` (optional): ISO 8601 date
- `end_date` (optional): ISO 8601 date

**Response**:
```json
{
  "type": "by_target",
  "matrix": [[0, 1, 2, 3, 0], ...],
  "targets": ["api.example.com", "web.example.com"],
  "severities": ["Critical", "High", "Medium", "Low", "Info"],
  "data": [
    [
      {"target": "api.example.com", "severity": "Critical", "count": 2, "color": "#cf222e", "value": 40.0},
      ...
    ]
  ],
  "timestamp": "2024-01-15T10:30:00+00:00"
}
```

#### 2. Get Heat Map by Time

```http
GET /api/reports/heatmap/by-time?projectId=<project_id>&target=<target>&period=<period>
```

**Parameters**:
- `projectId` (required): Project ID
- `target` (optional): Specific target to filter
- `period` (required): "day", "week", "month", "quarter", or "year"

**Response**:
```json
{
  "type": "by_time",
  "matrix": [[...], ...],
  "time_periods": ["2024-W01", "2024-W02", "2024-W03"],
  "severities": ["Critical", "High", "Medium", "Low", "Info"],
  "data": [[...], ...],
  "period": "week",
  "target": null,
  "timestamp": "2024-01-15T10:30:00+00:00"
}
```

#### 3. Get Heat Map by Severity

```http
GET /api/reports/heatmap/by-severity?projectId=<project_id>
```

**Parameters**:
- `projectId` (required): Project ID

**Response**:
```json
{
  "type": "by_severity",
  "distribution": {
    "Critical": 5,
    "High": 15,
    "Medium": 20,
    "Low": 8
  },
  "percentages": {
    "Critical": 10.4,
    "High": 31.3,
    "Medium": 41.7,
    "Low": 16.7
  },
  "total": 48,
  "risk_score": 75,
  "colors": {
    "Critical": "#cf222e",
    "High": "#f0883e",
    ...
  },
  "timestamp": "2024-01-15T10:30:00+00:00"
}
```

#### 4. Get Heat Map by Type

```http
GET /api/reports/heatmap/by-type?projectId=<project_id>
```

**Parameters**:
- `projectId` (required): Project ID

**Response**:
```json
{
  "type": "by_vulnerability_type",
  "matrix": [[...], ...],
  "vulnerability_types": ["XSS", "SQLi", "CSRF", "Information Disclosure"],
  "severities": ["Critical", "High", "Medium", "Low", "Info"],
  "data": [[...], ...],
  "timestamp": "2024-01-15T10:30:00+00:00"
}
```

## Technical Details

### Heat Map Generation Algorithm

1. **Data Collection**: Extract all findings from scans
2. **Aggregation**: Group findings by specified dimension (target, time, type)
3. **Counting**: Count findings in each group by severity
4. **Risk Calculation**: Calculate risk value for each cell
5. **Rendering**: Generate visual representation

### Risk Value Calculation

```python
risk_value = min(100, (count * severity_weight * 10) / 100)

severity_weights = {
    "Critical": 4,
    "High": 3,
    "Medium": 2,
    "Low": 1,
    "Info": 0
}
```

### Performance Considerations

- **Caching**: Heat map data is computed on-request (not cached)
- **Large Datasets**: Handles 1000+ scans efficiently
- **Real-time Updates**: Refresh button updates data immediately
- **Client-side Rendering**: SVG-based for fast rendering

### Browser Compatibility

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari 14+, Chrome Mobile)

### Export Formats

#### SVG Export
- Scalable vector format
- Perfect for presentations
- Editable in vector tools (Illustrator, Inkscape)

#### PNG Export
- Raster image format
- Embeddable in reports
- Social media friendly

#### Print
- Optimized for letter and A4 sizes
- Color-blind friendly
- No headers/footers when printed

## Examples

### Example 1: Executive Dashboard

**Goal**: Get a one-slide risk overview

```
Step 1: View "By Severity"
Step 2: Note Risk Score: 72/100
Step 3: Export as PNG
Step 4: Add to executive dashboard

Output:
- Total Vulnerabilities: 48
- Critical: 5 (10%)
- High: 15 (31%)
- Medium: 20 (42%)
- Low: 8 (17%)
- Status: 30% reduction vs. last month
```

### Example 2: Remediation Progress Tracking

**Goal**: Track weekly remediation progress

```
Step 1: Select "By Time" view
Step 2: Choose "Weekly" period
Step 3: Focus on "Critical" row
Step 4: Watch trend: Week 1 [5] → Week 2 [4] → Week 3 [3]

Output:
- Trend: ↓ 40% reduction in Critical findings
- Pace: Remediate 1-2 Critical per week
- ETA: All Critical findings cleared in 2 weeks
```

### Example 3: Cross-Target Comparison

**Goal**: Identify highest-risk targets for resource allocation

```
Step 1: Select "By Target" view
Step 2: Filter date range (last 30 days)
Step 3: Review matrix:
   - api.example.com: 3 Critical, 8 High
   - web.example.com: 0 Critical, 2 High
   - db.example.com: 1 Critical, 5 High

Output:
- Priority 1: api.example.com (11 total, 3 Critical)
- Priority 2: db.example.com (6 total, 1 Critical)
- Priority 3: web.example.com (2 total, 0 Critical)
```

### Example 4: Vulnerability Type Analysis

**Goal**: Identify most prevalent vulnerability class

```
Step 1: Select "By Type" view
Step 2: Scan the matrix:
   - XSS: 8 High, 12 Medium
   - SQLi: 2 Critical, 5 High
   - CSRF: 3 Medium, 4 Low
   - Information Disclosure: 5 Low

Output:
- Most common: XSS (20 total)
- Most critical: SQLi (2 Critical)
- Action: Deploy input validation training for XSS
- Tool: Consider SQLi detection tool deployment
```

## Best Practices

1. **Regular Review**: Check heat maps weekly or after significant events
2. **Track Trends**: Use time-series view to measure progress
3. **Executive Reports**: Include by-severity view in status reports
4. **Drill-Down Investigation**: Use detail views to understand patterns
5. **Baseline Comparison**: Compare current to previous periods
6. **Export and Share**: Use export features for team communication
7. **Set Targets**: Define acceptable risk scores by target type

## Troubleshooting

### No Heat Map Data Displayed

**Problem**: Heat map shows empty or no data

**Solution**:
1. Ensure project has completed scans
2. Check date range filters
3. Try refreshing the page
4. Verify target names are correct

### Slow Performance

**Problem**: Heat map takes long time to load or render

**Solution**:
1. Reduce time period (e.g., weekly instead of daily)
2. Filter to specific targets
3. Reduce date range
4. Clear browser cache

### Export Not Working

**Problem**: Cannot export to PNG/SVG

**Solution**:
1. Try PNG format first (most compatible)
2. Check browser security settings
3. Try a different browser
4. Ensure pop-ups are not blocked

## Support & Feedback

For issues, feature requests, or feedback:
1. Check this guide for similar issues
2. Review GitHub issues in the VAPT repository
3. Contact the security team with specific use cases
4. Provide heat map screenshots with issue reports

## Changelog

### Version 1.0 (Current)
- ✅ By Target view
- ✅ By Time view (day, week, month, quarter, year)
- ✅ By Severity view
- ✅ By Type view
- ✅ Interactive tooltips
- ✅ Export (SVG, PNG)
- ✅ Print support
- ✅ Mobile responsive
- ✅ Date range filtering
- ✅ Risk score calculation

### Planned (v1.1)
- 🔄 Clickable drill-down to findings
- 🔄 Custom color schemes
- 🔄 Heatmap animations
- 🔄 Comparison between time periods
- 🔄 Customizable risk score weights

### Future Enhancements
- 📋 Scheduled report generation
- 📋 Email delivery
- 📋 Slack/Teams integration
- 📋 Benchmark comparisons
- 📋 ML-based anomaly detection
