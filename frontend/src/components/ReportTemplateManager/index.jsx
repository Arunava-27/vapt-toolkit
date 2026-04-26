import React from 'react';
import { useTemplateManager } from './hooks/useTemplateManager';
import { TemplateList } from './TemplateList';
import { PreviewPanel } from './PreviewPanel';

export default function ReportTemplateManager() {
  const state = useTemplateManager();

  return (
    <div style={styles.templateManager}>
      <div style={styles.templateHeader}>
        <h2>Report Template Manager</h2>
        <div style={styles.projectSelector}>
          <label>Select Project:</label>
          <select
            value={state.projectId}
            onChange={(e) => state.setProjectId(e.target.value)}
            style={styles.inputField}
          >
            <option value="">All Projects</option>
          </select>
        </div>
      </div>

      <div style={styles.templateContainer}>
        <TemplateList
          templates={state.templates}
          selectedTemplate={state.selectedTemplate}
          prebuiltTemplates={state.prebuiltTemplates}
          loading={state.loading}
          onSelectTemplate={state.handleSelectTemplate}
          onDeleteTemplate={state.handleDeleteTemplate}
          onCreateClick={() => state.setIsCreating(true)}
        />

        <PreviewPanel
          isCreating={state.isCreating}
          selectedTemplate={state.selectedTemplate}
          preview={state.preview}
          loading={state.loading}
          projectId={state.projectId}
          newTemplate={state.newTemplate}
          setNewTemplate={state.setNewTemplate}
          onCreateTemplate={state.handleCreateTemplate}
          onCancelCreate={() => {
            state.setIsCreating(false);
            state.setNewTemplate({ name: '', content: '' });
          }}
          onApplyTemplate={state.handleApplyTemplate}
        />
      </div>
    </div>
  );
}

const styles = {
  templateManager: {
    padding: '20px',
    background: '#f5f5f5',
    borderRadius: '8px',
  },
  templateHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px',
  },
  projectSelector: {
    display: 'flex',
    gap: '10px',
    alignItems: 'center',
  },
  templateContainer: {
    display: 'grid',
    gridTemplateColumns: '1fr 2fr',
    gap: '20px',
    marginTop: '20px',
  },
  inputField: {
    padding: '10px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontFamily: 'inherit',
  },
  '@media (max-width: 1024px)': {
    templateContainer: {
      gridTemplateColumns: '1fr',
    },
  },
};
