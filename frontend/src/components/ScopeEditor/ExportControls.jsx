export function ExportControls({ onExport }) {
  return (
    <div style={styles.exportControls}>
      <button onClick={() => onExport('json')} style={styles.btnSmall}>
        JSON
      </button>
      <button onClick={() => onExport('yaml')} style={styles.btnSmall}>
        YAML
      </button>
      <button onClick={() => onExport('txt')} style={styles.btnSmall}>
        TXT
      </button>
    </div>
  );
}

const styles = {
  exportControls: {
    display: 'flex',
    gap: '8px',
    marginBottom: '15px',
  },
  btnSmall: {
    flex: 1,
    padding: '6px 12px',
    background: '#607D8B',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '12px',
  },
};
