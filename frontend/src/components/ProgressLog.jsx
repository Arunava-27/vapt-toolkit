export default function ProgressLog({ entries, scanning }) {
  if (!entries.length) return null;
  const hasActiveStep = entries.some((e) => e.type === "progress");
  const isActive = scanning || hasActiveStep;

  return (
    <div className="progress-log">
      <h3>{isActive ? "⏳ Scan Progress" : "✅ Scan Summary"}</h3>
      <div className="log-entries">
        {entries.map((e, i) => (
          <div key={i} className={`log-entry ${e.type}`}>
            <span className="dot" />
            <span>{e.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
