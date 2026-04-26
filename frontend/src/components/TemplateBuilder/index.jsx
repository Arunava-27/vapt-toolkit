import React from 'react';
import { useTemplateBuilder } from './hooks/useTemplateBuilder';
import { AvailableSections } from './AvailableSections';
import { Canvas } from './Canvas';
import { PreviewPanel } from './PreviewPanel';

export default function TemplateBuilder() {
  const state = useTemplateBuilder();

  return (
    <div style={styles.templateBuilder}>
      <div style={styles.builderHeader}>
        <h2>Visual Template Builder</h2>
        <input
          type="text"
          placeholder="Template name"
          value={state.templateName}
          onChange={(e) => state.setTemplateName(e.target.value)}
          style={styles.templateNameInput}
        />
      </div>

      <div style={styles.builderContainer}>
        <AvailableSections
          availableSections={state.AVAILABLE_SECTIONS}
          onDragStart={state.handleDragStart}
        />

        <Canvas
          sections={state.sections}
          draggedSection={state.draggedSection}
          showCustomization={state.showCustomization}
          onDragOver={state.handleDragOver}
          onDrop={state.handleDrop}
          onShowCustomization={state.setShowCustomization}
          onRemoveSection={state.removeSection}
          onMoveSectionUp={state.moveSectionUp}
          onMoveSectionDown={state.moveSectionDown}
          onUpdateSectionSetting={state.updateSectionSetting}
        />

        <PreviewPanel
          preview={state.preview}
          loading={state.loading}
          onRefresh={state.generatePreview}
        />
      </div>

      <div style={styles.builderFooter}>
        <button
          style={styles.btnPrimary}
          onClick={state.handleSaveTemplate}
          disabled={state.loading || state.sections.length === 0}
        >
          💾 Save Template
        </button>
      </div>
    </div>
  );
}

const styles = {
  templateBuilder: {
    padding: '20px',
    background: '#f5f5f5',
    borderRadius: '8px',
  },
  builderHeader: {
    display: 'flex',
    gap: '20px',
    alignItems: 'center',
    marginBottom: '20px',
  },
  templateNameInput: {
    padding: '10px 15px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '14px',
    flex: '1',
    maxWidth: '300px',
  },
  builderContainer: {
    display: 'grid',
    gridTemplateColumns: '200px 1fr 250px',
    gap: '20px',
    marginBottom: '20px',
  },
  builderFooter: {
    display: 'flex',
    justifyContent: 'center',
    gap: '10px',
  },
  btnPrimary: {
    padding: '12px 30px',
    background: '#2196F3',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '16px',
    fontWeight: 'bold',
    transition: 'background 0.2s',
  },
  '@media (max-width: 1200px)': {
    builderContainer: {
      gridTemplateColumns: '1fr',
    },
  },
};
