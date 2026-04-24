import WordlistPicker from "./WordlistPicker";

const PORT_PRESETS = [
  { label: "Top 100",   value: "top-100",  est: "~10s"   },
  { label: "Top 1000",  value: "top-1000", est: "~30s"   },
  { label: "Top 5000",  value: "top-5000", est: "~2 min" },
  { label: "Full",      value: "full",     est: "~10 min", warn: true },
  { label: "Custom",    value: "custom",   est: null      },
];

const SCAN_TYPES = [
  { value: "connect",    label: "Connect",    desc: "Full TCP (-sT) · no root needed" },
  { value: "syn",        label: "SYN",        desc: "Stealth half-open (-sS) · needs root/Npcap" },
  { value: "aggressive", label: "Aggressive", desc: "-A · OS + version + scripts + traceroute" },
  { value: "udp",        label: "UDP",        desc: "-sU · slow · needs root" },
  { value: "syn_udp",    label: "SYN+UDP",    desc: "Both TCP & UDP · needs root" },
];

const SCRIPT_PRESETS = [
  { value: "",          label: "None"       },
  { value: "default",   label: "Default"    },
  { value: "banner",    label: "Banner"     },
  { value: "safe",      label: "Safe"       },
  { value: "vuln",      label: "Vuln ⚠"    },
  { value: "discovery", label: "Discovery"  },
  { value: "http",      label: "HTTP"       },
  { value: "ssl",       label: "SSL/TLS"    },
  { value: "smb",       label: "SMB"        },
  { value: "ftp",       label: "FTP"        },
  { value: "ssh",       label: "SSH"        },
  { value: "smtp",      label: "SMTP"       },
  { value: "dns",       label: "DNS"        },
];

const WEB_DEPTHS = [
  { value: 1, label: "Basic",    desc: "Homepage only · SQLi · XSS · Redirect"        },
  { value: 2, label: "Standard", desc: "Crawl site · more payloads · security headers" },
  { value: 3, label: "Deep",     desc: "Full crawl · header injection · path traversal"},
];

const WEB_EST = { 1: "~10s", 2: "~30s", 3: "~2 min" };

const SCAN_CLASSIFICATIONS = [
  { value: "passive", label: "🔍 Passive", desc: "OSINT + DNS lookup only. NO packets sent, NO port scanning, NO HTTP probing." },
  { value: "active",  label: "⚡ Active", desc: "Port scanning + web probing + service enumeration. INTRUSIVE." },
  { value: "hybrid",  label: "🎯 Hybrid", desc: "All modules · deepest analysis. MOST INTRUSIVE." },
];

function Toggle({ label, sub, icon, active, onChange, disabled }) {
  return (
    <div className={`module-check${active ? " active" : ""}`}
         onClick={() => !disabled && onChange(!active)}>
      {icon && <span className="module-icon">{icon}</span>}
      <span className="module-label">
        <strong>{label}</strong>
        {sub && <span>{sub}</span>}
      </span>
      <span style={{ marginLeft: "auto", fontSize: ".85rem",
                     color: active ? "var(--accent)" : "var(--border)" }}>
        {active ? "✓" : "○"}
      </span>
    </div>
  );
}

export default function ScanForm({ config, onChange, onScan, scanning }) {
  const set = (patch) => onChange({ ...config, ...patch });

  const classification = config.scan_classification || "active";
  const isPassive = classification === "passive";
  const isActive = classification === "active";
  const isHybrid = classification === "hybrid";

  // For hybrid, show all modules; for passive, only recon+cve; for active, only ports+web+cve
  const allModules = [
    { key: "recon",     icon: "🔍", label: "Recon",      desc: "Subdomain enumeration" },
    { key: "ports",     icon: "🚪", label: "Port Scan",  desc: "Nmap port & service scan" },
    { key: "cve",       icon: "🐛", label: "CVE Lookup", desc: "NVD API correlation" },
    { key: "web",       icon: "🕸️", label: "Web Vulns",  desc: "Probe web vulnerabilities" },
    { key: "full_scan", icon: "⚡", label: "Full Scan",  desc: "All modules above" },
  ];

  // Filter modules based on scan classification
  let modules;
  if (isPassive) {
    modules = allModules.filter(m => ["recon", "cve"].includes(m.key));
  } else if (isActive) {
    modules = allModules.filter(m => ["ports", "cve", "web"].includes(m.key));
  } else {
    modules = allModules; // hybrid shows all
  }

  const toggle = (key) => {
    if (key === "full_scan") {
      set({ full_scan: !config.full_scan, recon: false, ports: false, cve: false, web: false });
    } else {
      set({ [key]: !config[key], full_scan: false });
    }
  };

  const portsActive = config.ports || config.full_scan;
  const webActive   = config.web   || config.full_scan;
  const reconActive = config.recon || config.full_scan;
  const nothingSelected = !config.full_scan && !config.recon && !config.ports && !config.cve && !config.web;

  const isPreset     = PORT_PRESETS.some((p) => p.value !== "custom" && p.value === config.port_range);
  const activePreset = PORT_PRESETS.find((p) => p.value === config.port_range);

  return (
    <>
      <h2>Target</h2>
      <div className="form-group">
        <label>Domain or IP</label>
        <input type="text" placeholder="example.com"
          value={config.target} disabled={scanning}
          onChange={(e) => set({ target: e.target.value })} />
      </div>

      <h2>Scan Type</h2>
      <div className="classification-options">
        {SCAN_CLASSIFICATIONS.map((c) => (
          <div key={c.value}
               className={`classification-opt${config.scan_classification === c.value ? " active" : ""}`}
               onClick={() => !scanning && set({ scan_classification: c.value })}>
            <strong>{c.label}</strong>
            <span>{c.desc}</span>
          </div>
        ))}
      </div>

      {isPassive && (
        <div className="scan-constraint-notice">
          <strong>🔒 Passive Scan Constraints:</strong>
          <ul>
            <li>✓ Public data sources only (OSINT APIs, Certificate Transparency, DNS queries)</li>
            <li>✓ NO direct packet transmission</li>
            <li>✓ NO port scanning (Nmap disabled)</li>
            <li>✓ NO HTTP probing (Web scanner disabled)</li>
            <li>✗ CVE lookups limited to OSINT recon data</li>
          </ul>
        </div>
      )}

      {isActive && (
        <div className="scan-constraint-notice active">
          <strong>⚡ Active Scan Constraints:</strong>
          <ul>
            <li>✓ Only authorized targets in scope</li>
            <li>✓ Rate-limited to avoid DoS</li>
            <li>✓ Safe PoC payloads only (no data modification)</li>
            <li>✓ All requests logged for audit trail</li>
            <li>✓ Respects robots.txt by default</li>
          </ul>
        </div>
      )}

      {/* ── Scope for active scans ── */}
      {isActive && (
        <div className="settings-block">
          <label className="settings-label">Authorized Scope (optional)</label>
          <textarea
            className="scope-textarea"
            placeholder="example.com&#10;192.168.1.0/24&#10;https://api.example.com"
            value={config.scope ? config.scope.join('\n') : ''}
            disabled={scanning}
            onChange={(e) => {
              const lines = e.target.value.trim().split('\n').filter(l => l.trim());
              set({ scope: lines.length > 0 ? lines : null });
            }}
          />
          <p className="scope-hint">One target per line. Leave empty to allow any target.</p>
          {config.scope && config.scope.length > 0 && (
            <p className="scope-active">🔒 In-scope: {config.scope.join(', ')}</p>
          )}
        </div>
      )}

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
              const isActive = p.value === "custom" ? !isPreset : config.port_range === p.value;
              return (
                <button key={p.value}
                  className={`preset-pill${isActive ? " active" : ""}${p.warn ? " warn" : ""}`}
                  disabled={scanning}
                  onClick={() => set({ port_range: p.value === "custom" ? "" : p.value })}>
                  {p.label}
                  {p.est && <span className="pill-est">{p.est}</span>}
                </button>
              );
            })}
          </div>
          {!isPreset && (
            <input className="custom-range-input" type="text"
              placeholder="e.g. 80,443,8000-9000"
              value={config.port_range} disabled={scanning}
              onChange={(e) => set({ port_range: e.target.value })} />
          )}
          {activePreset?.warn && (
            <p className="setting-warn">⚠ Full port scan is very slow (~10 min).</p>
          )}

          {/* Scan type */}
          <label className="settings-label" style={{ marginTop: ".75rem" }}>Scan Type</label>
          <div className="scan-type-grid">
            {SCAN_TYPES.map((t) => (
              <div key={t.value}
                   className={`scan-type-opt${config.scan_type === t.value ? " active" : ""}`}
                   onClick={() => !scanning && set({ scan_type: t.value })}>
                <strong>{t.label}</strong>
                <span>{t.desc}</span>
              </div>
            ))}
          </div>
          {(config.scan_type === "syn" || config.scan_type === "syn_udp" || config.scan_type === "udp") && (
            <p className="setting-warn">⚠ Requires root / Administrator + Npcap on Windows.</p>
          )}

          {/* Timing */}
          <label className="settings-label" style={{ marginTop: ".75rem" }}>
            Timing — T{config.port_timing ?? 4}
            <span className="timing-desc"> {["Paranoid","Sneaky","Polite","Normal","Aggressive","Insane"][config.port_timing ?? 4]}</span>
          </label>
          <input type="range" min="0" max="5" step="1"
            className="timing-slider"
            value={config.port_timing ?? 4}
            disabled={scanning}
            onChange={(e) => set({ port_timing: parseInt(e.target.value) })} />
          <div className="timing-labels">
            {["T0","T1","T2","T3","T4","T5"].map((t, i) => (
              <span key={t} className={config.port_timing === i ? "tl-active" : ""}>{t}</span>
            ))}
          </div>

          {/* NSE Scripts */}
          <label className="settings-label" style={{ marginTop: ".75rem" }}>NSE Scripts</label>
          <div className="script-pills">
            {SCRIPT_PRESETS.map((s) => (
              <button key={s.value}
                className={`preset-pill${config.port_script === s.value ? " active" : ""}${s.value === "vuln" ? " warn" : ""}`}
                disabled={scanning}
                onClick={() => set({ port_script: s.value })}>
                {s.label}
              </button>
            ))}
          </div>

          {/* Toggles row */}
          <div style={{ display: "flex", flexDirection: "column", gap: ".35rem", marginTop: ".5rem" }}>
            <Toggle label="Version Detection" sub="-sV · adds ~1-2 min" icon="🔬"
              active={!!config.version_detect} disabled={scanning || config.scan_type === "aggressive"}
              onChange={(v) => set({ version_detect: v })} />
            <Toggle label="OS Detection" sub="-O · guesses OS" icon="🖥️"
              active={!!config.os_detect} disabled={scanning || config.scan_type === "aggressive"}
              onChange={(v) => set({ os_detect: v })} />
            <Toggle label="Skip Ping (-Pn)" sub="Treat host as up even if ICMP blocked" icon="🔇"
              active={!!config.skip_ping} disabled={scanning}
              onChange={(v) => set({ skip_ping: v })} />
          </div>

          {/* Extra flags */}
          <div className="form-group" style={{ marginTop: ".5rem" }}>
            <label>Extra nmap flags</label>
            <input type="text" placeholder="e.g. --min-rate 1000 --ttl 64"
              value={config.port_extra_flags ?? ""} disabled={scanning}
              onChange={(e) => set({ port_extra_flags: e.target.value })} />
          </div>
        </div>
      )}

      {/* ── Recon wordlist ── */}
      {reconActive && (
        <div className="settings-block">
          <WordlistPicker
            value={config.recon_wordlist}
            onChange={(name) => set({ recon_wordlist: name })}
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
                   onClick={() => !scanning && set({ web_depth: d.value })}>
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
