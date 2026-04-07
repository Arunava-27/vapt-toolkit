export default function PortResults({ data }) {
  if (!data) return null;
  const ports = data.open_ports || [];
  return (
    <div className="section">
      <div className="section-header">
        <span>🚪</span>
        <h2>Open Ports</h2>
        <span className="badge-count">{ports.length} port{ports.length !== 1 ? "s" : ""}</span>
      </div>
      {ports.length === 0 ? (
        <p className="none-msg">No open ports found.</p>
      ) : (
        <div className="tbl-wrap">
          <table>
            <thead><tr><th>Port</th><th>Service</th><th>Product / Version</th></tr></thead>
            <tbody>
              {ports.map((p, i) => (
                <tr key={i}>
                  <td><code>{p.port}</code></td>
                  <td>{p.service || "—"}</td>
                  <td>{[p.product, p.version].filter(Boolean).join(" ") || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
