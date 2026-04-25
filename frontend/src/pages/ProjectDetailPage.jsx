import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import ResultsDashboard from "../components/ResultsDashboard";
import RiskHeatMap from "../components/RiskHeatMap";
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
  const [activeTab, setActiveTab] = useState("results");  // "results" or "heatmap"

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

      {/* Tab Navigation */}
      <div className="tab-navigation" style={{ borderBottom: "2px solid #e5e7eb", marginTop: "24px" }}>
        <button
          className={`tab-button ${activeTab === "results" ? "active" : ""}`}
          onClick={() => setActiveTab("results")}
          style={{
            padding: "12px 24px",
            border: "none",
            background: activeTab === "results" ? "#3b82f6" : "transparent",
            color: activeTab === "results" ? "white" : "#6b7280",
            cursor: "pointer",
            fontWeight: activeTab === "results" ? "600" : "500",
            fontSize: "14px",
            borderRadius: "6px 6px 0 0",
            marginRight: "8px"
          }}
        >
          📊 Scan Results
        </button>
        <button
          className={`tab-button ${activeTab === "heatmap" ? "active" : ""}`}
          onClick={() => setActiveTab("heatmap")}
          style={{
            padding: "12px 24px",
            border: "none",
            background: activeTab === "heatmap" ? "#3b82f6" : "transparent",
            color: activeTab === "heatmap" ? "white" : "#6b7280",
            cursor: "pointer",
            fontWeight: activeTab === "heatmap" ? "600" : "500",
            fontSize: "14px",
            borderRadius: "6px 6px 0 0",
            marginRight: "8px"
          }}
        >
          🔥 Risk Heat Map
        </button>
      </div>

      {/* Tab Content */}
      <div style={{ marginTop: "0" }}>
        {activeTab === "results" && <ResultsDashboard results={results} collapsibleTables />}
        {activeTab === "heatmap" && <RiskHeatMap projectId={id} />}
      </div>
    </div>
  );
}
