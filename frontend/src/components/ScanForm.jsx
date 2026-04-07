const PORT_PRESETS = [
  { label: "Top 100",   value: "top-100",  est: "~10s",    warn: false },
  { label: "Top 1000",  value: "top-1000", est: "~30s",    warn: false },
  { label: "Top 5000",  value: "top-5000", est: "~2 min",  warn: false },
  { label: "1–65535",   value: "1-65535",  est: "~10 min", warn: true  },
  { label: "Custom",    value: "custom",   est: null,      warn: false },
];

const WEB_DEPTHS = [
  { value: 1, label: "Basic",    desc: "Homepage only · SQLi · XSS · Redirect"        },
  { value: 2, label: "Standard", desc: "Crawl site · more payloads · security headers" },
  { value: 3, label: "Deep",     desc: "Full crawl · header injection · path traversal"},
];

const WEB_EST = { 1: "~10s", 2: "~30s", 3: "~2 min" };

import WordlistPicker from "./WordlistPicker";

export default function ScanForm({ config, onChange, onScan, scanning }) {
  const modules = [
    { key: "recon",     icon: "🔍", label: "Recon",       desc: "Subdomain enumeration" },
    { key: "ports",     icon: "🚪", label: "Port Scan",   desc: "Nmap service detection" },
    { key: "cve",       icon: "🐛", label: "CVE Lookup",  desc: "NVD API correlation" },
    { key: "web",       icon: "🕸️", label: "Web Vulns",   desc: "Probe web vulnerabilities" },
    { key: "full_scan", icon: "⚡", label: "Full Scan",   desc: "All modules above" },
  ];

  const toggle = (key) => {
    if (key === "full_scan") {
      onChange({ ...config, full_scan: !config.full_scan, recon: false, ports: false, cve: false, web: false });
    } else {
      onChange({ ...config, [key]: !config[key], full_scan: false });
    }
  };

  const portsActive  = config.ports || config.full_scan;
  const webActive    = config.web   || config.full_scan;
  const nothingSelected = !config.full_scan && !config.recon && !config.ports && !config.cve && !config.web;

  // Determine if custom range is selected
  const isPreset     = PORT_PRESETS.some((p) => p.value !== "custom" && p.value === config.port_range);
  const activePreset = PORT_PRESETS.find((p) => p.value === config.port_range);

  return (
    <>
      <h2>Target</h2>
      <div className="form-group">
        <label>Domain or IP</label>
        <input
          type="text"
          placeholder="example.com"
          value={config.target}
          onChange={(e) => onChange({ ...config, target: e.target.value })}
          disabled={scanning}
        />
      </div>

      <h2>Modules</h2>
      <div className="modules">
        {modules.map(({ key, icon, label, desc }) => {
          const active = !!config[key];
          return (
            <div key={key} className={`module-check${active ? " active" : ""}`}
                 onClick={() => !scanning && toggle(key)}>
              <span className="module-icon">{icon}</span>
              <span className="module-label">
                <strong>{label}</strong>
                <span>{desc}</span>
              </span>
              <span style={{ marginLeft: "auto", fontSize: ".85rem",
                             color: active ? "var(--accent)" : "var(--border)" }}>
                {active ? "✓" : "○"}
              </span>
            </div>
          );
        })}
      </div>

      {/* ── Port settings ── */}
      {portsActive && (
        <div className="settings-block">
          <label className="settings-label">Port Range</label>
          <div className="preset-pills">
            {PORT_PRESETS.map((p) => {
              const isActive = p.value === "custom"
                ? !isPreset
                : config.port_range === p.value;
              return (
                <button key={p.value}
                  className={`preset-pill${isActive ? " active" : ""}${p.warn ? " warn" : ""}`}
                  disabled={scanning}
                  onClick={() => onChange({ ...config, port_range: p.value === "custom" ? "" : p.value })}>
                  {p.label}
                  {p.est && <span className="pill-est">{p.est}</span>}
                </button>
              );
            })}
          </div>
          {!isPreset && (
            <input className="custom-range-input" type="text" placeholder="e.g. 80,443,8000-9000"
              value={config.port_range} disabled={scanning}
              onChange={(e) => onChange({ ...config, port_range: e.target.value })} />
          )}
          {activePreset?.warn && (
            <p className="setting-warn">⚠ Full port scan is very slow (~10 min).</p>
          )}

          <div className={`module-check${config.version_detect ? " active" : ""}`}
               style={{ marginTop: ".5rem" }}
               onClick={() => !scanning && onChange({ ...config, version_detect: !config.version_detect })}>
            <span className="module-icon">🔬</span>
            <span className="module-label">
              <strong>Version Detection</strong>
              <span>nmap -sV · adds ~1–2 min</span>
            </span>
            <span style={{ marginLeft: "auto", fontSize: ".85rem",
                           color: config.version_detect ? "var(--accent)" : "var(--border)" }}>
              {config.version_detect ? "✓" : "○"}
            </span>
          </div>
        </div>
      )}

      {/* ── Recon wordlist ── */}
      {(config.recon || config.full_scan) && (
        <div className="settings-block">
          <WordlistPicker
            value={config.recon_wordlist}
            onChange={(name) => onChange({ ...config, recon_wordlist: name })}
            disabled={scanning}
          />
        </div>
      )}

      {/* ── Web depth ── */}
      {webActive && (
        <div className="settings-block">
          <label className="settings-label">Web Scan Depth</label>
          <div className="depth-options">
            {WEB_DEPTHS.map((d) => (
              <div key={d.value}
                   className={`depth-option${config.web_depth === d.value ? " active" : ""}`}
                   onClick={() => !scanning && onChange({ ...config, web_depth: d.value })}>
                <div className="depth-top">
                  <strong>{d.label}</strong>
                  <span className="depth-est">{WEB_EST[d.value]}</span>
                </div>
                <span className="depth-desc">{d.desc}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <button className="btn-scan" onClick={onScan}
              disabled={scanning || !config.target.trim() || nothingSelected}>
        {scanning ? "Scanning…" : "▶  Run Scan"}
      </button>
    </>
  );
}
