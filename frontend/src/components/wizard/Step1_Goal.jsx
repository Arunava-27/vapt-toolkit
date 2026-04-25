import "./Step1_Goal.css";

const SCAN_GOALS = [
  {
    id: "recon",
    title: "🔍 Quick Reconnaissance",
    description: "OSINT, DNS lookup. No port scanning. Safe.",
    classification: "passive",
    modules: { recon: true },
    time: "1-2 min",
    risk: "low",
    color: "green",
  },
  {
    id: "ports",
    title: "🚪 Find Open Services",
    description: "Discover open ports and running services. Moderate intrusion.",
    classification: "active",
    modules: { ports: true, recon: true, cve: true },
    time: "30s - 2 min",
    risk: "medium",
    color: "orange",
  },
  {
    id: "web",
    title: "🕸️ Web Vulnerabilities",
    description: "Find XSS, SQLi, CSRF, authentication flaws. Intrusive testing.",
    classification: "active",
    modules: { ports: true, web: true, cve: true },
    time: "1-3 min",
    risk: "high",
    color: "red",
  },
  {
    id: "full",
    title: "⚡ Full Assessment",
    description: "All modules: everything possible. Most intrusive.",
    classification: "hybrid",
    modules: { recon: true, ports: true, cve: true, web: true, full_scan: true },
    time: "5-10 min",
    risk: "very-high",
    color: "darkred",
  },
  {
    id: "compliance",
    title: "📋 Compliance Audit",
    description: "OWASP/CWE mapping, scope-enforced scanning.",
    classification: "passive",
    modules: { recon: true, cve: true },
    time: "2-5 min",
    risk: "low",
    color: "blue",
  },
  {
    id: "custom",
    title: "⚙️ Custom",
    description: "Choose exactly which modules to run.",
    classification: "hybrid",
    modules: {},
    time: "variable",
    risk: "variable",
    color: "gray",
  },
];

export default function Step1_Goal({ wizardData, updateData }) {
  const handleSelect = (goal) => {
    updateData({
      goal: goal.id,
      classification: goal.classification,
      modules: goal.modules,
      estimatedTime: goal.time,
      riskLevel: goal.risk,
    });
  };

  return (
    <div className="step-goal">
      <h3>What would you like to do?</h3>
      <p className="step-subtitle">
        Select a scanning goal and we'll recommend the right modules and
        settings.
      </p>

      <div className="goal-grid">
        {SCAN_GOALS.map((goal) => (
          <div
            key={goal.id}
            className={`goal-card ${wizardData.goal === goal.id ? "selected" : ""}`}
            onClick={() => handleSelect(goal)}
          >
            <div className={`goal-header color-${goal.color}`}>
              <span className="goal-title">{goal.title}</span>
              <span className="risk-label">{goal.risk}</span>
            </div>
            <p className="goal-description">{goal.description}</p>
            <div className="goal-meta">
              <span className="time">⏱ {goal.time}</span>
              <span className="classification">
                {goal.classification === "passive" && "🟢 Passive"}
                {goal.classification === "active" && "⚠️ Active"}
                {goal.classification === "hybrid" && "🔴 Hybrid"}
              </span>
            </div>
          </div>
        ))}
      </div>

      {wizardData.goal && (
        <div className="goal-summary">
          <h4>✓ Selected: {SCAN_GOALS.find((g) => g.id === wizardData.goal)?.title}</h4>
          <p>
            This scan will enable:{" "}
            <strong>
              {Object.entries(wizardData.modules)
                .filter(([, v]) => v)
                .map(([k]) => k)
                .join(", ") || "custom selection"}
            </strong>
          </p>
        </div>
      )}
    </div>
  );
}
