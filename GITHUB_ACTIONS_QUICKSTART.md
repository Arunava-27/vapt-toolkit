# VAPT Toolkit GitHub Actions - Quick Start

## Installation (5 minutes)

The GitHub Actions workflow is already included in the repository. No installation needed - it activates automatically!

## Step 1: Enable GitHub Actions (Already Done ✅)

The workflow file is at: `.github/workflows/vapt-scan.yml`

**Features Already Configured:**
- ✅ Triggers on `push` to main/develop/release branches
- ✅ Triggers on `pull_request` to main/develop
- ✅ Tests Python 3.10, 3.11, and 3.12 in parallel
- ✅ Uploads SARIF reports to GitHub Security tab
- ✅ Posts detailed PR comments with findings
- ✅ 30-minute timeout protection

## Step 2: Configure Secrets (Optional but Recommended)

To scan a specific target, set repository secrets:

```bash
# Option A: Using GitHub CLI
gh secret set VAPT_TARGET_URL --body "https://your-app.example.com"
gh secret set VAPT_API_KEY --body "your-api-key-here"

# Option B: Via GitHub Web UI
1. Go to Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add VAPT_TARGET_URL (e.g., https://your-app.com)
4. Add VAPT_API_KEY (if needed)
```

**Without secrets:**
- Workflow runs against `http://localhost:3000`
- Useful for testing and development
- Still generates all reports and comments

## Step 3: Verify Installation

Create a test push to trigger the workflow:

```bash
git add .github/workflows/vapt-scan.yml
git commit -m "feat: Enable VAPT GitHub Actions security scanning"
git push origin main
```

**Watch the workflow run:**
1. Go to your repository
2. Click on **Actions** tab
3. Select **VAPT Automated Security Scan**
4. Watch it execute

## Step 4: View Results

### Security Tab (SARIF Reports)
1. Go to **Security** → **Code scanning**
2. View findings by severity and location
3. Click findings for details

### Pull Request Comments
1. Create a pull request
2. Check PR comments for scan results
3. See findings summarized by severity

## Quick Configuration Examples

### Scan Your Development Server

```bash
gh secret set VAPT_TARGET_URL --body "https://dev.example.com:8080"
```

### Use API Authentication

```bash
gh secret set VAPT_API_KEY --body "Bearer token-abc123xyz"
```

### Require Scan to Pass Before Merge

1. Settings → Branches → Add rule for `main`
2. Enable "Require status checks to pass"
3. Select "VAPT Automated Security Scan"

## What Happens on Push

```
1. Code pushed to main/develop/release
   ↓
2. Workflow triggers automatically
   ↓
3. VAPT server starts (30s)
   ↓
4. Web vulnerability scan runs (3-5 min per Python version)
   ↓
5. SARIF report generated (JSON format)
   ↓
6. Report uploaded to GitHub Security tab
   ↓
7. Results available in Security → Code scanning
```

## What Happens on Pull Request

```
1. PR opened/updated
   ↓
2. Workflow triggers automatically
   ↓
3. Full security scan runs
   ↓
4. SARIF report uploaded
   ↓
5. Formatted comment posted to PR with findings:
   - Severity breakdown
   - Key vulnerabilities
   - Confidence scores
   - Remediation guidance
```

## PR Comment Example

Your PR will receive a comment like:

```
## 🛡️ VAPT Security Scan Results

| Severity | Count | Status |
|----------|-------|--------|
| 🔴 Critical | 1 | ❌ |
| 🟠 High | 2 | ❌ |
| 🟡 Medium | 1 | ⚠️ |
| 🟢 Low | 0 | ✅ |
| **Total** | **4** | |

### 🔴 Critical Severity Findings

#### 1. 🔴 SQL Injection
**Location**: `/api/users?id=...`
**Confidence**: 98% [████░]
**Evidence**: SQL error detected in response
**References**: CWE-89 | A03:2021 - Injection

[... more findings ...]
```

## Understanding Severity Levels

| Level | Icon | Meaning | Action |
|-------|------|---------|--------|
| Critical | 🔴 | Exploit likely, immediate risk | Fix before merge |
| High | 🟠 | Significant risk | Review and plan fix |
| Medium | 🟡 | Moderate risk | Track and schedule |
| Low | 🟢 | Minor risk | Document if needed |

## Viewing Detailed Results

### Security Tab Report
1. Go to **Security** tab
2. Click **Code scanning** 
3. Select **VAPT Toolkit** tool
4. View by:
   - Severity
   - Location
   - Rule type

### Scan Details
Each finding shows:
- Vulnerability type
- Location (file/endpoint)
- Confidence score
- Evidence collected
- CWE reference
- OWASP category
- Remediation guidance

## Troubleshooting

### Workflow Not Running?
- Check repository has Actions enabled
- Verify workflow file at `.github/workflows/vapt-scan.yml`
- Check branch permissions

### No PR Comment?
- Verify permissions: Settings → Actions → General
- Check `pull-requests: write` is enabled
- Workflow must run successfully first

### SARIF Not Showing?
- Check Security tab is enabled
- Verify `security-events: write` permission
- Workflow must complete without errors

### See Full Logs
1. Actions tab → Workflow run
2. Click job name to expand
3. Scroll through full log output

## Full Documentation

For complete setup and advanced configuration, see:

📖 **[docs/GITHUB_ACTIONS_SETUP.md](./docs/GITHUB_ACTIONS_SETUP.md)**
- Complete configuration guide
- Environment variable reference
- Advanced customization options
- Full troubleshooting section
- Integration examples

## Next Steps

### 1. Test Workflow
Push to main branch and watch it run in Actions tab

### 2. Configure Target (Optional)
```bash
gh secret set VAPT_TARGET_URL --body "https://your-target.com"
```

### 3. Create a PR
See scan results posted automatically as PR comment

### 4. Review Security Tab
Check detailed findings in Security → Code scanning

### 5. Set Up Requirements (Optional)
Require passing scan before merge (branch protection)

## Common Questions

**Q: Can I scan multiple targets?**  
A: Edit the workflow to add multiple targets in matrix strategy. See docs for examples.

**Q: How long does a scan take?**  
A: Typically 3-5 minutes per Python version, runs in parallel.

**Q: Will it scan branches other than main?**  
A: By default, only main/develop/release branches. Edit workflow to add others.

**Q: Can I skip the scan for certain commits?**  
A: Use `[skip ci]` in commit message or configure conditional steps in workflow.

**Q: What if I don't want Python 3.10/3.11 versions?**  
A: Edit workflow matrix to include only 3.11 for example.

**Q: Can I use this on a private repository?**  
A: Yes! Works identically on private repos.

## Monitoring

### View Workflow History
1. Actions tab → VAPT Automated Security Scan
2. See all workflow runs with status
3. Click run for detailed logs

### Set Up Notifications
GitHub can notify you of:
- Workflow failures
- Pull requests with failing checks
- New security findings

Enable in Settings → Notifications

## Support

Need help?

1. Check **[docs/GITHUB_ACTIONS_SETUP.md](./docs/GITHUB_ACTIONS_SETUP.md)** troubleshooting section
2. Review workflow logs: Actions tab → Workflow run details
3. Run validation: `python validate_github_actions.py`
4. Create an issue with error logs

## Integration Verification

To verify the integration is working:

```bash
# Run validation script
python validate_github_actions.py

# Expected output:
# ✅ SARIF Reporter tests PASSED
# ✅ PR Comment Generator tests PASSED
# ✅ ALL VALIDATION TESTS PASSED
```

---

**Ready?** Push your code and watch the automated security scanning begin! 🚀

See the full guide in [docs/GITHUB_ACTIONS_SETUP.md](./docs/GITHUB_ACTIONS_SETUP.md) for advanced options.
