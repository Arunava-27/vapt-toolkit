# Enhanced Data Exports Guide - Phase 5

## Overview

The Enhanced Data Exports feature provides comprehensive export functionality for scan results in multiple professional formats. Export your vulnerability findings with full control over metadata, evidence inclusion, and filtering.

## Supported Formats

### 1. JSON Export
**Best for:** Data analysis, integration, long-term archival, programmatic processing

- **Format**: Pretty-printed JSON with full details
- **Features**:
  - Complete finding details with all metadata
  - Nested structure for complex data relationships
  - Perfect for APIs and automated systems
  - Includes severity and confidence scoring
  - OWASP and CWE mappings
- **File Extension**: `.json`
- **Use Cases**:
  - Integration with SIEM systems
  - Custom report generation
  - Data warehouse ingestion
  - Programmatic analysis

**Sample Output Structure:**
```json
{
  "format": "json",
  "export_date": "2024-01-15T10:30:00",
  "metadata": {
    "scan_date": "2024-01-15T09:30:00",
    "target": "https://example.com",
    "scan_type": "active",
    "total_findings": 15,
    "findings_by_severity": {
      "critical": 2,
      "high": 5,
      "medium": 8,
      "low": 0
    }
  },
  "findings": [
    {
      "type": "web_vulnerability",
      "title": "SQL Injection in Login",
      "severity": "critical",
      "confidence": "high",
      "location": "/admin/login",
      "description": "SQL injection vulnerability found...",
      "remediation": "Use parameterized queries",
      "cwe_id": 89,
      "owasp": "A03:2021 - Injection"
    }
  ],
  "summary": {
    "total": 15,
    "by_type": {"web_vulnerability": 10, "cve": 3, "open_port": 2},
    "by_severity": {"critical": 2, "high": 5, "medium": 8, "low": 0}
  }
}
```

### 2. CSV Export
**Best for:** Spreadsheet applications, data import/export, quick analysis

- **Format**: Comma-separated values with headers
- **Features**:
  - Spreadsheet-compatible grid format
  - Automatic metadata comments at top
  - Easy to import to Excel, Google Sheets, etc.
  - All findings in flat structure
  - Includes metadata as header comments
- **File Extension**: `.csv`
- **Use Cases**:
  - Bulk imports to spreadsheet applications
  - Data analysis in Excel/Sheets
  - Report generation in other tools
  - Stakeholder distribution

**Columns:**
```
Type, Title, Severity, Confidence, Location, Description, Remediation, CWE ID, OWASP
```

### 3. HTML Export
**Best for:** Email distribution, web viewing, standalone reports, interactive presentation

- **Format**: Self-contained HTML5 with inline CSS
- **Features**:
  - Professional styling with responsive design
  - Color-coded severity levels
  - Interactive finding cards
  - Summary statistics
  - Code block formatting for evidence
  - No external dependencies
  - Mobile-responsive design
- **File Extension**: `.html`
- **Use Cases**:
  - Email reports to stakeholders
  - Web-based review
  - Print-friendly reports
  - Client presentations

**Design Elements:**
- Header with gradient background
- Severity summary with color coding
- Finding cards with collapsible details
- Evidence display in formatted code blocks
- Professional typography and spacing

### 4. Excel Export
**Best for:** Professional reports, executive summaries, data analysis

- **Format**: Multi-sheet Excel workbook with formatting
- **Features**:
  - **Summary Sheet**: Overview, statistics, key metrics
  - **Findings Sheet**: Detailed grid with all findings
  - **Evidence Sheet**: Screenshots and technical evidence
  - **Timeline Sheet**: Findings in discovery order
  - **Statistics Sheet**: Analysis by severity, type, confidence
  - Professional formatting with colors
  - Frozen header rows
  - Auto-sized columns
- **File Extension**: `.xlsx`
- **Sheets Included**:
  1. **Summary**: Project info, scan metadata, severity distribution
  2. **Findings**: Complete findings table with all details
  3. **Evidence**: Evidence and logs for findings
  4. **Timeline**: Chronological view of findings
  5. **Statistics**: Analysis and distribution charts
- **Use Cases**:
  - Executive presentations
  - Formal compliance reports
  - Data analysis and pivot tables
  - Professional client delivery

**Formatting:**
- Color-coded severity levels (Red=Critical, Orange=High, Yellow=Medium, Green=Low)
- Professional header styling
- Automatic column width adjustment
- Text wrapping for descriptions
- Links to CWE definitions

### 5. Markdown Export
**Best for:** GitHub, documentation, version control

- **Format**: GitHub-flavored Markdown
- **Features**:
  - GitHub-ready format
  - Table formatting for findings
  - Code blocks for evidence
  - Severity badges
  - OWASP and CWE references
  - Perfect for wikis and documentation
  - CI/CD pipeline friendly
- **File Extension**: `.md`
- **Use Cases**:
  - GitHub repository integration
  - Project wikis and documentation
  - Version-controlled reports
  - CI/CD pipeline reports
  - Knowledge base entries

**Structure:**
- Main title and description
- Scan information section
- Severity summary table
- Individual findings with full details
- References section for each finding

### 6. SARIF Export
**Best for:** GitHub Security, CI/CD integration, automated scanning

- **Format**: SARIF v2.1.0 (Static Analysis Results Format)
- **Features**:
  - GitHub Security Alerts compatible
  - Standardized security format
  - Tool information and run details
  - Integration with GitHub Actions
  - CI/CD pipeline friendly
  - Rule-based result format
- **File Extension**: `.sarif.json`
- **Use Cases**:
  - GitHub Security tab integration
  - GitHub Code Scanning
  - CI/CD workflow integration
  - Enterprise security tools
  - Standards-based reporting

## Export Options

### Metadata
Include scan metadata in the export:
- Scan date and time
- Target URL/IP
- Scan type (active/passive/hybrid)
- Scan duration
- Modules used
- Total findings count
- Findings distribution by severity

### Evidence
Include detailed evidence for findings:
- Technical evidence (payloads, logs, responses)
- Screenshots or captures
- Proof-of-concept demonstrations
- Raw HTTP responses
- Code snippets

### Filtering

#### Severity Levels
- **Critical**: Immediate exploitation likely
- **High**: Easy exploitation possible
- **Medium**: Exploitation possible with effort
- **Low**: Exploitation unlikely or requires specific conditions
- **Info**: Informational only

#### Confidence Levels
- **High**: Finding is definitely present
- **Medium**: Finding is likely present
- **Low**: Finding may be present

#### Finding Types
- web_vulnerability
- cve
- open_port

## API Endpoints

### Get Export Templates
```
GET /api/exports/templates
```
Returns list of available export formats and their descriptions.

**Response:**
```json
{
  "templates": [
    {
      "format": "json",
      "name": "JSON",
      "description": "Pretty JSON with full details and metadata",
      "use_case": "Data analysis, integration, archival"
    },
    ...
  ]
}
```

### Export Single Scan
```
GET /api/exports/scan/{project_id}?format=json&include_metadata=true&include_evidence=true&severity=&confidence=
```

**Parameters:**
- `format` (required): json, csv, html, xlsx, markdown, sarif
- `include_metadata` (optional): true/false (default: true)
- `include_evidence` (optional): true/false (default: true)
- `severity` (optional): critical, high, medium, low (default: all)
- `confidence` (optional): high, medium, low (default: all)

**Response:** Export file with appropriate content-type and disposition headers

### Export Multiple Scans
```
POST /api/exports/bulk
Content-Type: application/json

{
  "project_ids": ["pid1", "pid2", "pid3"],
  "format": "json",
  "include_metadata": true
}
```

**Response:**
```json
{
  "format": "json",
  "count": 3,
  "exports": [
    {
      "project_id": "pid1",
      "target": "example.com",
      "data": {...}
    }
  ]
}
```

## Frontend Usage

### Using ExportDialog Component

```jsx
import ExportDialog from '@/components/ExportDialog';

export default function ProjectPage() {
  const [showExport, setShowExport] = useState(false);

  return (
    <>
      <button onClick={() => setShowExport(true)}>
        Export Results
      </button>
      
      {showExport && (
        <ExportDialog
          projectId={projectId}
          projectName={projectName}
          onClose={() => setShowExport(false)}
        />
      )}
    </>
  );
}
```

### Export Dialog Features

1. **Format Selection**: Radio buttons for each format
2. **Options**:
   - Include Metadata checkbox
   - Include Evidence checkbox
3. **Filtering**:
   - Severity level dropdown
   - Confidence level dropdown
4. **Actions**:
   - Download button
   - Cancel button

## Command-Line Usage

### Using Export Generator Directly

```python
from scanner.reporters.export_generator import ExportGenerator, ExportFormat

# Load scan data
scan_data = {
    "config": config_dict,
    "results": results_dict,
    "timestamp": "2024-01-15T10:00:00"
}

# Create exporter
exporter = ExportGenerator(scan_data)

# Export to JSON
json_export = exporter.export_json(
    include_metadata=True,
    include_evidence=True,
    severity="critical"
)

# Export to HTML
html_export = exporter.export_html()

# Export to Excel
xlsx_bytes = exporter.export_xlsx()

# Save to file
with open("report.html", "w") as f:
    f.write(html_export)

with open("report.xlsx", "wb") as f:
    f.write(xlsx_bytes)
```

## Data Mappings

### OWASP Top 10 Mapping
The export system automatically maps findings to OWASP Top 10 2021 categories:

| Finding Type | OWASP Category |
|---|---|
| SQLi | A03:2021 - Injection |
| XSS | A07:2021 - Cross-Site Scripting |
| CSRF | A01:2021 - Broken Access Control |
| Authentication Issues | A07:2021 - Identification and Authentication Failures |
| Cryptography Issues | A02:2021 - Cryptographic Failures |
| Insecure Configuration | A05:2021 - Security Misconfiguration |

### CWE Mapping
Common findings are mapped to relevant CWE IDs:

| Finding Type | CWE ID |
|---|---|
| SQL Injection | 89 |
| XSS | 79 |
| CSRF | 352 |
| XXE | 611 |
| Authentication Bypass | 287 |
| Broken Access Control | 284 |
| Cryptographic Failure | 327 |

## Best Practices

### For Executive Reports
1. Use **Excel export** for professional appearance
2. Enable **metadata** for context
3. Filter to **High and Critical** severity only
4. Include **executive summary**

### For Developer Fixes
1. Use **JSON or CSV** export for tool integration
2. Include full **evidence** for reproduction
3. Export **all findings** for complete picture
4. Export as **Markdown** for documentation

### For Compliance Documentation
1. Use **HTML export** for archival
2. Enable full **metadata** and **evidence**
3. Export **all findings** for completeness
4. Include **scan parameters** for reproducibility

### For Integration with Tools
1. Use **JSON export** for programmatic processing
2. Use **SARIF export** for GitHub integration
3. Use **CSV export** for data warehouse ingestion
4. Disable metadata for cleaner data

## Performance Considerations

- **JSON export**: Fast, minimal memory overhead
- **CSV export**: Very fast, flat structure
- **HTML export**: Fast, can be large for many findings
- **Markdown export**: Fast, optimized for readability
- **Excel export**: Moderate overhead for formatting
- **SARIF export**: Medium-sized files with complete metadata

## Security Considerations

- Exports are not encrypted; use secure transmission
- Exported files may contain sensitive vulnerability data
- Implement access controls on exported files
- Consider PII in evidence (URLs, user data, etc.)
- Implement audit logging for bulk exports

## Troubleshooting

### Export fails with "Format not supported"
- Verify format parameter is one of: json, csv, html, xlsx, markdown, sarif

### Excel file corrupted
- Ensure openpyxl is installed: `pip install openpyxl`
- Try reducing evidence data size

### HTML too large
- Disable evidence inclusion
- Filter to specific severity levels
- Export fewer findings

### JSON parsing errors
- Ensure valid scan data is provided
- Check for special characters in finding descriptions

## Examples

### Export Critical Findings as JSON
```bash
curl "http://localhost:8000/api/exports/scan/project-123?format=json&severity=critical"
```

### Export Medium+ Findings as HTML
```bash
curl "http://localhost:8000/api/exports/scan/project-123?format=html&severity=medium" \
  -o report.html
```

### Export All Findings to Excel
```bash
curl "http://localhost:8000/api/exports/scan/project-123?format=xlsx" \
  -o report.xlsx
```

### Export to GitHub SARIF Format
```bash
curl "http://localhost:8000/api/exports/scan/project-123?format=sarif" \
  -o results.sarif.json
```

## Support and Issues

For issues or feature requests related to exports:
1. Check that all required dependencies are installed
2. Verify project contains completed scans
3. Review API endpoint documentation
4. Check application logs for detailed error messages

## Changelog

### Version 1.0.0 (Phase 5)
- Initial release of enhanced export functionality
- Support for 6 export formats
- Excel workbook generation
- Professional HTML reports
- SARIF 2.1.0 compliance
- Full filtering capabilities
- Metadata inclusion options
- Evidence handling
- OWASP and CWE mappings
