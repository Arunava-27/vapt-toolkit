import { TemplateCreator } from './TemplateCreator';

export function PreviewPanel({
  isCreating,
  selectedTemplate,
  preview,
  loading,
  projectId,
  newTemplate,
  setNewTemplate,
  onCreateTemplate,
  onCancelCreate,
  onApplyTemplate,
}) {
  return (
    <div style={styles.templatePreview}>
      {isCreating ? (
        <TemplateCreator
          newTemplate={newTemplate}
          setNewTemplate={setNewTemplate}
          loading={loading}
          onCreateTemplate={onCreateTemplate}
          onCancel={onCancelCreate}
        />
      ) : selectedTemplate ? (
        <>
          <div style={styles.previewInfo}>
            <h3>{selectedTemplate.name}</h3>
            <p>
              {selectedTemplate.description ||
                'Template preview and details'}
            </p>
          </div>
          <div style={styles.previewFrame}>
            {loading ? (
              <p>Loading preview...</p>
            ) : preview ? (
              <iframe
                title="Template Preview"
                srcDoc={preview}
                style={styles.previewIframe}
              />
            ) : (
              <p>No preview available</p>
            )}
          </div>
          <div style={styles.templateActions}>
            {projectId && (
              <button
                style={styles.btnPrimary}
                onClick={onApplyTemplate}
                disabled={loading}
              >
                Generate Report
              </button>
            )}
          </div>
        </>
      ) : (
        <div style={styles.emptyState}>
          <p>Select a template to view preview</p>
        </div>
      )}
    </div>
  );
}

const styles = {
  templatePreview: {
    background: 'white',
    padding: '15px',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
  },
  previewInfo: {
    marginBottom: '15px',
  },
  previewFrame: {
    margin: '15px 0',
    border: '1px solid #ddd',
    borderRadius: '4px',
    overflow: 'hidden',
  },
  previewIframe: {
    width: '100%',
    height: '400px',
    border: 'none',
  },
  templateActions: {
    display: 'flex',
    gap: '10px',
    marginTop: '15px',
  },
  btnPrimary: {
    flex: 1,
    background: '#2196F3',
    color: 'white',
    border: 'none',
    padding: '10px 20px',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
  },
  emptyState: {
    textAlign: 'center',
    color: '#999',
    padding: '40px 20px',
  },
};
