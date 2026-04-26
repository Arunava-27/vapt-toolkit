import { useState, useRef, useEffect } from 'react';

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

  if (value.match(/^https?:\/\//)) {
    try {
      new URL(value);
    } catch {
      errors.push('Invalid URL format');
    }
  }

  if (value.match(/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/)) {
    const parts = value.split('/')[0].split('.');
    if (parts.some(p => parseInt(p) > 255)) {
      errors.push('Invalid IP address');
    }
  }

  if (value.includes('*')) {
    if (!value.match(/^(\*\.)?[a-zA-Z0-9.-]*\*?[a-zA-Z0-9.-]*$/)) {
      errors.push('Invalid wildcard pattern');
    }
  }

  if (!value.match(/^https?:/) && !value.match(/^\d/) && !value.includes('*')) {
    if (!value.match(/^[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?(\:\d+)?$/)) {
      errors.push('Invalid domain format');
    }
  }

  return errors.length > 0 ? errors.join('; ') : null;
}

export function useScopeManagement(onScopeChange = () => {}, initialScope = []) {
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

  useEffect(() => {
    loadPresets();
  }, []);

  useEffect(() => {
    const validTargets = targets
      .filter(t => !t.error && t.value.trim())
      .map(t => t.value);
    onScopeChange(validTargets);
  }, [targets, onScopeChange]);

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

  return {
    targets,
    draggedId,
    presets,
    showPresets,
    setShowPresets,
    presetName,
    setPresetName,
    pasteBulk,
    setPasteBulk,
    showPasteBulk,
    setShowPasteBulk,
    fileInputRef,
    validCount,
    errorCount,
    targetsByType,
    handleAddTarget,
    handleUpdateTarget,
    handleRemoveTarget,
    handleDragStart,
    handleDragOver,
    handleDrop,
    handlePasteBulk,
    handleSavePreset,
    handleLoadPreset,
    handleExportScope,
    handleImportScope,
    handleValidateScope,
  };
}
