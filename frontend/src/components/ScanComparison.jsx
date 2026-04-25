import { useState, useEffect } from "react";
import SeverityBadge from "./SeverityBadge";

export default function ScanComparison({ scan1Id, scan2Id, onClose }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [activeTab, setActiveTab] = useState("new");
  const [expandedRows, setExpandedRows] = useState(new Set());
  const [filterSeverity, setFilterSeverity] = useState(null);
  const [filterType, setFilterType] = useState(null);

  useEffect(() => {
    fetchComparison();
  }, [scan1Id, scan2Id]);

  const fetchComparison = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/compare/scans", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scan_id_1: scan1Id,
          scan_id_2: scan2Id,
          severity_filter: filterSeverity ? [filterSeverity] : null,
          finding_types: filterType ? [filterType] : null,
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setComparison(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const toggleRow = (idx) => {
    const newSet = new Set(expandedRows);
    if (newSet.has(idx)) newSet.delete(idx);
    else newSet.add(idx);
    setExpandedRows(newSet);
  };

  const downloadReport = async () => {
    if (!comparison) return;
    try {
      const csv = generateCSVReport(comparison);
      const blob = new Blob([csv], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `scan-comparison-${Date.now()}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert("Failed to download report: " + err.message);
    }
  };

  const generateCSVReport = (data) => {
    let csv = "Scan Comparison Report\n";
    csv += `Generated: ${new Date().toISOString()}\n`;
    csv += `Scan 1 ID,${data.scan_1_id}\n`;
    csv += `Scan 2 ID,${data.scan_2_id}\n`;
    csv += `Risk Delta,${data.risk_delta.toFixed(2)}\n`;
    csv += `Trend,${data.risk_trend}\n\n`;

    csv += "New Findings\n";
    csv += "Type,Severity,Confidence,URL,Parameter\n";
    data.new_findings.forEach((f) => {
      csv += `"${f.finding_type}","${f.severity}","${f.confidence_score}","${f.url}","${f.parameter}"\n`;
    });

    csv += "\nFixed Findings\n";
    csv += "Type,Severity,Confidence,URL,Parameter\n";
    data.fixed_findings.forEach((f) => {
      csv += `"${f.finding_type}","${f.severity}","${f.confidence_score}","${f.url}","${f.parameter}"\n`;
    });

    csv += "\nRegressions\n";
    csv += "Type,Severity,Confidence,URL,Parameter\n";
    data.regressions.forEach((f) => {
      csv += `"${f.finding_type}","${f.severity}","${f.confidence_score}","${f.url}","${f.parameter}"\n`;
    });

    return csv;
  };

  if (loading) return <div style={{ padding: "2rem", textAlign: "center" }}>Loading comparison...</div>;
  if (error) return <div style={{ padding: "2rem", color: "red" }}>Error: {error}</div>;
  if (!comparison) return <div style={{ padding: "2rem" }}>No comparison data</div>;

  const currentFindings = 
    activeTab === "new" ? comparison.new_findings :
    activeTab === "fixed" ? comparison.fixed_findings :
    activeTab === "unchanged" ? comparison.unchanged_findings :
    comparison.regressions;

  const filteredFindings = currentFindings.filter((f) => {
    if (filterSeverity && f.severity !== filterSeverity) return false;
    if (filterType && f.finding_type !== filterType) return false;
    return true;
  });

  const FindingRow = ({ f, idx, status }) => {
    const isExpanded = expandedRows.has(idx);
    const bgColor = 
      status === "new" ? "#dcfce7" :
      status === "fixed" ? "#fee2e2" :
      status === "regression" ? "#fef3c7" :
      "transparent";

    return (
      <>
        <tr
          onClick={() => toggleRow(idx)}
          style={{
            cursor: "pointer",
            backgroundColor: isExpanded ? bgColor : "white",
            borderLeft: `4px solid ${status === "new" ? "#22c55e" : status === "fixed" ? "#ef4444" : status === "regression" ? "#f59e0b" : "#6b7280"}`,
          }}
        >
          <td style={{ fontWeight: 500 }}>{f.finding_type}</td>
          <td><SeverityBadge severity={f.severity} /></td>
          <td style={{ fontSize: "0.875rem", color: "#57606a" }}>{f.confidence_score}%</td>
          <td style={{ maxWidth: 250, wordBreak: "break-word", fontSize: "0.875rem" }}>
            <code>{f.url}</code>
          </td>
          <td style={{ fontSize: "0.875rem" }}><code>{f.parameter || "—"}</code></td>
          <td style={{ fontSize: "0.875rem", color: "#57606a" }}>{f.method || "GET"}</td>
        </tr>
        {isExpanded && (
          <tr style={{ backgroundColor: bgColor, opacity: 0.7 }}>
            <td colSpan="6" style={{ padding: "1rem" }}>
              <div style={{ fontSize: "0.875rem", color: "#1f2937" }}>
                {f.endpoint && (
                  <div style={{ marginBottom: "0.5rem" }}>
                    <strong>Endpoint:</strong> {f.endpoint}
                  </div>
                )}
                {f.payload && (
                  <div style={{ marginBottom: "0.5rem" }}>
                    <strong>Payload:</strong>
                    <pre style={{ background: "#f3f4f6", padding: "0.5rem", borderRadius: "0.25rem", overflow: "auto" }}>
                      {f.payload}
                    </pre>
                  </div>
                )}
                {f.evidence && (
                  <div style={{ marginBottom: "0.5rem" }}>
                    <strong>Evidence:</strong> {f.evidence}
                  </div>
                )}
                {f.appeared_in_scan && (
                  <div style={{ marginBottom: "0.5rem" }}>
                    <strong>Scan ID:</strong> {f.appeared_in_scan}
                  </div>
                )}
              </div>
            </td>
          </tr>
        )}
      </>
    );
  };

  return (
    <div style={{ padding: "2rem", maxWidth: "1400px", margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem" }}>
        <div>
          <h1 style={{ margin: 0, fontSize: "1.875rem", fontWeight: "bold" }}>Scan Comparison</h1>
          <p style={{ margin: "0.5rem 0 0 0", color: "#57606a" }}>
            Baseline: <code>{comparison.scan_1_id.substring(0, 8)}...</code> vs Current: <code>{comparison.scan_2_id.substring(0, 8)}...</code>
          </p>
        </div>
        <button
          onClick={onClose}
          style={{
            background: "none",
            border: "none",
            fontSize: "1.5rem",
            cursor: "pointer",
            color: "#57606a",
          }}
        >
          ✕
        </button>
      </div>

      {/* Risk Summary Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: "1rem", marginBottom: "2rem" }}>
        <div style={{ background: "#f6f8fa", padding: "1.5rem", borderRadius: "0.5rem", border: "1px solid #e5e7eb" }}>
          <div style={{ fontSize: "0.875rem", color: "#57606a", marginBottom: "0.5rem" }}>Risk Score (Scan 1)</div>
          <div style={{ fontSize: "2rem", fontWeight: "bold", color: "#1f2937" }}>{comparison.scan_1_risk_score.toFixed(1)}</div>
        </div>
        <div style={{ background: "#f6f8fa", padding: "1.5rem", borderRadius: "0.5rem", border: "1px solid #e5e7eb" }}>
          <div style={{ fontSize: "0.875rem", color: "#57606a", marginBottom: "0.5rem" }}>Risk Score (Scan 2)</div>
          <div style={{ fontSize: "2rem", fontWeight: "bold", color: "#1f2937" }}>{comparison.scan_2_risk_score.toFixed(1)}</div>
        </div>
        <div style={{ background: comparison.risk_delta < 0 ? "#dcfce7" : "#fee2e2", padding: "1.5rem", borderRadius: "0.5rem", border: "1px solid #e5e7eb" }}>
          <div style={{ fontSize: "0.875rem", color: "#57606a", marginBottom: "0.5rem" }}>Risk Delta</div>
          <div style={{ fontSize: "2rem", fontWeight: "bold", color: comparison.risk_delta < 0 ? "#22c55e" : "#ef4444" }}>
            {comparison.risk_delta > 0 ? "+" : ""}{comparison.risk_delta.toFixed(1)}
          </div>
          <div style={{ fontSize: "0.75rem", color: "#57606a", marginTop: "0.25rem" }}>Trend: {comparison.risk_trend}</div>
        </div>
      </div>

      {/* Vulnerability Summary */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "1rem", marginBottom: "2rem" }}>
        <div style={{ background: "#dcfce7", padding: "1rem", borderRadius: "0.5rem", border: "1px solid #86efac" }}>
          <div style={{ fontSize: "0.75rem", color: "#15803d", fontWeight: "bold", marginBottom: "0.25rem" }}>NEW FINDINGS</div>
          <div style={{ fontSize: "1.5rem", fontWeight: "bold", color: "#22c55e" }}>{comparison.new_findings.length}</div>
        </div>
        <div style={{ background: "#fee2e2", padding: "1rem", borderRadius: "0.5rem", border: "1px solid #fca5a5" }}>
          <div style={{ fontSize: "0.75rem", color: "#b91c1c", fontWeight: "bold", marginBottom: "0.25rem" }}>FIXED FINDINGS</div>
          <div style={{ fontSize: "1.5rem", fontWeight: "bold", color: "#ef4444" }}>{comparison.fixed_findings.length}</div>
        </div>
        <div style={{ background: "#fef3c7", padding: "1rem", borderRadius: "0.5rem", border: "1px solid #fde047" }}>
          <div style={{ fontSize: "0.75rem", color: "#b45309", fontWeight: "bold", marginBottom: "0.25rem" }}>REGRESSIONS</div>
          <div style={{ fontSize: "1.5rem", fontWeight: "bold", color: "#f59e0b" }}>{comparison.regressions.length}</div>
        </div>
        <div style={{ background: "#f3f4f6", padding: "1rem", borderRadius: "0.5rem", border: "1px solid #d1d5db" }}>
          <div style={{ fontSize: "0.75rem", color: "#374151", fontWeight: "bold", marginBottom: "0.25rem" }}>UNCHANGED FINDINGS</div>
          <div style={{ fontSize: "1.5rem", fontWeight: "bold", color: "#6b7280" }}>{comparison.unchanged_findings.length}</div>
        </div>
      </div>

      {/* Regression Alert */}
      {comparison.regressions.length > 0 && (
        <div style={{ background: "#fef3c7", border: "2px solid #f59e0b", borderRadius: "0.5rem", padding: "1rem", marginBottom: "2rem" }}>
          <div style={{ fontSize: "0.875rem", fontWeight: "bold", color: "#b45309", marginBottom: "0.5rem" }}>
            ⚠️ {comparison.regressions.length} Regression{comparison.regressions.length !== 1 ? "s" : ""} Detected
          </div>
          <p style={{ margin: 0, fontSize: "0.875rem", color: "#92400e" }}>
            {comparison.regressions.length} vulnerability/vulnerabilities that were previously fixed have reappeared.
          </p>
        </div>
      )}

      {/* Severity Distribution */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "2rem" }}>
        <div style={{ background: "#f6f8fa", padding: "1.5rem", borderRadius: "0.5rem", border: "1px solid #e5e7eb" }}>
          <h3 style={{ margin: "0 0 1rem 0", fontSize: "0.875rem", fontWeight: "bold", color: "#1f2937" }}>Scan 1 Severity Distribution</h3>
          {Object.entries(comparison.severity_distribution_1).map(([severity, count]) => (
            count > 0 && (
              <div key={severity} style={{ display: "flex", justifyContent: "space-between", fontSize: "0.875rem", marginBottom: "0.5rem" }}>
                <span>{severity}</span>
                <span style={{ fontWeight: "bold" }}>{count}</span>
              </div>
            )
          ))}
        </div>
        <div style={{ background: "#f6f8fa", padding: "1.5rem", borderRadius: "0.5rem", border: "1px solid #e5e7eb" }}>
          <h3 style={{ margin: "0 0 1rem 0", fontSize: "0.875rem", fontWeight: "bold", color: "#1f2937" }}>Scan 2 Severity Distribution</h3>
          {Object.entries(comparison.severity_distribution_2).map(([severity, count]) => (
            count > 0 && (
              <div key={severity} style={{ display: "flex", justifyContent: "space-between", fontSize: "0.875rem", marginBottom: "0.5rem" }}>
                <span>{severity}</span>
                <span style={{ fontWeight: "bold" }}>{count}</span>
              </div>
            )
          ))}
        </div>
      </div>

      {/* Tabs and Filters */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem", borderBottom: "1px solid #e5e7eb", paddingBottom: "1rem" }}>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          {["new", "fixed", "regression", "unchanged"].map((tab) => {
            const counts = {
              new: comparison.new_findings.length,
              fixed: comparison.fixed_findings.length,
              regression: comparison.regressions.length,
              unchanged: comparison.unchanged_findings.length,
            };
            return (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                style={{
                  padding: "0.5rem 1rem",
                  background: activeTab === tab ? "#3b82f6" : "#e5e7eb",
                  color: activeTab === tab ? "white" : "#374151",
                  border: "none",
                  borderRadius: "0.25rem",
                  cursor: "pointer",
                  fontSize: "0.875rem",
                  fontWeight: activeTab === tab ? "bold" : "normal",
                }}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)} ({counts[tab]})
              </button>
            );
          })}
        </div>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <select
            value={filterSeverity || ""}
            onChange={(e) => setFilterSeverity(e.target.value || null)}
            style={{ padding: "0.5rem", borderRadius: "0.25rem", border: "1px solid #d1d5db" }}
          >
            <option value="">All Severities</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
            <option value="Info">Info</option>
          </select>
          <button
            onClick={downloadReport}
            style={{
              padding: "0.5rem 1rem",
              background: "#10b981",
              color: "white",
              border: "none",
              borderRadius: "0.25rem",
              cursor: "pointer",
              fontSize: "0.875rem",
            }}
          >
            ↓ Download CSV
          </button>
        </div>
      </div>

      {/* Findings Table */}
      <div style={{ overflowX: "auto", border: "1px solid #e5e7eb", borderRadius: "0.5rem", background: "white" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ background: "#f9fafb", borderBottom: "1px solid #e5e7eb" }}>
              <th style={{ padding: "0.75rem", textAlign: "left", fontSize: "0.875rem", fontWeight: "bold", color: "#374151" }}>Type</th>
              <th style={{ padding: "0.75rem", textAlign: "left", fontSize: "0.875rem", fontWeight: "bold", color: "#374151" }}>Severity</th>
              <th style={{ padding: "0.75rem", textAlign: "left", fontSize: "0.875rem", fontWeight: "bold", color: "#374151" }}>Confidence</th>
              <th style={{ padding: "0.75rem", textAlign: "left", fontSize: "0.875rem", fontWeight: "bold", color: "#374151" }}>URL</th>
              <th style={{ padding: "0.75rem", textAlign: "left", fontSize: "0.875rem", fontWeight: "bold", color: "#374151" }}>Parameter</th>
              <th style={{ padding: "0.75rem", textAlign: "left", fontSize: "0.875rem", fontWeight: "bold", color: "#374151" }}>Method</th>
            </tr>
          </thead>
          <tbody>
            {filteredFindings.length === 0 ? (
              <tr>
                <td colSpan="6" style={{ padding: "2rem", textAlign: "center", color: "#57606a", fontSize: "0.875rem" }}>
                  No findings in this category
                </td>
              </tr>
            ) : (
              filteredFindings.map((f, idx) => (
                <FindingRow key={idx} f={f} idx={idx} status={activeTab === "regression" ? "regression" : activeTab} />
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
