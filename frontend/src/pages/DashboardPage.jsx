import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useScan } from "../context/ScanContext";

function fmt(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

const SEV_CONFIG = {
  CRITICAL: { color: "#f85149", label: "Critical" },
  HIGH:     { color: "#f0883e", label: "High"     },
  MEDIUM:   { color: "#d29922", label: "Medium"   },
  LOW:      { color: "#3fb950", label: "Low"       },
  NONE:     { color: "#8b949e", label: "Info/None" },
};

const MOD_CONFIG = {
  recon:  { icon: "🔍", label: "Recon"       },
  ports:  { icon: "🚪", label: "Port Scan"   },
  cve:    { icon: "🐛", label: "CVE Scan"    },
  web:    { icon: "🕸️", label: "Web Scan"    },
};

function StatCard({ icon, value, label, accent }) {
  return (
    <div className="db-stat-card">
      <span className="db-stat-icon">{icon}</span>
      <span className="db-stat-value" style={{ color: accent || "var(--accent)" }}>{value}</span>
      <span className="db-stat-label">{label}</span>
    </div>
  );
}

function SeverityBar({ counts, total }) {
  if (!total) return <p className="db-empty-note">No CVEs found across any project.</p>;
  return (
    <div className="db-sev-bars">
      {Object.entries(SEV_CONFIG).map(([key, { color, label }]) => {
        const count = counts[key] || 0;
        const pct   = total ? Math.round((count / total) * 100) : 0;
        return (
          <div key={key} className="db-sev-row">
            <span className="db-sev-label">{label}</span>
            <div className="db-sev-track">
              <div
                className="db-sev-fill"
                style={{ width: `${pct}%`, background: color }}
              />
            </div>
            <span className="db-sev-count" style={{ color }}>{count}</span>
          </div>
        );
      })}
    </div>
  );
}

function ModuleUsage({ usage, total }) {
  if (!total) return <p className="db-empty-note">No scans yet.</p>;
  return (
    <div className="db-mod-grid">
      {Object.entries(MOD_CONFIG).map(([key, { icon, label }]) => {
        const count = usage[key] || 0;
        const pct   = total ? Math.round((count / total) * 100) : 0;
        return (
          <div key={key} className="db-mod-card">
            <span className="db-mod-icon">{icon}</span>
            <span className="db-mod-label">{label}</span>
            <span className="db-mod-count">{count}<span style={{ color: "var(--muted)", fontSize: ".75rem" }}>/{total}</span></span>
            <div className="db-mod-bar-track">
              <div className="db-mod-bar-fill" style={{ width: `${pct}%` }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

function RecentScans({ projects }) {
  if (!projects.length)
    return <p className="db-empty-note">No scans yet. <Link to="/scan">Start one →</Link></p>;
  return (
    <div className="db-recent-list">
      {projects.map((p) => (
        <div key={p.id} className="db-recent-row">
          <div className="db-recent-info">
            <span className="db-recent-target">🎯 {p.target}</span>
            <span className="db-recent-name">{p.name}</span>
          </div>
          <div className="db-recent-stats">
            {p.summary.subdomains > 0 && <span className="db-badge db-badge-blue">🔍 {p.summary.subdomains}</span>}
            {p.summary.ports      > 0 && <span className="db-badge db-badge-blue">🚪 {p.summary.ports}</span>}
            {p.summary.cves       > 0 && <span className="db-badge db-badge-red">🐛 {p.summary.cves}</span>}
            {p.summary.web        > 0 && <span className="db-badge db-badge-orange">🕸️ {p.summary.web}</span>}
          </div>
          <div className="db-recent-right">
            <span className="db-recent-date">{fmt(p.created_at)}</span>
            <Link to={`/projects/${p.id}`} className="db-recent-link">View →</Link>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function DashboardPage() {
  const [data,    setData]    = useState(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);
  const { scanning } = useScan();
  const navigate = useNavigate();

  const load = () => {
    setLoading(true);
    fetch("/api/dashboard")
      .then((r) => { if (!r.ok) throw new Error(`${r.status}`); return r.json(); })
      .then((d) => { setData(d); setLoading(false); })
      .catch((e) => { setError(e.message); setLoading(false); });
  };

  useEffect(() => { load(); }, []);

  // Refresh when a scan completes (scanning transitions false → false with new data)
  useEffect(() => { if (!scanning && data) load(); }, [scanning]); // eslint-disable-line

  if (loading) return (
    <div className="db-page">
      <div className="db-loading">
        <span className="db-spin">⟳</span> Loading dashboard…
      </div>
    </div>
  );

  if (error) return (
    <div className="db-page">
      <p style={{ color: "var(--red)" }}>⚠ Could not load dashboard: {error}</p>
      <button className="btn-secondary" onClick={load} style={{ marginTop: ".5rem" }}>Retry</button>
    </div>
  );

  const { totals, severity, module_usage, active_scans, recent_projects } = data;
  const totalCVEs = Object.values(severity).reduce((s, v) => s + v, 0);

  return (
    <div className="db-page">
      {/* ── Header ── */}
      <div className="db-header">
        <div>
          <h2 className="db-title">📊 Dashboard</h2>
          <p className="db-subtitle">Overview of all your VAPT assessments</p>
        </div>
        <div style={{ display: "flex", gap: ".75rem", alignItems: "center" }}>
          {scanning && (
            <span className="db-active-badge">
              <span className="scan-dot" /> Scan in progress
            </span>
          )}
          {active_scans > 0 && !scanning && (
            <span className="db-active-badge">⚡ {active_scans} active scan{active_scans > 1 ? "s" : ""}</span>
          )}
          <button className="btn-scan db-new-scan-btn" onClick={() => navigate("/scan")}>
            ＋ New Scan
          </button>
        </div>
      </div>

      {/* ── Stat cards ── */}
      <div className="db-stats-row">
        <StatCard icon="🗂"  value={totals.projects}    label="Total Scans"    />
        <StatCard icon="🚪"  value={totals.ports}       label="Open Ports"     accent="var(--accent)" />
        <StatCard icon="🐛"  value={totals.cves}        label="CVEs Found"     accent="var(--red)"    />
        <StatCard icon="🔍"  value={totals.subdomains}  label="Subdomains"     accent="var(--green)"  />
        <StatCard icon="🕸️" value={totals.web}         label="Web Findings"   accent="var(--orange)" />
      </div>

      {/* ── Two-column content ── */}
      <div className="db-grid">
        {/* CVE Severity */}
        <div className="db-card">
          <h3 className="db-card-title">🐛 CVE Severity Distribution</h3>
          <SeverityBar counts={severity} total={totalCVEs} />
        </div>

        {/* Module Usage */}
        <div className="db-card">
          <h3 className="db-card-title">🧩 Module Usage</h3>
          <ModuleUsage usage={module_usage} total={totals.projects} />
        </div>
      </div>

      {/* ── Recent Scans ── */}
      <div className="db-card db-card-full">
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <h3 className="db-card-title" style={{ marginBottom: 0 }}>🕒 Recent Scans</h3>
          {totals.projects > 5 && (
            <Link to="/projects" style={{ fontSize: ".82rem", color: "var(--accent)" }}>
              View all {totals.projects} →
            </Link>
          )}
        </div>
        <RecentScans projects={recent_projects} />
      </div>

      {/* ── Empty state ── */}
      {totals.projects === 0 && (
        <div className="empty" style={{ padding: "2rem" }}>
          <div className="hero">🛡️</div>
          <h2>No scans yet</h2>
          <p>Run your first vulnerability assessment to see stats here.</p>
          <button className="btn-scan" style={{ marginTop: "1rem", width: "auto", padding: ".6rem 1.5rem" }}
            onClick={() => navigate("/scan")}>
            Start First Scan
          </button>
        </div>
      )}
    </div>
  );
}
