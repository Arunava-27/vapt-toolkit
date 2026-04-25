import React, { useState, useEffect } from 'react';
import '../styles/ScanInstructionBuilder.css';

const ScanInstructionBuilder = ({ onScanStart }) => {
  const [jsonInput, setJsonInput] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [templates, setTemplates] = useState([]);
  const [validation, setValidation] = useState(null);
  const [showErrors, setShowErrors] = useState(false);
  const [activeTab, setActiveTab] = useState('editor');
  const [isLoading, setIsLoading] = useState(false);
  const [schema, setSchema] = useState(null);

  useEffect(() => {
    fetchTemplates();
    fetchSchema();
  }, []);

  const fetchTemplates = async () => {
    try {
      const res = await fetch('/api/scans/json/templates');
      const data = await res.json();
      setTemplates(data.templates || []);
    } catch (err) {
      console.error('Failed to fetch templates:', err);
    }
  };

  const fetchSchema = async () => {
    try {
      const res = await fetch('/api/scans/json/schema');
      const data = await res.json();
      setSchema(data);
    } catch (err) {
      console.error('Failed to fetch schema:', err);
    }
  };

  const handleTemplateSelect = (template) => {
    setSelectedTemplate(template.id);
    const instructionCopy = JSON.parse(JSON.stringify(template.json_instruction));
    setJsonInput(JSON.stringify(instructionCopy, null, 2));
    setValidation(null);
  };

  const handleValidateJSON = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/scans/json/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ json_instruction: jsonInput })
      });
      const data = await res.json();
      setValidation(data);
      setShowErrors(!data.is_valid);
    } catch (err) {
      setValidation({
        is_valid: false,
        errors: ['Failed to validate: ' + err.message],
        suggestions: []
      });
      setShowErrors(true);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExecuteScan = async () => {
    if (!validation || !validation.is_valid) {
      alert('Please fix validation errors first');
      return;
    }

    setIsLoading(true);
    try {
      const res = await fetch('/api/scans/json/from-json', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ json_instruction: jsonInput })
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Failed to start scan');
      }

      const data = await res.json();
      alert(`Scan started! Scan ID: ${data.scan_id}`);
      
      if (onScanStart) {
        onScanStart(data.scan_id);
      }
      
      setJsonInput('');
      setValidation(null);
      setSelectedTemplate('');
    } catch (err) {
      alert('Error: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopyToClipboard = () => {
    navigator.clipboard.writeText(jsonInput);
    alert('JSON copied to clipboard');
  };

  const handleFormatJSON = () => {
    try {
      const parsed = JSON.parse(jsonInput);
      setJsonInput(JSON.stringify(parsed, null, 2));
    } catch (err) {
      alert('Invalid JSON: ' + err.message);
    }
  };

  const handleLoadFile = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = async (e) => {
      const file = e.target.files[0];
      if (file) {
        const content = await file.text();
        setJsonInput(content);
        setValidation(null);
      }
    };
    input.click();
  };

  const handleDownloadTemplate = () => {
    if (!jsonInput) {
      alert('Nothing to download');
      return;
    }

    const element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(jsonInput));
    element.setAttribute('download', 'scan-instruction.json');
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const renderTemplatePreview = (template) => (
    <div key={template.id} className="template-card">
      <div className="template-icon">{template.icon}</div>
      <div className="template-content">
        <h4 className="template-name">{template.name}</h4>
        <p className="template-desc">{template.description}</p>
        <span className="template-time">⏱️ {Math.round(template.estimated_time_seconds / 60)} min</span>
      </div>
      <button
        className="btn-template-select"
        onClick={() => handleTemplateSelect(template)}
      >
        Use Template
      </button>
    </div>
  );

  const renderValidationStatus = () => {
    if (!validation) return null;

    return (
      <div className={`validation-status ${validation.is_valid ? 'valid' : 'invalid'}`}>
        <div className="validation-header">
          <span className="validation-icon">
            {validation.is_valid ? '✓' : '✗'}
          </span>
          <span className="validation-message">
            {validation.is_valid
              ? 'JSON is valid and ready to scan'
              : `Found ${validation.errors.length} error(s)`}
          </span>
        </div>

        {validation.errors.length > 0 && (
          <div className="validation-errors">
            <h5>Errors:</h5>
            <ul>
              {validation.errors.map((error, i) => (
                <li key={i}>{error}</li>
              ))}
            </ul>
          </div>
        )}

        {validation.suggestions.length > 0 && (
          <div className="validation-suggestions">
            <h5>Suggestions:</h5>
            <ul>
              {validation.suggestions.map((suggestion, i) => (
                <li key={i}>{suggestion}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="scan-instruction-builder">
      <div className="builder-header">
        <h2>JSON Scan Instructions</h2>
        <p>Create and execute scans using JSON-based instructions</p>
      </div>

      <div className="builder-tabs">
        <button
          className={`tab-button ${activeTab === 'editor' ? 'active' : ''}`}
          onClick={() => setActiveTab('editor')}
        >
          JSON Editor
        </button>
        <button
          className={`tab-button ${activeTab === 'templates' ? 'active' : ''}`}
          onClick={() => setActiveTab('templates')}
        >
          Templates
        </button>
        <button
          className={`tab-button ${activeTab === 'docs' ? 'active' : ''}`}
          onClick={() => setActiveTab('docs')}
        >
          Documentation
        </button>
      </div>

      <div className="builder-content">
        {/* JSON Editor Tab */}
        {activeTab === 'editor' && (
          <div className="editor-section">
            <div className="editor-toolbar">
              <button
                className="btn-toolbar"
                onClick={handleFormatJSON}
                title="Format JSON"
              >
                ✨ Format
              </button>
              <button
                className="btn-toolbar"
                onClick={handleValidateJSON}
                disabled={isLoading}
                title="Validate JSON"
              >
                {isLoading ? '⏳ Validating...' : '✓ Validate'}
              </button>
              <button
                className="btn-toolbar"
                onClick={handleCopyToClipboard}
                title="Copy to clipboard"
              >
                📋 Copy
              </button>
              <button
                className="btn-toolbar"
                onClick={handleLoadFile}
                title="Load from file"
              >
                📂 Load File
              </button>
              <button
                className="btn-toolbar"
                onClick={handleDownloadTemplate}
                title="Download as JSON"
              >
                💾 Download
              </button>
            </div>

            <textarea
              className="json-editor"
              value={jsonInput}
              onChange={(e) => {
                setJsonInput(e.target.value);
                setValidation(null);
              }}
              placeholder={`{
  "name": "Example Scan",
  "target": "https://example.com",
  "modules": ["all"],
  "depth": "medium"
}`}
            />

            {renderValidationStatus()}

            <div className="editor-actions">
              <button
                className="btn-primary btn-execute"
                onClick={handleExecuteScan}
                disabled={!validation || !validation.is_valid || isLoading}
              >
                {isLoading ? '⏳ Starting...' : '▶️ Execute Scan'}
              </button>
            </div>
          </div>
        )}

        {/* Templates Tab */}
        {activeTab === 'templates' && (
          <div className="templates-section">
            <div className="templates-grid">
              {templates.map(renderTemplatePreview)}
            </div>
          </div>
        )}

        {/* Documentation Tab */}
        {activeTab === 'docs' && (
          <div className="docs-section">
            <div className="docs-content">
              <h3>JSON Schema Reference</h3>
              <p>
                JSON scan instructions allow you to define all scan parameters programmatically.
              </p>

              <h4>Required Fields</h4>
              <ul>
                <li><strong>name</strong> (string): Descriptive scan name</li>
                <li><strong>target</strong> (string): Target URL or domain</li>
              </ul>

              <h4>Core Options</h4>
              <ul>
                <li><strong>description</strong> (string): Scan description</li>
                <li><strong>scope</strong> (array): Authorized target patterns (e.g., ["https://example.com/*"])</li>
                <li><strong>modules</strong> (array): ["all"] or specific ["xss", "sqli", "csrf", "auth", "headers", etc.]</li>
                <li><strong>depth</strong> (string): "quick" | "medium" | "full"</li>
                <li><strong>concurrency</strong> (number): 1-50 concurrent requests (default: 5)</li>
                <li><strong>timeout</strong> (number): Request timeout in seconds (default: 600)</li>
              </ul>

              <h4>Notifications</h4>
              <pre>{`{
  "notifications": {
    "email": "admin@example.com",
    "slack_webhook": "https://hooks.slack.com/...",
    "severity_filter": "high",
    "channels": ["desktop", "email", "slack"]
  }
}`}</pre>

              <h4>Export Settings</h4>
              <pre>{`{
  "export": {
    "formats": ["pdf", "json", "csv"],
    "send_email": true,
    "email": "reports@example.com"
  }
}`}</pre>

              <h4>Scheduling</h4>
              <pre>{`{
  "schedule": {
    "recurring": "weekly",
    "day": "Monday",
    "time": "02:00"
  }
}`}</pre>

              <h4>Advanced Options</h4>
              <pre>{`{
  "advanced": {
    "skip_robots_txt": false,
    "user_agent": "Custom UA",
    "auth_type": "bearer",
    "auth_credentials": {
      "token": "..."
    }
  }
}`}</pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ScanInstructionBuilder;
