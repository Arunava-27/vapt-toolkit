"""Jinja2-based template engine for VAPT reports."""
import uuid
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from jinja2 import Environment, BaseLoader, TemplateNotFound, TemplateError


class TemplateEngine:
    """Manages report templates with Jinja2 rendering."""
    
    def __init__(self, db_conn_factory=None):
        """Initialize template engine with optional database connection."""
        self.jinja_env = Environment(loader=BaseLoader())
        self.db_conn = db_conn_factory
        self.templates_cache = {}
    
    def create_template(self, name: str, html_content: str, project_id: Optional[str] = None) -> str:
        """Create a new template and return template_id."""
        template_id = str(uuid.uuid4())
        template_data = {
            'id': template_id,
            'name': name,
            'content': html_content,
            'project_id': project_id,
            'created_at': datetime.now().isoformat(),
            'last_used': None,
            'variables': self._extract_variables(html_content)
        }
        
        if self.db_conn:
            from database import _conn
            with _conn() as c:
                c.execute(
                    '''INSERT INTO report_templates (id, project_id, name, content, created_at, last_used)
                       VALUES (?, ?, ?, ?, ?, ?)''',
                    (template_id, project_id, name, html_content, template_data['created_at'], None)
                )
                for var in template_data['variables']:
                    c.execute(
                        '''INSERT INTO template_variables (id, template_id, variable_name, description, type)
                           VALUES (?, ?, ?, ?, ?)''',
                        (str(uuid.uuid4()), template_id, var['name'], var['description'], var['type'])
                    )
        
        self.templates_cache[template_id] = template_data
        return template_id
    
    def apply_template(self, template_id: str, scan_data: Dict[str, Any]) -> str:
        """Render template with scan data."""
        template_content = self._get_template_content(template_id)
        if not template_content:
            raise TemplateNotFound(f"Template {template_id} not found")
        
        try:
            template = self.jinja_env.from_string(template_content)
            rendered = template.render(
                scan=scan_data,
                report_generated=datetime.now().isoformat(),
                **self._prepare_context(scan_data)
            )
            
            if self.db_conn:
                from database import _conn
                with _conn() as c:
                    c.execute(
                        'UPDATE report_templates SET last_used=? WHERE id=?',
                        (datetime.now().isoformat(), template_id)
                    )
            
            return rendered
        except TemplateError as e:
            raise ValueError(f"Template rendering failed: {str(e)}")
    
    def list_templates(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available templates."""
        if self.db_conn:
            from database import _conn
            with _conn() as c:
                if project_id:
                    rows = c.execute(
                        'SELECT id, name, created_at, last_used FROM report_templates WHERE project_id=? OR project_id IS NULL ORDER BY created_at DESC',
                        (project_id,)
                    ).fetchall()
                else:
                    rows = c.execute(
                        'SELECT id, name, created_at, last_used FROM report_templates ORDER BY created_at DESC'
                    ).fetchall()
                
                return [dict(row) for row in rows]
        
        return list(self.templates_cache.values())
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a template."""
        if self.db_conn:
            from database import _conn
            with _conn() as c:
                c.execute('DELETE FROM template_variables WHERE template_id=?', (template_id,))
                c.execute('DELETE FROM report_templates WHERE id=?', (template_id,))
        
        if template_id in self.templates_cache:
            del self.templates_cache[template_id]
        
        return True
    
    def save_template_preset(self, name: str, config: Dict[str, Any]) -> str:
        """Save a template preset configuration."""
        preset_id = str(uuid.uuid4())
        html_content = self._build_template_from_config(config)
        return self.create_template(name, html_content)
    
    def get_template_preview(self, template_id: str, sample_data: Optional[Dict] = None) -> str:
        """Get template preview with sample data."""
        if sample_data is None:
            sample_data = self._get_sample_scan_data()
        
        return self.apply_template(template_id, sample_data)
    
    def _extract_variables(self, html_content: str) -> List[Dict[str, str]]:
        """Extract Jinja2 variables from template content."""
        import re
        variables = []
        # Match {{ variable_name }} patterns
        pattern = r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_.]*)\s*\}\}'
        matches = set(re.findall(pattern, html_content))
        
        for match in matches:
            variables.append({
                'name': match,
                'description': f'Variable: {match}',
                'type': 'string'
            })
        
        return variables
    
    def _get_template_content(self, template_id: str) -> Optional[str]:
        """Get template content from cache or database."""
        if template_id in self.templates_cache:
            return self.templates_cache[template_id]['content']
        
        if self.db_conn:
            from database import _conn
            with _conn() as c:
                row = c.execute(
                    'SELECT content FROM report_templates WHERE id=?',
                    (template_id,)
                ).fetchone()
                if row:
                    return row['content']
        
        return None
    
    def _prepare_context(self, scan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare rendering context from scan data."""
        return {
            'project_name': scan_data.get('project_name', 'Unknown Project'),
            'target': scan_data.get('target', ''),
            'scan_date': scan_data.get('timestamp', datetime.now().isoformat()),
            'recon': scan_data.get('recon', {}),
            'ports': scan_data.get('ports', {}),
            'cves': scan_data.get('cve', {}),
            'web_vulnerabilities': scan_data.get('web_vulnerabilities', {}),
            'web': scan_data.get('web', {}),
            'severity_summary': self._calculate_severity_summary(scan_data),
        }
    
    def _calculate_severity_summary(self, scan_data: Dict[str, Any]) -> Dict[str, int]:
        """Calculate severity counts from scan data."""
        summary = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
        
        web_vulns = scan_data.get('web_vulnerabilities', {}).get('vulnerabilities', [])
        for vuln in web_vulns:
            severity = vuln.get('severity', 'info').lower()
            if severity in summary:
                summary[severity] += 1
        
        return summary
    
    def _build_template_from_config(self, config: Dict[str, Any]) -> str:
        """Build HTML template from configuration."""
        sections = config.get('sections', [])
        html_parts = ['<html><body>']
        
        for section in sections:
            if section.get('type') == 'header':
                html_parts.append(f"<h1>{section.get('title', 'Report')}</h1>")
            elif section.get('type') == 'summary':
                html_parts.append("<h2>Summary</h2><p>{{ scan.project_name }} - {{ scan.target }}</p>")
            elif section.get('type') == 'findings':
                html_parts.append("<h2>Findings</h2><table><tr><th>Issue</th><th>Severity</th></tr></table>")
            elif section.get('type') == 'remediation':
                html_parts.append("<h2>Remediation</h2><p>Detailed remediation steps here.</p>")
        
        html_parts.append("</body></html>")
        return "\n".join(html_parts)
    
    def _get_sample_scan_data(self) -> Dict[str, Any]:
        """Get sample scan data for preview."""
        return {
            'project_name': 'Sample Project',
            'target': 'example.com',
            'timestamp': datetime.now().isoformat(),
            'recon': {
                'subdomains': ['api.example.com', 'mail.example.com']
            },
            'ports': {
                'open_ports': [
                    {'port': 80, 'service': 'http'},
                    {'port': 443, 'service': 'https'}
                ]
            },
            'cve': {
                'total_cves': 5,
                'cves': []
            },
            'web_vulnerabilities': {
                'total_findings': 3,
                'vulnerabilities': [
                    {'title': 'XSS Vulnerability', 'severity': 'high'},
                    {'title': 'SQL Injection', 'severity': 'critical'}
                ]
            },
            'web': {
                'total': 10
            }
        }
