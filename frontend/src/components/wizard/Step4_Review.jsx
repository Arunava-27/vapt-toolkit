import "./Step4_Review.css";

export default function Step4_Review({ wizardData, onLaunchScan }) {
  const goalNames = {
    quick: "Reconnaissance Only",
    ports: "Open Ports & Services",
    web: "Web Vulnerabilities",
    full: "Everything (Full Audit)",
    custom: "Custom Modules",
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
        {/* Target Summary */}
        <div className="review-card">
          <div className="card-icon">🎯</div>
          <div className="card-content">
            <h4>Target</h4>
            <p className="card-value">
              {wizardData.targets.length === 1
                ? wizardData.targets[0]
                : `${wizardData.targets.length} targets`}
            </p>
            {wizardData.targets.length > 1 && (
              <div className="target-list-small">
                {wizardData.targets.slice(0, 3).map((target, i) => (
                  <span key={i} className="target-badge">
                    {target}
                  </span>
                ))}
                {wizardData.targets.length > 3 && (
                  <span className="target-badge">
                    +{wizardData.targets.length - 3} more
                  </span>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Modules Summary */}
        <div className="review-card">
          <div className="card-icon">📦</div>
          <div className="card-content">
            <h4>Modules to Run</h4>
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

        {/* Time & Risk */}
        <div className="review-card">
          <div className="card-icon">⏱</div>
          <div className="card-content">
            <h4>Estimated Duration</h4>
            <p className="card-value">{wizardData.estimatedTime}</p>
            <p className="card-description">
              Risk Level:{" "}
              <span
                style={{
                  backgroundColor:
                    riskColors[wizardData.riskLevel] || "#6b7280",
                  color: "white",
                  padding: "2px 8px",
                  borderRadius: "4px",
                  fontSize: "12px",
                  fontWeight: "600",
                  textTransform: "capitalize",
                }}
              >
                {wizardData.riskLevel}
              </span>
            </p>
          </div>
        </div>
      </div>

      {/* Important Notes */}
      <div className="review-notes">
        <h4>⚠️ Scan Information</h4>
        <ul>
          {selectedModules.includes("ports") && (
            <li>
              <strong>Port scanning enabled</strong> - may trigger alerts on
              security systems
            </li>
          )}
          {selectedModules.includes("web") && (
            <li>
              <strong>Web testing enabled</strong> - will send HTTP requests to
              the target
            </li>
          )}
          {wizardData.targets.length > 1 && (
            <li>
              Scanning <strong>{wizardData.targets.length} targets</strong> -
              total time will multiply
            </li>
          )}
          <li>
            Make sure you have <strong>permission</strong> to scan this target
          </li>
        </ul>
      </div>

      {/* Action Buttons */}
      <div className="review-actions">
        <button className="btn-launch" onClick={onLaunchScan}>
          🚀 Start Scan
        </button>
        <p className="action-hint">
          You'll see results in real-time as modules complete
        </p>
      </div>
    </div>
  );
}
