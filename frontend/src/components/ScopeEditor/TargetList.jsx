import { TargetInput } from './TargetInput';

export function TargetList({
  targetsByType,
  targets,
  draggedId,
  onDragStart,
  onDragOver,
  onDrop,
  onUpdateTarget,
  onRemoveTarget,
}) {
  return (
    <div style={styles.scopeList}>
      {Object.entries(targetsByType).map(([type, typeTargets]) => {
        if (typeTargets.length === 0) return null;

        return (
          <div key={type} style={styles.targetGroup}>
            <h3 style={styles.groupHeader}>
              <span style={{ ...styles.typeBadge, ...styles[`badge_${type}`] }}>
                {type.toUpperCase()}
              </span>
              <span style={styles.groupCount}>{typeTargets.length}</span>
            </h3>
            <div style={styles.targetsContainer}>
              {typeTargets.map(target => (
                <TargetInput
                  key={target.id}
                  target={target}
                  draggedId={draggedId}
                  onDragStart={onDragStart}
                  onDragOver={onDragOver}
                  onDrop={onDrop}
                  onUpdateTarget={onUpdateTarget}
                  onRemoveTarget={onRemoveTarget}
                />
              ))}
            </div>
          </div>
        );
      })}

      {targets.length === 0 && (
        <div style={styles.emptyState}>
          <p>No targets added yet</p>
          <p style={styles.hint}>Click "Add Target" or "Paste Bulk" to get started</p>
        </div>
      )}
    </div>
  );
}

const styles = {
  scopeList: {
    marginTop: '20px',
  },
  targetGroup: {
    marginBottom: '20px',
  },
  groupHeader: {
    display: 'flex',
    gap: '10px',
    alignItems: 'center',
    marginBottom: '12px',
    margin: '0 0 12px 0',
  },
  typeBadge: {
    display: 'inline-block',
    padding: '4px 12px',
    borderRadius: '3px',
    fontSize: '12px',
    fontWeight: 'bold',
    color: 'white',
  },
  badge_url: { background: '#2196F3' },
  badge_domain: { background: '#4CAF50' },
  badge_ip: { background: '#FF9800' },
  badge_wildcard: { background: '#9C27B0' },
  badge_endpoint: { background: '#F44336' },
  groupCount: {
    display: 'inline-block',
    padding: '2px 8px',
    background: '#f0f0f0',
    borderRadius: '12px',
    fontSize: '12px',
    color: '#666',
  },
  targetsContainer: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  emptyState: {
    textAlign: 'center',
    padding: '40px 20px',
    color: '#999',
  },
  hint: {
    fontSize: '12px',
    color: '#bbb',
    marginTop: '8px',
  },
};
