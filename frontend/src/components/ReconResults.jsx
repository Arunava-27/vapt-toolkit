function CdnBadge({ cdn }) {
  if (!cdn) return <span className="badge-direct" title="Direct server (no CDN detected)">Direct</span>;
  return <span className="badge-cdn" title={`Behind CDN: ${cdn}`}>CDN · {cdn}</span>;
}

export default function ReconResults({ data }) {
  if (!data) return null;
  const subs   = data.subdomains || [];
  const root   = data.root || {};
  const direct = subs.filter(s => !s.cdn).length;
  const behind = subs.filter(s =>  s.cdn).length;

  return (
    <div className="section">
      <div className="section-header">
        <span>🔍</span>
        <h2>Reconnaissance</h2>
        <span className="badge-count">{subs.length} subdomain{subs.length !== 1 ? "s" : ""}</span>
        {data.passive_found > 0 && (
          <span className="badge-passive" title="Discovered via crt.sh / HackerTarget / RapidDNS">
            {data.passive_found} passive
          </span>
        )}
      </div>

      {/* Root domain info */}
      {(root.ns?.length > 0 || root.mx?.length > 0 || root.a?.length > 0) && (
        <div className="root-info">
          {root.a?.length  > 0 && <span><b>Root A:</b> {root.a.join(", ")}</span>}
          {root.ns?.length > 0 && <span><b>NS:</b> {root.ns.join(", ")}</span>}
          {root.mx?.length > 0 && <span><b>MX:</b> {root.mx.join(", ")}</span>}
        </div>
      )}

      {/* CDN summary */}
      {subs.length > 0 && (
        <div className="cdn-summary">
          <span className="badge-direct">{direct} direct</span>
          <span className="badge-cdn">{behind} behind CDN</span>
        </div>
      )}

      {subs.length === 0 ? (
        <p className="none-msg">No subdomains discovered.</p>
      ) : (
        <div className="tbl-wrap">
          <table>
            <thead>
              <tr>
                <th>Subdomain</th>
                <th>IPv4</th>
                <th>IPv6</th>
                <th>CNAME Chain</th>
                <th>CDN / Hosting</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {subs.map((s, i) => (
                <tr key={i} className={s.cdn ? "row-cdn" : "row-direct"}>
                  <td><code>{s.subdomain}</code></td>
                  <td>{(s.ipv4 || s.ips || []).join(", ") || "—"}</td>
                  <td>{(s.ipv6 || []).join(", ") || "—"}</td>
                  <td>
                    {(s.cname || []).length > 0
                      ? <code className="cname-chain">{(s.cname || []).join(" → ")}</code>
                      : "—"}
                  </td>
                  <td><CdnBadge cdn={s.cdn} /></td>
                  <td><span className="source-tag">{s.source || "brute"}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
