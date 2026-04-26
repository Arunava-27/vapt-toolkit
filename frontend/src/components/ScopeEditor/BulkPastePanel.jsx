export function BulkPastePanel({ pasteBulk, setPasteBulk, onPasteBulk, onCancel, show }) {
  if (!show) return null;

  return (
    <div style={styles.pasteBulkPanel}>
      <textarea
        placeholder="Paste multiple targets (one per line or comma-separated)&#10;Examples:&#10;  https://example.com&#10;  example.com&#10;  192.168.1.1/24&#10;  *.subdomain.example.com"
        value={pasteBulk}
        onChange={e => setPasteBulk(e.target.value)}
        style={styles.bulkTextarea}
      />
      <div style={styles.bulkActions}>
        <button onClick={onPasteBulk} style={styles.btnPrimary}>
          Add Targets
        </button>
        <button onClick={onCancel} style={styles.btnSecondary}>
          Cancel
        </button>
      </div>
    </div>
  );
}

const styles = {
  pasteBulkPanel: {
    background: 'white',
    padding: '15px',
    borderRadius: '4px',
    border: '1px solid #ddd',
    marginBottom: '15px',
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
  },
  bulkTextarea: {
    padding: '10px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '13px',
    fontFamily: 'monospace',
    minHeight: '120px',
    resize: 'vertical',
  },
  bulkActions: {
    display: 'flex',
    gap: '10px',
  },
  btnPrimary: {
    flex: 1,
    padding: '8px 16px',
    background: '#2196F3',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
  },
  btnSecondary: {
    flex: 1,
    padding: '8px 16px',
    background: '#757575',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
  },
};
