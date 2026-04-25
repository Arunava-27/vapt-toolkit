import "./Step1_Goal.css";

const SCAN_PRESETS = [
  {
    id: "quick",
    title: "🔍 Reconnaissance Only",
    description: "OSINT, DNS lookup. Safe, no intrusion.",
    modules: { recon: true },
    time: "1-2 min",
    risk: "low",
  },
  {
    id: "ports",
    title: "🚪 Open Ports & Services",
    description: "Find open ports, services, versions.",
    modules: { ports: true, cve: true },
    time: "30s - 2 min",
    risk: "medium",
  },
  {
    id: "web",
    title: "🕸️ Web Vulnerabilities",
    description: "XSS, SQLi, CSRF, auth flaws, etc.",
    modules: { ports: true, web: true, cve: true },
    time: "1-3 min",
    risk: "high",
  },
  {
    id: "full",
    title: "⚡ Everything (Full Audit)",
    description: "All modules: recon + ports + CVE + web",
    modules: { recon: true, ports: true, cve: true, web: true },
    time: "5-10 min",
    risk: "very-high",
  },
  {
    id: "custom",
    title: "⚙️ Custom Modules",
    description: "You choose exactly which modules to run.",
    modules: {},
    time: "variable",
    risk: "variable",
  },
];

export default function Step1_Goal({ wizardData, updateData }) {
  const handleSelect = (preset) => {
    updateData({
      goal: preset.id,
      modules: preset.modules,
      estimatedTime: preset.time,
      riskLevel: preset.risk,
    });
  };

  return (
    <div className="step-goal">
      <h3>What do you want to scan?</h3>
      <p className="step-subtitle">
        Pick a preset or customize your modules on the next screen.
      </p>

      <div className="goal-grid">
        {SCAN_PRESETS.map((preset) => (
          <div
            key={preset.id}
            className={`goal-card ${wizardData.goal === preset.id ? "selected" : ""}`}
            onClick={() => handleSelect(preset)}
          >
            <div className="goal-header">
              <span className="goal-title">{preset.title}</span>
              <span className={`risk-label risk-${preset.risk}`}>
                {preset.risk}
              </span>
            </div>
            <p className="goal-description">{preset.description}</p>
            <div className="goal-meta">
              <span className="time">⏱ {preset.time}</span>
            </div>
          </div>
        ))}
      </div>

      {wizardData.goal && (
        <div className="goal-summary">
          <h4>✓ Selected Modules:</h4>
          <p>
            {Object.entries(wizardData.modules)
              .filter(([, v]) => v)
              .map(([k]) => k.charAt(0).toUpperCase() + k.slice(1))
              .join(", ") || "None selected"}
          </p>
        </div>
      )}
    </div>
  );
}
