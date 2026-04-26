export function TargetInput({ target, draggedId, onDragStart, onDragOver, onDrop, onUpdateTarget, onRemoveTarget }) {
  return (
    <div
      style={{
        ...styles.targetItem,
        ...(target.error ? styles.targetItemError : {}),
        ...(draggedId === target.id ? styles.targetItemDragging : {}),
      }}
      draggable
      onDragStart={e => onDragStart(e, target.id)}
      onDragOver={onDragOver}
      onDrop={e => onDrop(e, target.id)}
    >
      <div style={styles.targetDragHandle}>⋮⋮</div>
      <input
        type="text"
        style={styles.targetInputField}
        value={target.value}
        onChange={e => onUpdateTarget(target.id, e.target.value)}
        placeholder={`Enter ${target.type}...`}
      />
      <button
        onClick={() => onRemoveTarget(target.id)}
        style={styles.btnRemove}
        title="Remove target"
      >
        ✕
      </button>
      {target.error && (
        <div style={styles.targetError}>{target.error}</div>
      )}
    </div>
  );
}

const styles = {
  targetItem: {
    display: 'flex',
    gap: '8px',
    alignItems: 'center',
    padding: '12px',
    background: '#f9f9f9',
    border: '1px solid #ddd',
    borderRadius: '4px',
    marginBottom: '8px',
    transition: 'all 0.2s',
  },
  targetItemError: {
    borderColor: '#f44336',
    background: '#ffebee',
  },
  targetItemDragging: {
    opacity: 0.5,
    borderStyle: 'dashed',
  },
  targetDragHandle: {
    cursor: 'grab',
    color: '#999',
    userSelect: 'none',
    fontSize: '14px',
  },
  targetInputField: {
    flex: 1,
    padding: '8px',
    border: '1px solid #ddd',
    borderRadius: '3px',
    fontSize: '14px',
  },
  btnRemove: {
    padding: '6px 10px',
    background: '#f44336',
    color: 'white',
    border: 'none',
    borderRadius: '3px',
    cursor: 'pointer',
    fontSize: '12px',
  },
  targetError: {
    position: 'absolute',
    bottom: '-20px',
    left: '0',
    fontSize: '12px',
    color: '#f44336',
    width: '100%',
  },
};
