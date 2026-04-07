import { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";

function fmt(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" }) +
    " " + d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
}

function ModulePills({ modules }) {
  const map = { recon: "🔍", ports: "🚪", cve: "🐛", web: "🕸️" };
  const active = Object.entries(map)
    .filter(([k]) => modules?.full_scan || modules?.[k]);
  if (!active.length) return null;
  return (
    <span style={{ display: "flex", gap: ".3rem", flexWrap: "wrap" }}>
      {active.map(([, icon]) => (
        <span key={icon} style={{ fontSize: ".9rem" }}>{icon}</span>
      ))}
    </span>
  );
}

export default function ProjectsPage() {
  const [projects, setProjects] = useState([]);
  const [loading,  setLoading]  = useState(true);
  const [editingId, setEditingId] = useState(null);
  const [editName,  setEditName]  = useState("");
  const [deleteId,  setDeleteId]  = useState(null);
  const inputRef = useRef(null);

  const load = () =>
    fetch("/api/projects")
      .then((r) => r.json())
      .then((data) => { setProjects(data); setLoading(false); });

  useEffect(() => { load(); }, []);
  useEffect(() => { if (editingId) inputRef.current?.focus(); }, [editingId]);

  const startEdit = (p) => { setEditingId(p.id); setEditName(p.name); };

  const saveEdit = async (id) => {
    if (!editName.trim()) return;
    await fetch(`/api/projects/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: editName.trim() }),
    });
    setEditingId(null);
    load();
  };

  const confirmDelete = async () => {
    await fetch(`/api/projects/${deleteId}`, { method: "DELETE" });
    setDeleteId(null);
    load();
  };

  if (loading) return <div className="main"><p className="none-msg">Loading projects…</p></div>;

  return (
    <div className="projects-page">
      <div className="projects-header">
        <h2 style={{ color: "var(--accent)", fontSize: "1.1rem" }}>
          🗂 Saved Projects <span className="badge-count">{projects.length}</span>
        </h2>
      </div>

      {projects.length === 0 ? (
        <div className="empty" style={{ padding: "4rem" }}>
          <div className="hero">🗂</div>
          <h2>No projects yet</h2>
          <p>Run a scan and it will be saved here automatically.</p>
          <Link to="/" className="btn-scan" style={{ display: "inline-block", marginTop: "1rem", textDecoration: "none", padding: ".6rem 1.5rem", borderRadius: "6px" }}>
            Start a Scan
          </Link>
        </div>
      ) : (
        <div className="projects-grid">
          {projects.map((p) => (
            <div key={p.id} className="project-card">
              <div className="pc-top">
                {editingId === p.id ? (
                  <input ref={inputRef} className="pc-name-input" value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    onBlur={() => saveEdit(p.id)}
                    onKeyDown={(e) => { if (e.key === "Enter") saveEdit(p.id); if (e.key === "Escape") setEditingId(null); }} />
                ) : (
                  <span className="pc-name" title="Click to rename" onClick={() => startEdit(p)}>{p.name}</span>
                )}
                <button className="pc-delete" title="Delete" onClick={() => setDeleteId(p.id)}>🗑</button>
              </div>

              <div className="pc-meta">
                <span className="pc-target">🎯 {p.target}</span>
                <span className="pc-date">🕒 {fmt(p.created_at)}</span>
              </div>

              <ModulePills modules={p.modules} />

              <div className="pc-stats">
                {[
                  { icon: "🔍", val: p.summary.subdomains, lbl: "subdomains" },
                  { icon: "🚪", val: p.summary.ports,      lbl: "ports"      },
                  { icon: "🐛", val: p.summary.cves,       lbl: "CVEs"       },
                  { icon: "🕸️", val: p.summary.web,        lbl: "findings"   },
                ].map(({ icon, val, lbl }) => (
                  <div key={lbl} className="pc-stat">
                    <span className="pc-stat-num">{val}</span>
                    <span className="pc-stat-lbl">{lbl}</span>
                  </div>
                ))}
              </div>

              <Link to={`/projects/${p.id}`} className="pc-view-btn">View Report →</Link>
            </div>
          ))}
        </div>
      )}

      {/* Delete confirm modal */}
      {deleteId && (
        <div className="modal-overlay" onClick={() => setDeleteId(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Delete project?</h3>
            <p>This action cannot be undone.</p>
            <div className="modal-actions">
              <button className="btn-stop" onClick={confirmDelete}>Delete</button>
              <button className="btn-outline" onClick={() => setDeleteId(null)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
