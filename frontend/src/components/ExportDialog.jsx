import React, { useState } from "react";
import "../styles/ExportDialog.css";

export default function ExportDialog({ projectId, projectName, onClose }) {
  const [selectedFormat, setSelectedFormat] = useState("json");
  const [includeMetadata, setIncludeMetadata] = useState(true);
  const [includeEvidence, setIncludeEvidence] = useState(true);
  const [filterSeverity, setFilterSeverity] = useState("");
  const [filterConfidence, setFilterConfidence] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const formats = [
    { value: "json", label: "JSON", description: "Pretty JSON with full details" },
    { value: "csv", label: "CSV", description: "Spreadsheet-compatible findings grid" },
    { value: "html", label: "HTML", description: "Standalone interactive report" },
    { value: "xlsx", label: "Excel", description: "Professional multi-sheet workbook" },
    { value: "markdown", label: "Markdown", description: "For GitHub and documentation" },
    { value: "sarif", label: "SARIF", description: "GitHub Security format" },
  ];

  const severityOptions = [
    { value: "", label: "All Severities" },
    { value: "critical", label: "Critical" },
    { value: "high", label: "High" },
    { value: "medium", label: "Medium" },
    { value: "low", label: "Low" },
  ];

  const confidenceOptions = [
    { value: "", label: "All Confidence Levels" },
    { value: "high", label: "High" },
    { value: "medium", label: "Medium" },
    { value: "low", label: "Low" },
  ];

  const getFileExtension = () => {
    const extensions = {
      json: "json",
      csv: "csv",
      html: "html",
      xlsx: "xlsx",
      markdown: "md",
      sarif: "sarif.json",
    };
    return extensions[selectedFormat] || "txt";
  };

  const buildQueryParams = () => {
    const params = new URLSearchParams();
    params.append("format", selectedFormat);
    params.append("include_metadata", includeMetadata);
    params.append("include_evidence", includeEvidence);
    if (filterSeverity) params.append("severity", filterSeverity);
    if (filterConfidence) params.append("confidence", filterConfidence);
    return params.toString();
  };

  const handleExport = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const queryParams = buildQueryParams();
      const url = `/api/exports/scan/${projectId}?${queryParams}`;

      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Export failed: ${response.statusText}`);
      }

      // Handle different content types
      const contentType = response.headers.get("content-type");
      let blob;

      if (contentType && contentType.includes("application/json")) {
        const text = await response.text();
        blob = new Blob([text], { type: "application/json" });
      } else if (contentType && contentType.includes("text/csv")) {
        const text = await response.text();
        blob = new Blob([text], { type: "text/csv" });
      } else if (contentType && contentType.includes("text/html")) {
        const text = await response.text();
        blob = new Blob([text], { type: "text/html" });
      } else if (contentType && contentType.includes("text/markdown")) {
        const text = await response.text();
        blob = new Blob([text], { type: "text/markdown" });
      } else {
        blob = await response.blob();
      }

      // Trigger download
      const downloadUrl = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = downloadUrl;
      const timestamp = new Date().toISOString().split("T")[0];
      link.download = `${projectName}-export-${timestamp}.${getFileExtension()}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(downloadUrl);

      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="export-dialog-overlay" onClick={onClose}>
      <div className="export-dialog" onClick={(e) => e.stopPropagation()}>
        <div className="export-dialog-header">
          <h2>Export Scan Results</h2>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        <div className="export-dialog-body">
          {/* Format Selection */}
          <div className="export-section">
            <h3>Export Format</h3>
            <div className="format-grid">
              {formats.map((format) => (
                <div key={format.value} className="format-card">
                  <input
                    type="radio"
                    name="format"
                    value={format.value}
                    checked={selectedFormat === format.value}
                    onChange={(e) => setSelectedFormat(e.target.value)}
                    id={`format-${format.value}`}
                  />
                  <label htmlFor={`format-${format.value}`}>
                    <div className="format-label">{format.label}</div>
                    <div className="format-description">{format.description}</div>
                  </label>
                </div>
              ))}
            </div>
          </div>

          {/* Options */}
          <div className="export-section">
            <h3>Export Options</h3>
            <div className="options-grid">
              <label className="checkbox-option">
                <input
                  type="checkbox"
                  checked={includeMetadata}
                  onChange={(e) => setIncludeMetadata(e.target.checked)}
                />
                <span className="checkbox-label">Include Metadata</span>
                <span className="checkbox-help">Scan date, target, modules, duration</span>
              </label>

              <label className="checkbox-option">
                <input
                  type="checkbox"
                  checked={includeEvidence}
                  onChange={(e) => setIncludeEvidence(e.target.checked)}
                />
                <span className="checkbox-label">Include Evidence</span>
                <span className="checkbox-help">Screenshots, logs, technical details</span>
              </label>
            </div>
          </div>

          {/* Filtering */}
          <div className="export-section">
            <h3>Filter Findings</h3>
            <div className="filter-grid">
              <div className="filter-item">
                <label htmlFor="severity-filter">Severity Level</label>
                <select
                  id="severity-filter"
                  value={filterSeverity}
                  onChange={(e) => setFilterSeverity(e.target.value)}
                >
                  {severityOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="filter-item">
                <label htmlFor="confidence-filter">Confidence Level</label>
                <select
                  id="confidence-filter"
                  value={filterConfidence}
                  onChange={(e) => setFilterConfidence(e.target.value)}
                >
                  {confidenceOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {error && <div className="error-message">{error}</div>}
        </div>

        <div className="export-dialog-footer">
          <button className="btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button
            className="btn-primary"
            onClick={handleExport}
            disabled={isLoading}
          >
            {isLoading ? "Exporting..." : "Download Export"}
          </button>
        </div>
      </div>
    </div>
  );
}
