import "./Step2_Target.css";

export default function Step2_Target({ wizardData, updateData }) {
  const handleTargetChange = (e) => {
    const input = e.target.value;
    // Split by comma or newline for bulk input
    const targets = input
      .split(/[,\n]+/)
      .map((t) => t.trim())
      .filter((t) => t.length > 0);
    updateData({ targets });
  };

  return (
    <div className="step-target">
      <h3>Where do you want to scan?</h3>
      <p className="step-subtitle">
        Enter a single target or multiple targets (one per line or comma-separated)
      </p>

      <div className="target-input-section">
        <label>Target(s)</label>
        <textarea
          className="target-input"
          placeholder={`Examples:\n192.168.1.1\nexample.com\n10.0.0.1, 10.0.0.2, 10.0.0.3`}
          value={wizardData.targets.join("\n")}
          onChange={handleTargetChange}
          rows="5"
        />
        <p className="target-hint">
          Supports: IP addresses, domain names, HTTP(S) URLs
        </p>
      </div>

      {wizardData.targets.length > 0 && (
        <div className="target-preview">
          <h4>
            📍 {wizardData.targets.length === 1 ? "1 target" : `${wizardData.targets.length} targets`}
          </h4>
          <div className="target-list">
            {wizardData.targets.map((target, i) => (
              <div key={i} className="target-item">
                <span className="target-icon">
                  {target.includes("://") ? "🌐" : /^\d/.test(target) ? "📡" : "🌍"}
                </span>
                <span className="target-text">{target}</span>
                <span className="target-idx">#{i + 1}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {wizardData.targets.length > 1 && (
        <div className="bulk-info">
          <span className="info-icon">ℹ️</span>
          <div>
            <strong>Bulk Scanning Mode</strong>
            <p>
              All {wizardData.targets.length} targets will be scanned with the same configuration.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
