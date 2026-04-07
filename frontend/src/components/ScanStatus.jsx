const STATUS_META = {
  pending: { label: "Pending",  cls: "s-pending" },
  running: { label: "Running…", cls: "s-running" },
  done:    { label: "Done",     cls: "s-done"    },
  stopped: { label: "Stopped",  cls: "s-stopped" },
  error:   { label: "Error",    cls: "s-error"   },
  skipped: { label: "Skipped",  cls: "s-skipped" },
};

const MODULES = [
  { key: "recon", icon: "🔍", label: "Recon"      },
  { key: "ports", icon: "🚪", label: "Port Scan"  },
  { key: "cve",   icon: "🐛", label: "CVE Lookup" },
  { key: "web",   icon: "🕸️", label: "Web Vulns"  },
];

function fmt(secs) {
  if (secs === null || secs === undefined) return "";
  if (secs < 60) return `${secs}s`;
  return `${Math.floor(secs / 60)}m ${secs % 60}s`;
}

export default function ScanStatus({ moduleStatus, getElapsed, activatedModules, onStop, onResume, scanning, canResume }) {
  const active = MODULES.filter((m) => activatedModules.includes(m.key));
  if (!active.length) return null;

  return (
    <div className="scan-status-panel">
      <div className="scan-status-header">
        <span style={{ fontWeight: 600, fontSize: ".9rem" }}>Scan Pipeline</span>
        <div style={{ display: "flex", gap: ".5rem", marginLeft: "auto" }}>
          {scanning && (
            <button className="btn-stop" onClick={onStop}>⏹ Stop</button>
          )}
          {canResume && !scanning && (
            <button className="btn-resume" onClick={onResume}>▶ Resume</button>
          )}
        </div>
      </div>

      <div className="module-pipeline">
        {active.map(({ key, icon, label }, idx) => {
          const status = moduleStatus[key] || "pending";
          const meta = STATUS_META[status] || STATUS_META.pending;
          const elapsed = getElapsed(key);

          return (
            <div key={key} className={`pipeline-item ${meta.cls}`}>
              <span className="pi-icon">{icon}</span>
              <span className="pi-label">{label}</span>
              <span className={`pi-badge ${meta.cls}`}>{meta.label}</span>
              {elapsed !== null && (
                <span className="pi-time">{fmt(elapsed)}</span>
              )}
              {idx < active.length - 1 && (
                <span className="pi-arrow">→</span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
