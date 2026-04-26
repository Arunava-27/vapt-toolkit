export function TemplateList({ templates, selectedTemplate, prebuiltTemplates, loading, onSelectTemplate, onDeleteTemplate, onCreateClick }) {
  return (
    <div style={styles.templateList}>
      <div style={styles.listSection}>
        <h3>Custom Templates</h3>
        {templates.length === 0 ? (
          <p style={styles.emptyState}>No custom templates yet</p>
        ) : (
          <ul style={styles.templateItems}>
            {templates.map((template) => (
              <li
                key={template.id}
                style={{
                  ...styles.templateItem,
                  ...(selectedTemplate?.id === template.id ? styles.templateItemActive : {}),
                }}
                onClick={() => onSelectTemplate(template)}
              >
                <span>{template.name}</span>
                <button
                  style={styles.btnDelete}
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteTemplate(template.id);
                  }}
                >
                  ✕
                </button>
              </li>
            ))}
          </ul>
        )}
        <button
          style={styles.btnPrimary}
          onClick={onCreateClick}
          disabled={loading}
        >
          + New Template
        </button>
      </div>

      <div style={styles.listSection}>
        <h3>Prebuilt Templates</h3>
        <ul style={styles.templateItems}>
          {prebuiltTemplates.map((template) => (
            <li
              key={template.id}
              style={{
                ...styles.templateItem,
                ...styles.templateItemPrebuilt,
                ...(selectedTemplate?.id === template.id ? styles.templateItemActive : {}),
              }}
              onClick={() => onSelectTemplate(template)}
            >
              <div>
                <strong>{template.name}</strong>
                <p style={styles.templateDescription}>{template.description}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

const styles = {
  templateList: {
    background: 'white',
    padding: '15px',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
  },
  listSection: {
    marginBottom: '20px',
  },
  templateItems: {
    listStyle: 'none',
    padding: 0,
    margin: '10px 0',
  },
  templateItem: {
    padding: '10px',
    marginBottom: '5px',
    background: '#f9f9f9',
    border: '1px solid #ddd',
    borderRadius: '4px',
    cursor: 'pointer',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    transition: 'all 0.2s',
  },
  templateItemActive: {
    background: '#e3f2fd',
    borderColor: '#2196F3',
    fontWeight: 'bold',
  },
  templateItemPrebuilt: {
    flexDirection: 'column',
    alignItems: 'flexStart',
  },
  templateDescription: {
    fontSize: '12px',
    color: '#666',
    margin: '5px 0 0 0',
  },
  btnDelete: {
    background: '#f44336',
    color: 'white',
    border: 'none',
    padding: '5px 10px',
    borderRadius: '3px',
    cursor: 'pointer',
    fontSize: '12px',
  },
  btnPrimary: {
    background: '#2196F3',
    color: 'white',
    border: 'none',
    padding: '10px 20px',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
    width: '100%',
  },
  emptyState: {
    textAlign: 'center',
    color: '#999',
    padding: '20px',
  },
};
