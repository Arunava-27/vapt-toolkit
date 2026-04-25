import { useState } from "react";
import SeverityBadge from "./SeverityBadge";
import { WebCharts } from "./ScanCharts";
import CollapsibleTable from "./CollapsibleTable";

export default function WebResults({ data, collapsibleTables = false }) {
  const [expandedRows, setExpandedRows] = useState(new Set());

  if (!data) return null;
  const findings = data.findings || [];

  const toggleRow = (idx) => {
    const newSet = new Set(expandedRows);
    if (newSet.has(idx)) newSet.delete(idx);
    else newSet.add(idx);
    setExpandedRows(newSet);
  };

  const FindingRow = ({ f, idx, isExpanded }) => (
    <>
      <tr
        key={`row-${idx}`}
        onClick={() => toggleRow(idx)}
        style={{ cursor: "pointer", backgroundColor: isExpanded ? "#f6f8fa" : undefined }}
      >
        <td>{f.type}</td>
        <td><SeverityBadge severity={f.severity} /></td>
        <td><code>{f.parameter}</code></td>
        <td><code>{f.payload?.substring(0, 30)}...</code></td>
        <td>{f.evidence?.substring(0, 40)}...</td>
        <td style={{ maxWidth: 260, wordBreak: "break-all", fontSize: ".8rem" }}>
          {f.location}
          <div style={{ fontSize: "0.7rem", color: "#57606a", marginTop: "0.25rem" }}>
            {f.cwe_id && `${f.cwe_id} • `}
            {f.cvss_score && `CVSS: ${f.cvss_score.toFixed(1)}/10`}
          </div>
        </td>
      </tr>
      {isExpanded && (
        <tr key={`details-${idx}`} style={{ backgroundColor: "#fafbfc" }}>
          <td colSpan="6" style={{ padding: "1rem" }}>
            <div style={{ fontSize: "0.875rem" }}>
              {f.owasp_category && (
                <div style={{ marginBottom: "0.75rem" }}>
                  <strong>OWASP:</strong> {f.owasp_category}
                </div>
              )}
              {f.cwe_id && (
                <div style={{ marginBottom: "0.75rem" }}>
                  <strong>CWE-ID:</strong> {f.cwe_id}
                </div>
              )}
              {f.cvss_score && (
                <div style={{ marginBottom: "0.75rem" }}>
                  <strong>CVSS v3.1:</strong> {f.cvss_score.toFixed(1)}/10.0
                </div>
              )}
              {f.compliance_impact && f.compliance_impact.length > 0 && (
                <div style={{ marginBottom: "0.75rem" }}>
                  <strong>Compliance Impact:</strong> {f.compliance_impact.join(", ")}
                </div>
              )}
              {f.remediation_tips && f.remediation_tips.length > 0 && (
                <div style={{ marginBottom: "0.75rem" }}>
                  <strong>Remediation:</strong>
                  <ul style={{ margin: "0.5rem 0", paddingLeft: "1.5rem" }}>
                    {f.remediation_tips.slice(0, 3).map((tip, i) => (
                      <li key={i}>{tip}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  );

  return (
    <div className="section">
      <div className="section-header">
        <span>🕸️</span>
        <h2>Web Vulnerabilities</h2>
        <span className="badge-count">{findings.length} finding{findings.length !== 1 ? "s" : ""}</span>
      </div>

      {/* Charts */}
      <WebCharts data={data} />

      {findings.length === 0 ? (
        <p className="none-msg">No web vulnerabilities detected.</p>
      ) : collapsibleTables ? (
        <CollapsibleTable title="Findings" countLabel={`${findings.length} row${findings.length !== 1 ? "s" : ""}`}>
          <div className="tbl-wrap">
            <table>
              <thead>
                <tr><th>Type</th><th>Severity</th><th>Parameter</th><th>Payload</th><th>Evidence</th><th>Location</th></tr>
              </thead>
              <tbody>
                {findings.map((f, i) => (
                  <FindingRow key={i} f={f} idx={i} isExpanded={expandedRows.has(i)} />
                ))}
              </tbody>
            </table>
          </div>
        </CollapsibleTable>
      ) : (
        <div className="tbl-wrap">
          <table>
            <thead>
              <tr><th>Type</th><th>Severity</th><th>Parameter</th><th>Payload</th><th>Evidence</th><th>Location</th></tr>
            </thead>
            <tbody>
              {findings.map((f, i) => (
                <FindingRow key={i} f={f} idx={i} isExpanded={expandedRows.has(i)} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
