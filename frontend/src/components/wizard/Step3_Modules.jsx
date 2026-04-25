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
    description: "Nmap scan, service detection, banner grabbing",
    risk: "medium",
    time: "30s - 2m",
  },
  web: {
    name: "Web Vulnerabilities",
    description: "XSS, SQLi, CSRF, auth flaws, path traversal",
    risk: "high",
    time: "1-3m",
  },
  cve: {
    name: "CVE Lookup",
    description: "Known CVEs for detected services/versions",
    risk: "low",
    time: "30s",
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

  return (
    <div className="step-modules">
      <h3>Customize Modules (Optional)</h3>
      <p className="step-subtitle">
        Adjust the modules that will run. You can enable/disable each independently.
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
    recon: 0.33,
    ports: 1,
    web: 2,
    cve: 0.5,
  };
  return Object.entries(modules)
    .filter(([, enabled]) => enabled)
    .reduce((sum, [module]) => sum + (times[module] || 1), 0)
    .toFixed(0);
}
