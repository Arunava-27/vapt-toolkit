import React, { useState } from "react";

const AVAILABLE_SECTIONS = [
  { id: "header", name: "Header", icon: "📋" },
  { id: "summary", name: "Summary", icon: "📊" },
  { id: "findings", name: "Findings Grid", icon: "🔍" },
  { id: "remediation", name: "Remediation", icon: "🛠️" },
  { id: "footer", name: "Footer", icon: "📄" },
];

export default function TemplateBuilder() {
  const [sections, setSections] = useState([]);
  const [templateName, setTemplateName] = useState("");
  const [draggedSection, setDraggedSection] = useState(null);
  const [showCustomization, setShowCustomization] = useState(null);
  const [customization, setCustomization] = useState({});
  const [preview, setPreview] = useState("");
  const [loading, setLoading] = useState(false);

  const handleDragStart = (section) => {
    setDraggedSection(section);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (draggedSection) {
      const newSection = {
        id: `${draggedSection.id}_${Date.now()}`,
        type: draggedSection.id,
        name: draggedSection.name,
        settings: {},
      };
      setSections([...sections, newSection]);
      setDraggedSection(null);
    }
  };

  const removeSection = (sectionId) => {
    setSections(sections.filter((s) => s.id !== sectionId));
  };

  const moveSectionUp = (index) => {
    if (index > 0) {
      const newSections = [...sections];
      [newSections[index - 1], newSections[index]] = [
        newSections[index],
        newSections[index - 1],
      ];
      setSections(newSections);
    }
  };

  const moveSectionDown = (index) => {
    if (index < sections.length - 1) {
      const newSections = [...sections];
      [newSections[index], newSections[index + 1]] = [
        newSections[index + 1],
        newSections[index],
      ];
      setSections(newSections);
    }
  };

  const updateSectionSetting = (sectionId, key, value) => {
    setSections(
      sections.map((s) =>
        s.id === sectionId
          ? { ...s, settings: { ...s.settings, [key]: value } }
          : s
      )
    );
  };

  const generatePreview = () => {
    let html = "<html><head><style>";
    html += `
      body { font-family: Arial, sans-serif; margin: 20px; color: #333; }
      h1 { color: #2196F3; border-bottom: 3px solid #2196F3; }
      h2 { color: #2196F3; margin-top: 20px; }
      table { width: 100%; border-collapse: collapse; }
      th, td { padding: 10px; text-align: left; border: 1px solid #ddd; }
      th { background: #2196F3; color: white; }
    `;
    html += "</style></head><body>";

    sections.forEach((section) => {
      switch (section.type) {
        case "header":
          html += `<h1>${section.settings.title || "Report Title"}</h1>`;
          break;
        case "summary":
          html += "<h2>Summary</h2><p>Project: Sample Project<br/>Target: example.com</p>";
          break;
        case "findings":
          html += `<h2>Findings</h2>
            <table>
              <tr><th>Issue</th><th>Severity</th><th>Status</th></tr>
              <tr><td>XSS Vulnerability</td><td>High</td><td>Open</td></tr>
              <tr><td>Weak Password</td><td>Medium</td><td>Open</td></tr>
            </table>`;
          break;
        case "remediation":
          html += "<h2>Remediation</h2><ol><li>Fix XSS issues</li><li>Enforce strong passwords</li></ol>";
          break;
        case "footer":
          html += "<hr><p style='font-size: 12px; color: #666;'>This report is confidential.</p>";
          break;
        default:
          break;
      }
    });

    html += "</body></html>";
    setPreview(html);
  };

  const handleSaveTemplate = async () => {
    if (!templateName.trim()) {
      alert("Please enter a template name");
      return;
    }

    if (sections.length === 0) {
      alert("Please add at least one section");
      return;
    }

    try {
      setLoading(true);
      generatePreview();

      const templateConfig = {
        sections: sections.map((s) => ({
          type: s.type,
          settings: s.settings,
        })),
      };

      const response = await fetch("/api/templates/report/preset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: templateName,
          config: templateConfig,
        }),
      });

      if (response.ok) {
        alert("Template saved successfully!");
        setTemplateName("");
        setSections([]);
        setPreview("");
      } else {
        alert("Failed to save template");
      }
    } catch (error) {
      console.error("Error saving template:", error);
      alert("Error saving template");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="template-builder">
      <div className="builder-header">
        <h2>Visual Template Builder</h2>
        <input
          type="text"
          placeholder="Template name"
          value={templateName}
          onChange={(e) => setTemplateName(e.target.value)}
          className="template-name-input"
        />
      </div>

      <div className="builder-container">
        {/* Left - Available Sections */}
        <div className="available-sections">
          <h3>Available Sections</h3>
          <p className="hint">Drag sections to the canvas below</p>
          <div className="sections-list">
            {AVAILABLE_SECTIONS.map((section) => (
              <div
                key={section.id}
                className="section-item draggable"
                draggable
                onDragStart={() => handleDragStart(section)}
              >
                <span className="section-icon">{section.icon}</span>
                <span>{section.name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Center - Canvas */}
        <div className="canvas-area">
          <div
            className="canvas"
            onDragOver={handleDragOver}
            onDrop={handleDrop}
          >
            <div className="canvas-header">
              <h3>Template Canvas</h3>
              <p className="hint">Drop sections here to build template</p>
            </div>

            {sections.length === 0 ? (
              <div className="canvas-empty">
                <p>Drag sections here to build your template</p>
              </div>
            ) : (
              <div className="sections-stack">
                {sections.map((section, index) => (
                  <div key={section.id} className="canvas-section">
                    <div className="section-header">
                      <span className="section-name">{section.name}</span>
                      <div className="section-controls">
                        <button
                          className="btn-mini"
                          onClick={() => moveSectionUp(index)}
                          disabled={index === 0}
                          title="Move up"
                        >
                          ↑
                        </button>
                        <button
                          className="btn-mini"
                          onClick={() => moveSectionDown(index)}
                          disabled={index === sections.length - 1}
                          title="Move down"
                        >
                          ↓
                        </button>
                        <button
                          className="btn-mini settings"
                          onClick={() =>
                            setShowCustomization(
                              showCustomization === section.id
                                ? null
                                : section.id
                            )
                          }
                          title="Customize"
                        >
                          ⚙️
                        </button>
                        <button
                          className="btn-mini remove"
                          onClick={() => removeSection(section.id)}
                          title="Remove"
                        >
                          ✕
                        </button>
                      </div>
                    </div>

                    {showCustomization === section.id && (
                      <div className="section-customization">
                        {section.type === "header" && (
                          <>
                            <label>
                              Title:
                              <input
                                type="text"
                                value={section.settings.title || ""}
                                onChange={(e) =>
                                  updateSectionSetting(
                                    section.id,
                                    "title",
                                    e.target.value
                                  )
                                }
                                placeholder="Report Title"
                              />
                            </label>
                          </>
                        )}

                        {section.type === "summary" && (
                          <>
                            <label>
                              <input
                                type="checkbox"
                                checked={section.settings.show_project || false}
                                onChange={(e) =>
                                  updateSectionSetting(
                                    section.id,
                                    "show_project",
                                    e.target.checked
                                  )
                                }
                              />
                              Show Project Name
                            </label>
                            <label>
                              <input
                                type="checkbox"
                                checked={section.settings.show_date || false}
                                onChange={(e) =>
                                  updateSectionSetting(
                                    section.id,
                                    "show_date",
                                    e.target.checked
                                  )
                                }
                              />
                              Show Date
                            </label>
                          </>
                        )}

                        {section.type === "findings" && (
                          <>
                            <label>
                              Results per page:
                              <input
                                type="number"
                                value={section.settings.limit || 10}
                                onChange={(e) =>
                                  updateSectionSetting(
                                    section.id,
                                    "limit",
                                    parseInt(e.target.value)
                                  )
                                }
                                min="1"
                                max="100"
                              />
                            </label>
                            <label>
                              <input
                                type="checkbox"
                                checked={section.settings.show_severity || true}
                                onChange={(e) =>
                                  updateSectionSetting(
                                    section.id,
                                    "show_severity",
                                    e.target.checked
                                  )
                                }
                              />
                              Show Severity
                            </label>
                          </>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right - Preview */}
        <div className="preview-panel">
          <div className="preview-header">
            <h3>Live Preview</h3>
            <button
              className="btn-refresh"
              onClick={generatePreview}
              disabled={loading}
            >
              🔄 Refresh
            </button>
          </div>
          {preview ? (
            <iframe
              title="Template Preview"
              srcDoc={preview}
              className="preview-iframe"
            />
          ) : (
            <div className="preview-empty">
              <p>Preview will appear here</p>
            </div>
          )}
        </div>
      </div>

      <div className="builder-footer">
        <button
          className="btn-primary"
          onClick={handleSaveTemplate}
          disabled={loading || sections.length === 0}
        >
          💾 Save Template
        </button>
      </div>

      <style>{`
        .template-builder {
          padding: 20px;
          background: #f5f5f5;
          border-radius: 8px;
        }

        .builder-header {
          display: flex;
          gap: 20px;
          align-items: center;
          margin-bottom: 20px;
        }

        .template-name-input {
          padding: 10px 15px;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 14px;
          flex: 1;
          max-width: 300px;
        }

        .builder-container {
          display: grid;
          grid-template-columns: 200px 1fr 250px;
          gap: 20px;
          margin-bottom: 20px;
        }

        .available-sections {
          background: white;
          padding: 15px;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .available-sections h3 {
          margin-top: 0;
        }

        .hint {
          font-size: 12px;
          color: #999;
          margin: 10px 0;
        }

        .sections-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .section-item {
          padding: 10px;
          background: #f0f0f0;
          border: 1px solid #ddd;
          border-radius: 4px;
          cursor: move;
          display: flex;
          gap: 8px;
          align-items: center;
          transition: all 0.2s;
        }

        .section-item:hover {
          background: #e0e0e0;
          border-color: #2196F3;
        }

        .section-icon {
          font-size: 18px;
        }

        .canvas-area {
          background: white;
          padding: 15px;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .canvas {
          min-height: 400px;
          border: 2px dashed #2196F3;
          border-radius: 4px;
          padding: 15px;
          background: #fafafa;
        }

        .canvas-header h3 {
          margin-top: 0;
        }

        .canvas-empty {
          text-align: center;
          color: #999;
          padding: 60px 20px;
        }

        .sections-stack {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .canvas-section {
          background: white;
          border: 1px solid #ddd;
          border-radius: 4px;
          overflow: hidden;
        }

        .section-header {
          background: #f9f9f9;
          padding: 10px 12px;
          display: flex;
          justify-content: space-between;
          align-items: center;
          border-bottom: 1px solid #ddd;
        }

        .section-name {
          font-weight: bold;
          color: #333;
        }

        .section-controls {
          display: flex;
          gap: 4px;
        }

        .btn-mini {
          padding: 4px 8px;
          border: 1px solid #ddd;
          background: white;
          border-radius: 3px;
          cursor: pointer;
          font-size: 12px;
        }

        .btn-mini:hover:not(:disabled) {
          background: #f0f0f0;
        }

        .btn-mini:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .btn-mini.settings:hover {
          background: #ffd54f;
        }

        .btn-mini.remove:hover {
          background: #f44336;
          color: white;
          border-color: #f44336;
        }

        .section-customization {
          padding: 12px;
          background: #f0f8ff;
          border-top: 1px solid #ddd;
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .section-customization label {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 14px;
        }

        .section-customization input[type="text"],
        .section-customization input[type="number"] {
          padding: 6px;
          border: 1px solid #ddd;
          border-radius: 3px;
          font-size: 13px;
          flex: 1;
        }

        .preview-panel {
          background: white;
          padding: 15px;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
          display: flex;
          flex-direction: column;
        }

        .preview-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 10px;
        }

        .preview-header h3 {
          margin: 0;
        }

        .btn-refresh {
          padding: 6px 12px;
          background: #4CAF50;
          color: white;
          border: none;
          border-radius: 3px;
          cursor: pointer;
          font-size: 12px;
        }

        .btn-refresh:hover:not(:disabled) {
          background: #45a049;
        }

        .preview-iframe {
          flex: 1;
          border: 1px solid #ddd;
          border-radius: 4px;
          min-height: 300px;
        }

        .preview-empty {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #999;
        }

        .builder-footer {
          display: flex;
          justify-content: center;
          gap: 10px;
        }

        .btn-primary {
          padding: 12px 30px;
          background: #2196F3;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 16px;
          font-weight: bold;
        }

        .btn-primary:hover:not(:disabled) {
          background: #1976d2;
        }

        .btn-primary:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        @media (max-width: 1200px) {
          .builder-container {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
}
