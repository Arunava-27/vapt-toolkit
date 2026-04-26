export function TemplateCreator({ newTemplate, setNewTemplate, loading, onCreateTemplate, onCancel }) {
  return (
    <div style={styles.createTemplate}>
      <h3>Create New Template</h3>
      <input
        type="text"
        placeholder="Template name"
        value={newTemplate.name}
        onChange={(e) =>
          setNewTemplate({ ...newTemplate, name: e.target.value })
        }
        style={styles.inputField}
      />
      <textarea
        placeholder="HTML content (Jinja2 syntax supported)"
        value={newTemplate.content}
        onChange={(e) =>
          setNewTemplate({ ...newTemplate, content: e.target.value })
        }
        style={{ ...styles.inputField, ...styles.textarea }}
        rows={15}
      />
      <div style={styles.templateActions}>
        <button
          style={styles.btnPrimary}
          onClick={onCreateTemplate}
          disabled={loading}
        >
          Create
        </button>
        <button
          style={styles.btnSecondary}
          onClick={onCancel}
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

const styles = {
  createTemplate: {
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
  },
  inputField: {
    padding: '10px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontFamily: 'inherit',
    fontSize: '14px',
  },
  textarea: {
    fontFamily: '"Courier New", monospace',
    fontSize: '12px',
    resize: 'vertical',
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
  btnSecondary: {
    flex: 1,
    background: '#757575',
    color: 'white',
    border: 'none',
    padding: '10px 20px',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
  },
};
