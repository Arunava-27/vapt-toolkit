import { useState } from "react";
import Step1_Goal from "./wizard/Step1_Goal";
import Step2_Target from "./wizard/Step2_Target";
import Step3_Modules from "./wizard/Step3_Modules";
import Step4_Review from "./wizard/Step4_Review";
import "./ScanWizard.css";

export default function ScanWizard({ onScan, onCancel, scanning }) {
  const [step, setStep] = useState(1);
  const [wizardData, setWizardData] = useState({
    goal: null,
    targets: [],
    classification: "active",
    modules: {},
    estimatedTime: 0,
    riskLevel: "medium",
  });

  const updateData = (patch) => {
    setWizardData({ ...wizardData, ...patch });
  };

  const nextStep = () => setStep(step + 1);
  const prevStep = () => setStep(step > 1 ? step - 1 : 1);

  const handleLaunch = async () => {
    // Convert wizard data to scan config format
    const config = {
      target: wizardData.targets[0], // First target
      scan_classification: wizardData.classification,
      recon: wizardData.modules.recon || false,
      ports: wizardData.modules.ports || false,
      web_vulnerability_scan: wizardData.modules.web || false,
      cve: wizardData.modules.cve || false,
      full_scan: wizardData.modules.full_scan || false,
      ...wizardData.advancedOptions,
    };

    // For bulk targets, call bulk API instead
    if (wizardData.targets.length > 1) {
      // TODO: Handle bulk scanning
      console.log("Bulk scan config:", config, wizardData.targets);
    }

    await onScan(config);
  };

  return (
    <div className="scan-wizard">
      <div className="wizard-header">
        <h2>🚀 Smart Scan Wizard</h2>
        <p>Find the right scan for your needs</p>
      </div>

      <div className="wizard-progress">
        {[1, 2, 3, 4].map((s) => (
          <div
            key={s}
            className={`progress-step ${step === s ? "active" : ""} ${
              s < step ? "completed" : ""
            }`}
          >
            <span className="step-number">{s}</span>
            <span className="step-label">
              {["Goal", "Target", "Modules", "Review"][s - 1]}
            </span>
          </div>
        ))}
      </div>

      <div className="wizard-content">
        {step === 1 && (
          <Step1_Goal wizardData={wizardData} updateData={updateData} />
        )}
        {step === 2 && (
          <Step2_Target wizardData={wizardData} updateData={updateData} />
        )}
        {step === 3 && (
          <Step3_Modules wizardData={wizardData} updateData={updateData} />
        )}
        {step === 4 && (
          <Step4_Review wizardData={wizardData} updateData={updateData} />
        )}
      </div>

      <div className="wizard-footer">
        <button
          className="btn-secondary"
          onClick={step === 1 ? onCancel : prevStep}
          disabled={scanning}
        >
          {step === 1 ? "Cancel" : "← Back"}
        </button>

        <div className="wizard-info">
          <span className="time-est">⏱ {wizardData.estimatedTime}</span>
          <span className={`risk-badge risk-${wizardData.riskLevel}`}>
            {wizardData.riskLevel?.toUpperCase()}
          </span>
        </div>

        {step < 4 ? (
          <button
            className="btn-primary"
            onClick={nextStep}
            disabled={
              (step === 1 && !wizardData.goal) ||
              (step === 2 && wizardData.targets.length === 0)
            }
          >
            Next →
          </button>
        ) : (
          <button
            className="btn-scan"
            onClick={handleLaunch}
            disabled={scanning}
          >
            {scanning ? "Scanning..." : "🚀 Launch Scan"}
          </button>
        )}
      </div>
    </div>
  );
}
