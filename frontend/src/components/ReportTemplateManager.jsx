import React, { useState, useEffect } from "react";

export default function ReportTemplateManager() {
  const [templates, setTemplates] = useState([]);
  const [prebuiltTemplates, setPrebuiltTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [preview, setPreview] = useState(null);
  const [isCreating, setIsCreating] = useState(false);
  const [newTemplate, setNewTemplate] = useState({ name: "", content: "" });
  const [loading, setLoading] = useState(false);
  const [projectId, setProjectId] = useState("");

  useEffect(() => {
    fetchTemplates();
    fetchPrebuiltTemplates();
  }, [projectId]);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      const url = projectId
        ? `/api/templates/report?projectId=${projectId}`
        : "/api/templates/report";
      const response = await fetch(url);
      const data = await response.json();
      setTemplates(data.templates || []);
    } catch (error) {
      console.error("Error fetching templates:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPrebuiltTemplates = async () => {
    try {
      const response = await fetch("/api/templates/report/prebuilt");
      const data = await response.json();
      setPrebuiltTemplates(data.templates || []);
    } catch (error) {
      console.error("Error fetching prebuilt templates:", error);
    }
  };

  const handleSelectTemplate = async (template) => {
    setSelectedTemplate(template);
    await fetchPreview(template.id);
  };

  const fetchPreview = async (templateId) => {
    try {
      setLoading(true);
      const url = projectId
        ? `/api/templates/report/${templateId}/preview?projectId=${projectId}`
        : `/api/templates/report/${templateId}/preview`;
      const response = await fetch(url);
      const data = await response.json();
      setPreview(data.preview);
    } catch (error) {
      console.error("Error fetching preview:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTemplate = async () => {
    if (!newTemplate.name.trim() || !newTemplate.content.trim()) {
      alert("Name and content are required");
      return;
    }

    try {
      setLoading(true);
      const response = await fetch("/api/templates/report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newTemplate.name,
          content: newTemplate.content,
          project_id: projectId || null,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setTemplates([...templates, { id: data.id, name: data.name }]);
        setNewTemplate({ name: "", content: "" });
        setIsCreating(false);
        alert("Template created successfully");
      } else {
        alert("Failed to create template");
      }
    } catch (error) {
      console.error("Error creating template:", error);
      alert("Error creating template");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteTemplate = async (templateId) => {
    if (!window.confirm("Are you sure you want to delete this template?")) return;

    try {
      setLoading(true);
      const response = await fetch(`/api/templates/report/${templateId}`, {
        method: "DELETE",
      });

      if (response.ok) {
        setTemplates(templates.filter((t) => t.id !== templateId));
        setSelectedTemplate(null);
        setPreview(null);
        alert("Template deleted successfully");
      } else {
        alert("Failed to delete template");
      }
    } catch (error) {
      console.error("Error deleting template:", error);
      alert("Error deleting template");
    } finally {
      setLoading(false);
    }
  };

  const handleApplyTemplate = async () => {
    if (!selectedTemplate || !projectId) {
      alert("Please select a project and template");
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(
        `/api/templates/report/${selectedTemplate.id}/apply`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            project_id: projectId,
            scan_index: -1,
          }),
        }
      );

      if (response.ok) {
        const data = await response.json();
        downloadReport(data.report, selectedTemplate.name);
      } else {
        alert("Failed to generate report");
      }
    } catch (error) {
      console.error("Error applying template:", error);
      alert("Error generating report");
    } finally {
      setLoading(false);
    }
  };

  const downloadReport = (html, templateName) => {
    const element = document.createElement("a");
    const file = new Blob([html], { type: "text/html" });
    element.href = URL.createObjectURL(file);
    element.download = `${templateName}-${new Date().toISOString().split("T")[0]}.html`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <div className="template-manager">
      <div className="template-header">
        <h2>Report Template Manager</h2>
        <div className="project-selector">
          <label>Select Project:</label>
          <select
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
            className="input-field"
          >
            <option value="">All Projects</option>
            {/* Projects would be fetched and populated here */}
          </select>
        </div>
      </div>

      <div className="template-container">
        {/* Left panel - Template list */}
        <div className="template-list">
          <div className="list-section">
            <h3>Custom Templates</h3>
            {templates.length === 0 ? (
              <p className="empty-state">No custom templates yet</p>
            ) : (
              <ul className="template-items">
                {templates.map((template) => (
                  <li
                    key={template.id}
                    className={`template-item ${
                      selectedTemplate?.id === template.id ? "active" : ""
                    }`}
                    onClick={() => handleSelectTemplate(template)}
                  >
                    <span>{template.name}</span>
                    <button
                      className="btn-delete"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteTemplate(template.id);
                      }}
                    >
                      ✕
                    </button>
                  </li>
                ))}
              </ul>
            )}
            <button
              className="btn-primary"
              onClick={() => setIsCreating(true)}
              disabled={loading}
            >
              + New Template
            </button>
          </div>

          <div className="list-section">
            <h3>Prebuilt Templates</h3>
            <ul className="template-items">
              {prebuiltTemplates.map((template) => (
                <li
                  key={template.id}
                  className={`template-item prebuilt ${
                    selectedTemplate?.id === template.id ? "active" : ""
                  }`}
                  onClick={() => handleSelectTemplate(template)}
                >
                  <div>
                    <strong>{template.name}</strong>
                    <p className="template-description">{template.description}</p>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Right panel - Preview and actions */}
        <div className="template-preview">
          {isCreating ? (
            <div className="create-template">
              <h3>Create New Template</h3>
              <input
                type="text"
                placeholder="Template name"
                value={newTemplate.name}
                onChange={(e) =>
                  setNewTemplate({ ...newTemplate, name: e.target.value })
                }
                className="input-field"
              />
              <textarea
                placeholder="HTML content (Jinja2 syntax supported)"
                value={newTemplate.content}
                onChange={(e) =>
                  setNewTemplate({ ...newTemplate, content: e.target.value })
                }
                className="input-field textarea"
                rows={15}
              />
              <div className="template-actions">
                <button
                  className="btn-primary"
                  onClick={handleCreateTemplate}
                  disabled={loading}
                >
                  Create
                </button>
                <button
                  className="btn-secondary"
                  onClick={() => {
                    setIsCreating(false);
                    setNewTemplate({ name: "", content: "" });
                  }}
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : selectedTemplate ? (
            <>
              <div className="preview-info">
                <h3>{selectedTemplate.name}</h3>
                <p>
                  {selectedTemplate.description ||
                    "Template preview and details"}
                </p>
              </div>
              <div className="preview-frame">
                {loading ? (
                  <p>Loading preview...</p>
                ) : preview ? (
                  <iframe
                    title="Template Preview"
                    srcDoc={preview}
                    style={{
                      width: "100%",
                      height: "400px",
                      border: "1px solid #ddd",
                      borderRadius: "4px",
                    }}
                  />
                ) : (
                  <p>No preview available</p>
                )}
              </div>
              <div className="template-actions">
                {projectId && (
                  <button
                    className="btn-primary"
                    onClick={handleApplyTemplate}
                    disabled={loading}
                  >
                    Generate Report
                  </button>
                )}
              </div>
            </>
          ) : (
            <div className="empty-state">
              <p>Select a template to view preview</p>
            </div>
          )}
        </div>
      </div>

      <style>{`
        .template-manager {
          padding: 20px;
          background: #f5f5f5;
          border-radius: 8px;
        }

        .template-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }

        .project-selector {
          display: flex;
          gap: 10px;
          align-items: center;
        }

        .template-container {
          display: grid;
          grid-template-columns: 1fr 2fr;
          gap: 20px;
          margin-top: 20px;
        }

        .template-list {
          background: white;
          padding: 15px;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .list-section {
          margin-bottom: 20px;
        }

        .list-section h3 {
          margin-top: 0;
          color: #333;
        }

        .template-items {
          list-style: none;
          padding: 0;
          margin: 10px 0;
        }

        .template-item {
          padding: 10px;
          margin-bottom: 5px;
          background: #f9f9f9;
          border: 1px solid #ddd;
          border-radius: 4px;
          cursor: pointer;
          display: flex;
          justify-content: space-between;
          align-items: center;
          transition: all 0.2s;
        }

        .template-item:hover {
          background: #efefef;
          border-color: #2196F3;
        }

        .template-item.active {
          background: #e3f2fd;
          border-color: #2196F3;
          font-weight: bold;
        }

        .template-item.prebuilt {
          flex-direction: column;
          align-items: flex-start;
        }

        .template-description {
          font-size: 12px;
          color: #666;
          margin: 5px 0 0 0;
        }

        .btn-delete {
          background: #f44336;
          color: white;
          border: none;
          padding: 5px 10px;
          border-radius: 3px;
          cursor: pointer;
          font-size: 12px;
        }

        .btn-delete:hover {
          background: #d32f2f;
        }

        .btn-primary {
          background: #2196F3;
          color: white;
          border: none;
          padding: 10px 20px;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
          width: 100%;
        }

        .btn-primary:hover:not(:disabled) {
          background: #1976d2;
        }

        .btn-primary:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .btn-secondary {
          background: #757575;
          color: white;
          border: none;
          padding: 10px 20px;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
        }

        .btn-secondary:hover {
          background: #616161;
        }

        .template-preview {
          background: white;
          padding: 15px;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .preview-info h3 {
          margin-top: 0;
          color: #333;
        }

        .preview-frame {
          margin: 15px 0;
          border: 1px solid #ddd;
          border-radius: 4px;
          overflow: hidden;
        }

        .create-template {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .input-field {
          padding: 10px;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-family: inherit;
        }

        .input-field.textarea {
          font-family: "Courier New", monospace;
          font-size: 12px;
        }

        .template-actions {
          display: flex;
          gap: 10px;
          margin-top: 15px;
        }

        .template-actions button {
          flex: 1;
        }

        .empty-state {
          text-align: center;
          color: #999;
          padding: 40px 20px;
        }

        @media (max-width: 1024px) {
          .template-container {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
}
