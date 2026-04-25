import "./Step4_Review.css";

export default function Step4_Review({ wizardData, onLaunchScan }) {
  const goalNames = {
    recon: "Quick Reconnaissance",
    ports: "Find Open Services",
    web: "Web Vulnerabilities",
    full: "Full Assessment",
    compliance: "Compliance Audit",
    custom: "Custom Scan",
  };

  const selectedModules = Object.entries(wizardData.modules)
    .filter(([, enabled]) => enabled)
    .map(([name]) => name);

  const riskColors = {
    low: "#10b981",
    medium: "#f59e0b",
    high: "#ef4444",
    "very-high": "#7f1d1d",
  };

  return (
    <div className="step-review">
      <h3>Review & Launch Scan</h3>
      <p className="step-subtitle">
        Everything looks good? Click "Start Scan" to begin.
      </p>

      <div className="review-cards">
        {/* Goal Summary */}
        <div className="review-card">
          <div className="card-icon">🎯</div>
          <div className="card-content">
            <h4>Scanning Goal</h4>
            <p className="card-value">{goalNames[wizardData.goal]}</p>
            <p className="card-description">
              {wizardData.goal === "custom"
                ? "Custom configuration"
                : wizardData.classification === "passive"
                ? "Non-intrusive scanning"
                : wizardData.classification === "active"
                ? "Intrusive scanning"
                : "All modules enabled"}
            </p>
          </div>
        </div>

        {/* Target Summary */}
        <div className="review-card">
          <div className="card-icon">🎯</div>
          <div className="card-content">
            <h4>Targets</h4>
            <p className="card-value">
              {wizardData.targets.length === 1
                ? wizardData.targets[0]
                : `${wizardData.targets.length} targets`}
            </p>
            {wizardData.targets.length > 1 && (
              <div className="target-list-small">
                {wizardData.targets.map((target, i) => (
                  <span key={i} className="target-badge">
                    {target}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Modules Summary */}
        <div className="review-card">
          <div className="card-icon">📦</div>
          <div className="card-content">
            <h4>Modules</h4>
            <p className="card-value">{selectedModules.length} enabled</p>
            <div className="modules-badges">
              {selectedModules.map((mod) => (
                <span key={mod} className="module-badge">
                  {mod}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Risk & Time */}
        <div className="review-card">
          <div className="card-icon">⏱</div>
          <div className="card-content">
            <h4>Risk & Duration</h4>
            <p className="risk-assessment">
              <span
                className="risk-indicator"
                style={{ backgroundColor: riskColors[wizardData.riskLevel] }}
              >
                {wizardData.riskLevel}
              </span>
            </p>
            <p className="card-description">
              Estimated time: {wizardData.estimatedTime}
            </p>
          </div>
        </div>
      </div>

      {/* Important Notes */}
      <div className="review-notes">
        <h4>⚠️ Important Notes</h4>
        <ul>
          {wizardData.classification === "active" && (
            <li>
              This is an <strong>active scan</strong> - it may trigger alerts on
              the target system
            </li>
          )}
          {wizardData.classification === "hybrid" && (
            <li>
              This is a <strong>hybrid scan</strong> - comprehensive and quite intrusive
            </li>
          )}
          {wizardData.targets.length > 1 && (
            <li>
              Scanning <strong>{wizardData.targets.length} targets</strong> - total
              time will be multiplied
            </li>
          )}
          <li>
            Make sure you have <strong>permission</strong> to scan these targets
          </li>
        </ul>
      </div>

      {/* Action Buttons */}
      <div className="review-actions">
        <button className="btn-launch" onClick={onLaunchScan}>
          🚀 Start Scan
        </button>
        <p className="action-hint">
          You'll be able to monitor progress in real-time
        </p>
      </div>
    </div>
  );
}
