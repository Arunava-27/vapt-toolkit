import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import ResultsDashboard from "../components/ResultsDashboard";
import "../App-compliance.css";

function fmt(iso) {
  return new Date(iso).toLocaleString(undefined, {
    month: "short", day: "numeric", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

export default function ProjectDetailPage() {
  const { id } = useParams();
  const [project, setProject]   = useState(null);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState(null);
  const [selectedScanIdx, setSelectedScanIdx] = useState(-1);  // -1 = latest

  useEffect(() => {
    fetch(`/api/projects/${id}`)
      .then((r) => { if (!r.ok) throw new Error("Not found"); return r.json(); })
      .then((data) => { setProject(data); setLoading(false); setSelectedScanIdx(-1); })
      .catch((e) => { setError(e.message); setLoading(false); });
  }, [id]);

  const exportPDF = () => {
    const slug = project.target.replace(/[^a-z0-9]/gi, "-");
    const a = document.createElement("a");
    a.href = `/api/projects/${id}/pdf`;
    a.download = `vapt-${slug}-${id.slice(0, 8)}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  if (loading) return <div className="main"><p className="none-msg">Loading…</p></div>;
  if (error)   return <div className="main"><p className="none-msg">Error: {error}</p></div>;

  const scans = project.scans || [];
  const currentScan = selectedScanIdx === -1 ? scans[scans.length - 1] : scans[selectedScanIdx];
  const cfg = currentScan?.config || {};
  const results = currentScan?.results || {};

  return (
    <div className="detail-page">
      {/* ── Header row ── */}
      <div className="detail-header">
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: ".75rem", flexWrap: "wrap" }}>
            <h2 className="detail-title">{project.name}</h2>
            <span className="badge-count">{fmt(project.created_at)}</span>
          </div>
          <p className="detail-target">🎯 {project.target}</p>
          {scans.length > 1 && (
            <div className="detail-scan-selector">
              <label>📋 Scan History:</label>
              <select value={selectedScanIdx} onChange={(e) => setSelectedScanIdx(parseInt(e.target.value))}>
                <option value={-1}>Latest ({fmt(scans[scans.length - 1]?.timestamp)})</option>
                {scans.map((scan, idx) => (
                  <option key={idx} value={idx}>
                    Scan #{scans.length - idx} — {fmt(scan.timestamp)} ({scan.scan_type})
                  </option>
                ))}
              </select>
            </div>
          )}
          <div className="detail-config">
            {cfg.full_scan && <span className="cfg-tag">⚡ Full Scan</span>}
            {cfg.recon     && <span className="cfg-tag">🔍 Recon</span>}
            {cfg.ports     && <span className="cfg-tag">🚪 Ports ({cfg.port_range})</span>}
            {cfg.version_detect && <span className="cfg-tag">🔬 Version Detection</span>}
            {cfg.cve       && <span className="cfg-tag">🐛 CVE</span>}
            {cfg.web       && <span className="cfg-tag">🕸️ Web (depth {cfg.web_depth})</span>}
          </div>
        </div>
        <div className="detail-actions">
          <button className="btn-export" onClick={exportPDF}>
            ⬇ Export PDF
          </button>
          <Link to="/" className="btn-rescan"
            state={{ config: cfg }}>↺ Re-scan</Link>
          <Link to="/projects" className="btn-outline">← Back</Link>
        </div>
      </div>

      <ResultsDashboard results={results} collapsibleTables />
    </div>
  );
}
