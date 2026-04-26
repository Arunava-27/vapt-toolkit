import React from 'react';
import { useScopeManagement } from './hooks/useScopeManagement';
import { TargetList } from './TargetList';
import { BulkPastePanel } from './BulkPastePanel';
import { PresetsPanel } from './PresetsPanel';
import { ExportControls } from './ExportControls';
import '../../../styles/ScopeEditor.css';

export default function ScopeEditor({ onScopeChange = () => {}, initialScope = [] }) {
  const state = useScopeManagement(onScopeChange, initialScope);

  return (
    <div className="scope-editor">
      <div className="scope-header">
        <h2>Scan Scope Editor</h2>
        <div className="scope-stats">
          <span className="stat valid">✓ {state.validCount} valid</span>
          {state.errorCount > 0 && <span className="stat error">✕ {state.errorCount} errors</span>}
        </div>
      </div>

      <div className="scope-controls">
        <button onClick={state.handleAddTarget} className="btn-primary">
          + Add Target
        </button>
        <button onClick={() => state.setShowPasteBulk(!state.showPasteBulk)} className="btn-secondary">
          📋 Paste Bulk
        </button>
        <button onClick={() => state.fileInputRef.current?.click()} className="btn-secondary">
          📁 Import
        </button>
        <input
          ref={state.fileInputRef}
          type="file"
          accept=".json,.txt,.yaml,.yml"
          onChange={state.handleImportScope}
          style={{ display: 'none' }}
        />
        <button onClick={() => state.setShowPresets(!state.showPresets)} className="btn-secondary">
          💾 Presets {state.presets.length > 0 && `(${state.presets.length})`}
        </button>
        <button onClick={state.handleValidateScope} className="btn-accent">
          ✓ Validate
        </button>
      </div>

      <BulkPastePanel
        show={state.showPasteBulk}
        pasteBulk={state.pasteBulk}
        setPasteBulk={state.setPasteBulk}
        onPasteBulk={state.handlePasteBulk}
        onCancel={() => state.setShowPasteBulk(false)}
      />

      <PresetsPanel
        show={state.showPresets}
        presets={state.presets}
        presetName={state.presetName}
        setPresetName={state.setPresetName}
        onSavePreset={state.handleSavePreset}
        onLoadPreset={state.handleLoadPreset}
      />

      <ExportControls onExport={state.handleExportScope} />

      <TargetList
        targetsByType={state.targetsByType}
        targets={state.targets}
        draggedId={state.draggedId}
        onDragStart={state.handleDragStart}
        onDragOver={state.handleDragOver}
        onDrop={state.handleDrop}
        onUpdateTarget={state.handleUpdateTarget}
        onRemoveTarget={state.handleRemoveTarget}
      />
    </div>
  );
}
