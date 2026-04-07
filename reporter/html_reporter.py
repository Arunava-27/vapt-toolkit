"""HTML and JSON report generator using Jinja2."""
import json
import os
from jinja2 import Template
from datetime import datetime

SEVERITY_COLOR = {
    "Critical": "#f85149",
    "HIGH": "#f85149",
    "High": "#f0883e",
    "MEDIUM": "#f0883e",
    "Medium": "#d29922",
    "LOW": "#3fb950",
    "Low": "#3fb950",
    "N/A": "#8b949e",
}

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>VAPT Report — {{ target }}</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; }
    body { font-family: 'Segoe UI', monospace; background: #0d1117; color: #c9d1d9; padding: 2rem; margin: 0; }
    a { color: #58a6ff; }
    h1 { color: #58a6ff; margin-bottom: 0.25rem; }
    h2 { color: #79c0ff; border-bottom: 1px solid #30363d; padding-bottom: .4rem; margin-top: 2rem; }
    .meta { color: #8b949e; font-size: .9rem; margin-bottom: 2rem; }
    .summary { display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 2rem; }
    .card { background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 1rem 1.5rem; min-width: 140px; }
    .card .num { font-size: 2rem; font-weight: bold; color: #58a6ff; }
    .card .label { font-size: .8rem; color: #8b949e; }
    table { width: 100%; border-collapse: collapse; margin-bottom: 1.5rem; font-size: .9rem; }
    td, th { border: 1px solid #30363d; padding: .5rem .75rem; text-align: left; }
    th { background: #161b22; color: #8b949e; font-weight: 600; }
    tr:hover td { background: #161b22; }
    .badge { display: inline-block; padding: .15rem .5rem; border-radius: 4px; font-size: .75rem; font-weight: bold; color: #0d1117; }
    .none { color: #8b949e; font-style: italic; }
    .truncate { max-width: 400px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  </style>
</head>
<body>
<h1>🛡️ VAPT Report</h1>
<p class="meta">Target: <strong>{{ target }}</strong> &nbsp;|&nbsp; Generated: {{ timestamp }}</p>

<div class="summary">
  <div class="card"><div class="num">{{ results.recon.subdomains | length if results.recon else 0 }}</div><div class="label">Subdomains</div></div>
  <div class="card"><div class="num">{{ results.ports.open_ports | length if results.ports else 0 }}</div><div class="label">Open Ports</div></div>
  <div class="card"><div class="num">{{ results.cve.total_cves if results.cve else 0 }}</div><div class="label">CVEs Found</div></div>
  <div class="card"><div class="num">{{ results.web.total if results.web else 0 }}</div><div class="label">Web Findings</div></div>
</div>

{% if results.recon %}
<h2>🔍 Reconnaissance — Subdomains</h2>
{% if results.recon.subdomains %}
<table>
  <tr><th>Subdomain</th><th>IP Addresses</th></tr>
  {% for s in results.recon.subdomains %}
  <tr><td>{{ s.subdomain }}</td><td>{{ s.ips | join(', ') }}</td></tr>
  {% endfor %}
</table>
{% else %}
<p class="none">No subdomains discovered.</p>
{% endif %}
{% endif %}

{% if results.ports %}
<h2>🚪 Port Scan Results</h2>
{% if results.ports.open_ports %}
<table>
  <tr><th>Port</th><th>Service</th><th>Version</th></tr>
  {% for p in results.ports.open_ports %}
  <tr><td>{{ p.port }}</td><td>{{ p.service }}</td><td>{{ p.version or '—' }}</td></tr>
  {% endfor %}
</table>
{% else %}
<p class="none">No open ports found.</p>
{% endif %}
{% endif %}

{% if results.cve %}
<h2>🐛 CVE Correlation</h2>
{% for entry in results.cve.correlations %}
  {% if entry.cves %}
  <h3 style="color:#c9d1d9;margin-top:1rem">Port {{ entry.port }} — {{ entry.service }} {{ entry.version }}</h3>
  <table>
    <tr><th>CVE ID</th><th>Severity</th><th>Score</th><th>Description</th></tr>
    {% for cve in entry.cves %}
    {% set sev = cve.severity | upper %}
    <tr>
      <td><a href="https://nvd.nist.gov/vuln/detail/{{ cve.cve_id }}" target="_blank">{{ cve.cve_id }}</a></td>
      <td><span class="badge" style="background:{{ severity_color.get(cve.severity, '#8b949e') }}">{{ cve.severity }}</span></td>
      <td>{{ cve.score }}</td>
      <td class="truncate" title="{{ cve.description }}">{{ cve.description }}</td>
    </tr>
    {% endfor %}
  </table>
  {% endif %}
{% endfor %}
{% if results.cve.total_cves == 0 %}<p class="none">No CVEs correlated.</p>{% endif %}
{% endif %}

{% if results.web %}
<h2>🕸️ Web Vulnerability Findings</h2>
{% if results.web.findings %}
<table>
  <tr><th>Type</th><th>Severity</th><th>Parameter</th><th>Payload</th><th>Evidence</th><th>Location</th></tr>
  {% for f in results.web.findings %}
  <tr>
    <td>{{ f.type }}</td>
    <td><span class="badge" style="background:{{ severity_color.get(f.severity, '#8b949e') }}">{{ f.severity }}</span></td>
    <td>{{ f.parameter }}</td>
    <td><code>{{ f.payload }}</code></td>
    <td>{{ f.evidence }}</td>
    <td class="truncate" title="{{ f.location }}">{{ f.location }}</td>
  </tr>
  {% endfor %}
</table>
{% else %}
<p class="none">No web vulnerabilities detected.</p>
{% endif %}
{% endif %}

</body>
</html>"""


class HTMLReporter:
    def __init__(self, target: str, results: dict):
        self.target = target
        self.results = results

    def generate(self, output_path: str):
        tmpl = Template(TEMPLATE)
        html = tmpl.render(
            target=self.target,
            results=self.results,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            severity_color=SEVERITY_COLOR,
        )
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

    def generate_json(self, output_path: str):
        payload = {
            "target": self.target,
            "generated_at": datetime.now().isoformat(),
            "results": self.results,
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)
