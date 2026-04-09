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
  const [projects,  setProjects]  = useState([]);
  const [loading,   setLoading]   = useState(true);
  const [error,     setError]     = useState(null);
  const [query,     setQuery]     = useState("");
  const [selected,  setSelected]  = useState(new Set());
  const [editingId, setEditingId] = useState(null);
  const [editName,  setEditName]  = useState("");
  // deleteId = string  → single-project confirm
  // deleteId = "bulk"  → bulk-delete confirm
  const [deleteId,  setDeleteId]  = useState(null);
  const inputRef = useRef(null);

  const load = () =>
    fetch("/api/projects")
      .then((r) => {
        if (!r.ok) throw new Error(`Server returned ${r.status}`);
        return r.json();
      })
      .then((data) => { setProjects(data); setLoading(false); setError(null); })
      .catch((err) => { setProjects([]); setLoading(false); setError(err.message); });

  useEffect(() => { load(); }, []);
  useEffect(() => { if (editingId) inputRef.current?.focus(); }, [editingId]);

  // ── Filtered list ──────────────────────────────────────────────────────────
  const q = query.trim().toLowerCase();
  const filtered = q
    ? projects.filter((p) =>
        p.name.toLowerCase().includes(q) || p.target.toLowerCase().includes(q)
      )
    : projects;

  // ── Selection helpers ──────────────────────────────────────────────────────
  const toggleSelect = (id) =>
    setSelected((s) => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n; });

  const allVisibleSelected =
    filtered.length > 0 && filtered.every((p) => selected.has(p.id));

  const toggleAll = () => {
    if (allVisibleSelected) {
      setSelected((s) => { const n = new Set(s); filtered.forEach((p) => n.delete(p.id)); return n; });
    } else {
      setSelected((s) => { const n = new Set(s); filtered.forEach((p) => n.add(p.id)); return n; });
    }
  };

  // ── Edit / delete ──────────────────────────────────────────────────────────
  const startEdit = (p) => { setEditingId(p.id); setEditName(p.name); };

  const saveEdit = async (id) => {
    if (!editName.trim()) return;
    await fetch(`/api/projects/${id}`, {
      method:  "PUT",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ name: editName.trim() }),
    });
    setEditingId(null);
    load();
  };

  const confirmDelete = async () => {
    if (deleteId === "bulk") {
      await Promise.all([...selected].map((id) =>
        fetch(`/api/projects/${id}`, { method: "DELETE" })
      ));
      setSelected(new Set());
    } else {
      await fetch(`/api/projects/${deleteId}`, { method: "DELETE" });
      setSelected((s) => { const n = new Set(s); n.delete(deleteId); return n; });
    }
    setDeleteId(null);
    load();
  };

  // ── Render ─────────────────────────────────────────────────────────────────
  if (loading) return <div className="main"><p className="none-msg">Loading projects…</p></div>;
  if (error)   return (
    <div className="main">
      <p className="none-msg" style={{ color: "var(--danger)" }}>
        ⚠ Could not load projects: {error}
      </p>
      <button className="btn-secondary" onClick={load} style={{ marginTop: ".5rem" }}>Retry</button>
    </div>
  );

  const bulkCount = selected.size;

  return (
    <div className="projects-page">
      {/* ── Header bar ── */}
      <div className="projects-header">
        <h2 style={{ color: "var(--accent)", fontSize: "1.1rem" }}>
          🗂 Saved Projects <span className="badge-count">{projects.length}</span>
        </h2>

        <div className="projects-toolbar">
          {/* Search */}
          <div className="proj-search-wrap">
            <span className="proj-search-icon">🔎</span>
            <input
              className="proj-search"
              placeholder="Search by name or target…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            {query && (
              <button className="proj-search-clear" onClick={() => setQuery("")}>✕</button>
            )}
          </div>

          {/* Bulk-delete button */}
          {bulkCount > 0 && (
            <button className="btn-bulk-delete" onClick={() => setDeleteId("bulk")}>
              🗑 Delete {bulkCount} selected
            </button>
          )}
        </div>
      </div>

      {/* ── Select-all bar (only when results exist) ── */}
      {filtered.length > 0 && (
        <label className="select-all-bar">
          <input
            type="checkbox"
            checked={allVisibleSelected}
            onChange={toggleAll}
          />
          <span>
            {allVisibleSelected
              ? `Deselect all ${filtered.length}`
              : `Select all ${filtered.length}`}
            {q && " matching"}
          </span>
        </label>
      )}

      {projects.length === 0 ? (
        <div className="empty" style={{ padding: "4rem" }}>
          <div className="hero">🗂</div>
          <h2>No projects yet</h2>
          <p>Run a scan and it will be saved here automatically.</p>
          <Link to="/" className="btn-scan" style={{ display: "inline-block", marginTop: "1rem", textDecoration: "none", padding: ".6rem 1.5rem", borderRadius: "6px" }}>
            Start a Scan
          </Link>
        </div>
      ) : filtered.length === 0 ? (
        <div className="empty" style={{ padding: "3rem" }}>
          <div className="hero" style={{ fontSize: "2rem" }}>🔎</div>
          <p style={{ color: "var(--muted)" }}>No projects match "<strong>{query}</strong>"</p>
          <button className="btn-secondary" onClick={() => setQuery("")} style={{ marginTop: ".75rem" }}>
            Clear search
          </button>
        </div>
      ) : (
        <div className="projects-grid">
          {filtered.map((p) => (
            <div
              key={p.id}
              className={`project-card${selected.has(p.id) ? " pc-selected" : ""}`}
            >
              <div className="pc-top">
                {/* Inline checkbox */}
                <input
                  type="checkbox"
                  className="pc-checkbox"
                  checked={selected.has(p.id)}
                  onChange={() => toggleSelect(p.id)}
                  title="Select"
                />

                {editingId === p.id ? (
                  <input ref={inputRef} className="pc-name-input" value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    onBlur={() => saveEdit(p.id)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter")  saveEdit(p.id);
                      if (e.key === "Escape") setEditingId(null);
                    }} />
                ) : (
                  <span className="pc-name" title="Click to rename" onClick={() => startEdit(p)}>
                    {p.name}
                  </span>
                )}
                <button className="pc-delete" title="Delete project" onClick={() => setDeleteId(p.id)}>🗑</button>
              </div>

              <div className="pc-meta">
                <span className="pc-target">🎯 {p.target}</span>
                <span className="pc-date">🕒 {fmt(p.created_at)}</span>
              </div>

              <ModulePills modules={p.modules} />

              <div className="pc-stats">
                {[
                  { val: p.summary.subdomains, lbl: "subdomains" },
                  { val: p.summary.ports,      lbl: "ports"      },
                  { val: p.summary.cves,       lbl: "CVEs"       },
                  { val: p.summary.web,        lbl: "findings"   },
                ].map(({ val, lbl }) => (
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

      {/* ── Delete confirm modal ── */}
      {deleteId && (
        <div className="modal-overlay" onClick={() => setDeleteId(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>
              {deleteId === "bulk"
                ? `Delete ${bulkCount} project${bulkCount > 1 ? "s" : ""}?`
                : "Delete project?"}
            </h3>
            <p>This action cannot be undone.</p>
            <div className="modal-actions">
              <button className="btn-stop" onClick={confirmDelete}>
                {deleteId === "bulk" ? `Delete ${bulkCount}` : "Delete"}
              </button>
              <button className="btn-outline" onClick={() => setDeleteId(null)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
