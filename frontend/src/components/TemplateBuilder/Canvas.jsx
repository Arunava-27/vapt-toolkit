import { SectionCustomizer } from './SectionCustomizer';

export function Canvas({
  sections,
  draggedSection,
  showCustomization,
  onDragOver,
  onDrop,
  onShowCustomization,
  onRemoveSection,
  onMoveSectionUp,
  onMoveSectionDown,
  onUpdateSectionSetting,
}) {
  return (
    <div style={styles.canvasArea}>
      <div
        style={styles.canvas}
        onDragOver={onDragOver}
        onDrop={onDrop}
      >
        <div style={styles.canvasHeader}>
          <h3>Template Canvas</h3>
          <p style={styles.hint}>Drop sections here to build template</p>
        </div>

        {sections.length === 0 ? (
          <div style={styles.canvasEmpty}>
            <p>Drag sections here to build your template</p>
          </div>
        ) : (
          <div style={styles.sectionsStack}>
            {sections.map((section, index) => (
              <div key={section.id} style={styles.canvasSection}>
                <div style={styles.sectionHeader}>
                  <span style={styles.sectionName}>{section.name}</span>
                  <div style={styles.sectionControls}>
                    <button
                      style={{ ...styles.btnMini }}
                      onClick={() => onMoveSectionUp(index)}
                      disabled={index === 0}
                      title="Move up"
                    >
                      ↑
                    </button>
                    <button
                      style={{ ...styles.btnMini }}
                      onClick={() => onMoveSectionDown(index)}
                      disabled={index === sections.length - 1}
                      title="Move down"
                    >
                      ↓
                    </button>
                    <button
                      style={{ ...styles.btnMini, ...styles.btnSettings }}
                      onClick={() =>
                        onShowCustomization(
                          showCustomization === section.id
                            ? null
                            : section.id
                        )
                      }
                      title="Customize"
                    >
                      ⚙️
                    </button>
                    <button
                      style={{ ...styles.btnMini, ...styles.btnRemove }}
                      onClick={() => onRemoveSection(section.id)}
                      title="Remove"
                    >
                      ✕
                    </button>
                  </div>
                </div>

                {showCustomization === section.id && (
                  <SectionCustomizer
                    section={section}
                    onUpdateSetting={onUpdateSectionSetting}
                  />
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  canvasArea: {
    background: 'white',
    padding: '15px',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
  },
  canvas: {
    minHeight: '400px',
    border: '2px dashed #2196F3',
    borderRadius: '4px',
    padding: '15px',
    background: '#fafafa',
  },
  canvasHeader: {
    marginBottom: '20px',
  },
  hint: {
    fontSize: '12px',
    color: '#999',
    margin: '10px 0',
  },
  canvasEmpty: {
    textAlign: 'center',
    color: '#999',
    padding: '60px 20px',
  },
  sectionsStack: {
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
  },
  canvasSection: {
    background: 'white',
    border: '1px solid #ddd',
    borderRadius: '4px',
    overflow: 'hidden',
  },
  sectionHeader: {
    background: '#f9f9f9',
    padding: '10px 12px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottom: '1px solid #ddd',
  },
  sectionName: {
    fontWeight: 'bold',
    color: '#333',
  },
  sectionControls: {
    display: 'flex',
    gap: '4px',
  },
  btnMini: {
    padding: '4px 8px',
    border: '1px solid #ddd',
    background: 'white',
    borderRadius: '3px',
    cursor: 'pointer',
    fontSize: '12px',
    transition: 'all 0.2s',
  },
  btnSettings: {
    // Hover effects handled via CSS
  },
  btnRemove: {
    // Hover effects handled via CSS
  },
};
