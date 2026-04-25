import { useState } from "react";
import Step1_Goal from "./Step1_Goal";
import Step2_Target from "./Step2_Target";
import Step3_Modules from "./Step3_Modules";
import Step4_Review from "./Step4_Review";
import "./ScanWizard.css";

export default function ScanWizard({ onScanStart, onCancel }) {
  const [currentStep, setCurrentStep] = useState(1);
  const [wizardData, setWizardData] = useState({
    goal: null,
    targets: [],
    modules: {},
    classification: null,
    estimatedTime: "variable",
    riskLevel: "unknown",
  });

  const updateData = (updates) => {
    setWizardData({ ...wizardData, ...updates });
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrev = () => {
    setCurrentStep(currentStep - 1);
  };

  const validateStep = (step) => {
    switch (step) {
      case 1:
        return wizardData.goal !== null;
      case 2:
        return wizardData.targets.length > 0;
      case 3:
        return Object.values(wizardData.modules).some((enabled) => enabled);
      default:
        return true;
    }
  };

  const handleLaunchScan = () => {
    const scanRequest = {
      targets: wizardData.targets,
      classification: wizardData.classification,
      modules: wizardData.modules,
      scanType: determineScanType(wizardData),
    };
    onScanStart(scanRequest);
  };

  const isStepValid = validateStep(currentStep);
  const canNext = isStepValid && currentStep < 4;
  const canPrev = currentStep > 1;

  return (
    <div className="scan-wizard-overlay">
      <div className="scan-wizard">
        {/* Header */}
        <div className="wizard-header">
          <h2>🚀 Smart Scan Wizard</h2>
          <button className="close-btn" onClick={onCancel}>
            ✕
          </button>
        </div>

        {/* Progress Bar */}
        <div className="wizard-progress">
          {[1, 2, 3, 4].map((step) => (
            <div
              key={step}
              className={`progress-step ${
                step === currentStep ? "active" : ""
              } ${step < currentStep ? "completed" : ""}`}
            >
              <div className="step-number">
                {step < currentStep ? "✓" : step}
              </div>
              <div className="step-label">
                {["Goal", "Target", "Modules", "Review"][step - 1]}
              </div>
            </div>
          ))}
        </div>

        {/* Step Content */}
        <div className="wizard-content">
          {currentStep === 1 && (
            <Step1_Goal wizardData={wizardData} updateData={updateData} />
          )}
          {currentStep === 2 && (
            <Step2_Target wizardData={wizardData} updateData={updateData} />
          )}
          {currentStep === 3 && (
            <Step3_Modules wizardData={wizardData} updateData={updateData} />
          )}
          {currentStep === 4 && (
            <Step4_Review
              wizardData={wizardData}
              onLaunchScan={handleLaunchScan}
            />
          )}
        </div>

        {/* Footer */}
        <div className="wizard-footer">
          <button
            className="btn-secondary"
            onClick={handlePrev}
            disabled={!canPrev}
          >
            ← Previous
          </button>

          {currentStep < 4 ? (
            <button
              className="btn-primary"
              onClick={handleNext}
              disabled={!canNext}
            >
              Next →
            </button>
          ) : null}
        </div>

        {/* Validation Message */}
        {!isStepValid && currentStep < 4 && (
          <div className="validation-error">
            {currentStep === 1 && "Please select a scanning goal"}
            {currentStep === 2 && "Please enter at least one target"}
            {currentStep === 3 && "Please select at least one module"}
          </div>
        )}
      </div>
    </div>
  );
}

function determineScanType(wizardData) {
  if (wizardData.classification === "passive") return "passive";
  if (wizardData.classification === "active") return "active";
  return "hybrid";
}
