# Phase 6: Manual Testing on Real Targets — README

## 🎯 Objective

Conduct comprehensive manual testing of the VAPT Toolkit on real vulnerable applications to validate functionality, identify defects, and ensure production readiness.

**Status**: ✅ **READY FOR EXECUTION**

---

## 📋 What's Included

### Documentation (7 files)

| File | Size | Purpose |
|------|------|---------|
| `MANUAL_TESTING_GUIDE.md` | 22KB | Main testing strategy with 35 test scenarios |
| `TEST_ENVIRONMENTS_SETUP.md` | 10KB | Setup DVWA, WebGoat, Juice Shop |
| `DEFECTS_FOUND.md` | 5KB | Defect tracking template |
| `MANUAL_TESTING_REPORT.md` | 8KB | Test report template |
| `PHASE6_TESTING_CHECKLIST.md` | 11KB | Detailed execution checklist |
| `PHASE6_IMPLEMENTATION_SUMMARY.md` | 10KB | Overview and quick start |
| `test-environments-compose.yml` | 2KB | Docker Compose for environments |

### Python Tools (2 scripts)

| Script | Purpose |
|--------|---------|
| `manual_test_tracker.py` | Test tracking system (JSON/CSV) |
| `create_test_results_excel.py` | Excel spreadsheet generator (optional) |

### Test Data (auto-initialized)

```
test_results/
├── test_results.json    # Full test case data
├── test_results.csv     # CSV format
└── defects.json         # Defect tracking
```

---

## 🚀 Quick Start (5 Minutes)

### 1. Start Test Environments

```bash
# Using Docker Compose (recommended)
docker-compose -f test-environments-compose.yml up -d

# Check status
docker-compose -f test-environments-compose.yml ps

# Verify accessibility
curl http://localhost/DVWA/
curl http://localhost:8080/WebGoat
curl http://localhost:3000
```

### 2. Start VAPT Toolkit

```bash
# Terminal 1: Backend API (http://localhost:8000)
python server.py

# Terminal 2: Frontend UI (http://localhost:5173)
cd frontend && npm run dev
```

### 3. Initialize Test Tracker

```bash
python manual_test_tracker.py
```

Output:
```
✅ Added 30 default test cases
✅ Exported test results to test_results\test_results.csv

Test Results Summary:
- Total Tests: 35
- Passed: 0
- Failed: 0
- Pass Rate: 0%
```

### 4. Start Testing

Follow the **Execution Guide** below.

---

## 📊 Test Scenarios (35 Total)

### Web Scanning (15 tests)
- **WS-001 to WS-015**: SQLi, XSS, CSRF, IDOR, Auth bypass, Security headers, File upload, Path traversal, Command injection, XXE, SSRF, Open redirect, Info disclosure, Cookie security

### API Testing (5 tests)
- **API-001 to API-005**: Authentication, Rate limiting, Bulk scanning, Export formats, Webhook delivery

### Reporting (5 tests)
- **REP-001 to REP-005**: PDF generation, Excel export, Scan comparison, Heat map, Executive report

### UX Testing (5 tests)
- **UX-001 to UX-005**: Scope editor, Theme switching, Notifications, Scheduling, Search/filter

### Additional Tests (5 tests)
- Edge cases, error handling, performance, data integrity, recovery scenarios

---

## 🧪 Test Environments

### Environment 1: DVWA (Damn Vulnerable Web Application)
- **URL**: http://localhost/DVWA/
- **Login**: admin / password
- **Vulnerabilities**: 10+ classic web vulnerabilities
- **Best for**: SQL Injection, XSS, CSRF, File Upload, Path Traversal, Command Injection

### Environment 2: OWASP WebGoat
- **URL**: http://localhost:8080/WebGoat
- **Vulnerabilities**: 20+ security lessons
- **Best for**: Learning, IDOR, XXE, Authentication bypass, SQL Injection

### Environment 3: OWASP Juice Shop
- **URL**: http://localhost:3000
- **Login**: admin@juice-sh.op / admin123
- **Vulnerabilities**: 30+ real-world vulnerabilities
- **Best for**: XSS, IDOR, API testing, Business logic flaws

---

## 📝 Execution Guide

### Step-by-Step Testing

#### Phase 1: Web Scanning Tests (Days 1-3)

1. **WS-001: SQL Injection Detection**
   - Target: DVWA SQL injection page
   - Payload: `' OR '1'='1`
   - Expected: SQLi vulnerability detected

2. **WS-002-003: XSS Detection (Reflected & Stored)**
   - Target: DVWA XSS pages
   - Payload: `<script>alert('XSS')</script>`
   - Expected: XSS vulnerabilities identified

3. **Continue with WS-004 through WS-015**
   - Follow `MANUAL_TESTING_GUIDE.md` for each test
   - Document results in test tracker
   - Screenshot evidence for each

#### Phase 2: API Tests (Day 4)

1. **API-001: Authentication**
   ```bash
   curl -H "X-API-Key: YOUR_KEY" http://localhost:8000/api/scans
   ```

2. **API-002: Rate Limiting**
   ```bash
   for i in {1..100}; do curl -s http://localhost:8000/api/status; done
   ```

3. **Continue with API-003 through API-005**

#### Phase 3: Reporting Tests (Day 5)

1. Execute a scan
2. Generate PDF report
3. Export to Excel
4. Compare scans
5. Verify heat map
6. Generate executive report

#### Phase 4: UX Tests (Day 6)

1. Test scope editor workflow
2. Switch themes (dark/light)
3. Verify notifications
4. Create recurring schedule
5. Test search/filter

### Tracking Results

#### Update Test Results

```python
# After each test, update tracker:
from manual_test_tracker import TestTracker, TestCase, TestStatus

tracker = TestTracker()
tracker.update_test_status(
    test_id="WS-001",
    status=TestStatus.PASS,
    actual_result="SQL injection detected correctly",
    notes="Payload executed, vulnerability flagged as HIGH"
)
```

#### Log Defects

When you find issues, add to `DEFECTS_FOUND.md`:

```markdown
### Defect ID: DEF-001
**Title**: SQL Injection severity overestimated
**Severity**: MEDIUM
**Priority**: P2
**Status**: NEW

Description: SQLi marked as CRITICAL even for basic injection
Steps to Reproduce: [include steps]
Expected: Severity MEDIUM-HIGH
Actual: Severity CRITICAL
```

#### Update Report

Update `MANUAL_TESTING_REPORT.md` as you progress:
- Fill in test results tables
- Add defect statistics
- Document environment observations
- Calculate pass rates

---

## 📈 Success Criteria

### Minimum Requirements
- ✅ 30+ test scenarios executed
- ✅ 95%+ pass rate
- ✅ All critical defects resolved
- ✅ All environments verified working
- ✅ Test report completed

### Verification Checklist
- [ ] All 35 test cases executed
- [ ] Results documented for each
- [ ] Screenshots captured
- [ ] Defects logged and prioritized
- [ ] Pass rate calculated
- [ ] Test report generated
- [ ] Critical issues resolved
- [ ] Medium issues documented
- [ ] Team review completed
- [ ] Sign-off obtained

---

## 🔧 Troubleshooting

### Docker Issues

**DVWA won't start:**
```bash
docker logs vapt-dvwa
docker-compose down
docker-compose up -d --build
```

**Port already in use:**
```bash
# Find process using port
netstat -ano | findstr :80

# Kill process
taskkill /PID <PID> /F

# Or use different port in compose file
```

**Network issues:**
```bash
# Check container connectivity
docker exec vapt-dvwa ping webgoat
docker exec vapt-webgoat ping juice-shop
docker exec vapt-juice-shop ping dvwa
```

### Test Tracker Issues

**Reset test results:**
```bash
rm test_results/*.json
python manual_test_tracker.py  # Re-initializes
```

**Check test status:**
```bash
cat test_results/test_results.json | head -50
```

---

## 📊 Reporting

### Generate Summary
```bash
python manual_test_tracker.py
```

### View Results
```bash
cat test_results/test_results.csv
cat test_results/test_results.json
```

### Export to Excel (requires openpyxl)
```bash
pip install openpyxl
python create_test_results_excel.py
```

---

## 📚 Documentation Index

| Document | Usage |
|----------|-------|
| `MANUAL_TESTING_GUIDE.md` | Read first - main reference for all tests |
| `PHASE6_TESTING_CHECKLIST.md` | Use during execution - detailed checklists |
| `TEST_ENVIRONMENTS_SETUP.md` | Setup environments and troubleshoot |
| `DEFECTS_FOUND.md` | Log defects as you find them |
| `MANUAL_TESTING_REPORT.md` | Fill out during/after testing |
| `PHASE6_IMPLEMENTATION_SUMMARY.md` | Overview and quick reference |

---

## ⏱️ Time Estimates

| Phase | Duration | Tests |
|-------|----------|-------|
| Setup | 1-2 hours | - |
| Web Scanning | 2-3 days | 15 |
| API Testing | 1 day | 5 |
| Reporting | 1 day | 5 |
| UX Testing | 1 day | 5 |
| Report & Sign-off | 1 day | - |
| **TOTAL** | **7-10 days** | **35** |

---

## 🎓 Learning Resources

### Testing Foundations
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- SQL Injection: https://owasp.org/www-community/attacks/SQL_Injection
- XSS: https://owasp.org/www-community/attacks/xss/

### Tool Documentation
- DVWA Guide: http://localhost/DVWA/docs/
- WebGoat: http://localhost:8080/WebGoat/lessons
- Juice Shop: http://localhost:3000/#/score-board

---

## 🔐 Security Notes

⚠️ **Important**:
- These environments are intentionally vulnerable
- Use only for testing and learning
- Never deploy to production
- Never expose to public internet
- Reset after each test session
- Don't store real sensitive data

---

## 🤝 Team Collaboration

### Roles
- **QA Lead**: Oversees testing, approves results
- **Testers**: Execute test scenarios
- **Dev Lead**: Reviews defects, assigns fixes
- **PM**: Approves release readiness

### Communication
1. Daily status updates in test tracker
2. Critical defects reported immediately
3. Weekly progress reviews
4. Final sign-off meeting

---

## ✅ Pre-Launch Checklist

- [ ] All documentation reviewed
- [ ] Environments up and running
- [ ] VAPT toolkit accessible
- [ ] Test tracker initialized
- [ ] Team trained
- [ ] Screenshot tool ready
- [ ] Timeline agreed
- [ ] Defect escalation process defined

---

## 📞 Support

For issues:
1. Check relevant documentation
2. Review troubleshooting sections
3. Check Docker logs
4. Contact QA lead

---

**Ready to begin testing?** 

Start with:
1. `docker-compose -f test-environments-compose.yml up -d`
2. `python server.py` (in separate terminal)
3. `python manual_test_tracker.py`
4. Open `MANUAL_TESTING_GUIDE.md`

---

**Phase 6 Status**: ✅ READY FOR EXECUTION
**Created**: 2024-01-15
**Test Count**: 35 scenarios
**Expected Duration**: 7-10 days
**Success Target**: 95%+ pass rate
