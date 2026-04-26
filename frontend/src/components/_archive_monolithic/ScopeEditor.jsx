import React, { useState, useRef, useEffect } from 'react';
import '../styles/ScopeEditor.css';

/**
 * Drag-drop scope editor for managing scan targets.
 * Supports URLs, domains, endpoints with grouping and validation.
 */
const ScopeEditor = ({ onScopeChange = () => {}, initialScope = [] }) => {
  const [targets, setTargets] = useState(
    initialScope.map((t, i) => ({
      id: `target-${i}-${Date.now()}`,
      value: t,
      type: inferTargetType(t),
      error: null,
    })) || []
  );

  const [draggedId, setDraggedId] = useState(null);
  const [presets, setPresets] = useState([]);
  const [showPresets, setShowPresets] = useState(false);
  const [presetName, setPresetName] = useState('');
  const [pasteBulk, setPasteBulk] = useState('');
  const [showPasteBulk, setShowPasteBulk] = useState(false);
  const fileInputRef = useRef(null);

  // Load presets on mount
  useEffect(() => {
    loadPresets();
  }, []);

  // Notify parent of changes
  useEffect(() => {
    const validTargets = targets
      .filter(t => !t.error && t.value.trim())
      .map(t => t.value);
    onScopeChange(validTargets);
  }, [targets, onScopeChange]);

  function inferTargetType(value) {
    value = value.trim();
    if (value.match(/^https?:\/\//)) return 'url';
    if (value.match(/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(\/\d{1,2})?$/)) return 'ip';
    if (value.includes('*')) return 'wildcard';
    if (value.match(/^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*$/))
      return 'domain';
    return 'endpoint';
  }

  function validateTarget(value) {
    value = value.trim();
    if (!value) return null;

    const errors = [];

    // URL validation
    if (value.match(/^https?:\/\//)) {
      try {
        new URL(value);
      } catch {
        errors.push('Invalid URL format');
      }
    }

    // IP/CIDR validation
    if (value.match(/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/)) {
      const parts = value.split('/')[0].split('.');
      if (parts.some(p => parseInt(p) > 255)) {
        errors.push('Invalid IP address');
      }
    }

    // Wildcard validation
    if (value.includes('*')) {
      if (!value.match(/^(\*\.)?[a-zA-Z0-9.-]*\*?[a-zA-Z0-9.-]*$/)) {
        errors.push('Invalid wildcard pattern');
      }
    }

    // Domain validation (basic)
    if (!value.match(/^https?:/) && !value.match(/^\d/) && !value.includes('*')) {
      if (!value.match(/^[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?(\:\d+)?$/)) {
        errors.push('Invalid domain format');
      }
    }

    return errors.length > 0 ? errors.join('; ') : null;
  }

  function handleAddTarget() {
    const newTarget = {
      id: `target-${Date.now()}-${Math.random()}`,
      value: '',
      type: 'domain',
      error: null,
    };
    setTargets([...targets, newTarget]);
  }

  function handleUpdateTarget(id, newValue) {
    setTargets(targets.map(t => {
      if (t.id === id) {
        const error = validateTarget(newValue);
        return { ...t, value: newValue, type: inferTargetType(newValue), error };
      }
      return t;
    }));
  }

  function handleRemoveTarget(id) {
    setTargets(targets.filter(t => t.id !== id));
  }

  function handleDragStart(e, id) {
    setDraggedId(id);
    e.dataTransfer.effectAllowed = 'move';
  }

  function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  }

  function handleDrop(e, targetId) {
    e.preventDefault();
    if (!draggedId || draggedId === targetId) return;

    const draggedIdx = targets.findIndex(t => t.id === draggedId);
    const targetIdx = targets.findIndex(t => t.id === targetId);

    const newTargets = [...targets];
    [newTargets[draggedIdx], newTargets[targetIdx]] = [newTargets[targetIdx], newTargets[draggedIdx]];
    setTargets(newTargets);
    setDraggedId(null);
  }

  function handlePasteBulk() {
    if (!pasteBulk.trim()) return;

    const newLines = pasteBulk
      .split(/[\n,]/)
      .map(line => line.trim())
      .filter(line => line);

    const newTargets = newLines.map((line, idx) => ({
      id: `target-${Date.now()}-${idx}`,
      value: line,
      type: inferTargetType(line),
      error: validateTarget(line),
    }));

    setTargets([...targets, ...newTargets]);
    setPasteBulk('');
    setShowPasteBulk(false);
  }

  async function loadPresets() {
    try {
      const response = await fetch('/api/scans/scope/presets');
      if (response.ok) {
        const data = await response.json();
        setPresets(data.presets || []);
      }
    } catch (error) {
      console.error('Failed to load presets:', error);
    }
  }

  async function handleSavePreset() {
    if (!presetName.trim()) return;

    const validTargets = targets
      .filter(t => !t.error && t.value.trim())
      .map(t => t.value);

    try {
      const response = await fetch('/api/scans/scope/presets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: presetName,
          targets: validTargets,
        }),
      });

      if (response.ok) {
        setPresetName('');
        await loadPresets();
      }
    } catch (error) {
      console.error('Failed to save preset:', error);
    }
  }

  function handleLoadPreset(preset) {
    const newTargets = preset.targets.map((value, idx) => ({
      id: `target-${Date.now()}-${idx}`,
      value,
      type: inferTargetType(value),
      error: validateTarget(value),
    }));
    setTargets(newTargets);
    setShowPresets(false);
  }

  function handleExportScope(format) {
    const validTargets = targets
      .filter(t => !t.error && t.value.trim())
      .map(t => t.value);

    let content;
    let filename;

    if (format === 'json') {
      content = JSON.stringify({ targets: validTargets }, null, 2);
      filename = 'scope.json';
    } else if (format === 'yaml') {
      content = `targets:\n${validTargets.map(t => `  - ${t}`).join('\n')}`;
      filename = 'scope.yaml';
    } else if (format === 'txt') {
      content = validTargets.join('\n');
      filename = 'scope.txt';
    }

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  function handleImportScope(e) {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const content = event.target.result;
        let parsedTargets = [];

        if (file.name.endsWith('.json')) {
          const data = JSON.parse(content);
          parsedTargets = data.targets || data;
        } else {
          parsedTargets = content
            .split(/[\n,]/)
            .map(line => line.trim())
            .filter(line => line && !line.startsWith('#'));
        }

        const newTargets = parsedTargets.map((value, idx) => ({
          id: `target-${Date.now()}-${idx}`,
          value,
          type: inferTargetType(value),
          error: validateTarget(value),
        }));

        setTargets(newTargets);
      } catch (error) {
        console.error('Failed to parse file:', error);
      }
    };
    reader.readAsText(file);
    if (fileInputRef.current) fileInputRef.current.value = '';
  }

  async function handleValidateScope() {
    const validTargets = targets
      .filter(t => !t.error && t.value.trim())
      .map(t => t.value);

    try {
      const response = await fetch('/api/scans/scope/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ targets: validTargets }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.valid) {
          alert('✓ Scope is valid!');
        } else {
          alert(`✗ Validation failed:\n${data.errors?.join('\n')}`);
        }
      }
    } catch (error) {
      console.error('Validation failed:', error);
      alert('Validation error: ' + error.message);
    }
  }

  const validCount = targets.filter(t => !t.error && t.value.trim()).length;
  const errorCount = targets.filter(t => t.error).length;

  const targetsByType = {
    url: targets.filter(t => t.type === 'url'),
    domain: targets.filter(t => t.type === 'domain'),
    ip: targets.filter(t => t.type === 'ip'),
    wildcard: targets.filter(t => t.type === 'wildcard'),
    endpoint: targets.filter(t => t.type === 'endpoint'),
  };

  return (
    <div className="scope-editor">
      <div className="scope-header">
        <h2>Scan Scope Editor</h2>
        <div className="scope-stats">
          <span className="stat valid">✓ {validCount} valid</span>
          {errorCount > 0 && <span className="stat error">✕ {errorCount} errors</span>}
        </div>
      </div>

      <div className="scope-controls">
        <button onClick={handleAddTarget} className="btn-primary">
          + Add Target
        </button>
        <button onClick={() => setShowPasteBulk(!showPasteBulk)} className="btn-secondary">
          📋 Paste Bulk
        </button>
        <button onClick={() => fileInputRef.current?.click()} className="btn-secondary">
          📁 Import
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".json,.txt,.yaml,.yml"
          onChange={handleImportScope}
          style={{ display: 'none' }}
        />
        <button onClick={() => setShowPresets(!showPresets)} className="btn-secondary">
          💾 Presets {presets.length > 0 && `(${presets.length})`}
        </button>
        <button onClick={handleValidateScope} className="btn-accent">
          ✓ Validate
        </button>
      </div>

      {showPasteBulk && (
        <div className="paste-bulk-panel">
          <textarea
            placeholder="Paste multiple targets (one per line or comma-separated)&#10;Examples:&#10;  https://example.com&#10;  example.com&#10;  192.168.1.1/24&#10;  *.subdomain.example.com"
            value={pasteBulk}
            onChange={e => setPasteBulk(e.target.value)}
            className="bulk-textarea"
          />
          <div className="bulk-actions">
            <button onClick={handlePasteBulk} className="btn-primary">
              Add Targets
            </button>
            <button onClick={() => setShowPasteBulk(false)} className="btn-secondary">
              Cancel
            </button>
          </div>
        </div>
      )}

      {showPresets && (
        <div className="presets-panel">
          <div className="preset-save">
            <input
              type="text"
              placeholder="Preset name (e.g., 'Production Scope')"
              value={presetName}
              onChange={e => setPresetName(e.target.value)}
              className="preset-input"
            />
            <button onClick={handleSavePreset} className="btn-primary">
              Save Current
            </button>
          </div>

          {presets.length > 0 ? (
            <div className="preset-list">
              <h4>Saved Presets</h4>
              {presets.map(preset => (
                <div key={preset.id} className="preset-item">
                  <div className="preset-info">
                    <div className="preset-name">{preset.name}</div>
                    <div className="preset-count">{preset.targets?.length || 0} targets</div>
                  </div>
                  <button onClick={() => handleLoadPreset(preset)} className="btn-small">
                    Load
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p className="empty-message">No presets saved yet</p>
          )}
        </div>
      )}

      <div className="export-controls">
        <button onClick={() => handleExportScope('json')} className="btn-small">
          JSON
        </button>
        <button onClick={() => handleExportScope('yaml')} className="btn-small">
          YAML
        </button>
        <button onClick={() => handleExportScope('txt')} className="btn-small">
          TXT
        </button>
      </div>

      <div className="scope-list">
        {Object.entries(targetsByType).map(([type, typeTargets]) => {
          if (typeTargets.length === 0) return null;

          return (
            <div key={type} className="target-group">
              <h3 className="group-header">
                <span className="type-badge" data-type={type}>{type.toUpperCase()}</span>
                <span className="group-count">{typeTargets.length}</span>
              </h3>
              <div className="targets-container">
                {typeTargets.map(target => (
                  <div
                    key={target.id}
                    className={`target-item ${target.error ? 'error' : ''} ${draggedId === target.id ? 'dragging' : ''}`}
                    draggable
                    onDragStart={e => handleDragStart(e, target.id)}
                    onDragOver={handleDragOver}
                    onDrop={e => handleDrop(e, target.id)}
                  >
                    <div className="target-drag-handle">⋮⋮</div>
                    <input
                      type="text"
                      className="target-input"
                      value={target.value}
                      onChange={e => handleUpdateTarget(target.id, e.target.value)}
                      placeholder={`Enter ${type}...`}
                    />
                    <button
                      onClick={() => handleRemoveTarget(target.id)}
                      className="btn-remove"
                      title="Remove target"
                    >
                      ✕
                    </button>
                    {target.error && (
                      <div className="target-error">{target.error}</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          );
        })}

        {targets.length === 0 && (
          <div className="empty-state">
            <p>No targets added yet</p>
            <p className="hint">Click "Add Target" or "Paste Bulk" to get started</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ScopeEditor;
