import SeverityBadge from "./SeverityBadge";

export default function WebResults({ data }) {
  if (!data) return null;
  const findings = data.findings || [];
  return (
    <div className="section">
      <div className="section-header">
        <span>🕸️</span>
        <h2>Web Vulnerabilities</h2>
        <span className="badge-count">{findings.length} finding{findings.length !== 1 ? "s" : ""}</span>
      </div>
      {findings.length === 0 ? (
        <p className="none-msg">No web vulnerabilities detected.</p>
      ) : (
        <div className="tbl-wrap">
          <table>
            <thead>
              <tr><th>Type</th><th>Severity</th><th>Parameter</th><th>Payload</th><th>Evidence</th><th>Location</th></tr>
            </thead>
            <tbody>
              {findings.map((f, i) => (
                <tr key={i}>
                  <td>{f.type}</td>
                  <td><SeverityBadge severity={f.severity} /></td>
                  <td><code>{f.parameter}</code></td>
                  <td><code>{f.payload}</code></td>
                  <td>{f.evidence}</td>
                  <td style={{ maxWidth: 260, wordBreak: "break-all", fontSize: ".8rem" }}>{f.location}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
