import React, { useMemo } from "react";
import "../App-compliance.css";

function ComplianceReport({ findings = [] }) {
  const compliance = useMemo(() => {
    if (!findings || findings.length === 0) {
      return {
        risk_score: 0,
        owasp_summary: {},
        cwe_summary: {},
        severity_distribution: {},
        compliance_frameworks: new Set(),
        total_findings: 0,
      };
    }

    // Calculate OWASP summary
    const owasp_summary = {};
    const cwe_summary = {};
    const severity_dist = { Critical: 0, High: 0, Medium: 0, Low: 0, Info: 0 };
    const compliance_set = new Set();
    let total_cvss = 0;

    findings.forEach((finding) => {
      // OWASP
      const owasp = finding.owasp_category || "Unknown";
      owasp_summary[owasp] = (owasp_summary[owasp] || 0) + 1;

      // CWE
      const cwe = finding.cwe_id || "Unknown";
      cwe_summary[cwe] = (cwe_summary[cwe] || 0) + 1;

      // Severity
      const severity = finding.severity || "Info";
      if (severity_dist.hasOwnProperty(severity)) {
        severity_dist[severity]++;
      }

      // Compliance
      if (finding.compliance_impact && Array.isArray(finding.compliance_impact)) {
        finding.compliance_impact.forEach((framework) =>
          compliance_set.add(framework)
        );
      }

      // CVSS
      if (finding.cvss_score) {
        total_cvss += finding.cvss_score;
      }
    });

    // Calculate risk score (0-100)
    const avg_cvss = total_cvss / findings.length;
    const risk_score = Math.min(100, Math.round((avg_cvss / 10) * 100 * 1.2));

    return {
      risk_score,
      owasp_summary,
      cwe_summary,
      severity_distribution: severity_dist,
      compliance_frameworks: Array.from(compliance_set).sort(),
      total_findings: findings.length,
    };
  }, [findings]);

  const get_owasp_color = (owasp_code) => {
    const colors = {
      "A01:2021": "#cf222e",
      "A02:2021": "#bc4c00",
      "A03:2021": "#d29922",
      "A04:2021": "#9a6700",
      "A05:2021": "#8256d0",
      "A06:2021": "#0969da",
      "A07:2021": "#1f6feb",
      "A08:2021": "#238636",
      "A09:2021": "#57606a",
      "A10:2021": "#bf91f3",
    };

    for (const [key, color] of Object.entries(colors)) {
      if (owasp_code && owasp_code.startsWith(key)) return color;
    }
    return "#000000";
  };

  const risk_level = (score) => {
    if (score >= 80) return "CRITICAL";
    if (score >= 60) return "HIGH";
    if (score >= 40) return "MEDIUM";
    if (score >= 20) return "LOW";
    return "INFO";
  };

  const risk_color = (score) => {
    if (score >= 80) return "#cf222e";
    if (score >= 60) return "#bc4c00";
    if (score >= 40) return "#9a6700";
    if (score >= 20) return "#1a7f37";
    return "#0969da";
  };

  return (
    <div className="compliance-report">
      {/* ─── Risk Score Banner ─── */}
      <div className="risk-banner" style={{ borderLeftColor: risk_color(compliance.risk_score) }}>
        <div className="risk-score-container">
          <div className="risk-score-display">
            <div
              className="risk-score-number"
              style={{ color: risk_color(compliance.risk_score) }}
            >
              {compliance.risk_score}
            </div>
            <div className="risk-score-label">Risk Score</div>
          </div>
          <div className="risk-level-badge" style={{ backgroundColor: risk_color(compliance.risk_score) }}>
            {risk_level(compliance.risk_score)}
          </div>
        </div>
        <div className="risk-details">
          <p>{compliance.total_findings} findings identified</p>
          <p>
            {compliance.severity_distribution.Critical || 0} Critical •
            {compliance.severity_distribution.High || 0} High •
            {compliance.severity_distribution.Medium || 0} Medium
          </p>
        </div>
      </div>

      {/* ─── OWASP Top 10 Breakdown ─── */}
      <div className="section">
        <h3 className="section-title">📋 OWASP Top 10 2021</h3>
        <div className="owasp-grid">
          {Object.entries(compliance.owasp_summary)
            .sort((a, b) => b[1] - a[1])
            .map(([owasp, count]) => (
              <div
                key={owasp}
                className="owasp-item"
                style={{ borderLeftColor: get_owasp_color(owasp) }}
              >
                <div className="owasp-header">
                  <span className="owasp-code">{owasp.split("-")[0]}</span>
                  <span className="owasp-count">{count}</span>
                </div>
                <div className="owasp-description">
                  {owasp.split("-").slice(1).join("-").trim()}
                </div>
              </div>
            ))}
        </div>
      </div>

      {/* ─── Severity Distribution ─── */}
      <div className="section severity-section">
        <h3 className="section-title">⚠️ Severity Distribution</h3>
        <div className="severity-bars">
          {[
            { level: "Critical", count: compliance.severity_distribution.Critical, color: "#cf222e" },
            { level: "High", count: compliance.severity_distribution.High, color: "#bc4c00" },
            { level: "Medium", count: compliance.severity_distribution.Medium, color: "#9a6700" },
            { level: "Low", count: compliance.severity_distribution.Low, color: "#1a7f37" },
            { level: "Info", count: compliance.severity_distribution.Info, color: "#0969da" },
          ].map(({ level, count, color }) => (
            <div key={level} className="severity-bar-item">
              <div className="severity-label">{level}</div>
              <div className="severity-bar-container">
                <div
                  className="severity-bar"
                  style={{
                    backgroundColor: color,
                    width: `${Math.max(20, (count / compliance.total_findings) * 100)}%`,
                  }}
                />
              </div>
              <div className="severity-count">{count || 0}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ─── CWE References ─── */}
      <div className="section">
        <h3 className="section-title">🔍 CWE (Common Weakness Enumeration)</h3>
        <div className="cwe-list">
          {Object.entries(compliance.cwe_summary)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 15)
            .map(([cwe, count]) => (
              <div key={cwe} className="cwe-item">
                <span className="cwe-id">{cwe}</span>
                <span className="cwe-count">{count} finding{count > 1 ? "s" : ""}</span>
              </div>
            ))}
        </div>
      </div>

      {/* ─── Compliance Frameworks ─── */}
      {compliance.compliance_frameworks.length > 0 && (
        <div className="section">
          <h3 className="section-title">✅ Compliance Impact</h3>
          <div className="compliance-frameworks">
            {compliance.compliance_frameworks.map((framework) => (
              <span key={framework} className="framework-badge">
                {framework}
              </span>
            ))}
          </div>
          <p className="compliance-note">
            These findings may impact compliance with the above frameworks.
            Remediation required to maintain compliance.
          </p>
        </div>
      )}
    </div>
  );
}

export default ComplianceReport;
