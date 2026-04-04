"""HTML report generator using Jinja2."""
from jinja2 import Template
from datetime import datetime

TEMPLATE = """<!DOCTYPE html>
<html><head><title>VAPT Report — {{ target }}</title>
<style>body{font-family:monospace;background:#0d1117;color:#c9d1d9;padding:2rem}
h1{color:#58a6ff}table{width:100%;border-collapse:collapse}
td,th{border:1px solid #30363d;padding:.5rem}th{background:#161b22}</style></head>
<body><h1>🛡️ VAPT Report</h1>
<p>Target: <strong>{{ target }}</strong> | Generated: {{ timestamp }}</p>
{% if results.ports %}<h2>Open Ports</h2><table>
<tr><th>Port</th><th>Service</th><th>Version</th></tr>
{% for p in results.ports.open_ports %}
<tr><td>{{ p.port }}</td><td>{{ p.service }}</td><td>{{ p.version }}</td></tr>
{% endfor %}</table>{% endif %}
</body></html>"""

class HTMLReporter:
    def __init__(self, target: str, results: dict):
        self.target = target
        self.results = results

    def generate(self, output_path: str):
        tmpl = Template(TEMPLATE)
        html = tmpl.render(target=self.target, results=self.results, timestamp=datetime.now())
        with open(output_path, "w") as f:
            f.write(html)
