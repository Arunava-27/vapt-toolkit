import React, { useState, useEffect, useMemo } from "react";
import "../styles/ExecutiveReport.css";

export default function ExecutiveReport({ scanId, findings = [] }) {
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pdfLoading, setPdfLoading] = useState(false);

  useEffect(() => {
    const fetchReport = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/api/reports/executive/${scanId}`);
        if (!response.ok) throw new Error("Failed to fetch executive report");
        const data = await response.json();
        setReportData(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (scanId) {
      fetchReport();
    }
  }, [scanId]);

  const handleDownloadPDF = async () => {
    try {
      setPdfLoading(true);
      const response = await fetch(`/api/reports/executive/${scanId}/pdf`);
      if (!response.ok) throw new Error("Failed to download PDF");
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `executive-report-${new Date().toISOString().split("T")[0]}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      alert("Failed to download PDF: " + err.message);
    } finally {
      setPdfLoading(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  if (loading) {
    return <div className="exec-report loading">Loading executive report...</div>;
  }

  if (error) {
    return <div className="exec-report error">Error: {error}</div>;
  }

  if (!reportData) {
    return <div className="exec-report empty">No report data available</div>;
  }

  const riskScore = reportData.risk_score || 0;
  const riskLevel = reportData.risk_level || "Unknown";
  const metrics = reportData.metrics || {};
  const keyFindings = reportData.key_findings || [];
  const compliance = reportData.compliance_status || {};
  const roadmap = reportData.remediation_roadmap || [];

  const getRiskColor = (score) => {
    if (score >= 66) return "#cf222e";
    if (score >= 33) return "#f0883e";
    return "#3fb950";
  };

  const getRiskColorName = (score) => {
    if (score >= 66) return "critical";
    if (score >= 33) return "high";
    return "low";
  };

  const riskColor = getRiskColor(riskScore);
  const riskColorName = getRiskColorName(riskScore);

  return (
    <div className="exec-report">
      <div className="exec-header">
        <div>
          <h1>🛡️ Executive Security Summary</h1>
        </div>
        <div className="exec-actions">
          <button onClick={handleDownloadPDF} disabled={pdfLoading} className="btn-primary">
            {pdfLoading ? "Generating..." : "📥 Download PDF"}
          </button>
          <button onClick={handlePrint} className="btn-secondary">
            🖨️ Print
          </button>
        </div>
      </div>

      <div className="exec-risk-gauge">
        <div className="gauge-container">
          <svg viewBox="0 0 120 120" className="gauge">
            <circle cx="60" cy="60" r="50" fill="none" stroke="#e5e7eb" strokeWidth="8" />
            <circle
              cx="60"
              cy="60"
              r="50"
              fill="none"
              stroke={riskColor}
              strokeWidth="8"
              strokeDasharray={`${(riskScore / 100) * Math.PI * 100} ${Math.PI * 100}`}
              strokeLinecap="round"
              transform="rotate(-90 60 60)"
            />
            <text x="60" y="65" textAnchor="middle" fontSize="32" fontWeight="bold" fill={riskColor}>
              {riskScore}
            </text>
            <text x="60" y="80" textAnchor="middle" fontSize="10" fill="#57606a">
              / 100
            </text>
          </svg>
        </div>
        <div className="risk-info">
          <h3>Overall Risk Score: {riskScore}</h3>
          <div className={`risk-level risk-${riskColorName}`}>{riskLevel} Risk</div>
          <div className="risk-description">{getRiskDescription(riskScore)}</div>
        </div>
      </div>

      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-value">{metrics.total_findings || 0}</div>
          <div className="metric-label">Total Findings</div>
        </div>
        <div className="metric-card">
          <div className="metric-value metric-critical">{metrics.critical_count || 0}</div>
          <div className="metric-label">Critical</div>
        </div>
        <div className="metric-card">
          <div className="metric-value metric-high">{metrics.high_count || 0}</div>
          <div className="metric-label">High</div>
        </div>
        <div className="metric-card">
          <div className="metric-value metric-medium">{metrics.medium_count || 0}</div>
          <div className="metric-label">Medium</div>
        </div>
      </div>

      <div className="exec-section">
        <div className="section-title">🔴 Top Critical Findings</div>
        <div className="findings-list">
          {keyFindings.length > 0 ? (
            keyFindings.map((finding, idx) => (
              <div key={idx} className={`finding-item sev-${finding.severity.toLowerCase()}`}>
                <span className="finding-index">{idx + 1}.</span>
                <span className="finding-title">{finding.title}</span>
                <span className={`finding-severity sev-badge sev-${finding.severity.toLowerCase()}`}>
                  {finding.severity}
                </span>
              </div>
            ))
          ) : (
            <div className="empty-state">No critical findings detected</div>
          )}
        </div>
      </div>

      <div className="exec-section">
        <div className="section-title">📋 OWASP Top 10 Coverage</div>
        <div className="compliance-grid">
          {Object.entries(compliance).length > 0 ? (
            Object.entries(compliance)
              .sort((a, b) => b[1] - a[1])
              .slice(0, 8)
              .map(([category, percent]) => (
                <div key={category} className="compliance-item">
                  <span className="compliance-category">{category.split(":")[0]}</span>
                  <span className="compliance-percent">{percent.toFixed(0)}%</span>
                </div>
              ))
          ) : (
            <div className="empty-state full-width">No OWASP categories detected</div>
          )}
        </div>
      </div>

      <div className="exec-section">
        <div className="section-title">🔧 Remediation Roadmap (Quick Wins First)</div>
        <div className="roadmap-list">
          {roadmap.length > 0 ? (
            roadmap.slice(0, 5).map((item, idx) => (
              <div key={idx} className="roadmap-item">
                <div className="roadmap-header">
                  <span className={`roadmap-number sev-${item.severity.toLowerCase()}`}>{idx + 1}</span>
                  <span className="roadmap-title">{item.title}</span>
                  <span className={`roadmap-severity sev-${item.severity.toLowerCase()}`}>{item.severity}</span>
                </div>
                <div className="roadmap-details">
                  <span className="roadmap-impact">Impact: {item.impact}/3</span>
                  <span className="roadmap-effort">Effort: {item.effort}/3</span>
                  <span className="roadmap-ratio">Ratio: {item.ratio}</span>
                </div>
              </div>
            ))
          ) : (
            <div className="empty-state">No remediation items available</div>
          )}
        </div>
      </div>

      <div className="exec-footer">
        <p>Generated: {new Date().toLocaleString()} | VAPT Toolkit Executive Report</p>
      </div>
    </div>
  );
}

function getRiskDescription(score) {
  if (score >= 80) {
    return "Critical risk - immediate action required. Prioritize remediation of critical vulnerabilities.";
  } else if (score >= 60) {
    return "High risk - strong recommendation for immediate remediation planning and execution.";
  } else if (score >= 40) {
    return "Medium risk - develop remediation plan with clear timelines and resource allocation.";
  } else if (score >= 20) {
    return "Low risk - monitor and maintain current security posture with regular assessments.";
  } else {
    return "Minimal risk - continue current security practices with periodic reviews.";
  }
}
