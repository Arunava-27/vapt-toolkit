import { useState } from "react";
import SeverityBadge from "./SeverityBadge";
import { CVECharts } from "./ScanCharts";
import CollapsibleTable from "./CollapsibleTable";

const SOURCE_COLORS = {
  NVD:       { bg: "#1f3c5e", fg: "#58a6ff" },
  CIRCL:     { bg: "#2d2041", fg: "#bf91f3" },
  GitHub:    { bg: "#1b2f23", fg: "#3fb950" },
  ExploitDB: { bg: "#3d1a1a", fg: "#f85149" },
};

function SourceBadge({ source }) {
  const parts = source.split(", ");
  return (
    <span style={{ display: "inline-flex", gap: "3px", flexWrap: "wrap" }}>
      {parts.map((s) => {
        const key = Object.keys(SOURCE_COLORS).find((k) => s.includes(k)) || "NVD";
        const { bg, fg } = SOURCE_COLORS[key];
        return (
          <span key={s} style={{
            background: bg, color: fg,
            fontSize: ".65rem", fontWeight: 700,
            padding: "1px 6px", borderRadius: 10,
            letterSpacing: ".04em", whiteSpace: "nowrap",
          }}>{s}</span>
        );
      })}
    </span>
  );
}

function ExploitLinks({ exploits }) {
  if (!exploits || exploits.length === 0) return <span style={{ color: "var(--muted)", fontSize: ".75rem" }}>—</span>;
  return (
    <span style={{ display: "flex", flexDirection: "column", gap: 2 }}>
      {exploits.map((url, i) => (
        <a key={i} href={url} target="_blank" rel="noreferrer"
           style={{ fontSize: ".75rem", color: "var(--red)" }}>
          💥 {url.replace(/^https?:\/\//, "").slice(0, 40)}
        </a>
      ))}
    </span>
  );
}

export default function CVEResults({ data, collapsibleTables = false }) {
  const [sourceFilter, setSourceFilter] = useState("all");
  if (!data) return null;

  const sourcesUsed = data.sources_used || ["NVD"];
  const correlations = (data.correlations || []).filter((c) => c.cves && c.cves.length > 0);
  const hasExploits = correlations.some((c) => c.cves.some((v) => v.exploits?.length > 0));

  const filterCves = (cves) => {
    if (sourceFilter === "all") return cves;
    if (sourceFilter === "exploits") return cves.filter((v) => v.exploits?.length > 0);
    return cves.filter((v) => v.source?.includes(sourceFilter));
  };

  return (
    <div className="section">
      <div className="section-header">
        <span>🛡️</span>
        <h2>CVE Correlation</h2>
        <span className="badge-count">{data.total_cves} CVE{data.total_cves !== 1 ? "s" : ""}</span>
      </div>

      {/* Charts */}
      <CVECharts data={data} />

      {/* Sources used */}
      <div style={{ display: "flex", gap: 6, marginBottom: "0.75rem", flexWrap: "wrap", alignItems: "center" }}>
        <span style={{ fontSize: ".75rem", color: "var(--muted)" }}>Sources:</span>
        {sourcesUsed.map((s) => <SourceBadge key={s} source={s} />)}
        {data.searchsploit_available === false && (
          <span style={{ fontSize: ".7rem", color: "var(--muted)", fontStyle: "italic" }}>
            (SearchSploit not installed)
          </span>
        )}
      </div>

      {/* Filter pills */}
      <div style={{ display: "flex", gap: 6, marginBottom: "1rem", flexWrap: "wrap" }}>
        {["all", ...sourcesUsed, ...(hasExploits ? ["exploits"] : [])].map((f) => (
          <button key={f} className={`pill ${sourceFilter === f ? "active" : ""}`}
            onClick={() => setSourceFilter(f)}
            style={{ textTransform: "capitalize", fontSize: ".75rem" }}>
            {f === "exploits" ? "💥 Has Exploits" : f}
          </button>
        ))}
      </div>

      {correlations.length === 0 ? (
        <p className="none-msg">No CVEs correlated.</p>
      ) : (
        correlations.map((entry, i) => {
          const filtered = filterCves(entry.cves);
          if (filtered.length === 0) return null;
          const serviceLabel = [entry.service, entry.version].filter(Boolean).join(" ");
          const tableTitle = `Port ${entry.port}${serviceLabel ? ` — ${serviceLabel}` : ""}`;
          return (
            <div key={i} style={{ marginBottom: "1.25rem" }}>
              {collapsibleTables ? (
                <CollapsibleTable
                  title={tableTitle}
                  countLabel={`${filtered.length} result${filtered.length !== 1 ? "s" : ""}`}
                >
                  <div className="tbl-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>ID</th>
                          <th>Source</th>
                          <th>Severity</th>
                          <th>Score</th>
                          <th>Description</th>
                          <th>Exploits</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filtered.map((cve, j) => (
                          <tr key={j}>
                            <td>
                              <a href={(cve.references || [])[0] || `https://nvd.nist.gov/vuln/detail/${cve.cve_id}`}
                                 target="_blank" rel="noreferrer" style={{ whiteSpace: "nowrap" }}>
                                {cve.cve_id}
                              </a>
                            </td>
                            <td><SourceBadge source={cve.source || "NVD"} /></td>
                            <td><SeverityBadge severity={cve.severity} /></td>
                            <td>{cve.score}</td>
                            <td style={{ maxWidth: 340, wordBreak: "break-word", fontSize: ".8rem" }}>
                              {cve.description}
                            </td>
                            <td><ExploitLinks exploits={cve.exploits} /></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CollapsibleTable>
              ) : (
                <>
                  <p style={{ fontSize: ".85rem", color: "var(--muted)", marginBottom: ".5rem" }}>
                    Port <code>{entry.port}</code> — {entry.service} {entry.version}
                    <span style={{ marginLeft: 8, color: "var(--fg)", fontSize: ".75rem" }}>
                      ({filtered.length} result{filtered.length !== 1 ? "s" : ""})
                    </span>
                  </p>
                  <div className="tbl-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>ID</th>
                          <th>Source</th>
                          <th>Severity</th>
                          <th>Score</th>
                          <th>Description</th>
                          <th>Exploits</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filtered.map((cve, j) => (
                          <tr key={j}>
                            <td>
                              <a href={(cve.references || [])[0] || `https://nvd.nist.gov/vuln/detail/${cve.cve_id}`}
                                 target="_blank" rel="noreferrer" style={{ whiteSpace: "nowrap" }}>
                                {cve.cve_id}
                              </a>
                            </td>
                            <td><SourceBadge source={cve.source || "NVD"} /></td>
                            <td><SeverityBadge severity={cve.severity} /></td>
                            <td>{cve.score}</td>
                            <td style={{ maxWidth: 340, wordBreak: "break-word", fontSize: ".8rem" }}>
                              {cve.description}
                            </td>
                            <td><ExploitLinks exploits={cve.exploits} /></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}
            </div>
          );
        })
      )}
    </div>
  );
}
