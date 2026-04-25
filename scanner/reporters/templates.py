"""Pre-built HTML templates for VAPT reports."""

EXECUTIVE_SUMMARY_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Executive Summary Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; color: #333; }
        h1 { color: #1a1a1a; border-bottom: 3px solid #2196F3; padding-bottom: 10px; }
        h2 { color: #2196F3; margin-top: 20px; }
        .summary { background: #f5f5f5; padding: 15px; border-left: 4px solid #2196F3; }
        .severity-high { color: #d32f2f; font-weight: bold; }
        .severity-medium { color: #f57c00; font-weight: bold; }
        .severity-low { color: #388e3c; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #2196F3; color: white; }
        .footer { margin-top: 40px; border-top: 1px solid #ddd; padding-top: 15px; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <h1>{{ report.title | default("Security Assessment Report") }}</h1>
    
    <div class="summary">
        <h2>Report Summary</h2>
        <p><strong>Project:</strong> {{ scan.project_name }}</p>
        <p><strong>Target:</strong> {{ scan.target }}</p>
        <p><strong>Report Date:</strong> {{ report_generated }}</p>
        <p><strong>Assessment Scope:</strong> {{ scan.scope | default("Full Network Assessment") }}</p>
    </div>
    
    <h2>Key Findings</h2>
    <table>
        <tr>
            <th>Finding Type</th>
            <th>Count</th>
            <th>Severity</th>
        </tr>
        <tr>
            <td>Critical Issues</td>
            <td>{{ severity_summary.critical }}</td>
            <td><span class="severity-high">CRITICAL</span></td>
        </tr>
        <tr>
            <td>High Issues</td>
            <td>{{ severity_summary.high }}</td>
            <td><span class="severity-high">HIGH</span></td>
        </tr>
        <tr>
            <td>Medium Issues</td>
            <td>{{ severity_summary.medium }}</td>
            <td><span class="severity-medium">MEDIUM</span></td>
        </tr>
        <tr>
            <td>Low Issues</td>
            <td>{{ severity_summary.low }}</td>
            <td><span class="severity-low">LOW</span></td>
        </tr>
    </table>
    
    <h2>Top Recommendations</h2>
    <ol>
        {% for item in scan.recommendations | default([]) %}
            <li>{{ item }}</li>
        {% endfor %}
    </ol>
    
    <div class="footer">
        <p>This report is confidential and intended for authorized personnel only.</p>
        <p>Report generated on {{ report_generated }}</p>
    </div>
</body>
</html>
"""

TECHNICAL_REPORT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Technical Security Assessment Report</title>
    <style>
        body { font-family: 'Courier New', monospace; margin: 20px; color: #333; }
        h1 { color: #1a1a1a; border-bottom: 3px solid #d32f2f; }
        h2 { color: #d32f2f; margin-top: 30px; page-break-after: avoid; }
        .section { margin-bottom: 30px; }
        .vulnerability { border-left: 4px solid #d32f2f; padding: 15px; background: #fff3e0; margin: 10px 0; }
        .port { border-left: 4px solid #1976d2; padding: 15px; background: #e3f2fd; margin: 10px 0; }
        table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; font-size: 12px; }
        th { background: #424242; color: white; }
        code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }
    </style>
</head>
<body>
    <h1>{{ report.title | default("Technical Security Assessment") }}</h1>
    <p><strong>Target:</strong> {{ scan.target }}</p>
    <p><strong>Date:</strong> {{ report_generated }}</p>
    
    <div class="section">
        <h2>1. Reconnaissance Findings</h2>
        <p><strong>Discovered Subdomains:</strong> {{ scan.recon.subdomains | length }}</p>
        {% for subdomain in scan.recon.subdomains | default([]) %}
            <div>• {{ subdomain }}</div>
        {% endfor %}
    </div>
    
    <div class="section">
        <h2>2. Open Ports & Services</h2>
        <table>
            <tr><th>Port</th><th>Service</th><th>State</th></tr>
            {% for port in scan.ports.open_ports | default([]) %}
                <tr>
                    <td>{{ port.port }}</td>
                    <td>{{ port.service }}</td>
                    <td>Open</td>
                </tr>
            {% endfor %}
        </table>
    </div>
    
    <div class="section">
        <h2>3. Web Vulnerabilities</h2>
        {% for vuln in scan.web_vulnerabilities.vulnerabilities | default([]) %}
            <div class="vulnerability">
                <strong>{{ vuln.title }}</strong>
                <p><strong>Severity:</strong> {{ vuln.severity }}</p>
                <p>{{ vuln.description | default("") }}</p>
            </div>
        {% endfor %}
    </div>
    
    <div class="section">
        <h2>4. CVE Findings</h2>
        <p><strong>Total CVEs Found:</strong> {{ scan.cve.total_cves }}</p>
    </div>
</body>
</html>
"""

COMPLIANCE_REPORT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Compliance Assessment Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #1565c0; }
        h2 { color: #1565c0; border-bottom: 2px solid #1565c0; }
        .owasp { background: #fff8e1; padding: 10px; border-left: 4px solid #fbc02d; margin: 10px 0; }
        .cwe { background: #e8f5e9; padding: 10px; border-left: 4px solid #66bb6a; margin: 10px 0; }
        .cvss { background: #f3e5f5; padding: 10px; border-left: 4px solid #9c27b0; margin: 10px 0; }
        table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        th, td { padding: 10px; text-align: left; border: 1px solid #ddd; }
        th { background: #1565c0; color: white; }
    </style>
</head>
<body>
    <h1>Compliance Assessment Report</h1>
    <p><strong>Organization:</strong> {{ scan.project_name }}</p>
    <p><strong>Date:</strong> {{ report_generated }}</p>
    
    <h2>OWASP Top 10 Mapping</h2>
    {% for finding in scan.findings | default([]) %}
        <div class="owasp">
            <strong>{{ finding.owasp_category }}</strong>
            <p>{{ finding.description }}</p>
        </div>
    {% endfor %}
    
    <h2>CWE Classification</h2>
    <table>
        <tr><th>CWE ID</th><th>Description</th><th>Count</th></tr>
        {% for finding in scan.findings | default([]) %}
            <tr>
                <td>{{ finding.cwe }}</td>
                <td>{{ finding.cwe_description }}</td>
                <td>1</td>
            </tr>
        {% endfor %}
    </table>
    
    <h2>CVSS Scores</h2>
    <table>
        <tr><th>Finding</th><th>CVSS Base</th><th>Severity</th></tr>
        {% for finding in scan.findings | default([]) %}
            <tr>
                <td>{{ finding.title }}</td>
                <td>{{ finding.cvss_score }}</td>
                <td>{{ finding.severity }}</td>
            </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

RISK_ASSESSMENT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Risk Assessment Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #d32f2f; }
        h2 { color: #d32f2f; }
        .critical { background: #ffebee; border-left: 4px solid #d32f2f; padding: 10px; }
        .high { background: #fff3e0; border-left: 4px solid #f57c00; padding: 10px; }
        .medium { background: #fce4ec; border-left: 4px solid #c2185b; padding: 10px; }
        .low { background: #e8f5e9; border-left: 4px solid #388e3c; padding: 10px; }
        .risk-matrix { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 20px 0; }
        .risk-cell { padding: 15px; text-align: center; font-weight: bold; color: white; }
    </style>
</head>
<body>
    <h1>Risk Assessment Report</h1>
    <p><strong>Target:</strong> {{ scan.target }}</p>
    <p><strong>Assessment Date:</strong> {{ report_generated }}</p>
    
    <h2>Risk Matrix</h2>
    <div class="risk-matrix">
        <div class="risk-cell critical">Critical: {{ severity_summary.critical }}</div>
        <div class="risk-cell high">High: {{ severity_summary.high }}</div>
        <div class="risk-cell medium">Medium: {{ severity_summary.medium }}</div>
        <div class="risk-cell low">Low: {{ severity_summary.low }}</div>
    </div>
    
    <h2>Risk-Prioritized Findings</h2>
    {% for vuln in scan.web_vulnerabilities.vulnerabilities | default([]) | sort(attribute='risk_score', reverse=true) %}
        <div class="{{ vuln.severity | lower }}">
            <strong>{{ vuln.title }}</strong>
            <p>Risk Score: {{ vuln.risk_score | default("TBD") }}</p>
            <p>Impact: {{ vuln.impact | default("High") }}</p>
            <p>Remediation Timeline: {{ vuln.remediation_timeline | default("Immediate") }}</p>
        </div>
    {% endfor %}
</body>
</html>
"""

REMEDIATION_ROADMAP_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Remediation Roadmap</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #1976d2; }
        .phase { margin: 20px 0; padding: 15px; background: #e3f2fd; border-left: 4px solid #1976d2; }
        .phase h3 { margin-top: 0; color: #1976d2; }
        ol { margin: 10px 0; }
        .deadline { color: #d32f2f; font-weight: bold; }
        .completed { color: #388e3c; }
    </style>
</head>
<body>
    <h1>Remediation Roadmap</h1>
    <p><strong>Organization:</strong> {{ scan.project_name }}</p>
    <p><strong>Report Date:</strong> {{ report_generated }}</p>
    
    <div class="phase">
        <h3>Phase 1: Immediate (0-7 Days)</h3>
        <p>Address critical vulnerabilities that pose immediate risk:</p>
        <ol>
            {% for item in scan.immediate_actions | default([]) %}
                <li>{{ item }}</li>
            {% endfor %}
        </ol>
        <p><strong>Deadline:</strong> <span class="deadline">{{ report_generated }}</span></p>
    </div>
    
    <div class="phase">
        <h3>Phase 2: Short-term (1-3 Months)</h3>
        <p>Resolve high-priority findings:</p>
        <ol>
            {% for item in scan.short_term_actions | default([]) %}
                <li>{{ item }}</li>
            {% endfor %}
        </ol>
        <p><strong>Target Date:</strong> 30-90 days from report date</p>
    </div>
    
    <div class="phase">
        <h3>Phase 3: Long-term (3-6 Months)</h3>
        <p>Implement strategic improvements:</p>
        <ol>
            {% for item in scan.long_term_actions | default([]) %}
                <li>{{ item }}</li>
            {% endfor %}
        </ol>
        <p><strong>Target Date:</strong> 90-180 days from report date</p>
    </div>
</body>
</html>
"""
