# Risk Heat Map - Quick Reference Card

## 🚀 Getting Started

### Access the Heat Map
1. Open a project in VAPT toolkit
2. Click the **"🔥 Risk Heat Map"** tab
3. Choose your view mode
4. Adjust filters and click **Refresh**

---

## 📊 View Modes

| Mode | Shows | Best For |
|------|-------|----------|
| **By Target** | Targets × Severity | Finding high-risk targets |
| **By Time** | Time Periods × Severity | Tracking progress |
| **By Severity** | Severity Distribution | Executive reports |
| **By Type** | Vulnerability Type × Severity | Training needs |

---

## 🎨 Color Legend

```
🔴 Red       Critical   →  Immediate action needed
🟠 Orange    High       →  Urgent remediation
🟡 Yellow    Medium     →  Scheduled remediation
🟢 Green     Low        →  Regular updates
🔵 Blue      Info       →  Monitor only
```

---

## 📤 Export Options

| Format | Use Case | Size |
|--------|----------|------|
| **SVG** | Presentations, editing | Small (~50-200 KB) |
| **PNG** | Reports, emails | Medium (~100-500 KB) |
| **Print** | PDF output, paper | Full page |

---

## 🔗 API Endpoints

### By Target
```
GET /api/reports/heatmap/by-target?projectId=ID&start_date=DATE&end_date=DATE
```

### By Time Series
```
GET /api/reports/heatmap/by-time?projectId=ID&period=week&target=TARGET
```

### By Severity
```
GET /api/reports/heatmap/by-severity?projectId=ID
```

### By Type
```
GET /api/reports/heatmap/by-type?projectId=ID
```

---

## 💡 Common Use Cases

### 📈 Track Progress
1. Select "By Time" view
2. Choose "Weekly" period
3. Watch severity trends decrease

### 🎯 Prioritize Targets
1. Select "By Target" view
2. Sort by highest Critical count
3. Allocate resources accordingly

### 📊 Executive Report
1. Select "By Severity" view
2. Note the Risk Score
3. Export as PNG
4. Add to slides

### 🔍 Root Cause Analysis
1. Select "By Type" view
2. Identify most frequent vulnerability type
3. Plan training or tooling

---

## ⚙️ Filters

### By Target View
- **Start Date**: Show findings from this date onwards
- **End Date**: Show findings up to this date

### By Time View
- **Period**: Day, Week, Month, Quarter, Year
- **Target**: Filter to specific target (optional)

### By Severity View
- No filters (portfolio-wide view)

### By Type View
- No filters (portfolio-wide view)

---

## 📈 Risk Score Interpretation

| Score | Level | Action |
|-------|-------|--------|
| 0-20 | Low | Monitor |
| 21-40 | Medium-Low | Plan fixes |
| 41-60 | Medium | Schedule fixes |
| 61-80 | High | Urgent fixes |
| 81-100 | Critical | Immediate action |

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| No data showing | Ensure project has scans; check date range |
| Slow loading | Reduce time period; filter to specific targets |
| Export not working | Try PNG format; check browser settings |
| Text too small | Use browser zoom (Ctrl++); try mobile view |

---

## 📚 More Information

- Full Guide: See `HEATMAP_GUIDE.md`
- Implementation: See `HEATMAP_IMPLEMENTATION_SUMMARY.md`
- API Docs: See server.py line 2474+

---

## ✨ Key Features

✅ Multi-dimensional vulnerability analysis
✅ Interactive tooltips and drill-down
✅ Real-time data aggregation
✅ Professional color scheme
✅ Export to SVG/PNG
✅ Print-friendly layout
✅ Mobile responsive
✅ Date filtering
✅ Risk scoring
✅ Trend analysis

---

## 🎓 Tips & Tricks

1. **Weekly View is Best**: Weekly period balances granularity and readability
2. **Export Before Meetings**: Save PNG versions for presentations
3. **Check Trends**: Compare Week-over-Week to see real progress
4. **Target Filter**: Use "By Time" + target filter to track specific applications
5. **Type View**: Identify systemic issues (e.g., all targets have XSS)
6. **Mobile Friendly**: Heat map works great on phones for quick checks
7. **Severity Drill-down**: Higher opacity = higher risk (darker cells)

---

## 📞 Support

For help:
1. Check `HEATMAP_GUIDE.md` for detailed information
2. Review examples in the guide
3. Check GitHub issues
4. Contact your security team

---

**Version 1.0 | Phase 5 Professional Reporting**
