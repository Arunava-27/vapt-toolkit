import { useState } from "react";
import { Link } from "react-router-dom";
import { useScan } from "../context/ScanContext";
import ScanForm         from "../components/ScanForm";
import ProgressLog      from "../components/ProgressLog";
import ScanStatus       from "../components/ScanStatus";
import ResultsDashboard from "../components/ResultsDashboard";
import ResizableLayout  from "../components/ResizableLayout";
import ScheduleManager  from "../components/ScheduleManager";
import ScanInstructionBuilder from "../components/ScanInstructionBuilder";
import ScanWizard       from "../components/wizard/ScanWizard";

const DEFAULT_CONFIG = {
  target: "", recon: false, ports: false, cve: false, web: false,
  full_scan: false,
  port_range: "top-1000",
  scan_type: "connect",
  version_detect: false,
  os_detect: false,
  port_script: "",
  port_timing: 4,
  skip_ping: false,
  port_extra_flags: "",
  web_depth: 1,
  recon_wordlist: "subdomains-top5000.txt",
  scan_classification: "active",
};

const LEVEL_ICON = { error: "🚫", warning: "⚠️", info: "ℹ️" };
const LEVEL_COLOR = { error: "var(--red)", warning: "var(--orange)", info: "var(--accent)" };

function WarningsDialog({ warnings, onProceed, onCancel }) {
  const hasErrors = warnings.some((w) => w.level === "error");
  return (
    <div className="modal-backdrop">
      <div className="modal">
        <h3 style={{ marginBottom: "1rem" }}>⚠️ Scan Warnings</h3>
        <div style={{ display: "flex", flexDirection: "column", gap: ".6rem", marginBottom: "1.25rem" }}>
          {warnings.map((w, i) => (
            <div key={i} style={{
              display: "flex", gap: ".6rem", alignItems: "flex-start",
              padding: ".6rem .75rem", borderRadius: 6,
              background: "var(--bg2)", borderLeft: `3px solid ${LEVEL_COLOR[w.level]}`,
            }}>
              <span style={{ fontSize: "1rem", marginTop: 1 }}>{LEVEL_ICON[w.level]}</span>
              <span style={{ fontSize: ".82rem", lineHeight: 1.5, color: "var(--text)" }}>{w.message}</span>
            </div>
          ))}
        </div>
        <div style={{ display: "flex", gap: ".6rem", justifyContent: "flex-end" }}>
          <button className="btn-secondary" onClick={onCancel}>Cancel</button>
          {!hasErrors && (
            <button className="btn-scan" style={{ padding: ".5rem 1.25rem", fontSize: ".9rem" }}
                    onClick={onProceed}>
              Proceed Anyway
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ScanPage() {
  const [config, setConfig] = useState(DEFAULT_CONFIG);
  const [warnings, setWarnings] = useState(null);
  const [pendingConfig, setPendingConfig] = useState(null);
  const [showScheduler, setShowScheduler] = useState(false);
  const [scanMode, setScanMode] = useState("wizard"); // "wizard", "form" or "json"
  const [showWizard, setShowWizard] = useState(false);

  const {
    scanning, canResume, log, results, moduleStatus,
    activatedModules, savedProject, setSavedProject,
    startScan, stopScan, resumeScan, getElapsed,
  } = useScan();

  const hasResults = Object.keys(results).length > 0;

  const handleScan = async (scanConfig = config) => {
    try {
      const res  = await fetch("/api/scan/validate", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(scanConfig),
      });
      const data = await res.json();
      if (data.warnings && data.warnings.length > 0) {
        setWarnings(data.warnings);
        setPendingConfig(scanConfig);
      } else {
        setConfig(scanConfig);
        startScan(scanConfig);
      }
    } catch {
      startScan(scanConfig); // validation failed → proceed anyway
    }
  };

  const handleProceed = () => {
    setWarnings(null);
    startScan(pendingConfig);
  };

  const handleWizardScanStart = (wizardRequest) => {
    // Create a clean config object with only the modules selected
    const cleanConfig = {
      target: String(wizardRequest.targets[0] || ""),
      recon: Boolean(wizardRequest.modules.recon),
      ports: Boolean(wizardRequest.modules.ports),
      cve: Boolean(wizardRequest.modules.cve),
      web: Boolean(wizardRequest.modules.web),
      full_scan: false,
      port_range: "top-1000",
      scan_type: "connect",
      version_detect: true,
      os_detect: true,
      port_script: "",
      port_timing: 4,
      skip_ping: true,
      port_extra_flags: "",
      web_depth: 1,
      recon_wordlist: "subdomains-top5000.txt",
      scan_classification: "active", // Just use active by default - let modules define behavior
    };
    
    // If multiple targets, use bulk API
    if (wizardRequest.targets && wizardRequest.targets.length > 1) {
      handleBulkScan(wizardRequest.targets, cleanConfig);
    } else {
      setConfig(cleanConfig);
      handleScan(cleanConfig);
    }
    
    setShowWizard(false);
  };

  const handleBulkScan = async (targets, baseConfig) => {
    try {
      const res = await fetch("/api/scan/bulk", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          targets,
          config: baseConfig,
        }),
      });
      const data = await res.json();
      if (data.success) {
        // Bulk scan started - refresh or navigate to projects
        window.location.href = "/projects";
      }
    } catch (error) {
      console.error("Bulk scan failed:", error);
      alert("Failed to start bulk scan. Please try again.");
    }
  };

  return (
    <>
      {showWizard && (
        <ScanWizard 
          onScanStart={handleWizardScanStart} 
          onCancel={() => setShowWizard(false)} 
        />
      )}

      {warnings && (
        <WarningsDialog
          warnings={warnings}
          onProceed={handleProceed}
          onCancel={() => { setWarnings(null); setPendingConfig(null); }}
        />
      )}

      <ResizableLayout sidebar={
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem", height: "100%", overflowY: "auto" }}>
          {/* Scan Mode Tabs */}
          <div style={{
            display: "flex",
            gap: "0.5rem",
            borderBottom: "2px solid var(--bg2)",
            paddingBottom: "0.5rem",
            flexWrap: "wrap",
          }}>
            <button
              onClick={() => { setScanMode("wizard"); setShowWizard(true); }}
              style={{
                padding: "0.5rem 1rem",
                background: "var(--accent)",
                color: "var(--bg-primary)",
                border: "none",
                borderRadius: 4,
                cursor: "pointer",
                fontSize: "0.9rem",
                fontWeight: "600",
                transition: "all 0.2s",
              }}
              title="Quick guided scan"
            >
              🧙 Smart Wizard
            </button>
            <button
              onClick={() => setScanMode("form")}
              style={{
                padding: "0.5rem 1rem",
                background: scanMode === "form" ? "var(--accent)" : "transparent",
                color: scanMode === "form" ? "var(--bg-primary)" : "var(--text)",
                border: "none",
                borderRadius: 4,
                cursor: "pointer",
                fontSize: "0.9rem",
                fontWeight: scanMode === "form" ? "600" : "400",
                transition: "all 0.2s",
              }}
              title="Advanced form with all options"
            >
              📋 Advanced
            </button>
            <button
              onClick={() => setScanMode("json")}
              style={{
                padding: "0.5rem 1rem",
                background: scanMode === "json" ? "var(--accent)" : "transparent",
                color: scanMode === "json" ? "var(--bg-primary)" : "var(--text)",
                border: "none",
                borderRadius: 4,
                cursor: "pointer",
                fontSize: "0.9rem",
                fontWeight: scanMode === "json" ? "600" : "400",
                transition: "all 0.2s",
              }}
              title="JSON-based instructions for automation"
            >
              📝 JSON API
            </button>
          </div>

          {/* Form Mode */}
          {scanMode === "form" && (
            <>
              <ScanForm config={config} onChange={setConfig}
                onScan={handleScan}
                scanning={scanning} />
              
              {savedProject && (
                <div style={{ padding: "1rem", borderRadius: 8, background: "var(--bg2)" }}>
                  <div style={{ fontSize: "0.9rem", marginBottom: "0.5rem" }}>
                    💾 Saved as <strong>{savedProject.name}</strong>
                  </div>
                  <button
                    className="btn-secondary"
                    onClick={() => setShowScheduler(!showScheduler)}
                    style={{ width: "100%", marginBottom: "0.5rem" }}
                  >
                    {showScheduler ? "Hide" : "📅 Schedule"}
                  </button>
                  <Link className="save-banner-link" to={`/projects/${savedProject.id}`}
                    style={{ display: "block", textAlign: "center", marginBottom: "0.5rem" }}>
                    View project →
                  </Link>
                  <button className="btn-secondary" onClick={() => setSavedProject(null)} style={{ width: "100%" }}>
                    Clear
                  </button>
                </div>
              )}
              
              {savedProject && showScheduler && (
                <ScheduleManager projectId={savedProject.id} />
              )}
            </>
          )}

          {/* JSON Mode */}
          {scanMode === "json" && (
            <ScanInstructionBuilder onScanStart={handleScan} />
          )}
        </div>
      }>
        {log.length === 0 && !hasResults && (
          <div className="empty">
            <div className="hero">🛡️</div>
            <h2>Ready to scan</h2>
            <p>Enter a target, choose modules, and hit <strong>Run Scan</strong>.</p>
          </div>
        )}

        {(scanning || canResume) && activatedModules.length > 0 && (
          <ScanStatus moduleStatus={moduleStatus} getElapsed={getElapsed}
            activatedModules={activatedModules} onStop={stopScan} onResume={resumeScan}
            scanning={scanning} canResume={canResume} />
        )}

        {log.length > 0 && <ProgressLog entries={log} />}
        <ResultsDashboard results={results} />
      </ResizableLayout>
    </>
  );
}

