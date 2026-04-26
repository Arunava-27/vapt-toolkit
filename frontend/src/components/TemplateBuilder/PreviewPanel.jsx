export function PreviewPanel({ preview, loading, onRefresh }) {
  return (
    <div style={styles.previewPanel}>
      <div style={styles.previewHeader}>
        <h3 style={styles.heading}>Live Preview</h3>
        <button
          style={styles.btnRefresh}
          onClick={onRefresh}
          disabled={loading}
        >
          🔄 Refresh
        </button>
      </div>
      {preview ? (
        <iframe
          title="Template Preview"
          srcDoc={preview}
          style={styles.previewIframe}
        />
      ) : (
        <div style={styles.previewEmpty}>
          <p>Preview will appear here</p>
        </div>
      )}
    </div>
  );
}

const styles = {
  previewPanel: {
    background: 'white',
    padding: '15px',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
    display: 'flex',
    flexDirection: 'column',
  },
  previewHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '10px',
  },
  heading: {
    margin: 0,
  },
  btnRefresh: {
    padding: '6px 12px',
    background: '#4CAF50',
    color: 'white',
    border: 'none',
    borderRadius: '3px',
    cursor: 'pointer',
    fontSize: '12px',
    transition: 'background 0.2s',
  },
  previewIframe: {
    flex: 1,
    border: '1px solid #ddd',
    borderRadius: '4px',
    minHeight: '300px',
  },
  previewEmpty: {
    flex: 1,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#999',
  },
};
