export function SectionCustomizer({ section, onUpdateSetting }) {
  return (
    <div style={styles.sectionCustomization}>
      {section.type === 'header' && (
        <>
          <label style={styles.label}>
            Title:
            <input
              type="text"
              value={section.settings.title || ''}
              onChange={(e) =>
                onUpdateSetting(
                  section.id,
                  'title',
                  e.target.value
                )
              }
              placeholder="Report Title"
              style={styles.input}
            />
          </label>
        </>
      )}

      {section.type === 'summary' && (
        <>
          <label style={styles.label}>
            <input
              type="checkbox"
              checked={section.settings.show_project || false}
              onChange={(e) =>
                onUpdateSetting(
                  section.id,
                  'show_project',
                  e.target.checked
                )
              }
            />
            Show Project Name
          </label>
          <label style={styles.label}>
            <input
              type="checkbox"
              checked={section.settings.show_date || false}
              onChange={(e) =>
                onUpdateSetting(
                  section.id,
                  'show_date',
                  e.target.checked
                )
              }
            />
            Show Date
          </label>
        </>
      )}

      {section.type === 'findings' && (
        <>
          <label style={styles.label}>
            Results per page:
            <input
              type="number"
              value={section.settings.limit || 10}
              onChange={(e) =>
                onUpdateSetting(
                  section.id,
                  'limit',
                  parseInt(e.target.value)
                )
              }
              min="1"
              max="100"
              style={styles.input}
            />
          </label>
          <label style={styles.label}>
            <input
              type="checkbox"
              checked={section.settings.show_severity || true}
              onChange={(e) =>
                onUpdateSetting(
                  section.id,
                  'show_severity',
                  e.target.checked
                )
              }
            />
            Show Severity
          </label>
        </>
      )}
    </div>
  );
}

const styles = {
  sectionCustomization: {
    padding: '12px',
    background: '#f0f8ff',
    borderTop: '1px solid #ddd',
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
  },
  label: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '14px',
  },
  input: {
    padding: '6px',
    border: '1px solid #ddd',
    borderRadius: '3px',
    fontSize: '13px',
    flex: '1',
  },
};
