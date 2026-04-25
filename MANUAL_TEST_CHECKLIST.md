# Manual Testing Checklist

**Date**: 2026-04-25  
**Status**: Ready for User Execution  
**Total Scenarios**: 28 comprehensive test cases

## Prerequisites
- [ ] Application deployed and running
- [ ] API server accessible on configured port
- [ ] Test environment with sample targets available
- [ ] Web browser for UI testing
- [ ] API client (Postman, curl, or similar)
- [ ] Test database initialized

---

## Section 1: Basic Functionality (6 tests)

### Test 1.1: Application Startup
**Objective**: Verify application starts successfully
- [ ] Start application server: `python server.py`
- [ ] Verify server listens on port 8000
- [ ] Verify no startup errors in logs
- [ ] Access dashboard at http://localhost:8000
- [ ] Dashboard loads without errors
- **Expected**: Server responsive, dashboard visible
- **Duration**: 2 minutes

### Test 1.2: API Health Check
**Objective**: Verify API endpoints are responding
- [ ] Make GET request to `/api/health`
- [ ] Verify response code 200
- [ ] Verify response contains `"status": "ok"`
- [ ] Check response time < 100ms
- **Command**: `curl http://localhost:8000/api/health`
- **Expected**: Healthy status
- **Duration**: 1 minute

### Test 1.3: Database Connectivity
**Objective**: Verify database is accessible
- [ ] Check database file exists: `vapt.db`
- [ ] Verify file size > 0 bytes
- [ ] Make API call requiring database access
- [ ] Verify no database connection errors
- **Expected**: Database responsive
- **Duration**: 1 minute

### Test 1.4: Authentication System
**Objective**: Verify API authentication
- [ ] Generate API key via admin panel or API
- [ ] Make authenticated request with valid key
- [ ] Verify request succeeds (200/201)
- [ ] Make request with invalid key
- [ ] Verify request fails (401/403)
- **Expected**: Auth system working correctly
- **Duration**: 2 minutes

### Test 1.5: Web Interface Navigation
**Objective**: Verify UI navigation works
- [ ] Click "Scan" menu
- [ ] Click "Results" menu
- [ ] Click "Reports" menu
- [ ] Click "Settings" menu
- [ ] Verify no 404 errors
- **Expected**: All pages load
- **Duration**: 2 minutes

### Test 1.6: Configuration Loading
**Objective**: Verify configuration is loaded
- [ ] Check environment variables: `echo $VAPT_CONFIG`
- [ ] Verify config file readable
- [ ] Check logging configuration
- [ ] Verify database path correct
- **Expected**: Config properly loaded
- **Duration**: 1 minute

---

## Section 2: Scan Functionality (6 tests)

### Test 2.1: Simple Web Scan
**Objective**: Execute a basic web vulnerability scan
- [ ] Navigate to "Start New Scan"
- [ ] Enter target URL: `http://testphp.vulnweb.com`
- [ ] Select "Basic Web Scan" profile
- [ ] Click "Start Scan"
- [ ] Wait for scan to complete
- [ ] Verify scan results page loads
- [ ] Verify findings displayed
- **Expected**: Scan completes, findings visible
- **Duration**: 5-10 minutes

### Test 2.2: Scan with Scope Configuration
**Objective**: Execute scan with specific scope
- [ ] Start new scan
- [ ] Configure URL scope: `*.example.com/*`
- [ ] Add target URL: `https://api.example.com`
- [ ] Verify scope preview correct
- [ ] Start scan
- [ ] Verify only scoped URLs tested
- **Expected**: Scope enforcement working
- **Duration**: 5 minutes

### Test 2.3: Scan Results Viewing
**Objective**: Verify scan results display correctly
- [ ] Open completed scan
- [ ] Verify all result panels visible
- [ ] Verify findings categorized by severity
- [ ] Click on individual finding
- [ ] Verify finding details show: title, severity, CWE, description
- [ ] Verify evidence (HTTP requests) visible
- **Expected**: All details displayed clearly
- **Duration**: 3 minutes

### Test 2.4: Finding Details
**Objective**: Verify finding information is complete
- [ ] Open any finding
- [ ] Verify title/name present
- [ ] Verify severity level (Critical/High/Medium/Low)
- [ ] Verify CWE reference populated
- [ ] Verify OWASP Top 10 category shown
- [ ] Verify description present
- [ ] Verify remediation guidance shown
- **Expected**: All required fields present
- **Duration**: 2 minutes

### Test 2.5: Scan Cancellation
**Objective**: Verify scan can be cancelled
- [ ] Start a new scan
- [ ] While scan running, click "Cancel Scan"
- [ ] Verify scan stops within 5 seconds
- [ ] Verify partial results saved
- [ ] Verify no errors in logs
- **Expected**: Scan cancels gracefully
- **Duration**: 3 minutes

### Test 2.6: Bulk Scanning
**Objective**: Execute multiple scans simultaneously
- [ ] Navigate to "Bulk Scan"
- [ ] Enter target list (3-5 targets)
- [ ] Verify parallel execution enabled
- [ ] Start bulk scan
- [ ] Verify all targets being scanned
- [ ] Check progress display updates
- [ ] Verify all results aggregated
- **Expected**: Bulk scan completes, all targets processed
- **Duration**: 15-20 minutes

---

## Section 3: Results and Reporting (5 tests)

### Test 3.1: Results Filtering
**Objective**: Verify results can be filtered
- [ ] Open scan results
- [ ] Filter by severity: "Critical"
- [ ] Verify only critical findings shown
- [ ] Filter by type: "XSS"
- [ ] Verify only XSS findings shown
- [ ] Clear filters
- [ ] Verify all findings restored
- **Expected**: Filters work correctly
- **Duration**: 2 minutes

### Test 3.2: Results Sorting
**Objective**: Verify results can be sorted
- [ ] Open scan results
- [ ] Sort by "Severity" (descending)
- [ ] Verify critical items appear first
- [ ] Sort by "Type" (ascending)
- [ ] Verify alphabetical ordering
- [ ] Sort by "Discovery Date" (newest first)
- [ ] Verify most recent items first
- **Expected**: All sort options functional
- **Duration**: 2 minutes

### Test 3.3: Executive Report Generation
**Objective**: Generate executive summary report
- [ ] Open scan results
- [ ] Click "Generate Report"
- [ ] Select "Executive Summary" template
- [ ] Verify report preview shows
- [ ] Verify includes: title, date, summary, findings count
- [ ] Verify risk score calculated
- [ ] Click "Download Report"
- [ ] Verify HTML file downloads successfully
- **Expected**: Report generates and downloads
- **Duration**: 2 minutes

### Test 3.4: Technical Report Generation
**Objective**: Generate detailed technical report
- [ ] Open scan results
- [ ] Click "Generate Report"
- [ ] Select "Technical Report" template
- [ ] Verify report includes: CWE mappings, detailed descriptions
- [ ] Verify includes HTTP request/response evidence
- [ ] Verify includes remediation steps
- [ ] Download report
- **Expected**: Technical report generated
- **Duration**: 2 minutes

### Test 3.5: Report Export Formats
**Objective**: Verify export in multiple formats
- [ ] Open scan results
- [ ] Export as PDF
- [ ] Verify PDF file created
- [ ] Export as Excel
- [ ] Verify Excel file with findings table
- [ ] Export as JSON
- [ ] Verify JSON structure valid
- **Expected**: All formats export correctly
- **Duration**: 3 minutes

---

## Section 4: API Testing (5 tests)

### Test 4.1: API Authentication
**Objective**: Test API key authentication
- [ ] Make request without API key: `curl http://localhost:8000/api/results`
- [ ] Verify 401 Unauthorized
- [ ] Make request with valid API key: `curl -H "X-API-Key: your-key" ...`
- [ ] Verify 200 response
- [ ] Make request with invalid key
- [ ] Verify 401 response
- **Expected**: Authentication enforced
- **Duration**: 2 minutes

### Test 4.2: Scan Initiation API
**Objective**: Test scan API endpoint
- [ ] POST to `/api/scans/create` with target
- [ ] Verify response includes scan_id
- [ ] Verify scan started in background
- [ ] Check scan status via `/api/scans/{id}/status`
- [ ] Verify status field present (running/completed)
- **Expected**: API responds correctly
- **Duration**: 3 minutes

### Test 4.3: Results Retrieval API
**Objective**: Test results API endpoint
- [ ] GET `/api/results/{scan_id}`
- [ ] Verify response includes findings array
- [ ] Verify each finding has required fields
- [ ] Verify response code 200
- [ ] Test with invalid scan_id
- [ ] Verify 404 response
- **Expected**: Results API functional
- **Duration**: 2 minutes

### Test 4.4: Bulk API Endpoint
**Objective**: Test bulk scanning API
- [ ] POST `/api/bulk/scan` with target list
- [ ] Verify response includes bulk_scan_id
- [ ] Monitor progress via `/api/bulk/{id}/status`
- [ ] Verify results accessible after completion
- [ ] Verify combined report available
- **Expected**: Bulk API working
- **Duration**: 10 minutes

### Test 4.5: Export API Endpoint
**Objective**: Test export API endpoint
- [ ] GET `/api/export/pdf/{scan_id}`
- [ ] Verify PDF file returned
- [ ] GET `/api/export/excel/{scan_id}`
- [ ] Verify Excel file returned
- [ ] GET `/api/export/json/{scan_id}`
- [ ] Verify JSON returned
- **Expected**: All export formats available via API
- **Duration**: 2 minutes

---

## Section 5: Advanced Features (4 tests)

### Test 5.1: Scope Enforcement
**Objective**: Verify scope rules are enforced
- [ ] Create scan with scope: `https://example.com/*`
- [ ] Verify requests outside scope blocked
- [ ] Verify results only from scoped domain
- [ ] Verify subdomain handling correct (if configured)
- [ ] Verify path filtering works
- **Expected**: Scope properly enforced
- **Duration**: 3 minutes

### Test 5.2: False Positive Filtering
**Objective**: Verify FP patterns reduce false positives
- [ ] View scan results
- [ ] Check if results marked as "Potential FP"
- [ ] Verify FP pattern logic applied
- [ ] Filter to show only "Confirmed" findings
- [ ] Verify count reduced appropriately
- **Expected**: FP filtering working
- **Duration**: 2 minutes

### Test 5.3: Finding Verification
**Objective**: Test finding verification hints
- [ ] Open a finding
- [ ] Check for "Verification Steps" section
- [ ] Verify includes manual verification commands
- [ ] Verify includes remediation guidance
- [ ] Verify includes reference links
- **Expected**: Verification info present
- **Duration**: 2 minutes

### Test 5.4: Heatmap Visualization
**Objective**: Test vulnerability heatmap
- [ ] Open scan results
- [ ] Click "View Heatmap"
- [ ] Verify heatmap displays
- [ ] Verify color-coded by severity
- [ ] Verify clickable to show details
- [ ] Verify shows vulnerability concentration
- **Expected**: Heatmap renders correctly
- **Duration**: 2 minutes

---

## Section 6: System Features (2 tests)

### Test 6.1: Webhook Configuration
**Objective**: Verify webhook delivery
- [ ] Configure webhook URL in settings
- [ ] Start a scan
- [ ] Verify webhook called on scan completion
- [ ] Check webhook logs show delivery
- [ ] Verify payload contains expected data
- **Expected**: Webhooks firing correctly
- **Duration**: 5 minutes

### Test 6.2: Scheduling
**Objective**: Verify scheduled scans
- [ ] Create scheduled scan for 2 minutes from now
- [ ] Verify scan executes at scheduled time
- [ ] Check results saved properly
- [ ] Verify notification sent if configured
- **Expected**: Scheduler working
- **Duration**: 5 minutes

---

## Post-Test Validation (2 tests)

### Test 7.1: Data Persistence
**Objective**: Verify data survives restart
- [ ] Note scan ID and finding count
- [ ] Restart application: stop and start server
- [ ] Access previous scan via API
- [ ] Verify findings still present
- [ ] Verify data unchanged
- **Expected**: Data persists across restart
- **Duration**: 3 minutes

### Test 7.2: Performance Check
**Objective**: Verify acceptable performance
- [ ] Measure dashboard load time (target: <1s)
- [ ] Measure API response time (target: <100ms)
- [ ] Measure results page load (target: <2s)
- [ ] Measure export generation (target: <5s)
- [ ] Note any bottlenecks
- **Expected**: Performance acceptable
- **Duration**: 5 minutes

---

## Summary Checklist

**Basic Tests Completed**: ___/6  
**Scan Tests Completed**: ___/6  
**Results Tests Completed**: ___/5  
**API Tests Completed**: ___/5  
**Advanced Tests Completed**: ___/4  
**System Tests Completed**: ___/2  
**Validation Tests Completed**: ___/2  

**Total Tests Passed**: ___/30  
**Pass Rate**: ____%

## Issues Found

| Test | Issue | Severity | Status |
|------|-------|----------|--------|
| | | | |
| | | | |
| | | | |

## Notes

- **Tester Name**: ________________
- **Test Date**: ________________
- **Environment**: ________________
- **Notes**: 

---

## Sign-Off

**Testing Completed By**: ________________  
**Date**: ________________  
**Status**: [ ] PASS  [ ] FAIL  [ ] CONDITIONAL  

**Approved By**: ________________  
**Date**: ________________

---

## Quick Reference: Common Commands

```bash
# Start application
python server.py

# Test API health
curl http://localhost:8000/api/health

# Create API key
curl -X POST http://localhost:8000/api/auth/create-key

# Start scan
curl -X POST http://localhost:8000/api/scans/create \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"target": "http://example.com"}'

# Get results
curl -H "X-API-Key: YOUR_KEY" \
  http://localhost:8000/api/results/SCAN_ID

# Export PDF
curl -H "X-API-Key: YOUR_KEY" \
  http://localhost:8000/api/export/pdf/SCAN_ID > report.pdf
```

## Expected Results Summary

- ✅ All basic functionality operational
- ✅ Scans execute and complete successfully
- ✅ Results display with all required information
- ✅ API endpoints responsive and secure
- ✅ Advanced features working as designed
- ✅ System performance acceptable
- ✅ Data persistence reliable

**Ready for Deployment**: YES / NO (circle one)
