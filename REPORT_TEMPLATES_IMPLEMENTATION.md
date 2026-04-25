# Report Templates Implementation Guide

## Overview
The Report Templates system provides a flexible, Jinja2-based template engine for generating custom VAPT reports with 5 pre-built templates.

## Key Features
- **Template Engine**: Jinja2 rendering with variable extraction
- **Pre-built Templates**: Executive, Technical, Compliance, Risk, and Remediation
- **Template Management**: Create, edit, delete, and list templates
- **Database Storage**: Optional persistent template storage
- **API Integration**: RESTful endpoints for template operations

## Quick Reference

### Creating a Custom Template
```python
from scanner.reporters.template_engine import TemplateEngine

engine = TemplateEngine()

# Create template
template_id = engine.create_template(
    name="Custom Report",
    html_content="<html><body>{{ scan.project_name }}</body></html>"
)
```

### Applying a Template
```python
# Render template with scan data
report_html = engine.apply_template(
    template_id=template_id,
    scan_data={
        'project_name': 'My Project',
        'target': 'example.com',
        'findings': [...],
        'timestamp': '2026-04-25T10:00:00'
    }
)
```

### API Endpoints

#### 1. Get Template Preview
```
POST /api/templates/report/apply
Content-Type: application/json

{
  "template_id": "uuid-here",
  "scan_id": "scan-uuid"
}

Response:
{
  "html": "...",
  "status": "success"
}
```

#### 2. List Templates
```
GET /api/templates/report
Query params:
  - project_id (optional)

Response:
{
  "templates": [
    {
      "id": "uuid",
      "name": "Executive Summary",
      "created_at": "2026-04-25T...",
      "last_used": "..."
    }
  ]
}
```

#### 3. Create Template
```
POST /api/templates/report/create
Content-Type: application/json

{
  "name": "Custom Report",
  "html_content": "...",
  "project_id": "optional-uuid"
}

Response:
{
  "template_id": "new-uuid",
  "status": "created"
}
```

## Pre-built Templates

### 1. Executive Summary
- **Purpose**: High-level overview for non-technical stakeholders
- **Includes**: Risk score, severity breakdown, key findings summary
- **Output**: HTML with visual severity indicators
- **File**: scanner/reporters/templates/executive.html

### 2. Technical Report
- **Purpose**: Detailed technical findings for security engineers
- **Includes**: CWE mappings, detailed vulnerability descriptions, metadata
- **Output**: HTML with technical tables and code snippets
- **File**: scanner/reporters/templates/technical.html

### 3. Compliance Report
- **Purpose**: Framework compliance assessment (OWASP, CWE)
- **Includes**: Pass/fail status by framework, violation counts
- **Output**: HTML with compliance matrices
- **File**: scanner/reporters/templates/compliance.html

### 4. Risk Analysis
- **Purpose**: Risk scoring and prioritization
- **Includes**: Risk gauge visualization, risk point calculation
- **Output**: HTML with risk visualization
- **File**: scanner/reporters/templates/risk.html

### 5. Remediation Plan
- **Purpose**: Actionable remediation roadmap
- **Includes**: Priority timeline, implementation steps, effort estimates
- **Output**: HTML with implementation timeline
- **File**: scanner/reporters/templates/remediation.html

## Database Schema

### report_templates
```sql
CREATE TABLE report_templates (
    id TEXT PRIMARY KEY,
    project_id TEXT,
    name TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT,
    last_used TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id)
)
```

### template_variables
```sql
CREATE TABLE template_variables (
    id TEXT PRIMARY KEY,
    template_id TEXT,
    variable_name TEXT,
    description TEXT,
    type TEXT,
    FOREIGN KEY (template_id) REFERENCES report_templates(id)
)
```

## Configuration

### Initialization
```python
from scanner.reporters.template_engine import TemplateEngine

# With database
engine = TemplateEngine(db_conn_factory=lambda: connection)

# Without database (in-memory)
engine = TemplateEngine()
```

### Environment Variables
```
TEMPLATES_DIR=scanner/reporters/templates
TEMPLATE_CACHE_SIZE=100
```

## Integration Points

### With Scan Results
```python
# After scan completes
scan_data = scan_results.to_dict()
report_html = engine.apply_template(template_id, scan_data)

# Save report
with open(f"reports/{scan_id}.html", "w") as f:
    f.write(report_html)
```

### With API Server
Templates are auto-integrated into FastAPI server via:
- `POST /api/templates/report/apply`
- `GET /api/templates/report`
- `POST /api/templates/report/create`

## Performance Notes
- Template rendering: <100ms for average scan
- Template cache: In-memory with optional DB backing
- Maximum template size: 10MB
- Variable extraction: Automatic regex-based parsing

## Troubleshooting

### Template Not Found
- Check template_id is correct
- Verify project_id matches (if using project-scoped templates)

### Rendering Errors
- Verify all required variables are in scan_data
- Check template syntax (valid Jinja2)
- Review error message for missing variables

### Variable Extraction Issues
- Use simple variable names (alphanumeric + underscore)
- Avoid complex expressions in template source

## Examples

### Simple Executive Report
```html
<!DOCTYPE html>
<html>
<head><title>Report</title></head>
<body>
    <h1>{{ scan.project_name }}</h1>
    <p>Target: {{ scan.target }}</p>
    <p>Date: {{ scan.timestamp }}</p>
    <p>Findings: {{ scan.total_findings }}</p>
</body>
</html>
```

### Advanced Technical Report
```html
<!DOCTYPE html>
<html>
<body>
    {% for finding in scan.findings %}
    <h3>{{ finding.title }}</h3>
    <p>CWE: {{ finding.cwe }}</p>
    <p>Severity: {{ finding.severity }}</p>
    {% endfor %}
</body>
</html>
```

## Testing

Run template tests:
```bash
pytest tests_template_engine.py -v
```

Validate template syntax:
```bash
python -c "from scanner.reporters.template_engine import TemplateEngine; TemplateEngine()"
```

## Status
✅ Feature Complete
- Template engine implemented
- 5 pre-built templates ready
- API endpoints integrated
- Database support optional
