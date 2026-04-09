import { useState } from "react";
import { PortCharts } from "./ScanCharts";

function ProtoTag({ proto }) {
  return (
    <span className={`proto-tag proto-${proto?.toLowerCase()}`}>{proto || "TCP"}</span>
  );
}

function ScriptOutput({ scripts }) {
  const [open, setOpen] = useState(false);
  const entries = Object.entries(scripts || {});
  if (!entries.length) return null;
  return (
    <div className="script-block">
      <button className="script-toggle" onClick={() => setOpen(!open)}>
        {open ? "▾" : "▸"} {entries.length} script{entries.length > 1 ? "s" : ""}
      </button>
      {open && (
        <div className="script-outputs">
          {entries.map(([id, out]) => (
            <div key={id} className="script-entry">
              <div className="script-id">{id}</div>
              <pre className="script-out">{out}</pre>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function PortResults({ data }) {
  if (!data) return null;
  const ports    = data.open_ports  || [];
  const os       = data.os_info     || {};
  const host     = data.host_info   || {};
  const trace    = data.traceroute  || [];

  return (
    <div className="section">
      <div className="section-header">
        <span>🚪</span>
        <h2>Port Scan</h2>
        <span className="badge-count">{ports.length} open</span>
        {data.scan_args && (
          <code className="scan-args-badge" title={data.scan_args}>
            nmap {data.scan_args.split(" ").slice(0, 4).join(" ")}…
          </code>
        )}
      </div>

      {/* ── Charts ── */}
      <PortCharts data={data} />

      {/* ── Host info ── */}
      {(host.hostname || host.mac || host.vendor) && (
        <div className="host-info-bar">
          {host.hostname && <span><b>Hostname:</b> {host.hostname}</span>}
          {host.mac      && <span><b>MAC:</b> {host.mac}</span>}
          {host.vendor   && <span><b>Vendor:</b> {host.vendor}</span>}
          <span><b>State:</b> {host.state}</span>
        </div>
      )}

      {/* ── OS detection ── */}
      {os.name && (
        <div className="os-block">
          <div className="os-header">
            <span className="os-icon">🖥️</span>
            <span className="os-name">{os.name}</span>
            <span className={`os-acc acc-${os.accuracy >= 90 ? "high" : os.accuracy >= 70 ? "med" : "low"}`}>
              {os.accuracy}% confidence
            </span>
            {os.osfamily && <span className="os-tag">{os.osfamily}{os.osgen ? " " + os.osgen : ""}</span>}
            {os.cpe && <code className="os-cpe">{os.cpe}</code>}
          </div>
          {os.all_matches?.length > 1 && (
            <details className="os-alts">
              <summary>{os.all_matches.length - 1} other candidate{os.all_matches.length > 2 ? "s" : ""}</summary>
              <ul>
                {os.all_matches.slice(1).map((m, i) => (
                  <li key={i}>{m.name} — {m.accuracy}%</li>
                ))}
              </ul>
            </details>
          )}
        </div>
      )}

      {/* ── Ports table ── */}
      {ports.length === 0 ? (
        <p className="none-msg">No open ports found.</p>
      ) : (
        <div className="tbl-wrap">
          <table>
            <thead>
              <tr>
                <th>Port</th>
                <th>Proto</th>
                <th>Service</th>
                <th>Product / Version</th>
                <th>Extra Info</th>
                <th>CPE</th>
                <th>Scripts</th>
              </tr>
            </thead>
            <tbody>
              {ports.map((p, i) => (
                <tr key={i}>
                  <td><code>{p.port}</code></td>
                  <td><ProtoTag proto={p.proto} /></td>
                  <td>{p.service || "—"}</td>
                  <td>
                    {[p.product, p.version].filter(Boolean).join(" ") || "—"}
                    {p.extrainfo && <span className="extra-info"> ({p.extrainfo})</span>}
                  </td>
                  <td><span className="extra-info">{p.extrainfo || "—"}</span></td>
                  <td>{p.cpe ? <code className="cpe-tag">{p.cpe}</code> : "—"}</td>
                  <td><ScriptOutput scripts={p.scripts} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ── Traceroute ── */}
      {trace.length > 0 && (
        <details className="trace-block">
          <summary>Traceroute — {trace.length} hop{trace.length > 1 ? "s" : ""}</summary>
          <div className="tbl-wrap" style={{ marginTop: ".5rem" }}>
            <table>
              <thead><tr><th>Hop</th><th>IP</th><th>RTT</th></tr></thead>
              <tbody>
                {trace.map((t, i) => (
                  <tr key={i}>
                    <td>{t.hop}</td>
                    <td><code>{t.ip || "*"}</code></td>
                    <td>{t.rtt ? `${t.rtt} ms` : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      )}
    </div>
  );
}
