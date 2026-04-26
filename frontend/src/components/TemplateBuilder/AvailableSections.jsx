export function AvailableSections({ availableSections, onDragStart }) {
  return (
    <div style={styles.availableSections}>
      <h3>Available Sections</h3>
      <p style={styles.hint}>Drag sections to the canvas below</p>
      <div style={styles.sectionsList}>
        {availableSections.map((section) => (
          <div
            key={section.id}
            style={styles.sectionItem}
            draggable
            onDragStart={() => onDragStart(section)}
            onDragOver={(e) => e.preventDefault()}
          >
            <span style={styles.sectionIcon}>{section.icon}</span>
            <span>{section.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

const styles = {
  availableSections: {
    background: 'white',
    padding: '15px',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
  },
  hint: {
    fontSize: '12px',
    color: '#999',
    margin: '10px 0',
  },
  sectionsList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  sectionItem: {
    padding: '10px',
    background: '#f0f0f0',
    border: '1px solid #ddd',
    borderRadius: '4px',
    cursor: 'move',
    display: 'flex',
    gap: '8px',
    alignItems: 'center',
    transition: 'all 0.2s',
    userSelect: 'none',
  },
  sectionIcon: {
    fontSize: '18px',
  },
};
