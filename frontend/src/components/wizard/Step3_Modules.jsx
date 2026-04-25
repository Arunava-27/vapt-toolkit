import "./Step3_Modules.css";

const MODULE_INFO = {
  recon: {
    name: "Reconnaissance",
    description: "OSINT, DNS lookup, WHOIS, reverse DNS",
    risk: "low",
    time: "20s",
  },
  ports: {
    name: "Port Scanning",
    description: "Nmap port scan, service detection, banner grabbing",
    risk: "medium",
    time: "30s - 1m",
  },
  web: {
    name: "Web Vulnerabilities",
    description: "XSS, SQLi, CSRF, auth flaws, exposed endpoints",
    risk: "high",
    time: "1-3m",
  },
  cve: {
    name: "CVE Detection",
    description: "Known vulnerabilities, version detection, exploit lookup",
    risk: "low",
    time: "30s",
  },
  full_scan: {
    name: "Full Deep Scan",
    description: "All modules with aggressive settings",
    risk: "very-high",
    time: "5-10m",
  },
};

export default function Step3_Modules({ wizardData, updateData }) {
  const handleModuleToggle = (module) => {
    const updatedModules = {
      ...wizardData.modules,
      [module]: !wizardData.modules[module],
    };
    updateData({ modules: updatedModules });
  };

  const selectedCount = Object.values(wizardData.modules).filter(Boolean).length;
  const isCustom = wizardData.goal === "custom";

  return (
    <div className="step-modules">
      <h3>
        {isCustom ? "Select Modules" : "Recommended Modules"}
      </h3>
      <p className="step-subtitle">
        {isCustom
          ? "Choose exactly which scanning modules to enable"
          : "These modules are recommended for your selected goal. You can customize if needed."}
      </p>

      <div className="modules-grid">
        {Object.entries(MODULE_INFO).map(([moduleKey, moduleInfo]) => (
          <div
            key={moduleKey}
            className={`module-card ${
              wizardData.modules[moduleKey] ? "selected" : ""
            }`}
            onClick={() => handleModuleToggle(moduleKey)}
          >
            <div className="module-checkbox">
              {wizardData.modules[moduleKey] ? "✓" : ""}
            </div>
            <h4>{moduleInfo.name}</h4>
            <p className="module-description">{moduleInfo.description}</p>
            <div className="module-meta">
              <span
                className={`risk-badge risk-${moduleInfo.risk}`}
              >
                {moduleInfo.risk}
              </span>
              <span className="time-badge">⏱ {moduleInfo.time}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="modules-summary">
        <div className="summary-stats">
          <span className="stat">
            📦 {selectedCount} module{selectedCount !== 1 ? "s" : ""} selected
          </span>
          <span className="stat">
            ⏱ ~{calculateTotalTime(wizardData.modules)} minutes
          </span>
        </div>
      </div>

      {selectedCount === 0 && (
        <div className="warning-message">
          ⚠️ Please select at least one module to scan
        </div>
      )}
    </div>
  );
}

function calculateTotalTime(modules) {
  const times = {
    recon: 0.33, // 20s
    ports: 0.75, // 30s-1m
    web: 2, // 1-3m
    cve: 0.5, // 30s
    full_scan: 7.5, // 5-10m
  };
  return Object.entries(modules)
    .filter(([, enabled]) => enabled)
    .reduce((sum, [module]) => sum + (times[module] || 1), 0)
    .toFixed(0);
}
