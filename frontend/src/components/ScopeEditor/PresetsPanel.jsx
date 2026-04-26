export function PresetsPanel({ show, presets, presetName, setPresetName, onSavePreset, onLoadPreset }) {
  if (!show) return null;

  return (
    <div style={styles.presetsPanel}>
      <div style={styles.presetSave}>
        <input
          type="text"
          placeholder="Preset name (e.g., 'Production Scope')"
          value={presetName}
          onChange={e => setPresetName(e.target.value)}
          style={styles.presetInput}
        />
        <button onClick={onSavePreset} style={styles.btnPrimary}>
          Save Current
        </button>
      </div>

      {presets.length > 0 ? (
        <div style={styles.presetList}>
          <h4 style={styles.presetListHeading}>Saved Presets</h4>
          {presets.map(preset => (
            <div key={preset.id} style={styles.presetItem}>
              <div style={styles.presetInfo}>
                <div style={styles.presetItemName}>{preset.name}</div>
                <div style={styles.presetCount}>{preset.targets?.length || 0} targets</div>
              </div>
              <button onClick={() => onLoadPreset(preset)} style={styles.btnSmall}>
                Load
              </button>
            </div>
          ))}
        </div>
      ) : (
        <p style={styles.emptyMessage}>No presets saved yet</p>
      )}
    </div>
  );
}

const styles = {
  presetsPanel: {
    background: 'white',
    padding: '15px',
    borderRadius: '4px',
    border: '1px solid #ddd',
    marginBottom: '15px',
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  presetSave: {
    display: 'flex',
    gap: '8px',
  },
  presetInput: {
    flex: 1,
    padding: '8px 12px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '13px',
  },
  btnPrimary: {
    padding: '8px 16px',
    background: '#2196F3',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
  },
  presetList: {
    maxHeight: '250px',
    overflowY: 'auto',
  },
  presetListHeading: {
    margin: '0 0 10px 0',
    fontSize: '13px',
    color: '#666',
  },
  presetItem: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '10px',
    background: '#f9f9f9',
    border: '1px solid #eee',
    borderRadius: '3px',
    marginBottom: '6px',
  },
  presetInfo: {
    flex: 1,
  },
  presetItemName: {
    fontWeight: 'bold',
    fontSize: '13px',
    color: '#333',
  },
  presetCount: {
    fontSize: '12px',
    color: '#999',
    marginTop: '2px',
  },
  btnSmall: {
    padding: '4px 12px',
    background: '#4CAF50',
    color: 'white',
    border: 'none',
    borderRadius: '3px',
    cursor: 'pointer',
    fontSize: '12px',
  },
  emptyMessage: {
    textAlign: 'center',
    color: '#999',
    fontSize: '13px',
    margin: '8px 0',
  },
};
