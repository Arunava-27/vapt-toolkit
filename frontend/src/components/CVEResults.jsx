import SeverityBadge from "./SeverityBadge";

export default function CVEResults({ data }) {
  if (!data) return null;
  const correlations = (data.correlations || []).filter((c) => c.cves && c.cves.length > 0);

  return (
    <div className="section">
      <div className="section-header">
        <span>��</span>
        <h2>CVE Correlation</h2>
        <span className="badge-count">{data.total_cves} CVE{data.total_cves !== 1 ? "s" : ""}</span>
      </div>
      {correlations.length === 0 ? (
        <p className="none-msg">No CVEs correlated.</p>
      ) : (
        correlations.map((entry, i) => (
          <div key={i} style={{ marginBottom: "1rem" }}>
            <p style={{ fontSize: ".85rem", color: "var(--muted)", marginBottom: ".5rem" }}>
              Port <code>{entry.port}</code> — {entry.service} {entry.version}
            </p>
            <div className="tbl-wrap">
              <table>
                <thead>
                  <tr><th>CVE ID</th><th>Severity</th><th>Score</th><th>Description</th></tr>
                </thead>
                <tbody>
                  {entry.cves.map((cve, j) => (
                    <tr key={j}>
                      <td>
                        <a href={`https://nvd.nist.gov/vuln/detail/${cve.cve_id}`} target="_blank" rel="noreferrer">
                          {cve.cve_id}
                        </a>
                      </td>
                      <td><SeverityBadge severity={cve.severity} /></td>
                      <td>{cve.score}</td>
                      <td style={{ maxWidth: 400, wordBreak: "break-word" }}>{cve.description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))
      )}
    </div>
  );
}
