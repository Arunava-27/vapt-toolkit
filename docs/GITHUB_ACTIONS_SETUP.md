# GitHub Actions CI/CD Integration Guide

This guide explains how to set up and use VAPT Toolkit with GitHub Actions for automated security scanning on code pushes and pull requests.

## Overview

The VAPT GitHub Actions workflow automatically:
- Runs web vulnerability scans on every push and pull request
- Generates SARIF reports for GitHub Security tab integration
- Posts detailed security findings as PR comments
- Supports Python versions 3.10, 3.11, and 3.12
- Provides actionable remediation guidance

## Quick Start

### 1. Repository Setup

The workflow file is located at `.github/workflows/vapt-scan.yml`. No additional setup is required if you've cloned the repository.

If you're setting up from scratch:

```bash
mkdir -p .github/workflows
cp vapt-scan.yml .github/workflows/vapt-scan.yml
git add .github/workflows/vapt-scan.yml
git commit -m "feat: Add VAPT security scanning workflow"
git push
```

### 2. Configure Secrets

The workflow uses GitHub repository secrets for sensitive configuration.

Go to **Settings → Secrets and variables → Actions** and create:

#### Required Secrets

- **`VAPT_TARGET_URL`** *(Optional)*
  - URL to scan (e.g., `https://api.example.com`)
  - If not provided, defaults to `http://localhost:3000`
  - Used for active scanning tests

- **`VAPT_API_KEY`** *(Optional)*
  - API key for authenticated scanning
  - Used if your target requires authentication

#### Example Secret Configuration

```bash
# Via GitHub CLI
gh secret set VAPT_TARGET_URL --body "https://vulnerable-app.example.com"
gh secret set VAPT_API_KEY --body "your-api-key-here"
```

### 3. Verify Workflow Setup

The workflow will automatically run on:
- Push to `main`, `develop`, or `release/**` branches
- Pull requests to `main` or `develop` branches

To manually trigger a workflow run:
1. Go to **Actions** tab
2. Select **VAPT Automated Security Scan**
3. Click **Run workflow**

## Workflow Architecture

### Jobs Overview

```
setup → scan → report → comment → cleanup
```

#### Job 1: Setup
- Checks out code
- Sets up Python environment (3.10, 3.11, 3.12)
- Installs dependencies
- Starts VAPT server and verifies health

#### Job 2: Scan
- Configures scan target
- Runs VAPT web vulnerability scanner
- Tests for: XSS, SQLi, CSRF, IDOR, SSRF, Auth weakness, File uploads, Business logic
- Generates SARIF v2.1.0 report

#### Job 3: Report
- Generates security summary report
- Processes findings by severity
- Creates scan metrics

#### Job 4: Comment
- Generates formatted PR comment
- Posts results summary to pull request
- Includes severity breakdown and key findings

#### Job 5: Cleanup
- Terminates VAPT server processes
- Logs workflow summary

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SARIF_OUTPUT_DIR` | Directory for SARIF reports | `./sarif-reports` |
| `VAPT_TARGET_URL` | Target URL for scanning | `http://localhost:3000` |
| `VAPT_API_KEY` | Authentication token (optional) | None |

## Configuration Options

### Customizing Scan Parameters

Edit `.github/workflows/vapt-scan.yml` to modify scan configuration:

```yaml
- name: Run VAPT web vulnerability scan
  run: |
    python -c "
    scan_config = {
        'target': '${{ steps.config.outputs.target }}',
        'web': True,
        'web_vulnerability_scan': True,
        'web_test_injection': True,
        'web_test_xss': True,
        'web_test_auth': True,
        'web_test_idor': True,
        'web_test_csrf_ssrf': True,
        'web_test_file_upload': True,
        'web_test_misconfiguration': True,
        'web_test_sensitive_data': True,
        'web_test_business_logic': True,
        'web_test_rate_limiting': True,
        'web_depth': 2,  # Change crawl depth (1-3)
        'scan_classification': 'active',  # active|passive|hybrid
        'override_robots_txt': False
    }
    "
```

### Filtering Branches

Modify the `on` section to change when workflows trigger:

```yaml
on:
  push:
    branches: [main, develop, staging]  # Add more branches
  pull_request:
    branches: [main, develop]
```

### Matrix Customization

To test only specific Python versions:

```yaml
strategy:
  matrix:
    python-version: ['3.11']  # Only Python 3.11
```

## Understanding Results

### GitHub Security Tab Integration

SARIF reports are automatically uploaded to the GitHub Security tab:

1. Go to **Security → Code scanning**
2. View findings by severity and location
3. Click findings for detailed information

### PR Comments

When a scan runs on a pull request, a formatted comment is posted containing:

- Summary table (Critical, High, Medium, Low findings)
- Detailed findings with evidence
- Confidence scores
- CWE and OWASP references
- Remediation guidance
- Scan metadata (target, duration, timestamp)

### SARIF Report Format

SARIF (Static Analysis Results Format) v2.1.0 reports include:

```json
{
  "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/...",
  "version": "2.1.0",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "VAPT Toolkit",
          "rules": [...]
        }
      },
      "results": [
        {
          "ruleId": "VAPT-SQL-INJECTION",
          "level": "error",
          "message": { "text": "..." },
          "locations": [...]
        }
      ]
    }
  ]
}
```

## Interpreting Findings

### Severity Levels

| Level | Icon | Description |
|-------|------|-------------|
| Critical | 🔴 | Immediate security risk, exploit likely |
| High | 🟠 | Significant risk, reasonable exploit path |
| Medium | 🟡 | Moderate risk, requires specific conditions |
| Low | 🟢 | Minor risk, difficult or low-impact exploit |

### Confidence Scores

- **95-100%**: High confidence, likely real vulnerability
- **80-94%**: Good confidence, very probable vulnerability
- **60-79%**: Moderate confidence, investigate further
- **<60%**: Low confidence, may be false positive

### Common Findings

#### SQL Injection (Critical)
- **CWE**: CWE-89
- **OWASP**: A03:2021 - Injection
- **Fix**: Use parameterized queries, input validation, prepared statements

#### Cross-Site Scripting (High)
- **CWE**: CWE-79
- **OWASP**: A03:2021 - Injection
- **Fix**: Output encoding, Content Security Policy, input validation

#### CSRF (High)
- **CWE**: CWE-352
- **OWASP**: A01:2021 - Broken Access Control
- **Fix**: CSRF tokens, SameSite cookies, origin validation

#### Authentication Weakness (High)
- **CWE**: CWE-287
- **OWASP**: A07:2021 - Identification and Authentication Failures
- **Fix**: Strong passwords, MFA, secure session management

#### Security Misconfiguration (Medium)
- **CWE**: CWE-16
- **OWASP**: A05:2021 - Security Misconfiguration
- **Fix**: Security hardening, disable unnecessary features, review configs

## Troubleshooting

### Server Fails to Start

**Problem**: "Server failed to start" error

**Solutions**:
1. Check system resources (memory, CPU)
2. Verify Python version compatibility
3. Review `server.log` in workflow artifacts
4. Check for port conflicts

```bash
# Check server logs
cat server.log | tail -50
```

### Scan Timeout

**Problem**: Scan exceeds 25-minute timeout

**Solutions**:
1. Reduce `web_depth` from 2 to 1
2. Disable unnecessary test types
3. Use a simpler target for testing
4. Increase timeout in workflow (max recommended: 30 minutes)

### False Positives

**Problem**: Finding doesn't appear to be a real vulnerability

**Solutions**:
1. Review the evidence provided
2. Check confidence score (low confidence = likely false positive)
3. Test manually to verify
4. Report as issue if systematic

### SARIF Upload Fails

**Problem**: "Failed to upload SARIF" error

**Solutions**:
1. Verify `security-events: write` permission
2. Check SARIF file is valid JSON
3. Review file size (max 10MB per SARIF file)
4. Check GitHub Actions logs for detailed error

### PR Comment Not Posted

**Problem**: Scan runs but no comment appears on PR

**Solutions**:
1. Verify `pull-requests: write` permission
2. Ensure workflow triggers on `pull_request` event
3. Check for workflow errors in Actions tab
4. Review permissions in repository settings

## Advanced Configuration

### Custom Scan Targets

Use GitHub environment variables for different deployment stages:

```yaml
env:
  STAGING_TARGET: "https://staging.example.com"
  PRODUCTION_TARGET: "https://api.example.com"

jobs:
  scan:
    environment:
      name: ${{ github.ref == 'refs/heads/main' && 'production' || 'staging' }}
```

### Notification Integration

Send notifications on critical findings:

```yaml
- name: Notify on critical findings
  if: env.CRITICAL_COUNT > 0
  run: |
    # Send to Slack, Teams, or email
    curl -X POST ${{ secrets.SLACK_WEBHOOK }} \
      -H 'Content-Type: application/json' \
      -d '{"text":"Critical vulnerabilities detected!"}'
```

### Conditional Scanning

Skip scanning for certain file patterns:

```yaml
- name: Check if scan needed
  id: check_files
  run: |
    if git diff --name-only HEAD~1 | grep -E '\.(py|js|html)$'; then
      echo "should_scan=true" >> $GITHUB_OUTPUT
    else
      echo "should_scan=false" >> $GITHUB_OUTPUT
    fi

- name: Run scan
  if: steps.check_files.outputs.should_scan == 'true'
  run: # scan steps
```

## Integration with Other Tools

### Required Status Check

Require scan to pass before merging:

1. Go to **Settings → Branches → Branch protection rules**
2. Add rule for `main`
3. Enable **Require status checks to pass**
4. Select **VAPT Automated Security Scan** job

### Artifact Retention

Configure how long artifacts are retained:

```yaml
jobs:
  scan:
    # Keep artifacts for 30 days
    permissions:
      actions: write
```

### SARIF Upload to Alternative Services

Upload SARIF to other platforms:

```yaml
- name: Upload to DefectDojo
  run: |
    curl -X POST https://defectdojo.example.com/api/v2/import-scan/ \
      -H "Authorization: Token ${{ secrets.DEFECTDOJO_TOKEN }}" \
      -F "file=@./sarif-reports/vapt-scan.sarif"
```

## Best Practices

### 1. Regularly Update Scanning Rules

Keep the workflow updated with latest vulnerability patterns:

```bash
git pull origin main
git merge upstream  # If using fork
```

### 2. Monitor False Positives

Create an issue to track false positives and adjust confidence thresholds:

```yaml
- name: Filter by confidence
  if: github.event_name == 'pull_request'
  run: python -c "
    # Only post findings with >80% confidence to PRs
    min_confidence = 0.80
  "
```

### 3. Implement Fix Workflow

When findings are reported:
1. Review the evidence
2. Validate the vulnerability
3. Create issue with remediation steps
4. Submit fix in new PR
5. Re-run scan to verify fix

### 4. Regular Security Training

Share findings with team:
- Review common vulnerabilities found
- Discuss remediation strategies
- Update secure coding practices

### 5. Baseline Comparison

Compare results across scans:

```yaml
- name: Compare with baseline
  run: python -c "
    import json
    with open('latest-scan.sarif') as f:
      latest = json.load(f)
    # Compare to baseline and report changes
  "
```

## Performance Optimization

### Caching Dependencies

The workflow uses `cache: 'pip'` to cache Python packages:

```yaml
- name: Set up Python
  uses: actions/setup-python@v4
  with:
    python-version: ${{ matrix.python-version }}
    cache: 'pip'
```

### Parallel Testing

Current workflow tests 3 Python versions in parallel. To optimize:

```yaml
strategy:
  matrix:
    python-version: ['3.11']  # Test only latest
  max-parallel: 3
```

### Timeout Optimization

Adjust timeouts based on your needs:

```yaml
jobs:
  scan:
    timeout-minutes: 15  # Reduce from 25 for faster feedback
```

## Reporting Issues

If you encounter issues:

1. **Check Logs**: Go to **Actions → Workflow Run → Logs**
2. **Review Artifacts**: Check uploaded SARIF files
3. **Test Locally**: Run VAPT manually to reproduce
4. **Report Issue**: Include workflow logs and configuration

## Additional Resources

- [VAPT Toolkit Documentation](../README.md)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [SARIF Specification](https://docs.oasis-open.org/sarif/sarif/v2.1.0/)
- [OWASP Top 10 2021](https://owasp.org/Top10/)
- [CWE Directory](https://cwe.mitre.org/)

## Support

For questions or issues:
- Create an issue on GitHub
- Check existing issues for solutions
- Review workflow logs for error details
- Test with minimal configuration first

## Examples

### Example 1: Scanning Private Repository

```yaml
- name: Configure target
  env:
    TARGET: ${{ secrets.INTERNAL_API_URL }}
```

### Example 2: Matrix Testing Multiple Targets

```yaml
strategy:
  matrix:
    target: ['https://api.example.com', 'https://app.example.com']
    python-version: ['3.11']
```

### Example 3: Conditional Notifications

```yaml
- name: Notify team on critical findings
  if: contains(job.status, 'failure')
  uses: 8398a7/action-slack@v3
  with:
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
    text: 'Critical security findings detected!'
```

---

**Last Updated**: 2024-12-19
**Maintained By**: VAPT Toolkit Team
**Version**: 1.0.0
