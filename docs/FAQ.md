# 📚 VAPT Toolkit - Frequently Asked Questions (FAQ)

## Getting Started

### Q1: What is VAPT Toolkit and who should use it?

**A:** VAPT Toolkit is a professional-grade Vulnerability Assessment & Penetration Testing automation platform. It's designed for:
- **Security Teams** - Perform comprehensive vulnerability assessments at scale
- **Penetration Testers** - Automate reconnaissance and vulnerability detection workflows
- **DevSecOps Engineers** - Integrate security scanning into CI/CD pipelines
- **Compliance Auditors** - Generate detailed evidence-based security reports

The toolkit combines reconnaissance, vulnerability scanning, and professional reporting into a single unified platform with both CLI and web dashboard interfaces.

### Q2: What are the system requirements?

**A:** VAPT Toolkit requires:
- **Python:** 3.10 or higher
- **Memory:** 2GB minimum (4GB+ recommended for large scans)
- **Storage:** 1GB for installation, 2-5GB for databases/reports
- **Network:** Internet access for vulnerability data (NVD, exploit databases)
- **Operating System:** Windows, Linux, macOS (Docker also supported)

**Optional but Recommended:**
- Nmap (for advanced port scanning)
- Docker (for containerized deployment)
- Git (for version control)

### Q3: How do I install VAPT Toolkit?

**A:** Quick installation (3 steps):

```bash
# Clone the repository
git clone https://github.com/vapt/toolkit.git
cd vapt-toolkit

# Install dependencies
pip install -r requirements.txt

# Start the application
python main.py
```

**For Docker deployment:**
```bash
docker-compose up -d
# Access dashboard at http://localhost:8000
```

See `/docs/DEPLOYMENT_GUIDE.md` for detailed deployment options.

### Q4: How do I access the web dashboard?

**A:** After starting the application:
1. Open your browser to `http://localhost:8000`
2. You'll see the VAPT Dashboard home page
3. No authentication required by default (see security configuration for production)
4. Navigate using the left sidebar menu

**Features available:**
- Create and manage scan targets
- View scan results in real-time
- Generate reports in multiple formats
- Manage scan history and comparisons

### Q5: How do I verify the installation?

**A:** Run the verification command:

```bash
python -m pytest tests/test_database.py -v
python main.py --version
```

Or test via the API:
```bash
curl http://localhost:8000/api/health
```

Expected response: `{"status": "healthy"}`

---

## Configuration & Setup

### Q6: How do I configure scan targets?

**A:** Targets can be configured in three ways:

**1. Via Web Dashboard:**
- Go to "Scope Manager" tab
- Click "Add Target"
- Enter URL/IP address, ports, and scope options
- Save the target

**2. Via CLI:**
```bash
python main.py --target example.com --module web
```

**3. Via API:**
```bash
curl -X POST http://localhost:8000/api/targets \
  -H "Content-Type: application/json" \
  -d '{
    "name": "example",
    "target": "example.com",
    "ports": "80,443"
  }'
```

**Scope Management:**
- **In-Scope:** Define which endpoints/subdomains to scan
- **Out-of-Scope:** Explicitly exclude URLs to avoid scanning restricted areas
- **Rate Limiting:** Set requests/second to avoid triggering WAF

### Q7: What modules should I enable for my scan?

**A:** Choose based on your testing objectives:

| Objective | Recommended Modules |
|-----------|-------------------|
| **Web Application** | XSS Tester, SQL Injection, CSRF/SSRF, Auth Tester, Access Control |
| **API Security** | Injection Tester, Auth Tester, Rate Limit Tester |
| **Cloud Infrastructure** | Cloud Scanner, Port Scanner, Certificate Analysis |
| **Dependency Check** | JS Analyzer, CVE Scanner, Vulnerable Components |
| **Full Assessment** | All modules (requires more time) |
| **Quick Scan** | Web Scanner (XSS, SQL Injection, Basic Auth checks) |

**Module Descriptions:**
```
XSS Tester               → Detects cross-site scripting vulnerabilities
Injection Tester        → SQL, NoSQL, Command injection detection
CSRF/SSRF Tester        → Cross-site request forgery & server-side request forgery
Auth Tester             → Authentication bypass, session management flaws
Access Control Tester   → IDOR, path traversal, authorization weaknesses
Sensitive Data Tester   → Exposed API keys, credentials, personal data
File Misconfig Tester   → Security headers, SSL/TLS, misconfiguration
Business Logic Tester   → Business workflow abuse, logic flaws
Rate Limit Tester       → Rate limiting bypass attempts
Cloud Scanner           → AWS, Azure, GCP misconfiguration detection
JS Analyzer             → Frontend vulnerabilities, dependency analysis
CVE Scanner             → Correlate with NVD for known vulnerabilities
```

### Q8: How do I configure authentication credentials?

**A:** Authentication can be configured in the Scope Editor:

1. Go to **Scope Manager** → Select target → **Advanced Options**
2. Set authentication method:
   - **Basic Auth:** Username/password (base64 encoded)
   - **Bearer Token:** API token/JWT
   - **Cookie:** Session cookies
   - **Custom Header:** Custom authentication headers

**Example - Via API:**
```bash
curl -X POST http://localhost:8000/api/scans \
  -d '{
    "target": "example.com",
    "auth_type": "bearer",
    "auth_token": "YOUR_JWT_TOKEN"
  }'
```

**Security Note:** Credentials are stored encrypted in the database and never logged.

### Q9: How do I set up scheduled/recurring scans?

**A:** Use the Scheduling module:

1. Create a scan via dashboard or API
2. Go to **Scan Details** → **Schedule** tab
3. Choose recurrence:
   - Daily (specify time)
   - Weekly (choose days)
   - Monthly (choose date)
4. Set maximum concurrent scans limit
5. Save schedule

**Via CLI:**
```bash
python main.py --target example.com --schedule "0 2 * * *"  # Daily at 2 AM
```

---

## Common Errors & Solutions

### Q10: I'm getting "Connection refused" error

**A:** This typically means the service isn't running or listening on the wrong port.

**Solutions:**
```bash
# 1. Check if the service is running
ps aux | grep python

# 2. Verify the port is correct
# Default is 8000, check with:
netstat -tlnp | grep 8000

# 3. If port 8000 is in use, change it:
python main.py --port 9000

# 4. Check logs for startup errors:
tail -f logs/vapt.log

# 5. On Windows, try:
netstat -ano | findstr :8000
taskkill /PID <PID> /F  # Kill process using port
```

### Q11: Scans are timing out - what do I do?

**A:** Scan timeouts usually mean the target is slow or unresponsive.

**Solutions:**
```python
# In configuration or via API, increase timeouts:
{
    "scan_timeout": 3600,           # 1 hour (default)
    "request_timeout": 30,          # Per-request timeout
    "connection_timeout": 10,       # Connection establishment
    "max_retries": 3                # Retry failed requests
}
```

**Optimization tips:**
- Reduce scope to specific endpoints only
- Disable slowest modules (JS Analyzer, CVE correlation)
- Increase request rate (more concurrent threads)
- Scan during off-peak hours
- Use `--quick-scan` mode for rapid assessment

### Q12: My database is growing too large - what can I free up?

**A:** The SQLite database accumulates scan results, logs, and cache.

**Solutions:**
```bash
# Backup first!
cp vapt.db vapt.db.backup

# Clean old results (keep last 30 days):
python tools/cleanup.py --days 30

# Or manually via database:
# Delete scans older than 90 days:
DELETE FROM scans WHERE created_at < datetime('now', '-90 days');
VACUUM;
```

**Prevention:**
- Archive old scans to external storage
- Implement automated cleanup in scheduled tasks
- Use `--archive-only` mode to move old data

### Q13: "SSL Certificate Verification Failed" - what should I do?

**A:** This error occurs when scanning HTTPS sites with self-signed certificates.

**Solutions:**
```bash
# 1. Disable SSL verification (not recommended for production):
python main.py --target https://internal.example.com --ssl-verify=false

# 2. Add custom CA certificate:
python main.py --target https://internal.example.com \
  --ca-cert /path/to/ca-bundle.crt

# 3. Via configuration file:
# In config.yml:
ssl:
  verify: false
  ca_bundle: /path/to/ca-bundle.crt
```

**Security Note:** Only disable verification for trusted internal systems during testing.

### Q14: Finding false positives in results - how do I manage them?

**A:** VAPT Toolkit includes false positive pattern matching to reduce noise.

**Solutions:**
1. **Mark as False Positive:**
   - In dashboard: Click finding → "Mark as False Positive"
   - Saves pattern for future scans
   
2. **View False Positive Patterns:**
   - Go to **Settings** → **False Positive Patterns**
   - Review auto-learned patterns
   - Adjust thresholds if too aggressive

3. **Via API:**
   ```bash
   curl -X POST http://localhost:8000/api/findings/mark-fp \
     -d '{"finding_id": "12345", "reason": "Expected behavior"}'
   ```

4. **Confidence Scoring:**
   - System automatically calculates confidence (0-100%)
   - Filter by confidence threshold: `--min-confidence 70`

---

## Performance & Optimization

### Q15: How can I speed up scans?

**A:** Several optimization techniques:

**1. Parallel Processing:**
```bash
python main.py --target example.com \
  --threads 10                      # More concurrent threads
  --modules web_scanner             # Only essential modules
```

**2. Targeted Scanning:**
```bash
# Scan specific paths only:
python main.py --target example.com \
  --paths "/api,/admin,/login" \
  --exclude "/images,/assets"
```

**3. Quick Mode:**
```bash
# Skip time-consuming checks:
python main.py --target example.com --quick-scan
# Excludes: JS Analysis, CVE correlation, brute-forcing
```

**4. Module Selection:**
```bash
# Only run needed modules:
python main.py --target example.com \
  --modules xss_tester,injection_tester
```

**5. Rate Optimization:**
```bash
# Adjust request rate:
python main.py --target example.com \
  --requests-per-second 50          # Faster
  --concurrent-requests 20          # Parallel connections
```

**Typical Performance:**
- Simple website (10 pages): 2-5 minutes
- Medium application (100 pages): 10-20 minutes
- Large application (1000+ pages): 30-60 minutes
- With full CVE correlation: +5-10 minutes

### Q16: What are the resource requirements for large scans?

**A:** Resource usage scales with scan complexity:

| Scan Type | Memory | Disk | Duration |
|-----------|--------|------|----------|
| Quick (10 URLs) | 256MB | 50MB | 2 min |
| Standard (100 URLs) | 512MB | 200MB | 15 min |
| Large (1000 URLs) | 2GB | 1GB | 60 min |
| Enterprise (10k+ URLs) | 4-8GB | 5GB+ | 2-4 hours |

**Optimization for enterprise:**
- Distribute scans across multiple servers
- Use Docker for resource isolation
- Implement scan queuing
- Archive old results frequently

### Q17: How do I export results in different formats?

**A:** VAPT supports six export formats:

```bash
# HTML Report (best for review)
python main.py --target example.com --report-format html

# PDF Report (professional presentation)
python main.py --target example.com --report-format pdf

# Excel Export (analysis & filtering)
python main.py --target example.com --report-format excel

# JSON (API integration)
python main.py --target example.com --report-format json

# Markdown (documentation)
python main.py --target example.com --report-format markdown

# SARIF (CI/CD integration)
python main.py --target example.com --report-format sarif
```

**Bulk Export:**
```bash
# Export all recent scans
curl -X POST http://localhost:8000/api/export/bulk \
  -d '{
    "format": "excel",
    "days": 7,
    "include_false_positives": false
  }'
```

---

## When to Use Which Modules

### Q18: Should I use JS Analyzer for every scan?

**A:** JS Analyzer is valuable but slower. Use it when:

**✅ Use JS Analyzer when:**
- Testing frontend-heavy applications (SPAs, React, Vue, Angular)
- Security is critical (financial, healthcare apps)
- Scanning third-party dependencies is required
- Time is not a major constraint

**⏭️ Skip JS Analyzer when:**
- Backend APIs only (no frontend)
- Rapid assessment needed
- Scanning simple static sites
- Database/infrastructure focused

**Performance Impact:** +5-15 minutes per scan

### Q19: When should I use CVE Scanner vs regular vulnerability checks?

**A:** Different tools for different purposes:

| Tool | Purpose | When to Use | Time |
|------|---------|-----------|------|
| **Regular Vulns** | App logic flaws, misconfig | Always (web, auth, injection) | 2-10 min |
| **CVE Scanner** | Known package vulnerabilities | When dependencies matter | +10 min |
| **Both Together** | Complete assessment | Production/compliance | 15-30 min |

**Strategy:**
- Use regular scanners for active vulnerability discovery
- Use CVE Scanner to validate found vulnerabilities against known exploits
- Combine for full compliance/audit requirements

### Q20: What's the difference between Auth Tester and Access Control Tester?

**A:** They test different aspects:

| Module | Tests | Finds |
|--------|-------|-------|
| **Auth Tester** | Login mechanisms, session handling | Weak passwords, bypass techniques, MFA flaws |
| **Access Control** | Authorization, permissions | IDOR, path traversal, privilege escalation |

**Example:**
- Auth Tester: "Can I bypass login?"
- Access Control: "Can I access other users' data?"

**Use both together** for complete authentication & authorization testing.

---

## Advanced Topics

### Q21: Can I integrate VAPT with GitHub Actions?

**A:** Yes! VAPT has built-in GitHub Actions integration.

**Setup:**
```yaml
name: Security Scan
on: [push, pull_request]

jobs:
  vapt-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: VAPT Security Scan
        uses: vapt-toolkit/action@v1
        with:
          target: ${{ github.event.repository.clone_url }}
          modules: 'web_scanner,js_analyzer'
          report-format: 'sarif'
      - name: Upload SARIF Report
        uses: github/codeql-action/upload-sarif@v2
```

See `/docs/GITHUB_ACTIONS_SETUP.md` for complete guide.

### Q22: How do I set up webhooks for scan notifications?

**A:** Configure webhooks to get notifications on scan completion:

**Via Dashboard:**
1. Go to **Settings** → **Webhooks**
2. Add webhook URL
3. Choose events: `scan_started`, `scan_completed`, `finding_critical`

**Via API:**
```bash
curl -X POST http://localhost:8000/api/webhooks \
  -d '{
    "url": "https://your-app.com/webhook",
    "events": ["scan_completed", "critical_finding"],
    "secret": "your-secret-key"
  }'
```

**Webhook Payload:**
```json
{
  "event": "scan_completed",
  "scan_id": "abc123",
  "target": "example.com",
  "findings_count": 12,
  "high_severity": 2,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Q23: Can I compare results between scans?

**A:** Yes! Comparison engine shows changes between scans:

**Via Dashboard:**
1. Go to **Scan History**
2. Select two scans to compare
3. View side-by-side: new findings, fixed, still present

**Via API:**
```bash
curl http://localhost:8000/api/scans/compare \
  -d '{"scan_id1": "abc", "scan_id2": "def"}'
```

**Report Shows:**
- New vulnerabilities found
- Vulnerabilities fixed
- Unchanged vulnerabilities
- Severity trend
- OWASP category distribution

---

## Support & Resources

### Q24: Where can I find more documentation?

**A:** Complete documentation available at:

| Document | Purpose |
|----------|---------|
| `/docs/API_REFERENCE.md` | REST API endpoints and examples |
| `/docs/DEPLOYMENT_GUIDE.md` | Production deployment |
| `/docs/OWASP_MAPPING.md` | OWASP/CWE vulnerability mapping |
| `/docs/EXECUTIVE_REPORT_GUIDE.md` | Report generation and customization |
| `/docs/GITHUB_ACTIONS_SETUP.md` | CI/CD integration |
| `README.md` | Project overview and features |

### Q25: How do I report bugs or request features?

**A:** We welcome feedback!

**For Bugs:**
1. Check existing issues first
2. Create detailed bug report with:
   - VAPT version
   - OS and Python version
   - Steps to reproduce
   - Error logs

**For Features:**
- Describe use case
- Explain expected behavior
- Provide examples if possible

**Contact:**
- GitHub Issues: Primary channel
- Email: support@vapt-toolkit.dev
- Documentation: Check `/docs/` first

---

## Troubleshooting Checklist

✅ **Before Reporting Issues:**
- [ ] Updated to latest version: `git pull && pip install -r requirements.txt`
- [ ] Restarted the application
- [ ] Checked logs: `tail -f logs/vapt.log`
- [ ] Verified database integrity: `sqlite3 vapt.db "PRAGMA integrity_check;"`
- [ ] Tested with simple target first
- [ ] Reviewed relevant documentation
- [ ] Searched existing issues/FAQ

✅ **For Support:**
- [ ] Include VAPT version: `python main.py --version`
- [ ] Include Python version: `python --version`
- [ ] Include OS: `uname -a` or `systeminfo`
- [ ] Attach relevant logs
- [ ] Provide minimal reproduction case

---

## Key Takeaways

1. **Start Simple:** Use quick-scan mode for initial assessment
2. **Choose Modules Wisely:** Select based on your application type
3. **Monitor Performance:** Adjust threads/rate if scans timeout
4. **Manage False Positives:** Mark them to improve accuracy
5. **Automate:** Use scheduling and CI/CD integration
6. **Export Professionally:** Generate reports for stakeholders
7. **Keep Updated:** Regularly pull latest vulnerability data

---

## Quick Reference Commands

```bash
# Quick scan
python main.py --target example.com --quick-scan

# Full assessment
python main.py --target example.com --modules all

# With authentication
python main.py --target example.com --auth-token YOUR_TOKEN

# Custom report
python main.py --target example.com --report-format pdf

# Run tests
pytest tests/ -v

# Clean database
python tools/cleanup.py --days 30

# Export results
curl http://localhost:8000/api/export/bulk -o results.xlsx

# Check health
curl http://localhost:8000/api/health
```

---

*Last Updated: 2024*  
*VAPT Toolkit Version: 7.0+*  
*For Latest Information: Visit https://vapt-toolkit.dev*
